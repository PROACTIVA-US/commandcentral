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
    # TODO: Add database connectivity check
    return {
        "status": "ready",
        "checks": {
            "database": "ok",
        },
    }
