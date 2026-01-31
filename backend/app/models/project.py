"""
Project model - the primary isolation boundary.

Projects span all services but CommandCentral owns the entity and state.
"""

from sqlalchemy import Column, String, Text, DateTime, JSON, Enum as SQLEnum
from sqlalchemy.sql import func
from datetime import datetime
import uuid
import enum


from ..database import Base


class ProjectState(str, enum.Enum):
    """Project lifecycle states."""
    PROPOSED = "proposed"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    KILLED = "killed"


# Valid state transitions
PROJECT_TRANSITIONS = {
    ProjectState.PROPOSED: [ProjectState.ACTIVE, ProjectState.KILLED],
    ProjectState.ACTIVE: [ProjectState.PAUSED, ProjectState.COMPLETED, ProjectState.KILLED],
    ProjectState.PAUSED: [ProjectState.ACTIVE, ProjectState.KILLED],
    ProjectState.COMPLETED: [],  # Terminal state
    ProjectState.KILLED: [],  # Terminal state
}


class Project(Base):
    """
    Project - the primary isolation boundary across all services.

    CommandCentral owns the Project entity. Other services maintain
    projections or references to project_id.
    """

    __tablename__ = "projects"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)

    # State machine
    state = Column(SQLEnum(ProjectState), default=ProjectState.PROPOSED, nullable=False)
    state_changed_at = Column(DateTime, default=func.now())
    state_changed_by = Column(String, nullable=True)  # user_id

    # Ownership
    owner_id = Column(String, nullable=False)  # user_id
    team_ids = Column(JSON, default=list)  # list of user_ids

    # Configuration
    settings = Column(JSON, default=dict)
    extra_data = Column(JSON, default=dict)  # Renamed from 'metadata' (reserved by SQLAlchemy)

    # Repository link (for PIPELZR)
    repo_path = Column(String, nullable=True)
    repo_url = Column(String, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Project {self.slug} ({self.state.value})>"

    def can_transition_to(self, new_state: ProjectState) -> bool:
        """Check if transition to new_state is valid."""
        return new_state in PROJECT_TRANSITIONS.get(self.state, [])

    def allowed_transitions(self) -> list[ProjectState]:
        """Get list of allowed transitions from current state."""
        return PROJECT_TRANSITIONS.get(self.state, [])
