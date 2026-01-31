"""
Authentication router.

Handles login, registration, and token management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..services.auth_service import AuthService

router = APIRouter()
security = HTTPBearer()


# Request/Response schemas
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str]
    roles: list
    is_active: bool

    class Config:
        from_attributes = True


# Dependencies
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_session),
):
    """Get the current authenticated user."""
    auth_service = AuthService(session)
    user = await auth_service.validate_token(credentials.credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


# Endpoints
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    session: AsyncSession = Depends(get_session),
):
    """Register a new user account."""
    auth_service = AuthService(session)

    # Check if user already exists
    existing = await auth_service.get_user_by_email(request.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = await auth_service.create_user(
        email=request.email,
        password=request.password,
        name=request.name,
    )

    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    session: AsyncSession = Depends(get_session),
):
    """Login and get an access token."""
    auth_service = AuthService(session)

    result = await auth_service.authenticate(request.email, request.password)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    user, token = result
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user=Depends(get_current_user),
):
    """Get current user profile."""
    return current_user


@router.post("/logout")
async def logout(
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Logout (invalidate token - placeholder for token blacklist)."""
    # TODO: Implement token blacklist for proper logout
    return {"message": "Logged out successfully"}
