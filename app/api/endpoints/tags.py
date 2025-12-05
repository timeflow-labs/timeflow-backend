from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import settings
from app.models.tag import Tag
from app.schemas.tag import TagItem, TagListResponse

router = APIRouter()
DEFAULT_USER_ID = settings.default_user_id


@router.get("", response_model=TagListResponse)
def list_tags(db: Session = Depends(get_db)):
    """Return all tags belonging to the default user."""
    stmt = select(Tag).where(Tag.user_id == DEFAULT_USER_ID).order_by(Tag.name.asc())
    tags = db.scalars(stmt).all()
    return TagListResponse(items=[TagItem(id=tag.id, name=tag.name) for tag in tags])
