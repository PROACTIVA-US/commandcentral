"""
Pipeline model - represents a workflow of tasks.

Pipelines orchestrate task execution with dependencies,
parallelization, and error handling.
"""

from sqlalchemy import Column, String, Text, DateTime, JSON, Enum as SQLEnum, Integer, Float
from sqlalchemy.sql import func
import uuid
import enum

from ..database import Base


class PipelineState(str, enum.Enum):
    """Pipeline lifecycle states."""
    DRAFT = "draft"
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PipelineStage(str, enum.Enum):
    """Common pipeline stages."""
    SETUP = "setup"
    BUILD = "build"
    TEST = "test"
    DEPLOY = "deploy"
    VALIDATE = "validate"
    CLEANUP = "cleanup"


# Valid state transitions
PIPELINE_TRANSITIONS = {
    PipelineState.DRAFT: [PipelineState.PENDING, PipelineState.CANCELLED],
    PipelineState.PENDING: [PipelineState.RUNNING, PipelineState.CANCELLED],
    PipelineState.RUNNING: [PipelineState.PAUSED, PipelineState.COMPLETED, PipelineState.FAILED, PipelineState.CANCELLED],
    PipelineState.PAUSED: [PipelineState.RUNNING, PipelineState.CANCELLED],
    PipelineState.COMPLETED: [],  # Terminal state
    PipelineState.FAILED: [PipelineState.PENDING],  # Can retry
    PipelineState.CANCELLED: [],  # Terminal state
}


class Pipeline(Base):
    """
    Pipeline - orchestrates task execution.

    Pipelines define task graphs with dependencies,
    parallel execution, and error handling strategies.
    """

    __tablename__ = "pipelines"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    # Pipeline type
    pipeline_type = Column(String, default="generic")  # generic, build, deploy, etc.
    current_stage = Column(SQLEnum(PipelineStage), nullable=True)

    # Task graph
    tasks = Column(JSON, default=list)         # List of task definitions
    dependencies = Column(JSON, default=dict)  # Task dependency graph
    parallel_groups = Column(JSON, default=list)  # Groups of parallel tasks

    # State machine
    state = Column(SQLEnum(PipelineState), default=PipelineState.DRAFT, nullable=False)
    state_changed_at = Column(DateTime, default=func.now())
    
    # Ownership
    project_id = Column(String, nullable=True, index=True)  # CommandCentral project
    triggered_by = Column(String, nullable=True)  # user_id or system

    # Execution tracking
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    
    # Progress
    total_tasks = Column(Integer, default=0)
    completed_tasks = Column(Integer, default=0)
    failed_tasks = Column(Integer, default=0)
    progress_percent = Column(Float, default=0.0)

    # Results
    outputs = Column(JSON, default=dict)  # Pipeline outputs
    artifacts = Column(JSON, default=list)  # Generated artifacts
    error = Column(Text, nullable=True)

    # Configuration
    max_parallel = Column(Integer, default=5)
    timeout_seconds = Column(Integer, default=3600)
    retry_failed = Column(Integer, default=1)  # Number of retries for failed tasks
    stop_on_failure = Column(Integer, default=1)  # Boolean: stop pipeline on first failure
    extra_data = Column(JSON, default=dict)  # Renamed from 'metadata' (SQLAlchemy reserved)

    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Pipeline {self.name} ({self.state.value})>"

    def can_transition_to(self, new_state: PipelineState) -> bool:
        """Check if transition to new_state is valid."""
        return new_state in PIPELINE_TRANSITIONS.get(self.state, [])

    def allowed_transitions(self) -> list[PipelineState]:
        """Get list of allowed transitions from current state."""
        return PIPELINE_TRANSITIONS.get(self.state, [])
    
    def update_progress(self):
        """Update progress based on completed/failed tasks."""
        if self.total_tasks > 0:
            done = self.completed_tasks + self.failed_tasks
            self.progress_percent = (done / self.total_tasks) * 100
