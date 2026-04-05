"""
审计日志中间件
自动捕获API请求并记录审计日志
"""
import uuid
import time
import asyncio
from typing import Callable, Set, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ..utils.audit import (
    init_audit_context,
    set_audit_request_info,
    set_audit_user,
    create_audit_log_from_context,
    skip_audit_logging,
)
from ..services.audit_service import log_audit, ActionType, ResourceType, AuditStatus


SKIP_PATHS: Set[str] = {
    '/api/health',
    '/api/metrics',
    '/api/docs',
    '/api/openapi.json',
    '/api/redoc',
    '/favicon.ico',
    '/robots.txt',
    '/sitemap.xml',
}

SKIP_PREFIXES: Set[str] = {
    '/static/',
    '/assets/',
    '/uploads/',
    '/_next/',
}

SENSITIVE_HEADERS: Set[str] = {
    'authorization',
    'cookie',
    'set-cookie',
    'x-api-key',
    'x-auth-token',
}

HIGH_VALUE_PATHS: Set[str] = {
    '/api/auth/login',
    '/api/auth/logout',
    '/api/auth/register',
    '/api/tasks',
    '/api/reports',
    '/api/admin/',
}

METHOD_ACTION_MAP = {
    'POST': ActionType.API_ACCESS,
    'PUT': ActionType.API_ACCESS,
    'PATCH': ActionType.API_ACCESS,
    'DELETE': ActionType.API_ACCESS,
}


class AuditMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        skip_paths: Optional[Set[str]] = None,
        skip_prefixes: Optional[Set[str]] = None,
        high_value_paths: Optional[Set[str]] = None,
    ):
        super().__init__(app)
        self.skip_paths = skip_paths or SKIP_PATHS
        self.skip_prefixes = skip_prefixes or SKIP_PREFIXES
        self.high_value_paths = high_value_paths or HIGH_VALUE_PATHS

    def _should_skip(self, path: str) -> bool:
        if path in self.skip_paths:
            return True
        for prefix in self.skip_prefixes:
            if path.startswith(prefix):
                return True
        return False

    def _is_high_value(self, path: str) -> bool:
        for hvp in self.high_value_paths:
            if path.startswith(hvp):
                return True
        return False

    def _get_client_ip(self, request: Request) -> str:
        forwarded_for = request.headers.get('x-forwarded-for')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('x-real-ip')
        if real_ip:
            return real_ip
        
        if request.client:
            return request.client.host
        
        return 'unknown'

    def _sanitize_headers(self, headers: dict) -> dict:
        return {
            k: '***REDACTED***' if k.lower() in SENSITIVE_HEADERS else v
            for k, v in headers.items()
        }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path
        
        if self._should_skip(path):
            return await call_next(request)

        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        ctx = init_audit_context(request_id)
        
        ip_address = self._get_client_ip(request)
        user_agent = request.headers.get('user-agent', '')
        set_audit_request_info(ip_address, user_agent)
        
        if 'authorization' in request.headers:
            try:
                from auth import decode_token
                token = request.headers['authorization'].replace('Bearer ', '')
                payload = decode_token(token)
                if payload:
                    set_audit_user(
                        user_id=payload.get('sub'),
                        username=payload.get('username'),
                        user_role=payload.get('role')
                    )
            except Exception:
                pass

        if request.method in METHOD_ACTION_MAP and self._is_high_value(path):
            ctx.action_type = METHOD_ACTION_MAP[request.method].value
            ctx.resource_type = ResourceType.SYSTEM.value

        response = None
        error_occurred = False
        error_message = None

        try:
            response = await call_next(request)
        except Exception as e:
            error_occurred = True
            error_message = str(e)
            raise
        finally:
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000

            if not ctx.skip_logging and ctx.action_type:
                ctx.status = 'failure' if error_occurred else 'success'
                ctx.error_message = error_message

                asyncio.create_task(log_audit(
                    action_type=ActionType(ctx.action_type),
                    user_id=ctx.user_id,
                    username=ctx.username,
                    user_role=ctx.user_role,
                    ip_address=ctx.ip_address,
                    user_agent=ctx.user_agent,
                    resource_type=ResourceType(ctx.resource_type) if ctx.resource_type else None,
                    resource_id=ctx.resource_id,
                    old_value=ctx.old_value,
                    new_value=ctx.new_value,
                    status=AuditStatus(ctx.status),
                    error_message=ctx.error_message,
                ))

        response.headers['X-Request-ID'] = request_id
        response.headers['X-Response-Time'] = f'{duration_ms:.2f}ms'

        return response


def audit_decorator(
    action_type: ActionType,
    resource_type: Optional[ResourceType] = None,
    get_resource_id: Optional[Callable] = None,
    get_old_value: Optional[Callable] = None,
    get_new_value: Optional[Callable] = None,
):
    """
    审计日志装饰器
    
    用法:
    @router.delete("/tasks/{task_id}")
    @audit_decorator(
        action_type=ActionType.TASK_DELETE,
        resource_type=ResourceType.TASK,
        get_resource_id=lambda task_id: task_id,
    )
    async def delete_task(task_id: str, user=Depends(get_current_user)):
        ...
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            from utils.audit import (
                set_audit_action,
                set_audit_old_value,
                set_audit_new_value,
                set_audit_status,
                set_audit_error,
            )

            resource_id = None
            if get_resource_id:
                try:
                    resource_id = get_resource_id(*args, **kwargs)
                except Exception:
                    pass

            set_audit_action(
                action_type=action_type.value,
                resource_type=resource_type.value if resource_type else None,
                resource_id=resource_id,
            )

            if get_old_value:
                try:
                    old_value = await get_old_value(*args, **kwargs)
                    set_audit_old_value(old_value)
                except Exception:
                    pass

            try:
                result = await func(*args, **kwargs)

                if get_new_value:
                    try:
                        new_value = await get_new_value(*args, **kwargs, result=result)
                        set_audit_new_value(new_value)
                    except Exception:
                        pass

                set_audit_status('success')
                return result

            except Exception as e:
                set_audit_error(str(e))
                raise

        return wrapper
    return decorator


audit_log = audit_decorator
