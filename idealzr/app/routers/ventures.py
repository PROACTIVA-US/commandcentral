"""
Ventures router - venture studio management.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from pydantic import BaseModel, Field
from datetime import datetime

from ..database import get_session
from ..models.venture import Venture, VentureStage

router = APIRouter()


class VentureCreate(BaseModel):
    """Schema for creating a venture."""
    name: str
    codename: Optional[str] = None
    description: Optional[str] = None
    value_proposition: Optional[str] = None
    target_market: Optional[str] = None
    market_size: Optional[str] = None
    project_id: Optional[str] = None
    lead_id: Optional[str] = None
    team_ids: List[str] = Field(default_factory=list)
    north_star_metric: Optional[str] = None
    target_mvp_date: Optional[datetime] = None
    target_launch_date: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list)
    extra_data: dict = Field(default_factory=dict)


class VentureUpdate(BaseModel):
    """Schema for updating a venture."""
    name: Optional[str] = None
    codename: Optional[str] = None
    description: Optional[str] = None
    value_proposition: Optional[str] = None
    target_market: Optional[str] = None
    market_size: Optional[str] = None
    lead_id: Optional[str] = None
    team_ids: Optional[List[str]] = None
    north_star_metric: Optional[str] = None
    key_metrics: Optional[dict] = None
    investment_to_date: Optional[float] = None
    revenue_to_date: Optional[float] = None
    target_mvp_date: Optional[datetime] = None
    target_launch_date: Optional[datetime] = None
    tags: Optional[List[str]] = None
    extra_data: Optional[dict] = None


class VentureResponse(BaseModel):
    """Schema for venture response."""
    id: str
    name: str
    codename: Optional[str]
    description: Optional[str]
    value_proposition: Optional[str]
    target_market: Optional[str]
    market_size: Optional[str]
    stage: str
    investment_to_date: float
    revenue_to_date: float
    project_id: Optional[str]
    lead_id: Optional[str]
    team_ids: List[str]
    north_star_metric: Optional[str]
    key_metrics: dict
    tags: List[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StageTransition(BaseModel):
    """Schema for stage transition."""
    new_stage: str
    evidence: List[str] = Field(default_factory=list)  # Evidence IDs supporting transition
    notes: Optional[str] = None
    user_id: Optional[str] = None


@router.get("", response_model=List[VentureResponse])
async def list_ventures(
    project_id: Optional[str] = None,
    stage: Optional[str] = None,
    db: AsyncSession = Depends(get_session),
):
    """List ventures with optional filtering."""
    query = select(Venture)
    
    filters = []
    if project_id:
        filters.append(Venture.project_id == project_id)
    if stage:
        filters.append(Venture.stage == VentureStage(stage))
    
    if filters:
        query = query.where(and_(*filters))
    
    query = query.order_by(Venture.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=VentureResponse, status_code=201)
async def create_venture(
    venture: VentureCreate,
    db: AsyncSession = Depends(get_session),
):
    """Create a new venture."""
    new_venture = Venture(**venture.model_dump())
    db.add(new_venture)
    await db.flush()
    return new_venture


@router.get("/{venture_id}", response_model=VentureResponse)
async def get_venture(
    venture_id: str,
    db: AsyncSession = Depends(get_session),
):
    """Get a specific venture."""
    result = await db.execute(select(Venture).where(Venture.id == venture_id))
    venture = result.scalar_one_or_none()
    if not venture:
        raise HTTPException(status_code=404, detail="Venture not found")
    return venture


@router.patch("/{venture_id}", response_model=VentureResponse)
async def update_venture(
    venture_id: str,
    updates: VentureUpdate,
    db: AsyncSession = Depends(get_session),
):
    """Update a venture."""
    result = await db.execute(select(Venture).where(Venture.id == venture_id))
    venture = result.scalar_one_or_none()
    if not venture:
        raise HTTPException(status_code=404, detail="Venture not found")
    
    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(venture, field, value)
    
    await db.flush()
    return venture


@router.post("/{venture_id}/transition", response_model=VentureResponse)
async def transition_venture(
    venture_id: str,
    transition: StageTransition,
    db: AsyncSession = Depends(get_session),
):
    """Transition a venture to a new stage."""
    result = await db.execute(select(Venture).where(Venture.id == venture_id))
    venture = result.scalar_one_or_none()
    if not venture:
        raise HTTPException(status_code=404, detail="Venture not found")
    
    new_stage = VentureStage(transition.new_stage)
    if not venture.can_transition_to(new_stage):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition from {venture.stage.value} to {new_stage.value}. "
                   f"Allowed: {[s.value for s in venture.allowed_transitions()]}"
        )
    
    from datetime import datetime
    venture.stage = new_stage
    venture.stage_changed_at = datetime.utcnow()
    venture.stage_changed_by = transition.user_id
    venture.stage_evidence.extend(transition.evidence)
    
    await db.flush()
    return venture


@router.get("/{venture_id}/hypotheses")
async def get_venture_hypotheses(
    venture_id: str,
    db: AsyncSession = Depends(get_session),
):
    """Get hypotheses linked to a venture."""
    from ..models.hypothesis import Hypothesis
    result = await db.execute(
        select(Hypothesis).where(Hypothesis.venture_id == venture_id)
    )
    return result.scalars().all()


@router.post("/{venture_id}/metrics")
async def update_venture_metrics(
    venture_id: str,
    metrics: dict,
    db: AsyncSession = Depends(get_session),
):
    """Update venture metrics."""
    result = await db.execute(select(Venture).where(Venture.id == venture_id))
    venture = result.scalar_one_or_none()
    if not venture:
        raise HTTPException(status_code=404, detail="Venture not found")
    
    venture.key_metrics.update(metrics)
    await db.flush()
    return {"status": "updated", "metrics": venture.key_metrics}


@router.delete("/{venture_id}", status_code=204)
async def delete_venture(
    venture_id: str,
    db: AsyncSession = Depends(get_session),
):
    """Delete a venture."""
    result = await db.execute(select(Venture).where(Venture.id == venture_id))
    venture = result.scalar_one_or_none()
    if not venture:
        raise HTTPException(status_code=404, detail="Venture not found")
    await db.delete(venture)
