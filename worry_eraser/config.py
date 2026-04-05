"""
配置管理模块
从环境变量加载应用配置
兼容Python 3.10.19
"""

import os
from typing import Optional


class Settings:
    """应用配置"""
    
    def __init__(self):
        # 应用配置
        self.app_name = os.getenv("APP_NAME", "烦恼橡皮擦")
        self.app_version = os.getenv("APP_VERSION", "2.1.0")
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        self.environment = os.getenv("ENVIRONMENT", "development")
        
        # 服务器配置
        self.host = os.getenv("HOST", "0.0.0.0")
        self.port = int(os.getenv("PORT", "8001"))
        self.reload = os.getenv("RELOAD", "false").lower() == "true"
        
        # 数据库配置
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///./data.db")
        self.database_pool_size = int(os.getenv("DATABASE_POOL_SIZE", "5"))
        
        # 日志配置
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        
        # 功能开关
        self.enable_demo_mode = os.getenv("ENABLE_DEMO_MODE", "true").lower() == "true"
        self.enable_triple_animation = os.getenv("ENABLE_TRIPLE_ANIMATION", "true").lower() == "true"
        
        # 外部服务配置（可选）
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.redis_url = os.getenv("REDIS_URL")
    
    def dict(self):
        """返回所有配置的字典表示"""
        return {
            "app_name": self.app_name,
            "app_version": self.app_version,
            "debug": self.debug,
            "environment": self.environment,
            "host": self.host,
            "port": self.port,
            "reload": self.reload,
            "database_url": self.database_url,
            "database_pool_size": self.database_pool_size,
            "log_level": self.log_level,
            "enable_demo_mode": self.enable_demo_mode,
            "enable_triple_animation": self.enable_triple_animation,
        }


# 全局配置实例
settings = Settings()
