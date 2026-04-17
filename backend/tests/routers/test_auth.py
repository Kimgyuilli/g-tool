"""Tests for /auth endpoints."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import jwt
from httpx import AsyncClient
from sqlalchemy import select

from app.config import settings
from app.core.security import decrypt_value
from app.mail.models import User
from tests.conftest import auth_cookie


async def test_login_returns_auth_url(client: AsyncClient):
    """GET /auth/login should return auth_url."""
    response = await client.get("/auth/login")
    assert response.status_code == 200
    data = response.json()
    assert "auth_url" in data
    assert data["auth_url"].startswith("https://accounts.google.com/o/oauth2")


async def test_me_success(client: AsyncClient, sample_user):
    """GET /auth/me should return user info when user exists."""
    response = await client.get("/auth/me", headers=auth_cookie(sample_user.id))
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == sample_user.id
    assert data["email"] == sample_user.email
    assert data["google_connected"] is True
    assert data["naver_connected"] is False


async def test_me_not_authenticated(client: AsyncClient):
    """GET /auth/me should return 401 when no cookie is provided."""
    response = await client.get("/auth/me")
    assert response.status_code == 401
    data = response.json()
    assert "Not authenticated" in data["detail"]


async def test_callback_creates_user_and_sets_cookie(
    client: AsyncClient, db_session, monkeypatch
):
    credentials = SimpleNamespace(token="access-token", refresh_token="refresh-token")

    monkeypatch.setattr(
        "app.auth.router.exchange_code",
        lambda code: credentials,
    )

    async def fake_get_user_email(received_credentials):
        assert received_credentials is credentials
        return "new-user@example.com"

    monkeypatch.setattr("app.auth.router.get_user_email", fake_get_user_email)

    response = await client.get("/auth/callback?code=test-code", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == settings.frontend_url
    assert "session_token=" in response.headers["set-cookie"]

    created_user = await db_session.scalar(
        select(User).where(User.email == "new-user@example.com")
    )
    assert created_user is not None
    assert decrypt_value(created_user.google_oauth_token) == "access-token"
    assert decrypt_value(created_user.google_refresh_token) == "refresh-token"


async def test_callback_updates_existing_user_without_overwriting_refresh_token(
    client: AsyncClient, db_session, sample_user, monkeypatch
):
    credentials = SimpleNamespace(token="new-access-token", refresh_token=None)

    monkeypatch.setattr(
        "app.auth.router.exchange_code",
        lambda code: credentials,
    )

    async def fake_get_user_email(received_credentials):
        assert received_credentials is credentials
        return sample_user.email

    monkeypatch.setattr("app.auth.router.get_user_email", fake_get_user_email)

    original_refresh_token = sample_user.google_refresh_token

    response = await client.get("/auth/callback?code=test-code", follow_redirects=False)

    assert response.status_code == 307

    await db_session.refresh(sample_user)
    assert decrypt_value(sample_user.google_oauth_token) == "new-access-token"
    assert sample_user.google_refresh_token == original_refresh_token


async def test_callback_returns_400_when_exchange_code_fails(
    client: AsyncClient, monkeypatch
):
    def fake_exchange_code(_code: str):
        raise RuntimeError("boom")

    monkeypatch.setattr("app.auth.router.exchange_code", fake_exchange_code)

    response = await client.get("/auth/callback?code=test-code")

    assert response.status_code == 400
    assert response.json()["detail"] == "Token exchange failed: boom"


async def test_me_renews_cookie_when_token_is_past_half_life(
    client: AsyncClient, sample_user, monkeypatch
):
    now = datetime(2026, 4, 8, tzinfo=UTC)
    original_token = "token-near-expiry"

    class _FrozenDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return now if tz else now.replace(tzinfo=None)

        @classmethod
        def fromtimestamp(cls, timestamp, tz=None):
            return datetime.fromtimestamp(timestamp, tz=tz)

    monkeypatch.setattr(
        "app.core.dependencies.verify_access_token",
        lambda token: sample_user.id,
    )
    monkeypatch.setattr(
        "app.auth.router.pyjwt.decode",
        lambda token, key, algorithms: {
            "sub": str(sample_user.id),
            "exp": int(
                (
                    now + timedelta(minutes=settings.jwt_expire_minutes / 4)
                ).timestamp()
            ),
        },
    )
    monkeypatch.setattr("app.auth.router.datetime", _FrozenDateTime)

    response = await client.get(
        "/auth/me",
        headers={"Cookie": f"session_token={original_token}"},
    )

    assert response.status_code == 200
    set_cookie = response.headers["set-cookie"]
    assert "session_token=" in set_cookie
    assert original_token not in set_cookie


async def test_me_does_not_renew_cookie_when_token_has_enough_time_left(
    client: AsyncClient, sample_user, monkeypatch
):
    now = datetime(2026, 4, 8, tzinfo=UTC)
    token = "token-with-enough-time"

    class _FrozenDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return now if tz else now.replace(tzinfo=None)

        @classmethod
        def fromtimestamp(cls, timestamp, tz=None):
            return datetime.fromtimestamp(timestamp, tz=tz)

    monkeypatch.setattr(
        "app.core.dependencies.verify_access_token",
        lambda token: sample_user.id,
    )
    monkeypatch.setattr(
        "app.auth.router.pyjwt.decode",
        lambda token, key, algorithms: {
            "sub": str(sample_user.id),
            "exp": int(
                (
                    now + timedelta(minutes=settings.jwt_expire_minutes)
                ).timestamp()
            ),
        },
    )
    monkeypatch.setattr("app.auth.router.datetime", _FrozenDateTime)

    response = await client.get(
        "/auth/me",
        headers={"Cookie": f"session_token={token}"},
    )

    assert response.status_code == 200
    assert "set-cookie" not in response.headers


async def test_me_ignores_invalid_jwt_cookie_and_returns_user_info(
    client: AsyncClient, sample_user, monkeypatch
):
    def fake_decode(*args, **kwargs):
        raise jwt.InvalidTokenError("bad token")

    monkeypatch.setattr(
        "app.core.dependencies.verify_access_token",
        lambda token: sample_user.id,
    )
    monkeypatch.setattr("app.auth.router.pyjwt.decode", fake_decode)

    response = await client.get(
        "/auth/me",
        headers={"Cookie": "session_token=invalid-token"},
    )

    assert response.status_code == 200
    assert response.json()["user_id"] == sample_user.id


async def test_me_reports_google_disconnected_without_refresh_token(
    client: AsyncClient, db_session
):
    user = User(
        email="partial-google@example.com",
        google_oauth_token="access-token-only",
        google_refresh_token=None,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    response = await client.get("/auth/me", headers=auth_cookie(user.id))

    assert response.status_code == 200
    data = response.json()
    assert data["google_connected"] is True
    assert data["naver_connected"] is False
