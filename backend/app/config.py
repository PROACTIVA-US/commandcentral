"""
CommandCentral Configuration

The governance and truth state service for the CommandCentral platform.
"""

from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "CommandCentral"
    app_version: str = "1.0.0"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/commandcentral.db"

    # JWT Authentication
    secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:3001,http://localhost:3002,http://localhost:5173"

    # Rate Limiting
    rate_limit_requests: int = 10000
    rate_limit_window: int = 60  # seconds

    # Service URLs (other services in the platform)
    pipelzr_url: Optional[str] = "http://localhost:8001"
    vislzr_url: Optional[str] = "http://localhost:8002"
    idealzr_url: Optional[str] = "http://localhost:8003"

    # KnowledgeBeast
    knowledgebeast_collection: str = "commandcentral_governance"
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimension: int = 384

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
