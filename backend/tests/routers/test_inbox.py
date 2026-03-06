"""Tests for /api/inbox endpoints."""

from __future__ import annotations

from httpx import AsyncClient

from tests.conftest import auth_cookie


async def test_list_inbox_messages_all(
    client: AsyncClient, sample_user, sample_mails, sample_classification
):
    """GET /api/inbox/messages should return all messages from both sources."""
    response = await client.get(
        "/api/inbox/messages", headers=auth_cookie(sample_user.id)
    )
    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 3  # 2 Gmail + 1 Naver
    assert len(data["messages"]) == 3

    # Check sources
    sources = {msg["source"] for msg in data["messages"]}
    assert sources == {"gmail", "naver"}


async def test_list_inbox_messages_gmail_only(
    client: AsyncClient, sample_user, sample_mails
):
    """GET /api/inbox/messages?source=gmail should return only Gmail messages."""
    response = await client.get(
        "/api/inbox/messages?source=gmail",
        headers=auth_cookie(sample_user.id),
    )
    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 2
    assert len(data["messages"]) == 2
    assert all(msg["source"] == "gmail" for msg in data["messages"])


async def test_list_inbox_messages_naver_only(
    client: AsyncClient, sample_user, sample_mails
):
    """GET /api/inbox/messages?source=naver should return only Naver messages."""
    response = await client.get(
        "/api/inbox/messages?source=naver",
        headers=auth_cookie(sample_user.id),
    )
    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 1
    assert len(data["messages"]) == 1
    assert data["messages"][0]["source"] == "naver"


async def test_list_inbox_messages_by_category(
    client: AsyncClient, sample_user, sample_mails, sample_classification
):
    """GET /api/inbox/messages?category=업무 should filter by category."""
    response = await client.get(
        "/api/inbox/messages?category=업무",
        headers=auth_cookie(sample_user.id),
    )
    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 1  # Only gmail1 has 업무 classification
    assert len(data["messages"]) == 1
    assert data["messages"][0]["classification"]["category"] == "업무"


async def test_list_inbox_messages_unclassified(
    client: AsyncClient, sample_user, sample_mails, sample_classification
):
    """GET /api/inbox/messages?category=unclassified returns unclassified."""
    response = await client.get(
        "/api/inbox/messages?category=unclassified",
        headers=auth_cookie(sample_user.id),
    )
    assert response.status_code == 200
    data = response.json()

    # gmail1 is classified, gmail2 and naver1 are not
    assert data["total"] == 2
    assert len(data["messages"]) == 2


async def test_get_category_counts(
    client: AsyncClient, sample_user, sample_mails, sample_classification, sample_labels
):
    """GET /api/inbox/category-counts should return category statistics."""
    response = await client.get(
        "/api/inbox/category-counts",
        headers=auth_cookie(sample_user.id),
    )
    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 3  # Total mails
    assert data["unclassified"] == 2  # gmail2, naver1
    assert isinstance(data["categories"], list)

    # Find 업무 category
    work_category = next(
        (c for c in data["categories"] if c["name"] == "업무"), None
    )
    assert work_category is not None
    assert work_category["count"] == 1
    assert work_category["color"] == "blue"
