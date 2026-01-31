"""
CommandCentral - Governance & Truth State Service

The central authority for:
- State machines and entity lifecycle
- Permissions and authorization
- Audit logging
- Decision primitives
- Cross-service coordination
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .database import init_db, close_db

# Import routers
from .routers import auth, state_machine, decisions, events, projects, health

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print(f"Starting {settings.app_name} v{settings.app_version}")
    await init_db()
    print("Database initialized")

    yield

    # Shutdown
    print("Shutting down...")
    await close_db()
    print("Database connections closed")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Governance & Truth State Service for CommandCentral Platform",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health.router, tags=["Health"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(state_machine.router, prefix="/api/v1/state-machine", tags=["State Machine"])
app.include_router(decisions.router, prefix="/api/v1/decisions", tags=["Decisions"])
app.include_router(events.router, prefix="/api/v1/events", tags=["Events"])
app.include_router(projects.router, prefix="/api/v1/projects", tags=["Projects"])


@app.get("/")
async def root():
    """Root endpoint with service info."""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "operational",
        "description": "Governance & Truth State Service",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "auth": "/api/v1/auth",
            "state_machine": "/api/v1/state-machine",
            "decisions": "/api/v1/decisions",
            "events": "/api/v1/events",
            "projects": "/api/v1/projects",
        },
    }
