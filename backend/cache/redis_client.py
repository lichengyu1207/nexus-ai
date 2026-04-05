"""
Redis缓存客户端
提供异步Redis操作和缓存装饰器
"""
import os
import json
import functools
import hashlib
import time
from typing import Any, Optional, Callable, TypeVar, ParamSpec
from datetime import timedelta
import asyncio

try:
    import redis.asyncio as aioredis
    from redis.asyncio import Redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    Redis = None

from ..logger import get_logger

logger = get_logger("redis_client")

P = ParamSpec('P')
T = TypeVar('T')


class RedisConfig:
    """Redis配置"""
    
    URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    PASSWORD = os.getenv("REDIS_PASSWORD")
    MAX_CONNECTIONS = int(os.getenv("REDIS_MAX_CONNECTIONS", "50"))
    SOCKET_TIMEOUT = int(os.getenv("REDIS_SOCKET_TIMEOUT", "5"))
    SOCKET_CONNECT_TIMEOUT = int(os.getenv("REDIS_CONNECT_TIMEOUT", "5"))
    RETRY_ON_TIMEOUT = True
    HEALTH_CHECK_INTERVAL = int(os.getenv("REDIS_HEALTH_CHECK_INTERVAL", "30"))


class RedisClient:
    """Redis客户端封装"""
    
    _instance: Optional['RedisClient'] = None
    _client: Optional[Redis] = None
    _enabled: bool = False
    _fallback_cache: dict = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def connect(self) -> bool:
        """连接Redis"""
        if not REDIS_AVAILABLE:
            logger.warning("Redis library not installed, using in-memory fallback cache")
            self._enabled = False
            return False
        
        try:
            self._client = await aioredis.from_url(
                RedisConfig.URL,
                password=RedisConfig.PASSWORD,
                max_connections=RedisConfig.MAX_CONNECTIONS,
                socket_timeout=RedisConfig.SOCKET_TIMEOUT,
                socket_connect_timeout=RedisConfig.SOCKET_CONNECT_TIMEOUT,
                retry_on_timeout=RedisConfig.RETRY_ON_TIMEOUT,
                encoding="utf-8",
                decode_responses=True,
            )
            
            await self._client.ping()
            self._enabled = True
            logger.info(f"Redis connected successfully: {RedisConfig.URL}")
            return True
            
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}, using in-memory fallback")
            self._enabled = False
            self._client = None
            return False
    
    async def disconnect(self):
        """断开连接"""
        if self._client:
            await self._client.close()
            self._client = None
            self._enabled = False
            logger.info("Redis disconnected")
    
    @property
    def is_enabled(self) -> bool:
        return self._enabled
    
    @property
    def client(self) -> Optional[Redis]:
        return self._client
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if self._enabled and self._client:
            try:
                value = await self._client.get(key)
                if value:
                    return json.loads(value)
            except Exception as e:
                logger.warning(f"Redis get error: {e}")
        else:
            if key in self._fallback_cache:
                entry = self._fallback_cache[key]
                if entry["expires_at"] > time.time():
                    return entry["value"]
                del self._fallback_cache[key]
        return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = 60,
        nx: bool = False,
    ) -> bool:
        """设置缓存值"""
        if self._enabled and self._client:
            try:
                serialized = json.dumps(value, default=str)
                if nx:
                    result = await self._client.set(key, serialized, ex=ttl, nx=True)
                    return result is not None
                else:
                    await self._client.set(key, serialized, ex=ttl)
                return True
            except Exception as e:
                logger.warning(f"Redis set error: {e}")
                return False
        else:
            if len(self._fallback_cache) < 10000:
                self._fallback_cache[key] = {
                    "value": value,
                    "expires_at": time.time() + ttl,
                }
            return True
    
    async def delete(self, key: str) -> bool:
        """删除缓存"""
        if self._enabled and self._client:
            try:
                await self._client.delete(key)
                return True
            except Exception as e:
                logger.warning(f"Redis delete error: {e}")
                return False
        else:
            self._fallback_cache.pop(key, None)
            return True
    
    async def delete_pattern(self, pattern: str) -> int:
        """删除匹配模式的所有键"""
        if self._enabled and self._client:
            try:
                keys = []
                async for key in self._client.scan_iter(match=pattern):
                    keys.append(key)
                
                if keys:
                    await self._client.delete(*keys)
                return len(keys)
            except Exception as e:
                logger.warning(f"Redis delete_pattern error: {e}")
                return 0
        else:
            keys_to_delete = [k for k in self._fallback_cache if pattern.replace("*", "") in k]
            for key in keys_to_delete:
                del self._fallback_cache[key]
            return len(keys_to_delete)
    
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        if self._enabled and self._client:
            try:
                return await self._client.exists(key) > 0
            except Exception as e:
                logger.warning(f"Redis exists error: {e}")
                return False
        else:
            if key in self._fallback_cache:
                entry = self._fallback_cache[key]
                if entry["expires_at"] > time.time():
                    return True
                del self._fallback_cache[key]
            return False
    
    async def incr(self, key: str, amount: int = 1) -> int:
        """增加计数"""
        if self._enabled and self._client:
            try:
                return await self._client.incrby(key, amount)
            except Exception as e:
                logger.warning(f"Redis incr error: {e}")
                return 0
        else:
            current = self._fallback_cache.get(key, {"value": 0})["value"]
            new_value = current + amount
            self._fallback_cache[key] = {"value": new_value, "expires_at": time.time() + 86400}
            return new_value
    
    async def expire(self, key: str, ttl: int) -> bool:
        """设置过期时间"""
        if self._enabled and self._client:
            try:
                return await self._client.expire(key, ttl)
            except Exception as e:
                logger.warning(f"Redis expire error: {e}")
                return False
        return True
    
    async def ttl(self, key: str) -> int:
        """获取剩余过期时间"""
        if self._enabled and self._client:
            try:
                return await self._client.ttl(key)
            except Exception as e:
                logger.warning(f"Redis ttl error: {e}")
                return -1
        else:
            if key in self._fallback_cache:
                entry = self._fallback_cache[key]
                return max(0, int(entry["expires_at"] - time.time()))
            return -1
    
    async def info(self) -> dict:
        """获取Redis信息"""
        if self._enabled and self._client:
            try:
                info = await self._client.info()
                return {
                    "connected": True,
                    "used_memory_human": info.get("used_memory_human"),
                    "connected_clients": info.get("connected_clients"),
                    "total_commands_processed": info.get("total_commands_processed"),
                    "keyspace_hits": info.get("keyspace_hits"),
                    "keyspace_misses": info.get("keyspace_misses"),
                }
            except Exception as e:
                return {"connected": False, "error": str(e)}
        else:
            return {
                "connected": False,
                "fallback_cache_size": len(self._fallback_cache),
                "mode": "in-memory",
            }
    
    async def health_check(self) -> dict:
        """健康检查"""
        result = {
            "status": "healthy" if self._enabled else "degraded",
            "redis_available": REDIS_AVAILABLE,
            "connected": self._enabled,
        }
        
        if self._enabled and self._client:
            try:
                start = time.time()
                await self._client.ping()
                result["latency_ms"] = round((time.time() - start) * 1000, 2)
            except Exception as e:
                result["status"] = "unhealthy"
                result["error"] = str(e)
        
        return result


redis_client = RedisClient()


def get_cache_key(prefix: str, *args, **kwargs) -> str:
    """生成缓存键"""
    key_data = {
        "args": args,
        "kwargs": kwargs,
    }
    key_str = json.dumps(key_data, sort_keys=True, default=str)
    key_hash = hashlib.md5(key_str.encode()).hexdigest()[:16]
    return f"{prefix}:{key_hash}"


def cached(
    key_prefix: str,
    ttl: int = 60,
    skip_cache_func: Optional[Callable] = None,
):
    """缓存装饰器"""
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            if skip_cache_func and skip_cache_func(*args, **kwargs):
                return await func(*args, **kwargs)
            
            cache_key = get_cache_key(key_prefix, *args, **kwargs)
            
            cached_value = await redis_client.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            result = await func(*args, **kwargs)
            
            await redis_client.set(cache_key, result, ttl)
            
            return result
        
        @functools.wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            if skip_cache_func and skip_cache_func(*args, **kwargs):
                return func(*args, **kwargs)
            
            cache_key = get_cache_key(key_prefix, *args, **kwargs)
            
            loop = asyncio.get_event_loop()
            cached_value = loop.run_until_complete(redis_client.get(cache_key))
            if cached_value is not None:
                return cached_value
            
            result = func(*args, **kwargs)
            
            loop.run_until_complete(redis_client.set(cache_key, result, ttl))
            
            return result
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


async def invalidate_cache(pattern: str) -> int:
    """使缓存失效"""
    return await redis_client.delete_pattern(pattern)


async def init_redis() -> bool:
    """初始化Redis连接"""
    return await redis_client.connect()


async def close_redis():
    """关闭Redis连接"""
    await redis_client.disconnect()
