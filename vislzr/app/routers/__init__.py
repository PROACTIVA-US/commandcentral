"""
VISLZR API Routers

REST API endpoints for visualization and exploration.
"""

from .health import router as health_router
from .canvas import router as canvas_router
from .nodes import router as nodes_router
from .exploration import router as exploration_router

__all__ = [
    "health_router",
    "canvas_router",
    "nodes_router",
    "exploration_router",
]
