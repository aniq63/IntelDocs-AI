from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = Field(
        default="IntelDocs AI"
    )

    debug: bool = Field(
        default=False,
        alias="DEBUG"
    )

    # Database
    database_url: str = Field(
        ...,
        alias="DATABASE_URL"
    )

    # AI
    groq_api_key: Optional[str] = Field(
        default=None,
        alias="GROQ_API_KEY"
    )

    # Session
    session_token_expire_hours: int = Field(
        default=24 * 7,
        alias="SESSION_TOKEN_EXPIRE_HOURS"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()