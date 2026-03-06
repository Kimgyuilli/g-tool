import asyncio
import hashlib
import logging
import time
from datetime import datetime, timezone
from functools import partial

from app.schemas import ErrorReport
from app.services.ai_service import analyze_error, validate_ai_result
from app.config import settings
from app.services.discord_service import send_error_alert, send_failure_alert, send_pr_alert
from app.services.github_service import create_pull_request, fetch_files
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

        # 3. 소스코드 조회 (동기 → run_in_executor)
        file_paths = [e["file"] for e in entries]
        loop = asyncio.get_running_loop()
        files = await loop.run_in_executor(None, partial(fetch_files, file_paths))
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
            new_files = await loop.run_in_executor(None, partial(fetch_files, new_paths))
            all_files.update(new_files)
        context_files = {k: v for k, v in all_files.items() if k not in error_files}

        # 4. AI API로 분석 (동기 → run_in_executor)
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

        # 4-1. AI 응답 검증
        known_files = set(error_files.keys()) | set(context_files.keys())
        validation_error = validate_ai_result(result, known_files)
        if validation_error:
            logger.warning("AI 응답 검증 실패: %s", validation_error)
            await send_failure_alert(report, f"AI 응답 검증 실패: {validation_error}")
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
        pr_body = build_pr_body(report, result, original_files={**error_files, **context_files})

        # 7. GitHub PR 생성 (동기 → run_in_executor)
        try:
            pr_url = await loop.run_in_executor(
                None,
                partial(
                    create_pull_request,
                    files=result["files"],
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
