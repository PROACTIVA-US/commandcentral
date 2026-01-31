"""
Memory and Claims model - provenance-tracked knowledge.

Memories store information with source provenance tracking.
Claims are specific statements derived from memories.
"""

from sqlalchemy import Column, String, Text, DateTime, JSON, Enum as SQLEnum, Float, ForeignKey
from sqlalchemy.sql import func
import uuid
import enum

from ..database import Base


class MemoryType(str, enum.Enum):
    """Types of memory."""
    DOCUMENT = "document"  # From a document
    CONVERSATION = "conversation"  # From a conversation
    RESEARCH = "research"  # From research
    OBSERVATION = "observation"  # Direct observation
    INFERENCE = "inference"  # Derived/inferred
    EXTERNAL = "external"  # External API/data
    USER_INPUT = "user_input"  # Direct user input


class Memory(Base):
    """
    Memory - a unit of knowledge with provenance tracking.

    Memories can be searched and linked to evidence, hypotheses,
    and other entities. They maintain source provenance.
    """

    __tablename__ = "memories"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Core content
    title = Column(String, nullable=True)
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)  # AI-generated summary
    
    # Type and source
    memory_type = Column(SQLEnum(MemoryType), default=MemoryType.USER_INPUT, nullable=False)
    
    # Source provenance
    source_type = Column(String, nullable=True)  # "document", "url", "api", "user"
    source_id = Column(String, nullable=True)  # ID of source (document ID, URL, etc.)
    source_url = Column(String, nullable=True)
    source_title = Column(String, nullable=True)
    source_author = Column(String, nullable=True)
    source_date = Column(DateTime, nullable=True)
    
    # Extraction context
    extraction_method = Column(String, nullable=True)  # How was this extracted?
    extraction_confidence = Column(Float, default=1.0)  # Confidence in extraction
    
    # Embedding for semantic search
    embedding = Column(JSON, nullable=True)  # Vector embedding
    embedding_model = Column(String, nullable=True)  # Which model generated embedding
    
    # Links
    project_id = Column(String, nullable=True, index=True)
    related_memory_ids = Column(JSON, default=list)
    
    # Verification
    verified = Column(Float, default=False)
    verified_by = Column(String, nullable=True)
    verified_at = Column(DateTime, nullable=True)
    
    # Staleness tracking
    valid_from = Column(DateTime, default=func.now())
    valid_until = Column(DateTime, nullable=True)  # When does this become stale?
    staleness_check_at = Column(DateTime, nullable=True)  # When to re-verify
    
    # Access tracking
    access_count = Column(Float, default=0)
    last_accessed_at = Column(DateTime, nullable=True)
    
    # Extra data
    tags = Column(JSON, default=list)
    extra_data = Column(JSON, default=dict)  # Renamed from 'metadata' (reserved by SQLAlchemy)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        title = self.title or self.content[:30]
        return f"<Memory {title} ({self.memory_type.value})>"


class Claim(Base):
    """
    Claim - a specific statement with provenance.

    Claims are derived from memories and can be used as evidence.
    They maintain strong provenance tracking.
    """

    __tablename__ = "claims"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Core content
    statement = Column(Text, nullable=False)  # The actual claim
    
    # Provenance
    memory_id = Column(String, ForeignKey("memories.id"), nullable=True, index=True)
    source_text = Column(Text, nullable=True)  # Original text this was derived from
    
    # Confidence and verification
    confidence = Column(Float, default=0.8)  # Confidence in claim accuracy
    verified = Column(Float, default=False)
    verified_by = Column(String, nullable=True)
    verified_at = Column(DateTime, nullable=True)
    
    # Status
    is_current = Column(Float, default=True)  # Is this claim still believed true?
    superseded_by = Column(String, nullable=True)  # ID of claim that supersedes this
    refuted_by = Column(String, nullable=True)  # ID of evidence that refutes this
    
    # Links
    project_id = Column(String, nullable=True, index=True)
    evidence_ids = Column(JSON, default=list)  # Evidence using this claim
    hypothesis_ids = Column(JSON, default=list)  # Hypotheses this supports
    
    # Extra data
    tags = Column(JSON, default=list)
    extra_data = Column(JSON, default=dict)  # Renamed from 'metadata' (reserved by SQLAlchemy)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Claim {self.statement[:40]}... conf={self.confidence:.2f}>"
