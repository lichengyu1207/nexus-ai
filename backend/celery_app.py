"""
Celery应用配置
支持分布式任务队列、定时调度、任务监控
"""
from celery import Celery
from celery.schedules import crontab
import os

broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

celery_app = Celery(
    "fangdu",
    broker=broker_url,
    backend=result_backend,
    include=[
        "backend.workers.training_worker",
        "backend.workers.defense_worker",
        "backend.workers.data_worker",
        "backend.workers.maintenance_worker",
        "backend.workers.monitoring_worker",
    ]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,
    task_soft_time_limit=3300,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_default_retry_delay=60,
    task_max_retries=3,
)

celery_app.conf.beat_schedule = {
    "self-play-training-hourly": {
        "task": "backend.workers.training_worker.self_play_training_cycle",
        "schedule": crontab(minute=0),
        "options": {"queue": "training"},
    },
    "aggregate-defense-stats": {
        "task": "backend.workers.data_worker.aggregate_defense_stats",
        "schedule": crontab(minute="*/5"),
        "options": {"queue": "data"},
    },
    "memory-consolidation": {
        "task": "backend.workers.maintenance_worker.memory_consolidation_task",
        "schedule": crontab(hour=3, minute=0),
        "options": {"queue": "maintenance"},
    },
    "database-backup": {
        "task": "backend.workers.maintenance_worker.database_backup_task",
        "schedule": crontab(hour=4, minute=0),
        "options": {"queue": "maintenance"},
    },
    "cleanup-old-logs": {
        "task": "backend.workers.maintenance_worker.cleanup_old_logs",
        "schedule": crontab(hour=5, minute=0),
        "options": {"queue": "maintenance"},
    },
    "health-check": {
        "task": "backend.workers.maintenance_worker.health_check_task",
        "schedule": crontab(minute="*/10"),
        "options": {"queue": "maintenance"},
    },
    "update-metrics-cache": {
        "task": "backend.workers.data_worker.update_metrics_cache",
        "schedule": crontab(minute="*/5"),
        "options": {"queue": "data"},
    },
    "agent-status-report": {
        "task": "backend.workers.data_worker.agent_status_report",
        "schedule": crontab(minute="*/15"),
        "options": {"queue": "data"},
    },
}

celery_app.conf.task_queues = {
    "training": {
        "exchange": "training",
        "routing_key": "training",
    },
    "defense": {
        "exchange": "defense",
        "routing_key": "defense",
    },
    "data": {
        "exchange": "data",
        "routing_key": "data",
    },
    "maintenance": {
        "exchange": "maintenance",
        "routing_key": "maintenance",
    },
    "default": {
        "exchange": "default",
        "routing_key": "default",
    },
}
