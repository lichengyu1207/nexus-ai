"""
样本驱动进化
将数据采集与知识蒸馏接入进化引擎
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class EvolutionMetric(str, Enum):
    DATA_UTILIZATION = "data_utilization"
    LEARNING_EFFICIENCY = "learning_efficiency"
    SAMPLE_QUALITY_SENSITIVITY = "sample_quality_sensitivity"
    ADAPTATION_SPEED = "adaptation_speed"


class FitnessComponent(str, Enum):
    COLLECTION_ABILITY = "collection_ability"
    DISTILLATION_ABILITY = "distillation_ability"
    SAMPLE_EFFICIENCY = "sample_efficiency"
    KNOWLEDGE_TRANSFER = "knowledge_transfer"


class AgentDataProfile(BaseModel):
    agent_id: str
    samples_collected: int = 0
    samples_used: int = 0
    distillation_count: int = 0
    knowledge_transfers: int = 0
    avg_sample_quality: float = 0.5
    learning_improvements: float = 0.0
    data_utilization_rate: float = 0.0
    last_updated: datetime = Field(default_factory=datetime.now)


class EvolutionScore(BaseModel):
    agent_id: str
    total_score: float = 0.0
    components: Dict[str, float] = Field(default_factory=dict)
    rank: int = 0
    reproduction_probability: float = 0.0
    calculated_at: datetime = Field(default_factory=datetime.now)


class DataEvolutionGene(BaseModel):
    gene_id: str = Field(default_factory=lambda: str(uuid4()))
    agent_id: str
    collection_strategies: Dict[str, float] = Field(default_factory=dict)
    distillation_preferences: Dict[str, float] = Field(default_factory=dict)
    sample_selection_criteria: Dict[str, Any] = Field(default_factory=dict)
    learning_parameters: Dict[str, float] = Field(default_factory=dict)
    fitness_history: List[float] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)


class DataUtilizationEvaluator:
    def __init__(self):
        self.utilization_history: Dict[str, List[float]] = {}
    
    def evaluate(
        self,
        samples_collected: int,
        samples_used: int,
        quality_improvements: float
    ) -> float:
        if samples_collected == 0:
            return 0.0
        
        utilization_rate = samples_used / samples_collected
        
        effectiveness = min(1.0, quality_improvements / 10)
        
        score = utilization_rate * 0.6 + effectiveness * 0.4
        
        return min(1.0, score)
    
    def record_utilization(self, agent_id: str, score: float):
        if agent_id not in self.utilization_history:
            self.utilization_history[agent_id] = []
        self.utilization_history[agent_id].append(score)


class LearningEfficiencyEvaluator:
    def __init__(self):
        self.learning_records: Dict[str, List[Dict[str, Any]]] = {}
    
    def evaluate(
        self,
        distillation_count: int,
        avg_improvement: float,
        energy_consumed: float
    ) -> float:
        if distillation_count == 0:
            return 0.5
        
        improvement_score = min(1.0, avg_improvement * 5)
        
        efficiency_score = 1.0 - min(1.0, energy_consumed / (distillation_count * 100 + 1))
        
        return improvement_score * 0.7 + efficiency_score * 0.3
    
    def record_learning(
        self,
        agent_id: str,
        improvement: float,
        energy: float
    ):
        if agent_id not in self.learning_records:
            self.learning_records[agent_id] = []
        
        self.learning_records[agent_id].append({
            "improvement": improvement,
            "energy": energy,
            "timestamp": datetime.now().isoformat()
        })


class SampleQualitySensitivityEvaluator:
    def __init__(self):
        self.quality_sensitivity: Dict[str, float] = {}
    
    def evaluate(
        self,
        quality_improvements: Dict[float, float]
    ) -> float:
        if not quality_improvements:
            return 0.5
        
        sorted_qualities = sorted(quality_improvements.keys())
        
        if len(sorted_qualities) < 2:
            return 0.5
        
        low_quality = sorted_qualities[0]
        high_quality = sorted_qualities[-1]
        
        low_improvement = quality_improvements[low_quality]
        high_improvement = quality_improvements[high_quality]
        
        sensitivity = high_improvement - low_improvement
        
        return min(1.0, max(0.0, sensitivity * 2 + 0.5))


class SampleDrivenEvolution:
    def __init__(
        self,
        evolution_engine: Optional[Any] = None,
        sample_repository: Optional[Any] = None,
        distillation_system: Optional[Any] = None,
        energy_manager: Optional[Any] = None
    ):
        self.evolution_engine = evolution_engine
        self.sample_repository = sample_repository
        self.distillation_system = distillation_system
        self.energy_manager = energy_manager
        
        self.utilization_evaluator = DataUtilizationEvaluator()
        self.efficiency_evaluator = LearningEfficiencyEvaluator()
        self.sensitivity_evaluator = SampleQualitySensitivityEvaluator()
        
        self.agent_profiles: Dict[str, AgentDataProfile] = {}
        self.evolution_genes: Dict[str, DataEvolutionGene] = {}
        self.evolution_scores: Dict[str, EvolutionScore] = {}
        
        self.component_weights = {
            FitnessComponent.COLLECTION_ABILITY: 0.25,
            FitnessComponent.DISTILLATION_ABILITY: 0.30,
            FitnessComponent.SAMPLE_EFFICIENCY: 0.25,
            FitnessComponent.KNOWLEDGE_TRANSFER: 0.20
        }
        
        self.evolution_interval = timedelta(hours=24)
        self._running = False
        
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self):
        self.logger.info("SampleDrivenEvolution initialized")
    
    async def register_agent(
        self,
        agent_id: str,
        initial_gene: Optional[DataEvolutionGene] = None
    ):
        self.agent_profiles[agent_id] = AgentDataProfile(agent_id=agent_id)
        
        if initial_gene:
            self.evolution_genes[agent_id] = initial_gene
        else:
            self.evolution_genes[agent_id] = DataEvolutionGene(
                agent_id=agent_id,
                collection_strategies={
                    "web": 0.25,
                    "api": 0.25,
                    "user_interaction": 0.25,
                    "agent_interaction": 0.25
                },
                distillation_preferences={
                    "response": 0.4,
                    "feature": 0.3,
                    "experience": 0.3
                },
                sample_selection_criteria={
                    "min_quality": 0.5,
                    "diversity_weight": 0.3
                },
                learning_parameters={
                    "learning_rate": 0.001,
                    "batch_size": 32
                }
            )
    
    async def record_collection(
        self,
        agent_id: str,
        samples_count: int,
        avg_quality: float
    ):
        if agent_id not in self.agent_profiles:
            await self.register_agent(agent_id)
        
        profile = self.agent_profiles[agent_id]
        profile.samples_collected += samples_count
        
        total_quality = profile.avg_sample_quality * (profile.samples_collected - samples_count)
        profile.avg_sample_quality = (total_quality + avg_quality * samples_count) / profile.samples_collected
        
        profile.last_updated = datetime.now()
    
    async def record_sample_usage(
        self,
        agent_id: str,
        samples_used: int,
        quality_improvement: float
    ):
        if agent_id not in self.agent_profiles:
            return
        
        profile = self.agent_profiles[agent_id]
        profile.samples_used += samples_used
        profile.learning_improvements += quality_improvement
        
        if profile.samples_collected > 0:
            profile.data_utilization_rate = profile.samples_used / profile.samples_collected
    
    async def record_distillation(
        self,
        agent_id: str,
        success: bool,
        performance_gain: float,
        energy_consumed: float
    ):
        if agent_id not in self.agent_profiles:
            return
        
        profile = self.agent_profiles[agent_id]
        profile.distillation_count += 1
        
        self.efficiency_evaluator.record_learning(
            agent_id,
            performance_gain if success else 0,
            energy_consumed
        )
    
    async def record_knowledge_transfer(
        self,
        agent_id: str,
        as_teacher: bool,
        success: bool
    ):
        if agent_id not in self.agent_profiles:
            return
        
        profile = self.agent_profiles[agent_id]
        profile.knowledge_transfers += 1
    
    async def calculate_evolution_score(self, agent_id: str) -> EvolutionScore:
        if agent_id not in self.agent_profiles:
            return EvolutionScore(agent_id=agent_id)
        
        profile = self.agent_profiles[agent_id]
        
        collection_score = self._calculate_collection_score(profile)
        
        distillation_score = self._calculate_distillation_score(profile)
        
        efficiency_score = self._calculate_efficiency_score(profile)
        
        transfer_score = self._calculate_transfer_score(profile)
        
        components = {
            FitnessComponent.COLLECTION_ABILITY.value: collection_score,
            FitnessComponent.DISTILLATION_ABILITY.value: distillation_score,
            FitnessComponent.SAMPLE_EFFICIENCY.value: efficiency_score,
            FitnessComponent.KNOWLEDGE_TRANSFER.value: transfer_score
        }
        
        total_score = sum(
            components[comp.value] * weight
            for comp, weight in self.component_weights.items()
        )
        
        score = EvolutionScore(
            agent_id=agent_id,
            total_score=total_score,
            components=components
        )
        
        self.evolution_scores[agent_id] = score
        
        if agent_id in self.evolution_genes:
            self.evolution_genes[agent_id].fitness_history.append(total_score)
        
        return score
    
    def _calculate_collection_score(self, profile: AgentDataProfile) -> float:
        if profile.samples_collected == 0:
            return 0.0
        
        volume_score = min(1.0, profile.samples_collected / 1000)
        
        quality_score = profile.avg_sample_quality
        
        return volume_score * 0.4 + quality_score * 0.6
    
    def _calculate_distillation_score(self, profile: AgentDataProfile) -> float:
        if profile.distillation_count == 0:
            return 0.5
        
        improvement_per_distillation = profile.learning_improvements / profile.distillation_count
        
        return min(1.0, improvement_per_distillation * 10)
    
    def _calculate_efficiency_score(self, profile: AgentDataProfile) -> float:
        return self.utilization_evaluator.evaluate(
            profile.samples_collected,
            profile.samples_used,
            profile.learning_improvements
        )
    
    def _calculate_transfer_score(self, profile: AgentDataProfile) -> float:
        if profile.knowledge_transfers == 0:
            return 0.5
        
        transfer_score = min(1.0, profile.knowledge_transfers / 10)
        
        return transfer_score
    
    async def rank_agents(self) -> List[EvolutionScore]:
        scores = []
        
        for agent_id in self.agent_profiles:
            score = await self.calculate_evolution_score(agent_id)
            scores.append(score)
        
        scores.sort(key=lambda x: x.total_score, reverse=True)
        
        for i, score in enumerate(scores):
            score.rank = i + 1
            
            if len(scores) > 1:
                score.reproduction_probability = 1.0 - (i / (len(scores) - 1))
            else:
                score.reproduction_probability = 1.0
        
        return scores
    
    async def evolve_gene(
        self,
        parent_id: str,
        child_id: str,
        mutation_rate: float = 0.1
    ) -> DataEvolutionGene:
        if parent_id not in self.evolution_genes:
            await self.register_agent(parent_id)
        
        parent_gene = self.evolution_genes[parent_id]
        
        import random
        import copy
        
        child_strategies = copy.deepcopy(parent_gene.collection_strategies)
        for key in child_strategies:
            if random.random() < mutation_rate:
                child_strategies[key] = max(0.1, min(0.5, child_strategies[key] + random.gauss(0, 0.1)))
        
        total = sum(child_strategies.values())
        for key in child_strategies:
            child_strategies[key] /= total
        
        child_preferences = copy.deepcopy(parent_gene.distillation_preferences)
        for key in child_preferences:
            if random.random() < mutation_rate:
                child_preferences[key] = max(0.1, min(0.5, child_preferences[key] + random.gauss(0, 0.1)))
        
        total = sum(child_preferences.values())
        for key in child_preferences:
            child_preferences[key] /= total
        
        child_criteria = copy.deepcopy(parent_gene.sample_selection_criteria)
        for key in child_criteria:
            if random.random() < mutation_rate:
                if isinstance(child_criteria[key], float):
                    child_criteria[key] = max(0.1, min(0.9, child_criteria[key] + random.gauss(0, 0.1)))
        
        child_params = copy.deepcopy(parent_gene.learning_parameters)
        for key in child_params:
            if random.random() < mutation_rate:
                if key == "learning_rate":
                    child_params[key] = max(0.0001, min(0.01, child_params[key] * (1 + random.gauss(0, 0.2))))
                elif key == "batch_size":
                    child_params[key] = max(8, min(128, int(child_params[key] * (1 + random.gauss(0, 0.2)))))
        
        child_gene = DataEvolutionGene(
            agent_id=child_id,
            collection_strategies=child_strategies,
            distillation_preferences=child_preferences,
            sample_selection_criteria=child_criteria,
            learning_parameters=child_params
        )
        
        self.evolution_genes[child_id] = child_gene
        await self.register_agent(child_id, child_gene)
        
        return child_gene
    
    async def get_best_collectors(self, top_n: int = 5) -> List[str]:
        scores = await self.rank_agents()
        
        collection_scores = []
        for score in scores:
            collection_ability = score.components.get(
                FitnessComponent.COLLECTION_ABILITY.value, 0
            )
            collection_scores.append((score.agent_id, collection_ability))
        
        collection_scores.sort(key=lambda x: x[1], reverse=True)
        
        return [agent_id for agent_id, _ in collection_scores[:top_n]]
    
    async def get_best_distillers(self, top_n: int = 5) -> List[str]:
        scores = await self.rank_agents()
        
        distillation_scores = []
        for score in scores:
            distillation_ability = score.components.get(
                FitnessComponent.DISTILLATION_ABILITY.value, 0
            )
            distillation_scores.append((score.agent_id, distillation_ability))
        
        distillation_scores.sort(key=lambda x: x[1], reverse=True)
        
        return [agent_id for agent_id, _ in distillation_scores[:top_n]]
    
    async def integrate_with_evolution_engine(self):
        if not self.evolution_engine:
            return
        
        try:
            scores = await self.rank_agents()
            
            for score in scores:
                await self.evolution_engine.update_fitness(
                    score.agent_id,
                    "data_capability",
                    score.total_score
                )
            
            best_collectors = await self.get_best_collectors(3)
            for agent_id in best_collectors:
                await self.evolution_engine.increase_reproduction_probability(
                    agent_id,
                    0.1
                )
            
            self.logger.info("Integrated data evolution with evolution engine")
            
        except Exception as e:
            self.logger.error(f"Error integrating with evolution engine: {e}")
    
    async def start_evolution_loop(self):
        self._running = True
        asyncio.create_task(self._evolution_loop())
    
    async def stop_evolution_loop(self):
        self._running = False
    
    async def _evolution_loop(self):
        while self._running:
            try:
                await self.integrate_with_evolution_engine()
                
                await asyncio.sleep(self.evolution_interval.total_seconds())
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in evolution loop: {e}")
                await asyncio.sleep(3600)
    
    def get_statistics(self) -> Dict[str, Any]:
        total_samples_collected = sum(
            p.samples_collected for p in self.agent_profiles.values()
        )
        total_samples_used = sum(
            p.samples_used for p in self.agent_profiles.values()
        )
        total_distillations = sum(
            p.distillation_count for p in self.agent_profiles.values()
        )
        
        return {
            "registered_agents": len(self.agent_profiles),
            "total_samples_collected": total_samples_collected,
            "total_samples_used": total_samples_used,
            "total_distillations": total_distillations,
            "global_utilization_rate": total_samples_used / total_samples_collected if total_samples_collected > 0 else 0,
            "evolution_genes_count": len(self.evolution_genes)
        }
    
    def get_agent_profile(self, agent_id: str) -> Optional[Dict[str, Any]]:
        if agent_id not in self.agent_profiles:
            return None
        
        profile = self.agent_profiles[agent_id]
        score = self.evolution_scores.get(agent_id)
        gene = self.evolution_genes.get(agent_id)
        
        return {
            "agent_id": agent_id,
            "samples_collected": profile.samples_collected,
            "samples_used": profile.samples_used,
            "distillation_count": profile.distillation_count,
            "knowledge_transfers": profile.knowledge_transfers,
            "avg_sample_quality": profile.avg_sample_quality,
            "data_utilization_rate": profile.data_utilization_rate,
            "evolution_score": score.total_score if score else 0,
            "evolution_rank": score.rank if score else 0,
            "gene": {
                "collection_strategies": gene.collection_strategies if gene else {},
                "distillation_preferences": gene.distillation_preferences if gene else {}
            }
        }
    
    def get_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        sorted_scores = sorted(
            self.evolution_scores.values(),
            key=lambda x: x.total_score,
            reverse=True
        )
        
        return [
            {
                "rank": i + 1,
                "agent_id": score.agent_id,
                "total_score": score.total_score,
                "components": score.components,
                "reproduction_probability": score.reproduction_probability
            }
            for i, score in enumerate(sorted_scores[:limit])
        ]
