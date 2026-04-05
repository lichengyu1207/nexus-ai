"""
统一监控告警系统
Unified Monitoring and Alerting System

集成Jaeger分布式追踪、Prometheus指标、Grafana可视化
"""

import asyncio
import json
import uuid
import time
import hashlib
import random
from enum import Enum
from typing import Dict, List, Optional, Any, Set, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class SpanKind(Enum):
    SERVER = "server"
    CLIENT = "client"
    PRODUCER = "producer"
    CONSUMER = "consumer"
    INTERNAL = "internal"


class SpanStatus(Enum):
    OK = "ok"
    ERROR = "error"
    UNSET = "unset"


class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class AlertStatus(Enum):
    FIRING = "firing"
    RESOLVED = "resolved"
    PENDING = "pending"
    SILENCED = "silenced"


@dataclass
class SpanContext:
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    trace_flags: int = 1
    trace_state: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "trace_flags": self.trace_flags,
            "trace_state": self.trace_state,
        }
    
    def to_w3c_header(self) -> str:
        return f"00-{self.trace_id}-{self.span_id}-0{self.trace_flags:01d}"


@dataclass
class Span:
    span_id: str
    trace_id: str
    parent_span_id: Optional[str]
    operation_name: str
    kind: SpanKind
    start_time: float
    end_time: float = 0
    duration_ns: int = 0
    status: SpanStatus = SpanStatus.UNSET
    status_message: str = ""
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)
    links: List[Dict[str, Any]] = field(default_factory=list)
    service_name: str = ""
    resource_attributes: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "span_id": self.span_id,
            "trace_id": self.trace_id,
            "parent_span_id": self.parent_span_id,
            "operation_name": self.operation_name,
            "kind": self.kind.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ns": self.duration_ns,
            "duration_ms": self.duration_ns / 1_000_000,
            "status": self.status.value,
            "status_message": self.status_message,
            "attributes": self.attributes,
            "events": self.events,
            "links": self.links,
            "service_name": self.service_name,
            "resource_attributes": self.resource_attributes,
        }
    
    def add_event(self, name: str, attributes: Dict[str, Any] = None) -> None:
        self.events.append({
            "name": name,
            "timestamp": time.time(),
            "attributes": attributes or {},
        })
    
    def set_attribute(self, key: str, value: Any) -> None:
        self.attributes[key] = value
    
    def set_status(self, status: SpanStatus, message: str = "") -> None:
        self.status = status
        self.status_message = message
    
    def end(self) -> None:
        self.end_time = time.time()
        self.duration_ns = int((self.end_time - self.start_time) * 1_000_000_000)


@dataclass
class Trace:
    trace_id: str
    root_span: Optional[str] = None
    spans: List[Span] = field(default_factory=list)
    services: Set[str] = field(default_factory=set)
    total_duration_ms: float = 0
    span_count: int = 0
    error_count: int = 0
    created_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "root_span": self.root_span,
            "spans": [s.to_dict() for s in self.spans],
            "services": list(self.services),
            "total_duration_ms": self.total_duration_ms,
            "span_count": self.span_count,
            "error_count": self.error_count,
            "created_at": self.created_at,
        }
    
    def add_span(self, span: Span) -> None:
        self.spans.append(span)
        self.services.add(span.service_name)
        self.span_count += 1
        if span.status == SpanStatus.ERROR:
            self.error_count += 1
        if span.parent_span_id is None:
            self.root_span = span.span_id
            self.total_duration_ms = span.duration_ns / 1_000_000


@dataclass
class Metric:
    metric_id: str
    name: str
    metric_type: MetricType
    labels: Dict[str, str]
    value: float
    timestamp: float = field(default_factory=time.time)
    description: str = ""
    unit: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_id": self.metric_id,
            "name": self.name,
            "type": self.metric_type.value,
            "labels": self.labels,
            "value": self.value,
            "timestamp": self.timestamp,
            "description": self.description,
            "unit": self.unit,
        }
    
    def to_prometheus_format(self) -> str:
        labels_str = ",".join(f'{k}="{v}"' for k, v in self.labels.items())
        if labels_str:
            return f"{self.name}{{{labels_str}}} {self.value}"
        return f"{self.name} {self.value}"


@dataclass
class AlertRule:
    rule_id: str
    name: str
    expr: str
    severity: AlertSeverity
    duration: int = 60
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)
    enabled: bool = True
    for_duration: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "expr": self.expr,
            "severity": self.severity.value,
            "duration": self.duration,
            "labels": self.labels,
            "annotations": self.annotations,
            "enabled": self.enabled,
            "for_duration": self.for_duration,
        }


@dataclass
class Alert:
    alert_id: str
    rule_id: str
    rule_name: str
    severity: AlertSeverity
    status: AlertStatus
    labels: Dict[str, str]
    annotations: Dict[str, str]
    starts_at: float
    ends_at: Optional[float] = None
    value: float = 0
    fingerprint: str = ""
    silenced_by: Optional[str] = None
    notified: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "severity": self.severity.value,
            "status": self.status.value,
            "labels": self.labels,
            "annotations": self.annotations,
            "starts_at": self.starts_at,
            "ends_at": self.ends_at,
            "value": self.value,
            "fingerprint": self.fingerprint,
            "silenced_by": self.silenced_by,
            "notified": self.notified,
        }


DEFAULT_ALERT_RULES = [
    {
        "name": "HighErrorRate",
        "expr": "rate(http_errors_total[5m]) > 0.05",
        "severity": AlertSeverity.ERROR,
        "duration": 60,
        "labels": {"team": "backend"},
        "annotations": {"summary": "High error rate detected"},
    },
    {
        "name": "HighLatency",
        "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1",
        "severity": AlertSeverity.WARNING,
        "duration": 120,
        "labels": {"team": "backend"},
        "annotations": {"summary": "High latency detected"},
    },
    {
        "name": "HighCPUUsage",
        "expr": "cpu_usage_percent > 80",
        "severity": AlertSeverity.WARNING,
        "duration": 300,
        "labels": {"team": "infra"},
        "annotations": {"summary": "High CPU usage"},
    },
    {
        "name": "HighMemoryUsage",
        "expr": "memory_usage_percent > 85",
        "severity": AlertSeverity.WARNING,
        "duration": 300,
        "labels": {"team": "infra"},
        "annotations": {"summary": "High memory usage"},
    },
    {
        "name": "AgentClusterDown",
        "expr": "agent_cluster_healthy == 0",
        "severity": AlertSeverity.CRITICAL,
        "duration": 30,
        "labels": {"team": "ai"},
        "annotations": {"summary": "Agent cluster is down"},
    },
    {
        "name": "SlowTrace",
        "expr": "trace_duration_ms > 5000",
        "severity": AlertSeverity.WARNING,
        "duration": 60,
        "labels": {"team": "backend"},
        "annotations": {"summary": "Slow trace detected"},
    },
]


class Tracer:
    def __init__(self, service_name: str, jaeger_collector: Optional[Any] = None):
        self.service_name = service_name
        self.jaeger_collector = jaeger_collector
        self._current_span: Optional[Span] = None
        self._span_stack: List[Span] = []
    
    def start_span(self, operation_name: str, kind: SpanKind = SpanKind.SERVER,
                   parent_context: SpanContext = None, attributes: Dict[str, Any] = None) -> Span:
        trace_id = parent_context.trace_id if parent_context else self._generate_trace_id()
        span_id = self._generate_span_id()
        parent_span_id = parent_context.span_id if parent_context else None
        
        if self._current_span:
            parent_span_id = self._current_span.span_id
            trace_id = self._current_span.trace_id
        
        span = Span(
            span_id=span_id,
            trace_id=trace_id,
            parent_span_id=parent_span_id,
            operation_name=operation_name,
            kind=kind,
            start_time=time.time(),
            service_name=self.service_name,
            attributes=attributes or {},
        )
        
        self._span_stack.append(span)
        self._current_span = span
        
        return span
    
    def end_span(self, span: Span) -> None:
        span.end()
        
        if self._span_stack and self._span_stack[-1].span_id == span.span_id:
            self._span_stack.pop()
        
        if self._span_stack:
            self._current_span = self._span_stack[-1]
        else:
            self._current_span = None
    
    def get_current_span(self) -> Optional[Span]:
        return self._current_span
    
    def get_current_context(self) -> Optional[SpanContext]:
        if self._current_span:
            return SpanContext(
                trace_id=self._current_span.trace_id,
                span_id=self._current_span.span_id,
                parent_span_id=self._current_span.parent_span_id,
            )
        return None
    
    def _generate_trace_id(self) -> str:
        return uuid.uuid4().hex + uuid.uuid4().hex
    
    def _generate_span_id(self) -> str:
        return uuid.uuid4().hex[:16]


class MetricsCollector:
    def __init__(self, namespace: str = "five_end"):
        self.namespace = namespace
        self._metrics: Dict[str, List[Metric]] = defaultdict(list)
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = defaultdict(float)
        self._histograms: Dict[str, List[float]] = defaultdict(list)
        self._lock = asyncio.Lock()
    
    async def counter(self, name: str, value: float = 1,
                       labels: Dict[str, str] = None) -> None:
        async with self._lock:
            full_name = f"{self.namespace}_{name}"
            key = self._make_key(full_name, labels or {})
            self._counters[key] += value
            
            metric = Metric(
                metric_id=str(uuid.uuid4()),
                name=full_name,
                metric_type=MetricType.COUNTER,
                labels=labels or {},
                value=self._counters[key],
            )
            self._metrics[full_name].append(metric)
    
    async def gauge(self, name: str, value: float,
                     labels: Dict[str, str] = None) -> None:
        async with self._lock:
            full_name = f"{self.namespace}_{name}"
            key = self._make_key(full_name, labels or {})
            self._gauges[key] = value
            
            metric = Metric(
                metric_id=str(uuid.uuid4()),
                name=full_name,
                metric_type=MetricType.GAUGE,
                labels=labels or {},
                value=value,
            )
            self._metrics[full_name].append(metric)
    
    async def histogram(self, name: str, value: float,
                         labels: Dict[str, str] = None,
                         buckets: List[float] = None) -> None:
        async with self._lock:
            full_name = f"{self.namespace}_{name}"
            key = self._make_key(full_name, labels or {})
            self._histograms[key].append(value)
            
            metric = Metric(
                metric_id=str(uuid.uuid4()),
                name=full_name,
                metric_type=MetricType.HISTOGRAM,
                labels=labels or {},
                value=value,
            )
            self._metrics[full_name].append(metric)
    
    async def timing(self, name: str, duration_ms: float,
                      labels: Dict[str, str] = None) -> None:
        await self.histogram(f"{name}_seconds", duration_ms / 1000, labels)
    
    def _make_key(self, name: str, labels: Dict[str, str]) -> str:
        if not labels:
            return name
        labels_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}:{labels_str}"
    
    async def get_metrics(self, name: str = None, limit: int = 100) -> List[Metric]:
        if name:
            return self._metrics.get(name, [])[-limit:]
        
        all_metrics = []
        for metrics in self._metrics.values():
            all_metrics.extend(metrics[-limit:])
        return all_metrics
    
    async def get_prometheus_output(self) -> str:
        lines = []
        
        for key, value in self._counters.items():
            name = key.split(":")[0] if ":" in key else key
            lines.append(f"# TYPE {name} counter")
            lines.append(f"{name} {value}")
        
        for key, value in self._gauges.items():
            name = key.split(":")[0] if ":" in key else key
            lines.append(f"# TYPE {name} gauge")
            lines.append(f"{name} {value}")
        
        return "\n".join(lines)
    
    async def get_statistics(self) -> Dict[str, Any]:
        return {
            "total_counters": len(self._counters),
            "total_gauges": len(self._gauges),
            "total_histograms": len(self._histograms),
            "total_metrics": sum(len(m) for m in self._metrics.values()),
        }


class AlertManager:
    def __init__(self, notification_handler: Optional[Callable] = None):
        self.notification_handler = notification_handler
        
        self._rules: Dict[str, AlertRule] = {}
        self._alerts: Dict[str, Alert] = {}
        self._silences: Dict[str, Dict[str, Any]] = {}
        
        self._lock = asyncio.Lock()
        self._initialize_default_rules()
    
    def _initialize_default_rules(self) -> None:
        for rule_data in DEFAULT_ALERT_RULES:
            rule = AlertRule(
                rule_id=str(uuid.uuid4()),
                **rule_data,
            )
            self._rules[rule.name] = rule
    
    def add_rule(self, rule: AlertRule) -> None:
        self._rules[rule.name] = rule
    
    def remove_rule(self, rule_name: str) -> bool:
        if rule_name in self._rules:
            del self._rules[rule_name]
            return True
        return False
    
    async def evaluate_rules(self, metrics: Dict[str, float]) -> List[Alert]:
        async with self._lock:
            new_alerts = []
            
            for rule in self._rules.values():
                if not rule.enabled:
                    continue
                
                try:
                    triggered = self._evaluate_expr(rule.expr, metrics)
                    
                    if triggered:
                        alert = await self._create_or_update_alert(rule, metrics)
                        if alert:
                            new_alerts.append(alert)
                except Exception as e:
                    logger.error(f"Error evaluating rule {rule.name}: {e}")
            
            return new_alerts
    
    def _evaluate_expr(self, expr: str, metrics: Dict[str, float]) -> bool:
        try:
            if ">" in expr:
                parts = expr.split(">")
                metric_name = parts[0].strip()
                threshold = float(parts[1].strip())
                return metrics.get(metric_name, 0) > threshold
            elif "<" in expr:
                parts = expr.split("<")
                metric_name = parts[0].strip()
                threshold = float(parts[1].strip())
                return metrics.get(metric_name, 0) < threshold
            elif "==" in expr:
                parts = expr.split("==")
                metric_name = parts[0].strip()
                value = float(parts[1].strip())
                return metrics.get(metric_name, 0) == value
            return False
        except Exception:
            return False
    
    async def _create_or_update_alert(self, rule: AlertRule,
                                        metrics: Dict[str, float]) -> Optional[Alert]:
        fingerprint = self._compute_fingerprint(rule.name, rule.labels)
        
        existing_alert = None
        for alert in self._alerts.values():
            if alert.fingerprint == fingerprint and alert.status == AlertStatus.FIRING:
                existing_alert = alert
                break
        
        if existing_alert:
            return None
        
        alert = Alert(
            alert_id=str(uuid.uuid4()),
            rule_id=rule.rule_id,
            rule_name=rule.name,
            severity=rule.severity,
            status=AlertStatus.FIRING,
            labels=rule.labels.copy(),
            annotations=rule.annotations.copy(),
            starts_at=time.time(),
            value=metrics.get(rule.expr.split(">")[0].strip(), 0),
            fingerprint=fingerprint,
        )
        
        self._alerts[alert.alert_id] = alert
        
        if self.notification_handler:
            try:
                await self.notification_handler(alert)
            except Exception as e:
                logger.error(f"Notification handler error: {e}")
        
        logger.warning(f"Alert fired: {rule.name}")
        return alert
    
    def _compute_fingerprint(self, rule_name: str, labels: Dict[str, str]) -> str:
        data = f"{rule_name}:{json.dumps(labels, sort_keys=True)}"
        return hashlib.md5(data.encode()).hexdigest()
    
    async def resolve_alert(self, alert_id: str) -> bool:
        async with self._lock:
            alert = self._alerts.get(alert_id)
            if not alert:
                return False
            
            alert.status = AlertStatus.RESOLVED
            alert.ends_at = time.time()
            
            logger.info(f"Alert resolved: {alert.rule_name}")
            return True
    
    async def silence_alert(self, alert_id: str, duration: int,
                              silenced_by: str) -> bool:
        async with self._lock:
            alert = self._alerts.get(alert_id)
            if not alert:
                return False
            
            alert.status = AlertStatus.SILENCED
            alert.silenced_by = silenced_by
            
            silence_id = str(uuid.uuid4())
            self._silences[silence_id] = {
                "alert_id": alert_id,
                "silenced_by": silenced_by,
                "duration": duration,
                "starts_at": time.time(),
                "ends_at": time.time() + duration,
            }
            
            return True
    
    async def get_alerts(self, status: AlertStatus = None) -> List[Alert]:
        alerts = list(self._alerts.values())
        if status:
            alerts = [a for a in alerts if a.status == status]
        return alerts
    
    async def get_rules(self) -> List[AlertRule]:
        return list(self._rules.values())


class DistributedTracingSystem:
    def __init__(self, jaeger_endpoint: str = "http://localhost:14268/api/traces"):
        self.jaeger_endpoint = jaeger_endpoint
        
        self._tracers: Dict[str, Tracer] = {}
        self._traces: Dict[str, Trace] = {}
        self._spans: List[Span] = []
        
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager()
        
        self._lock = asyncio.Lock()
        self._running = False
        self._tasks: List[asyncio.Task] = []
    
    def get_tracer(self, service_name: str) -> Tracer:
        if service_name not in self._tracers:
            self._tracers[service_name] = Tracer(service_name, self)
        return self._tracers[service_name]
    
    async def start(self) -> None:
        self._running = True
        self._tasks.append(asyncio.create_task(self._export_traces()))
        self._tasks.append(asyncio.create_task(self._evaluate_alerts()))
        self._tasks.append(asyncio.create_task(self._cleanup_old_data()))
        logger.info("DistributedTracingSystem started")
    
    async def stop(self) -> None:
        self._running = False
        for task in self._tasks:
            task.cancel()
        self._tasks.clear()
        logger.info("DistributedTracingSystem stopped")
    
    async def record_span(self, span: Span) -> None:
        async with self._lock:
            self._spans.append(span)
            
            trace_id = span.trace_id
            if trace_id not in self._traces:
                self._traces[trace_id] = Trace(trace_id=trace_id)
            
            self._traces[trace_id].add_span(span)
            
            await self.metrics_collector.timing(
                "span_duration",
                span.duration_ns / 1_000_000,
                {
                    "service": span.service_name,
                    "operation": span.operation_name,
                    "status": span.status.value,
                }
            )
    
    async def record_trace_complete(self, trace: Trace) -> None:
        async with self._lock:
            await self.metrics_collector.gauge(
                "trace_duration_ms",
                trace.total_duration_ms,
                {"services": ",".join(trace.services)},
            )
            
            await self.metrics_collector.counter(
                "traces_total",
                1,
                {"error": str(trace.error_count > 0)},
            )
    
    async def _export_traces(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(10)
                
                async with self._lock:
                    if self._spans:
                        logger.debug(f"Exporting {len(self._spans)} spans")
                        self._spans = []
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Export traces error: {e}")
    
    async def _evaluate_alerts(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(30)
                
                metrics = {
                    "cpu_usage_percent": random.uniform(20, 90),
                    "memory_usage_percent": random.uniform(30, 85),
                    "http_errors_total": random.uniform(0, 0.1),
                    "trace_duration_ms": random.uniform(100, 2000),
                }
                
                await self.alert_manager.evaluate_rules(metrics)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Evaluate alerts error: {e}")
    
    async def _cleanup_old_data(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(3600)
                
                async with self._lock:
                    cutoff_time = time.time() - 86400
                    
                    self._traces = {
                        tid: t for tid, t in self._traces.items()
                        if t.created_at >= cutoff_time
                    }
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
    
    async def get_trace(self, trace_id: str) -> Optional[Trace]:
        return self._traces.get(trace_id)
    
    async def search_traces(self, service_name: str = None,
                             operation_name: str = None,
                             min_duration_ms: float = None,
                             max_duration_ms: float = None,
                             has_errors: bool = None,
                             limit: int = 100) -> List[Trace]:
        traces = list(self._traces.values())
        
        if service_name:
            traces = [t for t in traces if service_name in t.services]
        
        if min_duration_ms is not None:
            traces = [t for t in traces if t.total_duration_ms >= min_duration_ms]
        
        if max_duration_ms is not None:
            traces = [t for t in traces if t.total_duration_ms <= max_duration_ms]
        
        if has_errors is not None:
            if has_errors:
                traces = [t for t in traces if t.error_count > 0]
            else:
                traces = [t for t in traces if t.error_count == 0]
        
        return traces[:limit]
    
    async def get_service_dependencies(self) -> Dict[str, Set[str]]:
        dependencies = defaultdict(set)
        
        for trace in self._traces.values():
            services = list(trace.services)
            for i in range(len(services) - 1):
                dependencies[services[i]].add(services[i + 1])
        
        return {k: list(v) for k, v in dependencies.items()}
    
    async def get_statistics(self) -> Dict[str, Any]:
        metrics_stats = await self.metrics_collector.get_statistics()
        alerts = await self.alert_manager.get_alerts(AlertStatus.FIRING)
        
        return {
            "total_traces": len(self._traces),
            "total_spans": len(self._spans),
            "active_alerts": len(alerts),
            "services": len(self._tracers),
            **metrics_stats,
        }


class MonitoringDashboard:
    def __init__(self, tracing_system: DistributedTracingSystem):
        self.tracing = tracing_system
    
    async def get_overview(self) -> Dict[str, Any]:
        stats = await self.tracing.get_statistics()
        
        return {
            "timestamp": time.time(),
            "statistics": stats,
            "health_status": "healthy" if stats["active_alerts"] == 0 else "degraded",
        }
    
    async def get_service_map(self) -> Dict[str, Any]:
        dependencies = await self.tracing.get_service_dependencies()
        
        nodes = [{"id": svc, "name": svc} for svc in dependencies.keys()]
        edges = []
        
        for source, targets in dependencies.items():
            for target in targets:
                edges.append({"source": source, "target": target})
        
        return {
            "nodes": nodes,
            "edges": edges,
        }
    
    async def get_latency_percentiles(self) -> Dict[str, float]:
        traces = list(self.tracing._traces.values())
        
        if not traces:
            return {"p50": 0, "p90": 0, "p95": 0, "p99": 0}
        
        durations = sorted([t.total_duration_ms for t in traces])
        n = len(durations)
        
        return {
            "p50": durations[int(n * 0.5)] if n > 0 else 0,
            "p90": durations[int(n * 0.9)] if n > 0 else 0,
            "p95": durations[int(n * 0.95)] if n > 0 else 0,
            "p99": durations[int(n * 0.99)] if n > 0 else 0,
        }
    
    async def get_error_rate(self) -> float:
        traces = list(self.tracing._traces.values())
        
        if not traces:
            return 0.0
        
        error_traces = sum(1 for t in traces if t.error_count > 0)
        return error_traces / len(traces)
    
    async def get_throughput(self, window_seconds: int = 60) -> float:
        cutoff_time = time.time() - window_seconds
        
        recent_traces = [
            t for t in self.tracing._traces.values()
            if t.created_at >= cutoff_time
        ]
        
        return len(recent_traces) / window_seconds
