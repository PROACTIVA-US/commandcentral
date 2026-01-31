"""
Task management endpoints.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..models.task import TaskState, TaskType
from ..services.task_service import TaskService

router = APIRouter()


class TaskCreate(BaseModel):
    """Request body for creating a task."""
    name: str
    description: Optional[str] = None
    command: Optional[str] = None
    script: Optional[str] = None
    task_type: TaskType = TaskType.LOCAL
    project_id: Optional[str] = None
    pipeline_id: Optional[str] = None
    working_directory: Optional[str] = None
    environment: Optional[dict] = None
    timeout_seconds: int = 300
    extra_data: Optional[dict] = None


class TaskResponse(BaseModel):
    """Response body for a task."""
    id: str
    name: str
    description: Optional[str]
    task_type: str
    state: str
    project_id: Optional[str]
    pipeline_id: Optional[str]
    started_at: Optional[str]
    completed_at: Optional[str]
    duration_ms: Optional[int]
    exit_code: Optional[int]
    error: Optional[str]
    created_at: str


class TaskExecuteRequest(BaseModel):
    """Request body for executing a task."""
    async_execution: bool = False


class TaskStateTransition(BaseModel):
    """Request body for state transition."""
    new_state: TaskState


@router.post("", response_model=TaskResponse)
async def create_task(
    body: TaskCreate,
    session: AsyncSession = Depends(get_session),
):
    """Create a new task."""
    service = TaskService(session)
    task = await service.create_task(
        name=body.name,
        command=body.command,
        script=body.script,
        task_type=body.task_type,
        project_id=body.project_id,
        pipeline_id=body.pipeline_id,
        working_directory=body.working_directory,
        environment=body.environment,
        timeout_seconds=body.timeout_seconds,
        extra_data=body.extra_data,
    )
    
    return TaskResponse(
        id=task.id,
        name=task.name,
        description=task.description,
        task_type=task.task_type.value,
        state=task.state.value,
        project_id=task.project_id,
        pipeline_id=task.pipeline_id,
        started_at=task.started_at.isoformat() if task.started_at else None,
        completed_at=task.completed_at.isoformat() if task.completed_at else None,
        duration_ms=task.duration_ms,
        exit_code=task.exit_code,
        error=task.error,
        created_at=task.created_at.isoformat(),
    )


@router.get("", response_model=List[TaskResponse])
async def list_tasks(
    project_id: Optional[str] = None,
    pipeline_id: Optional[str] = None,
    state: Optional[TaskState] = None,
    limit: int = 100,
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
):
    """List tasks with optional filters."""
    service = TaskService(session)
    tasks = await service.list_tasks(
        project_id=project_id,
        pipeline_id=pipeline_id,
        state=state,
        limit=limit,
        offset=offset,
    )
    
    return [
        TaskResponse(
            id=task.id,
            name=task.name,
            description=task.description,
            task_type=task.task_type.value,
            state=task.state.value,
            project_id=task.project_id,
            pipeline_id=task.pipeline_id,
            started_at=task.started_at.isoformat() if task.started_at else None,
            completed_at=task.completed_at.isoformat() if task.completed_at else None,
            duration_ms=task.duration_ms,
            exit_code=task.exit_code,
            error=task.error,
            created_at=task.created_at.isoformat(),
        )
        for task in tasks
    ]


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Get a task by ID."""
    service = TaskService(session)
    task = await service.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return TaskResponse(
        id=task.id,
        name=task.name,
        description=task.description,
        task_type=task.task_type.value,
        state=task.state.value,
        project_id=task.project_id,
        pipeline_id=task.pipeline_id,
        started_at=task.started_at.isoformat() if task.started_at else None,
        completed_at=task.completed_at.isoformat() if task.completed_at else None,
        duration_ms=task.duration_ms,
        exit_code=task.exit_code,
        error=task.error,
        created_at=task.created_at.isoformat(),
    )


@router.post("/{task_id}/execute", response_model=TaskResponse)
async def execute_task(
    task_id: str,
    body: TaskExecuteRequest = TaskExecuteRequest(),
    session: AsyncSession = Depends(get_session),
):
    """Execute a task."""
    service = TaskService(session)
    task = await service.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = await service.execute_task(task)
    
    return TaskResponse(
        id=task.id,
        name=task.name,
        description=task.description,
        task_type=task.task_type.value,
        state=task.state.value,
        project_id=task.project_id,
        pipeline_id=task.pipeline_id,
        started_at=task.started_at.isoformat() if task.started_at else None,
        completed_at=task.completed_at.isoformat() if task.completed_at else None,
        duration_ms=task.duration_ms,
        exit_code=task.exit_code,
        error=task.error,
        created_at=task.created_at.isoformat(),
    )


@router.post("/{task_id}/cancel", response_model=TaskResponse)
async def cancel_task(
    task_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Cancel a task."""
    service = TaskService(session)
    task = await service.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    success = await service.cancel_task(task)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot cancel task in current state")
    
    return TaskResponse(
        id=task.id,
        name=task.name,
        description=task.description,
        task_type=task.task_type.value,
        state=task.state.value,
        project_id=task.project_id,
        pipeline_id=task.pipeline_id,
        started_at=task.started_at.isoformat() if task.started_at else None,
        completed_at=task.completed_at.isoformat() if task.completed_at else None,
        duration_ms=task.duration_ms,
        exit_code=task.exit_code,
        error=task.error,
        created_at=task.created_at.isoformat(),
    )


@router.post("/{task_id}/retry", response_model=TaskResponse)
async def retry_task(
    task_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Retry a failed task."""
    service = TaskService(session)
    task = await service.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = await service.retry_task(task)
    if not task:
        raise HTTPException(status_code=400, detail="Cannot retry task")
    
    return TaskResponse(
        id=task.id,
        name=task.name,
        description=task.description,
        task_type=task.task_type.value,
        state=task.state.value,
        project_id=task.project_id,
        pipeline_id=task.pipeline_id,
        started_at=task.started_at.isoformat() if task.started_at else None,
        completed_at=task.completed_at.isoformat() if task.completed_at else None,
        duration_ms=task.duration_ms,
        exit_code=task.exit_code,
        error=task.error,
        created_at=task.created_at.isoformat(),
    )
