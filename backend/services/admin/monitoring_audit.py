# -*- coding: utf-8 -*-
"""
监控与审计模块 - 提示词15-16
操作日志审计、错误监控与告警
"""
import asyncio
import json
import logging
import os
import time
import hashlib
import hmac
import traceback
from typing import Optional, Dict, Any, List, Set, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)


class AuditAction(Enum):
    LOGIN = "login"
    LOGOUT = "logout"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    VIEW = "view"
    EXPORT = "export"
    IMPORT = "import"
    START = "start"
    STOP = "stop"
    RESTART = "restart"
    SUSPEND = "suspend"
    ACTIVATE = "activate"
    RESET_PASSWORD = "reset_password"
    ADJUST_POINTS = "adjust_points"
    CONFIG_CHANGE = "config_change"


class AuditSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AuditLog:
    id: Optional[str] = None
    admin_id: str = ""
    admin_username: str = ""
    action: str = ""
    resource_type: str = ""
    resource_id: str = ""
    old_value: Dict[str, Any] = field(default_factory=dict)
    new_value: Dict[str, Any] = field(default_factory=dict)
    ip_address: str = ""
    user_agent: str = ""
    request_id: str = ""
    severity: str = "medium"
    created_at: datetime = None
    signature: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "admin_id": self.admin_id,
            "admin_username": self.admin_username,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "request_id": self.request_id,
            "severity": self.severity,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "signature": self.signature
        }


@dataclass
class AuditSearchParams:
    page: int = 1
    page_size: int = 50
    admin_id: Optional[str] = None
    action: Optional[str] = None
    resource_type: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    ip_address: Optional[str] = None
    severity: Optional[str] = None


class AuditService:
    """审计服务 - 提示词15"""

    def __init__(self, db_service=None, secret_key: str = None):
        self.db_service = db_service
        self.secret_key = secret_key or os.getenv("AUDIT_SECRET_KEY", "audit-secret-key")
        self._sensitive_fields = {"password", "password_hash", "token", "secret", "api_key"}

    async def log(
        self,
        admin_id: str,
        action: str,
        resource_type: str,
        resource_id: str = "",
        old_value: Dict = None,
        new_value: Dict = None,
        ip_address: str = "",
        user_agent: str = "",
        request_id: str = "",
        severity: str = "medium"
    ) -> str:
        """记录审计日志"""
        old_value = self._sanitize_data(old_value or {})
        new_value = self._sanitize_data(new_value or {})

        created_at = datetime.utcnow()
        
        log_entry = AuditLog(
            admin_id=admin_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            severity=severity,
            created_at=created_at
        )

        log_entry.signature = self._sign_log(log_entry)

        if self.db_service:
            try:
                result = await self.db_service.fetchrow_write("""
                    INSERT INTO admin_audit_logs (
                        admin_id, action, resource_type, resource_id,
                        old_value, new_value, ip_address, user_agent,
                        request_id, severity, created_at, signature
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                    RETURNING id
                """,
                    admin_id, action, resource_type, resource_id,
                    json.dumps(old_value), json.dumps(new_value),
                    ip_address, user_agent, request_id, severity,
                    created_at, log_entry.signature
                )
                log_entry.id = str(result["id"]) if result else None
            except Exception as e:
                logger.error(f"Failed to write audit log: {e}")

        return log_entry.id or ""

    async def get_logs(self, params: AuditSearchParams) -> Dict[str, Any]:
        """获取审计日志"""
        if not self.db_service:
            return {"logs": [], "total": 0, "page": params.page, "page_size": params.page_size}

        conditions = ["1=1"]
        args = []
        arg_idx = 1

        if params.admin_id:
            conditions.append(f"admin_id = ${arg_idx}")
            args.append(params.admin_id)
            arg_idx += 1

        if params.action:
            conditions.append(f"action LIKE ${arg_idx}")
            args.append(f"%{params.action}%")
            arg_idx += 1

        if params.resource_type:
            conditions.append(f"resource_type = ${arg_idx}")
            args.append(params.resource_type)
            arg_idx += 1

        if params.start_date:
            conditions.append(f"created_at >= ${arg_idx}")
            args.append(params.start_date)
            arg_idx += 1

        if params.end_date:
            conditions.append(f"created_at <= ${arg_idx}")
            args.append(params.end_date)
            arg_idx += 1

        if params.ip_address:
            conditions.append(f"ip_address = ${arg_idx}")
            args.append(params.ip_address)
            arg_idx += 1

        if params.severity:
            conditions.append(f"severity = ${arg_idx}")
            args.append(params.severity)
            arg_idx += 1

        where_clause = " AND ".join(conditions)

        count_sql = f"SELECT COUNT(*) FROM admin_audit_logs WHERE {where_clause}"
        total = await self.db_service.fetchval_read(count_sql, *args)

        offset = (params.page - 1) * params.page_size

        list_sql = f"""
            SELECT al.*, au.username as admin_username
            FROM admin_audit_logs al
            LEFT JOIN admin_users au ON al.admin_id = au.id
            WHERE {where_clause}
            ORDER BY al.created_at DESC
            LIMIT {params.page_size} OFFSET {offset}
        """

        logs = await self.db_service.execute_read(list_sql, *args)

        return {
            "logs": [self._format_log(dict(l)) for l in logs] if logs else [],
            "total": total,
            "page": params.page,
            "page_size": params.page_size,
            "total_pages": (total + params.page_size - 1) // params.page_size if total else 0
        }

    async def get_log_detail(self, log_id: str) -> Optional[Dict[str, Any]]:
        """获取审计日志详情"""
        if not self.db_service:
            return None

        log = await self.db_service.fetchrow_read("""
            SELECT al.*, au.username as admin_username
            FROM admin_audit_logs al
            LEFT JOIN admin_users au ON al.admin_id = au.id
            WHERE al.id = $1
        """, log_id)

        if not log:
            return None

        return self._format_log(dict(log))

    async def verify_log_integrity(self, log_id: str) -> bool:
        """验证日志完整性"""
        if not self.db_service:
            return False

        log = await self.db_service.fetchrow_read("""
            SELECT * FROM admin_audit_logs WHERE id = $1
        """, log_id)

        if not log:
            return False

        log_entry = AuditLog(
            admin_id=log["admin_id"],
            action=log["action"],
            resource_type=log["resource_type"],
            resource_id=log["resource_id"],
            old_value=log["old_value"] or {},
            new_value=log["new_value"] or {},
            ip_address=log["ip_address"],
            user_agent=log["user_agent"],
            request_id=log["request_id"],
            severity=log["severity"],
            created_at=log["created_at"]
        )

        expected_signature = self._sign_log(log_entry)
        
        return hmac.compare_digest(expected_signature, log["signature"] or "")

    async def get_statistics(
        self,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> Dict[str, Any]:
        """获取审计统计"""
        start_date = start_date or datetime.utcnow() - timedelta(days=7)
        end_date = end_date or datetime.utcnow()

        if not self.db_service:
            return {}

        summary = await self.db_service.fetchrow_read("""
            SELECT
                COUNT(*) as total_operations,
                COUNT(DISTINCT admin_id) as active_admins,
                COUNT(DISTINCT resource_type) as resource_types,
                COUNT(*) FILTER (WHERE severity = 'critical') as critical_count,
                COUNT(*) FILTER (WHERE severity = 'high') as high_count
            FROM admin_audit_logs
            WHERE created_at BETWEEN $1 AND $2
        """, start_date, end_date)

        action_breakdown = await self.db_service.execute_read("""
            SELECT action, COUNT(*) as count
            FROM admin_audit_logs
            WHERE created_at BETWEEN $1 AND $2
            GROUP BY action
            ORDER BY count DESC
            LIMIT 20
        """, start_date, end_date)

        daily_stats = await self.db_service.execute_read("""
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM admin_audit_logs
            WHERE created_at BETWEEN $1 AND $2
            GROUP BY DATE(created_at)
            ORDER BY date
        """, start_date, end_date)

        top_admins = await self.db_service.execute_read("""
            SELECT al.admin_id, au.username, COUNT(*) as operation_count
            FROM admin_audit_logs al
            LEFT JOIN admin_users au ON al.admin_id = au.id
            WHERE al.created_at BETWEEN $1 AND $2
            GROUP BY al.admin_id, au.username
            ORDER BY operation_count DESC
            LIMIT 10
        """, start_date, end_date)

        return {
            "summary": dict(summary) if summary else {},
            "action_breakdown": [dict(a) for a in action_breakdown] if action_breakdown else [],
            "daily_stats": [dict(d) for d in daily_stats] if daily_stats else [],
            "top_admins": [dict(a) for a in top_admins] if top_admins else []
        }

    async def export_logs(
        self,
        start_date: datetime,
        end_date: datetime,
        format: str = "json"
    ) -> str:
        """导出审计日志"""
        if not self.db_service:
            return ""

        logs = await self.db_service.execute_read("""
            SELECT al.*, au.username as admin_username
            FROM admin_audit_logs al
            LEFT JOIN admin_users au ON al.admin_id = au.id
            WHERE al.created_at BETWEEN $1 AND $2
            ORDER BY al.created_at DESC
        """, start_date, end_date)

        if format == "json":
            return json.dumps(
                [self._format_log(dict(l)) for l in logs] if logs else [],
                default=str,
                ensure_ascii=False
            )
        elif format == "csv":
            import csv
            import io

            output = io.StringIO()
            if logs:
                writer = csv.DictWriter(output, fieldnames=[
                    "id", "admin_username", "action", "resource_type",
                    "resource_id", "ip_address", "severity", "created_at"
                ])
                writer.writeheader()
                for log in logs:
                    row = {
                        "id": log.get("id"),
                        "admin_username": log.get("admin_username", ""),
                        "action": log.get("action"),
                        "resource_type": log.get("resource_type"),
                        "resource_id": log.get("resource_id", ""),
                        "ip_address": log.get("ip_address", ""),
                        "severity": log.get("severity"),
                        "created_at": log.get("created_at")
                    }
                    writer.writerow(row)

            return output.getvalue()

        return ""

    def _sanitize_data(self, data: Dict) -> Dict:
        """清理敏感数据"""
        sanitized = {}
        for key, value in data.items():
            if key.lower() in self._sensitive_fields:
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_data(value)
            else:
                sanitized[key] = value
        return sanitized

    def _sign_log(self, log_entry: AuditLog) -> str:
        """签名日志"""
        data = f"{log_entry.admin_id}|{log_entry.action}|{log_entry.resource_type}|{log_entry.resource_id}|{log_entry.created_at.isoformat() if log_entry.created_at else ''}"
        
        signature = hmac.new(
            self.secret_key.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return signature

    def _format_log(self, log: Dict) -> Dict:
        """格式化日志"""
        return {
            "id": str(log.get("id", "")),
            "admin_id": log.get("admin_id", ""),
            "admin_username": log.get("admin_username", ""),
            "action": log.get("action", ""),
            "resource_type": log.get("resource_type", ""),
            "resource_id": log.get("resource_id", ""),
            "old_value": log.get("old_value") or {},
            "new_value": log.get("new_value") or {},
            "ip_address": log.get("ip_address", ""),
            "user_agent": log.get("user_agent", ""),
            "severity": log.get("severity", "medium"),
            "created_at": log.get("created_at").isoformat() if log.get("created_at") else None
        }


class ErrorSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    FATAL = "fatal"


@dataclass
class ErrorEvent:
    id: str = ""
    error_type: str = ""
    error_message: str = ""
    stack_trace: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    severity: str = "error"
    source: str = ""
    user_id: str = ""
    request_id: str = ""
    created_at: datetime = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "stack_trace": self.stack_trace,
            "context": self.context,
            "severity": self.severity,
            "source": self.source,
            "user_id": self.user_id,
            "request_id": self.request_id,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


@dataclass
class AlertRule:
    id: str = ""
    name: str = ""
    condition: str = ""
    threshold: int = 10
    time_window_minutes: int = 5
    severity: str = "warning"
    channels: List[str] = field(default_factory=list)
    is_active: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "condition": self.condition,
            "threshold": self.threshold,
            "time_window_minutes": self.time_window_minutes,
            "severity": self.severity,
            "channels": self.channels,
            "is_active": self.is_active
        }


class ErrorMonitoringService:
    """错误监控服务 - 提示词16"""

    def __init__(self, db_service=None, redis_client=None, sentry_dsn: str = None):
        self.db_service = db_service
        self.redis_client = redis_client
        self.sentry_dsn = sentry_dsn or os.getenv("SENTRY_DSN")
        self._error_counts: Dict[str, List[float]] = defaultdict(list)
        self._alert_rules: Dict[str, AlertRule] = {}
        self._alert_handlers: Dict[str, Callable] = {}
        self._sentry_client = None

        if self.sentry_dsn:
            self._init_sentry()

    def _init_sentry(self):
        """初始化Sentry"""
        try:
            import sentry_sdk
            sentry_sdk.init(
                dsn=self.sentry_dsn,
                traces_sample_rate=0.1,
                profiles_sample_rate=0.1
            )
            self._sentry_client = sentry_sdk
            logger.info("Sentry initialized successfully")
        except ImportError:
            logger.warning("Sentry SDK not installed")
        except Exception as e:
            logger.error(f"Failed to initialize Sentry: {e}")

    async def capture_error(
        self,
        error: Exception,
        context: Dict[str, Any] = None,
        user_id: str = "",
        request_id: str = "",
        source: str = "backend"
    ) -> str:
        """捕获错误"""
        error_event = ErrorEvent(
            error_type=type(error).__name__,
            error_message=str(error),
            stack_trace=traceback.format_exc(),
            context=context or {},
            severity=self._determine_severity(error),
            source=source,
            user_id=user_id,
            request_id=request_id,
            created_at=datetime.utcnow()
        )

        if self._sentry_client:
            try:
                with self._sentry_client.push_scope() as scope:
                    scope.set_tag("source", source)
                    if user_id:
                        scope.user = {"id": user_id}
                    if context:
                        for key, value in context.items():
                            scope.set_extra(key, value)
                    self._sentry_client.capture_exception(error)
            except Exception as e:
                logger.error(f"Failed to capture error in Sentry: {e}")

        error_id = await self._store_error(error_event)

        await self._check_alerts(error_event)

        return error_id

    async def capture_message(
        self,
        message: str,
        level: str = "info",
        context: Dict[str, Any] = None,
        source: str = "backend"
    ) -> str:
        """捕获消息"""
        if self._sentry_client:
            try:
                self._sentry_client.capture_message(message, level=level)
            except Exception as e:
                logger.error(f"Failed to capture message in Sentry: {e}")

        error_event = ErrorEvent(
            error_type="message",
            error_message=message,
            context=context or {},
            severity=level,
            source=source,
            created_at=datetime.utcnow()
        )

        return await self._store_error(error_event)

    async def get_errors(
        self,
        page: int = 1,
        page_size: int = 50,
        error_type: str = None,
        severity: str = None,
        source: str = None,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> Dict[str, Any]:
        """获取错误列表"""
        if not self.db_service:
            return {"errors": [], "total": 0, "page": page, "page_size": page_size}

        conditions = ["1=1"]
        args = []
        arg_idx = 1

        if error_type:
            conditions.append(f"error_type = ${arg_idx}")
            args.append(error_type)
            arg_idx += 1

        if severity:
            conditions.append(f"severity = ${arg_idx}")
            args.append(severity)
            arg_idx += 1

        if source:
            conditions.append(f"source = ${arg_idx}")
            args.append(source)
            arg_idx += 1

        if start_date:
            conditions.append(f"created_at >= ${arg_idx}")
            args.append(start_date)
            arg_idx += 1

        if end_date:
            conditions.append(f"created_at <= ${arg_idx}")
            args.append(end_date)
            arg_idx += 1

        where_clause = " AND ".join(conditions)

        count_sql = f"SELECT COUNT(*) FROM error_logs WHERE {where_clause}"
        total = await self.db_service.fetchval_read(count_sql, *args)

        offset = (page - 1) * page_size

        list_sql = f"""
            SELECT * FROM error_logs
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT {page_size} OFFSET {offset}
        """

        errors = await self.db_service.execute_read(list_sql, *args)

        return {
            "errors": [dict(e) for e in errors] if errors else [],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if total else 0
        }

    async def get_error_stats(
        self,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> Dict[str, Any]:
        """获取错误统计"""
        start_date = start_date or datetime.utcnow() - timedelta(days=7)
        end_date = end_date or datetime.utcnow()

        if not self.db_service:
            return {}

        summary = await self.db_service.fetchrow_read("""
            SELECT
                COUNT(*) as total_errors,
                COUNT(*) FILTER (WHERE severity = 'error') as error_count,
                COUNT(*) FILTER (WHERE severity = 'warning') as warning_count,
                COUNT(*) FILTER (WHERE severity = 'fatal') as fatal_count
            FROM error_logs
            WHERE created_at BETWEEN $1 AND $2
        """, start_date, end_date)

        error_types = await self.db_service.execute_read("""
            SELECT error_type, COUNT(*) as count
            FROM error_logs
            WHERE created_at BETWEEN $1 AND $2
            GROUP BY error_type
            ORDER BY count DESC
            LIMIT 10
        """, start_date, end_date)

        daily_errors = await self.db_service.execute_read("""
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM error_logs
            WHERE created_at BETWEEN $1 AND $2
            GROUP BY DATE(created_at)
            ORDER BY date
        """, start_date, end_date)

        return {
            "summary": dict(summary) if summary else {},
            "error_types": [dict(e) for e in error_types] if error_types else [],
            "daily_errors": [dict(d) for d in daily_errors] if daily_errors else []
        }

    def add_alert_rule(
        self,
        name: str,
        condition: str,
        threshold: int,
        time_window_minutes: int,
        severity: str = "warning",
        channels: List[str] = None
    ) -> str:
        """添加告警规则"""
        rule_id = hashlib.md5(f"{name}:{condition}".encode()).hexdigest()[:12]
        
        rule = AlertRule(
            id=rule_id,
            name=name,
            condition=condition,
            threshold=threshold,
            time_window_minutes=time_window_minutes,
            severity=severity,
            channels=channels or ["email"]
        )
        
        self._alert_rules[rule_id] = rule
        
        return rule_id

    def remove_alert_rule(self, rule_id: str) -> bool:
        """移除告警规则"""
        if rule_id in self._alert_rules:
            del self._alert_rules[rule_id]
            return True
        return False

    def register_alert_handler(self, channel: str, handler: Callable):
        """注册告警处理器"""
        self._alert_handlers[channel] = handler

    async def _store_error(self, error_event: ErrorEvent) -> str:
        """存储错误"""
        if self.db_service:
            try:
                result = await self.db_service.fetchrow_write("""
                    INSERT INTO error_logs (
                        error_type, error_message, stack_trace, context,
                        severity, source, user_id, request_id, created_at
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    RETURNING id
                """,
                    error_event.error_type,
                    error_event.error_message,
                    error_event.stack_trace,
                    json.dumps(error_event.context),
                    error_event.severity,
                    error_event.source,
                    error_event.user_id,
                    error_event.request_id,
                    error_event.created_at
                )
                error_event.id = str(result["id"]) if result else ""
            except Exception as e:
                logger.error(f"Failed to store error: {e}")

        return error_event.id

    async def _check_alerts(self, error_event: ErrorEvent):
        """检查告警"""
        now = time.time()
        error_key = f"{error_event.error_type}:{error_event.source}"
        
        self._error_counts[error_key].append(now)
        
        cutoff = now - 300
        self._error_counts[error_key] = [
            t for t in self._error_counts[error_key] if t > cutoff
        ]

        for rule_id, rule in self._alert_rules.items():
            if not rule.is_active:
                continue

            if rule.condition in error_key or rule.condition == "*":
                count = len(self._error_counts.get(error_key, []))
                
                if count >= rule.threshold:
                    await self._trigger_alert(rule, error_event, count)

    async def _trigger_alert(self, rule: AlertRule, error_event: ErrorEvent, count: int):
        """触发告警"""
        alert_data = {
            "rule_name": rule.name,
            "error_type": error_event.error_type,
            "error_message": error_event.error_message,
            "count": count,
            "threshold": rule.threshold,
            "severity": rule.severity,
            "timestamp": datetime.utcnow().isoformat()
        }

        for channel in rule.channels:
            handler = self._alert_handlers.get(channel)
            if handler:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(alert_data)
                    else:
                        handler(alert_data)
                except Exception as e:
                    logger.error(f"Alert handler error for {channel}: {e}")

    def _determine_severity(self, error: Exception) -> str:
        """确定错误严重程度"""
        if isinstance(error, (SystemExit, KeyboardInterrupt)):
            return "fatal"
        elif isinstance(error, (MemoryError, OSError)):
            return "fatal"
        elif isinstance(error, (ValueError, TypeError, KeyError)):
            return "warning"
        else:
            return "error"


audit_service: Optional[AuditService] = None
error_monitoring_service: Optional[ErrorMonitoringService] = None


async def get_audit_service() -> AuditService:
    global audit_service
    if audit_service is None:
        from ..database.high_performance_db import get_db_service
        db = await get_db_service()
        audit_service = AuditService(db)
    return audit_service


async def get_error_monitoring_service() -> ErrorMonitoringService:
    global error_monitoring_service
    if error_monitoring_service is None:
        from ..database.high_performance_db import get_db_service
        db = await get_db_service()
        error_monitoring_service = ErrorMonitoringService(db)
    return error_monitoring_service
