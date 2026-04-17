import logging

import httpx
from tenacity import retry, stop_after_attempt, wait_fixed

from app.config import settings

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


@retry(stop=stop_after_attempt(2), wait=wait_fixed(1), reraise=True)
async def send_error_alert(report) -> None:
    embed = {
        "title": "\U0001f6a8 500 에러 발생",
        "color": 0xFF0000,
        "fields": [
            {"name": "에러 타입", "value": report.errorType, "inline": True},
            {"name": "요청", "value": report.requestUrl, "inline": True},
            {"name": "메시지", "value": report.errorMessage[:1024]},
            {"name": "발생 시간", "value": report.timestamp, "inline": True},
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
        {"name": "에러 타입", "value": report.errorType, "inline": True},
        {"name": "요청", "value": report.requestUrl, "inline": True},
        {"name": "메시지", "value": report.errorMessage[:1024]},
        {"name": "실패 사유", "value": reason[:1024]},
    ]
    if issue_url:
        fields.append({"name": "Issue", "value": issue_url})

    embed = {
        "title": "\u26a0\ufe0f 에러 자동 수정 실패",
        "color": 0xFFA500,
        "fields": fields,
    }
    await _post_webhook({"embeds": [embed]})
