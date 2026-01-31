"""
Rate limiting middleware using in-memory token bucket.

For production, use Redis-based rate limiting.
"""

import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from ..config import get_settings

settings = get_settings()


@dataclass
class TokenBucket:
    """Simple token bucket for rate limiting."""
    tokens: float
    last_update: float
    capacity: int
    fill_rate: float  # tokens per second
    
    def consume(self) -> bool:
        """Try to consume a token. Returns True if allowed."""
        now = time.time()
        # Add tokens based on time passed
        elapsed = now - self.last_update
        self.tokens = min(self.capacity, self.tokens + elapsed * self.fill_rate)
        self.last_update = now
        
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limit requests per client IP using token bucket.
    
    Defaults from settings:
    - RATE_LIMIT_REQUESTS: max requests per window
    - RATE_LIMIT_WINDOW: window size in seconds
    """
    
    def __init__(self, app, requests_per_window: int = None, window_seconds: int = None):
        super().__init__(app)
        self.requests_per_window = requests_per_window or settings.rate_limit_requests
        self.window_seconds = window_seconds or settings.rate_limit_window
        self.fill_rate = self.requests_per_window / self.window_seconds
        self.buckets: Dict[str, TokenBucket] = defaultdict(self._create_bucket)
    
    def _create_bucket(self) -> TokenBucket:
        """Create a new token bucket for a client."""
        return TokenBucket(
            tokens=self.requests_per_window,
            last_update=time.time(),
            capacity=self.requests_per_window,
            fill_rate=self.fill_rate,
        )
    
    def _get_client_key(self, request: Request) -> str:
        """Get rate limit key for client (IP-based)."""
        # Check X-Forwarded-For for clients behind proxies
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip rate limiting for health checks
        if request.url.path in ("/health", "/healthz", "/"):
            return await call_next(request)
        
        client_key = self._get_client_key(request)
        bucket = self.buckets[client_key]
        
        if not bucket.consume():
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded",
                    "retry_after": self.window_seconds,
                },
                headers={
                    "Retry-After": str(self.window_seconds),
                    "X-RateLimit-Limit": str(self.requests_per_window),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time() + self.window_seconds)),
                },
            )
        
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_window)
        response.headers["X-RateLimit-Remaining"] = str(int(bucket.tokens))
        
        return response
