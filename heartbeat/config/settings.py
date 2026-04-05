"""
配置管理模块
从环境变量读取心跳上报相关配置
"""
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Settings:
    """应用配置"""
    
    redis_url: str = "redis://localhost:6379/0"
    heartbeat_interval: int = 5
    heartbeat_ttl: int = 15
    log_level: str = "INFO"
    
    @classmethod
    def from_env(cls) -> "Settings":
        """从环境变量加载配置"""
        return cls(
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            heartbeat_interval=int(os.getenv("HEARTBEAT_INTERVAL", "5")),
            heartbeat_ttl=int(os.getenv("HEARTBEAT_TTL", "15")),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )


settings = Settings.from_env()
