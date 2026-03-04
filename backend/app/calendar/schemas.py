from __future__ import annotations

from pydantic import BaseModel


class CreateEventRequest(BaseModel):
    summary: str
    start: str
    end: str
    all_day: bool = False
    calendar_id: str = "primary"
    description: str | None = None
    location: str | None = None
