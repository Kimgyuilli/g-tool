from __future__ import annotations

import base64
import email.utils
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.mail.models import User


def _build_gmail(credentials: Credentials):
    """Build Gmail API service client."""
    return build("gmail", "v1", credentials=credentials)


async def list_message_ids(
    credentials: Credentials,
    max_results: int = 20,
    page_token: str | None = None,
    query: str | None = None,
) -> dict[str, Any]:
    """List message IDs from Gmail.

    Returns dict with 'message_ids' (list[str]) and
    'next_page_token' (str | None).
    """
    import asyncio

    service = _build_gmail(credentials)

    def _fetch():
        kwargs: dict[str, Any] = {
            "userId": "me",
            "maxResults": max_results,
        }
        if page_token:
            kwargs["pageToken"] = page_token
        if query:
            kwargs["q"] = query
        return service.users().messages().list(**kwargs).execute()

    result = await asyncio.to_thread(_fetch)
    messages = result.get("messages", [])
    return {
        "message_ids": [m["id"] for m in messages],
        "next_page_token": result.get("nextPageToken"),
    }


async def get_message_detail(
    credentials: Credentials,
    message_id: str,
) -> dict[str, Any]:
    """Fetch a single message's full detail and parse it."""
    import asyncio

    service = _build_gmail(credentials)

    def _fetch():
        return (
            service.users()
            .messages()
            .get(userId="me", id=message_id, format="full")
            .execute()
        )

    raw = await asyncio.to_thread(_fetch)
    return _parse_message(raw)


async def get_messages_batch(
    credentials: Credentials,
    message_ids: list[str],
) -> list[dict[str, Any]]:
    """Fetch multiple messages in sequence."""
    results = []
    for mid in message_ids:
        detail = await get_message_detail(credentials, mid)
        results.append(detail)
    return results


async def list_labels(
    credentials: Credentials,
) -> list[dict[str, str]]:
    """List all Gmail labels for the user."""
    import asyncio

    service = _build_gmail(credentials)

    def _fetch():
        return service.users().labels().list(userId="me").execute()

    result = await asyncio.to_thread(_fetch)
    return [
        {"id": lb["id"], "name": lb["name"]}
        for lb in result.get("labels", [])
    ]


async def create_label(
    credentials: Credentials,
    name: str,
) -> dict[str, str]:
    """Create a new Gmail label. Returns {id, name}."""
    import asyncio

    service = _build_gmail(credentials)

    def _create():
        body = {
            "name": name,
            "labelListVisibility": "labelShow",
            "messageListVisibility": "show",
        }
        return service.users().labels().create(
            userId="me", body=body
        ).execute()

    result = await asyncio.to_thread(_create)
    return {"id": result["id"], "name": result["name"]}


async def apply_labels(
    credentials: Credentials,
    message_id: str,
    add_label_ids: list[str],
) -> None:
    """Apply Gmail labels to a single message."""
    import asyncio

    service = _build_gmail(credentials)

    def _modify():
        service.users().messages().modify(
            userId="me",
            id=message_id,
            body={"addLabelIds": add_label_ids},
        ).execute()

    await asyncio.to_thread(_modify)


async def batch_apply_labels(
    credentials: Credentials,
    message_ids: list[str],
    add_label_ids: list[str],
) -> None:
    """Apply Gmail labels to multiple messages at once."""
    import asyncio

    service = _build_gmail(credentials)

    def _batch():
        service.users().messages().batchModify(
            userId="me",
            body={
                "ids": message_ids,
                "addLabelIds": add_label_ids,
            },
        ).execute()

    await asyncio.to_thread(_batch)


async def get_or_create_gmail_label(
    credentials: Credentials,
    label_name: str,
) -> str:
    """Find a Gmail label by name or create it. Returns label ID."""
    labels = await list_labels(credentials)
    for lb in labels:
        if lb["name"] == label_name:
            return lb["id"]
    new_label = await create_label(credentials, label_name)
    return new_label["id"]


def _parse_message(raw: dict) -> dict[str, Any]:
    """Parse Gmail API message response into a flat dict."""
    headers = {
        h["name"].lower(): h["value"]
        for h in raw.get("payload", {}).get("headers", [])
    }

    from_header = headers.get("from", "")
    from_name, from_email = _parse_from(from_header)

    subject = headers.get("subject", "")

    body = _extract_body(raw.get("payload", {}))

    internal_date_ms = int(raw.get("internalDate", "0"))
    received_at = datetime.fromtimestamp(
        internal_date_ms / 1000, tz=UTC
    )

    label_ids = raw.get("labelIds", [])
    is_read = "UNREAD" not in label_ids

    return {
        "external_id": raw["id"],
        "from_email": from_email,
        "from_name": from_name,
        "subject": subject,
        "body_text": body["text"],
        "body_html": body["html"],
        "received_at": received_at,
        "is_read": is_read,
    }


def _parse_from(from_header: str) -> tuple[str, str]:
    """Parse 'Name <email>' format."""
    name, addr = email.utils.parseaddr(from_header)
    return name, addr


def _extract_body(payload: dict) -> dict[str, str | None]:
    """Extract text and HTML body from Gmail payload."""
    mime_type = payload.get("mimeType", "")

    if mime_type == "text/plain":
        data = payload.get("body", {}).get("data", "")
        return {"text": _decode_base64url(data), "html": None}

    if mime_type == "text/html":
        data = payload.get("body", {}).get("data", "")
        html = _decode_base64url(data)
        return {"text": _strip_html(html), "html": html}

    parts = payload.get("parts", [])

    text_plain: str | None = None
    text_html: str | None = None

    for part in parts:
        part_mime = part.get("mimeType", "")
        if part_mime == "text/plain" and text_plain is None:
            data = part.get("body", {}).get("data", "")
            text_plain = _decode_base64url(data)
        elif part_mime == "text/html" and text_html is None:
            data = part.get("body", {}).get("data", "")
            text_html = _decode_base64url(data)

    if text_plain is not None or text_html is not None:
        plain = text_plain or (
            _strip_html(text_html) if text_html else ""
        )
        return {"text": plain, "html": text_html}

    # Recurse into nested multipart
    for part in parts:
        if part.get("mimeType", "").startswith("multipart/"):
            result = _extract_body(part)
            if result["text"] or result["html"]:
                return result

    return {"text": "", "html": None}


def _decode_base64url(data: str) -> str:
    """Decode base64url-encoded string."""
    if not data:
        return ""
    padded = data + "=" * (4 - len(data) % 4)
    return base64.urlsafe_b64decode(padded).decode("utf-8", errors="replace")


def _strip_html(html: str) -> str:
    """Minimal HTML tag stripping for plain text extraction."""
    import re

    text = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL)
    text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ---------------------------------------------------------------------------
# High-level sync operations for routers
# ---------------------------------------------------------------------------


async def sync_gmail_messages(
    db: AsyncSession,
    user: User,
    credentials: Credentials,
    max_results: int,
    query: str | None,
) -> dict[str, Any]:
    """Sync Gmail messages (single page) and save new ones to DB."""
    from app.mail.models import Mail
    from app.mail.services.helpers import filter_new_external_ids

    # List message IDs from Gmail
    result = await list_message_ids(
        credentials,
        max_results=max_results,
        query=query,
    )
    gmail_ids = result["message_ids"]

    if not gmail_ids:
        return {
            "synced": 0,
            "total_fetched": 0,
            "next_page_token": None,
        }

    # Filter out already-synced messages
    new_ids = await filter_new_external_ids(db, user.id, "gmail", gmail_ids)

    if not new_ids:
        return {
            "synced": 0,
            "total_fetched": len(gmail_ids),
            "next_page_token": result["next_page_token"],
        }

    # Fetch full details for new messages
    details = await get_messages_batch(credentials, new_ids)

    # Save to DB
    for detail in details:
        mail = Mail(
            user_id=user.id,
            source="gmail",
            external_id=detail["external_id"],
            from_email=detail["from_email"],
            from_name=detail["from_name"],
            subject=detail["subject"],
            body_text=detail["body_text"],
            body_html=detail["body_html"],
            received_at=detail["received_at"],
            is_read=detail["is_read"],
        )
        db.add(mail)

    await db.commit()

    return {
        "synced": len(details),
        "total_fetched": len(gmail_ids),
        "next_page_token": result["next_page_token"],
    }


async def sync_all_gmail_messages(
    db: AsyncSession,
    user: User,
    credentials: Credentials,
    max_pages: int,
    per_page: int,
    query: str | None,
) -> dict[str, int]:
    """Sync multiple pages of Gmail messages."""
    from app.mail.models import Mail
    from app.mail.services.helpers import filter_new_external_ids

    total_synced = 0
    page_token = None

    for _ in range(max_pages):
        result = await list_message_ids(
            credentials,
            max_results=per_page,
            page_token=page_token,
            query=query,
        )
        gmail_ids = result["message_ids"]

        if not gmail_ids:
            break

        # Filter already-synced
        new_ids = await filter_new_external_ids(db, user.id, "gmail", gmail_ids)

        if new_ids:
            details = await get_messages_batch(credentials, new_ids)
            for detail in details:
                mail = Mail(
                    user_id=user.id,
                    source="gmail",
                    external_id=detail["external_id"],
                    from_email=detail["from_email"],
                    from_name=detail["from_name"],
                    subject=detail["subject"],
                    body_text=detail["body_text"],
                    body_html=detail["body_html"],
                    received_at=detail["received_at"],
                    is_read=detail["is_read"],
                )
                db.add(mail)
            await db.commit()
            total_synced += len(details)

        page_token = result["next_page_token"]
        if not page_token:
            break

    return {"total_synced": total_synced}


async def apply_classification_labels_to_gmail(
    db: AsyncSession,
    user: User,
    credentials: Credentials,
    mail_ids: list[int],
) -> dict[str, Any]:
    """Apply AI classification results as Gmail labels."""
    from sqlalchemy import select

    from app.core.exceptions import MessageNotFoundException
    from app.mail.models import Classification, Label, Mail

    # Load mails with their classifications
    result = await db.execute(
        select(Mail).where(
            Mail.id.in_(mail_ids),
            Mail.user_id == user.id,
            Mail.source == "gmail",
        )
    )
    mails = list(result.scalars().all())

    if not mails:
        raise MessageNotFoundException()

    applied = []
    for mail in mails:
        # Get classification for this mail
        cls_result = await db.execute(
            select(Classification)
            .where(Classification.mail_id == mail.id)
            .order_by(Classification.created_at.desc())
        )
        classification = cls_result.scalar_one_or_none()
        if classification is None:
            continue

        # Get label name
        label_result = await db.execute(
            select(Label).where(Label.id == classification.label_id)
        )
        label = label_result.scalar_one_or_none()
        if label is None:
            continue

        # Prefix with "AI/" to avoid conflicts with user labels
        gmail_label_name = f"AI/{label.name}"
        gmail_label_id = await get_or_create_gmail_label(
            credentials, gmail_label_name
        )

        await apply_labels(
            credentials, mail.external_id, [gmail_label_id]
        )

        applied.append({
            "mail_id": mail.id,
            "subject": mail.subject,
            "gmail_label": gmail_label_name,
        })

    return {"applied": len(applied), "results": applied}
