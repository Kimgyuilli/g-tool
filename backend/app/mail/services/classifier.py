from __future__ import annotations

import json

import anthropic

from app.config import settings

DEFAULT_CATEGORIES = [
    "업무",       # Work
    "개인",       # Personal
    "금융",       # Finance
    "프로모션",   # Promotion
    "뉴스레터",   # Newsletter
    "알림",       # Notification
    "중요",       # Important
]

SYSTEM_PROMPT = """당신은 이메일 분류 전문가입니다.
주어진 이메일의 발신자, 제목, 본문을 분석하여 가장 적절한 카테고리를 분류하세요.

카테고리 목록:
- 업무: 회의, 업무 요청, 팀 커뮤니케이션
- 개인: 개인적인 연락, 가족/친구
- 금융: 은행, 결제, 카드, 보험
- 프로모션: 광고, 마케팅, 할인 쿠폰
- 뉴스레터: 구독 뉴스, 블로그 업데이트
- 알림: 서비스 알림, 비밀번호 변경, 배송 안내
- 중요: 긴급하거나 중요한 메일

응답은 반드시 아래 JSON 형식으로만 출력하세요. 다른 텍스트는 포함하지 마세요.
"""

SINGLE_TEMPLATE = """\
이메일:
- 발신자: {from_email} ({from_name})
- 제목: {subject}
- 본문 (일부): {body}

JSON 형식으로 응답:
{{"category": "카테고리명", "confidence": 0.0~1.0, "reason": "분류 이유 한 줄"}}"""

BATCH_TEMPLATE = """\
아래 이메일들을 각각 분류하세요.

{emails_text}

JSON 배열로 응답:
[{{"index": 0, "category": "카테고리명", \
"confidence": 0.0~1.0, "reason": "한 줄"}}, ...]"""


def _extract_json(text: str) -> str:
    """Extract JSON from text that may contain markdown code fences."""
    stripped = text.strip()
    if stripped.startswith("```"):
        # Remove opening fence (```json or ```)
        first_newline = stripped.index("\n")
        stripped = stripped[first_newline + 1 :]
        # Remove closing fence
        if stripped.endswith("```"):
            stripped = stripped[: -3].strip()
    return stripped


def _truncate_body(body: str | None, max_chars: int = 500) -> str:
    if not body:
        return "(본문 없음)"
    return body[:max_chars] + ("..." if len(body) > max_chars else "")


def _build_feedback_section(examples: list[dict]) -> str:
    """사용자 피드백 예시를 프롬프트에 추가할 섹션으로 변환."""
    if not examples:
        return ""

    lines = [
        "## 사용자의 이전 분류 수정 기록 (이 패턴을 참고하세요):",
        "",
    ]

    for ex in examples[:10]:  # 최대 10개만 사용
        from_info = f"{ex.get('from_email', '')} ({ex.get('from_name', '')})"
        subject = ex.get("subject", "")
        original = ex.get("original_category", "")
        corrected = ex.get("corrected_category", "")

        lines.append(
            f'- "발신자: {from_info}, 제목: {subject}" '
            f'→ 원래 "{original}"로 분류했으나 사용자가 "{corrected}"로 수정'
        )

    return "\n".join(lines)


async def classify_single(
    from_email: str,
    from_name: str,
    subject: str,
    body: str | None,
    feedback_examples: list[dict] | None = None,
    sender_rules: dict[str, str] | None = None,
) -> dict:
    """Classify a single email using Claude API."""
    # 발신자 규칙 우선 적용
    if sender_rules and from_email and from_email in sender_rules:
        return {
            "category": sender_rules[from_email],
            "confidence": 1.0,
            "reason": "발신자 규칙 적용 (사용자 피드백 기반)",
        }

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    # Few-shot 프롬프트 생성
    system_prompt = SYSTEM_PROMPT
    if feedback_examples:
        feedback_section = _build_feedback_section(feedback_examples)
        system_prompt = f"{SYSTEM_PROMPT}\n\n{feedback_section}"

    user_message = SINGLE_TEMPLATE.format(
        from_email=from_email or "",
        from_name=from_name or "",
        subject=subject or "(제목 없음)",
        body=_truncate_body(body),
    )

    response = await client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=256,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )

    text = _extract_json(response.content[0].text)
    return json.loads(text)


async def classify_batch(
    emails: list[dict],
    feedback_examples: list[dict] | None = None,
    sender_rules: dict[str, str] | None = None,
) -> list[dict]:
    """Classify multiple emails in a single API call."""
    if not emails:
        return []

    # 발신자 규칙으로 자동 분류 가능한 메일 분리
    auto_classified = []
    needs_ai = []
    index_map = {}  # AI 분류할 메일의 원래 인덱스 매핑

    for i, mail in enumerate(emails):
        from_email = mail.get("from_email", "")
        if sender_rules and from_email and from_email in sender_rules:
            auto_classified.append({
                "index": i,
                "category": sender_rules[from_email],
                "confidence": 1.0,
                "reason": "발신자 규칙 적용 (사용자 피드백 기반)",
            })
        else:
            index_map[len(needs_ai)] = i
            needs_ai.append(mail)

    # AI 분류가 필요한 메일이 없으면 바로 반환
    if not needs_ai:
        return auto_classified

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    # Few-shot 프롬프트 생성
    system_prompt = SYSTEM_PROMPT
    if feedback_examples:
        feedback_section = _build_feedback_section(feedback_examples)
        system_prompt = f"{SYSTEM_PROMPT}\n\n{feedback_section}"

    # 10개씩 청크로 나눠서 API 호출 (토큰 초과 방지)
    chunk_size = 10
    ai_results = []

    for chunk_start in range(0, len(needs_ai), chunk_size):
        chunk = needs_ai[chunk_start : chunk_start + chunk_size]

        parts = []
        for i, mail in enumerate(chunk):
            parts.append(
                f"[메일 {i}]\n"
                f"- 발신자: {mail.get('from_email', '')} "
                f"({mail.get('from_name', '')})\n"
                f"- 제목: {mail.get('subject', '(제목 없음)')}\n"
                f"- 본문: {_truncate_body(mail.get('body'))}"
            )

        user_message = BATCH_TEMPLATE.format(emails_text="\n\n".join(parts))

        response = await client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )

        text = _extract_json(response.content[0].text)
        chunk_results = json.loads(text)

        # 청크 내 index를 원래 메일 목록의 index로 변환
        for result in chunk_results:
            ai_index = result.get("index", 0)
            key = chunk_start + ai_index
            original_index = index_map.get(key, key)
            result["index"] = original_index
        ai_results.extend(chunk_results)

    # 자동 분류 결과와 AI 분류 결과 병합 후 index 순으로 정렬
    all_results = auto_classified + ai_results
    all_results.sort(key=lambda x: x.get("index", 0))

    return all_results
