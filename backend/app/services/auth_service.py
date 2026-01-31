"""
Authentication Service

Handles user authentication, JWT tokens, and session management.
"""

from datetime import datetime, timedelta
from typing import Optional
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext
from jose import JWTError, jwt

from ..config import get_settings
from ..models.user import User
from ..models.audit import AuditEntry, AuditEventType

settings = get_settings()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Service for authentication operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # Password utilities
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password for storage."""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)

    # JWT utilities
    @staticmethod
    def create_access_token(user_id: str, email: str, roles: list = None) -> str:
        """Create a JWT access token."""
        expire = datetime.utcnow() + timedelta(hours=settings.jwt_expiration_hours)
        to_encode = {
            "sub": user_id,
            "email": email,
            "roles": roles or [],
            "exp": expire,
            "iat": datetime.utcnow(),
            "jti": str(uuid.uuid4()),  # Unique token ID
        }
        return jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)

    @staticmethod
    def decode_token(token: str) -> Optional[dict]:
        """Decode and validate a JWT token."""
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
            return payload
        except JWTError:
            return None

    # User operations
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email address."""
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_user(
        self,
        email: str,
        password: str,
        name: str = None,
        roles: list = None,
    ) -> User:
        """Create a new user account."""
        user = User(
            email=email,
            hashed_password=self.hash_password(password),
            name=name,
            roles=roles or ["user"],
        )
        self.session.add(user)
        await self.session.flush()

        # Audit log
        audit = AuditEntry(
            event_type=AuditEventType.ENTITY_CREATED,
            event_name="user.created",
            entity_type="user",
            entity_id=user.id,
            actor_type="system",
            actor_id=user.id,
            success=True,
        )
        self.session.add(audit)

        return user

    async def authenticate(self, email: str, password: str) -> Optional[tuple[User, str]]:
        """
        Authenticate user and return user + token if successful.

        Returns None if authentication fails.
        """
        user = await self.get_user_by_email(email)

        if not user or not self.verify_password(password, user.hashed_password):
            # Log failed attempt
            audit = AuditEntry(
                event_type=AuditEventType.AUTH_FAILED,
                event_name="auth.login.failed",
                actor_type="user",
                actor_id=email,
                success=False,
                failure_reason="Invalid credentials",
            )
            self.session.add(audit)
            return None

        if not user.is_active:
            audit = AuditEntry(
                event_type=AuditEventType.AUTH_FAILED,
                event_name="auth.login.failed",
                actor_type="user",
                actor_id=user.id,
                success=False,
                failure_reason="Account inactive",
            )
            self.session.add(audit)
            return None

        # Update last login
        user.last_login_at = datetime.utcnow()

        # Create token
        token = self.create_access_token(user.id, user.email, user.roles)

        # Log success
        audit = AuditEntry(
            event_type=AuditEventType.AUTH_LOGIN,
            event_name="auth.login.success",
            entity_type="user",
            entity_id=user.id,
            actor_type="user",
            actor_id=user.id,
            success=True,
        )
        self.session.add(audit)

        return user, token

    async def validate_token(self, token: str) -> Optional[User]:
        """Validate a token and return the user if valid."""
        payload = self.decode_token(token)
        if not payload:
            return None

        user_id = payload.get("sub")
        if not user_id:
            return None

        return await self.get_user_by_id(user_id)
