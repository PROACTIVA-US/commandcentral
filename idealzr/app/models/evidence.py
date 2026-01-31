"""
Evidence model - supporting or contradicting data for hypotheses.

Evidence can come from various sources and has different strengths.
It is linked to hypotheses and memories for provenance tracking.
"""

from sqlalchemy import Column, String, Text, DateTime, JSON, Enum as SQLEnum, Float, ForeignKey
from sqlalchemy.sql import func
import uuid
import enum

from ..database import Base


class EvidenceType(str, enum.Enum):
    """Types of evidence."""
    DATA = "data"  # Quantitative data, metrics
    RESEARCH = "research"  # External research, studies
    INTERVIEW = "interview"  # User interviews, feedback
    EXPERIMENT = "experiment"  # A/B tests, experiments
    OBSERVATION = "observation"  # Direct observations
    DOCUMENT = "document"  # Documents, reports
    EXPERT = "expert"  # Expert opinion
    ANECDOTE = "anecdote"  # Anecdotal evidence


class EvidenceStrength(str, enum.Enum):
    """Strength of evidence."""
    WEAK = "weak"  # Suggestive but not conclusive
    MODERATE = "moderate"  # Reasonably compelling
    STRONG = "strong"  # Highly compelling
    DEFINITIVE = "definitive"  # Conclusive proof


class Evidence(Base):
    """
    Evidence - data that supports or contradicts hypotheses.

    Evidence has provenance tracking through links to memory/claims
    and can be associated with multiple hypotheses.
    """

    __tablename__ = "evidence"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Primary link
    hypothesis_id = Column(String, ForeignKey("hypotheses.id"), nullable=True, index=True)
    project_id = Column(String, nullable=True, index=True)
    
    # Core fields
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    
    # Classification
    evidence_type = Column(SQLEnum(EvidenceType), default=EvidenceType.DATA, nullable=False)
    strength = Column(SQLEnum(EvidenceStrength), default=EvidenceStrength.MODERATE, nullable=False)
    
    # Direction (does this support or contradict the hypothesis?)
    supports_hypothesis = Column(Float, default=True)  # True = supports, False = contradicts
    confidence_impact = Column(Float, default=0.0)  # How much this changes confidence (-1 to 1)
    
    # Source and provenance
    source = Column(String, nullable=True)  # Where did this come from?
    source_url = Column(String, nullable=True)  # Link to source
    source_date = Column(DateTime, nullable=True)  # When was source created?
    
    # Memory/claim link for provenance
    memory_id = Column(String, nullable=True, index=True)  # Links to memory system
    claim_ids = Column(JSON, default=list)  # Associated claims with provenance
    
    # Data (for quantitative evidence)
    data_value = Column(Float, nullable=True)  # The actual data point
    data_unit = Column(String, nullable=True)  # Unit of measurement
    data_context = Column(Text, nullable=True)  # Context for the data
    
    # Attachments
    attachment_urls = Column(JSON, default=list)  # Links to files/documents
    
    # Verification
    verified = Column(Float, default=False)
    verified_by = Column(String, nullable=True)  # user_id
    verified_at = Column(DateTime, nullable=True)
    
    # Ownership
    submitted_by = Column(String, nullable=True)  # user_id
    
    # Extra data
    tags = Column(JSON, default=list)
    extra_data = Column(JSON, default=dict)  # Renamed from 'metadata' (reserved by SQLAlchemy)
    
    # Timestamps
    collected_at = Column(DateTime, default=func.now())  # When was evidence collected?
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        direction = "+" if self.supports_hypothesis else "-"
        return f"<Evidence {direction} {self.title[:30]} ({self.evidence_type.value}/{self.strength.value})>"
