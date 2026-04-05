"""
统计服务模块
提供系统统计数据计算和缓存功能
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from functools import lru_cache
import time

from ..database import get_db_connection


class StatsCache:
    """统计缓存"""
    
    def __init__(self, ttl_seconds: int = 60):
        self._cache: Dict[str, Any] = {}
        self._timestamps: Dict[str, float] = {}
        self._ttl = ttl_seconds
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        async with self._lock:
            if key not in self._cache:
                return None
            
            if time.time() - self._timestamps.get(key, 0) > self._ttl:
                return None
            
            return self._cache[key]
    
    async def set(self, key: str, value: Any) -> None:
        """设置缓存值"""
        async with self._lock:
            self._cache[key] = value
            self._timestamps[key] = time.time()
    
    async def clear(self) -> None:
        """清除缓存"""
        async with self._lock:
            self._cache.clear()
            self._timestamps.clear()


stats_cache = StatsCache(ttl_seconds=60)


async def get_overview_stats() -> Dict[str, Any]:
    """
    获取概览统计数据
    
    Returns:
        概览统计字典
    """
    cached = await stats_cache.get("overview")
    if cached:
        return cached
    
    conn = await get_db_connection()
    try:
        stats = {}
        
        cursor = await conn.execute("SELECT COUNT(*) as count FROM users")
        stats["total_users"] = (await cursor.fetchone())["count"]
        
        cursor = await conn.execute(
            "SELECT COUNT(*) as count FROM users WHERE is_active = 1"
        )
        stats["active_users"] = (await cursor.fetchone())["count"]
        
        today = datetime.now().strftime("%Y-%m-%d")
        cursor = await conn.execute(
            "SELECT COUNT(*) as count FROM users WHERE DATE(created_at) = ?",
            (today,)
        )
        stats["new_users_today"] = (await cursor.fetchone())["count"]
        
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        cursor = await conn.execute(
            "SELECT COUNT(*) as count FROM users WHERE DATE(created_at) >= ?",
            (week_ago,)
        )
        stats["new_users_week"] = (await cursor.fetchone())["count"]
        
        cursor = await conn.execute("SELECT COUNT(*) as count FROM analysis_tasks")
        stats["total_tasks"] = (await cursor.fetchone())["count"]
        
        cursor = await conn.execute(
            "SELECT COUNT(*) as count FROM analysis_tasks WHERE status = 'completed'"
        )
        stats["completed_tasks"] = (await cursor.fetchone())["count"]
        
        cursor = await conn.execute(
            "SELECT COUNT(*) as count FROM analysis_tasks WHERE status = 'running'"
        )
        stats["running_tasks"] = (await cursor.fetchone())["count"]
        
        cursor = await conn.execute(
            "SELECT COUNT(*) as count FROM analysis_tasks WHERE status = 'failed'"
        )
        stats["failed_tasks"] = (await cursor.fetchone())["count"]
        
        cursor = await conn.execute("SELECT COUNT(*) as count FROM reports")
        stats["total_reports"] = (await cursor.fetchone())["count"]
        
        cursor = await conn.execute("SELECT COUNT(*) as count FROM teams")
        stats["total_teams"] = (await cursor.fetchone())["count"]
        
        cursor = await conn.execute("SELECT COUNT(*) as count FROM comments")
        stats["total_comments"] = (await cursor.fetchone())["count"]
        
        if stats["total_tasks"] > 0:
            stats["completion_rate"] = round(
                stats["completed_tasks"] / stats["total_tasks"] * 100, 2
            )
        else:
            stats["completion_rate"] = 0
        
        await stats_cache.set("overview", stats)
        
        return stats
    finally:
        await conn.close()


async def get_user_growth_stats(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    granularity: str = "day"
) -> List[Dict[str, Any]]:
    """
    获取用户增长趋势
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
        granularity: 粒度 (day/month)
        
    Returns:
        增长趋势列表
    """
    conn = await get_db_connection()
    try:
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        if granularity == "month":
            cursor = await conn.execute(
                """
                SELECT 
                    strftime('%Y-%m', created_at) as period,
                    COUNT(*) as new_users
                FROM users
                WHERE DATE(created_at) >= ? AND DATE(created_at) <= ?
                GROUP BY strftime('%Y-%m', created_at)
                ORDER BY period
                """,
                (start_date, end_date)
            )
        else:
            cursor = await conn.execute(
                """
                SELECT 
                    DATE(created_at) as period,
                    COUNT(*) as new_users
                FROM users
                WHERE DATE(created_at) >= ? AND DATE(created_at) <= ?
                GROUP BY DATE(created_at)
                ORDER BY period
                """,
                (start_date, end_date)
            )
        
        rows = await cursor.fetchall()
        
        return [dict(row) for row in rows]
    finally:
        await conn.close()


async def get_task_stats(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    granularity: str = "day"
) -> Dict[str, Any]:
    """
    获取任务统计
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
        granularity: 粒度
        
    Returns:
        任务统计字典
    """
    conn = await get_db_connection()
    try:
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        result = {
            "by_status": {},
            "by_period": [],
            "by_style": {}
        }
        
        cursor = await conn.execute(
            """
            SELECT status, COUNT(*) as count
            FROM analysis_tasks
            GROUP BY status
            """
        )
        for row in await cursor.fetchall():
            result["by_status"][row["status"]] = row["count"]
        
        if granularity == "month":
            cursor = await conn.execute(
                """
                SELECT 
                    strftime('%Y-%m', created_at) as period,
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
                FROM analysis_tasks
                WHERE DATE(created_at) >= ? AND DATE(created_at) <= ?
                GROUP BY strftime('%Y-%m', created_at)
                ORDER BY period
                """,
                (start_date, end_date)
            )
        else:
            cursor = await conn.execute(
                """
                SELECT 
                    DATE(created_at) as period,
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
                FROM analysis_tasks
                WHERE DATE(created_at) >= ? AND DATE(created_at) <= ?
                GROUP BY DATE(created_at)
                ORDER BY period
                """,
                (start_date, end_date)
            )
        
        result["by_period"] = [dict(row) for row in await cursor.fetchall()]
        
        cursor = await conn.execute(
            """
            SELECT style, COUNT(*) as count
            FROM analysis_tasks
            WHERE style IS NOT NULL
            GROUP BY style
            """
        )
        for row in await cursor.fetchall():
            result["by_style"][row["style"]] = row["count"]
        
        return result
    finally:
        await conn.close()


async def get_system_health() -> Dict[str, Any]:
    """
    获取系统健康状态
    
    Returns:
        系统健康状态字典
    """
    import psutil
    import os
    
    health = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": None,
        "cpu": {},
        "memory": {},
        "disk": {},
        "database": {},
        "process": {}
    }
    
    try:
        boot_time = psutil.boot_time()
        health["uptime_seconds"] = int(time.time() - boot_time)
    except:
        pass
    
    try:
        health["cpu"]["percent"] = psutil.cpu_percent(interval=1)
        health["cpu"]["count"] = psutil.cpu_count()
        health["cpu"]["load_avg"] = list(psutil.getloadavg()) if hasattr(psutil, 'getloadavg') else None
    except:
        health["cpu"]["error"] = "Unable to get CPU info"
    
    try:
        mem = psutil.virtual_memory()
        health["memory"]["total_mb"] = round(mem.total / (1024 * 1024), 2)
        health["memory"]["available_mb"] = round(mem.available / (1024 * 1024), 2)
        health["memory"]["used_mb"] = round(mem.used / (1024 * 1024), 2)
        health["memory"]["percent"] = mem.percent
    except:
        health["memory"]["error"] = "Unable to get memory info"
    
    try:
        disk = psutil.disk_usage('/')
        health["disk"]["total_gb"] = round(disk.total / (1024 * 1024 * 1024), 2)
        health["disk"]["used_gb"] = round(disk.used / (1024 * 1024 * 1024), 2)
        health["disk"]["free_gb"] = round(disk.free / (1024 * 1024 * 1024), 2)
        health["disk"]["percent"] = disk.percent
    except:
        health["disk"]["error"] = "Unable to get disk info"
    
    try:
        conn = await get_db_connection()
        start = time.time()
        await conn.execute("SELECT 1")
        duration = time.time() - start
        await conn.close()
        
        health["database"]["status"] = "connected"
        health["database"]["response_time_ms"] = round(duration * 1000, 2)
        
        conn = await get_db_connection()
        cursor = await conn.execute("PRAGMA database_list")
        db_info = await cursor.fetchone()
        await conn.close()
        
        if db_info:
            db_path = db_info["file"]
            if db_path and os.path.exists(db_path):
                db_size = os.path.getsize(db_path)
                health["database"]["size_mb"] = round(db_size / (1024 * 1024), 2)
    except Exception as e:
        health["database"]["status"] = "error"
        health["database"]["error"] = str(e)
        health["status"] = "degraded"
    
    try:
        process = psutil.Process(os.getpid())
        health["process"]["pid"] = os.getpid()
        health["process"]["memory_mb"] = round(process.memory_info().rss / (1024 * 1024), 2)
        health["process"]["cpu_percent"] = process.cpu_percent()
        health["process"]["threads"] = process.num_threads()
        health["process"]["open_files"] = len(process.open_files()) if hasattr(process, 'open_files') else None
    except:
        health["process"]["error"] = "Unable to get process info"
    
    if health["memory"].get("percent", 0) > 90:
        health["status"] = "warning"
    if health["disk"].get("percent", 0) > 90:
        health["status"] = "warning"
    
    return health


async def get_activity_stats(days: int = 7) -> Dict[str, Any]:
    """
    获取活动统计
    
    Args:
        days: 统计天数
        
    Returns:
        活动统计字典
    """
    conn = await get_db_connection()
    try:
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        result = {
            "period_days": days,
            "daily_activity": []
        }
        
        cursor = await conn.execute(
            """
            SELECT 
                DATE(created_at) as date,
                (SELECT COUNT(*) FROM users WHERE DATE(created_at) = date) as new_users,
                (SELECT COUNT(*) FROM analysis_tasks WHERE DATE(created_at) = date) as new_tasks,
                (SELECT COUNT(*) FROM reports WHERE DATE(created_at) = date) as new_reports,
                (SELECT COUNT(*) FROM comments WHERE DATE(created_at) = date) as new_comments
            FROM (
                SELECT created_at FROM users
                UNION ALL
                SELECT created_at FROM analysis_tasks
                UNION ALL
                SELECT created_at FROM reports
                UNION ALL
                SELECT created_at FROM comments
            )
            WHERE DATE(created_at) >= ?
            GROUP BY DATE(created_at)
            ORDER BY date
            """,
            (start_date,)
        )
        
        result["daily_activity"] = [dict(row) for row in await cursor.fetchall()]
        
        return result
    finally:
        await conn.close()


async def export_stats_csv(stat_type: str) -> str:
    """
    导出统计数据为CSV
    
    Args:
        stat_type: 统计类型
        
    Returns:
        CSV字符串
    """
    import csv
    import io
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    if stat_type == "overview":
        stats = await get_overview_stats()
        writer.writerow(["指标", "值"])
        for key, value in stats.items():
            writer.writerow([key, value])
    
    elif stat_type == "users":
        data = await get_user_growth_stats()
        writer.writerow(["日期", "新增用户数"])
        for row in data:
            writer.writerow([row["period"], row["new_users"]])
    
    elif stat_type == "tasks":
        stats = await get_task_stats()
        writer.writerow(["日期", "总数", "完成数", "失败数"])
        for row in stats["by_period"]:
            writer.writerow([row["period"], row["total"], row["completed"], row["failed"]])
    
    else:
        raise ValueError(f"Unknown stat type: {stat_type}")
    
    return output.getvalue()
