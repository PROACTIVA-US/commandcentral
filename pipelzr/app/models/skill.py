"""
Skill model - represents a reusable capability.

Skills are executable capabilities that agents can invoke.
They define inputs, outputs, and execution logic.
"""

from sqlalchemy import Column, String, Text, DateTime, JSON, Enum as SQLEnum, Integer, Float
from sqlalchemy.sql import func
import uuid
import enum

from ..database import Base


class SkillCategory(str, enum.Enum):
    """Categories of skills."""
    CODEBASE = "codebase"       # Code analysis, search, indexing
    EXECUTION = "execution"     # Task execution, commands
    ANALYSIS = "analysis"       # Data analysis, metrics
    COMMUNICATION = "communication"  # Messaging, notifications
    INTEGRATION = "integration"  # External service integration
    VALIDATION = "validation"   # Testing, verification
    GENERATION = "generation"   # Code/content generation
    RESEARCH = "research"       # Web search, knowledge retrieval


class Skill(Base):
    """
    Skill - a reusable agent capability.

    Skills encapsulate specific capabilities that agents
    can use to accomplish tasks. They define clear interfaces
    and can be composed into more complex workflows.
    """

    __tablename__ = "skills"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, unique=True)
    slug = Column(String, nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    
    # Categorization
    category = Column(SQLEnum(SkillCategory), nullable=False)
    tags = Column(JSON, default=list)
    
    # Interface definition
    inputs = Column(JSON, default=list)   # Input parameter definitions
    outputs = Column(JSON, default=list)  # Output definitions
    
    # Execution
    implementation = Column(Text, nullable=True)  # Code or reference
    implementation_type = Column(String, default="python")  # python, bash, api
    dependencies = Column(JSON, default=list)  # Required skills or packages
    
    # Prompts
    system_prompt = Column(Text, nullable=True)  # Context for LLM
    examples = Column(JSON, default=list)  # Usage examples
    
    # Configuration
    enabled = Column(Integer, default=1)  # Boolean: is skill active
    requires_approval = Column(Integer, default=0)  # Boolean: needs human approval
    cost_estimate = Column(Float, default=0.0)  # Estimated cost per invocation
    timeout_seconds = Column(Integer, default=60)
    
    # Usage tracking
    invocation_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    avg_duration_ms = Column(Float, default=0.0)
    
    # Versioning
    version = Column(String, default="1.0.0")
    changelog = Column(JSON, default=list)
    
    # Configuration
    extra_data = Column(JSON, default=dict)  # Renamed from 'metadata' (SQLAlchemy reserved)

    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Skill {self.slug} ({self.category.value})>"
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        total = self.success_count + self.failure_count
        if total == 0:
            return 1.0
        return self.success_count / total
    
    def record_invocation(self, success: bool, duration_ms: float):
        """Record a skill invocation."""
        self.invocation_count += 1
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
        
        # Update running average duration
        total = self.success_count + self.failure_count
        if total == 1:
            self.avg_duration_ms = duration_ms
        else:
            self.avg_duration_ms = (
                (self.avg_duration_ms * (total - 1) + duration_ms) / total
            )
