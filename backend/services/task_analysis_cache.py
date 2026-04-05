"""
任务分析缓存服务
为任务分析提供智能缓存，降低P95响应时间
"""
import hashlib
import json
import logging
import time
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

from .cache import get_cache, MultiLevelCache

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """缓存条目"""
    result: Dict[str, Any]
    query_hash: str
    city: Optional[str] = None
    district: Optional[str] = None
    created_at: float = 0.0
    hit_count: int = 0
    ttl: int = 3600


class TaskAnalysisCache:
    """任务分析缓存服务"""
    
    _instance: Optional['TaskAnalysisCache'] = None
    
    CACHE_PREFIX = "task_analysis:"
    RESULT_CACHE_PREFIX = "result:"
    DATA_CACHE_PREFIX = "data:"
    MARKET_CACHE_PREFIX = "market:"
    
    DEFAULT_TTL = 3600
    MARKET_DATA_TTL = 1800
    QUERY_RESULT_TTL = 7200
    
    def __init__(self):
        self._cache: Optional[MultiLevelCache] = None
        self._local_cache: Dict[str, CacheEntry] = {}
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "total_queries": 0
        }
        self._initialized = False
    
    @classmethod
    async def get_instance(cls) -> 'TaskAnalysisCache':
        if cls._instance is None:
            cls._instance = cls()
            await cls._instance.initialize()
        return cls._instance
    
    async def initialize(self) -> bool:
        if self._initialized:
            return True
        
        self._cache = await get_cache()
        self._initialized = True
        logger.info("TaskAnalysisCache initialized")
        return True
    
    def _hash_query(self, query: str, style: str = "balanced") -> str:
        """生成查询哈希"""
        normalized = query.lower().strip()
        content = f"{normalized}:{style}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _extract_location(self, query: str) -> Tuple[Optional[str], Optional[str]]:
        """从查询中提取城市和区域"""
        cities = [
            "北京", "上海", "深圳", "广州", "杭州", "苏州", "成都", "武汉",
            "南京", "西安", "重庆", "天津", "长沙", "郑州"
        ]
        
        city = None
        district = None
        
        for c in cities:
            if c in query:
                city = c
                break
        
        if city:
            district_patterns = [
                f"{city}([^市区县]{2,3}[市区县])",
                f"([^市]{2,3}[区县]).*{city}"
            ]
            import re
            for pattern in district_patterns:
                match = re.search(pattern, query)
                if match:
                    district = match.group(1) if match.lastindex else match.group(0)
                    break
        
        return city, district
    
    async def get_cached_result(
        self, 
        query: str, 
        style: str = "balanced"
    ) -> Optional[Dict[str, Any]]:
        """获取缓存的分析结果"""
        self._stats["total_queries"] += 1
        
        query_hash = self._hash_query(query, style)
        cache_key = f"{self.CACHE_PREFIX}{self.RESULT_CACHE_PREFIX}{query_hash}"
        
        if query_hash in self._local_cache:
            entry = self._local_cache[query_hash]
            if time.time() < entry.created_at + entry.ttl:
                entry.hit_count += 1
                self._stats["hits"] += 1
                logger.debug(f"Cache hit (local): {query[:50]}...")
                return entry.result
        
        if self._cache:
            cached = await self._cache.get(cache_key)
            if cached:
                self._stats["hits"] += 1
                logger.debug(f"Cache hit (redis): {query[:50]}...")
                return cached
        
        self._stats["misses"] += 1
        logger.debug(f"Cache miss: {query[:50]}...")
        return None
    
    async def set_cached_result(
        self,
        query: str,
        result: Dict[str, Any],
        style: str = "balanced",
        ttl: int = None
    ) -> bool:
        """缓存分析结果"""
        query_hash = self._hash_query(query, style)
        cache_key = f"{self.CACHE_PREFIX}{self.RESULT_CACHE_PREFIX}{query_hash}"
        city, district = self._extract_location(query)
        
        entry = CacheEntry(
            result=result,
            query_hash=query_hash,
            city=city,
            district=district,
            created_at=time.time(),
            ttl=ttl or self.QUERY_RESULT_TTL
        )
        
        if len(self._local_cache) < 1000:
            self._local_cache[query_hash] = entry
        
        if self._cache:
            await self._cache.set(cache_key, result, ttl or self.QUERY_RESULT_TTL)
        
        logger.debug(f"Cached result for: {query[:50]}...")
        return True
    
    async def get_market_data(
        self,
        city: str,
        district: str = None
    ) -> Optional[Dict[str, Any]]:
        """获取市场数据缓存"""
        cache_key = f"{self.CACHE_PREFIX}{self.MARKET_CACHE_PREFIX}{city}:{district or 'all'}"
        
        if self._cache:
            return await self._cache.get(cache_key)
        return None
    
    async def set_market_data(
        self,
        city: str,
        district: str,
        data: Dict[str, Any],
        ttl: int = None
    ) -> bool:
        """缓存市场数据"""
        cache_key = f"{self.CACHE_PREFIX}{self.MARKET_CACHE_PREFIX}{city}:{district or 'all'}"
        
        if self._cache:
            await self._cache.set(cache_key, data, ttl or self.MARKET_DATA_TTL)
        return True
    
    async def invalidate_query(self, query: str, style: str = "balanced") -> bool:
        """使查询缓存失效"""
        query_hash = self._hash_query(query, style)
        cache_key = f"{self.CACHE_PREFIX}{self.RESULT_CACHE_PREFIX}{query_hash}"
        
        if query_hash in self._local_cache:
            del self._local_cache[query_hash]
        
        if self._cache:
            await self._cache.delete(cache_key)
        
        return True
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        total = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / total if total > 0 else 0.0
        
        return {
            **self._stats,
            "hit_rate": hit_rate,
            "local_cache_size": len(self._local_cache)
        }
    
    async def clear_all(self) -> bool:
        """清除所有缓存"""
        self._local_cache.clear()
        
        if self._cache:
            keys = await self._cache.keys(f"{self.CACHE_PREFIX}*")
            for key in keys:
                await self._cache.delete(key)
        
        logger.info("All task analysis cache cleared")
        return True


task_analysis_cache: Optional[TaskAnalysisCache] = None


async def get_task_analysis_cache() -> TaskAnalysisCache:
    global task_analysis_cache
    
    if task_analysis_cache is None:
        task_analysis_cache = await TaskAnalysisCache.get_instance()
    
    return task_analysis_cache
