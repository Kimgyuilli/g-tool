from __future__ import annotations

from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.todo.models import Subtask, Task
from app.todo.schemas import (
    ReorderRequest,
    SubtaskCreate,
    SubtaskUpdate,
    TaskCreate,
    TaskUpdate,
)

# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------


async def get_tasks(db: AsyncSession, user_id: int) -> list[dict]:
    """사용자의 전체 태스크 목록 조회 (subtask count 포함)."""
    result = await db.execute(
        select(Task)
        .where(Task.user_id == user_id)
        .options(selectinload(Task.subtasks))
        .order_by(Task.position)
    )
    tasks = result.scalars().all()
    return [_task_to_dict(t) for t in tasks]


async def create_task(db: AsyncSession, user_id: int, data: TaskCreate) -> dict:
    """태스크 생성."""
    max_pos = await db.execute(
        select(func.max(Task.position)).where(Task.user_id == user_id)
    )
    pos = (max_pos.scalar() or 0) + 1.0

    due_date = None
    if data.due_date:
        due_date = datetime.fromisoformat(data.due_date)

    task = Task(
        user_id=user_id,
        title=data.title,
        description=data.description,
        status=data.status,
        priority=data.priority,
        due_date=due_date,
        position=pos,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return _task_to_dict(task, subtasks_loaded=[])


async def update_task(
    db: AsyncSession, user_id: int, task_id: int, data: TaskUpdate
) -> dict:
    """태스크 수정."""
    task = await _get_task_or_404(db, user_id, task_id)

    if data.title is not None:
        task.title = data.title
    if data.description is not None:
        task.description = data.description
    if data.status is not None:
        task.status = data.status
    if data.priority is not None:
        task.priority = data.priority
    if data.due_date is not None:
        task.due_date = datetime.fromisoformat(data.due_date) if data.due_date else None

    await db.commit()

    # subtasks 로드
    result = await db.execute(
        select(Task)
        .where(Task.id == task_id)
        .options(selectinload(Task.subtasks))
    )
    task = result.scalar_one()
    return _task_to_dict(task)


async def delete_task(db: AsyncSession, user_id: int, task_id: int) -> None:
    """태스크 삭제 (cascade)."""
    task = await _get_task_or_404(db, user_id, task_id)
    await db.delete(task)
    await db.commit()


async def reorder_tasks(db: AsyncSession, user_id: int, data: ReorderRequest) -> None:
    """태스크 순서 변경."""
    for item in data.items:
        result = await db.execute(
            select(Task).where(Task.id == item["id"], Task.user_id == user_id)
        )
        task = result.scalar_one_or_none()
        if task:
            task.position = item["position"]
            if "status" in item:
                task.status = item["status"]
    await db.commit()


# ---------------------------------------------------------------------------
# Subtasks
# ---------------------------------------------------------------------------


async def get_subtasks(
    db: AsyncSession, user_id: int, task_id: int
) -> list[dict]:
    """서브태스크 목록 조회."""
    await _get_task_or_404(db, user_id, task_id)

    result = await db.execute(
        select(Subtask)
        .where(Subtask.task_id == task_id)
        .order_by(Subtask.position)
    )
    return [_subtask_to_dict(s) for s in result.scalars().all()]


async def create_subtask(
    db: AsyncSession, user_id: int, data: SubtaskCreate
) -> dict:
    """서브태스크 생성."""
    await _get_task_or_404(db, user_id, data.task_id)

    max_pos = await db.execute(
        select(func.max(Subtask.position)).where(Subtask.task_id == data.task_id)
    )
    pos = (max_pos.scalar() or 0) + 1.0

    subtask = Subtask(
        task_id=data.task_id,
        title=data.title,
        position=pos,
    )
    db.add(subtask)
    await db.commit()
    await db.refresh(subtask)
    return _subtask_to_dict(subtask)


async def update_subtask(
    db: AsyncSession, user_id: int, subtask_id: int, data: SubtaskUpdate
) -> dict:
    """서브태스크 수정."""
    subtask = await _get_subtask_or_404(db, user_id, subtask_id)
    if data.title is not None:
        subtask.title = data.title
    if data.is_completed is not None:
        subtask.is_completed = data.is_completed
    await db.commit()
    await db.refresh(subtask)
    return _subtask_to_dict(subtask)


async def delete_subtask(db: AsyncSession, user_id: int, subtask_id: int) -> None:
    """서브태스크 삭제."""
    subtask = await _get_subtask_or_404(db, user_id, subtask_id)
    await db.delete(subtask)
    await db.commit()


async def toggle_subtask(db: AsyncSession, user_id: int, subtask_id: int) -> dict:
    """서브태스크 완료 토글."""
    subtask = await _get_subtask_or_404(db, user_id, subtask_id)
    subtask.is_completed = not subtask.is_completed
    await db.commit()
    await db.refresh(subtask)
    return _subtask_to_dict(subtask)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _get_task_or_404(db: AsyncSession, user_id: int, task_id: int) -> Task:
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.user_id == user_id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="태스크를 찾을 수 없습니다")
    return task


async def _get_subtask_or_404(
    db: AsyncSession, user_id: int, subtask_id: int
) -> Subtask:
    result = await db.execute(
        select(Subtask)
        .where(Subtask.id == subtask_id)
        .options(selectinload(Subtask.task))
    )
    subtask = result.scalar_one_or_none()
    if not subtask or subtask.task.user_id != user_id:
        raise HTTPException(status_code=404, detail="서브태스크를 찾을 수 없습니다")
    return subtask


def _task_to_dict(task: Task, subtasks_loaded: list | None = None) -> dict:
    subtasks = subtasks_loaded if subtasks_loaded is not None else task.subtasks
    completed = sum(1 for s in subtasks if s.is_completed)
    return {
        "id": task.id,
        "user_id": task.user_id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "priority": task.priority,
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "position": task.position,
        "subtask_count": len(subtasks),
        "subtask_completed": completed,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "updated_at": task.updated_at.isoformat() if task.updated_at else None,
    }


def _subtask_to_dict(subtask: Subtask) -> dict:
    return {
        "id": subtask.id,
        "task_id": subtask.task_id,
        "title": subtask.title,
        "is_completed": subtask.is_completed,
        "position": subtask.position,
        "created_at": subtask.created_at.isoformat() if subtask.created_at else None,
        "updated_at": subtask.updated_at.isoformat() if subtask.updated_at else None,
    }
