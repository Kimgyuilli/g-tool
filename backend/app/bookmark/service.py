from __future__ import annotations

from urllib.parse import urlparse

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.bookmark.models import Bookmark, BookmarkCategory
from app.bookmark.schemas import (
    BookmarkCreate,
    BookmarkResponse,
    BookmarkUpdate,
    CategoryCreate,
    CategoryResponse,
)

# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------


async def get_categories(
    db: AsyncSession, user_id: int
) -> list[CategoryResponse]:
    """사용자의 카테고리 목록 조회 (북마크 개수 포함)."""
    result = await db.execute(
        select(BookmarkCategory)
        .where(BookmarkCategory.user_id == user_id)
        .order_by(BookmarkCategory.position)
    )
    categories = result.scalars().all()

    # 카테고리별 북마크 개수 조회
    counts_result = await db.execute(
        select(
            Bookmark.category_id,
            func.count(Bookmark.id).label("count")
        )
        .where(Bookmark.user_id == user_id)
        .group_by(Bookmark.category_id)
    )
    counts_map = {cat_id: count for cat_id, count in counts_result.all()}

    return [
        _category_to_response(cat, counts_map.get(cat.id, 0))
        for cat in categories
    ]


async def create_category(
    db: AsyncSession, user_id: int, data: CategoryCreate
) -> CategoryResponse:
    """카테고리 생성."""
    # 마지막 position 조회
    result = await db.execute(
        select(BookmarkCategory.position)
        .where(BookmarkCategory.user_id == user_id)
        .order_by(BookmarkCategory.position.desc())
        .limit(1)
    )
    last_pos = result.scalar()
    pos = (last_pos or 0) + 1.0

    category = BookmarkCategory(
        user_id=user_id,
        name=data.name,
        color=data.color,
        position=pos,
    )
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return _category_to_response(category, 0)


async def delete_category(
    db: AsyncSession, user_id: int, category_id: int
) -> None:
    """카테고리 삭제 (북마크는 category_id가 NULL로 설정됨)."""
    category = await _get_category_or_404(db, user_id, category_id)
    await db.delete(category)
    await db.commit()


# ---------------------------------------------------------------------------
# Bookmarks
# ---------------------------------------------------------------------------


async def get_bookmarks(
    db: AsyncSession, user_id: int, category_id: int | None = None
) -> list[BookmarkResponse]:
    """북마크 목록 조회 (카테고리 필터링 옵션)."""
    stmt = (
        select(Bookmark)
        .where(Bookmark.user_id == user_id)
        .order_by(Bookmark.position)
    )

    if category_id is not None:
        stmt = stmt.where(Bookmark.category_id == category_id)

    result = await db.execute(stmt)
    bookmarks = result.scalars().all()
    return [_bookmark_to_response(bm) for bm in bookmarks]


async def create_bookmark(
    db: AsyncSession, user_id: int, data: BookmarkCreate
) -> BookmarkResponse:
    """북마크 생성."""
    # 카테고리 검증 (있는 경우)
    if data.category_id is not None:
        await _get_category_or_404(db, user_id, data.category_id)

    # 마지막 position 조회 (카테고리 내)
    stmt = (
        select(Bookmark.position)
        .where(Bookmark.user_id == user_id)
        .order_by(Bookmark.position.desc())
        .limit(1)
    )
    if data.category_id is not None:
        stmt = stmt.where(Bookmark.category_id == data.category_id)

    result = await db.execute(stmt)
    last_pos = result.scalar()
    pos = (last_pos or 0) + 1.0

    # favicon URL 자동 생성
    favicon_url = _generate_favicon_url(data.url)

    bookmark = Bookmark(
        user_id=user_id,
        category_id=data.category_id,
        title=data.title,
        url=data.url,
        description=data.description,
        favicon_url=favicon_url,
        position=pos,
    )
    db.add(bookmark)
    await db.commit()
    await db.refresh(bookmark)
    return _bookmark_to_response(bookmark)


async def update_bookmark(
    db: AsyncSession,
    user_id: int,
    bookmark_id: int,
    data: BookmarkUpdate,
) -> BookmarkResponse:
    """북마크 수정."""
    bookmark = await _get_bookmark_or_404(db, user_id, bookmark_id)

    # 카테고리 변경 시 검증
    if data.category_id is not None:
        await _get_category_or_404(db, user_id, data.category_id)

    if data.title is not None:
        bookmark.title = data.title
    if data.url is not None:
        bookmark.url = data.url
        # URL 변경 시 favicon도 업데이트
        bookmark.favicon_url = _generate_favicon_url(data.url)
    if data.description is not None:
        bookmark.description = data.description
    if data.category_id is not None:
        bookmark.category_id = data.category_id

    await db.commit()
    await db.refresh(bookmark)
    return _bookmark_to_response(bookmark)


async def delete_bookmark(
    db: AsyncSession, user_id: int, bookmark_id: int
) -> None:
    """북마크 삭제."""
    bookmark = await _get_bookmark_or_404(db, user_id, bookmark_id)
    await db.delete(bookmark)
    await db.commit()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _get_category_or_404(
    db: AsyncSession, user_id: int, category_id: int
) -> BookmarkCategory:
    result = await db.execute(
        select(BookmarkCategory).where(
            BookmarkCategory.id == category_id,
            BookmarkCategory.user_id == user_id
        )
    )
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(
            status_code=404, detail="카테고리를 찾을 수 없습니다"
        )
    return category


async def _get_bookmark_or_404(
    db: AsyncSession, user_id: int, bookmark_id: int
) -> Bookmark:
    result = await db.execute(
        select(Bookmark).where(
            Bookmark.id == bookmark_id,
            Bookmark.user_id == user_id
        )
    )
    bookmark = result.scalar_one_or_none()
    if not bookmark:
        raise HTTPException(
            status_code=404, detail="북마크를 찾을 수 없습니다"
        )
    return bookmark


def _generate_favicon_url(url: str) -> str:
    """URL에서 도메인을 추출하여 favicon URL 생성."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path.split("/")[0]
        return f"https://www.google.com/s2/favicons?domain={domain}&sz=32"
    except Exception:
        return "https://www.google.com/s2/favicons?domain=example.com&sz=32"


def _category_to_response(
    category: BookmarkCategory, bookmark_count: int
) -> CategoryResponse:
    return CategoryResponse(
        id=category.id,
        name=category.name,
        color=category.color,
        position=category.position,
        bookmark_count=bookmark_count,
        created_at=(
            category.created_at.isoformat()
            if category.created_at
            else None
        ),
    )


def _bookmark_to_response(bookmark: Bookmark) -> BookmarkResponse:
    return BookmarkResponse(
        id=bookmark.id,
        user_id=bookmark.user_id,
        category_id=bookmark.category_id,
        title=bookmark.title,
        url=bookmark.url,
        description=bookmark.description,
        favicon_url=bookmark.favicon_url,
        position=bookmark.position,
        created_at=(
            bookmark.created_at.isoformat()
            if bookmark.created_at
            else None
        ),
        updated_at=(
            bookmark.updated_at.isoformat()
            if bookmark.updated_at
            else None
        ),
    )
