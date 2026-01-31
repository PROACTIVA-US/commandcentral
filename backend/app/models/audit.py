"""
Audit Entry model for governance audit trail.

Every state change, permission check, and significant action
is logged here for compliance and debugging.
"""

from sqlalchemy import Column, String, Text, DateTime, JSON, Boolean, Enum as SQLEnum
from sqlalchemy.sql import func
from datetime import datetime
import uuid
import enum

from ..database import Base


class AuditEventType(str, enum.Enum):
    """Types of audit events."""
    # State machine events
    TRANSITION_ATTEMPT = "transition_attempt"
    TRANSITION_SUCCESS = "transition_success"
    TRANSITION_DENIED = "transition_denied"

    # Permission events
    PERMISSION_CHECK = "permission_check"
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_DENIED = "permission_denied"

    # Entity events
    ENTITY_CREATED = "entity_created"
    ENTITY_UPDATED = "entity_updated"
    ENTITY_DELETED = "entity_deleted"

    # Auth events
    AUTH_LOGIN = "auth_login"
    AUTH_LOGOUT = "auth_logout"
    AUTH_FAILED = "auth_failed"

    # Cross-service events
    SERVICE_CALL = "service_call"
    SERVICE_EVENT = "service_event"

    # System events
    SYSTEM_EVENT = "system_event"
    ERROR = "error"


class AuditEntry(Base):
    """
    Immutable audit log entry.

    Once created, audit entries cannot be modified or deleted.
    This provides a complete trail for governance and compliance.
    """

    __tablename__ = "audit_entries"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Event classification
    event_type = Column(SQLEnum(AuditEventType), nullable=False, index=True)
    event_name = Column(String, nullable=False)  # e.g., "decision.activate"

    # Entity reference
    entity_type = Column(String, nullable=True, index=True)  # e.g., "decision", "project"
    entity_id = Column(String, nullable=True, index=True)

    # Actor
    actor_type = Column(String, nullable=False)  # "user", "system", "service"
    actor_id = Column(String, nullable=True, index=True)  # user_id or service name

    # State change details (for transitions)
    from_state = Column(String, nullable=True)
    to_state = Column(String, nullable=True)
    transition_name = Column(String, nullable=True)

    # Outcome
    success = Column(Boolean, nullable=False, default=True)
    failure_reason = Column(Text, nullable=True)

    # Context
    project_id = Column(String, nullable=True, index=True)
    correlation_id = Column(String, nullable=True, index=True)  # Request tracing

    # Details
    rationale = Column(Text, nullable=True)
    extra_data = Column(JSON, default=dict)
    side_effects = Column(JSON, default=list)  # What else happened

    # Timestamps
    timestamp = Column(DateTime, default=func.now(), nullable=False, index=True)

    def __repr__(self):
        return f"<AuditEntry {self.event_type.value}:{self.event_name} @ {self.timestamp}>"

    @classmethod
    def create_transition_attempt(
        cls,
        entity_type: str,
        entity_id: str,
        from_state: str,
        to_state: str,
        actor_id: str,
        actor_type: str = "user",
        project_id: str = None,
        correlation_id: str = None,
    ) -> "AuditEntry":
        """Factory method for transition attempt events."""
        return cls(
            event_type=AuditEventType.TRANSITION_ATTEMPT,
            event_name=f"{entity_type}.transition.{to_state}",
            entity_type=entity_type,
            entity_id=entity_id,
            from_state=from_state,
            to_state=to_state,
            actor_type=actor_type,
            actor_id=actor_id,
            project_id=project_id,
            correlation_id=correlation_id,
            success=True,  # Will be updated based on outcome
        )

    @classmethod
    def create_permission_check(
        cls,
        permission: str,
        granted: bool,
        actor_id: str,
        entity_type: str = None,
        entity_id: str = None,
        project_id: str = None,
        reason: str = None,
    ) -> "AuditEntry":
        """Factory method for permission check events."""
        return cls(
            event_type=AuditEventType.PERMISSION_GRANTED if granted else AuditEventType.PERMISSION_DENIED,
            event_name=f"permission.{permission}",
            entity_type=entity_type,
            entity_id=entity_id,
            actor_type="user",
            actor_id=actor_id,
            project_id=project_id,
            success=granted,
            failure_reason=reason if not granted else None,
        )
