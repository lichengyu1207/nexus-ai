"""
缓存模块
"""
from .redis_client import (
    redis_client,
    init_redis,
    close_redis,
    cached,
    invalidate_cache,
    get_cache_key,
)
from .decorators import (
    cache_user_data,
    cache_settings,
    cache_task_list,
    cache_report,
    cache_statistics,
    cache_api_response,
    CacheInvalidator,
    CacheWarmup,
)

__all__ = [
    "redis_client",
    "init_redis",
    "close_redis",
    "cached",
    "invalidate_cache",
    "get_cache_key",
    "cache_user_data",
    "cache_settings",
    "cache_task_list",
    "cache_report",
    "cache_statistics",
    "cache_api_response",
    "CacheInvalidator",
    "CacheWarmup",
]
