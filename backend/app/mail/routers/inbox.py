from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.mail.models import Classification, Label, Mail, User
from app.mail.services.helpers import get_mail_classifications

router = APIRouter(prefix="/api/inbox", tags=["inbox"])


@router.get("/messages")
async def list_all_messages(
    source: str | None = Query(default=None),
    category: str | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List synced messages from all sources (Gmail + Naver) with classification."""
    user_id = user.id

    # Build query with optional filters
    if category == "unclassified":
        query = (
            select(Mail)
            .outerjoin(Classification, Mail.id == Classification.mail_id)
            .where(Mail.user_id == user_id)
            .where(Classification.id.is_(None))
        )
        count_query = (
            select(func.count(Mail.id))
            .outerjoin(Classification, Mail.id == Classification.mail_id)
            .where(Mail.user_id == user_id)
            .where(Classification.id.is_(None))
        )

        if source:
            query = query.where(Mail.source == source)
            count_query = count_query.where(Mail.source == source)

    elif category:
        query = (
            select(Mail)
            .join(Classification, Mail.id == Classification.mail_id)
            .join(Label, Classification.label_id == Label.id)
            .where(Mail.user_id == user_id)
            .where(Label.name == category)
        )
        count_query = (
            select(func.count(Mail.id))
            .join(Classification, Mail.id == Classification.mail_id)
            .join(Label, Classification.label_id == Label.id)
            .where(Mail.user_id == user_id)
            .where(Label.name == category)
        )

        if source:
            query = query.where(Mail.source == source)
            count_query = count_query.where(Mail.source == source)

    else:
        where_clauses = [Mail.user_id == user_id]
        if source:
            where_clauses.append(Mail.source == source)

        query = select(Mail).where(*where_clauses)
        count_query = select(func.count(Mail.id)).where(*where_clauses)

    # Apply ordering and pagination
    query = query.order_by(Mail.received_at.desc()).offset(offset).limit(limit)

    result = await db.execute(query)
    mails = list(result.scalars().all())

    count_result = await db.execute(count_query)
    total = count_result.scalar()

    classifications = await get_mail_classifications(db, [m.id for m in mails])

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "messages": [
            {
                "id": m.id,
                "source": m.source,
                "external_id": m.external_id,
                "from_email": m.from_email,
                "from_name": m.from_name,
                "subject": m.subject,
                "to_email": m.to_email,
                "folder": m.folder,
                "received_at": (
                    m.received_at.isoformat() if m.received_at else None
                ),
                "is_read": m.is_read,
                "classification": classifications.get(m.id),
            }
            for m in mails
        ],
    }


@router.get("/category-counts")
async def get_category_counts(
    source: str | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get message counts by category."""
    user_id = user.id

    # Build base where clause
    where_clauses = [Mail.user_id == user_id]
    if source:
        where_clauses.append(Mail.source == source)

    # Total count
    total_result = await db.execute(
        select(func.count(Mail.id)).where(*where_clauses)
    )
    total = total_result.scalar() or 0

    # Unclassified count
    unclassified_query = (
        select(func.count(Mail.id))
        .outerjoin(Classification, Mail.id == Classification.mail_id)
        .where(*where_clauses)
        .where(Classification.id.is_(None))
    )
    unclassified_result = await db.execute(unclassified_query)
    unclassified = unclassified_result.scalar() or 0

    # Category counts (latest classification per mail)
    latest_classification_subquery = (
        select(
            Classification.mail_id,
            func.max(Classification.created_at).label("max_created_at"),
        )
        .group_by(Classification.mail_id)
        .subquery()
    )

    category_query = (
        select(Label.name, Label.color, func.count(Mail.id).label("count"))
        .select_from(Mail)
        .join(Classification, Mail.id == Classification.mail_id)
        .join(
            latest_classification_subquery,
            (Classification.mail_id == latest_classification_subquery.c.mail_id)
            & (
                Classification.created_at
                == latest_classification_subquery.c.max_created_at
            ),
        )
        .join(Label, Classification.label_id == Label.id)
        .where(Mail.user_id == user_id)
    )

    if source:
        category_query = category_query.where(Mail.source == source)

    category_query = category_query.group_by(Label.name, Label.color)

    category_result = await db.execute(category_query)
    category_rows = category_result.all()

    categories = [
        {"name": name, "count": count, "color": color}
        for name, color, count in category_rows
    ]

    return {
        "total": total,
        "unclassified": unclassified,
        "categories": categories,
    }
