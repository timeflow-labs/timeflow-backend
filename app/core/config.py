from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration pulled from environment variables."""

    api_v1_prefix: str = "/api/v1"
    default_user_id: str = "demo-user"
    default_user_email: str = "demo@example.com"
    default_user_name: str = "Demo User"
    default_user_password: str = "demo-password"
    cors_allow_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173"], alias="CORS_ALLOW_ORIGINS"
    )

    app_env: str = Field(default="local", alias="APP_ENV")
    db_host: str = Field(default="127.0.0.1", alias="DB_HOST")
    db_port: int = Field(default=5432, alias="DB_PORT")
    db_user: str = Field(default="studylog", alias="DB_USER")
    db_password: str = Field(default="studylog_pw", alias="DB_PASSWORD")
    db_name: str = Field(default="studylog_db", alias="DB_NAME")
    database_url_override: str | None = Field(default=None, alias="DATABASE_URL")
    sqlalchemy_database_uri: str | None = Field(
        default=None, alias="SQLALCHEMY_DATABASE_URI"
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def database_url(self) -> str:
        """Construct the SQLAlchemy database URL."""
        if self.database_url_override:
            return self.database_url_override
        if self.sqlalchemy_database_uri:
            return self.sqlalchemy_database_uri
        return (
            "postgresql+psycopg2://"
            f"{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
