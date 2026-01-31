"""
IDEALZR - Ideas & Strategic Intelligence Service

The strategic intelligence hub for:
- Goals hierarchy and progress tracking
- Hypotheses lifecycle management
- Evidence collection and linking
- Predictions and forecasting
- Venture studio management
- Ideas capture and development
- Intelligence feed aggregation
- Memory/claims with provenance tracking
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from .config import get_settings
from .database import init_db, close_db

# Import routers
from .routers import (
    health,
    goals,
    hypotheses,
    evidence,
    forecasts,
    ventures,
    ideas,
    memory,
)

# Import middleware
from .middleware import (
    LoggingMiddleware,
    RateLimitMiddleware,
    MetricsMiddleware,
    CorrelationMiddleware,
)
from .middleware.metrics import get_metrics

settings = get_settings()

# Configure structlog
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer() if not settings.debug else structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger = structlog.get_logger("idealzr.startup")
    
    # Startup
    await logger.ainfo(
        "starting_service",
        service=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
    )
    await init_db()
    await logger.ainfo("database_initialized")

    yield

    # Shutdown
    await logger.ainfo("shutting_down")
    await close_db()
    await logger.ainfo("database_closed")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Ideas & Strategic Intelligence Service for CommandCentral Platform",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Add middleware (order matters - first added = last executed)
# Correlation ID first (outermost)
app.add_middleware(CorrelationMiddleware)
# Metrics
app.add_middleware(MetricsMiddleware)
# Rate limiting
app.add_middleware(RateLimitMiddleware)
# Logging
app.add_middleware(LoggingMiddleware)
# CORS (innermost)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health.router, tags=["Health"])
app.include_router(goals.router, prefix="/api/v1/goals", tags=["Goals"])
app.include_router(hypotheses.router, prefix="/api/v1/hypotheses", tags=["Hypotheses"])
app.include_router(evidence.router, prefix="/api/v1/evidence", tags=["Evidence"])
app.include_router(forecasts.router, prefix="/api/v1/forecasts", tags=["Forecasts"])
app.include_router(ventures.router, prefix="/api/v1/ventures", tags=["Ventures"])
app.include_router(ideas.router, prefix="/api/v1/ideas", tags=["Ideas"])
app.include_router(memory.router, prefix="/api/v1/memory", tags=["Memory"])


@app.get("/")
async def root():
    """Root endpoint with service info."""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "operational",
        "description": "Ideas & Strategic Intelligence Service",
        "endpoints": {
            "health": "/health",
            "metrics": "/metrics",
            "docs": "/docs",
            "goals": "/api/v1/goals",
            "hypotheses": "/api/v1/hypotheses",
            "evidence": "/api/v1/evidence",
            "forecasts": "/api/v1/forecasts",
            "ventures": "/api/v1/ventures",
            "ideas": "/api/v1/ideas",
            "memory": "/api/v1/memory",
        },
    }


@app.get("/metrics")
async def metrics():
    """Get service metrics."""
    return get_metrics()


def main():
    """Entry point for running with `python -m app.main`."""
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )


if __name__ == "__main__":
    main()
