"""
VISLZR Configuration

The visualization and exploration service for the CommandCentral platform.
"""

from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "VISLZR"
    app_version: str = "1.0.0"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8000  # Default port (8002 assigned via docker-compose)

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/vislzr.db"

    # JWT Authentication (for validating tokens from CommandCentral)
    secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:3001,http://localhost:3002,http://localhost:5173"

    # Rate Limiting
    rate_limit_requests: int = 10000
    rate_limit_window: int = 60  # seconds

    # Service URLs (other services in the platform)
    commandcentral_url: Optional[str] = "http://localhost:8000"
    pipelzr_url: Optional[str] = "http://localhost:8001"
    idealzr_url: Optional[str] = "http://localhost:8003"

    # Canvas Configuration
    default_layout: str = "force-directed"
    max_nodes_per_canvas: int = 500
    max_relationships_per_canvas: int = 2000

    # Exploration Configuration
    max_depth: int = 5
    default_depth: int = 2

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
