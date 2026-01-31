"""
VISLZR - Visualization & Exploration Service

The visualization and exploration service for:
- Canvas/graph visualization
- Wander navigation
- Node rendering
- Exploration queries
- Relationship visualization
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from .config import get_settings
from .database import init_db, close_db

# Import routers
from .routers import health, canvas, nodes, exploration

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
    logger = structlog.get_logger("vislzr.startup")
    
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
    description="Visualization & Exploration Service for CommandCentral Platform",
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
app.include_router(canvas.router, prefix="/api/v1/canvases", tags=["Canvases"])
app.include_router(nodes.router, prefix="/api/v1/nodes", tags=["Nodes"])
app.include_router(exploration.router, prefix="/api/v1/exploration", tags=["Exploration"])


@app.get("/")
async def root():
    """Root endpoint with service info."""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "operational",
        "description": "Visualization & Exploration Service",
        "endpoints": {
            "health": "/health",
            "metrics": "/metrics",
            "docs": "/docs",
            "canvases": "/api/v1/canvases",
            "nodes": "/api/v1/nodes",
            "exploration": "/api/v1/exploration",
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
