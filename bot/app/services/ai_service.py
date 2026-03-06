import json
import logging
import os

from app.services.ai_provider import call_ai

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
너는 FastAPI + Next.js 풀스택 애플리케이션의 코드를 분석하고 수정하는 봇이다.
에러 정보와 소스코드를 받아서 수정안을 반환한다.
"에러 발생 소스 코드"는 스택트레이스에 직접 등장한 파일이고,
"관련 참고 코드"는 import로 연결된 참고용 파일이다. 참고 코드는 수정 맥락 파악용이다.

## 핵심 규칙
- 수정이 필요 없으면 should_fix를 false로 설정하라. 억지로 수정하지 마라.
- 환경 문제, 네트워크 문제, 외부 API 문제 등 코드 변경으로 해결할 수 없는 경우 should_fix를 false로 설정하라.
- changes의 original은 원본 소스 코드에서 변경할 부분을 **글자 하나 틀리지 않고 그대로** 복사하라. 공백, 들여쓰기, 줄바꿈까지 정확히 일치해야 한다.
- original과 modified가 동일하면 안 된다. 실제로 변경되는 부분만 포함하라.
- 기존 코드를 생략하거나 요약하지 마라.
- 파일 전체를 다시 작성하지 마라. 변경이 필요한 부분만 제공하라.
- FastAPI 컨벤션: HTTPException 사용, dict return 지양.
반드시 한국어로만 응답하라. 중국어, 일본어 등 다른 언어를 섞지 마라.
summary는 PR 제목으로 사용되므로 50자 이내의 간결한 한 줄로 작성하라."""

USER_PROMPT_TEMPLATE = """\
## 에러
- 타입: {error_type}
- 메시지: {error_message}

## 스택 트레이스
{stack_trace}

{source_code_section}

## 지시사항
1. 에러 원인을 분석하라
2. 수정이 필요 없으면 should_fix를 false로 설정하고 skip_reason에 이유를 적어라
3. 수정이 필요하면 changes에 변경할 부분의 original(변경 전)과 modified(변경 후)만 제공하라
4. 파일 전체를 다시 작성하지 마라. 변경이 필요한 최소 범위만 제공하라"""

RESPONSE_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "error_fix",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "should_fix": {"type": "boolean"},
                "skip_reason": {"type": ["string", "null"]},
                "analysis": {"type": "string"},
                "root_cause": {"type": "string"},
                "fix_description": {"type": "string"},
                "changes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"},
                            "original": {"type": "string"},
                            "modified": {"type": "string"},
                        },
                        "required": ["path", "original", "modified"],
                        "additionalProperties": False,
                    },
                },
                "summary": {"type": "string"},
            },
            "required": [
                "should_fix", "skip_reason", "analysis", "root_cause",
                "fix_description", "changes", "summary",
            ],
            "additionalProperties": False,
        },
    },
}


def _get_lang_tag(file_path: str) -> str:
    """파일 확장자에 따라 코드 블록 언어 태그를 반환."""
    ext = os.path.splitext(file_path)[1].lower()
    lang_map = {
        ".py": "python",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".js": "javascript",
        ".jsx": "javascript",
        ".json": "json",
        ".html": "html",
        ".css": "css",
        ".sql": "sql",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".toml": "toml",
    }
    return lang_map.get(ext, "")


def _build_source_section(
    error_files: dict[str, str], context_files: dict[str, str]
) -> str:
    parts = ["## 에러 발생 소스 코드 (스택트레이스에 포함된 파일)"]
    for path, content in error_files.items():
        lang = _get_lang_tag(path)
        parts.append(f"### {path}\n```{lang}\n{content}\n```")
    if context_files:
        parts.append("\n## 관련 참고 코드 (import된 프로젝트 내부 파일)")
        for path, content in context_files.items():
            lang = _get_lang_tag(path)
            parts.append(f"### {path}\n```{lang}\n{content}\n```")
    return "\n\n".join(parts)


def validate_ai_result(result: dict, known_files: set[str]) -> str | None:
    """AI 응답 검증. 문제 있으면 사유 문자열, 정상이면 None."""
    changes = result.get("changes")
    if not changes:
        return "수정 파일이 없음"
    for c in changes:
        if "path" not in c or "original" not in c or "modified" not in c:
            return "changes 항목에 path, original, 또는 modified 누락"
        if c["path"] not in known_files:
            return f"알 수 없는 파일 경로: {c['path']}"
        if not c["original"].strip():
            return f"빈 original 내용: {c['path']}"
        if not c["modified"].strip():
            return f"빈 modified 내용: {c['path']}"
    return None


def analyze_error(
    error_type: str,
    error_message: str,
    stack_trace: str,
    error_files: dict[str, str],
    context_files: dict[str, str] | None = None,
) -> dict | None:
    """AI API로 에러를 분석하고 수정안을 반환한다. 실패 시 None."""
    user_prompt = USER_PROMPT_TEMPLATE.format(
        error_type=error_type,
        error_message=error_message,
        stack_trace=stack_trace,
        source_code_section=_build_source_section(error_files, context_files or {}),
    )

    try:
        text = call_ai(SYSTEM_PROMPT, user_prompt, response_format=RESPONSE_SCHEMA)
        return json.loads(text)
    except Exception:
        logger.exception("AI API 호출 실패")
        return None
