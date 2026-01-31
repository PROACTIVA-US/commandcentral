"""
Audit Service

Centralized audit logging for all governance events.
"""

from datetime import datetime, timedelta
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc

from ..models.audit import AuditEntry, AuditEventType


class AuditService:
    """Service for audit log operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def log(
        self,
        event_type: AuditEventType,
        event_name: str,
        actor_id: str,
        actor_type: str = "user",
        entity_type: str = None,
        entity_id: str = None,
        project_id: str = None,
        from_state: str = None,
        to_state: str = None,
        success: bool = True,
        failure_reason: str = None,
        rationale: str = None,
        metadata: dict = None,
        correlation_id: str = None,
    ) -> AuditEntry:
        """Log an audit event."""
        entry = AuditEntry(
            event_type=event_type,
            event_name=event_name,
            actor_type=actor_type,
            actor_id=actor_id,
            entity_type=entity_type,
            entity_id=entity_id,
            project_id=project_id,
            from_state=from_state,
            to_state=to_state,
            success=success,
            failure_reason=failure_reason,
            rationale=rationale,
            metadata=metadata or {},
            correlation_id=correlation_id,
        )
        self.session.add(entry)
        await self.session.flush()
        return entry

    async def log_transition(
        self,
        entity_type: str,
        entity_id: str,
        from_state: str,
        to_state: str,
        actor_id: str,
        success: bool,
        project_id: str = None,
        failure_reason: str = None,
        rationale: str = None,
        correlation_id: str = None,
    ) -> AuditEntry:
        """Log a state transition event."""
        event_type = (
            AuditEventType.TRANSITION_SUCCESS if success
            else AuditEventType.TRANSITION_DENIED
        )
        return await self.log(
            event_type=event_type,
            event_name=f"{entity_type}.transition.{to_state}",
            actor_id=actor_id,
            entity_type=entity_type,
            entity_id=entity_id,
            project_id=project_id,
            from_state=from_state,
            to_state=to_state,
            success=success,
            failure_reason=failure_reason,
            rationale=rationale,
            correlation_id=correlation_id,
        )

    async def get_by_id(self, audit_id: str) -> Optional[AuditEntry]:
        """Get a single audit entry by ID."""
        result = await self.session.execute(
            select(AuditEntry).where(AuditEntry.id == audit_id)
        )
        return result.scalar_one_or_none()

    async def get_by_entity(
        self,
        entity_type: str,
        entity_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[AuditEntry]:
        """Get audit entries for a specific entity."""
        result = await self.session.execute(
            select(AuditEntry)
            .where(
                and_(
                    AuditEntry.entity_type == entity_type,
                    AuditEntry.entity_id == entity_id,
                )
            )
            .order_by(desc(AuditEntry.timestamp))
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def get_by_actor(
        self,
        actor_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[AuditEntry]:
        """Get audit entries for a specific actor."""
        result = await self.session.execute(
            select(AuditEntry)
            .where(AuditEntry.actor_id == actor_id)
            .order_by(desc(AuditEntry.timestamp))
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def get_by_project(
        self,
        project_id: str,
        limit: int = 50,
        offset: int = 0,
        event_types: List[AuditEventType] = None,
    ) -> List[AuditEntry]:
        """Get audit entries for a specific project."""
        query = select(AuditEntry).where(AuditEntry.project_id == project_id)

        if event_types:
            query = query.where(AuditEntry.event_type.in_(event_types))

        query = query.order_by(desc(AuditEntry.timestamp)).limit(limit).offset(offset)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_failed_transitions(
        self,
        entity_type: str = None,
        project_id: str = None,
        since: datetime = None,
        limit: int = 50,
    ) -> List[AuditEntry]:
        """Get failed transition attempts for analysis."""
        conditions = [AuditEntry.event_type == AuditEventType.TRANSITION_DENIED]

        if entity_type:
            conditions.append(AuditEntry.entity_type == entity_type)
        if project_id:
            conditions.append(AuditEntry.project_id == project_id)
        if since:
            conditions.append(AuditEntry.timestamp >= since)

        result = await self.session.execute(
            select(AuditEntry)
            .where(and_(*conditions))
            .order_by(desc(AuditEntry.timestamp))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_recent(
        self,
        limit: int = 100,
        event_types: List[AuditEventType] = None,
        success_only: bool = None,
    ) -> List[AuditEntry]:
        """Get recent audit entries."""
        query = select(AuditEntry)

        conditions = []
        if event_types:
            conditions.append(AuditEntry.event_type.in_(event_types))
        if success_only is not None:
            conditions.append(AuditEntry.success == success_only)

        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(desc(AuditEntry.timestamp)).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_stats(
        self,
        project_id: str = None,
        since: datetime = None,
    ) -> dict:
        """Get audit statistics."""
        if since is None:
            since = datetime.utcnow() - timedelta(days=7)

        conditions = [AuditEntry.timestamp >= since]
        if project_id:
            conditions.append(AuditEntry.project_id == project_id)

        result = await self.session.execute(
            select(AuditEntry).where(and_(*conditions))
        )
        entries = list(result.scalars().all())

        # Calculate stats
        total = len(entries)
        by_type = {}
        by_success = {"success": 0, "failure": 0}

        for entry in entries:
            # By type
            type_key = entry.event_type.value
            by_type[type_key] = by_type.get(type_key, 0) + 1

            # By success
            if entry.success:
                by_success["success"] += 1
            else:
                by_success["failure"] += 1

        return {
            "total": total,
            "since": since.isoformat(),
            "by_type": by_type,
            "by_success": by_success,
        }
