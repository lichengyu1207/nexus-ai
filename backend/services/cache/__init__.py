"""
缓存服务模块
"""
from .multi_level_cache import (
    MultiLevelCache,
    get_cache,
    init_cache,
    close_cache,
    LRUCache,
    CacheProtection,
    DistributedLock,
    cached
)

__all__ = [
    "MultiLevelCache",
    "get_cache",
    "init_cache",
    "close_cache",
    "LRUCache",
    "CacheProtection",
    "DistributedLock",
    "cached"
]
