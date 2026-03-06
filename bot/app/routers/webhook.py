import asyncio
import logging
from datetime import datetime, timezone

from fastapi import APIRouter

from app.pipeline import process_error
from app.schemas import ErrorReport

logger = logging.getLogger(__name__)

router = APIRouter()


def _log_task_exception(task: asyncio.Task) -> None:
    if not task.cancelled() and task.exception():
        logger.error("백그라운드 태스크 실패", exc_info=task.exception())


@router.post("/webhook/error")
async def receive_error(report: ErrorReport):
    task = asyncio.create_task(process_error(report))
    task.add_done_callback(_log_task_exception)
    return {"status": "received"}


@router.post("/api/test-webhook")
async def test_webhook():
    now = datetime.now(timezone.utc)
    sample = ErrorReport(
        errorType="KeyError",
        errorMessage=f"'subject' (test-{now.strftime('%H%M%S')})",
        stackTrace=(
            'Traceback (most recent call last):\n'
            '  File "backend/app/mail/services/gmail.py", line 208, in _parse_message\n'
            '    "external_id": raw["id"],\n'
            'KeyError: \'id\'\n'
        ),
        requestUrl="GET /api/gmail/sync",
        timestamp=now.isoformat(),
    )
    task = asyncio.create_task(process_error(sample))
    task.add_done_callback(_log_task_exception)
    return {"status": "test sent"}
