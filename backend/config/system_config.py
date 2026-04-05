"""
系统配置文件
"""

import os
import json
from typing import Dict, Any


class SystemConfig:
    """系统配置"""
    
    def __init__(self, config_file: str = None):
        self.config_file = config_file or os.path.join(
            os.path.dirname(__file__), "..", "data", "system_config.json"
        )
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        default_config = {
            "api": {
                "host": "0.0.0.0",
                "port": 8000,
                "debug": False
            },
            "models": {
                "default": "qwen-1.8b",
                "lightweight": ["qwen-1.8b", "llama-3"],
                "heavyweight": ["deepseek"]
            },
            "budget": {
                "daily_limit": 100.0,
                "warning_threshold": 80.0,
                "degradation_threshold": 95.0
            },
            "alert": {
                "enabled": True,
                "smtp": {
                    "server": "smtp.example.com",
                    "port": 587,
                    "username": "alert@example.com",
                    "password": "your_password",
                    "from_email": "alert@example.com"
                },
                "recipients": ["admin@example.com"],
                "alert_interval": 3600
            },
            "agents": {
                "enabled": True,
                "endpoint": "http://localhost:8002/api/agents"
            }
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"加载配置失败: {e}")
        
        # 保存默认配置
        self._save_config(default_config)
        return default_config
    
    def _save_config(self, config: Dict[str, Any]):
        """保存配置"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            key: 配置键，支持点号分隔的路径
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key.split(".")
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """设置配置值
        
        Args:
            key: 配置键，支持点号分隔的路径
            value: 配置值
        """
        keys = key.split(".")
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        self._save_config(self.config)
    
    def get_config(self) -> Dict[str, Any]:
        """获取完整配置
        
        Returns:
            完整配置
        """
        return self.config


# 全局配置实例
system_config = SystemConfig()


def get_config() -> SystemConfig:
    """获取系统配置实例"""
    return system_config


def get(key: str, default: Any = None) -> Any:
    """获取配置值"""
    return system_config.get(key, default)


def set(key: str, value: Any):
    """设置配置值"""
    system_config.set(key, value)
