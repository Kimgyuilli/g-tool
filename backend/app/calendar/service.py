from __future__ import annotations

import asyncio
from typing import Any

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


def _build_calendar(credentials: Credentials):
    """Build Google Calendar API service client."""
    return build("calendar", "v3", credentials=credentials)


async def list_calendars(credentials: Credentials) -> list[dict[str, Any]]:
    """사용자의 캘린더 목록 조회."""
    service = _build_calendar(credentials)

    def _fetch():
        return service.calendarList().list().execute()

    result = await asyncio.to_thread(_fetch)
    return [
        {
            "id": cal["id"],
            "summary": cal.get("summary", ""),
            "background_color": cal.get("backgroundColor"),
            "foreground_color": cal.get("foregroundColor"),
            "primary": cal.get("primary", False),
            "selected": cal.get("selected", True),
        }
        for cal in result.get("items", [])
    ]


async def list_events(
    credentials: Credentials,
    calendar_id: str = "primary",
    time_min: str | None = None,
    time_max: str | None = None,
    max_results: int = 250,
) -> list[dict[str, Any]]:
    """이벤트 목록 조회. time_min/time_max는 RFC3339 형식."""
    service = _build_calendar(credentials)

    def _fetch():
        kwargs: dict[str, Any] = {
            "calendarId": calendar_id,
            "maxResults": max_results,
            "singleEvents": True,
            "orderBy": "startTime",
        }
        if time_min:
            kwargs["timeMin"] = time_min
        if time_max:
            kwargs["timeMax"] = time_max
        return service.events().list(**kwargs).execute()

    result = await asyncio.to_thread(_fetch)
    return [_parse_event(ev, calendar_id) for ev in result.get("items", [])]


async def get_event(
    credentials: Credentials,
    calendar_id: str,
    event_id: str,
) -> dict[str, Any]:
    """단일 이벤트 상세 조회."""
    service = _build_calendar(credentials)

    def _fetch():
        return (
            service.events()
            .get(calendarId=calendar_id, eventId=event_id)
            .execute()
        )

    raw = await asyncio.to_thread(_fetch)
    return _parse_event(raw, calendar_id)


async def create_event(
    credentials: Credentials,
    calendar_id: str,
    summary: str,
    start: str,
    end: str,
    all_day: bool = False,
    description: str | None = None,
    location: str | None = None,
) -> dict[str, Any]:
    """Google Calendar에 새 이벤트 생성."""
    service = _build_calendar(credentials)

    body: dict[str, Any] = {
        "summary": summary,
    }

    if all_day:
        # 종일 이벤트: date 형식 (YYYY-MM-DD)
        body["start"] = {"date": start}
        body["end"] = {"date": end}
    else:
        # 시간 이벤트: dateTime 형식 (RFC3339)
        body["start"] = {"dateTime": start}
        body["end"] = {"dateTime": end}

    if description:
        body["description"] = description
    if location:
        body["location"] = location

    def _create():
        return service.events().insert(calendarId=calendar_id, body=body).execute()

    raw = await asyncio.to_thread(_create)
    return _parse_event(raw, calendar_id)


def _parse_event(raw: dict, calendar_id: str) -> dict[str, Any]:
    """Google Calendar 이벤트 응답을 파싱."""
    start = raw.get("start", {})
    end = raw.get("end", {})
    all_day = "date" in start and "dateTime" not in start

    attendees_raw = raw.get("attendees")
    attendees = None
    if attendees_raw:
        attendees = [
            {
                "email": a.get("email", ""),
                "response_status": a.get("responseStatus", ""),
            }
            for a in attendees_raw
        ]

    return {
        "id": raw.get("id", ""),
        "summary": raw.get("summary", "(제목 없음)"),
        "description": raw.get("description"),
        "location": raw.get("location"),
        "start": start.get("dateTime") or start.get("date", ""),
        "end": end.get("dateTime") or end.get("date", ""),
        "all_day": all_day,
        "calendar_id": calendar_id,
        "status": raw.get("status", "confirmed"),
        "html_link": raw.get("htmlLink"),
        "color_id": raw.get("colorId"),
        "creator": raw.get("creator", {}).get("email"),
        "organizer": raw.get("organizer", {}).get("email"),
        "attendees": attendees,
        "recurrence": raw.get("recurrence"),
        "created": raw.get("created"),
        "updated": raw.get("updated"),
    }
