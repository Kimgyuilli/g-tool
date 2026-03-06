import json
from unittest.mock import patch

from app.services.ai_service import analyze_error


def test_analyze_error_returns_parsed_response():
    expected = {
        "should_fix": True,
        "skip_reason": None,
        "analysis": "원인",
        "root_cause": "null 체크 누락",
        "fix_description": "null 체크 추가",
        "changes": [
            {"path": "a.py", "original": "old code", "modified": "new code"},
        ],
        "summary": "수정",
    }

    with patch("app.services.ai_service.call_ai", return_value=json.dumps(expected)):
        result = analyze_error(
            "NPE", "msg", "trace",
            error_files={"a.py": "code"},
            context_files={"b.py": "ref code"},
        )

    assert result == expected


def test_analyze_error_returns_none_on_api_exception():
    with patch("app.services.ai_service.call_ai", side_effect=RuntimeError("API down")):
        result = analyze_error("NPE", "msg", "trace", error_files={"a.py": "code"})

    assert result is None


def test_analyze_error_should_fix_false():
    expected = {
        "should_fix": False,
        "skip_reason": "환경 설정 문제로 코드 수정 불필요",
        "analysis": "분석",
        "root_cause": "원인",
        "fix_description": "",
        "changes": [],
        "summary": "",
    }

    with patch("app.services.ai_service.call_ai", return_value=json.dumps(expected)):
        result = analyze_error("RuntimeError", "msg", "trace", error_files={"a.py": "code"})

    assert result is not None
    assert result["should_fix"] is False
    assert result["skip_reason"] == "환경 설정 문제로 코드 수정 불필요"
