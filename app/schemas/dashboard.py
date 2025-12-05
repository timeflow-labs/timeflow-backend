from datetime import date
from typing import List

from pydantic import BaseModel


class TopTag(BaseModel):
    name: str
    minutes: int


class TodaySummaryResponse(BaseModel):
    date: date
    total_minutes: int
    avg_focus: float | None
    session_count: int
    top_tags: List[TopTag]
    highlight_memo: str | None = None


class DailyPoint(BaseModel):
    date: date
    total_minutes: int
    avg_focus: float | None
    session_count: int


class WeeklySummaryResponse(BaseModel):
    start_date: date
    end_date: date
    days: List[DailyPoint]


class HeatmapCell(BaseModel):
    date: date
    total_minutes: int


class HeatmapResponse(BaseModel):
    start_date: date
    end_date: date
    cells: List[HeatmapCell]


class StreakResponse(BaseModel):
    current_streak: int
    longest_streak: int
    last_study_date: date | None
