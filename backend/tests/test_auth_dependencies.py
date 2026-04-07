from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from google.auth.exceptions import RefreshError

from app.auth.dependencies import get_google_user


class _FailingCredentials:
    expired = True
    refresh_token = "refresh-token"
    token = "stale-token"

    def refresh(self, _request) -> None:
        raise RefreshError("refresh token revoked")


class _UnusedDbSession:
    async def commit(self) -> None:
        raise AssertionError("commit should not run when refresh fails")


@pytest.mark.asyncio
async def test_get_google_user_returns_401_on_refresh_error(monkeypatch):
    user = SimpleNamespace(
        id=123,
        google_oauth_token="encrypted-token",
        google_refresh_token="encrypted-refresh-token",
    )

    async def fake_to_thread(func, *args, **kwargs):
        return func(*args, **kwargs)

    monkeypatch.setattr("app.auth.dependencies.decrypt_value", lambda value: value)
    monkeypatch.setattr(
        "app.auth.dependencies.build_credentials",
        lambda token, refresh_token: _FailingCredentials(),
    )
    monkeypatch.setattr("app.auth.dependencies.asyncio.to_thread", fake_to_thread)

    with pytest.raises(HTTPException) as exc_info:
        await get_google_user(user=user, db=_UnusedDbSession())

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail["code"] == "token_expired"
    assert "다시 로그인" in exc_info.value.detail["message"]
