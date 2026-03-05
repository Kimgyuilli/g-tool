from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class BookmarkCategory(Base):
    __tablename__ = "bookmark_categories"
    __table_args__ = (
        Index("ix_bookmark_category_user_position", "user_id", "position"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    color: Mapped[str] = mapped_column(String, default="gray")
    position: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(tz=UTC)
    )

    bookmarks: Mapped[list[Bookmark]] = relationship(
        "Bookmark", back_populates="category"
    )


class Bookmark(Base):
    __tablename__ = "bookmarks"
    __table_args__ = (
        Index(
            "ix_bookmark_user_category_position",
            "user_id",
            "category_id",
            "position",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    category_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("bookmark_categories.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    url: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    favicon_url: Mapped[str | None] = mapped_column(String, nullable=True)
    position: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(tz=UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(tz=UTC),
        onupdate=lambda: datetime.now(tz=UTC),
    )

    category: Mapped[BookmarkCategory | None] = relationship(
        "BookmarkCategory", back_populates="bookmarks"
    )
