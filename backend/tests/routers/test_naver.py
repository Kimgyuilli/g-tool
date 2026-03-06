"""Tests for /api/naver endpoints."""

from __future__ import annotations

from httpx import AsyncClient

from tests.conftest import auth_cookie


async def test_list_naver_messages_success(
    client: AsyncClient, sample_user, sample_mails
):
    """GET /api/naver/messages should return Naver messages."""
    response = await client.get(
        "/api/naver/messages", headers=auth_cookie(sample_user.id)
    )
    assert response.status_code == 200
    data = response.json()

    assert "total" in data
    assert "messages" in data
    assert data["total"] == 1  # 1 Naver message
    assert len(data["messages"]) == 1
    assert data["messages"][0]["folder"] == "INBOX"


async def test_list_naver_messages_pagination(
    client: AsyncClient, sample_user, sample_mails
):
    """GET /api/naver/messages should support offset and limit."""
    response = await client.get(
        "/api/naver/messages?offset=0&limit=10",
        headers=auth_cookie(sample_user.id),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["offset"] == 0
    assert data["limit"] == 10


async def test_get_naver_message_success(
    client: AsyncClient, sample_user, sample_mails
):
    """GET /api/naver/messages/{id} should return mail detail with folder."""
    mail_id = sample_mails["naver1"].id
    response = await client.get(
        f"/api/naver/messages/{mail_id}",
        headers=auth_cookie(sample_user.id),
    )
    assert response.status_code == 200
    data = response.json()

    assert data["id"] == mail_id
    assert data["subject"] == "Test Naver Mail"
    assert data["folder"] == "INBOX"
    assert data["body_text"] is not None


async def test_get_naver_message_not_found(client: AsyncClient, sample_user):
    """GET /api/naver/messages/{id} should return 404 for non-existent mail."""
    response = await client.get(
        "/api/naver/messages/999",
        headers=auth_cookie(sample_user.id),
    )
    assert response.status_code == 404
    data = response.json()
    assert "Message not found" in data["detail"]
