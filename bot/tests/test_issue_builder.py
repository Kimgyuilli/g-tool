from app.services.issue_builder import (
    FailureStage,
    build_dedup_key,
    build_issue_payload,
    get_issue_labels,
)


def test_build_dedup_key_is_stable(sample_error_report):
    key1 = build_dedup_key(
        sample_error_report.errorType,
        sample_error_report.errorMessage,
        FailureStage.AI_ANALYSIS_FAILED,
    )
    key2 = build_dedup_key(
        sample_error_report.errorType,
        sample_error_report.errorMessage,
        FailureStage.AI_ANALYSIS_FAILED,
    )
    assert key1 == key2
    assert len(key1) == 10


def test_build_issue_payload_contains_sanitized_reason(sample_error_report):
    payload = build_issue_payload(
        sample_error_report,
        FailureStage.PULL_REQUEST_FAILED,
        "Authorization: Bearer secret-token",
    )

    assert payload["stage"] == FailureStage.PULL_REQUEST_FAILED
    assert "secret-token" not in payload["body"]
    assert "[REDACTED_TOKEN]" in payload["body"]
    assert payload["title"].startswith(f"[{payload['dedup_key']}]")


def test_build_issue_payload_force_fallback(sample_error_report):
    payload = build_issue_payload(
        sample_error_report,
        FailureStage.PIPELINE_INTERNAL_ERROR,
        "raw reason",
        force_fallback=True,
    )

    assert "unknown_stage" in payload["title"]
    assert "raw reason" not in payload["body"]


def test_get_issue_labels_always_contains_default():
    labels = get_issue_labels()
    assert "auto-fix-failed" in labels
