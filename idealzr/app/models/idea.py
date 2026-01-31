"""
Idea model - lightweight idea capture before they become hypotheses or ventures.

Ideas are quick captures that can be promoted to hypotheses, ventures,
or goals when they mature.
"""

from sqlalchemy import Column, String, Text, DateTime, JSON, Enum as SQLEnum, Float
from sqlalchemy.sql import func
import uuid
import enum

from ..database import Base


class IdeaStatus(str, enum.Enum):
    """Idea status."""
    CAPTURED = "captured"  # Just captured, not reviewed
    REVIEWING = "reviewing"  # Under review
    PROMOTED = "promoted"  # Promoted to hypothesis/venture/goal
    PARKED = "parked"  # Good idea but not now
    REJECTED = "rejected"  # Not pursuing


class Idea(Base):
    """
    Idea - a quick capture of a thought or opportunity.

    Ideas are lightweight and can be promoted to more formal
    structures like hypotheses, ventures, or goals.
    """

    __tablename__ = "ideas"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Core fields
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    # Quick capture context
    source = Column(String, nullable=True)  # Where did this come from?
    trigger = Column(Text, nullable=True)  # What triggered this idea?
    
    # Status
    status = Column(SQLEnum(IdeaStatus), default=IdeaStatus.CAPTURED, nullable=False)
    status_changed_at = Column(DateTime, default=func.now())
    
    # Assessment
    potential_impact = Column(String, default="unknown")  # low, medium, high, transformative
    effort_estimate = Column(String, default="unknown")  # low, medium, high
    urgency = Column(String, default="unknown")  # low, medium, high, critical
    
    # Scoring (for prioritization)
    impact_score = Column(Float, nullable=True)  # 0-10
    confidence_score = Column(Float, nullable=True)  # 0-10
    ease_score = Column(Float, nullable=True)  # 0-10
    ice_score = Column(Float, nullable=True)  # Calculated: impact * confidence * ease
    
    # Promotion tracking
    promoted_to_type = Column(String, nullable=True)  # "hypothesis", "venture", "goal"
    promoted_to_id = Column(String, nullable=True)  # ID of the promoted entity
    promoted_at = Column(DateTime, nullable=True)
    
    # Links
    project_id = Column(String, nullable=True, index=True)
    related_idea_ids = Column(JSON, default=list)  # Related ideas
    
    # Ownership
    submitted_by = Column(String, nullable=True)  # user_id
    
    # Extra data
    tags = Column(JSON, default=list)
    extra_data = Column(JSON, default=dict)  # Renamed from 'metadata' (reserved by SQLAlchemy)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Idea {self.title[:30]} ({self.status.value})>"

    def calculate_ice_score(self):
        """Calculate ICE score from component scores."""
        if all([self.impact_score, self.confidence_score, self.ease_score]):
            self.ice_score = self.impact_score * self.confidence_score * self.ease_score
        return self.ice_score
