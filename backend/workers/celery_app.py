"""
Celery后台任务系统
Background Task System for Production Deployment

实现智能体后台自运行机制，包括：
- 自博弈训练任务
- 实时防御决策任务
- 数据聚合任务
- 数据库备份任务
"""

import os
import json
import time
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import traceback

from celery import Celery, Task
from celery.schedules import crontab
from celery.signals import task_prerun, task_postrun, task_failure

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/fangdu")

app = Celery(
    "fangdu",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "backend.workers.training_tasks",
        "backend.workers.defense_tasks",
        "backend.workers.data_tasks",
        "backend.workers.backup_tasks",
        "backend.workers.continuous_training"
    ]
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,
    task_soft_time_limit=3000,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    result_expires=86400,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_default_retry_delay=60,
    task_max_retries=3,
)

app.conf.beat_schedule = {
    "self-play-training-hourly": {
        "task": "backend.workers.training_tasks.self_play_training_cycle",
        "schedule": crontab(minute=0),
        "options": {"queue": "training_queue"},
    },
    "aggregate-defense-stats-hourly": {
        "task": "backend.workers.data_tasks.aggregate_defense_stats",
        "schedule": crontab(minute=5),
        "options": {"queue": "data_queue"},
    },
    "generate-daily-report": {
        "task": "backend.workers.data_tasks.generate_daily_report",
        "schedule": crontab(hour=6, minute=0),
        "options": {"queue": "data_queue"},
    },
    "backup-database-daily": {
        "task": "backend.workers.backup_tasks.backup_database",
        "schedule": crontab(hour=3, minute=0),
        "options": {"queue": "backup_queue"},
    },
    "cleanup-old-logs": {
        "task": "backend.workers.data_tasks.cleanup_old_logs",
        "schedule": crontab(hour=4, minute=0),
        "options": {"queue": "data_queue"},
    },
    "health-check": {
        "task": "backend.workers.data_tasks.health_check",
        "schedule": 60.0,
        "options": {"queue": "monitor_queue"},
    },
    "continuous-evolution-training-daily": {
        "task": "backend.workers.continuous_training.run_daily_training",
        "schedule": crontab(hour=2, minute=0),
        "options": {"queue": "training_queue"},
    },
}


class DatabaseTask(Task):
    _db = None
    
    async def get_db(self):
        if self._db is None:
            from backend.database import get_db_connection
            self._db = get_db_connection()
        return self._db


@app.task(bind=True, base=DatabaseTask, name="base_task")
def base_task(self, *args, **kwargs):
    pass


@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **extra):
    logger.info(f"Task starting: {task.name} [{task_id}]")
    
    from backend.database import get_db_connection
    import asyncio
    
    async def log_task_start():
        async for conn in get_db_connection():
            try:
                await conn.execute("""
                    INSERT INTO task_execution_log 
                    (task_id, task_name, status, started_at, args, kwargs)
                    VALUES ($1, $2, 'running', CURRENT_TIMESTAMP, $3, $4)
                    ON CONFLICT (task_id) DO UPDATE SET
                        status = 'running',
                        started_at = CURRENT_TIMESTAMP
                """, task_id, task.name, json.dumps(args), json.dumps(kwargs))
            finally:
                await conn.close()
                break
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    loop.run_until_complete(log_task_start())


@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, state=None, **extra):
    logger.info(f"Task completed: {task.name} [{task_id}] - {state}")
    
    from backend.database import get_db_connection
    import asyncio
    
    async def log_task_complete():
        async for conn in get_db_connection():
            try:
                await conn.execute("""
                    UPDATE task_execution_log 
                    SET status = $1, completed_at = CURRENT_TIMESTAMP, result = $2
                    WHERE task_id = $3
                """, state, json.dumps(retval) if retval else None, task_id)
            finally:
                await conn.close()
                break
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    loop.run_until_complete(log_task_complete())


@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, args=None, kwargs=None, traceback=None, **extra):
    logger.error(f"Task failed: {sender.name} [{task_id}] - {exception}")
    
    from backend.database import get_db_connection
    import asyncio
    
    async def log_task_failure():
        async for conn in get_db_connection():
            try:
                await conn.execute("""
                    UPDATE task_execution_log 
                    SET status = 'failed', 
                        completed_at = CURRENT_TIMESTAMP,
                        error_message = $1,
                        error_traceback = $2
                    WHERE task_id = $3
                """, str(exception), traceback, task_id)
            finally:
                await conn.close()
                break
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    loop.run_until_complete(log_task_failure())


@dataclass
class TaskResult:
    success: bool
    task_id: str
    task_name: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "task_id": self.task_id,
            "task_name": self.task_name,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result,
            "error": self.error
        }


class TaskManager:
    
    def __init__(self):
        self.app = app
    
    def submit_training_task(self, num_episodes: int = 1000) -> str:
        from backend.workers.training_tasks import self_play_training_cycle
        result = self_play_training_cycle.delay(num_episodes)
        return result.id
    
    def submit_defense_task(self, flow_features: List[float]) -> str:
        from backend.workers.defense_tasks import make_defense_decision
        result = make_defense_decision.delay(flow_features)
        return result.id
    
    def submit_aggregation_task(self) -> str:
        from backend.workers.data_tasks import aggregate_defense_stats
        result = aggregate_defense_stats.delay()
        return result.id
    
    def submit_backup_task(self, backup_type: str = "full") -> str:
        from backend.workers.backup_tasks import backup_database
        result = backup_database.delay(backup_type)
        return result.id
    
    def get_task_status(self, task_id: str) -> Dict:
        result = app.AsyncResult(task_id)
        
        return {
            "task_id": task_id,
            "status": result.status,
            "result": result.result if result.ready() else None,
            "traceback": result.traceback if result.failed() else None
        }
    
    def revoke_task(self, task_id: str, terminate: bool = False):
        app.control.revoke(task_id, terminate=terminate)
    
    def get_active_tasks(self) -> List[Dict]:
        inspect = app.control.inspect()
        active = inspect.active()
        
        tasks = []
        if active:
            for worker, worker_tasks in active.items():
                for task in worker_tasks:
                    tasks.append({
                        "worker": worker,
                        "task_id": task["id"],
                        "task_name": task["name"],
                        "args": task.get("args", []),
                        "kwargs": task.get("kwargs", {})
                    })
        
        return tasks
    
    def get_scheduled_tasks(self) -> List[Dict]:
        inspect = app.control.inspect()
        scheduled = inspect.scheduled()
        
        tasks = []
        if scheduled:
            for worker, worker_tasks in scheduled.items():
                for task in worker_tasks:
                    tasks.append({
                        "worker": worker,
                        "task_id": task["request"]["id"],
                        "task_name": task["request"]["name"],
                        "eta": task.get("eta")
                    })
        
        return tasks
    
    def get_worker_stats(self) -> Dict:
        inspect = app.control.inspect()
        stats = inspect.stats()
        
        return stats or {}


task_manager = TaskManager()


def get_celery_app():
    return app


def start_worker(queue_name: str = "default", concurrency: int = 4, loglevel: str = "info"):
    import sys
    sys.argv = [
        "celery",
        "worker",
        "-A", "backend.workers.celery_app",
        "-Q", queue_name,
        f"--concurrency={concurrency}",
        f"--loglevel={loglevel}",
    ]
    app.worker_main()


def start_beat():
    import sys
    sys.argv = [
        "celery",
        "beat",
        "-A", "backend.workers.celery_app",
        "--loglevel=info",
    ]
    app.start()
