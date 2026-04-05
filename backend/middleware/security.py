"""
安全中间件
提供速率限制、安全头等功能
"""
import os
import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Callable, Optional
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from ..logger import get_logger

logger = get_logger("security")


class RateLimiter:
    """速率限制器"""
    
    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        block_duration_minutes: int = 5,
    ):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.block_duration = timedelta(minutes=block_duration_minutes)
        
        self._minute_counts: dict[str, list[float]] = defaultdict(list)
        self._hour_counts: dict[str, list[float]] = defaultdict(list)
        self._blocked: dict[str, float] = {}
    
    def _cleanup_old_requests(self, client_id: str):
        """清理过期请求记录"""
        now = time.time()
        
        self._minute_counts[client_id] = [
            t for t in self._minute_counts[client_id]
            if now - t < 60
        ]
        
        self._hour_counts[client_id] = [
            t for t in self._hour_counts[client_id]
            if now - t < 3600
        ]
        
        self._blocked = {
            k: v for k, v in self._blocked.items()
            if now - v < self.block_duration.total_seconds()
        }
    
    def is_allowed(self, client_id: str) -> tuple[bool, Optional[str]]:
        """检查是否允许请求"""
        self._cleanup_old_requests(client_id)
        
        if client_id in self._blocked:
            return False, "Client is temporarily blocked"
        
        minute_count = len(self._minute_counts[client_id])
        hour_count = len(self._hour_counts[client_id])
        
        if minute_count >= self.requests_per_minute:
            self._blocked[client_id] = time.time()
            return False, f"Rate limit exceeded: {minute_count} requests per minute"
        
        if hour_count >= self.requests_per_hour:
            self._blocked[client_id] = time.time()
            return False, f"Rate limit exceeded: {hour_count} requests per hour"
        
        return True, None
    
    def record_request(self, client_id: str):
        """记录请求"""
        now = time.time()
        self._minute_counts[client_id].append(now)
        self._hour_counts[client_id].append(now)
    
    def get_stats(self, client_id: str) -> dict:
        """获取统计信息"""
        self._cleanup_old_requests(client_id)
        return {
            "minute_count": len(self._minute_counts[client_id]),
            "hour_count": len(self._hour_counts[client_id]),
            "is_blocked": client_id in self._blocked,
        }


class SecurityMiddleware(BaseHTTPMiddleware):
    """安全中间件"""
    
    def __init__(self, app, **kwargs):
        super().__init__(app)
        self.rate_limiter = RateLimiter(
            requests_per_minute=int(os.getenv("RATE_LIMIT_PER_MINUTE", "60")),
            requests_per_hour=int(os.getenv("RATE_LIMIT_PER_HOUR", "1000")),
        )
        
        self.strict_endpoints = [
            "/api/auth/login",
            "/api/auth/register",
            "/api/auth/forgot-password",
        ]
        
        self.strict_rate_limiter = RateLimiter(
            requests_per_minute=5,
            requests_per_hour=20,
            block_duration_minutes=15,
        )
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = self._get_client_ip(request)
        
        if request.url.path in self.strict_endpoints:
            allowed, reason = self.strict_rate_limiter.is_allowed(client_ip)
            if not allowed:
                logger.warning(f"Strict rate limit exceeded for {client_ip}: {reason}")
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many requests. Please try again later."},
                    headers={"Retry-After": "300"}
                )
            self.strict_rate_limiter.record_request(client_ip)
        
        allowed, reason = self.rate_limiter.is_allowed(client_ip)
        if not allowed:
            logger.warning(f"Rate limit exceeded for {client_ip}: {reason}")
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
                headers={"Retry-After": "60"}
            )
        
        self.rate_limiter.record_request(client_ip)
        
        response = await call_next(request)
        
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        if not request.url.path.startswith("/api/"):
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self' wss: https:; "
                "frame-ancestors 'self';"
            )
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP"""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"


class InputSanitizer:
    """输入清理器"""
    
    SQL_KEYWORDS = [
        "SELECT", "INSERT", "UPDATE", "DELETE", "DROP", "UNION",
        "OR", "AND", "WHERE", "FROM", "INTO", "VALUES", "SET",
    ]
    
    XSS_PATTERNS = [
        "<script", "</script>", "javascript:", "onerror=", "onload=",
        "eval(", "document.cookie", "innerHTML",
    ]
    
    @classmethod
    def sanitize_string(cls, value: str) -> str:
        """清理字符串"""
        if not isinstance(value, str):
            return value
        
        sanitized = value
        
        for pattern in cls.XSS_PATTERNS:
            sanitized = sanitized.replace(pattern.lower(), "")
            sanitized = sanitized.replace(pattern.upper(), "")
        
        return sanitized.strip()
    
    @classmethod
    def check_sql_injection(cls, value: str) -> bool:
        """检查SQL注入"""
        if not isinstance(value, str):
            return False
        
        upper_value = value.upper()
        
        for keyword in cls.SQL_KEYWORDS:
            if keyword in upper_value and ("'" in value or '"' in value or ";" in value):
                return True
        
        return False
    
    @classmethod
    def sanitize_dict(cls, data: dict) -> dict:
        """清理字典数据"""
        sanitized = {}
        for key, value in data.items():
            if isinstance(value, str):
                sanitized[key] = cls.sanitize_string(value)
            elif isinstance(value, dict):
                sanitized[key] = cls.sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    cls.sanitize_string(item) if isinstance(item, str) else item
                    for item in value
                ]
            else:
                sanitized[key] = value
        return sanitized


def validate_password_strength(password: str) -> tuple[bool, list[str]]:
    """验证密码强度"""
    errors = []
    
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    
    if not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")
    
    if not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")
    
    if not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one digit")
    
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        errors.append("Password must contain at least one special character")
    
    return len(errors) == 0, errors


def generate_csrf_token() -> str:
    """生成CSRF令牌"""
    import secrets
    return secrets.token_urlsafe(32)


def validate_csrf_token(token: str, expected: str) -> bool:
    """验证CSRF令牌"""
    import secrets
    return secrets.compare_digest(token, expected)
