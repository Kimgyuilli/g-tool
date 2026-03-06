import asyncio
import hashlib
import logging
import time
from datetime import datetime, timezone
from functools import partial

from app.config import settings
from app.schemas import ErrorReport
from app.services.ai_service import analyze_error, validate_ai_result
from app.services.discord_service import send_error_alert, send_failure_alert, send_pr_alert
from app.services.file_reader import read_files
from app.services.github_service import create_pull_request
from app.services.pr_builder import build_pr_body
from app.utils.stack_trace_parser import extract_related_imports, parse_stack_trace

logger = logging.getLogger(__name__)

# 중복 에러 필터링
_recent_errors: dict[str, float] = {}  # {dedup_key: timestamp}
DEDUP_TTL = 1800  # 30분


def _is_duplicate(report: "ErrorReport") -> bool:
    key = hashlib.sha256(
        f"{report.errorType}{report.errorMessage}{report.stackTrace[:200]}".encode()
    ).hexdigest()
    now = time.time()
    # 만료된 항목 정리
    expired = [k for k, t in _recent_errors.items() if now - t > DEDUP_TTL]
    for k in expired:
        del _recent_errors[k]
    # 중복 체크
    if key in _recent_errors:
        return True
    _recent_errors[key] = now
    return False


def apply_changes(original_files: dict[str, str], changes: list[dict]) -> list[dict] | str:
    """changes의 original→modified를 원본에 적용.
    성공 시 [{"path": ..., "content": ...}] 반환.
    실패 시 에러 문자열 반환.
    """
    result = []
    # 파일별로 changes를 그룹화
    file_changes: dict[str, list[dict]] = {}
    for c in changes:
        file_changes.setdefault(c["path"], []).append(c)

    for path, path_changes in file_changes.items():
        if path not in original_files:
            return f"원본 파일을 찾을 수 없음: {path}"
        content = original_files[path]
        for c in path_changes:
            if c["original"] not in content:
                return f"original 블록을 원본에서 찾을 수 없음: {path}"
            content = content.replace(c["original"], c["modified"], 1)
        result.append({"path": path, "content": content})

    return result


def validate_changes(
    original_files: dict[str, str], applied_files: list[dict]
) -> str | None:
    """적용된 변경이 안전한지 검증. 문제 있으면 사유 문자열, 정상이면 None."""
    for f in applied_files:
        original = original_files.get(f["path"], "")
        original_lines = original.splitlines()
        new_lines = f["content"].splitlines()

        original_count = len(original_lines)
        new_count = len(new_lines)

        if original_count == 0:
            continue

        deleted = max(0, original_count - new_count)
        added = max(0, new_count - original_count)

        # 삭제 줄 > 추가 줄 × 3 → 차단
        if added > 0 and deleted > added * 3:
            return f"과도한 삭제: {f['path']} (삭제 {deleted}줄 > 추가 {added}줄 × 3)"
        # 원본 대비 50% 이상 삭제 → 차단
        if deleted > original_count * 0.5:
            return f"원본의 50% 이상 삭제: {f['path']} (삭제 {deleted}/{original_count}줄)"

    return None


async def process_error(report: ErrorReport) -> None:
    try:
        # 0. 중복 에러 필터링
        if _is_duplicate(report):
            logger.info("중복 에러 무시: %s", report.errorType)
            return

        # 1. Discord 에러 알림
        await send_error_alert(report)

        # 2. 스택트레이스 파싱
        entries = parse_stack_trace(report.stackTrace, settings.project_root)
        if not entries:
            logger.warning("스택트레이스에서 프로젝트 코드를 찾지 못함")
            return

        # 3. 소스코드 조회 (로컬 파일 읽기 — 빠르므로 executor 불필요)
        file_paths = [e["file"] for e in entries]
        files = read_files(file_paths)
        if not files:
            logger.warning("파일을 조회하지 못함: %s", file_paths)
            return

        # 3-1. import 기반 관련 파일 추가 fetch (N depth)
        error_files = dict(files)
        all_files = dict(files)
        for _ in range(settings.import_depth):
            new_paths = []
            for source_code in all_files.values():
                new_paths.extend(
                    extract_related_imports(source_code, settings.project_root, set(all_files.keys()))
                )
            new_paths = list(dict.fromkeys(p for p in new_paths if p not in all_files))
            if not new_paths:
                break
            all_files.update(read_files(new_paths))
        context_files = {k: v for k, v in all_files.items() if k not in error_files}

        # 4. AI API로 분석 (네트워크 호출 — executor 사용)
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None,
            partial(
                analyze_error,
                error_type=report.errorType,
                error_message=report.errorMessage,
                stack_trace=report.stackTrace,
                error_files=error_files,
                context_files=context_files,
            ),
        )
        if not result:
            logger.warning("AI 분석 결과 없음")
            await send_failure_alert(report, "AI 분석 실패")
            return

        # 4-1. should_fix 체크 — 수정 불필요 시 분석 결과만 알리고 종료
        if not result.get("should_fix", True):
            skip_reason = result.get("skip_reason", "수정 불필요")
            logger.info("AI 판단: 수정 불필요 — %s", skip_reason)
            await send_failure_alert(report, f"수정 불필요: {skip_reason}")
            return

        # 4-2. no-op 변경 필터링 (original == modified)
        result["changes"] = [
            c for c in result.get("changes", [])
            if c.get("original") != c.get("modified")
        ]

        # 4-3. AI 응답 검증
        known_files = set(error_files.keys()) | set(context_files.keys())
        validation_error = validate_ai_result(result, known_files)
        if validation_error:
            logger.warning("AI 응답 검증 실패: %s", validation_error)
            await send_failure_alert(report, f"AI 응답 검증 실패: {validation_error}")
            return

        # 4-4. diff 적용 (original → modified 치환)
        applied = apply_changes(all_files, result["changes"])
        if isinstance(applied, str):
            logger.warning("diff 적용 실패: %s", applied)
            await send_failure_alert(report, f"diff 적용 실패: {applied}")
            return

        # 4-5. 변경 안전성 검증
        change_error = validate_changes(all_files, applied)
        if change_error:
            logger.warning("변경 검증 실패: %s", change_error)
            await send_failure_alert(report, f"변경 검증 실패: {change_error}")
            return

        summary = result.get("summary", "에러 자동 수정")
        logger.info("분석 완료: %s", summary)

        # 5. 브랜치명 생성
        error_id = hashlib.sha256(
            f"{report.errorType}{report.errorMessage}".encode()
        ).hexdigest()[:7]
        ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        branch_name = f"fix/error-{error_id}-{ts}"

        # 6. PR 본문 생성
        pr_body = build_pr_body(report, result, original_files=all_files)

        # 7. GitHub PR 생성 (네트워크 호출 — executor 사용)
        try:
            pr_url = await loop.run_in_executor(
                None,
                partial(
                    create_pull_request,
                    files=applied,
                    summary=summary,
                    pr_body=pr_body,
                    branch_name=branch_name,
                ),
            )
        except Exception as e:
            logger.exception("PR 생성 실패")
            await send_failure_alert(report, f"PR 생성 실패: {e}")
            return

        logger.info("PR 생성 완료: %s", pr_url)

        # 8. Discord PR 완료 알림
        await send_pr_alert(pr_url, summary)

    except Exception:
        logger.exception("에러 처리 중 실패")
