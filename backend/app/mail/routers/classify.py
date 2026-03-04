from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.exceptions import (
    ClassificationFailedException,
    ClassificationNotFoundException,
    NotAuthorizedException,
)
from app.mail.models import Classification, Label, Mail, User
from app.mail.services.classifier import (
    DEFAULT_CATEGORIES,
    classify_batch,
    classify_single,
)
from app.mail.services.feedback import (
    get_feedback_examples,
    get_feedback_stats,
    get_sender_rules,
)

router = APIRouter(prefix="/api/classify", tags=["classify"])


class ClassifySingleRequest(BaseModel):
    from_email: str = ""
    from_name: str = ""
    subject: str = ""
    body: str | None = None


class ClassifySingleResponse(BaseModel):
    category: str
    confidence: float
    reason: str


@router.post("/single", response_model=ClassifySingleResponse)
async def classify_single_mail(req: ClassifySingleRequest):
    """Classify a single email (stateless, no DB save)."""
    try:
        result = await classify_single(
            from_email=req.from_email,
            from_name=req.from_name,
            subject=req.subject,
            body=req.body,
        )
    except Exception as exc:
        raise ClassificationFailedException(detail=f"Classification failed: {exc}")

    return ClassifySingleResponse(
        category=result.get("category", "알림"),
        confidence=result.get("confidence", 0.0),
        reason=result.get("reason", ""),
    )


@router.post("/mails")
async def classify_user_mails(
    source: str | None = Query(default=None),
    mail_ids: list[int] | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Classify user's mails and save results to DB."""
    user_id = user.id

    query = select(Mail).where(Mail.user_id == user_id)
    if source:
        query = query.where(Mail.source == source)
    if mail_ids:
        query = query.where(Mail.id.in_(mail_ids))

    result = await db.execute(query)
    mails = list(result.scalars().all())

    if not mails:
        return {"classified": 0, "results": []}

    # Filter out already classified mails (unless specific IDs requested)
    if not mail_ids:
        classified_mail_ids_result = await db.execute(
            select(Classification.mail_id).where(
                Classification.mail_id.in_([m.id for m in mails])
            )
        )
        already_classified = set(classified_mail_ids_result.scalars().all())
        mails = [m for m in mails if m.id not in already_classified]

    if not mails:
        return {"classified": 0, "results": []}

    # 피드백 데이터 조회
    feedback_examples = await get_feedback_examples(db, user_id, limit=20)
    sender_rules = await get_sender_rules(db, user_id, min_count=2)

    # Prepare batch input
    email_dicts = [
        {
            "from_email": m.from_email or "",
            "from_name": m.from_name or "",
            "subject": m.subject or "",
            "body": m.body_text,
        }
        for m in mails
    ]

    try:
        classifications = await classify_batch(
            email_dicts,
            feedback_examples=feedback_examples,
            sender_rules=sender_rules,
        )
    except Exception as exc:
        raise ClassificationFailedException(detail=f"Classification failed: {exc}")

    # Ensure default labels exist and build label cache
    await _ensure_default_labels(db, user_id)
    label_cache: dict[str, Label] = {}
    all_labels_result = await db.execute(
        select(Label).where(Label.user_id == user_id)
    )
    for lbl in all_labels_result.scalars().all():
        label_cache[lbl.name] = lbl

    results = []
    for cls in classifications:
        idx = cls.get("index", 0)
        if idx >= len(mails):
            continue

        mail = mails[idx]
        category = cls.get("category", "알림")
        confidence = cls.get("confidence", 0.0)

        # Find or create label (using cache)
        label = label_cache.get(category)
        if label is None:
            label = Label(user_id=user_id, name=category, is_default=False)
            db.add(label)
            await db.flush()
            label_cache[category] = label

        # Save classification
        classification = Classification(
            mail_id=mail.id,
            label_id=label.id,
            confidence=confidence,
        )
        db.add(classification)

        results.append({
            "mail_id": mail.id,
            "subject": mail.subject,
            "category": category,
            "confidence": confidence,
            "reason": cls.get("reason", ""),
        })

    await db.commit()
    return {"classified": len(results), "results": results}


class UpdateClassificationRequest(BaseModel):
    classification_id: int
    new_category: str


@router.put("/update")
async def update_classification(
    req: UpdateClassificationRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually update a classification's label (user feedback)."""
    user_id = user.id

    result = await db.execute(
        select(Classification).where(
            Classification.id == req.classification_id
        )
    )
    classification = result.scalar_one_or_none()
    if classification is None:
        raise ClassificationNotFoundException()

    # Verify mail belongs to user
    mail_result = await db.execute(
        select(Mail).where(
            Mail.id == classification.mail_id,
            Mail.user_id == user_id,
        )
    )
    if mail_result.scalar_one_or_none() is None:
        raise NotAuthorizedException()

    # Find or create the new label
    label_result = await db.execute(
        select(Label).where(
            Label.user_id == user_id,
            Label.name == req.new_category,
        )
    )
    label = label_result.scalar_one_or_none()
    if label is None:
        label = Label(
            user_id=user_id,
            name=req.new_category,
            is_default=False,
        )
        db.add(label)
        await db.flush()

    # 원래 카테고리 보존 (첫 수정 시에만)
    if classification.original_category is None:
        old_label_result = await db.execute(
            select(Label).where(Label.id == classification.label_id)
        )
        old_label = old_label_result.scalar_one_or_none()
        classification.original_category = old_label.name if old_label else None

    classification.label_id = label.id
    classification.user_feedback = req.new_category
    await db.commit()

    return {
        "classification_id": classification.id,
        "new_category": req.new_category,
        "message": "분류가 수정되었습니다.",
    }


@router.get("/categories")
async def get_categories():
    """Return the list of available classification categories."""
    return {"categories": DEFAULT_CATEGORIES}


@router.get("/feedback-stats")
async def get_classification_feedback_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """사용자의 분류 피드백 통계 조회."""
    stats = await get_feedback_stats(db, user.id)
    return stats


async def _ensure_default_labels(db: AsyncSession, user_id: int) -> None:
    """Create default category labels if they don't exist."""
    for category in DEFAULT_CATEGORIES:
        result = await db.execute(
            select(Label).where(Label.user_id == user_id, Label.name == category)
        )
        if result.scalar_one_or_none() is None:
            db.add(Label(user_id=user_id, name=category, is_default=True))
    await db.flush()
