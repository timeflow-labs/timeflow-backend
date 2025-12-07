from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_request_user_id
from app.models.tag import Tag
from app.schemas.tag import TagItem, TagListResponse

router = APIRouter()


@router.get("", response_model=TagListResponse)
def list_tags(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_request_user_id),
):
    """Return all tags belonging to the current user."""
    stmt = select(Tag).where(Tag.user_id == user_id).order_by(Tag.name.asc())
    tags = db.scalars(stmt).all()
    return TagListResponse(items=[TagItem(id=tag.id, name=tag.name) for tag in tags])
