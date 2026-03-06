"""Tests for /api/gmail endpoints."""

from __future__ import annotations

from httpx import AsyncClient

from tests.conftest import auth_cookie


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


async def test_get_gmail_message_user_not_found(client: AsyncClient):
    """GET /api/gmail/messages should return 404 when no cookie is provided."""
    response = await client.get("/api/gmail/messages")
    assert response.status_code == 404
    data = response.json()
    assert "User not found" in data["detail"]
