"""
Goal model - hierarchical objectives with progress tracking.

Goals form a tree structure and can be linked to hypotheses,
ventures, and other strategic elements.
"""

from sqlalchemy import Column, String, Text, DateTime, JSON, Enum as SQLEnum, Float, ForeignKey
from sqlalchemy.sql import func
from datetime import datetime
import uuid
import enum

from ..database import Base


class GoalState(str, enum.Enum):
    """Goal lifecycle states."""
    DRAFT = "draft"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    ACHIEVED = "achieved"
    ABANDONED = "abandoned"


# Valid state transitions
GOAL_TRANSITIONS = {
    GoalState.DRAFT: [GoalState.ACTIVE, GoalState.ABANDONED],
    GoalState.ACTIVE: [GoalState.ON_HOLD, GoalState.ACHIEVED, GoalState.ABANDONED],
    GoalState.ON_HOLD: [GoalState.ACTIVE, GoalState.ABANDONED],
    GoalState.ACHIEVED: [],  # Terminal state
    GoalState.ABANDONED: [],  # Terminal state
}


class Goal(Base):
    """
    Goal - a strategic objective in the hierarchy.

    Goals can have parent goals (forming a tree) and are linked
    to hypotheses, ventures, and progress metrics.
    """

    __tablename__ = "goals"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Hierarchy
    parent_id = Column(String, ForeignKey("goals.id"), nullable=True, index=True)
    project_id = Column(String, nullable=True, index=True)  # Links to CommandCentral project
    
    # Core fields
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    success_criteria = Column(Text, nullable=True)  # How do we know we've achieved this?
    
    # State machine
    state = Column(SQLEnum(GoalState), default=GoalState.DRAFT, nullable=False)
    state_changed_at = Column(DateTime, default=func.now())
    state_changed_by = Column(String, nullable=True)  # user_id
    
    # Progress tracking
    progress = Column(Float, default=0.0)  # 0.0 to 1.0
    progress_notes = Column(Text, nullable=True)
    
    # Timeline
    target_date = Column(DateTime, nullable=True)
    achieved_date = Column(DateTime, nullable=True)
    
    # Priority and ordering
    priority = Column(String, default="medium")  # low, medium, high, critical
    sort_order = Column(Float, default=0.0)  # For manual ordering
    
    # Ownership
    owner_id = Column(String, nullable=True)  # user_id
    stakeholder_ids = Column(JSON, default=list)  # list of user_ids
    
    # Linked entities
    hypothesis_ids = Column(JSON, default=list)  # list of hypothesis IDs
    venture_ids = Column(JSON, default=list)  # list of venture IDs
    
    # Extra data
    tags = Column(JSON, default=list)
    extra_data = Column(JSON, default=dict)  # Renamed from 'metadata' (reserved by SQLAlchemy)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Goal {self.title[:30]} ({self.state.value}) {self.progress*100:.0f}%>"

    def can_transition_to(self, new_state: GoalState) -> bool:
        """Check if transition to new_state is valid."""
        return new_state in GOAL_TRANSITIONS.get(self.state, [])

    def allowed_transitions(self) -> list[GoalState]:
        """Get list of allowed transitions from current state."""
        return GOAL_TRANSITIONS.get(self.state, [])
