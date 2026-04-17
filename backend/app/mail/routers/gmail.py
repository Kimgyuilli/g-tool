from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Query
from google.auth.exceptions import RefreshError
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_google_user
from app.auth.google_errors import (
    GoogleRefreshOutcome,
    build_google_refresh_http_exception,
    classify_google_refresh_error,
    disconnect_google_account,
)
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.mail.models import User
from app.mail.services.gmail import (
    apply_classification_labels_to_gmail,
    sync_all_gmail_messages,
    sync_gmail_messages,
)
from app.mail.services.helpers import (
    format_mail_response,
    get_mail_classifications,
    get_user_mail,
    list_user_mails,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/gmail", tags=["gmail"])


async def _raise_refresh_error(
    exc: RefreshError, user: User, db: AsyncSession
) -> None:
    """RefreshError를 401 HTTPException으로 변환 후 raise."""
    logger.warning(f"Gmail refresh 실패 (user={user.id}): {exc}")
    outcome = classify_google_refresh_error(exc)
    if outcome is GoogleRefreshOutcome.SCOPE_MISMATCH:
        await disconnect_google_account(user, db)
    raise build_google_refresh_http_exception(outcome) from exc


@router.post("/sync")
async def sync_messages(
    max_results: int = Query(default=20, le=100),
    query: str | None = Query(default=None),
    user_credentials: tuple[User, object] = Depends(get_google_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetch messages from Gmail and save new ones to DB."""
    user, credentials = user_credentials
    try:
        return await sync_gmail_messages(db, user, credentials, max_results, query)
    except RefreshError as exc:
        await _raise_refresh_error(exc, user, db)


@router.get("/messages")
async def list_messages(
    user: User = Depends(get_current_user),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List synced Gmail messages from DB with classification."""
    mails, total = await list_user_mails(db, user.id, "gmail", offset, limit)
    classifications = await get_mail_classifications(db, [m.id for m in mails])

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "messages": [
            {
                "id": m.id,
                "external_id": m.external_id,
                "from_email": m.from_email,
                "from_name": m.from_name,
                "subject": m.subject,
                "received_at": (
                    m.received_at.isoformat()
                    if m.received_at
                    else None
                ),
                "is_read": m.is_read,
                "classification": classifications.get(m.id),
            }
            for m in mails
        ],
    }


@router.get("/messages/{mail_id}")
async def get_message(
    mail_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single synced message with body."""
    mail = await get_user_mail(db, user.id, mail_id, "gmail")
    classifications = await get_mail_classifications(db, [mail.id])
    return format_mail_response(
        mail, classifications.get(mail.id), include_naver_fields=False
    )


@router.post("/sync/full")
async def sync_all_messages(
    max_pages: int = Query(default=5, le=20),
    per_page: int = Query(default=50, le=100),
    query: str | None = Query(default=None),
    user_credentials: tuple[User, object] = Depends(get_google_user),
    db: AsyncSession = Depends(get_db),
):
    """Sync multiple pages of messages from Gmail."""
    user, credentials = user_credentials
    try:
        return await sync_all_gmail_messages(
            db, user, credentials, max_pages, per_page, query
        )
    except RefreshError as exc:
        await _raise_refresh_error(exc, user, db)


class ApplyLabelsRequest(BaseModel):
    mail_ids: list[int]


@router.post("/apply-labels")
async def apply_classification_labels(
    req: ApplyLabelsRequest,
    user_credentials: tuple[User, object] = Depends(get_google_user),
    db: AsyncSession = Depends(get_db),
):
    """Apply AI classification results as Gmail labels."""
    user, credentials = user_credentials
    try:
        return await apply_classification_labels_to_gmail(
            db, user, credentials, req.mail_ids
        )
    except RefreshError as exc:
        await _raise_refresh_error(exc, user, db)
