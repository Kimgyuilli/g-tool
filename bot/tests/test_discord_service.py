from unittest.mock import AsyncMock, patch

from app.schemas import ErrorReport
from app.services.discord_service import send_error_alert, send_failure_alert, send_pr_alert


@patch("app.services.discord_service._post_webhook", new_callable=AsyncMock)
async def test_send_error_alert_posts_correct_embed(mock_post, sample_error_report):
    await send_error_alert(sample_error_report)
    payload = mock_post.call_args[0][0]
    embed = payload["embeds"][0]
    assert embed["title"] == "🚨 500 에러 발생"
    assert embed["color"] == 0xFF0000
    assert any(f["name"] == "에러 타입" for f in embed["fields"])


@patch("app.services.discord_service._post_webhook", new_callable=AsyncMock)
async def test_send_pr_alert_posts_correct_embed(mock_post):
    await send_pr_alert("https://github.com/pr/1", "수정 요약")
    payload = mock_post.call_args[0][0]
    embed = payload["embeds"][0]
    assert embed["title"] == "✅ 자동 수정 PR 생성"
    assert embed["color"] == 0x00FF00


@patch("app.services.discord_service._post_webhook", new_callable=AsyncMock)
async def test_send_failure_alert_posts_correct_embed(mock_post, sample_error_report):
    await send_failure_alert(sample_error_report, "AI 실패")
    payload = mock_post.call_args[0][0]
    embed = payload["embeds"][0]
    assert embed["title"] == "⚠️ 에러 자동 수정 실패"
    assert embed["color"] == 0xFFA500
    assert any(f["value"] == "AI 실패" for f in embed["fields"])


@patch("app.services.discord_service._post_webhook", new_callable=AsyncMock)
async def test_send_failure_alert_includes_issue_url(mock_post, sample_error_report):
    await send_failure_alert(sample_error_report, "AI 실패", "https://github.com/owner/repo/issues/1")
    payload = mock_post.call_args[0][0]
    embed = payload["embeds"][0]
    assert any(f["name"] == "Issue" for f in embed["fields"])


def _field_map(embed: dict) -> dict[str, str]:
    return {field["name"]: field["value"] for field in embed["fields"]}


@patch("app.services.discord_service._post_webhook", new_callable=AsyncMock)
async def test_send_error_alert_sanitizes_report_fields(mock_post):
    report = ErrorReport(
        errorType="AuthError user@example.com",
        errorMessage="Authorization: Bearer secret-token",
        stackTrace="trace",
        requestUrl="GET /api?token=ya29.secret",
        timestamp="2026-04-17T10:00:00Z",
    )

    await send_error_alert(report)

    embed = mock_post.call_args[0][0]["embeds"][0]
    fields = _field_map(embed)
    assert "user@example.com" not in fields["에러 타입"]
    assert "secret-token" not in fields["메시지"]
    assert "ya29.secret" not in fields["요청"]


@patch("app.services.discord_service._post_webhook", new_callable=AsyncMock)
async def test_send_failure_alert_sanitizes_report_and_reason(mock_post):
    report = ErrorReport(
        errorType="CookieError",
        errorMessage="Cookie: session=secret",
        stackTrace="trace",
        requestUrl="GET /api?email=dev@example.com",
        timestamp="2026-04-17T10:00:00Z",
    )

    await send_failure_alert(report, "Bearer secret-token failed")

    embed = mock_post.call_args[0][0]["embeds"][0]
    fields = _field_map(embed)
    assert "session=secret" not in fields["메시지"]
    assert "dev@example.com" not in fields["요청"]
    assert "secret-token" not in fields["실패 사유"]
