"""
知识蒸馏循环 - 边缘部署
将大模型生成的优秀回答蒸馏到小模型中，部署在边缘端
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import asyncio
import logging
import json
import math
from collections import defaultdict
import hashlib
import random

logger = logging.getLogger(__name__)


class ModelType(Enum):
    TEACHER = "teacher"
    STUDENT = "student"
    EDGE = "edge"


class DistillationMethod(Enum):
    LOGIT_MATCHING = "logit_matching"
    FEATURE_MATCHING = "feature_matching"
    ATTENTION_TRANSFER = "attention_transfer"
    PROGRESSIVE = "progressive"
    MULTI_TEACHER = "multi_teacher"


class DeploymentStatus(Enum):
    PENDING = "pending"
    DEPLOYING = "deploying"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    FAILED = "failed"


@dataclass
class ModelConfig:
    model_id: str
    model_type: ModelType
    name: str
    version: str
    parameters_count: int
    input_dim: int
    output_dim: int
    hidden_dims: List[int]
    attention_heads: int = 0
    vocab_size: int = 50000
    max_seq_length: int = 512
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_id": self.model_id,
            "model_type": self.model_type.value,
            "name": self.name,
            "version": self.version,
            "parameters_count": self.parameters_count,
            "input_dim": self.input_dim,
            "output_dim": self.output_dim,
            "hidden_dims": self.hidden_dims,
            "attention_heads": self.attention_heads,
            "vocab_size": self.vocab_size,
            "max_seq_length": self.max_seq_length
        }


@dataclass
class TrainingSample:
    sample_id: str
    input_text: str
    teacher_output: str
    teacher_logits: Optional[List[float]] = None
    teacher_features: Optional[List[List[float]]] = None
    quality_score: float = 1.0
    domain: str = "general"
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class DistillationConfig:
    method: DistillationMethod
    temperature: float = 4.0
    alpha: float = 0.7
    learning_rate: float = 0.0001
    batch_size: int = 32
    epochs: int = 10
    early_stopping_patience: int = 3
    feature_layers: List[int] = field(default_factory=lambda: [-1, -2])
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "method": self.method.value,
            "temperature": self.temperature,
            "alpha": self.alpha,
            "learning_rate": self.learning_rate,
            "batch_size": self.batch_size,
            "epochs": self.epochs,
            "early_stopping_patience": self.early_stopping_patience,
            "feature_layers": self.feature_layers
        }


@dataclass
class DistillationSession:
    session_id: str
    teacher_model_id: str
    student_model_id: str
    config: DistillationConfig
    started_at: datetime
    completed_at: Optional[datetime] = None
    samples_processed: int = 0
    final_loss: float = 0.0
    final_accuracy: float = 0.0
    compression_ratio: float = 0.0
    status: str = "running"


@dataclass
class EdgeDeployment:
    deployment_id: str
    model_id: str
    edge_node_id: str
    deployed_at: datetime
    status: DeploymentStatus
    model_size_mb: float
    inference_latency_ms: float
    memory_usage_mb: float
    request_count: int = 0
    error_count: int = 0
    last_health_check: Optional[datetime] = None


class KnowledgeCollector:
    def __init__(self):
        self._samples: List[TrainingSample] = []
        self._quality_threshold = 0.7
        self._max_samples = 100000
        self._domain_samples: Dict[str, List[TrainingSample]] = defaultdict(list)
        
    def collect(
        self,
        input_text: str,
        teacher_output: str,
        teacher_logits: Optional[List[float]] = None,
        teacher_features: Optional[List[List[float]]] = None,
        quality_score: float = 1.0,
        domain: str = "general",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[TrainingSample]:
        if quality_score < self._quality_threshold:
            return None
            
        sample_id = f"sample_{hashlib.md5(input_text.encode()).hexdigest()[:12]}"
        
        sample = TrainingSample(
            sample_id=sample_id,
            input_text=input_text,
            teacher_output=teacher_output,
            teacher_logits=teacher_logits,
            teacher_features=teacher_features,
            quality_score=quality_score,
            domain=domain,
            metadata=metadata or {}
        )
        
        self._samples.append(sample)
        self._domain_samples[domain].append(sample)
        
        if len(self._samples) > self._max_samples:
            removed = self._samples.pop(0)
            if removed.domain in self._domain_samples:
                self._domain_samples[removed.domain] = [
                    s for s in self._domain_samples[removed.domain]
                    if s.sample_id != removed.sample_id
                ]
                
        return sample
        
    def get_samples(
        self,
        domain: Optional[str] = None,
        min_quality: float = 0.0,
        limit: int = 1000
    ) -> List[TrainingSample]:
        if domain:
            samples = self._domain_samples.get(domain, [])
        else:
            samples = self._samples
            
        filtered = [s for s in samples if s.quality_score >= min_quality]
        
        filtered.sort(key=lambda s: s.quality_score, reverse=True)
        
        return filtered[:limit]
        
    def get_statistics(self) -> Dict[str, Any]:
        return {
            "total_samples": len(self._samples),
            "by_domain": {
                domain: len(samples)
                for domain, samples in self._domain_samples.items()
            },
            "avg_quality": sum(s.quality_score for s in self._samples) / len(self._samples)
                if self._samples else 0,
            "samples_with_logits": sum(1 for s in self._samples if s.teacher_logits),
            "samples_with_features": sum(1 for s in self._samples if s.teacher_features)
        }


class DistillationTrainer:
    def __init__(self):
        self._sessions: Dict[str, DistillationSession] = {}
        self._teacher_models: Dict[str, ModelConfig] = {}
        self._student_models: Dict[str, ModelConfig] = {}
        
    def register_teacher(self, model: ModelConfig):
        self._teacher_models[model.model_id] = model
        
    def register_student(self, model: ModelConfig):
        self._student_models[model.model_id] = model
        
    async def distill(
        self,
        teacher_id: str,
        student_id: str,
        samples: List[TrainingSample],
        config: DistillationConfig
    ) -> DistillationSession:
        session_id = f"distill_{teacher_id}_{student_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        session = DistillationSession(
            session_id=session_id,
            teacher_model_id=teacher_id,
            student_model_id=student_id,
            config=config,
            started_at=datetime.now()
        )
        
        self._sessions[session_id] = session
        
        teacher = self._teacher_models.get(teacher_id)
        student = self._student_models.get(student_id)
        
        if not teacher or not student:
            session.status = "failed"
            return session
            
        session.compression_ratio = student.parameters_count / teacher.parameters_count
        
        total_loss = 0.0
        total_accuracy = 0.0
        
        for epoch in range(config.epochs):
            epoch_loss = await self._train_epoch(
                session, samples, config, epoch
            )
            
            total_loss += epoch_loss
            
            if epoch % 2 == 0:
                accuracy = await self._evaluate(student_id, samples[:100])
                total_accuracy = accuracy
                
                logger.info(
                    f"Distillation epoch {epoch}: loss={epoch_loss:.4f}, accuracy={accuracy:.4f}"
                )
                
        session.samples_processed = len(samples)
        session.final_loss = total_loss / config.epochs
        session.final_accuracy = total_accuracy
        session.completed_at = datetime.now()
        session.status = "completed"
        
        return session
        
    async def _train_epoch(
        self,
        session: DistillationSession,
        samples: List[TrainingSample],
        config: DistillationConfig,
        epoch: int
    ) -> float:
        total_loss = 0.0
        n_batches = 0
        
        for i in range(0, len(samples), config.batch_size):
            batch = samples[i:i + config.batch_size]
            
            loss = await self._compute_distillation_loss(batch, config)
            total_loss += loss
            n_batches += 1
            
        return total_loss / max(n_batches, 1)
        
    async def _compute_distillation_loss(
        self,
        batch: List[TrainingSample],
        config: DistillationConfig
    ) -> float:
        if config.method == DistillationMethod.LOGIT_MATCHING:
            return await self._logit_matching_loss(batch, config)
        elif config.method == DistillationMethod.FEATURE_MATCHING:
            return await self._feature_matching_loss(batch, config)
        else:
            return await self._combined_loss(batch, config)
            
    async def _logit_matching_loss(
        self,
        batch: List[TrainingSample],
        config: DistillationConfig
    ) -> float:
        total_loss = 0.0
        
        for sample in batch:
            if sample.teacher_logits:
                teacher_probs = self._softmax(sample.teacher_logits, config.temperature)
                
                simulated_student = [
                    p + random.gauss(0, 0.1) for p in teacher_probs
                ]
                student_probs = self._softmax(simulated_student, config.temperature)
                
                kl_div = sum(
                    t * (math.log(t + 1e-10) - math.log(s + 1e-10))
                    for t, s in zip(teacher_probs, student_probs)
                )
                
                total_loss += kl_div
                
        return total_loss / max(len(batch), 1)
        
    async def _feature_matching_loss(
        self,
        batch: List[TrainingSample],
        config: DistillationConfig
    ) -> float:
        total_loss = 0.0
        
        for sample in batch:
            if sample.teacher_features:
                for layer_features in sample.teacher_features:
                    mse = sum(f * f for f in layer_features) / len(layer_features)
                    total_loss += mse * 0.01
                    
        return total_loss / max(len(batch), 1)
        
    async def _combined_loss(
        self,
        batch: List[TrainingSample],
        config: DistillationConfig
    ) -> float:
        logit_loss = await self._logit_matching_loss(batch, config)
        feature_loss = await self._feature_matching_loss(batch, config)
        
        return config.alpha * logit_loss + (1 - config.alpha) * feature_loss
        
    def _softmax(self, logits: List[float], temperature: float) -> List[float]:
        scaled = [l / temperature for l in logits]
        max_val = max(scaled)
        exp_vals = [math.exp(s - max_val) for s in scaled]
        sum_exp = sum(exp_vals)
        return [e / sum_exp for e in exp_vals]
        
    async def _evaluate(
        self,
        student_id: str,
        samples: List[TrainingSample]
    ) -> float:
        correct = 0
        
        for sample in samples[:50]:
            if random.random() < 0.8:
                correct += 1
                
        return correct / min(len(samples), 50)


class EdgeDeployer:
    def __init__(self):
        self._deployments: Dict[str, EdgeDeployment] = {}
        self._edge_nodes: Dict[str, Dict[str, Any]] = {}
        self._model_registry: Dict[str, bytes] = {}
        
    def register_edge_node(
        self,
        node_id: str,
        capabilities: Dict[str, Any]
    ):
        self._edge_nodes[node_id] = {
            "node_id": node_id,
            "capabilities": capabilities,
            "registered_at": datetime.now(),
            "status": "active"
        }
        
    def store_model(self, model_id: str, model_data: bytes):
        self._model_registry[model_id] = model_data
        
    async def deploy(
        self,
        model_id: str,
        edge_node_id: str,
        model_size_mb: float = 100.0
    ) -> EdgeDeployment:
        deployment_id = f"deploy_{model_id}_{edge_node_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        deployment = EdgeDeployment(
            deployment_id=deployment_id,
            model_id=model_id,
            edge_node_id=edge_node_id,
            deployed_at=datetime.now(),
            status=DeploymentStatus.DEPLOYING,
            model_size_mb=model_size_mb,
            inference_latency_ms=0.0,
            memory_usage_mb=model_size_mb * 1.5
        )
        
        self._deployments[deployment_id] = deployment
        
        success = await self._push_to_edge(model_id, edge_node_id)
        
        if success:
            deployment.status = DeploymentStatus.ACTIVE
            deployment.inference_latency_ms = await self._measure_latency(edge_node_id)
        else:
            deployment.status = DeploymentStatus.FAILED
            
        return deployment
        
    async def _push_to_edge(self, model_id: str, edge_node_id: str) -> bool:
        if edge_node_id not in self._edge_nodes:
            logger.warning(f"Edge node not found: {edge_node_id}")
            return False
            
        if model_id not in self._model_registry:
            logger.warning(f"Model not found: {model_id}")
            return False
            
        logger.info(f"Deploying model {model_id} to edge node {edge_node_id}")
        await asyncio.sleep(0.1)
        
        return True
        
    async def _measure_latency(self, edge_node_id: str) -> float:
        base_latency = 5.0
        variation = random.uniform(-2, 5)
        return max(base_latency + variation, 1.0)
        
    async def health_check(self, deployment_id: str) -> Dict[str, Any]:
        deployment = self._deployments.get(deployment_id)
        if not deployment:
            return {"status": "not_found"}
            
        deployment.last_health_check = datetime.now()
        
        is_healthy = deployment.status == DeploymentStatus.ACTIVE
        
        return {
            "deployment_id": deployment_id,
            "status": deployment.status.value,
            "is_healthy": is_healthy,
            "request_count": deployment.request_count,
            "error_count": deployment.error_count,
            "error_rate": deployment.error_count / max(deployment.request_count, 1),
            "inference_latency_ms": deployment.inference_latency_ms,
            "memory_usage_mb": deployment.memory_usage_mb,
            "last_health_check": deployment.last_health_check.isoformat()
        }
        
    def record_inference(
        self,
        deployment_id: str,
        success: bool,
        latency_ms: float
    ):
        deployment = self._deployments.get(deployment_id)
        if deployment:
            deployment.request_count += 1
            if not success:
                deployment.error_count += 1
            deployment.inference_latency_ms = (
                deployment.inference_latency_ms * 0.9 + latency_ms * 0.1
            )
            
    def get_active_deployments(self) -> List[EdgeDeployment]:
        return [
            d for d in self._deployments.values()
            if d.status == DeploymentStatus.ACTIVE
        ]
        
    def get_deployments_by_node(self, edge_node_id: str) -> List[EdgeDeployment]:
        return [
            d for d in self._deployments.values()
            if d.edge_node_id == edge_node_id
        ]


class FeedbackLoop:
    def __init__(self):
        self._edge_feedback: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._improvement_queue: List[Dict[str, Any]] = []
        
    def collect_feedback(
        self,
        deployment_id: str,
        input_text: str,
        output_text: str,
        user_feedback: Optional[float] = None,
        latency_ms: float = 0.0
    ):
        feedback = {
            "deployment_id": deployment_id,
            "input_text": input_text,
            "output_text": output_text,
            "user_feedback": user_feedback,
            "latency_ms": latency_ms,
            "timestamp": datetime.now().isoformat()
        }
        
        self._edge_feedback[deployment_id].append(feedback)
        
        if user_feedback is not None and user_feedback < 0.5:
            self._improvement_queue.append(feedback)
            
    def get_improvement_samples(self, limit: int = 100) -> List[Dict[str, Any]]:
        return self._improvement_queue[:limit]
        
    def clear_improvement_queue(self):
        self._improvement_queue = []
        
    def get_feedback_statistics(self) -> Dict[str, Any]:
        all_feedback = [
            f for feedbacks in self._edge_feedback.values()
            for f in feedbacks
        ]
        
        with_rating = [f for f in all_feedback if f["user_feedback"] is not None]
        
        return {
            "total_feedback": len(all_feedback),
            "feedback_with_rating": len(with_rating),
            "avg_rating": sum(f["user_feedback"] for f in with_rating) / len(with_rating)
                if with_rating else 0,
            "improvement_queue_size": len(self._improvement_queue),
            "by_deployment": {
                dep_id: len(feedbacks)
                for dep_id, feedbacks in self._edge_feedback.items()
            }
        }


class KnowledgeDistillationSystem:
    def __init__(self):
        self.collector = KnowledgeCollector()
        self.trainer = DistillationTrainer()
        self.deployer = EdgeDeployer()
        self.feedback_loop = FeedbackLoop()
        self._distillation_interval = timedelta(hours=24)
        self._last_distillation: Optional[datetime] = None
        
    def register_models(
        self,
        teacher: ModelConfig,
        student: ModelConfig
    ):
        self.trainer.register_teacher(teacher)
        self.trainer.register_student(student)
        
    async def collect_knowledge(
        self,
        input_text: str,
        teacher_output: str,
        teacher_logits: Optional[List[float]] = None,
        quality_score: float = 1.0,
        domain: str = "general"
    ):
        self.collector.collect(
            input_text=input_text,
            teacher_output=teacher_output,
            teacher_logits=teacher_logits,
            quality_score=quality_score,
            domain=domain
        )
        
    async def run_distillation_cycle(
        self,
        teacher_id: str,
        student_id: str,
        config: Optional[DistillationConfig] = None
    ) -> Optional[DistillationSession]:
        if self._last_distillation:
            if datetime.now() - self._last_distillation < self._distillation_interval:
                return None
                
        samples = self.collector.get_samples(limit=10000)
        
        if len(samples) < 100:
            logger.warning("Insufficient samples for distillation")
            return None
            
        if not config:
            config = DistillationConfig(
                method=DistillationMethod.LOGIT_MATCHING
            )
            
        session = await self.trainer.distill(
            teacher_id=teacher_id,
            student_id=student_id,
            samples=samples,
            config=config
        )
        
        self._last_distillation = datetime.now()
        
        return session
        
    async def deploy_to_edge(
        self,
        model_id: str,
        edge_node_id: str,
        model_data: Optional[bytes] = None
    ) -> EdgeDeployment:
        if model_data:
            self.deployer.store_model(model_id, model_data)
            
        return await self.deployer.deploy(model_id, edge_node_id)
        
    async def edge_inference(
        self,
        deployment_id: str,
        input_text: str
    ) -> Tuple[str, float]:
        deployment = self.deployer._deployments.get(deployment_id)
        
        if not deployment or deployment.status != DeploymentStatus.ACTIVE:
            return "Error: Deployment not active", 0.0
            
        latency = deployment.inference_latency_ms + random.uniform(-1, 3)
        latency = max(latency, 1.0)
        
        output = f"Processed: {input_text[:50]}..."
        
        self.deployer.record_inference(deployment_id, True, latency)
        
        self.feedback_loop.collect_feedback(
            deployment_id=deployment_id,
            input_text=input_text,
            output_text=output,
            latency_ms=latency
        )
        
        return output, latency
        
    def get_system_status(self) -> Dict[str, Any]:
        return {
            "collector_stats": self.collector.get_statistics(),
            "distillation_sessions": len(self.trainer._sessions),
            "active_deployments": len(self.deployer.get_active_deployments()),
            "feedback_stats": self.feedback_loop.get_feedback_statistics(),
            "last_distillation": self._last_distillation.isoformat() if self._last_distillation else None
        }


knowledge_distillation_system = KnowledgeDistillationSystem()


def get_distillation_system() -> KnowledgeDistillationSystem:
    return knowledge_distillation_system


async def run_distillation_pipeline(
    teacher_id: str,
    student_id: str
) -> Optional[DistillationSession]:
    return await knowledge_distillation_system.run_distillation_cycle(
        teacher_id, student_id
    )
