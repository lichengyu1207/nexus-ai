"""
登录限流模块
实现基于IP和用户的登录限流
"""
import asyncio
from typing import Dict, Tuple, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class LoginRateLimiter:
    """登录限流器"""
    
    _instance: Optional['LoginRateLimiter'] = None
    _lock = asyncio.Lock()
    
    def __init__(
        self,
        max_attempts_per_ip: int = 10,
        max_attempts_per_user: int = 5,
        window_minutes: int = 15,
        block_duration_minutes: int = 30
    ):
        self.max_attempts_per_ip = max_attempts_per_ip
        self.max_attempts_per_user = max_attempts_per_user
        self.window_minutes = window_minutes
        self.block_duration_minutes = block_duration_minutes
        
        # 存储格式: {key: [(timestamp, success), ...]}
        self._ip_attempts: Dict[str, list] = defaultdict(list)
        self._user_attempts: Dict[str, list] = defaultdict(list)
        
        # 被封锁的IP和用户
        self._blocked_ips: Dict[str, datetime] = {}
        self._blocked_users: Dict[str, datetime] = {}
        
        # 清理任务
        self._cleanup_task: Optional[asyncio.Task] = None
    
    @classmethod
    async def get_instance(cls, **kwargs) -> 'LoginRateLimiter':
        """获取单例实例"""
        if cls._instance is None:
            async with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(**kwargs)
                    cls._instance._start_cleanup_task()
        return cls._instance
    
    def _start_cleanup_task(self):
        """启动清理任务"""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def _cleanup_loop(self):
        """定期清理过期记录"""
        while True:
            try:
                await asyncio.sleep(300)  # 每5分钟清理一次
                await self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
    
    async def _cleanup_expired(self):
        """清理过期记录"""
        now = datetime.now()
        cutoff = now - timedelta(minutes=self.window_minutes + self.block_duration_minutes)
        
        # 清理IP尝试记录
        for ip in list(self._ip_attempts.keys()):
            self._ip_attempts[ip] = [
                (ts, success) for ts, success in self._ip_attempts[ip]
                if ts > cutoff
            ]
            if not self._ip_attempts[ip]:
                del self._ip_attempts[ip]
        
        # 清理用户尝试记录
        for user in list(self._user_attempts.keys()):
            self._user_attempts[user] = [
                (ts, success) for ts, success in self._user_attempts[user]
                if ts > cutoff
            ]
            if not self._user_attempts[user]:
                del self._user_attempts[user]
        
        # 清理封锁记录
        for ip in list(self._blocked_ips.keys()):
            if self._blocked_ips[ip] < now:
                del self._blocked_ips[ip]
        
        for user in list(self._blocked_users.keys()):
            if self._blocked_users[user] < now:
                del self._blocked_users[user]
    
    def is_blocked(self, ip: str, user: str) -> Tuple[bool, str]:
        """检查是否被封锁"""
        now = datetime.now()
        
        if ip in self._blocked_ips:
            if self._blocked_ips[ip] > now:
                remaining = (self._blocked_ips[ip] - now).seconds // 60
                return True, f"IP被封锁，请{remaining}分钟后再试"
            else:
                del self._blocked_ips[ip]
        
        if user in self._blocked_users:
            if self._blocked_users[user] > now:
                remaining = (self._blocked_users[user] - now).seconds // 60
                return True, f"账号被临时锁定，请{remaining}分钟后再试"
            else:
                del self._blocked_users[user]
        
        return False, ""
    
    def check_rate_limit(self, ip: str, user: str) -> Tuple[bool, str]:
        """检查是否超过限流"""
        # 先检查是否被封锁
        blocked, msg = self.is_blocked(ip, user)
        if blocked:
            return False, msg
        
        now = datetime.now()
        window_start = now - timedelta(minutes=self.window_minutes)
        
        # 检查IP限流
        ip_attempts = [
            ts for ts, _ in self._ip_attempts[ip]
            if ts > window_start
        ]
        if len(ip_attempts) >= self.max_attempts_per_ip:
            return False, f"该IP登录尝试过多，请稍后再试"
        
        # 检查用户限流
        user_attempts = [
            ts for ts, _ in self._user_attempts[user]
            if ts > window_start
        ]
        if len(user_attempts) >= self.max_attempts_per_user:
            return False, f"该账号登录尝试过多，请稍后再试"
        
        return True, ""
    
    def record_attempt(self, ip: str, user: str, success: bool):
        """记录登录尝试"""
        now = datetime.now()
        
        self._ip_attempts[ip].append((now, success))
        self._user_attempts[user].append((now, success))
        
        # 如果失败次数过多，进行封锁
        if not success:
            window_start = now - timedelta(minutes=self.window_minutes)
            
            # 检查IP失败次数
            ip_failures = sum(
                1 for ts, s in self._ip_attempts[ip]
                if ts > window_start and not s
            )
            if ip_failures >= self.max_attempts_per_ip:
                self._blocked_ips[ip] = now + timedelta(minutes=self.block_duration_minutes)
                logger.warning(f"IP {ip} blocked due to too many failed attempts")
            
            # 检查用户失败次数
            user_failures = sum(
                1 for ts, s in self._user_attempts[user]
                if ts > window_start and not s
            )
            if user_failures >= self.max_attempts_per_user:
                self._blocked_users[user] = now + timedelta(minutes=self.block_duration_minutes)
                logger.warning(f"User {user} blocked due to too many failed attempts")
    
    def get_remaining_attempts(self, ip: str, user: str) -> Dict[str, int]:
        """获取剩余尝试次数"""
        now = datetime.now()
        window_start = now - timedelta(minutes=self.window_minutes)
        
        ip_attempts = len([
            ts for ts, _ in self._ip_attempts[ip]
            if ts > window_start
        ])
        
        user_attempts = len([
            ts for ts, _ in self._user_attempts[user]
            if ts > window_start
        ])
        
        return {
            "ip_remaining": max(0, self.max_attempts_per_ip - ip_attempts),
            "user_remaining": max(0, self.max_attempts_per_user - user_attempts)
        }

# 全局限流器实例
_rate_limiter: Optional[LoginRateLimiter] = None

async def get_rate_limiter() -> LoginRateLimiter:
    """获取限流器实例"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = await LoginRateLimiter.get_instance()
    return _rate_limiter
