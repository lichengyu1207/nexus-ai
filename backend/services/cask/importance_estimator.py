# -*- coding: utf-8 -*-
"""
CASK 重要性估计器模块
实现查询-键交互分数和位置衰减因子
"""
from dataclasses import dataclass
from typing import List, Optional, Tuple
import math
import random

from .config import CASKConfig
from .models import ImportanceScore


@dataclass
class QKScoreCalculator:
    sample_size: int = 64
    window_size: int = 512
    
    def calculate(self, query: List[float], keys: List[List[float]]) -> List[float]:
        if not keys:
            return []
        
        n_keys = len(keys)
        if n_keys <= self.window_size:
            return self._full_calculation(query, keys)
        else:
            return self._sliding_window_approx(query, keys)
    
    def _full_calculation(self, query: List[float], keys: List[List[float]]) -> List[float]:
        scores = []
        for key in keys:
            score = self._dot_product(query, key)
            scores.append(score)
        return self._normalize_scores(scores)
    
    def _sliding_window_approx(self, query: List[float], keys: List[List[float]]) -> List[float]:
        n_keys = len(keys)
        scores = [0.0] * n_keys
        
        window_start = max(0, n_keys - self.window_size)
        for i in range(window_start, n_keys):
            scores[i] = self._dot_product(query, keys[i])
        
        sample_indices = random.sample(
            range(window_start), 
            min(self.sample_size, window_start)
        )
        for idx in sample_indices:
            scores[idx] = self._dot_product(query, keys[idx])
        
        return self._normalize_scores(scores)
    
    def _dot_product(self, a: List[float], b: List[float]) -> float:
        if len(a) != len(b):
            return 0.0
        return sum(x * y for x, y in zip(a, b))
    
    def _normalize_scores(self, scores: List[float]) -> List[float]:
        if not scores:
            return scores
        
        max_score = max(abs(s) for s in scores) if scores else 1.0
        if max_score == 0:
            return scores
        
        return [s / max_score for s in scores]


@dataclass
class PositionDecay:
    lambda_decay: float = 0.1
    
    def compute(self, positions: List[int], total_length: int) -> List[float]:
        if total_length == 0:
            return [1.0] * len(positions)
        
        decay_scores = []
        for pos in positions:
            relative_pos = pos / total_length
            decay = math.exp(-self.lambda_decay * (1 - relative_pos))
            decay_scores.append(decay)
        
        return decay_scores
    
    def adaptive_lambda(self, context_length: int, threshold: int = 4096) -> float:
        if context_length <= threshold:
            return self.lambda_decay
        else:
            ratio = context_length / threshold
            return self.lambda_decay * math.log(ratio + 1)


class ImportanceEstimator:
    def __init__(self, config: CASKConfig):
        self.config = config
        self.qk_calculator = QKScoreCalculator(
            sample_size=config.sample_size,
            window_size=config.window_size
        )
        self.position_decay = PositionDecay(lambda_decay=config.decay_lambda)
    
    def estimate(
        self, 
        query: List[float], 
        kv_cache: List[Tuple[List[float], List[float]]],
        current_position: int = 0
    ) -> List[ImportanceScore]:
        if not kv_cache:
            return []
        
        keys = [kv[0] for kv in kv_cache]
        positions = list(range(len(kv_cache)))
        
        qk_scores = self.qk_calculator.calculate(query, keys)
        
        if self.config.enable_position_decay:
            adaptive_lambda = self.position_decay.adaptive_lambda(len(kv_cache))
            self.position_decay.lambda_decay = adaptive_lambda
            decay_scores = self.position_decay.compute(positions, len(kv_cache))
        else:
            decay_scores = [1.0] * len(kv_cache)
        
        importance_scores = []
        for i, (qk, decay) in enumerate(zip(qk_scores, decay_scores)):
            combined = self._combine_scores(qk, decay)
            importance_scores.append(ImportanceScore(
                index=i,
                qk_score=qk,
                position_decay=decay,
                combined_score=combined
            ))
        
        return importance_scores
    
    def _combine_scores(self, qk_score: float, decay_score: float) -> float:
        alpha = 0.7
        return alpha * qk_score + (1 - alpha) * decay_score
    
    def select_top_k(
        self, 
        importance_scores: List[ImportanceScore], 
        sparsity_rate: float
    ) -> List[int]:
        if not importance_scores:
            return []
        
        n_total = len(importance_scores)
        n_retain = max(1, int(n_total * (1 - sparsity_rate)))
        
        sorted_scores = sorted(
            importance_scores, 
            key=lambda x: x.combined_score, 
            reverse=True
        )
        
        selected_indices = [score.index for score in sorted_scores[:n_retain]]
        
        return sorted(selected_indices)
    
    def get_importance_threshold(
        self, 
        importance_scores: List[ImportanceScore], 
        sparsity_rate: float
    ) -> float:
        if not importance_scores:
            return 0.0
        
        sorted_scores = sorted(
            [s.combined_score for s in importance_scores], 
            reverse=True
        )
        
        threshold_idx = max(0, int(len(sorted_scores) * (1 - sparsity_rate)) - 1)
        return sorted_scores[threshold_idx]
    
    def update_config(self, config: CASKConfig):
        self.config = config
        self.qk_calculator = QKScoreCalculator(
            sample_size=config.sample_size,
            window_size=config.window_size
        )
        self.position_decay = PositionDecay(lambda_decay=config.decay_lambda)
