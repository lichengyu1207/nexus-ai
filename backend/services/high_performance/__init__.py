"""
高并发高性能服务整合模块
统一初始化和管理所有高性能组件
"""
import asyncio
import logging
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

from ..services.database import (
    get_db_service,
    init_db_service,
    close_db_service
)
from ..services.cache import (
    get_cache,
    init_cache,
    close_cache
)
from ..services.queue import (
    get_task_queue,
    init_task_queue,
    close_task_queue
)
from ..services.api import (
    get_rate_limiter,
    init_rate_limiter,
    close_rate_limiter,
    CircuitBreakerRegistry,
    DegradationManager
)
from ..services.monitoring import (
    get_monitoring,
    init_monitoring,
    MetricsConfig
)
from ..services.fault_tolerance import (
    init_fault_tolerance,
    get_health_status,
    GracefulShutdown,
    ExceptionMiddleware
)

logger = logging.getLogger(__name__)


class HighPerformanceService:
    """高性能服务整合器"""
    
    _instance: Optional['HighPerformanceService'] = None
    _initialized = False
    
    def __init__(self):
        self._db_service = None
        self._cache = None
        self._task_queue = None
        self._rate_limiter = None
        self._monitoring = None
        self._shutdown_handler = None
    
    @classmethod
    async def get_instance(cls) -> 'HighPerformanceService':
        if cls._instance is None:
            cls._instance = cls()
            await cls._instance.initialize()
        return cls._instance
    
    async def initialize(self) -> Dict[str, bool]:
        """初始化所有高性能服务"""
        if self._initialized:
            return {"status": "already_initialized"}
        
        results = {}
        
        logger.info("Initializing high performance services...")
        
        try:
            self._db_service = await get_db_service()
            results["database"] = self._db_service._initialized
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            results["database"] = False
        
        try:
            self._cache = await get_cache()
            results["cache"] = self._cache._initialized
        except Exception as e:
            logger.error(f"Cache initialization failed: {e}")
            results["cache"] = False
        
        try:
            self._task_queue = await get_task_queue()
            results["task_queue"] = self._task_queue._initialized
        except Exception as e:
            logger.error(f"Task queue initialization failed: {e}")
            results["task_queue"] = False
        
        try:
            self._rate_limiter = await get_rate_limiter()
            results["rate_limiter"] = True
        except Exception as e:
            logger.error(f"Rate limiter initialization failed: {e}")
            results["rate_limiter"] = False
        
        try:
            self._monitoring = await get_monitoring()
            results["monitoring"] = self._monitoring._initialized
        except Exception as e:
            logger.error(f"Monitoring initialization failed: {e}")
            results["monitoring"] = False
        
        try:
            await init_fault_tolerance()
            results["fault_tolerance"] = True
        except Exception as e:
            logger.error(f"Fault tolerance initialization failed: {e}")
            results["fault_tolerance"] = False
        
        self._shutdown_handler = GracefulShutdown.get_instance()
        self._shutdown_handler.register_handler(self._cleanup)
        
        self._initialized = True
        logger.info(f"High performance services initialized: {results}")
        
        return results
    
    async def _cleanup(self):
        """清理所有服务"""
        logger.info("Cleaning up high performance services...")
        
        try:
            await close_db_service()
        except Exception as e:
            logger.error(f"Error closing database: {e}")
        
        try:
            await close_cache()
        except Exception as e:
            logger.error(f"Error closing cache: {e}")
        
        try:
            await close_task_queue()
        except Exception as e:
            logger.error(f"Error closing task queue: {e}")
        
        try:
            await close_rate_limiter()
        except Exception as e:
            logger.error(f"Error closing rate limiter: {e}")
        
        logger.info("High performance services cleanup completed")
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        health_status = await get_health_status()
        
        status = {
            "healthy": health_status.get("healthy", False),
            "timestamp": health_status.get("timestamp"),
            "services": {}
        }
        
        if self._db_service:
            db_stats = self._db_service.get_stats()
            status["services"]["database"] = {
                "healthy": self._db_service._initialized,
                "slow_queries": len(self._db_service.get_slow_queries(10))
            }
        
        if self._cache:
            cache_stats = await self._cache.get_stats()
            status["services"]["cache"] = {
                "healthy": self._cache._initialized,
                "hit_rate": cache_stats.get("overall", {}).get("hit_rate", 0)
            }
        
        if self._task_queue:
            queue_stats = self._task_queue.get_stats()
            status["services"]["task_queue"] = {
                "healthy": self._task_queue._initialized,
                "workers": len(queue_stats.get("workers", {}))
            }
        
        if self._monitoring:
            status["services"]["monitoring"] = {
                "healthy": self._monitoring._initialized
            }
        
        circuit_stats = CircuitBreakerRegistry.get_instance().get_all_stats()
        status["services"]["circuit_breakers"] = circuit_stats
        
        degradation_status = DegradationManager.get_instance().get_status()
        status["services"]["degradation"] = degradation_status
        
        return status
    
    async def get_metrics(self) -> bytes:
        """获取Prometheus指标"""
        if self._monitoring:
            return self._monitoring.get_metrics()
        return b"# Monitoring not initialized\n"
    
    def get_stats(self) -> Dict[str, Any]:
        """获取所有服务统计"""
        return {
            "initialized": self._initialized,
            "database": self._db_service.get_stats() if self._db_service else None,
            "task_queue": self._task_queue.get_stats() if self._task_queue else None,
            "monitoring": self._monitoring.get_stats() if self._monitoring else None
        }


hp_service: Optional[HighPerformanceService] = None


async def get_hp_service() -> HighPerformanceService:
    """获取高性能服务实例"""
    global hp_service
    if hp_service is None:
        hp_service = await HighPerformanceService.get_instance()
    return hp_service


async def init_high_performance() -> Dict[str, bool]:
    """初始化高性能服务"""
    global hp_service
    hp_service = await HighPerformanceService.get_instance()
    return await hp_service.initialize()


async def get_all_health() -> Dict[str, Any]:
    """获取所有服务健康状态"""
    service = await get_hp_service()
    return await service.health_check()


async def get_all_metrics() -> bytes:
    """获取所有指标"""
    service = await get_hp_service()
    return await service.get_metrics()


def get_exception_middleware(app):
    """获取异常处理中间件"""
    return ExceptionMiddleware(app)


@asynccontextmanager
async def lifespan_context(app):
    """FastAPI生命周期上下文"""
    try:
        results = await init_high_performance()
        logger.info(f"Application started: {results}")
        yield
    finally:
        shutdown = GracefulShutdown.get_instance()
        await shutdown.shutdown()
        logger.info("Application shutdown completed")
