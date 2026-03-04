"""Common database query helpers shared across routers."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import MessageNotFoundException
from app.mail.models import Classification, Label, Mail


async def get_mail_classifications(
    db: AsyncSession,
    mail_ids: list[int],
) -> dict[int, dict]:
    """Get latest classification for each mail. Returns {mail_id: {...}}."""
    if not mail_ids:
        return {}

    result = await db.execute(
        select(Classification, Label)
        .join(Label, Classification.label_id == Label.id)
        .where(Classification.mail_id.in_(mail_ids))
        .order_by(Classification.created_at.desc())
    )
    rows = result.all()

    classifications: dict[int, dict] = {}
    for cls, label in rows:
        if cls.mail_id not in classifications:
            classifications[cls.mail_id] = {
                "classification_id": cls.id,
                "category": label.name,
                "confidence": cls.confidence,
                "user_feedback": cls.user_feedback,
            }
    return classifications


async def filter_new_external_ids(
    db: AsyncSession,
    user_id: int,
    source: str,
    external_ids: list[str],
) -> list[str]:
    """Filter out already-synced message IDs. Returns only new IDs."""
    if not external_ids:
        return []

    existing = await db.execute(
        select(Mail.external_id).where(
            Mail.user_id == user_id,
            Mail.source == source,
            Mail.external_id.in_(external_ids),
        )
    )
    existing_ids = set(existing.scalars().all())
    return [eid for eid in external_ids if eid not in existing_ids]


async def list_user_mails(
    db: AsyncSession,
    user_id: int,
    source: str | None,
    offset: int,
    limit: int,
) -> tuple[list[Mail], int]:
    """List user mails with pagination. Returns (mails, total).

    If source is None, returns all mails. Otherwise filters by source.
    """
    query_base = select(Mail).where(Mail.user_id == user_id)
    if source:
        query_base = query_base.where(Mail.source == source)

    query = (
        query_base
        .order_by(Mail.received_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(query)
    mails = list(result.scalars().all())

    count_query = select(func.count(Mail.id)).where(Mail.user_id == user_id)
    if source:
        count_query = count_query.where(Mail.source == source)
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    return mails, total


async def get_user_mail(
    db: AsyncSession,
    user_id: int,
    mail_id: int,
    source: str | None,
) -> Mail:
    """Get a single user mail by ID.

    Raises MessageNotFoundException if not found.
    If source is provided, also validates the source.
    """
    query = select(Mail).where(
        Mail.id == mail_id,
        Mail.user_id == user_id,
    )
    if source:
        query = query.where(Mail.source == source)

    result = await db.execute(query)
    mail = result.scalar_one_or_none()
    if mail is None:
        raise MessageNotFoundException()
    return mail


def format_mail_response(
    mail: Mail,
    classification: dict | None,
    *,
    include_naver_fields: bool = True,
) -> dict:
    """Format mail object into API response dict.

    Set include_naver_fields=False for Gmail-only endpoints
    to exclude to_email and folder fields.
    """
    result: dict = {
        "id": mail.id,
        "external_id": mail.external_id,
        "from_email": mail.from_email,
        "from_name": mail.from_name,
        "subject": mail.subject,
        "body_text": mail.body_text,
        "body_html": mail.body_html,
        "received_at": (
            mail.received_at.isoformat() if mail.received_at else None
        ),
        "is_read": mail.is_read,
        "classification": classification,
    }
    if include_naver_fields:
        result["to_email"] = mail.to_email
        result["folder"] = mail.folder
    return result
