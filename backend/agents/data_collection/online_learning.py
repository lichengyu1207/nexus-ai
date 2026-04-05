"""
智能体在线学习接口
使智能体能够利用新样本实时更新策略
"""
import asyncio
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class LearningTrigger(str, Enum):
    PULL = "pull"
    PUSH = "push"
    SCHEDULED = "scheduled"
    THRESHOLD = "threshold"


class LearningStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class LearningConfig(BaseModel):
    learning_rate: float = 0.001
    batch_size: int = 32
    epochs: int = 1
    momentum: float = 0.9
    weight_decay: float = 0.0001
    gradient_clip: float = 1.0
    early_stopping_patience: int = 5
    validation_split: float = 0.1


class LearningSession(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid4()))
    agent_id: str
    trigger: LearningTrigger
    samples_count: int = 0
    status: LearningStatus = LearningStatus.PENDING
    config: LearningConfig = Field(default_factory=LearningConfig)
    metrics: Dict[str, float] = Field(default_factory=dict)
    old_model_version: Optional[str] = None
    new_model_version: Optional[str] = None
    performance_before: Optional[float] = None
    performance_after: Optional[float] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class ModelVersion(BaseModel):
    version_id: str
    agent_id: str
    created_at: datetime
    performance: float
    sample_count: int
    parent_version: Optional[str] = None
    is_active: bool = False


class IncrementalLearner(ABC):
    @abstractmethod
    async def partial_fit(
        self,
        samples: List[Dict[str, Any]],
        config: LearningConfig
    ) -> Dict[str, float]:
        pass
    
    @abstractmethod
    async def evaluate(
        self,
        samples: List[Dict[str, Any]]
    ) -> float:
        pass
    
    @abstractmethod
    def get_parameters(self) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def set_parameters(self, parameters: Dict[str, Any]):
        pass


class MockIncrementalLearner(IncrementalLearner):
    def __init__(self):
        self.parameters: Dict[str, Any] = {}
        self.training_step = 0
    
    async def partial_fit(
        self,
        samples: List[Dict[str, Any]],
        config: LearningConfig
    ) -> Dict[str, float]:
        self.training_step += 1
        
        import random
        loss = 1.0 / (1 + self.training_step * 0.1) + random.uniform(-0.05, 0.05)
        loss = max(0.1, loss)
        
        accuracy = min(0.95, 0.5 + self.training_step * 0.02)
        
        return {
            "loss": loss,
            "accuracy": accuracy,
            "samples_processed": len(samples)
        }
    
    async def evaluate(self, samples: List[Dict[str, Any]]) -> float:
        return min(0.95, 0.5 + self.training_step * 0.02)
    
    def get_parameters(self) -> Dict[str, Any]:
        return {"step": self.training_step, "params": self.parameters}
    
    def set_parameters(self, parameters: Dict[str, Any]):
        self.parameters = parameters.get("params", {})
        self.training_step = parameters.get("step", 0)


class OnlineGradientDescent(IncrementalLearner):
    def __init__(self, learning_rate: float = 0.01):
        self.learning_rate = learning_rate
        self.weights: Dict[str, float] = {}
        self.bias: float = 0.0
    
    async def partial_fit(
        self,
        samples: List[Dict[str, Any]],
        config: LearningConfig
    ) -> Dict[str, float]:
        total_loss = 0.0
        
        for sample in samples:
            features = self._extract_features(sample)
            label = sample.get("label", sample.get("reward", 0))
            
            prediction = self._forward(features)
            error = label - prediction
            
            for key, value in features.items():
                if key not in self.weights:
                    self.weights[key] = 0.0
                self.weights[key] += config.learning_rate * error * value
            
            self.bias += config.learning_rate * error
            
            total_loss += error ** 2
        
        avg_loss = total_loss / len(samples) if samples else 0
        
        return {
            "loss": avg_loss,
            "samples_processed": len(samples)
        }
    
    async def evaluate(self, samples: List[Dict[str, Any]]) -> float:
        if not samples:
            return 0.0
        
        correct = 0
        for sample in samples:
            features = self._extract_features(sample)
            label = sample.get("label", sample.get("reward", 0))
            
            prediction = self._forward(features)
            
            if abs(prediction - label) < 0.5:
                correct += 1
        
        return correct / len(samples)
    
    def _extract_features(self, sample: Dict[str, Any]) -> Dict[str, float]:
        features = {}
        
        content = sample.get("content", {})
        
        def extract_from_dict(d: Dict[str, Any], prefix: str = ""):
            for key, value in d.items():
                full_key = f"{prefix}{key}" if prefix else key
                if isinstance(value, (int, float)):
                    features[full_key] = float(value)
                elif isinstance(value, bool):
                    features[full_key] = 1.0 if value else 0.0
                elif isinstance(value, dict):
                    extract_from_dict(value, f"{full_key}.")
        
        extract_from_dict(content)
        
        return features
    
    def _forward(self, features: Dict[str, float]) -> float:
        result = self.bias
        for key, value in features.items():
            result += self.weights.get(key, 0.0) * value
        return result
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            "weights": self.weights,
            "bias": self.bias,
            "learning_rate": self.learning_rate
        }
    
    def set_parameters(self, parameters: Dict[str, Any]):
        self.weights = parameters.get("weights", {})
        self.bias = parameters.get("bias", 0.0)
        self.learning_rate = parameters.get("learning_rate", self.learning_rate)


class VersionController:
    def __init__(self, max_versions: int = 10):
        self.max_versions = max_versions
        self.versions: Dict[str, List[ModelVersion]] = {}
        self.active_versions: Dict[str, str] = {}
    
    def save_version(
        self,
        agent_id: str,
        parameters: Dict[str, Any],
        performance: float,
        sample_count: int,
        parent_version: Optional[str] = None
    ) -> str:
        version_id = f"v_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{agent_id}"
        
        version = ModelVersion(
            version_id=version_id,
            agent_id=agent_id,
            created_at=datetime.now(),
            performance=performance,
            sample_count=sample_count,
            parent_version=parent_version
        )
        
        if agent_id not in self.versions:
            self.versions[agent_id] = []
        
        self.versions[agent_id].append(version)
        
        if len(self.versions[agent_id]) > self.max_versions:
            old_versions = self.versions[agent_id][:-self.max_versions]
            for old in old_versions:
                if old.version_id == self.active_versions.get(agent_id):
                    continue
        
        return version_id
    
    def set_active_version(self, agent_id: str, version_id: str) -> bool:
        if agent_id not in self.versions:
            return False
        
        for version in self.versions[agent_id]:
            if version.version_id == version_id:
                version.is_active = True
                self.active_versions[agent_id] = version_id
                return True
        
        return False
    
    def get_active_version(self, agent_id: str) -> Optional[ModelVersion]:
        version_id = self.active_versions.get(agent_id)
        if not version_id:
            return None
        
        for version in self.versions.get(agent_id, []):
            if version.version_id == version_id:
                return version
        
        return None
    
    def rollback(self, agent_id: str) -> Optional[str]:
        versions = self.versions.get(agent_id, [])
        if len(versions) < 2:
            return None
        
        current_active = self.active_versions.get(agent_id)
        
        for i, version in enumerate(reversed(versions)):
            if version.version_id == current_active:
                if i + 1 < len(versions):
                    previous = versions[-(i + 2)]
                    self.set_active_version(agent_id, previous.version_id)
                    return previous.version_id
                break
        
        return None


class OnlineLearningInterface:
    def __init__(
        self,
        agent_id: str,
        learner: Optional[IncrementalLearner] = None,
        energy_manager: Optional[Any] = None,
        sample_distribution: Optional[Any] = None,
        sample_repository: Optional[Any] = None
    ):
        self.agent_id = agent_id
        self.learner = learner or MockIncrementalLearner()
        self.energy_manager = energy_manager
        self.sample_distribution = sample_distribution
        self.sample_repository = sample_repository
        
        self.version_controller = VersionController()
        
        self.default_config = LearningConfig()
        
        self.learning_sessions: List[LearningSession] = []
        self.active_session: Optional[LearningSession] = None
        
        self.learning_threshold = 100
        self.pending_samples: List[Dict[str, Any]] = []
        
        self._running = False
        
        self.logger = logging.getLogger(f"{__name__}.{agent_id}")
    
    async def initialize(self):
        current_params = self.learner.get_parameters()
        version_id = self.version_controller.save_version(
            self.agent_id,
            current_params,
            0.5,
            0
        )
        self.version_controller.set_active_version(self.agent_id, version_id)
        
        self.logger.info(f"OnlineLearningInterface {self.agent_id} initialized")
    
    async def pull_samples(
        self,
        sample_types: List[str],
        quantity: int = 100,
        min_quality: float = 0.5
    ) -> List[Dict[str, Any]]:
        if not self.sample_distribution:
            return []
        
        from .sample_distribution import SampleRequest, DistributionMode
        
        request = SampleRequest(
            agent_id=self.agent_id,
            sample_types=sample_types,
            quantity=quantity,
            min_quality=min_quality,
            mode=DistributionMode.PULL
        )
        
        batch = await self.sample_distribution.request_samples(request)
        
        return batch.samples
    
    async def receive_pushed_samples(self, samples: List[Dict[str, Any]]):
        self.pending_samples.extend(samples)
        
        if len(self.pending_samples) >= self.learning_threshold:
            await self.trigger_learning(LearningTrigger.THRESHOLD)
    
    async def trigger_learning(
        self,
        trigger: LearningTrigger = LearningTrigger.PULL,
        config: Optional[LearningConfig] = None
    ) -> LearningSession:
        session = LearningSession(
            agent_id=self.agent_id,
            trigger=trigger,
            config=config or self.default_config
        )
        
        self.active_session = session
        session.status = LearningStatus.RUNNING
        session.started_at = datetime.now()
        
        try:
            old_params = self.learner.get_parameters()
            old_version = self.version_controller.get_active_version(self.agent_id)
            session.old_model_version = old_version.version_id if old_version else None
            
            performance_before = await self.learner.evaluate(self.pending_samples[:100])
            session.performance_before = performance_before
            
            samples_to_learn = self.pending_samples[:config.batch_size * config.epochs] if config else self.pending_samples
            session.samples_count = len(samples_to_learn)
            
            energy_cost = self._estimate_energy_cost(len(samples_to_learn))
            if self.energy_manager:
                can_proceed = await self.energy_manager.consume(
                    self.agent_id,
                    energy_cost,
                    "online_learning"
                )
                if not can_proceed:
                    session.status = LearningStatus.FAILED
                    session.error_message = "Insufficient energy"
                    return session
            
            metrics = await self.learner.partial_fit(
                samples_to_learn,
                session.config
            )
            session.metrics = metrics
            
            performance_after = await self.learner.evaluate(self.pending_samples[:100])
            session.performance_after = performance_after
            
            if performance_after >= performance_before:
                new_params = self.learner.get_parameters()
                new_version_id = self.version_controller.save_version(
                    self.agent_id,
                    new_params,
                    performance_after,
                    len(samples_to_learn),
                    session.old_model_version
                )
                self.version_controller.set_active_version(self.agent_id, new_version_id)
                session.new_model_version = new_version_id
                
                self.pending_samples = self.pending_samples[len(samples_to_learn):]
            else:
                self.learner.set_parameters(old_params)
                session.status = LearningStatus.ROLLED_BACK
                self.logger.warning(
                    f"Learning rolled back: performance degraded "
                    f"({performance_before:.4f} -> {performance_after:.4f})"
                )
            
            session.status = LearningStatus.COMPLETED
            session.completed_at = datetime.now()
            
        except Exception as e:
            self.logger.error(f"Learning session failed: {e}")
            session.status = LearningStatus.FAILED
            session.error_message = str(e)
        
        finally:
            self.learning_sessions.append(session)
            self.active_session = None
        
        return session
    
    def _estimate_energy_cost(self, sample_count: int) -> float:
        return sample_count * 0.01
    
    async def rollback_model(self) -> bool:
        previous_version = self.version_controller.rollback(self.agent_id)
        
        if previous_version:
            self.logger.info(f"Rolled back to version {previous_version}")
            return True
        
        return False
    
    async def request_distillation(
        self,
        distiller_agent: Any,
        sample_types: List[str]
    ) -> Optional[str]:
        samples = await self.pull_samples(sample_types, quantity=1000)
        
        if not samples:
            return None
        
        from .knowledge_distiller import DistillationMethod
        
        result = await distiller_agent.execute_distillation_cycle(
            sample_type=sample_types[0] if sample_types else "text",
            method=DistillationMethod.RESPONSE_DISTILLATION
        )
        
        if result.status.value == "completed" and result.knowledge_artifact:
            self.learner.set_parameters(result.knowledge_artifact)
            return result.id
        
        return None
    
    async def start_continuous_learning(self, interval_seconds: int = 300):
        self._running = True
        asyncio.create_task(self._continuous_learning_loop(interval_seconds))
    
    async def stop_continuous_learning(self):
        self._running = False
    
    async def _continuous_learning_loop(self, interval_seconds: int):
        while self._running:
            try:
                if len(self.pending_samples) >= self.learning_threshold:
                    await self.trigger_learning(LearningTrigger.SCHEDULED)
                
                await asyncio.sleep(interval_seconds)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in continuous learning loop: {e}")
                await asyncio.sleep(60)
    
    def get_statistics(self) -> Dict[str, Any]:
        completed_sessions = [s for s in self.learning_sessions if s.status == LearningStatus.COMPLETED]
        
        avg_improvement = 0.0
        if completed_sessions:
            improvements = [
                (s.performance_after or 0) - (s.performance_before or 0)
                for s in completed_sessions
                if s.performance_before is not None and s.performance_after is not None
            ]
            if improvements:
                avg_improvement = sum(improvements) / len(improvements)
        
        return {
            "total_sessions": len(self.learning_sessions),
            "completed_sessions": len(completed_sessions),
            "pending_samples": len(self.pending_samples),
            "learning_threshold": self.learning_threshold,
            "average_improvement": avg_improvement,
            "current_version": self.version_controller.get_active_version(self.agent_id).version_id
            if self.version_controller.get_active_version(self.agent_id) else None,
            "active_session": self.active_session.session_id if self.active_session else None
        }
    
    def get_learning_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        return [
            {
                "session_id": s.session_id,
                "trigger": s.trigger.value,
                "samples_count": s.samples_count,
                "status": s.status.value,
                "performance_before": s.performance_before,
                "performance_after": s.performance_after,
                "started_at": s.started_at.isoformat() if s.started_at else None,
                "completed_at": s.completed_at.isoformat() if s.completed_at else None
            }
            for s in self.learning_sessions[-limit:]
        ]
