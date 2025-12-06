import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.user import User

logger = logging.getLogger(__name__)

app = FastAPI(title="StudyLog API", version="1.0.0")


def ensure_default_user() -> None:
    """Create the default demo user so dashboard endpoints don't 404."""
    with SessionLocal() as db:
        existing = db.get(User, settings.default_user_id)
        if existing:
            return
        user = User(
            id=settings.default_user_id,
            email=settings.default_user_email,
            password_hash=hash_password(settings.default_user_password),
            name=settings.default_user_name,
        )
        db.add(user)
        db.commit()
        logger.info("Created default user %s", settings.default_user_id)


@app.on_event("startup")
def startup_event() -> None:
    ensure_default_user()


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/")
def root():
    return {"message": "StudyLog backend is running"}
