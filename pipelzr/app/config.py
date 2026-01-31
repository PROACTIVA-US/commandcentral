"""
PIPELZR Configuration

The codebase & execution service for the CommandCentral platform.
"""

from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "PIPELZR"
    app_version: str = "1.0.0"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8000  # Default port (8001 assigned via docker-compose)

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/pipelzr.db"

    # JWT Authentication (shared with CommandCentral)
    secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:3001,http://localhost:3002,http://localhost:5173"

    # Rate Limiting
    rate_limit_requests: int = 10000
    rate_limit_window: int = 60  # seconds

    # Service URLs (other services in the platform)
    commandcentral_url: Optional[str] = "http://localhost:8000"
    vislzr_url: Optional[str] = "http://localhost:8002"
    idealzr_url: Optional[str] = "http://localhost:8003"

    # Execution Backends
    dagger_enabled: bool = False
    e2b_enabled: bool = False
    e2b_api_key: Optional[str] = None

    # Agent Configuration
    max_concurrent_agents: int = 10
    agent_timeout_seconds: int = 300
    agent_max_iterations: int = 100

    # Pipeline Configuration
    max_concurrent_pipelines: int = 5
    pipeline_timeout_seconds: int = 3600

    # Codebase Indexing
    index_directory: str = "./data/indexes"
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
