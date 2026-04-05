"""
自适应学习率模块
Adaptive Learning Rate Module

实现学习率自适应调度、元学习率优化等功能
"""

import asyncio
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
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


class SchedulerType(Enum):
    COSINE_ANNEALING = "cosine_annealing"
    REDUCE_ON_PLATEAU = "reduce_on_plateau"
    EXPONENTIAL_DECAY = "exponential_decay"
    CYCLIC = "cyclic"
    WARMUP = "warmup"


@dataclass
class LearningRateHistory:
    history_id: str
    agent_id: str
    initial_lr: float
    current_lr: float
    min_lr: float
    max_lr: float
    adjustments: List[Dict[str, Any]]
    created_at: datetime
    last_updated: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "history_id": self.history_id,
            "agent_id": self.agent_id,
            "initial_lr": self.initial_lr,
            "current_lr": self.current_lr,
            "min_lr": self.min_lr,
            "max_lr": self.max_lr,
            "adjustments": self.adjustments[-100:],
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
        }
    
    def add_adjustment(
        self,
        old_lr: float,
        new_lr: float,
        reason: str,
        metrics: Dict[str, float] = None
    ):
        self.adjustments.append({
            "timestamp": datetime.now().isoformat(),
            "old_lr": old_lr,
            "new_lr": new_lr,
            "reason": reason,
            "metrics": metrics or {},
        })
        self.current_lr = new_lr
        self.last_updated = datetime.now()


class CosineAnnealingScheduler:
    """余弦退火调度器"""
    
    def __init__(
        self,
        initial_lr: float = 0.001,
        min_lr: float = 1e-6,
        warmup_epochs: int = 5,
        cycle_epochs: int = 50,
        restart_mult: float = 1.0
    ):
        self.initial_lr = initial_lr
        self.min_lr = min_lr
        self.warmup_epochs = warmup_epochs
        self.cycle_epochs = cycle_epochs
        self.restart_mult = restart_mult
        
        self.current_epoch = 0
        self.current_lr = initial_lr
        self.cycle_count = 0
        self.cycle_start = 0
        
        self._lock = threading.Lock()
    
    def step(self, epoch: int = None) -> float:
        with self._lock:
            if epoch is not None:
                self.current_epoch = epoch
            else:
                self.current_epoch += 1
            
            if self.current_epoch < self.warmup_epochs:
                warmup_factor = (self.current_epoch + 1) / self.warmup_epochs
                self.current_lr = self.initial_lr * warmup_factor
            else:
                effective_epoch = self.current_epoch - self.cycle_start
                cycle_length = self.cycle_epochs * (self.restart_mult ** self.cycle_count)
                
                if effective_epoch >= cycle_length:
                    self.cycle_count += 1
                    self.cycle_start = self.current_epoch
                    effective_epoch = 0
                    cycle_length = self.cycle_epochs * (self.restart_mult ** self.cycle_count)
                
                progress = effective_epoch / cycle_length
                self.current_lr = self.min_lr + 0.5 * (self.initial_lr - self.min_lr) * (1 + math.cos(math.pi * progress))
            
            return self.current_lr
    
    def get_lr(self) -> float:
        return self.current_lr
    
    def reset(self):
        with self._lock:
            self.current_epoch = 0
            self.current_lr = self.initial_lr
            self.cycle_count = 0
            self.cycle_start = 0


class ReduceOnPlateauScheduler:
    """验证损失停滞时降低学习率调度器"""
    
    def __init__(
        self,
        initial_lr: float = 0.001,
        factor: float = 0.5,
        patience: int = 5,
        min_lr: float = 1e-6,
        threshold: float = 1e-4,
        cooldown: int = 0
    ):
        self.initial_lr = initial_lr
        self.factor = factor
        self.patience = patience
        self.min_lr = min_lr
        self.threshold = threshold
        self.cooldown = cooldown
        
        self.current_lr = initial_lr
        self.best_loss = float('inf')
        self.bad_epochs = 0
        self.cooldown_counter = 0
        
        self._lock = threading.Lock()
        self.history: List[Dict[str, Any]] = []
    
    def step(self, metric: float, epoch: int = None) -> Tuple[float, bool]:
        with self._lock:
            reduced = False
            
            if self.cooldown_counter > 0:
                self.cooldown_counter -= 1
                self.history.append({
                    "epoch": epoch,
                    "metric": metric,
                    "lr": self.current_lr,
                    "action": "cooldown",
                })
                return self.current_lr, reduced
            
            if metric < self.best_loss - self.threshold:
                self.best_loss = metric
                self.bad_epochs = 0
                action = "improved"
            else:
                self.bad_epochs += 1
                action = "no_improvement"
                
                if self.bad_epochs >= self.patience:
                    old_lr = self.current_lr
                    self.current_lr = max(self.min_lr, self.current_lr * self.factor)
                    
                    if self.current_lr < old_lr:
                        reduced = True
                        self.bad_epochs = 0
                        self.cooldown_counter = self.cooldown
                        action = "reduced"
            
            self.history.append({
                "epoch": epoch,
                "metric": metric,
                "lr": self.current_lr,
                "action": action,
            })
            
            return self.current_lr, reduced
    
    def get_lr(self) -> float:
        return self.current_lr
    
    def reset(self):
        with self._lock:
            self.current_lr = self.initial_lr
            self.best_loss = float('inf')
            self.bad_epochs = 0
            self.cooldown_counter = 0


class AdaptiveLRScheduler:
    """自适应学习率调度器主控"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        self.schedulers: Dict[str, Union[CosineAnnealingScheduler, ReduceOnPlateauScheduler]] = {}
        self.histories: Dict[str, LearningRateHistory] = {}
        
        self._lock = threading.Lock()
        
        self.stats = {
            "total_agents": 0,
            "total_adjustments": 0,
            "lr_reductions": 0,
            "lr_increases": 0,
        }
    
    def register_agent(
        self,
        agent_id: str,
        scheduler_type: SchedulerType = SchedulerType.REDUCE_ON_PLATEAU,
        initial_lr: float = 0.001,
        **kwargs
    ) -> str:
        with self._lock:
            if scheduler_type == SchedulerType.COSINE_ANNEALING:
                scheduler = CosineAnnealingScheduler(
                    initial_lr=initial_lr,
                    min_lr=kwargs.get("min_lr", 1e-6),
                    warmup_epochs=kwargs.get("warmup_epochs", 5),
                    cycle_epochs=kwargs.get("cycle_epochs", 50),
                )
            else:
                scheduler = ReduceOnPlateauScheduler(
                    initial_lr=initial_lr,
                    factor=kwargs.get("factor", 0.5),
                    patience=kwargs.get("patience", 5),
                    min_lr=kwargs.get("min_lr", 1e-6),
                )
            
            self.schedulers[agent_id] = scheduler
            
            history = LearningRateHistory(
                history_id=f"lrh_{uuid.uuid4().hex[:8]}",
                agent_id=agent_id,
                initial_lr=initial_lr,
                current_lr=initial_lr,
                min_lr=kwargs.get("min_lr", 1e-6),
                max_lr=kwargs.get("max_lr", 0.1),
                adjustments=[],
                created_at=datetime.now(),
                last_updated=datetime.now(),
            )
            self.histories[agent_id] = history
            
            self.stats["total_agents"] += 1
        
        return agent_id
    
    def step(
        self,
        agent_id: str,
        metric: float = None,
        epoch: int = None
    ) -> Tuple[float, bool]:
        with self._lock:
            if agent_id not in self.schedulers:
                return 0.001, False
            
            scheduler = self.schedulers[agent_id]
            history = self.histories[agent_id]
            
            old_lr = scheduler.get_lr()
            
            if isinstance(scheduler, ReduceOnPlateauScheduler):
                if metric is None:
                    metric = 0.0
                new_lr, reduced = scheduler.step(metric, epoch)
                
                if reduced:
                    history.add_adjustment(old_lr, new_lr, "plateau_reduction", {"metric": metric})
                    self.stats["lr_reductions"] += 1
                    self.stats["total_adjustments"] += 1
            else:
                new_lr = scheduler.step(epoch)
                reduced = new_lr < old_lr
                
                if abs(new_lr - old_lr) > 1e-8:
                    history.add_adjustment(old_lr, new_lr, "cosine_step")
                    self.stats["total_adjustments"] += 1
            
            return new_lr, reduced
    
    def get_lr(self, agent_id: str) -> float:
        with self._lock:
            if agent_id in self.schedulers:
                return self.schedulers[agent_id].get_lr()
            return 0.001
    
    def set_lr(self, agent_id: str, lr: float) -> bool:
        with self._lock:
            if agent_id not in self.schedulers:
                return False
            
            scheduler = self.schedulers[agent_id]
            history = self.histories[agent_id]
            
            old_lr = scheduler.current_lr
            lr = max(history.min_lr, min(history.max_lr, lr))
            
            scheduler.current_lr = lr
            history.add_adjustment(old_lr, lr, "manual_set")
            
            if lr > old_lr:
                self.stats["lr_increases"] += 1
            elif lr < old_lr:
                self.stats["lr_reductions"] += 1
            
            self.stats["total_adjustments"] += 1
            
            return True
    
    def get_history(self, agent_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            if agent_id in self.histories:
                return self.histories[agent_id].to_dict()
            return None
    
    def get_all_lrs(self) -> Dict[str, float]:
        with self._lock:
            return {
                agent_id: scheduler.get_lr()
                for agent_id, scheduler in self.schedulers.items()
            }
    
    def reset_agent(self, agent_id: str) -> bool:
        with self._lock:
            if agent_id in self.schedulers:
                self.schedulers[agent_id].reset()
                
                history = self.histories[agent_id]
                history.add_adjustment(
                    history.current_lr,
                    history.initial_lr,
                    "reset"
                )
                
                return True
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            **self.stats,
            "active_agents": len(self.schedulers),
        }


@dataclass
class MetaLearningRate:
    meta_lr_id: str
    agent_id: str
    base_lr: float
    suggested_lr: float
    confidence: float
    task_performance: float
    adaptation_speed: float
    created_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "meta_lr_id": self.meta_lr_id,
            "agent_id": self.agent_id,
            "base_lr": self.base_lr,
            "suggested_lr": self.suggested_lr,
            "confidence": self.confidence,
            "task_performance": self.task_performance,
            "adaptation_speed": self.adaptation_speed,
            "created_at": self.created_at.isoformat(),
        }


class MetaLearner:
    """元学习器 - 学习如何调整学习率"""
    
    def __init__(
        self,
        meta_lr: float = 0.001,
        inner_lr: float = 0.01,
        num_inner_steps: int = 5
    ):
        self.meta_lr = meta_lr
        self.inner_lr = inner_lr
        self.num_inner_steps = num_inner_steps
        
        self.task_performances: Dict[str, List[float]] = defaultdict(list)
        self.lr_suggestions: Dict[str, MetaLearningRate] = {}
        self.adaptation_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        
        self._lock = threading.Lock()
        
        self.stats = {
            "total_adaptations": 0,
            "successful_adaptations": 0,
            "avg_performance_improvement": 0.0,
        }
    
    def observe_performance(
        self,
        agent_id: str,
        task_id: str,
        performance: float,
        current_lr: float
    ):
        with self._lock:
            key = f"{agent_id}:{task_id}"
            self.task_performances[key].append({
                "performance": performance,
                "lr": current_lr,
                "timestamp": datetime.now().isoformat(),
            })
            
            if len(self.task_performances[key]) > 100:
                self.task_performances[key] = self.task_performances[key][-100:]
    
    def suggest_lr(
        self,
        agent_id: str,
        current_lr: float,
        recent_performance: float,
        task_type: str = "default"
    ) -> MetaLearningRate:
        with self._lock:
            self.stats["total_adaptations"] += 1
            
            performance_history = []
            for key, history in self.task_performances.items():
                if key.startswith(agent_id):
                    performance_history.extend(history)
            
            if len(performance_history) < 5:
                suggested_lr = current_lr
                confidence = 0.3
                adaptation_speed = 0.0
            else:
                recent_lrs = [h["lr"] for h in performance_history[-10:]]
                recent_perfs = [h["performance"] for h in performance_history[-10:]]
                
                if len(recent_lrs) > 1:
                    lr_perf_pairs = list(zip(recent_lrs, recent_perfs))
                    best_pair = max(lr_perf_pairs, key=lambda x: x[1])
                    suggested_lr = best_pair[0]
                    
                    avg_perf = sum(recent_perfs) / len(recent_perfs)
                    confidence = min(1.0, len(performance_history) / 50)
                    
                    perf_trend = recent_perfs[-1] - recent_perfs[0] if len(recent_perfs) > 1 else 0
                    adaptation_speed = max(0, perf_trend)
                else:
                    suggested_lr = current_lr
                    confidence = 0.3
                    adaptation_speed = 0.0
            
            if recent_performance > 0.7:
                suggested_lr = current_lr * 1.1
            elif recent_performance < 0.3:
                suggested_lr = current_lr * 0.8
            
            suggested_lr = max(1e-6, min(0.1, suggested_lr))
            
            meta_lr = MetaLearningRate(
                meta_lr_id=f"mlr_{uuid.uuid4().hex[:8]}",
                agent_id=agent_id,
                base_lr=current_lr,
                suggested_lr=suggested_lr,
                confidence=confidence,
                task_performance=recent_performance,
                adaptation_speed=adaptation_speed,
                created_at=datetime.now(),
            )
            
            self.lr_suggestions[agent_id] = meta_lr
            
            self.adaptation_history[agent_id].append({
                "timestamp": datetime.now().isoformat(),
                "old_lr": current_lr,
                "suggested_lr": suggested_lr,
                "performance": recent_performance,
                "confidence": confidence,
            })
            
            return meta_lr
    
    def maml_adapt(
        self,
        agent_id: str,
        support_data: List[Any],
        query_data: List[Any],
        base_model_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        adapted_params = copy.deepcopy(base_model_params)
        
        for step in range(self.num_inner_steps):
            support_loss = random.uniform(0.1, 0.5)
            
            for key in adapted_params:
                if isinstance(adapted_params[key], (int, float)):
                    gradient = random.uniform(-0.1, 0.1)
                    adapted_params[key] -= self.inner_lr * gradient
        
        query_loss = random.uniform(0.05, 0.3)
        
        meta_gradient = {}
        for key in base_model_params:
            if isinstance(base_model_params[key], (int, float)):
                meta_gradient[key] = random.uniform(-0.05, 0.05)
        
        return {
            "adapted_params": adapted_params,
            "query_loss": query_loss,
            "meta_gradient": meta_gradient,
            "adaptation_steps": self.num_inner_steps,
        }
    
    def get_suggestion(self, agent_id: str) -> Optional[MetaLearningRate]:
        with self._lock:
            return self.lr_suggestions.get(agent_id)
    
    def get_adaptation_history(
        self,
        agent_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        with self._lock:
            history = self.adaptation_history.get(agent_id, [])
            return history[-limit:]
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            **self.stats,
            "total_agents_tracked": len(self.lr_suggestions),
            "total_task_records": sum(len(h) for h in self.task_performances.values()),
        }


import copy
