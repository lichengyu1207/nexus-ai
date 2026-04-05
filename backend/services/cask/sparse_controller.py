# -*- coding: utf-8 -*-
"""
CASK 自适应稀疏控制器模块
实现复杂度评估和稀疏率动态调整
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import math

from .config import CASKConfig


@dataclass
class ComplexityEstimator:
    method: str = "attention_entropy"
    
    def estimate(self, attention_weights: List[float]) -> float:
        if not attention_weights:
            return 0.5
        
        if self.method == "attention_entropy":
            return self._compute_entropy(attention_weights)
        elif self.method == "gini":
            return self._compute_gini(attention_weights)
        else:
            return self._compute_variance(attention_weights)
    
    def _compute_entropy(self, weights: List[float]) -> float:
        total = sum(abs(w) for w in weights)
        if total == 0:
            return 0.0
        
        probs = [abs(w) / total for w in weights]
        entropy = 0.0
        for p in probs:
            if p > 0:
                entropy -= p * math.log2(p + 1e-10)
        
        max_entropy = math.log2(len(weights)) if len(weights) > 1 else 1.0
        normalized = entropy / max_entropy if max_entropy > 0 else 0.0
        
        return min(1.0, max(0.0, normalized))
    
    def _compute_gini(self, weights: List[float]) -> float:
        n = len(weights)
        if n == 0:
            return 0.0
        
        sorted_weights = sorted(abs(w) for w in weights)
        cumsum = 0.0
        for i, w in enumerate(sorted_weights):
            cumsum += (2 * (i + 1) - n - 1) * w
        
        total = sum(sorted_weights)
        if total == 0:
            return 0.0
        
        gini = cumsum / (n * total)
        return min(1.0, max(0.0, gini))
    
    def _compute_variance(self, weights: List[float]) -> float:
        if not weights:
            return 0.0
        
        mean = sum(abs(w) for w in weights) / len(weights)
        variance = sum((abs(w) - mean) ** 2 for w in weights) / len(weights)
        
        return min(1.0, variance * 10)


@dataclass
class SparsityScheduler:
    stage_thresholds: Dict[str, Dict] = field(default_factory=lambda: {
        "warmup": {"min": 0.0, "max": 0.1},
        "rampup": {"min": 0.2, "max": 0.5},
        "stable": {"min": 0.3, "max": 0.7}
    })
    
    def get_sparsity(
        self, 
        step: int, 
        context_length: int, 
        warmup_steps: int,
        base_sparsity: float
    ) -> float:
        stage = self._determine_stage(step, warmup_steps)
        thresholds = self.stage_thresholds.get(stage, {"min": 0.3, "max": 0.7})
        
        if stage == "warmup":
            return thresholds["max"] * (step / warmup_steps) if warmup_steps > 0 else 0.0
        elif stage == "rampup":
            progress = (step - warmup_steps) / warmup_steps if warmup_steps > 0 else 1.0
            return thresholds["min"] + progress * (thresholds["max"] - thresholds["min"])
        else:
            return base_sparsity
    
    def _determine_stage(self, step: int, warmup_steps: int) -> str:
        if step < warmup_steps:
            return "warmup"
        elif step < warmup_steps * 2:
            return "rampup"
        else:
            return "stable"
    
    def update_thresholds(self, feedback: Dict) -> None:
        if "warmup_max" in feedback:
            self.stage_thresholds["warmup"]["max"] = feedback["warmup_max"]
        if "stable_min" in feedback:
            self.stage_thresholds["stable"]["min"] = feedback["stable_min"]
        if "stable_max" in feedback:
            self.stage_thresholds["stable"]["max"] = feedback["stable_max"]


class SparseController:
    def __init__(self, config: CASKConfig):
        self.config = config
        self.complexity_estimator = ComplexityEstimator(method="attention_entropy")
        self.scheduler = SparsityScheduler()
        self._current_sparsity = config.default_sparsity
        self._complexity_history: List[float] = []
    
    def compute_sparsity(
        self, 
        context_length: int, 
        attention_weights: Optional[List[float]] = None,
        step: int = 0
    ) -> float:
        if not self.config.enable_adaptive:
            return self.config.default_sparsity
        
        if context_length < self.config.context_threshold:
            return 0.0
        
        complexity = 0.5
        if attention_weights:
            complexity = self.complexity_estimator.estimate(attention_weights)
            self._complexity_history.append(complexity)
            if len(self._complexity_history) > 100:
                self._complexity_history = self._complexity_history[-100:]
        
        base_sparsity = self.config.get_sparsity_for_complexity(complexity)
        
        stage_sparsity = self.scheduler.get_sparsity(
            step, context_length, self.config.warmup_steps, base_sparsity
        )
        
        final_sparsity = max(
            self.config.min_sparsity,
            min(self.config.max_sparsity, stage_sparsity)
        )
        
        self._current_sparsity = final_sparsity
        return final_sparsity
    
    def get_current_sparsity(self) -> float:
        return self._current_sparsity
    
    def get_complexity(self) -> float:
        if self._complexity_history:
            return self._complexity_history[-1]
        return 0.5
    
    def get_avg_complexity(self) -> float:
        if not self._complexity_history:
            return 0.5
        return sum(self._complexity_history) / len(self._complexity_history)
    
    def get_stage(self, step: int) -> str:
        return self.scheduler._determine_stage(step, self.config.warmup_steps)
    
    def estimate_memory_savings(
        self, 
        kv_pairs_total: int, 
        sparsity_rate: float,
        hidden_dim: int = 4096,
        precision_bytes: int = 2
    ) -> Dict[str, float]:
        bytes_per_kv = 2 * hidden_dim * precision_bytes
        
        memory_before = kv_pairs_total * bytes_per_kv / (1024 * 1024)
        
        kv_pairs_retained = int(kv_pairs_total * (1 - sparsity_rate))
        memory_after = kv_pairs_retained * bytes_per_kv / (1024 * 1024)
        
        memory_saved = memory_before - memory_after
        compression_ratio = memory_saved / memory_before if memory_before > 0 else 0.0
        
        return {
            "memory_before_mb": memory_before,
            "memory_after_mb": memory_after,
            "memory_saved_mb": memory_saved,
            "compression_ratio": compression_ratio,
            "kv_pairs_retained": kv_pairs_retained
        }
    
    def update_config(self, config: CASKConfig):
        self.config = config
        self._current_sparsity = config.default_sparsity
    
    def reset(self):
        self._complexity_history = []
        self._current_sparsity = self.config.default_sparsity
