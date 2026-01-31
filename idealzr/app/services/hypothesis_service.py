"""
Hypothesis service - business logic for hypothesis lifecycle.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from ..models.hypothesis import Hypothesis, HypothesisState, HYPOTHESIS_TRANSITIONS

logger = structlog.get_logger("idealzr.services.hypothesis")


class HypothesisService:
    """Service for managing hypothesis lifecycle."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_hypothesis(self, data: dict) -> Hypothesis:
        """Create a new hypothesis."""
        # Set current confidence to initial confidence
        if "initial_confidence" in data:
            data["current_confidence"] = data["initial_confidence"]
        
        hypothesis = Hypothesis(**data)
        self.db.add(hypothesis)
        await self.db.flush()
        
        await logger.ainfo(
            "hypothesis_created",
            hypothesis_id=hypothesis.id,
            title=hypothesis.title,
            initial_confidence=hypothesis.initial_confidence,
        )
        
        return hypothesis

    async def get_hypothesis(self, hypothesis_id: str) -> Optional[Hypothesis]:
        """Get a hypothesis by ID."""
        result = await self.db.execute(
            select(Hypothesis).where(Hypothesis.id == hypothesis_id)
        )
        return result.scalar_one_or_none()

    async def update_hypothesis(self, hypothesis_id: str, updates: dict) -> Optional[Hypothesis]:
        """Update a hypothesis."""
        hypothesis = await self.get_hypothesis(hypothesis_id)
        if not hypothesis:
            return None

        for field, value in updates.items():
            if hasattr(hypothesis, field):
                setattr(hypothesis, field, value)

        await self.db.flush()
        
        await logger.ainfo(
            "hypothesis_updated",
            hypothesis_id=hypothesis_id,
            updates=list(updates.keys()),
        )
        
        return hypothesis

    async def transition_hypothesis(
        self, hypothesis_id: str, new_state: HypothesisState, user_id: Optional[str] = None
    ) -> Optional[Hypothesis]:
        """Transition a hypothesis to a new state."""
        hypothesis = await self.get_hypothesis(hypothesis_id)
        if not hypothesis:
            return None

        if not hypothesis.can_transition_to(new_state):
            raise ValueError(
                f"Cannot transition from {hypothesis.state.value} to {new_state.value}. "
                f"Allowed: {[s.value for s in hypothesis.allowed_transitions()]}"
            )

        old_state = hypothesis.state
        hypothesis.state = new_state
        hypothesis.state_changed_at = datetime.utcnow()
        hypothesis.state_changed_by = user_id

        # Handle terminal states
        if new_state in [HypothesisState.VALIDATED, HypothesisState.REFUTED]:
            hypothesis.resolved_date = datetime.utcnow()

        await self.db.flush()
        
        await logger.ainfo(
            "hypothesis_transitioned",
            hypothesis_id=hypothesis_id,
            from_state=old_state.value,
            to_state=new_state.value,
            user_id=user_id,
        )
        
        return hypothesis

    async def update_confidence(
        self, hypothesis_id: str, new_confidence: float, evidence_id: Optional[str] = None
    ) -> Optional[Hypothesis]:
        """Update confidence level for a hypothesis."""
        hypothesis = await self.get_hypothesis(hypothesis_id)
        if not hypothesis:
            return None

        old_confidence = hypothesis.current_confidence
        hypothesis.current_confidence = max(0.0, min(1.0, new_confidence))
        
        # Track confidence history
        history_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "old_confidence": old_confidence,
            "new_confidence": hypothesis.current_confidence,
            "evidence_id": evidence_id,
        }
        hypothesis.confidence_history.append(history_entry)

        await self.db.flush()
        
        await logger.ainfo(
            "hypothesis_confidence_updated",
            hypothesis_id=hypothesis_id,
            old_confidence=old_confidence,
            new_confidence=hypothesis.current_confidence,
            evidence_id=evidence_id,
        )
        
        return hypothesis

    async def add_evidence(
        self, hypothesis_id: str, evidence_id: str, supports: bool, impact: float
    ) -> Optional[Hypothesis]:
        """Add evidence to a hypothesis and update confidence."""
        hypothesis = await self.get_hypothesis(hypothesis_id)
        if not hypothesis:
            return None

        # Update evidence counts
        if supports:
            hypothesis.supporting_evidence_count += 1
        else:
            hypothesis.contradicting_evidence_count += 1

        # Calculate new confidence based on evidence impact
        confidence_delta = impact if supports else -impact
        new_confidence = hypothesis.current_confidence + confidence_delta
        
        await self.update_confidence(hypothesis_id, new_confidence, evidence_id)
        
        await self.db.flush()
        return hypothesis

    async def get_active_hypotheses(self, project_id: Optional[str] = None) -> list:
        """Get all hypotheses in investigating state."""
        query = select(Hypothesis).where(
            Hypothesis.state == HypothesisState.INVESTIGATING
        )
        if project_id:
            query = query.where(Hypothesis.project_id == project_id)
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_hypotheses_needing_evidence(self, min_evidence_count: int = 3) -> list:
        """Get hypotheses that need more evidence."""
        query = select(Hypothesis).where(
            Hypothesis.state == HypothesisState.INVESTIGATING,
            (Hypothesis.supporting_evidence_count + Hypothesis.contradicting_evidence_count) < min_evidence_count,
        )
        result = await self.db.execute(query)
        return result.scalars().all()
