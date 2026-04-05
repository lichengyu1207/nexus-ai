"""
API优化模块
限流、熔断、降级、响应优化
"""
import asyncio
import time
import logging
from typing import Any, Optional, Callable, Dict, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from abc import ABC, abstractmethod
import hashlib
import json

try:
    import redis.asyncio as aioredis
    from redis.asyncio import Redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    Redis = None

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitStats:
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[float] = None
    last_state_change: float = field(default_factory=time.time)
    total_requests: int = 0
    total_failures: int = 0
    total_successes: int = 0


@dataclass
class RateLimitConfig:
    requests_per_second: int = 100
    requests_per_minute: int = 6000
    burst_size: int = 200
    key_prefix: str = "ratelimit"


@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5
    success_threshold: int = 3
    timeout: float = 30.0
    half_open_requests: int = 3


class RateLimiterBackend(ABC):
    """限流后端抽象"""
    
    @abstractmethod
    async def is_allowed(self, key: str, config: RateLimitConfig) -> tuple[bool, Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def reset(self, key: str) -> bool:
        pass


class InMemoryRateLimiter(RateLimiterBackend):
    """内存限流器"""
    
    def __init__(self):
        self._counters: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
    
    async def is_allowed(self, key: str, config: RateLimitConfig) -> tuple[bool, Dict[str, Any]]:
        async with self._lock:
            now = time.time()
            current_second = int(now)
            current_minute = int(now / 60)
            
            if key not in self._counters:
                self._counters[key] = {
                    "second_counters": {},
                    "minute_counters": {},
                    "burst_tokens": config.burst_size,
                    "last_refill": now
                }
            
            counter = self._counters[key]
            
            elapsed = now - counter["last_refill"]
            tokens_to_add = int(elapsed * config.requests_per_second)
            counter["burst_tokens"] = min(
                config.burst_size,
                counter["burst_tokens"] + tokens_to_add
            )
            counter["last_refill"] = now
            
            second_key = str(current_second)
            minute_key = str(current_minute)
            
            second_count = counter["second_counters"].get(second_key, 0)
            minute_count = counter["minute_counters"].get(minute_key, 0)
            
            allowed = (
                second_count < config.requests_per_second
                and minute_count < config.requests_per_minute
                and counter["burst_tokens"] > 0
            )
            
            if allowed:
                counter["second_counters"][second_key] = second_count + 1
                counter["minute_counters"][minute_key] = minute_count + 1
                counter["burst_tokens"] -= 1
            
            self._cleanup_old_counters(counter, current_second, current_minute)
            
            return allowed, {
                "second_remaining": max(0, config.requests_per_second - second_count - 1),
                "minute_remaining": max(0, config.requests_per_minute - minute_count - 1),
                "burst_remaining": counter["burst_tokens"],
                "limit": config.requests_per_second
            }
    
    def _cleanup_old_counters(self, counter: Dict, current_second: int, current_minute: int):
        counter["second_counters"] = {
            k: v for k, v in counter["second_counters"].items()
            if int(k) >= current_second - 2
        }
        counter["minute_counters"] = {
            k: v for k, v in counter["minute_counters"].items()
            if int(k) >= current_minute - 2
        }
    
    async def reset(self, key: str) -> bool:
        async with self._lock:
            if key in self._counters:
                del self._counters[key]
                return True
            return False


class RedisRateLimiter(RateLimiterBackend):
    """Redis分布式限流器"""
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
    
    async def is_allowed(self, key: str, config: RateLimitConfig) -> tuple[bool, Dict[str, Any]]:
        now = time.time()
        current_second = int(now)
        current_minute = int(now / 60)
        
        second_key = f"{config.key_prefix}:{key}:second:{current_second}"
        minute_key = f"{config.key_prefix}:{key}:minute:{current_minute}"
        burst_key = f"{config.key_prefix}:{key}:burst"
        
        try:
            pipe = self.redis.pipeline()
            
            pipe.incr(second_key)
            pipe.expire(second_key, 2)
            
            pipe.incr(minute_key)
            pipe.expire(minute_key, 120)
            
            results = await pipe.execute()
            
            second_count = results[0]
            minute_count = results[2]
            
            burst_tokens = await self.redis.get(burst_key)
            burst_tokens = int(burst_tokens) if burst_tokens else config.burst_size
            
            elapsed = now % 1
            tokens_to_add = int(elapsed * config.requests_per_second)
            burst_tokens = min(config.burst_size, burst_tokens + tokens_to_add)
            
            allowed = (
                second_count <= config.requests_per_second
                and minute_count <= config.requests_per_minute
                and burst_tokens > 0
            )
            
            if allowed:
                await self.redis.decr(burst_key)
                burst_tokens -= 1
            else:
                await self.redis.set(burst_key, burst_tokens, ex=60)
            
            return allowed, {
                "second_remaining": max(0, config.requests_per_second - second_count),
                "minute_remaining": max(0, config.requests_per_minute - minute_count),
                "burst_remaining": max(0, burst_tokens),
                "limit": config.requests_per_second
            }
            
        except Exception as e:
            logger.warning(f"Redis rate limiter error: {e}")
            return True, {"error": str(e)}
    
    async def reset(self, key: str) -> bool:
        try:
            pattern = f"ratelimit:{key}:*"
            keys = []
            async for k in self.redis.scan_iter(match=pattern):
                keys.append(k)
            
            if keys:
                await self.redis.delete(*keys)
            return True
        except Exception as e:
            logger.warning(f"Redis reset error: {e}")
            return False


class DistributedRateLimiter:
    """分布式限流器"""
    
    def __init__(self, redis_url: str = None):
        self._redis: Optional[Redis] = None
        self._redis_url = redis_url
        self._memory_limiter = InMemoryRateLimiter()
        self._redis_limiter: Optional[RedisRateLimiter] = None
        self._use_redis = False
        self._configs: Dict[str, RateLimitConfig] = {}
    
    async def initialize(self) -> bool:
        if REDIS_AVAILABLE and self._redis_url:
            try:
                self._redis = await aioredis.from_url(
                    self._redis_url,
                    encoding="utf-8",
                    decode_responses=True
                )
                await self._redis.ping()
                self._redis_limiter = RedisRateLimiter(self._redis)
                self._use_redis = True
                logger.info("Distributed rate limiter initialized with Redis")
                return True
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}, using memory limiter")
        
        self._use_redis = False
        logger.info("Rate limiter initialized with in-memory backend")
        return True
    
    async def close(self):
        if self._redis:
            await self._redis.close()
    
    def configure(self, name: str, config: RateLimitConfig):
        self._configs[name] = config
    
    async def is_allowed(
        self,
        identifier: str,
        config_name: str = "default"
    ) -> tuple[bool, Dict[str, Any]]:
        config = self._configs.get(config_name, RateLimitConfig())
        
        if self._use_redis and self._redis_limiter:
            return await self._redis_limiter.is_allowed(identifier, config)
        else:
            return await self._memory_limiter.is_allowed(identifier, config)
    
    async def reset(self, identifier: str) -> bool:
        if self._use_redis and self._redis_limiter:
            return await self._redis_limiter.reset(identifier)
        else:
            return await self._memory_limiter.reset(identifier)


class CircuitBreaker:
    """熔断器"""
    
    def __init__(
        self,
        name: str,
        config: CircuitBreakerConfig = None
    ):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self._stats = CircuitStats()
        self._lock = asyncio.Lock()
        self._half_open_count = 0
    
    @property
    def state(self) -> CircuitState:
        return self._stats.state
    
    @property
    def is_open(self) -> bool:
        return self._stats.state == CircuitState.OPEN
    
    @property
    def is_closed(self) -> bool:
        return self._stats.state == CircuitState.CLOSED
    
    @property
    def is_half_open(self) -> bool:
        return self._stats.state == CircuitState.HALF_OPEN
    
    async def can_execute(self) -> bool:
        async with self._lock:
            if self._stats.state == CircuitState.CLOSED:
                return True
            
            if self._stats.state == CircuitState.OPEN:
                elapsed = time.time() - self._stats.last_failure_time
                
                if elapsed >= self.config.timeout:
                    await self._transition_to(CircuitState.HALF_OPEN)
                    return True
                return False
            
            if self._stats.state == CircuitState.HALF_OPEN:
                if self._half_open_count < self.config.half_open_requests:
                    self._half_open_count += 1
                    return True
                return False
        
        return False
    
    async def record_success(self):
        async with self._lock:
            self._stats.success_count += 1
            self._stats.total_successes += 1
            self._stats.total_requests += 1
            
            if self._stats.state == CircuitState.HALF_OPEN:
                if self._stats.success_count >= self.config.success_threshold:
                    await self._transition_to(CircuitState.CLOSED)
            
            elif self._stats.state == CircuitState.CLOSED:
                self._stats.failure_count = 0
    
    async def record_failure(self):
        async with self._lock:
            self._stats.failure_count += 1
            self._stats.total_failures += 1
            self._stats.total_requests += 1
            self._stats.last_failure_time = time.time()
            
            if self._stats.state == CircuitState.HALF_OPEN:
                await self._transition_to(CircuitState.OPEN)
            
            elif self._stats.state == CircuitState.CLOSED:
                if self._stats.failure_count >= self.config.failure_threshold:
                    await self._transition_to(CircuitState.OPEN)
    
    async def _transition_to(self, new_state: CircuitState):
        old_state = self._stats.state
        self._stats.state = new_state
        self._stats.last_state_change = time.time()
        
        if new_state == CircuitState.CLOSED:
            self._stats.failure_count = 0
            self._stats.success_count = 0
            self._half_open_count = 0
        
        elif new_state == CircuitState.HALF_OPEN:
            self._stats.success_count = 0
            self._half_open_count = 0
        
        elif new_state == CircuitState.OPEN:
            self._half_open_count = 0
        
        logger.info(f"Circuit breaker '{self.name}': {old_state.value} -> {new_state.value}")
    
    async def force_open(self):
        async with self._lock:
            await self._transition_to(CircuitState.OPEN)
    
    async def force_close(self):
        async with self._lock:
            await self._transition_to(CircuitState.CLOSED)
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "state": self._stats.state.value,
            "failure_count": self._stats.failure_count,
            "success_count": self._stats.success_count,
            "total_requests": self._stats.total_requests,
            "total_failures": self._stats.total_failures,
            "total_successes": self._stats.total_successes,
            "last_failure_time": self._stats.last_failure_time,
            "last_state_change": self._stats.last_state_change
        }


class CircuitBreakerRegistry:
    """熔断器注册表"""
    
    _instance: Optional['CircuitBreakerRegistry'] = None
    
    def __init__(self):
        self._breakers: Dict[str, CircuitBreaker] = {}
        self._configs: Dict[str, CircuitBreakerConfig] = {}
    
    @classmethod
    def get_instance(cls) -> 'CircuitBreakerRegistry':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def configure(self, name: str, config: CircuitBreakerConfig):
        self._configs[name] = config
        
        if name in self._breakers:
            self._breakers[name].config = config
    
    def get_breaker(self, name: str) -> CircuitBreaker:
        if name not in self._breakers:
            config = self._configs.get(name, CircuitBreakerConfig())
            self._breakers[name] = CircuitBreaker(name, config)
        return self._breakers[name]
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        return {
            name: breaker.get_stats()
            for name, breaker in self._breakers.items()
        }


class DegradationManager:
    """降级管理器"""
    
    _instance: Optional['DegradationManager'] = None
    
    def __init__(self):
        self._degraded_features: Dict[str, bool] = {}
        self._fallback_handlers: Dict[str, Callable] = {}
        self._config: Dict[str, Any] = {}
    
    @classmethod
    def get_instance(cls) -> 'DegradationManager':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def register_fallback(self, feature: str, handler: Callable):
        self._fallback_handlers[feature] = handler
    
    def set_degraded(self, feature: str, degraded: bool = True):
        self._degraded_features[feature] = degraded
        logger.warning(f"Feature '{feature}' degradation set to: {degraded}")
    
    def is_degraded(self, feature: str) -> bool:
        return self._degraded_features.get(feature, False)
    
    async def get_fallback_result(self, feature: str, *args, **kwargs) -> Any:
        handler = self._fallback_handlers.get(feature)
        if handler:
            if asyncio.iscoroutinefunction(handler):
                return await handler(*args, **kwargs)
            else:
                return handler(*args, **kwargs)
        return None
    
    def get_status(self) -> Dict[str, Any]:
        return {
            "degraded_features": self._degraded_features,
            "registered_features": list(self._fallback_handlers.keys())
        }


def rate_limit(
    identifier_func: Callable = None,
    config_name: str = "default"
):
    """限流装饰器"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            limiter = await DistributedRateLimiter.get_instance()
            
            if identifier_func:
                identifier = identifier_func(*args, **kwargs)
            else:
                identifier = "default"
            
            allowed, info = await limiter.is_allowed(identifier, config_name)
            
            if not allowed:
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded",
                    headers={
                        "X-RateLimit-Limit": str(info.get("limit", 100)),
                        "X-RateLimit-Remaining": str(info.get("burst_remaining", 0)),
                        "Retry-After": "60"
                    }
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def circuit_breaker(
    name: str,
    fallback: Callable = None
):
    """熔断装饰器"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            registry = CircuitBreakerRegistry.get_instance()
            breaker = registry.get_breaker(name)
            
            if not await breaker.can_execute():
                if fallback:
                    if asyncio.iscoroutinefunction(fallback):
                        return await fallback(*args, **kwargs)
                    return fallback(*args, **kwargs)
                
                raise Exception(f"Circuit breaker '{name}' is open")
            
            try:
                result = await func(*args, **kwargs)
                await breaker.record_success()
                return result
            except Exception as e:
                await breaker.record_failure()
                raise
        
        return wrapper
    return decorator


def degradeable(
    feature: str,
    fallback: Callable = None
):
    """降级装饰器"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            manager = DegradationManager.get_instance()
            
            if manager.is_degraded(feature):
                if fallback:
                    if asyncio.iscoroutinefunction(fallback):
                        return await fallback(*args, **kwargs)
                    return fallback(*args, **kwargs)
                
                return await manager.get_fallback_result(feature, *args, **kwargs)
            
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Feature '{feature}' failed, activating degradation: {e}")
                manager.set_degraded(feature, True)
                
                if fallback:
                    if asyncio.iscoroutinefunction(fallback):
                        return await fallback(*args, **kwargs)
                    return fallback(*args, **kwargs)
                
                raise
        
        return wrapper
    return decorator


rate_limiter_instance: Optional[DistributedRateLimiter] = None


async def get_rate_limiter() -> DistributedRateLimiter:
    global rate_limiter_instance
    if rate_limiter_instance is None:
        rate_limiter_instance = DistributedRateLimiter()
        await rate_limiter_instance.initialize()
    return rate_limiter_instance


async def init_rate_limiter() -> bool:
    limiter = await get_rate_limiter()
    limiter.configure("default", RateLimitConfig())
    limiter.configure("strict", RateLimitConfig(
        requests_per_second=10,
        requests_per_minute=100,
        burst_size=20
    ))
    limiter.configure("loose", RateLimitConfig(
        requests_per_second=1000,
        requests_per_minute=60000,
        burst_size=2000
    ))
    return True


async def close_rate_limiter():
    global rate_limiter_instance
    if rate_limiter_instance:
        await rate_limiter_instance.close()
        rate_limiter_instance = None
