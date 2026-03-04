from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.mail.models import User
from app.todo.schemas import (
    ProjectCreate,
    ProjectUpdate,
    ReorderRequest,
    SubtaskCreate,
    SubtaskUpdate,
    TaskCreate,
    TaskUpdate,
)
from app.todo.service import (
    create_project,
    create_subtask,
    create_task,
    delete_project,
    delete_subtask,
    delete_task,
    get_projects,
    get_subtasks,
    get_tasks_by_project,
    reorder_projects,
    reorder_tasks,
    toggle_subtask,
    update_project,
    update_subtask,
    update_task,
)

router = APIRouter(prefix="/api/todo", tags=["todo"])


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------


@router.get("/projects")
async def list_projects(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    projects = await get_projects(db, user.id)
    return {"projects": projects}


@router.post("/projects")
async def create_new_project(
    data: ProjectCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await create_project(db, user.id, data)


@router.patch("/projects/{project_id}")
async def patch_project(
    project_id: int,
    data: ProjectUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await update_project(db, user.id, project_id, data)


@router.delete("/projects/{project_id}")
async def remove_project(
    project_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await delete_project(db, user.id, project_id)
    return {"ok": True}


@router.post("/projects/reorder")
async def reorder_project_list(
    data: ReorderRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await reorder_projects(db, user.id, data)
    return {"ok": True}


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------


@router.get("/projects/{project_id}/tasks")
async def list_tasks(
    project_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tasks = await get_tasks_by_project(db, user.id, project_id)
    return {"tasks": tasks}


@router.post("/tasks")
async def create_new_task(
    data: TaskCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await create_task(db, user.id, data)


@router.patch("/tasks/{task_id}")
async def patch_task(
    task_id: int,
    data: TaskUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await update_task(db, user.id, task_id, data)


@router.delete("/tasks/{task_id}")
async def remove_task(
    task_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await delete_task(db, user.id, task_id)
    return {"ok": True}


@router.post("/tasks/reorder")
async def reorder_task_list(
    data: ReorderRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await reorder_tasks(db, user.id, data)
    return {"ok": True}


# ---------------------------------------------------------------------------
# Subtasks
# ---------------------------------------------------------------------------


@router.get("/tasks/{task_id}/subtasks")
async def list_subtasks(
    task_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    subtasks = await get_subtasks(db, user.id, task_id)
    return {"subtasks": subtasks}


@router.post("/subtasks")
async def create_new_subtask(
    data: SubtaskCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await create_subtask(db, user.id, data)


@router.patch("/subtasks/{subtask_id}")
async def patch_subtask(
    subtask_id: int,
    data: SubtaskUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await update_subtask(db, user.id, subtask_id, data)


@router.delete("/subtasks/{subtask_id}")
async def remove_subtask(
    subtask_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await delete_subtask(db, user.id, subtask_id)
    return {"ok": True}


@router.post("/subtasks/{subtask_id}/toggle")
async def toggle_subtask_completion(
    subtask_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await toggle_subtask(db, user.id, subtask_id)
