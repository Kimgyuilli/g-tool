import logging
import traceback
from datetime import datetime, timezone

import httpx
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import (
    BaseHTTPMiddleware,
    RequestResponseEndpoint,
)

from app.config import settings

logger = logging.getLogger(__name__)


async def _send_to_error_bot(
    request: Request,
    error_type: str,
    error_message: str,
    stack_trace: str,
) -> None:
    """error-bot에 에러 리포트를 전송."""
    if not settings.error_bot_url:
        return

    payload = {
        "errorType": error_type,
        "errorMessage": error_message,
        "stackTrace": stack_trace,
        "requestUrl": f"{request.method} {request.url.path}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            url = f"{settings.error_bot_url}/webhook/error"
            await client.post(url, json=payload)
    except Exception:
        logger.warning("error-bot에 에러 리포트 전송 실패", exc_info=True)


class ErrorReporterMiddleware(BaseHTTPMiddleware):
    """미들웨어 밖으로 전파되는 unhandled exception을 error-bot에 전송."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        try:
            return await call_next(request)
        except Exception as exc:
            tb = traceback.format_exc()
            await _send_to_error_bot(
                request, type(exc).__name__, str(exc), tb
            )
            raise


def register_error_handlers(app: FastAPI) -> None:
    """HTTPException(500+) 스택트레이스를 캡처하는 handler 등록."""

    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request, exc: HTTPException
    ) -> JSONResponse:
        if exc.status_code >= 500 and exc.__traceback__:
            tb = "".join(
                traceback.format_exception(type(exc), exc, exc.__traceback__)
            )
            await _send_to_error_bot(
                request,
                error_type=type(exc).__name__,
                error_message=str(exc.detail),
                stack_trace=tb,
            )
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )
