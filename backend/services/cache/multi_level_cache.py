"""
多级缓存系统
实现本地缓存 + Redis分布式缓存 + 缓存防护机制
"""
import asyncio
import time
import hashlib
import json
import random
import logging
from typing import Any, Optional, Callable, Dict, List, TypeVar, ParamSpec
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import wraps
from contextlib import asynccontextmanager
import os

try:
    import redis.asyncio as aioredis
    from redis.asyncio import Redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    Redis = None

P = ParamSpec('P')
T = TypeVar('T')

logger = logging.getLogger(__name__)


@dataclass
class CacheConfig:
    max_size: int = 10000
    default_ttl: int = 60
    cleanup_interval: int = 60
    enable_metrics: bool = True


@dataclass
class CacheEntry:
    value: Any
    expires_at: float
    created_at: float
    access_count: int = 0
    last_access: float = 0.0
    size_bytes: int = 0


@dataclass
class CacheStats:
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_size: int = 0
    entry_count: int = 0
    
    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


class LRUCache:
    """本地LRU缓存"""
    
    def __init__(self, max_size: int = 10000, default_ttl: int = 60):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, CacheEntry] = {}
        self._access_order: List[str] = []
        self._stats = CacheStats()
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None
    
    async def start_cleanup(self):
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def stop_cleanup(self):
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
    
    async def _cleanup_loop(self):
        while True:
            try:
                await asyncio.sleep(60)
                await self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cache cleanup error: {e}")
    
    async def _cleanup_expired(self):
        now = time.time()
        expired_keys = [
            k for k, v in self._cache.items()
            if v.expires_at < now
        ]
        
        for key in expired_keys:
            await self._delete(key)
        
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    def _evict_lru(self):
        while len(self._cache) >= self.max_size and self._access_order:
            oldest_key = self._access_order.pop(0)
            if oldest_key in self._cache:
                del self._cache[oldest_key]
                self._stats.evictions += 1
    
    async def get(self, key: str) -> Optional[Any]:
        async with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                self._stats.misses += 1
                return None
            
            if entry.expires_at < time.time():
                await self._delete_unlocked(key)
                self._stats.misses += 1
                return None
            
            entry.access_count += 1
            entry.last_access = time.time()
            
            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)
            
            self._stats.hits += 1
            return entry.value
    
    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        if ttl is None:
            ttl = self.default_ttl
        
        async with self._lock:
            if len(self._cache) >= self.max_size:
                self._evict_lru()
            
            now = time.time()
            entry = CacheEntry(
                value=value,
                expires_at=now + ttl,
                created_at=now,
                access_count=0,
                last_access=now,
                size_bytes=self._estimate_size(value)
            )
            
            self._cache[key] = entry
            
            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)
            
            self._stats.entry_count = len(self._cache)
            self._stats.total_size = sum(e.size_bytes for e in self._cache.values())
            
            return True
    
    async def delete(self, key: str) -> bool:
        async with self._lock:
            return await self._delete_unlocked(key)
    
    async def _delete(self, key: str) -> bool:
        async with self._lock:
            return await self._delete_unlocked(key)
    
    async def _delete_unlocked(self, key: str) -> bool:
        if key in self._cache:
            del self._cache[key]
            if key in self._access_order:
                self._access_order.remove(key)
            self._stats.entry_count = len(self._cache)
            return True
        return False
    
    async def clear(self):
        async with self._lock:
            self._cache.clear()
            self._access_order.clear()
            self._stats = CacheStats()
    
    def _estimate_size(self, value: Any) -> int:
        try:
            return len(json.dumps(value, default=str))
        except:
            return 100
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "hits": self._stats.hits,
            "misses": self._stats.misses,
            "hit_rate": round(self._stats.hit_rate * 100, 2),
            "evictions": self._stats.evictions,
            "entry_count": self._stats.entry_count,
            "total_size_bytes": self._stats.total_size,
            "max_size": self.max_size
        }


class DistributedLock:
    """分布式锁"""
    
    def __init__(self, redis_client: Redis, key: str, ttl: int = 10):
        self.redis = redis_client
        self.key = key
        self.ttl = ttl
        self._token: Optional[str] = None
    
    async def acquire(self, timeout: float = 5.0) -> bool:
        start_time = time.time()
        self._token = hashlib.md5(f"{self.key}:{time.time()}".encode()).hexdigest()
        
        while time.time() - start_time < timeout:
            try:
                acquired = await self.redis.set(
                    self.key, self._token, ex=self.ttl, nx=True
                )
                if acquired:
                    return True
            except Exception as e:
                logger.warning(f"Lock acquire error: {e}")
            
            await asyncio.sleep(0.05)
        
        return False
    
    async def release(self) -> bool:
        if not self._token:
            return False
        
        try:
            script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("del", KEYS[1])
            else
                return 0
            end
            """
            result = await self.redis.eval(script, [self.key], [self._token])
            return bool(result)
        except Exception as e:
            logger.warning(f"Lock release error: {e}")
            return False
    
    async def extend(self, ttl: int = None) -> bool:
        if not self._token:
            return False
        
        try:
            script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("expire", KEYS[1], ARGV[2])
            else
                return 0
            end
            """
            result = await self.redis.eval(
                script, [self.key], [self._token, ttl or self.ttl]
            )
            return bool(result)
        except Exception as e:
            logger.warning(f"Lock extend error: {e}")
            return False
    
    @asynccontextmanager
    async def __call__(self, timeout: float = 5.0):
        acquired = await self.acquire(timeout)
        if not acquired:
            raise TimeoutError(f"Failed to acquire lock: {self.key}")
        try:
            yield self
        finally:
            await self.release()


class CacheProtection:
    """缓存防护机制"""
    
    def __init__(self, redis_client: Redis = None):
        self.redis = redis_client
        self._null_cache_ttl = 60
        self._lock_prefix = "cache_lock:"
        self._null_marker = "__NULL__"
    
    def _get_random_ttl(self, base_ttl: int, variance: float = 0.2) -> int:
        variance_seconds = int(base_ttl * variance)
        random_offset = random.randint(-variance_seconds, variance_seconds)
        return max(1, base_ttl + random_offset)
    
    async def prevent_penetration(
        self,
        key: str,
        fetch_func: Callable,
        ttl: int = 60
    ) -> Optional[Any]:
        if self.redis:
            cached = await self.redis.get(key)
            if cached is not None:
                if cached == self._null_marker:
                    return None
                try:
                    return json.loads(cached)
                except:
                    return cached
        
        result = await fetch_func()
        
        if self.redis:
            if result is None:
                await self.redis.set(
                    key, self._null_marker, ex=self._null_cache_ttl
                )
            else:
                serialized = json.dumps(result, default=str)
                await self.redis.set(key, serialized, ex=ttl)
        
        return result
    
    async def prevent_breakdown(
        self,
        key: str,
        fetch_func: Callable,
        ttl: int = 60,
        lock_timeout: float = 5.0
    ) -> Optional[Any]:
        if self.redis:
            cached = await self.redis.get(key)
            if cached is not None:
                try:
                    return json.loads(cached)
                except:
                    return cached
        
        if self.redis:
            lock = DistributedLock(self.redis, f"{self._lock_prefix}{key}")
            
            async with lock(lock_timeout):
                cached = await self.redis.get(key)
                if cached is not None:
                    try:
                        return json.loads(cached)
                    except:
                        return cached
                
                result = await fetch_func()
                
                if result is not None:
                    serialized = json.dumps(result, default=str)
                    random_ttl = self._get_random_ttl(ttl)
                    await self.redis.set(key, serialized, ex=random_ttl)
                
                return result
        else:
            result = await fetch_func()
            return result
    
    async def prevent_avalanche(
        self,
        keys: List[str],
        fetch_func: Callable[[str], Any],
        base_ttl: int = 60
    ) -> Dict[str, Any]:
        results = {}
        
        for key in keys:
            random_ttl = self._get_random_ttl(base_ttl)
            
            if self.redis:
                cached = await self.redis.get(key)
                if cached is not None:
                    try:
                        results[key] = json.loads(cached)
                        continue
                    except:
                        pass
            
            result = await fetch_func(key)
            results[key] = result
            
            if self.redis and result is not None:
                serialized = json.dumps(result, default=str)
                await self.redis.set(key, serialized, ex=random_ttl)
        
        return results


class MultiLevelCache:
    """多级缓存系统"""
    
    _instance: Optional['MultiLevelCache'] = None
    
    def __init__(
        self,
        local_max_size: int = 10000,
        local_default_ttl: int = 60,
        redis_url: str = None
    ):
        self.l1_cache = LRUCache(
            max_size=local_max_size,
            default_ttl=local_default_ttl
        )
        
        self._redis: Optional[Redis] = None
        self._redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._redis_enabled = False
        
        self._protection: Optional[CacheProtection] = None
        self._stats = CacheStats()
        self._initialized = False
    
    @classmethod
    async def get_instance(cls) -> 'MultiLevelCache':
        if cls._instance is None:
            cls._instance = cls()
            await cls._instance.initialize()
        return cls._instance
    
    async def initialize(self) -> bool:
        if self._initialized:
            return True
        
        await self.l1_cache.start_cleanup()
        
        if REDIS_AVAILABLE:
            try:
                self._redis = await aioredis.from_url(
                    self._redis_url,
                    encoding="utf-8",
                    decode_responses=True
                )
                await self._redis.ping()
                self._redis_enabled = True
                self._protection = CacheProtection(self._redis)
                logger.info(f"Redis connected: {self._redis_url}")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}, using local cache only")
                self._redis_enabled = False
        
        self._initialized = True
        return True
    
    async def close(self):
        await self.l1_cache.stop_cleanup()
        
        if self._redis:
            await self._redis.close()
            self._redis = None
        
        self._initialized = False
        logger.info("Multi-level cache closed")
    
    async def get(self, key: str) -> Optional[Any]:
        value = await self.l1_cache.get(key)
        if value is not None:
            self._stats.hits += 1
            return value
        
        if self._redis_enabled and self._redis:
            try:
                cached = await self._redis.get(key)
                if cached is not None:
                    value = json.loads(cached)
                    await self.l1_cache.set(key, value)
                    self._stats.hits += 1
                    return value
            except Exception as e:
                logger.warning(f"Redis get error: {e}")
        
        self._stats.misses += 1
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 60) -> bool:
        await self.l1_cache.set(key, value, ttl)
        
        if self._redis_enabled and self._redis:
            try:
                serialized = json.dumps(value, default=str)
                await self._redis.set(key, serialized, ex=ttl)
            except Exception as e:
                logger.warning(f"Redis set error: {e}")
        
        return True
    
    async def delete(self, key: str) -> bool:
        await self.l1_cache.delete(key)
        
        if self._redis_enabled and self._redis:
            try:
                await self._redis.delete(key)
            except Exception as e:
                logger.warning(f"Redis delete error: {e}")
        
        return True
    
    async def delete_pattern(self, pattern: str) -> int:
        count = 0
        
        if self._redis_enabled and self._redis:
            try:
                keys = []
                async for key in self._redis.scan_iter(match=pattern):
                    keys.append(key)
                
                if keys:
                    await self._redis.delete(*keys)
                    count = len(keys)
            except Exception as e:
                logger.warning(f"Redis delete_pattern error: {e}")
        
        return count
    
    async def get_or_fetch(
        self,
        key: str,
        fetch_func: Callable,
        ttl: int = 60,
        use_protection: str = "breakdown"
    ) -> Optional[Any]:
        value = await self.get(key)
        if value is not None:
            return value
        
        if use_protection == "penetration" and self._protection:
            return await self._protection.prevent_penetration(
                key, fetch_func, ttl
            )
        elif use_protection == "breakdown" and self._protection:
            return await self._protection.prevent_breakdown(
                key, fetch_func, ttl
            )
        else:
            result = await fetch_func()
            if result is not None:
                await self.set(key, result, ttl)
            return result
    
    async def warmup(self, warmup_data: Dict[str, Any], ttl: int = 300):
        for key, value in warmup_data.items():
            await self.set(key, value, ttl)
        
        logger.info(f"Cache warmed up with {len(warmup_data)} entries")
    
    async def get_stats(self) -> Dict[str, Any]:
        l1_stats = self.l1_cache.get_stats()
        
        redis_stats = {}
        if self._redis_enabled and self._redis:
            try:
                info = await self._redis.info()
                redis_stats = {
                    "connected": True,
                    "used_memory": info.get("used_memory_human"),
                    "connected_clients": info.get("connected_clients"),
                    "keyspace_hits": info.get("keyspace_hits"),
                    "keyspace_misses": info.get("keyspace_misses"),
                }
            except Exception as e:
                redis_stats = {"connected": False, "error": str(e)}
        else:
            redis_stats = {"connected": False}
        
        return {
            "l1_cache": l1_stats,
            "l2_cache": redis_stats,
            "overall": {
                "hits": self._stats.hits,
                "misses": self._stats.misses,
                "hit_rate": round(
                    self._stats.hit_rate * 100, 2
                )
            }
        }


def cached(
    key_prefix: str,
    ttl: int = 60,
    protection: str = None
):
    """缓存装饰器"""
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            cache = await MultiLevelCache.get_instance()
            
            key_data = {
                "prefix": key_prefix,
                "args": str(args)[:100],
                "kwargs": str(sorted(kwargs.items()))[:100]
            }
            key = hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()
            cache_key = f"{key_prefix}:{key}"
            
            async def fetch():
                return await func(*args, **kwargs)
            
            if protection:
                result = await cache.get_or_fetch(
                    cache_key, fetch, ttl, protection
                )
            else:
                result = await cache.get(cache_key)
                if result is None:
                    result = await fetch()
                    if result is not None:
                        await cache.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


multi_level_cache: Optional[MultiLevelCache] = None


async def get_cache() -> MultiLevelCache:
    global multi_level_cache
    if multi_level_cache is None:
        multi_level_cache = await MultiLevelCache.get_instance()
    return multi_level_cache


async def init_cache() -> bool:
    global multi_level_cache
    multi_level_cache = await MultiLevelCache.get_instance()
    return multi_level_cache._initialized


async def close_cache():
    global multi_level_cache
    if multi_level_cache:
        await multi_level_cache.close()
        multi_level_cache = None
