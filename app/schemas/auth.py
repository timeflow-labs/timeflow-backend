from pydantic import BaseModel, EmailStr, Field

from app.schemas.user import UserBase, UserSummary


class SignUpRequest(BaseModel):
    user_id: str = Field(min_length=3, max_length=64)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    gender: str | None = None
    name: str | None = None


class LoginRequest(BaseModel):
    user_id: str
    password: str


class SignUpResponse(UserBase):
    pass


class LoginResponse(UserSummary):
    pass
