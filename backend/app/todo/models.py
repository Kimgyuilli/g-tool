from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
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


class Project(Base):
    __tablename__ = "projects"
    __table_args__ = (Index("ix_project_user_position", "user_id", "position"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    color: Mapped[str | None] = mapped_column(String, nullable=True)
    position: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(tz=UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(tz=UTC),
        onupdate=lambda: datetime.now(tz=UTC),
    )

    tasks: Mapped[list[Task]] = relationship(
        "Task", back_populates="project", cascade="all, delete-orphan"
    )


class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = (Index("ix_task_project_position", "project_id", "position"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # todo / in_progress / done
    status: Mapped[str] = mapped_column(String, default="todo")
    # low / medium / high / urgent
    priority: Mapped[str] = mapped_column(String, default="medium")
    due_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    position: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(tz=UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(tz=UTC),
        onupdate=lambda: datetime.now(tz=UTC),
    )

    project: Mapped[Project] = relationship("Project", back_populates="tasks")
    subtasks: Mapped[list[Subtask]] = relationship(
        "Subtask", back_populates="task", cascade="all, delete-orphan"
    )


class Subtask(Base):
    __tablename__ = "subtasks"
    __table_args__ = (Index("ix_subtask_task_position", "task_id", "position"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    position: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(tz=UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(tz=UTC),
        onupdate=lambda: datetime.now(tz=UTC),
    )

    task: Mapped[Task] = relationship("Task", back_populates="subtasks")
