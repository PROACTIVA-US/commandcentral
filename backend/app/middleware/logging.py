"""
Request/Response logging middleware using structlog.
"""

import time
import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = structlog.get_logger("commandcentral.http")


class LoggingMiddleware(BaseHTTPMiddleware):
    """Log all HTTP requests and responses with timing."""

    async def dispatch(self, request: Request, call_next) -> Response:
        # Get correlation ID if present
        correlation_id = request.headers.get("X-Correlation-ID", "-")
        
        # Start timer
        start_time = time.perf_counter()
        
        # Log request
        await logger.ainfo(
            "request_started",
            method=request.method,
            path=request.url.path,
            query=str(request.query_params),
            client=request.client.host if request.client else "-",
            correlation_id=correlation_id,
        )
        
        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            # Log error
            duration_ms = (time.perf_counter() - start_time) * 1000
            await logger.aerror(
                "request_failed",
                method=request.method,
                path=request.url.path,
                error=str(e),
                duration_ms=round(duration_ms, 2),
                correlation_id=correlation_id,
            )
            raise
        
        # Calculate duration
        duration_ms = (time.perf_counter() - start_time) * 1000
        
        # Log response
        await logger.ainfo(
            "request_completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
            correlation_id=correlation_id,
        )
        
        # Add timing header
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
        
        return response
