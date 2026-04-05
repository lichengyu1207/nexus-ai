"""
群体遗传算法进化模块
Genetic Algorithm Evolution Module

实现智能体种群进化、染色体编码、选择/交叉/变异操作等功能
"""

import asyncio
import copy
import hashlib
import json
import logging
import math
import random
import threading
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

logger = logging.getLogger(__name__)


class GeneType(Enum):
    WEIGHT = "weight"
    BIAS = "bias"
    THRESHOLD = "threshold"
    PARAMETER = "parameter"
    RULE = "rule"


class SelectionMethod(Enum):
    TOURNAMENT = "tournament"
    ROULETTE = "roulette"
    RANK = "rank"
    ELITE = "elite"


class CrossoverType(Enum):
    SINGLE_POINT = "single_point"
    TWO_POINT = "two_point"
    UNIFORM = "uniform"
    ARITHMETIC = "arithmetic"


class MutationType(Enum):
    GAUSSIAN = "gaussian"
    UNIFORM = "uniform"
    BIT_FLIP = "bit_flip"
    SWAP = "swap"


@dataclass
class Gene:
    gene_id: str
    gene_type: GeneType
    name: str
    value: float
    min_value: float
    max_value: float
    mutation_rate: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "gene_id": self.gene_id,
            "gene_type": self.gene_type.value,
            "name": self.name,
            "value": self.value,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "mutation_rate": self.mutation_rate,
        }
    
    def mutate(self, mutation_type: MutationType = MutationType.GAUSSIAN):
        if random.random() > self.mutation_rate:
            return
        
        if mutation_type == MutationType.GAUSSIAN:
            delta = random.gauss(0, (self.max_value - self.min_value) * 0.1)
            self.value = max(self.min_value, min(self.max_value, self.value + delta))
        elif mutation_type == MutationType.UNIFORM:
            self.value = random.uniform(self.min_value, self.max_value)
        elif mutation_type == MutationType.BIT_FLIP:
            self.value = self.max_value if self.value < (self.min_value + self.max_value) / 2 else self.min_value


@dataclass
class Chromosome:
    chromosome_id: str
    genes: List[Gene]
    fitness: float
    generation: int
    parent_ids: List[str]
    created_at: datetime
    evaluation_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "chromosome_id": self.chromosome_id,
            "genes": [g.to_dict() for g in self.genes],
            "fitness": self.fitness,
            "generation": self.generation,
            "parent_ids": self.parent_ids,
            "created_at": self.created_at.isoformat(),
            "evaluation_count": self.evaluation_count,
        }
    
    def get_gene_values(self) -> List[float]:
        return [g.value for g in self.genes]
    
    def set_gene_values(self, values: List[float]):
        for i, value in enumerate(values):
            if i < len(self.genes):
                self.genes[i].value = max(
                    self.genes[i].min_value,
                    min(self.genes[i].max_value, value)
                )
    
    def get_gene_by_name(self, name: str) -> Optional[Gene]:
        for gene in self.genes:
            if gene.name == name:
                return gene
        return None
    
    def copy(self) -> 'Chromosome':
        return Chromosome(
            chromosome_id=f"chr_{uuid.uuid4().hex[:8]}",
            genes=[Gene(
                gene_id=g.gene_id,
                gene_type=g.gene_type,
                name=g.name,
                value=g.value,
                min_value=g.min_value,
                max_value=g.max_value,
                mutation_rate=g.mutation_rate,
            ) for g in self.genes],
            fitness=self.fitness,
            generation=self.generation,
            parent_ids=[self.chromosome_id],
            created_at=datetime.now(),
            evaluation_count=0,
        )


@dataclass
class Population:
    population_id: str
    chromosomes: List[Chromosome]
    generation: int
    best_fitness: float
    average_fitness: float
    diversity: float
    created_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "population_id": self.population_id,
            "chromosomes": [c.to_dict() for c in self.chromosomes],
            "generation": self.generation,
            "best_fitness": self.best_fitness,
            "average_fitness": self.average_fitness,
            "diversity": self.diversity,
            "created_at": self.created_at.isoformat(),
            "size": len(self.chromosomes),
        }
    
    def calculate_statistics(self):
        if not self.chromosomes:
            self.best_fitness = 0.0
            self.average_fitness = 0.0
            self.diversity = 0.0
            return
        
        fitnesses = [c.fitness for c in self.chromosomes]
        self.best_fitness = max(fitnesses)
        self.average_fitness = sum(fitnesses) / len(fitnesses)
        
        if len(self.chromosomes) > 1:
            total_distance = 0.0
            count = 0
            
            for i, c1 in enumerate(self.chromosomes):
                for c2 in self.chromosomes[i+1:]:
                    v1 = c1.get_gene_values()
                    v2 = c2.get_gene_values()
                    
                    distance = math.sqrt(sum((a - b) ** 2 for a, b in zip(v1, v2)))
                    total_distance += distance
                    count += 1
            
            self.diversity = total_distance / max(count, 1)
        else:
            self.diversity = 0.0


@dataclass
class EvolutionNode:
    node_id: str
    chromosome_id: str
    generation: int
    fitness: float
    parent_ids: List[str]
    children_ids: List[str]
    is_elite: bool
    created_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "chromosome_id": self.chromosome_id,
            "generation": self.generation,
            "fitness": self.fitness,
            "parent_ids": self.parent_ids,
            "children_ids": self.children_ids,
            "is_elite": self.is_elite,
            "created_at": self.created_at.isoformat(),
        }


class EvolutionTree:
    """进化树 - 记录进化历史"""
    
    def __init__(self, max_depth: int = 100):
        self.max_depth = max_depth
        self.nodes: Dict[str, EvolutionNode] = {}
        self.generation_nodes: Dict[int, List[str]] = defaultdict(list)
        self.root_id: Optional[str] = None
        
        self._lock = threading.Lock()
        
        self.stats = {
            "total_nodes": 0,
            "max_generation": 0,
            "elite_count": 0,
        }
    
    def add_node(
        self,
        chromosome: Chromosome,
        parent_ids: List[str] = None,
        is_elite: bool = False
    ) -> str:
        node_id = f"node_{chromosome.chromosome_id}"
        
        node = EvolutionNode(
            node_id=node_id,
            chromosome_id=chromosome.chromosome_id,
            generation=chromosome.generation,
            fitness=chromosome.fitness,
            parent_ids=parent_ids or [],
            children_ids=[],
            is_elite=is_elite,
            created_at=datetime.now(),
        )
        
        with self._lock:
            self.nodes[node_id] = node
            self.generation_nodes[chromosome.generation].append(node_id)
            
            if self.root_id is None:
                self.root_id = node_id
            
            for parent_id in (parent_ids or []):
                parent_node_id = f"node_{parent_id}"
                if parent_node_id in self.nodes:
                    self.nodes[parent_node_id].children_ids.append(node_id)
            
            self.stats["total_nodes"] += 1
            self.stats["max_generation"] = max(
                self.stats["max_generation"],
                chromosome.generation
            )
            if is_elite:
                self.stats["elite_count"] += 1
        
        return node_id
    
    def get_ancestry(self, chromosome_id: str) -> List[EvolutionNode]:
        ancestry = []
        node_id = f"node_{chromosome_id}"
        
        with self._lock:
            current_id = node_id
            while current_id and current_id in self.nodes:
                node = self.nodes[current_id]
                ancestry.append(node)
                
                if node.parent_ids:
                    current_id = f"node_{node.parent_ids[0]}"
                else:
                    break
        
        return ancestry
    
    def get_generation_stats(self, generation: int) -> Dict[str, Any]:
        with self._lock:
            node_ids = self.generation_nodes.get(generation, [])
            
            if not node_ids:
                return {"generation": generation, "count": 0}
            
            nodes = [self.nodes[nid] for nid in node_ids]
            fitnesses = [n.fitness for n in nodes]
            
            return {
                "generation": generation,
                "count": len(nodes),
                "best_fitness": max(fitnesses),
                "average_fitness": sum(fitnesses) / len(fitnesses),
                "elite_count": sum(1 for n in nodes if n.is_elite),
            }
    
    def get_feature_preservation(self) -> Dict[str, float]:
        feature_preservation: Dict[str, int] = defaultdict(int)
        
        with self._lock:
            for node in self.nodes.values():
                if node.is_elite:
                    feature_preservation[node.chromosome_id] += 1
        
        return dict(feature_preservation)


class SelectionStrategy:
    """选择策略"""
    
    def __init__(
        self,
        method: SelectionMethod = SelectionMethod.TOURNAMENT,
        elite_ratio: float = 0.2,
        tournament_size: int = 3
    ):
        self.method = method
        self.elite_ratio = elite_ratio
        self.tournament_size = tournament_size
    
    def select(
        self,
        population: Population,
        count: int
    ) -> List[Chromosome]:
        if self.method == SelectionMethod.ELITE:
            return self._elite_selection(population, count)
        elif self.method == SelectionMethod.TOURNAMENT:
            return self._tournament_selection(population, count)
        elif self.method == SelectionMethod.ROULETTE:
            return self._roulette_selection(population, count)
        elif self.method == SelectionMethod.RANK:
            return self._rank_selection(population, count)
        else:
            return self._tournament_selection(population, count)
    
    def _elite_selection(
        self,
        population: Population,
        count: int
    ) -> List[Chromosome]:
        sorted_chromosomes = sorted(
            population.chromosomes,
            key=lambda c: c.fitness,
            reverse=True
        )
        return sorted_chromosomes[:count]
    
    def _tournament_selection(
        self,
        population: Population,
        count: int
    ) -> List[Chromosome]:
        selected = []
        
        for _ in range(count):
            tournament = random.sample(
                population.chromosomes,
                min(self.tournament_size, len(population.chromosomes))
            )
            winner = max(tournament, key=lambda c: c.fitness)
            selected.append(winner.copy())
        
        return selected
    
    def _roulette_selection(
        self,
        population: Population,
        count: int
    ) -> List[Chromosome]:
        fitnesses = [max(0.001, c.fitness) for c in population.chromosomes]
        total_fitness = sum(fitnesses)
        
        if total_fitness == 0:
            return [c.copy() for c in random.sample(
                population.chromosomes,
                min(count, len(population.chromosomes))
            )]
        
        probabilities = [f / total_fitness for f in fitnesses]
        
        selected = []
        for _ in range(count):
            r = random.random()
            cumulative = 0.0
            
            for i, prob in enumerate(probabilities):
                cumulative += prob
                if r <= cumulative:
                    selected.append(population.chromosomes[i].copy())
                    break
        
        return selected
    
    def _rank_selection(
        self,
        population: Population,
        count: int
    ) -> List[Chromosome]:
        sorted_chromosomes = sorted(
            population.chromosomes,
            key=lambda c: c.fitness
        )
        
        n = len(sorted_chromosomes)
        ranks = list(range(1, n + 1))
        total_rank = sum(ranks)
        
        probabilities = [r / total_rank for r in ranks]
        
        selected = []
        for _ in range(count):
            r = random.random()
            cumulative = 0.0
            
            for i, prob in enumerate(probabilities):
                cumulative += prob
                if r <= cumulative:
                    selected.append(sorted_chromosomes[i].copy())
                    break
        
        return selected


class CrossoverOperator:
    """交叉操作器"""
    
    def __init__(self, crossover_type: CrossoverType = CrossoverType.UNIFORM):
        self.crossover_type = crossover_type
    
    def crossover(
        self,
        parent1: Chromosome,
        parent2: Chromosome
    ) -> Tuple[Chromosome, Chromosome]:
        if self.crossover_type == CrossoverType.SINGLE_POINT:
            return self._single_point_crossover(parent1, parent2)
        elif self.crossover_type == CrossoverType.TWO_POINT:
            return self._two_point_crossover(parent1, parent2)
        elif self.crossover_type == CrossoverType.UNIFORM:
            return self._uniform_crossover(parent1, parent2)
        elif self.crossover_type == CrossoverType.ARITHMETIC:
            return self._arithmetic_crossover(parent1, parent2)
        else:
            return self._uniform_crossover(parent1, parent2)
    
    def _single_point_crossover(
        self,
        parent1: Chromosome,
        parent2: Chromosome
    ) -> Tuple[Chromosome, Chromosome]:
        child1 = parent1.copy()
        child2 = parent2.copy()
        
        n_genes = min(len(parent1.genes), len(parent2.genes))
        if n_genes < 2:
            return child1, child2
        
        point = random.randint(1, n_genes - 1)
        
        child1_genes = parent1.get_gene_values()[:point] + parent2.get_gene_values()[point:]
        child2_genes = parent2.get_gene_values()[:point] + parent1.get_gene_values()[point:]
        
        child1.set_gene_values(child1_genes)
        child2.set_gene_values(child2_genes)
        
        child1.parent_ids = [parent1.chromosome_id, parent2.chromosome_id]
        child2.parent_ids = [parent1.chromosome_id, parent2.chromosome_id]
        
        return child1, child2
    
    def _two_point_crossover(
        self,
        parent1: Chromosome,
        parent2: Chromosome
    ) -> Tuple[Chromosome, Chromosome]:
        child1 = parent1.copy()
        child2 = parent2.copy()
        
        n_genes = min(len(parent1.genes), len(parent2.genes))
        if n_genes < 3:
            return child1, child2
        
        points = sorted(random.sample(range(1, n_genes), 2))
        
        v1 = parent1.get_gene_values()
        v2 = parent2.get_gene_values()
        
        child1_genes = v1[:points[0]] + v2[points[0]:points[1]] + v1[points[1]:]
        child2_genes = v2[:points[0]] + v1[points[0]:points[1]] + v2[points[1]:]
        
        child1.set_gene_values(child1_genes)
        child2.set_gene_values(child2_genes)
        
        child1.parent_ids = [parent1.chromosome_id, parent2.chromosome_id]
        child2.parent_ids = [parent1.chromosome_id, parent2.chromosome_id]
        
        return child1, child2
    
    def _uniform_crossover(
        self,
        parent1: Chromosome,
        parent2: Chromosome
    ) -> Tuple[Chromosome, Chromosome]:
        child1 = parent1.copy()
        child2 = parent2.copy()
        
        v1 = parent1.get_gene_values()
        v2 = parent2.get_gene_values()
        
        child1_genes = []
        child2_genes = []
        
        for i in range(min(len(v1), len(v2))):
            if random.random() < 0.5:
                child1_genes.append(v1[i])
                child2_genes.append(v2[i])
            else:
                child1_genes.append(v2[i])
                child2_genes.append(v1[i])
        
        child1.set_gene_values(child1_genes)
        child2.set_gene_values(child2_genes)
        
        child1.parent_ids = [parent1.chromosome_id, parent2.chromosome_id]
        child2.parent_ids = [parent1.chromosome_id, parent2.chromosome_id]
        
        return child1, child2
    
    def _arithmetic_crossover(
        self,
        parent1: Chromosome,
        parent2: Chromosome
    ) -> Tuple[Chromosome, Chromosome]:
        child1 = parent1.copy()
        child2 = parent2.copy()
        
        v1 = parent1.get_gene_values()
        v2 = parent2.get_gene_values()
        
        alpha = random.random()
        
        child1_genes = [alpha * a + (1 - alpha) * b for a, b in zip(v1, v2)]
        child2_genes = [(1 - alpha) * a + alpha * b for a, b in zip(v1, v2)]
        
        child1.set_gene_values(child1_genes)
        child2.set_gene_values(child2_genes)
        
        child1.parent_ids = [parent1.chromosome_id, parent2.chromosome_id]
        child2.parent_ids = [parent1.chromosome_id, parent2.chromosome_id]
        
        return child1, child2


class MutationOperator:
    """变异操作器"""
    
    def __init__(
        self,
        mutation_type: MutationType = MutationType.GAUSSIAN,
        mutation_rate: float = 0.1,
        mutation_strength: float = 0.2
    ):
        self.mutation_type = mutation_type
        self.mutation_rate = mutation_rate
        self.mutation_strength = mutation_strength
    
    def mutate(self, chromosome: Chromosome) -> Chromosome:
        mutated = chromosome.copy()
        
        for gene in mutated.genes:
            if random.random() < self.mutation_rate:
                self._mutate_gene(gene)
        
        return mutated
    
    def _mutate_gene(self, gene: Gene):
        if self.mutation_type == MutationType.GAUSSIAN:
            delta = random.gauss(0, (gene.max_value - gene.min_value) * self.mutation_strength)
            gene.value = max(gene.min_value, min(gene.max_value, gene.value + delta))
        
        elif self.mutation_type == MutationType.UNIFORM:
            gene.value = random.uniform(gene.min_value, gene.max_value)
        
        elif self.mutation_type == MutationType.BIT_FLIP:
            mid = (gene.min_value + gene.max_value) / 2
            gene.value = gene.max_value if gene.value < mid else gene.min_value
        
        elif self.mutation_type == MutationType.SWAP:
            gene.value = gene.max_value - gene.value + gene.min_value


class GeneticEvolution:
    """遗传算法进化系统主控"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        self.population_size = self.config.get("population_size", 50)
        self.elite_ratio = self.config.get("elite_ratio", 0.2)
        self.mutation_rate = self.config.get("mutation_rate", 0.1)
        self.crossover_rate = self.config.get("crossover_rate", 0.8)
        
        self.selection = SelectionStrategy(
            method=SelectionMethod(self.config.get("selection_method", "tournament")),
            elite_ratio=self.elite_ratio,
            tournament_size=self.config.get("tournament_size", 3)
        )
        
        self.crossover = CrossoverOperator(
            crossover_type=CrossoverType(self.config.get("crossover_type", "uniform"))
        )
        
        self.mutation = MutationOperator(
            mutation_type=MutationType(self.config.get("mutation_type", "gaussian")),
            mutation_rate=self.mutation_rate,
            mutation_strength=self.config.get("mutation_strength", 0.2)
        )
        
        self.evolution_tree = EvolutionTree()
        
        self.current_population: Optional[Population] = None
        self.generation = 0
        
        self.fitness_function: Optional[Callable] = None
        
        self._lock = threading.Lock()
        
        self._running = False
        self._evolution_task = None
        
        self.stats = {
            "total_generations": 0,
            "total_evaluations": 0,
            "best_fitness_ever": 0.0,
            "improvements": 0,
        }
    
    def set_fitness_function(self, func: Callable):
        self.fitness_function = func
    
    def create_initial_population(
        self,
        gene_templates: List[Dict[str, Any]]
    ) -> Population:
        chromosomes = []
        
        for i in range(self.population_size):
            genes = []
            
            for template in gene_templates:
                gene = Gene(
                    gene_id=f"gene_{uuid.uuid4().hex[:8]}",
                    gene_type=GeneType(template.get("type", "parameter")),
                    name=template["name"],
                    value=random.uniform(template.get("min", 0), template.get("max", 1)),
                    min_value=template.get("min", 0),
                    max_value=template.get("max", 1),
                    mutation_rate=template.get("mutation_rate", self.mutation_rate),
                )
                genes.append(gene)
            
            chromosome = Chromosome(
                chromosome_id=f"chr_{uuid.uuid4().hex[:8]}",
                genes=genes,
                fitness=0.0,
                generation=0,
                parent_ids=[],
                created_at=datetime.now(),
            )
            
            chromosomes.append(chromosome)
        
        population = Population(
            population_id=f"pop_{int(time.time())}_{uuid.uuid4().hex[:8]}",
            chromosomes=chromosomes,
            generation=0,
            best_fitness=0.0,
            average_fitness=0.0,
            diversity=0.0,
            created_at=datetime.now(),
        )
        
        with self._lock:
            self.current_population = population
            self.generation = 0
        
        return population
    
    async def evaluate_population(
        self,
        population: Population
    ) -> Population:
        if not self.fitness_function:
            return population
        
        for chromosome in population.chromosomes:
            try:
                fitness = await self.fitness_function(chromosome.get_gene_values())
                chromosome.fitness = fitness
                chromosome.evaluation_count += 1
                self.stats["total_evaluations"] += 1
            except Exception as e:
                logger.error(f"Fitness evaluation error: {e}")
                chromosome.fitness = 0.0
        
        population.calculate_statistics()
        
        if population.best_fitness > self.stats["best_fitness_ever"]:
            self.stats["best_fitness_ever"] = population.best_fitness
            self.stats["improvements"] += 1
        
        return population
    
    def evolve_generation(self) -> Population:
        if not self.current_population:
            raise ValueError("No population to evolve")
        
        self.stats["total_generations"] += 1
        self.generation += 1
        
        elite_count = int(self.population_size * self.elite_ratio)
        elites = self.selection._elite_selection(self.current_population, elite_count)
        
        for elite in elites:
            self.evolution_tree.add_node(elite, elite.parent_ids, is_elite=True)
        
        offspring = []
        
        while len(offspring) < self.population_size - elite_count:
            parents = self.selection.select(self.current_population, 2)
            
            if random.random() < self.crossover_rate:
                child1, child2 = self.crossover.crossover(parents[0], parents[1])
            else:
                child1, child2 = parents[0].copy(), parents[1].copy()
            
            child1 = self.mutation.mutate(child1)
            child2 = self.mutation.mutate(child2)
            
            child1.generation = self.generation
            child2.generation = self.generation
            
            offspring.extend([child1, child2])
        
        offspring = offspring[:self.population_size - elite_count]
        
        for child in offspring:
            self.evolution_tree.add_node(child, child.parent_ids, is_elite=False)
        
        new_chromosomes = elites + offspring
        
        new_population = Population(
            population_id=f"pop_{int(time.time())}_{uuid.uuid4().hex[:8]}",
            chromosomes=new_chromosomes,
            generation=self.generation,
            best_fitness=0.0,
            average_fitness=0.0,
            diversity=0.0,
            created_at=datetime.now(),
        )
        
        with self._lock:
            self.current_population = new_population
        
        return new_population
    
    async def run_evolution(
        self,
        generations: int = 100,
        gene_templates: List[Dict[str, Any]] = None
    ) -> Chromosome:
        if gene_templates and not self.current_population:
            self.create_initial_population(gene_templates)
        
        if not self.current_population:
            raise ValueError("No population initialized")
        
        best_chromosome = None
        
        for gen in range(generations):
            self.current_population = await self.evaluate_population(self.current_population)
            
            sorted_chromosomes = sorted(
                self.current_population.chromosomes,
                key=lambda c: c.fitness,
                reverse=True
            )
            
            if best_chromosome is None or sorted_chromosomes[0].fitness > best_chromosome.fitness:
                best_chromosome = sorted_chromosomes[0].copy()
            
            if gen < generations - 1:
                self.evolve_generation()
        
        return best_chromosome
    
    async def start_continuous_evolution(self, interval: int = 86400):
        self._running = True
        self._evolution_task = asyncio.create_task(self._evolution_loop(interval))
    
    def stop_continuous_evolution(self):
        self._running = False
        if self._evolution_task:
            self._evolution_task.cancel()
    
    async def _evolution_loop(self, interval: int):
        while self._running:
            try:
                if self.current_population:
                    self.current_population = await self.evaluate_population(self.current_population)
                    self.evolve_generation()
                
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Evolution loop error: {e}")
                await asyncio.sleep(60)
    
    def get_best_chromosome(self) -> Optional[Chromosome]:
        if not self.current_population:
            return None
        
        return max(
            self.current_population.chromosomes,
            key=lambda c: c.fitness
        )
    
    def get_population_stats(self) -> Dict[str, Any]:
        if not self.current_population:
            return {}
        
        return {
            "generation": self.generation,
            "population_size": len(self.current_population.chromosomes),
            "best_fitness": self.current_population.best_fitness,
            "average_fitness": self.current_population.average_fitness,
            "diversity": self.current_population.diversity,
            "best_fitness_ever": self.stats["best_fitness_ever"],
        }
    
    def get_evolution_history(self, generations: int = 10) -> List[Dict[str, Any]]:
        history = []
        
        for gen in range(max(0, self.generation - generations), self.generation + 1):
            stats = self.evolution_tree.get_generation_stats(gen)
            history.append(stats)
        
        return history
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "genetic_evolution": self.stats,
            "evolution_tree": self.evolution_tree.stats,
            "population": self.get_population_stats(),
        }
