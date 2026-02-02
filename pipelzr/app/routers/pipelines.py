"""
Pipeline orchestration endpoints.

Includes:
- Standard pipeline CRUD and execution
- YAML pipeline loading, validation, and triggering
- Credential validation
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
import json

from ..database import get_session
from ..models.pipeline import PipelineState
from ..services.pipeline_service import PipelineService
from ..services.pipeline_loader import pipeline_loader
from ..services.pipeline_validator import pipeline_validator
from ..services.pipeline_executor import pipeline_executor, StageStatus

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


# =============================================================================
# YAML Pipeline Endpoints
# =============================================================================


class YamlPipelineInfo(BaseModel):
    """Info about an available YAML pipeline."""
    filename: str
    name: str
    display_name: str
    description: str
    version: str
    category: str
    stage_count: int


class ValidationRequest(BaseModel):
    """Request to validate a pipeline YAML."""
    yaml_content: str
    validate_credentials: bool = True


class ValidationResponse(BaseModel):
    """Response from pipeline validation."""
    valid: bool
    errors: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    credential_status: Dict[str, Any]
    estimated_duration_seconds: int


class TriggerRequest(BaseModel):
    """Request to trigger a YAML pipeline."""
    input_params: Dict[str, Any] = {}
    auto_approval: bool = False
    validate_credentials: bool = True


class TriggerResponse(BaseModel):
    """Response from pipeline trigger."""
    success: bool
    pipeline_name: str
    execution_id: str
    stage_results: Dict[str, Any]
    outputs: Dict[str, Any]
    error: Optional[str]
    duration_ms: int


class CredentialValidationResponse(BaseModel):
    """Response from credential validation."""
    all_valid: bool
    credentials: Dict[str, Any]


@router.get("/yaml/available", response_model=List[YamlPipelineInfo])
async def list_yaml_pipelines():
    """List all available YAML pipeline definitions."""
    pipelines = pipeline_loader.list_available_pipelines()
    return [YamlPipelineInfo(**p) for p in pipelines]


@router.get("/yaml/{pipeline_name}/definition")
async def get_yaml_pipeline_definition(pipeline_name: str):
    """Get raw YAML pipeline definition by name."""
    definition = pipeline_loader.get_pipeline_definition(pipeline_name)
    if not definition:
        raise HTTPException(status_code=404, detail=f"Pipeline '{pipeline_name}' not found")
    return definition


@router.post("/yaml/validate", response_model=ValidationResponse)
async def validate_yaml_pipeline(body: ValidationRequest):
    """Validate a pipeline YAML definition.

    Checks:
    - YAML syntax
    - Schema structure
    - Stage dependencies (no cycles)
    - Template syntax
    - API credentials (if validate_credentials=true)
    """
    result = await pipeline_validator.validate(
        yaml_content=body.yaml_content,
        validate_credentials=body.validate_credentials
    )
    return ValidationResponse(
        valid=result.valid,
        errors=[e.to_dict() for e in result.errors],
        warnings=[w.to_dict() for w in result.warnings],
        credential_status=result.credential_status,
        estimated_duration_seconds=result.estimated_duration_seconds
    )


@router.post("/yaml/validate-credentials", response_model=CredentialValidationResponse)
async def validate_credentials():
    """Validate all configured API credentials.

    Checks:
    - GEMINI_API_KEY
    - ANTHROPIC_API_KEY
    - GITHUB_TOKEN

    Returns status for each credential.
    """
    # Create a minimal pipeline to trigger credential validation
    yaml_content = """
name: credential-check
stages:
  - id: gemini
    name: Gemini Check
    persona: vision-reviewer
    config:
      model: gemini-3-flash-preview
  - id: claude
    name: Claude Check
    persona: reviewer
    config:
      model: claude-sonnet-4-20250514
  - id: github
    name: GitHub Check
    type: action
    action: git.create_pr
"""
    result = await pipeline_validator.validate(
        yaml_content=yaml_content,
        validate_credentials=True
    )

    all_valid = all(v.get("valid", False) for v in result.credential_status.values())

    return CredentialValidationResponse(
        all_valid=all_valid,
        credentials=result.credential_status
    )


@router.post("/yaml/{pipeline_name}/trigger", response_model=TriggerResponse)
async def trigger_yaml_pipeline(
    pipeline_name: str,
    body: TriggerRequest,
    background_tasks: BackgroundTasks
):
    """Trigger a YAML pipeline by name.

    Loads the pipeline from the pipelines directory, validates it,
    and executes it with the provided input parameters.

    Args:
        pipeline_name: Name of the pipeline (without .yaml extension)
        body.input_params: Input parameters matching the pipeline's input schema
        body.auto_approval: Skip approval gates for autonomous execution
        body.validate_credentials: Validate API keys before execution

    Returns:
        Execution result with stage outputs and any errors.
    """
    import uuid

    # Find the pipeline file
    filename = f"{pipeline_name}.yaml"

    try:
        # Load and validate
        pipeline_def, validation = await pipeline_loader.load_from_file(
            filename,
            validate=True,
            validate_credentials=body.validate_credentials
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Pipeline '{pipeline_name}' not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Generate execution ID
    execution_id = str(uuid.uuid4())

    # Execute pipeline
    result = await pipeline_executor.execute(
        pipeline=pipeline_def,
        input_params=body.input_params,
        auto_approval=body.auto_approval
    )

    return TriggerResponse(
        success=result.success,
        pipeline_name=pipeline_name,
        execution_id=execution_id,
        stage_results={k: v.to_dict() for k, v in result.stage_results.items()},
        outputs=result.outputs,
        error=result.error,
        duration_ms=result.duration_ms
    )


@router.post("/yaml/run")
async def run_yaml_pipeline(
    body: Dict[str, Any]
):
    """Run a pipeline from raw YAML content.

    Args:
        body.yaml_content: Raw YAML pipeline definition
        body.input_params: Input parameters
        body.auto_approval: Skip approval gates
        body.validate_credentials: Validate API keys

    Returns:
        Execution result.
    """
    import uuid

    yaml_content = body.get("yaml_content")
    if not yaml_content:
        raise HTTPException(status_code=400, detail="yaml_content is required")

    input_params = body.get("input_params", {})
    auto_approval = body.get("auto_approval", False)
    validate_credentials = body.get("validate_credentials", True)

    try:
        pipeline_def, validation = await pipeline_loader.load_from_yaml(
            yaml_content,
            validate=True,
            validate_credentials=validate_credentials
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    execution_id = str(uuid.uuid4())

    result = await pipeline_executor.execute(
        pipeline=pipeline_def,
        input_params=input_params,
        auto_approval=auto_approval
    )

    return {
        "success": result.success,
        "execution_id": execution_id,
        "stage_results": {k: v.to_dict() for k, v in result.stage_results.items()},
        "outputs": result.outputs,
        "error": result.error,
        "duration_ms": result.duration_ms
    }


# Progress tracking for streaming
_execution_progress: Dict[str, List[Dict]] = {}


@router.get("/yaml/execution/{execution_id}/stream")
async def stream_execution_progress(execution_id: str):
    """Stream execution progress as Server-Sent Events.

    Connect to this endpoint before triggering a pipeline to
    receive real-time progress updates.
    """
    async def event_generator():
        # Initialize progress list if not exists
        if execution_id not in _execution_progress:
            _execution_progress[execution_id] = []

        last_index = 0
        timeout = 600  # 10 minute timeout
        elapsed = 0

        while elapsed < timeout:
            # Check for new events
            events = _execution_progress.get(execution_id, [])
            if len(events) > last_index:
                for event in events[last_index:]:
                    yield f"data: {json.dumps(event)}\n\n"
                last_index = len(events)

                # Check if completed
                if events and events[-1].get("status") in ["completed", "failed"]:
                    break

            await asyncio.sleep(0.5)
            elapsed += 0.5

        # Cleanup
        if execution_id in _execution_progress:
            del _execution_progress[execution_id]

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
