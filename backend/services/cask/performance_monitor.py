# -*- coding: utf-8 -*-
"""
CASK 性能监控器模块
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
from uuid import UUID
import time
import statistics

from .models import PerformanceMetric, SparsityDecision


@dataclass
class MetricRecord:
    metric_type: str
    metric_name: str
    value: float
    unit: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)


class PerformanceMonitor:
    def __init__(self):
        self._metrics: List[MetricRecord] = []
        self._decisions: List[SparsityDecision] = []
        self._start_time = time.time()
        self._latency_history: List[float] = []
        self._memory_history: List[float] = []
        self._sparsity_history: List[float] = []
    
    def record_metric(
        self, 
        metric_type: str, 
        metric_name: str, 
        value: float,
        unit: str = "",
        metadata: Optional[Dict] = None
    ) -> PerformanceMetric:
        record = MetricRecord(
            metric_type=metric_type,
            metric_name=metric_name,
            value=value,
            unit=unit,
            metadata=metadata or {}
        )
        self._metrics.append(record)
        
        if metric_name == "latency_ms":
            self._latency_history.append(value)
        elif metric_name == "memory_mb":
            self._memory_history.append(value)
        elif metric_name == "sparsity_rate":
            self._sparsity_history.append(value)
        
        return PerformanceMetric(
            metric_type=metric_type,
            metric_name=metric_name,
            value=value,
            unit=unit,
            metadata=metadata or {}
        )
    
    def record_decision(self, decision: SparsityDecision):
        self._decisions.append(decision)
    
    def get_metrics(
        self, 
        metric_type: Optional[str] = None,
        limit: int = 100
    ) -> List[MetricRecord]:
        metrics = self._metrics
        if metric_type:
            metrics = [m for m in metrics if m.metric_type == metric_type]
        return metrics[-limit:]
    
    def get_decisions(self, limit: int = 100) -> List[SparsityDecision]:
        return self._decisions[-limit:]
    
    def get_statistics(self) -> Dict:
        stats = {
            "uptime_seconds": time.time() - self._start_time,
            "total_metrics": len(self._metrics),
            "total_decisions": len(self._decisions),
            "latency": {},
            "memory": {},
            "sparsity": {}
        }
        
        if self._latency_history:
            stats["latency"] = {
                "count": len(self._latency_history),
                "mean_ms": statistics.mean(self._latency_history),
                "median_ms": statistics.median(self._latency_history),
                "min_ms": min(self._latency_history),
                "max_ms": max(self._latency_history),
                "p95_ms": self._percentile(self._latency_history, 95),
                "p99_ms": self._percentile(self._latency_history, 99)
            }
        
        if self._memory_history:
            stats["memory"] = {
                "count": len(self._memory_history),
                "mean_mb": statistics.mean(self._memory_history),
                "min_mb": min(self._memory_history),
                "max_mb": max(self._memory_history)
            }
        
        if self._sparsity_history:
            stats["sparsity"] = {
                "count": len(self._sparsity_history),
                "mean": statistics.mean(self._sparsity_history),
                "min": min(self._sparsity_history),
                "max": max(self._sparsity_history)
            }
        
        if self._decisions:
            compression_ratios = [d.compression_ratio for d in self._decisions]
            memory_saved = [d.memory_saved_mb for d in self._decisions]
            
            stats["compression"] = {
                "total_decisions": len(self._decisions),
                "avg_compression_ratio": statistics.mean(compression_ratios) if compression_ratios else 0,
                "total_memory_saved_mb": sum(memory_saved),
                "avg_memory_saved_mb": statistics.mean(memory_saved) if memory_saved else 0
            }
        
        return stats
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        index = min(index, len(sorted_data) - 1)
        return sorted_data[index]
    
    def get_summary(self) -> Dict:
        stats = self.get_statistics()
        
        return {
            "status": "healthy",
            "uptime_seconds": stats["uptime_seconds"],
            "metrics_collected": stats["total_metrics"],
            "decisions_recorded": stats["total_decisions"],
            "avg_latency_ms": stats.get("latency", {}).get("mean_ms", 0),
            "avg_sparsity": stats.get("sparsity", {}).get("mean", 0),
            "total_memory_saved_mb": stats.get("compression", {}).get("total_memory_saved_mb", 0),
            "avg_compression_ratio": stats.get("compression", {}).get("avg_compression_ratio", 0)
        }
    
    def clear(self):
        self._metrics = []
        self._decisions = []
        self._latency_history = []
        self._memory_history = []
        self._sparsity_history = []
        self._start_time = time.time()
    
    def export_metrics(self) -> List[Dict]:
        return [
            {
                "metric_type": m.metric_type,
                "metric_name": m.metric_name,
                "value": m.value,
                "unit": m.unit,
                "timestamp": m.timestamp.isoformat(),
                "metadata": m.metadata
            }
            for m in self._metrics
        ]
    
    def export_decisions(self) -> List[Dict]:
        return [d.to_dict() for d in self._decisions]
