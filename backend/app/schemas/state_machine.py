"""
State machine and transition schemas.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class TransitionGuardType(str, Enum):
    """Types of transition guards."""
    PERMISSION = "permission"
    STATE_CHECK = "state_check"
    CUSTOM = "custom"


class StateDefinition(BaseModel):
    """Definition of a state in a state machine."""
    name: str
    description: Optional[str] = None
    is_initial: bool = False
    is_terminal: bool = False
    allowed_transitions: List[str] = Field(default_factory=list)
    entry_actions: List[str] = Field(default_factory=list)
    exit_actions: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TransitionRequest(BaseModel):
    """Request to transition an entity to a new state."""
    entity_type: str
    entity_id: str
    target_state: str
    rationale: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    force: bool = Field(default=False, description="Skip guards (superuser only)")


class TransitionResponse(BaseModel):
    """Response from a transition attempt."""
    success: bool
    entity_type: str
    entity_id: str
    from_state: str
    to_state: str
    transition_name: str
    timestamp: datetime
    side_effects: List[str] = Field(default_factory=list)
    audit_id: str


class EntityStateResponse(BaseModel):
    """Current state of an entity."""
    entity_type: str
    entity_id: str
    current_state: str
    state_definition: StateDefinition
    available_transitions: List[str]
    state_entered_at: datetime
    state_metadata: Dict[str, Any]

    class Config:
        from_attributes = True
