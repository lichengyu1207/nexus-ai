"""
API限流中间件
支持IP限流、用户限流、接口限流
使用滑动窗口算法
"""
import time
import asyncio
from typing import Dict, Optional, Callable, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
from datetime import datetime, timedelta
import logging

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """限流配置"""
    requests_per_second: int = 10
    requests_per_minute: int = 100
    requests_per_hour: int = 1000
    burst_size: int = 20
    enabled: bool = True


@dataclass
class RateLimitState:
    """限流状态"""
    tokens: float = 0.0
    last_update: float = field(default_factory=time.time)
    request_times: list = field(default_factory=list)


class SlidingWindowCounter:
    """滑动窗口计数器"""

    def __init__(self, window_size: int = 60):
        self.window_size = window_size
        self.requests: Dict[str, list] = defaultdict(list)

    def is_allowed(self, key: str, limit: int) -> Tuple[bool, int]:
        """
        检查是否允许请求
        
        Returns:
            (is_allowed, remaining_count)
        """
        now = time.time()
        window_start = now - self.window_size
        
        self.requests[key] = [
            t for t in self.requests[key] if t > window_start
        ]
        
        current_count = len(self.requests[key])
        
        if current_count < limit:
            self.requests[key].append(now)
            return True, limit - current_count - 1
        
        return False, 0

    def get_wait_time(self, key: str) -> float:
        """获取需要等待的时间"""
        if not self.requests[key]:
            return 0.0
        
        oldest = min(self.requests[key])
        return max(0, oldest + self.window_size - time.time())


class TokenBucket:
    """令牌桶算法"""

    def __init__(self, rate: float, capacity: int):
        self.rate = rate
        self.capacity = capacity
        self.buckets: Dict[str, RateLimitState] = {}

    def _get_bucket(self, key: str) -> RateLimitState:
        if key not in self.buckets:
            self.buckets[key] = RateLimitState(tokens=float(self.capacity))
        return self.buckets[key]

    def is_allowed(self, key: str, tokens_needed: int = 1) -> Tuple[bool, float]:
        """
        检查是否允许请求
        
        Returns:
            (is_allowed, remaining_tokens)
        """
        bucket = self._get_bucket(key)
        now = time.time()
        
        elapsed = now - bucket.last_update
        bucket.tokens = min(
            self.capacity,
            bucket.tokens + elapsed * self.rate
        )
        bucket.last_update = now
        
        if bucket.tokens >= tokens_needed:
            bucket.tokens -= tokens_needed
            return True, bucket.tokens
        
        return False, bucket.tokens

    def get_wait_time(self, key: str, tokens_needed: int = 1) -> float:
        """获取需要等待的时间"""
        bucket = self._get_bucket(key)
        
        if bucket.tokens >= tokens_needed:
            return 0.0
        
        tokens_needed = tokens_needed - bucket.tokens
        return tokens_needed / self.rate


class RateLimiter:
    """限流器"""

    def __init__(self):
        self.ip_limiter = SlidingWindowCounter(window_size=60)
        self.user_limiter = SlidingWindowCounter(window_size=60)
        self.endpoint_limiter = SlidingWindowCounter(window_size=60)
        self.token_bucket = TokenBucket(rate=10.0, capacity=100)
        
        self.configs: Dict[str, RateLimitConfig] = {
            "default": RateLimitConfig(),
            "api/tasks": RateLimitConfig(requests_per_minute=30, burst_size=10),
            "api/tasks/batch": RateLimitConfig(requests_per_minute=10, burst_size=5),
            "api/auth": RateLimitConfig(requests_per_minute=20, burst_size=5),
            "api/three-provinces": RateLimitConfig(requests_per_minute=50, burst_size=20),
        }
        
        self.whitelist_ips: set = set()
        self.blacklist_ips: set = set()

    def get_config(self, path: str) -> RateLimitConfig:
        """获取路径对应的限流配置"""
        for key, config in self.configs.items():
            if key in path:
                return config
        return self.configs["default"]

    def check_ip_rate_limit(
        self, 
        ip: str, 
        path: str
    ) -> Tuple[bool, Dict[str, any]]:
        """检查IP限流"""
        if ip in self.whitelist_ips:
            return True, {"limited": False}
        
        if ip in self.blacklist_ips:
            return False, {
                "limited": True,
                "reason": "IP黑名单",
                "retry_after": 3600
            }
        
        config = self.get_config(path)
        if not config.enabled:
            return True, {"limited": False}
        
        key = f"ip:{ip}:{path}"
        allowed, remaining = self.ip_limiter.is_allowed(
            key, 
            config.requests_per_minute
        )
        
        if allowed:
            return True, {
                "limited": False,
                "remaining": remaining,
                "limit": config.requests_per_minute
            }
        
        wait_time = self.ip_limiter.get_wait_time(key)
        return False, {
            "limited": True,
            "reason": "IP请求频率超限",
            "retry_after": int(wait_time) + 1,
            "limit": config.requests_per_minute
        }

    def check_user_rate_limit(
        self, 
        user_id: str, 
        path: str
    ) -> Tuple[bool, Dict[str, any]]:
        """检查用户限流"""
        config = self.get_config(path)
        if not config.enabled:
            return True, {"limited": False}
        
        key = f"user:{user_id}:{path}"
        allowed, remaining = self.user_limiter.is_allowed(
            key,
            config.requests_per_minute
        )
        
        if allowed:
            return True, {
                "limited": False,
                "remaining": remaining,
                "limit": config.requests_per_minute
            }
        
        wait_time = self.user_limiter.get_wait_time(key)
        return False, {
            "limited": True,
            "reason": "用户请求频率超限",
            "retry_after": int(wait_time) + 1,
            "limit": config.requests_per_minute
        }

    def check_endpoint_rate_limit(
        self, 
        path: str
    ) -> Tuple[bool, Dict[str, any]]:
        """检查接口限流"""
        config = self.get_config(path)
        if not config.enabled:
            return True, {"limited": False}
        
        key = f"endpoint:{path}"
        allowed, remaining = self.endpoint_limiter.is_allowed(
            key,
            config.requests_per_minute * 10
        )
        
        if allowed:
            return True, {
                "limited": False,
                "remaining": remaining
            }
        
        wait_time = self.endpoint_limiter.get_wait_time(key)
        return False, {
            "limited": True,
            "reason": "接口请求频率超限",
            "retry_after": int(wait_time) + 1
        }

    def add_to_whitelist(self, ip: str) -> None:
        """添加IP到白名单"""
        self.whitelist_ips.add(ip)
        self.blacklist_ips.discard(ip)

    def add_to_blacklist(self, ip: str) -> None:
        """添加IP到黑名单"""
        self.blacklist_ips.add(ip)
        self.whitelist_ips.discard(ip)

    def get_stats(self) -> Dict[str, any]:
        """获取限流统计"""
        return {
            "ip_requests": dict(self.ip_limiter.requests),
            "user_requests": dict(self.user_limiter.requests),
            "endpoint_requests": dict(self.endpoint_limiter.requests),
            "whitelist_count": len(self.whitelist_ips),
            "blacklist_count": len(self.blacklist_ips),
        }


_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """获取全局限流器"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


class RateLimitMiddleware(BaseHTTPMiddleware):
    """限流中间件"""

    def __init__(
        self,
        app: ASGIApp,
        enabled: bool = True,
        default_requests_per_minute: int = 100
    ):
        super().__init__(app)
        self.enabled = enabled
        self.limiter = get_rate_limiter()
        self.default_rpm = default_requests_per_minute

    async def dispatch(self, request: Request, call_next):
        if not self.enabled:
            return await call_next(request)
        
        if request.method == "OPTIONS":
            return await call_next(request)
        
        if request.url.path.startswith("/health"):
            return await call_next(request)
        
        if request.url.path.startswith("/docs") or request.url.path.startswith("/openapi"):
            return await call_next(request)
        
        ip = self._get_client_ip(request)
        
        allowed, info = self.limiter.check_ip_rate_limit(ip, request.url.path)
        
        if not allowed:
            logger.warning(f"IP rate limit exceeded: {ip} - {info}")
            return JSONResponse(
                status_code=429,
                content={
                    "detail": info.get("reason", "请求频率超限"),
                    "retry_after": info.get("retry_after", 60),
                    "limit": info.get("limit", 100)
                },
                headers={
                    "Retry-After": str(info.get("retry_after", 60)),
                    "X-RateLimit-Limit": str(info.get("limit", 100)),
                    "X-RateLimit-Remaining": "0"
                }
            )
        
        user_id = self._get_user_id(request)
        if user_id:
            allowed, info = self.limiter.check_user_rate_limit(
                user_id, 
                request.url.path
            )
            
            if not allowed:
                logger.warning(f"User rate limit exceeded: {user_id} - {info}")
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": info.get("reason", "请求频率超限"),
                        "retry_after": info.get("retry_after", 60),
                        "limit": info.get("limit", 100)
                    },
                    headers={
                        "Retry-After": str(info.get("retry_after", 60)),
                        "X-RateLimit-Limit": str(info.get("limit", 100)),
                        "X-RateLimit-Remaining": "0"
                    }
                )
        
        response = await call_next(request)
        
        response.headers["X-RateLimit-Limit"] = str(info.get("limit", self.default_rpm))
        response.headers["X-RateLimit-Remaining"] = str(info.get("remaining", 0))
        
        return response

    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP"""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        if request.client:
            return request.client.host
        
        return "unknown"

    def _get_user_id(self, request: Request) -> Optional[str]:
        """获取用户ID"""
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return f"user:{auth_header[7:20]}"
        return None


def setup_rate_limit(app, enabled: bool = True, default_rpm: int = 100):
    """设置限流中间件"""
    app.add_middleware(
        RateLimitMiddleware,
        enabled=enabled,
        default_requests_per_minute=default_rpm
    )
