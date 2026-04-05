"""
高性能服务API路由
提供健康检查、监控指标、服务状态等API
"""
import time
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, Request, Response, HTTPException, Depends
from fastapi.responses import PlainTextResponse, JSONResponse
from pydantic import BaseModel

router = APIRouter(prefix="/api/hp", tags=["High Performance"])


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    services: Dict[str, Any]
    version: str = "1.0.0"


class MetricsResponse(BaseModel):
    metrics: str
    content_type: str = "text/plain"


class CacheStatsResponse(BaseModel):
    l1_cache: Dict[str, Any]
    l2_cache: Dict[str, Any]
    overall: Dict[str, Any]


class RateLimitStatus(BaseModel):
    identifier: str
    allowed: bool
    remaining: int
    limit: int
    reset_at: Optional[str] = None


class CircuitBreakerStatus(BaseModel):
    name: str
    state: str
    failure_count: int
    success_count: int
    last_failure_time: Optional[str] = None


class TaskQueueStatus(BaseModel):
    initialized: bool
    use_rabbitmq: bool
    workers: Dict[str, Any]
    handlers: list


async def get_hp_service():
    from backend.services.high_performance import get_hp_service
    return await get_hp_service()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    from backend.services.fault_tolerance import get_health_status
    
    health = await get_health_status()
    
    return HealthResponse(
        status="healthy" if health.get("healthy", False) else "degraded",
        timestamp=datetime.utcnow().isoformat() + "Z",
        services=health.get("checks", {}),
        version="1.0.0"
    )


@router.get("/health/live")
async def liveness_probe():
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness_probe():
    from backend.services.fault_tolerance import get_health_status
    
    health = await get_health_status()
    
    if not health.get("healthy", False):
        raise HTTPException(status_code=503, detail="Service not ready")
    
    return {"status": "ready"}


@router.get("/metrics", response_class=PlainTextResponse)
async def prometheus_metrics():
    from backend.services.high_performance import get_all_metrics
    
    metrics = await get_all_metrics()
    return Response(
        content=metrics,
        media_type="text/plain; version=0.0.4; charset=utf-8"
    )


@router.get("/stats")
async def get_all_stats():
    service = await get_hp_service()
    return service.get_stats()


@router.get("/stats/database")
async def get_database_stats():
    from backend.services.database import get_db_service
    
    db = await get_db_service()
    return db.get_stats()


@router.get("/stats/cache", response_model=CacheStatsResponse)
async def get_cache_stats():
    from backend.services.cache import get_cache
    
    cache = await get_cache()
    stats = await cache.get_stats()
    
    return CacheStatsResponse(
        l1_cache=stats.get("l1_cache", {}),
        l2_cache=stats.get("l2_cache", {}),
        overall=stats.get("overall", {})
    )


@router.get("/stats/queue", response_model=TaskQueueStatus)
async def get_queue_stats():
    from backend.services.queue import get_task_queue
    
    queue = await get_task_queue()
    stats = queue.get_stats()
    
    return TaskQueueStatus(
        initialized=stats.get("initialized", False),
        use_rabbitmq=stats.get("use_rabbitmq", False),
        workers=stats.get("workers", {}),
        handlers=stats.get("handlers", [])
    )


@router.get("/stats/rate-limiter")
async def get_rate_limiter_stats():
    from backend.services.api import get_rate_limiter
    
    limiter = await get_rate_limiter()
    
    return {
        "enabled": limiter._use_redis,
        "configs": {}
    }


@router.get("/stats/circuit-breakers")
async def get_circuit_breakers():
    from backend.services.api import CircuitBreakerRegistry
    
    registry = CircuitBreakerRegistry.get_instance()
    return registry.get_all_stats()


@router.post("/circuit-breakers/{name}/reset")
async def reset_circuit_breaker(name: str):
    from backend.services.api import CircuitBreakerRegistry
    
    registry = CircuitBreakerRegistry.get_instance()
    breaker = registry.get_breaker(name)
    await breaker.force_close()
    
    return {"status": "reset", "name": name}


@router.get("/slow-queries")
async def get_slow_queries(limit: int = 20):
    from backend.services.database import get_db_service
    
    db = await get_db_service()
    slow_queries = db.get_slow_queries(limit)
    
    return {
        "count": len(slow_queries),
        "queries": slow_queries
    }


@router.get("/query-metrics")
async def get_query_metrics():
    from backend.services.database import get_db_service
    
    db = await get_db_service()
    metrics = db.get_query_metrics()
    
    return {
        "count": len(metrics),
        "metrics": metrics
    }


@router.post("/cache/clear")
async def clear_cache():
    from backend.services.cache import get_cache
    
    cache = await get_cache()
    await cache.l1_cache.clear()
    
    return {"status": "cleared"}


@router.delete("/cache/{key}")
async def delete_cache_key(key: str):
    from backend.services.cache import get_cache
    
    cache = await get_cache()
    await cache.delete(key)
    
    return {"status": "deleted", "key": key}


@router.post("/cache/warmup")
async def warmup_cache(keys: Dict[str, Any]):
    from backend.services.cache import get_cache
    
    cache = await get_cache()
    await cache.warmup(keys)
    
    return {"status": "warmed", "count": len(keys)}


@router.post("/tasks/submit")
async def submit_task(
    task_type: str,
    payload: Dict[str, Any],
    priority: int = 5,
    queue_name: str = "default"
):
    from backend.services.queue import get_task_queue
    
    queue = await get_task_queue()
    task_id = await queue.submit_task(
        task_type=task_type,
        payload=payload,
        priority=priority,
        queue_name=queue_name
    )
    
    return {"task_id": task_id, "status": "submitted"}


@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    from backend.services.queue import get_task_queue
    
    queue = await get_task_queue()
    status = await queue.get_task_status(task_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return status


@router.get("/queue/{queue_name}/size")
async def get_queue_size(queue_name: str = "default"):
    from backend.services.queue import get_task_queue
    
    queue = await get_task_queue()
    size = await queue.get_queue_size(queue_name)
    
    return {"queue_name": queue_name, "size": size}


@router.post("/workers/{queue_name}/start")
async def start_worker(queue_name: str, concurrency: int = 5):
    from backend.services.queue import get_task_queue
    
    queue = await get_task_queue()
    worker = await queue.start_worker(queue_name, concurrency)
    
    return {"status": "started", "queue_name": queue_name, "concurrency": concurrency}


@router.post("/workers/{queue_name}/stop")
async def stop_worker(queue_name: str):
    from backend.services.queue import get_task_queue
    
    queue = await get_task_queue()
    await queue.stop_worker(queue_name)
    
    return {"status": "stopped", "queue_name": queue_name}


@router.get("/benchmark")
async def run_benchmark():
    from backend.tests.stress_test import run_benchmark
    
    report = await run_benchmark()
    return PlainTextResponse(content=report)


@router.get("/stress-test")
async def run_stress_test(users: int = 50, duration: int = 30):
    from backend.tests.stress_test import run_stress_test
    
    results = await run_stress_test(users=users, duration=duration)
    return results


def include_router(app):
    """将路由包含到FastAPI应用"""
    app.include_router(router)
