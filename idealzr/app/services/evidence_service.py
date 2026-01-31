"""
Evidence service - business logic for evidence collection.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from ..models.evidence import Evidence, EvidenceType, EvidenceStrength
from ..models.hypothesis import Hypothesis
from .hypothesis_service import HypothesisService

logger = structlog.get_logger("idealzr.services.evidence")


class EvidenceService:
    """Service for managing evidence collection."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_evidence(self, data: dict) -> Evidence:
        """Create new evidence."""
        # Convert string enums
        if "evidence_type" in data and isinstance(data["evidence_type"], str):
            data["evidence_type"] = EvidenceType(data["evidence_type"])
        if "strength" in data and isinstance(data["strength"], str):
            data["strength"] = EvidenceStrength(data["strength"])
        
        evidence = Evidence(**data)
        self.db.add(evidence)
        await self.db.flush()
        
        await logger.ainfo(
            "evidence_created",
            evidence_id=evidence.id,
            title=evidence.title,
            hypothesis_id=evidence.hypothesis_id,
            supports=evidence.supports_hypothesis,
        )
        
        # Update hypothesis if linked
        if evidence.hypothesis_id:
            await self._update_hypothesis_from_evidence(evidence)
        
        return evidence

    async def get_evidence(self, evidence_id: str) -> Optional[Evidence]:
        """Get evidence by ID."""
        result = await self.db.execute(
            select(Evidence).where(Evidence.id == evidence_id)
        )
        return result.scalar_one_or_none()

    async def update_evidence(self, evidence_id: str, updates: dict) -> Optional[Evidence]:
        """Update evidence."""
        evidence = await self.get_evidence(evidence_id)
        if not evidence:
            return None

        # Convert string enums
        if "evidence_type" in updates and isinstance(updates["evidence_type"], str):
            updates["evidence_type"] = EvidenceType(updates["evidence_type"])
        if "strength" in updates and isinstance(updates["strength"], str):
            updates["strength"] = EvidenceStrength(updates["strength"])

        for field, value in updates.items():
            if hasattr(evidence, field):
                setattr(evidence, field, value)

        await self.db.flush()
        
        await logger.ainfo(
            "evidence_updated",
            evidence_id=evidence_id,
            updates=list(updates.keys()),
        )
        
        return evidence

    async def verify_evidence(self, evidence_id: str, user_id: str) -> Optional[Evidence]:
        """Mark evidence as verified."""
        evidence = await self.get_evidence(evidence_id)
        if not evidence:
            return None

        evidence.verified = True
        evidence.verified_by = user_id
        evidence.verified_at = datetime.utcnow()
        
        await self.db.flush()
        
        await logger.ainfo(
            "evidence_verified",
            evidence_id=evidence_id,
            verified_by=user_id,
        )
        
        return evidence

    async def link_to_hypothesis(self, evidence_id: str, hypothesis_id: str) -> Optional[Evidence]:
        """Link evidence to a hypothesis."""
        evidence = await self.get_evidence(evidence_id)
        if not evidence:
            return None

        # Verify hypothesis exists
        result = await self.db.execute(
            select(Hypothesis).where(Hypothesis.id == hypothesis_id)
        )
        hypothesis = result.scalar_one_or_none()
        if not hypothesis:
            return None

        evidence.hypothesis_id = hypothesis_id
        await self.db.flush()
        
        # Update hypothesis confidence
        await self._update_hypothesis_from_evidence(evidence)
        
        await logger.ainfo(
            "evidence_linked",
            evidence_id=evidence_id,
            hypothesis_id=hypothesis_id,
        )
        
        return evidence

    async def _update_hypothesis_from_evidence(self, evidence: Evidence) -> None:
        """Update hypothesis based on new evidence."""
        if not evidence.hypothesis_id:
            return

        hypothesis_service = HypothesisService(self.db)
        
        # Calculate impact based on evidence strength
        strength_impacts = {
            EvidenceStrength.WEAK: 0.05,
            EvidenceStrength.MODERATE: 0.1,
            EvidenceStrength.STRONG: 0.15,
            EvidenceStrength.DEFINITIVE: 0.25,
        }
        
        impact = strength_impacts.get(evidence.strength, 0.1)
        if evidence.confidence_impact != 0:
            impact = abs(evidence.confidence_impact)
        
        await hypothesis_service.add_evidence(
            evidence.hypothesis_id,
            evidence.id,
            evidence.supports_hypothesis,
            impact,
        )

    async def get_evidence_for_hypothesis(self, hypothesis_id: str) -> dict:
        """Get all evidence for a hypothesis, organized by support/contradict."""
        supporting = await self.db.execute(
            select(Evidence).where(
                Evidence.hypothesis_id == hypothesis_id,
                Evidence.supports_hypothesis == True,
            )
        )
        contradicting = await self.db.execute(
            select(Evidence).where(
                Evidence.hypothesis_id == hypothesis_id,
                Evidence.supports_hypothesis == False,
            )
        )
        
        return {
            "supporting": supporting.scalars().all(),
            "contradicting": contradicting.scalars().all(),
        }

    async def get_unverified_evidence(self, limit: int = 50) -> list:
        """Get evidence that needs verification."""
        result = await self.db.execute(
            select(Evidence)
            .where(Evidence.verified == False)
            .order_by(Evidence.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
