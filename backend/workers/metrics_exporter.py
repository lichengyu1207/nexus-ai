"""
Prometheus指标导出器
Prometheus Metrics Exporter

导出系统运行指标供Prometheus监控
"""

import os
import logging
from typing import Dict, List
from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST

logger = logging.getLogger(__name__)


class MetricsCollector:
    """指标收集器"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.defense_requests_total = Counter(
            'defense_requests_total',
            'Total defense requests processed'
        )
        
        self.defense_success_total = Counter(
            'defense_success_total',
            'Total successful defense actions'
        )
        
        self.defense_failure_total = Counter(
            'defense_failure_total',
            'Total failed defense actions'
        )
        
        self.defense_latency_seconds = Histogram(
            'defense_latency_seconds',
            'Defense decision latency in seconds'
        )
        
        self.attack_requests_total = Counter(
            'attack_requests_total',
            'Total attack requests detected'
        )
        
        self.attack_blocked_total = Counter(
            'attack_blocked_total',
            'Total attacks blocked'
        )
        
        self.attack_missed_total = Counter(
            'attack_missed_total',
            'Total attacks missed'
        )
        
        self.false_positive_total = Counter(
            'false_positive_total',
            'Total false positives'
        )
        
        self.model_inference_latency = Histogram(
            'model_inference_latency',
            'Model inference latency in seconds'
        )
        
        self.training_episodes_total = Counter(
            'training_episodes_total',
            'Total training episodes completed'
        )
        
        self.model_updates_total = Counter(
            'model_updates_total',
            'Total model updates'
        )
        
        self.active_workers = Gauge(
            'active_workers',
            'Number of active Celery workers'
        )
        
        self.pending_tasks = Gauge(
            'pending_tasks',
            'Number of pending Celery tasks'
        )
        
        self.cpu_usage_percent = Gauge(
            'cpu_usage_percent',
            'CPU usage percentage'
        )
        
        self.memory_usage_bytes = Gauge(
            'memory_usage_bytes',
            'Memory usage in bytes'
        )
        
        self.disk_usage_percent = Gauge(
            'disk_usage_percent',
            'Disk usage percentage'
        )
        
        self.tpr = Gauge(
            'defense_tpr',
            'Defense true positive rate'
        )
        
        self.fpr = Gauge(
            'defense_fpr',
            'Defense false positive rate'
        )
        
        self.model_version = Gauge(
            'model_version',
            'Current active model version'
        )
        
        self.training_progress = Gauge(
            'training_progress_episode',
            'Current training episode'
        )
        
        self._initialized = True
    
    def record_defense_request(self, success: bool, latency_ms: float):
        self.defense_requests_total.inc()
        if success:
            self.defense_success_total.inc()
        else:
            self.defense_failure_total.inc()
        self.defense_latency_seconds.observe(latency_ms / 1000)
    
    def record_attack(self, blocked: bool, false_positive: bool = False):
        self.attack_requests_total.inc()
        if blocked:
            self.attack_blocked_total.inc()
        else:
            self.attack_missed_total.inc()
        if false_positive:
            self.false_positive_total.inc()
    
    def record_inference_latency(self, latency_ms: float):
        self.model_inference_latency.observe(latency_ms / 1000)
    
    def record_training_progress(self, episode: int):
        self.training_episodes_total.inc()
        self.training_progress.set(episode)
    
    def record_model_update(self, version: int):
        self.model_updates_total.inc()
        self.model_version.set(version)
    
    def set_workers(self, active: int, pending: int):
        self.active_workers.set(active)
        self.pending_tasks.set(pending)
    
    def set_system_metrics(self, cpu: float, memory: int, disk: float):
        self.cpu_usage_percent.set(cpu)
        self.memory_usage_bytes.set(memory)
        self.disk_usage_percent.set(disk)
    
    def set_defense_metrics(self, tpr: float, fpr: float):
        self.tpr.set(tpr)
        self.fpr.set(fpr)
    
    def get_metrics(self) -> str:
        return generate_latest()


metrics_collector = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    return metrics_collector
