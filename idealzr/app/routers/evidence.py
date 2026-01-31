"""
Evidence router - supporting/contradicting data for hypotheses.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from pydantic import BaseModel, Field
from datetime import datetime

from ..database import get_session
from ..models.evidence import Evidence, EvidenceType, EvidenceStrength
from ..services.evidence_service import EvidenceService

router = APIRouter()


class EvidenceCreate(BaseModel):
    """Schema for creating evidence."""
    title: str
    description: str
    hypothesis_id: Optional[str] = None
    project_id: Optional[str] = None
    evidence_type: str = "data"
    strength: str = "moderate"
    supports_hypothesis: bool = True
    confidence_impact: float = 0.0
    source: Optional[str] = None
    source_url: Optional[str] = None
    source_date: Optional[datetime] = None
    memory_id: Optional[str] = None
    claim_ids: List[str] = Field(default_factory=list)
    data_value: Optional[float] = None
    data_unit: Optional[str] = None
    data_context: Optional[str] = None
    attachment_urls: List[str] = Field(default_factory=list)
    submitted_by: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    extra_data: dict = Field(default_factory=dict)


class EvidenceUpdate(BaseModel):
    """Schema for updating evidence."""
    title: Optional[str] = None
    description: Optional[str] = None
    evidence_type: Optional[str] = None
    strength: Optional[str] = None
    supports_hypothesis: Optional[bool] = None
    confidence_impact: Optional[float] = None
    source: Optional[str] = None
    source_url: Optional[str] = None
    data_value: Optional[float] = None
    data_unit: Optional[str] = None
    data_context: Optional[str] = None
    attachment_urls: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    extra_data: Optional[dict] = None


class EvidenceResponse(BaseModel):
    """Schema for evidence response."""
    id: str
    hypothesis_id: Optional[str]
    project_id: Optional[str]
    title: str
    description: str
    evidence_type: str
    strength: str
    supports_hypothesis: float
    confidence_impact: float
    source: Optional[str]
    source_url: Optional[str]
    verified: float
    submitted_by: Optional[str]
    tags: List[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@router.get("", response_model=List[EvidenceResponse])
async def list_evidence(
    hypothesis_id: Optional[str] = None,
    project_id: Optional[str] = None,
    evidence_type: Optional[str] = None,
    supports: Optional[bool] = None,
    db: AsyncSession = Depends(get_session),
):
    """List evidence with optional filtering."""
    query = select(Evidence)
    
    filters = []
    if hypothesis_id:
        filters.append(Evidence.hypothesis_id == hypothesis_id)
    if project_id:
        filters.append(Evidence.project_id == project_id)
    if evidence_type:
        filters.append(Evidence.evidence_type == EvidenceType(evidence_type))
    if supports is not None:
        filters.append(Evidence.supports_hypothesis == supports)
    
    if filters:
        query = query.where(and_(*filters))
    
    query = query.order_by(Evidence.collected_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=EvidenceResponse, status_code=201)
async def create_evidence(
    evidence: EvidenceCreate,
    db: AsyncSession = Depends(get_session),
):
    """Create new evidence."""
    service = EvidenceService(db)
    return await service.create_evidence(evidence.model_dump())


@router.get("/{evidence_id}", response_model=EvidenceResponse)
async def get_evidence(
    evidence_id: str,
    db: AsyncSession = Depends(get_session),
):
    """Get specific evidence."""
    result = await db.execute(select(Evidence).where(Evidence.id == evidence_id))
    evidence = result.scalar_one_or_none()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return evidence


@router.patch("/{evidence_id}", response_model=EvidenceResponse)
async def update_evidence(
    evidence_id: str,
    updates: EvidenceUpdate,
    db: AsyncSession = Depends(get_session),
):
    """Update evidence."""
    service = EvidenceService(db)
    evidence = await service.update_evidence(
        evidence_id, updates.model_dump(exclude_unset=True)
    )
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return evidence


@router.post("/{evidence_id}/verify", response_model=EvidenceResponse)
async def verify_evidence(
    evidence_id: str,
    user_id: str = Query(..., description="User verifying the evidence"),
    db: AsyncSession = Depends(get_session),
):
    """Mark evidence as verified."""
    service = EvidenceService(db)
    evidence = await service.verify_evidence(evidence_id, user_id)
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return evidence


@router.post("/{evidence_id}/link-hypothesis")
async def link_to_hypothesis(
    evidence_id: str,
    hypothesis_id: str = Query(..., description="Hypothesis to link"),
    db: AsyncSession = Depends(get_session),
):
    """Link evidence to a hypothesis."""
    service = EvidenceService(db)
    result = await service.link_to_hypothesis(evidence_id, hypothesis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Evidence or hypothesis not found")
    return {"status": "linked", "evidence_id": evidence_id, "hypothesis_id": hypothesis_id}


@router.delete("/{evidence_id}", status_code=204)
async def delete_evidence(
    evidence_id: str,
    db: AsyncSession = Depends(get_session),
):
    """Delete evidence."""
    result = await db.execute(select(Evidence).where(Evidence.id == evidence_id))
    evidence = result.scalar_one_or_none()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")
    await db.delete(evidence)
