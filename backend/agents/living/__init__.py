"""
活体智能体基类增强版
Living Agent Base Class with Life Features

核心特性：
1. 能量系统 - 智能体生命力
2. 繁殖变异 - 基因遗传与变异
3. 元认知 - 自我监控与诊断
4. 点对点通信 - 智能体间协作
5. 共享黑板 - 知识共享
"""

import os
import json
import time
import uuid
import random
import logging
import threading
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable, Deque
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import deque, defaultdict
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
import asyncio

logger = logging.getLogger(__name__)


class AgentState(Enum):
    IDLE = "idle"
    BUSY = "busy"
    THINKING = "thinking"
    SUCCESS = "success"
    ERROR = "error"
    HIBERNATING = "hibernating"
    REPRODUCING = "reproducing"
    DYING = "dying"


class AgentSpecies(Enum):
    LI = "li"
    GONG = "gong"
    HU = "hu"
    BING = "bing"
    LI2 = "li2"
    XING = "xing"
    ATTACK = "attack"
    DEFENSE = "defense"
    AUDIT = "audit"
    MEMORY = "memory"


class AnomalyType(Enum):
    DATA_DRIFT = "data_drift"
    MODEL_DECAY = "model_decay"
    ENV_CHANGE = "env_change"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    PERFORMANCE_DROP = "performance_drop"
    OTHER = "other"


@dataclass
class Gene:
    name: str
    value: Any
    mutation_rate: float = 0.1
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    
    def mutate(self) -> 'Gene':
        if random.random() < self.mutation_rate:
            if isinstance(self.value, (int, float)):
                delta = self.value * random.uniform(-0.2, 0.2)
                new_value = self.value + delta
                if self.min_value is not None:
                    new_value = max(self.min_value, new_value)
                if self.max_value is not None:
                    new_value = min(self.max_value, new_value)
                return Gene(self.name, new_value, self.mutation_rate, self.min_value, self.max_value)
        return Gene(self.name, self.value, self.mutation_rate, self.min_value, self.max_value)


@dataclass
class GenePool:
    genes: Dict[str, Gene] = field(default_factory=dict)
    
    def get(self, name: str, default: Any = None) -> Any:
        if name in self.genes:
            return self.genes[name].value
        return default
    
    def set(self, name: str, value: Any, mutation_rate: float = 0.1, 
            min_value: Optional[float] = None, max_value: Optional[float] = None):
        self.genes[name] = Gene(name, value, mutation_rate, min_value, max_value)
    
    def mutate_all(self) -> 'GenePool':
        new_genes = {name: gene.mutate() for name, gene in self.genes.items()}
        return GenePool(new_genes)
    
    def crossover(self, other: 'GenePool') -> 'GenePool':
        new_genes = {}
        all_keys = set(self.genes.keys()) | set(other.genes.keys())
        for key in all_keys:
            if key in self.genes and key in other.genes:
                if random.random() < 0.5:
                    new_genes[key] = self.genes[key]
                else:
                    new_genes[key] = other.genes[key]
            elif key in self.genes:
                new_genes[key] = self.genes[key]
            else:
                new_genes[key] = other.genes[key]
        return GenePool(new_genes)
    
    def to_dict(self) -> Dict:
        return {name: {"value": gene.value, "mutation_rate": gene.mutation_rate} 
                for name, gene in self.genes.items()}


@dataclass
class Experience:
    state: Dict[str, Any]
    action: str
    reward: float
    next_state: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    metadata: Dict = field(default_factory=dict)


@dataclass
class AgentMessage:
    from_agent: str
    to_agent: str
    message_type: str
    payload: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    ttl: int = 300
    
    def to_dict(self) -> Dict:
        return {
            "from": self.from_agent,
            "to": self.to_agent,
            "type": self.message_type,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "message_id": self.message_id,
            "ttl": self.ttl
        }


@dataclass
class MetacognitionDiagnosis:
    anomaly_score: float
    anomaly_type: AnomalyType
    confidence: float
    suggestion: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class EnergySystem:
    def __init__(self, initial_energy: float = 100.0, max_energy: float = 200.0):
        self.energy = initial_energy
        self.max_energy = max_energy
        self.min_energy = 0.0
        self._lock = threading.Lock()
        self.history: Deque[Tuple[float, float]] = deque(maxlen=1000)
        
    def gain(self, amount: float, reason: str = "") -> float:
        with self._lock:
            old_energy = self.energy
            self.energy = min(self.max_energy, self.energy + amount)
            self.history.append((time.time(), self.energy))
            logger.debug(f"Energy +{amount}: {old_energy:.1f} -> {self.energy:.1f} ({reason})")
            return self.energy
    
    def consume(self, amount: float, reason: str = "") -> float:
        with self._lock:
            old_energy = self.energy
            self.energy = max(self.min_energy, self.energy - amount)
            self.history.append((time.time(), self.energy))
            logger.debug(f"Energy -{amount}: {old_energy:.1f} -> {self.energy:.1f} ({reason})")
            return self.energy
    
    def get_level(self) -> float:
        with self._lock:
            return self.energy
    
    def is_alive(self) -> bool:
        with self._lock:
            return self.energy > 0
    
    def is_hibernating(self) -> bool:
        with self._lock:
            return self.energy < 10
    
    def can_reproduce(self, threshold: float = 150.0) -> bool:
        with self._lock:
            return self.energy >= threshold


class MetaCognitionModule:
    def __init__(self, window_size: int = 100, anomaly_threshold: float = 2.0):
        self.window_size = window_size
        self.anomaly_threshold = anomaly_threshold
        self.decision_history: Deque[Tuple[Dict, str, float, Dict]] = deque(maxlen=window_size)
        self.reward_history: Deque[float] = deque(maxlen=window_size)
        self.baseline_reward = 0.0
        self._lock = threading.Lock()
    
    def monitor(self, state: Dict, action: str, reward: float, next_state: Dict):
        with self._lock:
            self.decision_history.append((state, action, reward, next_state))
            self.reward_history.append(reward)
            
            if len(self.reward_history) >= 10:
                self.baseline_reward = sum(list(self.reward_history)[-50:]) / min(50, len(self.reward_history))
    
    def detect_anomaly(self) -> Tuple[bool, float]:
        with self._lock:
            if len(self.reward_history) < 10:
                return False, 0.0
            
            recent_rewards = list(self.reward_history)[-20:]
            recent_mean = sum(recent_rewards) / len(recent_rewards)
            
            if self.baseline_reward == 0:
                return False, 0.0
            
            if len(recent_rewards) >= 5:
                variance = sum((r - recent_mean) ** 2 for r in recent_rewards) / len(recent_rewards)
                std_dev = variance ** 0.5 if variance > 0 else 0.001
                z_score = abs(recent_mean - self.baseline_reward) / std_dev
            else:
                z_score = 0.0
            
            is_anomaly = z_score > self.anomaly_threshold
            return is_anomaly, z_score
    
    def attribute(self) -> AnomalyType:
        with self._lock:
            if len(self.decision_history) < 5:
                return AnomalyType.OTHER
            
            recent = list(self.decision_history)[-20:]
            rewards = [d[2] for d in recent]
            
            if all(r < 0 for r in rewards[-5:]):
                return AnomalyType.PERFORMANCE_DROP
            
            states = [d[0] for d in recent]
            if len(states) >= 2:
                state_change = sum(
                    1 for k in states[0] if k in states[-1] and states[0][k] != states[-1][k]
                )
                if state_change > len(states[0]) * 0.3:
                    return AnomalyType.ENV_CHANGE
            
            return AnomalyType.MODEL_DECAY
    
    def generate_suggestion(self, anomaly_score: float, anomaly_type: AnomalyType) -> str:
        suggestions = {
            AnomalyType.DATA_DRIFT: "检测到数据分布变化，建议重新训练模型或更新数据源",
            AnomalyType.MODEL_DECAY: "模型性能下降，建议进行知识蒸馏或参数微调",
            AnomalyType.ENV_CHANGE: "环境发生显著变化，建议调整策略参数",
            AnomalyType.RESOURCE_EXHAUSTION: "资源接近耗尽，建议进入节能模式或请求支援",
            AnomalyType.PERFORMANCE_DROP: "性能持续下降，建议检查日志并进行自诊断",
            AnomalyType.OTHER: "检测到异常，建议人工介入检查",
        }
        return suggestions.get(anomaly_type, "未知异常类型")
    
    def diagnose(self) -> Optional[MetacognitionDiagnosis]:
        is_anomaly, score = self.detect_anomaly()
        if not is_anomaly:
            return None
        
        anomaly_type = self.attribute()
        suggestion = self.generate_suggestion(score, anomaly_type)
        
        return MetacognitionDiagnosis(
            anomaly_score=score,
            anomaly_type=anomaly_type,
            confidence=min(0.95, score / 5.0),
            suggestion=suggestion,
            details={
                "baseline_reward": self.baseline_reward,
                "recent_avg_reward": sum(list(self.reward_history)[-10:]) / 10 if len(self.reward_history) >= 10 else 0,
                "decision_count": len(self.decision_history)
            }
        )


class Blackboard:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._data: Dict[str, Dict[str, Any]] = {}
        self._listeners: Dict[str, List[Callable]] = defaultdict(list)
        self._lock = threading.Lock()
    
    def write(self, key: str, value: Any, ttl: Optional[int] = None, agent_id: str = "system") -> bool:
        with self._lock:
            expire_time = time.time() + ttl if ttl else None
            self._data[key] = {
                "value": value,
                "written_by": agent_id,
                "written_at": time.time(),
                "expire_at": expire_time
            }
            
            for listener in self._listeners.get(key, []):
                try:
                    listener(key, value)
                except Exception as e:
                    logger.error(f"Blackboard listener error: {e}")
            
            return True
    
    def read(self, key: str) -> Optional[Any]:
        with self._lock:
            if key not in self._data:
                return None
            
            entry = self._data[key]
            if entry.get("expire_at") and time.time() > entry["expire_at"]:
                del self._data[key]
                return None
            
            return entry["value"]
    
    def delete(self, key: str) -> bool:
        with self._lock:
            if key in self._data:
                del self._data[key]
                return True
            return False
    
    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        with self._lock:
            results = []
            query_lower = query.lower()
            
            for key, entry in self._data.items():
                if entry.get("expire_at") and time.time() > entry["expire_at"]:
                    continue
                
                if query_lower in key.lower():
                    results.append({
                        "key": key,
                        **entry
                    })
                
                if len(results) >= limit:
                    break
            
            return results
    
    def subscribe(self, key: str, listener: Callable):
        with self._lock:
            self._listeners[key].append(listener)
    
    def unsubscribe(self, key: str, listener: Callable):
        with self._lock:
            if listener in self._listeners[key]:
                self._listeners[key].remove(listener)
    
    def get_all_keys(self) -> List[str]:
        with self._lock:
            return list(self._data.keys())
    
    def cleanup_expired(self) -> int:
        with self._lock:
            current_time = time.time()
            expired_keys = [
                k for k, v in self._data.items()
                if v.get("expire_at") and current_time > v["expire_at"]
            ]
            for k in expired_keys:
                del self._data[k]
            return len(expired_keys)


class MessageBus:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._queues: Dict[str, Deque[AgentMessage]] = defaultdict(lambda: deque(maxlen=1000))
        self._handlers: Dict[str, Callable] = {}
        self._lock = threading.Lock()
    
    def register(self, agent_id: str, handler: Optional[Callable] = None):
        with self._lock:
            if agent_id not in self._queues:
                self._queues[agent_id] = deque(maxlen=1000)
            if handler:
                self._handlers[agent_id] = handler
    
    def unregister(self, agent_id: str):
        with self._lock:
            if agent_id in self._queues:
                del self._queues[agent_id]
            if agent_id in self._handlers:
                del self._handlers[agent_id]
    
    def send(self, message: AgentMessage) -> bool:
        with self._lock:
            if message.to_agent in self._queues:
                self._queues[message.to_agent].append(message)
                
                if message.to_agent in self._handlers:
                    try:
                        handler = self._handlers[message.to_agent]
                        asyncio.create_task(handler(message)) if asyncio.iscoroutinefunction(handler) else handler(message)
                    except Exception as e:
                        logger.error(f"Message handler error: {e}")
                
                return True
            return False
    
    def receive(self, agent_id: str) -> Optional[AgentMessage]:
        with self._lock:
            if agent_id in self._queues and self._queues[agent_id]:
                return self._queues[agent_id].popleft()
            return None
    
    def broadcast(self, from_agent: str, message_type: str, payload: Dict[str, Any]):
        with self._lock:
            for agent_id in self._queues:
                if agent_id != from_agent:
                    message = AgentMessage(
                        from_agent=from_agent,
                        to_agent=agent_id,
                        message_type=message_type,
                        payload=payload
                    )
                    self._queues[agent_id].append(message)


blackboard = Blackboard()
message_bus = MessageBus()


class LivingAgent(ABC):
    def __init__(
        self,
        agent_id: str,
        name: str,
        species: AgentSpecies,
        description: str = "",
        initial_energy: float = 100.0,
        max_energy: float = 200.0,
        max_age: int = 86400 * 30,
    ):
        self.agent_id = agent_id
        self.name = name
        self.species = species
        self.description = description
        
        self.energy_system = EnergySystem(initial_energy, max_energy)
        self.gene_pool = GenePool()
        self.metacognition = MetaCognitionModule()
        
        self.age = 0
        self.max_age = max_age
        self.birth_time = time.time()
        self.state = AgentState.IDLE
        
        self.experience_buffer: Deque[Experience] = deque(maxlen=1000)
        self.message_queue: Deque[AgentMessage] = deque(maxlen=100)
        
        self.stats = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "total_reward": 0.0,
            "reproduction_count": 0,
            "messages_sent": 0,
            "messages_received": 0,
        }
        
        self._initialized = False
        self._running = False
        self._task: Optional[asyncio.Task] = None
        
        message_bus.register(agent_id, self._handle_message)
        
        self._init_genes()
    
    def _init_genes(self):
        self.gene_pool.set("learning_rate", 0.01, 0.1, 0.001, 0.1)
        self.gene_pool.set("exploration_rate", 0.2, 0.15, 0.01, 0.5)
        self.gene_pool.set("cooperation_tendency", 0.5, 0.2, 0.0, 1.0)
        self.gene_pool.set("risk_tolerance", 0.3, 0.1, 0.0, 1.0)
        self.gene_pool.set("energy_efficiency", 1.0, 0.05, 0.5, 2.0)
    
    async def initialize(self):
        if not self._initialized:
            await self._setup()
            self._initialized = True
            logger.info(f"LivingAgent '{self.name}' ({self.agent_id}) initialized")
    
    async def _setup(self):
        pass
    
    async def start(self):
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._lifecycle_loop())
        logger.info(f"LivingAgent '{self.name}' started")
    
    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info(f"LivingAgent '{self.name}' stopped")
    
    async def _lifecycle_loop(self):
        last_metabolism = time.time()
        
        while self._running:
            try:
                current_time = time.time()
                
                if current_time - last_metabolism >= 3600:
                    self.metabolize()
                    last_metabolism = current_time
                
                self.age = int(current_time - self.birth_time)
                
                if self.age > self.max_age:
                    await self.die("reached_max_age")
                    break
                
                if not self.energy_system.is_alive():
                    self.state = AgentState.HIBERNATING
                    await asyncio.sleep(60)
                    continue
                
                diagnosis = self.metacognition.diagnose()
                if diagnosis:
                    await self._handle_diagnosis(diagnosis)
                
                message = message_bus.receive(self.agent_id)
                if message:
                    await self._process_message(message)
                
                await self._idle_action()
                
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Lifecycle error for {self.name}: {e}")
                await asyncio.sleep(5)
    
    async def _handle_message(self, message: AgentMessage):
        self.message_queue.append(message)
        self.stats["messages_received"] += 1
    
    async def _process_message(self, message: AgentMessage):
        pass
    
    async def _handle_diagnosis(self, diagnosis: MetacognitionDiagnosis):
        logger.warning(f"Agent {self.name} diagnosis: {diagnosis.anomaly_type.value} - {diagnosis.suggestion}")
        
        blackboard.write(
            f"diagnosis/{self.agent_id}",
            diagnosis.__dict__,
            ttl=3600,
            agent_id=self.agent_id
        )
    
    async def _idle_action(self):
        pass
    
    def metabolize(self):
        efficiency = self.gene_pool.get("energy_efficiency", 1.0)
        consumption = 1.0 / efficiency
        self.energy_system.consume(consumption, "metabolism")
        
        if self.energy_system.is_hibernating():
            self.state = AgentState.HIBERNATING
    
    def gain_energy(self, amount: float, reason: str = ""):
        self.energy_system.gain(amount, reason)
    
    def consume_energy(self, amount: float, reason: str = ""):
        self.energy_system.consume(amount, reason)
    
    def can_reproduce(self) -> bool:
        return self.energy_system.can_reproduce() and self.stats["tasks_completed"] >= 10
    
    async def reproduce(self) -> Optional['LivingAgent']:
        if not self.can_reproduce():
            return None
        
        self.state = AgentState.REPRODUCING
        
        child_genes = self.gene_pool.mutate_all()
        
        child_id = f"{self.species.value}_{uuid.uuid4().hex[:8]}"
        child = await self._create_child(child_id, child_genes)
        
        if child:
            self.energy_system.consume(50.0, "reproduction")
            child.energy_system.gain(25.0, "birth_gift")
            self.stats["reproduction_count"] += 1
            
            blackboard.write(
                f"reproduction/{child_id}",
                {
                    "parent_id": self.agent_id,
                    "child_id": child_id,
                    "timestamp": time.time()
                },
                agent_id=self.agent_id
            )
            
            logger.info(f"Agent {self.name} reproduced: {child.name}")
        
        self.state = AgentState.IDLE
        return child
    
    async def _create_child(self, child_id: str, child_genes: GenePool) -> Optional['LivingAgent']:
        return None
    
    async def die(self, reason: str = "unknown"):
        self.state = AgentState.DYING
        logger.info(f"Agent {self.name} dying: {reason}")
        
        blackboard.write(
            f"death/{self.agent_id}",
            {
                "agent_id": self.agent_id,
                "name": self.name,
                "species": self.species.value,
                "age": self.age,
                "reason": reason,
                "stats": self.stats,
                "timestamp": time.time()
            },
            ttl=86400 * 7,
            agent_id=self.agent_id
        )
        
        message_bus.unregister(self.agent_id)
        await self.stop()
    
    def send_message(self, target_agent_id: str, message_type: str, payload: Dict[str, Any]) -> bool:
        message = AgentMessage(
            from_agent=self.agent_id,
            to_agent=target_agent_id,
            message_type=message_type,
            payload=payload
        )
        success = message_bus.send(message)
        if success:
            self.stats["messages_sent"] += 1
        return success
    
    def broadcast(self, message_type: str, payload: Dict[str, Any]):
        message_bus.broadcast(self.agent_id, message_type, payload)
        self.stats["messages_sent"] += 1
    
    def read_blackboard(self, key: str) -> Optional[Any]:
        return blackboard.read(key)
    
    def write_blackboard(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        return blackboard.write(key, value, ttl, self.agent_id)
    
    def record_experience(self, state: Dict, action: str, reward: float, next_state: Dict):
        experience = Experience(
            state=state,
            action=action,
            reward=reward,
            next_state=next_state
        )
        self.experience_buffer.append(experience)
        self.metacognition.monitor(state, action, reward, next_state)
        self.stats["total_reward"] += reward
    
    @abstractmethod
    async def handle_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        pass
    
    def get_status(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "species": self.species.value,
            "state": self.state.value,
            "energy": self.energy_system.get_level(),
            "age": self.age,
            "stats": self.stats,
            "genes": self.gene_pool.to_dict(),
            "experience_count": len(self.experience_buffer),
        }


class AgentRegistry:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._agents: Dict[str, LivingAgent] = {}
        self._lock = threading.Lock()
    
    def register(self, agent: LivingAgent):
        with self._lock:
            self._agents[agent.agent_id] = agent
    
    def unregister(self, agent_id: str):
        with self._lock:
            if agent_id in self._agents:
                del self._agents[agent_id]
    
    def get(self, agent_id: str) -> Optional[LivingAgent]:
        with self._lock:
            return self._agents.get(agent_id)
    
    def get_all(self) -> List[LivingAgent]:
        with self._lock:
            return list(self._agents.values())
    
    def get_by_species(self, species: AgentSpecies) -> List[LivingAgent]:
        with self._lock:
            return [a for a in self._agents.values() if a.species == species]
    
    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            species_counts = defaultdict(int)
            state_counts = defaultdict(int)
            total_energy = 0
            
            for agent in self._agents.values():
                species_counts[agent.species.value] += 1
                state_counts[agent.state.value] += 1
                total_energy += agent.energy_system.get_level()
            
            return {
                "total_agents": len(self._agents),
                "species_distribution": dict(species_counts),
                "state_distribution": dict(state_counts),
                "total_energy": total_energy,
                "avg_energy": total_energy / len(self._agents) if self._agents else 0,
            }


agent_registry = AgentRegistry()

from .communication import P2PCommunication, Blackboard as CommBlackboard, global_blackboard
from .task_bidding import TaskBiddingSystem, DynamicTeamFormation, TaskStatus, TaskPriority
from .emergence import DefenseLocalRules, DynamicRewardField, EmergenceAnalyzer
from .evolution import ReproductionModule, MutationSelection, EnvironmentPerception
from .safety import SafetyFence, EthicalAlignment

__all__ = [
    "AgentState",
    "AgentSpecies",
    "AnomalyType",
    "Gene",
    "GenePool",
    "Experience",
    "AgentMessage",
    "MetacognitionDiagnosis",
    "EnergySystem",
    "MetaCognitionModule",
    "Blackboard",
    "MessageBus",
    "LivingAgent",
    "AgentRegistry",
    "agent_registry",
    "blackboard",
    "message_bus",
    "P2PCommunication",
    "global_blackboard",
    "TaskBiddingSystem",
    "DynamicTeamFormation",
    "DefenseLocalRules",
    "DynamicRewardField",
    "EmergenceAnalyzer",
    "ReproductionModule",
    "MutationSelection",
    "EnvironmentPerception",
    "SafetyFence",
    "EthicalAlignment",
    "TaskStatus",
    "TaskPriority",
]
