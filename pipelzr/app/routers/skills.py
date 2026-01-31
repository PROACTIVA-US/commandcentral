"""
Skill management endpoints.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_session
from ..models.skill import Skill, SkillCategory

router = APIRouter()


class SkillCreate(BaseModel):
    """Request body for creating a skill."""
    name: str
    slug: str
    description: Optional[str] = None
    category: SkillCategory
    tags: Optional[List[str]] = None
    inputs: Optional[List[dict]] = None
    outputs: Optional[List[dict]] = None
    implementation: Optional[str] = None
    implementation_type: str = "python"
    dependencies: Optional[List[str]] = None
    system_prompt: Optional[str] = None
    examples: Optional[List[dict]] = None
    requires_approval: bool = False
    cost_estimate: float = 0.0
    timeout_seconds: int = 60
    extra_data: Optional[dict] = None


class SkillUpdate(BaseModel):
    """Request body for updating a skill."""
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    inputs: Optional[List[dict]] = None
    outputs: Optional[List[dict]] = None
    implementation: Optional[str] = None
    system_prompt: Optional[str] = None
    examples: Optional[List[dict]] = None
    enabled: Optional[bool] = None
    requires_approval: Optional[bool] = None
    cost_estimate: Optional[float] = None
    timeout_seconds: Optional[int] = None


class SkillResponse(BaseModel):
    """Response body for a skill."""
    id: str
    name: str
    slug: str
    description: Optional[str]
    category: str
    tags: List[str]
    implementation_type: str
    enabled: bool
    requires_approval: bool
    cost_estimate: float
    invocation_count: int
    success_count: int
    failure_count: int
    success_rate: float
    avg_duration_ms: float
    version: str
    created_at: str
    updated_at: str


class SkillInvokeRequest(BaseModel):
    """Request body for invoking a skill."""
    inputs: dict = {}
    context: Optional[dict] = None


class SkillInvokeResponse(BaseModel):
    """Response body for skill invocation."""
    skill_id: str
    success: bool
    outputs: Optional[dict] = None
    error: Optional[str] = None
    duration_ms: float


@router.post("", response_model=SkillResponse)
async def create_skill(
    body: SkillCreate,
    session: AsyncSession = Depends(get_session),
):
    """Create a new skill."""
    # Check if slug already exists
    existing = await session.execute(
        select(Skill).where(Skill.slug == body.slug)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Skill with this slug already exists")
    
    skill = Skill(
        name=body.name,
        slug=body.slug,
        description=body.description,
        category=body.category,
        tags=body.tags or [],
        inputs=body.inputs or [],
        outputs=body.outputs or [],
        implementation=body.implementation,
        implementation_type=body.implementation_type,
        dependencies=body.dependencies or [],
        system_prompt=body.system_prompt,
        examples=body.examples or [],
        requires_approval=1 if body.requires_approval else 0,
        cost_estimate=body.cost_estimate,
        timeout_seconds=body.timeout_seconds,
        extra_data=body.extra_data or {},
    )
    session.add(skill)
    await session.flush()
    
    return SkillResponse(
        id=skill.id,
        name=skill.name,
        slug=skill.slug,
        description=skill.description,
        category=skill.category.value,
        tags=skill.tags,
        implementation_type=skill.implementation_type,
        enabled=bool(skill.enabled),
        requires_approval=bool(skill.requires_approval),
        cost_estimate=skill.cost_estimate,
        invocation_count=skill.invocation_count,
        success_count=skill.success_count,
        failure_count=skill.failure_count,
        success_rate=skill.success_rate,
        avg_duration_ms=skill.avg_duration_ms,
        version=skill.version,
        created_at=skill.created_at.isoformat(),
        updated_at=skill.updated_at.isoformat(),
    )


@router.get("", response_model=List[SkillResponse])
async def list_skills(
    category: Optional[SkillCategory] = None,
    enabled: Optional[bool] = None,
    tag: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
):
    """List skills with optional filters."""
    query = select(Skill)
    
    if category:
        query = query.where(Skill.category == category)
    if enabled is not None:
        query = query.where(Skill.enabled == (1 if enabled else 0))
    
    query = query.order_by(Skill.name).limit(limit).offset(offset)
    result = await session.execute(query)
    skills = list(result.scalars().all())
    
    # Filter by tag in Python (JSON field)
    if tag:
        skills = [s for s in skills if tag in (s.tags or [])]
    
    return [
        SkillResponse(
            id=skill.id,
            name=skill.name,
            slug=skill.slug,
            description=skill.description,
            category=skill.category.value,
            tags=skill.tags,
            implementation_type=skill.implementation_type,
            enabled=bool(skill.enabled),
            requires_approval=bool(skill.requires_approval),
            cost_estimate=skill.cost_estimate,
            invocation_count=skill.invocation_count,
            success_count=skill.success_count,
            failure_count=skill.failure_count,
            success_rate=skill.success_rate,
            avg_duration_ms=skill.avg_duration_ms,
            version=skill.version,
            created_at=skill.created_at.isoformat(),
            updated_at=skill.updated_at.isoformat(),
        )
        for skill in skills
    ]


@router.get("/{skill_id}", response_model=SkillResponse)
async def get_skill(
    skill_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Get a skill by ID."""
    result = await session.execute(
        select(Skill).where(Skill.id == skill_id)
    )
    skill = result.scalar_one_or_none()
    
    if not skill:
        # Try by slug
        result = await session.execute(
            select(Skill).where(Skill.slug == skill_id)
        )
        skill = result.scalar_one_or_none()
    
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    
    return SkillResponse(
        id=skill.id,
        name=skill.name,
        slug=skill.slug,
        description=skill.description,
        category=skill.category.value,
        tags=skill.tags,
        implementation_type=skill.implementation_type,
        enabled=bool(skill.enabled),
        requires_approval=bool(skill.requires_approval),
        cost_estimate=skill.cost_estimate,
        invocation_count=skill.invocation_count,
        success_count=skill.success_count,
        failure_count=skill.failure_count,
        success_rate=skill.success_rate,
        avg_duration_ms=skill.avg_duration_ms,
        version=skill.version,
        created_at=skill.created_at.isoformat(),
        updated_at=skill.updated_at.isoformat(),
    )


@router.patch("/{skill_id}", response_model=SkillResponse)
async def update_skill(
    skill_id: str,
    body: SkillUpdate,
    session: AsyncSession = Depends(get_session),
):
    """Update a skill."""
    result = await session.execute(
        select(Skill).where(Skill.id == skill_id)
    )
    skill = result.scalar_one_or_none()
    
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    
    # Update fields if provided
    if body.name is not None:
        skill.name = body.name
    if body.description is not None:
        skill.description = body.description
    if body.tags is not None:
        skill.tags = body.tags
    if body.inputs is not None:
        skill.inputs = body.inputs
    if body.outputs is not None:
        skill.outputs = body.outputs
    if body.implementation is not None:
        skill.implementation = body.implementation
    if body.system_prompt is not None:
        skill.system_prompt = body.system_prompt
    if body.examples is not None:
        skill.examples = body.examples
    if body.enabled is not None:
        skill.enabled = 1 if body.enabled else 0
    if body.requires_approval is not None:
        skill.requires_approval = 1 if body.requires_approval else 0
    if body.cost_estimate is not None:
        skill.cost_estimate = body.cost_estimate
    if body.timeout_seconds is not None:
        skill.timeout_seconds = body.timeout_seconds
    
    await session.flush()
    
    return SkillResponse(
        id=skill.id,
        name=skill.name,
        slug=skill.slug,
        description=skill.description,
        category=skill.category.value,
        tags=skill.tags,
        implementation_type=skill.implementation_type,
        enabled=bool(skill.enabled),
        requires_approval=bool(skill.requires_approval),
        cost_estimate=skill.cost_estimate,
        invocation_count=skill.invocation_count,
        success_count=skill.success_count,
        failure_count=skill.failure_count,
        success_rate=skill.success_rate,
        avg_duration_ms=skill.avg_duration_ms,
        version=skill.version,
        created_at=skill.created_at.isoformat(),
        updated_at=skill.updated_at.isoformat(),
    )


@router.delete("/{skill_id}")
async def delete_skill(
    skill_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Delete a skill."""
    result = await session.execute(
        select(Skill).where(Skill.id == skill_id)
    )
    skill = result.scalar_one_or_none()
    
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    
    await session.delete(skill)
    await session.flush()
    
    return {"status": "deleted", "skill_id": skill_id}


@router.post("/{skill_id}/invoke", response_model=SkillInvokeResponse)
async def invoke_skill(
    skill_id: str,
    body: SkillInvokeRequest,
    session: AsyncSession = Depends(get_session),
):
    """Invoke a skill."""
    import time
    
    result = await session.execute(
        select(Skill).where(Skill.id == skill_id)
    )
    skill = result.scalar_one_or_none()
    
    if not skill:
        # Try by slug
        result = await session.execute(
            select(Skill).where(Skill.slug == skill_id)
        )
        skill = result.scalar_one_or_none()
    
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    
    if not skill.enabled:
        raise HTTPException(status_code=400, detail="Skill is disabled")
    
    start_time = time.perf_counter()
    success = False
    outputs = None
    error = None
    
    try:
        # TODO: Actually execute the skill based on implementation_type
        # For now, just return a mock response
        outputs = {"status": "executed", "inputs": body.inputs}
        success = True
        
    except Exception as e:
        error = str(e)
        success = False
    
    duration_ms = (time.perf_counter() - start_time) * 1000
    
    # Record invocation
    skill.record_invocation(success, duration_ms)
    await session.flush()
    
    return SkillInvokeResponse(
        skill_id=skill.id,
        success=success,
        outputs=outputs,
        error=error,
        duration_ms=duration_ms,
    )
