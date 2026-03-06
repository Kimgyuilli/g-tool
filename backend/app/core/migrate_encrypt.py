"""기존 평문 토큰을 암호화하는 1회성 마이그레이션 스크립트.

Usage:
    cd backend && uv run python -m app.core.migrate_encrypt
"""

from __future__ import annotations

import asyncio
import logging

from cryptography.fernet import InvalidToken
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.security import _get_fernet, encrypt_value
from app.mail.models import User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _is_already_encrypted(value: str) -> bool:
    """Check if the value is already Fernet-encrypted."""
    try:
        _get_fernet().decrypt(value.encode())
        return True
    except (InvalidToken, Exception):
        return False


async def migrate():
    """Encrypt all plaintext tokens in the users table."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User))
        users = list(result.scalars().all())

        migrated = 0
        for user in users:
            changed = False

            if user.google_oauth_token and not _is_already_encrypted(
                user.google_oauth_token
            ):
                user.google_oauth_token = encrypt_value(user.google_oauth_token)
                changed = True

            if user.google_refresh_token and not _is_already_encrypted(
                user.google_refresh_token
            ):
                user.google_refresh_token = encrypt_value(
                    user.google_refresh_token
                )
                changed = True

            if user.naver_app_password and not _is_already_encrypted(
                user.naver_app_password
            ):
                user.naver_app_password = encrypt_value(user.naver_app_password)
                changed = True

            if changed:
                migrated += 1
                logger.info(f"User {user.id} ({user.email}): 토큰 암호화 완료")

        await db.commit()
        logger.info(f"마이그레이션 완료: {migrated}/{len(users)} 사용자 처리")


if __name__ == "__main__":
    asyncio.run(migrate())
