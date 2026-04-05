"""
全局异常处理中间件
提供统一的错误响应格式
"""
import uuid
import traceback
from typing import Callable, Dict, Any, Optional, List
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging

from .logger import get_logger, RequestLogger

logger = get_logger("exception")


class ErrorCode:
    AUTH_FAILED = "AUTH_FAILED"
    AUTH_TOKEN_EXPIRED = "AUTH_TOKEN_EXPIRED"
    AUTH_INVALID_TOKEN = "AUTH_INVALID_TOKEN"
    NOT_FOUND = "NOT_FOUND"
    TASK_NOT_FOUND = "TASK_NOT_FOUND"
    REPORT_NOT_FOUND = "REPORT_NOT_FOUND"
    USER_NOT_FOUND = "USER_NOT_FOUND"
    TEAM_NOT_FOUND = "TEAM_NOT_FOUND"
    BAD_REQUEST = "BAD_REQUEST"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    CONFLICT = "CONFLICT"
    DUPLICATE_ENTRY = "DUPLICATE_ENTRY"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    AI_SERVICE_ERROR = "AI_SERVICE_ERROR"
    FILE_UPLOAD_ERROR = "FILE_UPLOAD_ERROR"
    EXPORT_ERROR = "EXPORT_ERROR"


ERROR_MESSAGES = {
    ErrorCode.AUTH_FAILED: "认证失败，请检查用户名或密码",
    ErrorCode.AUTH_TOKEN_EXPIRED: "登录已过期，请重新登录",
    ErrorCode.AUTH_INVALID_TOKEN: "无效的认证信息",
    ErrorCode.NOT_FOUND: "请求的资源不存在",
    ErrorCode.TASK_NOT_FOUND: "任务不存在或已被删除",
    ErrorCode.REPORT_NOT_FOUND: "报告不存在或已被删除",
    ErrorCode.USER_NOT_FOUND: "用户不存在",
    ErrorCode.TEAM_NOT_FOUND: "团队不存在或已被删除",
    ErrorCode.BAD_REQUEST: "请求参数错误",
    ErrorCode.VALIDATION_ERROR: "数据验证失败",
    ErrorCode.UNAUTHORIZED: "未授权访问，请先登录",
    ErrorCode.FORBIDDEN: "没有权限执行此操作",
    ErrorCode.CONFLICT: "资源冲突",
    ErrorCode.DUPLICATE_ENTRY: "该数据已存在",
    ErrorCode.RATE_LIMIT_EXCEEDED: "请求过于频繁，请稍后再试",
    ErrorCode.SERVICE_UNAVAILABLE: "服务暂时不可用",
    ErrorCode.INTERNAL_ERROR: "服务器内部错误，请稍后重试",
    ErrorCode.AI_SERVICE_ERROR: "AI服务暂时不可用，请稍后重试",
    ErrorCode.FILE_UPLOAD_ERROR: "文件上传失败",
    ErrorCode.EXPORT_ERROR: "数据导出失败",
}


class ErrorDetail:
    def __init__(
        self,
        field: str = None,
        message: str = None,
        value: Any = None
    ):
        self.field = field
        self.message = message
        self.value = value
    
    def to_dict(self) -> Dict[str, Any]:
        result = {}
        if self.field:
            result["field"] = self.field
        if self.message:
            result["message"] = self.message
        if self.value is not None:
            result["value"] = self.value
        return result


class ErrorResponse:
    def __init__(
        self,
        code: str,
        message: str = None,
        details: List[ErrorDetail] = None,
        request_id: str = None
    ):
        self.code = code
        self.message = message or ERROR_MESSAGES.get(code, "未知错误")
        self.details = details or []
        self.request_id = request_id
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "code": self.code,
            "message": self.message,
        }
        if self.details:
            result["details"] = [d.to_dict() for d in self.details]
        if self.request_id:
            result["request_id"] = self.request_id
        return result


class AppException(Exception):
    """应用自定义异常基类"""
    
    def __init__(
        self,
        message: str = None,
        code: str = ErrorCode.INTERNAL_ERROR,
        status_code: int = 500,
        details: List[ErrorDetail] = None
    ):
        self.message = message or ERROR_MESSAGES.get(code, "未知错误")
        self.code = code
        self.status_code = status_code
        self.details = details or []
        super().__init__(self.message)


class NotFoundException(AppException):
    """资源未找到异常"""
    
    def __init__(self, message: str = None, code: str = ErrorCode.NOT_FOUND, details: List[ErrorDetail] = None):
        super().__init__(
            message=message,
            code=code,
            status_code=404,
            details=details
        )


class BadRequestException(AppException):
    """错误请求异常"""
    
    def __init__(self, message: str = None, details: List[ErrorDetail] = None):
        super().__init__(
            message=message,
            code=ErrorCode.BAD_REQUEST,
            status_code=400,
            details=details
        )


class UnauthorizedException(AppException):
    """未授权异常"""
    
    def __init__(self, message: str = None, code: str = ErrorCode.UNAUTHORIZED, details: List[ErrorDetail] = None):
        super().__init__(
            message=message,
            code=code,
            status_code=401,
            details=details
        )


class ForbiddenException(AppException):
    """禁止访问异常"""
    
    def __init__(self, message: str = None, details: List[ErrorDetail] = None):
        super().__init__(
            message=message,
            code=ErrorCode.FORBIDDEN,
            status_code=403,
            details=details
        )


class ConflictException(AppException):
    """冲突异常"""
    
    def __init__(self, message: str = None, code: str = ErrorCode.CONFLICT, details: List[ErrorDetail] = None):
        super().__init__(
            message=message,
            code=code,
            status_code=409,
            details=details
        )


class RateLimitException(AppException):
    """速率限制异常"""
    
    def __init__(self, message: str = None, details: List[ErrorDetail] = None):
        super().__init__(
            message=message,
            code=ErrorCode.RATE_LIMIT_EXCEEDED,
            status_code=429,
            details=details
        )


class ServiceException(AppException):
    """服务异常"""
    
    def __init__(self, message: str = None, code: str = ErrorCode.SERVICE_UNAVAILABLE, details: List[ErrorDetail] = None):
        super().__init__(
            message=message,
            code=code,
            status_code=503,
            details=details
        )


class ExceptionMiddleware(BaseHTTPMiddleware):
    """全局异常处理中间件"""
    
    def __init__(self, app: ASGIApp, debug: bool = False):
        super().__init__(app)
        self.debug = debug
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id
        
        try:
            response = await call_next(request)
            return response
            
        except AppException as e:
            return self._handle_app_exception(request, e, request_id)
            
        except HTTPException as e:
            return self._handle_http_exception(request, e, request_id)
            
        except RequestValidationError as e:
            return self._handle_validation_error(request, e, request_id)
            
        except Exception as e:
            return self._handle_unexpected_error(request, e, request_id)
    
    def _handle_app_exception(
        self, 
        request: Request, 
        exc: AppException, 
        request_id: str
    ) -> JSONResponse:
        """处理应用自定义异常"""
        user_id = getattr(request.state, "user_id", None)
        
        logger.warning(
            f"AppException: {exc.code} - {exc.message}",
            extra={
                "request_id": request_id,
                "user_id": user_id,
                "path": request.url.path,
                "method": request.method,
                "status_code": exc.status_code,
                "details": [d.to_dict() for d in exc.details] if exc.details else []
            }
        )
        
        response = ErrorResponse(
            code=exc.code,
            message=exc.message,
            details=exc.details,
            request_id=request_id
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=response.to_dict()
        )
    
    def _handle_http_exception(
        self, 
        request: Request, 
        exc: HTTPException, 
        request_id: str
    ) -> JSONResponse:
        """处理 HTTP 异常"""
        user_id = getattr(request.state, "user_id", None)
        
        logger.warning(
            f"HTTPException: {exc.status_code} - {exc.detail}",
            extra={
                "request_id": request_id,
                "user_id": user_id,
                "path": request.url.path,
                "method": request.method
            }
        )
        
        code_map = {
            401: ErrorCode.UNAUTHORIZED,
            403: ErrorCode.FORBIDDEN,
            404: ErrorCode.NOT_FOUND,
            405: ErrorCode.BAD_REQUEST,
            409: ErrorCode.CONFLICT,
            429: ErrorCode.RATE_LIMIT_EXCEEDED,
        }
        
        response = ErrorResponse(
            code=code_map.get(exc.status_code, f"HTTP_{exc.status_code}"),
            message=str(exc.detail),
            request_id=request_id
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=response.to_dict()
        )
    
    def _handle_validation_error(
        self, 
        request: Request, 
        exc: RequestValidationError, 
        request_id: str
    ) -> JSONResponse:
        """处理请求验证错误"""
        user_id = getattr(request.state, "user_id", None)
        details = []
        
        for error in exc.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            details.append(ErrorDetail(
                field=field,
                message=error["msg"],
                value=str(error.get("input", ""))[:100]
            ))
        
        logger.warning(
            f"ValidationError: {len(details)} errors",
            extra={
                "request_id": request_id,
                "user_id": user_id,
                "path": request.url.path,
                "method": request.method,
                "errors": [d.to_dict() for d in details]
            }
        )
        
        response = ErrorResponse(
            code=ErrorCode.VALIDATION_ERROR,
            details=details,
            request_id=request_id
        )
        
        return JSONResponse(
            status_code=422,
            content=response.to_dict()
        )
    
    def _handle_unexpected_error(
        self, 
        request: Request, 
        exc: Exception, 
        request_id: str
    ) -> JSONResponse:
        """处理未预期的错误"""
        user_id = getattr(request.state, "user_id", None)
        
        logger.error(
            f"UnexpectedError: {type(exc).__name__} - {str(exc)}",
            extra={
                "request_id": request_id,
                "user_id": user_id,
                "path": request.url.path,
                "method": request.method,
                "traceback": traceback.format_exc()
            }
        )
        
        if self.debug:
            message = f"{type(exc).__name__}: {str(exc)}"
            details = [ErrorDetail(
                field="traceback",
                message=traceback.format_exc()
            )]
        else:
            message = ERROR_MESSAGES[ErrorCode.INTERNAL_ERROR]
            details = []
        
        response = ErrorResponse(
            code=ErrorCode.INTERNAL_ERROR,
            message=message,
            details=details,
            request_id=request_id
        )
        
        return JSONResponse(
            status_code=500,
            content=response.to_dict()
        )


def setup_exception_handlers(app):
    """配置 FastAPI 异常处理器"""
    
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.message,
                "code": exc.code
            }
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.detail,
                "code": f"HTTP_{exc.status_code}"
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        errors = []
        for error in exc.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            errors.append({
                "field": field,
                "message": error["msg"]
            })
        
        return JSONResponse(
            status_code=422,
            content={
                "detail": "请求参数验证失败",
                "code": "VALIDATION_ERROR",
                "errors": errors
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {type(exc).__name__}: {str(exc)}")
        
        return JSONResponse(
            status_code=500,
            content={
                "detail": "服务器内部错误",
                "code": "INTERNAL_ERROR"
            }
        )
