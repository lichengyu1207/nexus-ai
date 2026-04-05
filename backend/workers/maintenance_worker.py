"""
维护任务Worker
Maintenance Worker

实现数据库备份、记忆整理、日志清理等后台任务
"""

import os
import json
import time
import asyncio
import logging
import shutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import traceback

from celery import shared_task

logger = logging.getLogger(__name__)


def get_event_loop():
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop


@shared_task(
    bind=True,
    name="backend.workers.maintenance_worker.database_backup_task",
    max_retries=2
)
def database_backup_task(self) -> Dict:
    """
    数据库备份任务
    """
    task_id = self.request.id
    logger.info(f"Starting database backup, task_id={task_id}")
    
    try:
        db_path = os.getenv("DATABASE_PATH", "data/property-ai.db")
        if not os.path.isabs(db_path):
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            db_path = os.path.join(base_dir, db_path)
        
        backup_dir = os.path.join(os.path.dirname(db_path), "backups")
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_dir, f"property-ai_{timestamp}.db")
        
        if os.path.exists(db_path):
            shutil.copy2(db_path, backup_path)
            backup_size = os.path.getsize(backup_path)
            
            loop = get_event_loop()
            loop.run_until_complete(_cleanup_old_backups(backup_dir))
            
            return {
                "success": True,
                "task_id": task_id,
                "backup_path": backup_path,
                "backup_size_mb": round(backup_size / (1024 * 1024), 2),
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "task_id": task_id,
                "error": f"Database file not found: {db_path}"
            }
            
    except Exception as e:
        logger.error(f"Database backup failed: {e}")
        raise self.retry(exc=e)


async def _cleanup_old_backups(backup_dir: str, max_backups: int = 7):
    try:
        backups = sorted([
            f for f in os.listdir(backup_dir)
            if f.startswith("property-ai_") and f.endswith(".db")
        ])
        
        while len(backups) > max_backups:
            old_backup = os.path.join(backup_dir, backups.pop(0))
            os.remove(old_backup)
            logger.info(f"Removed old backup: {old_backup}")
            
    except Exception as e:
        logger.warning(f"Backup cleanup failed: {e}")


@shared_task(
    bind=True,
    name="backend.workers.maintenance_worker.memory_consolidation_task",
    max_retries=2
)
def memory_consolidation_task(self) -> Dict:
    """
    记忆整理任务（睡眠计算）
    """
    task_id = self.request.id
    logger.info(f"Starting memory consolidation, task_id={task_id}")
    
    try:
        loop = get_event_loop()
        result = loop.run_until_complete(_run_memory_consolidation())
        
        return {
            "success": True,
            "task_id": task_id,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Memory consolidation failed: {e}")
        raise self.retry(exc=e)


async def _run_memory_consolidation() -> Dict:
    result = {
        "memories_processed": 0,
        "memories_merged": 0,
        "memories_forgotten": 0,
        "relations_created": 0
    }
    
    try:
        from backend.hippocampus.manager import memory_manager
        
        consolidation_result = await memory_manager.consolidate()
        
        result["memories_processed"] = consolidation_result.memories_processed
        result["memories_merged"] = consolidation_result.memories_merged
        result["memories_forgotten"] = consolidation_result.memories_forgotten
        result["relations_created"] = consolidation_result.relations_created
        
    except ImportError:
        logger.warning("Memory manager not available, using basic consolidation")
        result = await _basic_consolidation()
    except Exception as e:
        logger.error(f"Consolidation error: {e}")
        result["error"] = str(e)
    
    return result


async def _basic_consolidation() -> Dict:
    from backend.database import get_db_connection
    
    result = {
        "memories_processed": 0,
        "memories_merged": 0,
        "memories_forgotten": 0
    }
    
    async for conn in get_db_connection():
        try:
            cursor = await conn.execute("""
                SELECT COUNT(*) FROM memory_entries
                WHERE importance < 0.3
                AND access_count < 2
                AND created_at < datetime('now', '-30 days')
            """)
            row = await cursor.fetchone()
            forgotten_count = row[0] if row else 0
            
            await conn.execute("""
                DELETE FROM memory_entries
                WHERE importance < 0.3
                AND access_count < 2
                AND created_at < datetime('now', '-30 days')
            """)
            
            result["memories_forgotten"] = forgotten_count
            
            cursor = await conn.execute("SELECT COUNT(*) FROM memory_entries")
            row = await cursor.fetchone()
            result["memories_processed"] = row[0] if row else 0
            
        finally:
            await conn.close()
            break
    
    return result


@shared_task(
    bind=True,
    name="backend.workers.maintenance_worker.cleanup_old_logs",
    max_retries=2
)
def cleanup_old_logs(self, days: int = 30) -> Dict:
    """
    清理旧日志
    """
    task_id = self.request.id
    logger.info(f"Starting log cleanup (older than {days} days), task_id={task_id}")
    
    try:
        loop = get_event_loop()
        result = loop.run_until_complete(_cleanup_logs(days))
        
        return {
            "success": True,
            "task_id": task_id,
            "days_kept": days,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Log cleanup failed: {e}")
        raise self.retry(exc=e)


async def _cleanup_logs(days: int) -> Dict:
    from backend.database import get_db_connection
    
    result = {
        "audit_logs_deleted": 0,
        "slow_queries_deleted": 0,
        "old_sessions_deleted": 0
    }
    
    async for conn in get_db_connection():
        try:
            cursor = await conn.execute("""
                DELETE FROM audit_logs
                WHERE created_at < datetime('now', ?)
            """, (f"-{days} days",))
            result["audit_logs_deleted"] = cursor.rowcount if hasattr(cursor, 'rowcount') else 0
            
            cursor = await conn.execute("""
                DELETE FROM slow_queries
                WHERE timestamp < datetime('now', ?)
            """, (f"-{days} days",))
            result["slow_queries_deleted"] = cursor.rowcount if hasattr(cursor, 'rowcount') else 0
            
            cursor = await conn.execute("""
                DELETE FROM consult_sessions
                WHERE status = 'ended'
                AND created_at < datetime('now', ?)
            """, (f"-{days} days",))
            result["old_sessions_deleted"] = cursor.rowcount if hasattr(cursor, 'rowcount') else 0
            
        finally:
            await conn.close()
            break
    
    return result


@shared_task(
    bind=True,
    name="backend.workers.maintenance_worker.health_check_task",
    max_retries=1
)
def health_check_task(self) -> Dict:
    """
    系统健康检查
    """
    task_id = self.request.id
    logger.info(f"Running health check, task_id={task_id}")
    
    try:
        import psutil
        
        health = {
            "status": "healthy",
            "issues": [],
            "checks": {}
        }
        
        cpu_percent = psutil.cpu_percent(interval=0.1)
        health["checks"]["cpu"] = {
            "usage_percent": cpu_percent,
            "status": "ok" if cpu_percent < 90 else "warning"
        }
        if cpu_percent > 90:
            health["issues"].append(f"High CPU usage: {cpu_percent}%")
        
        memory = psutil.virtual_memory()
        health["checks"]["memory"] = {
            "usage_percent": memory.percent,
            "available_gb": round(memory.available / (1024**3), 2),
            "status": "ok" if memory.percent < 90 else "warning"
        }
        if memory.percent > 90:
            health["issues"].append(f"High memory usage: {memory.percent}%")
        
        disk = psutil.disk_usage('/')
        health["checks"]["disk"] = {
            "usage_percent": disk.percent,
            "free_gb": round(disk.free / (1024**3), 2),
            "status": "ok" if disk.percent < 95 else "warning"
        }
        if disk.percent > 95:
            health["issues"].append(f"Low disk space: {disk.percent}% used")
        
        loop = get_event_loop()
        db_health = loop.run_until_complete(_check_database_health())
        health["checks"]["database"] = db_health
        if db_health.get("status") != "ok":
            health["issues"].append(f"Database issue: {db_health.get('message', 'unknown')}")
        
        redis_health = loop.run_until_complete(_check_redis_health())
        health["checks"]["redis"] = redis_health
        if redis_health.get("status") != "ok":
            health["issues"].append(f"Redis issue: {redis_health.get('message', 'unknown')}")
        
        if len(health["issues"]) > 0:
            health["status"] = "degraded" if len(health["issues"]) < 3 else "unhealthy"
        
        loop.run_until_complete(_record_health_check(health))
        
        return {
            "success": True,
            "task_id": task_id,
            "health": health,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "success": False,
            "task_id": task_id,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


async def _check_database_health() -> Dict:
    try:
        from backend.database import get_db_connection
        
        async for conn in get_db_connection():
            try:
                cursor = await conn.execute("SELECT 1")
                await cursor.fetchone()
                return {"status": "ok", "message": "Database connection successful"}
            finally:
                await conn.close()
                break
                
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def _check_redis_health() -> Dict:
    try:
        from backend.cache.redis_client import redis_client
        
        info = await redis_client.info()
        if info.get("connected"):
            return {"status": "ok", "message": "Redis connected"}
        else:
            return {"status": "warning", "message": "Redis using fallback cache"}
            
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def _record_health_check(health: Dict):
    try:
        from backend.database import get_db_connection
        
        async for conn in get_db_connection():
            try:
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS health_checks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        status TEXT,
                        issues TEXT,
                        checks_json TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                await conn.execute("""
                    INSERT INTO health_checks (status, issues, checks_json)
                    VALUES (?, ?, ?)
                """, (
                    health["status"],
                    json.dumps(health["issues"]),
                    json.dumps(health["checks"])
                ))
                
                await conn.execute("""
                    DELETE FROM health_checks
                    WHERE created_at < datetime('now', '-7 days')
                """)
                
            finally:
                await conn.close()
                break
                
    except Exception as e:
        logger.warning(f"Failed to record health check: {e}")


@shared_task(
    bind=True,
    name="backend.workers.maintenance_worker.optimize_database",
    max_retries=1
)
def optimize_database(self) -> Dict:
    """
    数据库优化任务
    """
    task_id = self.request.id
    logger.info(f"Starting database optimization, task_id={task_id}")
    
    try:
        loop = get_event_loop()
        result = loop.run_until_complete(_run_optimize())
        
        return {
            "success": True,
            "task_id": task_id,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Database optimization failed: {e}")
        raise self.retry(exc=e)


async def _run_optimize() -> Dict:
    from backend.database import get_db_connection
    
    result = {
        "vacuum": False,
        "analyze": False,
        "size_before_mb": 0,
        "size_after_mb": 0
    }
    
    db_path = os.getenv("DATABASE_PATH", "data/property-ai.db")
    if not os.path.isabs(db_path):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        db_path = os.path.join(base_dir, db_path)
    
    if os.path.exists(db_path):
        result["size_before_mb"] = round(os.path.getsize(db_path) / (1024 * 1024), 2)
    
    async for conn in get_db_connection():
        try:
            await conn.execute("PRAGMA optimize")
            result["analyze"] = True
            
            await conn.execute("VACUUM")
            result["vacuum"] = True
            
        finally:
            await conn.close()
            break
    
    if os.path.exists(db_path):
        result["size_after_mb"] = round(os.path.getsize(db_path) / (1024 * 1024), 2)
    
    return result
