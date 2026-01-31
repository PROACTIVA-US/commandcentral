"""
Correlation ID middleware for request tracing.

Adds correlation IDs to all requests for distributed tracing.
"""

import uuid
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Context variable for correlation ID (accessible throughout request lifecycle)
correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="-")


def get_correlation_id() -> str:
    """Get the current correlation ID."""
    return correlation_id_var.get()


class CorrelationMiddleware(BaseHTTPMiddleware):
    """
    Add correlation IDs to requests for tracing.
    
    - Uses X-Correlation-ID header if present
    - Generates a new UUID if not present
    - Adds correlation ID to response headers
    """
    
    HEADER_NAME = "X-Correlation-ID"
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Get existing correlation ID or generate new one
        correlation_id = request.headers.get(self.HEADER_NAME)
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
        
        # Set in context var (accessible throughout request)
        correlation_id_var.set(correlation_id)
        
        # Store in request state for access in route handlers
        request.state.correlation_id = correlation_id
        
        # Process request
        response = await call_next(request)
        
        # Add to response headers
        response.headers[self.HEADER_NAME] = correlation_id
        
        return response
