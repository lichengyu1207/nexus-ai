"""
记忆版本控制模块 - 快照回滚
定期快照，支持按时间点回滚，防止记忆污染
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import asyncio
import json
import logging
import hashlib
from collections import defaultdict

logger = logging.getLogger(__name__)


class SnapshotType(Enum):
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"


class MemoryType(Enum):
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"
    WORKING = "working"


class RollbackStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class MemorySnapshot:
    snapshot_id: str
    agent_id: str
    snapshot_type: SnapshotType
    memory_type: MemoryType
    timestamp: datetime
    data_hash: str
    size_bytes: int
    memory_count: int
    parent_snapshot_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    storage_path: Optional[str] = None
    is_valid: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "agent_id": self.agent_id,
            "snapshot_type": self.snapshot_type.value,
            "memory_type": self.memory_type.value,
            "timestamp": self.timestamp.isoformat(),
            "data_hash": self.data_hash,
            "size_bytes": self.size_bytes,
            "memory_count": self.memory_count,
            "parent_snapshot_id": self.parent_snapshot_id,
            "metadata": self.metadata,
            "storage_path": self.storage_path,
            "is_valid": self.is_valid
        }


@dataclass
class MemoryVersion:
    version_id: str
    snapshot_id: str
    version_number: int
    created_at: datetime
    description: str
    changes: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class RollbackOperation:
    rollback_id: str
    agent_id: str
    target_snapshot_id: str
    target_timestamp: Optional[datetime]
    status: RollbackStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    affected_memories: int = 0
    error_message: Optional[str] = None


@dataclass
class MemoryChange:
    change_id: str
    snapshot_id: str
    change_type: str
    memory_id: str
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    timestamp: datetime = field(default_factory=datetime.now)


class MemorySnapshotManager:
    def __init__(self):
        self._snapshots: Dict[str, MemorySnapshot] = {}
        self._agent_snapshots: Dict[str, List[str]] = defaultdict(list)
        self._versions: Dict[str, MemoryVersion] = {}
        self._changes: Dict[str, List[MemoryChange]] = defaultdict(list)
        self._rollback_history: List[RollbackOperation] = []
        self._max_snapshots_per_agent = 50
        self._snapshot_interval_hours = 6
        
    def create_snapshot(
        self,
        agent_id: str,
        memory_type: MemoryType,
        memory_data: List[Dict[str, Any]],
        snapshot_type: SnapshotType = SnapshotType.FULL,
        parent_snapshot_id: Optional[str] = None
    ) -> MemorySnapshot:
        snapshot_id = self._generate_snapshot_id(agent_id, memory_type)
        
        data_str = json.dumps(memory_data, sort_keys=True, default=str)
        data_hash = hashlib.sha256(data_str.encode()).hexdigest()
        size_bytes = len(data_str.encode())
        
        snapshot = MemorySnapshot(
            snapshot_id=snapshot_id,
            agent_id=agent_id,
            snapshot_type=snapshot_type,
            memory_type=memory_type,
            timestamp=datetime.now(),
            data_hash=data_hash,
            size_bytes=size_bytes,
            memory_count=len(memory_data),
            parent_snapshot_id=parent_snapshot_id,
            storage_path=f"snapshots/{agent_id}/{snapshot_id}.json"
        )
        
        self._snapshots[snapshot_id] = snapshot
        self._agent_snapshots[agent_id].append(snapshot_id)
        
        self._cleanup_old_snapshots(agent_id)
        
        logger.info(f"Created snapshot: {snapshot_id} for agent {agent_id}")
        return snapshot
        
    def _generate_snapshot_id(self, agent_id: str, memory_type: MemoryType) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"snap_{agent_id}_{memory_type.value}_{timestamp}"
        
    def _cleanup_old_snapshots(self, agent_id: str):
        snapshot_ids = self._agent_snapshots[agent_id]
        
        if len(snapshot_ids) > self._max_snapshots_per_agent:
            snapshots = [self._snapshots[sid] for sid in snapshot_ids if sid in self._snapshots]
            
            full_snapshots = [s for s in snapshots if s.snapshot_type == SnapshotType.FULL]
            incremental_snapshots = [s for s in snapshots if s.snapshot_type == SnapshotType.INCREMENTAL]
            
            incremental_snapshots.sort(key=lambda s: s.timestamp)
            
            while len(snapshot_ids) > self._max_snapshots_per_agent and incremental_snapshots:
                old_snapshot = incremental_snapshots.pop(0)
                if old_snapshot.snapshot_id in self._snapshots:
                    del self._snapshots[old_snapshot.snapshot_id]
                if old_snapshot.snapshot_id in snapshot_ids:
                    snapshot_ids.remove(old_snapshot.snapshot_id)
                    
    def get_snapshot(self, snapshot_id: str) -> Optional[MemorySnapshot]:
        return self._snapshots.get(snapshot_id)
        
    def get_agent_snapshots(
        self,
        agent_id: str,
        memory_type: Optional[MemoryType] = None
    ) -> List[MemorySnapshot]:
        snapshot_ids = self._agent_snapshots.get(agent_id, [])
        snapshots = [self._snapshots[sid] for sid in snapshot_ids if sid in self._snapshots]
        
        if memory_type:
            snapshots = [s for s in snapshots if s.memory_type == memory_type]
            
        return sorted(snapshots, key=lambda s: s.timestamp, reverse=True)
        
    def get_snapshot_at_time(
        self,
        agent_id: str,
        target_time: datetime,
        memory_type: Optional[MemoryType] = None
    ) -> Optional[MemorySnapshot]:
        snapshots = self.get_agent_snapshots(agent_id, memory_type)
        
        for snapshot in snapshots:
            if snapshot.timestamp <= target_time:
                return snapshot
                
        return None
        
    def record_change(
        self,
        snapshot_id: str,
        change_type: str,
        memory_id: str,
        old_value: Any = None,
        new_value: Any = None
    ):
        change = MemoryChange(
            change_id=f"change_{snapshot_id}_{memory_id}_{datetime.now().timestamp()}",
            snapshot_id=snapshot_id,
            change_type=change_type,
            memory_id=memory_id,
            old_value=old_value,
            new_value=new_value
        )
        
        self._changes[snapshot_id].append(change)
        
    def get_changes(self, snapshot_id: str) -> List[MemoryChange]:
        return self._changes.get(snapshot_id, [])


class MemoryRollbackManager:
    def __init__(self, snapshot_manager: MemorySnapshotManager):
        self.snapshot_manager = snapshot_manager
        self._rollback_history: List[RollbackOperation] = []
        self._current_memories: Dict[str, List[Dict[str, Any]]] = {}
        
    def set_current_memory(
        self,
        agent_id: str,
        memory_type: MemoryType,
        memories: List[Dict[str, Any]]
    ):
        key = f"{agent_id}_{memory_type.value}"
        self._current_memories[key] = memories
        
    def get_current_memory(
        self,
        agent_id: str,
        memory_type: MemoryType
    ) -> List[Dict[str, Any]]:
        key = f"{agent_id}_{memory_type.value}"
        return self._current_memories.get(key, [])
        
    async def rollback_to_snapshot(
        self,
        agent_id: str,
        snapshot_id: str,
        memory_data: List[Dict[str, Any]]
    ) -> RollbackOperation:
        snapshot = self.snapshot_manager.get_snapshot(snapshot_id)
        
        if not snapshot:
            return RollbackOperation(
                rollback_id=f"rollback_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                agent_id=agent_id,
                target_snapshot_id=snapshot_id,
                target_timestamp=None,
                status=RollbackStatus.FAILED,
                started_at=datetime.now(),
                error_message="Snapshot not found"
            )
            
        rollback = RollbackOperation(
            rollback_id=f"rollback_{agent_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            agent_id=agent_id,
            target_snapshot_id=snapshot_id,
            target_timestamp=snapshot.timestamp,
            status=RollbackStatus.IN_PROGRESS,
            started_at=datetime.now()
        )
        
        try:
            current_memories = self.get_current_memory(agent_id, snapshot.memory_type)
            
            pre_snapshot = self.snapshot_manager.create_snapshot(
                agent_id=agent_id,
                memory_type=snapshot.memory_type,
                memory_data=current_memories,
                snapshot_type=SnapshotType.FULL,
                parent_snapshot_id=None
            )
            pre_snapshot.metadata["rollback_pre_snapshot"] = True
            pre_snapshot.metadata["rollback_target"] = snapshot_id
            
            self.set_current_memory(agent_id, snapshot.memory_type, memory_data)
            
            rollback.status = RollbackStatus.COMPLETED
            rollback.completed_at = datetime.now()
            rollback.affected_memories = len(current_memories)
            
            logger.info(f"Rollback completed: {rollback.rollback_id}")
            
        except Exception as e:
            rollback.status = RollbackStatus.FAILED
            rollback.error_message = str(e)
            logger.error(f"Rollback failed: {e}")
            
        self._rollback_history.append(rollback)
        return rollback
        
    async def rollback_to_time(
        self,
        agent_id: str,
        target_time: datetime,
        memory_type: MemoryType,
        memory_data: List[Dict[str, Any]]
    ) -> Optional[RollbackOperation]:
        snapshot = self.snapshot_manager.get_snapshot_at_time(
            agent_id, target_time, memory_type
        )
        
        if not snapshot:
            logger.warning(f"No snapshot found before {target_time}")
            return None
            
        return await self.rollback_to_snapshot(agent_id, snapshot.snapshot_id, memory_data)
        
    def get_rollback_history(
        self,
        agent_id: Optional[str] = None
    ) -> List[RollbackOperation]:
        if agent_id:
            return [r for r in self._rollback_history if r.agent_id == agent_id]
        return self._rollback_history


class MemoryIntegrityChecker:
    def __init__(self, snapshot_manager: MemorySnapshotManager):
        self.snapshot_manager = snapshot_manager
        self._integrity_issues: List[Dict[str, Any]] = []
        
    def verify_snapshot(self, snapshot: MemorySnapshot, data: List[Dict[str, Any]]) -> bool:
        data_str = json.dumps(data, sort_keys=True, default=str)
        computed_hash = hashlib.sha256(data_str.encode()).hexdigest()
        
        if computed_hash != snapshot.data_hash:
            self._integrity_issues.append({
                "snapshot_id": snapshot.snapshot_id,
                "issue": "hash_mismatch",
                "expected": snapshot.data_hash,
                "computed": computed_hash,
                "timestamp": datetime.now().isoformat()
            })
            return False
            
        if len(data) != snapshot.memory_count:
            self._integrity_issues.append({
                "snapshot_id": snapshot.snapshot_id,
                "issue": "count_mismatch",
                "expected": snapshot.memory_count,
                "actual": len(data),
                "timestamp": datetime.now().isoformat()
            })
            return False
            
        return True
        
    def detect_pollution(
        self,
        memories: List[Dict[str, Any]],
        rules: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        polluted = []
        
        for memory in memories:
            for rule in rules:
                if self._check_pollution_rule(memory, rule):
                    polluted.append({
                        "memory_id": memory.get("id", "unknown"),
                        "rule_matched": rule.get("name", "unknown"),
                        "reason": rule.get("description", ""),
                        "memory": memory
                    })
                    break
                    
        return polluted
        
    def _check_pollution_rule(
        self,
        memory: Dict[str, Any],
        rule: Dict[str, Any]
    ) -> bool:
        content = memory.get("content", "")
        
        if rule.get("type") == "keyword":
            keywords = rule.get("keywords", [])
            return any(kw in content for kw in keywords)
            
        elif rule.get("type") == "pattern":
            import re
            pattern = rule.get("pattern", "")
            return bool(re.search(pattern, content))
            
        elif rule.get("type") == "threshold":
            field = rule.get("field", "importance")
            threshold = rule.get("threshold", 0)
            return memory.get(field, 0) < threshold
            
        return False
        
    def get_integrity_issues(self) -> List[Dict[str, Any]]:
        return self._integrity_issues


class MemoryVersionControl:
    def __init__(self):
        self.snapshot_manager = MemorySnapshotManager()
        self.rollback_manager = MemoryRollbackManager(self.snapshot_manager)
        self.integrity_checker = MemoryIntegrityChecker(self.snapshot_manager)
        self._auto_snapshot_enabled = True
        self._snapshot_interval = timedelta(hours=6)
        self._last_snapshot_time: Dict[str, datetime] = {}
        
    async def auto_snapshot(
        self,
        agent_id: str,
        memory_type: MemoryType,
        memories: List[Dict[str, Any]]
    ) -> Optional[MemorySnapshot]:
        if not self._auto_snapshot_enabled:
            return None
            
        key = f"{agent_id}_{memory_type.value}"
        last_time = self._last_snapshot_time.get(key)
        
        if last_time and datetime.now() - last_time < self._snapshot_interval:
            return None
            
        snapshot = self.snapshot_manager.create_snapshot(
            agent_id=agent_id,
            memory_type=memory_type,
            memory_data=memories,
            snapshot_type=SnapshotType.FULL
        )
        
        self._last_snapshot_time[key] = datetime.now()
        return snapshot
        
    def create_version(
        self,
        agent_id: str,
        snapshot_id: str,
        description: str
    ) -> MemoryVersion:
        snapshot = self.snapshot_manager.get_snapshot(snapshot_id)
        if not snapshot:
            raise ValueError(f"Snapshot not found: {snapshot_id}")
            
        agent_versions = [
            v for v in self.snapshot_manager._versions.values()
            if v.snapshot_id.startswith(f"v_{agent_id}")
        ]
        version_number = len(agent_versions) + 1
        
        version = MemoryVersion(
            version_id=f"v_{agent_id}_{version_number}",
            snapshot_id=snapshot_id,
            version_number=version_number,
            created_at=datetime.now(),
            description=description,
            changes=self.snapshot_manager.get_changes(snapshot_id)
        )
        
        self.snapshot_manager._versions[version.version_id] = version
        return version
        
    def list_versions(self, agent_id: str) -> List[MemoryVersion]:
        versions = [
            v for v in self.snapshot_manager._versions.values()
            if v.version_id.startswith(f"v_{agent_id}")
        ]
        return sorted(versions, key=lambda v: v.version_number, reverse=True)
        
    def compare_snapshots(
        self,
        snapshot_id1: str,
        snapshot_id2: str
    ) -> Dict[str, Any]:
        snapshot1 = self.snapshot_manager.get_snapshot(snapshot_id1)
        snapshot2 = self.snapshot_manager.get_snapshot(snapshot_id2)
        
        if not snapshot1 or not snapshot2:
            return {"error": "One or both snapshots not found"}
            
        changes1 = self.snapshot_manager.get_changes(snapshot_id1)
        changes2 = self.snapshot_manager.get_changes(snapshot_id2)
        
        return {
            "snapshot1": {
                "id": snapshot_id1,
                "timestamp": snapshot1.timestamp.isoformat(),
                "memory_count": snapshot1.memory_count,
                "changes_count": len(changes1)
            },
            "snapshot2": {
                "id": snapshot_id2,
                "timestamp": snapshot2.timestamp.isoformat(),
                "memory_count": snapshot2.memory_count,
                "changes_count": len(changes2)
            },
            "memory_diff": snapshot2.memory_count - snapshot1.memory_count,
            "time_diff_seconds": (snapshot2.timestamp - snapshot1.timestamp).total_seconds()
        }
        
    def get_snapshot_chain(self, snapshot_id: str) -> List[MemorySnapshot]:
        chain = []
        current = self.snapshot_manager.get_snapshot(snapshot_id)
        
        while current:
            chain.append(current)
            if current.parent_snapshot_id:
                current = self.snapshot_manager.get_snapshot(current.parent_snapshot_id)
            else:
                break
                
        return chain


memory_version_control = MemoryVersionControl()


def get_version_control() -> MemoryVersionControl:
    return memory_version_control


async def create_memory_snapshot(
    agent_id: str,
    memory_type: MemoryType,
    memories: List[Dict[str, Any]]
) -> MemorySnapshot:
    return memory_version_control.snapshot_manager.create_snapshot(
        agent_id=agent_id,
        memory_type=memory_type,
        memory_data=memories
    )
