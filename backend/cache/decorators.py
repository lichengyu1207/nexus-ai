"""
缓存装饰器模块
提供便捷的缓存装饰器
"""
from .redis_client import cached, invalidate_cache, redis_client, init_redis, close_redis
from typing import Optional, Callable, Any
import functools
import asyncio


def cache_user_data(ttl: int = 300):
    """缓存用户数据"""
    return cached("user", ttl=ttl)


def cache_settings(ttl: int = 600):
    """缓存系统设置"""
    return cached("settings", ttl=ttl)


def cache_task_list(ttl: int = 30):
    """缓存任务列表"""
    return cached("tasks", ttl=ttl)


def cache_report(ttl: int = 300):
    """缓存报告数据"""
    return cached("report", ttl=ttl)


def cache_statistics(ttl: int = 60):
    """缓存统计数据"""
    return cached("stats", ttl=ttl)


def cache_api_response(key_prefix: str, ttl: int = 60):
    """缓存API响应"""
    return cached(key_prefix, ttl=ttl)


class CacheInvalidator:
    """缓存失效管理器"""
    
    @staticmethod
    async def on_user_update(user_id: int):
        """用户更新时失效缓存"""
        await invalidate_cache(f"user:*{user_id}*")
        await invalidate_cache("user:list*")
    
    @staticmethod
    async def on_settings_update():
        """设置更新时失效缓存"""
        await invalidate_cache("settings:*")
    
    @staticmethod
    async def on_task_update(task_id: int, user_id: int):
        """任务更新时失效缓存"""
        await invalidate_cache(f"tasks:*{user_id}*")
        await invalidate_cache(f"task:*{task_id}*")
    
    @staticmethod
    async def on_report_update(report_id: int, task_id: int):
        """报告更新时失效缓存"""
        await invalidate_cache(f"report:*{report_id}*")
        await invalidate_cache(f"report:task:*{task_id}*")
    
    @staticmethod
    async def on_statistics_update():
        """统计更新时失效缓存"""
        await invalidate_cache("stats:*")


def with_cache_fallback(fallback_value: Any = None):
    """缓存失败时的回退装饰器"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                return fallback_value
        return wrapper
    return decorator


class CacheWarmup:
    """缓存预热"""
    
    @staticmethod
    async def warmup_user_cache(user_id: int, db):
        """预热用户缓存"""
        from ..services.user_service import get_user_by_id
        
        user = await get_user_by_id(db, user_id)
        if user:
            cache_key = f"user:{user_id}"
            await redis_client.set(cache_key, user, ttl=300)
    
    @staticmethod
    async def warmup_settings_cache(db):
        """预热设置缓存"""
        from ..utils.settings import load_settings_cache
        
        await load_settings_cache()
    
    @staticmethod
    async def warmup_all(db):
        """预热所有缓存"""
        await CacheWarmup.warmup_settings_cache(db)


__all__ = [
    "cached",
    "invalidate_cache",
    "redis_client",
    "init_redis",
    "close_redis",
    "cache_user_data",
    "cache_settings",
    "cache_task_list",
    "cache_report",
    "cache_statistics",
    "cache_api_response",
    "CacheInvalidator",
    "CacheWarmup",
]
