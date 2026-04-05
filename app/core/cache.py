import json
import hashlib
import asyncio
from functools import wraps, partial
from typing import Optional, Any, Callable, TypeVar, ParamSpec
import redis.asyncio as redis
from app.core.config import settings

# 类型变量定义
P = ParamSpec('P')
R = TypeVar('R')

# Redis连接池
redis_pool = redis.ConnectionPool.from_url(
    settings.REDIS_URL,
    max_connections=50,
    decode_responses=True
)

# Redis客户端
redis_client = redis.Redis(connection_pool=redis_pool)


class CacheError(Exception):
    """缓存相关错误"""
    pass


def _generate_cache_key(func: Callable, args: tuple, kwargs: dict, key_prefix: str) -> str:
    """生成缓存键
    
    Args:
        func: 被装饰的函数
        args: 函数参数
        kwargs: 函数关键字参数
        key_prefix: 键前缀
        
    Returns:
        str: 生成的缓存键
    """
    # 构建键的基本部分
    func_name = func.__qualname__
    
    # 序列化参数
    params = {
        'args': args,
        'kwargs': kwargs
    }
    
    # 对参数进行哈希，避免键过长
    params_hash = hashlib.md5(
        json.dumps(params, sort_keys=True, default=str).encode()
    ).hexdigest()
    
    # 构建最终的键
    return f"{key_prefix}{func_name}:{params_hash}"


def redis_cache(
    ttl: int = 300,
    key_prefix: str = "cache:",
    ignore_errors: bool = True
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """基于Redis的缓存装饰器
    
    Args:
        ttl: 缓存过期时间（秒），默认5分钟
        key_prefix: 缓存键前缀，默认"cache:"
        ignore_errors: 是否忽略缓存错误，默认True
        
    Returns:
        Callable: 装饰器函数
    """
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        if asyncio.iscoroutinefunction(func):
            # 处理异步函数
            @wraps(func)
            async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                try:
                    # 生成缓存键
                    cache_key = _generate_cache_key(func, args, kwargs, key_prefix)
                    
                    # 尝试从缓存获取
                    cached_value = await redis_client.get(cache_key)
                    if cached_value:
                        try:
                            # 反序列化缓存值
                            return json.loads(cached_value)
                        except json.JSONDecodeError:
                            # 反序列化失败，继续执行函数
                            pass
                    
                    # 缓存未命中，执行函数
                    result = await func(*args, **kwargs)
                    
                    # 将结果存入缓存
                    try:
                        await redis_client.setex(
                            cache_key,
                            ttl,
                            json.dumps(result, default=str)
                        )
                    except Exception as e:
                        if not ignore_errors:
                            raise CacheError(f"缓存设置失败: {str(e)}")
                    
                    return result
                    
                except Exception as e:
                    if not ignore_errors:
                        raise
                    # 缓存错误时，执行原函数
                    return await func(*args, **kwargs)
            
            return async_wrapper
        else:
            # 处理同步函数
            @wraps(func)
            def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                try:
                    # 生成缓存键
                    cache_key = _generate_cache_key(func, args, kwargs, key_prefix)
                    
                    # 尝试从缓存获取
                    cached_value = redis_client.get(cache_key)
                    if cached_value:
                        try:
                            # 反序列化缓存值
                            return json.loads(cached_value)
                        except json.JSONDecodeError:
                            # 反序列化失败，继续执行函数
                            pass
                    
                    # 缓存未命中，执行函数
                    result = func(*args, **kwargs)
                    
                    # 将结果存入缓存
                    try:
                        redis_client.setex(
                            cache_key,
                            ttl,
                            json.dumps(result, default=str)
                        )
                    except Exception as e:
                        if not ignore_errors:
                            raise CacheError(f"缓存设置失败: {str(e)}")
                    
                    return result
                    
                except Exception as e:
                    if not ignore_errors:
                        raise
                    # 缓存错误时，执行原函数
                    return func(*args, **kwargs)
            
            return sync_wrapper
    
    return decorator


async def acquire_lock(
    lock_name: str,
    timeout: int = 10,
    expire: int = 15
) -> bool:
    """获取Redis分布式锁
    
    Args:
        lock_name: 锁名称
        timeout: 获取锁的超时时间（秒）
        expire: 锁的过期时间（秒）
        
    Returns:
        bool: 是否成功获取锁
    """
    lock_key = f"lock:{lock_name}"
    start_time = asyncio.get_event_loop().time()
    
    while asyncio.get_event_loop().time() - start_time < timeout:
        # 尝试设置锁
        success = await redis_client.set(
            lock_key,
            "1",
            ex=expire,
            nx=True  # 只在键不存在时设置
        )
        
        if success:
            return True
        
        # 短暂睡眠后重试
        await asyncio.sleep(0.1)
    
    return False


async def release_lock(lock_name: str) -> bool:
    """释放Redis分布式锁
    
    Args:
        lock_name: 锁名称
        
    Returns:
        bool: 是否成功释放锁
    """
    lock_key = f"lock:{lock_name}"
    return await redis_client.delete(lock_key) > 0


async def clear_cache(pattern: str) -> int:
    """清除匹配模式的缓存
    
    Args:
        pattern: 键模式，如"cache:*"
        
    Returns:
        int: 清除的键数量
    """
    keys = await redis_client.keys(pattern)
    if keys:
        return await redis_client.delete(*keys)
    return 0


async def close_redis():
    """关闭Redis连接"""
    await redis_client.close()
    await redis_pool.disconnect()


# 导出
__all__ = [
    "redis_cache",
    "acquire_lock",
    "release_lock",
    "clear_cache",
    "close_redis",
    "CacheError"
]
