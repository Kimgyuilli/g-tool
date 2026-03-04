from __future__ import annotations

import asyncio
import email
import email.header
import email.utils
import imaplib
import re
from contextlib import contextmanager
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.mail.models import User


@contextmanager
def _imap_connection(
    host: str,
    port: int,
    user: str,
    password: str,
):
    """Context manager for IMAP connection with guaranteed cleanup."""
    conn = imaplib.IMAP4_SSL(host, port)
    try:
        conn.login(user, password)
        yield conn
    finally:
        try:
            conn.logout()
        except Exception:
            pass


async def verify_credentials(
    host: str,
    port: int,
    user: str,
    password: str,
) -> bool:
    """Test IMAP login. Returns True if successful."""

    def _test():
        with _imap_connection(host, port, user, password):
            return True

    return await asyncio.to_thread(_test)


async def list_folders(
    host: str,
    port: int,
    user: str,
    password: str,
) -> list[str]:
    """List all IMAP folders."""

    def _fetch():
        with _imap_connection(host, port, user, password) as conn:
            status, data = conn.list()
            if status != "OK":
                return []
            folders = []
            for item in data:
                if item is None:
                    continue
                if isinstance(item, bytes):
                    decoded = item.decode(
                        "utf-8", errors="replace"
                    )
                else:
                    decoded = item
                # Parse folder name from IMAP LIST response
                # Format: (\\flags) "delimiter" "folder_name"
                match = re.search(
                    r'"[^"]*"\s+"?([^"]*)"?\s*$', decoded
                )
                if match:
                    folders.append(match.group(1))
                else:
                    parts = decoded.rsplit('"', 2)
                    if len(parts) >= 2:
                        folders.append(parts[-2])
            return folders

    return await asyncio.to_thread(_fetch)


async def fetch_messages(
    host: str,
    port: int,
    user: str,
    password: str,
    folder: str = "INBOX",
    since_uid: str | None = None,
    max_results: int = 50,
) -> dict[str, Any]:
    """Fetch messages from a folder via IMAP."""

    def _fetch():
        with _imap_connection(
            host, port, user, password
        ) as conn:
            status, _ = conn.select(folder, readonly=True)
            if status != "OK":
                return {
                    "messages": [],
                    "last_uid": since_uid,
                }

            # Search for messages
            if since_uid:
                try:
                    uid_start = int(since_uid) + 1
                except ValueError:
                    uid_start = 1
                search_criteria = f"UID {uid_start}:*"
                status, data = conn.uid(
                    "SEARCH", None, search_criteria
                )
            else:
                status, data = conn.uid(
                    "SEARCH", None, "ALL"
                )

            if status != "OK" or not data[0]:
                return {
                    "messages": [],
                    "last_uid": since_uid,
                }

            uids = data[0].split()

            # Filter out since_uid itself (range is inclusive)
            if since_uid:
                try:
                    threshold = int(since_uid)
                    uids = [
                        u for u in uids
                        if int(u) > threshold
                    ]
                except ValueError:
                    pass

            if not uids:
                return {
                    "messages": [],
                    "last_uid": since_uid,
                }

            # Take most recent N messages
            uids = uids[-max_results:]

            messages = []
            for uid in uids:
                msg = _fetch_single(conn, uid, folder)
                if msg:
                    messages.append(msg)

            if uids:
                last = uids[-1]
                last_uid = _uid_to_str(last)
            else:
                last_uid = since_uid

            return {
                "messages": messages,
                "last_uid": last_uid,
            }

    return await asyncio.to_thread(_fetch)


def _fetch_single(
    conn: imaplib.IMAP4_SSL,
    uid: bytes | str,
    folder: str,
) -> dict[str, Any] | None:
    """Fetch and parse a single message by UID."""
    status, msg_data = conn.uid(
        "FETCH", uid, "(RFC822 FLAGS)"
    )
    if status != "OK" or not msg_data or not msg_data[0]:
        return None

    raw_email = msg_data[0]
    if not isinstance(raw_email, tuple):
        return None

    flags_part = raw_email[0]
    body = raw_email[1]

    uid_str = _uid_to_str(uid)
    parsed = _parse_email(body, uid_str)

    # Check flags for read status
    if isinstance(flags_part, bytes):
        flags_str = flags_part.decode(
            "utf-8", errors="replace"
        )
    else:
        flags_str = str(flags_part)
    parsed["is_read"] = "\\Seen" in flags_str
    parsed["folder"] = folder

    return parsed


def _uid_to_str(uid: bytes | str) -> str:
    """Convert IMAP UID to string."""
    if isinstance(uid, bytes):
        return uid.decode()
    return str(uid)


def _parse_email(
    raw_bytes: bytes, uid: str
) -> dict[str, Any]:
    """Parse raw email bytes into a flat dict."""
    msg = email.message_from_bytes(raw_bytes)

    from_header = msg.get("From", "")
    from_name, from_email_addr = _decode_header_addr(
        from_header
    )

    to_header = msg.get("To", "")
    _, to_email_addr = _decode_header_addr(to_header)

    subject = _decode_header_value(msg.get("Subject", ""))

    body = _extract_body(msg)

    date_header = msg.get("Date", "")
    received_at = _parse_date(date_header)

    return {
        "external_id": uid,
        "from_email": from_email_addr,
        "from_name": from_name,
        "to_email": to_email_addr,
        "subject": subject,
        "body_text": body["text"],
        "body_html": body["html"],
        "received_at": received_at,
        "is_read": False,
        "folder": "INBOX",
    }


def _decode_header_value(value: str | None) -> str:
    """Decode MIME encoded header value."""
    if not value:
        return ""
    parts = email.header.decode_header(value)
    decoded_parts = []
    for part, charset in parts:
        if isinstance(part, bytes):
            decoded_parts.append(
                part.decode(charset or "utf-8", errors="replace")
            )
        else:
            decoded_parts.append(part)
    return " ".join(decoded_parts)


def _decode_header_addr(
    header: str,
) -> tuple[str, str]:
    """Decode and parse 'Name <email>' header."""
    decoded = _decode_header_value(header)
    name, addr = email.utils.parseaddr(decoded)
    return name, addr


def _extract_body(msg: email.message.Message) -> dict[str, str | None]:
    """Extract text and HTML body from email message."""
    if not msg.is_multipart():
        content_type = msg.get_content_type()
        payload = msg.get_payload(decode=True)
        if payload is None:
            return {"text": "", "html": None}
        charset = msg.get_content_charset() or "utf-8"
        decoded = payload.decode(charset, errors="replace")
        if content_type == "text/html":
            return {"text": _strip_html(decoded), "html": decoded}
        return {"text": decoded, "html": None}

    # Multipart: collect both text/plain and text/html
    text_plain: str | None = None
    text_html: str | None = None

    for part in msg.walk():
        ct = part.get_content_type()
        if ct == "text/plain" and text_plain is None:
            payload = part.get_payload(decode=True)
            if payload is not None:
                charset = part.get_content_charset() or "utf-8"
                text_plain = payload.decode(charset, errors="replace")
        elif ct == "text/html" and text_html is None:
            payload = part.get_payload(decode=True)
            if payload is not None:
                charset = part.get_content_charset() or "utf-8"
                text_html = payload.decode(charset, errors="replace")

    plain = text_plain or (
        _strip_html(text_html) if text_html else ""
    )
    return {"text": plain, "html": text_html}


def _strip_html(html: str) -> str:
    """Minimal HTML tag stripping."""
    text = re.sub(
        r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL
    )
    text = re.sub(
        r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL
    )
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _parse_date(date_str: str) -> datetime | None:
    """Parse email Date header to datetime."""
    if not date_str:
        return None
    try:
        parsed = email.utils.parsedate_to_datetime(date_str)
    except (ValueError, TypeError):
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


# ---------------------------------------------------------------------------
# High-level sync operations for routers
# ---------------------------------------------------------------------------


async def sync_naver_messages(
    db: AsyncSession,
    user: User,
    host: str,
    port: int,
    folder: str,
    max_results: int,
) -> dict[str, int]:
    """Sync Naver IMAP messages and save new ones to DB."""
    from sqlalchemy import select

    from app.mail.models import Mail, SyncState
    from app.mail.services.helpers import filter_new_external_ids

    sync_result = await db.execute(
        select(SyncState).where(
            SyncState.user_id == user.id,
            SyncState.source == "naver",
        )
    )
    sync_state = sync_result.scalar_one_or_none()
    since_uid = sync_state.last_uid if sync_state else None

    # Fetch messages from IMAP
    result = await fetch_messages(
        host,
        port,
        user.naver_email,
        user.naver_app_password,
        folder=folder,
        since_uid=since_uid,
        max_results=max_results,
    )

    messages = result["messages"]
    last_uid = result["last_uid"]

    if not messages:
        return {"synced": 0, "total_fetched": 0}

    # Filter out already-synced messages
    external_ids = [m["external_id"] for m in messages]
    new_external_ids = await filter_new_external_ids(db, user.id, "naver", external_ids)
    new_messages = [m for m in messages if m["external_id"] in set(new_external_ids)]

    # Save new messages to DB
    for msg in new_messages:
        mail = Mail(
            user_id=user.id,
            source="naver",
            external_id=msg["external_id"],
            from_email=msg["from_email"],
            from_name=msg["from_name"],
            to_email=msg["to_email"],
            subject=msg["subject"],
            body_text=msg["body_text"],
            body_html=msg["body_html"],
            folder=msg["folder"],
            received_at=msg["received_at"],
            is_read=msg["is_read"],
        )
        db.add(mail)

    # Update sync state
    if last_uid:
        if sync_state is None:
            sync_state = SyncState(
                user_id=user.id,
                source="naver",
                last_uid=last_uid,
                last_synced_at=datetime.now(tz=UTC),
            )
            db.add(sync_state)
        else:
            sync_state.last_uid = last_uid
            sync_state.last_synced_at = datetime.now(tz=UTC)

    await db.commit()

    return {
        "synced": len(new_messages),
        "total_fetched": len(messages),
    }
