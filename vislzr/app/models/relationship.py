"""
Relationship model for graph edges.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Column, String, Text, DateTime, Float, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship

from ..database import Base


class RelationshipType(str, Enum):
    """Types of relationships between nodes."""
    RELATED_TO = "related_to"
    PARENT_OF = "parent_of"
    CHILD_OF = "child_of"
    DEPENDS_ON = "depends_on"
    BLOCKS = "blocks"
    CONTAINS = "contains"
    REFERENCES = "references"
    SIMILAR_TO = "similar_to"
    DERIVED_FROM = "derived_from"
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    IMPLEMENTS = "implements"
    USES = "uses"
    CUSTOM = "custom"


class Relationship(Base):
    """
    A relationship (edge) between two nodes in the graph.
    
    Relationships represent connections, dependencies, or
    associations between nodes.
    """
    __tablename__ = "relationships"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Connection
    source_id = Column(String(36), ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False, index=True)
    target_id = Column(String(36), ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Relationship details
    relationship_type = Column(SQLEnum(RelationshipType), default=RelationshipType.RELATED_TO, nullable=False)
    label = Column(String(255), nullable=True)  # Optional edge label
    description = Column(Text, nullable=True)
    
    # Weight/strength
    weight = Column(Float, default=1.0)  # Relationship strength (0.0 - 1.0)
    confidence = Column(Float, default=1.0)  # Confidence in relationship
    
    # Visual properties
    color = Column(String(20), nullable=True)  # Hex color
    style = Column(String(20), default="solid")  # solid, dashed, dotted
    is_directed = Column(String(5), default="true")  # Whether edge has direction
    
    # Extra data (using extra_data instead of metadata - SQLAlchemy reserved)
    extra_data = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Relationship(id={self.id}, {self.source_id} -> {self.target_id}, type={self.relationship_type})>"

    def to_dict(self) -> dict:
        """Convert relationship to dictionary for API responses."""
        return {
            "id": self.id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relationship_type": self.relationship_type.value if self.relationship_type else None,
            "label": self.label,
            "description": self.description,
            "weight": self.weight,
            "confidence": self.confidence,
            "color": self.color,
            "style": self.style,
            "is_directed": self.is_directed == "true",
            "extra_data": self.extra_data or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
