from __future__ import annotations

import imaplib

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_naver_user
from app.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.exceptions import ExternalServiceException, IMAPAuthenticationException
from app.mail.models import User
from app.mail.services.helpers import (
    format_mail_response,
    get_mail_classifications,
    get_user_mail,
    list_user_mails,
)
from app.mail.services.naver import (
    list_folders,
    sync_naver_messages,
    verify_credentials,
)

router = APIRouter(prefix="/api/naver", tags=["naver"])


class NaverConnectRequest(BaseModel):
    naver_email: str
    naver_app_password: str


@router.post("/connect")
async def connect_naver(
    req: NaverConnectRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Connect Naver account by verifying IMAP credentials."""
    # Verify IMAP credentials
    try:
        ok = await verify_credentials(
            settings.naver_imap_host,
            settings.naver_imap_port,
            req.naver_email,
            req.naver_app_password,
        )
    except imaplib.IMAP4.error as exc:
        raise IMAPAuthenticationException(detail=f"IMAP 인증 실패: {exc}")
    except (TimeoutError, OSError) as exc:
        raise ExternalServiceException(detail=f"IMAP 서버 연결 실패: {exc}")

    if not ok:
        raise IMAPAuthenticationException()

    # Save credentials
    user.naver_email = req.naver_email
    user.naver_app_password = req.naver_app_password
    await db.commit()

    return {"status": "connected", "naver_email": req.naver_email}


@router.get("/folders")
async def get_folders(
    user: User = Depends(get_naver_user),
):
    """List available IMAP folders."""
    folders = await list_folders(
        settings.naver_imap_host,
        settings.naver_imap_port,
        user.naver_email,
        user.naver_app_password,
    )

    return {"folders": folders}


@router.post("/sync")
async def sync_messages(
    folder: str = Query(default="INBOX"),
    max_results: int = Query(default=50, le=200),
    user: User = Depends(get_naver_user),
    db: AsyncSession = Depends(get_db),
):
    """Sync messages from Naver IMAP folder."""
    return await sync_naver_messages(
        db,
        user,
        settings.naver_imap_host,
        settings.naver_imap_port,
        folder,
        max_results,
    )


@router.get("/messages")
async def list_messages(
    user: User = Depends(get_current_user),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List synced Naver messages from DB with classification."""
    mails, total = await list_user_mails(db, user.id, "naver", offset, limit)
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


@router.get("/messages/{mail_id}")
async def get_message(
    mail_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single synced Naver message with body."""
    mail = await get_user_mail(db, user.id, mail_id, "naver")
    classifications = await get_mail_classifications(db, [mail.id])
    return format_mail_response(mail, classifications.get(mail.id))
