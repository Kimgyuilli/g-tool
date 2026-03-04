from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

# ---------------------------------------------------------------------------
# Association table
# ---------------------------------------------------------------------------

mail_labels = Table(
    "mail_labels",
    Base.metadata,
    Column("mail_id", Integer, ForeignKey("mails.id"), primary_key=True),
    Column("label_id", Integer, ForeignKey("labels.id"), primary_key=True),
)


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    google_oauth_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    google_refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    naver_email: Mapped[str | None] = mapped_column(String, nullable=True)
    naver_app_password: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(tz=UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(tz=UTC),
        onupdate=lambda: datetime.now(tz=UTC),
    )

    mails: Mapped[list[Mail]] = relationship("Mail", back_populates="user")
    labels: Mapped[list[Label]] = relationship("Label", back_populates="user")


# ---------------------------------------------------------------------------
# Mail
# ---------------------------------------------------------------------------


class Mail(Base):
    __tablename__ = "mails"
    __table_args__ = (
        UniqueConstraint("user_id", "source", "external_id", name="uq_mail_source"),
        Index("ix_mail_user_source", "user_id", "source"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    source: Mapped[str] = mapped_column(String, nullable=False)
    external_id: Mapped[str] = mapped_column(String, nullable=False)
    from_email: Mapped[str | None] = mapped_column(String, nullable=True)
    from_name: Mapped[str | None] = mapped_column(String, nullable=True)
    subject: Mapped[str | None] = mapped_column(String, nullable=True)
    to_email: Mapped[str | None] = mapped_column(String, nullable=True)
    body_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    body_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    folder: Mapped[str | None] = mapped_column(String, nullable=True)
    received_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(tz=UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(tz=UTC),
        onupdate=lambda: datetime.now(tz=UTC),
    )

    user: Mapped[User] = relationship("User", back_populates="mails")
    labels: Mapped[list[Label]] = relationship(
        "Label", secondary=mail_labels, back_populates="mails"
    )
    classifications: Mapped[list[Classification]] = relationship(
        "Classification", back_populates="mail"
    )


# ---------------------------------------------------------------------------
# Label & Classification
# ---------------------------------------------------------------------------


class Label(Base):
    __tablename__ = "labels"
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_label_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    source: Mapped[str | None] = mapped_column(String, nullable=True)
    color: Mapped[str | None] = mapped_column(String, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(tz=UTC)
    )

    user: Mapped[User] = relationship("User", back_populates="labels")
    mails: Mapped[list[Mail]] = relationship(
        "Mail", secondary=mail_labels, back_populates="labels"
    )


class Classification(Base):
    __tablename__ = "classifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mail_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("mails.id"), nullable=False
    )
    label_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("labels.id"), nullable=False
    )
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    user_feedback: Mapped[str | None] = mapped_column(String, nullable=True)
    original_category: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(tz=UTC)
    )

    mail: Mapped[Mail] = relationship("Mail", back_populates="classifications")
    label: Mapped[Label] = relationship("Label")


# ---------------------------------------------------------------------------
# SyncState
# ---------------------------------------------------------------------------


class SyncState(Base):
    __tablename__ = "sync_states"
    __table_args__ = (
        UniqueConstraint("user_id", "source", name="uq_sync_state_source"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    source: Mapped[str] = mapped_column(String, nullable=False)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_uid: Mapped[str | None] = mapped_column(String, nullable=True)
    next_page_token: Mapped[str | None] = mapped_column(String, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(tz=UTC),
        onupdate=lambda: datetime.now(tz=UTC),
    )
