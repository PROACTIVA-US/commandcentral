"""
Venture model - business initiatives in the venture studio.

Ventures represent new business opportunities being explored,
with stage-gated progression from ideation to scale.
"""

from sqlalchemy import Column, String, Text, DateTime, JSON, Enum as SQLEnum, Float
from sqlalchemy.sql import func
import uuid
import enum

from ..database import Base


class VentureStage(str, enum.Enum):
    """Venture development stages."""
    IDEATION = "ideation"  # Initial idea exploration
    VALIDATION = "validation"  # Testing core assumptions
    MVP = "mvp"  # Minimum viable product
    PILOT = "pilot"  # Limited deployment
    GROWTH = "growth"  # Scaling up
    MATURE = "mature"  # Established business
    SUNSET = "sunset"  # Winding down
    KILLED = "killed"  # Terminated


# Valid stage transitions
VENTURE_TRANSITIONS = {
    VentureStage.IDEATION: [VentureStage.VALIDATION, VentureStage.KILLED],
    VentureStage.VALIDATION: [VentureStage.MVP, VentureStage.IDEATION, VentureStage.KILLED],
    VentureStage.MVP: [VentureStage.PILOT, VentureStage.VALIDATION, VentureStage.KILLED],
    VentureStage.PILOT: [VentureStage.GROWTH, VentureStage.MVP, VentureStage.KILLED],
    VentureStage.GROWTH: [VentureStage.MATURE, VentureStage.PILOT, VentureStage.SUNSET],
    VentureStage.MATURE: [VentureStage.SUNSET],
    VentureStage.SUNSET: [VentureStage.KILLED],
    VentureStage.KILLED: [],  # Terminal state
}


class Venture(Base):
    """
    Venture - a business initiative in the venture studio.

    Ventures progress through stages and are linked to goals,
    hypotheses, and key metrics.
    """

    __tablename__ = "ventures"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Core fields
    name = Column(String, nullable=False)
    codename = Column(String, unique=True, nullable=True, index=True)  # Internal codename
    description = Column(Text, nullable=True)
    value_proposition = Column(Text, nullable=True)
    
    # Target market
    target_market = Column(Text, nullable=True)
    market_size = Column(String, nullable=True)  # e.g., "$10B TAM"
    
    # Stage
    stage = Column(SQLEnum(VentureStage), default=VentureStage.IDEATION, nullable=False)
    stage_changed_at = Column(DateTime, default=func.now())
    stage_changed_by = Column(String, nullable=True)
    
    # Stage gate criteria
    stage_criteria = Column(JSON, default=dict)  # Criteria to pass to next stage
    stage_evidence = Column(JSON, default=list)  # Evidence used to pass stage gate
    
    # Financial
    investment_to_date = Column(Float, default=0.0)
    revenue_to_date = Column(Float, default=0.0)
    projected_revenue = Column(Float, nullable=True)
    projected_costs = Column(Float, nullable=True)
    
    # Timeline
    started_at = Column(DateTime, default=func.now())
    target_mvp_date = Column(DateTime, nullable=True)
    target_launch_date = Column(DateTime, nullable=True)
    
    # Ownership
    lead_id = Column(String, nullable=True)  # Venture lead user_id
    team_ids = Column(JSON, default=list)  # team member user_ids
    
    # Links
    project_id = Column(String, nullable=True, index=True)  # CommandCentral project
    goal_ids = Column(JSON, default=list)  # Linked goals
    hypothesis_ids = Column(JSON, default=list)  # Key hypotheses
    
    # Key metrics
    north_star_metric = Column(String, nullable=True)
    key_metrics = Column(JSON, default=dict)  # {metric_name: {value, target, unit}}
    
    # Extra data
    tags = Column(JSON, default=list)
    extra_data = Column(JSON, default=dict)  # Renamed from 'metadata' (reserved by SQLAlchemy)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Venture {self.name} ({self.stage.value})>"

    def can_transition_to(self, new_stage: VentureStage) -> bool:
        """Check if transition to new_stage is valid."""
        return new_stage in VENTURE_TRANSITIONS.get(self.stage, [])

    def allowed_transitions(self) -> list[VentureStage]:
        """Get list of allowed transitions from current stage."""
        return VENTURE_TRANSITIONS.get(self.stage, [])
