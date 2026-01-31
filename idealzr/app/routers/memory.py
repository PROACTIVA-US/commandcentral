"""
Memory router - provenance-tracked knowledge and claims.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from pydantic import BaseModel, Field
from datetime import datetime

from ..database import get_session
from ..models.memory import Memory, MemoryType, Claim

router = APIRouter()


class MemoryCreate(BaseModel):
    """Schema for creating a memory."""
    content: str
    title: Optional[str] = None
    summary: Optional[str] = None
    memory_type: str = "user_input"
    source_type: Optional[str] = None
    source_id: Optional[str] = None
    source_url: Optional[str] = None
    source_title: Optional[str] = None
    source_author: Optional[str] = None
    source_date: Optional[datetime] = None
    project_id: Optional[str] = None
    valid_until: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list)
    extra_data: dict = Field(default_factory=dict)


class MemoryUpdate(BaseModel):
    """Schema for updating a memory."""
    title: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    valid_until: Optional[datetime] = None
    tags: Optional[List[str]] = None
    extra_data: Optional[dict] = None


class MemoryResponse(BaseModel):
    """Schema for memory response."""
    id: str
    title: Optional[str]
    content: str
    summary: Optional[str]
    memory_type: str
    source_type: Optional[str]
    source_url: Optional[str]
    source_title: Optional[str]
    verified: float
    project_id: Optional[str]
    valid_from: datetime
    valid_until: Optional[datetime]
    access_count: float
    tags: List[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ClaimCreate(BaseModel):
    """Schema for creating a claim."""
    statement: str
    memory_id: Optional[str] = None
    source_text: Optional[str] = None
    confidence: float = 0.8
    project_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    extra_data: dict = Field(default_factory=dict)


class ClaimResponse(BaseModel):
    """Schema for claim response."""
    id: str
    statement: str
    memory_id: Optional[str]
    source_text: Optional[str]
    confidence: float
    verified: float
    is_current: float
    project_id: Optional[str]
    tags: List[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SearchQuery(BaseModel):
    """Schema for semantic search."""
    query: str
    limit: int = 10
    project_id: Optional[str] = None
    memory_type: Optional[str] = None


# Memory endpoints

@router.get("", response_model=List[MemoryResponse])
async def list_memories(
    project_id: Optional[str] = None,
    memory_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_session),
):
    """List memories with optional filtering."""
    query = select(Memory)
    
    filters = []
    if project_id:
        filters.append(Memory.project_id == project_id)
    if memory_type:
        filters.append(Memory.memory_type == MemoryType(memory_type))
    
    if filters:
        query = query.where(and_(*filters))
    
    query = query.order_by(Memory.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=MemoryResponse, status_code=201)
async def create_memory(
    memory: MemoryCreate,
    db: AsyncSession = Depends(get_session),
):
    """Create a new memory."""
    new_memory = Memory(
        **memory.model_dump(),
        memory_type=MemoryType(memory.memory_type),
    )
    db.add(new_memory)
    await db.flush()
    return new_memory


@router.get("/{memory_id}", response_model=MemoryResponse)
async def get_memory(
    memory_id: str,
    db: AsyncSession = Depends(get_session),
):
    """Get a specific memory."""
    result = await db.execute(select(Memory).where(Memory.id == memory_id))
    memory = result.scalar_one_or_none()
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    # Track access
    memory.access_count += 1
    memory.last_accessed_at = datetime.utcnow()
    await db.flush()
    
    return memory


@router.patch("/{memory_id}", response_model=MemoryResponse)
async def update_memory(
    memory_id: str,
    updates: MemoryUpdate,
    db: AsyncSession = Depends(get_session),
):
    """Update a memory."""
    result = await db.execute(select(Memory).where(Memory.id == memory_id))
    memory = result.scalar_one_or_none()
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(memory, field, value)
    
    await db.flush()
    return memory


@router.post("/{memory_id}/verify", response_model=MemoryResponse)
async def verify_memory(
    memory_id: str,
    user_id: str = Query(..., description="User verifying the memory"),
    db: AsyncSession = Depends(get_session),
):
    """Mark a memory as verified."""
    result = await db.execute(select(Memory).where(Memory.id == memory_id))
    memory = result.scalar_one_or_none()
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    memory.verified = True
    memory.verified_by = user_id
    memory.verified_at = datetime.utcnow()
    await db.flush()
    return memory


@router.post("/search")
async def search_memories(
    search: SearchQuery,
    db: AsyncSession = Depends(get_session),
):
    """Semantic search over memories (placeholder - needs embedding implementation)."""
    # TODO: Implement actual semantic search with embeddings
    # For now, do simple text search
    query = select(Memory)
    
    filters = [Memory.content.ilike(f"%{search.query}%")]
    if search.project_id:
        filters.append(Memory.project_id == search.project_id)
    if search.memory_type:
        filters.append(Memory.memory_type == MemoryType(search.memory_type))
    
    query = query.where(and_(*filters)).limit(search.limit)
    result = await db.execute(query)
    memories = result.scalars().all()
    
    return {
        "query": search.query,
        "results": memories,
        "count": len(memories),
        "note": "Basic text search - semantic search requires embedding configuration",
    }


@router.delete("/{memory_id}", status_code=204)
async def delete_memory(
    memory_id: str,
    db: AsyncSession = Depends(get_session),
):
    """Delete a memory."""
    result = await db.execute(select(Memory).where(Memory.id == memory_id))
    memory = result.scalar_one_or_none()
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    await db.delete(memory)


# Claim endpoints

@router.get("/claims", response_model=List[ClaimResponse])
async def list_claims(
    memory_id: Optional[str] = None,
    project_id: Optional[str] = None,
    is_current: bool = True,
    limit: int = 50,
    db: AsyncSession = Depends(get_session),
):
    """List claims with optional filtering."""
    query = select(Claim)
    
    filters = [Claim.is_current == is_current]
    if memory_id:
        filters.append(Claim.memory_id == memory_id)
    if project_id:
        filters.append(Claim.project_id == project_id)
    
    query = query.where(and_(*filters)).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/claims", response_model=ClaimResponse, status_code=201)
async def create_claim(
    claim: ClaimCreate,
    db: AsyncSession = Depends(get_session),
):
    """Create a new claim."""
    new_claim = Claim(**claim.model_dump())
    db.add(new_claim)
    await db.flush()
    return new_claim


@router.get("/claims/{claim_id}", response_model=ClaimResponse)
async def get_claim(
    claim_id: str,
    db: AsyncSession = Depends(get_session),
):
    """Get a specific claim."""
    result = await db.execute(select(Claim).where(Claim.id == claim_id))
    claim = result.scalar_one_or_none()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    return claim


@router.post("/claims/{claim_id}/verify", response_model=ClaimResponse)
async def verify_claim(
    claim_id: str,
    user_id: str = Query(..., description="User verifying the claim"),
    db: AsyncSession = Depends(get_session),
):
    """Mark a claim as verified."""
    result = await db.execute(select(Claim).where(Claim.id == claim_id))
    claim = result.scalar_one_or_none()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    claim.verified = True
    claim.verified_by = user_id
    claim.verified_at = datetime.utcnow()
    await db.flush()
    return claim


@router.post("/claims/{claim_id}/supersede", response_model=ClaimResponse)
async def supersede_claim(
    claim_id: str,
    new_statement: str = Query(..., description="New claim statement"),
    db: AsyncSession = Depends(get_session),
):
    """Supersede a claim with a new one."""
    result = await db.execute(select(Claim).where(Claim.id == claim_id))
    old_claim = result.scalar_one_or_none()
    if not old_claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    # Create new claim
    new_claim = Claim(
        statement=new_statement,
        memory_id=old_claim.memory_id,
        project_id=old_claim.project_id,
        tags=old_claim.tags,
    )
    db.add(new_claim)
    await db.flush()
    
    # Mark old claim as superseded
    old_claim.is_current = False
    old_claim.superseded_by = new_claim.id
    await db.flush()
    
    return new_claim


@router.delete("/claims/{claim_id}", status_code=204)
async def delete_claim(
    claim_id: str,
    db: AsyncSession = Depends(get_session),
):
    """Delete a claim."""
    result = await db.execute(select(Claim).where(Claim.id == claim_id))
    claim = result.scalar_one_or_none()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    await db.delete(claim)
