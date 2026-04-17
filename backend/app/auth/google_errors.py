"""Google OAuth refresh 에러 분류 및 HTTP 변환 공통 모듈.

router와 background worker가 동일한 정책으로 RefreshError를 처리할 수 있도록
책임을 세 개로 분리한다.

- ``classify_google_refresh_error``: 부수효과 없이 에러를 분류만 수행
- ``disconnect_google_account``: DB에 저장된 OAuth 토큰 제거
- ``build_google_refresh_http_exception``: 분류 결과를 HTTPException으로 변환
"""

from __future__ import annotations

from enum import Enum

from fastapi import HTTPException
from google.auth.exceptions import RefreshError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.service import is_google_scope_mismatch_error
from app.mail.models import User


class GoogleRefreshOutcome(Enum):
    """Google refresh 실패 시 분류 결과."""

    TOKEN_INVALID_OR_EXPIRED = "token_invalid_or_expired"
    SCOPE_MISMATCH = "scope_mismatch"


def classify_google_refresh_error(exc: RefreshError) -> GoogleRefreshOutcome:
    """RefreshError를 분류한다. 부수효과 없음."""
    if is_google_scope_mismatch_error(exc):
        return GoogleRefreshOutcome.SCOPE_MISMATCH
    return GoogleRefreshOutcome.TOKEN_INVALID_OR_EXPIRED


async def disconnect_google_account(user: User, db: AsyncSession) -> None:
    """저장된 Google OAuth 자격증명을 제거한다."""
    user.google_oauth_token = None
    user.google_refresh_token = None
    await db.commit()


def build_google_refresh_http_exception(
    outcome: GoogleRefreshOutcome,
) -> HTTPException:
    """분류 결과를 401 HTTPException으로 변환한다."""
    if outcome is GoogleRefreshOutcome.SCOPE_MISMATCH:
        return HTTPException(
            status_code=401,
            detail={
                "code": "google_reconnect_required",
                "message": (
                    "Google 권한 구성이 변경되어 계정 재연결이 필요합니다. "
                    "Google 로그인을 다시 진행해주세요."
                ),
            },
        )
    return HTTPException(
        status_code=401,
        detail={
            "code": "token_expired",
            "message": (
                "Google 인증 정보가 만료되었거나 취소되었습니다. "
                "다시 로그인해야 합니다."
            ),
        },
    )
