"""
Hypotheses router - testable assumptions lifecycle.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from pydantic import BaseModel, Field
from datetime import datetime

from ..database import get_session
from ..models.hypothesis import Hypothesis, HypothesisState
from ..services.hypothesis_service import HypothesisService

router = APIRouter()


class HypothesisCreate(BaseModel):
    """Schema for creating a hypothesis."""
    title: str
    statement: str
    rationale: Optional[str] = None
    falsifiable_criteria: Optional[str] = None
    success_criteria: Optional[str] = None
    project_id: Optional[str] = None
    goal_id: Optional[str] = None
    venture_id: Optional[str] = None
    initial_confidence: float = 0.5
    priority: str = "medium"
    impact_if_true: Optional[str] = None
    impact_if_false: Optional[str] = None
    owner_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    extra_data: dict = Field(default_factory=dict)


class HypothesisUpdate(BaseModel):
    """Schema for updating a hypothesis."""
    title: Optional[str] = None
    statement: Optional[str] = None
    rationale: Optional[str] = None
    falsifiable_criteria: Optional[str] = None
    success_criteria: Optional[str] = None
    current_confidence: Optional[float] = None
    priority: Optional[str] = None
    impact_if_true: Optional[str] = None
    impact_if_false: Optional[str] = None
    target_resolution_date: Optional[datetime] = None
    tags: Optional[List[str]] = None
    extra_data: Optional[dict] = None


class HypothesisResponse(BaseModel):
    """Schema for hypothesis response."""
    id: str
    project_id: Optional[str]
    goal_id: Optional[str]
    venture_id: Optional[str]
    title: str
    statement: str
    rationale: Optional[str]
    state: str
    initial_confidence: float
    current_confidence: float
    supporting_evidence_count: float
    contradicting_evidence_count: float
    priority: str
    owner_id: Optional[str]
    tags: List[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@router.get("", response_model=List[HypothesisResponse])
async def list_hypotheses(
    project_id: Optional[str] = None,
    goal_id: Optional[str] = None,
    venture_id: Optional[str] = None,
    state: Optional[str] = None,
    db: AsyncSession = Depends(get_session),
):
    """List hypotheses with optional filtering."""
    query = select(Hypothesis)
    
    filters = []
    if project_id:
        filters.append(Hypothesis.project_id == project_id)
    if goal_id:
        filters.append(Hypothesis.goal_id == goal_id)
    if venture_id:
        filters.append(Hypothesis.venture_id == venture_id)
    if state:
        filters.append(Hypothesis.state == HypothesisState(state))
    
    if filters:
        query = query.where(and_(*filters))
    
    query = query.order_by(Hypothesis.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=HypothesisResponse, status_code=201)
async def create_hypothesis(
    hypothesis: HypothesisCreate,
    db: AsyncSession = Depends(get_session),
):
    """Create a new hypothesis."""
    service = HypothesisService(db)
    return await service.create_hypothesis(hypothesis.model_dump())


@router.get("/{hypothesis_id}", response_model=HypothesisResponse)
async def get_hypothesis(
    hypothesis_id: str,
    db: AsyncSession = Depends(get_session),
):
    """Get a specific hypothesis."""
    result = await db.execute(select(Hypothesis).where(Hypothesis.id == hypothesis_id))
    hypothesis = result.scalar_one_or_none()
    if not hypothesis:
        raise HTTPException(status_code=404, detail="Hypothesis not found")
    return hypothesis


@router.patch("/{hypothesis_id}", response_model=HypothesisResponse)
async def update_hypothesis(
    hypothesis_id: str,
    updates: HypothesisUpdate,
    db: AsyncSession = Depends(get_session),
):
    """Update a hypothesis."""
    service = HypothesisService(db)
    hypothesis = await service.update_hypothesis(
        hypothesis_id, updates.model_dump(exclude_unset=True)
    )
    if not hypothesis:
        raise HTTPException(status_code=404, detail="Hypothesis not found")
    return hypothesis


@router.post("/{hypothesis_id}/transition", response_model=HypothesisResponse)
async def transition_hypothesis(
    hypothesis_id: str,
    new_state: str = Query(..., description="Target state"),
    user_id: Optional[str] = Query(None, description="User making the transition"),
    db: AsyncSession = Depends(get_session),
):
    """Transition a hypothesis to a new state."""
    service = HypothesisService(db)
    hypothesis = await service.transition_hypothesis(
        hypothesis_id, HypothesisState(new_state), user_id
    )
    if not hypothesis:
        raise HTTPException(status_code=404, detail="Hypothesis not found")
    return hypothesis


@router.post("/{hypothesis_id}/update-confidence", response_model=HypothesisResponse)
async def update_confidence(
    hypothesis_id: str,
    confidence: float = Query(..., ge=0.0, le=1.0, description="New confidence level"),
    evidence_id: Optional[str] = Query(None, description="Evidence triggering update"),
    db: AsyncSession = Depends(get_session),
):
    """Update confidence level for a hypothesis."""
    service = HypothesisService(db)
    hypothesis = await service.update_confidence(hypothesis_id, confidence, evidence_id)
    if not hypothesis:
        raise HTTPException(status_code=404, detail="Hypothesis not found")
    return hypothesis


@router.delete("/{hypothesis_id}", status_code=204)
async def delete_hypothesis(
    hypothesis_id: str,
    db: AsyncSession = Depends(get_session),
):
    """Delete a hypothesis."""
    result = await db.execute(select(Hypothesis).where(Hypothesis.id == hypothesis_id))
    hypothesis = result.scalar_one_or_none()
    if not hypothesis:
        raise HTTPException(status_code=404, detail="Hypothesis not found")
    await db.delete(hypothesis)
