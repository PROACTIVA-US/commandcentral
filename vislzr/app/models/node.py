"""
Node model for graph visualization.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Column, String, Text, DateTime, Float, JSON, Enum as SQLEnum
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON

from ..database import Base


class NodeType(str, Enum):
    """Types of nodes in the visualization graph."""
    ENTITY = "entity"
    CONCEPT = "concept"
    DOCUMENT = "document"
    PERSON = "person"
    ORGANIZATION = "organization"
    EVENT = "event"
    LOCATION = "location"
    PROJECT = "project"
    TASK = "task"
    IDEA = "idea"
    HYPOTHESIS = "hypothesis"
    PIPELINE = "pipeline"
    CUSTOM = "custom"


class Node(Base):
    """
    A node in the visualization graph.
    
    Nodes represent entities, concepts, documents, or any
    other visualizable object in the exploration canvas.
    """
    __tablename__ = "nodes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Core identification
    external_id = Column(String(255), nullable=True, index=True)  # Reference to external system
    source_service = Column(String(50), nullable=True)  # Which service owns this entity
    
    # Node content
    label = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    node_type = Column(SQLEnum(NodeType), default=NodeType.ENTITY, nullable=False)
    
    # Visual properties
    x = Column(Float, default=0.0)  # X position
    y = Column(Float, default=0.0)  # Y position
    size = Column(Float, default=1.0)  # Relative size
    color = Column(String(20), nullable=True)  # Hex color
    icon = Column(String(50), nullable=True)  # Icon identifier
    
    # State
    is_expanded = Column(String(5), default="false")  # Whether children are visible
    is_pinned = Column(String(5), default="false")  # Whether position is locked
    is_hidden = Column(String(5), default="false")  # Whether node is hidden
    
    # Extra data (using extra_data instead of metadata - SQLAlchemy reserved)
    extra_data = Column(JSON, default=dict)  # Arbitrary additional data
    properties = Column(JSON, default=dict)  # Node-specific properties
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Node(id={self.id}, label='{self.label}', type={self.node_type})>"

    def to_dict(self) -> dict:
        """Convert node to dictionary for API responses."""
        return {
            "id": self.id,
            "external_id": self.external_id,
            "source_service": self.source_service,
            "label": self.label,
            "description": self.description,
            "node_type": self.node_type.value if self.node_type else None,
            "position": {"x": self.x, "y": self.y},
            "size": self.size,
            "color": self.color,
            "icon": self.icon,
            "is_expanded": self.is_expanded == "true",
            "is_pinned": self.is_pinned == "true",
            "is_hidden": self.is_hidden == "true",
            "extra_data": self.extra_data or {},
            "properties": self.properties or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
