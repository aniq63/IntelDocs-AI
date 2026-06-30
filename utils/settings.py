from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Keys
    groq_api_key: Optional[str] = Field(default=None, alias="GROQ_API_KEY")
    usda_api_key: Optional[str] = Field(default=None, alias="USDA_API_KEY")
    serpapi_key: Optional[str] = Field(default=None, alias="SERPAPI_KEY")
    ingredients_recogination_token: Optional[str] = Field(default=None, alias="INGREDIENTS_RECOGINATION_TOKEN")
    
    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/nutrichef", 
        alias="DATABASE_URL"
    )
    
    # Application Settings
    app_name: str = "Nutri Chef AI"
    debug: bool = Field(default=False, alias="DEBUG")
    
    # Session Settings
    session_token_expire_hours: int = Field(
        default=24 * 7, 
        alias="SESSION_TOKEN_EXPIRE_HOURS"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()