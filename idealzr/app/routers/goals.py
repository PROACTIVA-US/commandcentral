"""
Goals router - hierarchical objectives management.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from pydantic import BaseModel, Field
from datetime import datetime

from ..database import get_session
from ..models.goal import Goal, GoalState
from ..services.goals_service import GoalsService

router = APIRouter()


class GoalCreate(BaseModel):
    """Schema for creating a goal."""
    title: str
    description: Optional[str] = None
    success_criteria: Optional[str] = None
    parent_id: Optional[str] = None
    project_id: Optional[str] = None
    priority: str = "medium"
    target_date: Optional[datetime] = None
    owner_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    extra_data: dict = Field(default_factory=dict)


class GoalUpdate(BaseModel):
    """Schema for updating a goal."""
    title: Optional[str] = None
    description: Optional[str] = None
    success_criteria: Optional[str] = None
    progress: Optional[float] = None
    progress_notes: Optional[str] = None
    priority: Optional[str] = None
    target_date: Optional[datetime] = None
    owner_id: Optional[str] = None
    tags: Optional[List[str]] = None
    extra_data: Optional[dict] = None


class GoalResponse(BaseModel):
    """Schema for goal response."""
    id: str
    parent_id: Optional[str]
    project_id: Optional[str]
    title: str
    description: Optional[str]
    success_criteria: Optional[str]
    state: str
    progress: float
    progress_notes: Optional[str]
    target_date: Optional[datetime]
    achieved_date: Optional[datetime]
    priority: str
    owner_id: Optional[str]
    tags: List[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@router.get("", response_model=List[GoalResponse])
async def list_goals(
    project_id: Optional[str] = None,
    parent_id: Optional[str] = None,
    state: Optional[str] = None,
    include_children: bool = False,
    db: AsyncSession = Depends(get_session),
):
    """List goals with optional filtering."""
    query = select(Goal)
    
    filters = []
    if project_id:
        filters.append(Goal.project_id == project_id)
    if parent_id:
        filters.append(Goal.parent_id == parent_id)
    elif not include_children:
        # By default, only show root goals
        filters.append(Goal.parent_id == None)
    if state:
        filters.append(Goal.state == GoalState(state))
    
    if filters:
        query = query.where(and_(*filters))
    
    query = query.order_by(Goal.sort_order, Goal.created_at)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=GoalResponse, status_code=201)
async def create_goal(
    goal: GoalCreate,
    db: AsyncSession = Depends(get_session),
):
    """Create a new goal."""
    service = GoalsService(db)
    return await service.create_goal(goal.model_dump())


@router.get("/{goal_id}", response_model=GoalResponse)
async def get_goal(
    goal_id: str,
    db: AsyncSession = Depends(get_session),
):
    """Get a specific goal."""
    result = await db.execute(select(Goal).where(Goal.id == goal_id))
    goal = result.scalar_one_or_none()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    return goal


@router.patch("/{goal_id}", response_model=GoalResponse)
async def update_goal(
    goal_id: str,
    updates: GoalUpdate,
    db: AsyncSession = Depends(get_session),
):
    """Update a goal."""
    service = GoalsService(db)
    goal = await service.update_goal(goal_id, updates.model_dump(exclude_unset=True))
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    return goal


@router.post("/{goal_id}/transition", response_model=GoalResponse)
async def transition_goal(
    goal_id: str,
    new_state: str = Query(..., description="Target state"),
    user_id: Optional[str] = Query(None, description="User making the transition"),
    db: AsyncSession = Depends(get_session),
):
    """Transition a goal to a new state."""
    service = GoalsService(db)
    goal = await service.transition_goal(goal_id, GoalState(new_state), user_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    return goal


@router.delete("/{goal_id}", status_code=204)
async def delete_goal(
    goal_id: str,
    db: AsyncSession = Depends(get_session),
):
    """Delete a goal."""
    result = await db.execute(select(Goal).where(Goal.id == goal_id))
    goal = result.scalar_one_or_none()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    await db.delete(goal)


@router.get("/{goal_id}/children", response_model=List[GoalResponse])
async def get_goal_children(
    goal_id: str,
    db: AsyncSession = Depends(get_session),
):
    """Get child goals of a specific goal."""
    result = await db.execute(
        select(Goal).where(Goal.parent_id == goal_id).order_by(Goal.sort_order)
    )
    return result.scalars().all()


@router.get("/{goal_id}/hierarchy")
async def get_goal_hierarchy(
    goal_id: str,
    db: AsyncSession = Depends(get_session),
):
    """Get the full hierarchy for a goal (ancestors and descendants)."""
    service = GoalsService(db)
    return await service.get_goal_hierarchy(goal_id)
