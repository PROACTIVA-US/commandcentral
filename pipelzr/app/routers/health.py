"""
Health check endpoints.
"""

from fastapi import APIRouter

from ..config import get_settings

router = APIRouter()
settings = get_settings()


@router.get("/health")
async def health_check():
    """Basic health check."""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
    }


@router.get("/ready")
async def readiness_check():
    """Readiness check for orchestration."""
    return {
        "status": "ready",
        "checks": {
            "database": "ok",
            "execution_backends": {
                "local": "ok",
                "dagger": "enabled" if settings.dagger_enabled else "disabled",
                "e2b": "enabled" if settings.e2b_enabled else "disabled",
            },
        },
    }
