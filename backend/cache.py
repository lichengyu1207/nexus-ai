"""
Redis缓存模块
实现高并发场景下的缓存支持
"""
import json
import asyncio
import logging
from typing import Optional, Any, Dict, List
from datetime import timedelta
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_ENABLED = os.getenv("REDIS_ENABLED", "false").lower() == "true"

class RedisCache:
    """
    Redis缓存管理器
    支持高并发场景下的缓存操作
    """
    
    _instance: Optional['RedisCache'] = None
    _lock = asyncio.Lock()
    
    def __init__(self, url: str = REDIS_URL):
        self.url = url
        self._client = None
        self._connected = False
        self._local_cache: Dict[str, Any] = {}
        self._cache_ttl: Dict[str, float] = {}
    
    @classmethod
    async def get_instance(cls) -> 'RedisCache':
        if cls._instance is None:
            async with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
                    await cls._instance._connect()
        return cls._instance
    
    async def _connect(self):
        if not REDIS_ENABLED:
            logger.info("Redis is disabled, using local cache")
            self._connected = False
            return
            
        try:
            import redis.asyncio as redis
            self._client = redis.from_url(self.url, encoding="utf-8", decode_responses=True)
            await self._client.ping()
            self._connected = True
            logger.info(f"Redis connected: {self.url}")
        except ImportError:
            logger.warning("redis package not installed, using local cache")
            self._connected = False
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}, using local cache")
            self._connected = False
    
    async def get(self, key: str) -> Optional[Any]:
        if self._connected and self._client:
            try:
                value = await self._client.get(key)
                if value:
                    return json.loads(value)
            except Exception as e:
                logger.debug(f"Redis get error: {e}")
        
        if key in self._local_cache:
            import time
            if key in self._cache_ttl and self._cache_ttl[key] < time.time():
                del self._local_cache[key]
                del self._cache_ttl[key]
                return None
            return self._local_cache[key]
        
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600):
        if self._connected and self._client:
            try:
                await self._client.setex(key, ttl, json.dumps(value, ensure_ascii=False))
                return
            except Exception as e:
                logger.debug(f"Redis set error: {e}")
        
        self._local_cache[key] = value
        import time
        self._cache_ttl[key] = time.time() + ttl
    
    async def delete(self, key: str):
        if self._connected and self._client:
            try:
                await self._client.delete(key)
            except Exception as e:
                logger.debug(f"Redis delete error: {e}")
        
        if key in self._local_cache:
            del self._local_cache[key]
        if key in self._cache_ttl:
            del self._cache_ttl[key]
    
    async def delete_pattern(self, pattern: str):
        if self._connected and self._client:
            try:
                keys = await self._client.keys(pattern)
                if keys:
                    await self._client.delete(*keys)
            except Exception as e:
                logger.debug(f"Redis delete_pattern error: {e}")
        
        import fnmatch
        keys_to_delete = [k for k in self._local_cache.keys() if fnmatch.fnmatch(k, pattern)]
        for key in keys_to_delete:
            del self._local_cache[key]
            if key in self._cache_ttl:
                del self._cache_ttl[key]
    
    async def incr(self, key: str) -> int:
        if self._connected and self._client:
            try:
                return await self._client.incr(key)
            except Exception as e:
                logger.debug(f"Redis incr error: {e}")
        
        current = self._local_cache.get(key, 0)
        if isinstance(current, int):
            self._local_cache[key] = current + 1
            return self._local_cache[key]
        return 1
    
    async def expire(self, key: str, ttl: int):
        if self._connected and self._client:
            try:
                await self._client.expire(key, ttl)
            except Exception as e:
                logger.debug(f"Redis expire error: {e}")
        
        if key in self._local_cache:
            import time
            self._cache_ttl[key] = time.time() + ttl
    
    async def close(self):
        if self._client:
            await self._client.close()
        self._local_cache.clear()
        self._cache_ttl.clear()
        logger.info("Redis cache closed")

cache: Optional[RedisCache] = None

async def get_cache() -> RedisCache:
    global cache
    if cache is None:
        cache = await RedisCache.get_instance()
    return cache

async def cache_get(key: str) -> Optional[Any]:
    c = await get_cache()
    return await c.get(key)

async def cache_set(key: str, value: Any, ttl: int = 3600):
    c = await get_cache()
    await c.set(key, value, ttl)

async def cache_delete(key: str):
    c = await get_cache()
    await c.delete(key)

async def cache_delete_pattern(pattern: str):
    c = await get_cache()
    await c.delete_pattern(pattern)

def cache_key(prefix: str, *args, **kwargs) -> str:
    parts = [prefix]
    for arg in args:
        parts.append(str(arg))
    for k, v in sorted(kwargs.items()):
        parts.append(f"{k}:{v}")
    return ":".join(parts)
