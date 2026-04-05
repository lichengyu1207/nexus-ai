"""
分布式审计蜂群协调器
Audit Swarm Coordinator - 协调多个审计智能体协同工作
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set
import asyncio
import json
import uuid
import hashlib


class NodeStatus(Enum):
    ACTIVE = "active"
    IDLE = "idle"
    BUSY = "busy"
    OFFLINE = "offline"
    SYNCING = "syncing"


class TaskStatus(Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class ConsensusType(Enum):
    MAJORITY = "majority"
    UNANIMOUS = "unanimous"
    WEIGHTED = "weighted"


@dataclass
class DistributedAuditNode:
    node_id: str
    node_name: str
    status: NodeStatus = NodeStatus.IDLE
    capabilities: List[str] = field(default_factory=list)
    current_load: float = 0.0
    max_capacity: float = 100.0
    last_heartbeat: datetime = field(default_factory=datetime.utcnow)
    performance_score: float = 1.0
    audit_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AuditTask:
    task_id: str
    task_type: str
    priority: int
    parameters: Dict[str, Any]
    status: TaskStatus = TaskStatus.PENDING
    assigned_nodes: List[str] = field(default_factory=list)
    results: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    deadline: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class SwarmConsensus:
    consensus_id: str
    task_id: str
    consensus_type: ConsensusType
    votes: Dict[str, Any]
    result: Any
    confidence: float
    participating_nodes: List[str]
    reached_at: datetime


class HeartbeatManager:
    def __init__(self, timeout_seconds: int = 30):
        self.timeout_seconds = timeout_seconds
        self.heartbeats: Dict[str, datetime] = {}

    def record_heartbeat(self, node_id: str) -> None:
        self.heartbeats[node_id] = datetime.utcnow()

    def check_node_status(self, node_id: str) -> NodeStatus:
        last_beat = self.heartbeats.get(node_id)
        if not last_beat:
            return NodeStatus.OFFLINE

        elapsed = (datetime.utcnow() - last_beat).total_seconds()
        if elapsed > self.timeout_seconds:
            return NodeStatus.OFFLINE

        return NodeStatus.ACTIVE

    def get_active_nodes(self) -> List[str]:
        active = []
        for node_id in self.heartbeats.keys():
            if self.check_node_status(node_id) == NodeStatus.ACTIVE:
                active.append(node_id)
        return active


class TaskDistributor:
    def __init__(self):
        self.task_queue: List[AuditTask] = []
        self.task_history: List[AuditTask] = []

    def add_task(self, task: AuditTask) -> None:
        self.task_queue.append(task)
        self.task_queue.sort(key=lambda t: t.priority, reverse=True)

    def get_next_task(self) -> Optional[AuditTask]:
        if self.task_queue:
            return self.task_queue.pop(0)
        return None

    def assign_task(self, task: AuditTask, node_ids: List[str]) -> None:
        task.assigned_nodes = node_ids
        task.status = TaskStatus.ASSIGNED

    def complete_task(
        self, task_id: str, results: Dict[str, Any]
    ) -> Optional[AuditTask]:
        task = self._find_task(task_id)
        if task:
            task.results = results
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            self.task_history.append(task)
        return task

    def _find_task(self, task_id: str) -> Optional[AuditTask]:
        for task in self.task_queue:
            if task.task_id == task_id:
                return task
        for task in self.task_history:
            if task.task_id == task_id:
                return task
        return None

    def get_pending_tasks(self) -> List[AuditTask]:
        return [t for t in self.task_queue if t.status == TaskStatus.PENDING]


class ConsensusEngine:
    def __init__(self, consensus_type: ConsensusType = ConsensusType.MAJORITY):
        self.consensus_type = consensus_type
        self.consensus_history: List[SwarmConsensus] = []

    def reach_consensus(
        self,
        task_id: str,
        votes: Dict[str, Any],
        node_weights: Dict[str, float] = None,
    ) -> SwarmConsensus:
        consensus_id = f"consensus_{uuid.uuid4().hex[:8]}"

        if self.consensus_type == ConsensusType.MAJORITY:
            result, confidence = self._majority_vote(votes)
        elif self.consensus_type == ConsensusType.UNANIMOUS:
            result, confidence = self._unanimous_vote(votes)
        else:
            result, confidence = self._weighted_vote(votes, node_weights or {})

        consensus = SwarmConsensus(
            consensus_id=consensus_id,
            task_id=task_id,
            consensus_type=self.consensus_type,
            votes=votes,
            result=result,
            confidence=confidence,
            participating_nodes=list(votes.keys()),
            reached_at=datetime.utcnow(),
        )

        self.consensus_history.append(consensus)
        return consensus

    def _majority_vote(self, votes: Dict[str, Any]) -> tuple:
        if not votes:
            return None, 0.0

        vote_counts: Dict[Any, int] = {}
        for vote in votes.values():
            vote_counts[vote] = vote_counts.get(vote, 0) + 1

        total = len(votes)
        max_vote = max(vote_counts.items(), key=lambda x: x[1])
        confidence = max_vote[1] / total

        return max_vote[0], confidence

    def _unanimous_vote(self, votes: Dict[str, Any]) -> tuple:
        if not votes:
            return None, 0.0

        unique_votes = set(votes.values())
        if len(unique_votes) == 1:
            return list(unique_votes)[0], 1.0

        return None, 0.0

    def _weighted_vote(
        self, votes: Dict[str, Any], weights: Dict[str, float]
    ) -> tuple:
        if not votes:
            return None, 0.0

        weighted_counts: Dict[Any, float] = {}
        total_weight = 0.0

        for node_id, vote in votes.items():
            weight = weights.get(node_id, 1.0)
            weighted_counts[vote] = weighted_counts.get(vote, 0.0) + weight
            total_weight += weight

        if total_weight == 0:
            return None, 0.0

        max_vote = max(weighted_counts.items(), key=lambda x: x[1])
        confidence = max_vote[1] / total_weight

        return max_vote[0], confidence


class LogSynchronizer:
    def __init__(self):
        self.log_hashes: Dict[str, List[str]] = {}
        self.sync_status: Dict[str, Dict] = {}

    def register_log_batch(
        self, node_id: str, batch_id: str, log_hash: str
    ) -> None:
        if batch_id not in self.log_hashes:
            self.log_hashes[batch_id] = []
        self.log_hashes[batch_id].append((node_id, log_hash))

    def check_consistency(self, batch_id: str) -> Dict[str, Any]:
        result = {
            "batch_id": batch_id,
            "consistent": True,
            "hash_mismatches": [],
            "participating_nodes": [],
        }

        hashes = self.log_hashes.get(batch_id, [])
        if not hashes:
            return result

        hash_values = [h[1] for h in hashes]
        unique_hashes = set(hash_values)

        if len(unique_hashes) > 1:
            result["consistent"] = False
            hash_counts: Dict[str, int] = {}
            for h in hash_values:
                hash_counts[h] = hash_counts.get(h, 0) + 1

            majority_hash = max(hash_counts.items(), key=lambda x: x[1])[0]
            for node_id, log_hash in hashes:
                if log_hash != majority_hash:
                    result["hash_mismatches"].append(
                        {
                            "node_id": node_id,
                            "expected": majority_hash,
                            "actual": log_hash,
                        }
                    )

        result["participating_nodes"] = [h[0] for h in hashes]
        return result

    def sync_logs(self, batch_id: str, source_node: str, target_nodes: List[str]) -> Dict[str, Any]:
        result = {
            "batch_id": batch_id,
            "source": source_node,
            "targets": target_nodes,
            "sync_status": {},
            "synced_at": datetime.utcnow().isoformat(),
        }

        for node in target_nodes:
            result["sync_status"][node] = "synced"

        self.sync_status[batch_id] = result
        return result


class AuditSwarmCoordinator:
    def __init__(self, coordinator_id: str = "swarm_coordinator_001"):
        self.coordinator_id = coordinator_id
        self.nodes: Dict[str, DistributedAuditNode] = {}
        self.heartbeat_manager = HeartbeatManager()
        self.task_distributor = TaskDistributor()
        self.consensus_engine = ConsensusEngine()
        self.log_sync = LogSynchronizer()

        self.audit_results: List[Dict] = []
        self.swarm_metrics: Dict[str, Any] = {}

    def register_node(
        self,
        node_id: str,
        node_name: str,
        capabilities: List[str],
        max_capacity: float = 100.0,
    ) -> DistributedAuditNode:
        node = DistributedAuditNode(
            node_id=node_id,
            node_name=node_name,
            capabilities=capabilities,
            max_capacity=max_capacity,
            status=NodeStatus.IDLE,
        )
        self.nodes[node_id] = node
        self.heartbeat_manager.record_heartbeat(node_id)
        return node

    def unregister_node(self, node_id: str) -> bool:
        if node_id in self.nodes:
            del self.nodes[node_id]
            return True
        return False

    def receive_heartbeat(self, node_id: str) -> bool:
        if node_id in self.nodes:
            self.heartbeat_manager.record_heartbeat(node_id)
            self.nodes[node_id].last_heartbeat = datetime.utcnow()
            return True
        return False

    def get_active_nodes(self) -> List[DistributedAuditNode]:
        active_ids = self.heartbeat_manager.get_active_nodes()
        return [self.nodes[nid] for nid in active_ids if nid in self.nodes]

    def create_audit_task(
        self,
        task_type: str,
        parameters: Dict[str, Any],
        priority: int = 5,
        deadline_minutes: int = 60,
    ) -> AuditTask:
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        task = AuditTask(
            task_id=task_id,
            task_type=task_type,
            priority=priority,
            parameters=parameters,
            deadline=datetime.utcnow() + timedelta(minutes=deadline_minutes),
        )
        self.task_distributor.add_task(task)
        return task

    def distribute_task(self, task: AuditTask, replication: int = 3) -> List[str]:
        active_nodes = self.get_active_nodes()
        capable_nodes = [
            n
            for n in active_nodes
            if task.task_type in n.capabilities or "all" in n.capabilities
        ]

        capable_nodes.sort(key=lambda n: n.current_load / n.max_capacity)

        selected = capable_nodes[:replication]
        selected_ids = [n.node_id for n in selected]

        if selected_ids:
            self.task_distributor.assign_task(task, selected_ids)
            for node_id in selected_ids:
                self.nodes[node_id].status = NodeStatus.BUSY
                self.nodes[node_id].current_load += 10

        return selected_ids

    async def collect_results(
        self, task_id: str, timeout_seconds: int = 300
    ) -> Dict[str, Any]:
        results = {}
        start_time = datetime.utcnow()

        while (datetime.utcnow() - start_time).total_seconds() < timeout_seconds:
            for node_id, node in self.nodes.items():
                if node_id in results:
                    continue

            await asyncio.sleep(1)

        return results

    def reach_consensus(
        self, task_id: str, votes: Dict[str, Any]
    ) -> SwarmConsensus:
        node_weights = {
            node_id: self.nodes[node_id].performance_score
            for node_id in votes.keys()
            if node_id in self.nodes
        }

        return self.consensus_engine.reach_consensus(task_id, votes, node_weights)

    def broadcast_anomaly(self, source_node: str, anomaly_data: Dict) -> Dict[str, Any]:
        broadcast_id = f"broadcast_{uuid.uuid4().hex[:8]}"
        active_nodes = self.get_active_nodes()

        broadcast_result = {
            "broadcast_id": broadcast_id,
            "source": source_node,
            "anomaly_type": anomaly_data.get("type", "unknown"),
            "timestamp": datetime.utcnow().isoformat(),
            "recipients": [n.node_id for n in active_nodes if n.node_id != source_node],
            "status": "sent",
        }

        return broadcast_result

    def coordinate_investigation(
        self, anomaly_id: str, investigating_nodes: List[str]
    ) -> Dict[str, Any]:
        investigation_id = f"investigation_{uuid.uuid4().hex[:8]}"

        coordination = {
            "investigation_id": investigation_id,
            "anomaly_id": anomaly_id,
            "coordinator": self.coordinator_id,
            "investigating_nodes": investigating_nodes,
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "findings": [],
        }

        return coordination

    def balance_load(self) -> Dict[str, Any]:
        active_nodes = self.get_active_nodes()
        if not active_nodes:
            return {"status": "no_active_nodes"}

        avg_load = sum(n.current_load for n in active_nodes) / len(active_nodes)
        rebalance_actions = []

        for node in active_nodes:
            if node.current_load > avg_load * 1.5:
                underloaded = [
                    n
                    for n in active_nodes
                    if n.current_load < avg_load * 0.5
                ]
                if underloaded:
                    target = min(underloaded, key=lambda n: n.current_load)
                    rebalance_actions.append(
                        {
                            "from": node.node_id,
                            "to": target.node_id,
                            "amount": 10,
                        }
                    )

        return {
            "status": "balanced" if not rebalance_actions else "rebalanced",
            "average_load": avg_load,
            "actions": rebalance_actions,
        }

    def get_swarm_metrics(self) -> Dict[str, Any]:
        active_nodes = self.get_active_nodes()
        total_capacity = sum(n.max_capacity for n in active_nodes)
        used_capacity = sum(n.current_load for n in active_nodes)

        return {
            "total_nodes": len(self.nodes),
            "active_nodes": len(active_nodes),
            "offline_nodes": len(self.nodes) - len(active_nodes),
            "total_capacity": total_capacity,
            "used_capacity": used_capacity,
            "utilization_rate": used_capacity / total_capacity if total_capacity > 0 else 0,
            "pending_tasks": len(self.task_distributor.get_pending_tasks()),
            "completed_tasks": len(self.task_distributor.task_history),
            "consensus_reached": len(self.consensus_engine.consensus_history),
        }

    def handle_node_failure(self, node_id: str) -> Dict[str, Any]:
        result = {
            "failed_node": node_id,
            "timestamp": datetime.utcnow().isoformat(),
            "actions_taken": [],
        }

        if node_id in self.nodes:
            self.nodes[node_id].status = NodeStatus.OFFLINE

            for task in self.task_distributor.task_queue:
                if node_id in task.assigned_nodes:
                    task.assigned_nodes.remove(node_id)
                    task.status = TaskStatus.PENDING
                    result["actions_taken"].append(
                        f"Reassigning task {task.task_id}"
                    )

        return result

    def sync_audit_logs(
        self, batch_id: str, log_data: Dict[str, str]
    ) -> Dict[str, Any]:
        for node_id, log_hash in log_data.items():
            self.log_sync.register_log_batch(node_id, batch_id, log_hash)

        consistency = self.log_sync.check_consistency(batch_id)

        if not consistency["consistent"]:
            majority_nodes = [
                n
                for n in consistency["participating_nodes"]
                if n not in [m["node_id"] for m in consistency["hash_mismatches"]]
            ]

            if majority_nodes:
                source = majority_nodes[0]
                targets = [m["node_id"] for m in consistency["hash_mismatches"]]
                return self.log_sync.sync_logs(batch_id, source, targets)

        return consistency
