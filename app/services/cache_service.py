"""
Redis缓存服务
用于缓存常用数据和报告
"""
import redis
import json
import os
from typing import Any, Optional
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class CacheService:
    """
    Redis缓存服务
    提供数据缓存和检索功能
    """
    
    def __init__(self):
        """初始化Redis连接"""
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/1")
        self.redis_client = redis.from_url(
            self.redis_url,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )
        
        # 测试连接
        try:
            self.redis_client.ping()
            logger.info("Redis connection established successfully")
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            self.redis_client = None
    
    def is_available(self) -> bool:
        """检查Redis是否可用"""
        if not self.redis_client:
            return False
        
        try:
            self.redis_client.ping()
            return True
        except:
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            Optional[Any]: 缓存值，不存在返回None
        """
        if not self.is_available():
            return None
        
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Error getting cache for key {key}: {str(e)}")
            return None
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），None表示永不过期
            
        Returns:
            bool: 是否成功
        """
        if not self.is_available():
            return False
        
        try:
            serialized = json.dumps(value)
            
            if ttl:
                self.redis_client.setex(key, ttl, serialized)
            else:
                self.redis_client.set(key, serialized)
            
            return True
        except Exception as e:
            logger.error(f"Error setting cache for key {key}: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        删除缓存
        
        Args:
            key: 缓存键
            
        Returns:
            bool: 是否成功
        """
        if not self.is_available():
            return False
        
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error deleting cache for key {key}: {str(e)}")
            return False
    
    def exists(self, key: str) -> bool:
        """
        检查缓存是否存在
        
        Args:
            key: 缓存键
            
        Returns:
            bool: 是否存在
        """
        if not self.is_available():
            return False
        
        try:
            return self.redis_client.exists(key) > 0
        except Exception as e:
            logger.error(f"Error checking cache existence for key {key}: {str(e)}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """
        清除匹配模式的所有缓存
        
        Args:
            pattern: 匹配模式（如 "task:*"）
            
        Returns:
            int: 删除的缓存数量
        """
        if not self.is_available():
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Error clearing cache for pattern {pattern}: {str(e)}")
            return 0
    
    def get_task_cache(self, task_id: str) -> Optional[dict]:
        """
        获取任务缓存
        
        Args:
            task_id: 任务ID
            
        Returns:
            Optional[dict]: 任务数据
        """
        key = f"task:{task_id}"
        return self.get(key)
    
    def set_task_cache(
        self,
        task_id: str,
        task_data: dict,
        ttl: int = 3600
    ) -> bool:
        """
        设置任务缓存
        
        Args:
            task_id: 任务ID
            task_data: 任务数据
            ttl: 过期时间（秒），默认1小时
            
        Returns:
            bool: 是否成功
        """
        key = f"task:{task_id}"
        return self.set(key, task_data, ttl)
    
    def get_report_cache(self, task_id: str) -> Optional[dict]:
        """
        获取报告缓存
        
        Args:
            task_id: 任务ID
            
        Returns:
            Optional[dict]: 报告数据
        """
        key = f"report:{task_id}"
        return self.get(key)
    
    def set_report_cache(
        self,
        task_id: str,
        report_data: dict,
        ttl: int = 7200
    ) -> bool:
        """
        设置报告缓存
        
        Args:
            task_id: 任务ID
            report_data: 报告数据
            ttl: 过期时间（秒），默认2小时
            
        Returns:
            bool: 是否成功
        """
        key = f"report:{task_id}"
        return self.set(key, report_data, ttl)


# 全局缓存服务实例
cache_service = CacheService()


def cache_result(ttl: int = 3600, key_prefix: str = ""):
    """
    缓存装饰器
    
    Args:
        ttl: 过期时间（秒）
        key_prefix: 键前缀
        
    Returns:
        装饰器函数
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # 尝试从缓存获取
            cached_result = cache_service.get(cache_key)
            if cached_result is not None:
                logger.info(f"Cache hit for {cache_key}")
                return cached_result
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 缓存结果
            cache_service.set(cache_key, result, ttl)
            logger.info(f"Cached result for {cache_key}")
            
            return result
        
        return wrapper
    return decorator
