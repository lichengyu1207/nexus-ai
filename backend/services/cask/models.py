# -*- coding: utf-8 -*-
"""
CASK 数据模型定义
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4
import json


@dataclass
class CacheSession:
    id: UUID = field(default_factory=uuid4)
    user_id: Optional[UUID] = None
    model_name: str = "default"
    max_context_length: int = 8192
    total_memory_mb: float = 0.0
    total_tokens: int = 0
    cask_enabled: bool = True
    started_at: datetime = field(default_factory=datetime.now)
    ended_at: Optional[datetime] = None
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "id": str(self.id),
            "user_id": str(self.user_id) if self.user_id else None,
            "model_name": self.model_name,
            "max_context_length": self.max_context_length,
            "total_memory_mb": self.total_memory_mb,
            "total_tokens": self.total_tokens,
            "cask_enabled": self.cask_enabled,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_db_row(cls, row: Dict) -> 'CacheSession':
        return cls(
            id=row["id"],
            user_id=row.get("user_id"),
            model_name=row.get("model_name", "default"),
            max_context_length=row.get("max_context_length", 8192),
            total_memory_mb=row.get("total_memory_mb", 0.0),
            total_tokens=row.get("total_tokens", 0),
            cask_enabled=row.get("cask_enabled", True),
            started_at=row.get("started_at"),
            ended_at=row.get("ended_at"),
            metadata=row.get("metadata", {})
        )


@dataclass
class KVCacheBlock:
    id: UUID = field(default_factory=uuid4)
    session_id: UUID = field(default_factory=uuid4)
    block_index: int = 0
    start_position: int = 0
    end_position: int = 0
    compressed_data: Dict = field(default_factory=dict)
    csr_values: List[float] = field(default_factory=list)
    csr_col_indices: List[int] = field(default_factory=list)
    csr_row_ptr: List[int] = field(default_factory=list)
    avg_importance: float = 0.0
    token_count: int = 0
    is_sparse: bool = False
    sparsity_rate: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "id": str(self.id),
            "session_id": str(self.session_id),
            "block_index": self.block_index,
            "start_position": self.start_position,
            "end_position": self.end_position,
            "compressed_data": self.compressed_data,
            "csr_values": self.csr_values,
            "csr_col_indices": self.csr_col_indices,
            "csr_row_ptr": self.csr_row_ptr,
            "avg_importance": self.avg_importance,
            "token_count": self.token_count,
            "is_sparse": self.is_sparse,
            "sparsity_rate": self.sparsity_rate,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
            "access_count": self.access_count
        }
    
    @classmethod
    def from_db_row(cls, row: Dict) -> 'KVCacheBlock':
        return cls(
            id=row["id"],
            session_id=row["session_id"],
            block_index=row.get("block_index", 0),
            start_position=row.get("start_position", 0),
            end_position=row.get("end_position", 0),
            compressed_data=row.get("compressed_data", {}),
            csr_values=row.get("csr_values", []),
            csr_col_indices=row.get("csr_col_indices", []),
            csr_row_ptr=row.get("csr_row_ptr", []),
            avg_importance=row.get("avg_importance", 0.0),
            token_count=row.get("token_count", 0),
            is_sparse=row.get("is_sparse", False),
            sparsity_rate=row.get("sparsity_rate", 0.0),
            created_at=row.get("created_at"),
            last_accessed=row.get("last_accessed"),
            access_count=row.get("access_count", 0)
        )


@dataclass
class SparsityDecision:
    id: UUID = field(default_factory=uuid4)
    session_id: UUID = field(default_factory=uuid4)
    context_length: int = 0
    complexity_score: float = 0.0
    complexity_method: str = "attention_entropy"
    sparsity_rate: float = 0.5
    kv_pairs_total: int = 0
    kv_pairs_retained: int = 0
    memory_before_mb: float = 0.0
    memory_after_mb: float = 0.0
    memory_saved_mb: float = 0.0
    compression_ratio: float = 0.0
    latency_ms: float = 0.0
    stage: str = "stable"
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "id": str(self.id),
            "session_id": str(self.session_id),
            "context_length": self.context_length,
            "complexity_score": self.complexity_score,
            "complexity_method": self.complexity_method,
            "sparsity_rate": self.sparsity_rate,
            "kv_pairs_total": self.kv_pairs_total,
            "kv_pairs_retained": self.kv_pairs_retained,
            "memory_before_mb": self.memory_before_mb,
            "memory_after_mb": self.memory_after_mb,
            "memory_saved_mb": self.memory_saved_mb,
            "compression_ratio": self.compression_ratio,
            "latency_ms": self.latency_ms,
            "stage": self.stage,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_db_row(cls, row: Dict) -> 'SparsityDecision':
        return cls(
            id=row["id"],
            session_id=row["session_id"],
            context_length=row.get("context_length", 0),
            complexity_score=row.get("complexity_score", 0.0),
            complexity_method=row.get("complexity_method", "attention_entropy"),
            sparsity_rate=row.get("sparsity_rate", 0.5),
            kv_pairs_total=row.get("kv_pairs_total", 0),
            kv_pairs_retained=row.get("kv_pairs_retained", 0),
            memory_before_mb=row.get("memory_before_mb", 0.0),
            memory_after_mb=row.get("memory_after_mb", 0.0),
            memory_saved_mb=row.get("memory_saved_mb", 0.0),
            compression_ratio=row.get("compression_ratio", 0.0),
            latency_ms=row.get("latency_ms", 0.0),
            stage=row.get("stage", "stable"),
            created_at=row.get("created_at")
        )


@dataclass
class PerformanceMetric:
    id: UUID = field(default_factory=uuid4)
    session_id: Optional[UUID] = None
    metric_type: str = ""
    metric_name: str = ""
    value: float = 0.0
    unit: str = ""
    metadata: Dict = field(default_factory=dict)
    recorded_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "id": str(self.id),
            "session_id": str(self.session_id) if self.session_id else None,
            "metric_type": self.metric_type,
            "metric_name": self.metric_name,
            "value": self.value,
            "unit": self.unit,
            "metadata": self.metadata,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None
        }


@dataclass
class SparsityConfig:
    id: UUID = field(default_factory=uuid4)
    model_name: str = "default"
    min_sparsity: float = 0.3
    max_sparsity: float = 0.7
    default_sparsity: float = 0.5
    warmup_steps: int = 128
    block_size: int = 64
    decay_lambda: float = 0.1
    window_size: int = 512
    sample_size: int = 64
    complexity_threshold_low: float = 0.3
    complexity_threshold_high: float = 0.7
    enable_adaptive: bool = True
    enable_position_decay: bool = True
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "id": str(self.id),
            "model_name": self.model_name,
            "min_sparsity": self.min_sparsity,
            "max_sparsity": self.max_sparsity,
            "default_sparsity": self.default_sparsity,
            "warmup_steps": self.warmup_steps,
            "block_size": self.block_size,
            "decay_lambda": self.decay_lambda,
            "window_size": self.window_size,
            "sample_size": self.sample_size,
            "complexity_threshold_low": self.complexity_threshold_low,
            "complexity_threshold_high": self.complexity_threshold_high,
            "enable_adaptive": self.enable_adaptive,
            "enable_position_decay": self.enable_position_decay,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_db_row(cls, row: Dict) -> 'SparsityConfig':
        return cls(
            id=row["id"],
            model_name=row.get("model_name", "default"),
            min_sparsity=row.get("min_sparsity", 0.3),
            max_sparsity=row.get("max_sparsity", 0.7),
            default_sparsity=row.get("default_sparsity", 0.5),
            warmup_steps=row.get("warmup_steps", 128),
            block_size=row.get("block_size", 64),
            decay_lambda=row.get("decay_lambda", 0.1),
            window_size=row.get("window_size", 512),
            sample_size=row.get("sample_size", 64),
            complexity_threshold_low=row.get("complexity_threshold_low", 0.3),
            complexity_threshold_high=row.get("complexity_threshold_high", 0.7),
            enable_adaptive=row.get("enable_adaptive", True),
            enable_position_decay=row.get("enable_position_decay", True),
            is_active=row.get("is_active", True),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at")
        )


@dataclass
class ImportanceScore:
    index: int
    qk_score: float = 0.0
    position_decay: float = 1.0
    combined_score: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            "index": self.index,
            "qk_score": self.qk_score,
            "position_decay": self.position_decay,
            "combined_score": self.combined_score
        }


@dataclass
class SparseCacheResult:
    indices: List[int]
    importance_scores: List[ImportanceScore]
    sparsity_rate: float
    kv_pairs_retained: int
    kv_pairs_total: int
    memory_saved_mb: float = 0.0
    compression_ratio: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            "indices": self.indices,
            "importance_scores": [s.to_dict() for s in self.importance_scores],
            "sparsity_rate": self.sparsity_rate,
            "kv_pairs_retained": self.kv_pairs_retained,
            "kv_pairs_total": self.kv_pairs_total,
            "memory_saved_mb": self.memory_saved_mb,
            "compression_ratio": self.compression_ratio
        }


@dataclass
class CASKContext:
    session_id: UUID
    step: int = 0
    context_length: int = 0
    current_sparsity: float = 0.5
    is_warmup: bool = True
    complexity_score: float = 0.5
    stage: str = "warmup"
    
    def update_stage(self, warmup_steps: int):
        if self.step < warmup_steps:
            self.stage = "warmup"
            self.is_warmup = True
        elif self.step < warmup_steps * 2:
            self.stage = "rampup"
            self.is_warmup = False
        else:
            self.stage = "stable"
            self.is_warmup = False
    
    def to_dict(self) -> Dict:
        return {
            "session_id": str(self.session_id),
            "step": self.step,
            "context_length": self.context_length,
            "current_sparsity": self.current_sparsity,
            "is_warmup": self.is_warmup,
            "complexity_score": self.complexity_score,
            "stage": self.stage
        }
