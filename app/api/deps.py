from fastapi import Header
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db as _get_db


def get_db() -> Session:
    """Expose DB dependency for routers."""
    yield from _get_db()


def get_request_user_id(x_user_id: str | None = Header(default=None)) -> str:
    """
    Return the requester user ID, falling back to the default demo user.
    """
    return x_user_id or settings.default_user_id
