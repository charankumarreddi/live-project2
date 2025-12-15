"""
Prometheus metrics collection for monitoring application performance.
"""
import time
from typing import Dict, Any
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from prometheus_client.core import CollectorRegistry
from functools import wraps
import structlog

from .config import settings

logger = structlog.get_logger(__name__)

# Create custom registry
registry = CollectorRegistry()

# Request metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status_code'],
    registry=registry
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    registry=registry
)

REQUEST_SIZE = Histogram(
    'http_request_size_bytes',
    'HTTP request size in bytes',
    ['method', 'endpoint'],
    registry=registry
)

RESPONSE_SIZE = Histogram(
    'http_response_size_bytes',
    'HTTP response size in bytes',
    ['method', 'endpoint'],
    registry=registry
)

# Application metrics
ACTIVE_CONNECTIONS = Gauge(
    'active_connections_total',
    'Number of active connections',
    registry=registry
)

DATABASE_CONNECTIONS = Gauge(
    'database_connections_active',
    'Number of active database connections',
    registry=registry
)

CACHE_HITS = Counter(
    'cache_hits_total',
    'Total number of cache hits',
    ['cache_type'],
    registry=registry
)

CACHE_MISSES = Counter(
    'cache_misses_total',
    'Total number of cache misses',
    ['cache_type'],
    registry=registry
)

# Business metrics
USER_REGISTRATIONS = Counter(
    'user_registrations_total',
    'Total number of user registrations',
    registry=registry
)

LOGIN_ATTEMPTS = Counter(
    'login_attempts_total',
    'Total number of login attempts',
    ['status'],
    registry=registry
)

API_CALLS = Counter(
    'api_calls_total',
    'Total number of API calls',
    ['service', 'operation'],
    registry=registry
)

ERROR_COUNT = Counter(
    'errors_total',
    'Total number of errors',
    ['error_type', 'service'],
    registry=registry
)

# Performance metrics
TASK_DURATION = Histogram(
    'task_duration_seconds',
    'Task execution duration in seconds',
    ['task_name'],
    registry=registry
)


class MetricsCollector:
    """Centralized metrics collection and management."""
    
    def __init__(self):
        self.registry = registry
        self.enabled = settings.metrics_enabled
        logger.info("Metrics collector initialized", enabled=self.enabled)
    
    def record_request(self, method: str, endpoint: str, status_code: int, 
                      duration: float, request_size: int = 0, response_size: int = 0):
        """Record HTTP request metrics."""
        if not self.enabled:
            return
            
        REQUEST_COUNT.labels(
            method=method,
            endpoint=endpoint, 
            status_code=str(status_code)
        ).inc()
        
        REQUEST_DURATION.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
        
        if request_size > 0:
            REQUEST_SIZE.labels(
                method=method,
                endpoint=endpoint
            ).observe(request_size)
            
        if response_size > 0:
            RESPONSE_SIZE.labels(
                method=method,
                endpoint=endpoint
            ).observe(response_size)
    
    def record_cache_hit(self, cache_type: str):
        """Record cache hit."""
        if self.enabled:
            CACHE_HITS.labels(cache_type=cache_type).inc()
    
    def record_cache_miss(self, cache_type: str):
        """Record cache miss."""
        if self.enabled:
            CACHE_MISSES.labels(cache_type=cache_type).inc()
    
    def record_user_registration(self):
        """Record user registration."""
        if self.enabled:
            USER_REGISTRATIONS.inc()
    
    def record_login_attempt(self, success: bool):
        """Record login attempt."""
        if self.enabled:
            status = "success" if success else "failure"
            LOGIN_ATTEMPTS.labels(status=status).inc()
    
    def record_api_call(self, service: str, operation: str):
        """Record API call."""
        if self.enabled:
            API_CALLS.labels(service=service, operation=operation).inc()
    
    def record_error(self, error_type: str, service: str):
        """Record error occurrence."""
        if self.enabled:
            ERROR_COUNT.labels(error_type=error_type, service=service).inc()
    
    def set_active_connections(self, count: int):
        """Set number of active connections."""
        if self.enabled:
            ACTIVE_CONNECTIONS.set(count)
    
    def set_database_connections(self, count: int):
        """Set number of active database connections."""
        if self.enabled:
            DATABASE_CONNECTIONS.set(count)
    
    def get_metrics(self) -> str:
        """Get all metrics in Prometheus format."""
        if not self.enabled:
            return ""
        return generate_latest(self.registry)


# Global metrics collector instance
metrics_collector = MetricsCollector()


def track_time(task_name: str):
    """Decorator to track task execution time."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if not metrics_collector.enabled:
                return await func(*args, **kwargs)
                
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                TASK_DURATION.labels(task_name=task_name).observe(duration)
                logger.debug("Task completed", task=task_name, duration=duration)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            if not metrics_collector.enabled:
                return func(*args, **kwargs)
                
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                TASK_DURATION.labels(task_name=task_name).observe(duration)
                logger.debug("Task completed", task=task_name, duration=duration)
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator