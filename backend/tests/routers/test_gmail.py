"""Tests for /api/gmail endpoints."""

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


def _patch_google_dependency(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.auth.dependencies.decrypt_value", lambda value: value
    )
    monkeypatch.setattr(
        "app.auth.dependencies.build_credentials",
        lambda token, refresh_token: _StubCredentials(),
    )


async def test_list_gmail_messages_success(
    client: AsyncClient, sample_user, sample_mails, sample_classification
):
    """GET /api/gmail/messages should return Gmail messages."""
    response = await client.get(
        "/api/gmail/messages", headers=auth_cookie(sample_user.id)
    )
    assert response.status_code == 200
    data = response.json()

    assert "total" in data
    assert "messages" in data
    assert data["total"] == 2  # 2 Gmail messages
    assert len(data["messages"]) == 2


async def test_list_gmail_messages_pagination(
    client: AsyncClient, sample_user, sample_mails
):
    """GET /api/gmail/messages should support offset and limit."""
    response = await client.get(
        "/api/gmail/messages?offset=0&limit=1",
        headers=auth_cookie(sample_user.id),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["messages"]) == 1
    assert data["offset"] == 0
    assert data["limit"] == 1


async def test_get_gmail_message_success(
    client: AsyncClient, sample_user, sample_mails, sample_classification
):
    """GET /api/gmail/messages/{id} should return mail detail."""
    mail_id = sample_mails["gmail1"].id
    response = await client.get(
        f"/api/gmail/messages/{mail_id}",
        headers=auth_cookie(sample_user.id),
    )
    assert response.status_code == 200
    data = response.json()

    assert data["id"] == mail_id
    assert data["subject"] == "Test Gmail 1"
    assert data["body_text"] is not None
    assert "classification" in data


async def test_get_gmail_message_not_found(client: AsyncClient, sample_user):
    """GET /api/gmail/messages/{id} should return 404 for non-existent mail."""
    response = await client.get(
        "/api/gmail/messages/999",
        headers=auth_cookie(sample_user.id),
    )
    assert response.status_code == 404
    data = response.json()
    assert "Message not found" in data["detail"]


async def test_get_gmail_message_not_authenticated(client: AsyncClient):
    """GET /api/gmail/messages should return 401 when no cookie is provided."""
    response = await client.get("/api/gmail/messages")
    assert response.status_code == 401
    data = response.json()
    assert "Not authenticated" in data["detail"]


@pytest.mark.asyncio
async def test_sync_gmail_returns_401_on_refresh_error(
    client: AsyncClient, sample_user, monkeypatch
):
    """POST /api/gmail/sync 중 RefreshError는 401 token_expired로 변환되어야 한다."""
    _patch_google_dependency(monkeypatch)

    async def fake_sync(*_args, **_kwargs):
        raise RefreshError("Token has been expired or revoked")

    monkeypatch.setattr(
        "app.mail.routers.gmail.sync_gmail_messages", fake_sync
    )

    response = await client.post(
        "/api/gmail/sync", headers=auth_cookie(sample_user.id)
    )
    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "token_expired"


@pytest.mark.asyncio
async def test_sync_gmail_returns_401_on_scope_mismatch(
    client: AsyncClient, sample_user, monkeypatch
):
    """invalid_scope RefreshError는 google_reconnect_required + 계정 disconnect."""
    _patch_google_dependency(monkeypatch)

    async def fake_sync(*_args, **_kwargs):
        raise RefreshError(
            "('invalid_scope: Bad Request', {'error': 'invalid_scope'})"
        )

    monkeypatch.setattr(
        "app.mail.routers.gmail.sync_gmail_messages", fake_sync
    )

    response = await client.post(
        "/api/gmail/sync", headers=auth_cookie(sample_user.id)
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
async def test_sync_all_gmail_returns_401_on_refresh_error(
    client: AsyncClient, sample_user, monkeypatch
):
    """POST /sync/full도 RefreshError를 401로 변환해야 한다."""
    _patch_google_dependency(monkeypatch)

    async def fake_sync_all(*_args, **_kwargs):
        raise RefreshError("Token has been expired or revoked")

    monkeypatch.setattr(
        "app.mail.routers.gmail.sync_all_gmail_messages", fake_sync_all
    )

    response = await client.post(
        "/api/gmail/sync/full", headers=auth_cookie(sample_user.id)
    )
    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "token_expired"


@pytest.mark.asyncio
async def test_apply_labels_returns_401_on_scope_mismatch(
    client: AsyncClient,
    sample_user,
    sample_mails,
    sample_classification,
    monkeypatch,
):
    """POST /apply-labels도 invalid_scope 시 reconnect + disconnect를 반환해야 한다."""
    _patch_google_dependency(monkeypatch)

    async def fake_apply_labels(*_args, **_kwargs):
        raise RefreshError(
            "('invalid_scope: Bad Request', {'error': 'invalid_scope'})"
        )

    monkeypatch.setattr(
        "app.mail.routers.gmail.apply_classification_labels_to_gmail",
        fake_apply_labels,
    )

    response = await client.post(
        "/api/gmail/apply-labels",
        headers=auth_cookie(sample_user.id),
        json={"mail_ids": [sample_mails["gmail1"].id]},
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
