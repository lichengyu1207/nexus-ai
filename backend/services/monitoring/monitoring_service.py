"""
监控系统模块
Prometheus指标、OpenTelemetry链路追踪、结构化日志
"""
import asyncio
import time
import logging
import json
import os
from typing import Any, Optional, Dict, List, Callable
from dataclasses import dataclass, field
from datetime import datetime
from functools import wraps
from contextlib import contextmanager
import uuid
import traceback

try:
    from prometheus_client import Counter, Histogram, Gauge, Info, CollectorRegistry, generate_latest
    from prometheus_client import CONTENT_TYPE_LATEST
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    Counter = Histogram = Gauge = Info = None

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.trace import Status, StatusCode
    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False
    trace = None

logger = logging.getLogger(__name__)


@dataclass
class MetricsConfig:
    service_name: str = "fangdu-backend"
    service_version: str = "1.0.0"
    enable_prometheus: bool = True
    enable_tracing: bool = True
    jaeger_host: str = "localhost"
    jaeger_port: int = 6831
    sample_rate: float = 1.0


class PrometheusMetrics:
    """Prometheus指标收集器"""
    
    _instance: Optional['PrometheusMetrics'] = None
    
    def __init__(self, config: MetricsConfig = None):
        self.config = config or MetricsConfig()
        self._enabled = PROMETHEUS_AVAILABLE and self.config.enable_prometheus
        self._registry = None
        self._metrics: Dict[str, Any] = {}
        
        if self._enabled:
            self._setup_metrics()
    
    @classmethod
    def get_instance(cls, config: MetricsConfig = None) -> 'PrometheusMetrics':
        if cls._instance is None:
            cls._instance = cls(config)
        return cls._instance
    
    def _setup_metrics(self):
        if not self._enabled:
            return
        
        try:
            from prometheus_client import REGISTRY
            self._registry = REGISTRY
            
            self._metrics["http_requests_total"] = Counter(
                "http_requests_total",
                "Total HTTP requests",
                ["method", "endpoint", "status"]
            )
            
            self._metrics["http_request_duration_seconds"] = Histogram(
                "http_request_duration_seconds",
                "HTTP request duration in seconds",
                ["method", "endpoint"],
                buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
            )
            
            self._metrics["http_requests_in_progress"] = Gauge(
                "http_requests_in_progress",
                "Number of HTTP requests in progress",
                ["method", "endpoint"]
            )
            
            self._metrics["db_query_duration_seconds"] = Histogram(
                "db_query_duration_seconds",
                "Database query duration in seconds",
                ["query_type", "table"],
                buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
            )
            
            self._metrics["db_connections_active"] = Gauge(
                "db_connections_active",
                "Number of active database connections",
                ["pool"]
            )
            
            self._metrics["cache_hits_total"] = Counter(
                "cache_hits_total",
                "Total cache hits",
                ["cache_level"]
            )
            
            self._metrics["cache_misses_total"] = Counter(
                "cache_misses_total",
                "Total cache misses",
                ["cache_level"]
            )
            
            self._metrics["cache_hit_ratio"] = Gauge(
                "cache_hit_ratio",
                "Cache hit ratio",
                ["cache_level"]
            )
            
            self._metrics["task_queue_size"] = Gauge(
                "task_queue_size",
                "Task queue size",
                ["queue_name"]
            )
            
            self._metrics["task_processing_duration_seconds"] = Histogram(
                "task_processing_duration_seconds",
                "Task processing duration in seconds",
                ["task_type"],
                buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0]
            )
            
            self._metrics["circuit_breaker_state"] = Gauge(
                "circuit_breaker_state",
                "Circuit breaker state (0=closed, 1=open, 2=half_open)",
                ["name"]
            )
            
            self._metrics["rate_limit_exceeded_total"] = Counter(
                "rate_limit_exceeded_total",
                "Total rate limit exceeded events",
                ["identifier", "endpoint"]
            )
            
            self._metrics["errors_total"] = Counter(
                "errors_total",
                "Total errors",
                ["error_type", "endpoint"]
            )
            
            self._metrics["service_info"] = Info(
                "service",
                "Service information"
            )
            self._metrics["service_info"].info({
                "name": self.config.service_name,
                "version": self.config.service_version
            })
            
            logger.info("Prometheus metrics initialized")
            
        except Exception as e:
            logger.error(f"Failed to setup Prometheus metrics: {e}")
            self._enabled = False
    
    def record_http_request(
        self,
        method: str,
        endpoint: str,
        status: int,
        duration: float
    ):
        if not self._enabled:
            return
        
        try:
            self._metrics["http_requests_total"].labels(
                method=method, endpoint=endpoint, status=str(status)
            ).inc()
            
            self._metrics["http_request_duration_seconds"].labels(
                method=method, endpoint=endpoint
            ).observe(duration)
        except Exception as e:
            logger.warning(f"Failed to record HTTP request: {e}")
    
    def start_http_request(self, method: str, endpoint: str):
        if not self._enabled:
            return
        
        try:
            self._metrics["http_requests_in_progress"].labels(
                method=method, endpoint=endpoint
            ).inc()
        except Exception:
            pass
    
    def end_http_request(self, method: str, endpoint: str):
        if not self._enabled:
            return
        
        try:
            self._metrics["http_requests_in_progress"].labels(
                method=method, endpoint=endpoint
            ).dec()
        except Exception:
            pass
    
    def record_db_query(self, query_type: str, table: str, duration: float):
        if not self._enabled:
            return
        
        try:
            self._metrics["db_query_duration_seconds"].labels(
                query_type=query_type, table=table
            ).observe(duration)
        except Exception as e:
            logger.warning(f"Failed to record DB query: {e}")
    
    def set_db_connections(self, pool: str, count: int):
        if not self._enabled:
            return
        
        try:
            self._metrics["db_connections_active"].labels(pool=pool).set(count)
        except Exception:
            pass
    
    def record_cache_hit(self, cache_level: str):
        if not self._enabled:
            return
        
        try:
            self._metrics["cache_hits_total"].labels(cache_level=cache_level).inc()
        except Exception:
            pass
    
    def record_cache_miss(self, cache_level: str):
        if not self._enabled:
            return
        
        try:
            self._metrics["cache_misses_total"].labels(cache_level=cache_level).inc()
        except Exception:
            pass
    
    def set_cache_hit_ratio(self, cache_level: str, ratio: float):
        if not self._enabled:
            return
        
        try:
            self._metrics["cache_hit_ratio"].labels(cache_level=cache_level).set(ratio)
        except Exception:
            pass
    
    def set_queue_size(self, queue_name: str, size: int):
        if not self._enabled:
            return
        
        try:
            self._metrics["task_queue_size"].labels(queue_name=queue_name).set(size)
        except Exception:
            pass
    
    def record_task_processing(self, task_type: str, duration: float):
        if not self._enabled:
            return
        
        try:
            self._metrics["task_processing_duration_seconds"].labels(
                task_type=task_type
            ).observe(duration)
        except Exception:
            pass
    
    def set_circuit_breaker_state(self, name: str, state: str):
        if not self._enabled:
            return
        
        state_map = {"closed": 0, "open": 1, "half_open": 2}
        try:
            self._metrics["circuit_breaker_state"].labels(name=name).set(
                state_map.get(state, 0)
            )
        except Exception:
            pass
    
    def record_rate_limit_exceeded(self, identifier: str, endpoint: str):
        if not self._enabled:
            return
        
        try:
            self._metrics["rate_limit_exceeded_total"].labels(
                identifier=identifier, endpoint=endpoint
            ).inc()
        except Exception:
            pass
    
    def record_error(self, error_type: str, endpoint: str):
        if not self._enabled:
            return
        
        try:
            self._metrics["errors_total"].labels(
                error_type=error_type, endpoint=endpoint
            ).inc()
        except Exception:
            pass
    
    def get_metrics(self) -> bytes:
        if not self._enabled:
            return b"# Prometheus metrics disabled\n"
        
        try:
            return generate_latest(self._registry)
        except Exception as e:
            logger.error(f"Failed to generate metrics: {e}")
            return b"# Error generating metrics\n"


class TracingContext:
    """链路追踪上下文"""
    
    def __init__(self):
        self.trace_id: Optional[str] = None
        self.span_id: Optional[str] = None
        self.parent_span_id: Optional[str] = None
        self.operation_name: str = ""
        self.start_time: float = 0
        self.attributes: Dict[str, Any] = {}
        self.events: List[Dict[str, Any]] = []
        self.status: str = "ok"
    
    def set_attribute(self, key: str, value: Any):
        self.attributes[key] = value
    
    def add_event(self, name: str, attributes: Dict[str, Any] = None):
        self.events.append({
            "name": name,
            "timestamp": time.time(),
            "attributes": attributes or {}
        })
    
    def set_status(self, status: str, description: str = ""):
        self.status = status
        if description:
            self.attributes["status_description"] = description


class TracingManager:
    """链路追踪管理器"""
    
    _instance: Optional['TracingManager'] = None
    
    def __init__(self, config: MetricsConfig = None):
        self.config = config or MetricsConfig()
        self._enabled = OPENTELEMETRY_AVAILABLE and self.config.enable_tracing
        self._tracer = None
        self._current_context: Dict[str, TracingContext] = {}
        
        if self._enabled:
            self._setup_tracing()
    
    @classmethod
    def get_instance(cls, config: MetricsConfig = None) -> 'TracingManager':
        if cls._instance is None:
            cls._instance = cls(config)
        return cls._instance
    
    def _setup_tracing(self):
        if not self._enabled:
            return
        
        try:
            resource = Resource.create({
                "service.name": self.config.service_name,
                "service.version": self.config.service_version
            })
            
            provider = TracerProvider(resource=resource)
            
            try:
                from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
                exporter = OTLPSpanExporter(
                    endpoint=f"{self.config.jaeger_host}:{self.config.jaeger_port}"
                )
                provider.add_span_processor(BatchSpanProcessor(exporter))
            except ImportError:
                logger.warning("OTLP exporter not available, using console export")
            
            trace.set_tracer_provider(provider)
            self._tracer = trace.get_tracer(self.config.service_name)
            
            logger.info("OpenTelemetry tracing initialized")
            
        except Exception as e:
            logger.error(f"Failed to setup tracing: {e}")
            self._enabled = False
    
    def generate_trace_id(self) -> str:
        return str(uuid.uuid4()).replace("-", "")
    
    def generate_span_id(self) -> str:
        return str(uuid.uuid4()).replace("-", "")[:16]
    
    @contextmanager
    def start_span(self, operation_name: str, attributes: Dict[str, Any] = None):
        context = TracingContext()
        context.trace_id = self.generate_trace_id()
        context.span_id = self.generate_span_id()
        context.operation_name = operation_name
        context.start_time = time.time()
        
        if attributes:
            for key, value in attributes.items():
                context.set_attribute(key, value)
        
        self._current_context[context.span_id] = context
        
        try:
            if self._enabled and self._tracer:
                with self._tracer.start_as_current_span(operation_name) as span:
                    if attributes:
                        for key, value in attributes.items():
                            span.set_attribute(key, str(value))
                    yield context
            else:
                yield context
        except Exception as e:
            context.set_status("error", str(e))
            context.add_event("exception", {
                "type": type(e).__name__,
                "message": str(e),
                "stacktrace": traceback.format_exc()
            })
            raise
        finally:
            context.set_attribute("duration_ms", (time.time() - context.start_time) * 1000)
            self._current_context.pop(context.span_id, None)
    
    def get_current_context(self) -> Optional[TracingContext]:
        if self._current_context:
            return list(self._current_context.values())[-1]
        return None


class StructuredLogger:
    """结构化日志记录器"""
    
    def __init__(self, name: str, config: MetricsConfig = None):
        self.name = name
        self.config = config or MetricsConfig()
        self._logger = logging.getLogger(name)
        self._tracer = TracingManager.get_instance(self.config)
    
    def _format_log(self, level: str, message: str, **kwargs) -> Dict[str, Any]:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level,
            "logger": self.name,
            "message": message,
            "service": self.config.service_name,
            "version": self.config.service_version
        }
        
        context = self._tracer.get_current_context()
        if context:
            log_data["trace_id"] = context.trace_id
            log_data["span_id"] = context.span_id
        
        log_data.update(kwargs)
        
        return log_data
    
    def debug(self, message: str, **kwargs):
        log_data = self._format_log("DEBUG", message, **kwargs)
        self._logger.debug(json.dumps(log_data, default=str))
    
    def info(self, message: str, **kwargs):
        log_data = self._format_log("INFO", message, **kwargs)
        self._logger.info(json.dumps(log_data, default=str))
    
    def warning(self, message: str, **kwargs):
        log_data = self._format_log("WARNING", message, **kwargs)
        self._logger.warning(json.dumps(log_data, default=str))
    
    def error(self, message: str, exc_info: bool = False, **kwargs):
        log_data = self._format_log("ERROR", message, **kwargs)
        if exc_info:
            log_data["stacktrace"] = traceback.format_exc()
        self._logger.error(json.dumps(log_data, default=str))
    
    def critical(self, message: str, **kwargs):
        log_data = self._format_log("CRITICAL", message, **kwargs)
        self._logger.critical(json.dumps(log_data, default=str))


class MonitoringService:
    """监控服务"""
    
    _instance: Optional['MonitoringService'] = None
    
    def __init__(self, config: MetricsConfig = None):
        self.config = config or MetricsConfig()
        self._metrics = PrometheusMetrics.get_instance(self.config)
        self._tracer = TracingManager.get_instance(self.config)
        self._initialized = False
    
    @classmethod
    async def get_instance(cls, config: MetricsConfig = None) -> 'MonitoringService':
        if cls._instance is None:
            cls._instance = cls(config)
            await cls._instance.initialize()
        return cls._instance
    
    async def initialize(self) -> bool:
        if self._initialized:
            return True
        
        self._initialized = True
        logger.info("Monitoring service initialized")
        return True
    
    def get_metrics(self) -> bytes:
        return self._metrics.get_metrics()
    
    @contextmanager
    def trace(self, operation_name: str, attributes: Dict[str, Any] = None):
        with self._tracer.start_span(operation_name, attributes) as context:
            yield context
    
    def record_http_request(
        self,
        method: str,
        endpoint: str,
        status: int,
        duration: float
    ):
        self._metrics.record_http_request(method, endpoint, status, duration)
    
    def record_db_query(self, query_type: str, table: str, duration: float):
        self._metrics.record_db_query(query_type, table, duration)
    
    def record_cache_hit(self, cache_level: str):
        self._metrics.record_cache_hit(cache_level)
    
    def record_cache_miss(self, cache_level: str):
        self._metrics.record_cache_miss(cache_level)
    
    def record_error(self, error_type: str, endpoint: str):
        self._metrics.record_error(error_type, endpoint)
    
    def get_logger(self, name: str) -> StructuredLogger:
        return StructuredLogger(name, self.config)


def monitored(
    operation_name: str = None,
    record_metrics: bool = True
):
    """监控装饰器"""
    def decorator(func: Callable):
        op_name = operation_name or func.__name__
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            service = MonitoringService._instance
            
            start_time = time.time()
            
            if service:
                with service.trace(op_name) as span:
                    try:
                        result = await func(*args, **kwargs)
                        
                        if record_metrics:
                            duration = time.time() - start_time
                            service._metrics.record_http_request(
                                "INTERNAL", op_name, 200, duration
                            )
                        
                        span.set_status("ok")
                        return result
                        
                    except Exception as e:
                        if service:
                            service.record_error(type(e).__name__, op_name)
                        span.set_status("error", str(e))
                        raise
            else:
                return await func(*args, **kwargs)
        
        return async_wrapper
    return decorator


monitoring_service: Optional[MonitoringService] = None


async def get_monitoring() -> MonitoringService:
    global monitoring_service
    if monitoring_service is None:
        monitoring_service = await MonitoringService.get_instance()
    return monitoring_service


async def init_monitoring(config: MetricsConfig = None) -> bool:
    global monitoring_service
    monitoring_service = await MonitoringService.get_instance(config)
    return monitoring_service._initialized


def get_structured_logger(name: str) -> StructuredLogger:
    return StructuredLogger(name)
