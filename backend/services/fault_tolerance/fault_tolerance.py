"""
容错保障模块
异常处理、健康检查、优雅停机、故障恢复
"""
import asyncio
import signal
import sys
import time
import logging
import traceback
from typing import Any, Optional, Callable, Dict, List, Type
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from functools import wraps
from abc import ABC, abstractmethod
import os

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    BUSINESS = "business"
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    NOT_FOUND = "not_found"
    RATE_LIMIT = "rate_limit"
    EXTERNAL = "external"
    DATABASE = "database"
    CACHE = "cache"
    INTERNAL = "internal"
    TIMEOUT = "timeout"


@dataclass
class ErrorContext:
    error_id: str
    timestamp: datetime
    error_type: str
    message: str
    severity: ErrorSeverity
    category: ErrorCategory
    stacktrace: Optional[str] = None
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    additional_info: Dict[str, Any] = field(default_factory=dict)


class AppException(Exception):
    """应用异常基类"""
    
    def __init__(
        self,
        message: str,
        error_code: str = "UNKNOWN_ERROR",
        status_code: int = 500,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        category: ErrorCategory = ErrorCategory.INTERNAL,
        details: Dict[str, Any] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.severity = severity
        self.category = category
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": True,
            "error_code": self.error_code,
            "message": self.message,
            "severity": self.severity.value,
            "category": self.category.value,
            "details": self.details
        }


class BusinessError(AppException):
    """业务异常"""
    
    def __init__(self, message: str, error_code: str = "BUSINESS_ERROR", details: Dict[str, Any] = None):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=400,
            severity=ErrorSeverity.LOW,
            category=ErrorCategory.BUSINESS,
            details=details
        )


class ValidationError(AppException):
    """验证异常"""
    
    def __init__(self, message: str, field: str = None, details: Dict[str, Any] = None):
        details = details or {}
        if field:
            details["field"] = field
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=422,
            severity=ErrorSeverity.LOW,
            category=ErrorCategory.VALIDATION,
            details=details
        )


class AuthenticationError(AppException):
    """认证异常"""
    
    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            status_code=401,
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.AUTHENTICATION
        )


class AuthorizationError(AppException):
    """授权异常"""
    
    def __init__(self, message: str = "Permission denied"):
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            status_code=403,
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.AUTHORIZATION
        )


class NotFoundError(AppException):
    """资源不存在异常"""
    
    def __init__(self, resource: str = "Resource"):
        super().__init__(
            message=f"{resource} not found",
            error_code="NOT_FOUND",
            status_code=404,
            severity=ErrorSeverity.LOW,
            category=ErrorCategory.NOT_FOUND
        )


class RateLimitError(AppException):
    """限流异常"""
    
    def __init__(self, retry_after: int = 60):
        super().__init__(
            message="Rate limit exceeded",
            error_code="RATE_LIMIT_ERROR",
            status_code=429,
            severity=ErrorSeverity.LOW,
            category=ErrorCategory.RATE_LIMIT,
            details={"retry_after": retry_after}
        )


class ExternalServiceError(AppException):
    """外部服务异常"""
    
    def __init__(self, service: str, message: str = None):
        super().__init__(
            message=message or f"External service '{service}' error",
            error_code="EXTERNAL_SERVICE_ERROR",
            status_code=502,
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.EXTERNAL,
            details={"service": service}
        )


class DatabaseError(AppException):
    """数据库异常"""
    
    def __init__(self, message: str = "Database error"):
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            status_code=500,
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.DATABASE
        )


class TimeoutError(AppException):
    """超时异常"""
    
    def __init__(self, operation: str = "Operation", timeout: float = None):
        details = {}
        if timeout:
            details["timeout_seconds"] = timeout
        super().__init__(
            message=f"{operation} timed out",
            error_code="TIMEOUT_ERROR",
            status_code=504,
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.TIMEOUT,
            details=details
        )


class ExceptionHandler:
    """异常处理器"""
    
    def __init__(self):
        self._handlers: Dict[Type[Exception], Callable] = {}
        self._error_counts: Dict[str, int] = {}
        self._error_history: List[ErrorContext] = []
        self._max_history = 1000
    
    def register_handler(self, exception_type: Type[Exception], handler: Callable):
        self._handlers[exception_type] = handler
    
    async def handle(self, exc: Exception, request: Request = None) -> JSONResponse:
        error_id = self._generate_error_id()
        
        if isinstance(exc, AppException):
            app_exc = exc
        else:
            app_exc = self._convert_exception(exc)
        
        self._record_error(error_id, app_exc, request)
        
        response_data = app_exc.to_dict()
        response_data["error_id"] = error_id
        
        if app_exc.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            logger.error(
                f"Critical error [{error_id}]: {app_exc.message}",
                extra={
                    "error_id": error_id,
                    "error_code": app_exc.error_code,
                    "severity": app_exc.severity.value,
                    "stacktrace": traceback.format_exc()
                }
            )
        else:
            logger.warning(
                f"Error [{error_id}]: {app_exc.message}",
                extra={"error_id": error_id, "error_code": app_exc.error_code}
            )
        
        return JSONResponse(
            status_code=app_exc.status_code,
            content=response_data
        )
    
    def _convert_exception(self, exc: Exception) -> AppException:
        exception_map = {
            ValueError: ValidationError,
            KeyError: NotFoundError,
            asyncio.TimeoutError: TimeoutError,
        }
        
        app_exc_class = exception_map.get(type(exc), AppException)
        
        if app_exc_class == AppException:
            return AppException(
                message=str(exc),
                error_code=type(exc).__name__.upper(),
                severity=ErrorSeverity.MEDIUM,
                category=ErrorCategory.INTERNAL
            )
        
        return app_exc_class(str(exc))
    
    def _generate_error_id(self) -> str:
        import uuid
        return str(uuid.uuid4())[:8]
    
    def _record_error(self, error_id: str, exc: AppException, request: Request):
        context = ErrorContext(
            error_id=error_id,
            timestamp=datetime.now(),
            error_type=type(exc).__name__,
            message=exc.message,
            severity=exc.severity,
            category=exc.category,
            stacktrace=traceback.format_exc() if exc.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL] else None,
            endpoint=str(request.url.path) if request else None,
            method=request.method if request else None
        )
        
        self._error_history.append(context)
        if len(self._error_history) > self._max_history:
            self._error_history.pop(0)
        
        error_key = exc.error_code
        self._error_counts[error_key] = self._error_counts.get(error_key, 0) + 1
    
    def get_error_stats(self) -> Dict[str, Any]:
        return {
            "total_errors": len(self._error_history),
            "error_counts": self._error_counts.copy(),
            "recent_errors": [
                {
                    "error_id": e.error_id,
                    "timestamp": e.timestamp.isoformat(),
                    "error_type": e.error_type,
                    "message": e.message,
                    "severity": e.severity.value
                }
                for e in self._error_history[-20:]
            ]
        }


exception_handler = ExceptionHandler()


class HealthChecker:
    """健康检查器"""
    
    def __init__(self):
        self._checks: Dict[str, Callable] = {}
        self._last_results: Dict[str, Dict[str, Any]] = {}
    
    def register_check(self, name: str, check_func: Callable):
        self._checks[name] = check_func
    
    async def run_checks(self) -> Dict[str, Any]:
        results = {}
        overall_healthy = True
        
        for name, check_func in self._checks.items():
            try:
                start_time = time.time()
                
                if asyncio.iscoroutinefunction(check_func):
                    result = await check_func()
                else:
                    result = check_func()
                
                duration = (time.time() - start_time) * 1000
                
                if isinstance(result, bool):
                    healthy = result
                    details = {}
                elif isinstance(result, dict):
                    healthy = result.get("healthy", True)
                    details = result
                else:
                    healthy = True
                    details = {"result": str(result)}
                
                results[name] = {
                    "healthy": healthy,
                    "duration_ms": round(duration, 2),
                    "timestamp": datetime.now().isoformat(),
                    **details
                }
                
                if not healthy:
                    overall_healthy = False
                    
            except Exception as e:
                results[name] = {
                    "healthy": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                overall_healthy = False
        
        self._last_results = results
        
        return {
            "healthy": overall_healthy,
            "timestamp": datetime.now().isoformat(),
            "checks": results
        }
    
    def get_last_results(self) -> Dict[str, Any]:
        return self._last_results


health_checker = HealthChecker()


def register_health_checks():
    """注册默认健康检查"""
    
    async def check_database():
        try:
            from ..database.high_performance_db import get_db_service
            db = await get_db_service()
            if db._initialized:
                return {"healthy": True, "message": "Database connected"}
            return {"healthy": False, "message": "Database not initialized"}
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    async def check_cache():
        try:
            from ..cache.multi_level_cache import get_cache
            cache = await get_cache()
            if cache._initialized:
                return {"healthy": True, "message": "Cache connected"}
            return {"healthy": False, "message": "Cache not initialized"}
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    async def check_task_queue():
        try:
            from ..queue.async_task_queue import get_task_queue
            queue = await get_task_queue()
            if queue._initialized:
                return {"healthy": True, "message": "Task queue ready"}
            return {"healthy": False, "message": "Task queue not initialized"}
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    async def check_memory():
        try:
            import psutil
            memory = psutil.virtual_memory()
            if memory.percent < 90:
                return {
                    "healthy": True,
                    "percent_used": memory.percent,
                    "available_mb": memory.available // (1024 * 1024)
                }
            return {
                "healthy": False,
                "percent_used": memory.percent,
                "message": "Memory usage too high"
            }
        except ImportError:
            return {"healthy": True, "message": "psutil not available"}
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    async def check_disk():
        try:
            import psutil
            disk = psutil.disk_usage('/')
            if disk.percent < 90:
                return {
                    "healthy": True,
                    "percent_used": disk.percent,
                    "free_gb": disk.free // (1024 * 1024 * 1024)
                }
            return {
                "healthy": False,
                "percent_used": disk.percent,
                "message": "Disk usage too high"
            }
        except ImportError:
            return {"healthy": True, "message": "psutil not available"}
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    health_checker.register_check("database", check_database)
    health_checker.register_check("cache", check_cache)
    health_checker.register_check("task_queue", check_task_queue)
    health_checker.register_check("memory", check_memory)
    health_checker.register_check("disk", check_disk)


class GracefulShutdown:
    """优雅停机管理器"""
    
    _instance: Optional['GracefulShutdown'] = None
    
    def __init__(self):
        self._shutdown_handlers: List[Callable] = []
        self._is_shutting_down = False
        self._shutdown_timeout = 30.0
        self._active_requests = 0
        self._lock = asyncio.Lock()
    
    @classmethod
    def get_instance(cls) -> 'GracefulShutdown':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def register_handler(self, handler: Callable):
        self._shutdown_handlers.append(handler)
    
    def setup_signal_handlers(self):
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        logger.info("Signal handlers registered for graceful shutdown")
    
    def _signal_handler(self, signum, frame):
        logger.info(f"Received signal {signum}, initiating graceful shutdown")
        asyncio.create_task(self.shutdown())
    
    async def shutdown(self):
        if self._is_shutting_down:
            return
        
        self._is_shutting_down = True
        logger.info("Starting graceful shutdown...")
        
        start_time = time.time()
        
        while self._active_requests > 0:
            elapsed = time.time() - start_time
            if elapsed > self._shutdown_timeout:
                logger.warning(f"Shutdown timeout reached, {self._active_requests} requests still active")
                break
            
            logger.info(f"Waiting for {self._active_requests} active requests to complete...")
            await asyncio.sleep(0.5)
        
        for handler in self._shutdown_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler()
                else:
                    handler()
            except Exception as e:
                logger.error(f"Shutdown handler error: {e}")
        
        logger.info("Graceful shutdown completed")
    
    async def increment_request(self):
        async with self._lock:
            self._active_requests += 1
    
    async def decrement_request(self):
        async with self._lock:
            self._active_requests -= 1
    
    @property
    def is_shutting_down(self) -> bool:
        return self._is_shutting_down


class ExceptionMiddleware(BaseHTTPMiddleware):
    """异常处理中间件"""
    
    def __init__(self, app):
        super().__init__(app)
        self._shutdown = GracefulShutdown.get_instance()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if self._shutdown.is_shutting_down:
            return JSONResponse(
                status_code=503,
                content={
                    "error": True,
                    "error_code": "SERVICE_UNAVAILABLE",
                    "message": "Service is shutting down"
                }
            )
        
        await self._shutdown.increment_request()
        
        try:
            response = await call_next(request)
            return response
            
        except AppException as exc:
            return await exception_handler.handle(exc, request)
            
        except Exception as exc:
            return await exception_handler.handle(exc, request)
            
        finally:
            await self._shutdown.decrement_request()


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    exponential_backoff: bool = True,
    exceptions: tuple = (Exception,)
):
    """重试装饰器"""
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_attempts - 1:
                        wait_time = delay * (2 ** attempt) if exponential_backoff else delay
                        logger.warning(
                            f"Retry {attempt + 1}/{max_attempts} for {func.__name__}: {e}"
                        )
                        await asyncio.sleep(wait_time)
            
            raise last_exception
        
        return async_wrapper
    return decorator


def fallback(fallback_func: Callable):
    """降级装饰器"""
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.warning(f"Function {func.__name__} failed, using fallback: {e}")
                
                if asyncio.iscoroutinefunction(fallback_func):
                    return await fallback_func(*args, **kwargs)
                return fallback_func(*args, **kwargs)
        
        return async_wrapper
    return decorator


async def init_fault_tolerance() -> bool:
    """初始化容错系统"""
    register_health_checks()
    
    shutdown = GracefulShutdown.get_instance()
    shutdown.setup_signal_handlers()
    
    logger.info("Fault tolerance system initialized")
    return True


async def get_health_status() -> Dict[str, Any]:
    """获取健康状态"""
    return await health_checker.run_checks()
