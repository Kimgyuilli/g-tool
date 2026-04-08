"""Auth dependencies: get_google_user, get_naver_user."""

from __future__ import annotations

import asyncio
import logging

from fastapi import Depends, HTTPException
from google.auth.exceptions import RefreshError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.service import build_credentials, is_google_scope_mismatch_error
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.exceptions import AccountNotConnectedException
from app.core.security import decrypt_value, encrypt_value
from app.mail.models import User

logger = logging.getLogger(__name__)


async def _disconnect_google_account(
    user: User,
    db: AsyncSession,
) -> None:
    """Remove stored Google OAuth credentials for the user."""
    user.google_oauth_token = None
    user.google_refresh_token = None
    await db.commit()


async def get_google_user(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> tuple[User, object]:
    """Validate user has Google OAuth connected and return (user, credentials).

    Also handles token refresh if expired.
    """
    if not user.google_oauth_token or not user.google_refresh_token:
        raise AccountNotConnectedException("Google")

    token = decrypt_value(user.google_oauth_token)
    refresh_token = decrypt_value(user.google_refresh_token)
    credentials = build_credentials(token, refresh_token)

    if credentials.expired and credentials.refresh_token:
        try:
            from google.auth.transport.requests import Request

            await asyncio.to_thread(credentials.refresh, Request())
            user.google_oauth_token = encrypt_value(credentials.token)
            await db.commit()
        except RefreshError as exc:
            logger.warning(f"Google 토큰 갱신 실패 (user={user.id}): {exc}")
            if is_google_scope_mismatch_error(exc):
                await _disconnect_google_account(user, db)
                raise HTTPException(
                    status_code=401,
                    detail={
                        "code": "google_reconnect_required",
                        "message": (
                            "Google 권한 구성이 변경되어 계정 재연결이 필요합니다. "
                            "Google 로그인을 다시 진행해주세요."
                        ),
                    },
                ) from exc
            raise HTTPException(
                status_code=401,
                detail={
                    "code": "token_expired",
                    "message": (
                        "Google 인증 정보가 만료되었거나 취소되었습니다. "
                        "다시 로그인해야 합니다."
                    ),
                },
            ) from exc

    return user, credentials


async def get_naver_user(
    user: User = Depends(get_current_user),
) -> User:
    """Validate user has Naver IMAP credentials connected."""
    if not user.naver_email or not user.naver_app_password:
        raise AccountNotConnectedException("Naver")
    return user
