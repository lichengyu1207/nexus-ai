# -*- coding: utf-8 -*-
"""
功能模块重构 - 提示词8-11
用户管理模块重构、智能体监控模块、统计报表模块、配置管理模块
"""
import asyncio
import json
import logging
import time
import os
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class UserStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class AgentStatus(Enum):
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    STARTING = "starting"
    STOPPING = "stopping"


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class PaginationParams:
    page: int = 1
    page_size: int = 20
    sort_by: str = "created_at"
    sort_order: str = "desc"


@dataclass
class UserFilterParams(PaginationParams):
    search: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None


@dataclass
class AgentFilterParams(PaginationParams):
    agent_type: Optional[str] = None
    status: Optional[str] = None


@dataclass
class TaskFilterParams(PaginationParams):
    user_id: Optional[str] = None
    status: Optional[str] = None
    task_type: Optional[str] = None
    started_after: Optional[datetime] = None
    started_before: Optional[datetime] = None


@dataclass
class PaginatedResult:
    items: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int
    total_pages: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "items": self.items,
            "total": self.total,
            "page": self.page,
            "page_size": self.page_size,
            "total_pages": self.total_pages
        }


class BaseRepository(ABC):
    """基础仓储抽象类"""

    def __init__(self, db_service=None):
        self.db_service = db_service

    @abstractmethod
    async def find_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def find_all(self, params: Any) -> PaginatedResult:
        pass

    @abstractmethod
    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def update(self, id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def delete(self, id: str) -> bool:
        pass


class UserRepository(BaseRepository):
    """用户仓储"""

    async def find_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        if not self.db_service:
            return None
        result = await self.db_service.fetchrow_read("""
            SELECT id, username, email, role, status, points, created_at, 
                   updated_at, last_login, login_count, metadata, preferences
            FROM users
            WHERE id = $1 AND deleted_at IS NULL
        """, id)
        return dict(result) if result else None

    async def find_all(self, params: UserFilterParams) -> PaginatedResult:
        if not self.db_service:
            return PaginatedResult(items=[], total=0, page=params.page, 
                                   page_size=params.page_size, total_pages=0)

        conditions = ["deleted_at IS NULL"]
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

        if params.created_after:
            conditions.append(f"created_at >= ${arg_idx}")
            args.append(params.created_after)
            arg_idx += 1

        if params.created_before:
            conditions.append(f"created_at <= ${arg_idx}")
            args.append(params.created_before)
            arg_idx += 1

        where_clause = " AND ".join(conditions)

        count_sql = f"SELECT COUNT(*) FROM users WHERE {where_clause}"
        total = await self.db_service.fetchval_read(count_sql, *args)

        order_clause = f"ORDER BY {params.sort_by} {params.sort_order.upper()}"
        offset = (params.page - 1) * params.page_size

        list_sql = f"""
            SELECT id, username, email, role, status, points, created_at, 
                   last_login, login_count
            FROM users
            WHERE {where_clause}
            {order_clause}
            LIMIT {params.page_size} OFFSET {offset}
        """

        items = await self.db_service.execute_read(list_sql, *args)
        items = [dict(item) for item in items]

        total_pages = (total + params.page_size - 1) // params.page_size

        return PaginatedResult(
            items=items,
            total=total,
            page=params.page,
            page_size=params.page_size,
            total_pages=total_pages
        )

    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.db_service:
            raise ValueError("Database service not available")

        result = await self.db_service.fetchrow_write("""
            INSERT INTO users (username, email, password_hash, role, status, points, metadata, preferences)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id, username, email, role, status, points, created_at
        """,
            data.get("username"),
            data.get("email"),
            data.get("password_hash"),
            data.get("role", "user"),
            data.get("status", "active"),
            data.get("points", 0),
            data.get("metadata", {}),
            data.get("preferences", {})
        )
        return dict(result) if result else None

    async def update(self, id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not self.db_service:
            return None

        allowed_fields = ["email", "role", "status", "points", "metadata", "preferences"]
        update_fields = []
        update_values = []
        arg_idx = 1

        for field in allowed_fields:
            if field in data:
                update_fields.append(f"{field} = ${arg_idx}")
                update_values.append(data[field])
                arg_idx += 1

        if not update_fields:
            return await self.find_by_id(id)

        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        update_values.append(id)

        update_sql = f"""
            UPDATE users
            SET {', '.join(update_fields)}
            WHERE id = ${arg_idx}
            RETURNING id, username, email, role, status, points, created_at, updated_at
        """

        result = await self.db_service.fetchrow_write(update_sql, *update_values)
        return dict(result) if result else None

    async def delete(self, id: str) -> bool:
        if not self.db_service:
            return False

        result = await self.db_service.execute_write("""
            UPDATE users SET deleted_at = CURRENT_TIMESTAMP WHERE id = $1
        """, id)
        return result > 0

    async def update_password(self, id: str, password_hash: str) -> bool:
        if not self.db_service:
            return False

        result = await self.db_service.execute_write("""
            UPDATE users 
            SET password_hash = $1, password_changed_at = CURRENT_TIMESTAMP
            WHERE id = $2
        """, password_hash, id)
        return result > 0

    async def update_points(self, id: str, points_delta: int) -> Optional[int]:
        if not self.db_service:
            return None

        new_points = await self.db_service.fetchval_write("""
            UPDATE users 
            SET points = GREATEST(0, points + $1)
            WHERE id = $2
            RETURNING points
        """, points_delta, id)
        return new_points

    async def update_last_login(self, id: str) -> bool:
        if not self.db_service:
            return False

        result = await self.db_service.execute_write("""
            UPDATE users 
            SET last_login = CURRENT_TIMESTAMP, login_count = login_count + 1
            WHERE id = $1
        """, id)
        return result > 0


class UserService:
    """用户服务 - 提示词8"""

    def __init__(self, user_repo: UserRepository = None, audit_service=None):
        self.user_repo = user_repo
        self.audit_service = audit_service

    async def get_user_list(self, params: UserFilterParams) -> PaginatedResult:
        """获取用户列表（支持筛选、搜索、分页）"""
        return await self.user_repo.find_all(params)

    async def get_user_detail(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户详情"""
        user = await self.user_repo.find_by_id(user_id)
        if not user:
            return None

        user["task_stats"] = await self._get_user_task_stats(user_id)
        user["point_history"] = await self._get_user_point_history(user_id)
        return user

    async def update_user_role(
        self, 
        user_id: str, 
        new_role: str, 
        admin_id: str
    ) -> Optional[Dict[str, Any]]:
        """更新用户角色"""
        valid_roles = ["user", "premium", "enterprise", "admin"]
        if new_role not in valid_roles:
            raise ValueError(f"Invalid role: {new_role}")

        old_user = await self.user_repo.find_by_id(user_id)
        if not old_user:
            raise ValueError("User not found")

        updated = await self.user_repo.update(user_id, {"role": new_role})

        await self._log_audit(
            admin_id=admin_id,
            action="update_role",
            resource_type="user",
            resource_id=user_id,
            old_value={"role": old_user["role"]},
            new_value={"role": new_role}
        )

        return updated

    async def suspend_user(
        self, 
        user_id: str, 
        reason: str, 
        admin_id: str
    ) -> Optional[Dict[str, Any]]:
        """暂停用户"""
        old_user = await self.user_repo.find_by_id(user_id)
        if not old_user:
            raise ValueError("User not found")

        updated = await self.user_repo.update(user_id, {
            "status": "suspended",
            "metadata": {"suspension_reason": reason, "suspended_by": admin_id}
        })

        await self._log_audit(
            admin_id=admin_id,
            action="suspend_user",
            resource_type="user",
            resource_id=user_id,
            old_value={"status": old_user["status"]},
            new_value={"status": "suspended", "reason": reason}
        )

        return updated

    async def activate_user(self, user_id: str, admin_id: str) -> Optional[Dict[str, Any]]:
        """激活用户"""
        old_user = await self.user_repo.find_by_id(user_id)
        if not old_user:
            raise ValueError("User not found")

        updated = await self.user_repo.update(user_id, {"status": "active"})

        await self._log_audit(
            admin_id=admin_id,
            action="activate_user",
            resource_type="user",
            resource_id=user_id,
            old_value={"status": old_user["status"]},
            new_value={"status": "active"}
        )

        return updated

    async def reset_user_password(
        self, 
        user_id: str, 
        new_password: str, 
        admin_id: str
    ) -> bool:
        """重置用户密码"""
        import hashlib
        password_hash = hashlib.sha256(new_password.encode()).hexdigest()

        success = await self.user_repo.update_password(user_id, password_hash)

        if success:
            await self._log_audit(
                admin_id=admin_id,
                action="reset_password",
                resource_type="user",
                resource_id=user_id,
                new_value={"password_reset": True}
            )

        return success

    async def adjust_user_points(
        self, 
        user_id: str, 
        points: int, 
        reason: str, 
        admin_id: str
    ) -> Dict[str, Any]:
        """调整用户积分"""
        old_user = await self.user_repo.find_by_id(user_id)
        if not old_user:
            raise ValueError("User not found")

        old_points = old_user.get("points", 0)
        new_points = await self.user_repo.update_points(user_id, points)

        if new_points is not None:
            await self._log_audit(
                admin_id=admin_id,
                action="adjust_points",
                resource_type="user",
                resource_id=user_id,
                old_value={"points": old_points},
                new_value={"points": new_points, "delta": points, "reason": reason}
            )

        return {
            "user_id": user_id,
            "old_points": old_points,
            "new_points": new_points,
            "delta": points
        }

    async def _get_user_task_stats(self, user_id: str) -> Dict[str, int]:
        """获取用户任务统计"""
        if not self.user_repo.db_service:
            return {}
        
        stats = await self.user_repo.db_service.fetchrow_read("""
            SELECT 
                COUNT(*) FILTER (WHERE status = 'completed') as completed,
                COUNT(*) FILTER (WHERE status = 'pending') as pending,
                COUNT(*) FILTER (WHERE status = 'running') as running,
                COUNT(*) FILTER (WHERE status = 'failed') as failed
            FROM tasks
            WHERE user_id = $1
        """, user_id)
        return dict(stats) if stats else {}

    async def _get_user_point_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        """获取用户积分历史"""
        if not self.user_repo.db_service:
            return []
        
        history = await self.user_repo.db_service.execute_read("""
            SELECT amount, balance, type, reason, created_at
            FROM point_transactions
            WHERE user_id = $1
            ORDER BY created_at DESC
            LIMIT $2
        """, user_id, limit)
        return [dict(h) for h in history] if history else []

    async def _log_audit(self, **kwargs):
        """记录审计日志"""
        if self.audit_service:
            await self.audit_service.log(**kwargs)


class AgentMonitorService:
    """智能体监控服务 - 提示词9"""

    def __init__(self, db_service=None, redis_client=None, libu_agent=None):
        self.db_service = db_service
        self.redis_client = redis_client
        self.libu_agent = libu_agent
        self._status_cache: Dict[str, Dict] = {}
        self._cache_ttl = 30

    async def get_agent_list(self, params: AgentFilterParams) -> PaginatedResult:
        """获取智能体列表"""
        if not self.db_service:
            return PaginatedResult(items=[], total=0, page=params.page,
                                   page_size=params.page_size, total_pages=0)

        conditions = ["1=1"]
        args = []
        arg_idx = 1

        if params.agent_type:
            conditions.append(f"agent_type = ${arg_idx}")
            args.append(params.agent_type)
            arg_idx += 1

        if params.status:
            conditions.append(f"status = ${arg_idx}")
            args.append(params.status)
            arg_idx += 1

        where_clause = " AND ".join(conditions)

        count_sql = f"SELECT COUNT(*) FROM agent_registry WHERE {where_clause}"
        total = await self.db_service.fetchval_read(count_sql, *args)

        order_clause = f"ORDER BY {params.sort_by} {params.sort_order.upper()}"
        offset = (params.page - 1) * params.page_size

        list_sql = f"""
            SELECT id, name, agent_type, status, created_at, 
                   last_heartbeat, metadata, config
            FROM agent_registry
            WHERE {where_clause}
            {order_clause}
            LIMIT {params.page_size} OFFSET {offset}
        """

        items = await self.db_service.execute_read(list_sql, *args)
        items = [dict(item) for item in items]

        for item in items:
            item["real_time_status"] = await self._get_real_time_status(item["id"])
            item["resource_usage"] = await self._get_resource_usage(item["id"])

        total_pages = (total + params.page_size - 1) // params.page_size

        return PaginatedResult(
            items=items,
            total=total,
            page=params.page,
            page_size=params.page_size,
            total_pages=total_pages
        )

    async def get_agent_detail(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """获取智能体详情"""
        if not self.db_service:
            return None

        agent = await self.db_service.fetchrow_read("""
            SELECT id, name, agent_type, status, created_at, 
                   last_heartbeat, metadata, config, error_message
            FROM agent_registry
            WHERE id = $1
        """, agent_id)

        if not agent:
            return None

        result = dict(agent)
        result["real_time_status"] = await self._get_real_time_status(agent_id)
        result["resource_usage"] = await self._get_resource_usage(agent_id)
        result["recent_tasks"] = await self._get_recent_tasks(agent_id)
        result["health_history"] = await self._get_health_history(agent_id)

        return result

    async def start_agent(self, agent_id: str, admin_id: str) -> Dict[str, Any]:
        """启动智能体"""
        if self.libu_agent:
            result = await self.libu_agent.start_agent(agent_id)
        else:
            if not self.db_service:
                raise ValueError("Database service not available")

            await self.db_service.execute_write("""
                UPDATE agent_registry 
                SET status = 'running', last_heartbeat = CURRENT_TIMESTAMP
                WHERE id = $1
            """, agent_id)
            result = {"success": True, "agent_id": agent_id}

        await self._log_agent_operation(admin_id, "start_agent", agent_id, result)
        return result

    async def stop_agent(self, agent_id: str, admin_id: str) -> Dict[str, Any]:
        """停止智能体"""
        if self.libu_agent:
            result = await self.libu_agent.stop_agent(agent_id)
        else:
            if not self.db_service:
                raise ValueError("Database service not available")

            await self.db_service.execute_write("""
                UPDATE agent_registry 
                SET status = 'stopped'
                WHERE id = $1
            """, agent_id)
            result = {"success": True, "agent_id": agent_id}

        await self._log_agent_operation(admin_id, "stop_agent", agent_id, result)
        return result

    async def restart_agent(self, agent_id: str, admin_id: str) -> Dict[str, Any]:
        """重启智能体"""
        await self.stop_agent(agent_id, admin_id)
        await asyncio.sleep(2)
        return await self.start_agent(agent_id, admin_id)

    async def update_agent_config(
        self, 
        agent_id: str, 
        config: Dict[str, Any], 
        admin_id: str
    ) -> bool:
        """更新智能体配置"""
        if not self.db_service:
            return False

        result = await self.db_service.execute_write("""
            UPDATE agent_registry 
            SET config = $1, updated_at = CURRENT_TIMESTAMP
            WHERE id = $2
        """, json.dumps(config), agent_id)

        await self._log_agent_operation(admin_id, "update_config", agent_id, {"config": config})
        return result > 0

    async def _get_real_time_status(self, agent_id: str) -> Dict[str, Any]:
        """获取实时状态"""
        cache_key = f"agent_status:{agent_id}"
        
        if cache_key in self._status_cache:
            cached = self._status_cache[cache_key]
            if time.time() - cached["timestamp"] < self._cache_ttl:
                return cached["data"]

        status = {"is_alive": False, "last_check": datetime.utcnow().isoformat()}

        if self.redis_client:
            try:
                heartbeat = await self.redis_client.get(f"agent:{agent_id}:heartbeat")
                if heartbeat:
                    status["is_alive"] = True
                    status["last_heartbeat"] = heartbeat.decode() if isinstance(heartbeat, bytes) else heartbeat
            except Exception as e:
                logger.warning(f"Redis error getting agent status: {e}")

        self._status_cache[cache_key] = {"timestamp": time.time(), "data": status}
        return status

    async def _get_resource_usage(self, agent_id: str) -> Dict[str, Any]:
        """获取资源使用率"""
        if self.redis_client:
            try:
                usage = await self.redis_client.get(f"agent:{agent_id}:resources")
                if usage:
                    return json.loads(usage)
            except Exception as e:
                logger.warning(f"Redis error getting resource usage: {e}")

        return {"cpu_percent": 0, "memory_percent": 0, "disk_percent": 0}

    async def _get_recent_tasks(self, agent_id: str, limit: int = 10) -> List[Dict]:
        """获取最近任务"""
        if not self.db_service:
            return []

        tasks = await self.db_service.execute_read("""
            SELECT id, task_type, status, created_at, completed_at, error_message
            FROM tasks
            WHERE agent_id = $1
            ORDER BY created_at DESC
            LIMIT $2
        """, agent_id, limit)
        return [dict(t) for t in tasks] if tasks else []

    async def _get_health_history(self, agent_id: str, hours: int = 24) -> List[Dict]:
        """获取健康历史"""
        if not self.db_service:
            return []

        history = await self.db_service.execute_read("""
            SELECT status, checked_at, response_time_ms, error_message
            FROM agent_health_checks
            WHERE agent_id = $1 AND checked_at > NOW() - INTERVAL '%s hours'
            ORDER BY checked_at DESC
        """, agent_id, hours)
        return [dict(h) for h in history] if history else []

    async def _log_agent_operation(self, admin_id: str, action: str, agent_id: str, result: Dict):
        """记录智能体操作日志"""
        if self.db_service:
            await self.db_service.execute_write("""
                INSERT INTO admin_audit_logs (
                    admin_id, action, resource_type, resource_id, new_value, created_at
                )
                VALUES ($1, $2, $3, $4, $5, CURRENT_TIMESTAMP)
            """, admin_id, action, "agent", agent_id, json.dumps(result))


class StatisticsService:
    """统计报表服务 - 提示词10"""

    def __init__(self, db_service=None, redis_client=None):
        self.db_service = db_service
        self.redis_client = redis_client
        self._cache_prefix = "stats:"

    async def get_overview_stats(self) -> Dict[str, Any]:
        """获取总览统计"""
        cache_key = f"{self._cache_prefix}overview"
        cached = await self._get_cached(cache_key)
        if cached:
            return cached

        if not self.db_service:
            return self._default_overview()

        stats = {}

        user_stats = await self.db_service.fetchrow_read("""
            SELECT 
                COUNT(*) as total_users,
                COUNT(*) FILTER (WHERE status = 'active') as active_users,
                COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours') as new_users_today
            FROM users WHERE deleted_at IS NULL
        """)
        stats["users"] = dict(user_stats) if user_stats else {}

        task_stats = await self.db_service.fetchrow_read("""
            SELECT 
                COUNT(*) as total_tasks,
                COUNT(*) FILTER (WHERE status = 'completed') as completed_tasks,
                COUNT(*) FILTER (WHERE status = 'running') as running_tasks,
                COUNT(*) FILTER (WHERE status = 'failed') as failed_tasks,
                COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours') as tasks_today
            FROM tasks
        """)
        stats["tasks"] = dict(task_stats) if task_stats else {}

        agent_stats = await self.db_service.fetchrow_read("""
            SELECT 
                COUNT(*) as total_agents,
                COUNT(*) FILTER (WHERE status = 'running') as running_agents,
                COUNT(*) FILTER (WHERE status = 'stopped') as stopped_agents
            FROM agent_registry
        """)
        stats["agents"] = dict(agent_stats) if agent_stats else {}

        await self._set_cached(cache_key, stats, ttl=300)
        return stats

    async def get_user_stats(
        self, 
        start_date: datetime = None, 
        end_date: datetime = None
    ) -> Dict[str, Any]:
        """获取用户统计"""
        start_date = start_date or datetime.utcnow() - timedelta(days=30)
        end_date = end_date or datetime.utcnow()

        cache_key = f"{self._cache_prefix}users:{start_date.date()}:{end_date.date()}"
        cached = await self._get_cached(cache_key)
        if cached:
            return cached

        if not self.db_service:
            return {}

        daily_new_users = await self.db_service.execute_read("""
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM users
            WHERE created_at BETWEEN $1 AND $2 AND deleted_at IS NULL
            GROUP BY DATE(created_at)
            ORDER BY date
        """, start_date, end_date)

        role_distribution = await self.db_service.execute_read("""
            SELECT role, COUNT(*) as count
            FROM users
            WHERE deleted_at IS NULL
            GROUP BY role
        """)

        activity_stats = await self.db_service.fetchrow_read("""
            SELECT 
                COUNT(DISTINCT user_id) as active_users,
                COUNT(*) as total_logins
            FROM user_login_logs
            WHERE login_at BETWEEN $1 AND $2
        """, start_date, end_date)

        result = {
            "daily_new_users": [dict(d) for d in daily_new_users] if daily_new_users else [],
            "role_distribution": [dict(r) for r in role_distribution] if role_distribution else [],
            "activity": dict(activity_stats) if activity_stats else {}
        }

        await self._set_cached(cache_key, result, ttl=300)
        return result

    async def get_task_stats(
        self, 
        start_date: datetime = None, 
        end_date: datetime = None
    ) -> Dict[str, Any]:
        """获取任务统计"""
        start_date = start_date or datetime.utcnow() - timedelta(days=30)
        end_date = end_date or datetime.utcnow()

        cache_key = f"{self._cache_prefix}tasks:{start_date.date()}:{end_date.date()}"
        cached = await self._get_cached(cache_key)
        if cached:
            return cached

        if not self.db_service:
            return {}

        daily_tasks = await self.db_service.execute_read("""
            SELECT DATE(created_at) as date, 
                   COUNT(*) as total,
                   COUNT(*) FILTER (WHERE status = 'completed') as completed,
                   COUNT(*) FILTER (WHERE status = 'failed') as failed
            FROM tasks
            WHERE created_at BETWEEN $1 AND $2
            GROUP BY DATE(created_at)
            ORDER BY date
        """, start_date, end_date)

        type_distribution = await self.db_service.execute_read("""
            SELECT task_type, COUNT(*) as count
            FROM tasks
            WHERE created_at BETWEEN $1 AND $2
            GROUP BY task_type
            ORDER BY count DESC
        """, start_date, end_date)

        avg_completion_time = await self.db_service.fetchval_read("""
            SELECT AVG(EXTRACT(EPOCH FROM (completed_at - created_at)))
            FROM tasks
            WHERE status = 'completed' 
              AND created_at BETWEEN $1 AND $2
              AND completed_at IS NOT NULL
        """, start_date, end_date)

        result = {
            "daily_tasks": [dict(d) for d in daily_tasks] if daily_tasks else [],
            "type_distribution": [dict(t) for t in type_distribution] if type_distribution else [],
            "avg_completion_time_seconds": float(avg_completion_time) if avg_completion_time else 0
        }

        await self._set_cached(cache_key, result, ttl=300)
        return result

    async def get_agent_stats(
        self, 
        start_date: datetime = None, 
        end_date: datetime = None
    ) -> Dict[str, Any]:
        """获取智能体统计"""
        start_date = start_date or datetime.utcnow() - timedelta(days=30)
        end_date = end_date or datetime.utcnow()

        cache_key = f"{self._cache_prefix}agents:{start_date.date()}:{end_date.date()}"
        cached = await self._get_cached(cache_key)
        if cached:
            return cached

        if not self.db_service:
            return {}

        agent_performance = await self.db_service.execute_read("""
            SELECT 
                a.id, a.name, a.agent_type,
                COUNT(t.id) as total_tasks,
                COUNT(t.id) FILTER (WHERE t.status = 'completed') as completed_tasks,
                AVG(EXTRACT(EPOCH FROM (t.completed_at - t.created_at))) FILTER (
                    WHERE t.status = 'completed'
                ) as avg_completion_time
            FROM agent_registry a
            LEFT JOIN tasks t ON a.id = t.agent_id AND t.created_at BETWEEN $1 AND $2
            GROUP BY a.id, a.name, a.agent_type
            ORDER BY total_tasks DESC
        """, start_date, end_date)

        status_distribution = await self.db_service.execute_read("""
            SELECT status, COUNT(*) as count
            FROM agent_registry
            GROUP BY status
        """)

        result = {
            "agent_performance": [dict(a) for a in agent_performance] if agent_performance else [],
            "status_distribution": [dict(s) for s in status_distribution] if status_distribution else []
        }

        await self._set_cached(cache_key, result, ttl=300)
        return result

    async def export_report(
        self, 
        report_type: str, 
        format: str = "json",
        start_date: datetime = None,
        end_date: datetime = None
    ) -> str:
        """导出报表"""
        if report_type == "users":
            data = await self.get_user_stats(start_date, end_date)
        elif report_type == "tasks":
            data = await self.get_task_stats(start_date, end_date)
        elif report_type == "agents":
            data = await self.get_agent_stats(start_date, end_date)
        else:
            data = await self.get_overview_stats()

        if format == "json":
            return json.dumps(data, default=str, ensure_ascii=False)
        elif format == "csv":
            return self._to_csv(data, report_type)
        else:
            return json.dumps(data, default=str, ensure_ascii=False)

    async def _get_cached(self, key: str) -> Optional[Dict]:
        """获取缓存"""
        if self.redis_client:
            try:
                cached = await self.redis_client.get(key)
                if cached:
                    return json.loads(cached)
            except Exception as e:
                logger.warning(f"Redis cache get error: {e}")
        return None

    async def _set_cached(self, key: str, value: Dict, ttl: int = 300):
        """设置缓存"""
        if self.redis_client:
            try:
                await self.redis_client.setex(key, ttl, json.dumps(value, default=str))
            except Exception as e:
                logger.warning(f"Redis cache set error: {e}")

    def _default_overview(self) -> Dict[str, Any]:
        """默认总览数据"""
        return {
            "users": {"total_users": 0, "active_users": 0, "new_users_today": 0},
            "tasks": {"total_tasks": 0, "completed_tasks": 0, "running_tasks": 0, "failed_tasks": 0},
            "agents": {"total_agents": 0, "running_agents": 0, "stopped_agents": 0}
        }

    def _to_csv(self, data: Dict, report_type: str) -> str:
        """转换为CSV"""
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        for key, value in data.items():
            if isinstance(value, list) and value:
                writer.writerow([key])
                if isinstance(value[0], dict):
                    writer.writerow(value[0].keys())
                    for item in value:
                        writer.writerow(item.values())
                else:
                    writer.writerow(value)
                writer.writerow([])

        return output.getvalue()


class ConfigService:
    """配置管理服务 - 提示词11"""

    def __init__(self, db_service=None, redis_client=None):
        self.db_service = db_service
        self.redis_client = redis_client
        self._config_cache: Dict[str, Any] = {}
        self._change_callbacks: Dict[str, List[Callable]] = {}

    async def get_all_configs(self) -> List[Dict[str, Any]]:
        """获取所有配置"""
        if not self.db_service:
            return []

        configs = await self.db_service.execute_read("""
            SELECT key, value, value_type, description, is_public,
                   updated_at, updated_by
            FROM admin_configs
            ORDER BY key
        """)
        return [self._parse_config(dict(c)) for c in configs] if configs else []

    async def get_config(self, key: str) -> Optional[Dict[str, Any]]:
        """获取单个配置"""
        if key in self._config_cache:
            return self._config_cache[key]

        if not self.db_service:
            return None

        config = await self.db_service.fetchrow_read("""
            SELECT key, value, value_type, description, is_public,
                   updated_at, updated_by
            FROM admin_configs
            WHERE key = $1
        """, key)

        if not config:
            return None

        result = self._parse_config(dict(config))
        self._config_cache[key] = result
        return result

    async def get_config_value(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        config = await self.get_config(key)
        if config:
            return config.get("parsed_value", config.get("value"))
        return default

    async def set_config(
        self, 
        key: str, 
        value: Any, 
        admin_id: str,
        value_type: str = "string",
        description: str = None,
        is_public: bool = False
    ) -> Dict[str, Any]:
        """设置配置"""
        if not self.db_service:
            raise ValueError("Database service not available")

        if value_type == "json":
            value_str = json.dumps(value)
        else:
            value_str = str(value)

        await self.db_service.execute_write("""
            INSERT INTO admin_configs (key, value, value_type, description, is_public, updated_at, updated_by)
            VALUES ($1, $2, $3, $4, $5, CURRENT_TIMESTAMP, $6)
            ON CONFLICT (key)
            DO UPDATE SET 
                value = $2, 
                value_type = $3,
                description = COALESCE($4, admin_configs.description),
                is_public = $5,
                updated_at = CURRENT_TIMESTAMP, 
                updated_by = $6
        """, key, value_str, value_type, description, is_public, admin_id)

        await self._publish_config_change(key, value)

        self._config_cache.pop(key, None)

        return await self.get_config(key)

    async def delete_config(self, key: str, admin_id: str) -> bool:
        """删除配置"""
        if not self.db_service:
            return False

        old_config = await self.get_config(key)
        if not old_config:
            return False

        await self.db_service.execute_write("""
            DELETE FROM admin_configs WHERE key = $1
        """, key)

        await self._publish_config_change(key, None, deleted=True)

        self._config_cache.pop(key, None)

        return True

    async def reload_configs(self) -> Dict[str, Any]:
        """重新加载所有配置"""
        self._config_cache.clear()
        configs = await self.get_all_configs()

        for config in configs:
            self._config_cache[config["key"]] = config

        await self._publish_reload_event()

        return {"reloaded": len(configs), "configs": [c["key"] for c in configs]}

    def register_change_callback(self, key: str, callback: Callable):
        """注册配置变更回调"""
        if key not in self._change_callbacks:
            self._change_callbacks[key] = []
        self._change_callbacks[key].append(callback)

    def unregister_change_callback(self, key: str, callback: Callable):
        """取消注册配置变更回调"""
        if key in self._change_callbacks:
            try:
                self._change_callbacks[key].remove(callback)
            except ValueError:
                pass

    async def _publish_config_change(self, key: str, value: Any, deleted: bool = False):
        """发布配置变更事件"""
        event = {
            "key": key,
            "value": value,
            "deleted": deleted,
            "timestamp": datetime.utcnow().isoformat()
        }

        if self.redis_client:
            try:
                await self.redis_client.publish("config:changes", json.dumps(event))
            except Exception as e:
                logger.warning(f"Redis publish error: {e}")

        if key in self._change_callbacks:
            for callback in self._change_callbacks[key]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(key, value, deleted)
                    else:
                        callback(key, value, deleted)
                except Exception as e:
                    logger.error(f"Config change callback error: {e}")

    async def _publish_reload_event(self):
        """发布配置重载事件"""
        if self.redis_client:
            try:
                await self.redis_client.publish("config:reload", json.dumps({
                    "timestamp": datetime.utcnow().isoformat()
                }))
            except Exception as e:
                logger.warning(f"Redis publish reload error: {e}")

    def _parse_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """解析配置值"""
        value_type = config.get("value_type", "string")
        value = config.get("value")

        try:
            if value_type == "int":
                config["parsed_value"] = int(value)
            elif value_type == "float":
                config["parsed_value"] = float(value)
            elif value_type == "bool":
                config["parsed_value"] = str(value).lower() in ("true", "1", "yes")
            elif value_type == "json":
                config["parsed_value"] = json.loads(value)
            else:
                config["parsed_value"] = value
        except Exception as e:
            logger.warning(f"Config parse error for {config.get('key')}: {e}")
            config["parsed_value"] = value

        return config


user_service: Optional[UserService] = None
agent_monitor_service: Optional[AgentMonitorService] = None
statistics_service: Optional[StatisticsService] = None
config_service: Optional[ConfigService] = None


async def get_user_service() -> UserService:
    global user_service
    if user_service is None:
        from ..database.high_performance_db import get_db_service
        db = await get_db_service()
        user_repo = UserRepository(db)
        user_service = UserService(user_repo)
    return user_service


async def get_agent_monitor_service() -> AgentMonitorService:
    global agent_monitor_service
    if agent_monitor_service is None:
        from ..database.high_performance_db import get_db_service
        db = await get_db_service()
        agent_monitor_service = AgentMonitorService(db)
    return agent_monitor_service


async def get_statistics_service() -> StatisticsService:
    global statistics_service
    if statistics_service is None:
        from ..database.high_performance_db import get_db_service
        db = await get_db_service()
        statistics_service = StatisticsService(db)
    return statistics_service


async def get_config_service() -> ConfigService:
    global config_service
    if config_service is None:
        from ..database.high_performance_db import get_db_service
        db = await get_db_service()
        config_service = ConfigService(db)
    return config_service
