from __future__ import annotations

from pydantic import BaseModel


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None
    color: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    color: str | None = None


class TaskCreate(BaseModel):
    project_id: int
    title: str
    description: str | None = None
    status: str = "todo"
    priority: str = "medium"
    due_date: str | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    priority: str | None = None
    due_date: str | None = None
    project_id: int | None = None  # 프로젝트 이동용


class SubtaskCreate(BaseModel):
    task_id: int
    title: str


class SubtaskUpdate(BaseModel):
    title: str | None = None
    is_completed: bool | None = None


class ReorderRequest(BaseModel):
    items: list[dict]  # [{"id": 1, "position": 0.0}, ...]
