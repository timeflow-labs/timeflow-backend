from datetime import date, datetime
from typing import List

from pydantic import BaseModel, Field


class DailyReportRequest(BaseModel):
    date: date
    format: str = Field(pattern="^(csv|json|pdf)$")


class WeeklyReportRequest(BaseModel):
    week_start: date
    format: str = Field(pattern="^(csv|json|pdf)$")


class ReportResponse(BaseModel):
    report_id: int
    report_type: str
    period_start: date
    period_end: date
    file_format: str
    download_url: str
    created_at: datetime


class ReportListItem(BaseModel):
    id: int
    report_type: str
    period_start: date
    period_end: date
    file_format: str
    created_at: datetime


class ReportListResponse(BaseModel):
    items: List[ReportListItem]


class ReportDownloadResponse(BaseModel):
    report_id: int
    download_url: str
