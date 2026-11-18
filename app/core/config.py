"""Application settings loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    APP_NAME: str = "Mini Shop API"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str = "postgresql+psycopg://minishop:minishop_secret@db:5432/minishop_db"
    TEST_DATABASE_URL: str = (
        "postgresql+psycopg://minishop:minishop_secret@db:5432/minishop_test_db"
    )

    JWT_SECRET_KEY: str = "change-this-to-a-strong-random-secret-key-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    LOGIN_RATE_LIMIT: str = "5/minute"


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings instance."""
    return Settings()
