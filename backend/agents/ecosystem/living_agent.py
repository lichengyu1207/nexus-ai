"""
活体智能体基类
Living Agent Base Class

实现智能体的生命特征：能量、年龄、繁殖、变异、协作、竞争
"""

import os
import json
import time
import logging
import threading
import uuid
import copy
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import deque, defaultdict
import random
import math

import numpy as np

try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None
    nn = None

logger = logging.getLogger(__name__)


class AgentRole(Enum):
    ATTACK = "attack"
    DEFENSE = "defense"
    MEMORY = "memory"
    OBSERVER = "observer"


class AgentStatus(Enum):
    IDLE = "idle"
    WORKING = "working"
    RESTING = "resting"
    REPRODUCING = "reproducing"
    DYING = "dying"
    DEAD = "dead"


@dataclass
class Gene:
    gene_id: str
    name: str
    value: Any
    mutation_rate: float = 0.1
    mutation_range: Tuple[float, float] = (-0.5, 0.5)
    
    def mutate(self) -> 'Gene':
        if random.random() < self.mutation_rate:
            if isinstance(self.value, (int, float)):
                delta = random.uniform(*self.mutation_range)
                new_value = self.value + delta
            elif isinstance(self.value, list):
                new_value = [v + random.uniform(*self.mutation_range) for v in self.value]
            else:
                new_value = self.value
            
            return Gene(
                gene_id=f"gene_{uuid.uuid4().hex[:8]}",
                name=self.name,
                value=new_value,
                mutation_rate=self.mutation_rate,
                mutation_range=self.mutation_range
            )
        return self


@dataclass
class GenePool:
    genes: Dict[str, Gene] = field(default_factory=dict)
    
    def add_gene(self, gene: Gene):
        self.genes[gene.name] = gene
    
    def get_gene(self, name: str) -> Optional[Gene]:
        return self.genes.get(name)
    
    def mutate_all(self) -> 'GenePool':
        new_genes = {name: gene.mutate() for name, gene in self.genes.items()}
        return GenePool(genes=new_genes)
    
    def crossover(self, other: 'GenePool') -> 'GenePool':
        new_genes = {}
        for name in set(self.genes.keys()) | set(other.genes.keys()):
            if name in self.genes and name in other.genes:
                if random.random() < 0.5:
                    new_genes[name] = copy.deepcopy(self.genes[name])
                else:
                    new_genes[name] = copy.deepcopy(other.genes[name])
            elif name in self.genes:
                new_genes[name] = copy.deepcopy(self.genes[name])
            else:
                new_genes[name] = copy.deepcopy(other.genes[name])
        
        return GenePool(genes=new_genes)
    
    def to_dict(self) -> Dict:
        return {name: {"value": gene.value, "mutation_rate": gene.mutation_rate} 
                for name, gene in self.genes.items()}


class LivingAgent:
    
    def __init__(
        self,
        agent_id: str,
        role: AgentRole,
        species: str = "default",
        initial_energy: float = 100.0,
        max_age: int = 1000,
        reproduction_threshold: float = 200.0,
        energy_consumption_rate: float = 0.1,
        blackboard=None,
        communication=None
    ):
        self.agent_id = agent_id
        self.role = role
        self.species = species
        
        self.energy = initial_energy
        self.initial_energy = initial_energy
        self.max_energy = initial_energy * 3
        self.max_age = max_age
        self.reproduction_threshold = reproduction_threshold
        self.energy_consumption_rate = energy_consumption_rate
        
        self.age = 0
        self.generation = 0
        self.status = AgentStatus.IDLE
        
        self.gene_pool = GenePool()
        self._init_default_genes()
        
        self.parent_ids: List[str] = []
        self.children_ids: List[str] = []
        self.alliance_ids: Set[str] = set()
        
        self.experience_buffer: deque = deque(maxlen=10000)
        self.success_count = 0
        self.failure_count = 0
        
        self.blackboard = blackboard
        self.communication = communication
        
        self.created_at = time.time()
        self.last_action_at = time.time()
        
        self._lock = threading.RLock()
        self._running = False
        self._main_thread = None
        
        self.stats = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "energy_earned": 0,
            "energy_spent": 0,
            "reproductions": 0,
            "mutations": 0
        }
    
    def _init_default_genes(self):
        self.gene_pool.add_gene(Gene(
            gene_id="gene_learning_rate",
            name="learning_rate",
            value=0.001,
            mutation_rate=0.1,
            mutation_range=(-0.0005, 0.0005)
        ))
        
        self.gene_pool.add_gene(Gene(
            gene_id="gene_exploration",
            name="exploration_rate",
            value=0.3,
            mutation_rate=0.15,
            mutation_range=(-0.1, 0.1)
        ))
        
        self.gene_pool.add_gene(Gene(
            gene_id="gene_cooperation",
            name="cooperation_tendency",
            value=0.5,
            mutation_rate=0.1,
            mutation_range=(-0.2, 0.2)
        ))
        
        self.gene_pool.add_gene(Gene(
            gene_id="gene_aggression",
            name="aggression_level",
            value=0.5,
            mutation_rate=0.1,
            mutation_range=(-0.2, 0.2)
        ))
    
    def start(self):
        self._running = True
        self._main_thread = threading.Thread(target=self._life_loop, daemon=True)
        self._main_thread.start()
        logger.info(f"Living agent {self.agent_id} started")
    
    def stop(self):
        self._running = False
        logger.info(f"Living agent {self.agent_id} stopped")
    
    def _life_loop(self):
        while self._running:
            try:
                self.metabolize()
                
                if self.energy <= 0:
                    self.die()
                    break
                
                if self.age >= self.max_age:
                    self.die()
                    break
                
                if self.status != AgentStatus.DEAD:
                    self._live_cycle()
                
                self.age += 1
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in life loop for {self.agent_id}: {e}")
                time.sleep(1)
    
    def _live_cycle(self):
        pass
    
    def metabolize(self, environment: Optional[Dict] = None):
        with self._lock:
            base_consumption = self.energy_consumption_rate
            
            if self.status == AgentStatus.WORKING:
                base_consumption *= 2
            elif self.status == AgentStatus.RESTING:
                base_consumption *= 0.5
            
            self.energy -= base_consumption
            self.stats["energy_spent"] += base_consumption
            
            if environment:
                env_energy = environment.get("available_energy", 0)
                if env_energy > 0:
                    absorbed = min(env_energy * 0.1, self.max_energy - self.energy)
                    self.energy += absorbed
    
    def add_energy(self, amount: float):
        with self._lock:
            self.energy = min(self.max_energy, self.energy + amount)
            self.stats["energy_earned"] += amount
    
    def consume_energy(self, amount: float) -> bool:
        with self._lock:
            if self.energy >= amount:
                self.energy -= amount
                self.stats["energy_spent"] += amount
                return True
            return False
    
    def can_reproduce(self) -> bool:
        return (
            self.energy >= self.reproduction_threshold and
            self.status != AgentStatus.DYING and
            self.status != AgentStatus.DEAD
        )
    
    def reproduce_asexual(self, offspring_id: str) -> Optional['LivingAgent']:
        if not self.can_reproduce():
            return None
        
        with self._lock:
            self.status = AgentStatus.REPRODUCING
            
            energy_transfer = self.energy * 0.5
            self.energy -= energy_transfer
            
            offspring = self._create_offspring(offspring_id, energy_transfer)
            
            offspring.parent_ids = [self.agent_id]
            offspring.generation = self.generation + 1
            offspring.gene_pool = self.gene_pool.mutate_all()
            
            self.children_ids.append(offspring_id)
            self.stats["reproductions"] += 1
            
            self.status = AgentStatus.IDLE
            
            logger.info(f"Agent {self.agent_id} reproduced asexually -> {offspring_id}")
            
            return offspring
    
    def reproduce_sexual(
        self,
        partner: 'LivingAgent',
        offspring_id: str
    ) -> Optional['LivingAgent']:
        if not self.can_reproduce() or not partner.can_reproduce():
            return None
        
        with self._lock:
            self.status = AgentStatus.REPRODUCING
            partner.status = AgentStatus.REPRODUCING
            
            energy_transfer = self.energy * 0.3
            partner_energy_transfer = partner.energy * 0.3
            total_transfer = energy_transfer + partner_energy_transfer
            
            self.energy -= energy_transfer
            partner.energy -= partner_energy_transfer
            
            offspring = self._create_offspring(offspring_id, total_transfer)
            
            offspring.parent_ids = [self.agent_id, partner.agent_id]
            offspring.generation = max(self.generation, partner.generation) + 1
            offspring.gene_pool = self.gene_pool.crossover(partner.gene_pool).mutate_all()
            
            self.children_ids.append(offspring_id)
            partner.children_ids.append(offspring_id)
            
            self.stats["reproductions"] += 1
            partner.stats["reproductions"] += 1
            
            self.status = AgentStatus.IDLE
            partner.status = AgentStatus.IDLE
            
            logger.info(f"Agents {self.agent_id} + {partner.agent_id} reproduced sexually -> {offspring_id}")
            
            return offspring
    
    def _create_offspring(self, offspring_id: str, initial_energy: float) -> 'LivingAgent':
        return LivingAgent(
            agent_id=offspring_id,
            role=self.role,
            species=self.species,
            initial_energy=initial_energy,
            max_age=self.max_age,
            reproduction_threshold=self.reproduction_threshold,
            energy_consumption_rate=self.energy_consumption_rate,
            blackboard=self.blackboard,
            communication=self.communication
        )
    
    def mutate(self):
        with self._lock:
            self.gene_pool = self.gene_pool.mutate_all()
            self.stats["mutations"] += 1
            logger.debug(f"Agent {self.agent_id} mutated")
    
    def cooperate(self, other_agents: List['LivingAgent']) -> bool:
        cooperation_tendency = self.gene_pool.get_gene("cooperation_tendency")
        if cooperation_tendency and random.random() > cooperation_tendency.value:
            return False
        
        energy_cost = len(other_agents) * 0.5
        if not self.consume_energy(energy_cost):
            return False
        
        for agent in other_agents:
            self.alliance_ids.add(agent.agent_id)
        
        logger.debug(f"Agent {self.agent_id} formed alliance with {len(other_agents)} agents")
        
        return True
    
    def compete(self, other_agents: List['LivingAgent']) -> Tuple[bool, float]:
        aggression = self.gene_pool.get_gene("aggression_level")
        aggression_value = aggression.value if aggression else 0.5
        
        my_strength = self.energy * (1 + aggression_value)
        total_strength = my_strength + sum(a.energy for a in other_agents)
        
        win_probability = my_strength / total_strength if total_strength > 0 else 0.5
        
        won = random.random() < win_probability
        
        if won:
            reward = sum(a.energy * 0.1 for a in other_agents)
            self.add_energy(reward)
        else:
            penalty = self.energy * 0.1
            self.consume_energy(penalty)
        
        return won, win_probability
    
    def record_experience(self, experience: Dict):
        self.experience_buffer.append({
            **experience,
            "timestamp": time.time(),
            "energy": self.energy,
            "age": self.age
        })
    
    def die(self):
        with self._lock:
            self.status = AgentStatus.DEAD
            
            if self.blackboard:
                self.blackboard.write(
                    f"death:{self.agent_id}",
                    {
                        "agent_id": self.agent_id,
                        "role": self.role.value,
                        "species": self.species,
                        "generation": self.generation,
                        "age": self.age,
                        "final_energy": self.energy,
                        "stats": self.stats,
                        "timestamp": time.time()
                    },
                    ttl=86400,
                    notify=True
                )
            
            logger.info(f"Agent {self.agent_id} died at age {self.age}")
    
    def is_alive(self) -> bool:
        return self.status != AgentStatus.DEAD and self.energy > 0
    
    def get_state(self) -> Dict:
        with self._lock:
            return {
                "agent_id": self.agent_id,
                "role": self.role.value,
                "species": self.species,
                "energy": self.energy,
                "age": self.age,
                "generation": self.generation,
                "status": self.status.value,
                "parent_ids": self.parent_ids,
                "children_count": len(self.children_ids),
                "alliance_count": len(self.alliance_ids),
                "gene_pool": self.gene_pool.to_dict(),
                "stats": self.stats.copy(),
                "is_alive": self.is_alive()
            }
    
    def get_fitness(self) -> float:
        success_rate = (
            self.success_count / (self.success_count + self.failure_count)
            if (self.success_count + self.failure_count) > 0 else 0.5
        )
        
        energy_factor = self.energy / self.initial_energy
        age_factor = 1 - (self.age / self.max_age)
        reproduction_factor = min(1.0, len(self.children_ids) / 5)
        
        return (
            success_rate * 0.4 +
            energy_factor * 0.2 +
            age_factor * 0.2 +
            reproduction_factor * 0.2
        )
