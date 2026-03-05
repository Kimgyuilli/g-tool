from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, model_validator


class CreateEventRequest(BaseModel):
    summary: str
    start: str
    end: str
    all_day: bool = False
    calendar_id: str = "primary"
    description: str | None = None
    location: str | None = None

    @model_validator(mode="after")
    def validate_time_range(self) -> CreateEventRequest:
        """시작 시간이 종료 시간보다 늦으면 거부."""
        try:
            if self.all_day:
                s = date.fromisoformat(self.start)
                e = date.fromisoformat(self.end)
            else:
                s = datetime.fromisoformat(self.start)
                e = datetime.fromisoformat(self.end)
        except ValueError:
            return self  # 파싱 실패는 Google API가 처리

        if s >= e:
            msg = "종료 시간은 시작 시간보다 이후여야 합니다"
            raise ValueError(msg)
        return self
