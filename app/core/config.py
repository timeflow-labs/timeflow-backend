from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration pulled from environment variables."""

    api_v1_prefix: str = "/api/v1"
    default_user_id: str = "demo-user"
    default_user_email: str = "demo@example.com"
    default_user_name: str = "Demo User"
    default_user_password: str = "demo-password"
    cors_allow_origins: list[str] = ["http://localhost:5173"]

    app_env: str = "local"
    database_url: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
