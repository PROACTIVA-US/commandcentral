"""
Decision primitive model.

Decisions follow a governed state machine:
draft → active → decided → archived
"""

from sqlalchemy import Column, String, Text, DateTime, JSON, Enum as SQLEnum, ForeignKey
from sqlalchemy.sql import func
from datetime import datetime
import uuid
import enum

from ..database import Base


class DecisionState(str, enum.Enum):
    """Decision lifecycle states."""
    DRAFT = "draft"
    ACTIVE = "active"
    DECIDED = "decided"
    ARCHIVED = "archived"


# Valid state transitions
DECISION_TRANSITIONS = {
    DecisionState.DRAFT: [DecisionState.ACTIVE],
    DecisionState.ACTIVE: [DecisionState.DECIDED, DecisionState.ARCHIVED],
    DecisionState.DECIDED: [DecisionState.ARCHIVED],
    DecisionState.ARCHIVED: [],  # Terminal state
}

# Transition requirements
TRANSITION_REQUIREMENTS = {
    (DecisionState.DRAFT, DecisionState.ACTIVE): ["question", "options"],
    (DecisionState.ACTIVE, DecisionState.DECIDED): ["selected_option", "rationale"],
}


class Decision(Base):
    """
    Decision primitive with governed state machine.

    Represents a decision that must go through proper governance
    before being finalized.
    """

    __tablename__ = "decisions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"), nullable=False, index=True)

    # Core fields
    title = Column(String, nullable=False)
    question = Column(Text, nullable=True)  # Required for activation
    context = Column(Text, nullable=True)

    # Options
    options = Column(JSON, default=list)  # List of option objects

    # Decision outcome (set when decided)
    selected_option = Column(String, nullable=True)
    rationale = Column(Text, nullable=True)

    # State machine
    state = Column(SQLEnum(DecisionState), default=DecisionState.DRAFT, nullable=False)
    state_changed_at = Column(DateTime, default=func.now())
    state_changed_by = Column(String, nullable=True)  # user_id

    # Relationships
    related_decision_ids = Column(JSON, default=list)
    related_hypothesis_ids = Column(JSON, default=list)  # Links to IDEALZR
    related_evidence_ids = Column(JSON, default=list)  # Links to IDEALZR

    # Tags and metadata
    tags = Column(JSON, default=list)
    extra_data = Column(JSON, default=dict)

    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    decided_at = Column(DateTime, nullable=True)

    # Ownership
    created_by = Column(String, nullable=False)  # user_id
    decided_by = Column(String, nullable=True)  # user_id

    def __repr__(self):
        return f"<Decision {self.title[:30]} ({self.state.value})>"

    def can_transition_to(self, new_state: DecisionState) -> bool:
        """Check if transition to new_state is valid."""
        return new_state in DECISION_TRANSITIONS.get(self.state, [])

    def allowed_transitions(self) -> list[DecisionState]:
        """Get list of allowed transitions from current state."""
        return DECISION_TRANSITIONS.get(self.state, [])

    def check_transition_requirements(self, new_state: DecisionState) -> tuple[bool, list[str]]:
        """
        Check if all requirements are met for a transition.

        Returns (is_valid, list_of_missing_fields)
        """
        requirements = TRANSITION_REQUIREMENTS.get((self.state, new_state), [])
        missing = []

        for field in requirements:
            value = getattr(self, field, None)
            if value is None or (isinstance(value, (list, dict, str)) and not value):
                missing.append(field)

        return len(missing) == 0, missing
