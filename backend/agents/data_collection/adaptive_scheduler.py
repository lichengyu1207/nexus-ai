"""
自适应采集调度器
让数据采集智能体根据需求、资源、成功率自主决策采集计划
"""
import asyncio
import json
import logging
import random
from collections import deque
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class SchedulePriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class CollectionTask(BaseModel):
    task_id: str = Field(default_factory=lambda: str(uuid4()))
    collector_id: str
    data_type: str
    source_config: Dict[str, Any]
    priority: SchedulePriority = SchedulePriority.NORMAL
    scheduled_time: Optional[datetime] = None
    estimated_energy: float = 10.0
    expected_reward: float = 10.0
    status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.now)


class CollectorState(BaseModel):
    collector_id: str
    energy: float = 100.0
    max_energy: float = 100.0
    current_load: float = 0.0
    success_rate: float = 0.8
    last_collection: Optional[datetime] = None
    total_collected: int = 0
    specializations: List[str] = Field(default_factory=list)


class SourceStats(BaseModel):
    source_id: str
    source_type: str
    success_count: int = 0
    failure_count: int = 0
    total_samples: int = 0
    avg_quality: float = 0.5
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    update_frequency: timedelta = timedelta(hours=24)
    next_suggested: Optional[datetime] = None


class SchedulingPolicy:
    def __init__(
        self,
        exploration_rate: float = 0.1,
        short_term_weight: float = 0.6,
        long_term_weight: float = 0.4
    ):
        self.exploration_rate = exploration_rate
        self.short_term_weight = short_term_weight
        self.long_term_weight = long_term_weight
        
        self.task_history: deque = deque(maxlen=1000)
        self.reward_history: Dict[str, deque] = {}
    
    def compute_task_score(
        self,
        task: CollectionTask,
        collector_state: CollectorState,
        source_stats: Optional[SourceStats] = None
    ) -> float:
        score = 0.0
        
        priority_scores = {
            SchedulePriority.LOW: 1,
            SchedulePriority.NORMAL: 2,
            SchedulePriority.HIGH: 3,
            SchedulePriority.URGENT: 4
        }
        score += priority_scores.get(task.priority, 2) * 0.2
        
        if collector_state.energy >= task.estimated_energy:
            energy_ratio = collector_state.energy / collector_state.max_energy
            score += energy_ratio * 0.2
        else:
            score -= 0.5
        
        if collector_state.current_load < 0.8:
            score += (1 - collector_state.current_load) * 0.15
        
        if source_stats:
            score += source_stats.success_rate * 0.15
            score += source_stats.avg_quality * 0.1
        
        score += (task.expected_reward / 100) * 0.2
        
        return max(0, score)
    
    def should_explore(self) -> bool:
        return random.random() < self.exploration_rate
    
    def record_task_result(
        self,
        task: CollectionTask,
        success: bool,
        reward: float
    ):
        self.task_history.append({
            "task_id": task.task_id,
            "data_type": task.data_type,
            "success": success,
            "reward": reward,
            "timestamp": datetime.now().isoformat()
        })
        
        if task.data_type not in self.reward_history:
            self.reward_history[task.data_type] = deque(maxlen=100)
        self.reward_history[task.data_type].append(reward)
    
    def get_avg_reward(self, data_type: str) -> float:
        if data_type in self.reward_history and self.reward_history[data_type]:
            return sum(self.reward_history[data_type]) / len(self.reward_history[data_type])
        return 0.0


class TaskCoordinator:
    def __init__(self, conflict_window: int = 60):
        self.conflict_window = conflict_window
        
        self.scheduled_tasks: Dict[str, CollectionTask] = {}
        self.collector_assignments: Dict[str, List[str]] = {}
        self.source_locks: Dict[str, str] = {}
    
    def schedule_task(self, task: CollectionTask) -> bool:
        source_id = task.source_config.get("source_id", task.task_id)
        
        if source_id in self.source_locks:
            lock_holder = self.source_locks[source_id]
            if lock_holder != task.collector_id:
                return False
        
        if task.collector_id not in self.collector_assignments:
            self.collector_assignments[task.collector_id] = []
        
        conflicting = self._find_conflicting_tasks(task)
        if conflicting:
            for existing_task in conflicting:
                if existing_task.priority.value < task.priority.value:
                    self._cancel_task(existing_task)
                else:
                    return False
        
        self.scheduled_tasks[task.task_id] = task
        self.collector_assignments[task.collector_id].append(task.task_id)
        self.source_locks[source_id] = task.collector_id
        
        return True
    
    def _find_conflicting_tasks(self, task: CollectionTask) -> List[CollectionTask]:
        conflicting = []
        
        scheduled_time = task.scheduled_time
        if not scheduled_time:
            return conflicting
        
        window = timedelta(seconds=self.conflict_window)
        
        for existing in self.scheduled_tasks.values():
            if existing.collector_id == task.collector_id:
                if existing.scheduled_time:
                    if abs(existing.scheduled_time - scheduled_time) < window:
                        conflicting.append(existing)
        
        return conflicting
    
    def _cancel_task(self, task: CollectionTask):
        if task.task_id in self.scheduled_tasks:
            del self.scheduled_tasks[task.task_id]
        
        if task.collector_id in self.collector_assignments:
            if task.task_id in self.collector_assignments[task.collector_id]:
                self.collector_assignments[task.collector_id].remove(task.task_id)
    
    def complete_task(self, task_id: str):
        if task_id in self.scheduled_tasks:
            task = self.scheduled_tasks[task_id]
            source_id = task.source_config.get("source_id", task_id)
            
            if source_id in self.source_locks:
                del self.source_locks[source_id]
            
            del self.scheduled_tasks[task_id]
            
            if task.collector_id in self.collector_assignments:
                if task_id in self.collector_assignments[task.collector_id]:
                    self.collector_assignments[task.collector_id].remove(task_id)
    
    def get_collector_tasks(self, collector_id: str) -> List[CollectionTask]:
        task_ids = self.collector_assignments.get(collector_id, [])
        return [self.scheduled_tasks[tid] for tid in task_ids if tid in self.scheduled_tasks]


class AdaptiveCollectionScheduler:
    def __init__(
        self,
        agent_id: str,
        energy_manager: Optional[Any] = None,
        demand_sensor: Optional[Any] = None,
        sample_repository: Optional[Any] = None
    ):
        self.agent_id = agent_id
        self.energy_manager = energy_manager
        self.demand_sensor = demand_sensor
        self.sample_repository = sample_repository
        
        self.policy = SchedulingPolicy()
        self.coordinator = TaskCoordinator()
        
        self.collector_states: Dict[str, CollectorState] = {}
        self.source_stats: Dict[str, SourceStats] = {}
        
        self.schedule_interval = timedelta(minutes=5)
        self.min_interval = timedelta(minutes=1)
        self.max_interval = timedelta(hours=24)
        
        self._running = False
        self._schedule_task: Optional[asyncio.Task] = None
        
        self.logger = logging.getLogger(f"{__name__}.{agent_id}")
    
    async def initialize(self):
        self.logger.info(f"AdaptiveCollectionScheduler {self.agent_id} initialized")
    
    def register_collector(
        self,
        collector_id: str,
        specializations: Optional[List[str]] = None,
        max_energy: float = 100.0
    ):
        self.collector_states[collector_id] = CollectorState(
            collector_id=collector_id,
            max_energy=max_energy,
            energy=max_energy,
            specializations=specializations or []
        )
    
    def update_collector_state(
        self,
        collector_id: str,
        energy: Optional[float] = None,
        success: Optional[bool] = None,
        samples_collected: Optional[int] = None
    ):
        if collector_id not in self.collector_states:
            return
        
        state = self.collector_states[collector_id]
        
        if energy is not None:
            state.energy = energy
        
        if success is not None:
            if success:
                state.success_rate = min(1.0, state.success_rate + 0.01)
            else:
                state.success_rate = max(0.0, state.success_rate - 0.02)
        
        if samples_collected is not None:
            state.total_collected += samples_collected
        
        state.last_collection = datetime.now()
    
    def update_source_stats(
        self,
        source_id: str,
        source_type: str,
        success: bool,
        samples: int = 0,
        quality: float = 0.5
    ):
        if source_id not in self.source_stats:
            self.source_stats[source_id] = SourceStats(
                source_id=source_id,
                source_type=source_type
            )
        
        stats = self.source_stats[source_id]
        
        if success:
            stats.success_count += 1
            stats.last_success = datetime.now()
            stats.total_samples += samples
            
            if samples > 0:
                stats.avg_quality = (stats.avg_quality * (stats.success_count - 1) + quality) / stats.success_count
        else:
            stats.failure_count += 1
            stats.last_failure = datetime.now()
        
        self._update_source_frequency(stats)
    
    def _update_source_frequency(self, stats: SourceStats):
        total = stats.success_count + stats.failure_count
        if total < 3:
            return
        
        success_rate = stats.success_count / total
        
        if success_rate > 0.8:
            stats.update_frequency = timedelta(hours=1)
        elif success_rate > 0.5:
            stats.update_frequency = timedelta(hours=6)
        else:
            stats.update_frequency = timedelta(hours=24)
        
        stats.next_suggested = datetime.now() + stats.update_frequency
    
    async def schedule_collection(
        self,
        collector_id: str,
        data_type: str,
        source_config: Dict[str, Any],
        priority: SchedulePriority = SchedulePriority.NORMAL
    ) -> Optional[CollectionTask]:
        if collector_id not in self.collector_states:
            self.logger.warning(f"Unknown collector: {collector_id}")
            return None
        
        task = CollectionTask(
            collector_id=collector_id,
            data_type=data_type,
            source_config=source_config,
            priority=priority,
            estimated_energy=self._estimate_energy(source_config),
            expected_reward=self._estimate_reward(data_type)
        )
        
        scheduled = self.coordinator.schedule_task(task)
        
        if scheduled:
            self.logger.info(f"Scheduled task {task.task_id} for collector {collector_id}")
            return task
        
        return None
    
    def _estimate_energy(self, source_config: Dict[str, Any]) -> float:
        base_energy = 10.0
        
        source_type = source_config.get("type", "unknown")
        
        if source_type == "web":
            depth = source_config.get("max_depth", 1)
            base_energy *= (1 + depth * 0.5)
        elif source_type == "api":
            base_energy *= 0.8
        elif source_type == "database":
            base_energy *= 1.2
        
        return base_energy
    
    def _estimate_reward(self, data_type: str) -> float:
        avg_reward = self.policy.get_avg_reward(data_type)
        
        if avg_reward > 0:
            return avg_reward
        
        return 10.0
    
    async def decide_next_collection(
        self,
        collector_id: str
    ) -> Optional[CollectionTask]:
        if collector_id not in self.collector_states:
            return None
        
        state = self.collector_states[collector_id]
        
        if state.energy < 10:
            self.logger.debug(f"Collector {collector_id} has low energy, skipping")
            return None
        
        if state.current_load >= 0.9:
            self.logger.debug(f"Collector {collector_id} is at full load")
            return None
        
        if self.policy.should_explore():
            return await self._exploratory_schedule(collector_id, state)
        else:
            return await self._exploitative_schedule(collector_id, state)
    
    async def _exploratory_schedule(
        self,
        collector_id: str,
        state: CollectorState
    ) -> Optional[CollectionTask]:
        available_sources = [
            s for s in self.source_stats.values()
            if s.next_suggested and s.next_suggested <= datetime.now()
        ]
        
        if not available_sources:
            return None
        
        source = random.choice(available_sources)
        
        return await self.schedule_collection(
            collector_id=collector_id,
            data_type=source.source_type,
            source_config={"source_id": source.source_id},
            priority=SchedulePriority.LOW
        )
    
    async def _exploitative_schedule(
        self,
        collector_id: str,
        state: CollectorState
    ) -> Optional[CollectionTask]:
        matching_demands = []
        
        if self.demand_sensor:
            try:
                demands = await self.demand_sensor.get_matching_demands(
                    state.specializations
                )
                matching_demands = demands
            except Exception as e:
                self.logger.error(f"Error getting demands: {e}")
        
        if not matching_demands:
            return await self._exploratory_schedule(collector_id, state)
        
        best_task = None
        best_score = -1
        
        for demand in matching_demands:
            task = CollectionTask(
                collector_id=collector_id,
                data_type=demand.data_type,
                source_config={"demand_id": demand.demand_id},
                priority=SchedulePriority.HIGH if demand.urgency.value in ["high", "critical"] else SchedulePriority.NORMAL,
                expected_reward=demand.reward_offer
            )
            
            source_stats = self.source_stats.get(demand.data_type)
            score = self.policy.compute_task_score(task, state, source_stats)
            
            if score > best_score:
                best_score = score
                best_task = task
        
        if best_task:
            scheduled = self.coordinator.schedule_task(best_task)
            if scheduled:
                return best_task
        
        return None
    
    async def record_collection_result(
        self,
        task_id: str,
        success: bool,
        samples_collected: int = 0,
        quality: float = 0.5,
        energy_consumed: float = 0.0
    ):
        tasks = self.coordinator.get_collector_tasks(
            self.collector_states[list(self.collector_states.keys())[0]].collector_id
            if self.collector_states else ""
        )
        
        task = None
        for t in tasks:
            if t.task_id == task_id:
                task = t
                break
        
        if not task:
            return
        
        self.update_collector_state(
            task.collector_id,
            success=success,
            samples_collected=samples_collected
        )
        
        source_id = task.source_config.get("source_id", task.data_type)
        self.update_source_stats(
            source_id,
            task.data_type,
            success,
            samples_collected,
            quality
        )
        
        reward = task.expected_reward if success else 0
        self.policy.record_task_result(task, success, reward)
        
        self.coordinator.complete_task(task_id)
        
        self.logger.info(
            f"Collection result: task={task_id}, success={success}, "
            f"samples={samples_collected}, reward={reward}"
        )
    
    async def start_scheduling(self):
        if self._running:
            return
        
        self._running = True
        self._schedule_task = asyncio.create_task(self._scheduling_loop())
    
    async def stop_scheduling(self):
        self._running = False
        if self._schedule_task:
            self._schedule_task.cancel()
            try:
                await self._schedule_task
            except asyncio.CancelledError:
                pass
    
    async def _scheduling_loop(self):
        while self._running:
            try:
                for collector_id in self.collector_states:
                    task = await self.decide_next_collection(collector_id)
                    if task:
                        self.logger.debug(f"Auto-scheduled task {task.task_id}")
                
                await asyncio.sleep(self.schedule_interval.total_seconds())
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in scheduling loop: {e}")
                await asyncio.sleep(60)
    
    def get_schedule_stats(self) -> Dict[str, Any]:
        return {
            "registered_collectors": len(self.collector_states),
            "tracked_sources": len(self.source_stats),
            "scheduled_tasks": len(self.coordinator.scheduled_tasks),
            "avg_success_rate": sum(s.success_rate for s in self.collector_states.values()) / len(self.collector_states) if self.collector_states else 0,
            "policy_exploration_rate": self.policy.exploration_rate
        }
    
    def get_collector_schedule(self, collector_id: str) -> List[Dict[str, Any]]:
        tasks = self.coordinator.get_collector_tasks(collector_id)
        
        return [
            {
                "task_id": t.task_id,
                "data_type": t.data_type,
                "priority": t.priority.value,
                "scheduled_time": t.scheduled_time.isoformat() if t.scheduled_time else None,
                "status": t.status
            }
            for t in tasks
        ]
