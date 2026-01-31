"""
Simple metrics collection middleware.

Tracks request counts, latencies, and error rates.
For production, integrate with Prometheus or similar.
"""

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


@dataclass
class EndpointMetrics:
    """Metrics for a single endpoint."""
    request_count: int = 0
    error_count: int = 0
    total_latency_ms: float = 0.0
    latencies: List[float] = field(default_factory=list)
    
    def record(self, latency_ms: float, is_error: bool):
        """Record a request."""
        self.request_count += 1
        self.total_latency_ms += latency_ms
        
        # Keep last 1000 latencies for percentile calculations
        self.latencies.append(latency_ms)
        if len(self.latencies) > 1000:
            self.latencies = self.latencies[-1000:]
        
        if is_error:
            self.error_count += 1
    
    @property
    def avg_latency_ms(self) -> float:
        if self.request_count == 0:
            return 0.0
        return self.total_latency_ms / self.request_count
    
    @property
    def p50_latency_ms(self) -> float:
        if not self.latencies:
            return 0.0
        sorted_latencies = sorted(self.latencies)
        return sorted_latencies[len(sorted_latencies) // 2]
    
    @property
    def p99_latency_ms(self) -> float:
        if not self.latencies:
            return 0.0
        sorted_latencies = sorted(self.latencies)
        idx = int(len(sorted_latencies) * 0.99)
        return sorted_latencies[min(idx, len(sorted_latencies) - 1)]
    
    @property
    def error_rate(self) -> float:
        if self.request_count == 0:
            return 0.0
        return self.error_count / self.request_count


class MetricsCollector:
    """Central metrics collector."""
    
    def __init__(self):
        self.endpoints: Dict[str, EndpointMetrics] = defaultdict(EndpointMetrics)
        self.start_time = time.time()
    
    def record_request(self, method: str, path: str, latency_ms: float, status_code: int):
        """Record a request to an endpoint."""
        key = f"{method} {path}"
        is_error = status_code >= 400
        self.endpoints[key].record(latency_ms, is_error)
    
    def get_summary(self) -> dict:
        """Get a summary of all metrics."""
        total_requests = sum(m.request_count for m in self.endpoints.values())
        total_errors = sum(m.error_count for m in self.endpoints.values())
        
        return {
            "uptime_seconds": time.time() - self.start_time,
            "total_requests": total_requests,
            "total_errors": total_errors,
            "error_rate": total_errors / total_requests if total_requests > 0 else 0.0,
            "endpoints": {
                key: {
                    "requests": m.request_count,
                    "errors": m.error_count,
                    "error_rate": m.error_rate,
                    "avg_latency_ms": round(m.avg_latency_ms, 2),
                    "p50_latency_ms": round(m.p50_latency_ms, 2),
                    "p99_latency_ms": round(m.p99_latency_ms, 2),
                }
                for key, m in self.endpoints.items()
            },
        }


# Global collector instance
collector = MetricsCollector()


class MetricsMiddleware(BaseHTTPMiddleware):
    """Collect metrics for all requests."""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.perf_counter()
        
        response = await call_next(request)
        
        latency_ms = (time.perf_counter() - start_time) * 1000
        
        # Normalize path for metrics (avoid cardinality explosion)
        path = self._normalize_path(request.url.path)
        
        collector.record_request(
            method=request.method,
            path=path,
            latency_ms=latency_ms,
            status_code=response.status_code,
        )
        
        return response
    
    def _normalize_path(self, path: str) -> str:
        """
        Normalize path to prevent high cardinality.
        
        Replaces UUIDs and numeric IDs with placeholders.
        """
        import re
        
        # Replace UUIDs
        path = re.sub(
            r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
            "{id}",
            path,
            flags=re.IGNORECASE,
        )
        
        # Replace numeric IDs
        path = re.sub(r"/\d+(/|$)", "/{id}\\1", path)
        
        return path


def get_metrics() -> dict:
    """Get current metrics summary."""
    return collector.get_summary()
