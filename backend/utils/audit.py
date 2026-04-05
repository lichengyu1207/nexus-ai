"""
审计日志上下文管理
用于在请求处理过程中传递审计数据
"""
import contextvars
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime

_audit_context: contextvars.ContextVar[Optional['AuditContext']] = contextvars.ContextVar(
    'audit_context', default=None
)


@dataclass
class AuditContext:
    request_id: str
    user_id: Optional[str] = None
    username: Optional[str] = None
    user_role: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    action_type: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    old_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None
    status: str = 'success'
    error_message: Optional[str] = None
    extra_data: Dict[str, Any] = field(default_factory=dict)
    skip_logging: bool = False
    logs: List[Dict[str, Any]] = field(default_factory=list)


def get_audit_context() -> Optional[AuditContext]:
    return _audit_context.get()


def set_audit_context(ctx: AuditContext) -> contextvars.Token:
    return _audit_context.set(ctx)


def reset_audit_context(token: contextvars.Token) -> None:
    _audit_context.reset(token)


def init_audit_context(request_id: str) -> AuditContext:
    ctx = AuditContext(request_id=request_id)
    _audit_context.set(ctx)
    return ctx


def set_audit_user(
    user_id: Optional[str] = None,
    username: Optional[str] = None,
    user_role: Optional[str] = None
) -> None:
    ctx = get_audit_context()
    if ctx:
        ctx.user_id = user_id
        ctx.username = username
        ctx.user_role = user_role


def set_audit_request_info(
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> None:
    ctx = get_audit_context()
    if ctx:
        ctx.ip_address = ip_address
        ctx.user_agent = user_agent


def set_audit_action(
    action_type: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None
) -> None:
    ctx = get_audit_context()
    if ctx:
        ctx.action_type = action_type
        ctx.resource_type = resource_type
        ctx.resource_id = resource_id


def set_audit_old_value(value: Dict[str, Any]) -> None:
    ctx = get_audit_context()
    if ctx:
        ctx.old_value = value


def set_audit_new_value(value: Dict[str, Any]) -> None:
    ctx = get_audit_context()
    if ctx:
        ctx.new_value = value


def set_audit_status(status: str, error_message: Optional[str] = None) -> None:
    ctx = get_audit_context()
    if ctx:
        ctx.status = status
        ctx.error_message = error_message


def set_audit_error(error_message: str) -> None:
    ctx = get_audit_context()
    if ctx:
        ctx.status = 'failure'
        ctx.error_message = error_message


def skip_audit_logging() -> None:
    ctx = get_audit_context()
    if ctx:
        ctx.skip_logging = True


def add_audit_extra(key: str, value: Any) -> None:
    ctx = get_audit_context()
    if ctx:
        ctx.extra_data[key] = value


def add_audit_log(log_entry: Dict[str, Any]) -> None:
    ctx = get_audit_context()
    if ctx:
        ctx.logs.append(log_entry)


class AuditContextManager:
    def __init__(self, request_id: str):
        self.request_id = request_id
        self.token = None
        self.ctx = None

    def __enter__(self) -> AuditContext:
        self.ctx = AuditContext(request_id=self.request_id)
        self.token = _audit_context.set(self.ctx)
        return self.ctx

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None and self.ctx:
            self.ctx.status = 'failure'
            self.ctx.error_message = str(exc_val)
        
        if self.token is not None:
            _audit_context.reset(self.token)


def create_audit_log_from_context() -> Optional[Dict[str, Any]]:
    ctx = get_audit_context()
    if not ctx or ctx.skip_logging or not ctx.action_type:
        return None
    
    return {
        'request_id': ctx.request_id,
        'user_id': ctx.user_id,
        'username': ctx.username,
        'user_role': ctx.user_role,
        'ip_address': ctx.ip_address,
        'user_agent': ctx.user_agent,
        'action_type': ctx.action_type,
        'resource_type': ctx.resource_type,
        'resource_id': ctx.resource_id,
        'old_value': ctx.old_value,
        'new_value': ctx.new_value,
        'status': ctx.status,
        'error_message': ctx.error_message,
        'extra_data': ctx.extra_data,
        'timestamp': datetime.utcnow().isoformat(),
    }
