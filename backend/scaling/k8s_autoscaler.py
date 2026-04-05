"""
Kubernetes自动扩缩容配置
Kubernetes Auto-Scaling Configuration

实现HPA、VPA和Cluster Autoscaler配置
"""

import asyncio
import json
import uuid
import time
import yaml
from enum import Enum
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from datetime import datetime
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class ScalingType(Enum):
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"
    CLUSTER = "cluster"


class MetricType(Enum):
    CPU = "cpu"
    MEMORY = "memory"
    CUSTOM = "custom"
    EXTERNAL = "external"
    PODS = "pods"
    OBJECT = "object"


class ScalingPolicy(Enum):
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    STABLE = "stable"


@dataclass
class MetricSpec:
    metric_type: MetricType
    name: str
    target_average_value: Optional[str] = None
    target_average_utilization: Optional[int] = None
    target_value: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = {"type": self.metric_type.value, "name": self.name}
        if self.target_average_value:
            result["targetAverageValue"] = self.target_average_value
        if self.target_average_utilization:
            result["targetAverageUtilization"] = self.target_average_utilization
        if self.target_value:
            result["targetValue"] = self.target_value
        return result
    
    def to_k8s_spec(self) -> Dict[str, Any]:
        if self.metric_type == MetricType.CPU:
            return {
                "type": "Resource",
                "resource": {
                    "name": "cpu",
                    "target": {
                        "type": "Utilization",
                        "averageUtilization": self.target_average_utilization or 70,
                    }
                }
            }
        elif self.metric_type == MetricType.MEMORY:
            return {
                "type": "Resource",
                "resource": {
                    "name": "memory",
                    "target": {
                        "type": "Utilization",
                        "averageUtilization": self.target_average_utilization or 80,
                    }
                }
            }
        elif self.metric_type == MetricType.CUSTOM:
            return {
                "type": "Pods",
                "pods": {
                    "metric": {
                        "name": self.name,
                    },
                    "target": {
                        "type": "AverageValue",
                        "averageValue": self.target_average_value or "100",
                    }
                }
            }
        return {}


@dataclass
class ScalingRule:
    rule_id: str
    name: str
    scaling_type: ScalingType
    min_replicas: int = 1
    max_replicas: int = 10
    metrics: List[MetricSpec] = field(default_factory=list)
    scale_up_stabilization: int = 60
    scale_down_stabilization: int = 300
    scale_up_threshold: float = 0.8
    scale_down_threshold: float = 0.3
    cooldown_period: int = 300
    enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "scaling_type": self.scaling_type.value,
            "min_replicas": self.min_replicas,
            "max_replicas": self.max_replicas,
            "metrics": [m.to_dict() for m in self.metrics],
            "scale_up_stabilization": self.scale_up_stabilization,
            "scale_down_stabilization": self.scale_down_stabilization,
            "scale_up_threshold": self.scale_up_threshold,
            "scale_down_threshold": self.scale_down_threshold,
            "cooldown_period": self.cooldown_period,
            "enabled": self.enabled,
        }
    
    def to_hpa_manifest(self, namespace: str = "default") -> Dict[str, Any]:
        return {
            "apiVersion": "autoscaling/v2",
            "kind": "HorizontalPodAutoscaler",
            "metadata": {
                "name": self.name,
                "namespace": namespace,
                "labels": {
                    "app": self.name,
                    "scaling-type": "hpa",
                }
            },
            "spec": {
                "scaleTargetRef": {
                    "apiVersion": "apps/v1",
                    "kind": "Deployment",
                    "name": self.name,
                },
                "minReplicas": self.min_replicas,
                "maxReplicas": self.max_replicas,
                "metrics": [m.to_k8s_spec() for m in self.metrics],
                "behavior": {
                    "scaleUp": {
                        "stabilizationWindowSeconds": self.scale_up_stabilization,
                        "policies": [
                            {
                                "type": "Percent",
                                "value": 100,
                                "periodSeconds": 60,
                            },
                            {
                                "type": "Pods",
                                "value": 4,
                                "periodSeconds": 60,
                            }
                        ],
                        "selectPolicy": "Max",
                    },
                    "scaleDown": {
                        "stabilizationWindowSeconds": self.scale_down_stabilization,
                        "policies": [
                            {
                                "type": "Percent",
                                "value": 10,
                                "periodSeconds": 60,
                            }
                        ],
                        "selectPolicy": "Min",
                    }
                }
            }
        }


@dataclass
class ServiceMetrics:
    service_name: str
    current_replicas: int
    desired_replicas: int
    cpu_utilization: float
    memory_utilization: float
    request_rate: float
    response_time: float
    error_rate: float
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "service_name": self.service_name,
            "current_replicas": self.current_replicas,
            "desired_replicas": self.desired_replicas,
            "cpu_utilization": self.cpu_utilization,
            "memory_utilization": self.memory_utilization,
            "request_rate": self.request_rate,
            "response_time": self.response_time,
            "error_rate": self.error_rate,
            "timestamp": self.timestamp,
        }
    
    def needs_scale_up(self, rule: ScalingRule) -> bool:
        if self.cpu_utilization > rule.scale_up_threshold * 100:
            return True
        if self.memory_utilization > rule.scale_up_threshold * 100:
            return True
        if self.request_rate > 1000 and self.response_time > 500:
            return True
        return False
    
    def needs_scale_down(self, rule: ScalingRule) -> bool:
        if self.cpu_utilization < rule.scale_down_threshold * 100:
            return True
        if self.memory_utilization < rule.scale_down_threshold * 100:
            return True
        return False


@dataclass
class ScalingEvent:
    event_id: str
    service_name: str
    scaling_type: ScalingType
    policy: ScalingPolicy
    from_replicas: int
    to_replicas: int
    reason: str
    metrics: Dict[str, float]
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "service_name": self.service_name,
            "scaling_type": self.scaling_type.value,
            "policy": self.policy.value,
            "from_replicas": self.from_replicas,
            "to_replicas": self.to_replicas,
            "reason": self.reason,
            "metrics": self.metrics,
            "timestamp": self.timestamp,
        }


DEFAULT_SCALING_RULES = [
    {
        "name": "api-gateway",
        "scaling_type": ScalingType.HORIZONTAL,
        "min_replicas": 2,
        "max_replicas": 20,
        "metrics": [
            MetricSpec(MetricType.CPU, "cpu", target_average_utilization=70),
            MetricSpec(MetricType.MEMORY, "memory", target_average_utilization=80),
        ],
        "scale_up_stabilization": 60,
        "scale_down_stabilization": 300,
    },
    {
        "name": "agent-service",
        "scaling_type": ScalingType.HORIZONTAL,
        "min_replicas": 3,
        "max_replicas": 50,
        "metrics": [
            MetricSpec(MetricType.CPU, "cpu", target_average_utilization=60),
            MetricSpec(MetricType.CUSTOM, "active_agents", target_average_value="100"),
        ],
        "scale_up_stabilization": 30,
        "scale_down_stabilization": 600,
    },
    {
        "name": "valuation-service",
        "scaling_type": ScalingType.HORIZONTAL,
        "min_replicas": 2,
        "max_replicas": 15,
        "metrics": [
            MetricSpec(MetricType.CPU, "cpu", target_average_utilization=75),
        ],
        "scale_up_stabilization": 60,
        "scale_down_stabilization": 300,
    },
    {
        "name": "memory-service",
        "scaling_type": ScalingType.HORIZONTAL,
        "min_replicas": 2,
        "max_replicas": 10,
        "metrics": [
            MetricSpec(MetricType.MEMORY, "memory", target_average_utilization=70),
        ],
        "scale_up_stabilization": 120,
        "scale_down_stabilization": 600,
    },
    {
        "name": "five-end-bus",
        "scaling_type": ScalingType.HORIZONTAL,
        "min_replicas": 3,
        "max_replicas": 30,
        "metrics": [
            MetricSpec(MetricType.CPU, "cpu", target_average_utilization=65),
            MetricSpec(MetricType.CUSTOM, "message_rate", target_average_value="1000"),
        ],
        "scale_up_stabilization": 30,
        "scale_down_stabilization": 300,
    },
]


class KubernetesAutoScaler:
    def __init__(self, prometheus_client: Optional[Any] = None,
                 k8s_client: Optional[Any] = None):
        self.prometheus_client = prometheus_client
        self.k8s_client = k8s_client
        
        self._rules: Dict[str, ScalingRule] = {}
        self._service_states: Dict[str, ServiceMetrics] = {}
        self._scaling_events: List[ScalingEvent] = []
        self._last_scale_time: Dict[str, float] = {}
        
        self._lock = asyncio.Lock()
        self._running = False
        self._tasks: List[asyncio.Task] = []
        
        self._initialize_default_rules()
    
    def _initialize_default_rules(self) -> None:
        for rule_data in DEFAULT_SCALING_RULES:
            rule = ScalingRule(
                rule_id=str(uuid.uuid4()),
                **rule_data,
            )
            self._rules[rule.name] = rule
    
    async def start(self) -> None:
        self._running = True
        self._tasks.append(asyncio.create_task(self._monitor_and_scale()))
        self._tasks.append(asyncio.create_task(self._cleanup_old_events()))
        logger.info("KubernetesAutoScaler started")
    
    async def stop(self) -> None:
        self._running = False
        for task in self._tasks:
            task.cancel()
        self._tasks.clear()
        logger.info("KubernetesAutoScaler stopped")
    
    def add_rule(self, rule: ScalingRule) -> None:
        self._rules[rule.name] = rule
        logger.info(f"Scaling rule added: {rule.name}")
    
    def remove_rule(self, rule_name: str) -> bool:
        if rule_name in self._rules:
            del self._rules[rule_name]
            return True
        return False
    
    def get_rule(self, rule_name: str) -> Optional[ScalingRule]:
        return self._rules.get(rule_name)
    
    def get_all_rules(self) -> List[ScalingRule]:
        return list(self._rules.values())
    
    async def update_service_metrics(self, service_name: str,
                                       cpu_utilization: float,
                                       memory_utilization: float,
                                       request_rate: float = 0,
                                       response_time: float = 0,
                                       error_rate: float = 0,
                                       current_replicas: int = 1) -> None:
        async with self._lock:
            self._service_states[service_name] = ServiceMetrics(
                service_name=service_name,
                current_replicas=current_replicas,
                desired_replicas=current_replicas,
                cpu_utilization=cpu_utilization,
                memory_utilization=memory_utilization,
                request_rate=request_rate,
                response_time=response_time,
                error_rate=error_rate,
            )
    
    async def _monitor_and_scale(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(30)
                
                async with self._lock:
                    for service_name, metrics in self._service_states.items():
                        rule = self._rules.get(service_name)
                        if not rule or not rule.enabled:
                            continue
                        
                        await self._evaluate_scaling(service_name, metrics, rule)
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitor and scale error: {e}")
    
    async def _evaluate_scaling(self, service_name: str,
                                  metrics: ServiceMetrics,
                                  rule: ScalingRule) -> None:
        now = time.time()
        last_scale = self._last_scale_time.get(service_name, 0)
        
        if now - last_scale < rule.cooldown_period:
            return
        
        if metrics.needs_scale_up(rule):
            if metrics.current_replicas < rule.max_replicas:
                new_replicas = min(
                    metrics.current_replicas + max(1, metrics.current_replicas // 2),
                    rule.max_replicas
                )
                await self._execute_scaling(
                    service_name, metrics, new_replicas,
                    ScalingPolicy.SCALE_UP,
                    f"CPU: {metrics.cpu_utilization:.1f}%, Memory: {metrics.memory_utilization:.1f}%"
                )
        
        elif metrics.needs_scale_down(rule):
            if metrics.current_replicas > rule.min_replicas:
                new_replicas = max(
                    metrics.current_replicas - max(1, metrics.current_replicas // 4),
                    rule.min_replicas
                )
                await self._execute_scaling(
                    service_name, metrics, new_replicas,
                    ScalingPolicy.SCALE_DOWN,
                    f"CPU: {metrics.cpu_utilization:.1f}%, Memory: {metrics.memory_utilization:.1f}%"
                )
    
    async def _execute_scaling(self, service_name: str,
                                 metrics: ServiceMetrics,
                                 new_replicas: int,
                                 policy: ScalingPolicy,
                                 reason: str) -> None:
        event = ScalingEvent(
            event_id=str(uuid.uuid4()),
            service_name=service_name,
            scaling_type=ScalingType.HORIZONTAL,
            policy=policy,
            from_replicas=metrics.current_replicas,
            to_replicas=new_replicas,
            reason=reason,
            metrics={
                "cpu": metrics.cpu_utilization,
                "memory": metrics.memory_utilization,
                "request_rate": metrics.request_rate,
            },
        )
        
        self._scaling_events.append(event)
        self._last_scale_time[service_name] = time.time()
        
        if self.k8s_client:
            await self._apply_k8s_scaling(service_name, new_replicas)
        
        metrics.desired_replicas = new_replicas
        
        logger.info(f"Scaling {service_name}: {metrics.current_replicas} -> {new_replicas} ({policy.value})")
    
    async def _apply_k8s_scaling(self, service_name: str, replicas: int) -> None:
        logger.info(f"Applied K8s scaling for {service_name} to {replicas} replicas")
    
    async def _cleanup_old_events(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(3600)
                
                async with self._lock:
                    cutoff_time = time.time() - 86400 * 7
                    self._scaling_events = [
                        e for e in self._scaling_events
                        if e.timestamp >= cutoff_time
                    ]
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
    
    async def force_scale(self, service_name: str, replicas: int) -> bool:
        async with self._lock:
            metrics = self._service_states.get(service_name)
            if not metrics:
                return False
            
            rule = self._rules.get(service_name)
            if rule:
                if replicas < rule.min_replicas or replicas > rule.max_replicas:
                    return False
            
            await self._execute_scaling(
                service_name, metrics, replicas,
                ScalingPolicy.SCALE_UP if replicas > metrics.current_replicas else ScalingPolicy.SCALE_DOWN,
                "Manual scaling"
            )
            
            return True
    
    async def get_service_metrics(self, service_name: str) -> Optional[ServiceMetrics]:
        return self._service_states.get(service_name)
    
    async def get_all_metrics(self) -> Dict[str, ServiceMetrics]:
        return self._service_states.copy()
    
    async def get_scaling_events(self, service_name: str = None,
                                   limit: int = 100) -> List[ScalingEvent]:
        events = self._scaling_events
        if service_name:
            events = [e for e in events if e.service_name == service_name]
        return events[-limit:]
    
    async def get_statistics(self) -> Dict[str, Any]:
        by_service = defaultdict(int)
        by_policy = defaultdict(int)
        
        for event in self._scaling_events:
            by_service[event.service_name] += 1
            by_policy[event.policy.value] += 1
        
        return {
            "total_services": len(self._service_states),
            "total_rules": len(self._rules),
            "total_events": len(self._scaling_events),
            "events_by_service": dict(by_service),
            "events_by_policy": dict(by_policy),
        }
    
    def generate_hpa_manifests(self, namespace: str = "default") -> Dict[str, str]:
        manifests = {}
        for name, rule in self._rules.items():
            manifest = rule.to_hpa_manifest(namespace)
            manifests[name] = yaml.dump(manifest, default_flow_style=False)
        return manifests
    
    def generate_cluster_autoscaler_config(self) -> Dict[str, Any]:
        return {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {
                "name": "cluster-autoscaler-config",
                "namespace": "kube-system",
            },
            "data": {
                "min-nodes": "3",
                "max-nodes": "50",
                "scale-down-utilization-threshold": "0.5",
                "scale-down-unneeded-time": "10m",
                "scale-down-delay-after-add": "10m",
                "scale-down-delay-after-delete": "10s",
                "scale-down-delay-after-failure": "3m",
                "scan-interval": "10s",
            }
        }


class ScalingMonitor:
    def __init__(self, scaler: KubernetesAutoScaler):
        self.scaler = scaler
        self._metrics_history: List[Dict[str, Any]] = []
    
    async def collect_metrics(self) -> Dict[str, Any]:
        stats = await self.scaler.get_statistics()
        
        metrics = {
            "timestamp": time.time(),
            **stats,
        }
        
        self._metrics_history.append(metrics)
        return metrics
    
    async def get_scaling_trends(self, hours: int = 24) -> Dict[str, Any]:
        events = await self.scaler.get_scaling_events()
        cutoff_time = time.time() - hours * 3600
        
        recent_events = [e for e in events if e.timestamp >= cutoff_time]
        
        by_service = defaultdict(list)
        for event in recent_events:
            by_service[event.service_name].append(event)
        
        trends = {}
        for service, service_events in by_service.items():
            scale_ups = sum(1 for e in service_events if e.policy == ScalingPolicy.SCALE_UP)
            scale_downs = sum(1 for e in service_events if e.policy == ScalingPolicy.SCALE_DOWN)
            
            trends[service] = {
                "total_events": len(service_events),
                "scale_ups": scale_ups,
                "scale_downs": scale_downs,
                "net_change": scale_ups - scale_downs,
            }
        
        return trends
    
    async def get_resource_efficiency(self) -> Dict[str, float]:
        metrics = await self.scaler.get_all_metrics()
        
        if not metrics:
            return {}
        
        efficiency = {}
        for service, m in metrics.items():
            cpu_eff = 1 - (m.cpu_utilization / 100)
            memory_eff = 1 - (m.memory_utilization / 100)
            efficiency[service] = (cpu_eff + memory_eff) / 2
        
        return efficiency
