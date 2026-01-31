"""
Projects router.

CRUD and state transitions for projects.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..services.project_service import ProjectService
from ..models.project import ProjectState
from .auth import get_current_user

router = APIRouter()


# Request/Response schemas
class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    slug: Optional[str] = None
    repo_path: Optional[str] = None
    repo_url: Optional[str] = None
    settings: Optional[dict] = None
    metadata: Optional[dict] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    repo_path: Optional[str] = None
    repo_url: Optional[str] = None
    settings: Optional[dict] = None
    metadata: Optional[dict] = None


class ProjectResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: Optional[str]
    state: str
    state_changed_at: datetime
    owner_id: str
    team_ids: list
    repo_path: Optional[str]
    repo_url: Optional[str]
    settings: dict
    metadata: dict
    created_at: datetime
    updated_at: datetime
    allowed_transitions: List[str]

    class Config:
        from_attributes = True


class TransitionRequest(BaseModel):
    rationale: Optional[str] = None


class TransitionResponse(BaseModel):
    success: bool
    message: str
    project: Optional[ProjectResponse] = None


class TeamMemberRequest(BaseModel):
    user_id: str


def project_to_response(project) -> ProjectResponse:
    """Convert Project model to response."""
    return ProjectResponse(
        id=project.id,
        name=project.name,
        slug=project.slug,
        description=project.description,
        state=project.state.value,
        state_changed_at=project.state_changed_at,
        owner_id=project.owner_id,
        team_ids=project.team_ids or [],
        repo_path=project.repo_path,
        repo_url=project.repo_url,
        settings=project.settings or {},
        metadata=project.metadata or {},
        created_at=project.created_at,
        updated_at=project.updated_at,
        allowed_transitions=[t.value for t in project.allowed_transitions()],
    )


# Endpoints
@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    state: Optional[str] = None,
    limit: int = Query(50, le=100),
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """List projects the user has access to."""
    service = ProjectService(session)

    state_filter = ProjectState(state) if state else None
    projects = await service.list_all(
        state=state_filter,
        owner_id=current_user.id,
        limit=limit,
        offset=offset,
    )

    return [project_to_response(p) for p in projects]


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    request: ProjectCreate,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """Create a new project."""
    service = ProjectService(session)

    project = await service.create(
        name=request.name,
        owner_id=current_user.id,
        description=request.description,
        slug=request.slug,
        repo_path=request.repo_path,
        repo_url=request.repo_url,
        settings=request.settings,
        metadata=request.metadata,
    )

    return project_to_response(project)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """Get a project by ID."""
    service = ProjectService(session)
    project = await service.get_by_id(project_id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    return project_to_response(project)


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    request: ProjectUpdate,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """Update a project."""
    service = ProjectService(session)

    project = await service.update(
        project_id=project_id,
        actor_id=current_user.id,
        name=request.name,
        description=request.description,
        repo_path=request.repo_path,
        repo_url=request.repo_url,
        settings=request.settings,
        metadata=request.metadata,
    )

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    return project_to_response(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """Delete a project (proposed only)."""
    service = ProjectService(session)

    success = await service.delete(project_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete project (not found or not in proposed state)",
        )


# State transitions
@router.post("/{project_id}/activate", response_model=TransitionResponse)
async def activate_project(
    project_id: str,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """Activate a proposed project."""
    service = ProjectService(session)
    success, message, project = await service.activate(project_id, current_user.id)

    return TransitionResponse(
        success=success,
        message=message,
        project=project_to_response(project) if project else None,
    )


@router.post("/{project_id}/pause", response_model=TransitionResponse)
async def pause_project(
    project_id: str,
    request: TransitionRequest = None,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """Pause an active project."""
    service = ProjectService(session)
    rationale = request.rationale if request else None
    success, message, project = await service.pause(project_id, current_user.id, rationale)

    return TransitionResponse(
        success=success,
        message=message,
        project=project_to_response(project) if project else None,
    )


@router.post("/{project_id}/resume", response_model=TransitionResponse)
async def resume_project(
    project_id: str,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """Resume a paused project."""
    service = ProjectService(session)
    success, message, project = await service.resume(project_id, current_user.id)

    return TransitionResponse(
        success=success,
        message=message,
        project=project_to_response(project) if project else None,
    )


@router.post("/{project_id}/complete", response_model=TransitionResponse)
async def complete_project(
    project_id: str,
    request: TransitionRequest = None,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """Mark a project as completed."""
    service = ProjectService(session)
    rationale = request.rationale if request else None
    success, message, project = await service.complete(project_id, current_user.id, rationale)

    return TransitionResponse(
        success=success,
        message=message,
        project=project_to_response(project) if project else None,
    )


@router.post("/{project_id}/kill", response_model=TransitionResponse)
async def kill_project(
    project_id: str,
    request: TransitionRequest = None,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """Kill a project."""
    service = ProjectService(session)
    rationale = request.rationale if request else None
    success, message, project = await service.kill(project_id, current_user.id, rationale)

    return TransitionResponse(
        success=success,
        message=message,
        project=project_to_response(project) if project else None,
    )


# Team management
@router.post("/{project_id}/team", response_model=ProjectResponse)
async def add_team_member(
    project_id: str,
    request: TeamMemberRequest,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """Add a team member to a project."""
    service = ProjectService(session)

    project = await service.add_team_member(
        project_id=project_id,
        user_id=request.user_id,
        actor_id=current_user.id,
    )

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    return project_to_response(project)


@router.delete("/{project_id}/team/{user_id}", response_model=ProjectResponse)
async def remove_team_member(
    project_id: str,
    user_id: str,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """Remove a team member from a project."""
    service = ProjectService(session)

    project = await service.remove_team_member(
        project_id=project_id,
        user_id=user_id,
        actor_id=current_user.id,
    )

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    return project_to_response(project)


@router.get("/{project_id}/transitions")
async def get_allowed_transitions(
    project_id: str,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """Get allowed transitions for a project."""
    service = ProjectService(session)
    project = await service.get_by_id(project_id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    return {
        "current_state": project.state.value,
        "allowed_transitions": [t.value for t in project.allowed_transitions()],
    }


@router.get("/{project_id}/audit")
async def get_project_audit(
    project_id: str,
    limit: int = Query(50, le=100),
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """Get audit trail for a project."""
    service = ProjectService(session)

    # Verify project exists
    project = await service.get_by_id(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    entries = await service.get_audit_trail(project_id, limit=limit)

    return {
        "project_id": project_id,
        "entries": [
            {
                "id": e.id,
                "event_type": e.event_type.value,
                "event_name": e.event_name,
                "entity_type": e.entity_type,
                "entity_id": e.entity_id,
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
