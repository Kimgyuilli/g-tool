from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from googleapiclient.errors import HttpError

from app.auth.dependencies import get_google_user
from app.calendar.schemas import CreateEventRequest
from app.calendar.service import (
    create_event,
    delete_event,
    get_event,
    list_calendars,
    list_events,
)
from app.mail.models import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/calendar", tags=["calendar"])


@router.get("/calendars")
async def get_calendars(
    user_credentials: tuple[User, object] = Depends(get_google_user),
):
    """사용자의 Google Calendar 목록 조회."""
    _user, credentials = user_credentials
    try:
        calendars = await list_calendars(credentials)
    except HttpError as exc:
        logger.warning(f"Google Calendar API 에러: {exc}")
        raise HTTPException(status_code=exc.resp.status, detail=str(exc)) from exc
    return {"calendars": calendars}


@router.get("/events")
async def get_events(
    calendar_id: str = Query(default="primary"),
    time_min: str | None = Query(default=None),
    time_max: str | None = Query(default=None),
    max_results: int = Query(default=250, le=2500),
    user_credentials: tuple[User, object] = Depends(get_google_user),
):
    """캘린더 이벤트 목록 조회."""
    _user, credentials = user_credentials
    try:
        events = await list_events(
            credentials, calendar_id, time_min, time_max, max_results
        )
    except HttpError as exc:
        logger.warning(f"Google Calendar API 에러: {exc}")
        raise HTTPException(status_code=exc.resp.status, detail=str(exc)) from exc
    return {"events": events, "calendar_id": calendar_id}


@router.get("/events/{event_id}")
async def get_event_detail(
    event_id: str,
    calendar_id: str = Query(default="primary"),
    user_credentials: tuple[User, object] = Depends(get_google_user),
):
    """단일 이벤트 상세 조회."""
    _user, credentials = user_credentials
    try:
        event = await get_event(credentials, calendar_id, event_id)
    except HttpError as exc:
        logger.warning(f"Google Calendar API 에러: {exc}")
        raise HTTPException(status_code=exc.resp.status, detail=str(exc)) from exc
    return event


@router.post("/events")
async def create_new_event(
    req: CreateEventRequest,
    user_credentials: tuple[User, object] = Depends(get_google_user),
):
    """Google Calendar에 새 이벤트 생성."""
    _user, credentials = user_credentials
    try:
        event = await create_event(
            credentials,
            calendar_id=req.calendar_id,
            summary=req.summary,
            start=req.start,
            end=req.end,
            all_day=req.all_day,
            description=req.description,
            location=req.location,
        )
    except HttpError as exc:
        logger.warning(f"Google Calendar API 에러: {exc}")
        raise HTTPException(status_code=exc.resp.status, detail=str(exc)) from exc
    return event


@router.delete("/events/{event_id}")
async def delete_existing_event(
    event_id: str,
    calendar_id: str = Query(default="primary"),
    user_credentials: tuple[User, object] = Depends(get_google_user),
):
    """Google Calendar에서 이벤트 삭제."""
    _user, credentials = user_credentials
    try:
        await delete_event(credentials, calendar_id, event_id)
    except HttpError as exc:
        logger.warning(f"Google Calendar API 에러: {exc}")
        raise HTTPException(status_code=exc.resp.status, detail=str(exc)) from exc
    return {"ok": True}
