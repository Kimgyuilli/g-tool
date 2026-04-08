from __future__ import annotations

import pytest
from google.auth.exceptions import RefreshError
from sqlalchemy import select

from app.core.background_sync import sync_user_gmail
from app.mail.models import User


class _Credentials:
    token = "access-token"


@pytest.mark.asyncio
async def test_sync_user_gmail_disconnects_on_invalid_scope(
    monkeypatch, db_session, sample_user
):
    monkeypatch.setattr(
        "app.core.background_sync.decrypt_value",
        lambda value: value,
    )
    monkeypatch.setattr(
        "app.core.background_sync.build_credentials",
        lambda token, refresh_token: _Credentials(),
    )

    async def fake_list_message_ids(*args, **kwargs):
        raise RefreshError(
            "('invalid_scope: Bad Request', {'error': 'invalid_scope'})"
        )

    monkeypatch.setattr(
        "app.core.background_sync.list_message_ids",
        fake_list_message_ids,
    )

    synced_count = await sync_user_gmail(sample_user, db_session)
    assert synced_count == 0

    refreshed_user = await db_session.scalar(
        select(User).where(User.id == sample_user.id)
    )
    assert refreshed_user is not None
    assert refreshed_user.google_oauth_token is None
    assert refreshed_user.google_refresh_token is None
