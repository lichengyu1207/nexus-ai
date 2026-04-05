"""
进化机制模块
Evolution Mechanism Module

实现智能体繁殖、变异和自然选择机制
"""

import os
import json
import time
import logging
import threading
import copy
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import deque, defaultdict
import random

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


class MutationType(Enum):
    WEIGHT_PERTURBATION = "weight_perturbation"
    LAYER_ADDITION = "layer_addition"
    LAYER_REMOVAL = "layer_removal"
    ACTIVATION_CHANGE = "activation_change"
    LEARNING_RATE_CHANGE = "learning_rate_change"
    ARCHITECTURE_CHANGE = "architecture_change"


@dataclass
class AgentGenome:
    genome_id: str
    agent_id: str
    parent_ids: List[str]
    generation: int
    architecture: Dict
    weights_hash: str
    fitness_score: float = 0.0
    mutation_history: List[Dict] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict:
        return {
            "genome_id": self.genome_id,
            "agent_id": self.agent_id,
            "parent_ids": self.parent_ids,
            "generation": self.generation,
            "architecture": self.architecture,
            "weights_hash": self.weights_hash,
            "fitness_score": self.fitness_score,
            "mutation_history": self.mutation_history,
            "created_at": self.created_at
        }


@dataclass
class ReproductionRecord:
    reproduction_id: str
    parent_id: str
    offspring_id: str
    reproduction_type: str
    energy_transferred: float
    mutations: List[Dict]
    timestamp: float = field(default_factory=time.time)


class ReproductionModule:
    
    def __init__(
        self,
        blackboard,
        energy_threshold: float = 100.0,
        min_reproduction_energy: float = 50.0,
        max_offspring_per_parent: int = 3,
        mutation_rate: float = 0.1
    ):
        self.blackboard = blackboard
        self.energy_threshold = energy_threshold
        self.min_reproduction_energy = min_reproduction_energy
        self.max_offspring_per_parent = max_offspring_per_parent
        self.mutation_rate = mutation_rate
        
        self.genomes: Dict[str, AgentGenome] = {}
        self.reproduction_tree: Dict[str, List[str]] = defaultdict(list)
        self.reproduction_records: deque = deque(maxlen=10000)
        
        self.agent_energies: Dict[str, float] = {}
        self.offspring_counts: Dict[str, int] = defaultdict(int)
        
        self.stats = {
            "total_reproductions": 0,
            "asexual_reproductions": 0,
            "sexual_reproductions": 0,
            "failed_reproductions": 0
        }
    
    def register_agent(
        self,
        agent_id: str,
        model: nn.Module,
        parent_ids: Optional[List[str]] = None,
        generation: int = 0
    ) -> AgentGenome:
        genome_id = f"genome_{agent_id}_{int(time.time())}"
        
        architecture = self._extract_architecture(model)
        weights_hash = self._compute_weights_hash(model)
        
        genome = AgentGenome(
            genome_id=genome_id,
            agent_id=agent_id,
            parent_ids=parent_ids or [],
            generation=generation,
            architecture=architecture,
            weights_hash=weights_hash
        )
        
        self.genomes[agent_id] = genome
        self.agent_energies[agent_id] = self.min_reproduction_energy
        
        if parent_ids:
            for parent_id in parent_ids:
                self.reproduction_tree[parent_id].append(agent_id)
        
        logger.info(f"Registered agent {agent_id} with genome {genome_id}")
        
        return genome
    
    def _extract_architecture(self, model: nn.Module) -> Dict:
        architecture = {
            "layers": [],
            "total_params": sum(p.numel() for p in model.parameters())
        }
        
        for name, module in model.named_modules():
            if isinstance(module, nn.Linear):
                architecture["layers"].append({
                    "type": "linear",
                    "in_features": module.in_features,
                    "out_features": module.out_features
                })
            elif isinstance(module, nn.ReLU):
                architecture["layers"].append({"type": "relu"})
            elif isinstance(module, nn.Tanh):
                architecture["layers"].append({"type": "tanh"})
            elif isinstance(module, nn.Sigmoid):
                architecture["layers"].append({"type": "sigmoid"})
        
        return architecture
    
    def _compute_weights_hash(self, model: nn.Module) -> str:
        weights_bytes = b""
        for param in model.parameters():
            weights_bytes += param.data.cpu().numpy().tobytes()
        
        return hashlib.md5(weights_bytes).hexdigest()[:16]
    
    def can_reproduce(self, agent_id: str) -> bool:
        energy = self.agent_energies.get(agent_id, 0)
        offspring_count = self.offspring_counts.get(agent_id, 0)
        
        return (
            energy >= self.energy_threshold and
            offspring_count < self.max_offspring_per_parent
        )
    
    def update_energy(self, agent_id: str, delta: float):
        if agent_id in self.agent_energies:
            self.agent_energies[agent_id] = max(0, self.agent_energies[agent_id] + delta)
    
    def set_energy(self, agent_id: str, energy: float):
        self.agent_energies[agent_id] = max(0, energy)
    
    def reproduce_asexual(
        self,
        parent_id: str,
        parent_model: nn.Module,
        offspring_id: str
    ) -> Tuple[Optional[nn.Module], Optional[AgentGenome]]:
        if not self.can_reproduce(parent_id):
            logger.warning(f"Agent {parent_id} cannot reproduce")
            return None, None
        
        parent_genome = self.genomes.get(parent_id)
        if not parent_genome:
            logger.warning(f"No genome found for agent {parent_id}")
            return None, None
        
        offspring_model = copy.deepcopy(parent_model)
        mutations = self._apply_mutations(offspring_model)
        
        offspring_genome = AgentGenome(
            genome_id=f"genome_{offspring_id}_{int(time.time())}",
            agent_id=offspring_id,
            parent_ids=[parent_id],
            generation=parent_genome.generation + 1,
            architecture=self._extract_architecture(offspring_model),
            weights_hash=self._compute_weights_hash(offspring_model),
            mutation_history=mutations
        )
        
        self.genomes[offspring_id] = offspring_genome
        self.reproduction_tree[parent_id].append(offspring_id)
        
        parent_energy = self.agent_energies[parent_id]
        energy_transferred = parent_energy * 0.5
        self.agent_energies[parent_id] = parent_energy - energy_transferred
        self.agent_energies[offspring_id] = energy_transferred
        
        self.offspring_counts[parent_id] += 1
        
        record = ReproductionRecord(
            reproduction_id=f"repro_{int(time.time())}_{parent_id}",
            parent_id=parent_id,
            offspring_id=offspring_id,
            reproduction_type="asexual",
            energy_transferred=energy_transferred,
            mutations=mutations
        )
        self.reproduction_records.append(record)
        
        self.stats["total_reproductions"] += 1
        self.stats["asexual_reproductions"] += 1
        
        self.blackboard.write(
            f"reproduction:{offspring_id}",
            {
                "parent_id": parent_id,
                "offspring_id": offspring_id,
                "type": "asexual",
                "mutations": mutations
            })
        
        logger.info(f"Asexual reproduction: {parent_id} -> {offspring_id}")
        
        return offspring_model, offspring_genome
    
    def reproduce_sexual(
        self,
        parent1_id: str,
        parent1_model: nn.Module,
        parent2_id: str,
        parent2_model: nn.Module,
        offspring_id: str
    ) -> Tuple[Optional[nn.Module], Optional[AgentGenome]]:
        if not self.can_reproduce(parent1_id) or not self.can_reproduce(parent2_id):
            logger.warning(f"Parents cannot reproduce")
            return None, None
        
        parent1_genome = self.genomes.get(parent1_id)
        parent2_genome = self.genomes.get(parent2_id)
        
        if not parent1_genome or not parent2_genome:
            logger.warning("Missing genome for parents")
            return None, None
        
        offspring_model = self._crossover_models(parent1_model, parent2_model)
        mutations = self._apply_mutations(offspring_model)
        
        offspring_genome = AgentGenome(
            genome_id=f"genome_{offspring_id}_{int(time.time())}",
            agent_id=offspring_id,
            parent_ids=[parent1_id, parent2_id],
            generation=max(parent1_genome.generation, parent2_genome.generation) + 1,
            architecture=self._extract_architecture(offspring_model),
            weights_hash=self._compute_weights_hash(offspring_model),
            mutation_history=mutations
        )
        
        self.genomes[offspring_id] = offspring_genome
        self.reproduction_tree[parent1_id].append(offspring_id)
        self.reproduction_tree[parent2_id].append(offspring_id)
        
        parent1_energy = self.agent_energies[parent1_id]
        parent2_energy = self.agent_energies[parent2_id]
        total_energy = parent1_energy + parent2_energy
        
        energy_transferred = total_energy * 0.3
        self.agent_energies[parent1_id] = parent1_energy * 0.7
        self.agent_energies[parent2_id] = parent2_energy * 0.7
        self.agent_energies[offspring_id] = energy_transferred
        
        self.offspring_counts[parent1_id] += 1
        self.offspring_counts[parent2_id] += 1
        
        record = ReproductionRecord(
            reproduction_id=f"repro_{int(time.time())}_{parent1_id}_{parent2_id}",
            parent_id=f"{parent1_id},{parent2_id}",
            offspring_id=offspring_id,
            reproduction_type="sexual",
            energy_transferred=energy_transferred,
            mutations=mutations
        )
        self.reproduction_records.append(record)
        
        self.stats["total_reproductions"] += 1
        self.stats["sexual_reproductions"] += 1
        
        self.blackboard.write(
            f"reproduction:{offspring_id}",
            {
                "parent_ids": [parent1_id, parent2_id],
                "offspring_id": offspring_id,
                "type": "sexual",
                "mutations": mutations
            })
        
        logger.info(f"Sexual reproduction: {parent1_id} + {parent2_id} -> {offspring_id}")
        
        return offspring_model, offspring_genome
    
    def _crossover_models(
        self,
        parent1: nn.Module,
        parent2: nn.Module
    ) -> nn.Module:
        offspring = copy.deepcopy(parent1)
        
        p1_params = list(parent1.named_parameters())
        p2_params = dict(parent2.named_parameters())
        
        for name, param in offspring.named_parameters():
            if name in p2_params:
                if random.random() < 0.5:
                    param.data.copy_(p2_params[name].data)
        
        return offspring
    
    def _apply_mutations(self, model: nn.Module) -> List[Dict]:
        mutations = []
        
        for name, param in model.named_parameters():
            if random.random() < self.mutation_rate:
                mutation_type = random.choice([
                    MutationType.WEIGHT_PERTURBATION.value
                ])
                
                if mutation_type == MutationType.WEIGHT_PERTURBATION.value:
                    noise = torch.randn_like(param.data) * 0.1
                    param.data.add_(noise)
                    
                    mutations.append({
                        "type": mutation_type,
                        "parameter": name,
                        "magnitude": 0.1
                    })
        
        return mutations
    
    def get_genome(self, agent_id: str) -> Optional[AgentGenome]:
        return self.genomes.get(agent_id)
    
    def get_ancestry(self, agent_id: str, generations: int = 5) -> List[str]:
        ancestry = []
        current = agent_id
        
        for _ in range(generations):
            genome = self.genomes.get(current)
            if not genome or not genome.parent_ids:
                break
            
            ancestry.append(current)
            current = genome.parent_ids[0]
        
        return ancestry
    
    def get_descendants(self, agent_id: str) -> List[str]:
        descendants = []
        queue = [agent_id]
        
        while queue:
            current = queue.pop(0)
            children = self.reproduction_tree.get(current, [])
            descendants.extend(children)
            queue.extend(children)
        
        return descendants
    
    def get_stats(self) -> Dict:
        return {
            "total_agents": len(self.genomes),
            "total_energies": sum(self.agent_energies.values()),
            "avg_energy": np.mean(list(self.agent_energies.values())) if self.agent_energies else 0,
            "reproduction_stats": self.stats.copy()
        }


class MutationSelection:
    
    def __init__(
        self,
        reproduction_module: ReproductionModule,
        blackboard,
        selection_pressure: float = 0.05,
        elite_ratio: float = 0.1,
        energy_decay_rate: float = 0.01,
        min_energy: float = 0.0
    ):
        self.reproduction_module = reproduction_module
        self.blackboard = blackboard
        self.selection_pressure = selection_pressure
        self.elite_ratio = elite_ratio
        self.energy_decay_rate = energy_decay_rate
        self.min_energy = min_energy
        
        self.fitness_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.elite_agents: Set[str] = set()
        self.eliminated_agents: List[str] = []
        
        self.stats = {
            "selections_performed": 0,
            "agents_eliminated": 0,
            "elite_count": 0
        }
    
    def record_fitness(self, agent_id: str, fitness: float):
        self.fitness_history[agent_id].append({
            "fitness": fitness,
            "timestamp": time.time()
        })
        
        genome = self.reproduction_module.genomes.get(agent_id)
        if genome:
            genome.fitness_score = fitness
    
    def apply_energy_decay(self):
        for agent_id in list(self.reproduction_module.agent_energies.keys()):
            current_energy = self.reproduction_module.agent_energies[agent_id]
            new_energy = current_energy * (1 - self.energy_decay_rate)
            self.reproduction_module.agent_energies[agent_id] = new_energy
    
    def run_selection(self, agent_ids: List[str]) -> Tuple[List[str], List[str]]:
        self.stats["selections_performed"] += 1
        
        fitness_scores = []
        for agent_id in agent_ids:
            genome = self.reproduction_module.genomes.get(agent_id)
            if genome:
                fitness_scores.append((agent_id, genome.fitness_score))
            else:
                fitness_scores.append((agent_id, 0))
        
        fitness_scores.sort(key=lambda x: x[1], reverse=True)
        
        elite_count = max(1, int(len(agent_ids) * self.elite_ratio))
        self.elite_agents = set(agent_id for agent_id, _ in fitness_scores[:elite_count])
        self.stats["elite_count"] = len(self.elite_agents)
        
        eliminate_count = max(0, int(len(agent_ids) * self.selection_pressure))
        eliminated = [agent_id for agent_id, _ in fitness_scores[-eliminate_count:]]
        
        for agent_id in eliminated:
            if agent_id not in self.elite_agents:
                self.eliminated_agents.append(agent_id)
                self.stats["agents_eliminated"] += 1
                
                if agent_id in self.reproduction_module.agent_energies:
                    del self.reproduction_module.agent_energies[agent_id]
                if agent_id in self.reproduction_module.genomes:
                    del self.reproduction_module.genomes[agent_id]
        
        if eliminate_count > 0:
            survivors = [agent_id for agent_id, _ in fitness_scores[:-eliminate_count]]
        else:
            survivors = agent_ids
        
        self.blackboard.write(
            "selection:result",
            {
                "survivors": survivors,
                "eliminated": eliminated,
                "elite": list(self.elite_agents),
                "timestamp": time.time()
            })
        
        logger.info(f"Selection completed: {len(survivors)} survivors, {len(eliminated)} eliminated")
        
        return survivors, eliminated
    
    def is_elite(self, agent_id: str) -> bool:
        return agent_id in self.elite_agents
    
    def get_avg_fitness(self, agent_id: str) -> float:
        history = list(self.fitness_history.get(agent_id, []))
        if not history:
            return 0.0
        return np.mean([h["fitness"] for h in history])
    
    def get_population_stats(self) -> Dict:
        all_fitness = []
        for agent_id, genome in self.reproduction_module.genomes.items():
            all_fitness.append(genome.fitness_score)
        
        return {
            "population_size": len(self.reproduction_module.genomes),
            "avg_fitness": np.mean(all_fitness) if all_fitness else 0,
            "max_fitness": max(all_fitness) if all_fitness else 0,
            "min_fitness": min(all_fitness) if all_fitness else 0,
            "elite_count": len(self.elite_agents),
            "selection_stats": self.stats.copy()
        }


class EnvironmentPerception:
    
    def __init__(
        self,
        blackboard,
        perception_interval: float = 1.0
    ):
        self.blackboard = blackboard
        self.perception_interval = perception_interval
        
        self.environment_state: Dict = {}
        self.perception_history: deque = deque(maxlen=1000)
        
        self._running = False
        self._perception_thread = None
    
    def start(self):
        self._running = True
        self._perception_thread = threading.Thread(target=self._perception_loop, daemon=True)
        self._perception_thread.start()
        logger.info("Environment Perception started")
    
    def stop(self):
        self._running = False
        logger.info("Environment Perception stopped")
    
    def _perception_loop(self):
        while self._running:
            try:
                self._update_perception()
                time.sleep(self.perception_interval)
            except Exception as e:
                logger.error(f"Error in perception loop: {e}")
                time.sleep(1)
    
    def _update_perception(self):
        self.environment_state = {
            "qps": self._get_metric("qps", 0),
            "error_rate": self._get_metric("error_rate", 0),
            "latency": self._get_metric("latency", 0),
            "active_agents": self._get_metric("active_agents", 0),
            "task_queue_size": self._get_metric("task_queue_size", 0),
            "memory_usage": self._get_metric("memory_usage", 0),
            "cpu_usage": self._get_metric("cpu_usage", 0),
            "timestamp": time.time()
        }
        
        self.perception_history.append(self.environment_state.copy())
        
        self.blackboard.write(
            "environment:state",
            self.environment_state,
            ttl=60
        )
    
    def _get_metric(self, metric_name: str, default: float) -> float:
        value = self.blackboard.read(f"metric:{metric_name}")
        if value is not None:
            return float(value)
        return default
    
    def perceive(self) -> Dict:
        return self.environment_state.copy()
    
    def get_state_vector(self) -> np.ndarray:
        if not self.environment_state:
            return np.zeros(8)
        
        return np.array([
            self.environment_state.get("qps", 0),
            self.environment_state.get("error_rate", 0),
            self.environment_state.get("latency", 0),
            self.environment_state.get("active_agents", 0),
            self.environment_state.get("task_queue_size", 0),
            self.environment_state.get("memory_usage", 0),
            self.environment_state.get("cpu_usage", 0),
            1.0
        ])
    
    def detect_anomaly(self) -> Tuple[bool, Optional[str]]:
        if not self.environment_state:
            return False, None
        
        if self.environment_state.get("error_rate", 0) > 0.1:
            return True, "high_error_rate"
        
        if self.environment_state.get("latency", 0) > 1000:
            return True, "high_latency"
        
        if self.environment_state.get("task_queue_size", 0) > 100:
            return True, "task_backlog"
        
        return False, None
    
    def get_stats(self) -> Dict:
        return {
            "current_state": self.environment_state,
            "history_size": len(self.perception_history),
            "running": self._running
        }
