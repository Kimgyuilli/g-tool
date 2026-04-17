import logging

import httpx
from tenacity import retry, stop_after_attempt, wait_fixed

from app.config import settings
from app.services.sanitizer import sanitize_excerpt

logger = logging.getLogger(__name__)

_client: httpx.AsyncClient | None = None


def init_client() -> None:
    global _client
    _client = httpx.AsyncClient()


async def close_client() -> None:
    global _client
    if _client:
        await _client.aclose()
        _client = None


async def health_check() -> dict:
    """Discord webhook 연결 상태 확인."""
    try:
        if _client is None:
            return {"status": "error", "detail": "client not initialized"}
        response = await _client.head(settings.discord_webhook_url)
        response.raise_for_status()
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


async def _post_webhook(payload: dict) -> None:
    if _client is None:
        raise RuntimeError("httpx client not initialized")
    response = await _client.post(settings.discord_webhook_url, json=payload)
    response.raise_for_status()


def _build_sanitized_report_fields(report) -> list[dict]:
    return [
        {"name": "에러 타입", "value": sanitize_excerpt(report.errorType, limit=256), "inline": True},
        {"name": "요청", "value": sanitize_excerpt(report.requestUrl, limit=512), "inline": True},
        {"name": "메시지", "value": sanitize_excerpt(report.errorMessage, limit=1024)},
    ]


@retry(stop=stop_after_attempt(2), wait=wait_fixed(1), reraise=True)
async def send_error_alert(report) -> None:
    embed = {
        "title": "\U0001f6a8 500 에러 발생",
        "color": 0xFF0000,
        "fields": [
            *_build_sanitized_report_fields(report),
            {"name": "발생 시간", "value": sanitize_excerpt(report.timestamp, limit=120), "inline": True},
        ],
    }
    await _post_webhook({"embeds": [embed]})


@retry(stop=stop_after_attempt(2), wait=wait_fixed(1), reraise=True)
async def send_pr_alert(pr_url: str, summary: str) -> None:
    embed = {
        "title": "\u2705 자동 수정 PR 생성",
        "color": 0x00FF00,
        "fields": [
            {"name": "변경 사항", "value": summary[:1024]},
            {"name": "PR 링크", "value": pr_url},
        ],
    }
    await _post_webhook({"embeds": [embed]})


@retry(stop=stop_after_attempt(2), wait=wait_fixed(1), reraise=True)
async def send_failure_alert(report, reason: str, issue_url: str | None = None) -> None:
    fields = [
        *_build_sanitized_report_fields(report),
        {"name": "실패 사유", "value": sanitize_excerpt(reason, limit=1024)},
    ]
    if issue_url:
        fields.append({"name": "Issue", "value": sanitize_excerpt(issue_url, limit=512)})

    embed = {
        "title": "\u26a0\ufe0f 에러 자동 수정 실패",
        "color": 0xFFA500,
        "fields": fields,
    }
    await _post_webhook({"embeds": [embed]})
