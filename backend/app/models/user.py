"""
User model for authentication and authorization.
"""

from sqlalchemy import Column, String, Boolean, DateTime, JSON
from sqlalchemy.sql import func
from datetime import datetime
import uuid

from ..database import Base


class User(Base):
    """User account for authentication and authorization."""

    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)

    # Profile
    name = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)

    # Status
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)

    # Roles and permissions
    roles = Column(JSON, default=list)  # ["admin", "user", "viewer"]
    permissions = Column(JSON, default=dict)  # {"projects.create": true, ...}

    # Context - which projects user has access to
    project_ids = Column(JSON, default=list)
    active_project_id = Column(String, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_login_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<User {self.email}>"

    def has_role(self, role: str) -> bool:
        """Check if user has a specific role."""
        return role in (self.roles or [])

    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission."""
        if self.is_superuser:
            return True
        return (self.permissions or {}).get(permission, False)
