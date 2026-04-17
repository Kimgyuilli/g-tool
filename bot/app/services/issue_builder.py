import hashlib
from enum import StrEnum

from app.config import settings
from app.schemas import ErrorReport
from app.services.sanitizer import SAFE_FALLBACK_TEXT, sanitize_excerpt, sanitize_text

DEFAULT_STAGE = "unknown_stage"


class FailureStage(StrEnum):
    STACK_TRACE_PARSE_FAILED = "stack_trace_parse_failed"
    SOURCE_FILE_READ_FAILED = "source_file_read_failed"
    AI_ANALYSIS_FAILED = "ai_analysis_failed"
    FIX_SKIPPED = "fix_skipped"
    AI_VALIDATION_FAILED = "ai_validation_failed"
    DIFF_APPLY_FAILED = "diff_apply_failed"
    CHANGE_VALIDATION_FAILED = "change_validation_failed"
    PULL_REQUEST_FAILED = "pull_request_failed"
    PIPELINE_INTERNAL_ERROR = "pipeline_internal_error"


ISSUE_ELIGIBLE_STAGES = {
    FailureStage.AI_ANALYSIS_FAILED,
    FailureStage.FIX_SKIPPED,
    FailureStage.AI_VALIDATION_FAILED,
    FailureStage.DIFF_APPLY_FAILED,
    FailureStage.CHANGE_VALIDATION_FAILED,
    FailureStage.PULL_REQUEST_FAILED,
    FailureStage.PIPELINE_INTERNAL_ERROR,
}


def build_dedup_key(error_type: str, error_message: str, stage: str | FailureStage) -> str:
    return hashlib.sha256(f"{error_type}{error_message}{stage}".encode()).hexdigest()[:10]


def get_issue_labels() -> list[str]:
    labels = [label.strip() for label in settings.issue_labels.split(",") if label.strip()]
    if "auto-fix-failed" not in labels:
        labels.insert(0, "auto-fix-failed")
    return labels


def build_issue_payload(
    report: ErrorReport,
    stage: FailureStage,
    reason: str,
    *,
    force_fallback: bool = False,
) -> dict:
    dedup_key = build_dedup_key(report.errorType, report.errorMessage, stage)
    short_error_type = sanitize_excerpt(report.errorType, limit=80)
    safe_stage = stage.value

    if force_fallback:
        title = f"[{dedup_key}] {DEFAULT_STAGE} - pipeline internal error"
        body = "\n".join(
            [
                "## Auto-Fix Failure Report",
                "",
                f"- Stage: {DEFAULT_STAGE}",
                f"- Error Type: {SAFE_FALLBACK_TEXT}",
                f"- Request: {SAFE_FALLBACK_TEXT}",
                f"- Timestamp: {sanitize_excerpt(report.timestamp, limit=120)}",
                f"- Reason: {SAFE_FALLBACK_TEXT}",
                "",
                "Sanitized payload generation fell back to the minimum safe format.",
            ]
        )
    else:
        title = f"[{dedup_key}] {safe_stage} - {short_error_type}"
        body = "\n".join(
            [
                "## Auto-Fix Failure Report",
                "",
                f"- Stage: {safe_stage}",
                f"- Error Type: {sanitize_excerpt(report.errorType, limit=120)}",
                f"- Request: {sanitize_excerpt(report.requestUrl, limit=300)}",
                f"- Timestamp: {sanitize_excerpt(report.timestamp, limit=120)}",
                "",
                "### Reason",
                sanitize_excerpt(reason, limit=1000),
                "",
                "### Error Message",
                sanitize_excerpt(report.errorMessage, limit=1000),
                "",
                "### Stack Trace Excerpt",
                "```",
                sanitize_excerpt(report.stackTrace, limit=2000),
                "```",
                "",
                "### Next Action",
                "- Review the sanitized failure reason and stack trace excerpt.",
                "- Check whether this issue matches an existing deployment or environment problem.",
                "- Close automatically once the auto-fix pipeline succeeds again.",
            ]
        )

    return {
        "stage": safe_stage,
        "dedup_key": dedup_key,
        "title": title,
        "body": body,
        "labels": get_issue_labels(),
        "issue_enabled": settings.issue_enabled,
        "comment": (
            f"Reproduced at {sanitize_excerpt(report.timestamp, limit=120)}\n\n"
            f"Reason: {sanitize_excerpt(reason, limit=600)}"
        ),
    }


def sanitize_failure_reason(reason: str) -> str:
    return sanitize_text(reason)
