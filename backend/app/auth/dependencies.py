"""Auth dependencies: get_google_user, get_naver_user."""

from __future__ import annotations

import asyncio
import logging

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.service import build_credentials
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.exceptions import AccountNotConnectedException
from app.core.security import decrypt_value, encrypt_value
from app.mail.models import User

logger = logging.getLogger(__name__)


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
        except google.auth.exceptions.RefreshError as exc:
            logger.warning(f"Google 토큰 갱신 실패 (user={user.id}): {exc}")
            raise HTTPException(
                status_code=401,
                detail={
                    "code": "token_expired",
                    "message": "Google 인증 정보가 만료되었거나 취소되었습니다. 다시 로그인해야 합니다.",
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
