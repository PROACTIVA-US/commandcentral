"""
Task Service - handles task execution and lifecycle.
"""

import asyncio
import subprocess
from datetime import datetime
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from ..models.task import Task, TaskState, TaskType
from ..config import get_settings

logger = structlog.get_logger("pipelzr.task_service")
settings = get_settings()


class TaskService:
    """Service for managing task execution."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_task(
        self,
        name: str,
        command: Optional[str] = None,
        script: Optional[str] = None,
        task_type: TaskType = TaskType.LOCAL,
        project_id: Optional[str] = None,
        pipeline_id: Optional[str] = None,
        working_directory: Optional[str] = None,
        environment: Optional[dict] = None,
        timeout_seconds: int = 300,
        extra_data: Optional[dict] = None,
    ) -> Task:
        """Create a new task."""
        task = Task(
            name=name,
            command=command,
            script=script,
            task_type=task_type,
            project_id=project_id,
            pipeline_id=pipeline_id,
            working_directory=working_directory,
            environment=environment or {},
            timeout_seconds=timeout_seconds,
            extra_data=extra_data or {},
        )
        self.session.add(task)
        await self.session.flush()
        
        await logger.ainfo(
            "task_created",
            task_id=task.id,
            name=name,
            task_type=task_type.value,
        )
        
        return task

    async def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        result = await self.session.execute(
            select(Task).where(Task.id == task_id)
        )
        return result.scalar_one_or_none()

    async def list_tasks(
        self,
        project_id: Optional[str] = None,
        pipeline_id: Optional[str] = None,
        state: Optional[TaskState] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Task]:
        """List tasks with optional filters."""
        query = select(Task)
        
        if project_id:
            query = query.where(Task.project_id == project_id)
        if pipeline_id:
            query = query.where(Task.pipeline_id == pipeline_id)
        if state:
            query = query.where(Task.state == state)
        
        query = query.order_by(Task.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def transition_state(self, task: Task, new_state: TaskState) -> bool:
        """Transition task to a new state."""
        if not task.can_transition_to(new_state):
            await logger.awarning(
                "invalid_state_transition",
                task_id=task.id,
                current_state=task.state.value,
                requested_state=new_state.value,
            )
            return False
        
        old_state = task.state
        task.state = new_state
        task.state_changed_at = datetime.utcnow()
        
        await logger.ainfo(
            "task_state_changed",
            task_id=task.id,
            old_state=old_state.value,
            new_state=new_state.value,
        )
        
        return True

    async def execute_task(self, task: Task) -> Task:
        """Execute a task based on its type."""
        if task.state != TaskState.PENDING:
            await self.transition_state(task, TaskState.QUEUED)
        
        await self.transition_state(task, TaskState.RUNNING)
        task.started_at = datetime.utcnow()
        
        try:
            if task.task_type == TaskType.LOCAL:
                await self._execute_local(task)
            elif task.task_type == TaskType.SUBPROCESS:
                await self._execute_subprocess(task)
            elif task.task_type == TaskType.DAGGER:
                await self._execute_dagger(task)
            elif task.task_type == TaskType.E2B:
                await self._execute_e2b(task)
            
            await self.transition_state(task, TaskState.COMPLETED)
            
        except asyncio.TimeoutError:
            task.error = "Task timed out"
            await self.transition_state(task, TaskState.FAILED)
            
        except Exception as e:
            task.error = str(e)
            task.retry_count += 1
            await self.transition_state(task, TaskState.FAILED)
            
            await logger.aerror(
                "task_execution_failed",
                task_id=task.id,
                error=str(e),
            )
        
        finally:
            task.completed_at = datetime.utcnow()
            if task.started_at:
                task.duration_ms = int(
                    (task.completed_at - task.started_at).total_seconds() * 1000
                )
        
        return task

    async def _execute_local(self, task: Task):
        """Execute task as local Python code."""
        # This would execute Python code directly
        # For now, just log
        await logger.ainfo("executing_local_task", task_id=task.id)
        task.result = {"status": "executed"}

    async def _execute_subprocess(self, task: Task):
        """Execute task as a subprocess."""
        if not task.command:
            raise ValueError("No command specified for subprocess task")
        
        process = await asyncio.create_subprocess_shell(
            task.command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=task.working_directory,
            env=task.environment if task.environment else None,
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=task.timeout_seconds,
            )
            
            task.exit_code = process.returncode
            task.stdout = stdout.decode() if stdout else None
            task.stderr = stderr.decode() if stderr else None
            
            if process.returncode != 0:
                raise RuntimeError(f"Process exited with code {process.returncode}")
                
        except asyncio.TimeoutError:
            process.kill()
            raise

    async def _execute_dagger(self, task: Task):
        """Execute task in a Dagger container."""
        if not settings.dagger_enabled:
            raise RuntimeError("Dagger execution is not enabled")
        
        # TODO: Implement Dagger execution
        await logger.ainfo("dagger_execution_not_implemented", task_id=task.id)
        task.result = {"status": "dagger_not_implemented"}

    async def _execute_e2b(self, task: Task):
        """Execute task in an E2B sandbox."""
        if not settings.e2b_enabled:
            raise RuntimeError("E2B execution is not enabled")
        
        # TODO: Implement E2B execution
        await logger.ainfo("e2b_execution_not_implemented", task_id=task.id)
        task.result = {"status": "e2b_not_implemented"}

    async def cancel_task(self, task: Task) -> bool:
        """Cancel a task."""
        if task.state in [TaskState.COMPLETED, TaskState.CANCELLED]:
            return False
        
        return await self.transition_state(task, TaskState.CANCELLED)

    async def retry_task(self, task: Task) -> Optional[Task]:
        """Retry a failed task."""
        if task.state != TaskState.FAILED:
            return None
        
        if task.retry_count >= task.max_retries:
            await logger.awarning(
                "max_retries_exceeded",
                task_id=task.id,
                retry_count=task.retry_count,
                max_retries=task.max_retries,
            )
            return None
        
        await self.transition_state(task, TaskState.QUEUED)
        return await self.execute_task(task)
