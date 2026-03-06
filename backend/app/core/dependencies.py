"""Core dependency: get_current_user (JWT cookie-based)."""

from __future__ import annotations

from fastapi import Cookie, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import UserNotFoundException
from app.core.security import verify_access_token
from app.mail.models import User


async def get_current_user(
    session_token: str | None = Cookie(None),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Validate and return current user from JWT cookie."""
    if not session_token:
        raise UserNotFoundException()
    user_id = verify_access_token(session_token)
    if user_id is None:
        raise UserNotFoundException()
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise UserNotFoundException()
    return user
