from __future__ import annotations

from pydantic import BaseModel, field_validator


# Category schemas
class CategoryCreate(BaseModel):
    name: str
    color: str = "gray"


class CategoryResponse(BaseModel):
    id: int
    name: str
    color: str
    position: float
    bookmark_count: int
    created_at: str | None


# Bookmark schemas
class BookmarkCreate(BaseModel):
    title: str
    url: str
    description: str | None = None
    category_id: int | None = None

    @field_validator("url", mode="before")
    @classmethod
    def normalize_url(cls, v):
        if isinstance(v, str) and not v.startswith(("http://", "https://")):
            v = "https://" + v
        return v


class BookmarkUpdate(BaseModel):
    title: str | None = None
    url: str | None = None
    description: str | None = None
    category_id: int | None = None

    @field_validator("url", mode="before")
    @classmethod
    def normalize_url(cls, v):
        if v is None:
            return v
        if isinstance(v, str) and not v.startswith(("http://", "https://")):
            v = "https://" + v
        return v


class BookmarkResponse(BaseModel):
    id: int
    user_id: int
    category_id: int | None
    title: str
    url: str
    description: str | None
    favicon_url: str | None
    position: float
    created_at: str | None
    updated_at: str | None
