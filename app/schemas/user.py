from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    id: str
    email: EmailStr
    gender: str | None = None
    name: str | None = None
    created_at: datetime
    current_streak: int
    longest_streak: int


class UserSummary(BaseModel):
    id: str
    email: EmailStr
    name: str | None = None
