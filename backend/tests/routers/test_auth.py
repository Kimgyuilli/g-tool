"""Tests for /auth endpoints."""

from __future__ import annotations

from httpx import AsyncClient

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


async def test_me_user_not_found(client: AsyncClient):
    """GET /auth/me should return 404 when no cookie is provided."""
    response = await client.get("/auth/me")
    assert response.status_code == 404
    data = response.json()
    assert "User not found" in data["detail"]
