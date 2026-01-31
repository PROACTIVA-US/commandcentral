"""
Pipeline Service - handles pipeline orchestration and execution.
"""

import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from ..models.pipeline import Pipeline, PipelineState, PipelineStage
from ..models.task import Task, TaskState
from .task_service import TaskService
from ..config import get_settings

logger = structlog.get_logger("pipelzr.pipeline_service")
settings = get_settings()


class PipelineService:
    """Service for managing pipeline orchestration."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.task_service = TaskService(session)

    async def create_pipeline(
        self,
        name: str,
        tasks: Optional[List[Dict[str, Any]]] = None,
        dependencies: Optional[Dict[str, List[str]]] = None,
        project_id: Optional[str] = None,
        triggered_by: Optional[str] = None,
        pipeline_type: str = "generic",
        max_parallel: int = 5,
        timeout_seconds: int = 3600,
        stop_on_failure: bool = True,
        extra_data: Optional[dict] = None,
    ) -> Pipeline:
        """Create a new pipeline."""
        pipeline = Pipeline(
            name=name,
            tasks=tasks or [],
            dependencies=dependencies or {},
            project_id=project_id,
            triggered_by=triggered_by,
            pipeline_type=pipeline_type,
            max_parallel=max_parallel,
            timeout_seconds=timeout_seconds,
            stop_on_failure=1 if stop_on_failure else 0,
            total_tasks=len(tasks) if tasks else 0,
            extra_data=extra_data or {},
        )
        self.session.add(pipeline)
        await self.session.flush()
        
        await logger.ainfo(
            "pipeline_created",
            pipeline_id=pipeline.id,
            name=name,
            total_tasks=pipeline.total_tasks,
        )
        
        return pipeline

    async def get_pipeline(self, pipeline_id: str) -> Optional[Pipeline]:
        """Get a pipeline by ID."""
        result = await self.session.execute(
            select(Pipeline).where(Pipeline.id == pipeline_id)
        )
        return result.scalar_one_or_none()

    async def list_pipelines(
        self,
        project_id: Optional[str] = None,
        state: Optional[PipelineState] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Pipeline]:
        """List pipelines with optional filters."""
        query = select(Pipeline)
        
        if project_id:
            query = query.where(Pipeline.project_id == project_id)
        if state:
            query = query.where(Pipeline.state == state)
        
        query = query.order_by(Pipeline.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def transition_state(self, pipeline: Pipeline, new_state: PipelineState) -> bool:
        """Transition pipeline to a new state."""
        if not pipeline.can_transition_to(new_state):
            await logger.awarning(
                "invalid_state_transition",
                pipeline_id=pipeline.id,
                current_state=pipeline.state.value,
                requested_state=new_state.value,
            )
            return False
        
        old_state = pipeline.state
        pipeline.state = new_state
        pipeline.state_changed_at = datetime.utcnow()
        
        await logger.ainfo(
            "pipeline_state_changed",
            pipeline_id=pipeline.id,
            old_state=old_state.value,
            new_state=new_state.value,
        )
        
        return True

    async def start_pipeline(self, pipeline: Pipeline) -> Pipeline:
        """Start pipeline execution."""
        if pipeline.state == PipelineState.DRAFT:
            await self.transition_state(pipeline, PipelineState.PENDING)
        
        await self.transition_state(pipeline, PipelineState.RUNNING)
        pipeline.started_at = datetime.utcnow()
        
        await logger.ainfo(
            "pipeline_started",
            pipeline_id=pipeline.id,
            name=pipeline.name,
        )
        
        return pipeline

    async def execute_pipeline(self, pipeline: Pipeline) -> Pipeline:
        """Execute a pipeline's tasks."""
        await self.start_pipeline(pipeline)
        
        try:
            # Build task execution order based on dependencies
            execution_order = await self._build_execution_order(pipeline)
            
            # Execute tasks in order (respecting dependencies)
            for task_batch in execution_order:
                if pipeline.state != PipelineState.RUNNING:
                    break
                
                # Execute batch in parallel
                await self._execute_batch(pipeline, task_batch)
                
                # Check for failures
                if pipeline.stop_on_failure and pipeline.failed_tasks > 0:
                    await logger.awarning(
                        "pipeline_stopped_on_failure",
                        pipeline_id=pipeline.id,
                        failed_tasks=pipeline.failed_tasks,
                    )
                    await self.transition_state(pipeline, PipelineState.FAILED)
                    break
            
            # Complete pipeline if all tasks done
            if pipeline.state == PipelineState.RUNNING:
                if pipeline.failed_tasks > 0:
                    await self.transition_state(pipeline, PipelineState.FAILED)
                else:
                    await self.transition_state(pipeline, PipelineState.COMPLETED)
            
        except asyncio.TimeoutError:
            pipeline.error = "Pipeline timed out"
            await self.transition_state(pipeline, PipelineState.FAILED)
            
        except Exception as e:
            pipeline.error = str(e)
            await self.transition_state(pipeline, PipelineState.FAILED)
            
            await logger.aerror(
                "pipeline_execution_failed",
                pipeline_id=pipeline.id,
                error=str(e),
            )
        
        finally:
            pipeline.completed_at = datetime.utcnow()
            if pipeline.started_at:
                pipeline.duration_ms = int(
                    (pipeline.completed_at - pipeline.started_at).total_seconds() * 1000
                )
            pipeline.update_progress()
        
        return pipeline

    async def _build_execution_order(self, pipeline: Pipeline) -> List[List[Dict[str, Any]]]:
        """
        Build task execution order based on dependencies.
        
        Returns list of batches, where each batch can run in parallel.
        """
        if not pipeline.tasks:
            return []
        
        # Simple topological sort
        tasks_by_name = {t.get("name"): t for t in pipeline.tasks}
        dependencies = pipeline.dependencies or {}
        
        # Track completed tasks
        completed = set()
        batches = []
        
        while len(completed) < len(pipeline.tasks):
            # Find tasks with all dependencies satisfied
            batch = []
            for task in pipeline.tasks:
                task_name = task.get("name")
                if task_name in completed:
                    continue
                
                task_deps = dependencies.get(task_name, [])
                if all(dep in completed for dep in task_deps):
                    batch.append(task)
            
            if not batch:
                # Circular dependency or missing tasks
                await logger.aerror(
                    "dependency_resolution_failed",
                    pipeline_id=pipeline.id,
                    remaining=len(pipeline.tasks) - len(completed),
                )
                break
            
            batches.append(batch)
            for task in batch:
                completed.add(task.get("name"))
        
        return batches

    async def _execute_batch(self, pipeline: Pipeline, task_batch: List[Dict[str, Any]]):
        """Execute a batch of tasks in parallel."""
        # Limit concurrency
        semaphore = asyncio.Semaphore(pipeline.max_parallel)
        
        async def run_task(task_def: Dict[str, Any]):
            async with semaphore:
                task = await self.task_service.create_task(
                    name=task_def.get("name", "unnamed"),
                    command=task_def.get("command"),
                    script=task_def.get("script"),
                    project_id=pipeline.project_id,
                    pipeline_id=pipeline.id,
                    timeout_seconds=task_def.get("timeout_seconds", 300),
                )
                
                result = await self.task_service.execute_task(task)
                
                if result.state == TaskState.COMPLETED:
                    pipeline.completed_tasks += 1
                else:
                    pipeline.failed_tasks += 1
                
                pipeline.update_progress()
                return result
        
        await asyncio.gather(
            *[run_task(task_def) for task_def in task_batch],
            return_exceptions=True,
        )

    async def pause_pipeline(self, pipeline: Pipeline) -> bool:
        """Pause a running pipeline."""
        if pipeline.state != PipelineState.RUNNING:
            return False
        return await self.transition_state(pipeline, PipelineState.PAUSED)

    async def resume_pipeline(self, pipeline: Pipeline) -> bool:
        """Resume a paused pipeline."""
        if pipeline.state != PipelineState.PAUSED:
            return False
        return await self.transition_state(pipeline, PipelineState.RUNNING)

    async def cancel_pipeline(self, pipeline: Pipeline) -> bool:
        """Cancel a pipeline."""
        if pipeline.state in [PipelineState.COMPLETED, PipelineState.CANCELLED]:
            return False
        
        # Cancel all running tasks
        tasks = await self.task_service.list_tasks(
            pipeline_id=pipeline.id,
            state=TaskState.RUNNING,
        )
        for task in tasks:
            await self.task_service.cancel_task(task)
        
        return await self.transition_state(pipeline, PipelineState.CANCELLED)

    async def retry_pipeline(self, pipeline: Pipeline) -> Optional[Pipeline]:
        """Retry a failed pipeline."""
        if pipeline.state != PipelineState.FAILED:
            return None
        
        # Reset counters
        pipeline.completed_tasks = 0
        pipeline.failed_tasks = 0
        pipeline.progress_percent = 0.0
        pipeline.error = None
        
        await self.transition_state(pipeline, PipelineState.PENDING)
        return await self.execute_pipeline(pipeline)
