from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.router import router as auth_router
from app.calendar.router import router as calendar_router
from app.config import settings
from app.core.background_sync import sync_all_users
from app.core.database import Base, engine
from app.mail.routers.classify import router as classify_router
from app.mail.routers.gmail import router as gmail_router
from app.mail.routers.inbox import router as inbox_router
from app.mail.routers.naver import router as naver_router
from app.todo.router import router as todo_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # DB 테이블 생성
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 스케줄러 시작
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        sync_all_users,
        "interval",
        minutes=settings.sync_interval_minutes,
        id="sync_all_users",
        name="전체 사용자 메일 동기화",
    )
    scheduler.start()
    logger.info(
        f"백그라운드 스케줄러 시작 (간격: {settings.sync_interval_minutes}분)"
    )

    yield

    # 스케줄러 종료
    scheduler.shutdown()
    logger.info("백그라운드 스케줄러 종료")


app = FastAPI(title="Mail Organizer", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router)
app.include_router(calendar_router)
app.include_router(classify_router)
app.include_router(gmail_router)
app.include_router(inbox_router)
app.include_router(naver_router)
app.include_router(todo_router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
