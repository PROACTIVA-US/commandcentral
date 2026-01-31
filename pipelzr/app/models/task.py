"""
Task model - represents an executable unit of work.

Tasks can run locally, in Dagger containers, or in E2B sandboxes.
"""

from sqlalchemy import Column, String, Text, DateTime, JSON, Enum as SQLEnum, Integer
from sqlalchemy.sql import func
import uuid
import enum

from ..database import Base


class TaskState(str, enum.Enum):
    """Task lifecycle states."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(str, enum.Enum):
    """Types of task execution."""
    LOCAL = "local"           # Run in local process
    DAGGER = "dagger"         # Run in Dagger container
    E2B = "e2b"               # Run in E2B sandbox
    SUBPROCESS = "subprocess"  # Run as subprocess


# Valid state transitions
TASK_TRANSITIONS = {
    TaskState.PENDING: [TaskState.QUEUED, TaskState.CANCELLED],
    TaskState.QUEUED: [TaskState.RUNNING, TaskState.CANCELLED],
    TaskState.RUNNING: [TaskState.PAUSED, TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELLED],
    TaskState.PAUSED: [TaskState.RUNNING, TaskState.CANCELLED],
    TaskState.COMPLETED: [],  # Terminal state
    TaskState.FAILED: [TaskState.QUEUED],  # Can retry
    TaskState.CANCELLED: [],  # Terminal state
}


class Task(Base):
    """
    Task - an executable unit of work.

    Tasks are atomic units that can be composed into pipelines.
    They track execution state, outputs, and errors.
    """

    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    # Execution configuration
    task_type = Column(SQLEnum(TaskType), default=TaskType.LOCAL, nullable=False)
    command = Column(Text, nullable=True)  # Command to execute
    script = Column(Text, nullable=True)   # Script content
    working_directory = Column(String, nullable=True)
    environment = Column(JSON, default=dict)  # Environment variables

    # State machine
    state = Column(SQLEnum(TaskState), default=TaskState.PENDING, nullable=False)
    state_changed_at = Column(DateTime, default=func.now())
    
    # Ownership
    project_id = Column(String, nullable=True, index=True)  # CommandCentral project
    pipeline_id = Column(String, nullable=True, index=True)  # Parent pipeline
    agent_id = Column(String, nullable=True, index=True)    # Executing agent

    # Execution tracking
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)

    # Results
    exit_code = Column(Integer, nullable=True)
    stdout = Column(Text, nullable=True)
    stderr = Column(Text, nullable=True)
    result = Column(JSON, nullable=True)  # Structured result
    error = Column(Text, nullable=True)

    # Configuration
    timeout_seconds = Column(Integer, default=300)
    extra_data = Column(JSON, default=dict)  # Renamed from 'metadata' (SQLAlchemy reserved)

    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Task {self.name} ({self.state.value})>"

    def can_transition_to(self, new_state: TaskState) -> bool:
        """Check if transition to new_state is valid."""
        return new_state in TASK_TRANSITIONS.get(self.state, [])

    def allowed_transitions(self) -> list[TaskState]:
        """Get list of allowed transitions from current state."""
        return TASK_TRANSITIONS.get(self.state, [])
