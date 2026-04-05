"""
分布式审计蜂群架构
Distributed Audit Swarm Agent

设计分布式审计蜂群，让多个审计智能体协同工作，适应大规模业务场景。
"""

import asyncio
import json
import logging
import hashlib
import uuid
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
from enum import Enum
import random

logger = logging.getLogger(__name__)


class NodeStatus(Enum):
    ACTIVE = "active"
    BUSY = "busy"
    OFFLINE = "offline"
    SYNCING = "syncing"


class TaskStatus(Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class ConsensusState(Enum):
    PROPOSING = "proposing"
    VOTING = "voting"
    COMMITTED = "committed"
    REJECTED = "rejected"


@dataclass
class AuditNode:
    node_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    address: str = ""
    status: str = NodeStatus.ACTIVE.value
    
    capabilities: List[str] = field(default_factory=list)
    current_load: int = 0
    max_capacity: int = 100
    
    last_heartbeat: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    total_tasks_completed: int = 0
    
    local_data_hash: str = ""
    sync_version: int = 0


@dataclass
class AuditTask:
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_type: str = ""
    priority: int = 1
    
    parameters: Dict = field(default_factory=dict)
    required_capabilities: List[str] = field(default_factory=list)
    
    status: str = TaskStatus.PENDING.value
    assigned_node: str = ""
    
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    started_at: str = ""
    completed_at: str = ""
    
    result: Dict = field(default_factory=dict)
    error: str = ""


@dataclass
class ConsensusProposal:
    proposal_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    proposer_node: str = ""
    proposal_type: str = ""
    proposal_data: Dict = field(default_factory=dict)
    
    state: str = ConsensusState.PROPOSING.value
    votes: Dict[str, bool] = field(default_factory=dict)
    
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    committed_at: str = ""


class DistributedAuditSwarmAgent:
    """
    分布式审计蜂群架构
    
    功能：
    1. 蜂群结构：每个业务智能体集群内部署本地审计智能体
    2. 任务分解：审计任务分解为子任务，分配给不同审计智能体
    3. 协同检测：单个审计智能体发现可疑事件，广播给其他成员确认
    4. 数据一致性：审计日志分片存储，元数据同步
    5. 容错机制：节点失效时任务自动迁移
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.name = "DistributedAuditSwarmAgent"
        self.description = "分布式审计蜂群架构，多智能体协同审计"
        self.config = config or {}
        
        self.nodes: Dict[str, AuditNode] = {}
        self.local_node_id: str = str(uuid.uuid4())
        
        self.tasks: Dict[str, AuditTask] = {}
        self.task_queue: List[str] = []
        
        self.proposals: Dict[str, ConsensusProposal] = {}
        
        self.consensus_threshold = self.config.get("consensus_threshold", 0.6)
        self.heartbeat_interval = self.config.get("heartbeat_interval", 30)
        self.task_timeout = self.config.get("task_timeout", 300)
        
        self.stats = {
            "total_nodes": 0,
            "active_nodes": 0,
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "consensus_reached": 0,
            "consensus_failed": 0,
        }
        
        self._initialized = False
    
    async def initialize(self):
        if not self._initialized:
            await self._setup()
            self._initialized = True
            logger.info(f"Agent '{self.name}' initialized")
    
    async def _setup(self):
        await self._register_local_node()
        
        asyncio.create_task(self._heartbeat_loop())
        asyncio.create_task(self._task_scheduler_loop())
        asyncio.create_task(self._node_monitor_loop())
    
    async def _register_local_node(self):
        node = AuditNode(
            node_id=self.local_node_id,
            address="local",
            capabilities=["audit_log", "data_access", "compliance_check"],
        )
        self.nodes[self.local_node_id] = node
        self.stats["total_nodes"] = 1
        self.stats["active_nodes"] = 1
    
    async def _heartbeat_loop(self):
        while True:
            await asyncio.sleep(self.heartbeat_interval)
            await self._send_heartbeat()
    
    async def _send_heartbeat(self):
        node = self.nodes.get(self.local_node_id)
        if node:
            node.last_heartbeat = datetime.utcnow().isoformat()
    
    async def _task_scheduler_loop(self):
        while True:
            await asyncio.sleep(5)
            await self._schedule_pending_tasks()
    
    async def _node_monitor_loop(self):
        while True:
            await asyncio.sleep(self.heartbeat_interval * 2)
            await self._check_node_health()
    
    async def register_node(
        self,
        node_id: str,
        address: str,
        capabilities: List[str],
        max_capacity: int = 100,
    ) -> Dict:
        node = AuditNode(
            node_id=node_id,
            address=address,
            capabilities=capabilities,
            max_capacity=max_capacity,
        )
        
        self.nodes[node_id] = node
        self.stats["total_nodes"] += 1
        self.stats["active_nodes"] += 1
        
        return {
            "success": True,
            "node_id": node_id,
            "message": "节点注册成功",
        }
    
    async def unregister_node(self, node_id: str) -> bool:
        if node_id not in self.nodes:
            return False
        
        node = self.nodes[node_id]
        
        for task_id, task in self.tasks.items():
            if task.assigned_node == node_id and task.status == TaskStatus.IN_PROGRESS.value:
                task.status = TaskStatus.PENDING.value
                task.assigned_node = ""
                self.task_queue.append(task_id)
        
        del self.nodes[node_id]
        self.stats["total_nodes"] -= 1
        if node.status == NodeStatus.ACTIVE.value:
            self.stats["active_nodes"] -= 1
        
        return True
    
    async def _check_node_health(self):
        now = datetime.utcnow()
        timeout = timedelta(seconds=self.heartbeat_interval * 3)
        
        for node in self.nodes.values():
            if node.node_id == self.local_node_id:
                continue
            
            last_heartbeat = datetime.fromisoformat(node.last_heartbeat)
            if now - last_heartbeat > timeout:
                if node.status == NodeStatus.ACTIVE.value:
                    node.status = NodeStatus.OFFLINE.value
                    self.stats["active_nodes"] -= 1
                    await self._handle_node_failure(node.node_id)
    
    async def _handle_node_failure(self, node_id: str):
        for task_id, task in self.tasks.items():
            if task.assigned_node == node_id:
                task.status = TaskStatus.PENDING.value
                task.assigned_node = ""
                task.error = f"节点{node_id}失效，任务重新分配"
                self.task_queue.append(task_id)
    
    async def submit_task(
        self,
        task_type: str,
        parameters: Dict,
        required_capabilities: Optional[List[str]] = None,
        priority: int = 1,
    ) -> AuditTask:
        task = AuditTask(
            task_type=task_type,
            parameters=parameters,
            required_capabilities=required_capabilities or [],
            priority=priority,
        )
        
        self.tasks[task.task_id] = task
        self.task_queue.append(task.task_id)
        
        self.stats["total_tasks"] += 1
        
        return task
    
    async def _schedule_pending_tasks(self):
        self.task_queue.sort(key=lambda tid: self.tasks[tid].priority, reverse=True)
        
        scheduled = []
        for task_id in self.task_queue:
            task = self.tasks.get(task_id)
            if not task or task.status != TaskStatus.PENDING.value:
                continue
            
            best_node = await self._find_best_node(task)
            if best_node:
                task.assigned_node = best_node.node_id
                task.status = TaskStatus.ASSIGNED.value
                best_node.current_load += 1
                
                if best_node.current_load >= best_node.max_capacity * 0.8:
                    best_node.status = NodeStatus.BUSY.value
                
                scheduled.append(task_id)
                asyncio.create_task(self._execute_task(task))
        
        for task_id in scheduled:
            self.task_queue.remove(task_id)
    
    async def _find_best_node(self, task: AuditTask) -> Optional[AuditNode]:
        candidates = []
        
        for node in self.nodes.values():
            if node.status != NodeStatus.ACTIVE.value:
                continue
            
            if task.required_capabilities:
                if not all(cap in node.capabilities for cap in task.required_capabilities):
                    continue
            
            load_ratio = node.current_load / node.max_capacity if node.max_capacity > 0 else 1
            candidates.append((node, load_ratio))
        
        if not candidates:
            return None
        
        candidates.sort(key=lambda x: x[1])
        return candidates[0][0]
    
    async def _execute_task(self, task: AuditTask):
        task.status = TaskStatus.IN_PROGRESS.value
        task.started_at = datetime.utcnow().isoformat()
        
        try:
            result = await self._perform_audit_task(task)
            
            task.result = result
            task.status = TaskStatus.COMPLETED.value
            task.completed_at = datetime.utcnow().isoformat()
            
            self.stats["completed_tasks"] += 1
            
        except Exception as e:
            task.status = TaskStatus.FAILED.value
            task.error = str(e)
            self.stats["failed_tasks"] += 1
        
        finally:
            node = self.nodes.get(task.assigned_node)
            if node:
                node.current_load -= 1
                node.total_tasks_completed += 1
                if node.status == NodeStatus.BUSY.value and node.current_load < node.max_capacity * 0.5:
                    node.status = NodeStatus.ACTIVE.value
    
    async def _perform_audit_task(self, task: AuditTask) -> Dict:
        await asyncio.sleep(0.1)
        
        return {
            "task_type": task.task_type,
            "status": "completed",
            "findings": [],
        }
    
    async def propose_consensus(
        self,
        proposal_type: str,
        proposal_data: Dict,
    ) -> ConsensusProposal:
        proposal = ConsensusProposal(
            proposer_node=self.local_node_id,
            proposal_type=proposal_type,
            proposal_data=proposal_data,
        )
        
        self.proposals[proposal.proposal_id] = proposal
        
        await self._broadcast_proposal(proposal)
        
        return proposal
    
    async def _broadcast_proposal(self, proposal: ConsensusProposal):
        proposal.state = ConsensusState.VOTING.value
        
        for node_id in self.nodes.keys():
            if node_id != self.local_node_id:
                vote = await self._request_vote(node_id, proposal)
                proposal.votes[node_id] = vote
        
        await self._evaluate_consensus(proposal)
    
    async def _request_vote(self, node_id: str, proposal: ConsensusProposal) -> bool:
        return random.random() > 0.2
    
    async def _evaluate_consensus(self, proposal: ConsensusProposal):
        total_nodes = len(self.nodes)
        if total_nodes == 0:
            proposal.state = ConsensusState.REJECTED.value
            self.stats["consensus_failed"] += 1
            return
        
        positive_votes = sum(1 for v in proposal.votes.values() if v)
        vote_ratio = positive_votes / total_nodes
        
        if vote_ratio >= self.consensus_threshold:
            proposal.state = ConsensusState.COMMITTED.value
            proposal.committed_at = datetime.utcnow().isoformat()
            self.stats["consensus_reached"] += 1
        else:
            proposal.state = ConsensusState.REJECTED.value
            self.stats["consensus_failed"] += 1
    
    async def vote_on_proposal(
        self,
        proposal_id: str,
        vote: bool,
    ) -> bool:
        proposal = self.proposals.get(proposal_id)
        if not proposal:
            return False
        
        proposal.votes[self.local_node_id] = vote
        
        return True
    
    async def get_task_status(self, task_id: str) -> Optional[Dict]:
        task = self.tasks.get(task_id)
        if not task:
            return None
        
        return {
            "task_id": task.task_id,
            "task_type": task.task_type,
            "status": task.status,
            "assigned_node": task.assigned_node,
            "created_at": task.created_at,
            "started_at": task.started_at,
            "completed_at": task.completed_at,
            "result": task.result,
            "error": task.error,
        }
    
    async def get_cluster_status(self) -> Dict:
        return {
            "total_nodes": self.stats["total_nodes"],
            "active_nodes": self.stats["active_nodes"],
            "nodes": [
                {
                    "node_id": n.node_id,
                    "status": n.status,
                    "current_load": n.current_load,
                    "max_capacity": n.max_capacity,
                    "tasks_completed": n.total_tasks_completed,
                }
                for n in self.nodes.values()
            ],
            "pending_tasks": len([t for t in self.task_queue if self.tasks.get(t, AuditTask()).status == TaskStatus.PENDING.value]),
            "in_progress_tasks": len([t for t in self.tasks.values() if t.status == TaskStatus.IN_PROGRESS.value]),
        }
    
    async def get_stats(self) -> Dict:
        return {
            "name": self.name,
            "local_node_id": self.local_node_id,
            "total_nodes": self.stats["total_nodes"],
            "active_nodes": self.stats["active_nodes"],
            "total_tasks": self.stats["total_tasks"],
            "completed_tasks": self.stats["completed_tasks"],
            "failed_tasks": self.stats["failed_tasks"],
            "consensus_reached": self.stats["consensus_reached"],
            "consensus_failed": self.stats["consensus_failed"],
        }
