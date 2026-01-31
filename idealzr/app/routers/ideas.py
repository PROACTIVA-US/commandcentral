"""
Ideas router - lightweight idea capture.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from pydantic import BaseModel, Field
from datetime import datetime

from ..database import get_session
from ..models.idea import Idea, IdeaStatus

router = APIRouter()


class IdeaCreate(BaseModel):
    """Schema for creating an idea."""
    title: str
    description: Optional[str] = None
    source: Optional[str] = None
    trigger: Optional[str] = None
    project_id: Optional[str] = None
    potential_impact: str = "unknown"
    effort_estimate: str = "unknown"
    urgency: str = "unknown"
    submitted_by: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    extra_data: dict = Field(default_factory=dict)


class IdeaUpdate(BaseModel):
    """Schema for updating an idea."""
    title: Optional[str] = None
    description: Optional[str] = None
    potential_impact: Optional[str] = None
    effort_estimate: Optional[str] = None
    urgency: Optional[str] = None
    impact_score: Optional[float] = None
    confidence_score: Optional[float] = None
    ease_score: Optional[float] = None
    tags: Optional[List[str]] = None
    extra_data: Optional[dict] = None


class IdeaResponse(BaseModel):
    """Schema for idea response."""
    id: str
    title: str
    description: Optional[str]
    source: Optional[str]
    trigger: Optional[str]
    status: str
    potential_impact: str
    effort_estimate: str
    urgency: str
    impact_score: Optional[float]
    confidence_score: Optional[float]
    ease_score: Optional[float]
    ice_score: Optional[float]
    promoted_to_type: Optional[str]
    promoted_to_id: Optional[str]
    project_id: Optional[str]
    submitted_by: Optional[str]
    tags: List[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class IdeaPromotion(BaseModel):
    """Schema for promoting an idea."""
    promote_to: str  # "hypothesis", "venture", "goal"
    additional_data: dict = Field(default_factory=dict)


@router.get("", response_model=List[IdeaResponse])
async def list_ideas(
    project_id: Optional[str] = None,
    status: Optional[str] = None,
    sort_by: str = "created_at",
    db: AsyncSession = Depends(get_session),
):
    """List ideas with optional filtering."""
    query = select(Idea)
    
    filters = []
    if project_id:
        filters.append(Idea.project_id == project_id)
    if status:
        filters.append(Idea.status == IdeaStatus(status))
    
    if filters:
        query = query.where(and_(*filters))
    
    # Sorting
    if sort_by == "ice_score":
        query = query.order_by(Idea.ice_score.desc().nullslast())
    else:
        query = query.order_by(Idea.created_at.desc())
    
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=IdeaResponse, status_code=201)
async def create_idea(
    idea: IdeaCreate,
    db: AsyncSession = Depends(get_session),
):
    """Quick capture a new idea."""
    new_idea = Idea(**idea.model_dump())
    db.add(new_idea)
    await db.flush()
    return new_idea


@router.get("/{idea_id}", response_model=IdeaResponse)
async def get_idea(
    idea_id: str,
    db: AsyncSession = Depends(get_session),
):
    """Get a specific idea."""
    result = await db.execute(select(Idea).where(Idea.id == idea_id))
    idea = result.scalar_one_or_none()
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")
    return idea


@router.patch("/{idea_id}", response_model=IdeaResponse)
async def update_idea(
    idea_id: str,
    updates: IdeaUpdate,
    db: AsyncSession = Depends(get_session),
):
    """Update an idea."""
    result = await db.execute(select(Idea).where(Idea.id == idea_id))
    idea = result.scalar_one_or_none()
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")
    
    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(idea, field, value)
    
    # Recalculate ICE score if component scores changed
    idea.calculate_ice_score()
    
    await db.flush()
    return idea


@router.post("/{idea_id}/score", response_model=IdeaResponse)
async def score_idea(
    idea_id: str,
    impact: float = Query(..., ge=0, le=10, description="Impact score 0-10"),
    confidence: float = Query(..., ge=0, le=10, description="Confidence score 0-10"),
    ease: float = Query(..., ge=0, le=10, description="Ease score 0-10"),
    db: AsyncSession = Depends(get_session),
):
    """Score an idea using ICE framework."""
    result = await db.execute(select(Idea).where(Idea.id == idea_id))
    idea = result.scalar_one_or_none()
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")
    
    idea.impact_score = impact
    idea.confidence_score = confidence
    idea.ease_score = ease
    idea.calculate_ice_score()
    idea.status = IdeaStatus.REVIEWING
    
    await db.flush()
    return idea


@router.post("/{idea_id}/promote", response_model=IdeaResponse)
async def promote_idea(
    idea_id: str,
    promotion: IdeaPromotion,
    db: AsyncSession = Depends(get_session),
):
    """Promote an idea to a hypothesis, venture, or goal."""
    result = await db.execute(select(Idea).where(Idea.id == idea_id))
    idea = result.scalar_one_or_none()
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")
    
    if idea.status == IdeaStatus.PROMOTED:
        raise HTTPException(status_code=400, detail="Idea already promoted")
    
    # Create the promoted entity based on type
    promoted_id = None
    if promotion.promote_to == "hypothesis":
        from ..models.hypothesis import Hypothesis
        hypothesis = Hypothesis(
            title=idea.title,
            statement=idea.description or idea.title,
            project_id=idea.project_id,
            tags=idea.tags,
            **promotion.additional_data,
        )
        db.add(hypothesis)
        await db.flush()
        promoted_id = hypothesis.id
        
    elif promotion.promote_to == "venture":
        from ..models.venture import Venture
        venture = Venture(
            name=idea.title,
            description=idea.description,
            project_id=idea.project_id,
            tags=idea.tags,
            **promotion.additional_data,
        )
        db.add(venture)
        await db.flush()
        promoted_id = venture.id
        
    elif promotion.promote_to == "goal":
        from ..models.goal import Goal
        goal = Goal(
            title=idea.title,
            description=idea.description,
            project_id=idea.project_id,
            tags=idea.tags,
            **promotion.additional_data,
        )
        db.add(goal)
        await db.flush()
        promoted_id = goal.id
    else:
        raise HTTPException(status_code=400, detail="Invalid promotion type")
    
    # Update idea status
    idea.status = IdeaStatus.PROMOTED
    idea.promoted_to_type = promotion.promote_to
    idea.promoted_to_id = promoted_id
    idea.promoted_at = datetime.utcnow()
    
    await db.flush()
    return idea


@router.post("/{idea_id}/park", response_model=IdeaResponse)
async def park_idea(
    idea_id: str,
    db: AsyncSession = Depends(get_session),
):
    """Park an idea for later."""
    result = await db.execute(select(Idea).where(Idea.id == idea_id))
    idea = result.scalar_one_or_none()
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")
    
    idea.status = IdeaStatus.PARKED
    idea.status_changed_at = datetime.utcnow()
    await db.flush()
    return idea


@router.post("/{idea_id}/reject", response_model=IdeaResponse)
async def reject_idea(
    idea_id: str,
    reason: Optional[str] = Query(None, description="Reason for rejection"),
    db: AsyncSession = Depends(get_session),
):
    """Reject an idea."""
    result = await db.execute(select(Idea).where(Idea.id == idea_id))
    idea = result.scalar_one_or_none()
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")
    
    idea.status = IdeaStatus.REJECTED
    idea.status_changed_at = datetime.utcnow()
    if reason:
        idea.extra_data["rejection_reason"] = reason
    await db.flush()
    return idea


@router.delete("/{idea_id}", status_code=204)
async def delete_idea(
    idea_id: str,
    db: AsyncSession = Depends(get_session),
):
    """Delete an idea."""
    result = await db.execute(select(Idea).where(Idea.id == idea_id))
    idea = result.scalar_one_or_none()
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")
    await db.delete(idea)
