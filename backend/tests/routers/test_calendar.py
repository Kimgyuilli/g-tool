"""Tests for /api/calendar endpoints — Google refresh 방어선 회귀 테스트."""

from __future__ import annotations

import pytest
from google.auth.exceptions import RefreshError
from httpx import AsyncClient
from sqlalchemy import select

from app.mail.models import User
from tests.conftest import TestingSessionLocal, auth_cookie


class _StubCredentials:
    """get_google_user의 선제 refresh 분기를 건너뛰기 위한 더미."""

    expired = False
    refresh_token = "refresh-token"
    token = "access-token"


def _patch_dependency(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.auth.dependencies.decrypt_value", lambda value: value
    )
    monkeypatch.setattr(
        "app.auth.dependencies.build_credentials",
        lambda token, refresh_token: _StubCredentials(),
    )


@pytest.mark.asyncio
async def test_get_calendars_returns_401_on_refresh_error(
    client: AsyncClient, sample_user, monkeypatch
):
    """googleapiclient 내부 RefreshError가 401 token_expired로 변환되어야 한다."""
    _patch_dependency(monkeypatch)

    async def fake_list_calendars(*_args, **_kwargs):
        raise RefreshError("Token has been expired or revoked")

    monkeypatch.setattr(
        "app.calendar.router.list_calendars", fake_list_calendars
    )

    response = await client.get(
        "/api/calendar/calendars", headers=auth_cookie(sample_user.id)
    )
    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "token_expired"


@pytest.mark.asyncio
async def test_get_calendars_returns_401_on_scope_mismatch(
    client: AsyncClient, sample_user, monkeypatch
):
    """invalid_scope RefreshError는 google_reconnect_required + 계정 disconnect."""
    _patch_dependency(monkeypatch)

    async def fake_list_calendars(*_args, **_kwargs):
        raise RefreshError(
            "('invalid_scope: Bad Request', {'error': 'invalid_scope'})"
        )

    monkeypatch.setattr(
        "app.calendar.router.list_calendars", fake_list_calendars
    )

    response = await client.get(
        "/api/calendar/calendars", headers=auth_cookie(sample_user.id)
    )
    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "google_reconnect_required"

    async with TestingSessionLocal() as verify:
        refreshed = await verify.scalar(
            select(User).where(User.id == sample_user.id)
        )
        assert refreshed is not None
        assert refreshed.google_oauth_token is None
        assert refreshed.google_refresh_token is None


@pytest.mark.asyncio
async def test_get_events_returns_401_on_refresh_error(
    client: AsyncClient, sample_user, monkeypatch
):
    """GET /events도 동일한 방어선이 적용되어야 한다."""
    _patch_dependency(monkeypatch)

    async def fake_list_events(*_args, **_kwargs):
        raise RefreshError("Token has been expired or revoked")

    monkeypatch.setattr("app.calendar.router.list_events", fake_list_events)

    response = await client.get(
        "/api/calendar/events", headers=auth_cookie(sample_user.id)
    )
    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "token_expired"
