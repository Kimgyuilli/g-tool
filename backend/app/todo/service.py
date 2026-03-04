from __future__ import annotations

from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.todo.models import Project, Subtask, Task
from app.todo.schemas import (
    ProjectCreate,
    ProjectUpdate,
    ReorderRequest,
    SubtaskCreate,
    SubtaskUpdate,
    TaskCreate,
    TaskUpdate,
)

# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------


async def get_projects(db: AsyncSession, user_id: int) -> list[dict]:
    """프로젝트 목록 조회 (task_count 포함)."""
    result = await db.execute(
        select(Project)
        .where(Project.user_id == user_id)
        .order_by(Project.position)
    )
    projects = result.scalars().all()

    # task count 조회
    count_result = await db.execute(
        select(Task.project_id, func.count(Task.id))
        .where(Task.project_id.in_([p.id for p in projects]))
        .group_by(Task.project_id)
    )
    task_counts = dict(count_result.all())

    return [
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "color": p.color,
            "position": p.position,
            "task_count": task_counts.get(p.id, 0),
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "updated_at": p.updated_at.isoformat() if p.updated_at else None,
        }
        for p in projects
    ]


async def create_project(
    db: AsyncSession, user_id: int, data: ProjectCreate
) -> dict:
    """프로젝트 생성."""
    # position: 현재 최대값 + 1
    max_pos = await db.execute(
        select(func.max(Project.position)).where(Project.user_id == user_id)
    )
    pos = (max_pos.scalar() or 0) + 1.0

    project = Project(
        user_id=user_id,
        name=data.name,
        description=data.description,
        color=data.color,
        position=pos,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "color": project.color,
        "position": project.position,
        "task_count": 0,
        "created_at": project.created_at.isoformat() if project.created_at else None,
        "updated_at": project.updated_at.isoformat() if project.updated_at else None,
    }


async def update_project(
    db: AsyncSession, user_id: int, project_id: int, data: ProjectUpdate
) -> dict:
    """프로젝트 수정."""
    project = await _get_project_or_404(db, user_id, project_id)
    if data.name is not None:
        project.name = data.name
    if data.description is not None:
        project.description = data.description
    if data.color is not None:
        project.color = data.color
    await db.commit()
    await db.refresh(project)

    count_result = await db.execute(
        select(func.count(Task.id)).where(Task.project_id == project.id)
    )
    task_count = count_result.scalar() or 0

    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "color": project.color,
        "position": project.position,
        "task_count": task_count,
        "created_at": project.created_at.isoformat() if project.created_at else None,
        "updated_at": project.updated_at.isoformat() if project.updated_at else None,
    }


async def delete_project(db: AsyncSession, user_id: int, project_id: int) -> None:
    """프로젝트 삭제 (cascade)."""
    project = await _get_project_or_404(db, user_id, project_id)
    await db.delete(project)
    await db.commit()


async def reorder_projects(
    db: AsyncSession, user_id: int, data: ReorderRequest
) -> None:
    """프로젝트 순서 변경."""
    for item in data.items:
        result = await db.execute(
            select(Project).where(
                Project.id == item["id"], Project.user_id == user_id
            )
        )
        project = result.scalar_one_or_none()
        if project:
            project.position = item["position"]
    await db.commit()


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------


async def get_tasks_by_project(
    db: AsyncSession, user_id: int, project_id: int
) -> list[dict]:
    """프로젝트의 태스크 목록 조회 (subtask count 포함)."""
    await _get_project_or_404(db, user_id, project_id)

    result = await db.execute(
        select(Task)
        .where(Task.project_id == project_id)
        .options(selectinload(Task.subtasks))
        .order_by(Task.position)
    )
    tasks = result.scalars().all()

    return [_task_to_dict(t) for t in tasks]


async def create_task(db: AsyncSession, user_id: int, data: TaskCreate) -> dict:
    """태스크 생성."""
    await _get_project_or_404(db, user_id, data.project_id)

    max_pos = await db.execute(
        select(func.max(Task.position)).where(Task.project_id == data.project_id)
    )
    pos = (max_pos.scalar() or 0) + 1.0

    due_date = None
    if data.due_date:
        due_date = datetime.fromisoformat(data.due_date)

    task = Task(
        project_id=data.project_id,
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
    return _task_to_dict(task)


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
    if data.project_id is not None:
        await _get_project_or_404(db, user_id, data.project_id)
        task.project_id = data.project_id

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
            select(Task)
            .where(Task.id == item["id"])
            .options(selectinload(Task.project))
        )
        task = result.scalar_one_or_none()
        if task and task.project.user_id == user_id:
            task.position = item["position"]
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


async def _get_project_or_404(
    db: AsyncSession, user_id: int, project_id: int
) -> Project:
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == user_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")
    return project


async def _get_task_or_404(db: AsyncSession, user_id: int, task_id: int) -> Task:
    result = await db.execute(
        select(Task)
        .where(Task.id == task_id)
        .options(selectinload(Task.project))
    )
    task = result.scalar_one_or_none()
    if not task or task.project.user_id != user_id:
        raise HTTPException(status_code=404, detail="태스크를 찾을 수 없습니다")
    return task


async def _get_subtask_or_404(
    db: AsyncSession, user_id: int, subtask_id: int
) -> Subtask:
    result = await db.execute(
        select(Subtask)
        .where(Subtask.id == subtask_id)
        .options(selectinload(Subtask.task).selectinload(Task.project))
    )
    subtask = result.scalar_one_or_none()
    if not subtask or subtask.task.project.user_id != user_id:
        raise HTTPException(status_code=404, detail="서브태스크를 찾을 수 없습니다")
    return subtask


def _task_to_dict(task: Task) -> dict:
    subtasks = getattr(task, "subtasks", None) or []
    completed = sum(1 for s in subtasks if s.is_completed)
    return {
        "id": task.id,
        "project_id": task.project_id,
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
