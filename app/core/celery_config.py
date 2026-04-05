"""
Celery配置文件
用于异步任务处理
"""
from celery import Celery
from celery.schedules import crontab
import os

# Celery配置
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

# 创建Celery应用
celery_app = Celery(
    "fangtan_ai",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=["app.tasks.analysis_tasks"]
)

# Celery配置
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30分钟超时
    task_soft_time_limit=25 * 60,  # 25分钟软超时
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# 定时任务配置
celery_app.conf.beat_schedule = {
    "cleanup-old-tasks": {
        "task": "app.tasks.analysis_tasks.cleanup_old_tasks",
        "schedule": crontab(hour=2, minute=0),  # 每天凌晨2点执行
    },
    "update-market-data": {
        "task": "app.tasks.analysis_tasks.update_market_data",
        "schedule": crontab(hour=6, minute=0),  # 每天早上6点执行
    },
}
