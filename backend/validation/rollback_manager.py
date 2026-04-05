"""
回滚管理器
Rollback Manager

提供模型版本回滚功能，支持自动和手动回滚
"""

import os
import json
import logging
import time
import shutil
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import asyncio
from collections import defaultdict

logger = logging.getLogger(__name__)


class RollbackStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RollbackTrigger(Enum):
    MANUAL = "manual"
    AUTO_ERROR_RATE = "auto_error_rate"
    AUTO_LATENCY = "auto_latency"
    AUTO_ACCURACY = "auto_accuracy"
    AUTO_USER_FEEDBACK = "auto_user_feedback"
    SCHEDULED = "scheduled"


@dataclass
class VersionSnapshot:
    version_id: str
    model_path: str
    config_path: Optional[str]
    checksum: str
    created_at: float
    metrics: Dict[str, float]
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_stable: bool = True
    rollback_count: int = 0


@dataclass
class RollbackRecord:
    rollback_id: str
    from_version: str
    to_version: str
    trigger: RollbackTrigger
    status: RollbackStatus
    reason: str
    started_at: float
    completed_at: Optional[float] = None
    duration: float = 0.0
    error_message: Optional[str] = None
    metrics_before: Dict[str, float] = field(default_factory=dict)
    metrics_after: Dict[str, float] = field(default_factory=dict)


class RollbackManager:
    """
    回滚管理器
    
    功能：
    1. 版本快照管理
    2. 自动回滚触发
    3. 回滚执行和验证
    4. 回滚历史追踪
    5. 回滚影响评估
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        self.versions: Dict[str, VersionSnapshot] = {}
        self.current_version: Optional[str] = None
        self.stable_versions: List[str] = []
        
        self.rollback_history: List[RollbackRecord] = []
        self.max_history = self.config.get("max_history", 100)
        
        self.auto_rollback_enabled = self.config.get("auto_rollback_enabled", True)
        self.auto_rollback_thresholds = {
            "error_rate": self.config.get("error_rate_threshold", 0.05),
            "latency_p95": self.config.get("latency_threshold", 500.0),
            "accuracy": self.config.get("accuracy_threshold", 0.85),
            "user_satisfaction": self.config.get("satisfaction_threshold", 3.5),
        }
        
        self.pre_rollback_hooks: List[Callable] = []
        self.post_rollback_hooks: List[Callable] = []
        self.validation_hooks: List[Callable] = []
        
        self.backup_dir = self.config.get("backup_dir", "./backups/versions")
        os.makedirs(self.backup_dir, exist_ok=True)
        
        logger.info("RollbackManager initialized")
    
    def register_version(
        self,
        version_id: str,
        model_path: str,
        config_path: Optional[str] = None,
        metrics: Optional[Dict[str, float]] = None,
        metadata: Optional[Dict] = None,
        make_current: bool = True
    ) -> VersionSnapshot:
        """注册新版本"""
        checksum = self._calculate_checksum(model_path) if os.path.exists(model_path) else ""
        
        snapshot = VersionSnapshot(
            version_id=version_id,
            model_path=model_path,
            config_path=config_path,
            checksum=checksum,
            created_at=time.time(),
            metrics=metrics or {},
            metadata=metadata or {},
        )
        
        self.versions[version_id] = snapshot
        
        if make_current:
            if self.current_version and self.current_version in self.versions:
                self.stable_versions.append(self.current_version)
            self.current_version = version_id
        
        self._backup_version(snapshot)
        
        logger.info(f"Registered version {version_id}")
        return snapshot
    
    def _calculate_checksum(self, filepath: str) -> str:
        """计算文件校验和"""
        hash_md5 = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _backup_version(self, snapshot: VersionSnapshot):
        """备份版本"""
        if not os.path.exists(snapshot.model_path):
            return
        
        backup_path = os.path.join(self.backup_dir, snapshot.version_id)
        os.makedirs(backup_path, exist_ok=True)
        
        model_backup = os.path.join(backup_path, os.path.basename(snapshot.model_path))
        shutil.copy2(snapshot.model_path, model_backup)
        
        if snapshot.config_path and os.path.exists(snapshot.config_path):
            config_backup = os.path.join(backup_path, os.path.basename(snapshot.config_path))
            shutil.copy2(snapshot.config_path, config_backup)
        
        meta_path = os.path.join(backup_path, "metadata.json")
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(snapshot.__dict__, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"Backed up version {snapshot.version_id}")
    
    def add_pre_rollback_hook(self, hook: Callable):
        """添加回滚前钩子"""
        self.pre_rollback_hooks.append(hook)
    
    def add_post_rollback_hook(self, hook: Callable):
        """添加回滚后钩子"""
        self.post_rollback_hooks.append(hook)
    
    def add_validation_hook(self, hook: Callable):
        """添加验证钩子"""
        self.validation_hooks.append(hook)
    
    def check_auto_rollback(self, current_metrics: Dict[str, float]) -> Optional[Dict]:
        """检查是否需要自动回滚"""
        if not self.auto_rollback_enabled:
            return None
        
        if not self.stable_versions:
            return None
        
        triggers = []
        
        error_rate = current_metrics.get("error_rate", 0)
        if error_rate > self.auto_rollback_thresholds["error_rate"]:
            triggers.append({
                "type": RollbackTrigger.AUTO_ERROR_RATE.value,
                "current": error_rate,
                "threshold": self.auto_rollback_thresholds["error_rate"],
            })
        
        latency_p95 = current_metrics.get("latency_p95", 0)
        if latency_p95 > self.auto_rollback_thresholds["latency_p95"]:
            triggers.append({
                "type": RollbackTrigger.AUTO_LATENCY.value,
                "current": latency_p95,
                "threshold": self.auto_rollback_thresholds["latency_p95"],
            })
        
        accuracy = current_metrics.get("accuracy", 1.0)
        if accuracy < self.auto_rollback_thresholds["accuracy"]:
            triggers.append({
                "type": RollbackTrigger.AUTO_ACCURACY.value,
                "current": accuracy,
                "threshold": self.auto_rollback_thresholds["accuracy"],
            })
        
        if triggers:
            return {
                "should_rollback": True,
                "triggers": triggers,
                "target_version": self.stable_versions[-1],
            }
        
        return None
    
    def execute_rollback(
        self,
        target_version: str,
        trigger: RollbackTrigger = RollbackTrigger.MANUAL,
        reason: str = ""
    ) -> RollbackRecord:
        """执行回滚"""
        if target_version not in self.versions:
            raise ValueError(f"Target version {target_version} not found")
        
        if not self.current_version:
            raise ValueError("No current version to rollback from")
        
        from_version = self.current_version
        to_version = target_version
        
        rollback_id = f"rb_{int(time.time())}_{from_version}_to_{to_version}"
        
        record = RollbackRecord(
            rollback_id=rollback_id,
            from_version=from_version,
            to_version=to_version,
            trigger=trigger,
            status=RollbackStatus.PENDING,
            reason=reason,
            started_at=time.time(),
            metrics_before=self.versions[from_version].metrics.copy() if from_version in self.versions else {},
        )
        
        try:
            for hook in self.pre_rollback_hooks:
                try:
                    hook(from_version, to_version)
                except Exception as e:
                    logger.warning(f"Pre-rollback hook failed: {e}")
            
            record.status = RollbackStatus.RUNNING
            
            target_snapshot = self.versions[to_version]
            
            if not self._verify_backup(target_snapshot):
                raise ValueError(f"Backup verification failed for version {to_version}")
            
            self._restore_version(target_snapshot)
            
            self.current_version = to_version
            
            if from_version in self.versions:
                self.versions[from_version].rollback_count += 1
            
            for hook in self.validation_hooks:
                try:
                    if not hook(to_version):
                        raise ValueError(f"Validation hook failed for version {to_version}")
                except Exception as e:
                    logger.warning(f"Validation hook error: {e}")
            
            record.status = RollbackStatus.COMPLETED
            record.completed_at = time.time()
            record.duration = record.completed_at - record.started_at
            record.metrics_after = target_snapshot.metrics.copy()
            
            for hook in self.post_rollback_hooks:
                try:
                    hook(from_version, to_version, record)
                except Exception as e:
                    logger.warning(f"Post-rollback hook failed: {e}")
            
            logger.info(f"Rollback completed: {from_version} -> {to_version}")
            
        except Exception as e:
            record.status = RollbackStatus.FAILED
            record.completed_at = time.time()
            record.duration = record.completed_at - record.started_at
            record.error_message = str(e)
            
            logger.error(f"Rollback failed: {e}")
        
        self.rollback_history.append(record)
        
        if len(self.rollback_history) > self.max_history:
            self.rollback_history = self.rollback_history[-self.max_history:]
        
        return record
    
    def _verify_backup(self, snapshot: VersionSnapshot) -> bool:
        """验证备份完整性"""
        backup_path = os.path.join(self.backup_dir, snapshot.version_id)
        
        if not os.path.exists(backup_path):
            logger.error(f"Backup path not found: {backup_path}")
            return False
        
        model_backup = os.path.join(backup_path, os.path.basename(snapshot.model_path))
        if not os.path.exists(model_backup):
            logger.error(f"Model backup not found: {model_backup}")
            return False
        
        current_checksum = self._calculate_checksum(model_backup)
        if current_checksum != snapshot.checksum:
            logger.error(f"Checksum mismatch for {snapshot.version_id}")
            return False
        
        return True
    
    def _restore_version(self, snapshot: VersionSnapshot):
        """恢复版本"""
        backup_path = os.path.join(self.backup_dir, snapshot.version_id)
        
        model_backup = os.path.join(backup_path, os.path.basename(snapshot.model_path))
        
        if os.path.exists(snapshot.model_path):
            backup_current = snapshot.model_path + ".bak"
            shutil.move(snapshot.model_path, backup_current)
        
        shutil.copy2(model_backup, snapshot.model_path)
        
        if snapshot.config_path:
            config_backup = os.path.join(backup_path, os.path.basename(snapshot.config_path))
            if os.path.exists(config_backup):
                shutil.copy2(config_backup, snapshot.config_path)
        
        logger.info(f"Restored version {snapshot.version_id}")
    
    def get_rollback_history(self, limit: int = 20) -> List[Dict]:
        """获取回滚历史"""
        history = [
            {
                "rollback_id": r.rollback_id,
                "from_version": r.from_version,
                "to_version": r.to_version,
                "trigger": r.trigger.value,
                "status": r.status.value,
                "reason": r.reason,
                "started_at": datetime.fromtimestamp(r.started_at).isoformat(),
                "completed_at": datetime.fromtimestamp(r.completed_at).isoformat() if r.completed_at else None,
                "duration": r.duration,
                "error_message": r.error_message,
            }
            for r in self.rollback_history[-limit:]
        ]
        
        return history
    
    def get_version_info(self, version_id: str) -> Optional[Dict]:
        """获取版本信息"""
        if version_id not in self.versions:
            return None
        
        snapshot = self.versions[version_id]
        
        return {
            "version_id": snapshot.version_id,
            "model_path": snapshot.model_path,
            "checksum": snapshot.checksum,
            "created_at": datetime.fromtimestamp(snapshot.created_at).isoformat(),
            "metrics": snapshot.metrics,
            "metadata": snapshot.metadata,
            "is_stable": snapshot.is_stable,
            "rollback_count": snapshot.rollback_count,
            "is_current": version_id == self.current_version,
        }
    
    def list_versions(self) -> List[Dict]:
        """列出所有版本"""
        return [
            self.get_version_info(vid)
            for vid in self.versions.keys()
        ]
    
    def get_last_stable_version(self) -> Optional[str]:
        """获取最后一个稳定版本"""
        if not self.stable_versions:
            return None
        return self.stable_versions[-1]
    
    def mark_version_stable(self, version_id: str):
        """标记版本为稳定"""
        if version_id not in self.versions:
            return
        
        self.versions[version_id].is_stable = True
        
        if version_id not in self.stable_versions:
            self.stable_versions.append(version_id)
        
        logger.info(f"Marked version {version_id} as stable")
    
    def get_rollback_statistics(self) -> Dict:
        """获取回滚统计"""
        total_rollbacks = len(self.rollback_history)
        
        if total_rollbacks == 0:
            return {
                "total_rollbacks": 0,
                "message": "No rollback history",
            }
        
        successful = sum(1 for r in self.rollback_history if r.status == RollbackStatus.COMPLETED)
        failed = sum(1 for r in self.rollback_history if r.status == RollbackStatus.FAILED)
        
        trigger_counts = defaultdict(int)
        for r in self.rollback_history:
            trigger_counts[r.trigger.value] += 1
        
        avg_duration = sum(r.duration for r in self.rollback_history if r.duration > 0) / max(1, successful)
        
        version_rollback_counts = defaultdict(int)
        for r in self.rollback_history:
            if r.status == RollbackStatus.COMPLETED:
                version_rollback_counts[r.from_version] += 1
        
        most_problematic = max(version_rollback_counts.items(), key=lambda x: x[1]) if version_rollback_counts else (None, 0)
        
        return {
            "total_rollbacks": total_rollbacks,
            "successful": successful,
            "failed": failed,
            "success_rate": successful / total_rollbacks,
            "trigger_breakdown": dict(trigger_counts),
            "average_duration": avg_duration,
            "most_problematic_version": most_problematic[0],
            "most_problematic_count": most_problematic[1],
        }
    
    def export_state(self, filepath: str):
        """导出状态"""
        data = {
            "versions": {
                vid: {
                    "version_id": v.version_id,
                    "model_path": v.model_path,
                    "config_path": v.config_path,
                    "checksum": v.checksum,
                    "created_at": v.created_at,
                    "metrics": v.metrics,
                    "metadata": v.metadata,
                    "is_stable": v.is_stable,
                    "rollback_count": v.rollback_count,
                }
                for vid, v in self.versions.items()
            },
            "current_version": self.current_version,
            "stable_versions": self.stable_versions,
            "rollback_history": [
                {
                    "rollback_id": r.rollback_id,
                    "from_version": r.from_version,
                    "to_version": r.to_version,
                    "trigger": r.trigger.value,
                    "status": r.status.value,
                    "reason": r.reason,
                    "started_at": r.started_at,
                    "completed_at": r.completed_at,
                    "duration": r.duration,
                    "error_message": r.error_message,
                }
                for r in self.rollback_history
            ],
            "exported_at": datetime.now().isoformat(),
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"Exported rollback state to {filepath}")


_global_manager: Optional[RollbackManager] = None


def get_rollback_manager() -> RollbackManager:
    """获取全局回滚管理器实例"""
    global _global_manager
    if _global_manager is None:
        _global_manager = RollbackManager()
    return _global_manager
