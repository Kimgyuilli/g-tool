import difflib

from app.schemas import ErrorReport

PR_BODY_TEMPLATE = """\
## 자동 생성된 에러 수정 PR

### 에러 정보
| 항목 | 내용 |
|------|------|
| 타입 | `{error_type}` |
| 메시지 | {error_message} |
| 요청 | {request_url} |
| 발생 시간 | {timestamp} |

### 근본 원인
{root_cause}

### AI 분석
{analysis}

### 수정 내용
{fix_description}

### 수정된 파일
{changed_files}

### 변경 diff
{diff_section}

---
> 이 PR은 Error Bot이 자동으로 생성했습니다.
> 반드시 코드 리뷰 후 머지하세요."""


def build_diff(original_files: dict[str, str], modified_files: list[dict]) -> str:
    parts = []
    for f in modified_files:
        original = original_files.get(f["path"], "")
        diff = difflib.unified_diff(
            original.splitlines(keepends=True),
            f["content"].splitlines(keepends=True),
            fromfile=f"a/{f['path']}", tofile=f"b/{f['path']}",
        )
        diff_text = "".join(diff)
        if diff_text:
            parts.append(f"#### {f['path']}\n```diff\n{diff_text}```")
    return "\n\n".join(parts) or "변경 없음"


def build_pr_body(report: ErrorReport, result: dict, original_files: dict[str, str] | None = None) -> str:
    changes = result.get("changes", [])
    changed_files = "\n".join(
        f"- `{c['path']}`" for c in changes
    ) or "- 없음"

    # changes에서 original→modified를 적용한 최종 파일을 생성하여 diff 계산
    if original_files and changes:
        applied: dict[str, str] = {}
        for c in changes:
            path = c["path"]
            content = applied.get(path, original_files.get(path, ""))
            content = content.replace(c["original"], c["modified"], 1)
            applied[path] = content
        modified_files = [{"path": p, "content": ct} for p, ct in applied.items()]
    else:
        modified_files = []

    diff_section = build_diff(original_files or {}, modified_files)

    return PR_BODY_TEMPLATE.format(
        error_type=report.errorType,
        error_message=report.errorMessage,
        request_url=report.requestUrl,
        timestamp=report.timestamp,
        root_cause=result.get("root_cause", ""),
        analysis=result.get("analysis", ""),
        fix_description=result.get("fix_description", ""),
        changed_files=changed_files,
        diff_section=diff_section,
    )
