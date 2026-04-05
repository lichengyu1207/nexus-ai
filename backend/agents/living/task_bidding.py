"""
任务发布与竞标机制
Task Publishing and Bidding System

实现智能体间的任务竞标和动态团队形成
"""

import os
import json
import time
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import random

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    PENDING = "pending"
    BIDDING = "bidding"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4
    EMERGENCY = 5


@dataclass
class TaskSkill:
    skill_name: str
    min_level: float = 0.0
    max_level: float = 1.0
    required: bool = True


@dataclass
class Task:
    task_id: str
    task_type: str
    description: str
    required_skills: List[TaskSkill]
    priority: TaskPriority
    reward: float
    deadline: Optional[float] = None
    max_team_size: int = 5
    min_team_size: int = 1
    status: TaskStatus = TaskStatus.PENDING
    created_at: float = field(default_factory=time.time)
    created_by: str = ""
    assigned_agents: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "description": self.description,
            "required_skills": [
                {"skill_name": s.skill_name, "min_level": s.min_level, 
                 "max_level": s.max_level, "required": s.required}
                for s in self.required_skills
            ],
            "priority": self.priority.value,
            "reward": self.reward,
            "deadline": self.deadline,
            "max_team_size": self.max_team_size,
            "min_team_size": self.min_team_size,
            "status": self.status.value,
            "created_at": self.created_at,
            "created_by": self.created_by,
            "assigned_agents": self.assigned_agents,
            "metadata": self.metadata
        }


@dataclass
class Bid:
    bid_id: str
    task_id: str
    agent_id: str
    estimated_completion_time: float
    success_probability: float
    proposed_reward: float
    capabilities: Dict[str, float]
    message: str = ""
    created_at: float = field(default_factory=time.time)
    status: str = "pending"
    
    def to_dict(self) -> Dict:
        return {
            "bid_id": self.bid_id,
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "estimated_completion_time": self.estimated_completion_time,
            "success_probability": self.success_probability,
            "proposed_reward": self.proposed_reward,
            "capabilities": self.capabilities,
            "message": self.message,
            "created_at": self.created_at,
            "status": self.status
        }


class TaskBiddingSystem:
    
    def __init__(
        self,
        blackboard,
        bidding_window_seconds: float = 30.0,
        min_bids_required: int = 1,
        auto_assign: bool = True
    ):
        self.blackboard = blackboard
        self.bidding_window_seconds = bidding_window_seconds
        self.min_bids_required = min_bids_required
        self.auto_assign = auto_assign
        
        self.tasks: Dict[str, Task] = {}
        self.bids: Dict[str, List[Bid]] = defaultdict(list)
        self.agent_tasks: Dict[str, List[str]] = defaultdict(list)
        
        self.bidding_timers: Dict[str, threading.Timer] = {}
        
        self.task_handlers: Dict[str, Callable] = {}
        self.bid_evaluators: List[Callable] = []
        
        self.stats = {
            "tasks_created": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "bids_submitted": 0,
            "bids_accepted": 0
        }
    
    def publish_task(
        self,
        task_type: str,
        description: str,
        required_skills: List[Dict],
        priority: TaskPriority = TaskPriority.NORMAL,
        reward: float = 10.0,
        deadline: Optional[float] = None,
        max_team_size: int = 5,
        min_team_size: int = 1,
        created_by: str = "system",
        metadata: Optional[Dict] = None
    ) -> Task:
        task_id = f"task_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
        
        skills = [
            TaskSkill(
                skill_name=s.get("skill_name", ""),
                min_level=s.get("min_level", 0.0),
                max_level=s.get("max_level", 1.0),
                required=s.get("required", True)
            )
            for s in required_skills
        ]
        
        task = Task(
            task_id=task_id,
            task_type=task_type,
            description=description,
            required_skills=skills,
            priority=priority,
            reward=reward,
            deadline=deadline,
            max_team_size=max_team_size,
            min_team_size=min_team_size,
            created_by=created_by,
            metadata=metadata or {}
        )
        
        self.tasks[task_id] = task
        self.stats["tasks_created"] += 1
        
        self.blackboard.write(
            f"task:{task_id}",
            task.to_dict(),
            ttl=3600)
        
        task.status = TaskStatus.BIDDING
        
        if self.auto_assign:
            timer = threading.Timer(
                self.bidding_window_seconds,
                self._close_bidding,
                args=[task_id]
            )
            timer.start()
            self.bidding_timers[task_id] = timer
        
        logger.info(f"Task {task_id} published: {description}")
        
        return task
    
    def submit_bid(
        self,
        task_id: str,
        agent_id: str,
        estimated_completion_time: float,
        success_probability: float,
        proposed_reward: Optional[float] = None,
        capabilities: Optional[Dict[str, float]] = None,
        message: str = ""
    ) -> Optional[Bid]:
        task = self.tasks.get(task_id)
        
        if not task:
            logger.warning(f"Task {task_id} not found")
            return None
        
        if task.status != TaskStatus.BIDDING:
            logger.warning(f"Task {task_id} is not accepting bids (status: {task.status})")
            return None
        
        if len(task.assigned_agents) >= task.max_team_size:
            logger.warning(f"Task {task_id} has reached max team size")
            return None
        
        bid_id = f"bid_{task_id}_{agent_id}_{int(time.time())}"
        
        bid = Bid(
            bid_id=bid_id,
            task_id=task_id,
            agent_id=agent_id,
            estimated_completion_time=estimated_completion_time,
            success_probability=success_probability,
            proposed_reward=proposed_reward or task.reward,
            capabilities=capabilities or {},
            message=message
        )
        
        self.bids[task_id].append(bid)
        self.stats["bids_submitted"] += 1
        
        self.blackboard.write(
            f"bid:{bid_id}",
            bid.to_dict(),
            ttl=3600
        )
        
        logger.info(f"Agent {agent_id} submitted bid for task {task_id}")
        
        return bid
    
    def _close_bidding(self, task_id: str):
        task = self.tasks.get(task_id)
        if not task or task.status != TaskStatus.BIDDING:
            return
        
        bids = self.bids.get(task_id, [])
        
        if len(bids) < self.min_bids_required:
            logger.warning(f"Task {task_id} has insufficient bids ({len(bids)} < {self.min_bids_required})")
            task.status = TaskStatus.PENDING
            return
        
        selected_bids = self._select_bids(task, bids)
        
        if selected_bids:
            for bid in selected_bids:
                bid.status = "accepted"
                task.assigned_agents.append(bid.agent_id)
                self.agent_tasks[bid.agent_id].append(task_id)
                self.stats["bids_accepted"] += 1
            
            task.status = TaskStatus.ASSIGNED
            
            self.blackboard.write(
                f"task:{task_id}:assigned",
                {"agents": task.assigned_agents})
            
            for bid in selected_bids:
                self.blackboard.write(
                    f"agent:{bid.agent_id}:task_assigned",
                    {"task_id": task_id})
            
            logger.info(f"Task {task_id} assigned to agents: {task.assigned_agents}")
        else:
            task.status = TaskStatus.FAILED
            self.stats["tasks_failed"] += 1
            logger.warning(f"Task {task_id} failed to assign")
    
    def _select_bids(self, task: Task, bids: List[Bid]) -> List[Bid]:
        if not bids:
            return []
        
        for evaluator in self.bid_evaluators:
            try:
                selected = evaluator(task, bids)
                if selected:
                    return selected
            except Exception as e:
                logger.error(f"Error in bid evaluator: {e}")
        
        scored_bids = []
        for bid in bids:
            score = self._calculate_bid_score(task, bid)
            scored_bids.append((bid, score))
        
        scored_bids.sort(key=lambda x: x[1], reverse=True)
        
        num_to_select = min(task.max_team_size, len(scored_bids))
        return [bid for bid, score in scored_bids[:num_to_select]]
    
    def _calculate_bid_score(self, task: Task, bid: Bid) -> float:
        score = 0.0
        
        score += bid.success_probability * 40
        
        time_score = max(0, 100 - bid.estimated_completion_time) / 100 * 30
        score += time_score
        
        skill_match = 0.0
        matched_skills = 0
        for req_skill in task.required_skills:
            if req_skill.skill_name in bid.capabilities:
                agent_level = bid.capabilities[req_skill.skill_name]
                if req_skill.min_level <= agent_level <= req_skill.max_level:
                    skill_match += 1
                matched_skills += 1
        
        if task.required_skills:
            score += (skill_match / len(task.required_skills)) * 30
        
        return score
    
    def accept_task(self, task_id: str, agent_id: str) -> bool:
        task = self.tasks.get(task_id)
        if not task:
            return False
        
        if agent_id not in task.assigned_agents:
            return False
        
        task.status = TaskStatus.IN_PROGRESS
        
        return True
    
    def complete_task(
        self,
        task_id: str,
        agent_id: str,
        result: Optional[Dict] = None,
        success: bool = True
    ) -> bool:
        task = self.tasks.get(task_id)
        if not task:
            return False
        
        if agent_id not in task.assigned_agents:
            return False
        
        if success:
            task.status = TaskStatus.COMPLETED
            self.stats["tasks_completed"] += 1
        else:
            task.status = TaskStatus.FAILED
            self.stats["tasks_failed"] += 1
        
        self.blackboard.write(
            f"task:{task_id}:result",
            {"success": success, "result": result, "agent_id": agent_id})
        
        logger.info(f"Task {task_id} {'completed' if success else 'failed'} by {agent_id}")
        
        return True
    
    def cancel_task(self, task_id: str, reason: str = "") -> bool:
        task = self.tasks.get(task_id)
        if not task:
            return False
        
        task.status = TaskStatus.CANCELLED
        
        if task_id in self.bidding_timers:
            self.bidding_timers[task_id].cancel()
            del self.bidding_timers[task_id]
        
        self.blackboard.write(
            f"task:{task_id}:cancelled",
            {"task_id": task_id, "reason": reason})
        
        logger.info(f"Task {task_id} cancelled: {reason}")
        
        return True
    
    def get_task(self, task_id: str) -> Optional[Task]:
        return self.tasks.get(task_id)
    
    def get_agent_tasks(self, agent_id: str) -> List[Task]:
        task_ids = self.agent_tasks.get(agent_id, [])
        return [self.tasks[tid] for tid in task_ids if tid in self.tasks]
    
    def get_pending_tasks(self) -> List[Task]:
        return [
            t for t in self.tasks.values()
            if t.status in [TaskStatus.PENDING, TaskStatus.BIDDING]
        ]
    
    def get_active_tasks(self) -> List[Task]:
        return [
            t for t in self.tasks.values()
            if t.status in [TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS]
        ]
    
    def register_task_handler(self, task_type: str, handler: Callable):
        self.task_handlers[task_type] = handler
    
    def add_bid_evaluator(self, evaluator: Callable):
        self.bid_evaluators.append(evaluator)
    
    def get_stats(self) -> Dict:
        return {
            "total_tasks": len(self.tasks),
            "pending_tasks": len(self.get_pending_tasks()),
            "active_tasks": len(self.get_active_tasks()),
            "stats": self.stats.copy()
        }


class DynamicTeamFormation:
    
    def __init__(
        self,
        bidding_system: TaskBiddingSystem,
        blackboard,
        max_team_lifetime: float = 3600
    ):
        self.bidding_system = bidding_system
        self.blackboard = blackboard
        self.max_team_lifetime = max_team_lifetime
        
        self.teams: Dict[str, Dict] = {}
        self.agent_teams: Dict[str, List[str]] = defaultdict(list)
        
        self.stats = {
            "teams_formed": 0,
            "teams_dissolved": 0
        }
    
    def form_team(
        self,
        team_name: str,
        task_id: str,
        agent_ids: List[str],
        leader_id: Optional[str] = None
    ) -> str:
        team_id = f"team_{int(time.time() * 1000)}"
        
        if not leader_id and agent_ids:
            leader_id = agent_ids[0]
        
        team = {
            "team_id": team_id,
            "team_name": team_name,
            "task_id": task_id,
            "members": agent_ids,
            "leader_id": leader_id,
            "created_at": time.time(),
            "status": "active"
        }
        
        self.teams[team_id] = team
        
        for agent_id in agent_ids:
            self.agent_teams[agent_id].append(team_id)
        
        self.stats["teams_formed"] += 1
        
        self.blackboard.write(
            f"team:{team_id}",
            team,
            ttl=int(self.max_team_lifetime))
        
        logger.info(f"Team {team_id} formed for task {task_id}")
        
        return team_id
    
    def dissolve_team(self, team_id: str, reason: str = ""):
        team = self.teams.get(team_id)
        if not team:
            return
        
        team["status"] = "dissolved"
        
        for agent_id in team["members"]:
            if team_id in self.agent_teams.get(agent_id, []):
                self.agent_teams[agent_id].remove(team_id)
        
        self.stats["teams_dissolved"] += 1
        
        self.blackboard.write(
            f"team:{team_id}:dissolved",
            {"reason": reason})
        
        logger.info(f"Team {team_id} dissolved: {reason}")
    
    def add_member(self, team_id: str, agent_id: str) -> bool:
        team = self.teams.get(team_id)
        if not team or team["status"] != "active":
            return False
        
        if agent_id not in team["members"]:
            team["members"].append(agent_id)
            self.agent_teams[agent_id].append(team_id)
            
            self.blackboard.write(
                f"team:{team_id}",
                team)
        
        return True
    
    def remove_member(self, team_id: str, agent_id: str) -> bool:
        team = self.teams.get(team_id)
        if not team:
            return False
        
        if agent_id in team["members"]:
            team["members"].remove(agent_id)
            if team_id in self.agent_teams.get(agent_id, []):
                self.agent_teams[agent_id].remove(team_id)
            
            if team["leader_id"] == agent_id and team["members"]:
                team["leader_id"] = team["members"][0]
            
            self.blackboard.write(
                f"team:{team_id}",
                team)
        
        return True
    
    def get_team(self, team_id: str) -> Optional[Dict]:
        return self.teams.get(team_id)
    
    def get_agent_teams(self, agent_id: str) -> List[Dict]:
        team_ids = self.agent_teams.get(agent_id, [])
        return [self.teams[tid] for tid in team_ids if tid in self.teams]
    
    def get_active_teams(self) -> List[Dict]:
        return [t for t in self.teams.values() if t["status"] == "active"]
    
    def get_stats(self) -> Dict:
        return {
            "total_teams": len(self.teams),
            "active_teams": len(self.get_active_teams()),
            "stats": self.stats.copy()
        }
