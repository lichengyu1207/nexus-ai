"""
生态系统协调器
Ecosystem Coordinator

协调攻击、防御、记忆三大集群的交互与协同进化
"""

import os
import json
import time
import logging
import threading
import random
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from collections import deque, defaultdict
from dataclasses import dataclass, field
from enum import Enum
import numpy as np

from .living_agent import LivingAgent, AgentRole, AgentStatus
from .living_attack_agent import LivingAttackAgent
from .living_defense_agent import LivingDefenseAgent
from .living_memory_agent import LivingMemoryAgent

logger = logging.getLogger(__name__)


class EcosystemState(Enum):
    STABLE = "stable"
    STRESSED = "stressed"
    UNDER_ATTACK = "under_attack"
    RECOVERING = "recovering"
    EVOLVING = "evolving"


@dataclass
class EcosystemMetrics:
    total_agents: int = 0
    attack_agents: int = 0
    defense_agents: int = 0
    memory_agents: int = 0
    
    total_energy: float = 0.0
    avg_energy: float = 0.0
    
    attack_success_rate: float = 0.0
    defense_success_rate: float = 0.0
    
    reproduction_rate: float = 0.0
    death_rate: float = 0.0
    
    diversity_index: float = 0.0
    
    emergence_events: int = 0
    
    timestamp: float = field(default_factory=time.time)


class EcosystemCoordinator:
    
    def __init__(
        self,
        blackboard,
        communication,
        max_attack_agents: int = 20,
        max_defense_agents: int = 30,
        max_memory_agents: int = 10,
        evolution_interval: float = 60.0,
        selection_pressure: float = 0.05
    ):
        self.blackboard = blackboard
        self.communication = communication
        
        self.max_attack_agents = max_attack_agents
        self.max_defense_agents = max_defense_agents
        self.max_memory_agents = max_memory_agents
        self.evolution_interval = evolution_interval
        self.selection_pressure = selection_pressure
        
        self.attack_agents: Dict[str, LivingAttackAgent] = {}
        self.defense_agents: Dict[str, LivingDefenseAgent] = {}
        self.memory_agents: Dict[str, LivingMemoryAgent] = {}
        
        self.state = EcosystemState.STABLE
        self.metrics_history: deque = deque(maxlen=1000)
        
        self.evolution_events: deque = deque(maxlen=10000)
        self.emergence_patterns: Dict[str, Dict] = {}
        
        self.generation = 0
        self.total_births = 0
        self.total_deaths = 0
        
        self._running = False
        self._coordinator_thread = None
        self._evolution_thread = None
        
        self.stats = {
            "total_interactions": 0,
            "successful_cooperations": 0,
            "failed_cooperations": 0,
            "emergence_detected": 0
        }
    
    def start(self):
        self._running = True
        
        self._coordinator_thread = threading.Thread(target=self._coordination_loop, daemon=True)
        self._coordinator_thread.start()
        
        self._evolution_thread = threading.Thread(target=self._evolution_loop, daemon=True)
        self._evolution_thread.start()
        
        logger.info("Ecosystem Coordinator started")
    
    def stop(self):
        self._running = False
        
        for agent in list(self.attack_agents.values()):
            agent.stop()
        for agent in list(self.defense_agents.values()):
            agent.stop()
        for agent in list(self.memory_agents.values()):
            agent.stop()
        
        logger.info("Ecosystem Coordinator stopped")
    
    def spawn_attack_agent(
        self,
        species: str = "default",
        parent_ids: Optional[List[str]] = None
    ) -> LivingAttackAgent:
        agent_id = f"attack_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
        
        agent = LivingAttackAgent(
            agent_id=agent_id,
            species=species,
            blackboard=self.blackboard,
            communication=self.communication
        )
        
        if parent_ids:
            agent.parent_ids = parent_ids
            agent.generation = max(
                self.attack_agents.get(pid, LivingAttackAgent("", "")).generation + 1
                for pid in parent_ids
                if pid in self.attack_agents
            ) if parent_ids else 0
        
        self.attack_agents[agent_id] = agent
        agent.start()
        
        self.total_births += 1
        self._record_evolution_event("birth", agent_id, "attack")
        
        logger.info(f"Spawned attack agent: {agent_id}")
        
        return agent
    
    def spawn_defense_agent(
        self,
        species: str = "default",
        parent_ids: Optional[List[str]] = None
    ) -> LivingDefenseAgent:
        agent_id = f"defense_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
        
        agent = LivingDefenseAgent(
            agent_id=agent_id,
            species=species,
            blackboard=self.blackboard,
            communication=self.communication
        )
        
        if parent_ids:
            agent.parent_ids = parent_ids
            agent.generation = max(
                self.defense_agents.get(pid, LivingDefenseAgent("", "")).generation + 1
                for pid in parent_ids
                if pid in self.defense_agents
            ) if parent_ids else 0
        
        self.defense_agents[agent_id] = agent
        agent.start()
        
        self.total_births += 1
        self._record_evolution_event("birth", agent_id, "defense")
        
        logger.info(f"Spawned defense agent: {agent_id}")
        
        return agent
    
    def spawn_memory_agent(
        self,
        species: str = "default"
    ) -> LivingMemoryAgent:
        agent_id = f"memory_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
        
        agent = LivingMemoryAgent(
            agent_id=agent_id,
            species=species,
            blackboard=self.blackboard,
            communication=self.communication
        )
        
        self.memory_agents[agent_id] = agent
        agent.start()
        
        self.total_births += 1
        self._record_evolution_event("birth", agent_id, "memory")
        
        logger.info(f"Spawned memory agent: {agent_id}")
        
        return agent
    
    def _coordination_loop(self):
        while self._running:
            try:
                self._update_ecosystem_state()
                
                self._collect_metrics()
                
                self._detect_emergence()
                
                self._balance_populations()
                
                self._facilitate_interactions()
                
                time.sleep(5)
                
            except Exception as e:
                logger.error(f"Error in coordination loop: {e}")
                time.sleep(1)
    
    def _evolution_loop(self):
        while self._running:
            try:
                time.sleep(self.evolution_interval)
                
                self.generation += 1
                
                self._run_selection()
                
                self._run_reproduction()
                
                self._run_mutation()
                
                self._record_evolution_event("generation", f"gen_{self.generation}", "system")
                
                logger.info(f"Evolution cycle completed: Generation {self.generation}")
                
            except Exception as e:
                logger.error(f"Error in evolution loop: {e}")
                time.sleep(1)
    
    def _update_ecosystem_state(self):
        metrics = self._calculate_metrics()
        
        if metrics.attack_success_rate > 0.7:
            self.state = EcosystemState.UNDER_ATTACK
        elif metrics.defense_success_rate < 0.3:
            self.state = EcosystemState.STRESSED
        elif metrics.death_rate > 0.1:
            self.state = EcosystemState.RECOVERING
        elif metrics.reproduction_rate > 0.05:
            self.state = EcosystemState.EVOLVING
        else:
            self.state = EcosystemState.STABLE
        
        if self.blackboard:
            self.blackboard.write(
                "ecosystem:state",
                {
                    "state": self.state.value,
                    "metrics": metrics.__dict__,
                    "timestamp": time.time()
                },
                ttl=60
            )
    
    def _calculate_metrics(self) -> EcosystemMetrics:
        metrics = EcosystemMetrics()
        
        metrics.attack_agents = len([a for a in self.attack_agents.values() if a.is_alive()])
        metrics.defense_agents = len([a for a in self.defense_agents.values() if a.is_alive()])
        metrics.memory_agents = len([a for a in self.memory_agents.values() if a.is_alive()])
        metrics.total_agents = metrics.attack_agents + metrics.defense_agents + metrics.memory_agents
        
        all_agents = (
            list(self.attack_agents.values()) +
            list(self.defense_agents.values()) +
            list(self.memory_agents.values())
        )
        
        if all_agents:
            metrics.total_energy = sum(a.energy for a in all_agents if a.is_alive())
            metrics.avg_energy = metrics.total_energy / metrics.total_agents if metrics.total_agents > 0 else 0
        
        attack_successes = sum(a.success_count for a in self.attack_agents.values())
        attack_failures = sum(a.failure_count for a in self.attack_agents.values())
        if attack_successes + attack_failures > 0:
            metrics.attack_success_rate = attack_successes / (attack_successes + attack_failures)
        
        defense_successes = sum(a.success_count for a in self.defense_agents.values())
        defense_failures = sum(a.failure_count for a in self.defense_agents.values())
        if defense_successes + defense_failures > 0:
            metrics.defense_success_rate = defense_successes / (defense_successes + defense_failures)
        
        metrics.diversity_index = self._calculate_diversity()
        
        return metrics
    
    def _calculate_diversity(self) -> float:
        species_counts = defaultdict(int)
        
        for agent in self.attack_agents.values():
            if agent.is_alive():
                species_counts[agent.species] += 1
        
        for agent in self.defense_agents.values():
            if agent.is_alive():
                species_counts[agent.species] += 1
        
        total = sum(species_counts.values())
        if total == 0:
            return 0
        
        proportions = [count / total for count in species_counts.values()]
        diversity = -sum(p * np.log(p) for p in proportions if p > 0)
        
        return diversity
    
    def _collect_metrics(self):
        metrics = self._calculate_metrics()
        self.metrics_history.append(metrics)
    
    def _detect_emergence(self):
        if len(self.metrics_history) < 10:
            return
        
        recent = list(self.metrics_history)[-10:]
        
        cooperation_patterns = self._detect_cooperation_patterns()
        if cooperation_patterns:
            for pattern in cooperation_patterns:
                pattern_id = self._generate_pattern_id(pattern)
                if pattern_id not in self.emergence_patterns:
                    self.emergence_patterns[pattern_id] = {
                        "pattern": pattern,
                        "first_detected": time.time(),
                        "occurrence_count": 1
                    }
                    self.stats["emergence_detected"] += 1
                    self._record_evolution_event("emergence", pattern_id, "system")
                else:
                    self.emergence_patterns[pattern_id]["occurrence_count"] += 1
    
    def _detect_cooperation_patterns(self) -> List[Dict]:
        patterns = []
        
        alliance_counts = defaultdict(int)
        for agent in self.attack_agents.values():
            if agent.is_alive():
                for ally_id in agent.alliance_ids:
                    alliance_counts[(agent.agent_id, ally_id)] += 1
        
        for (a1, a2), count in alliance_counts.items():
            if count >= 3:
                patterns.append({
                    "type": "stable_alliance",
                    "agents": [a1, a2],
                    "stability": count
                })
        
        team_counts = defaultdict(int)
        for agent in self.defense_agents.values():
            if agent.is_alive():
                for team_id in agent.team:
                    team_counts[(agent.agent_id, team_id)] += 1
        
        for (d1, d2), count in team_counts.items():
            if count >= 3:
                patterns.append({
                    "type": "stable_team",
                    "agents": [d1, d2],
                    "stability": count
                })
        
        return patterns
    
    def _generate_pattern_id(self, pattern: Dict) -> str:
        pattern_str = json.dumps(pattern, sort_keys=True)
        return hashlib.md5(pattern_str.encode()).hexdigest()[:16]
    
    def _balance_populations(self):
        alive_attack = len([a for a in self.attack_agents.values() if a.is_alive()])
        alive_defense = len([a for a in self.defense_agents.values() if a.is_alive()])
        alive_memory = len([a for a in self.memory_agents.values() if a.is_alive()])
        
        if alive_attack < self.max_attack_agents * 0.5:
            self.spawn_attack_agent()
        
        if alive_defense < self.max_defense_agents * 0.5:
            self.spawn_defense_agent()
        
        if alive_memory < self.max_memory_agents * 0.5:
            self.spawn_memory_agent()
    
    def _facilitate_interactions(self):
        self._process_attack_defense_interactions()
        
        self._process_memory_queries()
    
    def _process_attack_defense_interactions(self):
        for attack_agent in list(self.attack_agents.values()):
            if not attack_agent.is_alive():
                continue
            
            for defense_agent in list(self.defense_agents.values()):
                if not defense_agent.is_alive():
                    continue
                
                if random.random() < 0.01:
                    self.stats["total_interactions"] += 1
    
    def _process_memory_queries(self):
        pass
    
    def _run_selection(self):
        self._select_agents(self.attack_agents, "attack")
        self._select_agents(self.defense_agents, "defense")
        self._select_agents(self.memory_agents, "memory")
    
    def _select_agents(self, agents: Dict, agent_type: str):
        alive = [(aid, a) for aid, a in agents.items() if a.is_alive()]
        
        if len(alive) < 2:
            return
        
        fitness_scores = [(aid, a.get_fitness()) for aid, a in alive]
        fitness_scores.sort(key=lambda x: x[1])
        
        eliminate_count = max(1, int(len(alive) * self.selection_pressure))
        
        for aid, _ in fitness_scores[:eliminate_count]:
            if aid in agents:
                agents[aid].die()
                self.total_deaths += 1
                self._record_evolution_event("death", aid, agent_type)
    
    def _run_reproduction(self):
        self._reproduce_agents(self.attack_agents, "attack")
        self._reproduce_agents(self.defense_agents, "defense")
    
    def _reproduce_agents(self, agents: Dict, agent_type: str):
        alive = [(aid, a) for aid, a in agents.items() if a.is_alive() and a.can_reproduce()]
        
        for aid, agent in alive:
            if random.random() < 0.3:
                offspring_id = f"{agent_type}_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
                
                if agent_type == "attack":
                    offspring = agent.reproduce_asexual(offspring_id)
                    if offspring:
                        self.attack_agents[offspring_id] = offspring
                        offspring.start()
                elif agent_type == "defense":
                    offspring = agent.reproduce_asexual(offspring_id)
                    if offspring:
                        self.defense_agents[offspring_id] = offspring
                        offspring.start()
                
                self._record_evolution_event("reproduction", f"{aid}->{offspring_id}", agent_type)
    
    def _run_mutation(self):
        for agent in list(self.attack_agents.values()):
            if agent.is_alive() and random.random() < 0.1:
                agent.mutate()
        
        for agent in list(self.defense_agents.values()):
            if agent.is_alive() and random.random() < 0.1:
                agent.mutate()
    
    def _record_evolution_event(self, event_type: str, subject: str, category: str):
        event = {
            "event_type": event_type,
            "subject": subject,
            "category": category,
            "generation": self.generation,
            "timestamp": time.time()
        }
        
        self.evolution_events.append(event)
        
        if self.blackboard:
            self.blackboard.write(
                f"evolution:event:{int(time.time() * 1000)}",
                event,
                ttl=86400
            )
    
    def get_status(self) -> Dict:
        metrics = self._calculate_metrics()
        
        return {
            "state": self.state.value,
            "generation": self.generation,
            "total_births": self.total_births,
            "total_deaths": self.total_deaths,
            "metrics": {
                "total_agents": metrics.total_agents,
                "attack_agents": metrics.attack_agents,
                "defense_agents": metrics.defense_agents,
                "memory_agents": metrics.memory_agents,
                "avg_energy": metrics.avg_energy,
                "attack_success_rate": metrics.attack_success_rate,
                "defense_success_rate": metrics.defense_success_rate,
                "diversity_index": metrics.diversity_index
            },
            "emergence_patterns": len(self.emergence_patterns),
            "stats": self.stats.copy()
        }
    
    def get_agent_states(self, agent_type: Optional[str] = None) -> List[Dict]:
        states = []
        
        if agent_type is None or agent_type == "attack":
            for agent in self.attack_agents.values():
                states.append(agent.get_state())
        
        if agent_type is None or agent_type == "defense":
            for agent in self.defense_agents.values():
                states.append(agent.get_state())
        
        if agent_type is None or agent_type == "memory":
            for agent in self.memory_agents.values():
                states.append(agent.get_state())
        
        return states
    
    def get_evolution_history(self, limit: int = 100) -> List[Dict]:
        return list(self.evolution_events)[-limit:]
    
    def get_emergence_patterns(self) -> List[Dict]:
        return [
            {
                "pattern_id": pid,
                **pdata
            }
            for pid, pdata in self.emergence_patterns.items()
        ]
