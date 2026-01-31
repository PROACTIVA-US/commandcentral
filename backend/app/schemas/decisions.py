"""
Decision primitive schemas.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class DecisionType(str, Enum):
    """Types of decisions."""
    YES_NO = "yes_no"
    CHOICE = "choice"
    PRIORITIZATION = "prioritization"
    ALLOCATION = "allocation"
    APPROVAL = "approval"


class DecisionStatus(str, Enum):
    """Status of a decision."""
    DRAFT = "draft"
    PENDING = "pending"
    DECIDED = "decided"
    EXECUTED = "executed"
    REVERSED = "reversed"


class DecisionCreate(BaseModel):
    """Schema for creating a decision."""
    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None
    decision_type: DecisionType
    options: List[str] = Field(min_length=2)
    context: Optional[str] = None
    deadline: Optional[datetime] = None
    stakeholders: List[str] = Field(default_factory=list)
    project_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DecisionUpdate(BaseModel):
    """Schema for updating a decision."""
    title: Optional[str] = None
    description: Optional[str] = None
    options: Optional[List[str]] = None
    context: Optional[str] = None
    deadline: Optional[datetime] = None
    stakeholders: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class DecisionResponse(BaseModel):
    """Decision response schema."""
    id: str
    title: str
    description: Optional[str]
    decision_type: DecisionType
    status: DecisionStatus
    options: List[str]
    selected_option: Optional[str]
    rationale: Optional[str]
    context: Optional[str]
    deadline: Optional[datetime]
    decided_at: Optional[datetime]
    decided_by: Optional[str]
    stakeholders: List[str]
    project_id: Optional[str]
    created_by: str
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]

    class Config:
        from_attributes = True
