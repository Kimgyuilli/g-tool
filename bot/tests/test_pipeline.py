from unittest.mock import AsyncMock, patch

import pytest

from app.pipeline import process_error
from app.schemas import ErrorReport
from app.services.ai_service import validate_ai_result
from app.services.pr_builder import build_diff


FILE_PATH = "backend/app/mail/services/gmail.py"


async def test_process_error_full_flow(sample_error_report, mock_discord):
    ai_result = {
        "analysis": "AttributeError 원인 분석",
        "root_cause": "null 체크 누락",
        "fix_description": "null 체크 추가",
        "files": [{"path": FILE_PATH, "content": "fixed"}],
        "summary": "AttributeError 수정",
    }
    with (
        patch("app.pipeline.fetch_files", return_value={FILE_PATH: "code"}),
        patch("app.pipeline.analyze_error", return_value=ai_result),
        patch("app.pipeline.create_pull_request", return_value="https://github.com/pr/1"),
    ):
        await process_error(sample_error_report)

    mock_discord["error"].assert_awaited_once()
    mock_discord["pr"].assert_awaited_once()
    mock_discord["failure"].assert_not_awaited()


async def test_process_error_skips_duplicate(sample_error_report, mock_discord):
    with (
        patch("app.pipeline.fetch_files", return_value={FILE_PATH: "code"}),
        patch("app.pipeline.analyze_error", return_value={"analysis": "", "root_cause": "", "fix_description": "", "files": [], "summary": "s"}),
        patch("app.pipeline.create_pull_request", return_value="url"),
    ):
        await process_error(sample_error_report)
        await process_error(sample_error_report)  # 두 번째는 중복

    # send_error_alert는 1번만 호출
    assert mock_discord["error"].await_count == 1


async def test_process_error_no_stack_entries(mock_discord):
    report = ErrorReport(
        errorType="RuntimeError",
        errorMessage="error",
        stackTrace='  File "/usr/lib/python3.12/asyncio/runners.py", line 194, in run\n',
        requestUrl="GET /api",
        timestamp="2026-01-01T00:00:00Z",
    )
    await process_error(report)

    mock_discord["error"].assert_awaited_once()
    mock_discord["pr"].assert_not_awaited()


async def test_process_error_ai_failure_sends_failure_alert(sample_error_report, mock_discord):
    with (
        patch("app.pipeline.fetch_files", return_value={FILE_PATH: "code"}),
        patch("app.pipeline.analyze_error", return_value=None),
    ):
        await process_error(sample_error_report)

    mock_discord["failure"].assert_awaited_once()


async def test_process_error_ai_validation_failure_sends_failure_alert(sample_error_report, mock_discord):
    ai_result = {
        "analysis": "분석",
        "root_cause": "원인",
        "fix_description": "수정",
        "files": [{"path": "unknown/path.py", "content": "code"}],
        "summary": "수정",
    }
    with (
        patch("app.pipeline.fetch_files", return_value={FILE_PATH: "code"}),
        patch("app.pipeline.analyze_error", return_value=ai_result),
        patch("app.pipeline.create_pull_request", return_value="url") as mock_pr,
    ):
        await process_error(sample_error_report)

    mock_pr.assert_not_called()
    mock_discord["failure"].assert_awaited_once()


def test_validate_ai_result_no_files():
    assert validate_ai_result({"files": []}, {"a.py"}) == "수정 파일이 없음"


def test_validate_ai_result_missing_path():
    result = {"files": [{"content": "code"}]}
    assert validate_ai_result(result, {"a.py"}) is not None


def test_validate_ai_result_unknown_path():
    result = {"files": [{"path": "x.py", "content": "code"}]}
    assert validate_ai_result(result, {"a.py"}) is not None


def test_validate_ai_result_empty_content():
    result = {"files": [{"path": "a.py", "content": "  "}]}
    assert validate_ai_result(result, {"a.py"}) is not None


def test_validate_ai_result_valid():
    result = {"files": [{"path": "a.py", "content": "code"}]}
    assert validate_ai_result(result, {"a.py"}) is None


def test_build_diff_shows_changes():
    original = {"a.py": "line1\nline2\n"}
    modified = [{"path": "a.py", "content": "line1\nline2_modified\n"}]
    diff = build_diff(original, modified)
    assert "```diff" in diff
    assert "a.py" in diff


def test_build_diff_no_changes():
    original = {"a.py": "same\n"}
    modified = [{"path": "a.py", "content": "same\n"}]
    assert build_diff(original, modified) == "변경 없음"


async def test_pr_body_contains_diff_section(sample_error_report, mock_discord):
    ai_result = {
        "analysis": "분석",
        "root_cause": "원인",
        "fix_description": "수정",
        "files": [{"path": FILE_PATH, "content": "fixed_code"}],
        "summary": "수정",
    }
    with (
        patch("app.pipeline.fetch_files", return_value={FILE_PATH: "original_code"}),
        patch("app.pipeline.analyze_error", return_value=ai_result),
        patch("app.pipeline.create_pull_request", return_value="https://github.com/pr/1") as mock_pr,
    ):
        await process_error(sample_error_report)

    pr_body = mock_pr.call_args.kwargs["pr_body"]
    assert "### 변경 diff" in pr_body
    assert "```diff" in pr_body


async def test_pr_body_contains_new_sections(sample_error_report, mock_discord):
    ai_result = {
        "analysis": "AttributeError 원인 분석",
        "root_cause": "null 체크 누락",
        "fix_description": "gmail_service에 null 체크 추가",
        "files": [{"path": FILE_PATH, "content": "fixed"}],
        "summary": "AttributeError 수정",
    }
    with (
        patch("app.pipeline.fetch_files", return_value={FILE_PATH: "code"}),
        patch("app.pipeline.analyze_error", return_value=ai_result),
        patch("app.pipeline.create_pull_request", return_value="https://github.com/pr/1") as mock_pr,
    ):
        await process_error(sample_error_report)

    pr_body = mock_pr.call_args.kwargs["pr_body"]
    assert "### 근본 원인" in pr_body
    assert "null 체크 누락" in pr_body
    assert "### 수정 내용" in pr_body
    assert "gmail_service에 null 체크 추가" in pr_body
    assert "### 수정된 파일" in pr_body
    assert f"`{FILE_PATH}`" in pr_body


async def test_process_error_pr_failure_sends_failure_alert(sample_error_report, mock_discord):
    ai_result = {
        "analysis": "분석",
        "root_cause": "원인",
        "fix_description": "수정 설명",
        "files": [{"path": FILE_PATH, "content": "fixed"}],
        "summary": "수정",
    }
    with (
        patch("app.pipeline.fetch_files", return_value={FILE_PATH: "code"}),
        patch("app.pipeline.analyze_error", return_value=ai_result),
        patch("app.pipeline.create_pull_request", side_effect=RuntimeError("fail")),
    ):
        await process_error(sample_error_report)

    mock_discord["failure"].assert_awaited_once()
