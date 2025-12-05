from datetime import datetime
from typing import List

from pydantic import BaseModel, Field, field_validator


class SessionCreate(BaseModel):
    start_time: datetime
    end_time: datetime
    focus_level: int = Field(ge=1, le=5)
    memo: str | None = None
    tags: List[str] = Field(default_factory=list)

    @field_validator("end_time")
    @classmethod
    def validate_time_order(cls, end_time: datetime, values: dict):
        start_time = values.get("start_time")
        if start_time and end_time <= start_time:
            raise ValueError("end_time must be greater than start_time")
        return end_time


class SessionPublic(BaseModel):
    id: int
    start_time: datetime
    end_time: datetime
    duration_minutes: int
    focus_level: int
    memo: str | None = None
    tags: List[str]


class SessionDetail(SessionPublic):
    user_id: str
    created_at: datetime


class SessionListResponse(BaseModel):
    items: List[SessionPublic]


class SessionUpdate(SessionCreate):
    """Payload used for session updates (identical to creation schema)."""
