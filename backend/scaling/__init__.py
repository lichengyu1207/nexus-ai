"""
扩缩容模块初始化
Scaling Module Initialization
"""

from .k8s_autoscaler import (
    KubernetesAutoScaler,
    ScalingRule,
    ScalingType,
    ScalingPolicy,
    MetricSpec,
    MetricType,
    ServiceMetrics,
    ScalingEvent,
    ScalingMonitor,
)

__all__ = [
    "KubernetesAutoScaler",
    "ScalingRule",
    "ScalingType",
    "ScalingPolicy",
    "MetricSpec",
    "MetricType",
    "ServiceMetrics",
    "ScalingEvent",
    "ScalingMonitor",
]
