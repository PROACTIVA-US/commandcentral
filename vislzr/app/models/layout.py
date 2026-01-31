"""
Layout and Canvas models for visualization.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, List

from sqlalchemy import Column, String, Text, DateTime, Float, JSON, Integer, Enum as SQLEnum

from ..database import Base


class LayoutType(str, Enum):
    """Types of graph layouts."""
    FORCE_DIRECTED = "force-directed"
    HIERARCHICAL = "hierarchical"
    RADIAL = "radial"
    CIRCULAR = "circular"
    GRID = "grid"
    TREE = "tree"
    DAGRE = "dagre"
    CONCENTRIC = "concentric"
    CUSTOM = "custom"


class Layout(Base):
    """
    A saved layout configuration for a canvas.
    
    Layouts store the positions and visual states of nodes
    for a particular view of the graph.
    """
    __tablename__ = "layouts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Identification
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    canvas_id = Column(String(36), nullable=True, index=True)  # Associated canvas
    
    # Layout configuration
    layout_type = Column(SQLEnum(LayoutType), default=LayoutType.FORCE_DIRECTED, nullable=False)
    
    # Node positions (JSON mapping node_id -> {x, y})
    positions = Column(JSON, default=dict)
    
    # Layout parameters
    parameters = Column(JSON, default=dict)  # Layout-specific parameters
    
    # Viewport state
    viewport_x = Column(Float, default=0.0)
    viewport_y = Column(Float, default=0.0)
    zoom = Column(Float, default=1.0)
    
    # Extra data (using extra_data instead of metadata - SQLAlchemy reserved)
    extra_data = Column(JSON, default=dict)
    
    # State
    is_default = Column(String(5), default="false")  # Default layout for canvas
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Layout(id={self.id}, name='{self.name}', type={self.layout_type})>"

    def to_dict(self) -> dict:
        """Convert layout to dictionary for API responses."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "canvas_id": self.canvas_id,
            "layout_type": self.layout_type.value if self.layout_type else None,
            "positions": self.positions or {},
            "parameters": self.parameters or {},
            "viewport": {
                "x": self.viewport_x,
                "y": self.viewport_y,
                "zoom": self.zoom,
            },
            "extra_data": self.extra_data or {},
            "is_default": self.is_default == "true",
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Canvas(Base):
    """
    A visualization canvas containing nodes and relationships.
    
    Canvases are the main container for graph visualizations,
    allowing users to explore and interact with data.
    """
    __tablename__ = "canvases"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Identification
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Ownership
    owner_id = Column(String(36), nullable=True, index=True)  # User or service
    
    # Canvas content (stored as JSON for flexibility)
    node_ids = Column(JSON, default=list)  # List of node IDs in canvas
    relationship_ids = Column(JSON, default=list)  # List of relationship IDs
    
    # Active layout
    active_layout_id = Column(String(36), nullable=True)
    
    # Canvas settings
    settings = Column(JSON, default=dict)  # Visual settings, filters, etc.
    
    # Extra data (using extra_data instead of metadata - SQLAlchemy reserved)
    extra_data = Column(JSON, default=dict)
    
    # State
    is_public = Column(String(5), default="false")
    is_archived = Column(String(5), default="false")
    
    # Stats
    node_count = Column(Integer, default=0)
    relationship_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_accessed_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Canvas(id={self.id}, name='{self.name}', nodes={self.node_count})>"

    def to_dict(self) -> dict:
        """Convert canvas to dictionary for API responses."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "owner_id": self.owner_id,
            "node_ids": self.node_ids or [],
            "relationship_ids": self.relationship_ids or [],
            "active_layout_id": self.active_layout_id,
            "settings": self.settings or {},
            "extra_data": self.extra_data or {},
            "is_public": self.is_public == "true",
            "is_archived": self.is_archived == "true",
            "node_count": self.node_count,
            "relationship_count": self.relationship_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_accessed_at": self.last_accessed_at.isoformat() if self.last_accessed_at else None,
        }
