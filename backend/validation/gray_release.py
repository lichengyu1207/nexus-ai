"""
灰度发布控制器
Gray Release Controller

提供模型灰度发布功能，支持渐进式发布和自动回滚
"""

import os
import json
import logging
import time
import random
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import asyncio
from collections import defaultdict

logger = logging.getLogger(__name__)


class ReleaseStatus(Enum):
    DRAFT = "draft"
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


class ReleaseStage(Enum):
    CANARY = "canary"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    FULL = "full"


@dataclass
class StageConfig:
    name: str
    traffic_percentage: float
    duration_minutes: int
    success_threshold: float = 0.95
    error_rate_threshold: float = 0.01
    latency_threshold: float = 100.0
    auto_advance: bool = True


@dataclass
class ReleaseMetrics:
    requests_total: int = 0
    requests_success: int = 0
    requests_failed: int = 0
    error_rate: float = 0.0
    latency_p50: float = 0.0
    latency_p95: float = 0.0
    latency_p99: float = 0.0
    user_satisfaction: float = 0.0
    conversion_rate: float = 0.0


@dataclass
class ReleaseStageResult:
    stage: str
    status: str
    start_time: float
    end_time: Optional[float] = None
    metrics: Optional[ReleaseMetrics] = None
    passed: bool = False
    rollback_triggered: bool = False
    message: str = ""


class GrayReleaseController:
    """
    灰度发布控制器
    
    功能：
    1. 多阶段渐进发布 (金丝雀 -> 小流量 -> 中流量 -> 大流量 -> 全量)
    2. 实时监控和自动回滚
    3. 用户分桶和流量分配
    4. 发布审批流程
    5. 发布历史追踪
    """
    
    DEFAULT_STAGES = [
        StageConfig("canary", 1.0, 30, 0.99, 0.001, 50.0),
        StageConfig("small", 5.0, 60, 0.98, 0.005, 80.0),
        StageConfig("medium", 20.0, 120, 0.97, 0.008, 100.0),
        StageConfig("large", 50.0, 180, 0.96, 0.01, 120.0),
        StageConfig("full", 100.0, 0, 0.95, 0.01, 150.0),
    ]
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.stages: List[StageConfig] = self.config.get("stages", self.DEFAULT_STAGES)
        
        self.releases: Dict[str, Dict] = {}
        self.current_release: Optional[str] = None
        
        self.user_buckets: Dict[str, str] = {}
        self.bucket_count = self.config.get("bucket_count", 1000)
        
        self.metrics_collector: Optional[Callable] = None
        self.rollback_handler: Optional[Callable] = None
        
        self._monitoring_task: Optional[asyncio.Task] = None
        
        logger.info("GrayReleaseController initialized with %d stages", len(self.stages))
    
    def set_metrics_collector(self, collector: Callable):
        self.metrics_collector = collector
    
    def set_rollback_handler(self, handler: Callable):
        self.rollback_handler = handler
    
    def create_release(
        self,
        release_id: str,
        model_version: str,
        description: str = "",
        stages: Optional[List[StageConfig]] = None,
        approval_required: bool = True,
        target_users: Optional[List[str]] = None,
        exclude_users: Optional[List[str]] = None
    ) -> Dict:
        """创建发布计划"""
        if release_id in self.releases:
            raise ValueError(f"Release {release_id} already exists")
        
        release_stages = stages or self.stages
        
        release = {
            "release_id": release_id,
            "model_version": model_version,
            "description": description,
            "status": ReleaseStatus.DRAFT.value,
            "stages": [
                {
                    "name": s.name,
                    "traffic_percentage": s.traffic_percentage,
                    "duration_minutes": s.duration_minutes,
                    "success_threshold": s.success_threshold,
                    "error_rate_threshold": s.error_rate_threshold,
                    "latency_threshold": s.latency_threshold,
                    "auto_advance": s.auto_advance,
                }
                for s in release_stages
            ],
            "current_stage_index": 0,
            "stage_results": [],
            "approval_required": approval_required,
            "approved": False,
            "approver": None,
            "approval_time": None,
            "target_users": target_users or [],
            "exclude_users": exclude_users or [],
            "created_at": time.time(),
            "started_at": None,
            "completed_at": None,
            "metrics_history": [],
        }
        
        self.releases[release_id] = release
        logger.info(f"Created release {release_id} for model {model_version}")
        
        return release
    
    def approve_release(self, release_id: str, approver: str) -> Dict:
        """审批发布"""
        if release_id not in self.releases:
            raise ValueError(f"Release {release_id} not found")
        
        release = self.releases[release_id]
        
        if release["status"] != ReleaseStatus.DRAFT.value:
            raise ValueError(f"Release {release_id} is not in draft status")
        
        release["approved"] = True
        release["approver"] = approver
        release["approval_time"] = time.time()
        release["status"] = ReleaseStatus.PENDING.value
        
        logger.info(f"Release {release_id} approved by {approver}")
        return release
    
    def start_release(self, release_id: str) -> Dict:
        """开始发布"""
        if release_id not in self.releases:
            raise ValueError(f"Release {release_id} not found")
        
        release = self.releases[release_id]
        
        if release["approval_required"] and not release["approved"]:
            raise ValueError(f"Release {release_id} requires approval")
        
        if release["status"] not in [ReleaseStatus.DRAFT.value, ReleaseStatus.PENDING.value]:
            raise ValueError(f"Release {release_id} cannot be started from {release['status']}")
        
        release["status"] = ReleaseStatus.RUNNING.value
        release["started_at"] = time.time()
        release["current_stage_index"] = 0
        
        stage_result = ReleaseStageResult(
            stage=release["stages"][0]["name"],
            status="running",
            start_time=time.time()
        )
        release["stage_results"].append(stage_result.__dict__)
        
        self.current_release = release_id
        
        logger.info(f"Started release {release_id} at stage {release['stages'][0]['name']}")
        return release
    
    def advance_stage(self, release_id: str) -> Dict:
        """推进到下一阶段"""
        if release_id not in self.releases:
            raise ValueError(f"Release {release_id} not found")
        
        release = self.releases[release_id]
        
        if release["status"] != ReleaseStatus.RUNNING.value:
            raise ValueError(f"Release {release_id} is not running")
        
        current_index = release["current_stage_index"]
        current_stage = release["stages"][current_index]
        
        if release["stage_results"]:
            last_result = release["stage_results"][-1]
            last_result["status"] = "completed"
            last_result["end_time"] = time.time()
        
        if current_index >= len(release["stages"]) - 1:
            release["status"] = ReleaseStatus.COMPLETED.value
            release["completed_at"] = time.time()
            self.current_release = None
            logger.info(f"Release {release_id} completed successfully")
            return release
        
        release["current_stage_index"] = current_index + 1
        next_stage = release["stages"][release["current_stage_index"]]
        
        stage_result = ReleaseStageResult(
            stage=next_stage["name"],
            status="running",
            start_time=time.time()
        )
        release["stage_results"].append(stage_result.__dict__)
        
        logger.info(f"Release {release_id} advanced to stage {next_stage['name']}")
        return release
    
    def pause_release(self, release_id: str) -> Dict:
        """暂停发布"""
        if release_id not in self.releases:
            raise ValueError(f"Release {release_id} not found")
        
        release = self.releases[release_id]
        
        if release["status"] != ReleaseStatus.RUNNING.value:
            raise ValueError(f"Release {release_id} is not running")
        
        release["status"] = ReleaseStatus.PAUSED.value
        
        if release["stage_results"]:
            release["stage_results"][-1]["status"] = "paused"
        
        logger.info(f"Release {release_id} paused")
        return release
    
    def resume_release(self, release_id: str) -> Dict:
        """恢复发布"""
        if release_id not in self.releases:
            raise ValueError(f"Release {release_id} not found")
        
        release = self.releases[release_id]
        
        if release["status"] != ReleaseStatus.PAUSED.value:
            raise ValueError(f"Release {release_id} is not paused")
        
        release["status"] = ReleaseStatus.RUNNING.value
        
        if release["stage_results"]:
            release["stage_results"][-1]["status"] = "running"
        
        logger.info(f"Release {release_id} resumed")
        return release
    
    def rollback_release(self, release_id: str, reason: str = "") -> Dict:
        """回滚发布"""
        if release_id not in self.releases:
            raise ValueError(f"Release {release_id} not found")
        
        release = self.releases[release_id]
        
        release["status"] = ReleaseStatus.ROLLED_BACK.value
        release["completed_at"] = time.time()
        
        if release["stage_results"]:
            last_result = release["stage_results"][-1]
            last_result["status"] = "rolled_back"
            last_result["end_time"] = time.time()
            last_result["rollback_triggered"] = True
            last_result["message"] = reason
        
        if self.rollback_handler:
            try:
                self.rollback_handler(release_id, release["model_version"])
            except Exception as e:
                logger.error(f"Rollback handler failed: {e}")
        
        if self.current_release == release_id:
            self.current_release = None
        
        logger.warning(f"Release {release_id} rolled back: {reason}")
        return release
    
    def get_user_bucket(self, user_id: str, release_id: Optional[str] = None) -> str:
        """
        获取用户所属分桶
        
        使用一致性哈希确保用户始终路由到同一版本
        """
        if release_id is None:
            release_id = self.current_release
        
        if release_id is None or release_id not in self.releases:
            return "control"
        
        release = self.releases[release_id]
        
        if release["status"] != ReleaseStatus.RUNNING.value:
            return "control"
        
        if user_id in release["exclude_users"]:
            return "control"
        
        if release["target_users"] and user_id not in release["target_users"]:
            return "control"
        
        hash_value = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
        bucket = hash_value % self.bucket_count
        
        current_stage = release["stages"][release["current_stage_index"]]
        traffic_percentage = current_stage["traffic_percentage"]
        treatment_buckets = int(self.bucket_count * traffic_percentage / 100)
        
        if bucket < treatment_buckets:
            return "treatment"
        return "control"
    
    def should_use_new_version(self, user_id: str, release_id: Optional[str] = None) -> bool:
        """判断用户是否应该使用新版本"""
        return self.get_user_bucket(user_id, release_id) == "treatment"
    
    def record_metrics(self, release_id: str, metrics: ReleaseMetrics):
        """记录指标"""
        if release_id not in self.releases:
            return
        
        release = self.releases[release_id]
        
        metrics_record = {
            "timestamp": time.time(),
            "stage": release["stages"][release["current_stage_index"]]["name"],
            "metrics": {
                "requests_total": metrics.requests_total,
                "requests_success": metrics.requests_success,
                "requests_failed": metrics.requests_failed,
                "error_rate": metrics.error_rate,
                "latency_p50": metrics.latency_p50,
                "latency_p95": metrics.latency_p95,
                "latency_p99": metrics.latency_p99,
            }
        }
        
        release["metrics_history"].append(metrics_record)
        
        if len(release["metrics_history"]) > 10000:
            release["metrics_history"] = release["metrics_history"][-10000:]
    
    def check_stage_health(self, release_id: str) -> Dict:
        """检查当前阶段健康状态"""
        if release_id not in self.releases:
            return {"error": "Release not found"}
        
        release = self.releases[release_id]
        
        if release["status"] != ReleaseStatus.RUNNING.value:
            return {"status": release["status"]}
        
        current_stage = release["stages"][release["current_stage_index"]]
        
        recent_metrics = release["metrics_history"][-100:] if release["metrics_history"] else []
        
        if not recent_metrics:
            return {
                "status": "running",
                "stage": current_stage["name"],
                "message": "No metrics available yet"
            }
        
        avg_error_rate = sum(m["metrics"]["error_rate"] for m in recent_metrics) / len(recent_metrics)
        avg_latency_p95 = sum(m["metrics"]["latency_p95"] for m in recent_metrics) / len(recent_metrics)
        
        total_requests = sum(m["metrics"]["requests_total"] for m in recent_metrics)
        total_success = sum(m["metrics"]["requests_success"] for m in recent_metrics)
        success_rate = total_success / total_requests if total_requests > 0 else 0
        
        health_status = "healthy"
        issues = []
        
        if avg_error_rate > current_stage["error_rate_threshold"]:
            health_status = "unhealthy"
            issues.append(f"Error rate {avg_error_rate:.2%} exceeds threshold {current_stage['error_rate_threshold']:.2%}")
        
        if avg_latency_p95 > current_stage["latency_threshold"]:
            health_status = "degraded"
            issues.append(f"Latency P95 {avg_latency_p95:.2f}ms exceeds threshold {current_stage['latency_threshold']:.2f}ms")
        
        if success_rate < current_stage["success_threshold"]:
            health_status = "unhealthy"
            issues.append(f"Success rate {success_rate:.2%} below threshold {current_stage['success_threshold']:.2%}")
        
        result = {
            "status": health_status,
            "stage": current_stage["name"],
            "metrics": {
                "error_rate": avg_error_rate,
                "latency_p95": avg_latency_p95,
                "success_rate": success_rate,
            },
            "thresholds": {
                "error_rate": current_stage["error_rate_threshold"],
                "latency_p95": current_stage["latency_threshold"],
                "success_rate": current_stage["success_threshold"],
            },
            "issues": issues,
            "should_rollback": health_status == "unhealthy",
            "can_advance": health_status in ["healthy", "degraded"] and len(issues) == 0,
        }
        
        return result
    
    def auto_advance_check(self, release_id: str) -> Dict:
        """自动推进检查"""
        health = self.check_stage_health(release_id)
        
        if health.get("should_rollback"):
            return {
                "action": "rollback",
                "reason": health.get("issues", ["Health check failed"]),
            }
        
        if health.get("can_advance"):
            release = self.releases.get(release_id)
            if release:
                current_stage = release["stages"][release["current_stage_index"]]
                if current_stage.get("auto_advance", True):
                    stage_start = release["stage_results"][-1]["start_time"]
                    elapsed_minutes = (time.time() - stage_start) / 60
                    
                    if elapsed_minutes >= current_stage["duration_minutes"]:
                        return {
                            "action": "advance",
                            "reason": f"Stage duration {current_stage['duration_minutes']} minutes completed",
                        }
        
        return {
            "action": "continue",
            "reason": "Stage still in progress",
        }
    
    def get_release_status(self, release_id: str) -> Dict:
        """获取发布状态"""
        if release_id not in self.releases:
            return {"error": "Release not found"}
        
        release = self.releases[release_id]
        
        return {
            "release_id": release["release_id"],
            "model_version": release["model_version"],
            "status": release["status"],
            "current_stage": release["stages"][release["current_stage_index"]]["name"] if release["current_stage_index"] < len(release["stages"]) else "completed",
            "traffic_percentage": release["stages"][release["current_stage_index"]]["traffic_percentage"] if release["current_stage_index"] < len(release["stages"]) else 100.0,
            "stage_progress": f"{release['current_stage_index'] + 1}/{len(release['stages'])}",
            "created_at": datetime.fromtimestamp(release["created_at"]).isoformat(),
            "started_at": datetime.fromtimestamp(release["started_at"]).isoformat() if release["started_at"] else None,
            "completed_at": datetime.fromtimestamp(release["completed_at"]).isoformat() if release["completed_at"] else None,
            "approved": release["approved"],
            "approver": release["approver"],
        }
    
    def list_releases(self, status: Optional[str] = None) -> List[Dict]:
        """列出发布"""
        releases = []
        
        for release_id, release in self.releases.items():
            if status is None or release["status"] == status:
                releases.append(self.get_release_status(release_id))
        
        return releases
    
    def export_release_history(self, filepath: str):
        """导出发布历史"""
        data = {
            "releases": self.releases,
            "exported_at": datetime.now().isoformat(),
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"Exported release history to {filepath}")


_global_controller: Optional[GrayReleaseController] = None


def get_controller() -> GrayReleaseController:
    """获取全局控制器实例"""
    global _global_controller
    if _global_controller is None:
        _global_controller = GrayReleaseController()
    return _global_controller
