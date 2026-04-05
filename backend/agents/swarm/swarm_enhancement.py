"""
蜂群强化模块
Swarm Enhancement Module

实现自适应共识协议、群体免疫、涌现智能孵化器
"""

import asyncio
import copy
import hashlib
import json
import logging
import random
import threading
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class ConsensusType(Enum):
    """共识类型"""
    RAFT = "raft"
    PBFT = "pbft"
    GOSSIP = "gossip"
    NONE = "none"


class TrustLevel(Enum):
    """信任等级"""
    TRUSTED = "trusted"
    NORMAL = "normal"
    SUSPICIOUS = "suspicious"
    QUARANTINED = "quarantined"
    BLACKLISTED = "blacklisted"


class MutationType(Enum):
    """变异类型"""
    WEIGHT_NOISE = "weight_noise"
    LAYER_ADD = "layer_add"
    ACTIVATION_CHANGE = "activation_change"
    HYBRID = "hybrid"


@dataclass
class NetworkStats:
    """网络状态"""
    node_count: int
    avg_latency: float
    byzantine_ratio: float
    message_rate: float
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class TrustRecord:
    """信任记录"""
    agent_id: str
    trust_score: float
    level: TrustLevel
    interactions: int
    consistent_count: int
    inconsistent_count: int
    last_updated: datetime
    quarantine_start: Optional[datetime] = None
    quarantine_reason: str = ""


@dataclass
class MutationCandidate:
    """变异候选"""
    candidate_id: str
    source_agent_id: str
    mutation_type: MutationType
    mutation_params: Dict[str, Any]
    fitness_score: float
    created_at: datetime
    evaluated: bool = False


@dataclass
class EvolutionRecord:
    """进化记录"""
    generation: int
    population_size: int
    avg_fitness: float
    best_fitness: float
    mutations_applied: int
    replacements: int
    timestamp: datetime


class AdaptiveConsensus:
    """自适应共识协议"""
    
    def __init__(self, node_id: str = "default"):
        self.node_id = node_id
        self.current_consensus: ConsensusType = ConsensusType.RAFT
        self.network_stats = NetworkStats(
            node_count=1,
            avg_latency=0.0,
            byzantine_ratio=0.0,
            message_rate=0.0
        )
        self.pending_proposals: deque = deque(maxlen=1000)
        self.stats = {
            "total_proposals": 0,
            "successful_proposals": 0,
            "consensus_switches": 0,
            "by_type": defaultdict(int),
        }
        self._lock = threading.Lock()
    
    def update_network_stats(
        self,
        node_count: int,
        avg_latency: float,
        byzantine_ratio: float,
        message_rate: float
    ):
        """更新网络状态"""
        self.network_stats = NetworkStats(
            node_count=node_count,
            avg_latency=avg_latency,
            byzantine_ratio=byzantine_ratio,
            message_rate=message_rate
        )
        
        new_consensus = self._choose_consensus()
        if new_consensus != self.current_consensus:
            self._switch_consensus(new_consensus)
    
    def _choose_consensus(self) -> ConsensusType:
        """选择共识算法"""
        stats = self.network_stats
        
        if stats.byzantine_ratio > 0.1:
            return ConsensusType.PBFT
        
        if stats.node_count < 10 and stats.avg_latency < 100:
            return ConsensusType.RAFT
        
        if stats.node_count > 100:
            return ConsensusType.GOSSIP
        
        return ConsensusType.RAFT
    
    def _switch_consensus(self, new_consensus: ConsensusType):
        """切换共识算法"""
        old_consensus = self.current_consensus
        
        pending = list(self.pending_proposals)
        self.pending_proposals.clear()
        
        self.current_consensus = new_consensus
        self.stats["consensus_switches"] += 1
        
        for proposal in pending:
            self.pending_proposals.append(proposal)
        
        logger.info(f"Switched consensus from {old_consensus.value} to {new_consensus.value}")
    
    async def propose(self, value: Any) -> bool:
        """提议"""
        self.stats["total_proposals"] += 1
        self.stats["by_type"][self.current_consensus.value] += 1
        
        proposal_id = f"prop_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        if self.current_consensus == ConsensusType.RAFT:
            result = await self._raft_propose(proposal_id, value)
        elif self.current_consensus == ConsensusType.PBFT:
            result = await self._pbft_propose(proposal_id, value)
        elif self.current_consensus == ConsensusType.GOSSIP:
            result = await self._gossip_propose(proposal_id, value)
        else:
            result = True
        
        if result:
            self.stats["successful_proposals"] += 1
        
        return result
    
    async def _raft_propose(self, proposal_id: str, value: Any) -> bool:
        """Raft提议"""
        await asyncio.sleep(0.01)
        return True
    
    async def _pbft_propose(self, proposal_id: str, value: Any) -> bool:
        """PBFT提议"""
        await asyncio.sleep(0.02)
        return True
    
    async def _gossip_propose(self, proposal_id: str, value: Any) -> bool:
        """Gossip提议"""
        await asyncio.sleep(0.005)
        return True
    
    def get_consensus_type(self) -> ConsensusType:
        return self.current_consensus


class TrustManager:
    """信任管理器"""
    
    def __init__(self, trust_threshold: float = -10.0):
        self.trust_threshold = trust_threshold
        self.trust_records: Dict[str, TrustRecord] = {}
        self.blacklist: Set[str] = set()
        self.quarantine_zone: Set[str] = set()
        self.quarantine_duration: int = 7 * 24 * 3600
        self._lock = threading.Lock()
        self.stats = {
            "total_interactions": 0,
            "suspicious_detected": 0,
            "quarantined": 0,
            "recovered": 0,
            "blacklisted": 0,
        }
    
    def record_interaction(
        self,
        agent_id: str,
        other_agent_id: str,
        is_consistent: bool
    ):
        """记录交互"""
        self.stats["total_interactions"] += 1
        
        with self._lock:
            if other_agent_id not in self.trust_records:
                self.trust_records[other_agent_id] = TrustRecord(
                    agent_id=other_agent_id,
                    trust_score=0.0,
                    level=TrustLevel.NORMAL,
                    interactions=0,
                    consistent_count=0,
                    inconsistent_count=0,
                    last_updated=datetime.now()
                )
            
            record = self.trust_records[other_agent_id]
            record.interactions += 1
            
            if is_consistent:
                record.consistent_count += 1
                record.trust_score += 1
            else:
                record.inconsistent_count += 1
                record.trust_score -= 1
            
            record.last_updated = datetime.now()
            
            self._update_trust_level(other_agent_id)
    
    def _update_trust_level(self, agent_id: str):
        """更新信任等级"""
        record = self.trust_records[agent_id]
        
        if record.trust_score <= self.trust_threshold:
            if record.level != TrustLevel.QUARANTINED:
                record.level = TrustLevel.QUARANTINED
                record.quarantine_start = datetime.now()
                self.quarantine_zone.add(agent_id)
                self.stats["quarantined"] += 1
                logger.warning(f"Agent {agent_id} moved to quarantine")
        elif record.trust_score <= self.trust_threshold / 2:
            record.level = TrustLevel.SUSPICIOUS
            self.stats["suspicious_detected"] += 1
        elif record.trust_score > 10:
            record.level = TrustLevel.TRUSTED
        else:
            record.level = TrustLevel.NORMAL
    
    def check_quarantine_recovery(self):
        """检查隔离恢复"""
        now = datetime.now()
        
        with self._lock:
            for agent_id in list(self.quarantine_zone):
                record = self.trust_records.get(agent_id)
                if not record or not record.quarantine_start:
                    continue
                
                elapsed = (now - record.quarantine_start).total_seconds()
                if elapsed >= self.quarantine_duration:
                    if record.trust_score > self.trust_threshold:
                        record.level = TrustLevel.NORMAL
                        record.quarantine_start = None
                        self.quarantine_zone.discard(agent_id)
                        self.stats["recovered"] += 1
                        logger.info(f"Agent {agent_id} recovered from quarantine")
    
    def is_trusted(self, agent_id: str) -> bool:
        """是否可信"""
        with self._lock:
            if agent_id in self.blacklist:
                return False
            
            record = self.trust_records.get(agent_id)
            if not record:
                return True
            
            return record.level not in [TrustLevel.QUARANTINED, TrustLevel.BLACKLISTED]
    
    def get_trust_score(self, agent_id: str) -> float:
        """获取信任分数"""
        with self._lock:
            record = self.trust_records.get(agent_id)
            return record.trust_score if record else 0.0


class QuarantineZone:
    """隔离区"""
    
    def __init__(self, review_callback: Callable = None):
        self.quarantined_agents: Dict[str, Dict[str, Any]] = {}
        self.review_callback = review_callback
        self.review_queue: deque = deque(maxlen=1000)
        self.stats = {
            "total_quarantined": 0,
            "total_released": 0,
            "total_blacklisted": 0,
            "reviews_pending": 0,
        }
    
    def add_agent(
        self,
        agent_id: str,
        reason: str,
        original_state: Dict[str, Any] = None
    ):
        """添加到隔离区"""
        self.quarantined_agents[agent_id] = {
            "reason": reason,
            "original_state": original_state,
            "quarantined_at": datetime.now(),
            "tasks_completed": 0,
            "tasks_reviewed": 0,
        }
        self.stats["total_quarantined"] += 1
        
        logger.warning(f"Agent {agent_id} added to quarantine: {reason}")
    
    def remove_agent(self, agent_id: str, release: bool = True):
        """从隔离区移除"""
        if agent_id in self.quarantined_agents:
            del self.quarantined_agents[agent_id]
            
            if release:
                self.stats["total_released"] += 1
            else:
                self.stats["total_blacklisted"] += 1
    
    async def process_task(
        self,
        agent_id: str,
        task: Any,
        task_result: Any
    ) -> Tuple[bool, Any]:
        """处理隔离区智能体的任务"""
        if agent_id not in self.quarantined_agents:
            return True, task_result
        
        self.quarantined_agents[agent_id]["tasks_completed"] += 1
        
        if self.review_callback:
            review_result = await self.review_callback(agent_id, task, task_result)
            self.quarantined_agents[agent_id]["tasks_reviewed"] += 1
            return review_result
        
        return True, task_result


class EvolutionIncubator:
    """涌现智能孵化器"""
    
    def __init__(self, population_size: int = 20):
        self.population_size = population_size
        self.mutation_pool: List[MutationCandidate] = []
        self.evolution_records: List[EvolutionRecord] = []
        self.generation = 0
        self.evaluation_tasks: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        self.stats = {
            "total_mutations": 0,
            "total_evaluations": 0,
            "total_replacements": 0,
            "generations": 0,
        }
    
    def create_mutation(
        self,
        source_agent_id: str,
        mutation_type: MutationType,
        params: Dict[str, Any] = None
    ) -> MutationCandidate:
        """创建变异候选"""
        candidate_id = f"mut_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        candidate = MutationCandidate(
            candidate_id=candidate_id,
            source_agent_id=source_agent_id,
            mutation_type=mutation_type,
            mutation_params=params or {},
            fitness_score=0.0,
            created_at=datetime.now()
        )
        
        with self._lock:
            self.mutation_pool.append(candidate)
            self.stats["total_mutations"] += 1
        
        return candidate
    
    def mutate_weights(
        self,
        weights: Dict[str, Any],
        noise_scale: float = 0.01
    ) -> Dict[str, Any]:
        """权重变异"""
        mutated = copy.deepcopy(weights)
        
        for key in mutated:
            if isinstance(mutated[key], list):
                for i in range(len(mutated[key])):
                    if random.random() < 0.1:
                        mutated[key][i] += random.gauss(0, noise_scale)
        
        return mutated
    
    def mutate_structure(
        self,
        architecture: Dict[str, Any]
    ) -> Dict[str, Any]:
        """结构变异"""
        mutated = copy.deepcopy(architecture)
        
        if random.random() < 0.3:
            layers = mutated.get("layers", [])
            if layers:
                insert_pos = random.randint(0, len(layers))
                new_layer = {
                    "type": "dense",
                    "units": random.choice([64, 128, 256]),
                    "activation": random.choice(["relu", "tanh", "sigmoid"])
                }
                layers.insert(insert_pos, new_layer)
        
        return mutated
    
    async def evaluate_candidate(
        self,
        candidate: MutationCandidate,
        test_tasks: List[Dict[str, Any]]
    ) -> float:
        """评估变异候选"""
        self.stats["total_evaluations"] += 1
        
        total_score = 0.0
        for task in test_tasks:
            score = random.uniform(0.5, 1.0)
            total_score += score
        
        avg_score = total_score / max(len(test_tasks), 1)
        candidate.fitness_score = avg_score
        candidate.evaluated = True
        
        return avg_score
    
    async def run_evolution_cycle(
        self,
        population: List[Any],
        test_tasks: List[Dict[str, Any]]
    ) -> EvolutionRecord:
        """运行进化周期"""
        self.generation += 1
        
        fitness_scores = []
        for agent in population:
            score = random.uniform(0.5, 1.0)
            fitness_scores.append((agent.agent_id if hasattr(agent, 'agent_id') else str(agent), score))
        
        fitness_scores.sort(key=lambda x: x[1], reverse=True)
        
        avg_fitness = sum(s for _, s in fitness_scores) / max(len(fitness_scores), 1)
        best_fitness = fitness_scores[0][1] if fitness_scores else 0.0
        
        bottom_10_percent = max(1, len(population) // 10)
        top_mutations = sorted(self.mutation_pool, key=lambda x: x.fitness_score, reverse=True)[:bottom_10_percent]
        
        record = EvolutionRecord(
            generation=self.generation,
            population_size=len(population),
            avg_fitness=avg_fitness,
            best_fitness=best_fitness,
            mutations_applied=len(top_mutations),
            replacements=min(len(top_mutations), bottom_10_percent),
            timestamp=datetime.now()
        )
        
        with self._lock:
            self.evolution_records.append(record)
            self.stats["generations"] += 1
            self.stats["total_replacements"] += record.replacements
        
        return record
    
    def get_best_mutations(self, count: int = 5) -> List[MutationCandidate]:
        """获取最佳变异"""
        with self._lock:
            sorted_pool = sorted(
                [m for m in self.mutation_pool if m.evaluated],
                key=lambda x: x.fitness_score,
                reverse=True
            )
            return sorted_pool[:count]


class SwarmEnhancementSystem:
    """蜂群强化系统主控"""
    
    def __init__(self, node_id: str = "default"):
        self.node_id = node_id
        self.adaptive_consensus = AdaptiveConsensus(node_id)
        self.trust_manager = TrustManager()
        self.quarantine_zone = QuarantineZone()
        self.evolution_incubator = EvolutionIncubator()
        
        self._running = False
    
    async def start(self):
        """启动系统"""
        self._running = True
        
        asyncio.create_task(self._periodic_trust_check())
    
    def stop(self):
        """停止系统"""
        self._running = False
    
    async def _periodic_trust_check(self):
        """定期信任检查"""
        while self._running:
            self.trust_manager.check_quarantine_recovery()
            await asyncio.sleep(3600)
    
    def record_interaction(
        self,
        agent_id: str,
        other_agent_id: str,
        is_consistent: bool
    ):
        """记录交互"""
        self.trust_manager.record_interaction(agent_id, other_agent_id, is_consistent)
    
    async def propose_consensus(self, value: Any) -> bool:
        """提议共识"""
        return await self.adaptive_consensus.propose(value)
    
    def create_mutation(
        self,
        source_agent_id: str,
        mutation_type: MutationType
    ) -> MutationCandidate:
        """创建变异"""
        return self.evolution_incubator.create_mutation(source_agent_id, mutation_type)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "consensus": {
                "type": self.adaptive_consensus.current_consensus.value,
                "stats": self.adaptive_consensus.stats,
            },
            "trust_manager": self.trust_manager.stats,
            "quarantine_zone": self.quarantine_zone.stats,
            "evolution_incubator": self.evolution_incubator.stats,
        }
