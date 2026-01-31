"""
State Machine router.

Generic state machine management for any entity type.
Enables centralized state governance across all services.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_session
from ..models.entity_state import EntityState
from ..models.audit import AuditEventType
from ..services.audit_service import AuditService
from .auth import get_current_user

router = APIRouter()


# Predefined state machines for known entity types
STATE_MACHINES: Dict[str, Dict] = {
    "project": {
        "states": ["proposed", "active", "paused", "completed", "killed"],
        "transitions": {
            "proposed": ["active", "killed"],
            "active": ["paused", "completed", "killed"],
            "paused": ["active", "killed"],
            "completed": [],
            "killed": [],
        },
        "initial": "proposed",
        "terminal": ["completed", "killed"],
    },
    "decision": {
        "states": ["draft", "active", "decided", "archived"],
        "transitions": {
            "draft": ["active"],
            "active": ["decided", "archived"],
            "decided": ["archived"],
            "archived": [],
        },
        "initial": "draft",
        "terminal": ["archived"],
    },
    "task": {
        "states": ["backlog", "in_progress", "review", "done", "blocked"],
        "transitions": {
            "backlog": ["in_progress", "blocked"],
            "in_progress": ["review", "blocked", "backlog"],
            "review": ["done", "in_progress"],
            "done": [],
            "blocked": ["backlog", "in_progress"],
        },
        "initial": "backlog",
        "terminal": ["done"],
    },
    "hypothesis": {
        "states": ["proposed", "testing", "validated", "invalidated", "archived"],
        "transitions": {
            "proposed": ["testing", "archived"],
            "testing": ["validated", "invalidated", "proposed"],
            "validated": ["archived"],
            "invalidated": ["archived"],
            "archived": [],
        },
        "initial": "proposed",
        "terminal": ["archived"],
    },
    "evidence": {
        "states": ["pending", "validated", "referenced", "deprecated"],
        "transitions": {
            "pending": ["validated", "deprecated"],
            "validated": ["referenced", "deprecated"],
            "referenced": ["deprecated"],
            "deprecated": [],
        },
        "initial": "pending",
        "terminal": ["deprecated"],
    },
}


# Request/Response schemas
class EntityStateResponse(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    service: str
    current_state: str
    allowed_transitions: List[str]
    last_transition_at: datetime
    last_transition_by: Optional[str]
    last_transition_from: Optional[str]

    class Config:
        from_attributes = True


class TransitionRequest(BaseModel):
    to_state: str
    rationale: Optional[str] = None


class TransitionResponse(BaseModel):
    success: bool
    message: str
    from_state: str
    to_state: str
    audit_id: Optional[str] = None


class RegisterEntityRequest(BaseModel):
    entity_type: str
    entity_id: str
    service: str
    initial_state: Optional[str] = None
    project_id: Optional[str] = None


# Endpoints
@router.get("/definitions")
async def list_state_machine_definitions(
    current_user=Depends(get_current_user),
):
    """List all predefined state machine definitions."""
    return {
        "definitions": STATE_MACHINES,
    }


@router.get("/definitions/{entity_type}")
async def get_state_machine_definition(
    entity_type: str,
    current_user=Depends(get_current_user),
):
    """Get state machine definition for an entity type."""
    if entity_type not in STATE_MACHINES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No state machine defined for entity type: {entity_type}",
        )

    return STATE_MACHINES[entity_type]


@router.get("/entities")
async def list_entity_states(
    entity_type: Optional[str] = None,
    service: Optional[str] = None,
    project_id: Optional[str] = None,
    limit: int = Query(50, le=100),
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """List tracked entity states."""
    query = select(EntityState)

    if entity_type:
        query = query.where(EntityState.entity_type == entity_type)
    if service:
        query = query.where(EntityState.service == service)
    if project_id:
        query = query.where(EntityState.project_id == project_id)

    query = query.limit(limit)

    result = await session.execute(query)
    entities = list(result.scalars().all())

    return {
        "entities": [
            {
                "id": e.id,
                "entity_type": e.entity_type,
                "entity_id": e.entity_id,
                "service": e.service,
                "current_state": e.current_state,
                "allowed_transitions": e.allowed_transitions or [],
                "project_id": e.project_id,
                "last_transition_at": e.last_transition_at.isoformat() if e.last_transition_at else None,
            }
            for e in entities
        ],
        "count": len(entities),
    }


@router.get("/entities/{service}/{entity_type}/{entity_id}")
async def get_entity_state(
    service: str,
    entity_type: str,
    entity_id: str,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """Get the current state of an entity."""
    result = await session.execute(
        select(EntityState).where(
            EntityState.service == service,
            EntityState.entity_type == entity_type,
            EntityState.entity_id == entity_id,
        )
    )
    entity = result.scalar_one_or_none()

    if not entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entity state not found",
        )

    return {
        "id": entity.id,
        "entity_type": entity.entity_type,
        "entity_id": entity.entity_id,
        "service": entity.service,
        "current_state": entity.current_state,
        "allowed_transitions": entity.allowed_transitions or [],
        "project_id": entity.project_id,
        "last_transition_at": entity.last_transition_at.isoformat() if entity.last_transition_at else None,
        "last_transition_by": entity.last_transition_by,
        "last_transition_from": entity.last_transition_from,
    }


@router.post("/entities/register")
async def register_entity(
    request: RegisterEntityRequest,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """Register an entity for state tracking."""
    # Check if already registered
    result = await session.execute(
        select(EntityState).where(
            EntityState.service == request.service,
            EntityState.entity_type == request.entity_type,
            EntityState.entity_id == request.entity_id,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Entity already registered",
        )

    # Get initial state from state machine definition
    initial_state = request.initial_state
    if not initial_state and request.entity_type in STATE_MACHINES:
        initial_state = STATE_MACHINES[request.entity_type]["initial"]

    if not initial_state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="initial_state required (no default defined for entity type)",
        )

    # Get allowed transitions
    allowed = []
    if request.entity_type in STATE_MACHINES:
        allowed = STATE_MACHINES[request.entity_type]["transitions"].get(initial_state, [])

    entity = EntityState(
        entity_type=request.entity_type,
        entity_id=request.entity_id,
        service=request.service,
        current_state=initial_state,
        allowed_transitions=allowed,
        project_id=request.project_id,
        last_transition_by=current_user.id,
    )
    session.add(entity)
    await session.flush()

    # Audit log
    audit = AuditService(session)
    await audit.log(
        event_type=AuditEventType.ENTITY_CREATED,
        event_name=f"{request.entity_type}.registered",
        entity_type=request.entity_type,
        entity_id=request.entity_id,
        project_id=request.project_id,
        actor_id=current_user.id,
        metadata={"service": request.service, "initial_state": initial_state},
    )

    return {
        "id": entity.id,
        "entity_type": entity.entity_type,
        "entity_id": entity.entity_id,
        "service": entity.service,
        "current_state": entity.current_state,
        "allowed_transitions": entity.allowed_transitions,
    }


@router.post("/transitions/execute")
async def execute_transition(
    service: str,
    entity_type: str,
    entity_id: str,
    request: TransitionRequest,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """Execute a state transition for an entity."""
    # Get current state
    result = await session.execute(
        select(EntityState).where(
            EntityState.service == service,
            EntityState.entity_type == entity_type,
            EntityState.entity_id == entity_id,
        )
    )
    entity = result.scalar_one_or_none()

    if not entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entity state not found",
        )

    from_state = entity.current_state
    to_state = request.to_state

    # Check if transition is allowed
    allowed = entity.allowed_transitions or []
    if to_state not in allowed:
        # Log denied transition
        audit = AuditService(session)
        entry = await audit.log_transition(
            entity_type=entity_type,
            entity_id=entity_id,
            from_state=from_state,
            to_state=to_state,
            actor_id=current_user.id,
            project_id=entity.project_id,
            success=False,
            failure_reason=f"Transition to {to_state} not allowed from {from_state}",
        )

        return TransitionResponse(
            success=False,
            message=f"Transition to {to_state} not allowed from {from_state}. Allowed: {allowed}",
            from_state=from_state,
            to_state=to_state,
            audit_id=entry.id,
        )

    # Perform transition
    entity.last_transition_from = from_state
    entity.current_state = to_state
    entity.last_transition_at = datetime.utcnow()
    entity.last_transition_by = current_user.id

    # Update allowed transitions
    if entity_type in STATE_MACHINES:
        entity.allowed_transitions = STATE_MACHINES[entity_type]["transitions"].get(to_state, [])

    # Log successful transition
    audit = AuditService(session)
    entry = await audit.log_transition(
        entity_type=entity_type,
        entity_id=entity_id,
        from_state=from_state,
        to_state=to_state,
        actor_id=current_user.id,
        project_id=entity.project_id,
        success=True,
        rationale=request.rationale,
    )

    return TransitionResponse(
        success=True,
        message=f"Transitioned from {from_state} to {to_state}",
        from_state=from_state,
        to_state=to_state,
        audit_id=entry.id,
    )


@router.get("/permissions/matrix")
async def get_permissions_matrix(
    current_user=Depends(get_current_user),
):
    """
    Get the permissions matrix for state transitions.

    This is a placeholder - full implementation would check
    user roles and entity ownership.
    """
    return {
        "description": "Permissions matrix for state transitions",
        "user_roles": current_user.roles or ["user"],
        "permissions": {
            "project": {
                "activate": ["owner", "admin"],
                "pause": ["owner", "admin"],
                "complete": ["owner", "admin"],
                "kill": ["owner", "admin"],
            },
            "decision": {
                "activate": ["owner", "admin", "user"],
                "decide": ["owner", "admin"],
                "archive": ["owner", "admin"],
            },
            "task": {
                "all": ["owner", "admin", "user"],
            },
        },
    }
