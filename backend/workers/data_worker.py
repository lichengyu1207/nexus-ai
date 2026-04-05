"""
数据聚合Worker
Data Aggregation Worker

实现数据聚合、报表生成等后台任务
"""

import os
import json
import time
import asyncio
import logging
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
    name="backend.workers.data_worker.aggregate_defense_stats",
    max_retries=3,
    default_retry_delay=60
)
def aggregate_defense_stats(self) -> Dict:
    """
    聚合防御统计数据
    """
    task_id = self.request.id
    logger.info(f"Aggregating defense stats, task_id={task_id}")
    
    try:
        loop = get_event_loop()
        stats = loop.run_until_complete(_aggregate_stats())
        
        return {
            "success": True,
            "task_id": task_id,
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Defense stats aggregation failed: {e}")
        raise self.retry(exc=e)


async def _aggregate_stats() -> Dict:
    try:
        from backend.database import get_db_connection
        
        stats = {
            "period": "hourly",
            "total_decisions": 0,
            "total_attacks": 0,
            "blocked_count": 0,
            "allowed_count": 0,
            "avg_confidence": 0,
            "avg_latency_ms": 0,
            "attack_types": {},
            "top_source_ips": []
        }
        
        async for conn in get_db_connection():
            try:
                cursor = await conn.execute("""
                    SELECT COUNT(*) FROM defense_decisions
                    WHERE created_at >= datetime('now', '-1 hour')
                """)
                row = await cursor.fetchone()
                stats["total_decisions"] = row[0] if row else 0
                
                cursor = await conn.execute("""
                    SELECT COUNT(*) FROM attack_events
                    WHERE created_at >= datetime('now', '-1 hour')
                """)
                row = await cursor.fetchone()
                stats["total_attacks"] = row[0] if row else 0
                
                cursor = await conn.execute("""
                    SELECT AVG(confidence), AVG(latency_ms)
                    FROM defense_decisions
                    WHERE created_at >= datetime('now', '-1 hour')
                """)
                row = await cursor.fetchone()
                if row:
                    stats["avg_confidence"] = round(row[0] or 0, 3)
                    stats["avg_latency_ms"] = round(row[1] or 0, 2)
                
                cursor = await conn.execute("""
                    SELECT action, COUNT(*) as cnt
                    FROM defense_decisions
                    WHERE created_at >= datetime('now', '-1 hour')
                    GROUP BY action
                """)
                action_counts = await cursor.fetchall()
                for action, cnt in action_counts:
                    if action in ["block", "quarantine"]:
                        stats["blocked_count"] += cnt
                    elif action in ["allow"]:
                        stats["allowed_count"] += cnt
                
                cursor = await conn.execute("""
                    SELECT event_type, COUNT(*) as cnt
                    FROM attack_events
                    WHERE created_at >= datetime('now', '-1 hour')
                    GROUP BY event_type
                """)
                attack_types = await cursor.fetchall()
                stats["attack_types"] = {t: c for t, c in attack_types}
                
                cursor = await conn.execute("""
                    SELECT source_ip, COUNT(*) as cnt
                    FROM attack_events
                    WHERE created_at >= datetime('now', '-1 hour')
                    GROUP BY source_ip
                    ORDER BY cnt DESC
                    LIMIT 10
                """)
                top_ips = await cursor.fetchall()
                stats["top_source_ips"] = [{"ip": ip, "count": cnt} for ip, cnt in top_ips]
                
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS defense_stats_hourly (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        period_start TIMESTAMP,
                        period_end TIMESTAMP,
                        stats_json TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                await conn.execute("""
                    INSERT INTO defense_stats_hourly (period_start, period_end, stats_json)
                    VALUES (?, ?, ?)
                """, (
                    datetime.now() - timedelta(hours=1),
                    datetime.now(),
                    json.dumps(stats)
                ))
                
            finally:
                await conn.close()
                break
        
        return stats
        
    except Exception as e:
        logger.error(f"Stats aggregation error: {e}")
        return {"error": str(e)}


@shared_task(
    bind=True,
    name="backend.workers.data_worker.update_metrics_cache",
    max_retries=2
)
def update_metrics_cache(self) -> Dict:
    """
    更新指标缓存
    """
    task_id = self.request.id
    logger.info(f"Updating metrics cache, task_id={task_id}")
    
    try:
        loop = get_event_loop()
        metrics = loop.run_until_complete(_collect_metrics())
        
        loop.run_until_complete(_cache_metrics(metrics))
        
        return {
            "success": True,
            "task_id": task_id,
            "metrics_updated": list(metrics.keys()),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Metrics cache update failed: {e}")
        raise self.retry(exc=e)


async def _collect_metrics() -> Dict:
    from backend.database import get_db_connection
    
    metrics = {}
    
    async for conn in get_db_connection():
        try:
            cursor = await conn.execute("SELECT COUNT(*) FROM users")
            row = await cursor.fetchone()
            metrics["total_users"] = row[0] if row else 0
            
            cursor = await conn.execute("""
                SELECT COUNT(*) FROM users
                WHERE DATE(created_at) = DATE('now')
            """)
            row = await cursor.fetchone()
            metrics["new_users_today"] = row[0] if row else 0
            
            cursor = await conn.execute("SELECT COUNT(*) FROM analysis_tasks")
            row = await cursor.fetchone()
            metrics["total_tasks"] = row[0] if row else 0
            
            cursor = await conn.execute("""
                SELECT COUNT(*) FROM analysis_tasks
                WHERE DATE(created_at) = DATE('now')
            """)
            row = await cursor.fetchone()
            metrics["tasks_today"] = row[0] if row else 0
            
            cursor = await conn.execute("SELECT COUNT(*) FROM reports")
            row = await cursor.fetchone()
            metrics["total_reports"] = row[0] if row else 0
            
            cursor = await conn.execute("SELECT COUNT(*) FROM memory_entries")
            row = await cursor.fetchone()
            metrics["total_memories"] = row[0] if row else 0
            
        finally:
            await conn.close()
            break
    
    return metrics


async def _cache_metrics(metrics: Dict):
    try:
        from backend.cache.redis_client import redis_client
        
        await redis_client.set("metrics:dashboard", json.dumps(metrics), ex=300)
        
        for key, value in metrics.items():
            await redis_client.set(f"metrics:{key}", str(value), ex=300)
            
    except Exception as e:
        logger.warning(f"Failed to cache metrics in Redis: {e}")


@shared_task(
    bind=True,
    name="backend.workers.data_worker.agent_status_report",
    max_retries=2
)
def agent_status_report(self) -> Dict:
    """
    生成智能体状态报告
    """
    task_id = self.request.id
    logger.info(f"Generating agent status report, task_id={task_id}")
    
    try:
        loop = get_event_loop()
        report = loop.run_until_complete(_generate_agent_report())
        
        return {
            "success": True,
            "task_id": task_id,
            "report": report,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Agent status report failed: {e}")
        raise self.retry(exc=e)


async def _generate_agent_report() -> Dict:
    from backend.database import get_db_connection
    
    report = {
        "agents": [],
        "total_active": 0,
        "total_idle": 0,
        "departments": {}
    }
    
    departments = ["li", "gong", "hu", "bing", "li_guan", "xing", "attack", "defense", "memory"]
    
    for dept in departments:
        report["departments"][dept] = {
            "active": 0,
            "idle": 0,
            "tasks_completed": 0
        }
    
    try:
        async for conn in get_db_connection():
            try:
                cursor = await conn.execute("""
                    SELECT agent_name, COUNT(*) as task_count
                    FROM memory_entries
                    WHERE created_at >= datetime('now', '-1 day')
                    GROUP BY agent_name
                """)
                agent_tasks = await cursor.fetchall()
                
                for agent_name, task_count in agent_tasks:
                    report["agents"].append({
                        "name": agent_name,
                        "tasks_24h": task_count,
                        "status": "active" if task_count > 5 else "idle"
                    })
                    
                    if task_count > 5:
                        report["total_active"] += 1
                    else:
                        report["total_idle"] += 1
                
            finally:
                await conn.close()
                break
    except Exception as e:
        logger.warning(f"Failed to get agent data: {e}")
    
    return report


@shared_task(
    bind=True,
    name="backend.workers.data_worker.generate_daily_report",
    max_retries=2
)
def generate_daily_report(self, date: str = None) -> Dict:
    """
    生成每日报告
    
    Args:
        date: 报告日期 (YYYY-MM-DD)，默认为今天
    """
    task_id = self.request.id
    report_date = date or datetime.now().strftime("%Y-%m-%d")
    
    logger.info(f"Generating daily report for {report_date}, task_id={task_id}")
    
    try:
        loop = get_event_loop()
        report = loop.run_until_complete(_generate_daily_report(report_date))
        
        return {
            "success": True,
            "task_id": task_id,
            "date": report_date,
            "report": report,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Daily report generation failed: {e}")
        raise self.retry(exc=e)


async def _generate_daily_report(date: str) -> Dict:
    from backend.database import get_db_connection
    
    report = {
        "date": date,
        "users": {},
        "tasks": {},
        "defense": {},
        "memory": {}
    }
    
    async for conn in get_db_connection():
        try:
            cursor = await conn.execute("""
                SELECT COUNT(*) FROM users
                WHERE DATE(created_at) = ?
            """, (date,))
            row = await cursor.fetchone()
            report["users"]["new_users"] = row[0] if row else 0
            
            cursor = await conn.execute("""
                SELECT COUNT(*) FROM analysis_tasks
                WHERE DATE(created_at) = ?
            """, (date,))
            row = await cursor.fetchone()
            report["tasks"]["total"] = row[0] if row else 0
            
            cursor = await conn.execute("""
                SELECT COUNT(*) FROM analysis_tasks
                WHERE DATE(created_at) = ? AND status = 'completed'
            """, (date,))
            row = await cursor.fetchone()
            report["tasks"]["completed"] = row[0] if row else 0
            
            cursor = await conn.execute("""
                SELECT COUNT(*) FROM defense_decisions
                WHERE DATE(created_at) = ?
            """, (date,))
            row = await cursor.fetchone()
            report["defense"]["total_decisions"] = row[0] if row else 0
            
            cursor = await conn.execute("""
                SELECT COUNT(*) FROM attack_events
                WHERE DATE(created_at) = ?
            """, (date,))
            row = await cursor.fetchone()
            report["defense"]["attack_events"] = row[0] if row else 0
            
            cursor = await conn.execute("""
                SELECT COUNT(*) FROM memory_entries
                WHERE DATE(created_at) = ?
            """, (date,))
            row = await cursor.fetchone()
            report["memory"]["new_memories"] = row[0] if row else 0
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS daily_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_date TEXT UNIQUE,
                    report_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await conn.execute("""
                INSERT OR REPLACE INTO daily_reports (report_date, report_json)
                VALUES (?, ?)
            """, (date, json.dumps(report)))
            
        finally:
            await conn.close()
            break
    
    return report
