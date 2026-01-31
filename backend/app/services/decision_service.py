"""
Decision Service

Manages decision primitives with governed state machine.
"""

from datetime import datetime
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc

from ..models.decision import Decision, DecisionState
from ..models.audit import AuditEventType
from .audit_service import AuditService


class DecisionService:
    """Service for decision operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.audit = AuditService(session)

    async def create(
        self,
        project_id: str,
        title: str,
        created_by: str,
        question: str = None,
        context: str = None,
        options: list = None,
        tags: list = None,
    ) -> Decision:
        """Create a new decision in draft state."""
        decision = Decision(
            project_id=project_id,
            title=title,
            question=question,
            context=context,
            options=options or [],
            tags=tags or [],
            created_by=created_by,
            state=DecisionState.DRAFT,
        )
        self.session.add(decision)
        await self.session.flush()

        # Audit log
        await self.audit.log(
            event_type=AuditEventType.ENTITY_CREATED,
            event_name="decision.created",
            entity_type="decision",
            entity_id=decision.id,
            project_id=project_id,
            actor_id=created_by,
        )

        return decision

    async def get_by_id(self, decision_id: str) -> Optional[Decision]:
        """Get a decision by ID."""
        result = await self.session.execute(
            select(Decision).where(Decision.id == decision_id)
        )
        return result.scalar_one_or_none()

    async def list_by_project(
        self,
        project_id: str,
        state: DecisionState = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Decision]:
        """List decisions for a project."""
        query = select(Decision).where(Decision.project_id == project_id)

        if state:
            query = query.where(Decision.state == state)

        query = query.order_by(desc(Decision.updated_at)).limit(limit).offset(offset)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update(
        self,
        decision_id: str,
        actor_id: str,
        title: str = None,
        question: str = None,
        context: str = None,
        options: list = None,
        tags: list = None,
    ) -> Optional[Decision]:
        """Update a decision (only allowed in draft/active states)."""
        decision = await self.get_by_id(decision_id)
        if not decision:
            return None

        # Only allow updates in draft or active state
        if decision.state not in [DecisionState.DRAFT, DecisionState.ACTIVE]:
            await self.audit.log(
                event_type=AuditEventType.ENTITY_UPDATED,
                event_name="decision.update.denied",
                entity_type="decision",
                entity_id=decision_id,
                project_id=decision.project_id,
                actor_id=actor_id,
                success=False,
                failure_reason=f"Cannot update decision in {decision.state.value} state",
            )
            return None

        # Update fields
        if title is not None:
            decision.title = title
        if question is not None:
            decision.question = question
        if context is not None:
            decision.context = context
        if options is not None:
            decision.options = options
        if tags is not None:
            decision.tags = tags

        decision.updated_at = datetime.utcnow()

        await self.audit.log(
            event_type=AuditEventType.ENTITY_UPDATED,
            event_name="decision.updated",
            entity_type="decision",
            entity_id=decision_id,
            project_id=decision.project_id,
            actor_id=actor_id,
        )

        return decision

    async def transition(
        self,
        decision_id: str,
        to_state: DecisionState,
        actor_id: str,
        rationale: str = None,
        selected_option: str = None,
    ) -> tuple[bool, str, Optional[Decision]]:
        """
        Attempt to transition a decision to a new state.

        Returns (success, message, decision)
        """
        decision = await self.get_by_id(decision_id)
        if not decision:
            return False, "Decision not found", None

        from_state = decision.state

        # Check if transition is allowed
        if not decision.can_transition_to(to_state):
            await self.audit.log_transition(
                entity_type="decision",
                entity_id=decision_id,
                from_state=from_state.value,
                to_state=to_state.value,
                actor_id=actor_id,
                project_id=decision.project_id,
                success=False,
                failure_reason=f"Transition from {from_state.value} to {to_state.value} not allowed",
            )
            return False, f"Cannot transition from {from_state.value} to {to_state.value}", decision

        # Check requirements
        is_valid, missing = decision.check_transition_requirements(to_state)
        if not is_valid:
            await self.audit.log_transition(
                entity_type="decision",
                entity_id=decision_id,
                from_state=from_state.value,
                to_state=to_state.value,
                actor_id=actor_id,
                project_id=decision.project_id,
                success=False,
                failure_reason=f"Missing required fields: {', '.join(missing)}",
            )
            return False, f"Missing required fields: {', '.join(missing)}", decision

        # Special handling for decide transition
        if to_state == DecisionState.DECIDED:
            if not selected_option:
                await self.audit.log_transition(
                    entity_type="decision",
                    entity_id=decision_id,
                    from_state=from_state.value,
                    to_state=to_state.value,
                    actor_id=actor_id,
                    project_id=decision.project_id,
                    success=False,
                    failure_reason="selected_option required for decide transition",
                )
                return False, "Must provide selected_option to decide", decision

            decision.selected_option = selected_option
            decision.rationale = rationale
            decision.decided_at = datetime.utcnow()
            decision.decided_by = actor_id

        # Perform transition
        decision.state = to_state
        decision.state_changed_at = datetime.utcnow()
        decision.state_changed_by = actor_id

        await self.audit.log_transition(
            entity_type="decision",
            entity_id=decision_id,
            from_state=from_state.value,
            to_state=to_state.value,
            actor_id=actor_id,
            project_id=decision.project_id,
            success=True,
            rationale=rationale,
        )

        return True, f"Transitioned to {to_state.value}", decision

    async def activate(self, decision_id: str, actor_id: str) -> tuple[bool, str, Optional[Decision]]:
        """Activate a draft decision."""
        return await self.transition(decision_id, DecisionState.ACTIVE, actor_id)

    async def decide(
        self,
        decision_id: str,
        actor_id: str,
        selected_option: str,
        rationale: str = None,
    ) -> tuple[bool, str, Optional[Decision]]:
        """Mark a decision as decided."""
        return await self.transition(
            decision_id,
            DecisionState.DECIDED,
            actor_id,
            rationale=rationale,
            selected_option=selected_option,
        )

    async def archive(self, decision_id: str, actor_id: str) -> tuple[bool, str, Optional[Decision]]:
        """Archive a decision."""
        return await self.transition(decision_id, DecisionState.ARCHIVED, actor_id)

    async def get_audit_trail(self, decision_id: str, limit: int = 50) -> List:
        """Get audit trail for a decision."""
        return await self.audit.get_by_entity("decision", decision_id, limit=limit)

    async def delete(self, decision_id: str, actor_id: str) -> bool:
        """Delete a decision (only allowed in draft state)."""
        decision = await self.get_by_id(decision_id)
        if not decision:
            return False

        if decision.state != DecisionState.DRAFT:
            await self.audit.log(
                event_type=AuditEventType.ENTITY_DELETED,
                event_name="decision.delete.denied",
                entity_type="decision",
                entity_id=decision_id,
                project_id=decision.project_id,
                actor_id=actor_id,
                success=False,
                failure_reason="Can only delete decisions in draft state",
            )
            return False

        await self.session.delete(decision)

        await self.audit.log(
            event_type=AuditEventType.ENTITY_DELETED,
            event_name="decision.deleted",
            entity_type="decision",
            entity_id=decision_id,
            project_id=decision.project_id,
            actor_id=actor_id,
        )

        return True
