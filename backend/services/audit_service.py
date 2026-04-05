"""
合规审计日志服务
支持哈希链和数字签名
"""
import hashlib
import json
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from enum import Enum

from ..database import get_db


class ActionType(str, Enum):
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    LOGIN_FAILED = "LOGIN_FAILED"
    REGISTER = "REGISTER"
    PASSWORD_CHANGE = "PASSWORD_CHANGE"
    PROFILE_UPDATE = "PROFILE_UPDATE"
    TASK_CREATE = "TASK_CREATE"
    TASK_VIEW = "TASK_VIEW"
    TASK_UPDATE = "TASK_UPDATE"
    TASK_DELETE = "TASK_DELETE"
    TASK_ASSIGN = "TASK_ASSIGN"
    REPORT_CREATE = "REPORT_CREATE"
    REPORT_VIEW = "REPORT_VIEW"
    REPORT_EXPORT = "REPORT_EXPORT"
    REPORT_DELETE = "REPORT_DELETE"
    REPORT_SHARE = "REPORT_SHARE"
    TEAM_CREATE = "TEAM_CREATE"
    TEAM_JOIN = "TEAM_JOIN"
    TEAM_LEAVE = "TEAM_LEAVE"
    TEAM_MEMBER_ADD = "TEAM_MEMBER_ADD"
    TEAM_MEMBER_REMOVE = "TEAM_MEMBER_REMOVE"
    TEAM_DELETE = "TEAM_DELETE"
    FEEDBACK_CREATE = "FEEDBACK_CREATE"
    FEEDBACK_REPLY = "FEEDBACK_REPLY"
    REPORT_SUBMIT = "REPORT_SUBMIT"
    REPORT_PROCESS = "REPORT_PROCESS"
    ADMIN_USER_VIEW = "ADMIN_USER_VIEW"
    ADMIN_USER_CREATE = "ADMIN_USER_CREATE"
    ADMIN_USER_UPDATE = "ADMIN_USER_UPDATE"
    ADMIN_USER_DELETE = "ADMIN_USER_DELETE"
    ADMIN_SETTING_CHANGE = "ADMIN_SETTING_CHANGE"
    ADMIN_ANNOUNCEMENT_CREATE = "ADMIN_ANNOUNCEMENT_CREATE"
    ADMIN_ANNOUNCEMENT_PUBLISH = "ADMIN_ANNOUNCEMENT_PUBLISH"
    DATA_EXPORT = "DATA_EXPORT"
    DATA_IMPORT = "DATA_IMPORT"
    API_ACCESS = "API_ACCESS"
    FILE_UPLOAD = "FILE_UPLOAD"
    FILE_DOWNLOAD = "FILE_DOWNLOAD"
    PRIVACY_CONSENT = "PRIVACY_CONSENT"


class ResourceType(str, Enum):
    USER = "user"
    TASK = "task"
    REPORT = "report"
    TEAM = "team"
    FEEDBACK = "feedback"
    ANNOUNCEMENT = "announcement"
    SETTING = "setting"
    FILE = "file"
    SYSTEM = "system"


class AuditStatus(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    PENDING = "pending"


@dataclass
class AuditLog:
    id: str
    timestamp: datetime
    user_id: Optional[str]
    username: Optional[str]
    user_role: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    action_type: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    old_value: Optional[str]
    new_value: Optional[str]
    status: str
    error_message: Optional[str]
    hash: Optional[str]
    prev_hash: Optional[str]
    signature: Optional[str]


class AuditService:
    def __init__(self):
        self._hash_key = "fangtanai_audit_secret_key_2024"
    
    def _compute_hash(self, log_data: Dict[str, Any]) -> str:
        data = json.dumps(log_data, sort_keys=True, default=str)
        return hashlib.sha256((data + self._hash_key).encode()).hexdigest()
    
    async def _get_prev_hash(self) -> str:
        async with get_db() as conn:
            cursor = await conn.execute(
                "SELECT hash FROM audit_logs ORDER BY timestamp DESC LIMIT 1"
            )
            last_log = await cursor.fetchone()
            return last_log["hash"] if last_log else "0" * 64
    
    async def log(
        self,
        action_type: ActionType,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        user_role: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        resource_type: Optional[ResourceType] = None,
        resource_id: Optional[str] = None,
        old_value: Optional[Dict[str, Any]] = None,
        new_value: Optional[Dict[str, Any]] = None,
        status: AuditStatus = AuditStatus.SUCCESS,
        error_message: Optional[str] = None,
    ) -> str:
        log_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()
        prev_hash = await self._get_prev_hash()
        
        log_data = {
            "id": log_id,
            "timestamp": timestamp.isoformat(),
            "user_id": user_id,
            "username": username,
            "user_role": user_role,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "action_type": action_type.value if isinstance(action_type, ActionType) else action_type,
            "resource_type": resource_type.value if resource_type and isinstance(resource_type, ResourceType) else resource_type,
            "resource_id": resource_id,
            "old_value": json.dumps(old_value, default=str) if old_value else None,
            "new_value": json.dumps(new_value, default=str) if new_value else None,
            "status": status.value if isinstance(status, AuditStatus) else status,
            "error_message": error_message,
            "prev_hash": prev_hash,
        }
        
        log_hash = self._compute_hash(log_data)
        
        async with get_db() as conn:
            await conn.execute("""
                INSERT INTO audit_logs 
                (id, timestamp, user_id, username, user_role, ip_address, user_agent,
                 action_type, resource_type, resource_id, old_value, new_value,
                 status, error_message, hash, prev_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                log_id, timestamp.isoformat() if hasattr(timestamp, 'isoformat') else timestamp, user_id, username, user_role, ip_address, user_agent,
                action_type.value if isinstance(action_type, ActionType) else action_type,
                resource_type.value if resource_type and isinstance(resource_type, ResourceType) else resource_type,
                resource_id,
                json.dumps(old_value, default=str) if old_value else None,
                json.dumps(new_value, default=str) if new_value else None,
                status.value if isinstance(status, AuditStatus) else status,
                error_message, log_hash, prev_hash
            ))
            await conn.commit()
        
        await self._update_stats(action_type, status)
        await self._check_anomaly(action_type, user_id, username, ip_address, status)
        
        return log_id
    
    async def _update_stats(self, action_type: ActionType, status: AuditStatus):
        today = datetime.utcnow().strftime("%Y-%m-%d")
        
        async with get_db() as conn:
            existing = await conn.execute(
                "SELECT id FROM audit_stats WHERE date = ?", (today,)
            )
            existing_row = await existing.fetchone()
            
            if existing_row:
                updates = ["total_logs = total_logs + 1"]
                
                if action_type == ActionType.LOGIN:
                    updates.append("login_count = login_count + 1")
                elif action_type == ActionType.LOGOUT:
                    updates.append("logout_count = logout_count + 1")
                elif action_type == ActionType.TASK_CREATE:
                    updates.append("task_create_count = task_create_count + 1")
                elif action_type == ActionType.TASK_DELETE:
                    updates.append("task_delete_count = task_delete_count + 1")
                elif action_type == ActionType.REPORT_EXPORT:
                    updates.append("report_export_count = report_export_count + 1")
                elif action_type.value.startswith("ADMIN_"):
                    updates.append("admin_action_count = admin_action_count + 1")
                
                if status == AuditStatus.FAILURE:
                    updates.append("failure_count = failure_count + 1")
                
                await conn.execute(
                    f"UPDATE audit_stats SET {', '.join(updates)} WHERE date = ?",
                    [today]
                )
            else:
                await conn.execute("""
                    INSERT INTO audit_stats (id, date, total_logs, login_count, logout_count,
                        task_create_count, task_delete_count, report_export_count,
                        admin_action_count, failure_count)
                    VALUES (?, ?, 1, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(uuid.uuid4()), today,
                    1 if action_type == ActionType.LOGIN else 0,
                    1 if action_type == ActionType.LOGOUT else 0,
                    1 if action_type == ActionType.TASK_CREATE else 0,
                    1 if action_type == ActionType.TASK_DELETE else 0,
                    1 if action_type == ActionType.REPORT_EXPORT else 0,
                    1 if action_type.value.startswith("ADMIN_") else 0,
                    1 if status == AuditStatus.FAILURE else 0,
                ))
            await conn.commit()
    
    async def _check_anomaly(
        self,
        action_type: ActionType,
        user_id: Optional[str],
        username: Optional[str],
        ip_address: Optional[str],
        status: AuditStatus
    ):
        if action_type == ActionType.LOGIN_FAILED and status == AuditStatus.FAILURE:
            async with get_db() as conn:
                recent_failures = await conn.execute("""
                    SELECT COUNT(*) as count FROM audit_logs
                    WHERE action_type = 'LOGIN_FAILED'
                        AND ip_address = ?
                        AND timestamp > datetime('now', '-15 minutes')
                """, (ip_address,))
                recent_failures_row = await recent_failures.fetchone()
                
                if recent_failures_row and recent_failures_row["count"] >= 5:
                    await conn.execute("""
                        INSERT INTO audit_anomalies (id, user_id, username, anomaly_type, severity, description)
                        VALUES (?, ?, ?, 'BRUTE_FORCE', 'high', ?)
                    """, (
                        str(uuid.uuid4()), user_id, username,
                        f"IP {ip_address} 有 {recent_failures_row['count']} 次登录失败"
                    ))
                    await conn.commit()
        
        if action_type == ActionType.TASK_DELETE:
            async with get_db() as conn:
                recent_deletes = await conn.execute("""
                    SELECT COUNT(*) as count FROM audit_logs
                    WHERE action_type = 'TASK_DELETE'
                        AND user_id = ?
                        AND timestamp > datetime('now', '-1 hour')
                """, (user_id,))
                recent_deletes_row = await recent_deletes.fetchone()
                
                if recent_deletes_row and recent_deletes_row["count"] >= 10:
                    await conn.execute("""
                        INSERT INTO audit_anomalies (id, user_id, username, anomaly_type, severity, description)
                        VALUES (?, ?, ?, 'BULK_DELETE', 'medium', ?)
                    """, (
                        str(uuid.uuid4()), user_id, username,
                        f"用户在1小时内删除了 {recent_deletes_row['count']} 个任务"
                    ))
                    await conn.commit()
    
    def verify_chain(self, limit: int = 1000) -> Dict[str, Any]:
        with get_db() as conn:
            logs = conn.execute("""
                SELECT * FROM audit_logs
                ORDER BY timestamp ASC
                LIMIT ?
            """, (limit,)).fetchall()
        
        if not logs:
            return {"valid": True, "checked": 0, "errors": []}
        
        errors = []
        prev_hash = "0" * 64
        
        for log in logs:
            if log["prev_hash"] != prev_hash:
                errors.append({
                    "log_id": log["id"],
                    "error": "prev_hash_mismatch",
                    "expected": prev_hash,
                    "actual": log["prev_hash"]
                })
            
            log_data = {
                "id": log["id"],
                "timestamp": log["timestamp"],
                "user_id": log["user_id"],
                "username": log["username"],
                "user_role": log["user_role"],
                "ip_address": log["ip_address"],
                "user_agent": log["user_agent"],
                "action_type": log["action_type"],
                "resource_type": log["resource_type"],
                "resource_id": log["resource_id"],
                "old_value": log["old_value"],
                "new_value": log["new_value"],
                "status": log["status"],
                "error_message": log["error_message"],
                "prev_hash": log["prev_hash"],
            }
            
            expected_hash = self._compute_hash(log_data)
            if log["hash"] != expected_hash:
                errors.append({
                    "log_id": log["id"],
                    "error": "hash_mismatch",
                    "expected": expected_hash,
                    "actual": log["hash"]
                })
            
            prev_hash = log["hash"]
        
        return {
            "valid": len(errors) == 0,
            "checked": len(logs),
            "errors": errors
        }
    
    def get_logs(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[str] = None,
        action_type: Optional[str] = None,
        resource_type: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        query = "SELECT * FROM audit_logs WHERE 1=1"
        params = []
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date.isoformat())
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date.isoformat())
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        if action_type:
            query += " AND action_type = ?"
            params.append(action_type)
        if resource_type:
            query += " AND resource_type = ?"
            params.append(resource_type)
        if status:
            query += " AND status = ?"
            params.append(status)
        if search:
            query += " AND (username LIKE ? OR resource_id LIKE ? OR error_message LIKE ?)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term, search_term])
        
        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        with get_db() as conn:
            logs = conn.execute(query, params).fetchall()
            return [dict(log) for log in logs]
    
    def get_stats(self, days: int = 30) -> Dict[str, Any]:
        with get_db() as conn:
            stats = conn.execute("""
                SELECT 
                    SUM(total_logs) as total_logs,
                    SUM(login_count) as total_logins,
                    SUM(logout_count) as total_logouts,
                    SUM(task_create_count) as total_tasks_created,
                    SUM(task_delete_count) as total_tasks_deleted,
                    SUM(report_export_count) as total_reports_exported,
                    SUM(admin_action_count) as total_admin_actions,
                    SUM(failure_count) as total_failures
                FROM audit_stats
                WHERE date >= date('now', ?)
            """, (f'-{days} days',)).fetchone()
            
            daily_stats = conn.execute("""
                SELECT date, total_logs, login_count, task_create_count, 
                       report_export_count, failure_count
                FROM audit_stats
                WHERE date >= date('now', ?)
                ORDER BY date DESC
            """, (f'-{days} days',)).fetchall()
            
            action_breakdown = conn.execute("""
                SELECT action_type, COUNT(*) as count
                FROM audit_logs
                WHERE timestamp >= datetime('now', ?)
                GROUP BY action_type
                ORDER BY count DESC
                LIMIT 20
            """, (f'-{days} days',)).fetchall()
            
            return {
                "summary": dict(stats) if stats else {},
                "daily": [dict(s) for s in daily_stats],
                "action_breakdown": [dict(a) for a in action_breakdown]
            }
    
    def get_anomalies(
        self,
        is_resolved: Optional[bool] = None,
        severity: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        query = "SELECT * FROM audit_anomalies WHERE 1=1"
        params = []
        
        if is_resolved is not None:
            query += " AND is_resolved = ?"
            params.append(1 if is_resolved else 0)
        if severity:
            query += " AND severity = ?"
            params.append(severity)
        
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        with get_db() as conn:
            anomalies = conn.execute(query, params).fetchall()
            return [dict(a) for a in anomalies]
    
    def resolve_anomaly(self, anomaly_id: str, resolved_by: str) -> bool:
        with get_db() as conn:
            conn.execute("""
                UPDATE audit_anomalies
                SET is_resolved = 1, resolved_by = ?, resolved_at = ?
                WHERE id = ?
            """, (resolved_by, datetime.utcnow(), anomaly_id))
            conn.commit()
            return True
    
    def export_logs(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        format: str = "csv"
    ) -> str:
        logs = self.get_logs(
            start_date=start_date,
            end_date=end_date,
            limit=10000
        )
        
        if format == "csv":
            import io
            import csv
            
            output = io.StringIO()
            if logs:
                writer = csv.DictWriter(output, fieldnames=logs[0].keys())
                writer.writeheader()
                writer.writerows(logs)
            
            return output.getvalue()
        
        return json.dumps(logs, default=str, indent=2)


audit_service = AuditService()


async def log_audit(
    action_type: ActionType,
    user_id: Optional[str] = None,
    username: Optional[str] = None,
    user_role: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    resource_type: Optional[ResourceType] = None,
    resource_id: Optional[str] = None,
    old_value: Optional[Dict[str, Any]] = None,
    new_value: Optional[Dict[str, Any]] = None,
    status: AuditStatus = AuditStatus.SUCCESS,
    error_message: Optional[str] = None,
) -> str:
    return await audit_service.log(
        action_type=action_type,
        user_id=user_id,
        username=username,
        user_role=user_role,
        ip_address=ip_address,
        user_agent=user_agent,
        resource_type=resource_type,
        resource_id=resource_id,
        old_value=old_value,
        new_value=new_value,
        status=status,
        error_message=error_message,
    )
