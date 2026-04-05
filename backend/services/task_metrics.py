"""
任务调度监控指标模块
提供Prometheus指标采集和Grafana仪表盘配置
"""
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict
import logging
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class TaskMetrics:
    """任务指标"""
    task_id: str
    task_type: str
    status: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    retry_count: int = 0
    error_message: Optional[str] = None


@dataclass
class BatchMetrics:
    """批量任务指标"""
    parent_task_id: str
    total_tasks: int
    completed_tasks: int = 0
    failed_tasks: int = 0
    running_tasks: int = 0
    pending_tasks: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_duration_ms: Optional[int] = None


class TaskMetricsCollector:
    """任务指标收集器"""

    def __init__(self):
        self._task_metrics: Dict[str, TaskMetrics] = {}
        self._batch_metrics: Dict[str, BatchMetrics] = {}
        self._hourly_stats: Dict[str, Dict[str, int]] = defaultdict(lambda: {
            "total": 0,
            "completed": 0,
            "failed": 0,
            "avg_duration_ms": 0,
        })
        self._type_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "count": 0,
            "success_count": 0,
            "fail_count": 0,
            "total_duration_ms": 0,
            "avg_duration_ms": 0,
        })
        self._start_time = time.time()

    def record_task_created(self, task_id: str, task_type: str) -> None:
        """记录任务创建"""
        self._task_metrics[task_id] = TaskMetrics(
            task_id=task_id,
            task_type=task_type,
            status="pending",
            created_at=datetime.utcnow()
        )
        
        self._type_stats[task_type]["count"] += 1
        
        hour_key = datetime.utcnow().strftime("%Y-%m-%d %H:00")
        self._hourly_stats[hour_key]["total"] += 1

    def record_task_started(self, task_id: str) -> None:
        """记录任务开始"""
        if task_id in self._task_metrics:
            self._task_metrics[task_id].status = "running"
            self._task_metrics[task_id].started_at = datetime.utcnow()

    def record_task_completed(
        self, 
        task_id: str, 
        success: bool = True,
        error_message: Optional[str] = None
    ) -> None:
        """记录任务完成"""
        if task_id not in self._task_metrics:
            return
        
        metrics = self._task_metrics[task_id]
        metrics.status = "completed" if success else "failed"
        metrics.completed_at = datetime.utcnow()
        
        if metrics.started_at:
            duration = (metrics.completed_at - metrics.started_at).total_seconds() * 1000
            metrics.duration_ms = int(duration)
        
        if error_message:
            metrics.error_message = error_message
        
        task_type = metrics.task_type
        if success:
            self._type_stats[task_type]["success_count"] += 1
        else:
            self._type_stats[task_type]["fail_count"] += 1
        
        if metrics.duration_ms:
            self._type_stats[task_type]["total_duration_ms"] += metrics.duration_ms
            count = self._type_stats[task_type]["success_count"] + self._type_stats[task_type]["fail_count"]
            if count > 0:
                self._type_stats[task_type]["avg_duration_ms"] = (
                    self._type_stats[task_type]["total_duration_ms"] // count
                )
        
        hour_key = datetime.utcnow().strftime("%Y-%m-%d %H:00")
        if success:
            self._hourly_stats[hour_key]["completed"] += 1
        else:
            self._hourly_stats[hour_key]["failed"] += 1

    def record_task_retry(self, task_id: str) -> None:
        """记录任务重试"""
        if task_id in self._task_metrics:
            self._task_metrics[task_id].retry_count += 1

    def record_batch_created(
        self, 
        parent_task_id: str, 
        total_tasks: int
    ) -> None:
        """记录批量任务创建"""
        self._batch_metrics[parent_task_id] = BatchMetrics(
            parent_task_id=parent_task_id,
            total_tasks=total_tasks,
            created_at=datetime.utcnow()
        )

    def update_batch_progress(
        self,
        parent_task_id: str,
        completed: int,
        failed: int,
        running: int,
        pending: int
    ) -> None:
        """更新批量任务进度"""
        if parent_task_id in self._batch_metrics:
            batch = self._batch_metrics[parent_task_id]
            batch.completed_tasks = completed
            batch.failed_tasks = failed
            batch.running_tasks = running
            batch.pending_tasks = pending
            
            if batch.started_at is None and running > 0:
                batch.started_at = datetime.utcnow()
            
            if completed + failed == batch.total_tasks:
                batch.completed_at = datetime.utcnow()
                if batch.started_at:
                    batch.total_duration_ms = int(
                        (batch.completed_at - batch.started_at).total_seconds() * 1000
                    )

    def get_prometheus_metrics(self) -> str:
        """获取Prometheus格式的指标"""
        lines = []
        
        lines.append("# HELP task_total Total number of tasks")
        lines.append("# TYPE task_total counter")
        total_count = len(self._task_metrics)
        lines.append(f"task_total {total_count}")
        
        lines.append("# HELP task_completed Total completed tasks")
        lines.append("# TYPE task_completed counter")
        completed_count = sum(1 for m in self._task_metrics.values() if m.status == "completed")
        lines.append(f"task_completed {completed_count}")
        
        lines.append("# HELP task_failed Total failed tasks")
        lines.append("# TYPE task_failed counter")
        failed_count = sum(1 for m in self._task_metrics.values() if m.status == "failed")
        lines.append(f"task_failed {failed_count}")
        
        lines.append("# HELP task_running Currently running tasks")
        lines.append("# TYPE task_running gauge")
        running_count = sum(1 for m in self._task_metrics.values() if m.status == "running")
        lines.append(f"task_running {running_count}")
        
        lines.append("# HELP task_pending Pending tasks")
        lines.append("# TYPE task_pending gauge")
        pending_count = sum(1 for m in self._task_metrics.values() if m.status == "pending")
        lines.append(f"task_pending {pending_count}")
        
        lines.append("# HELP task_duration_ms Task duration in milliseconds")
        lines.append("# TYPE task_duration_ms summary")
        durations = [m.duration_ms for m in self._task_metrics.values() if m.duration_ms]
        if durations:
            avg_duration = sum(durations) // len(durations)
            lines.append(f'task_duration_ms{{quantile="0.5"}} {avg_duration}')
            sorted_durations = sorted(durations)
            p50 = sorted_durations[len(sorted_durations) // 2]
            p95 = sorted_durations[int(len(sorted_durations) * 0.95)] if len(sorted_durations) > 20 else p50
            p99 = sorted_durations[int(len(sorted_durations) * 0.99)] if len(sorted_durations) > 100 else p95
            lines.append(f'task_duration_ms{{quantile="0.95"}} {p95}')
            lines.append(f'task_duration_ms{{quantile="0.99"}} {p99}')
        
        lines.append("# HELP task_by_type Tasks by type")
        lines.append("# TYPE task_by_type counter")
        for task_type, stats in self._type_stats.items():
            lines.append(f'task_by_type{{type="{task_type}"}} {stats["count"]}')
        
        lines.append("# HELP task_success_by_type Successful tasks by type")
        lines.append("# TYPE task_success_by_type counter")
        for task_type, stats in self._type_stats.items():
            lines.append(f'task_success_by_type{{type="{task_type}"}} {stats["success_count"]}')
        
        lines.append("# HELP batch_total Total batch tasks")
        lines.append("# TYPE batch_total counter")
        batch_count = len(self._batch_metrics)
        lines.append(f"batch_total {batch_count}")
        
        lines.append("# HELP batch_avg_size Average batch size")
        lines.append("# TYPE batch_avg_size gauge")
        if self._batch_metrics:
            avg_size = sum(b.total_tasks for b in self._batch_metrics.values()) // len(self._batch_metrics)
            lines.append(f"batch_avg_size {avg_size}")
        
        lines.append("# HELP system_uptime_seconds System uptime in seconds")
        lines.append("# TYPE system_uptime_seconds gauge")
        uptime = int(time.time() - self._start_time)
        lines.append(f"system_uptime_seconds {uptime}")
        
        return "\n".join(lines)

    def get_dashboard_stats(self) -> Dict[str, Any]:
        """获取仪表盘统计数据"""
        now = datetime.utcnow()
        one_hour_ago = now - timedelta(hours=1)
        one_day_ago = now - timedelta(hours=24)
        
        hourly_stats = []
        for hour_key, stats in sorted(self._hourly_stats.items(), reverse=True)[:24]:
            hourly_stats.append({
                "hour": hour_key,
                **stats
            })
        
        type_stats = []
        for task_type, stats in self._type_stats.items():
            success_rate = 0
            total = stats["success_count"] + stats["fail_count"]
            if total > 0:
                success_rate = round((stats["success_count"] / total) * 100, 1)
            
            type_stats.append({
                "type": task_type,
                "count": stats["count"],
                "success_count": stats["success_count"],
                "fail_count": stats["fail_count"],
                "success_rate": success_rate,
                "avg_duration_ms": stats["avg_duration_ms"]
            })
        
        recent_tasks = sorted(
            [m for m in self._task_metrics.values()],
            key=lambda x: x.created_at,
            reverse=True
        )[:50]
        
        active_batches = [
            {
                "parent_task_id": b.parent_task_id,
                "total": b.total_tasks,
                "completed": b.completed_tasks,
                "failed": b.failed_tasks,
                "running": b.running_tasks,
                "pending": b.pending_tasks,
                "progress_percent": round((b.completed_tasks / b.total_tasks) * 100, 1) if b.total_tasks > 0 else 0
            }
            for b in self._batch_metrics.values()
            if b.completed_at is None
        ]
        
        return {
            "summary": {
                "total_tasks": len(self._task_metrics),
                "completed": sum(1 for m in self._task_metrics.values() if m.status == "completed"),
                "failed": sum(1 for m in self._task_metrics.values() if m.status == "failed"),
                "running": sum(1 for m in self._task_metrics.values() if m.status == "running"),
                "pending": sum(1 for m in self._task_metrics.values() if m.status == "pending"),
                "total_batches": len(self._batch_metrics),
                "active_batches": len(active_batches)
            },
            "hourly_stats": hourly_stats,
            "type_stats": type_stats,
            "recent_tasks": [
                {
                    "task_id": t.task_id,
                    "type": t.task_type,
                    "status": t.status,
                    "duration_ms": t.duration_ms,
                    "created_at": t.created_at.isoformat(),
                    "retry_count": t.retry_count
                }
                for t in recent_tasks
            ],
            "active_batches": active_batches
        }

    def get_grafana_dashboard_json(self) -> Dict[str, Any]:
        """生成Grafana仪表盘JSON配置"""
        return {
            "dashboard": {
                "title": "Task Scheduler Dashboard",
                "uid": "task-scheduler",
                "panels": [
                    {
                        "title": "Task Overview",
                        "type": "stat",
                        "gridPos": {"x": 0, "y": 0, "w": 6, "h": 4},
                        "targets": [
                            {"expr": "task_total", "legendFormat": "Total"}
                        ]
                    },
                    {
                        "title": "Completed Tasks",
                        "type": "stat",
                        "gridPos": {"x": 6, "y": 0, "w": 6, "h": 4},
                        "targets": [
                            {"expr": "task_completed", "legendFormat": "Completed"}
                        ]
                    },
                    {
                        "title": "Failed Tasks",
                        "type": "stat",
                        "gridPos": {"x": 12, "y": 0, "w": 6, "h": 4},
                        "targets": [
                            {"expr": "task_failed", "legendFormat": "Failed"}
                        ]
                    },
                    {
                        "title": "Running Tasks",
                        "type": "stat",
                        "gridPos": {"x": 18, "y": 0, "w": 6, "h": 4},
                        "targets": [
                            {"expr": "task_running", "legendFormat": "Running"}
                        ]
                    },
                    {
                        "title": "Task Duration (ms)",
                        "type": "graph",
                        "gridPos": {"x": 0, "y": 4, "w": 12, "h": 8},
                        "targets": [
                            {"expr": "task_duration_ms", "legendFormat": "{{quantile}}"}
                        ]
                    },
                    {
                        "title": "Tasks by Type",
                        "type": "piechart",
                        "gridPos": {"x": 12, "y": 4, "w": 12, "h": 8},
                        "targets": [
                            {"expr": "task_by_type", "legendFormat": "{{type}}"}
                        ]
                    },
                    {
                        "title": "Batch Tasks",
                        "type": "graph",
                        "gridPos": {"x": 0, "y": 12, "w": 24, "h": 8},
                        "targets": [
                            {"expr": "batch_total", "legendFormat": "Total Batches"},
                            {"expr": "batch_avg_size", "legendFormat": "Avg Batch Size"}
                        ]
                    }
                ],
                "schemaVersion": 27,
                "version": 1,
                "refresh": "30s"
            }
        }


_metrics_collector: Optional[TaskMetricsCollector] = None


def get_metrics_collector() -> TaskMetricsCollector:
    """获取全局指标收集器"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = TaskMetricsCollector()
    return _metrics_collector
