from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    SignUpRequest,
    SignUpResponse,
)

router = APIRouter()


@router.post("/signup", response_model=SignUpResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignUpRequest, db: Session = Depends(get_db)):
    """Registers a new user after validating email uniqueness."""
    existing_id = db.get(User, payload.user_id)
    if existing_id:
        raise HTTPException(status_code=400, detail="User ID already in use")
    existing_email = db.scalar(select(User).where(User.email == payload.email))
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        id=payload.user_id,
        email=payload.email,
        password_hash=hash_password(payload.password),
        gender=payload.gender,
        name=payload.name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return SignUpResponse(
        id=user.id,
        email=user.email,
        gender=user.gender,
        name=user.name,
        created_at=user.created_at,
        current_streak=user.current_streak,
        longest_streak=user.longest_streak,
    )


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticates a user with email/password.

    Future versions can return JWTs or session tokens. For v1 we simply return user info.
    """
    user = db.get(User, payload.user_id)
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    return LoginResponse(
        id=user.id,
        email=user.email,
        name=user.name,
    )
