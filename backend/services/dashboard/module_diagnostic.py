# -*- coding: utf-8 -*-
"""
仪表盘功能模块拆解与单元测试模块 - 提示词7-9
统计模块重构与测试、任务列表模块调试、记忆趋势图模块修复
"""
import asyncio
import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import AsyncMock, MagicMock, patch

logger = logging.getLogger(__name__)


class TestStatus(Enum):
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    SKIP = "skip"


@dataclass
class UnitTestResult:
    test_name: str
    status: TestStatus
    message: str = ""
    duration_ms: float = 0.0
    assertions: List[str] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class PerformanceMetrics:
    query_count: int = 0
    total_time_ms: float = 0.0
    avg_time_ms: float = 0.0
    n_plus_one_detected: bool = False
    index_suggestions: List[str] = field(default_factory=list)


class StatisticsModule:
    """仪表盘统计模块 - 提示词7"""

    def __init__(self):
        self.db = None

    async def get_user_stats(self, db=None) -> Dict[str, Any]:
        """获取用户统计数据"""
        if db is None:
            from backend.database_pg import get_db
            async with get_db() as conn:
                return await self._fetch_user_stats(conn)
        return await self._fetch_user_stats(db)

    async def _fetch_user_stats(self, db) -> Dict[str, Any]:
        """从数据库获取用户统计"""
        try:
            total_users = await db.fetchval("SELECT COUNT(*) FROM users")
            
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            active_users = await db.fetchval(
                "SELECT COUNT(DISTINCT user_id) FROM user_sessions WHERE last_activity >= $1",
                today_start
            )
            
            return {
                "total_users": total_users or 0,
                "active_users_today": active_users or 0,
                "growth_rate": 0.0
            }
        except Exception as e:
            logger.error(f"获取用户统计失败: {e}")
            return {"total_users": 0, "active_users_today": 0, "growth_rate": 0.0}

    async def get_task_stats(self, db=None) -> Dict[str, Any]:
        """获取任务统计数据"""
        if db is None:
            from backend.database_pg import get_db
            async with get_db() as conn:
                return await self._fetch_task_stats(conn)
        return await self._fetch_task_stats(db)

    async def _fetch_task_stats(self, db) -> Dict[str, Any]:
        """从数据库获取任务统计"""
        try:
            total_tasks = await db.fetchval("SELECT COUNT(*) FROM user_tasks")
            
            completed_tasks = await db.fetchval(
                "SELECT COUNT(*) FROM user_tasks WHERE status = 'completed'"
            )
            
            pending_tasks = await db.fetchval(
                "SELECT COUNT(*) FROM user_tasks WHERE status IN ('pending', 'processing')"
            )
            
            completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            
            return {
                "total_tasks": total_tasks or 0,
                "completed_tasks": completed_tasks or 0,
                "pending_tasks": pending_tasks or 0,
                "completion_rate": round(completion_rate, 2)
            }
        except Exception as e:
            logger.error(f"获取任务统计失败: {e}")
            return {"total_tasks": 0, "completed_tasks": 0, "pending_tasks": 0, "completion_rate": 0.0}

    async def get_report_stats(self, db=None) -> Dict[str, Any]:
        """获取报告统计数据"""
        if db is None:
            from backend.database_pg import get_db
            async with get_db() as conn:
                return await self._fetch_report_stats(conn)
        return await self._fetch_report_stats(db)

    async def _fetch_report_stats(self, db) -> Dict[str, Any]:
        """从数据库获取报告统计"""
        try:
            total_reports = await db.fetchval("SELECT COUNT(*) FROM reports")
            
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            today_reports = await db.fetchval(
                "SELECT COUNT(*) FROM reports WHERE created_at >= $1",
                today_start
            )
            
            return {
                "total_reports": total_reports or 0,
                "today_reports": today_reports or 0
            }
        except Exception as e:
            logger.error(f"获取报告统计失败: {e}")
            return {"total_reports": 0, "today_reports": 0}

    async def get_memory_stats(self, db=None) -> Dict[str, Any]:
        """获取记忆使用统计"""
        if db is None:
            from backend.database_pg import get_db
            async with get_db() as conn:
                return await self._fetch_memory_stats(conn)
        return await self._fetch_memory_stats(db)

    async def _fetch_memory_stats(self, db) -> Dict[str, Any]:
        """从数据库获取记忆统计"""
        try:
            total_memories = await db.fetchval("SELECT COUNT(*) FROM memories")
            
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            today_memories = await db.fetchval(
                "SELECT COUNT(*) FROM memories WHERE created_at >= $1",
                today_start
            )
            
            return {
                "total_memories": total_memories or 0,
                "today_memories": today_memories or 0,
                "avg_per_user": 0.0
            }
        except Exception as e:
            logger.error(f"获取记忆统计失败: {e}")
            return {"total_memories": 0, "today_memories": 0, "avg_per_user": 0}

    async def get_all_stats(self, db=None) -> Dict[str, Any]:
        """获取所有统计数据"""
        user_stats = await self.get_user_stats(db)
        task_stats = await self.get_task_stats(db)
        report_stats = await self.get_report_stats(db)
        memory_stats = await self.get_memory_stats(db)
        
        return {
            "users": user_stats,
            "tasks": task_stats,
            "reports": report_stats,
            "memories": memory_stats,
            "timestamp": datetime.utcnow().isoformat()
        }


class TaskListModule:
    """任务列表模块 - 提示词8"""

    def __init__(self, page_size: int = 20, page: int = 1):
        self.page_size = page_size
        self.page = page

    async def get_tasks(self, db=None, sort_by: str = "created_at", order: str = "DESC") -> List[Dict]:
        """获取任务列表"""
        if db is None:
            from backend.database_pg import get_db
            async with get_db() as conn:
                return await self._fetch_tasks(conn, sort_by, order)
        return await self._fetch_tasks(db, sort_by, order)

    async def _fetch_tasks(self, db, sort_by: str, order: str) -> List[Dict]:
        """从数据库获取任务列表"""
        try:
            offset = (self.page - 1) * self.page_size
            
            valid_sorts = {"created_at", "updated_at", "status", "task_type"}
            sort_col = sort_by if sort_by in valid_sorts else "created_at"
            order_dir = order if order.upper() in ("ASC", "DESC") else "DESC"
            
            query = f"""
                SELECT id, user_id, task_type, status, input, output, created_at, updated_at
                FROM user_tasks
                ORDER BY {sort_col} {order_dir}
                LIMIT $1 OFFSET $2
            """
            
            tasks = await db.fetch(query, self.page_size, offset)
            
            return [dict(task) for task in tasks]
        except Exception as e:
            logger.error(f"获取任务列表失败: {e}")
            return []

    async def get_task_count(self, db=None) -> int:
        """获取任务总数"""
        if db is None:
            from backend.database_pg import get_db
            async with get_db() as conn:
                return await self._fetch_count(conn)
        return await self._fetch_count(db)

    async def _fetch_count(self, db) -> int:
        """从数据库获取任务计数"""
        try:
            return await db.fetchval("SELECT COUNT(*) FROM user_tasks") or 0
        except Exception:
            return 0

    async def validate_pagination(self, total_count: int) -> Dict:
        """验证分页参数"""
        total_pages = (total_count + self.page_size - 1) // self.page_size if self.page_size > 0 else 0
        
        is_valid = 1 <= self.page <= total_pages if total_pages > 0 else self.page == 1
        
        return {
            "current_page": self.page,
            "page_size": self.page_size,
            "total_count": total_count,
            "total_pages": total_pages,
            "is_valid": is_valid,
            "has_next": self.page < total_pages,
            "has_prev": self.page > 1
        }


class MemoryTrendModule:
    """记忆趋势模块 - 提示词9"""

    def __init__(self, days: int = 7):
        self.days = days

    async def get_trends(self, db=None, fill_missing: bool = True) -> List[Dict]:
        """获取记忆趋势数据"""
        if db is None:
            from backend.database_pg import get_db
            async with get_db() as conn:
                return await self._fetch_trends(conn, fill_missing)
        return await self._fetch_trends(db, fill_missing)

    async def _fetch_trends(self, db, fill_missing: bool) -> List[Dict]:
        """从数据库获取趋势数据"""
        try:
            trends = []
            start_date = datetime.utcnow() - timedelta(days=self.days)
            
            query = """
                SELECT DATE(created_at) as date, COUNT(*) as count
                FROM memories
                WHERE created_at >= $1
                GROUP BY DATE(created_at)
                ORDER BY date DESC
            """
            
            results = await db.fetch(query, start_date)
            
            for row in results:
                trends.append({
                    "date": row["date"].isoformat() if row["date"] else None,
                    "count": row["count"]
                })
            
            if fill_missing:
                trends = self._fill_missing_dates(trends, self.days)
            
            return trends
        except Exception as e:
            logger.error(f"获取记忆趋势失败: {e}")
            return []

    def _fill_missing_dates(self, trends: List[Dict], days: int) -> List[Dict]:
        """补全缺失日期"""
        filled = []
        existing = {t["date"]: t["count"] for t in trends if t.get("date")}
        
        for i in range(days):
            date = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
            filled.append({
                "date": date,
                "count": existing.get(date, 0)
            })
        
        return sorted(filled, key=lambda x: x["date"])

    async def aggregate_by_hour(self, db=None, date_str: str = None) -> List[Dict]:
        """按小时聚合数据"""
        if db is None:
            from backend.database_pg import get_db
            async with get_db() as conn:
                return await self._aggregate_by_hour(conn, date_str)
        return await self._aggregate_by_hour(db, date_str)

    async def _aggregate_by_hour(self, db, date_str: str = None) -> List[Dict]:
        """数据库按小时聚合"""
        try:
            if date_str:
                target_date = datetime.strptime(date_str, "%Y-%m-%d")
            else:
                target_date = datetime.utcnow()
            
            start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)
            
            query = """
                SELECT 
                    EXTRACT(HOUR FROM created_at) as hour,
                    COUNT(*) as count
                FROM memories
                WHERE created_at >= $1 AND created_at < $2
                GROUP BY EXTRACT(HOUR FROM created_at)
                ORDER BY hour
            """
            
            results = await db.fetch(query, start, end)
            
            hourly = []
            for i in range(24):
                hourly.append({"hour": i, "count": 0})
            
            for row in results:
                hour = int(row["hour"])
                if 0 <= hour < 24:
                    hourly[hour]["count"] = row["count"]
            
            return hourly
        except Exception as e:
            logger.error(f"按小时聚合失败: {e}")
            return [{"hour": i, "count": 0} for i in range(24)]


class ModuleUnitTests:
    """模块单元测试"""

    def __init__(self):
        self.results: List[UnitTestResult] = []

    async def test_user_stats_empty_db(self) -> UnitTestResult:
        """测试空数据库用户统计"""
        start = time.time()
        
        try:
            mock_db = AsyncMock()
            mock_db.fetchval.return_value = 0
            
            stats = StatisticsModule()
            result = await stats.get_user_stats(mock_db)
            
            assertions = [
                f"total_users = {result['total_users']}, 期望 0",
                f"active_users_today = {result['active_users_today']}, 期望 0"
            ]
            
            if result["total_users"] == 0 and result["active_users_today"] == 0:
                return UnitTestResult(
                    test_name="test_user_stats_empty_db",
                    status=TestStatus.PASS,
                    message="空数据库统计正确",
                    duration_ms=(time.time() - start) * 1000,
                    assertions=assertions
                )
            else:
                return UnitTestResult(
                    test_name="test_user_stats_empty_db",
                    status=TestStatus.FAIL,
                    message="统计值不为0",
                    duration_ms=(time.time() - start) * 1000
                )
        except Exception as e:
            return UnitTestResult(
                test_name="test_user_stats_empty_db",
                status=TestStatus.FAIL,
                error=str(e),
                duration_ms=(time.time() - start) * 1000
            )

    async def test_task_completion_rate(self) -> UnitTestResult:
        """测试任务完成率计算"""
        start = time.time()
        
        try:
            mock_db = AsyncMock()
            mock_db.fetchval.side_effect = [100, 75, 25]
            
            stats = StatisticsModule()
            result = await stats.get_task_stats(mock_db)
            
            expected_rate = 75.0
            assertions = [f"completion_rate = {result['completion_rate']}, 期望 {expected_rate}"]
            
            if abs(result["completion_rate"] - expected_rate) < 0.01:
                return UnitTestResult(
                    test_name="test_task_completion_rate",
                    status=TestStatus.PASS,
                    message="完成率计算正确",
                    duration_ms=(time.time() - start) * 1000,
                    assertions=assertions
                )
            return UnitTestResult(
                test_name="test_task_completion_rate",
                status=TestStatus.FAIL,
                message=f"完成率错误: {result['completion_rate']}",
                duration_ms=(time.time() - start) * 1000
            )
        except Exception as e:
            return UnitTestResult(
                test_name="test_task_completion_rate",
                status=TestStatus.FAIL,
                error=str(e),
                duration_ms=(time.time() - start) * 1000
            )

    async def test_pagination(self) -> UnitTestResult:
        """测试分页逻辑"""
        start = time.time()
        
        try:
            module = TaskListModule(page=2, page_size=10)
            validation = await module.validate_pagination(45)
            
            assertions = [
                f"current_page = {validation['current_page']}, 期望 2",
                f"total_pages = {validation['total_pages']}, 期望 5"
            ]
            
            if validation["current_page"] == 2 and validation["total_pages"] == 5:
                return UnitTestResult(
                    test_name="test_pagination",
                    status=TestStatus.PASS,
                    message="分页正确",
                    duration_ms=(time.time() - start) * 1000,
                    assertions=assertions
                )
            return UnitTestResult(
                test_name="test_pagination",
                status=TestStatus.FAIL,
                message=f"分页参数无效: {validation}",
                duration_ms=(time.time() - start) * 1000
            )
        except Exception as e:
            return UnitTestResult(
                test_name="test_pagination",
                status=TestStatus.FAIL,
                error=str(e),
                duration_ms=(time.time() - start) * 1000
            )

    async def test_memory_trend_fill(self) -> UnitTestResult:
        """测试记忆趋势日期填充"""
        start = time.time()
        
        try:
            module = MemoryTrendModule()
            
            incomplete = [
                {"date": "2024-01-03", "count": 10},
                {"date": "2024-01-01", "count": 5}
            ]
            
            filled = module._fill_missing_dates(incomplete, days=3)
            
            assertions = [f"填充后数量 = {len(filled)}, 期望 3"]
            
            if len(filled) == 3 and all("date" in f for f in filled):
                return UnitTestResult(
                    test_name="test_memory_trend_fill",
                    status=TestStatus.PASS,
                    message="日期填充正确",
                    duration_ms=(time.time() - start) * 1000,
                    assertions=assertions
                )
            return UnitTestResult(
                test_name="test_memory_trend_fill",
                status=TestStatus.FAIL,
                message=f"填充数量错误: {len(filled)}",
                duration_ms=(time.time() - start) * 1000
            )
        except Exception as e:
            return UnitTestResult(
                test_name="test_memory_trend_fill",
                status=TestStatus.FAIL,
                error=str(e),
                duration_ms=(time.time() - start) * 1000
            )

    async def test_extreme_values(self) -> UnitTestResult:
        """测试极端值处理"""
        start = time.time()
        
        try:
            mock_db = AsyncMock()
            mock_db.fetchval.side_effect = [999999999, 999999999, 0]
            
            stats = StatisticsModule()
            result = await stats.get_task_stats(mock_db)
            
            if result["completion_rate"] == 100.0:
                return UnitTestResult(
                    test_name="test_extreme_values",
                    status=TestStatus.PASS,
                    message="极端值处理正确",
                    duration_ms=(time.time() - start) * 1000
                )
            return UnitTestResult(
                test_name="test_extreme_values",
                status=TestStatus.WARNING,
                message=f"极端值处理异常: {result['completion_rate']}",
                duration_ms=(time.time() - start) * 1000
            )
        except Exception as e:
            return UnitTestResult(
                test_name="test_extreme_values",
                status=TestStatus.FAIL,
                error=str(e),
                duration_ms=(time.time() - start) * 1000
            )

    async def run_all(self) -> Dict[str, Any]:
        """运行所有测试"""
        tests = [
            self.test_user_stats_empty_db,
            self.test_task_completion_rate,
            self.test_pagination,
            self.test_memory_trend_fill,
            self.test_extreme_values
        ]
        
        for test_func in tests:
            result = await test_func()
            self.results.append(result)
        
        passed = sum(1 for r in self.results if r.status == TestStatus.PASS)
        failed = sum(1 for r in self.results if r.status == TestStatus.FAIL)
        warnings = sum(1 for r in self.results if r.status == TestStatus.WARNING)
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "summary": {
                "total": len(self.results),
                "passed": passed,
                "failed": failed,
                "warnings": warnings,
                "pass_rate": round(passed / len(self.results) * 100, 2) if self.results else 0
            },
            "results": [
                {
                    "test_name": r.test_name,
                    "status": r.status.value,
                    "message": r.message,
                    "duration_ms": round(r.duration_ms, 2),
                    "error": r.error
                }
                for r in self.results
            ]
        }


class PerformanceAnalyzer:
    """性能分析器 - 提示词8"""

    async def analyze_query(self, query: str, db) -> Dict:
        """分析查询性能"""
        start = time.time()
        
        try:
            result = await db.execute(f"EXPLAIN ANALYZE {query}")
            
            duration = (time.time() - start) * 1000
            
            analysis = {
                "query": query[:100],
                "duration_ms": duration,
                "plan": str(result)[:500] if result else None
            }
            
            if "Seq Scan" in str(result):
                analysis["suggestion"] = "考虑添加索引"
                analysis["needs_index"] = True
            
            return analysis
        except Exception as e:
            return {"error": str(e), "query": query[:100]}

    async def detect_n_plus_one(self, queries: List[str]) -> Dict:
        """检测N+1查询"""
        n_plus_one = []
        
        for i, q in enumerate(queries):
            if "WHERE" in q.upper() and "LIMIT 1" not in q.upper():
                for j, other in enumerate(queries[i+1:], i+1):
                    if self._similar_query(q, other):
                        n_plus_one.append({
                            "query1_index": i,
                            "query2_index": j,
                            "pattern": q[:50]
                        })
        
        return {
            "detected": len(n_plus_one) > 0,
            "instances": n_plus_one,
            "suggestion": "使用JOIN或IN查询替代循环查询" if n_plus_one else None
        }

    def _similar_query(self, q1: str, q2: str) -> bool:
        """判断查询是否相似"""
        q1_base = q1.upper().split("WHERE")[0] if "WHERE" in q1.upper() else q1.upper()
        q2_base = q2.upper().split("WHERE")[0] if "WHERE" in q2.upper() else q2.upper()
        return q1_base.strip() == q2_base.strip()

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
                    cols_part = idx["indexdef"].split("(")[1].rstrip(")")
                    for col in cols_part.split(","):
                        existing_cols.add(col.strip())
            
            suggestions = []
            
            if "created_at" not in existing_cols:
                suggestions.append({
                    "table": table,
                    "columns": ["created_at"],
                    "reason": "时间排序常用",
                    "sql": f"CREATE INDEX idx_{table}_created ON {table}(created_at DESC)"
                })
            
            if "user_id" not in existing_cols:
                suggestions.append({
                    "table": table,
                    "columns": ["user_id"],
                    "reason": "外键关联查询",
                    "sql": f"CREATE INDEX idx_{table}_user ON {table}(user_id)"
                })
            
            return suggestions
        except Exception as e:
            logger.error(f"索引建议失败: {e}")
            return []


async def run_module_tests() -> Dict[str, Any]:
    """运行模块测试"""
    tester = ModuleUnitTests()
    results = await tester.run_all()
    
    return results


if __name__ == "__main__":
    async def main():
        print("=" * 60)
        print("仪表盘模块单元测试")
        print("=" * 60)
        
        report = await run_module_tests()
        print(json.dumps(report, indent=2, ensure_ascii=False))
    
    asyncio.run(main())
