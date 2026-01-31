"""
Common schemas used across the API.
"""

from pydantic import BaseModel, Field
from typing import Generic, TypeVar, Optional, List, Any
from datetime import datetime

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Pagination parameters for list endpoints."""
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    
    @classmethod
    def create(cls, items: List[T], total: int, page: int, page_size: int):
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size,
        )


class ErrorResponse(BaseModel):
    """Standard error response."""
    detail: str
    error_code: Optional[str] = None
    correlation_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SuccessResponse(BaseModel):
    """Standard success response."""
    message: str
    data: Optional[Any] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    service: str
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    checks: dict = Field(default_factory=dict)
