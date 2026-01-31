"""
Decisions router.

CRUD and state transitions for decision primitives.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..services.decision_service import DecisionService
from ..models.decision import DecisionState
from .auth import get_current_user

router = APIRouter()


# Request/Response schemas
class DecisionCreate(BaseModel):
    project_id: str
    title: str
    question: Optional[str] = None
    context: Optional[str] = None
    options: Optional[List[dict]] = None
    tags: Optional[List[str]] = None


class DecisionUpdate(BaseModel):
    title: Optional[str] = None
    question: Optional[str] = None
    context: Optional[str] = None
    options: Optional[List[dict]] = None
    tags: Optional[List[str]] = None


class DecisionResponse(BaseModel):
    id: str
    project_id: str
    title: str
    question: Optional[str]
    context: Optional[str]
    options: list
    selected_option: Optional[str]
    rationale: Optional[str]
    state: str
    state_changed_at: datetime
    tags: list
    created_at: datetime
    updated_at: datetime
    created_by: str
    decided_by: Optional[str]
    decided_at: Optional[datetime]
    allowed_transitions: List[str]

    class Config:
        from_attributes = True


class TransitionRequest(BaseModel):
    selected_option: Optional[str] = None
    rationale: Optional[str] = None


class TransitionResponse(BaseModel):
    success: bool
    message: str
    decision: Optional[DecisionResponse] = None


def decision_to_response(decision) -> DecisionResponse:
    """Convert Decision model to response."""
    return DecisionResponse(
        id=decision.id,
        project_id=decision.project_id,
        title=decision.title,
        question=decision.question,
        context=decision.context,
        options=decision.options or [],
        selected_option=decision.selected_option,
        rationale=decision.rationale,
        state=decision.state.value,
        state_changed_at=decision.state_changed_at,
        tags=decision.tags or [],
        created_at=decision.created_at,
        updated_at=decision.updated_at,
        created_by=decision.created_by,
        decided_by=decision.decided_by,
        decided_at=decision.decided_at,
        allowed_transitions=[t.value for t in decision.allowed_transitions()],
    )


# Endpoints
@router.get("/", response_model=List[DecisionResponse])
async def list_decisions(
    project_id: str,
    state: Optional[str] = None,
    limit: int = Query(50, le=100),
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """List decisions for a project."""
    service = DecisionService(session)

    state_filter = DecisionState(state) if state else None
    decisions = await service.list_by_project(
        project_id=project_id,
        state=state_filter,
        limit=limit,
        offset=offset,
    )

    return [decision_to_response(d) for d in decisions]


@router.post("/", response_model=DecisionResponse, status_code=status.HTTP_201_CREATED)
async def create_decision(
    request: DecisionCreate,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """Create a new decision."""
    service = DecisionService(session)

    decision = await service.create(
        project_id=request.project_id,
        title=request.title,
        question=request.question,
        context=request.context,
        options=request.options,
        tags=request.tags,
        created_by=current_user.id,
    )

    return decision_to_response(decision)


@router.get("/{decision_id}", response_model=DecisionResponse)
async def get_decision(
    decision_id: str,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """Get a decision by ID."""
    service = DecisionService(session)
    decision = await service.get_by_id(decision_id)

    if not decision:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Decision not found",
        )

    return decision_to_response(decision)


@router.put("/{decision_id}", response_model=DecisionResponse)
async def update_decision(
    decision_id: str,
    request: DecisionUpdate,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """Update a decision."""
    service = DecisionService(session)

    decision = await service.update(
        decision_id=decision_id,
        actor_id=current_user.id,
        title=request.title,
        question=request.question,
        context=request.context,
        options=request.options,
        tags=request.tags,
    )

    if not decision:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update decision (not found or invalid state)",
        )

    return decision_to_response(decision)


@router.delete("/{decision_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_decision(
    decision_id: str,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """Delete a decision (draft only)."""
    service = DecisionService(session)

    success = await service.delete(decision_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete decision (not found or not in draft state)",
        )


# State transitions
@router.post("/{decision_id}/activate", response_model=TransitionResponse)
async def activate_decision(
    decision_id: str,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """Activate a draft decision."""
    service = DecisionService(session)
    success, message, decision = await service.activate(decision_id, current_user.id)

    return TransitionResponse(
        success=success,
        message=message,
        decision=decision_to_response(decision) if decision else None,
    )


@router.post("/{decision_id}/decide", response_model=TransitionResponse)
async def decide_decision(
    decision_id: str,
    request: TransitionRequest,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """Mark a decision as decided."""
    service = DecisionService(session)

    if not request.selected_option:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="selected_option is required",
        )

    success, message, decision = await service.decide(
        decision_id=decision_id,
        actor_id=current_user.id,
        selected_option=request.selected_option,
        rationale=request.rationale,
    )

    return TransitionResponse(
        success=success,
        message=message,
        decision=decision_to_response(decision) if decision else None,
    )


@router.post("/{decision_id}/archive", response_model=TransitionResponse)
async def archive_decision(
    decision_id: str,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """Archive a decision."""
    service = DecisionService(session)
    success, message, decision = await service.archive(decision_id, current_user.id)

    return TransitionResponse(
        success=success,
        message=message,
        decision=decision_to_response(decision) if decision else None,
    )


@router.get("/{decision_id}/transitions")
async def get_allowed_transitions(
    decision_id: str,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """Get allowed transitions for a decision."""
    service = DecisionService(session)
    decision = await service.get_by_id(decision_id)

    if not decision:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Decision not found",
        )

    return {
        "current_state": decision.state.value,
        "allowed_transitions": [t.value for t in decision.allowed_transitions()],
    }


@router.get("/{decision_id}/audit")
async def get_decision_audit(
    decision_id: str,
    limit: int = Query(50, le=100),
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """Get audit trail for a decision."""
    service = DecisionService(session)

    # Verify decision exists
    decision = await service.get_by_id(decision_id)
    if not decision:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Decision not found",
        )

    entries = await service.get_audit_trail(decision_id, limit=limit)

    return {
        "decision_id": decision_id,
        "entries": [
            {
                "id": e.id,
                "event_type": e.event_type.value,
                "event_name": e.event_name,
                "from_state": e.from_state,
                "to_state": e.to_state,
                "actor_id": e.actor_id,
                "success": e.success,
                "failure_reason": e.failure_reason,
                "timestamp": e.timestamp.isoformat(),
            }
            for e in entries
        ],
    }
