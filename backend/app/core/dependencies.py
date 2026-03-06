from __future__ import annotations

from fastapi import Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import UserNotFoundException
from app.mail.models import User


async def get_current_user(
    user_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Validate and return current user by user_id query parameter."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise UserNotFoundException()
    return user
