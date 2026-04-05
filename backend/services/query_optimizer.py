"""
数据库查询优化服务
提供查询缓存和优化功能
"""
import functools
import time
import hashlib
import json
from typing import Any, Callable, Optional, TypeVar, ParamSpec
from datetime import datetime, timedelta
import asyncio
from collections import OrderedDict

P = ParamSpec('P')
T = TypeVar('T')


class QueryCache:
    """内存查询缓存"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 60):
        self._cache: OrderedDict[str, tuple[Any, float, float]] = OrderedDict()
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._hits = 0
        self._misses = 0
    
    def _generate_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """生成缓存键"""
        key_data = {
            "func": func_name,
            "args": args,
            "kwargs": kwargs,
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if key in self._cache:
            value, expiry, _ = self._cache[key]
            if time.time() < expiry:
                self._cache.move_to_end(key)
                self._hits += 1
                return value
            else:
                del self._cache[key]
        self._misses += 1
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存值"""
        if len(self._cache) >= self._max_size:
            self._cache.popitem(last=False)
        
        expiry = time.time() + (ttl or self._default_ttl)
        self._cache[key] = (value, expiry, time.time())
    
    def invalidate(self, pattern: Optional[str] = None) -> int:
        """清除缓存"""
        if pattern is None:
            count = len(self._cache)
            self._cache.clear()
            return count
        
        keys_to_delete = [k for k in self._cache if pattern in k]
        for key in keys_to_delete:
            del self._cache[key]
        return len(keys_to_delete)
    
    def stats(self) -> dict:
        """获取缓存统计"""
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0
        
        return {
            "size": len(self._cache),
            "max_size": self._max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(hit_rate, 4),
        }


query_cache = QueryCache()


def cached_query(ttl: int = 60, key_prefix: str = ""):
    """查询缓存装饰器"""
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            cache_key = f"{key_prefix}:{query_cache._generate_key(func.__name__, args, kwargs)}"
            
            cached_result = query_cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            result = await func(*args, **kwargs)
            query_cache.set(cache_key, result, ttl)
            return result
        
        @functools.wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            cache_key = f"{key_prefix}:{query_cache._generate_key(func.__name__, args, kwargs)}"
            
            cached_result = query_cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            result = func(*args, **kwargs)
            query_cache.set(cache_key, result, ttl)
            return result
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


class QueryOptimizer:
    """查询优化器"""
    
    def __init__(self):
        self._slow_queries: list[dict] = []
        self._slow_threshold_ms = 500
    
    def log_slow_query(self, query: str, duration_ms: float, params: dict = None):
        """记录慢查询"""
        if duration_ms > self._slow_threshold_ms:
            self._slow_queries.append({
                "query": query[:500],
                "duration_ms": duration_ms,
                "params": params,
                "timestamp": datetime.now().isoformat(),
            })
            
            if len(self._slow_queries) > 100:
                self._slow_queries = self._slow_queries[-100:]
    
    def get_slow_queries(self, limit: int = 20) -> list[dict]:
        """获取慢查询列表"""
        return sorted(self._slow_queries, key=lambda x: x["duration_ms"], reverse=True)[:limit]
    
    @staticmethod
    def optimize_select(query: str) -> str:
        """优化SELECT查询"""
        if "SELECT *" in query.upper():
            pass
        
        return query
    
    @staticmethod
    def add_limit(query: str, limit: int = 1000) -> str:
        """添加LIMIT限制"""
        if "LIMIT" not in query.upper():
            return f"{query.rstrip(';')} LIMIT {limit}"
        return query


query_optimizer = QueryOptimizer()


class PaginationHelper:
    """分页助手"""
    
    @staticmethod
    def get_offset(page: int, page_size: int) -> int:
        """计算偏移量"""
        return (page - 1) * page_size
    
    @staticmethod
    def build_paginated_response(
        items: list,
        total: int,
        page: int,
        page_size: int
    ) -> dict:
        """构建分页响应"""
        total_pages = (total + page_size - 1) // page_size
        
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        }
    
    @staticmethod
    async def paginate_query(
        db,
        query: str,
        count_query: str,
        page: int = 1,
        page_size: int = 20,
        params: tuple = (),
    ) -> dict:
        """执行分页查询"""
        offset = PaginationHelper.get_offset(page, page_size)
        
        cursor = await db.execute(count_query, params)
        total = (await cursor.fetchone())[0]
        
        paginated_query = f"{query} LIMIT {page_size} OFFSET {offset}"
        cursor = await db.execute(paginated_query, params)
        items = await cursor.fetchall()
        
        return PaginationHelper.build_paginated_response(items, total, page, page_size)


def measure_query_time(func: Callable[P, T]) -> Callable[P, T]:
    """测量查询时间装饰器"""
    @functools.wraps(func)
    async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            duration_ms = (time.time() - start_time) * 1000
            if duration_ms > query_optimizer._slow_threshold_ms:
                query_optimizer.log_slow_query(
                    func.__name__,
                    duration_ms,
                    {"args": str(args)[:200], "kwargs": str(kwargs)[:200]}
                )
    
    @functools.wraps(func)
    def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            duration_ms = (time.time() - start_time) * 1000
            if duration_ms > query_optimizer._slow_threshold_ms:
                query_optimizer.log_slow_query(
                    func.__name__,
                    duration_ms,
                    {"args": str(args)[:200], "kwargs": str(kwargs)[:200]}
                )
    
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper
