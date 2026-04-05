"""
高并发高性能架构测试
验证所有模块功能
"""
import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestDatabaseOptimization:
    """数据库优化测试"""
    
    def test_database_config(self):
        from backend.services.database.high_performance_db import DatabaseConfig, DatabaseRole
        
        config = DatabaseConfig(
            host="localhost",
            port=5432,
            database="test_db",
            user="test_user",
            password="test_pass"
        )
        
        assert config.host == "localhost"
        assert config.port == 5432
        assert config.database == "test_db"
        assert "postgresql://" in config.dsn
    
    def test_connection_pool_stats(self):
        from backend.services.database.high_performance_db import ConnectionPoolStats
        
        stats = ConnectionPoolStats(
            pool_name="test_pool",
            size=10,
            idle=8,
            busy=2,
            min_size=5,
            max_size=20
        )
        
        assert stats.pool_name == "test_pool"
        assert stats.size == 10
        assert stats.idle == 8
        assert stats.busy == 2
    
    def test_slow_query_monitor(self):
        from backend.services.database.high_performance_db import SlowQueryMonitor
        
        monitor = SlowQueryMonitor(slow_threshold_ms=100.0)
        
        monitor.record_query("SELECT * FROM users", 50.0, True)
        monitor.record_query("SELECT * FROM large_table", 150.0, True)
        monitor.record_query("SELECT * FROM users WHERE id = 1", 200.0, True)
        
        stats = monitor.get_stats()
        assert stats["total_slow_queries"] == 2
        
        slow_queries = monitor.get_slow_queries(10)
        assert len(slow_queries) == 2
        
        metrics = monitor.get_query_metrics()
        assert len(metrics) == 3
    
    @pytest.mark.asyncio
    async def test_connection_pool_manager(self):
        from backend.services.database.high_performance_db import (
            ConnectionPoolManager, DatabaseConfig
        )
        
        config = DatabaseConfig(
            host="localhost",
            port=5432,
            database="test",
            user="test",
            password="test",
            min_connections=1,
            max_connections=5
        )
        
        manager = ConnectionPoolManager(config, "test_pool")
        
        assert manager.pool_name == "test_pool"
        assert manager._pool is None
        
        stats = manager.get_stats()
        assert stats.pool_name == "test_pool"


class TestMultiLevelCache:
    """多级缓存测试"""
    
    def test_lru_cache_basic(self):
        from backend.services.cache.multi_level_cache import LRUCache
        
        cache = LRUCache(max_size=3, default_ttl=60)
        
        asyncio.run(cache.set("key1", "value1"))
        asyncio.run(cache.set("key2", "value2"))
        asyncio.run(cache.set("key3", "value3"))
        
        result = asyncio.run(cache.get("key1"))
        assert result == "value1"
        
        result = asyncio.run(cache.get("nonexistent"))
        assert result is None
    
    def test_lru_cache_eviction(self):
        from backend.services.cache.multi_level_cache import LRUCache
        
        cache = LRUCache(max_size=2, default_ttl=60)
        
        asyncio.run(cache.set("key1", "value1"))
        asyncio.run(cache.set("key2", "value2"))
        asyncio.run(cache.set("key3", "value3"))
        
        result = asyncio.run(cache.get("key1"))
        assert result is None
        
        result = asyncio.run(cache.get("key2"))
        assert result == "value2"
        
        result = asyncio.run(cache.get("key3"))
        assert result == "value3"
    
    def test_lru_cache_stats(self):
        from backend.services.cache.multi_level_cache import LRUCache
        
        cache = LRUCache(max_size=10, default_ttl=60)
        
        asyncio.run(cache.set("key1", "value1"))
        asyncio.run(cache.get("key1"))
        asyncio.run(cache.get("key1"))
        asyncio.run(cache.get("nonexistent"))
        
        stats = cache.get_stats()
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["hit_rate"] > 0
    
    def test_cache_entry(self):
        from backend.services.cache.multi_level_cache import CacheEntry
        import time
        
        entry = CacheEntry(
            value="test_value",
            expires_at=time.time() + 60,
            created_at=time.time(),
            access_count=0
        )
        
        assert entry.value == "test_value"
        assert entry.access_count == 0
    
    def test_cache_stats(self):
        from backend.services.cache.multi_level_cache import CacheStats
        
        stats = CacheStats(hits=100, misses=10)
        
        assert stats.hits == 100
        assert stats.misses == 10
        assert stats.hit_rate > 0.9


class TestAsyncTaskQueue:
    """异步任务队列测试"""
    
    def test_task_definition(self):
        from backend.services.queue.async_task_queue import TaskDefinition, TaskStatus
        
        task = TaskDefinition(
            task_id="test-123",
            task_type="test_task",
            payload={"key": "value"}
        )
        
        assert task.task_id == "test-123"
        assert task.task_type == "test_task"
        assert task.status == TaskStatus.PENDING.value
        
        task_dict = task.to_dict()
        assert task_dict["task_id"] == "test-123"
        
        restored = TaskDefinition.from_dict(task_dict)
        assert restored.task_id == task.task_id
    
    def test_retry_policy(self):
        from backend.services.queue.async_task_queue import RetryPolicy
        
        policy = RetryPolicy(max_retries=3, base_delay=1.0)
        
        delay1 = policy.get_delay(0)
        delay2 = policy.get_delay(1)
        delay3 = policy.get_delay(2)
        
        assert delay1 < delay2 < delay3
    
    def test_task_status_enum(self):
        from backend.services.queue.async_task_queue import TaskStatus
        
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.RUNNING.value == "running"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
    
    def test_task_priority_enum(self):
        from backend.services.queue.async_task_queue import TaskPriority
        
        assert TaskPriority.LOW.value == 1
        assert TaskPriority.NORMAL.value == 5
        assert TaskPriority.HIGH.value == 10
        assert TaskPriority.CRITICAL.value == 20
    
    @pytest.mark.asyncio
    async def test_in_memory_queue(self):
        from backend.services.queue.async_task_queue import InMemoryTaskQueue, TaskDefinition
        
        queue = InMemoryTaskQueue(max_size=100)
        
        task = TaskDefinition(
            task_id="test-1",
            task_type="test",
            payload={"data": "test"}
        )
        
        result = await queue.enqueue(task)
        assert result is True
        
        size = await queue.get_queue_size()
        assert size == 1
        
        dequeued = await queue.dequeue()
        assert dequeued is not None
        assert dequeued.task_id == "test-1"


class TestAPIOptimization:
    """API优化测试"""
    
    def test_rate_limit_config(self):
        from backend.services.api.api_optimization import RateLimitConfig
        
        config = RateLimitConfig(
            requests_per_second=100,
            requests_per_minute=6000,
            burst_size=200
        )
        
        assert config.requests_per_second == 100
        assert config.requests_per_minute == 6000
        assert config.burst_size == 200
    
    def test_circuit_breaker_config(self):
        from backend.services.api.api_optimization import CircuitBreakerConfig
        
        config = CircuitBreakerConfig(
            failure_threshold=5,
            success_threshold=3,
            timeout=30.0
        )
        
        assert config.failure_threshold == 5
        assert config.success_threshold == 3
        assert config.timeout == 30.0
    
    def test_circuit_state_enum(self):
        from backend.services.api.api_optimization import CircuitState
        
        assert CircuitState.CLOSED.value == "closed"
        assert CircuitState.OPEN.value == "open"
        assert CircuitState.HALF_OPEN.value == "half_open"
    
    @pytest.mark.asyncio
    async def test_in_memory_rate_limiter(self):
        from backend.services.api.api_optimization import InMemoryRateLimiter, RateLimitConfig
        
        limiter = InMemoryRateLimiter()
        config = RateLimitConfig(requests_per_second=10, requests_per_minute=100)
        
        allowed, info = await limiter.is_allowed("test_key", config)
        assert allowed is True
        
        for _ in range(15):
            allowed, _ = await limiter.is_allowed("test_key", config)
        
        assert allowed is False
    
    @pytest.mark.asyncio
    async def test_circuit_breaker(self):
        from backend.services.api.api_optimization import CircuitBreaker, CircuitBreakerConfig, CircuitState
        
        config = CircuitBreakerConfig(failure_threshold=3)
        breaker = CircuitBreaker("test", config)
        
        assert breaker.is_closed
        assert breaker.state == CircuitState.CLOSED
        
        can_exec = await breaker.can_execute()
        assert can_exec is True
        
        await breaker.record_failure()
        await breaker.record_failure()
        await breaker.record_failure()
        
        assert breaker.is_open
        assert breaker.state == CircuitState.OPEN
        
        can_exec = await breaker.can_execute()
        assert can_exec is False
    
    def test_degradation_manager(self):
        from backend.services.api.api_optimization import DegradationManager
        
        manager = DegradationManager.get_instance()
        
        manager.set_degraded("test_feature", True)
        assert manager.is_degraded("test_feature") is True
        
        manager.set_degraded("test_feature", False)
        assert manager.is_degraded("test_feature") is False
        
        status = manager.get_status()
        assert "degraded_features" in status


class TestMonitoring:
    """监控系统测试"""
    
    def test_metrics_config(self):
        from backend.services.monitoring.monitoring_service import MetricsConfig
        
        config = MetricsConfig(
            service_name="test-service",
            service_version="1.0.0"
        )
        
        assert config.service_name == "test-service"
        assert config.service_version == "1.0.0"
    
    def test_tracing_context(self):
        from backend.services.monitoring.monitoring_service import TracingContext
        
        context = TracingContext()
        context.trace_id = "test-trace-123"
        context.span_id = "test-span-456"
        context.operation_name = "test_operation"
        
        context.set_attribute("key1", "value1")
        context.add_event("test_event", {"detail": "test"})
        
        assert context.trace_id == "test-trace-123"
        assert "key1" in context.attributes
        assert len(context.events) == 1
    
    def test_structured_logger(self):
        from backend.services.monitoring.monitoring_service import StructuredLogger, MetricsConfig
        
        config = MetricsConfig(service_name="test")
        logger = StructuredLogger("test_logger", config)
        
        log_data = logger._format_log("INFO", "test message", extra_key="extra_value")
        
        assert log_data["level"] == "INFO"
        assert log_data["message"] == "test message"
        assert log_data["service"] == "test"
        assert log_data["extra_key"] == "extra_value"


class TestFaultTolerance:
    """容错保障测试"""
    
    def test_error_severity_enum(self):
        from backend.services.fault_tolerance.fault_tolerance import ErrorSeverity
        
        assert ErrorSeverity.LOW.value == "low"
        assert ErrorSeverity.MEDIUM.value == "medium"
        assert ErrorSeverity.HIGH.value == "high"
        assert ErrorSeverity.CRITICAL.value == "critical"
    
    def test_error_category_enum(self):
        from backend.services.fault_tolerance.fault_tolerance import ErrorCategory
        
        assert ErrorCategory.BUSINESS.value == "business"
        assert ErrorCategory.VALIDATION.value == "validation"
        assert ErrorCategory.DATABASE.value == "database"
    
    def test_app_exception(self):
        from backend.services.fault_tolerance.fault_tolerance import AppException, ErrorSeverity, ErrorCategory
        
        exc = AppException(
            message="Test error",
            error_code="TEST_ERROR",
            status_code=500,
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.INTERNAL
        )
        
        assert exc.message == "Test error"
        assert exc.error_code == "TEST_ERROR"
        assert exc.status_code == 500
        
        exc_dict = exc.to_dict()
        assert exc_dict["error"] is True
        assert exc_dict["error_code"] == "TEST_ERROR"
    
    def test_business_error(self):
        from backend.services.fault_tolerance.fault_tolerance import BusinessError
        
        exc = BusinessError("Business rule violated")
        
        assert exc.message == "Business rule violated"
        assert exc.status_code == 400
    
    def test_validation_error(self):
        from backend.services.fault_tolerance.fault_tolerance import ValidationError
        
        exc = ValidationError("Invalid field value", field="email")
        
        assert exc.message == "Invalid field value"
        assert exc.status_code == 422
        assert exc.details["field"] == "email"
    
    def test_not_found_error(self):
        from backend.services.fault_tolerance.fault_tolerance import NotFoundError
        
        exc = NotFoundError("User")
        
        assert "User" in exc.message
        assert exc.status_code == 404
    
    def test_graceful_shutdown(self):
        from backend.services.fault_tolerance.fault_tolerance import GracefulShutdown
        
        shutdown = GracefulShutdown.get_instance()
        
        assert shutdown.is_shutting_down is False
        
        handler_called = []
        
        def test_handler():
            handler_called.append(True)
        
        shutdown.register_handler(test_handler)
        assert len(shutdown._shutdown_handlers) > 0


class TestIntegration:
    """集成测试"""
    
    def test_all_modules_importable(self):
        from backend.services.database import HighPerformanceDatabaseService
        from backend.services.cache import MultiLevelCache, LRUCache
        from backend.services.queue import AsyncTaskQueue, TaskDefinition
        from backend.services.api import CircuitBreaker, DistributedRateLimiter
        from backend.services.monitoring import MonitoringService, PrometheusMetrics
        from backend.services.fault_tolerance import GracefulShutdown, AppException
        
        assert HighPerformanceDatabaseService is not None
        assert MultiLevelCache is not None
        assert AsyncTaskQueue is not None
        assert CircuitBreaker is not None
        assert MonitoringService is not None
        assert GracefulShutdown is not None
    
    def test_error_context(self):
        from backend.services.fault_tolerance.fault_tolerance import ErrorContext, ErrorSeverity, ErrorCategory
        
        context = ErrorContext(
            error_id="err-123",
            timestamp="2024-01-01T00:00:00",
            error_type="TestError",
            message="Test error message",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.INTERNAL
        )
        
        assert context.error_id == "err-123"
        assert context.severity == ErrorSeverity.HIGH


def run_tests():
    pytest.main([__file__, "-v", "--tb=short"])


if __name__ == "__main__":
    run_tests()
