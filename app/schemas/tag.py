from typing import List

from pydantic import BaseModel


class TagItem(BaseModel):
    id: int
    name: str


class TagListResponse(BaseModel):
    items: List[TagItem]
