"""
运维监控仪表盘API
Operations Monitoring Dashboard API

提供系统监控、任务管理、告警配置等接口
"""
import os
import json
import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel

from ..auth import require_admin
from ..database import get_db_connection
from ..cache.redis_client import redis_client
from ..logger import get_logger

logger = get_logger("ops_dashboard")

router = APIRouter(prefix="/api/admin/ops", tags=["ops-dashboard"])


class AlertConfig(BaseModel):
    alert_type: str
    threshold: float
    enabled: bool = True
    notify_channels: List[str] = ["email", "webhook"]


class TaskTrigger(BaseModel):
    task_name: str
    params: Optional[Dict[str, Any]] = None


START_TIME = time.time()


@router.get("/overview")
async def get_ops_overview(
    current_user: dict = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取运维概览
    """
    import psutil
    
    system_metrics = _get_system_metrics()
    db_metrics = await _get_database_metrics()
    task_metrics = await _get_task_metrics()
    agent_metrics = await _get_agent_metrics()
    
    return {
        "system": system_metrics,
        "database": db_metrics,
        "tasks": task_metrics,
        "agents": agent_metrics,
        "uptime_seconds": int(time.time() - START_TIME),
        "timestamp": datetime.now().isoformat()
    }


@router.get("/system")
async def get_system_details(
    current_user: dict = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取系统详细信息
    """
    import psutil
    
    cpu_percent = psutil.cpu_percent(interval=0.1, percpu=True)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    network = psutil.net_io_counters()
    
    return {
        "cpu": {
            "percent_per_cpu": cpu_percent,
            "avg_percent": sum(cpu_percent) / len(cpu_percent),
            "count": psutil.cpu_count(),
            "freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
        },
        "memory": {
            "total_gb": round(memory.total / (1024**3), 2),
            "available_gb": round(memory.available / (1024**3), 2),
            "used_gb": round(memory.used / (1024**3), 2),
            "percent": memory.percent
        },
        "disk": {
            "total_gb": round(disk.total / (1024**3), 2),
            "used_gb": round(disk.used / (1024**3), 2),
            "free_gb": round(disk.free / (1024**3), 2),
            "percent": disk.percent
        },
        "network": {
            "bytes_sent": network.bytes_sent,
            "bytes_recv": network.bytes_recv,
            "packets_sent": network.packets_sent,
            "packets_recv": network.packets_recv
        },
        "processes": len(psutil.pids()),
        "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat(),
        "timestamp": datetime.now().isoformat()
    }


@router.get("/database")
async def get_database_details(
    current_user: dict = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取数据库详细信息
    """
    db_path = os.getenv("DATABASE_PATH", "data/property-ai.db")
    if not os.path.isabs(db_path):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        db_path = os.path.join(base_dir, db_path)
    
    metrics = {
        "path": db_path,
        "exists": os.path.exists(db_path),
        "size_mb": 0,
        "tables": [],
        "indexes": [],
        "slow_queries": [],
        "connections": 1
    }
    
    if os.path.exists(db_path):
        metrics["size_mb"] = round(os.path.getsize(db_path) / (1024 * 1024), 2)
    
    async for conn in get_db_connection():
        try:
            cursor = await conn.execute("""
                SELECT name FROM sqlite_master WHERE type='table'
            """)
            tables = await cursor.fetchall()
            metrics["tables"] = [t[0] for t in tables]
            
            cursor = await conn.execute("""
                SELECT name FROM sqlite_master WHERE type='index'
            """)
            indexes = await cursor.fetchall()
            metrics["indexes"] = [i[0] for i in indexes]
            
            try:
                cursor = await conn.execute("""
                    SELECT query, duration_ms, timestamp
                    FROM slow_queries
                    WHERE timestamp >= datetime('now', '-1 hour')
                    ORDER BY duration_ms DESC
                    LIMIT 10
                """)
                slow_queries = await cursor.fetchall()
                metrics["slow_queries"] = [
                    {"query": q[0], "duration_ms": q[1], "timestamp": q[2]}
                    for q in slow_queries
                ]
            except:
                pass
            
        finally:
            await conn.close()
            break
    
    return metrics


@router.get("/tasks")
async def get_task_status(
    current_user: dict = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取任务状态
    """
    tasks = {
        "scheduled": [],
        "running": [],
        "recent_completed": [],
        "recent_failed": []
    }
    
    try:
        from celery.result import AsyncResult
        from ..celery_app import celery_app
        
        inspect = celery_app.control.inspect()
        
        scheduled = inspect.scheduled()
        if scheduled:
            for worker, task_list in scheduled.items():
                for task in task_list:
                    tasks["scheduled"].append({
                        "worker": worker,
                        "task_id": task.get("request", {}).get("id"),
                        "name": task.get("request", {}).get("name"),
                        "eta": str(task.get("eta"))
                    })
        
        active = inspect.active()
        if active:
            for worker, task_list in active.items():
                for task in task_list:
                    tasks["running"].append({
                        "worker": worker,
                        "task_id": task.get("id"),
                        "name": task.get("name"),
                        "args": str(task.get("args", []))[:100]
                    })
        
    except Exception as e:
        logger.warning(f"Failed to get Celery task status: {e}")
        tasks["error"] = str(e)
    
    async for conn in get_db_connection():
        try:
            cursor = await conn.execute("""
                SELECT session_id, start_time, end_time, num_episodes, status, error_message
                FROM training_sessions
                ORDER BY start_time DESC
                LIMIT 10
            """)
            sessions = await cursor.fetchall()
            tasks["recent_completed"] = [
                {
                    "session_id": s[0],
                    "start_time": s[1],
                    "end_time": s[2],
                    "episodes": s[3],
                    "status": s[4],
                    "error": s[5]
                }
                for s in sessions
            ]
        except:
            pass
        finally:
            await conn.close()
            break
    
    return tasks


@router.post("/tasks/trigger")
async def trigger_task(
    task: TaskTrigger,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_admin)
) -> Dict[str, Any]:
    """
    手动触发任务
    """
    try:
        from ..celery_app import celery_app
        
        task_mapping = {
            "self_play_training": "backend.workers.training_worker.self_play_training_cycle",
            "aggregate_stats": "backend.workers.data_worker.aggregate_defense_stats",
            "memory_consolidation": "backend.workers.maintenance_worker.memory_consolidation_task",
            "database_backup": "backend.workers.maintenance_worker.database_backup_task",
            "health_check": "backend.workers.maintenance_worker.health_check_task",
            "update_metrics": "backend.workers.data_worker.update_metrics_cache",
        }
        
        task_path = task_mapping.get(task.task_name)
        if not task_path:
            raise HTTPException(status_code=400, detail=f"Unknown task: {task.task_name}")
        
        result = celery_app.send_task(
            task_path,
            kwargs=task.params or {}
        )
        
        return {
            "success": True,
            "task_id": result.id,
            "task_name": task.task_name,
            "status": "triggered",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to trigger task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}")
async def get_task_result(
    task_id: str,
    current_user: dict = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取任务结果
    """
    try:
        from celery.result import AsyncResult
        from ..celery_app import celery_app
        
        result = AsyncResult(task_id, app=celery_app)
        
        return {
            "task_id": task_id,
            "status": result.status,
            "ready": result.ready(),
            "successful": result.successful() if result.ready() else None,
            "result": result.result if result.ready() else None,
            "traceback": result.traceback if result.failed() else None,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get task result: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents")
async def get_agent_status(
    current_user: dict = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取智能体状态
    """
    agents = {
        "departments": {},
        "total_active": 0,
        "total_idle": 0,
        "recent_tasks": []
    }
    
    departments = ["li", "gong", "hu", "bing", "li_guan", "xing", "attack", "defense", "memory"]
    
    async for conn in get_db_connection():
        try:
            for dept in departments:
                cursor = await conn.execute("""
                    SELECT COUNT(*) FROM memory_entries
                    WHERE agent_name LIKE ?
                    AND created_at >= datetime('now', '-1 hour')
                """, (f"%{dept}%",))
                row = await cursor.fetchone()
                active_count = row[0] if row else 0
                
                agents["departments"][dept] = {
                    "status": "active" if active_count > 5 else "idle",
                    "tasks_1h": active_count
                }
                
                if active_count > 5:
                    agents["total_active"] += 1
                else:
                    agents["total_idle"] += 1
            
            cursor = await conn.execute("""
                SELECT agent_name, summary, created_at
                FROM memory_entries
                ORDER BY created_at DESC
                LIMIT 20
            """)
            recent = await cursor.fetchall()
            agents["recent_tasks"] = [
                {
                    "agent": r[0],
                    "summary": r[1][:50] if r[1] else "",
                    "time": r[2]
                }
                for r in recent
            ]
            
        finally:
            await conn.close()
            break
    
    return agents


@router.get("/alerts")
async def get_alerts(
    hours: int = Query(24, ge=1, le=168),
    current_user: dict = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取告警列表
    """
    alerts = {
        "active": [],
        "history": [],
        "config": {}
    }
    
    async for conn in get_db_connection():
        try:
            cursor = await conn.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_type TEXT,
                    severity TEXT,
                    message TEXT,
                    source TEXT,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved_at TIMESTAMP
                )
            """)
            
            cursor = await conn.execute("""
                SELECT id, alert_type, severity, message, source, status, created_at, resolved_at
                FROM alerts
                WHERE created_at >= datetime('now', ?)
                ORDER BY created_at DESC
            """, (f"-{hours} hours",))
            
            rows = await cursor.fetchall()
            for row in rows:
                alert = {
                    "id": row[0],
                    "type": row[1],
                    "severity": row[2],
                    "message": row[3],
                    "source": row[4],
                    "status": row[5],
                    "created_at": row[6],
                    "resolved_at": row[7]
                }
                if alert["status"] == "active":
                    alerts["active"].append(alert)
                else:
                    alerts["history"].append(alert)
                    
        finally:
            await conn.close()
            break
    
    return alerts


@router.post("/alerts/config")
async def update_alert_config(
    config: AlertConfig,
    current_user: dict = Depends(require_admin)
) -> Dict[str, Any]:
    """
    更新告警配置
    """
    try:
        await redis_client.set(
            f"alert:config:{config.alert_type}",
            json.dumps({
                "threshold": config.threshold,
                "enabled": config.enabled,
                "notify_channels": config.notify_channels
            })
        )
        
        return {
            "success": True,
            "alert_type": config.alert_type,
            "message": "Alert configuration updated"
        }
        
    except Exception as e:
        logger.error(f"Failed to update alert config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: int,
    current_user: dict = Depends(require_admin)
) -> Dict[str, Any]:
    """
    解决告警
    """
    async for conn in get_db_connection():
        try:
            await conn.execute("""
                UPDATE alerts
                SET status = 'resolved', resolved_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (alert_id,))
            
        finally:
            await conn.close()
            break
    
    return {
        "success": True,
        "alert_id": alert_id,
        "status": "resolved"
    }


@router.get("/metrics/history")
async def get_metrics_history(
    metric_type: str = Query("system", regex="^(system|database|tasks|agents)$"),
    hours: int = Query(24, ge=1, le=168),
    current_user: dict = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取指标历史
    """
    history = []
    
    async for conn in get_db_connection():
        try:
            if metric_type == "system":
                cursor = await conn.execute("""
                    SELECT checks_json, created_at
                    FROM health_checks
                    WHERE created_at >= datetime('now', ?)
                    ORDER BY created_at DESC
                """, (f"-{hours} hours",))
                rows = await cursor.fetchall()
                history = [
                    {
                        "metrics": json.loads(r[0]) if r[0] else {},
                        "timestamp": r[1]
                    }
                    for r in rows
                ]
                
            elif metric_type == "database":
                cursor = await conn.execute("""
                    SELECT stats_json, created_at
                    FROM defense_stats_hourly
                    WHERE created_at >= datetime('now', ?)
                    ORDER BY created_at DESC
                """, (f"-{hours} hours",))
                rows = await cursor.fetchall()
                history = [
                    {
                        "stats": json.loads(r[0]) if r[0] else {},
                        "timestamp": r[1]
                    }
                    for r in rows
                ]
                
        finally:
            await conn.close()
            break
    
    return {
        "metric_type": metric_type,
        "hours": hours,
        "history": history
    }


@router.get("/reports/daily")
async def get_daily_reports(
    days: int = Query(7, ge=1, le=30),
    current_user: dict = Depends(require_admin)
) -> Dict[str, Any]:
    """
    获取每日报告
    """
    reports = []
    
    async for conn in get_db_connection():
        try:
            cursor = await conn.execute("""
                SELECT report_date, report_json, created_at
                FROM daily_reports
                WHERE report_date >= date('now', ?)
                ORDER BY report_date DESC
            """, (f"-{days} days",))
            rows = await cursor.fetchall()
            reports = [
                {
                    "date": r[0],
                    "report": json.loads(r[1]) if r[1] else {},
                    "generated_at": r[2]
                }
                for r in rows
            ]
        finally:
            await conn.close()
            break
    
    return {
        "days": days,
        "reports": reports
    }


def _get_system_metrics() -> Dict[str, Any]:
    import psutil
    
    return {
        "cpu_usage": psutil.cpu_percent(interval=0.1),
        "memory_usage": psutil.virtual_memory().percent,
        "disk_usage": psutil.disk_usage('/').percent,
        "active_connections": len(psutil.net_connections())
    }


async def _get_database_metrics() -> Dict[str, Any]:
    db_path = os.getenv("DATABASE_PATH", "data/property-ai.db")
    if not os.path.isabs(db_path):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        db_path = os.path.join(base_dir, db_path)
    
    metrics = {
        "size_mb": 0,
        "table_count": 0,
        "slow_queries": 0
    }
    
    if os.path.exists(db_path):
        metrics["size_mb"] = round(os.path.getsize(db_path) / (1024 * 1024), 2)
    
    async for conn in get_db_connection():
        try:
            cursor = await conn.execute("""
                SELECT COUNT(*) FROM sqlite_master WHERE type='table'
            """)
            row = await cursor.fetchone()
            metrics["table_count"] = row[0] if row else 0
            
            try:
                cursor = await conn.execute("""
                    SELECT COUNT(*) FROM slow_queries
                    WHERE timestamp >= datetime('now', '-1 hour')
                    AND duration_ms > 500
                """)
                row = await cursor.fetchone()
                metrics["slow_queries"] = row[0] if row else 0
            except:
                pass
            
        finally:
            await conn.close()
            break
    
    return metrics


async def _get_task_metrics() -> Dict[str, Any]:
    return {
        "pending": 0,
        "running": 0,
        "completed_today": 0,
        "failed_today": 0
    }


async def _get_agent_metrics() -> Dict[str, Any]:
    return {
        "total": 33,
        "active": 0,
        "idle": 0,
        "departments": 9
    }
