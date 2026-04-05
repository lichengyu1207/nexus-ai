"""
管理员统计 API 路由
"""
from fastapi import APIRouter, Depends
from typing import Dict, Any, List
from datetime import datetime, timedelta
import json

from ...auth import require_admin
from ...database import get_db_connection

router = APIRouter(prefix="/api/admin/stats", tags=["admin-stats"])


@router.get("")
@router.get("/")
async def get_admin_stats(admin: dict = Depends(require_admin)) -> Dict[str, Any]:
    """获取管理员统计数据（根端点）"""
    return await get_overview_stats(admin)


@router.get("/feedback")
async def get_feedback_stats(admin: dict = Depends(require_admin)) -> Dict[str, Any]:
    """获取反馈统计数据"""
    conn = await get_db_connection()
    try:
        stats = {}
        
        cursor = await conn.execute("SELECT COUNT(*) as count FROM user_feedback")
        stats["total_feedback"] = (await cursor.fetchone())["count"]
        
        cursor = await conn.execute(
            "SELECT COUNT(*) as count FROM user_feedback WHERE status = 'pending'"
        )
        stats["pending_feedback"] = (await cursor.fetchone())["count"]
        
        cursor = await conn.execute(
            """
            SELECT AVG(EXTRACT(EPOCH FROM (replied_at - created_at)) / 3600) as avg_hours
            FROM user_feedback 
            WHERE replied_at IS NOT NULL
            """
        )
        row = await cursor.fetchone()
        avg_hours = row["avg_hours"]
        if avg_hours:
            stats["avg_response_time"] = f"{avg_hours:.1f}h"
        else:
            stats["avg_response_time"] = "N/A"
        
        cursor = await conn.execute(
            "SELECT type, COUNT(*) as count FROM user_feedback GROUP BY type"
        )
        stats["feedback_by_type"] = {row["type"]: row["count"] for row in await cursor.fetchall()}
        
        cursor = await conn.execute(
            """
            SELECT date(created_at) as date, COUNT(*) as count 
            FROM user_feedback 
            WHERE created_at >= date('now', '-7 days')
            GROUP BY date(created_at)
            ORDER BY date
            """
        )
        stats["trend_last_7_days"] = [
            {"date": row["date"], "count": row["count"]} 
            for row in await cursor.fetchall()
        ]
        
        cursor = await conn.execute(
            """
            SELECT status, COUNT(*) as count 
            FROM user_feedback 
            GROUP BY status
            """
        )
        stats["feedback_by_status"] = {row["status"]: row["count"] for row in await cursor.fetchall()}
        
        cursor = await conn.execute(
            "SELECT COUNT(*) as count FROM user_feedback WHERE created_at >= date('now', '-30 days')"
        )
        stats["recent_month"] = (await cursor.fetchone())["count"]
        
        return stats
    finally:
        await conn.close()


@router.get("/reports")
async def get_reports_stats(admin: dict = Depends(require_admin)) -> Dict[str, Any]:
    """获取举报统计数据"""
    conn = await get_db_connection()
    try:
        stats = {}
        
        cursor = await conn.execute("SELECT COUNT(*) as count FROM content_reports")
        stats["total_reports"] = (await cursor.fetchone())["count"]
        
        cursor = await conn.execute(
            "SELECT COUNT(*) as count FROM content_reports WHERE status = 'pending'"
        )
        stats["pending_reports"] = (await cursor.fetchone())["count"]
        
        cursor = await conn.execute(
            """
            SELECT AVG(EXTRACT(EPOCH FROM (processed_at - created_at)) / 3600) as avg_hours
            FROM content_reports 
            WHERE processed_at IS NOT NULL
            """
        )
        row = await cursor.fetchone()
        avg_hours = row["avg_hours"]
        if avg_hours:
            stats["avg_process_time"] = f"{avg_hours:.1f}h"
        else:
            stats["avg_process_time"] = "N/A"
        
        cursor = await conn.execute(
            "SELECT reported_type, COUNT(*) as count FROM content_reports GROUP BY reported_type"
        )
        stats["reports_by_type"] = {row["reported_type"]: row["count"] for row in await cursor.fetchall()}
        
        cursor = await conn.execute(
            "SELECT reason, COUNT(*) as count FROM content_reports GROUP BY reason"
        )
        stats["reports_by_reason"] = {row["reason"]: row["count"] for row in await cursor.fetchall()}
        
        cursor = await conn.execute(
            """
            SELECT date(created_at) as date, COUNT(*) as count 
            FROM content_reports 
            WHERE created_at >= date('now', '-7 days')
            GROUP BY date(created_at)
            ORDER BY date
            """
        )
        stats["trend_last_7_days"] = [
            {"date": row["date"], "count": row["count"]} 
            for row in await cursor.fetchall()
        ]
        
        cursor = await conn.execute(
            """
            SELECT status, COUNT(*) as count 
            FROM content_reports 
            GROUP BY status
            """
        )
        stats["reports_by_status"] = {row["status"]: row["count"] for row in await cursor.fetchall()}
        
        return stats
    finally:
        await conn.close()


@router.get("/overview")
async def get_overview_stats(admin: dict = Depends(require_admin)) -> Dict[str, Any]:
    """获取总览统计数据"""
    import logging
    logger = logging.getLogger(__name__)
    
    conn = await get_db_connection()
    try:
        stats = {}
        
        try:
            cursor = await conn.execute("SELECT COUNT(*) as count FROM users")
            stats["total_users"] = (await cursor.fetchone())["count"]
        except Exception as e:
            logger.error(f"Error counting users: {e}")
            stats["total_users"] = 0
        
        try:
            cursor = await conn.execute(
                "SELECT COUNT(*) as count FROM users WHERE is_admin = 1"
            )
            stats["admin_users"] = (await cursor.fetchone())["count"]
        except Exception as e:
            logger.error(f"Error counting admin users: {e}")
            stats["admin_users"] = 0
        
        try:
            cursor = await conn.execute(
                "SELECT COUNT(*) as count FROM users WHERE is_active = 1"
            )
            stats["active_users"] = (await cursor.fetchone())["count"]
        except Exception as e:
            logger.error(f"Error counting active users: {e}")
            stats["active_users"] = 0
        
        try:
            cursor = await conn.execute(
                "SELECT COUNT(*) as count FROM users WHERE created_at >= date('now', '-7 days')"
            )
            stats["new_users_week"] = (await cursor.fetchone())["count"]
        except Exception as e:
            logger.error(f"Error counting new users: {e}")
            stats["new_users_week"] = 0
        
        try:
            cursor = await conn.execute(
                "SELECT COUNT(*) as count FROM users WHERE date(created_at) = date('now')"
            )
            stats["new_users_today"] = (await cursor.fetchone())["count"]
        except Exception as e:
            logger.error(f"Error counting new users today: {e}")
            stats["new_users_today"] = 0
        
        try:
            cursor = await conn.execute("SELECT COUNT(*) as count FROM analysis_tasks")
            stats["total_tasks"] = (await cursor.fetchone())["count"]
        except Exception as e:
            logger.error(f"Error counting tasks: {e}")
            stats["total_tasks"] = 0
        
        try:
            cursor = await conn.execute(
                "SELECT COUNT(*) as count FROM analysis_tasks WHERE status = 'completed'"
            )
            stats["completed_tasks"] = (await cursor.fetchone())["count"]
        except Exception as e:
            logger.error(f"Error counting completed tasks: {e}")
            stats["completed_tasks"] = 0
        
        try:
            cursor = await conn.execute(
                "SELECT COUNT(*) as count FROM analysis_tasks WHERE status = 'running'"
            )
            stats["running_tasks"] = (await cursor.fetchone())["count"]
        except Exception as e:
            logger.error(f"Error counting running tasks: {e}")
            stats["running_tasks"] = 0
        
        try:
            cursor = await conn.execute(
                "SELECT COUNT(*) as count FROM analysis_tasks WHERE status = 'failed'"
            )
            stats["failed_tasks"] = (await cursor.fetchone())["count"]
        except Exception as e:
            logger.error(f"Error counting failed tasks: {e}")
            stats["failed_tasks"] = 0
        
        total_tasks = stats.get("total_tasks", 0)
        completed_tasks = stats.get("completed_tasks", 0)
        stats["completion_rate"] = round((completed_tasks / total_tasks) * 100, 1) if total_tasks > 0 else 0
        
        try:
            cursor = await conn.execute(
                "SELECT COUNT(*) as count FROM analysis_tasks WHERE created_at >= date('now', '-7 days')"
            )
            stats["new_tasks_week"] = (await cursor.fetchone())["count"]
        except Exception as e:
            logger.error(f"Error counting new tasks: {e}")
            stats["new_tasks_week"] = 0
        
        try:
            cursor = await conn.execute("SELECT COUNT(*) as count FROM reports")
            stats["total_reports"] = (await cursor.fetchone())["count"]
        except Exception as e:
            logger.error(f"Error counting reports: {e}")
            stats["total_reports"] = 0
        
        try:
            cursor = await conn.execute("SELECT COUNT(*) as count FROM teams")
            stats["total_teams"] = (await cursor.fetchone())["count"]
        except Exception as e:
            logger.error(f"Error counting teams: {e}")
            stats["total_teams"] = 0
        
        try:
            cursor = await conn.execute("SELECT COUNT(*) as count FROM report_comments")
            stats["total_comments"] = (await cursor.fetchone())["count"]
        except Exception as e:
            logger.error(f"Error counting comments: {e}")
            stats["total_comments"] = 0
        
        try:
            cursor = await conn.execute(
                "SELECT COUNT(*) as count FROM user_feedback WHERE status = 'pending'"
            )
            stats["pending_feedback"] = (await cursor.fetchone())["count"]
        except Exception as e:
            logger.error(f"Error counting pending feedback: {e}")
            stats["pending_feedback"] = 0
        
        try:
            cursor = await conn.execute(
                "SELECT COUNT(*) as count FROM content_reports WHERE status = 'pending'"
            )
            stats["pending_reports"] = (await cursor.fetchone())["count"]
        except Exception as e:
            logger.error(f"Error counting pending reports: {e}")
            stats["pending_reports"] = 0
        
        return stats
    except Exception as e:
        logger.error(f"Error in get_overview_stats: {e}", exc_info=True)
        raise
    finally:
        await conn.close()


@router.get("/users")
async def get_user_growth_stats(
    admin: dict = Depends(require_admin),
    start_date: str = None,
    end_date: str = None,
    granularity: str = "day"
) -> List[Dict[str, Any]]:
    """获取用户增长统计数据"""
    import logging
    logger = logging.getLogger(__name__)
    
    conn = await get_db_connection()
    try:
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        if granularity == "month":
            query = """
                SELECT 
                    strftime('%Y-%m', created_at) as period,
                    COUNT(*) as new_users
                FROM users
                WHERE date(created_at) >= ? AND date(created_at) <= ?
                GROUP BY strftime('%Y-%m', created_at)
                ORDER BY period
            """
        else:
            query = """
                SELECT 
                    date(created_at) as period,
                    COUNT(*) as new_users
                FROM users
                WHERE date(created_at) >= ? AND date(created_at) <= ?
                GROUP BY date(created_at)
                ORDER BY period
            """
        
        cursor = await conn.execute(query, [start_date, end_date])
        results = []
        async for row in cursor:
            results.append({
                "period": row["period"],
                "new_users": row["new_users"]
            })
        
        return results
    except Exception as e:
        logger.error(f"Error in get_user_growth_stats: {e}")
        return []
    finally:
        await conn.close()


@router.get("/tasks")
async def get_task_stats(
    admin: dict = Depends(require_admin),
    start_date: str = None,
    end_date: str = None,
    granularity: str = "day"
) -> Dict[str, Any]:
    """获取任务统计数据"""
    import logging
    logger = logging.getLogger(__name__)
    
    conn = await get_db_connection()
    try:
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        by_status = {}
        try:
            cursor = await conn.execute(
                "SELECT status, COUNT(*) as count FROM analysis_tasks GROUP BY status"
            )
            async for row in cursor:
                by_status[row["status"]] = row["count"]
        except Exception as e:
            logger.error(f"Error getting task status stats: {e}")
        
        by_period = []
        try:
            if granularity == "month":
                query = """
                    SELECT 
                        strftime('%Y-%m', created_at) as period,
                        COUNT(*) as total,
                        SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                        SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
                    FROM analysis_tasks
                    WHERE date(created_at) >= ? AND date(created_at) <= ?
                    GROUP BY strftime('%Y-%m', created_at)
                    ORDER BY period
                """
            else:
                query = """
                    SELECT 
                        date(created_at) as period,
                        COUNT(*) as total,
                        SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                        SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
                    FROM analysis_tasks
                    WHERE date(created_at) >= ? AND date(created_at) <= ?
                    GROUP BY date(created_at)
                    ORDER BY period
                """
            
            cursor = await conn.execute(query, [start_date, end_date])
            async for row in cursor:
                by_period.append({
                    "period": row["period"],
                    "total": row["total"] or 0,
                    "completed": row["completed"] or 0,
                    "failed": row["failed"] or 0
                })
        except Exception as e:
            logger.error(f"Error getting task period stats: {e}")
        
        by_style = {}
        try:
            cursor = await conn.execute(
                "SELECT style, COUNT(*) as count FROM analysis_tasks GROUP BY style"
            )
            async for row in cursor:
                if row["style"]:
                    by_style[row["style"]] = row["count"]
        except Exception as e:
            logger.error(f"Error getting task style stats: {e}")
        
        return {
            "by_status": by_status,
            "by_period": by_period,
            "by_style": by_style
        }
    except Exception as e:
        logger.error(f"Error in get_task_stats: {e}")
        return {"by_status": {}, "by_period": [], "by_style": {}}
    finally:
        await conn.close()


@router.get("/system")
async def get_system_health(admin: dict = Depends(require_admin)) -> Dict[str, Any]:
    """获取系统健康状态"""
    import logging
    import platform
    import time
    logger = logging.getLogger(__name__)
    
    health = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": None,
        "cpu": {},
        "memory": {},
        "disk": {},
        "database": {},
        "process": {}
    }
    
    try:
        import psutil
        health["cpu"] = {
            "percent": psutil.cpu_percent(interval=0.1),
            "count": psutil.cpu_count(),
            "load_avg": list(psutil.getloadavg()) if hasattr(psutil, 'getloadavg') else None
        }
    except ImportError:
        health["cpu"] = {"error": "psutil not installed"}
    except Exception as e:
        health["cpu"] = {"error": str(e)}
    
    try:
        import psutil
        mem = psutil.virtual_memory()
        health["memory"] = {
            "total_mb": mem.total / (1024 * 1024),
            "available_mb": mem.available / (1024 * 1024),
            "used_mb": mem.used / (1024 * 1024),
            "percent": mem.percent
        }
    except ImportError:
        health["memory"] = {"error": "psutil not installed"}
    except Exception as e:
        health["memory"] = {"error": str(e)}
    
    try:
        import psutil
        import shutil
        disk_path = "C:\\" if platform.system() == "Windows" else "/"
        disk = shutil.disk_usage(disk_path)
        health["disk"] = {
            "total_gb": disk.total / (1024**3),
            "used_gb": disk.used / (1024**3),
            "free_gb": disk.free / (1024**3),
            "percent": (disk.used / disk.total) * 100
        }
    except Exception as e:
        health["disk"] = {"error": str(e)}
    
    try:
        conn = await get_db_connection()
        start = time.time()
        cursor = await conn.execute("SELECT 1")
        await cursor.fetchone()
        elapsed = (time.time() - start) * 1000
        
        cursor = await conn.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
        row = await cursor.fetchone()
        db_size = row["size"] / (1024 * 1024) if row else 0
        
        health["database"] = {
            "status": "healthy",
            "response_time_ms": elapsed,
            "size_mb": db_size
        }
        await conn.close()
    except Exception as e:
        health["database"] = {"status": "unhealthy", "error": str(e)}
        health["status"] = "degraded"
    
    try:
        import psutil
        process = psutil.Process()
        health["process"] = {
            "pid": process.pid,
            "memory_mb": process.memory_info().rss / (1024 * 1024),
            "cpu_percent": process.cpu_percent(),
            "threads": process.num_threads()
        }
    except ImportError:
        health["process"] = {"error": "psutil not installed"}
    except Exception as e:
        health["process"] = {"error": str(e)}
    
    if health["cpu"].get("percent", 0) > 80 or health["memory"].get("percent", 0) > 80:
        health["status"] = "warning"
    
    return health


@router.get("/metrics")
async def get_system_metrics(admin: dict = Depends(require_admin)) -> Dict[str, Any]:
    """获取系统指标"""
    conn = await get_db_connection()
    try:
        metrics = {}
        
        cursor = await conn.execute("SELECT COUNT(*) as count FROM users")
        metrics["total_users"] = (await cursor.fetchone())["count"]
        
        cursor = await conn.execute("SELECT COUNT(*) as count FROM analysis_tasks")
        metrics["total_tasks"] = (await cursor.fetchone())["count"]
        
        cursor = await conn.execute("SELECT COUNT(*) as count FROM reports")
        metrics["total_reports"] = (await cursor.fetchone())["count"]
        
        cursor = await conn.execute(
            "SELECT COUNT(*) as count FROM users WHERE created_at >= date('now', '-1 day')"
        )
        metrics["active_users_today"] = (await cursor.fetchone())["count"]
        
        cursor = await conn.execute(
            "SELECT COUNT(*) as count FROM analysis_tasks WHERE created_at >= date('now', '-1 day')"
        )
        metrics["tasks_today"] = (await cursor.fetchone())["count"]
        
        return metrics
    finally:
        await conn.close()
