"""
知识蒸馏智能体基类
从各种来源提炼知识，生成可用的策略或模型
"""
import asyncio
import json
import logging
from abc import abstractmethod
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class DistillationStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DistillationMethod(str, Enum):
    RESPONSE_DISTILLATION = "response_distillation"
    FEATURE_DISTILLATION = "feature_distillation"
    RELATION_DISTILLATION = "relation_distillation"
    BEHAVIOR_CLONING = "behavior_cloning"
    INVERSE_REINFORCEMENT = "inverse_reinforcement"
    PATTERN_MINING = "pattern_mining"


class KnowledgeType(str, Enum):
    MODEL_PARAMETERS = "model_parameters"
    RULES = "rules"
    DECISION_TREE = "decision_tree"
    HEURISTICS = "heuristics"
    EMBEDDINGS = "embeddings"
    SAMPLES = "samples"


class DistillationResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    status: DistillationStatus = DistillationStatus.PENDING
    method: DistillationMethod
    knowledge_type: KnowledgeType
    teacher_model: Optional[str] = None
    student_model: Optional[str] = None
    samples_used: int = 0
    training_time: float = 0.0
    performance_before: Optional[float] = None
    performance_after: Optional[float] = None
    performance_gain: float = 0.0
    knowledge_artifact: Optional[Dict[str, Any]] = None
    metrics: Dict[str, float] = Field(default_factory=dict)
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


class SampleSelection:
    def __init__(
        self,
        sample_repository: Optional[Any] = None,
        quality_threshold: float = 0.5,
        diversity_weight: float = 0.3
    ):
        self.sample_repository = sample_repository
        self.quality_threshold = quality_threshold
        self.diversity_weight = diversity_weight
        self.selection_history: List[Dict[str, Any]] = []
    
    async def select_samples(
        self,
        sample_type: str,
        batch_size: int,
        strategy: str = "balanced"
    ) -> List[Dict[str, Any]]:
        if not self.sample_repository:
            return []
        
        from .sample_repository import SampleQuery, SampleType
        
        try:
            query = SampleQuery(
                types=[SampleType(sample_type)] if sample_type else None,
                min_quality=self.quality_threshold,
                limit=batch_size * 2,
                order_by="quality",
                order_desc=True
            )
            
            samples = await self.sample_repository.query(query)
            
            if strategy == "balanced":
                samples = self._balance_selection(samples, batch_size)
            elif strategy == "diverse":
                samples = self._diversify_selection(samples, batch_size)
            elif strategy == "hard":
                samples = await self._select_hard_samples(samples, batch_size)
            else:
                samples = samples[:batch_size]
            
            self.selection_history.append({
                "sample_type": sample_type,
                "batch_size": batch_size,
                "strategy": strategy,
                "selected_count": len(samples),
                "timestamp": datetime.now().isoformat()
            })
            
            return [
                {
                    "id": s.id,
                    "content": s.content,
                    "quality": s.quality,
                    "tags": s.tags
                }
                for s in samples
            ]
            
        except Exception as e:
            logger.error(f"Error selecting samples: {e}")
            return []
    
    def _balance_selection(
        self,
        samples: List[Any],
        batch_size: int
    ) -> List[Any]:
        if len(samples) <= batch_size:
            return samples
        
        quality_buckets = {
            "high": [],
            "medium": [],
            "low": []
        }
        
        for sample in samples:
            if sample.quality >= 0.7:
                quality_buckets["high"].append(sample)
            elif sample.quality >= 0.4:
                quality_buckets["medium"].append(sample)
            else:
                quality_buckets["low"].append(sample)
        
        per_bucket = batch_size // 3
        remainder = batch_size % 3
        
        selected = []
        for bucket_name, bucket_samples in quality_buckets.items():
            count = per_bucket + (1 if remainder > 0 and bucket_name == "high" else 0)
            selected.extend(bucket_samples[:count])
            if remainder > 0 and bucket_name == "high":
                remainder -= 1
        
        return selected[:batch_size]
    
    def _diversify_selection(
        self,
        samples: List[Any],
        batch_size: int
    ) -> List[Any]:
        if len(samples) <= batch_size:
            return samples
        
        selected = [samples[0]]
        
        for sample in samples[1:]:
            if len(selected) >= batch_size:
                break
            
            min_distance = float('inf')
            for selected_sample in selected:
                distance = self._compute_distance(sample, selected_sample)
                min_distance = min(min_distance, distance)
            
            if min_distance > 0.3:
                selected.append(sample)
        
        while len(selected) < batch_size and len(samples) > len(selected):
            for sample in samples:
                if sample not in selected:
                    selected.append(sample)
                    break
        
        return selected[:batch_size]
    
    async def _select_hard_samples(
        self,
        samples: List[Any],
        batch_size: int
    ) -> List[Any]:
        return samples[:batch_size]
    
    def _compute_distance(self, sample1: Any, sample2: Any) -> float:
        tags1 = set(sample1.tags)
        tags2 = set(sample2.tags)
        
        if not tags1 and not tags2:
            return 0.0
        
        intersection = len(tags1 & tags2)
        union = len(tags1 | tags2)
        
        jaccard = intersection / union if union > 0 else 0.0
        
        return 1.0 - jaccard


class ModelRegistry:
    def __init__(self):
        self.models: Dict[str, Dict[str, Any]] = {}
        self.model_versions: Dict[str, List[str]] = {}
    
    def register_model(
        self,
        model_id: str,
        model_type: str,
        parameters: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.models[model_id] = {
            "id": model_id,
            "type": model_type,
            "parameters": parameters,
            "metadata": metadata or {},
            "registered_at": datetime.now().isoformat(),
            "performance": None
        }
        
        base_id = model_id.rsplit("_v", 1)[0] if "_v" in model_id else model_id
        if base_id not in self.model_versions:
            self.model_versions[base_id] = []
        self.model_versions[base_id].append(model_id)
    
    def get_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        return self.models.get(model_id)
    
    def get_latest_version(self, base_model_id: str) -> Optional[str]:
        versions = self.model_versions.get(base_model_id, [])
        if not versions:
            return None
        return versions[-1]
    
    def update_performance(self, model_id: str, performance: float):
        if model_id in self.models:
            self.models[model_id]["performance"] = performance
            self.models[model_id]["performance_updated_at"] = datetime.now().isoformat()
    
    def list_models(self, model_type: Optional[str] = None) -> List[Dict[str, Any]]:
        models = list(self.models.values())
        if model_type:
            models = [m for m in models if m["type"] == model_type]
        return models


class KnowledgeDistillerAgent:
    def __init__(
        self,
        agent_id: str,
        name: str = "KnowledgeDistiller",
        sample_repository: Optional[Any] = None,
        model_registry: Optional[ModelRegistry] = None,
        energy_manager: Optional[Any] = None,
        **kwargs
    ):
        self.agent_id = agent_id
        self.name = name
        self.sample_repository = sample_repository
        self.model_registry = model_registry or ModelRegistry()
        self.energy_manager = energy_manager
        
        self.sample_selector = SampleSelection(sample_repository)
        
        self.distillation_rate = timedelta(hours=24)
        self.sample_batch_size = 1000
        self.performance_gain_threshold = 0.05
        
        self.distillation_history: List[DistillationResult] = []
        self.active_distillations: Dict[str, DistillationResult] = {}
        
        self._running = False
        self._distillation_task: Optional[asyncio.Task] = None
        
        self.logger = logging.getLogger(f"{__name__}.{agent_id}")
    
    async def initialize(self):
        self.logger.info(f"KnowledgeDistillerAgent {self.agent_id} initialized")
    
    @abstractmethod
    async def distill(
        self,
        samples: List[Dict[str, Any]],
        method: DistillationMethod,
        config: Optional[Dict[str, Any]] = None
    ) -> DistillationResult:
        pass
    
    @abstractmethod
    async def evaluate(
        self,
        model_id: str,
        test_samples: List[Dict[str, Any]]
    ) -> float:
        pass
    
    async def select_samples(
        self,
        sample_type: str,
        strategy: str = "balanced"
    ) -> List[Dict[str, Any]]:
        return await self.sample_selector.select_samples(
            sample_type=sample_type,
            batch_size=self.sample_batch_size,
            strategy=strategy
        )
    
    async def execute_distillation_cycle(
        self,
        sample_type: str,
        method: DistillationMethod,
        config: Optional[Dict[str, Any]] = None
    ) -> DistillationResult:
        result = DistillationResult(
            method=method,
            knowledge_type=KnowledgeType.MODEL_PARAMETERS
        )
        
        try:
            self.active_distillations[result.id] = result
            result.status = DistillationStatus.RUNNING
            
            energy_cost = self._estimate_energy_cost(method, self.sample_batch_size)
            if self.energy_manager:
                can_proceed = await self.energy_manager.consume(
                    self.agent_id,
                    energy_cost,
                    "distillation"
                )
                if not can_proceed:
                    result.status = DistillationStatus.FAILED
                    result.error_message = "Insufficient energy"
                    return result
            
            samples = await self.select_samples(sample_type)
            if not samples:
                result.status = DistillationStatus.FAILED
                result.error_message = "No samples available"
                return result
            
            result.samples_used = len(samples)
            
            distillation_result = await self.distill(samples, method, config)
            
            result.status = distillation_result.status
            result.knowledge_artifact = distillation_result.knowledge_artifact
            result.metrics = distillation_result.metrics
            result.performance_before = distillation_result.performance_before
            result.performance_after = distillation_result.performance_after
            result.performance_gain = distillation_result.performance_gain
            result.completed_at = datetime.now()
            
            if result.status == DistillationStatus.COMPLETED:
                await self._handle_successful_distillation(result)
            else:
                await self._handle_failed_distillation(result)
            
        except Exception as e:
            self.logger.error(f"Distillation cycle failed: {e}")
            result.status = DistillationStatus.FAILED
            result.error_message = str(e)
            await self._handle_failed_distillation(result)
        
        finally:
            self.distillation_history.append(result)
            if result.id in self.active_distillations:
                del self.active_distillations[result.id]
        
        return result
    
    async def _handle_successful_distillation(self, result: DistillationResult):
        if self.energy_manager and result.performance_gain > self.performance_gain_threshold:
            reward = result.performance_gain * 100
            await self.energy_manager.reward(self.agent_id, reward, "successful_distillation")
        
        if result.knowledge_artifact:
            model_id = f"distilled_{result.id}"
            self.model_registry.register_model(
                model_id=model_id,
                model_type=result.knowledge_type.value,
                parameters=result.knowledge_artifact,
                metadata={
                    "distillation_method": result.method.value,
                    "samples_used": result.samples_used,
                    "performance_gain": result.performance_gain
                }
            )
            result.student_model = model_id
        
        self.logger.info(
            f"Distillation completed: {result.id}, "
            f"performance gain: {result.performance_gain:.4f}"
        )
    
    async def _handle_failed_distillation(self, result: DistillationResult):
        if self.energy_manager:
            penalty = 10
            await self.energy_manager.consume(
                self.agent_id,
                penalty,
                "failed_distillation_penalty"
            )
        
        self.logger.warning(
            f"Distillation failed: {result.id}, "
            f"error: {result.error_message}"
        )
    
    def _estimate_energy_cost(
        self,
        method: DistillationMethod,
        sample_count: int
    ) -> float:
        base_costs = {
            DistillationMethod.RESPONSE_DISTILLATION: 1.0,
            DistillationMethod.FEATURE_DISTILLATION: 2.0,
            DistillationMethod.RELATION_DISTILLATION: 1.5,
            DistillationMethod.BEHAVIOR_CLONING: 0.5,
            DistillationMethod.INVERSE_REINFORCEMENT: 3.0,
            DistillationMethod.PATTERN_MINING: 0.3
        }
        
        base_cost = base_costs.get(method, 1.0)
        sample_factor = sample_count / 1000
        
        return base_cost * sample_factor * 10
    
    async def publish_model(self, model_id: str) -> bool:
        model = self.model_registry.get_model(model_id)
        if not model:
            return False
        
        self.logger.info(f"Publishing model: {model_id}")
        return True
    
    async def adapt(self, result: DistillationResult):
        if result.performance_gain > 0.1:
            self.sample_batch_size = min(5000, int(self.sample_batch_size * 1.1))
        elif result.performance_gain < 0:
            self.sample_batch_size = max(100, int(self.sample_batch_size * 0.9))
        
        if result.status == DistillationStatus.FAILED:
            self.distillation_rate = min(
                timedelta(hours=48),
                self.distillation_rate * 2
            )
        elif result.performance_gain > self.performance_gain_threshold:
            self.distillation_rate = max(
                timedelta(hours=6),
                self.distillation_rate / 2
            )
    
    async def start_continuous_distillation(self):
        if self._running:
            return
        
        self._running = True
        self._distillation_task = asyncio.create_task(self._distillation_loop())
    
    async def stop_continuous_distillation(self):
        self._running = False
        if self._distillation_task:
            self._distillation_task.cancel()
            try:
                await self._distillation_task
            except asyncio.CancelledError:
                pass
    
    async def _distillation_loop(self):
        while self._running:
            try:
                result = await self.execute_distillation_cycle(
                    sample_type="text",
                    method=DistillationMethod.RESPONSE_DISTILLATION
                )
                
                await self.adapt(result)
                
                await asyncio.sleep(self.distillation_rate.total_seconds())
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in distillation loop: {e}")
                await asyncio.sleep(300)
    
    def get_statistics(self) -> Dict[str, Any]:
        successful = [r for r in self.distillation_history if r.status == DistillationStatus.COMPLETED]
        failed = [r for r in self.distillation_history if r.status == DistillationStatus.FAILED]
        
        avg_gain = 0.0
        if successful:
            avg_gain = sum(r.performance_gain for r in successful) / len(successful)
        
        return {
            "total_distillations": len(self.distillation_history),
            "successful": len(successful),
            "failed": len(failed),
            "average_performance_gain": avg_gain,
            "active_distillations": len(self.active_distillations),
            "sample_batch_size": self.sample_batch_size,
            "distillation_rate_hours": self.distillation_rate.total_seconds() / 3600,
            "registered_models": len(self.model_registry.models)
        }
    
    def get_distillation_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        return [
            {
                "id": r.id,
                "status": r.status.value,
                "method": r.method.value,
                "samples_used": r.samples_used,
                "performance_gain": r.performance_gain,
                "created_at": r.created_at.isoformat(),
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
                "error": r.error_message
            }
            for r in self.distillation_history[-limit:]
        ]
