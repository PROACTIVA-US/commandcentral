"""
Events/Audit router.

Query audit events and stream real-time events.
"""

from fastapi import APIRouter, Depends, Query
from typing import Optional, List
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..services.audit_service import AuditService
from ..models.audit import AuditEventType
from .auth import get_current_user

router = APIRouter()


@router.get("/")
async def list_events(
    project_id: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    actor_id: Optional[str] = None,
    event_type: Optional[str] = None,
    success: Optional[bool] = None,
    limit: int = Query(50, le=100),
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """List audit events with filters."""
    service = AuditService(session)

    # Get events based on filters
    if entity_type and entity_id:
        entries = await service.get_by_entity(
            entity_type=entity_type,
            entity_id=entity_id,
            limit=limit,
            offset=offset,
        )
    elif actor_id:
        entries = await service.get_by_actor(
            actor_id=actor_id,
            limit=limit,
            offset=offset,
        )
    elif project_id:
        event_types = [AuditEventType(event_type)] if event_type else None
        entries = await service.get_by_project(
            project_id=project_id,
            limit=limit,
            offset=offset,
            event_types=event_types,
        )
    else:
        event_types = [AuditEventType(event_type)] if event_type else None
        entries = await service.get_recent(
            limit=limit,
            event_types=event_types,
            success_only=success,
        )

    return {
        "entries": [
            {
                "id": e.id,
                "event_type": e.event_type.value,
                "event_name": e.event_name,
                "entity_type": e.entity_type,
                "entity_id": e.entity_id,
                "project_id": e.project_id,
                "actor_type": e.actor_type,
                "actor_id": e.actor_id,
                "from_state": e.from_state,
                "to_state": e.to_state,
                "success": e.success,
                "failure_reason": e.failure_reason,
                "rationale": e.rationale,
                "metadata": e.metadata,
                "timestamp": e.timestamp.isoformat(),
            }
            for e in entries
        ],
        "count": len(entries),
    }


@router.get("/{event_id}")
async def get_event(
    event_id: str,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """Get a single audit event by ID."""
    service = AuditService(session)
    entry = await service.get_by_id(event_id)

    if not entry:
        return {"error": "Event not found"}

    return {
        "id": entry.id,
        "event_type": entry.event_type.value,
        "event_name": entry.event_name,
        "entity_type": entry.entity_type,
        "entity_id": entry.entity_id,
        "project_id": entry.project_id,
        "actor_type": entry.actor_type,
        "actor_id": entry.actor_id,
        "from_state": entry.from_state,
        "to_state": entry.to_state,
        "success": entry.success,
        "failure_reason": entry.failure_reason,
        "rationale": entry.rationale,
        "metadata": entry.metadata,
        "side_effects": entry.side_effects,
        "correlation_id": entry.correlation_id,
        "timestamp": entry.timestamp.isoformat(),
    }


@router.get("/failed/transitions")
async def list_failed_transitions(
    entity_type: Optional[str] = None,
    project_id: Optional[str] = None,
    days: int = Query(7, le=30),
    limit: int = Query(50, le=100),
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """List failed transition attempts for analysis."""
    service = AuditService(session)

    since = datetime.utcnow() - timedelta(days=days)

    entries = await service.get_failed_transitions(
        entity_type=entity_type,
        project_id=project_id,
        since=since,
        limit=limit,
    )

    return {
        "entries": [
            {
                "id": e.id,
                "event_name": e.event_name,
                "entity_type": e.entity_type,
                "entity_id": e.entity_id,
                "project_id": e.project_id,
                "from_state": e.from_state,
                "to_state": e.to_state,
                "actor_id": e.actor_id,
                "failure_reason": e.failure_reason,
                "timestamp": e.timestamp.isoformat(),
            }
            for e in entries
        ],
        "count": len(entries),
        "since": since.isoformat(),
    }


@router.get("/stats")
async def get_event_stats(
    project_id: Optional[str] = None,
    days: int = Query(7, le=30),
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """Get audit event statistics."""
    service = AuditService(session)

    since = datetime.utcnow() - timedelta(days=days)

    stats = await service.get_stats(
        project_id=project_id,
        since=since,
    )

    return stats
