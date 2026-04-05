# -*- coding: utf-8 -*-
"""
CASK 注意力模块
集成重要性估计、稀疏控制和存储管理
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
from uuid import UUID, uuid4
import time
import math

from .config import CASKConfig, get_default_config
from .models import (
    CacheSession, KVCacheBlock, SparsityDecision,
    PerformanceMetric, ImportanceScore, SparseCacheResult, CASKContext
)
from .importance_estimator import ImportanceEstimator
from .sparse_controller import SparseController
from .sparse_storage import SparseStorage


@dataclass
class AttentionOutput:
    output: List[float]
    attention_weights: List[float]
    sparsity_rate: float = 0.0
    kv_pairs_used: int = 0
    latency_ms: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            "output": self.output[:10] if len(self.output) > 10 else self.output,
            "attention_weights": self.attention_weights[:10] if len(self.attention_weights) > 10 else self.attention_weights,
            "sparsity_rate": self.sparsity_rate,
            "kv_pairs_used": self.kv_pairs_used,
            "latency_ms": self.latency_ms
        }


class CASKAttention:
    def __init__(self, config: Optional[CASKConfig] = None):
        self.config = config or get_default_config()
        self.importance_estimator = ImportanceEstimator(self.config)
        self.sparse_controller = SparseController(self.config)
        self.sparse_storage = SparseStorage(self.config)
        
        self._kv_cache: List[Tuple[List[float], List[float]]] = []
        self._context = None
        self._session_id = uuid4()
        self._step = 0
    
    def forward(
        self, 
        query: List[float], 
        key: List[float], 
        value: List[float],
        attention_weights: Optional[List[float]] = None
    ) -> AttentionOutput:
        start_time = time.time()
        
        self._kv_cache.append((key, value))
        self._step += 1
        context_length = len(self._kv_cache)
        
        if not self.config.should_enable_cask(context_length):
            output = self._full_attention(query, self._kv_cache)
            latency = (time.time() - start_time) * 1000
            return AttentionOutput(
                output=output,
                attention_weights=[1.0 / context_length] * context_length,
                sparsity_rate=0.0,
                kv_pairs_used=context_length,
                latency_ms=latency
            )
        
        if self.config.is_in_warmup(self._step):
            output = self._full_attention(query, self._kv_cache)
            latency = (time.time() - start_time) * 1000
            return AttentionOutput(
                output=output,
                attention_weights=[1.0 / context_length] * context_length,
                sparsity_rate=0.0,
                kv_pairs_used=context_length,
                latency_ms=latency
            )
        
        importance_scores = self.importance_estimator.estimate(
            query, self._kv_cache, context_length - 1
        )
        
        sparsity_rate = self.sparse_controller.compute_sparsity(
            context_length, attention_weights, self._step
        )
        
        selected_indices = self.importance_estimator.select_top_k(
            importance_scores, sparsity_rate
        )
        
        sparse_kv = [self._kv_cache[i] for i in selected_indices]
        
        output, weights = self._sparse_attention(query, sparse_kv, selected_indices, context_length)
        
        latency = (time.time() - start_time) * 1000
        
        return AttentionOutput(
            output=output,
            attention_weights=weights,
            sparsity_rate=sparsity_rate,
            kv_pairs_used=len(sparse_kv),
            latency_ms=latency
        )
    
    def _full_attention(
        self, 
        query: List[float], 
        kv_cache: List[Tuple[List[float], List[float]]]
    ) -> List[float]:
        if not kv_cache:
            return [0.0] * len(query)
        
        keys = [kv[0] for kv in kv_cache]
        values = [kv[1] for kv in kv_cache]
        
        scores = []
        for k in keys:
            score = sum(q * ki for q, ki in zip(query, k))
            scores.append(score / math.sqrt(len(query)))
        
        max_score = max(scores) if scores else 0
        exp_scores = [math.exp(s - max_score) for s in scores]
        sum_exp = sum(exp_scores)
        attention_weights = [e / sum_exp for e in exp_scores]
        
        dim = len(values[0]) if values else len(query)
        output = [0.0] * dim
        for weight, v in zip(attention_weights, values):
            for i in range(min(len(output), len(v))):
                output[i] += weight * v[i]
        
        return output
    
    def _sparse_attention(
        self, 
        query: List[float], 
        sparse_kv: List[Tuple[List[float], List[float]]],
        selected_indices: List[int],
        total_length: int
    ) -> Tuple[List[float], List[float]]:
        if not sparse_kv:
            return [0.0] * len(query), []
        
        keys = [kv[0] for kv in sparse_kv]
        values = [kv[1] for kv in sparse_kv]
        
        scores = []
        for k in keys:
            score = sum(q * ki for q, ki in zip(query, k))
            scores.append(score / math.sqrt(len(query)))
        
        max_score = max(scores) if scores else 0
        exp_scores = [math.exp(s - max_score) for s in scores]
        sum_exp = sum(exp_scores)
        local_weights = [e / sum_exp for e in exp_scores]
        
        full_weights = [0.0] * total_length
        for idx, weight in zip(selected_indices, local_weights):
            if idx < total_length:
                full_weights[idx] = weight
        
        dim = len(values[0]) if values else len(query)
        output = [0.0] * dim
        for weight, v in zip(local_weights, values):
            for i in range(min(len(output), len(v))):
                output[i] += weight * v[i]
        
        return output, full_weights
    
    def get_context(self) -> CASKContext:
        return CASKContext(
            session_id=self._session_id,
            step=self._step,
            context_length=len(self._kv_cache),
            current_sparsity=self.sparse_controller.get_current_sparsity(),
            is_warmup=self.config.is_in_warmup(self._step),
            complexity_score=self.sparse_controller.get_complexity(),
            stage=self.sparse_controller.get_stage(self._step)
        )
    
    def get_statistics(self) -> Dict:
        return {
            "session_id": str(self._session_id),
            "step": self._step,
            "context_length": len(self._kv_cache),
            "current_sparsity": self.sparse_controller.get_current_sparsity(),
            "avg_complexity": self.sparse_controller.get_avg_complexity(),
            "stage": self.sparse_controller.get_stage(self._step),
            "config": self.config.to_dict()
        }
    
    def reset(self):
        self._kv_cache = []
        self._step = 0
        self._session_id = uuid4()
        self.sparse_controller.reset()
        self.sparse_storage.clear()
    
    def update_config(self, config: CASKConfig):
        self.config = config
        self.importance_estimator.update_config(config)
        self.sparse_controller.update_config(config)
        self.sparse_storage.update_config(config)


class CASKModule:
    def __init__(self, config: Optional[CASKConfig] = None):
        self.config = config or get_default_config()
        self._sessions: Dict[UUID, CASKAttention] = {}
        self._default_attention = CASKAttention(self.config)
    
    def create_session(
        self, 
        user_id: Optional[UUID] = None,
        model_name: str = "default"
    ) -> CacheSession:
        session_id = uuid4()
        config = get_default_config(model_name)
        
        attention = CASKAttention(config)
        self._sessions[session_id] = attention
        
        return CacheSession(
            id=session_id,
            user_id=user_id,
            model_name=model_name,
            max_context_length=config.context_threshold * 2,
            cask_enabled=True
        )
    
    def get_session(self, session_id: UUID) -> Optional[CASKAttention]:
        return self._sessions.get(session_id)
    
    def end_session(self, session_id: UUID) -> bool:
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False
    
    def process(
        self, 
        query: List[float],
        key: List[float],
        value: List[float],
        session_id: Optional[UUID] = None
    ) -> AttentionOutput:
        if session_id and session_id in self._sessions:
            attention = self._sessions[session_id]
        else:
            attention = self._default_attention
        
        return attention.forward(query, key, value)
    
    def get_session_statistics(self, session_id: UUID) -> Optional[Dict]:
        attention = self._sessions.get(session_id)
        if attention:
            return attention.get_statistics()
        return None
    
    def get_all_sessions(self) -> List[UUID]:
        return list(self._sessions.keys())
    
    def get_global_statistics(self) -> Dict:
        return {
            "total_sessions": len(self._sessions),
            "config": self.config.to_dict(),
            "sessions": [
                {
                    "session_id": str(sid),
                    "context_length": att._step
                }
                for sid, att in self._sessions.items()
            ]
        }
    
    def clear_all_sessions(self):
        self._sessions.clear()
