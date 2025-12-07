from datetime import date, timedelta
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_request_user_id
from app.models.report_file import ReportFile
from app.schemas.report import (
    DailyReportRequest,
    ReportDownloadResponse,
    ReportListItem,
    ReportListResponse,
    ReportResponse,
    WeeklyReportRequest,
)

router = APIRouter()
ALLOWED_FORMATS = {"csv", "json", "pdf"}
ALLOWED_REPORT_TYPES = {"daily", "weekly", "custom"}


@router.post("/daily", response_model=ReportResponse, status_code=201)
def create_daily_report(
    payload: DailyReportRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_request_user_id),
):
    """Persist metadata for a daily report and return a dummy download URL."""
    _validate_format(payload.format)
    report = _create_report_record(
        db=db,
        user_id=user_id,
        report_type="daily",
        period_start=payload.date,
        period_end=payload.date,
        file_format=payload.format,
    )
    return _build_report_response(report)


@router.post("/weekly", response_model=ReportResponse, status_code=201)
def create_weekly_report(
    payload: WeeklyReportRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_request_user_id),
):
    """Create a weekly report stub covering a 7-day window."""
    _validate_format(payload.format)
    period_start = payload.week_start
    period_end = payload.week_start + timedelta(days=6)
    report = _create_report_record(
        db=db,
        user_id=user_id,
        report_type="weekly",
        period_start=period_start,
        period_end=period_end,
        file_format=payload.format,
    )
    return _build_report_response(report)


@router.get("", response_model=ReportListResponse)
def list_reports(
    report_type: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_request_user_id),
):
    """Return recent report metadata, optionally filtered by type."""
    stmt = select(ReportFile).where(ReportFile.user_id == user_id)
    if report_type:
        if report_type not in ALLOWED_REPORT_TYPES:
            raise HTTPException(status_code=400, detail="Unsupported report type")
        stmt = stmt.where(ReportFile.report_type == report_type)
    stmt = stmt.order_by(ReportFile.created_at.desc()).limit(limit)
    reports = db.scalars(stmt).all()
    items = [
        ReportListItem(
            id=report.id,
            report_type=report.report_type,
            period_start=report.period_start,
            period_end=report.period_end,
            file_format=report.file_format,
            created_at=report.created_at,
        )
        for report in reports
    ]
    return ReportListResponse(items=items)


@router.post("/{report_id}/download", response_model=ReportDownloadResponse)
def generate_report_download(
    report_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_request_user_id),
):
    """Return a dummy download URL to mimic presigned URL regeneration."""
    report = _get_report_or_404(db, report_id, user_id)
    # In production this would call S3 to create a new signed URL.
    download_url = f"https://example.com/dummy/{report.s3_key}?token={uuid4()}"
    return ReportDownloadResponse(report_id=report.id, download_url=download_url)


def _validate_format(file_format: str) -> None:
    if file_format not in ALLOWED_FORMATS:
        raise HTTPException(status_code=400, detail="Unsupported file format")


def _get_report_or_404(db: Session, report_id: int, user_id: str) -> ReportFile:
    report = db.get(ReportFile, report_id)
    if not report or report.user_id != user_id:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


def _create_report_record(
    *,
    db: Session,
    user_id: str,
    report_type: str,
    period_start: date,
    period_end: date,
    file_format: str,
) -> ReportFile:
    """Persist report metadata and return the ORM object."""
    s3_key = f"reports/{report_type}/{period_start.isoformat()}-{uuid4()}.{file_format}"
    report = ReportFile(
        user_id=user_id,
        report_type=report_type,
        period_start=period_start,
        period_end=period_end,
        file_format=file_format,
        s3_key=s3_key,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def _build_report_response(report: ReportFile) -> ReportResponse:
    download_url = f"https://example.com/dummy/{report.s3_key}"
    return ReportResponse(
        report_id=report.id,
        report_type=report.report_type,
        period_start=report.period_start,
        period_end=report.period_end,
        file_format=report.file_format,
        download_url=download_url,
        created_at=report.created_at,
    )
