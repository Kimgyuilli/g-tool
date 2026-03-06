"""Tests for /api/classify endpoints."""

from __future__ import annotations

from httpx import AsyncClient

from tests.conftest import auth_cookie


async def test_get_categories(client: AsyncClient):
    """GET /api/classify/categories should return available categories."""
    response = await client.get("/api/classify/categories")
    assert response.status_code == 200
    data = response.json()

    assert "categories" in data
    assert isinstance(data["categories"], list)
    assert len(data["categories"]) > 0
    # Default categories from classifier
    assert "업무" in data["categories"]
    assert "개인" in data["categories"]


async def test_update_classification_success(
    client: AsyncClient,
    sample_user,
    sample_mails,
    sample_labels,
    sample_classification,
    db_session,
):
    """PUT /api/classify/update should update classification category."""
    # Ensure "개인" label exists (fixture creates it)
    _ = sample_labels["personal"]

    request_body = {
        "classification_id": sample_classification.id,
        "new_category": "개인",
    }

    response = await client.put(
        "/api/classify/update",
        json=request_body,
        headers=auth_cookie(sample_user.id),
    )
    assert response.status_code == 200
    data = response.json()

    assert data["classification_id"] == sample_classification.id
    assert data["new_category"] == "개인"
    assert "분류가 수정되었습니다" in data["message"]


async def test_update_classification_not_found(client: AsyncClient, sample_user):
    """PUT /api/classify/update should return 404 for invalid classification_id."""
    request_body = {
        "classification_id": 999,
        "new_category": "개인",
    }

    response = await client.put(
        "/api/classify/update",
        json=request_body,
        headers=auth_cookie(sample_user.id),
    )
    assert response.status_code == 404
    data = response.json()
    assert "Classification not found" in data["detail"]


async def test_update_classification_unauthorized(
    client: AsyncClient, sample_classification, db_session
):
    """PUT /api/classify/update should return 403 when user doesn't own the mail."""
    from app.mail.models import User

    # Create another user
    other_user = User(
        email="other@example.com",
        google_oauth_token="other_token",
        google_refresh_token="other_refresh",
    )
    db_session.add(other_user)
    await db_session.commit()
    await db_session.refresh(other_user)

    request_body = {
        "classification_id": sample_classification.id,
        "new_category": "개인",
    }

    response = await client.put(
        "/api/classify/update",
        json=request_body,
        headers=auth_cookie(other_user.id),
    )
    assert response.status_code == 403
    data = response.json()
    assert "Not authorized" in data["detail"]


async def test_get_feedback_stats(
    client: AsyncClient, sample_user, sample_classification
):
    """GET /api/classify/feedback-stats should return feedback statistics."""
    response = await client.get(
        "/api/classify/feedback-stats",
        headers=auth_cookie(sample_user.id),
    )
    assert response.status_code == 200
    data = response.json()

    assert "total_feedbacks" in data
    assert "sender_rules" in data
    assert "recent_feedbacks" in data
    assert isinstance(data["total_feedbacks"], int)
    assert isinstance(data["sender_rules"], list)
    assert isinstance(data["recent_feedbacks"], list)
