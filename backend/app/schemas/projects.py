"""
Project schemas.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ProjectStatus(str, Enum):
    """Project status states."""
    PLANNING = "planning"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ProjectCreate(BaseModel):
    """Schema for creating a project."""
    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = None
    goal: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""
    name: Optional[str] = None
    description: Optional[str] = None
    goal: Optional[str] = None
    status: Optional[ProjectStatus] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class ProjectResponse(BaseModel):
    """Project response schema."""
    id: str
    name: str
    description: Optional[str]
    goal: Optional[str]
    status: ProjectStatus
    tags: List[str]
    owner_id: str
    member_ids: List[str]
    created_at: datetime
    updated_at: datetime
    archived_at: Optional[datetime]
    metadata: Dict[str, Any]

    class Config:
        from_attributes = True
