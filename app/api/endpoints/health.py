from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.system import HealthResponse

router = APIRouter()


@router.get("", response_model=HealthResponse)
def health_check(db: Session = Depends(get_db)):
    """Return API and database availability."""
    db_status = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"
    return HealthResponse(status="ok", db=db_status, time=datetime.now(timezone.utc))
