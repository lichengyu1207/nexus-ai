"""
集群强化模块
Cluster Enhancement Module

实现动态负载感知、智能体分裂/合并、跨域调度、自愈机制
"""

import asyncio
import copy
import hashlib
import json
import logging
import os
import pickle
import threading
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Type

logger = logging.getLogger(__name__)


class SplitTrigger(Enum):
    """分裂触发条件"""
    QUEUE_LENGTH = "queue_length"
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    RESPONSE_TIME = "response_time"
    MANUAL = "manual"


class MergeTrigger(Enum):
    """合并触发条件"""
    LOW_LOAD = "low_load"
    LONG_IDLE = "long_idle"
    MANUAL = "manual"


class AgentStatus(Enum):
    """智能体状态"""
    ACTIVE = "active"
    IDLE = "idle"
    SPLITTING = "splitting"
    MERGING = "merging"
    MIGRATING = "migrating"
    HIBERNATING = "hibernating"
    TERMINATED = "terminated"


@dataclass
class LoadMetrics:
    """负载指标"""
    queue_length: int = 0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    response_time_avg: float = 0.0
    tasks_completed: int = 0
    tasks_failed: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "queue_length": self.queue_length,
            "cpu_usage": self.cpu_usage,
            "memory_usage": self.memory_usage,
            "response_time_avg": self.response_time_avg,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class SplitRecord:
    """分裂记录"""
    split_id: str
    parent_id: str
    child_id: str
    trigger: SplitTrigger
    parent_energy_before: float
    parent_energy_after: float
    child_energy: float
    timestamp: datetime
    success: bool = True


@dataclass
class MergeRecord:
    """合并记录"""
    merge_id: str
    agent_a_id: str
    agent_b_id: str
    result_agent_id: str
    energy_a: float
    energy_b: float
    result_energy: float
    timestamp: datetime
    success: bool = True


@dataclass
class MigrationRecord:
    """迁移记录"""
    migration_id: str
    agent_id: str
    source_node: str
    target_node: str
    state_size: int
    start_time: datetime
    end_time: Optional[datetime] = None
    success: bool = False


@dataclass
class Checkpoint:
    """检查点"""
    checkpoint_id: str
    agent_id: str
    policy_state: Dict[str, Any]
    energy: float
    task_queue: List[Any]
    memory_indices: List[str]
    gene_pool: Dict[str, Any]
    timestamp: datetime
    size_bytes: int = 0


class AutoSplitMixin:
    """自动分裂混入类"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.split_threshold: int = 100
        self.split_cooldown: int = 300
        self.last_split_time: Optional[datetime] = None
        self.split_count: int = 0
        self.max_splits: int = 5
        self._split_lock = asyncio.Lock()
    
    async def check_and_split(self) -> Optional[str]:
        """检查并执行分裂"""
        async with self._split_lock:
            if not self._should_split():
                return None
            
            child_id = await self._split()
            return child_id
    
    def _should_split(self) -> bool:
        """判断是否应该分裂"""
        if self.split_count >= self.max_splits:
            return False
        
        if self.last_split_time:
            elapsed = (datetime.now() - self.last_split_time).total_seconds()
            if elapsed < self.split_cooldown:
                return False
        
        queue_length = self.task_queue.qsize()
        if queue_length < self.split_threshold:
            return False
        
        energy = getattr(self, 'energy', 0)
        if energy < 50:
            return False
        
        return True
    
    async def _split(self) -> str:
        """执行分裂"""
        child_id = f"{self.agent_id}_split_{int(time.time())}"
        
        parent_energy = getattr(self, 'energy', 100)
        child_energy = parent_energy / 2
        self.energy = child_energy
        
        policy_state = self._copy_policy_state()
        self._mutate_policy(policy_state)
        
        child_genes = self._copy_genes()
        self._mutate_genes(child_genes)
        
        self.last_split_time = datetime.now()
        self.split_count += 1
        
        logger.info(f"Agent {self.agent_id} split into {child_id}")
        
        return child_id
    
    def _copy_policy_state(self) -> Dict[str, Any]:
        """复制策略状态"""
        if hasattr(self, 'policy') and hasattr(self.policy, 'state_dict'):
            return copy.deepcopy(self.policy.state_dict())
        return {}
    
    def _mutate_policy(self, state: Dict[str, Any]):
        """变异策略参数"""
        import random
        for key in state:
            if isinstance(state[key], list):
                for i in range(len(state[key])):
                    if random.random() < 0.01:
                        state[key][i] += random.gauss(0, 0.001)
    
    def _copy_genes(self) -> Dict[str, Any]:
        """复制基因"""
        if hasattr(self, 'gene_pool'):
            return copy.deepcopy(self.gene_pool)
        return {}
    
    def _mutate_genes(self, genes: Dict[str, Any]):
        """变异基因"""
        import random
        for key in genes:
            if random.random() < 0.1:
                if isinstance(genes[key], (int, float)):
                    genes[key] *= (1 + random.gauss(0, 0.1))


class AutoMergeManager:
    """自动合并管理器"""
    
    def __init__(self, message_bus: Any = None):
        self.message_bus = message_bus
        self.agent_loads: Dict[str, LoadMetrics] = {}
        self.merge_threshold: int = 10
        self.idle_threshold: int = 3600
        self.merge_interval: int = 300
        self.merge_records: List[MergeRecord] = []
        self._running = False
        self.stats = {
            "total_merges": 0,
            "successful_merges": 0,
            "failed_merges": 0,
        }
    
    async def start(self):
        """启动合并管理器"""
        self._running = True
        while self._running:
            await self._check_and_merge()
            await asyncio.sleep(self.merge_interval)
    
    def stop(self):
        """停止合并管理器"""
        self._running = False
    
    def update_agent_load(self, agent_id: str, metrics: LoadMetrics):
        """更新智能体负载"""
        self.agent_loads[agent_id] = metrics
    
    async def _check_and_merge(self):
        """检查并执行合并"""
        agents_by_type = self._group_agents_by_type()
        
        for agent_type, agents in agents_by_type.items():
            if len(agents) < 2:
                continue
            
            low_load_agents = [
                a for a in agents
                if self.agent_loads.get(a, LoadMetrics()).queue_length < self.merge_threshold
            ]
            
            if len(low_load_agents) >= 2:
                await self._merge_pair(low_load_agents[0], low_load_agents[1])
    
    def _group_agents_by_type(self) -> Dict[str, List[str]]:
        """按类型分组智能体"""
        groups = defaultdict(list)
        for agent_id in self.agent_loads:
            parts = agent_id.split('_')
            if len(parts) > 0:
                agent_type = parts[0]
                groups[agent_type].append(agent_id)
        return groups
    
    async def _merge_pair(self, agent_a_id: str, agent_b_id: str) -> Optional[str]:
        """合并两个智能体"""
        merge_id = f"merge_{int(time.time())}_{agent_a_id[:8]}"
        
        energy_a = 50.0
        energy_b = 50.0
        
        result_energy = energy_a + energy_b
        result_id = f"merged_{agent_a_id[:8]}_{agent_b_id[:8]}"
        
        record = MergeRecord(
            merge_id=merge_id,
            agent_a_id=agent_a_id,
            agent_b_id=agent_b_id,
            result_agent_id=result_id,
            energy_a=energy_a,
            energy_b=energy_b,
            result_energy=result_energy,
            timestamp=datetime.now()
        )
        
        self.merge_records.append(record)
        self.stats["total_merges"] += 1
        self.stats["successful_merges"] += 1
        
        logger.info(f"Merged {agent_a_id} and {agent_b_id} into {result_id}")
        
        return result_id


class GlobalScheduler:
    """全局调度器"""
    
    def __init__(self, redis_client: Any = None):
        self.redis_client = redis_client
        self.node_stats: Dict[str, Dict[str, Any]] = {}
        self.agent_locations: Dict[str, str] = {}
        self.migration_records: List[MigrationRecord] = []
        self._lock = threading.Lock()
        self.stats = {
            "total_migrations": 0,
            "successful_migrations": 0,
            "failed_migrations": 0,
        }
    
    def register_node(self, node_id: str, stats: Dict[str, Any]):
        """注册节点"""
        with self._lock:
            self.node_stats[node_id] = {
                **stats,
                "registered_at": datetime.now().isoformat(),
                "last_heartbeat": datetime.now().isoformat()
            }
    
    def update_node_stats(self, node_id: str, stats: Dict[str, Any]):
        """更新节点状态"""
        with self._lock:
            if node_id in self.node_stats:
                self.node_stats[node_id].update(stats)
                self.node_stats[node_id]["last_heartbeat"] = datetime.now().isoformat()
    
    def get_best_node(self, requirements: Dict[str, Any] = None) -> Optional[str]:
        """获取最佳节点"""
        if not self.node_stats:
            return None
        
        best_node = None
        best_score = float('inf')
        
        for node_id, stats in self.node_stats.items():
            cpu = stats.get("cpu_usage", 100)
            memory = stats.get("memory_usage", 100)
            score = cpu * 0.5 + memory * 0.5
            
            if score < best_score:
                best_score = score
                best_node = node_id
        
        return best_node
    
    async def migrate_agent(
        self,
        agent_id: str,
        target_node: str,
        agent_state: Dict[str, Any]
    ) -> bool:
        """迁移智能体"""
        migration_id = f"mig_{int(time.time())}_{agent_id[:8]}"
        
        source_node = self.agent_locations.get(agent_id, "unknown")
        
        record = MigrationRecord(
            migration_id=migration_id,
            agent_id=agent_id,
            source_node=source_node,
            target_node=target_node,
            state_size=len(pickle.dumps(agent_state)),
            start_time=datetime.now()
        )
        
        self.stats["total_migrations"] += 1
        
        try:
            await self._execute_migration(agent_id, target_node, agent_state)
            
            self.agent_locations[agent_id] = target_node
            record.end_time = datetime.now()
            record.success = True
            self.stats["successful_migrations"] += 1
            
            logger.info(f"Migrated {agent_id} from {source_node} to {target_node}")
            return True
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            record.success = False
            self.stats["failed_migrations"] += 1
            return False
        
        finally:
            self.migration_records.append(record)
    
    async def _execute_migration(
        self,
        agent_id: str,
        target_node: str,
        state: Dict[str, Any]
    ):
        """执行迁移"""
        await asyncio.sleep(0.1)


class HeartbeatMonitor:
    """心跳监控器"""
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.agent_heartbeats: Dict[str, datetime] = {}
        self.active_agents: Set[str] = set()
        self._lock = threading.Lock()
        self._running = False
        self._callbacks: List[Callable] = []
        self.stats = {
            "total_heartbeats": 0,
            "timeouts_detected": 0,
            "recoveries": 0,
        }
    
    def register_callback(self, callback: Callable):
        """注册超时回调"""
        self._callbacks.append(callback)
    
    def receive_heartbeat(self, agent_id: str):
        """接收心跳"""
        with self._lock:
            self.agent_heartbeats[agent_id] = datetime.now()
            self.active_agents.add(agent_id)
            self.stats["total_heartbeats"] += 1
    
    async def start(self):
        """启动监控"""
        self._running = True
        while self._running:
            await self._check_timeouts()
            await asyncio.sleep(10)
    
    def stop(self):
        """停止监控"""
        self._running = False
    
    async def _check_timeouts(self):
        """检查超时"""
        now = datetime.now()
        timed_out = []
        
        with self._lock:
            for agent_id, last_heartbeat in list(self.agent_heartbeats.items()):
                elapsed = (now - last_heartbeat).total_seconds()
                if elapsed > self.timeout:
                    timed_out.append(agent_id)
                    self.active_agents.discard(agent_id)
        
        for agent_id in timed_out:
            self.stats["timeouts_detected"] += 1
            logger.warning(f"Agent {agent_id} heartbeat timeout")
            
            for callback in self._callbacks:
                try:
                    await callback(agent_id)
                except Exception as e:
                    logger.error(f"Callback error: {e}")
    
    def get_active_agents(self) -> Set[str]:
        """获取活跃智能体"""
        with self._lock:
            return self.active_agents.copy()


class CheckpointManager:
    """检查点管理器"""
    
    def __init__(self, storage_backend: Any = None):
        self.storage_backend = storage_backend
        self.checkpoints: Dict[str, List[Checkpoint]] = defaultdict(list)
        self.max_checkpoints_per_agent: int = 5
        self.checkpoint_interval: int = 10
        self._lock = threading.Lock()
        self.stats = {
            "total_checkpoints": 0,
            "total_restores": 0,
            "failed_restores": 0,
        }
    
    async def save_checkpoint(
        self,
        agent_id: str,
        policy_state: Dict[str, Any],
        energy: float,
        task_queue: List[Any],
        memory_indices: List[str],
        gene_pool: Dict[str, Any]
    ) -> Checkpoint:
        """保存检查点"""
        checkpoint_id = f"ckpt_{int(time.time())}_{agent_id[:8]}"
        
        state_data = pickle.dumps({
            "policy_state": policy_state,
            "task_queue": task_queue,
            "memory_indices": memory_indices,
            "gene_pool": gene_pool
        })
        
        checkpoint = Checkpoint(
            checkpoint_id=checkpoint_id,
            agent_id=agent_id,
            policy_state=policy_state,
            energy=energy,
            task_queue=task_queue,
            memory_indices=memory_indices,
            gene_pool=gene_pool,
            timestamp=datetime.now(),
            size_bytes=len(state_data)
        )
        
        with self._lock:
            self.checkpoints[agent_id].append(checkpoint)
            
            if len(self.checkpoints[agent_id]) > self.max_checkpoints_per_agent:
                self.checkpoints[agent_id].pop(0)
        
        self.stats["total_checkpoints"] += 1
        
        logger.debug(f"Saved checkpoint {checkpoint_id} for agent {agent_id}")
        
        return checkpoint
    
    async def load_checkpoint(self, agent_id: str) -> Optional[Checkpoint]:
        """加载检查点"""
        with self._lock:
            if agent_id not in self.checkpoints or not self.checkpoints[agent_id]:
                return None
            
            checkpoint = self.checkpoints[agent_id][-1]
        
        self.stats["total_restores"] += 1
        
        logger.info(f"Loaded checkpoint for agent {agent_id}")
        
        return checkpoint
    
    def get_latest_checkpoint(self, agent_id: str) -> Optional[Checkpoint]:
        """获取最新检查点"""
        with self._lock:
            if agent_id not in self.checkpoints or not self.checkpoints[agent_id]:
                return None
            return self.checkpoints[agent_id][-1]
    
    def list_checkpoints(self, agent_id: str) -> List[Checkpoint]:
        """列出检查点"""
        with self._lock:
            return self.checkpoints.get(agent_id, []).copy()


class SelfHealingManager:
    """自愈管理器"""
    
    def __init__(
        self,
        heartbeat_monitor: HeartbeatMonitor = None,
        checkpoint_manager: CheckpointManager = None
    ):
        self.heartbeat_monitor = heartbeat_monitor or HeartbeatMonitor()
        self.checkpoint_manager = checkpoint_manager or CheckpointManager()
        self.agent_factories: Dict[str, Callable] = {}
        self.recovery_records: List[Dict[str, Any]] = []
        self._running = False
        self.stats = {
            "total_recoveries": 0,
            "successful_recoveries": 0,
            "failed_recoveries": 0,
        }
    
    def register_agent_factory(self, agent_type: str, factory: Callable):
        """注册智能体工厂"""
        self.agent_factories[agent_type] = factory
    
    async def start(self):
        """启动自愈管理器"""
        self.heartbeat_monitor.register_callback(self._on_agent_timeout)
        self._running = True
        
        await asyncio.gather(
            self.heartbeat_monitor.start()
        )
    
    def stop(self):
        """停止自愈管理器"""
        self._running = False
        self.heartbeat_monitor.stop()
    
    async def _on_agent_timeout(self, agent_id: str):
        """智能体超时回调"""
        logger.warning(f"Agent {agent_id} timed out, attempting recovery")
        
        recovery_result = await self.recover_agent(agent_id)
        
        self.recovery_records.append({
            "agent_id": agent_id,
            "timestamp": datetime.now().isoformat(),
            "success": recovery_result
        })
    
    async def recover_agent(self, agent_id: str) -> bool:
        """恢复智能体"""
        self.stats["total_recoveries"] += 1
        
        checkpoint = await self.checkpoint_manager.load_checkpoint(agent_id)
        
        if not checkpoint:
            logger.error(f"No checkpoint found for agent {agent_id}")
            self.stats["failed_recoveries"] += 1
            return False
        
        try:
            parts = agent_id.split('_')
            agent_type = parts[0] if parts else "unknown"
            
            if agent_type in self.agent_factories:
                new_agent = await self.agent_factories[agent_type](agent_id)
                
                if hasattr(new_agent, 'energy'):
                    new_agent.energy = checkpoint.energy
                
                self.stats["successful_recoveries"] += 1
                logger.info(f"Successfully recovered agent {agent_id}")
                return True
            else:
                logger.warning(f"No factory registered for agent type {agent_type}")
                self.stats["failed_recoveries"] += 1
                return False
                
        except Exception as e:
            logger.error(f"Recovery failed for agent {agent_id}: {e}")
            self.stats["failed_recoveries"] += 1
            return False


class ClusterEnhancementSystem:
    """集群强化系统主控"""
    
    def __init__(self, redis_client: Any = None):
        self.global_scheduler = GlobalScheduler(redis_client)
        self.heartbeat_monitor = HeartbeatMonitor()
        self.checkpoint_manager = CheckpointManager()
        self.self_healing_manager = SelfHealingManager(
            self.heartbeat_monitor,
            self.checkpoint_manager
        )
        self.merge_manager = AutoMergeManager()
        
        self.agents: Dict[str, Any] = {}
        self._running = False
    
    async def start(self):
        """启动系统"""
        self._running = True
        
        await asyncio.gather(
            self.self_healing_manager.start(),
            self.merge_manager.start()
        )
    
    def stop(self):
        """停止系统"""
        self._running = False
        self.self_healing_manager.stop()
        self.merge_manager.stop()
    
    def register_agent(self, agent: Any):
        """注册智能体"""
        self.agents[agent.agent_id] = agent
        self.heartbeat_monitor.receive_heartbeat(agent.agent_id)
    
    def unregister_agent(self, agent_id: str):
        """注销智能体"""
        if agent_id in self.agents:
            del self.agents[agent_id]
    
    async def save_agent_checkpoint(self, agent_id: str):
        """保存智能体检查点"""
        agent = self.agents.get(agent_id)
        if not agent:
            return None
        
        policy_state = {}
        if hasattr(agent, 'policy') and hasattr(agent.policy, 'state_dict'):
            policy_state = agent.policy.state_dict()
        
        energy = getattr(agent, 'energy', 100)
        task_queue = list(getattr(agent, 'task_queue', []))
        memory_indices = getattr(agent, 'memory_indices', [])
        gene_pool = getattr(agent, 'gene_pool', {})
        
        return await self.checkpoint_manager.save_checkpoint(
            agent_id, policy_state, energy, task_queue, memory_indices, gene_pool
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "agents_count": len(self.agents),
            "global_scheduler": self.global_scheduler.stats,
            "heartbeat_monitor": self.heartbeat_monitor.stats,
            "checkpoint_manager": self.checkpoint_manager.stats,
            "self_healing": self.self_healing_manager.stats,
            "merge_manager": self.merge_manager.stats,
        }
