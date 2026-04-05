"""
Workers模块初始化文件
"""

from backend.workers.celery_app import app
from backend.workers.training_tasks import self_play_training_cycle
from backend.workers.defense_tasks import make_defense_decision
from backend.workers.data_tasks import (
    aggregate_defense_stats,
)
from backend.workers.backup_tasks import backup_database

