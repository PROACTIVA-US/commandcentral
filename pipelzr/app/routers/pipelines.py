"""
Pipeline orchestration endpoints.
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..models.pipeline import PipelineState
from ..services.pipeline_service import PipelineService

router = APIRouter()


class PipelineCreate(BaseModel):
    """Request body for creating a pipeline."""
    name: str
    description: Optional[str] = None
    tasks: Optional[List[Dict[str, Any]]] = None
    dependencies: Optional[Dict[str, List[str]]] = None
    project_id: Optional[str] = None
    triggered_by: Optional[str] = None
    pipeline_type: str = "generic"
    max_parallel: int = 5
    timeout_seconds: int = 3600
    stop_on_failure: bool = True
    extra_data: Optional[dict] = None


class PipelineResponse(BaseModel):
    """Response body for a pipeline."""
    id: str
    name: str
    description: Optional[str]
    pipeline_type: str
    state: str
    project_id: Optional[str]
    triggered_by: Optional[str]
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    progress_percent: float
    started_at: Optional[str]
    completed_at: Optional[str]
    duration_ms: Optional[int]
    error: Optional[str]
    created_at: str


@router.post("", response_model=PipelineResponse)
async def create_pipeline(
    body: PipelineCreate,
    session: AsyncSession = Depends(get_session),
):
    """Create a new pipeline."""
    service = PipelineService(session)
    pipeline = await service.create_pipeline(
        name=body.name,
        tasks=body.tasks,
        dependencies=body.dependencies,
        project_id=body.project_id,
        triggered_by=body.triggered_by,
        pipeline_type=body.pipeline_type,
        max_parallel=body.max_parallel,
        timeout_seconds=body.timeout_seconds,
        stop_on_failure=body.stop_on_failure,
        extra_data=body.extra_data,
    )
    
    return PipelineResponse(
        id=pipeline.id,
        name=pipeline.name,
        description=pipeline.description,
        pipeline_type=pipeline.pipeline_type,
        state=pipeline.state.value,
        project_id=pipeline.project_id,
        triggered_by=pipeline.triggered_by,
        total_tasks=pipeline.total_tasks,
        completed_tasks=pipeline.completed_tasks,
        failed_tasks=pipeline.failed_tasks,
        progress_percent=pipeline.progress_percent,
        started_at=pipeline.started_at.isoformat() if pipeline.started_at else None,
        completed_at=pipeline.completed_at.isoformat() if pipeline.completed_at else None,
        duration_ms=pipeline.duration_ms,
        error=pipeline.error,
        created_at=pipeline.created_at.isoformat(),
    )


@router.get("", response_model=List[PipelineResponse])
async def list_pipelines(
    project_id: Optional[str] = None,
    state: Optional[PipelineState] = None,
    limit: int = 100,
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
):
    """List pipelines with optional filters."""
    service = PipelineService(session)
    pipelines = await service.list_pipelines(
        project_id=project_id,
        state=state,
        limit=limit,
        offset=offset,
    )
    
    return [
        PipelineResponse(
            id=pipeline.id,
            name=pipeline.name,
            description=pipeline.description,
            pipeline_type=pipeline.pipeline_type,
            state=pipeline.state.value,
            project_id=pipeline.project_id,
            triggered_by=pipeline.triggered_by,
            total_tasks=pipeline.total_tasks,
            completed_tasks=pipeline.completed_tasks,
            failed_tasks=pipeline.failed_tasks,
            progress_percent=pipeline.progress_percent,
            started_at=pipeline.started_at.isoformat() if pipeline.started_at else None,
            completed_at=pipeline.completed_at.isoformat() if pipeline.completed_at else None,
            duration_ms=pipeline.duration_ms,
            error=pipeline.error,
            created_at=pipeline.created_at.isoformat(),
        )
        for pipeline in pipelines
    ]


@router.get("/{pipeline_id}", response_model=PipelineResponse)
async def get_pipeline(
    pipeline_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Get a pipeline by ID."""
    service = PipelineService(session)
    pipeline = await service.get_pipeline(pipeline_id)
    
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    return PipelineResponse(
        id=pipeline.id,
        name=pipeline.name,
        description=pipeline.description,
        pipeline_type=pipeline.pipeline_type,
        state=pipeline.state.value,
        project_id=pipeline.project_id,
        triggered_by=pipeline.triggered_by,
        total_tasks=pipeline.total_tasks,
        completed_tasks=pipeline.completed_tasks,
        failed_tasks=pipeline.failed_tasks,
        progress_percent=pipeline.progress_percent,
        started_at=pipeline.started_at.isoformat() if pipeline.started_at else None,
        completed_at=pipeline.completed_at.isoformat() if pipeline.completed_at else None,
        duration_ms=pipeline.duration_ms,
        error=pipeline.error,
        created_at=pipeline.created_at.isoformat(),
    )


@router.post("/{pipeline_id}/start", response_model=PipelineResponse)
async def start_pipeline(
    pipeline_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Start a pipeline."""
    service = PipelineService(session)
    pipeline = await service.get_pipeline(pipeline_id)
    
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    pipeline = await service.start_pipeline(pipeline)
    
    return PipelineResponse(
        id=pipeline.id,
        name=pipeline.name,
        description=pipeline.description,
        pipeline_type=pipeline.pipeline_type,
        state=pipeline.state.value,
        project_id=pipeline.project_id,
        triggered_by=pipeline.triggered_by,
        total_tasks=pipeline.total_tasks,
        completed_tasks=pipeline.completed_tasks,
        failed_tasks=pipeline.failed_tasks,
        progress_percent=pipeline.progress_percent,
        started_at=pipeline.started_at.isoformat() if pipeline.started_at else None,
        completed_at=pipeline.completed_at.isoformat() if pipeline.completed_at else None,
        duration_ms=pipeline.duration_ms,
        error=pipeline.error,
        created_at=pipeline.created_at.isoformat(),
    )


@router.post("/{pipeline_id}/execute", response_model=PipelineResponse)
async def execute_pipeline(
    pipeline_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Execute a pipeline (start and run all tasks)."""
    service = PipelineService(session)
    pipeline = await service.get_pipeline(pipeline_id)
    
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    pipeline = await service.execute_pipeline(pipeline)
    
    return PipelineResponse(
        id=pipeline.id,
        name=pipeline.name,
        description=pipeline.description,
        pipeline_type=pipeline.pipeline_type,
        state=pipeline.state.value,
        project_id=pipeline.project_id,
        triggered_by=pipeline.triggered_by,
        total_tasks=pipeline.total_tasks,
        completed_tasks=pipeline.completed_tasks,
        failed_tasks=pipeline.failed_tasks,
        progress_percent=pipeline.progress_percent,
        started_at=pipeline.started_at.isoformat() if pipeline.started_at else None,
        completed_at=pipeline.completed_at.isoformat() if pipeline.completed_at else None,
        duration_ms=pipeline.duration_ms,
        error=pipeline.error,
        created_at=pipeline.created_at.isoformat(),
    )


@router.post("/{pipeline_id}/pause", response_model=PipelineResponse)
async def pause_pipeline(
    pipeline_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Pause a running pipeline."""
    service = PipelineService(session)
    pipeline = await service.get_pipeline(pipeline_id)
    
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    success = await service.pause_pipeline(pipeline)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot pause pipeline in current state")
    
    return PipelineResponse(
        id=pipeline.id,
        name=pipeline.name,
        description=pipeline.description,
        pipeline_type=pipeline.pipeline_type,
        state=pipeline.state.value,
        project_id=pipeline.project_id,
        triggered_by=pipeline.triggered_by,
        total_tasks=pipeline.total_tasks,
        completed_tasks=pipeline.completed_tasks,
        failed_tasks=pipeline.failed_tasks,
        progress_percent=pipeline.progress_percent,
        started_at=pipeline.started_at.isoformat() if pipeline.started_at else None,
        completed_at=pipeline.completed_at.isoformat() if pipeline.completed_at else None,
        duration_ms=pipeline.duration_ms,
        error=pipeline.error,
        created_at=pipeline.created_at.isoformat(),
    )


@router.post("/{pipeline_id}/resume", response_model=PipelineResponse)
async def resume_pipeline(
    pipeline_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Resume a paused pipeline."""
    service = PipelineService(session)
    pipeline = await service.get_pipeline(pipeline_id)
    
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    success = await service.resume_pipeline(pipeline)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot resume pipeline in current state")
    
    return PipelineResponse(
        id=pipeline.id,
        name=pipeline.name,
        description=pipeline.description,
        pipeline_type=pipeline.pipeline_type,
        state=pipeline.state.value,
        project_id=pipeline.project_id,
        triggered_by=pipeline.triggered_by,
        total_tasks=pipeline.total_tasks,
        completed_tasks=pipeline.completed_tasks,
        failed_tasks=pipeline.failed_tasks,
        progress_percent=pipeline.progress_percent,
        started_at=pipeline.started_at.isoformat() if pipeline.started_at else None,
        completed_at=pipeline.completed_at.isoformat() if pipeline.completed_at else None,
        duration_ms=pipeline.duration_ms,
        error=pipeline.error,
        created_at=pipeline.created_at.isoformat(),
    )


@router.post("/{pipeline_id}/cancel", response_model=PipelineResponse)
async def cancel_pipeline(
    pipeline_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Cancel a pipeline."""
    service = PipelineService(session)
    pipeline = await service.get_pipeline(pipeline_id)
    
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    success = await service.cancel_pipeline(pipeline)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot cancel pipeline in current state")
    
    return PipelineResponse(
        id=pipeline.id,
        name=pipeline.name,
        description=pipeline.description,
        pipeline_type=pipeline.pipeline_type,
        state=pipeline.state.value,
        project_id=pipeline.project_id,
        triggered_by=pipeline.triggered_by,
        total_tasks=pipeline.total_tasks,
        completed_tasks=pipeline.completed_tasks,
        failed_tasks=pipeline.failed_tasks,
        progress_percent=pipeline.progress_percent,
        started_at=pipeline.started_at.isoformat() if pipeline.started_at else None,
        completed_at=pipeline.completed_at.isoformat() if pipeline.completed_at else None,
        duration_ms=pipeline.duration_ms,
        error=pipeline.error,
        created_at=pipeline.created_at.isoformat(),
    )


@router.post("/{pipeline_id}/retry", response_model=PipelineResponse)
async def retry_pipeline(
    pipeline_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Retry a failed pipeline."""
    service = PipelineService(session)
    pipeline = await service.get_pipeline(pipeline_id)
    
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    pipeline = await service.retry_pipeline(pipeline)
    if not pipeline:
        raise HTTPException(status_code=400, detail="Cannot retry pipeline")
    
    return PipelineResponse(
        id=pipeline.id,
        name=pipeline.name,
        description=pipeline.description,
        pipeline_type=pipeline.pipeline_type,
        state=pipeline.state.value,
        project_id=pipeline.project_id,
        triggered_by=pipeline.triggered_by,
        total_tasks=pipeline.total_tasks,
        completed_tasks=pipeline.completed_tasks,
        failed_tasks=pipeline.failed_tasks,
        progress_percent=pipeline.progress_percent,
        started_at=pipeline.started_at.isoformat() if pipeline.started_at else None,
        completed_at=pipeline.completed_at.isoformat() if pipeline.completed_at else None,
        duration_ms=pipeline.duration_ms,
        error=pipeline.error,
        created_at=pipeline.created_at.isoformat(),
    )
