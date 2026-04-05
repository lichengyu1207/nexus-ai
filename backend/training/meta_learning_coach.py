"""
元学习框架 - 教练智能体
监控所有业务智能体表现，自动调整训练超参数或触发重新训练
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import asyncio
import logging
import json
from collections import defaultdict
import math

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    HEALTHY = "healthy"
    DEGRADING = "degrading"
    CRITICAL = "critical"
    RECOVERING = "recovering"
    TRAINING = "training"


class TrainingTrigger(Enum):
    PERFORMANCE_DROP = "performance_drop"
    SCHEDULED = "scheduled"
    FEEDBACK_ACCUMULATED = "feedback_accumulated"
    CONCEPT_DRIFT = "concept_drift"
    MANUAL = "manual"


class HyperparameterType(Enum):
    LEARNING_RATE = "learning_rate"
    BATCH_SIZE = "batch_size"
    EPOCHS = "epochs"
    HIDDEN_DIM = "hidden_dim"
    DROPOUT = "dropout"
    REGULARIZATION = "regularization"


@dataclass
class AgentMetrics:
    agent_id: str
    timestamp: datetime
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    latency_ms: float
    error_rate: float
    user_satisfaction: float
    task_completion_rate: float
    memory_usage_mb: float
    cpu_usage_percent: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "timestamp": self.timestamp.isoformat(),
            "accuracy": self.accuracy,
            "precision": self.precision,
            "recall": self.recall,
            "f1_score": self.f1_score,
            "latency_ms": self.latency_ms,
            "error_rate": self.error_rate,
            "user_satisfaction": self.user_satisfaction,
            "task_completion_rate": self.task_completion_rate,
            "memory_usage_mb": self.memory_usage_mb,
            "cpu_usage_percent": self.cpu_usage_percent
        }


@dataclass
class HyperparameterConfig:
    learning_rate: float = 0.001
    batch_size: int = 32
    epochs: int = 10
    hidden_dim: int = 256
    dropout: float = 0.1
    regularization: float = 0.01
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "learning_rate": self.learning_rate,
            "batch_size": self.batch_size,
            "epochs": self.epochs,
            "hidden_dim": self.hidden_dim,
            "dropout": self.dropout,
            "regularization": self.regularization
        }


@dataclass
class TrainingSession:
    session_id: str
    agent_id: str
    trigger: TrainingTrigger
    started_at: datetime
    completed_at: Optional[datetime] = None
    initial_metrics: Optional[AgentMetrics] = None
    final_metrics: Optional[AgentMetrics] = None
    hyperparameters: Optional[HyperparameterConfig] = None
    status: str = "running"
    improvement: float = 0.0


@dataclass
class FeedbackSignal:
    feedback_id: str
    agent_id: str
    feedback_type: str
    value: float
    context: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)


class PerformanceMonitor:
    def __init__(self):
        self._metrics_history: Dict[str, List[AgentMetrics]] = defaultdict(list)
        self._baselines: Dict[str, AgentMetrics] = {}
        self._degradation_threshold = 0.1
        self._window_size = 100
        
    def record_metrics(self, metrics: AgentMetrics):
        history = self._metrics_history[metrics.agent_id]
        history.append(metrics)
        
        if len(history) > self._window_size:
            history.pop(0)
            
        if metrics.agent_id not in self._baselines:
            self._baselines[metrics.agent_id] = metrics
            
    def get_recent_metrics(self, agent_id: str, n: int = 10) -> List[AgentMetrics]:
        history = self._metrics_history.get(agent_id, [])
        return history[-n:]
        
    def detect_degradation(self, agent_id: str) -> Tuple[bool, Optional[str]]:
        history = self._metrics_history.get(agent_id, [])
        
        if len(history) < 10:
            return False, None
            
        recent = history[-5:]
        baseline = self._baselines.get(agent_id)
        
        if not baseline:
            return False, None
            
        avg_accuracy = sum(m.accuracy for m in recent) / len(recent)
        accuracy_drop = baseline.accuracy - avg_accuracy
        
        if accuracy_drop > self._degradation_threshold:
            return True, f"准确率下降 {accuracy_drop:.2%}"
            
        avg_latency = sum(m.latency_ms for m in recent) / len(recent)
        latency_increase = avg_latency / baseline.latency_ms - 1
        
        if latency_increase > 0.5:
            return True, f"延迟增加 {latency_increase:.2%}"
            
        avg_error = sum(m.error_rate for m in recent) / len(recent)
        if avg_error > 0.05:
            return True, f"错误率过高 {avg_error:.2%}"
            
        return False, None
        
    def get_performance_trend(self, agent_id: str) -> Dict[str, Any]:
        history = self._metrics_history.get(agent_id, [])
        
        if len(history) < 2:
            return {"trend": "insufficient_data"}
            
        first_half = history[:len(history)//2]
        second_half = history[len(history)//2:]
        
        first_acc = sum(m.accuracy for m in first_half) / len(first_half)
        second_acc = sum(m.accuracy for m in second_half) / len(second_half)
        
        trend = "improving" if second_acc > first_acc else "declining"
        
        return {
            "trend": trend,
            "first_half_accuracy": first_acc,
            "second_half_accuracy": second_acc,
            "change": second_acc - first_acc
        }


class HyperparameterOptimizer:
    def __init__(self):
        self._configs: Dict[str, HyperparameterConfig] = {}
        self._optimization_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._bounds = {
            HyperparameterType.LEARNING_RATE: (1e-5, 1e-1),
            HyperparameterType.BATCH_SIZE: (8, 256),
            HyperparameterType.EPOCHS: (1, 100),
            HyperparameterType.HIDDEN_DIM: (64, 1024),
            HyperparameterType.DROPOUT: (0.0, 0.5),
            HyperparameterType.REGULARIZATION: (1e-5, 1e-1)
        }
        
    def get_config(self, agent_id: str) -> HyperparameterConfig:
        if agent_id not in self._configs:
            self._configs[agent_id] = HyperparameterConfig()
        return self._configs[agent_id]
        
    def optimize(
        self,
        agent_id: str,
        current_metrics: AgentMetrics,
        strategy: str = "bayesian"
    ) -> HyperparameterConfig:
        current = self.get_config(agent_id)
        
        if strategy == "adaptive":
            new_config = self._adaptive_optimize(agent_id, current, current_metrics)
        elif strategy == "gradient":
            new_config = self._gradient_optimize(agent_id, current, current_metrics)
        else:
            new_config = self._bayesian_optimize(agent_id, current, current_metrics)
            
        self._configs[agent_id] = new_config
        
        self._optimization_history[agent_id].append({
            "timestamp": datetime.now().isoformat(),
            "old_config": current.to_dict(),
            "new_config": new_config.to_dict(),
            "metrics": current_metrics.to_dict()
        })
        
        return new_config
        
    def _adaptive_optimize(
        self,
        agent_id: str,
        current: HyperparameterConfig,
        metrics: AgentMetrics
    ) -> HyperparameterConfig:
        new_config = HyperparameterConfig(
            learning_rate=current.learning_rate,
            batch_size=current.batch_size,
            epochs=current.epochs,
            hidden_dim=current.hidden_dim,
            dropout=current.dropout,
            regularization=current.regularization
        )
        
        if metrics.accuracy < 0.7:
            new_config.learning_rate *= 0.5
            new_config.epochs = min(current.epochs + 5, 50)
        elif metrics.accuracy > 0.95:
            new_config.learning_rate *= 1.2
            
        if metrics.error_rate > 0.05:
            new_config.dropout = min(current.dropout + 0.05, 0.5)
            new_config.regularization *= 1.5
            
        if metrics.latency_ms > 1000:
            new_config.batch_size = min(current.batch_size * 2, 256)
            
        new_config.learning_rate = max(1e-5, min(new_config.learning_rate, 1e-1))
        
        return new_config
        
    def _gradient_optimize(
        self,
        agent_id: str,
        current: HyperparameterConfig,
        metrics: AgentMetrics
    ) -> HyperparameterConfig:
        history = self._optimization_history.get(agent_id, [])
        
        if len(history) < 2:
            return self._adaptive_optimize(agent_id, current, metrics)
            
        last = history[-1]
        old_metrics = last.get("metrics", {})
        
        gradient = {
            "accuracy": metrics.accuracy - old_metrics.get("accuracy", 0),
            "error_rate": old_metrics.get("error_rate", 0) - metrics.error_rate
        }
        
        improvement = gradient["accuracy"] + gradient["error_rate"]
        
        new_config = HyperparameterConfig(
            learning_rate=current.learning_rate,
            batch_size=current.batch_size,
            epochs=current.epochs,
            hidden_dim=current.hidden_dim,
            dropout=current.dropout,
            regularization=current.regularization
        )
        
        if improvement > 0:
            new_config.learning_rate *= 1.1
        else:
            new_config.learning_rate *= 0.9
            
        return new_config
        
    def _bayesian_optimize(
        self,
        agent_id: str,
        current: HyperparameterConfig,
        metrics: AgentMetrics
    ) -> HyperparameterConfig:
        import random
        
        new_config = HyperparameterConfig(
            learning_rate=current.learning_rate * random.uniform(0.8, 1.2),
            batch_size=int(current.batch_size * random.uniform(0.9, 1.1)),
            epochs=current.epochs,
            hidden_dim=current.hidden_dim,
            dropout=min(0.5, current.dropout * random.uniform(0.9, 1.1)),
            regularization=current.regularization * random.uniform(0.9, 1.1)
        )
        
        new_config.learning_rate = max(1e-5, min(new_config.learning_rate, 1e-1))
        new_config.batch_size = max(8, min(new_config.batch_size, 256))
        
        return new_config


class FeedbackCollector:
    def __init__(self):
        self._feedback: Dict[str, List[FeedbackSignal]] = defaultdict(list)
        self._feedback_threshold = 100
        
    def collect_feedback(
        self,
        agent_id: str,
        feedback_type: str,
        value: float,
        context: Optional[Dict[str, Any]] = None
    ):
        feedback = FeedbackSignal(
            feedback_id=f"fb_{agent_id}_{datetime.now().timestamp()}",
            agent_id=agent_id,
            feedback_type=feedback_type,
            value=value,
            context=context or {}
        )
        
        self._feedback[agent_id].append(feedback)
        
    def get_aggregated_feedback(
        self,
        agent_id: str,
        feedback_type: Optional[str] = None
    ) -> Dict[str, Any]:
        feedback_list = self._feedback.get(agent_id, [])
        
        if feedback_type:
            feedback_list = [f for f in feedback_list if f.feedback_type == feedback_type]
            
        if not feedback_list:
            return {"count": 0, "mean": 0, "sum": 0}
            
        values = [f.value for f in feedback_list]
        
        return {
            "count": len(values),
            "mean": sum(values) / len(values),
            "sum": sum(values),
            "min": min(values),
            "max": max(values)
        }
        
    def should_trigger_training(self, agent_id: str) -> bool:
        feedback_list = self._feedback.get(agent_id, [])
        
        if len(feedback_list) >= self._feedback_threshold:
            return True
            
        recent = [f for f in feedback_list if 
                  (datetime.now() - f.timestamp).total_seconds() < 3600]
        
        if len(recent) >= 20:
            negative_ratio = sum(1 for f in recent if f.value < 0) / len(recent)
            if negative_ratio > 0.3:
                return True
                
        return False
        
    def clear_feedback(self, agent_id: str):
        self._feedback[agent_id] = []


class CoachAgent:
    def __init__(self):
        self.performance_monitor = PerformanceMonitor()
        self.hyperparameter_optimizer = HyperparameterOptimizer()
        self.feedback_collector = FeedbackCollector()
        self._training_sessions: Dict[str, TrainingSession] = {}
        self._agent_status: Dict[str, AgentStatus] = {}
        self._training_callbacks: Dict[str, Callable] = {}
        self._monitoring_interval = 60
        
    def register_agent(
        self,
        agent_id: str,
        training_callback: Optional[Callable] = None
    ):
        self._agent_status[agent_id] = AgentStatus.HEALTHY
        
        if training_callback:
            self._training_callbacks[agent_id] = training_callback
            
    async def monitor_agents(self):
        while True:
            for agent_id in list(self._agent_status.keys()):
                await self._check_agent_health(agent_id)
                
            await asyncio.sleep(self._monitoring_interval)
            
    async def _check_agent_health(self, agent_id: str):
        is_degrading, reason = self.performance_monitor.detect_degradation(agent_id)
        
        if is_degrading:
            self._agent_status[agent_id] = AgentStatus.DEGRADING
            await self._trigger_training(agent_id, TrainingTrigger.PERFORMANCE_DROP, reason)
            
        if self.feedback_collector.should_trigger_training(agent_id):
            await self._trigger_training(agent_id, TrainingTrigger.FEEDBACK_ACCUMULATED)
            
    async def _trigger_training(
        self,
        agent_id: str,
        trigger: TrainingTrigger,
        reason: Optional[str] = None
    ) -> Optional[TrainingSession]:
        if self._agent_status.get(agent_id) == AgentStatus.TRAINING:
            return None
            
        session_id = f"train_{agent_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        recent_metrics = self.performance_monitor.get_recent_metrics(agent_id, 1)
        initial_metrics = recent_metrics[0] if recent_metrics else None
        
        session = TrainingSession(
            session_id=session_id,
            agent_id=agent_id,
            trigger=trigger,
            started_at=datetime.now(),
            initial_metrics=initial_metrics,
            status="running"
        )
        
        self._training_sessions[session_id] = session
        self._agent_status[agent_id] = AgentStatus.TRAINING
        
        logger.info(f"Training triggered for {agent_id}: {trigger.value} - {reason}")
        
        if initial_metrics:
            optimized_config = self.hyperparameter_optimizer.optimize(
                agent_id, initial_metrics
            )
            session.hyperparameters = optimized_config
            
        callback = self._training_callbacks.get(agent_id)
        if callback:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(agent_id, session)
                else:
                    callback(agent_id, session)
            except Exception as e:
                logger.error(f"Training callback failed for {agent_id}: {e}")
                session.status = "failed"
                
        return session
        
    def complete_training(
        self,
        session_id: str,
        final_metrics: AgentMetrics,
        success: bool = True
    ):
        session = self._training_sessions.get(session_id)
        if not session:
            return
            
        session.completed_at = datetime.now()
        session.final_metrics = final_metrics
        session.status = "completed" if success else "failed"
        
        if session.initial_metrics and final_metrics:
            session.improvement = final_metrics.accuracy - session.initial_metrics.accuracy
            
        self._agent_status[session.agent_id] = AgentStatus.HEALTHY
        
        self.performance_monitor.record_metrics(final_metrics)
        self.feedback_collector.clear_feedback(session.agent_id)
        
        logger.info(
            f"Training completed for {session.agent_id}: "
            f"improvement={session.improvement:.2%}"
        )
        
    def record_agent_metrics(self, metrics: AgentMetrics):
        self.performance_monitor.record_metrics(metrics)
        
    def record_feedback(
        self,
        agent_id: str,
        feedback_type: str,
        value: float,
        context: Optional[Dict[str, Any]] = None
    ):
        self.feedback_collector.collect_feedback(agent_id, feedback_type, value, context)
        
    def get_agent_status(self, agent_id: str) -> AgentStatus:
        return self._agent_status.get(agent_id, AgentStatus.HEALTHY)
        
    def get_training_history(
        self,
        agent_id: str,
        limit: int = 10
    ) -> List[TrainingSession]:
        sessions = [
            s for s in self._training_sessions.values()
            if s.agent_id == agent_id
        ]
        return sorted(sessions, key=lambda s: s.started_at, reverse=True)[:limit]
        
    def get_coaching_report(self, agent_id: str) -> Dict[str, Any]:
        return {
            "agent_id": agent_id,
            "status": self.get_agent_status(agent_id).value,
            "performance_trend": self.performance_monitor.get_performance_trend(agent_id),
            "feedback_summary": self.feedback_collector.get_aggregated_feedback(agent_id),
            "current_hyperparameters": self.hyperparameter_optimizer.get_config(agent_id).to_dict(),
            "recent_training": [
                {
                    "session_id": s.session_id,
                    "trigger": s.trigger.value,
                    "improvement": s.improvement,
                    "started_at": s.started_at.isoformat()
                }
                for s in self.get_training_history(agent_id, 5)
            ]
        }


coach_agent = CoachAgent()


def get_coach_agent() -> CoachAgent:
    return coach_agent


async def start_coaching():
    await coach_agent.monitor_agents()
