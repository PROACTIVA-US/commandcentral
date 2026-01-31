"""
Generic Entity State model.

Tracks state for any entity type across the platform.
Enables centralized state machine management.
"""

from sqlalchemy import Column, String, DateTime, JSON, UniqueConstraint
from sqlalchemy.sql import func
from datetime import datetime
import uuid

from ..database import Base


class EntityState(Base):
    """
    Generic state tracking for any entity type.

    This allows CommandCentral to manage state machines for entities
    that live in other services (PIPELZR tasks, IDEALZR hypotheses, etc.)
    """

    __tablename__ = "entity_states"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Entity reference
    entity_type = Column(String, nullable=False, index=True)  # e.g., "task", "hypothesis"
    entity_id = Column(String, nullable=False, index=True)
    service = Column(String, nullable=False)  # e.g., "pipelzr", "idealzr"

    # Current state
    current_state = Column(String, nullable=False)

    # State machine definition reference
    state_machine_id = Column(String, nullable=True)  # Reference to state machine config

    # Context
    project_id = Column(String, nullable=True, index=True)

    # Last transition details
    last_transition_at = Column(DateTime, default=func.now())
    last_transition_by = Column(String, nullable=True)  # user_id or service
    last_transition_from = Column(String, nullable=True)

    # Allowed transitions (cached from state machine)
    allowed_transitions = Column(JSON, default=list)

    # Metadata
    extra_data = Column(JSON, default=dict)

    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Unique constraint: one state per entity
    __table_args__ = (
        UniqueConstraint("entity_type", "entity_id", "service", name="uq_entity_state"),
    )

    def __repr__(self):
        return f"<EntityState {self.service}.{self.entity_type}:{self.entity_id} = {self.current_state}>"
