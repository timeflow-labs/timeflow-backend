from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_request_user_id
from app.models.study_session import StudySession
from app.models.tag import Tag
from app.models.user import User
from app.schemas.session import (
    SessionCreate,
    SessionDetail,
    SessionListResponse,
    SessionPublic,
    SessionUpdate,
)

router = APIRouter()


@router.post("", response_model=SessionDetail, status_code=201)
def create_session(
    payload: SessionCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_request_user_id),
):
    """Create a study session entry with tag handling and streak updates."""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    duration_minutes = int(
        (payload.end_time - payload.start_time).total_seconds() // 60
    )
    if duration_minutes <= 0:
        raise HTTPException(status_code=400, detail="duration_minutes must be positive")

    session = StudySession(
        user_id=user_id,
        start_time=payload.start_time,
        end_time=payload.end_time,
        duration_minutes=duration_minutes,
        focus_level=payload.focus_level,
        memo=payload.memo,
    )
    session.tags = _get_or_create_tags(db, user_id, payload.tags)

    db.add(session)
    db.flush()
    _refresh_user_streaks(db, user)
    db.commit()
    db.refresh(session)
    return _build_session_detail(session)


@router.get("/recent", response_model=SessionListResponse)
def list_recent_sessions(
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_request_user_id),
):
    """Return most recent study sessions."""
    stmt = (
        select(StudySession)
        .where(StudySession.user_id == user_id)
        .order_by(StudySession.start_time.desc())
        .limit(limit)
    )
    sessions = db.scalars(stmt).unique().all()
    items = [_build_session_public(s) for s in sessions]
    return SessionListResponse(items=items)


@router.get("/{session_id}", response_model=SessionDetail)
def get_session(
    session_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_request_user_id),
):
    """Return a single study session."""
    session = _get_session_or_404(db, session_id, user_id)
    return _build_session_detail(session)


@router.put("/{session_id}", response_model=SessionDetail)
def update_session(
    session_id: int,
    payload: SessionUpdate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_request_user_id),
):
    """Update every field of the given study session."""
    session = _get_session_or_404(db, session_id, user_id)

    duration_minutes = int(
        (payload.end_time - payload.start_time).total_seconds() // 60
    )
    if duration_minutes <= 0:
        raise HTTPException(status_code=400, detail="duration_minutes must be positive")

    session.start_time = payload.start_time
    session.end_time = payload.end_time
    session.duration_minutes = duration_minutes
    session.focus_level = payload.focus_level
    session.memo = payload.memo
    session.tags = _get_or_create_tags(db, user_id, payload.tags)

    db.flush()
    _refresh_user_streaks(db, session.user)
    db.commit()
    db.refresh(session)
    return _build_session_detail(session)


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(
    session_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_request_user_id),
):
    """Remove a study session and recalculate streak metadata."""
    session = _get_session_or_404(db, session_id, user_id)
    user = session.user
    db.delete(session)
    db.flush()
    _refresh_user_streaks(db, user)
    db.commit()


def _get_or_create_tags(db: Session, user_id: int, names: list[str]) -> list[Tag]:
    """Ensure tags exist for the provided names and return Tag objects."""
    normalized = sorted({name.strip() for name in names if name.strip()})
    if not normalized:
        return []

    existing = db.scalars(
        select(Tag).where(Tag.user_id == user_id, Tag.name.in_(normalized))
    ).all()
    existing_map = {tag.name: tag for tag in existing}
    new_tags: list[Tag] = []
    for name in normalized:
        if name not in existing_map:
            tag = Tag(user_id=user_id, name=name)
            db.add(tag)
            new_tags.append(tag)
            existing_map[name] = tag
    if new_tags:
        db.flush()
    return list(existing_map.values())


def _get_session_or_404(db: Session, session_id: int, user_id: str) -> StudySession:
    """Fetch a session for the default user or raise 404."""
    session = db.get(StudySession, session_id)
    if not session or session.user_id != user_id:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


def _build_session_public(session: StudySession) -> SessionPublic:
    """Serialize a StudySession into SessionPublic."""
    return SessionPublic(
        id=session.id,
        start_time=session.start_time,
        end_time=session.end_time,
        duration_minutes=session.duration_minutes,
        focus_level=session.focus_level,
        memo=session.memo,
        tags=[tag.name for tag in session.tags],
    )


def _build_session_detail(session: StudySession) -> SessionDetail:
    """Serialize a StudySession into SessionDetail."""
    public = _build_session_public(session)
    return SessionDetail(
        **public.model_dump(),
        user_id=session.user_id,
        created_at=session.created_at,
    )


def _refresh_user_streaks(db: Session, user: User) -> None:
    """Recalculate streak fields based on all sessions for the user."""
    day_expr = func.date(StudySession.start_time)
    stmt = (
        select(day_expr)
        .where(StudySession.user_id == user.id)
        .distinct()
        .order_by(day_expr.desc())
    )
    days_desc = db.scalars(stmt).all()
    if not days_desc:
        user.last_study_date = None
        user.current_streak = 0
        user.longest_streak = 0
        return

    user.last_study_date = days_desc[0]

    current_streak = 1
    for idx in range(1, len(days_desc)):
        if (days_desc[idx - 1] - days_desc[idx]).days == 1:
            current_streak += 1
        else:
            break
    user.current_streak = current_streak

    days_asc = list(reversed(days_desc))
    longest = 1
    run = 1
    for idx in range(1, len(days_asc)):
        diff = (days_asc[idx] - days_asc[idx - 1]).days
        if diff == 1:
            run += 1
            longest = max(longest, run)
        else:
            run = 1
    user.longest_streak = longest
