from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base declarative class for SQLAlchemy models."""


# Import models here for Alembic autogeneration and metadata discovery.
from app.models import report_file, study_session, tag, user  # noqa: E402,F401
