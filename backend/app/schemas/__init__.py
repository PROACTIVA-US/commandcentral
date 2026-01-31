"""
Pydantic schemas for API request/response models.

Organized by domain:
- auth: Authentication and user schemas
- state_machine: State machine and transition schemas
- decisions: Decision primitive schemas
- events: Event and audit schemas
- projects: Project schemas
- common: Shared schemas (pagination, errors, etc.)
"""

from .common import (
    PaginationParams,
    PaginatedResponse,
    ErrorResponse,
    SuccessResponse,
    HealthResponse,
)
from .auth import (
    UserCreate,
    UserUpdate,
    UserResponse,
    TokenResponse,
    LoginRequest,
)
from .state_machine import (
    StateDefinition,
    TransitionRequest,
    TransitionResponse,
    EntityStateResponse,
)
from .decisions import (
    DecisionCreate,
    DecisionUpdate,
    DecisionResponse,
)
from .projects import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
)

__all__ = [
    # Common
    "PaginationParams",
    "PaginatedResponse",
    "ErrorResponse",
    "SuccessResponse",
    "HealthResponse",
    # Auth
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "TokenResponse",
    "LoginRequest",
    # State Machine
    "StateDefinition",
    "TransitionRequest",
    "TransitionResponse",
    "EntityStateResponse",
    # Decisions
    "DecisionCreate",
    "DecisionUpdate",
    "DecisionResponse",
    # Projects
    "ProjectCreate",
    "ProjectUpdate",
    "ProjectResponse",
]
