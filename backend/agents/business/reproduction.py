"""
业务智能体繁殖机制
Business Agent Reproduction

实现业务智能体的繁殖与变异
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


class ReproductionType(Enum):
    ASEXUAL = "asexual"
    SEXUAL = "sexual"
    CLONING = "cloning"
    MUTATION = "mutation"


class OffspringStatus(Enum):
    EMBRYO = "embryo"
    INCUBATING = "incubating"
    ACTIVE = "active"
    FAILED = "failed"
    TERMINATED = "terminated"


@dataclass
class ReproductionConfig:
    energy_threshold: float = 200.0
    min_tasks_completed: int = 10
    min_success_rate: float = 0.7
    energy_transfer_ratio: float = 0.5
    mutation_rate: float = 0.1
    mutation_strength: float = 0.2
    max_population: int = 100
    incubation_period: float = 60.0
    validation_required: bool = True
    
    def to_dict(self) -> Dict:
        return {
            "energy_threshold": self.energy_threshold,
            "min_tasks_completed": self.min_tasks_completed,
            "min_success_rate": self.min_success_rate,
            "energy_transfer_ratio": self.energy_transfer_ratio,
            "mutation_rate": self.mutation_rate,
            "mutation_strength": self.mutation_strength,
            "max_population": self.max_population,
            "incubation_period": self.incubation_period,
            "validation_required": self.validation_required
        }


@dataclass
class OffspringRecord:
    offspring_id: str
    parent_ids: List[str]
    reproduction_type: ReproductionType
    generation: int
    initial_energy: float
    gene_pool: Dict
    status: OffspringStatus
    created_at: float
    activated_at: Optional[float] = None
    terminated_at: Optional[float] = None
    validation_result: Optional[Dict] = None
    performance: Dict = field(default_factory=dict)
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "offspring_id": self.offspring_id,
            "parent_ids": self.parent_ids,
            "reproduction_type": self.reproduction_type.value,
            "generation": self.generation,
            "initial_energy": self.initial_energy,
            "gene_pool": self.gene_pool,
            "status": self.status.value,
            "created_at": self.created_at,
            "activated_at": self.activated_at,
            "terminated_at": self.terminated_at,
            "validation_result": self.validation_result,
            "performance": self.performance,
            "metadata": self.metadata
        }


class BusinessAgentReproduction:
    """
    业务智能体繁殖机制
    
    实现业务智能体的繁殖与变异：
    1. 繁殖条件：能量、任务完成数、成功率
    2. 繁殖过程：复制策略网络并变异
    3. 变异方向引导：向业务目标变异
    4. 繁殖记录：族谱追溯
    5. 防止过度繁殖：种群上限
    """
    
    def __init__(
        self,
        memory_agent: Optional[Any] = None,
        blackboard: Optional[Any] = None,
        config: Optional[ReproductionConfig] = None,
    ):
        self.memory_agent = memory_agent
        self.blackboard = blackboard
        self.config = config or ReproductionConfig()
        
        self.population: Dict[str, Any] = {}
        self.offspring_records: Dict[str, OffspringRecord] = {}
        self.family_tree: Dict[str, List[str]] = defaultdict(list)
        self.generation_counts: Dict[int, int] = defaultdict(int)
        
        self.incubation_queue: asyncio.Queue = asyncio.Queue()
        
        self._lock = threading.RLock()
        self._running = False
        self._incubation_task: Optional[asyncio.Task] = None
        
        self.stats = {
            "total_reproductions": 0,
            "asexual_reproductions": 0,
            "sexual_reproductions": 0,
            "successful_offspring": 0,
            "failed_offspring": 0,
            "terminated_offspring": 0,
            "avg_offspring_performance": 0.0,
            "population_size": 0,
        }
    
    async def start(self):
        self._running = True
        self._incubation_task = asyncio.create_task(self._incubation_loop())
        logger.info("Business agent reproduction started")
    
    async def stop(self):
        self._running = False
        if self._incubation_task:
            self._incubation_task.cancel()
            try:
                await self._incubation_task
            except asyncio.CancelledError:
                pass
        logger.info("Business agent reproduction stopped")
    
    async def _incubation_loop(self):
        while self._running:
            try:
                offspring_id = await asyncio.wait_for(
                    self.incubation_queue.get(),
                    timeout=10.0
                )
                await self._process_incubation(offspring_id)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in incubation loop: {e}")
    
    async def _process_incubation(self, offspring_id: str):
        if offspring_id not in self.offspring_records:
            return
        
        record = self.offspring_records[offspring_id]
        record.status = OffspringStatus.INCUBATING
        
        await asyncio.sleep(self.config.incubation_period)
        
        if self.config.validation_required:
            validation_result = await self._validate_offspring(offspring_id)
            record.validation_result = validation_result
            
            if not validation_result.get("passed", False):
                record.status = OffspringStatus.FAILED
                self.stats["failed_offspring"] += 1
                return
        
        record.status = OffspringStatus.ACTIVE
        record.activated_at = time.time()
        
        self.stats["successful_offspring"] += 1
        self.stats["population_size"] = len([
            r for r in self.offspring_records.values()
            if r.status == OffspringStatus.ACTIVE
        ])
        
        logger.info(f"Offspring activated: {offspring_id}")
    
    def can_reproduce(self, agent: Any) -> Tuple[bool, str]:
        if agent.energy < self.config.energy_threshold:
            return False, f"Insufficient energy: {agent.energy} < {self.config.energy_threshold}"
        
        if agent.stats.get("tasks_completed", 0) < self.config.min_tasks_completed:
            return False, f"Insufficient tasks: {agent.stats.get('tasks_completed', 0)} < {self.config.min_tasks_completed}"
        
        if agent.stats.get("tasks_success_rate", 0) < self.config.min_success_rate:
            return False, f"Success rate too low: {agent.stats.get('tasks_success_rate', 0)} < {self.config.min_success_rate}"
        
        with self._lock:
            active_count = sum(
                1 for r in self.offspring_records.values()
                if r.status == OffspringStatus.ACTIVE
            )
            if active_count >= self.config.max_population:
                return False, f"Population limit reached: {active_count} >= {self.config.max_population}"
        
        return True, "Eligible for reproduction"
    
    async def reproduce_asexual(
        self,
        parent: Any,
        offspring_id: Optional[str] = None,
    ) -> Optional[OffspringRecord]:
        can_repro, reason = self.can_reproduce(parent)
        if not can_repro:
            logger.warning(f"Asexual reproduction rejected: {reason}")
            return None
        
        if offspring_id is None:
            offspring_id = f"{parent.species}_{uuid.uuid4().hex[:8]}"
        
        energy_transfer = parent.energy * self.config.energy_transfer_ratio
        parent.energy -= energy_transfer
        
        mutated_gene_pool = self._mutate_gene_pool(parent.gene_pool)
        
        generation = getattr(parent, 'generation', 0) + 1
        
        record = OffspringRecord(
            offspring_id=offspring_id,
            parent_ids=[parent.agent_id],
            reproduction_type=ReproductionType.ASEXUAL,
            generation=generation,
            initial_energy=energy_transfer,
            gene_pool=mutated_gene_pool,
            status=OffspringStatus.EMBRYO,
            created_at=time.time(),
        )
        
        with self._lock:
            self.offspring_records[offspring_id] = record
            self.family_tree[parent.agent_id].append(offspring_id)
            self.generation_counts[generation] += 1
            
            self.stats["total_reproductions"] += 1
            self.stats["asexual_reproductions"] += 1
        
        await self.incubation_queue.put(offspring_id)
        
        if self.memory_agent:
            await self._store_reproduction_record(record)
        
        logger.info(f"Asexual reproduction: {parent.agent_id} -> {offspring_id}")
        
        return record
    
    async def reproduce_sexual(
        self,
        parent1: Any,
        parent2: Any,
        offspring_id: Optional[str] = None,
    ) -> Optional[OffspringRecord]:
        can_repro1, reason1 = self.can_reproduce(parent1)
        can_repro2, reason2 = self.can_reproduce(parent2)
        
        if not can_repro1 or not can_repro2:
            logger.warning(f"Sexual reproduction rejected: {reason1}, {reason2}")
            return None
        
        if offspring_id is None:
            offspring_id = f"{parent1.species}_{uuid.uuid4().hex[:8]}"
        
        energy_transfer1 = parent1.energy * self.config.energy_transfer_ratio * 0.5
        energy_transfer2 = parent2.energy * self.config.energy_transfer_ratio * 0.5
        total_energy = energy_transfer1 + energy_transfer2
        
        parent1.energy -= energy_transfer1
        parent2.energy -= energy_transfer2
        
        combined_gene_pool = self._crossover_gene_pools(
            parent1.gene_pool, parent2.gene_pool
        )
        mutated_gene_pool = self._mutate_gene_pool(combined_gene_pool)
        
        generation = max(
            getattr(parent1, 'generation', 0),
            getattr(parent2, 'generation', 0)
        ) + 1
        
        record = OffspringRecord(
            offspring_id=offspring_id,
            parent_ids=[parent1.agent_id, parent2.agent_id],
            reproduction_type=ReproductionType.SEXUAL,
            generation=generation,
            initial_energy=total_energy,
            gene_pool=mutated_gene_pool,
            status=OffspringStatus.EMBRYO,
            created_at=time.time(),
        )
        
        with self._lock:
            self.offspring_records[offspring_id] = record
            self.family_tree[parent1.agent_id].append(offspring_id)
            self.family_tree[parent2.agent_id].append(offspring_id)
            self.generation_counts[generation] += 1
            
            self.stats["total_reproductions"] += 1
            self.stats["sexual_reproductions"] += 1
        
        await self.incubation_queue.put(offspring_id)
        
        if self.memory_agent:
            await self._store_reproduction_record(record)
        
        logger.info(f"Sexual reproduction: {parent1.agent_id} + {parent2.agent_id} -> {offspring_id}")
        
        return record
    
    def _mutate_gene_pool(self, gene_pool: Any) -> Dict:
        if hasattr(gene_pool, 'to_dict'):
            genes = gene_pool.to_dict()
        elif hasattr(gene_pool, 'genes'):
            genes = {name: {"value": gene.value} for name, gene in gene_pool.genes.items()}
        else:
            genes = dict(gene_pool) if gene_pool else {}
        
        mutated = {}
        for name, gene_data in genes.items():
            if isinstance(gene_data, dict):
                value = gene_data.get("value", 0)
            else:
                value = gene_data
            
            if random.random() < self.config.mutation_rate:
                if isinstance(value, (int, float)):
                    mutation = random.uniform(
                        -self.config.mutation_strength,
                        self.config.mutation_strength
                    ) * abs(value) if value != 0 else self.config.mutation_strength
                    value = value + mutation
                    if isinstance(gene_data.get("value"), int):
                        value = int(round(value))
            
            mutated[name] = {"value": value}
        
        return mutated
    
    def _crossover_gene_pools(self, pool1: Any, pool2: Any) -> Dict:
        if hasattr(pool1, 'to_dict'):
            genes1 = pool1.to_dict()
        else:
            genes1 = dict(pool1) if pool1 else {}
        
        if hasattr(pool2, 'to_dict'):
            genes2 = pool2.to_dict()
        else:
            genes2 = dict(pool2) if pool2 else {}
        
        combined = {}
        all_keys = set(genes1.keys()) | set(genes2.keys())
        
        for key in all_keys:
            if key in genes1 and key in genes2:
                if random.random() < 0.5:
                    combined[key] = genes1[key]
                else:
                    combined[key] = genes2[key]
            elif key in genes1:
                combined[key] = genes1[key]
            else:
                combined[key] = genes2[key]
        
        return combined
    
    async def _validate_offspring(self, offspring_id: str) -> Dict:
        record = self.offspring_records.get(offspring_id)
        if not record:
            return {"passed": False, "reason": "not_found"}
        
        gene_pool = record.gene_pool
        
        critical_genes = ["learning_rate", "cooperation_tendency"]
        for gene_name in critical_genes:
            if gene_name in gene_pool:
                value = gene_pool[gene_name].get("value", 0)
                if value <= 0:
                    return {"passed": False, "reason": f"invalid_{gene_name}"}
        
        return {"passed": True, "score": random.uniform(0.7, 1.0)}
    
    async def terminate_offspring(
        self,
        offspring_id: str,
        reason: str = "",
    ) -> bool:
        if offspring_id not in self.offspring_records:
            return False
        
        record = self.offspring_records[offspring_id]
        record.status = OffspringStatus.TERMINATED
        record.terminated_at = time.time()
        record.metadata["termination_reason"] = reason
        
        self.stats["terminated_offspring"] += 1
        self.stats["population_size"] = len([
            r for r in self.offspring_records.values()
            if r.status == OffspringStatus.ACTIVE
        ])
        
        logger.info(f"Offspring terminated: {offspring_id} - {reason}")
        
        return True
    
    async def _store_reproduction_record(self, record: OffspringRecord):
        if self.memory_agent:
            try:
                await self.memory_agent.store({
                    "type": "reproduction_record",
                    "record": record.to_dict(),
                    "timestamp": time.time()
                })
            except Exception as e:
                logger.error(f"Failed to store reproduction record: {e}")
    
    def get_offspring(self, offspring_id: str) -> Optional[OffspringRecord]:
        return self.offspring_records.get(offspring_id)
    
    def get_children(self, parent_id: str) -> List[OffspringRecord]:
        child_ids = self.family_tree.get(parent_id, [])
        return [
            self.offspring_records[cid]
            for cid in child_ids
            if cid in self.offspring_records
        ]
    
    def get_ancestors(self, offspring_id: str, generations: int = 3) -> List[str]:
        ancestors = []
        
        def find_ancestors(oid: str, depth: int):
            if depth > generations:
                return
            record = self.offspring_records.get(oid)
            if record:
                for parent_id in record.parent_ids:
                    ancestors.append(parent_id)
                    find_ancestors(parent_id, depth + 1)
        
        find_ancestors(offspring_id, 1)
        return ancestors
    
    def get_family_tree(self) -> Dict:
        return dict(self.family_tree)
    
    def get_population_stats(self) -> Dict:
        with self._lock:
            active = [r for r in self.offspring_records.values() if r.status == OffspringStatus.ACTIVE]
            
            return {
                **self.stats,
                "generation_distribution": dict(self.generation_counts),
                "active_offspring": len(active),
                "avg_generation": (
                    sum(r.generation for r in active) / len(active)
                    if active else 0
                ),
            }
    
    def get_stats(self) -> Dict:
        with self._lock:
            return {
                **self.stats,
                "total_offspring": len(self.offspring_records),
            }
