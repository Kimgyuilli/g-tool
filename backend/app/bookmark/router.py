from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.bookmark.schemas import (
    BookmarkCreate,
    BookmarkUpdate,
    CategoryCreate,
)
from app.bookmark.service import (
    create_bookmark,
    create_category,
    delete_bookmark,
    delete_category,
    get_bookmarks,
    get_categories,
    update_bookmark,
)
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.mail.models import User

router = APIRouter(prefix="/api/bookmark", tags=["bookmark"])


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------


@router.get("/categories")
async def list_categories(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    categories = await get_categories(db, user.id)
    return {"categories": categories}


@router.post("/categories")
async def create_new_category(
    data: CategoryCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await create_category(db, user.id, data)


@router.delete("/categories/{category_id}")
async def remove_category(
    category_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await delete_category(db, user.id, category_id)
    return {"ok": True}


# ---------------------------------------------------------------------------
# Bookmarks
# ---------------------------------------------------------------------------


@router.get("/bookmarks")
async def list_bookmarks(
    category_id: int | None = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    bookmarks = await get_bookmarks(db, user.id, category_id)
    return {"bookmarks": bookmarks}


@router.post("/bookmarks")
async def create_new_bookmark(
    data: BookmarkCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await create_bookmark(db, user.id, data)


@router.patch("/bookmarks/{bookmark_id}")
async def patch_bookmark(
    bookmark_id: int,
    data: BookmarkUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await update_bookmark(db, user.id, bookmark_id, data)


@router.delete("/bookmarks/{bookmark_id}")
async def remove_bookmark(
    bookmark_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await delete_bookmark(db, user.id, bookmark_id)
    return {"ok": True}
