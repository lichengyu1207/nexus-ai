# -*- coding: utf-8 -*-
"""
Agent Swarm 任务公告板模块
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4
import time
from collections import defaultdict

from .config import SwarmConfig
from .models import SwarmTask, SwarmBid, SwarmTaskLog


@dataclass
class Task:
    id: UUID = field(default_factory=uuid4)
    task_type: str = "general"
    required_capabilities: List[str] = field(default_factory=list)
    priority: int = 5
    payload: Dict = field(default_factory=dict)
    parent_id: Optional[UUID] = None
    status: str = "pending"
    deadline: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_swarm_task(self, session_id: Optional[UUID] = None) -> SwarmTask:
        return SwarmTask(
            id=self.id,
            parent_task_id=self.parent_id,
            session_id=session_id,
            task_type=self.task_type,
            required_capabilities=self.required_capabilities,
            priority=self.priority,
            status=self.status,
            payload=self.payload,
            deadline=self.deadline,
            created_at=self.created_at
        )


@dataclass
class Bid:
    agent_id: UUID
    task_id: UUID
    score: float
    estimated_time: float = 0.0
    confidence: float = 0.5
    proposal: Dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_swarm_bid(self) -> SwarmBid:
        return SwarmBid(
            task_id=self.task_id,
            agent_id=self.agent_id,
            score=self.score,
            estimated_time=self.estimated_time,
            confidence=self.confidence,
            proposal=self.proposal
        )


class TaskBoard:
    def __init__(self, config: Optional[SwarmConfig] = None):
        self.config = config or SwarmConfig()
        self.tasks: Dict[UUID, SwarmTask] = {}
        self.bids: Dict[UUID, List[SwarmBid]] = defaultdict(list)
        self.logs: Dict[UUID, List[SwarmTaskLog]] = defaultdict(list)
        self._pending_queue: List[UUID] = []
        self._assigned_tasks: Dict[UUID, UUID] = {}
    
    def publish(self, task: SwarmTask) -> UUID:
        task.status = "pending"
        task.created_at = datetime.now()
        self.tasks[task.id] = task
        self._pending_queue.append(task.id)
        
        self._log_event(
            task_id=task.id,
            event_type="published",
            event_data={"task_type": task.task_type, "priority": task.priority}
        )
        
        return task.id
    
    def get_pending_tasks(self, limit: int = 100) -> List[SwarmTask]:
        pending = []
        for task_id in self._pending_queue[:limit]:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                if task.status == "pending":
                    pending.append(task)
        return pending
    
    def get_task(self, task_id: UUID) -> Optional[SwarmTask]:
        return self.tasks.get(task_id)
    
    def submit_bid(self, bid: SwarmBid) -> bool:
        if bid.task_id not in self.tasks:
            return False
        
        task = self.tasks[bid.task_id]
        if task.status != "pending":
            return False
        
        existing = [b for b in self.bids[bid.task_id] if b.agent_id == bid.agent_id]
        if existing:
            return False
        
        bid.created_at = datetime.now()
        self.bids[bid.task_id].append(bid)
        
        self._log_event(
            task_id=bid.task_id,
            agent_id=bid.agent_id,
            event_type="bid_submitted",
            event_data={"score": bid.score, "confidence": bid.confidence}
        )
        
        return True
    
    def get_bids(self, task_id: UUID) -> List[SwarmBid]:
        return self.bids.get(task_id, [])
    
    def select_winner(self, task_id: UUID) -> Optional[UUID]:
        if task_id not in self.tasks:
            return None
        
        task = self.tasks[task_id]
        if task.status != "pending":
            return None
        
        bids = self.bids.get(task_id, [])
        if not bids:
            return None
        
        valid_bids = [b for b in bids if b.score != float('inf')]
        if not valid_bids:
            return None
        
        winner = min(valid_bids, key=lambda b: b.score)
        
        winner.is_winner = True
        task.assigned_agent_id = winner.agent_id
        task.status = "assigned"
        task.started_at = datetime.now()
        
        self._assigned_tasks[task_id] = winner.agent_id
        
        if task_id in self._pending_queue:
            self._pending_queue.remove(task_id)
        
        self._log_event(
            task_id=task_id,
            agent_id=winner.agent_id,
            event_type="winner_selected",
            event_data={"score": winner.score, "estimated_time": winner.estimated_time}
        )
        
        return winner.agent_id
    
    def update_status(self, task_id: UUID, status: str, result: Optional[Dict] = None) -> bool:
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        old_status = task.status
        task.status = status
        
        if result:
            task.result = result
        
        if status == "completed":
            task.completed_at = datetime.now()
            if task_id in self._assigned_tasks:
                del self._assigned_tasks[task_id]
        elif status == "failed":
            if task_id in self._assigned_tasks:
                del self._assigned_tasks[task_id]
        
        self._log_event(
            task_id=task_id,
            event_type="status_updated",
            event_data={"old_status": old_status, "new_status": status}
        )
        
        return True
    
    def get_assigned_tasks(self, agent_id: UUID) -> List[SwarmTask]:
        return [
            self.tasks[task_id] 
            for task_id, assigned_agent in self._assigned_tasks.items() 
            if assigned_agent == agent_id and task_id in self.tasks
        ]
    
    def get_child_tasks(self, parent_id: UUID) -> List[SwarmTask]:
        return [
            task for task in self.tasks.values() 
            if task.parent_task_id == parent_id
        ]
    
    def get_task_tree(self, task_id: UUID) -> Dict:
        task = self.tasks.get(task_id)
        if not task:
            return {}
        
        tree = task.to_dict()
        children = self.get_child_tasks(task_id)
        
        if children:
            tree["children"] = [self.get_task_tree(child.id) for child in children]
        
        return tree
    
    def _log_event(
        self, 
        task_id: UUID, 
        event_type: str, 
        event_data: Dict,
        agent_id: Optional[UUID] = None
    ):
        log = SwarmTaskLog(
            task_id=task_id,
            agent_id=agent_id,
            event_type=event_type,
            event_data=event_data
        )
        self.logs[task_id].append(log)
    
    def get_logs(self, task_id: UUID) -> List[SwarmTaskLog]:
        return self.logs.get(task_id, [])
    
    def get_statistics(self) -> Dict:
        total = len(self.tasks)
        pending = len([t for t in self.tasks.values() if t.status == "pending"])
        assigned = len([t for t in self.tasks.values() if t.status == "assigned"])
        running = len([t for t in self.tasks.values() if t.status == "running"])
        completed = len([t for t in self.tasks.values() if t.status == "completed"])
        failed = len([t for t in self.tasks.values() if t.status == "failed"])
        
        total_bids = sum(len(b) for b in self.bids.values())
        
        return {
            "total_tasks": total,
            "pending_tasks": pending,
            "assigned_tasks": assigned,
            "running_tasks": running,
            "completed_tasks": completed,
            "failed_tasks": failed,
            "total_bids": total_bids,
            "pending_queue_length": len(self._pending_queue)
        }
    
    def clear_completed(self, max_age_hours: int = 24):
        cutoff = datetime.now()
        to_remove = []
        
        for task_id, task in self.tasks.items():
            if task.status in ["completed", "failed"] and task.completed_at:
                age_hours = (cutoff - task.completed_at).total_seconds() / 3600
                if age_hours > max_age_hours:
                    to_remove.append(task_id)
        
        for task_id in to_remove:
            del self.tasks[task_id]
            if task_id in self.bids:
                del self.bids[task_id]
            if task_id in self.logs:
                del self.logs[task_id]
        
        return len(to_remove)
