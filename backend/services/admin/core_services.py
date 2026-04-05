# -*- coding: utf-8 -*-
"""
管理员后台核心服务
用户管理、审计日志、配置管理
"""
import asyncio
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import hashlib

from ..database.high_performance_db import get_db_service
from .auth_service import AdminUser, get_rbac_service, PermissionDeniedError

logger = logging.getLogger(__name__)


class UserStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    DELETED = "deleted"


@dataclass
class UserListParams:
    page: int = 1
    page_size: int = 20
    search: str = None
    role: str = None
    status: str = None
    sort_by: str = "created_at"
    sort_order: str = "desc"


@dataclass
class UserListResult:
    users: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int
    total_pages: int


class AdminUserManagementService:
    """管理员用户管理服务"""
    
    async def get_user_list(self, params: UserListParams) -> UserListResult:
        """获取用户列表"""
        db = await get_db_service()
        
        conditions = ["1=1"]
        args = []
        arg_idx = 1
        
        if params.search:
            conditions.append(f"(username LIKE ${arg_idx} OR email LIKE ${arg_idx})")
            args.append(f"%{params.search}%")
            arg_idx += 1
        
        if params.role:
            conditions.append(f"role = ${arg_idx}")
            args.append(params.role)
            arg_idx += 1
        
        if params.status:
            conditions.append(f"status = ${arg_idx}")
            args.append(params.status)
            arg_idx += 1
        
        where_clause = " AND ".join(conditions)
        
        count_sql = f"SELECT COUNT(*) FROM users WHERE {where_clause}"
        total = await db.fetchval_read(count_sql, *args)
        
        order_clause = f"ORDER BY {params.sort_by} {params.sort_order.upper()}"
        offset = (params.page - 1) * params.page_size
        
        list_sql = f"""
            SELECT id, username, email, role, status, created_at, last_login,
                   login_count, metadata
            FROM users
            WHERE {where_clause}
            {order_clause}
            LIMIT {params.page_size} OFFSET {offset}
        """
        
        users = await db.execute_read(list_sql, *args)
        
        total_pages = (total + params.page_size - 1) // params.page_size
        
        return UserListResult(
            users=[dict(u) for u in users],
            total=total,
            page=params.page,
            page_size=params.page_size,
            total_pages=total_pages
        )
    
    async def get_user_detail(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户详情"""
        db = await get_db_service()
        
        user = await db.fetchrow_read("""
            SELECT id, username, email, role, status, created_at, updated_at,
                   last_login, login_count, metadata, preferences
            FROM users
            WHERE id = $1
        """, user_id)
        
        if not user:
            return None
        
        result = dict(user)
        
        stats = await db.fetchrow_read("""
            SELECT 
                COUNT(*) FILTER (WHERE status = 'completed') as completed_tasks,
                COUNT(*) FILTER (WHERE status = 'pending') as pending_tasks,
                COUNT(*) FILTER (WHERE status = 'failed') as failed_tasks
            FROM tasks
            WHERE user_id = $1
        """, user_id)
        
        result["task_stats"] = dict(stats) if stats else {}
        
        return result
    
    async def update_user(
        self,
        user_id: str,
        admin: AdminUser,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """更新用户"""
        db = await get_db_service()
        
        old_user = await db.fetchrow_read("""
            SELECT id, username, email, role, status, metadata
            FROM users
            WHERE id = $1
        """, user_id)
        
        if not old_user:
            raise ValueError("用户不存在")
        
        allowed_fields = ["email", "role", "status", "metadata", "preferences"]
        update_fields = []
        update_values = []
        arg_idx = 1
        
        for field in allowed_fields:
            if field in updates:
                update_fields.append(f"{field} = ${arg_idx}")
                update_values.append(updates[field])
                arg_idx += 1
        
        if not update_fields:
            return dict(old_user)
        
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        
        update_sql = f"""
            UPDATE users
            SET {', '.join(update_fields)}
            WHERE id = ${arg_idx}
            RETURNING id, username, email, role, status, created_at, updated_at
        """
        update_values.append(user_id)
        
        updated = await db.fetchrow_write(update_sql, *update_values)
        
        await self._log_audit(
            admin=admin,
            action="update_user",
            resource_type="user",
            resource_id=user_id,
            old_value=dict(old_user),
            new_value=updates
        )
        
        return dict(updated)
    
    async def update_user_role(
        self,
        user_id: str,
        new_role: str,
        admin: AdminUser
    ) -> Dict[str, Any]:
        """更新用户角色"""
        valid_roles = ["user", "premium", "enterprise", "admin"]
        if new_role not in valid_roles:
            raise ValueError(f"无效的角色: {new_role}")
        
        return await self.update_user(user_id, admin, {"role": new_role})
    
    async def suspend_user(
        self,
        user_id: str,
        reason: str,
        admin: AdminUser
    ) -> Dict[str, Any]:
        """暂停用户"""
        updates = {
            "status": "suspended",
            "metadata": {"suspension_reason": reason, "suspended_by": admin.id}
        }
        return await self.update_user(user_id, admin, updates)
    
    async def activate_user(
        self,
        user_id: str,
        admin: AdminUser
    ) -> Dict[str, Any]:
        """激活用户"""
        return await self.update_user(user_id, admin, {"status": "active"})
    
    async def reset_user_password(
        self,
        user_id: str,
        new_password: str,
        admin: AdminUser
    ) -> bool:
        """重置用户密码"""
        db = await get_db_service()
        
        password_hash = hashlib.sha256(new_password.encode()).hexdigest()
        
        await db.execute_write("""
            UPDATE users
            SET password_hash = $1, password_changed_at = CURRENT_TIMESTAMP,
                require_password_change = true
            WHERE id = $2
        """, password_hash, user_id)
        
        await self._log_audit(
            admin=admin,
            action="reset_password",
            resource_type="user",
            resource_id=user_id,
            new_value={"password_reset": True}
        )
        
        return True
    
    async def adjust_user_points(
        self,
        user_id: str,
        points: int,
        reason: str,
        admin: AdminUser
    ) -> Dict[str, Any]:
        """调整用户积分"""
        db = await get_db_service()
        
        old_points = await db.fetchval_read(
            "SELECT points FROM users WHERE id = $1", user_id
        )
        
        new_points = old_points + points
        if new_points < 0:
            raise ValueError("积分不能为负数")
        
        await db.execute_write("""
            UPDATE users SET points = $1 WHERE id = $2
        """, new_points, user_id)
        
        await db.execute_write("""
            INSERT INTO point_transactions (user_id, amount, balance, type, reason, operator_id)
            VALUES ($1, $2, $3, 'admin_adjust', $4, $5)
        """, user_id, points, new_points, reason, admin.id)
        
        await self._log_audit(
            admin=admin,
            action="adjust_points",
            resource_type="user",
            resource_id=user_id,
            old_value={"points": old_points},
            new_value={"points": new_points, "reason": reason}
        )
        
        return {"user_id": user_id, "old_points": old_points, "new_points": new_points}
    
    async def _log_audit(
        self,
        admin: AdminUser,
        action: str,
        resource_type: str,
        resource_id: str,
        old_value: Dict = None,
        new_value: Dict = None
    ):
        """记录审计日志"""
        db = await get_db_service()
        
        await db.execute_write("""
            INSERT INTO admin_audit_logs (
                admin_id, action, resource_type, resource_id,
                old_value, new_value, created_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, CURRENT_TIMESTAMP)
        """,
            admin.id,
            action,
            resource_type,
            resource_id,
            json.dumps(old_value) if old_value else None,
            json.dumps(new_value) if new_value else None
        )


class AdminAuditService:
    """管理员审计服务"""
    
    async def get_audit_logs(
        self,
        page: int = 1,
        page_size: int = 50,
        admin_id: str = None,
        action: str = None,
        resource_type: str = None,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> Dict[str, Any]:
        """获取审计日志"""
        db = await get_db_service()
        
        conditions = ["1=1"]
        args = []
        arg_idx = 1
        
        if admin_id:
            conditions.append(f"admin_id = ${arg_idx}")
            args.append(admin_id)
            arg_idx += 1
        
        if action:
            conditions.append(f"action LIKE ${arg_idx}")
            args.append(f"%{action}%")
            arg_idx += 1
        
        if resource_type:
            conditions.append(f"resource_type = ${arg_idx}")
            args.append(resource_type)
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
        
        count_sql = f"SELECT COUNT(*) FROM admin_audit_logs WHERE {where_clause}"
        total = await db.fetchval_read(count_sql, *args)
        
        offset = (page - 1) * page_size
        
        list_sql = f"""
            SELECT al.*, au.username as admin_username
            FROM admin_audit_logs al
            LEFT JOIN admin_users au ON al.admin_id = au.id
            WHERE {where_clause}
            ORDER BY al.created_at DESC
            LIMIT {page_size} OFFSET {offset}
        """
        
        logs = await db.execute_read(list_sql, *args)
        
        return {
            "logs": [dict(l) for l in logs],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    
    async def get_audit_stats(
        self,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> Dict[str, Any]:
        """获取审计统计"""
        db = await get_db_service()
        
        start_date = start_date or datetime.utcnow() - timedelta(days=7)
        end_date = end_date or datetime.utcnow()
        
        stats = await db.fetchrow_read("""
            SELECT
                COUNT(*) as total_operations,
                COUNT(DISTINCT admin_id) as active_admins,
                COUNT(DISTINCT resource_type) as resource_types
            FROM admin_audit_logs
            WHERE created_at BETWEEN $1 AND $2
        """, start_date, end_date)
        
        action_breakdown = await db.execute_read("""
            SELECT action, COUNT(*) as count
            FROM admin_audit_logs
            WHERE created_at BETWEEN $1 AND $2
            GROUP BY action
            ORDER BY count DESC
            LIMIT 20
        """, start_date, end_date)
        
        daily_stats = await db.execute_read("""
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM admin_audit_logs
            WHERE created_at BETWEEN $1 AND $2
            GROUP BY DATE(created_at)
            ORDER BY date
        """, start_date, end_date)
        
        return {
            "summary": dict(stats),
            "action_breakdown": [dict(a) for a in action_breakdown],
            "daily_stats": [dict(d) for d in daily_stats]
        }
    
    async def export_audit_logs(
        self,
        start_date: datetime,
        end_date: datetime,
        format: str = "json"
    ) -> str:
        """导出审计日志"""
        db = await get_db_service()
        
        logs = await db.execute_read("""
            SELECT al.*, au.username as admin_username
            FROM admin_audit_logs al
            LEFT JOIN admin_users au ON al.admin_id = au.id
            WHERE al.created_at BETWEEN $1 AND $2
            ORDER BY al.created_at DESC
        """, start_date, end_date)
        
        if format == "json":
            return json.dumps([dict(l) for l in logs], default=str, ensure_ascii=False)
        elif format == "csv":
            import csv
            import io
            
            output = io.StringIO()
            if logs:
                writer = csv.DictWriter(output, fieldnames=logs[0].keys())
                writer.writeheader()
                for log in logs:
                    row = dict(log)
                    for k, v in row.items():
                        if isinstance(v, (dict, list)):
                            row[k] = json.dumps(v, ensure_ascii=False)
                    writer.writerow(row)
            
            return output.getvalue()
        
        return ""


class AdminConfigService:
    """管理员配置服务"""
    
    async def get_all_configs(self) -> List[Dict[str, Any]]:
        """获取所有配置"""
        db = await get_db_service()
        
        configs = await db.execute_read("""
            SELECT key, value, value_type, description, is_public,
                   updated_at, updated_by
            FROM admin_configs
            ORDER BY key
        """)
        
        return [dict(c) for c in configs]
    
    async def get_config(self, key: str) -> Optional[Dict[str, Any]]:
        """获取单个配置"""
        db = await get_db_service()
        
        config = await db.fetchrow_read("""
            SELECT key, value, value_type, description, is_public,
                   updated_at, updated_by
            FROM admin_configs
            WHERE key = $1
        """, key)
        
        if not config:
            return None
        
        result = dict(config)
        
        if result["value_type"] == "int":
            result["parsed_value"] = int(result["value"])
        elif result["value_type"] == "float":
            result["parsed_value"] = float(result["value"])
        elif result["value_type"] == "bool":
            result["parsed_value"] = result["value"].lower() == "true"
        elif result["value_type"] == "json":
            result["parsed_value"] = json.loads(result["value"])
        else:
            result["parsed_value"] = result["value"]
        
        return result
    
    async def set_config(
        self,
        key: str,
        value: Any,
        admin: AdminUser,
        value_type: str = "string"
    ) -> Dict[str, Any]:
        """设置配置"""
        db = await get_db_service()
        
        if value_type == "json":
            value = json.dumps(value)
        else:
            value = str(value)
        
        await db.execute_write("""
            INSERT INTO admin_configs (key, value, value_type, updated_at, updated_by)
            VALUES ($1, $2, $3, CURRENT_TIMESTAMP, $4)
            ON CONFLICT (key)
            DO UPDATE SET value = $2, updated_at = CURRENT_TIMESTAMP, updated_by = $4
        """, key, value, value_type, admin.id)
        
        await self._log_audit(
            admin=admin,
            action="set_config",
            resource_type="config",
            resource_id=key,
            new_value={"value": value, "type": value_type}
        )
        
        return await self.get_config(key)
    
    async def delete_config(self, key: str, admin: AdminUser) -> bool:
        """删除配置"""
        db = await get_db_service()
        
        old_config = await self.get_config(key)
        if not old_config:
            return False
        
        await db.execute_write("""
            DELETE FROM admin_configs WHERE key = $1
        """, key)
        
        await self._log_audit(
            admin=admin,
            action="delete_config",
            resource_type="config",
            resource_id=key,
            old_value=old_config
        )
        
        return True
    
    async def _log_audit(
        self,
        admin: AdminUser,
        action: str,
        resource_type: str,
        resource_id: str,
        old_value: Dict = None,
        new_value: Dict = None
    ):
        """记录审计日志"""
        db = await get_db_service()
        
        await db.execute_write("""
            INSERT INTO admin_audit_logs (
                admin_id, action, resource_type, resource_id,
                old_value, new_value, created_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, CURRENT_TIMESTAMP)
        """,
            admin.id,
            action,
            resource_type,
            resource_id,
            json.dumps(old_value) if old_value else None,
            json.dumps(new_value) if new_value else None
        )


admin_user_service: Optional[AdminUserManagementService] = None
admin_audit_service: Optional[AdminAuditService] = None
admin_config_service: Optional[AdminConfigService] = None


async def get_admin_user_service() -> AdminUserManagementService:
    global admin_user_service
    if admin_user_service is None:
        admin_user_service = AdminUserManagementService()
    return admin_user_service


async def get_admin_audit_service() -> AdminAuditService:
    global admin_audit_service
    if admin_audit_service is None:
        admin_audit_service = AdminAuditService()
    return admin_audit_service


async def get_admin_config_service() -> AdminConfigService:
    global admin_config_service
    if admin_config_service is None:
        admin_config_service = AdminConfigService()
    return admin_config_service
