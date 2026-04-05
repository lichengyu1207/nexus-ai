"""
后台任务模块
"""
from .task_queue import task_queue, setup_task_queue, shutdown_task_queue

__all__ = ["task_queue", "setup_task_queue", "shutdown_task_queue"]
