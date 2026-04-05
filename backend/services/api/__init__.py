"""
API优化模块
"""
from .api_optimization import (
    DistributedRateLimiter,
    get_rate_limiter,
    init_rate_limiter,
    close_rate_limiter,
    CircuitBreaker,
    CircuitBreakerRegistry,
    CircuitBreakerConfig,
    DegradationManager,
    rate_limit,
    circuit_breaker,
    degradeable
)

__all__ = [
    "DistributedRateLimiter",
    "get_rate_limiter",
    "init_rate_limiter",
    "close_rate_limiter",
    "CircuitBreaker",
    "CircuitBreakerRegistry",
    "CircuitBreakerConfig",
    "DegradationManager",
    "rate_limit",
    "circuit_breaker",
    "degradeable"
]
