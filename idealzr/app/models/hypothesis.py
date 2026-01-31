"""
Hypothesis model - testable assumptions with evidence tracking.

Hypotheses go through a lifecycle from proposal to validation/refutation.
They are linked to evidence that supports or contradicts them.
"""

from sqlalchemy import Column, String, Text, DateTime, JSON, Enum as SQLEnum, Float, ForeignKey
from sqlalchemy.sql import func
import uuid
import enum

from ..database import Base


class HypothesisState(str, enum.Enum):
    """Hypothesis lifecycle states."""
    PROPOSED = "proposed"
    INVESTIGATING = "investigating"
    VALIDATED = "validated"
    REFUTED = "refuted"
    PAUSED = "paused"
    ABANDONED = "abandoned"


# Valid state transitions
HYPOTHESIS_TRANSITIONS = {
    HypothesisState.PROPOSED: [HypothesisState.INVESTIGATING, HypothesisState.ABANDONED],
    HypothesisState.INVESTIGATING: [
        HypothesisState.VALIDATED,
        HypothesisState.REFUTED,
        HypothesisState.PAUSED,
        HypothesisState.ABANDONED,
    ],
    HypothesisState.PAUSED: [HypothesisState.INVESTIGATING, HypothesisState.ABANDONED],
    HypothesisState.VALIDATED: [],  # Terminal state (can spawn new hypotheses)
    HypothesisState.REFUTED: [],  # Terminal state
    HypothesisState.ABANDONED: [],  # Terminal state
}


class Hypothesis(Base):
    """
    Hypothesis - a testable assumption about the business/product/market.

    Hypotheses are supported or contradicted by evidence. They can be
    linked to goals, ventures, and forecasts.
    """

    __tablename__ = "hypotheses"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Links
    project_id = Column(String, nullable=True, index=True)  # Links to CommandCentral project
    goal_id = Column(String, ForeignKey("goals.id"), nullable=True, index=True)
    venture_id = Column(String, nullable=True, index=True)  # Links to venture
    
    # Core fields
    title = Column(String, nullable=False)
    statement = Column(Text, nullable=False)  # The actual hypothesis statement
    rationale = Column(Text, nullable=True)  # Why we believe this might be true
    
    # Falsifiability
    falsifiable_criteria = Column(Text, nullable=True)  # What would prove this wrong?
    success_criteria = Column(Text, nullable=True)  # What would prove this right?
    
    # State machine
    state = Column(SQLEnum(HypothesisState), default=HypothesisState.PROPOSED, nullable=False)
    state_changed_at = Column(DateTime, default=func.now())
    state_changed_by = Column(String, nullable=True)  # user_id
    
    # Confidence tracking
    initial_confidence = Column(Float, default=0.5)  # 0.0 to 1.0
    current_confidence = Column(Float, default=0.5)  # Updated as evidence comes in
    confidence_history = Column(JSON, default=list)  # [{timestamp, confidence, evidence_id}]
    
    # Evidence summary (denormalized for quick access)
    supporting_evidence_count = Column(Float, default=0)
    contradicting_evidence_count = Column(Float, default=0)
    
    # Timeline
    proposed_date = Column(DateTime, default=func.now())
    target_resolution_date = Column(DateTime, nullable=True)
    resolved_date = Column(DateTime, nullable=True)
    
    # Priority
    priority = Column(String, default="medium")  # low, medium, high, critical
    impact_if_true = Column(Text, nullable=True)  # What happens if validated?
    impact_if_false = Column(Text, nullable=True)  # What happens if refuted?
    
    # Ownership
    owner_id = Column(String, nullable=True)  # user_id
    
    # Extra data
    tags = Column(JSON, default=list)
    related_hypothesis_ids = Column(JSON, default=list)  # Related hypotheses
    extra_data = Column(JSON, default=dict)  # Renamed from 'metadata' (reserved by SQLAlchemy)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Hypothesis {self.title[:30]} ({self.state.value}) conf={self.current_confidence:.2f}>"

    def can_transition_to(self, new_state: HypothesisState) -> bool:
        """Check if transition to new_state is valid."""
        return new_state in HYPOTHESIS_TRANSITIONS.get(self.state, [])

    def allowed_transitions(self) -> list[HypothesisState]:
        """Get list of allowed transitions from current state."""
        return HYPOTHESIS_TRANSITIONS.get(self.state, [])
