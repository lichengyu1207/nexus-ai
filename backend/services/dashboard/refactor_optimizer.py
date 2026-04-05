# -*- coding: utf-8 -*-
"""
仪表盘代码重构与优化模块 - 提示词13-15
重构仪表盘后端代码结构、优化数据库查询性能、前端组件拆分与状态管理优化
"""
import asyncio
import json
import logging
import os
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, TypeVar, Generic, Callable
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

T = TypeVar('T')


class DashboardException(Exception):
    """仪表盘基础异常"""
    def __init__(self, message: str, code: str = "DASHBOARD_ERROR", details: Dict = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


class DatabaseException(DashboardException):
    """数据库异常"""
    def __init__(self, message: str, query: str = None):
        super().__init__(message, "DATABASE_ERROR", {"query": query})


class CacheException(DashboardException):
    """缓存异常"""
    def __init__(self, message: str, key: str = None):
        super().__init__(message, "CACHE_ERROR", {"key": key})


class ValidationException(DashboardException):
    """验证异常"""
    def __init__(self, message: str, field: str = None):
        super().__init__(message, "VALIDATION_ERROR", {"field": field})


class NotFoundException(DashboardException):
    """资源未找到异常"""
    def __init__(self, resource: str, resource_id: str = None):
        super().__init__(f"{resource}未找到", "NOT_FOUND", {"resource": resource, "id": resource_id})


@dataclass
class QueryResult(Generic[T]):
    """查询结果封装"""
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    duration_ms: float = 0.0
    rows_affected: int = 0


class BaseDAO(ABC):
    """数据访问层基类 - 提示词13"""

    def __init__(self, db=None):
        self.db = db
        self._query_count = 0
        self._total_time_ms = 0.0

    @asynccontextmanager
    async def get_connection(self):
        """获取数据库连接"""
        if self.db:
            yield self.db
        else:
            from backend.database_pg import get_db
            async with get_db() as conn:
                yield conn

    async def execute_query(
        self,
        query: str,
        params: tuple = None,
        fetch: str = "all"
    ) -> QueryResult:
        """执行查询"""
        start_time = time.time()
        self._query_count += 1
        
        try:
            async with self.get_connection() as db:
                if fetch == "val":
                    result = await db.fetchval(query, *params) if params else await db.fetchval(query)
                elif fetch == "row":
                    result = await db.fetchrow(query, *params) if params else await db.fetchrow(query)
                else:
                    result = await db.fetch(query, *params) if params else await db.fetch(query)
                
                duration = (time.time() - start_time) * 1000
                self._total_time_ms += duration
                
                if duration > 1000:
                    logger.warning(f"慢查询 ({duration:.2f}ms): {query[:100]}")
                
                return QueryResult(
                    success=True,
                    data=result,
                    duration_ms=duration
                )
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            logger.error(f"查询失败: {str(e)}")
            return QueryResult(
                success=False,
                error=str(e),
                duration_ms=duration
            )

    async def execute_insert(
        self,
        query: str,
        params: tuple = None
    ) -> QueryResult:
        """执行插入"""
        return await self.execute_query(query, params, fetch="val")

    async def execute_update(
        self,
        query: str,
        params: tuple = None
    ) -> QueryResult:
        """执行更新"""
        start_time = time.time()
        
        try:
            async with self.get_connection() as db:
                result = await db.execute(query, *params) if params else await db.execute(query)
                
                duration = (time.time() - start_time) * 1000
                
                return QueryResult(
                    success=True,
                    duration_ms=duration,
                    rows_affected=result.split()[-1] if result else 0
                )
        except Exception as e:
            return QueryResult(success=False, error=str(e))

    def get_stats(self) -> Dict[str, Any]:
        """获取查询统计"""
        return {
            "query_count": self._query_count,
            "total_time_ms": round(self._total_time_ms, 2),
            "avg_time_ms": round(self._total_time_ms / self._query_count, 2) if self._query_count > 0 else 0
        }


class UserDAO(BaseDAO):
    """用户数据访问"""

    async def get_user_by_id(self, user_id: str) -> QueryResult:
        """根据ID获取用户"""
        return await self.execute_query(
            "SELECT * FROM users WHERE id = $1",
            (user_id,),
            fetch="row"
        )

    async def get_user_count(self) -> QueryResult:
        """获取用户总数"""
        return await self.execute_query(
            "SELECT COUNT(*) FROM users",
            fetch="val"
        )

    async def get_active_users_today(self) -> QueryResult:
        """获取今日活跃用户"""
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        return await self.execute_query(
            "SELECT COUNT(DISTINCT user_id) FROM user_sessions WHERE last_activity >= $1",
            (today_start,),
            fetch="val"
        )


class TaskDAO(BaseDAO):
    """任务数据访问"""

    async def get_task_list(
        self,
        user_id: str = None,
        status: str = None,
        limit: int = 20,
        offset: int = 0,
        sort_by: str = "created_at",
        order: str = "DESC"
    ) -> QueryResult:
        """获取任务列表"""
        conditions = []
        params = []
        param_idx = 1
        
        if user_id:
            conditions.append(f"user_id = ${param_idx}")
            params.append(user_id)
            param_idx += 1
        
        if status:
            conditions.append(f"status = ${param_idx}")
            params.append(status)
            param_idx += 1
        
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        
        valid_sorts = {"created_at", "updated_at", "status", "task_type"}
        sort_col = sort_by if sort_by in valid_sorts else "created_at"
        order_dir = order if order.upper() in ("ASC", "DESC") else "DESC"
        
        query = f"""
            SELECT * FROM user_tasks
            {where_clause}
            ORDER BY {sort_col} {order_dir}
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """
        params.extend([limit, offset])
        
        return await self.execute_query(query, tuple(params), fetch="all")

    async def get_task_stats(self) -> QueryResult:
        """获取任务统计"""
        return await self.execute_query("""
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE status = 'completed') as completed,
                COUNT(*) FILTER (WHERE status IN ('pending', 'processing')) as pending
            FROM user_tasks
        """, fetch="row")


class ReportDAO(BaseDAO):
    """报告数据访问"""

    async def get_latest_reports(self, limit: int = 10) -> QueryResult:
        """获取最新报告"""
        return await self.execute_query(
            "SELECT * FROM reports ORDER BY created_at DESC LIMIT $1",
            (limit,),
            fetch="all"
        )

    async def get_report_stats(self) -> QueryResult:
        """获取报告统计"""
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        return await self.execute_query("""
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE created_at >= $1) as today
            FROM reports
        """, (today_start,), fetch="row")


class BaseService(ABC):
    """服务层基类"""

    def __init__(self, dao: BaseDAO = None):
        self.dao = dao

    @abstractmethod
    async def get_data(self, *args, **kwargs) -> Any:
        """获取数据"""
        pass

    def handle_error(self, error: Exception, context: Dict = None) -> Dict:
        """统一错误处理"""
        if isinstance(error, DashboardException):
            return {
                "success": False,
                "error": error.code,
                "message": error.message,
                "details": error.details
            }
        
        logger.error(f"服务错误: {str(error)}", extra=context or {})
        return {
            "success": False,
            "error": "INTERNAL_ERROR",
            "message": "内部服务错误"
        }


class StatisticsService(BaseService):
    """统计服务 - 提示词13"""

    def __init__(self):
        super().__init__()
        self.user_dao = UserDAO()
        self.task_dao = TaskDAO()
        self.report_dao = ReportDAO()

    async def get_data(self, user_id: str = None) -> Dict[str, Any]:
        """获取仪表盘统计数据"""
        try:
            user_count = await self.user_dao.get_user_count()
            active_users = await self.user_dao.get_active_users_today()
            task_stats = await self.task_dao.get_task_stats()
            report_stats = await self.report_dao.get_report_stats()
            
            return {
                "success": True,
                "data": {
                    "users": {
                        "total": user_count.data or 0,
                        "active_today": active_users.data or 0
                    },
                    "tasks": {
                        "total": task_stats.data.get("total", 0) if task_stats.data else 0,
                        "completed": task_stats.data.get("completed", 0) if task_stats.data else 0,
                        "pending": task_stats.data.get("pending", 0) if task_stats.data else 0
                    },
                    "reports": {
                        "total": report_stats.data.get("total", 0) if report_stats.data else 0,
                        "today": report_stats.data.get("today", 0) if report_stats.data else 0
                    }
                }
            }
        except Exception as e:
            return self.handle_error(e, {"user_id": user_id})

    async def get_user_stats(self) -> Dict[str, Any]:
        """获取用户统计"""
        try:
            total = await self.user_dao.get_user_count()
            active = await self.user_dao.get_active_users_today()
            
            return {
                "success": True,
                "data": {
                    "total_users": total.data or 0,
                    "active_users_today": active.data or 0
                }
            }
        except Exception as e:
            return self.handle_error(e)

    async def get_task_stats(self) -> Dict[str, Any]:
        """获取任务统计"""
        try:
            result = await self.task_dao.get_task_stats()
            
            if result.success and result.data:
                total = result.data.get("total", 0)
                completed = result.data.get("completed", 0)
                rate = (completed / total * 100) if total > 0 else 0
                
                return {
                    "success": True,
                    "data": {
                        "total_tasks": total,
                        "completed_tasks": completed,
                        "pending_tasks": result.data.get("pending", 0),
                        "completion_rate": round(rate, 2)
                    }
                }
            
            return {"success": False, "error": "获取任务统计失败"}
        except Exception as e:
            return self.handle_error(e)


class TaskService(BaseService):
    """任务服务"""

    def __init__(self):
        super().__init__(TaskDAO())

    async def get_data(self, user_id: str = None, page: int = 1, page_size: int = 20) -> Dict:
        """获取任务列表"""
        try:
            offset = (page - 1) * page_size
            result = await self.dao.get_task_list(user_id=user_id, limit=page_size, offset=offset)
            
            if result.success:
                return {
                    "success": True,
                    "data": result.data or [],
                    "page": page,
                    "page_size": page_size
                }
            
            return {"success": False, "error": result.error}
        except Exception as e:
            return self.handle_error(e, {"user_id": user_id})

    async def validate_pagination(self, page: int, page_size: int, total: int) -> Dict:
        """验证分页参数"""
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        
        return {
            "current_page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "is_valid": 1 <= page <= total_pages if total_pages > 0 else page == 1
        }


class QueryOptimizer:
    """查询优化器 - 提示词14"""

    def __init__(self):
        self.slow_queries: List[Dict] = []
        self.suggestions: List[str] = []

    async def analyze_query(self, query: str, db) -> Dict:
        """分析查询执行计划"""
        try:
            explain_result = await db.fetch(f"EXPLAIN ANALYZE {query}")
            
            plan_text = "\n".join([row["QUERY PLAN"] for row in explain_result])
            
            analysis = {
                "query": query[:200],
                "plan": plan_text[:500],
                "issues": [],
                "suggestions": []
            }
            
            if "Seq Scan" in plan_text:
                analysis["issues"].append("全表扫描")
                analysis["suggestions"].append("考虑添加索引")
            
            if "Hash Join" in plan_text and "Hash Cond" in plan_text:
                analysis["issues"].append("Hash连接")
                analysis["suggestions"].append("检查连接条件是否有索引")
            
            if "Sort" in plan_text:
                analysis["issues"].append("排序操作")
                analysis["suggestions"].append("考虑添加排序字段索引")
            
            return analysis
        except Exception as e:
            return {"error": str(e), "query": query[:100]}

    async def suggest_indexes(self, table: str, db) -> List[Dict]:
        """建议索引"""
        try:
            existing = await db.fetch("""
                SELECT indexname, indexdef 
                FROM pg_indexes 
                WHERE tablename = $1
            """, table)
            
            existing_cols = set()
            for idx in existing:
                if "(" in idx["indexdef"]:
                    cols = idx["indexdef"].split("(")[1].rstrip(")").split(",")
                    for col in cols:
                        existing_cols.add(col.strip().lower())
            
            suggestions = []
            
            common_indexes = [
                ("created_at", "时间排序", f"CREATE INDEX idx_{table}_created ON {table}(created_at DESC)"),
                ("updated_at", "更新时间", f"CREATE INDEX idx_{table}_updated ON {table}(updated_at DESC)"),
                ("user_id", "用户关联", f"CREATE INDEX idx_{table}_user ON {table}(user_id)"),
                ("status", "状态筛选", f"CREATE INDEX idx_{table}_status ON {table}(status)")
            ]
            
            for col, reason, sql in common_indexes:
                if col not in existing_cols:
                    suggestions.append({
                        "column": col,
                        "reason": reason,
                        "sql": sql
                    })
            
            return suggestions
        except Exception as e:
            logger.error(f"索引建议失败: {e}")
            return []

    async def check_materialized_views(self, db) -> List[Dict]:
        """检查物化视图"""
        try:
            views = await db.fetch("""
                SELECT schemaname, matviewname, definition
                FROM pg_matviews
                WHERE schemaname = 'public'
            """)
            
            return [
                {
                    "name": v["matviewname"],
                    "definition": v["definition"][:200]
                }
                for v in views
            ]
        except Exception:
            return []

    async def suggest_materialized_views(self) -> List[Dict]:
        """建议物化视图"""
        return [
            {
                "name": "mv_dashboard_stats",
                "purpose": "仪表盘统计汇总",
                "definition": """
                    CREATE MATERIALIZED VIEW mv_dashboard_stats AS
                    SELECT 
                        DATE(created_at) as stat_date,
                        COUNT(*) as total_tasks,
                        COUNT(*) FILTER (WHERE status = 'completed') as completed_tasks
                    FROM user_tasks
                    GROUP BY DATE(created_at)
                """,
                "refresh": "REFRESH MATERIALIZED VIEW mv_dashboard_stats"
            },
            {
                "name": "mv_user_activity",
                "purpose": "用户活动汇总",
                "definition": """
                    CREATE MATERIALIZED VIEW mv_user_activity AS
                    SELECT 
                        user_id,
                        DATE(created_at) as activity_date,
                        COUNT(*) as task_count
                    FROM user_tasks
                    GROUP BY user_id, DATE(created_at)
                """,
                "refresh": "REFRESH MATERIALIZED VIEW mv_user_activity"
            }
        ]


class FrontendOptimizer:
    """前端优化器 - 提示词15"""

    def __init__(self):
        self.component_suggestions: List[Dict] = []
        self.state_suggestions: List[Dict] = []

    def analyze_component_structure(self, components: List[str]) -> Dict:
        """分析组件结构"""
        large_components = [c for c in components if len(c) > 500]
        
        return {
            "total_components": len(components),
            "large_components": len(large_components),
            "suggestions": [
                f"拆分大型组件: {c[:50]}..." for c in large_components[:3]
            ] if large_components else ["组件大小合理"]
        }

    def suggest_component_split(self, component_name: str) -> List[Dict]:
        """建议组件拆分"""
        splits = {
            "Dashboard": [
                {"name": "StatisticsPanel", "purpose": "统计面板"},
                {"name": "TaskList", "purpose": "任务列表"},
                {"name": "MemoryTrend", "purpose": "记忆趋势图"},
                {"name": "AgentStatus", "purpose": "智能体状态"}
            ],
            "StatisticsPanel": [
                {"name": "UserStats", "purpose": "用户统计"},
                {"name": "TaskStats", "purpose": "任务统计"},
                {"name": "ReportStats", "purpose": "报告统计"}
            ],
            "TaskList": [
                {"name": "TaskFilter", "purpose": "任务筛选"},
                {"name": "TaskItem", "purpose": "任务项"},
                {"name": "TaskPagination", "purpose": "分页控制"}
            ]
        }
        
        return splits.get(component_name, [])

    def suggest_state_management(self) -> Dict:
        """建议状态管理"""
        return {
            "store_structure": {
                "dashboard": {
                    "state": ["stats", "tasks", "reports", "memories"],
                    "actions": ["fetchStats", "fetchTasks", "refreshData"],
                    "getters": ["getStatsByRange", "getFilteredTasks"]
                }
            },
            "caching_strategy": {
                "local": ["user_preferences", "ui_state"],
                "session": ["dashboard_stats", "recent_tasks"],
                "api": ["historical_data", "reports"]
            },
            "optimization": [
                "使用computed属性缓存计算结果",
                "使用watch进行数据同步",
                "使用debounce处理频繁更新",
                "使用虚拟滚动优化长列表"
            ]
        }

    def generate_virtual_scroll_config(self, item_height: int = 60, visible_count: int = 20) -> Dict:
        """生成虚拟滚动配置"""
        return {
            "item_height": item_height,
            "visible_count": visible_count,
            "buffer_count": 5,
            "total_height": f"itemHeight * totalItems",
            "implementation": """
                <VirtualList
                    :items="tasks"
                    :item-height="60"
                    :buffer="5"
                >
                    <template #default="{ item }">
                        <TaskItem :task="item" />
                    </template>
                </VirtualList>
            """
        }


async def run_refactor_analysis() -> Dict[str, Any]:
    """运行重构分析"""
    stats_service = StatisticsService()
    task_service = TaskService()
    
    optimizer = QueryOptimizer()
    frontend_optimizer = FrontendOptimizer()
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "architecture": {
            "layers": ["Controller", "Service", "DAO"],
            "exception_handling": "DashboardException hierarchy",
            "type_annotations": "Python 3.10+ typing"
        },
        "services": {
            "statistics": stats_service.__class__.__name__,
            "tasks": task_service.__class__.__name__
        },
        "optimization_suggestions": {
            "query": {
                "index_suggestions": "见QueryOptimizer.suggest_indexes()",
                "materialized_views": "见QueryOptimizer.suggest_materialized_views()"
            },
            "frontend": {
                "component_split": frontend_optimizer.suggest_component_split("Dashboard"),
                "state_management": frontend_optimizer.suggest_state_management()
            }
        }
    }


if __name__ == "__main__":
    async def main():
        print("=" * 60)
        print("仪表盘代码重构与优化分析")
        print("=" * 60)
        
        report = await run_refactor_analysis()
        print(json.dumps(report, indent=2, ensure_ascii=False))
    
    asyncio.run(main())
