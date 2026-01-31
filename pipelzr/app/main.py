"""
PIPELZR - Codebase & Execution Service

The execution engine for:
- Task execution (local, Dagger, E2B)
- Pipeline orchestration (batch, parallel)
- Agent session management
- Skill execution
- Codebase indexing
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from .config import get_settings
from .database import init_db, close_db

# Import routers
from .routers import health, tasks, agents, pipelines, skills

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
    logger = structlog.get_logger("pipelzr.startup")
    
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
    description="Codebase & Execution Service for CommandCentral Platform",
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
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["Tasks"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["Agents"])
app.include_router(pipelines.router, prefix="/api/v1/pipelines", tags=["Pipelines"])
app.include_router(skills.router, prefix="/api/v1/skills", tags=["Skills"])


@app.get("/")
async def root():
    """Root endpoint with service info."""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "operational",
        "description": "Codebase & Execution Service",
        "endpoints": {
            "health": "/health",
            "metrics": "/metrics",
            "docs": "/docs",
            "tasks": "/api/v1/tasks",
            "agents": "/api/v1/agents",
            "pipelines": "/api/v1/pipelines",
            "skills": "/api/v1/skills",
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
