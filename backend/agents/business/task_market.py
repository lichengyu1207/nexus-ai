"""
业务任务市场
Business Task Market

作为业务任务发布与竞标的中心
"""

import os
import json
import time
import logging
import threading
import uuid
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import deque, defaultdict
import random
import math

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    PENDING = "pending"
    BIDDING = "bidding"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class TaskPriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5


class TaskType(Enum):
    CONSULTATION = "consultation"
    DATA_COLLECTION = "data_collection"
    ANALYSIS = "analysis"
    REPORT_GENERATION = "report_generation"
    RISK_ASSESSMENT = "risk_assessment"
    USER_MANAGEMENT = "user_management"
    COORDINATION = "coordination"
    COMPOSITE = "composite"


@dataclass
class BusinessTask:
    task_id: str
    task_type: TaskType
    title: str
    description: str
    complexity: float
    required_skills: List[str]
    required_roles: List[str]
    reward_energy: float
    deadline: float
    priority: TaskPriority
    user_id: Optional[str] = None
    request_data: Dict = field(default_factory=dict)
    parent_task_id: Optional[str] = None
    sub_task_ids: List[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    assigned_agents: List[str] = field(default_factory=list)
    team_id: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Optional[Dict] = None
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "task_id": self.task_id,
            "task_type": self.task_type.value,
            "title": self.title,
            "description": self.description,
            "complexity": self.complexity,
            "required_skills": self.required_skills,
            "required_roles": [r.value if hasattr(r, 'value') else r for r in self.required_roles],
            "reward_energy": self.reward_energy,
            "deadline": self.deadline,
            "priority": self.priority.value,
            "user_id": self.user_id,
            "status": self.status.value,
            "assigned_agents": self.assigned_agents,
            "team_id": self.team_id,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "metadata": self.metadata
        }
    
    def is_expired(self) -> bool:
        return time.time() > self.deadline
    
    def get_remaining_time(self) -> float:
        return max(0, self.deadline - time.time())


@dataclass
class TaskBid:
    bid_id: str
    task_id: str
    agent_id: str
    promised_completion_time: float
    success_rate_estimate: float
    energy_offer: float
    proposed_reward: float
    capabilities: List[str]
    message: str
    created_at: float = field(default_factory=time.time)
    status: str = "pending"
    
    def to_dict(self) -> Dict:
        return {
            "bid_id": self.bid_id,
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "promised_completion_time": self.promised_completion_time,
            "success_rate_estimate": self.success_rate_estimate,
            "energy_offer": self.energy_offer,
            "proposed_reward": self.proposed_reward,
            "capabilities": self.capabilities,
            "message": self.message,
            "created_at": self.created_at,
            "status": self.status
        }


class TaskMarket:
    """
    业务任务市场
    
    作为业务任务发布与竞标的中心：
    1. 任务发布：用户请求转化为业务任务
    2. 竞标机制：智能体评估并竞标任务
    3. 任务分配：选择中标者形成临时团队
    4. 动态定价：根据供需调整奖励能量
    """
    
    def __init__(
        self,
        blackboard: Optional[Any] = None,
        memory_agent: Optional[Any] = None,
        max_pending_tasks: int = 1000,
        max_bids_per_task: int = 20,
        default_task_timeout: float = 3600,
        bidding_window: float = 30,
    ):
        self.blackboard = blackboard
        self.memory_agent = memory_agent
        self.max_pending_tasks = max_pending_tasks
        self.max_bids_per_task = max_bids_per_task
        self.default_task_timeout = default_task_timeout
        self.bidding_window = bidding_window
        
        self.tasks: Dict[str, BusinessTask] = {}
        self.bids: Dict[str, List[TaskBid]] = {}
        self.agent_tasks: Dict[str, List[str]] = defaultdict(list)
        self.user_tasks: Dict[str, List[str]] = defaultdict(list)
        
        self.task_queue: deque = deque(maxlen=max_pending_tasks)
        self.completed_tasks: deque = deque(maxlen=10000)
        
        self._lock = threading.RLock()
        self._running = False
        self._main_task: Optional[asyncio.Task] = None
        
        self.pricing_engine = DynamicPricingEngine()
        self.matcher = TaskMatcher()
        
        self.stats = {
            "tasks_published": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "tasks_cancelled": 0,
            "total_bids": 0,
            "avg_bids_per_task": 0.0,
            "avg_completion_time": 0.0,
            "total_energy_distributed": 0.0,
        }
    
    async def start(self):
        self._running = True
        self._main_task = asyncio.create_task(self._market_loop())
        logger.info("Task market started")
    
    async def stop(self):
        self._running = False
        if self._main_task:
            self._main_task.cancel()
            try:
                await self._main_task
            except asyncio.CancelledError:
                pass
        logger.info("Task market stopped")
    
    async def _market_loop(self):
        while self._running:
            try:
                await self._process_expired_tasks()
                await self._adjust_pricing()
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in market loop: {e}")
                await asyncio.sleep(5)
    
    async def publish_task(
        self,
        task_type: TaskType,
        title: str,
        description: str,
        complexity: float,
        required_skills: List[str],
        required_roles: List[str],
        user_id: Optional[str] = None,
        request_data: Optional[Dict] = None,
        deadline: Optional[float] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        parent_task_id: Optional[str] = None,
    ) -> BusinessTask:
        """
        发布任务到市场
        
        Args:
            task_type: 任务类型
            title: 任务标题
            description: 任务描述
            complexity: 复杂度 (1.0-10.0)
            required_skills: 所需技能
            required_roles: 所需角色
            user_id: 用户ID
            request_data: 请求数据
            deadline: 截止时间
            priority: 优先级
            parent_task_id: 父任务ID
            
        Returns:
            BusinessTask: 创建的任务
        """
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        
        if deadline is None:
            deadline = time.time() + self.default_task_timeout
        
        base_reward = 10 * complexity
        dynamic_reward = self.pricing_engine.calculate_reward(
            task_type, complexity, priority
        )
        
        task = BusinessTask(
            task_id=task_id,
            task_type=task_type,
            title=title,
            description=description,
            complexity=complexity,
            required_skills=required_skills,
            required_roles=required_roles,
            reward_energy=dynamic_reward,
            deadline=deadline,
            priority=priority,
            user_id=user_id,
            request_data=request_data or {},
            parent_task_id=parent_task_id,
        )
        
        with self._lock:
            self.tasks[task_id] = task
            self.bids[task_id] = []
            self.task_queue.append(task_id)
            
            if user_id:
                self.user_tasks[user_id].append(task_id)
            
            self.stats["tasks_published"] += 1
        
        if self.blackboard:
            await self._announce_task(task)
        
        logger.info(f"Task published: {task_id} - {title}")
        
        return task
    
    async def submit_bid(
        self,
        task_id: str,
        agent_id: str,
        promised_completion_time: float,
        success_rate_estimate: float,
        capabilities: List[str],
        message: str = "",
        proposed_reward: Optional[float] = None,
    ) -> Optional[TaskBid]:
        """
        提交竞标
        
        Args:
            task_id: 任务ID
            agent_id: 智能体ID
            promised_completion_time: 承诺完成时间
            success_rate_estimate: 成功率预估
            capabilities: 能力列表
            message: 消息
            proposed_reward: 提议奖励
            
        Returns:
            TaskBid: 竞标，失败返回None
        """
        with self._lock:
            if task_id not in self.tasks:
                logger.warning(f"Task not found: {task_id}")
                return None
            
            task = self.tasks[task_id]
            
            if task.status != TaskStatus.PENDING:
                logger.warning(f"Task not accepting bids: {task_id} (status: {task.status})")
                return None
            
            if len(self.bids[task_id]) >= self.max_bids_per_task:
                logger.warning(f"Max bids reached for task: {task_id}")
                return None
            
            bid_id = f"bid_{uuid.uuid4().hex[:8]}"
            
            if proposed_reward is None:
                proposed_reward = task.reward_energy
            
            bid = TaskBid(
                bid_id=bid_id,
                task_id=task_id,
                agent_id=agent_id,
                promised_completion_time=promised_completion_time,
                success_rate_estimate=success_rate_estimate,
                energy_offer=0,
                proposed_reward=proposed_reward,
                capabilities=capabilities,
                message=message,
            )
            
            self.bids[task_id].append(bid)
            self.stats["total_bids"] += 1
        
        logger.debug(f"Bid submitted: {bid_id} for task {task_id} by agent {agent_id}")
        
        return bid
    
    async def select_winners(
        self,
        task_id: str,
        max_winners: int = 1,
        strategy: str = "best_fit",
    ) -> List[str]:
        """
        选择中标者
        
        Args:
            task_id: 任务ID
            max_winners: 最大中标数
            strategy: 选择策略 (best_fit, random, round_robin)
            
        Returns:
            List[str]: 中标智能体ID列表
        """
        with self._lock:
            if task_id not in self.tasks:
                return []
            
            task = self.tasks[task_id]
            bids = self.bids.get(task_id, [])
            
            if not bids:
                return []
            
            if strategy == "best_fit":
                scored_bids = [
                    (bid, self._calculate_bid_score(bid, task))
                    for bid in bids
                ]
                scored_bids.sort(key=lambda x: x[1], reverse=True)
                winners = [bid.agent_id for bid, _ in scored_bids[:max_winners]]
            
            elif strategy == "random":
                winners = [bid.agent_id for bid in random.sample(
                    bids, min(max_winners, len(bids))
                )]
            
            else:
                winners = [bids[0].agent_id] if bids else []
            
            task.assigned_agents = winners
            task.status = TaskStatus.ASSIGNED
            
            if len(winners) > 1:
                task.team_id = f"team_{uuid.uuid4().hex[:8]}"
            
            for agent_id in winners:
                self.agent_tasks[agent_id].append(task_id)
        
        logger.info(f"Winners selected for task {task_id}: {winners}")
        
        return winners
    
    def _calculate_bid_score(self, bid: TaskBid, task: BusinessTask) -> float:
        score = 0.0
        
        score += bid.success_rate_estimate * 40
        
        time_score = 1.0 - min(1.0, bid.promised_completion_time / 3600)
        score += time_score * 20
        
        skill_match = len(set(bid.capabilities) & set(task.required_skills))
        skill_score = skill_match / max(len(task.required_skills), 1)
        score += skill_score * 30
        
        reward_ratio = bid.proposed_reward / task.reward_energy
        if reward_ratio <= 1.0:
            score += (1.0 - reward_ratio) * 10
        
        return score
    
    async def start_task(self, task_id: str) -> bool:
        """
        开始任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否成功开始
        """
        with self._lock:
            if task_id not in self.tasks:
                return False
            
            task = self.tasks[task_id]
            
            if task.status != TaskStatus.ASSIGNED:
                return False
            
            task.status = TaskStatus.IN_PROGRESS
            task.started_at = time.time()
        
        logger.info(f"Task started: {task_id}")
        return True
    
    async def complete_task(
        self,
        task_id: str,
        result: Dict,
        agent_contributions: Optional[Dict[str, float]] = None,
    ) -> bool:
        """
        完成任务
        
        Args:
            task_id: 任务ID
            result: 任务结果
            agent_contributions: 智能体贡献度 {agent_id: contribution}
            
        Returns:
            bool: 是否成功完成
        """
        with self._lock:
            if task_id not in self.tasks:
                return False
            
            task = self.tasks[task_id]
            
            if task.status != TaskStatus.IN_PROGRESS:
                return False
            
            task.status = TaskStatus.COMPLETED
            task.completed_at = time.time()
            task.result = result
            
            completion_time = task.completed_at - task.started_at
            
            contributions = agent_contributions or {
                agent_id: 1.0 / len(task.assigned_agents)
                for agent_id in task.assigned_agents
            }
            
            total_distributed = 0.0
            for agent_id, contribution in contributions.items():
                reward = task.reward_energy * contribution
                total_distributed += reward
            
            self.stats["tasks_completed"] += 1
            self.stats["total_energy_distributed"] += total_distributed
            
            old_avg = self.stats["avg_completion_time"]
            count = self.stats["tasks_completed"]
            self.stats["avg_completion_time"] = (
                old_avg * (count - 1) + completion_time
            ) / count
            
            self.completed_tasks.append(task_id)
        
        if self.memory_agent:
            await self._store_task_case(task)
        
        logger.info(f"Task completed: {task_id}")
        
        return True
    
    async def fail_task(self, task_id: str, reason: str) -> bool:
        """
        标记任务失败
        
        Args:
            task_id: 任务ID
            reason: 失败原因
            
        Returns:
            bool: 是否成功标记
        """
        with self._lock:
            if task_id not in self.tasks:
                return False
            
            task = self.tasks[task_id]
            task.status = TaskStatus.FAILED
            task.completed_at = time.time()
            task.result = {"failed": True, "reason": reason}
            
            self.stats["tasks_failed"] += 1
        
        logger.warning(f"Task failed: {task_id} - {reason}")
        return True
    
    async def cancel_task(self, task_id: str, reason: str = "") -> bool:
        """
        取消任务
        
        Args:
            task_id: 任务ID
            reason: 取消原因
            
        Returns:
            bool: 是否成功取消
        """
        with self._lock:
            if task_id not in self.tasks:
                return False
            
            task = self.tasks[task_id]
            
            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                return False
            
            task.status = TaskStatus.CANCELLED
            task.result = {"cancelled": True, "reason": reason}
            
            self.stats["tasks_cancelled"] += 1
        
        logger.info(f"Task cancelled: {task_id}")
        return True
    
    async def _process_expired_tasks(self):
        current_time = time.time()
        
        with self._lock:
            for task_id, task in list(self.tasks.items()):
                if task.is_expired() and task.status in [
                    TaskStatus.PENDING, TaskStatus.BIDDING, TaskStatus.ASSIGNED
                ]:
                    task.status = TaskStatus.TIMEOUT
                    task.result = {"timeout": True}
                    self.stats["tasks_failed"] += 1
                    logger.warning(f"Task expired: {task_id}")
    
    async def _adjust_pricing(self):
        self.pricing_engine.update_market_conditions(
            pending_tasks=len([t for t in self.tasks.values() if t.status == TaskStatus.PENDING]),
            active_agents=0,
            avg_completion_rate=self._calculate_completion_rate()
        )
    
    def _calculate_completion_rate(self) -> float:
        total = self.stats["tasks_completed"] + self.stats["tasks_failed"]
        if total == 0:
            return 0.5
        return self.stats["tasks_completed"] / total
    
    async def _announce_task(self, task: BusinessTask):
        if self.blackboard:
            try:
                await self.blackboard.publish(
                    "task_market",
                    {
                        "event": "new_task",
                        "task": task.to_dict()
                    }
                )
            except Exception as e:
                logger.error(f"Failed to announce task: {e}")
    
    async def _store_task_case(self, task: BusinessTask):
        if self.memory_agent:
            try:
                await self.memory_agent.store({
                    "type": "successful_task",
                    "task_id": task.task_id,
                    "task_type": task.task_type.value,
                    "complexity": task.complexity,
                    "assigned_agents": task.assigned_agents,
                    "completion_time": task.completed_at - task.started_at if task.started_at else 0,
                    "reward": task.reward_energy,
                    "timestamp": time.time()
                })
            except Exception as e:
                logger.error(f"Failed to store task case: {e}")
    
    def get_pending_tasks(
        self,
        required_skills: Optional[List[str]] = None,
        required_roles: Optional[List[str]] = None,
        limit: int = 10,
    ) -> List[BusinessTask]:
        """
        获取待处理任务
        
        Args:
            required_skills: 筛选所需技能
            required_roles: 筛选所需角色
            limit: 返回数量限制
            
        Returns:
            List[BusinessTask]: 任务列表
        """
        with self._lock:
            pending = [
                task for task in self.tasks.values()
                if task.status == TaskStatus.PENDING
            ]
            
            if required_skills:
                pending = [
                    t for t in pending
                    if any(s in t.required_skills for s in required_skills)
                ]
            
            if required_roles:
                pending = [
                    t for t in pending
                    if any(r in t.required_roles for r in required_roles)
                ]
            
            pending.sort(key=lambda t: t.priority.value, reverse=True)
            
            return pending[:limit]
    
    def get_task(self, task_id: str) -> Optional[BusinessTask]:
        return self.tasks.get(task_id)
    
    def get_bids(self, task_id: str) -> List[TaskBid]:
        return self.bids.get(task_id, [])
    
    def get_agent_tasks(self, agent_id: str) -> List[BusinessTask]:
        task_ids = self.agent_tasks.get(agent_id, [])
        return [self.tasks[tid] for tid in task_ids if tid in self.tasks]
    
    def get_user_tasks(self, user_id: str) -> List[BusinessTask]:
        task_ids = self.user_tasks.get(user_id, [])
        return [self.tasks[tid] for tid in task_ids if tid in self.tasks]
    
    async def get_state(self) -> Dict:
        with self._lock:
            pending_count = sum(1 for t in self.tasks.values() if t.status == TaskStatus.PENDING)
            in_progress_count = sum(1 for t in self.tasks.values() if t.status == TaskStatus.IN_PROGRESS)
            
            return {
                "total_tasks": len(self.tasks),
                "pending_tasks": pending_count,
                "in_progress_tasks": in_progress_count,
                "stats": self.stats.copy(),
                "pricing": self.pricing_engine.get_state()
            }


class DynamicPricingEngine:
    """
    动态定价引擎
    
    根据供需关系动态调整任务奖励能量
    """
    
    def __init__(
        self,
        base_reward: float = 10.0,
        demand_factor: float = 1.0,
        supply_factor: float = 1.0,
    ):
        self.base_reward = base_reward
        self.demand_factor = demand_factor
        self.supply_factor = supply_factor
        
        self.task_type_multipliers: Dict[str, float] = defaultdict(lambda: 1.0)
        self.priority_multipliers = {
            TaskPriority.LOW: 0.8,
            TaskPriority.NORMAL: 1.0,
            TaskPriority.HIGH: 1.3,
            TaskPriority.URGENT: 1.6,
            TaskPriority.CRITICAL: 2.0,
        }
    
    def calculate_reward(
        self,
        task_type: TaskType,
        complexity: float,
        priority: TaskPriority,
    ) -> float:
        base = self.base_reward * complexity
        
        type_multiplier = self.task_type_multipliers[task_type.value]
        priority_multiplier = self.priority_multipliers.get(priority, 1.0)
        
        reward = base * type_multiplier * priority_multiplier
        reward *= self.demand_factor / self.supply_factor
        
        return round(reward, 2)
    
    def update_market_conditions(
        self,
        pending_tasks: int,
        active_agents: int,
        avg_completion_rate: float,
    ):
        if pending_tasks > 50:
            self.demand_factor = min(2.0, self.demand_factor * 1.05)
        elif pending_tasks < 10:
            self.demand_factor = max(0.5, self.demand_factor * 0.95)
        
        if active_agents > 0:
            self.supply_factor = min(2.0, max(0.5, active_agents / 10))
        
        if avg_completion_rate < 0.7:
            self.demand_factor *= 1.1
    
    def get_state(self) -> Dict:
        return {
            "base_reward": self.base_reward,
            "demand_factor": self.demand_factor,
            "supply_factor": self.supply_factor,
            "task_type_multipliers": dict(self.task_type_multipliers),
        }


class TaskMatcher:
    """
    任务匹配器
    
    匹配智能体能力与任务需求
    """
    
    def __init__(self):
        self.skill_weights: Dict[str, float] = defaultdict(lambda: 1.0)
    
    def calculate_match_score(
        self,
        agent_capabilities: List[str],
        agent_role: str,
        task: BusinessTask,
    ) -> float:
        score = 0.0
        
        if agent_role in [r.value if hasattr(r, 'value') else r for r in task.required_roles]:
            score += 0.4
        
        if task.required_skills:
            matched_skills = set(agent_capabilities) & set(task.required_skills)
            skill_score = len(matched_skills) / len(task.required_skills)
            score += skill_score * 0.4
        
        complexity_factor = 1.0 - (task.complexity / 10) * 0.2
        score *= complexity_factor
        
        return min(1.0, score)
    
    def find_best_tasks(
        self,
        agent_capabilities: List[str],
        agent_role: str,
        tasks: List[BusinessTask],
        limit: int = 5,
    ) -> List[Tuple[BusinessTask, float]]:
        scored_tasks = [
            (task, self.calculate_match_score(agent_capabilities, agent_role, task))
            for task in tasks
        ]
        
        scored_tasks.sort(key=lambda x: x[1], reverse=True)
        
        return scored_tasks[:limit]
