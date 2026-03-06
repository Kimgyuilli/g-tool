from unittest.mock import patch

from app.pipeline import apply_changes, process_error, validate_changes
from app.schemas import ErrorReport
from app.services.ai_service import validate_ai_result
from app.services.pr_builder import build_diff


FILE_PATH = "backend/app/mail/services/gmail.py"
ORIGINAL_CODE = "def sync_gmail(user):\n    user_id = current_user.id\n    return user_id\n"
FIXED_CODE = "def sync_gmail(user):\n    if current_user is None:\n        raise ValueError('user is None')\n    user_id = current_user.id\n    return user_id\n"


def _make_ai_result(
    should_fix=True,
    skip_reason=None,
    changes=None,
    summary="AttributeError 수정",
):
    if changes is None:
        changes = [{
            "path": FILE_PATH,
            "original": "    user_id = current_user.id\n",
            "modified": "    if current_user is None:\n        raise ValueError('user is None')\n    user_id = current_user.id\n",
        }]
    return {
        "should_fix": should_fix,
        "skip_reason": skip_reason,
        "analysis": "AttributeError 원인 분석",
        "root_cause": "null 체크 누락",
        "fix_description": "null 체크 추가",
        "changes": changes,
        "summary": summary,
    }


# --- apply_changes ---


def test_apply_changes_success():
    original = {FILE_PATH: ORIGINAL_CODE}
    changes = [{
        "path": FILE_PATH,
        "original": "    user_id = current_user.id\n",
        "modified": "    if current_user is None:\n        raise ValueError('user is None')\n    user_id = current_user.id\n",
    }]
    result = apply_changes(original, changes)
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["path"] == FILE_PATH
    assert "if current_user is None" in result[0]["content"]
    assert "def sync_gmail" in result[0]["content"]  # 기존 코드 보존


def test_apply_changes_original_not_found():
    original = {FILE_PATH: ORIGINAL_CODE}
    changes = [{
        "path": FILE_PATH,
        "original": "this does not exist in original",
        "modified": "something",
    }]
    result = apply_changes(original, changes)
    assert isinstance(result, str)
    assert "찾을 수 없음" in result


def test_apply_changes_file_not_found():
    original = {FILE_PATH: ORIGINAL_CODE}
    changes = [{"path": "nonexistent.py", "original": "x", "modified": "y"}]
    result = apply_changes(original, changes)
    assert isinstance(result, str)
    assert "원본 파일" in result


def test_apply_changes_multiple_changes_same_file():
    original = {"a.py": "line1\nline2\nline3\n"}
    changes = [
        {"path": "a.py", "original": "line1", "modified": "LINE1"},
        {"path": "a.py", "original": "line3", "modified": "LINE3"},
    ]
    result = apply_changes(original, changes)
    assert isinstance(result, list)
    assert "LINE1" in result[0]["content"]
    assert "LINE3" in result[0]["content"]
    assert "line2" in result[0]["content"]  # 변경되지 않은 줄 보존


# --- validate_changes ---


def test_validate_changes_ok():
    original = {FILE_PATH: ORIGINAL_CODE}
    applied = [{"path": FILE_PATH, "content": FIXED_CODE}]
    assert validate_changes(original, applied) is None


def test_validate_changes_excessive_deletion():
    original = {"a.py": "\n".join(f"line{i}" for i in range(100)) + "\n"}
    # 100줄 → 10줄 (90줄 삭제, 50% 이상)
    applied = [{"path": "a.py", "content": "\n".join(f"line{i}" for i in range(10)) + "\n"}]
    result = validate_changes(original, applied)
    assert result is not None
    assert "50%" in result


def test_validate_changes_delete_more_than_3x_add():
    original = {"a.py": "\n".join(f"line{i}" for i in range(40)) + "\n"}
    # 40줄 → 19줄: 삭제 21, 50% 이상(21/40=52.5%) → 차단
    applied = [{"path": "a.py", "content": "\n".join(f"line{i}" for i in range(19)) + "\n"}]
    result = validate_changes(original, applied)
    assert result is not None
    assert "50%" in result


# --- validate_ai_result ---


def test_validate_ai_result_no_changes():
    assert validate_ai_result({"changes": []}, {"a.py"}) == "수정 파일이 없음"


def test_validate_ai_result_missing_fields():
    result = {"changes": [{"path": "a.py", "original": "code"}]}
    assert validate_ai_result(result, {"a.py"}) is not None


def test_validate_ai_result_unknown_path():
    result = {"changes": [{"path": "x.py", "original": "old", "modified": "new"}]}
    assert validate_ai_result(result, {"a.py"}) is not None


def test_validate_ai_result_empty_original():
    result = {"changes": [{"path": "a.py", "original": "  ", "modified": "new"}]}
    assert validate_ai_result(result, {"a.py"}) is not None


def test_validate_ai_result_empty_modified():
    result = {"changes": [{"path": "a.py", "original": "old", "modified": "  "}]}
    assert validate_ai_result(result, {"a.py"}) is not None


def test_validate_ai_result_valid():
    result = {"changes": [{"path": "a.py", "original": "old", "modified": "new"}]}
    assert validate_ai_result(result, {"a.py"}) is None


# --- process_error full flow ---


async def test_process_error_full_flow(sample_error_report, mock_discord):
    ai_result = _make_ai_result()
    with (
        patch("app.pipeline.read_files", return_value={FILE_PATH: ORIGINAL_CODE}),
        patch("app.pipeline.analyze_error", return_value=ai_result),
        patch("app.pipeline.create_pull_request", return_value="https://github.com/pr/1"),
    ):
        await process_error(sample_error_report)

    mock_discord["error"].assert_awaited_once()
    mock_discord["pr"].assert_awaited_once()
    mock_discord["failure"].assert_not_awaited()


async def test_process_error_skips_duplicate(sample_error_report, mock_discord):
    ai_result = _make_ai_result()
    with (
        patch("app.pipeline.read_files", return_value={FILE_PATH: ORIGINAL_CODE}),
        patch("app.pipeline.analyze_error", return_value=ai_result),
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
        patch("app.pipeline.read_files", return_value={FILE_PATH: "code"}),
        patch("app.pipeline.analyze_error", return_value=None),
    ):
        await process_error(sample_error_report)

    mock_discord["failure"].assert_awaited_once()


async def test_process_error_should_fix_false_skips_pr(sample_error_report, mock_discord):
    ai_result = _make_ai_result(should_fix=False, skip_reason="환경 설정 문제", changes=[])
    with (
        patch("app.pipeline.read_files", return_value={FILE_PATH: "code"}),
        patch("app.pipeline.analyze_error", return_value=ai_result),
        patch("app.pipeline.create_pull_request") as mock_pr,
    ):
        await process_error(sample_error_report)

    mock_pr.assert_not_called()
    mock_discord["failure"].assert_awaited_once()


async def test_process_error_ai_validation_failure_sends_failure_alert(sample_error_report, mock_discord):
    ai_result = _make_ai_result(changes=[
        {"path": "unknown/path.py", "original": "old", "modified": "new"},
    ])
    with (
        patch("app.pipeline.read_files", return_value={FILE_PATH: "code"}),
        patch("app.pipeline.analyze_error", return_value=ai_result),
        patch("app.pipeline.create_pull_request", return_value="url") as mock_pr,
    ):
        await process_error(sample_error_report)

    mock_pr.assert_not_called()
    mock_discord["failure"].assert_awaited_once()


async def test_process_error_diff_apply_failure(sample_error_report, mock_discord):
    ai_result = _make_ai_result(changes=[
        {"path": FILE_PATH, "original": "nonexistent code block", "modified": "fix"},
    ])
    with (
        patch("app.pipeline.read_files", return_value={FILE_PATH: ORIGINAL_CODE}),
        patch("app.pipeline.analyze_error", return_value=ai_result),
        patch("app.pipeline.create_pull_request") as mock_pr,
    ):
        await process_error(sample_error_report)

    mock_pr.assert_not_called()
    mock_discord["failure"].assert_awaited_once()


async def test_process_error_pr_failure_sends_failure_alert(sample_error_report, mock_discord):
    ai_result = _make_ai_result()
    with (
        patch("app.pipeline.read_files", return_value={FILE_PATH: ORIGINAL_CODE}),
        patch("app.pipeline.analyze_error", return_value=ai_result),
        patch("app.pipeline.create_pull_request", side_effect=RuntimeError("fail")),
    ):
        await process_error(sample_error_report)

    mock_discord["failure"].assert_awaited_once()


# --- build_diff ---


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
    ai_result = _make_ai_result()
    with (
        patch("app.pipeline.read_files", return_value={FILE_PATH: ORIGINAL_CODE}),
        patch("app.pipeline.analyze_error", return_value=ai_result),
        patch("app.pipeline.create_pull_request", return_value="https://github.com/pr/1") as mock_pr,
    ):
        await process_error(sample_error_report)

    pr_body = mock_pr.call_args.kwargs["pr_body"]
    assert "### 변경 diff" in pr_body
    assert "```diff" in pr_body


async def test_pr_body_contains_new_sections(sample_error_report, mock_discord):
    ai_result = _make_ai_result()
    with (
        patch("app.pipeline.read_files", return_value={FILE_PATH: ORIGINAL_CODE}),
        patch("app.pipeline.analyze_error", return_value=ai_result),
        patch("app.pipeline.create_pull_request", return_value="https://github.com/pr/1") as mock_pr,
    ):
        await process_error(sample_error_report)

    pr_body = mock_pr.call_args.kwargs["pr_body"]
    assert "### 근본 원인" in pr_body
    assert "null 체크 누락" in pr_body
    assert "### 수정 내용" in pr_body
    assert "null 체크 추가" in pr_body
    assert "### 수정된 파일" in pr_body
    assert f"`{FILE_PATH}`" in pr_body
