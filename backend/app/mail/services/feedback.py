from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.mail.models import Classification, Label, Mail


async def get_feedback_examples(
    db: AsyncSession,
    user_id: int,
    limit: int = 20,
) -> list[dict]:
    """사용자의 최근 피드백 기록을 가져와서 few-shot 예시로 활용.

    Returns: list[dict] with keys:
        - from_email, from_name, subject
        - original_category (AI 원래 분류)
        - corrected_category (사용자 수정 분류)
    """
    # user_feedback IS NOT NULL인 최신 Classification을 가져오기
    result = await db.execute(
        select(Classification, Mail, Label)
        .join(Mail, Classification.mail_id == Mail.id)
        .join(Label, Classification.label_id == Label.id)
        .where(
            Mail.user_id == user_id,
            Classification.user_feedback.isnot(None),
        )
        .order_by(Classification.created_at.desc())
        .limit(limit)
    )

    examples = []
    for classification, mail, label in result.all():
        # original_category가 있으면 사용, 없으면 label.name과 다를 때만 유효
        original = classification.original_category or label.name
        corrected = classification.user_feedback
        # 원래 분류와 수정 분류가 같으면 (원래 카테고리 추적 실패) 스킵
        if original == corrected:
            continue
        examples.append({
            "from_email": mail.from_email or "",
            "from_name": mail.from_name or "",
            "subject": mail.subject or "",
            "original_category": original,
            "corrected_category": corrected,
        })

    return examples


async def get_sender_rules(
    db: AsyncSession,
    user_id: int,
    min_count: int = 2,
) -> dict[str, str]:
    """발신자별로 사용자가 일관되게 수정한 카테고리를 규칙으로 추출.

    같은 발신자의 메일을 min_count번 이상 동일 카테고리로 수정한 경우만 규칙으로 간주.

    Returns: dict[from_email, category]
    """
    rules = await _get_sender_rules_with_counts(db, user_id, min_count)
    return {email: category for email, (category, _) in rules.items()}


async def _get_sender_rules_with_counts(
    db: AsyncSession,
    user_id: int,
    min_count: int = 2,
) -> dict[str, tuple[str, int]]:
    """발신자 규칙을 카운트와 함께 반환. 내부 헬퍼."""
    result = await db.execute(
        select(
            Mail.from_email,
            Classification.user_feedback,
            func.count().label("count"),
        )
        .join(Mail, Classification.mail_id == Mail.id)
        .where(
            Mail.user_id == user_id,
            Classification.user_feedback.isnot(None),
            Mail.from_email.isnot(None),
        )
        .group_by(Mail.from_email, Classification.user_feedback)
        .having(func.count() >= min_count)
        .order_by(func.count().desc())
    )

    sender_rules: dict[str, tuple[str, int]] = {}
    for from_email, category, count in result.all():
        if from_email not in sender_rules or count > sender_rules[from_email][1]:
            sender_rules[from_email] = (category, count)

    return sender_rules


async def get_feedback_stats(
    db: AsyncSession,
    user_id: int,
) -> dict:
    """피드백 통계 조회.

    Returns:
        - total_feedbacks: 총 피드백 수
        - sender_rules: 발신자 규칙 목록 (발신자, 카테고리, 수정 횟수)
        - recent_feedbacks: 최근 피드백 목록 (제목, 원래 분류, 수정 분류, 날짜)
    """
    # 총 피드백 수
    total_result = await db.execute(
        select(func.count())
        .select_from(Classification)
        .join(Mail, Classification.mail_id == Mail.id)
        .where(
            Mail.user_id == user_id,
            Classification.user_feedback.isnot(None),
        )
    )
    total_feedbacks = total_result.scalar() or 0

    # 발신자 규칙 (min_count=2) — 카운트 포함, 단일 쿼리
    rules_with_counts = await _get_sender_rules_with_counts(db, user_id, min_count=2)
    sender_rules = [
        {"from_email": email, "category": category, "count": count}
        for email, (category, count) in rules_with_counts.items()
    ]

    # 최근 피드백 목록 (10개)
    recent_result = await db.execute(
        select(Classification, Mail, Label)
        .join(Mail, Classification.mail_id == Mail.id)
        .join(Label, Classification.label_id == Label.id)
        .where(
            Mail.user_id == user_id,
            Classification.user_feedback.isnot(None),
        )
        .order_by(Classification.created_at.desc())
        .limit(10)
    )

    recent_feedbacks = []
    for classification, mail, label in recent_result.all():
        recent_feedbacks.append({
            "subject": mail.subject or "(제목 없음)",
            "original": label.name,
            "corrected": classification.user_feedback,
            "date": classification.created_at.isoformat(),
        })

    return {
        "total_feedbacks": total_feedbacks,
        "sender_rules_count": len(sender_rules),
        "sender_rules": sender_rules,
        "recent_feedbacks": recent_feedbacks,
    }
