"""
Authentication and user schemas.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


class UserCreate(BaseModel):
    """Schema for creating a new user."""
    email: EmailStr
    password: str = Field(min_length=8, description="Password (min 8 chars)")
    name: Optional[str] = None


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    """User response schema."""
    id: str
    email: str
    name: Optional[str]
    avatar_url: Optional[str]
    roles: List[str]
    is_active: bool
    is_superuser: bool
    project_ids: List[str]
    active_project_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime]

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Token expiration in seconds")


class LoginRequest(BaseModel):
    """Login request schema."""
    email: EmailStr
    password: str
