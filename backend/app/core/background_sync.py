from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.service import build_credentials
from app.config import settings
from app.core.database import AsyncSessionLocal
from app.core.security import decrypt_value, encrypt_value
from app.mail.models import Classification, Label, Mail, SyncState, User
from app.mail.services.classifier import classify_batch
from app.mail.services.feedback import get_feedback_examples, get_sender_rules
from app.mail.services.gmail import get_messages_batch, list_message_ids
from app.mail.services.helpers import filter_new_external_ids
from app.mail.services.naver import fetch_messages

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Private helpers — shared sync logic
# ---------------------------------------------------------------------------


async def _get_sync_state(
    db: AsyncSession, user_id: int, source: str
) -> SyncState | None:
    """SyncState 조회."""
    result = await db.execute(
        select(SyncState).where(
            SyncState.user_id == user_id,
            SyncState.source == source,
        )
    )
    return result.scalar_one_or_none()


async def _update_sync_state(
    db: AsyncSession,
    user_id: int,
    source: str,
    sync_state: SyncState | None,
    *,
    next_page_token: str | None = None,
    last_uid: str | None = None,
) -> None:
    """SyncState 업데이트 또는 생성."""
    now = datetime.now(tz=UTC)
    if sync_state:
        if next_page_token is not None:
            sync_state.next_page_token = next_page_token
        if last_uid is not None:
            sync_state.last_uid = last_uid
        sync_state.last_synced_at = now
    else:
        sync_state = SyncState(
            user_id=user_id,
            source=source,
            next_page_token=next_page_token,
            last_uid=last_uid,
            last_synced_at=now,
        )
        db.add(sync_state)


def _save_mails(
    db: AsyncSession,
    user_id: int,
    source: str,
    messages: list[dict[str, Any]],
) -> None:
    """Mail 객체 생성 + DB 추가."""
    for msg in messages:
        mail = Mail(
            user_id=user_id,
            source=source,
            external_id=msg["external_id"],
            from_email=msg["from_email"],
            from_name=msg["from_name"],
            to_email=msg.get("to_email"),
            subject=msg["subject"],
            body_text=msg["body_text"],
            folder=msg.get("folder"),
            received_at=msg["received_at"],
            is_read=msg["is_read"],
        )
        db.add(mail)


# ---------------------------------------------------------------------------
# Public sync functions
# ---------------------------------------------------------------------------


async def sync_user_gmail(user: User, db: AsyncSession) -> int:
    """Gmail 동기화.

    Returns: 새로 동기화된 메일 수
    """
    if not user.google_oauth_token or not user.google_refresh_token:
        logger.debug(
            f"User {user.id}: Google OAuth 토큰 미설정, Gmail 동기화 스킵"
        )
        return 0

    try:
        token = decrypt_value(user.google_oauth_token)
        refresh_token = decrypt_value(user.google_refresh_token)
        credentials = build_credentials(token, refresh_token)

        sync_state = await _get_sync_state(db, user.id, "gmail")
        page_token = sync_state.next_page_token if sync_state else None

        result = await list_message_ids(
            credentials, max_results=50, page_token=page_token
        )
        gmail_ids = result["message_ids"]

        if not gmail_ids:
            logger.debug(f"User {user.id}: Gmail 새 메일 없음")
            return 0

        new_ids = await filter_new_external_ids(db, user.id, "gmail", gmail_ids)

        if not new_ids:
            await _update_sync_state(
                db, user.id, "gmail", sync_state,
                next_page_token=result["next_page_token"],
            )
            await db.commit()
            logger.debug(f"User {user.id}: Gmail 새 메일 없음 (중복 필터링)")
            return 0

        details = await get_messages_batch(credentials, new_ids)

        # OAuth 토큰이 갱신되었으면 DB에 암호화하여 저장
        if credentials.token != token:
            user.google_oauth_token = encrypt_value(credentials.token)

        _save_mails(db, user.id, "gmail", details)
        await _update_sync_state(
            db, user.id, "gmail", sync_state,
            next_page_token=result["next_page_token"],
        )

        await db.commit()
        logger.info(f"User {user.id}: Gmail {len(details)}개 메일 동기화 완료")
        return len(details)

    except Exception as exc:
        logger.error(
            f"User {user.id}: Gmail 동기화 실패 — {exc.__class__.__name__}: {exc}"
        )
        await db.rollback()
        return 0


async def sync_user_naver(user: User, db: AsyncSession) -> int:
    """네이버 동기화.

    Returns: 새로 동기화된 메일 수
    """
    if not user.naver_email or not user.naver_app_password:
        logger.debug(
            f"User {user.id}: 네이버 인증 미설정, 네이버 동기화 스킵"
        )
        return 0

    try:
        sync_state = await _get_sync_state(db, user.id, "naver")
        since_uid = sync_state.last_uid if sync_state else None

        result = await fetch_messages(
            settings.naver_imap_host,
            settings.naver_imap_port,
            user.naver_email,
            decrypt_value(user.naver_app_password),
            folder="INBOX",
            since_uid=since_uid,
            max_results=50,
        )

        messages = result["messages"]
        last_uid = result["last_uid"]

        if not messages:
            logger.debug(f"User {user.id}: 네이버 새 메일 없음")
            return 0

        external_ids = [m["external_id"] for m in messages]
        new_ids = await filter_new_external_ids(db, user.id, "naver", external_ids)
        new_messages = [m for m in messages if m["external_id"] in set(new_ids)]

        if not new_messages:
            if last_uid:
                await _update_sync_state(
                    db, user.id, "naver", sync_state, last_uid=last_uid
                )
            await db.commit()
            logger.debug(
                f"User {user.id}: 네이버 새 메일 없음 (중복 필터링)"
            )
            return 0

        _save_mails(db, user.id, "naver", new_messages)
        if last_uid:
            await _update_sync_state(
                db, user.id, "naver", sync_state, last_uid=last_uid
            )

        await db.commit()
        logger.info(
            f"User {user.id}: 네이버 {len(new_messages)}개 메일 동기화 완료"
        )
        return len(new_messages)

    except Exception as exc:
        logger.error(
            f"User {user.id}: 네이버 동기화 실패 — {exc.__class__.__name__}: {exc}"
        )
        await db.rollback()
        return 0


async def classify_user_mails(user: User, db: AsyncSession) -> int:
    """미분류 메일 배치 분류.

    Returns: 새로 분류된 메일 수
    """
    try:
        # 분류되지 않은 메일 조회
        unclassified_result = await db.execute(
            select(Mail)
            .outerjoin(Classification, Mail.id == Classification.mail_id)
            .where(
                Mail.user_id == user.id,
                Classification.id.is_(None),
            )
            .limit(50)
        )
        unclassified_mails = list(unclassified_result.scalars().all())

        if not unclassified_mails:
            logger.debug(f"User {user.id}: 미분류 메일 없음")
            return 0

        # 피드백 데이터 조회
        feedback_examples = await get_feedback_examples(db, user.id, limit=20)
        sender_rules = await get_sender_rules(db, user.id, min_count=2)

        # 분류 입력 데이터 준비
        emails = [
            {
                "from_email": mail.from_email or "",
                "from_name": mail.from_name or "",
                "subject": mail.subject or "",
                "body": mail.body_text or "",
            }
            for mail in unclassified_mails
        ]

        # 배치 분류 (피드백 활용)
        results = await classify_batch(
            emails,
            feedback_examples=feedback_examples,
            sender_rules=sender_rules,
        )

        # 기본 라벨 가져오기 또는 생성
        label_map: dict[str, int] = {}
        for result in results:
            category = result.get("category", "기타")
            if category not in label_map:
                label_result = await db.execute(
                    select(Label).where(
                        Label.user_id == user.id,
                        Label.name == category,
                        Label.source.is_(None),
                    )
                )
                label = label_result.scalar_one_or_none()
                if label is None:
                    label = Label(
                        user_id=user.id,
                        name=category,
                        source=None,
                    )
                    db.add(label)
                    await db.flush()
                label_map[category] = label.id

        # Classification 저장
        classified_count = 0
        for i, result in enumerate(results):
            idx = result.get("index", i)
            if idx >= len(unclassified_mails):
                continue

            mail = unclassified_mails[idx]
            category = result.get("category", "기타")
            confidence = result.get("confidence", 0.8)

            classification = Classification(
                mail_id=mail.id,
                label_id=label_map[category],
                confidence=confidence,
            )
            db.add(classification)
            classified_count += 1

        await db.commit()
        logger.info(
            f"User {user.id}: {classified_count}개 메일 분류 완료"
        )
        return classified_count

    except Exception as exc:
        logger.error(
            f"User {user.id}: 메일 분류 실패 — {exc.__class__.__name__}: {exc}"
        )
        await db.rollback()
        return 0


async def sync_all_users():
    """메인 스케줄러 함수 - 모든 사용자 순회하며 동기화+분류."""
    logger.info("백그라운드 동기화 시작")

    # 사용자 ID 목록 조회
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User.id))
        user_ids = list(result.scalars().all())

    if not user_ids:
        logger.info("등록된 사용자 없음, 동기화 스킵")
        return

    total_gmail = 0
    total_naver = 0
    total_classified = 0

    for user_id in user_ids:
        # 사용자별 독립 세션 — 한 사용자의 rollback이 다른 사용자에 영향 주지 않음
        try:
            async with AsyncSessionLocal() as db:
                # 세션에 바인딩된 User 객체 로드
                user = await db.get(User, user_id)
                if user is None:
                    continue

                logger.info(f"User {user.id} ({user.email}) 동기화 시작")

                # Gmail 동기화
                gmail_count = await sync_user_gmail(user, db)
                total_gmail += gmail_count

                # 네이버 동기화
                naver_count = await sync_user_naver(user, db)
                total_naver += naver_count

                # 자동 분류 (설정이 활성화된 경우)
                classified_count = 0
                if settings.auto_classify:
                    classified_count = await classify_user_mails(user, db)
                    total_classified += classified_count

                logger.info(
                    f"User {user.id} 완료: "
                    f"Gmail {gmail_count}, 네이버 {naver_count}, "
                    f"분류 {classified_count}"
                )

        except Exception as exc:
            logger.error(
                f"User {user_id} 동기화 실패 — {exc.__class__.__name__}: {exc}"
            )

    logger.info(
        f"전체 동기화 완료: "
        f"Gmail {total_gmail}, 네이버 {total_naver}, "
        f"분류 {total_classified}"
    )
