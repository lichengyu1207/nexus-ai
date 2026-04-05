"""
大模型知识蒸馏智能体
从大语言模型蒸馏知识到小模型
"""
import asyncio
import json
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from pydantic import BaseModel, Field

from .knowledge_distiller import (
    KnowledgeDistillerAgent,
    DistillationResult,
    DistillationStatus,
    DistillationMethod,
    KnowledgeType
)

logger = logging.getLogger(__name__)


class TeacherModel(str, Enum):
    GPT4 = "gpt-4"
    CLAUDE = "claude"
    WENXIN = "wenxin"
    QWEN = "qwen"
    LOCAL_LLM = "local_llm"


class StudentModelConfig(BaseModel):
    model_type: str = "transformer"
    hidden_size: int = 256
    num_layers: int = 4
    num_heads: int = 4
    vocab_size: int = 32000
    max_length: int = 512
    dropout: float = 0.1


class DistillationConfig(BaseModel):
    teacher_model: TeacherModel = TeacherModel.GPT4
    temperature: float = 2.0
    alpha: float = 0.5
    learning_rate: float = 1e-4
    epochs: int = 3
    batch_size: int = 32
    max_tokens: int = 512


class TeacherResponse(BaseModel):
    content: str
    log_probs: Optional[List[float]] = None
    hidden_states: Optional[List[List[float]]] = None
    attention_weights: Optional[List[List[List[float]]]] = None
    confidence: float = 1.0


class TeacherModelInterface:
    def __init__(self, model_type: TeacherModel, api_key: Optional[str] = None):
        self.model_type = model_type
        self.api_key = api_key
        self.request_count = 0
        self.total_tokens = 0
    
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        return_logits: bool = False
    ) -> TeacherResponse:
        self.request_count += 1
        
        response_content = f"[Distilled knowledge from {self.model_type.value}] Response to: {prompt[:100]}..."
        self.total_tokens += len(prompt.split()) + len(response_content.split())
        
        return TeacherResponse(
            content=response_content,
            confidence=0.85
        )
    
    async def batch_generate(
        self,
        prompts: List[str],
        max_tokens: int = 512,
        temperature: float = 0.7
    ) -> List[TeacherResponse]:
        responses = []
        for prompt in prompts:
            response = await self.generate(prompt, max_tokens, temperature)
            responses.append(response)
        return responses
    
    def get_usage_stats(self) -> Dict[str, Any]:
        return {
            "model_type": self.model_type.value,
            "request_count": self.request_count,
            "total_tokens": self.total_tokens
        }


class StudentModelInterface:
    def __init__(self, config: StudentModelConfig):
        self.config = config
        self.parameters: Dict[str, Any] = {}
        self.optimizer_state: Dict[str, Any] = {}
        self.training_step = 0
        self._initialize_parameters()
    
    def _initialize_parameters(self):
        import random
        random.seed(42)
        
        self.parameters = {
            "embedding": {
                "weight": [[random.gauss(0, 0.02) for _ in range(self.config.hidden_size)]
                          for _ in range(self.config.vocab_size)]
            },
            "layers": [
                {
                    "attention": {
                        "query_weight": [[random.gauss(0, 0.02) for _ in range(self.config.hidden_size)]
                                       for _ in range(self.config.hidden_size)],
                        "key_weight": [[random.gauss(0, 0.02) for _ in range(self.config.hidden_size)]
                                     for _ in range(self.config.hidden_size)],
                        "value_weight": [[random.gauss(0, 0.02) for _ in range(self.config.hidden_size)]
                                       for _ in range(self.config.hidden_size)]
                    },
                    "ffn": {
                        "weight": [[random.gauss(0, 0.02) for _ in range(self.config.hidden_size * 4)]
                                 for _ in range(self.config.hidden_size)]
                    }
                }
                for _ in range(self.config.num_layers)
            ],
            "output": {
                "weight": [[random.gauss(0, 0.02) for _ in range(self.config.vocab_size)]
                          for _ in range(self.config.hidden_size)]
            }
        }
    
    async def forward(self, input_ids: List[int]) -> Tuple[List[float], List[List[float]]]:
        self.training_step += 1
        
        logits = [0.1 * (i % 10) for i in range(self.config.vocab_size)]
        hidden_states = [[0.01 * j for j in range(self.config.hidden_size)]
                        for _ in range(len(input_ids))]
        
        return logits, hidden_states
    
    async def train_step(
        self,
        input_ids: List[int],
        teacher_logits: List[float],
        teacher_hidden: Optional[List[List[float]]] = None,
        config: Optional[DistillationConfig] = None
    ) -> Dict[str, float]:
        config = config or DistillationConfig()
        
        student_logits, student_hidden = await self.forward(input_ids)
        
        kl_loss = self._compute_kl_divergence(
            student_logits,
            teacher_logits,
            config.temperature
        )
        
        ce_loss = 0.5
        
        if teacher_hidden and student_hidden:
            hidden_loss = self._compute_hidden_loss(student_hidden, teacher_hidden)
        else:
            hidden_loss = 0.0
        
        total_loss = (
            config.alpha * kl_loss +
            (1 - config.alpha) * ce_loss +
            0.1 * hidden_loss
        )
        
        self._update_parameters(total_loss, config.learning_rate)
        
        return {
            "total_loss": total_loss,
            "kl_loss": kl_loss,
            "ce_loss": ce_loss,
            "hidden_loss": hidden_loss
        }
    
    def _compute_kl_divergence(
        self,
        student_logits: List[float],
        teacher_logits: List[float],
        temperature: float
    ) -> float:
        import math
        
        student_probs = self._softmax([l / temperature for l in student_logits])
        teacher_probs = self._softmax([l / temperature for l in teacher_logits])
        
        kl_div = 0.0
        for s, t in zip(student_probs, teacher_probs):
            if t > 0 and s > 0:
                kl_div += t * math.log(t / s)
        
        return kl_div
    
    def _compute_hidden_loss(
        self,
        student_hidden: List[List[float]],
        teacher_hidden: List[List[float]]
    ) -> float:
        if len(student_hidden) != len(teacher_hidden):
            return 1.0
        
        total_loss = 0.0
        for s_h, t_h in zip(student_hidden, teacher_hidden):
            for s, t in zip(s_h, t_h):
                total_loss += (s - t) ** 2
        
        return total_loss / (len(student_hidden) * len(student_hidden[0])) if student_hidden else 0.0
    
    def _softmax(self, logits: List[float]) -> List[float]:
        import math
        max_logit = max(logits)
        exp_logits = [math.exp(l - max_logit) for l in logits]
        sum_exp = sum(exp_logits)
        return [e / sum_exp for e in exp_logits]
    
    def _update_parameters(self, loss: float, learning_rate: float):
        pass
    
    def get_parameters(self) -> Dict[str, Any]:
        return self.parameters
    
    def set_parameters(self, parameters: Dict[str, Any]):
        self.parameters = parameters


class ActiveLearningSelector:
    def __init__(
        self,
        uncertainty_threshold: float = 0.3,
        diversity_weight: float = 0.3
    ):
        self.uncertainty_threshold = uncertainty_threshold
        self.diversity_weight = diversity_weight
        self.sample_uncertainties: Dict[str, float] = {}
    
    async def select_uncertain_samples(
        self,
        samples: List[Dict[str, Any]],
        student_model: StudentModelInterface,
        budget: int
    ) -> List[Dict[str, Any]]:
        uncertain_samples = []
        
        for sample in samples:
            content = sample.get("content", {})
            text = content.get("text", "") or content.get("query", "")
            
            if text:
                input_ids = [hash(text) % 32000]
                logits, _ = await student_model.forward(input_ids)
                
                uncertainty = self._compute_uncertainty(logits)
                self.sample_uncertainties[sample["id"]] = uncertainty
                
                if uncertainty > self.uncertainty_threshold:
                    sample["_uncertainty"] = uncertainty
                    uncertain_samples.append(sample)
        
        uncertain_samples.sort(key=lambda x: x.get("_uncertainty", 0), reverse=True)
        
        return uncertain_samples[:budget]
    
    def _compute_uncertainty(self, logits: List[float]) -> float:
        import math
        
        probs = self._softmax(logits[:100])
        
        entropy = 0.0
        for p in probs:
            if p > 0:
                entropy -= p * math.log(p)
        
        max_entropy = math.log(len(probs))
        
        return entropy / max_entropy if max_entropy > 0 else 0.0
    
    def _softmax(self, logits: List[float]) -> List[float]:
        import math
        max_logit = max(logits) if logits else 0
        exp_logits = [math.exp(l - max_logit) for l in logits]
        sum_exp = sum(exp_logits) if exp_logits else 1
        return [e / sum_exp for e in exp_logits]


class LLMDistillerAgent(KnowledgeDistillerAgent):
    def __init__(
        self,
        agent_id: str,
        name: str = "LLMDistiller",
        sample_repository: Optional[Any] = None,
        model_registry: Optional[Any] = None,
        energy_manager: Optional[Any] = None,
        teacher_models: Optional[Dict[TeacherModel, str]] = None,
        student_config: Optional[StudentModelConfig] = None,
        **kwargs
    ):
        super().__init__(
            agent_id=agent_id,
            name=name,
            sample_repository=sample_repository,
            model_registry=model_registry,
            energy_manager=energy_manager,
            **kwargs
        )
        
        self.teacher_interfaces: Dict[TeacherModel, TeacherModelInterface] = {}
        if teacher_models:
            for model_type, api_key in teacher_models.items():
                self.teacher_interfaces[model_type] = TeacherModelInterface(model_type, api_key)
        
        if not self.teacher_interfaces:
            self.teacher_interfaces[TeacherModel.LOCAL_LLM] = TeacherModelInterface(TeacherModel.LOCAL_LLM)
        
        self.student_config = student_config or StudentModelConfig()
        self.student_model = StudentModelInterface(self.student_config)
        
        self.active_learner = ActiveLearningSelector()
        
        self.task_teacher_mapping: Dict[str, TeacherModel] = {
            "valuation": TeacherModel.GPT4,
            "legal": TeacherModel.CLAUDE,
            "general": TeacherModel.LOCAL_LLM,
            "creative": TeacherModel.GPT4
        }
    
    async def distill(
        self,
        samples: List[Dict[str, Any]],
        method: DistillationMethod,
        config: Optional[Dict[str, Any]] = None
    ) -> DistillationResult:
        result = DistillationResult(
            method=method,
            knowledge_type=KnowledgeType.MODEL_PARAMETERS
        )
        
        try:
            distill_config = DistillationConfig(**config) if config else DistillationConfig()
            
            teacher = self._select_teacher(samples, distill_config)
            result.teacher_model = teacher.model_type.value
            
            performance_before = await self._evaluate_student(samples[:100])
            result.performance_before = performance_before
            
            if method == DistillationMethod.RESPONSE_DISTILLATION:
                await self._response_distillation(samples, teacher, distill_config)
            elif method == DistillationMethod.FEATURE_DISTILLATION:
                await self._feature_distillation(samples, teacher, distill_config)
            elif method == DistillationMethod.RELATION_DISTILLATION:
                await self._relation_distillation(samples, teacher, distill_config)
            
            performance_after = await self._evaluate_student(samples[:100])
            result.performance_after = performance_after
            result.performance_gain = performance_after - performance_before
            
            result.knowledge_artifact = self.student_model.get_parameters()
            result.status = DistillationStatus.COMPLETED
            result.completed_at = datetime.now()
            
        except Exception as e:
            self.logger.error(f"LLM distillation failed: {e}")
            result.status = DistillationStatus.FAILED
            result.error_message = str(e)
        
        return result
    
    def _select_teacher(
        self,
        samples: List[Dict[str, Any]],
        config: DistillationConfig
    ) -> TeacherModelInterface:
        if config.teacher_model in self.teacher_interfaces:
            return self.teacher_interfaces[config.teacher_model]
        
        task_types = set()
        for sample in samples:
            tags = sample.get("tags", [])
            for tag in tags:
                if tag in self.task_teacher_mapping:
                    task_types.add(tag)
        
        if task_types:
            primary_task = list(task_types)[0]
            preferred_teacher = self.task_teacher_mapping.get(primary_task, TeacherModel.LOCAL_LLM)
            if preferred_teacher in self.teacher_interfaces:
                return self.teacher_interfaces[preferred_teacher]
        
        return list(self.teacher_interfaces.values())[0]
    
    async def _response_distillation(
        self,
        samples: List[Dict[str, Any]],
        teacher: TeacherModelInterface,
        config: DistillationConfig
    ):
        self.logger.info(f"Starting response distillation with {len(samples)} samples")
        
        for epoch in range(config.epochs):
            total_loss = 0.0
            
            for i in range(0, len(samples), config.batch_size):
                batch = samples[i:i + config.batch_size]
                
                prompts = []
                for sample in batch:
                    content = sample.get("content", {})
                    prompt = content.get("text", "") or content.get("query", "") or json.dumps(content)
                    prompts.append(prompt)
                
                teacher_responses = await teacher.batch_generate(
                    prompts,
                    max_tokens=config.max_tokens,
                    temperature=config.temperature
                )
                
                for sample, response in zip(batch, teacher_responses):
                    text = sample.get("content", {}).get("text", "") or sample.get("content", {}).get("query", "")
                    input_ids = [hash(text) % 32000]
                    
                    teacher_logits = self._mock_logits_from_response(response)
                    
                    losses = await self.student_model.train_step(
                        input_ids,
                        teacher_logits,
                        config=config
                    )
                    total_loss += losses["total_loss"]
            
            avg_loss = total_loss / len(samples)
            self.logger.info(f"Epoch {epoch + 1}/{config.epochs}, Average loss: {avg_loss:.4f}")
    
    async def _feature_distillation(
        self,
        samples: List[Dict[str, Any]],
        teacher: TeacherModelInterface,
        config: DistillationConfig
    ):
        self.logger.info(f"Starting feature distillation with {len(samples)} samples")
        
        await self._response_distillation(samples, teacher, config)
    
    async def _relation_distillation(
        self,
        samples: List[Dict[str, Any]],
        teacher: TeacherModelInterface,
        config: DistillationConfig
    ):
        self.logger.info(f"Starting relation distillation with {len(samples)} samples")
        
        sample_pairs = []
        for i in range(0, len(samples) - 1, 2):
            sample_pairs.append((samples[i], samples[i + 1]))
        
        for sample1, sample2 in sample_pairs[:10]:
            text1 = sample1.get("content", {}).get("text", "")
            text2 = sample2.get("content", {}).get("text", "")
            
            prompt = f"Compare these two texts and describe their relationship:\n1. {text1[:100]}\n2. {text2[:100]}"
            await teacher.generate(prompt)
        
        await self._response_distillation(samples, teacher, config)
    
    def _mock_logits_from_response(self, response: TeacherResponse) -> List[float]:
        logits = []
        for i, char in enumerate(response.content[:100]):
            logits.append(ord(char) * 0.01 * response.confidence)
        
        while len(logits) < 32000:
            logits.append(0.0)
        
        return logits[:32000]
    
    async def _evaluate_student(self, samples: List[Dict[str, Any]]) -> float:
        correct = 0
        total = len(samples)
        
        for sample in samples:
            text = sample.get("content", {}).get("text", "") or sample.get("content", {}).get("query", "")
            if text:
                input_ids = [hash(text) % 32000]
                logits, _ = await self.student_model.forward(input_ids)
                
                if max(logits) > 0.5:
                    correct += 1
        
        return correct / total if total > 0 else 0.0
    
    async def distill_with_active_learning(
        self,
        initial_samples: List[Dict[str, Any]],
        total_budget: int = 1000,
        iterations: int = 5
    ) -> DistillationResult:
        result = DistillationResult(
            method=DistillationMethod.RESPONSE_DISTILLATION,
            knowledge_type=KnowledgeType.MODEL_PARAMETERS
        )
        
        try:
            samples_per_iter = total_budget // iterations
            current_samples = initial_samples[:samples_per_iter]
            
            for iteration in range(iterations):
                self.logger.info(f"Active learning iteration {iteration + 1}/{iterations}")
                
                iter_result = await self.distill(
                    current_samples,
                    DistillationMethod.RESPONSE_DISTILLATION
                )
                
                if iter_result.status != DistillationStatus.COMPLETED:
                    result.status = iter_result.status
                    result.error_message = iter_result.error_message
                    return result
                
                if iteration < iterations - 1:
                    remaining_samples = initial_samples[samples_per_iter * (iteration + 1):]
                    uncertain_samples = await self.active_learner.select_uncertain_samples(
                        remaining_samples,
                        self.student_model,
                        samples_per_iter
                    )
                    
                    if uncertain_samples:
                        current_samples = uncertain_samples
                    else:
                        current_samples = remaining_samples[:samples_per_iter]
            
            result.knowledge_artifact = self.student_model.get_parameters()
            result.status = DistillationStatus.COMPLETED
            result.completed_at = datetime.now()
            result.samples_used = total_budget
            
        except Exception as e:
            self.logger.error(f"Active learning distillation failed: {e}")
            result.status = DistillationStatus.FAILED
            result.error_message = str(e)
        
        return result
    
    async def evaluate(self, model_id: str, test_samples: List[Dict[str, Any]]) -> float:
        return await self._evaluate_student(test_samples)
    
    async def get_teacher_usage(self) -> Dict[str, Any]:
        usage = {}
        for model_type, interface in self.teacher_interfaces.items():
            usage[model_type.value] = interface.get_usage_stats()
        return usage
    
    def get_statistics(self) -> Dict[str, Any]:
        stats = super().get_statistics()
        stats["student_config"] = self.student_config.dict()
        stats["teacher_usage"] = {m.value: i.request_count for m, i in self.teacher_interfaces.items()}
        return stats
