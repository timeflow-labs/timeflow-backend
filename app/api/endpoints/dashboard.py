from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_request_user_id
from app.models.study_session import StudySession
from app.models.tag import SessionTag, Tag
from app.models.user import User
from app.schemas.dashboard import (
    DailyPoint,
    HeatmapCell,
    HeatmapResponse,
    StreakResponse,
    TodaySummaryResponse,
    TopTag,
    WeeklySummaryResponse,
)

router = APIRouter()


@router.get("/today", response_model=TodaySummaryResponse)
def get_today_summary(
    target_date: date | None = Query(default=None, alias="date"),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_request_user_id),
):
    """Return totals for the provided date (defaults to today)."""
    target = target_date or date.today()
    day_expr = func.date(StudySession.start_time)
    stmt = (
        select(
            func.coalesce(func.sum(StudySession.duration_minutes), 0),
            func.avg(StudySession.focus_level),
            func.count(StudySession.id),
        )
        .where(StudySession.user_id == user_id)
        .where(day_expr == target)
    )
    total_minutes, avg_focus, session_count = db.execute(stmt).one()

    tag_stmt = (
        select(
            Tag.name,
            func.coalesce(func.sum(StudySession.duration_minutes), 0).label("minutes"),
        )
        .join(SessionTag, SessionTag.tag_id == Tag.id)
        .join(StudySession, SessionTag.session_id == StudySession.id)
        .where(Tag.user_id == user_id)
        .where(day_expr == target)
        .group_by(Tag.name)
        .order_by(func.sum(StudySession.duration_minutes).desc())
        .limit(5)
    )
    top_tags = [
        TopTag(name=row.name, minutes=int(row.minutes)) for row in db.execute(tag_stmt)
    ]

    highlight_stmt = (
        select(StudySession.memo)
        .where(
            StudySession.user_id == user_id,
            day_expr == target,
            StudySession.memo.is_not(None),
        )
        .order_by(StudySession.end_time.desc())
        .limit(1)
    )
    highlight = db.scalar(highlight_stmt)

    return TodaySummaryResponse(
        date=target,
        total_minutes=int(total_minutes or 0),
        avg_focus=float(avg_focus) if avg_focus is not None else None,
        session_count=int(session_count or 0),
        top_tags=top_tags,
        highlight_memo=highlight,
    )


@router.get("/weekly", response_model=WeeklySummaryResponse)
def get_weekly_summary(
    end_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_request_user_id),
):
    """Return rolling 7-day study metrics ending with provided date."""
    end = end_date or date.today()
    start = end - timedelta(days=6)
    day_expr = func.date(StudySession.start_time)
    stmt = (
        select(
            day_expr.label("day"),
            func.coalesce(func.sum(StudySession.duration_minutes), 0),
            func.avg(StudySession.focus_level),
            func.count(StudySession.id),
        )
        .where(
            StudySession.user_id == user_id,
            day_expr >= start,
            day_expr <= end,
        )
        .group_by("day")
    )
    rows = db.execute(stmt).all()
    aggregates = {row.day: row for row in rows}

    days: list[DailyPoint] = []
    current = start
    while current <= end:
        if current in aggregates:
            row = aggregates[current]
            avg_focus = float(row[2]) if row[2] is not None else None
            days.append(
                DailyPoint(
                    date=current,
                    total_minutes=int(row[1]),
                    avg_focus=avg_focus,
                    session_count=int(row[3]),
                )
            )
        else:
            days.append(
                DailyPoint(
                    date=current,
                    total_minutes=0,
                    avg_focus=None,
                    session_count=0,
                )
            )
        current += timedelta(days=1)

    return WeeklySummaryResponse(start_date=start, end_date=end, days=days)


@router.get("/heatmap", response_model=HeatmapResponse)
def get_heatmap(
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_request_user_id),
):
    """Return date-level totals for a given period."""
    if end_date < start_date:
        raise HTTPException(status_code=400, detail="end_date must be after start_date")

    day_expr = func.date(StudySession.start_time)
    stmt = (
        select(
            day_expr.label("day"),
            func.coalesce(func.sum(StudySession.duration_minutes), 0),
        )
        .where(
            StudySession.user_id == user_id,
            day_expr >= start_date,
            day_expr <= end_date,
        )
        .group_by("day")
    )
    rows = db.execute(stmt).all()
    aggregates = {row.day: int(row[1]) for row in rows}

    cells: list[HeatmapCell] = []
    current = start_date
    while current <= end_date:
        cells.append(
            HeatmapCell(date=current, total_minutes=aggregates.get(current, 0))
        )
        current += timedelta(days=1)

    return HeatmapResponse(start_date=start_date, end_date=end_date, cells=cells)


@router.get("/streak", response_model=StreakResponse)
def get_streak(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_request_user_id),
):
    """Return streak info from user record."""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return StreakResponse(
        current_streak=user.current_streak,
        longest_streak=user.longest_streak,
        last_study_date=user.last_study_date,
    )
