from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, field_validator

# Type aliases for valid values
TaskStatus = Literal["todo", "in_progress", "on_hold", "done"]
TaskPriority = Literal["low", "medium", "high", "urgent"]


class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    status: TaskStatus = "todo"
    priority: TaskPriority = "medium"
    due_date: datetime | None = None

    @field_validator("due_date", mode="before")
    @classmethod
    def parse_due_date(cls, v):
        if v is None or isinstance(v, datetime):
            return v
        if isinstance(v, str):
            return datetime.fromisoformat(v)
        raise ValueError("due_date must be ISO format string or datetime")


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    due_date: datetime | None = None

    @field_validator("due_date", mode="before")
    @classmethod
    def parse_due_date(cls, v):
        if v is None or isinstance(v, datetime):
            return v
        if isinstance(v, str):
            return datetime.fromisoformat(v)
        raise ValueError("due_date must be ISO format string or datetime")


class SubtaskCreate(BaseModel):
    task_id: int
    title: str


class SubtaskUpdate(BaseModel):
    title: str | None = None
    is_completed: bool | None = None


class ReorderItem(BaseModel):
    id: int
    position: float
    status: TaskStatus | None = None


class ReorderRequest(BaseModel):
    items: list[ReorderItem]


# Response models
class SubtaskResponse(BaseModel):
    id: int
    task_id: int
    title: str
    is_completed: bool
    position: float
    created_at: str | None
    updated_at: str | None


class TaskResponse(BaseModel):
    id: int
    user_id: int
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    due_date: str | None
    position: float
    subtask_count: int
    subtask_completed: int
    created_at: str | None
    updated_at: str | None
