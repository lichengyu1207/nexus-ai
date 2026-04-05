"""
业务进化引擎
Business Evolution Engine

负责业务智能体的繁殖、变异、选择
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

logger = logging.getLogger(__name__)


class EvolutionPhase(Enum):
    SELECTION = "selection"
    REPRODUCTION = "reproduction"
    MUTATION = "mutation"
    EVALUATION = "evaluation"


@dataclass
class EvolutionConfig:
    population_size: int = 50
    max_population: int = 100
    selection_pressure: float = 0.3
    mutation_rate: float = 0.1
    crossover_rate: float = 0.5
    elitism_rate: float = 0.1
    energy_threshold: float = 50.0
    fitness_threshold: float = 0.5
    generation_interval: float = 3600
    
    def to_dict(self) -> Dict:
        return {
            "population_size": self.population_size,
            "max_population": self.max_population,
            "selection_pressure": self.selection_pressure,
            "mutation_rate": self.mutation_rate,
            "crossover_rate": self.crossover_rate,
            "elitism_rate": self.elitism_rate,
            "energy_threshold": self.energy_threshold,
            "fitness_threshold": self.fitness_threshold,
            "generation_interval": self.generation_interval
        }


class PopulationManager:
    """
    种群管理器
    
    管理业务智能体种群
    """
    
    def __init__(self, config: EvolutionConfig):
        self.config = config
        self.population: Dict[str, Any] = {}
        self.species_populations: Dict[str, List[str]] = defaultdict(list)
        self.generation = 0
        self.best_individuals: Dict[str, Any] = {}
        
        self._lock = threading.RLock()
    
    def add_agent(self, agent: Any):
        with self._lock:
            self.population[agent.agent_id] = agent
            self.species_populations[agent.species].append(agent.agent_id)
    
    def remove_agent(self, agent_id: str):
        with self._lock:
            if agent_id in self.population:
                agent = self.population[agent_id]
                del self.population[agent_id]
                
                if agent.species in self.species_populations:
                    if agent_id in self.species_populations[agent.species]:
                        self.species_populations[agent.species].remove(agent_id)
    
    def get_agent(self, agent_id: str) -> Optional[Any]:
        return self.population.get(agent_id)
    
    def get_population(self) -> List[Any]:
        return list(self.population.values())
    
    def get_species_population(self, species: str) -> List[Any]:
        agent_ids = self.species_populations.get(species, [])
        return [self.population[aid] for aid in agent_ids if aid in self.population]
    
    def get_population_size(self) -> int:
        return len(self.population)
    
    def get_fittest(self, n: int = 10) -> List[Any]:
        agents = list(self.population.values())
        agents.sort(key=lambda a: a.get_fitness(), reverse=True)
        return agents[:n]
    
    def get_least_fit(self, n: int = 10) -> List[Any]:
        agents = list(self.population.values())
        agents.sort(key=lambda a: a.get_fitness())
        return agents[:n]
    
    def update_best(self, species: str, agent: Any):
        current_best = self.best_individuals.get(species)
        if current_best is None or agent.get_fitness() > current_best.get_fitness():
            self.best_individuals[species] = agent
    
    def get_best(self, species: str) -> Optional[Any]:
        return self.best_individuals.get(species)


class BusinessEvolutionEngine:
    """
    业务进化引擎
    
    负责业务智能体的繁殖、变异、选择：
    1. 选择：根据适应度选择优秀个体
    2. 繁殖：产生后代
    3. 变异：引入随机变化
    4. 评估：评估新个体
    """
    
    def __init__(
        self,
        memory_agent: Optional[Any] = None,
        blackboard: Optional[Any] = None,
        config: Optional[EvolutionConfig] = None,
    ):
        self.memory_agent = memory_agent
        self.blackboard = blackboard
        self.config = config or EvolutionConfig()
        
        self.population_manager = PopulationManager(self.config)
        
        self.phase = EvolutionPhase.SELECTION
        self.generation = 0
        self.evolution_history: List[Dict] = []
        
        self._lock = threading.RLock()
        self._running = False
        self._evolution_task: Optional[asyncio.Task] = None
        
        self.stats = {
            "generations": 0,
            "total_reproductions": 0,
            "total_mutations": 0,
            "total_selections": 0,
            "avg_fitness": 0.0,
            "best_fitness": 0.0,
            "population_diversity": 0.0,
        }
    
    async def start(self):
        self._running = True
        self._evolution_task = asyncio.create_task(self._evolution_loop())
        logger.info("Business evolution engine started")
    
    async def stop(self):
        self._running = False
        if self._evolution_task:
            self._evolution_task.cancel()
            try:
                await self._evolution_task
            except asyncio.CancelledError:
                pass
        logger.info("Business evolution engine stopped")
    
    async def _evolution_loop(self):
        while self._running:
            try:
                await self._run_evolution_cycle()
                await asyncio.sleep(self.config.generation_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in evolution loop: {e}")
                await asyncio.sleep(60)
    
    async def _run_evolution_cycle(self):
        self.phase = EvolutionPhase.SELECTION
        selected = await self._selection()
        
        self.phase = EvolutionPhase.REPRODUCTION
        offspring = await self._reproduction(selected)
        
        self.phase = EvolutionPhase.MUTATION
        mutated = await self._mutation(offspring)
        
        self.phase = EvolutionPhase.EVALUATION
        await self._evaluation(mutated)
        
        self.generation += 1
        self.stats["generations"] = self.generation
        
        await self._record_evolution(selected, offspring, mutated)
    
    async def _selection(self) -> List[Any]:
        population = self.population_manager.get_population()
        
        if not population:
            return []
        
        population.sort(key=lambda a: a.get_fitness(), reverse=True)
        
        elite_count = int(len(population) * self.config.elitism_rate)
        elite = population[:elite_count]
        
        selected = list(elite)
        
        remaining = population[elite_count:]
        for agent in remaining:
            if random.random() < self.config.selection_pressure:
                selected.append(agent)
        
        self.stats["total_selections"] += len(selected)
        
        return selected
    
    async def _reproduction(self, selected: List[Any]) -> List[Any]:
        offspring = []
        
        for agent in selected:
            if agent.can_reproduce():
                if random.random() < self.config.crossover_rate:
                    partner = self._find_partner(agent, selected)
                    if partner:
                        child = await agent.reproduce_sexual(partner)
                        if child:
                            offspring.append(child)
                            self.stats["total_reproductions"] += 1
                else:
                    child = await agent.reproduce()
                    if child:
                        offspring.append(child)
                        self.stats["total_reproductions"] += 1
        
        return offspring
    
    def _find_partner(self, agent: Any, candidates: List[Any]) -> Optional[Any]:
        same_species = [
            a for a in candidates
            if a.species == agent.species and a.agent_id != agent.agent_id
        ]
        
        if not same_species:
            return None
        
        same_species.sort(key=lambda a: a.get_fitness(), reverse=True)
        
        return same_species[0] if same_species[0].can_reproduce() else None
    
    async def _mutation(self, offspring: List[Any]) -> List[Any]:
        mutated = []
        
        for agent in offspring:
            if random.random() < self.config.mutation_rate:
                agent.mutate()
                self.stats["total_mutations"] += 1
            
            mutated.append(agent)
        
        return mutated
    
    async def _evaluation(self, agents: List[Any]):
        for agent in agents:
            self.population_manager.add_agent(agent)
        
        population = self.population_manager.get_population()
        
        if population:
            fitnesses = [a.get_fitness() for a in population]
            self.stats["avg_fitness"] = sum(fitnesses) / len(fitnesses)
            self.stats["best_fitness"] = max(fitnesses)
            
            self.stats["population_diversity"] = self._calculate_diversity(population)
        
        await self._population_control()
    
    def _calculate_diversity(self, population: List[Any]) -> float:
        if len(population) < 2:
            return 0.0
        
        species_counts: Dict[str, int] = defaultdict(int)
        for agent in population:
            species_counts[agent.species] += 1
        
        total = len(population)
        diversity = 0.0
        
        for count in species_counts.values():
            p = count / total
            diversity -= p * (p ** 0.5) if p > 0 else 0
        
        return diversity
    
    async def _population_control(self):
        current_size = self.population_manager.get_population_size()
        
        if current_size > self.config.max_population:
            to_remove = current_size - self.config.max_population
            
            least_fit = self.population_manager.get_least_fit(to_remove)
            
            for agent in least_fit:
                self.population_manager.remove_agent(agent.agent_id)
    
    async def _record_evolution(
        self,
        selected: List[Any],
        offspring: List[Any],
        mutated: List[Any],
    ):
        record = {
            "generation": self.generation,
            "timestamp": time.time(),
            "selected_count": len(selected),
            "offspring_count": len(offspring),
            "mutated_count": len(mutated),
            "population_size": self.population_manager.get_population_size(),
            "avg_fitness": self.stats["avg_fitness"],
            "best_fitness": self.stats["best_fitness"],
        }
        
        self.evolution_history.append(record)
        
        if self.memory_agent:
            try:
                await self.memory_agent.store({
                    "type": "evolution_record",
                    "record": record,
                    "timestamp": time.time()
                })
            except Exception as e:
                logger.error(f"Failed to store evolution record: {e}")
    
    def register_agent(self, agent: Any):
        self.population_manager.add_agent(agent)
    
    def unregister_agent(self, agent_id: str):
        self.population_manager.remove_agent(agent_id)
    
    def get_agent(self, agent_id: str) -> Optional[Any]:
        return self.population_manager.get_agent(agent_id)
    
    def get_population(self) -> List[Any]:
        return self.population_manager.get_population()
    
    def get_species_population(self, species: str) -> List[Any]:
        return self.population_manager.get_species_population(species)
    
    def get_stats(self) -> Dict:
        with self._lock:
            return {
                **self.stats,
                "phase": self.phase.value,
                "generation": self.generation,
                "population_size": self.population_manager.get_population_size(),
            }
