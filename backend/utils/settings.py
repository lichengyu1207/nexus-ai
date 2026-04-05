"""
系统设置工具模块
提供设置缓存和获取功能
"""
import json
from typing import Optional, Dict, Any, List
from functools import lru_cache

from ..database import PrivacyPolicyDB


DEFAULT_SETTINGS: Dict[str, Dict[str, Any]] = {
    "allow_registration": {
        "value": True,
        "type": "bool",
        "description": "是否允许新用户注册",
        "group": "用户管理"
    },
    "default_analysis_style": {
        "value": "balanced",
        "type": "string",
        "description": "默认分析风格",
        "group": "分析设置",
        "options": ["balanced", "detailed", "concise", "investment"]
    },
    "max_tasks_per_user": {
        "value": 100,
        "type": "int",
        "description": "每用户最大任务数",
        "group": "用户管理",
        "min": 1,
        "max": 1000
    },
    "max_teams_per_user": {
        "value": 10,
        "type": "int",
        "description": "每用户最大团队数",
        "group": "用户管理",
        "min": 1,
        "max": 100
    },
    "maintenance_mode": {
        "value": False,
        "type": "bool",
        "description": "维护模式",
        "group": "系统设置"
    },
    "smtp_host": {
        "value": "",
        "type": "string",
        "description": "SMTP服务器地址",
        "group": "邮件设置"
    },
    "smtp_port": {
        "value": 587,
        "type": "int",
        "description": "SMTP服务器端口",
        "group": "邮件设置"
    },
    "smtp_user": {
        "value": "",
        "type": "string",
        "description": "SMTP用户名",
        "group": "邮件设置"
    },
    "smtp_password": {
        "value": "",
        "type": "password",
        "description": "SMTP密码",
        "group": "邮件设置"
    },
    "smtp_from_email": {
        "value": "",
        "type": "string",
        "description": "发件人邮箱",
        "group": "邮件设置"
    },
    "smtp_from_name": {
        "value": "房都督AI",
        "type": "string",
        "description": "发件人名称",
        "group": "邮件设置"
    },
    "site_name": {
        "value": "房都督AI",
        "type": "string",
        "description": "网站名称",
        "group": "基础设置"
    },
    "site_description": {
        "value": "智能房产分析与估值系统",
        "type": "string",
        "description": "网站描述",
        "group": "基础设置"
    },
    "contact_email": {
        "value": "",
        "type": "string",
        "description": "联系邮箱",
        "group": "基础设置"
    },
    "default_user_role": {
        "value": "user",
        "type": "string",
        "description": "新用户默认角色",
        "group": "用户管理",
        "options": ["user", "admin"]
    },
    "task_timeout_minutes": {
        "value": 30,
        "type": "int",
        "description": "任务超时时间（分钟）",
        "group": "分析设置",
        "min": 5,
        "max": 120
    },
    "max_report_history": {
        "value": 50,
        "type": "int",
        "description": "最大报告历史数量",
        "group": "分析设置",
        "min": 10,
        "max": 200
    }
}

_settings_cache: Dict[str, Any] = {}
_cache_loaded: bool = False


async def load_settings_cache() -> None:
    """加载设置到内存缓存"""
    global _settings_cache, _cache_loaded
    
    db_settings = await PrivacyPolicyDB.get_all_settings()
    
    _settings_cache = {}
    for key, config in DEFAULT_SETTINGS.items():
        if key in db_settings:
            value = db_settings[key]
            if config["type"] == "bool":
                _settings_cache[key] = value.lower() == "true"
            elif config["type"] == "int":
                _settings_cache[key] = int(value)
            else:
                _settings_cache[key] = value
        else:
            _settings_cache[key] = config["value"]
    
    _cache_loaded = True


def clear_settings_cache() -> None:
    """清除设置缓存"""
    global _settings_cache, _cache_loaded
    _settings_cache = {}
    _cache_loaded = False


async def get_setting(key: str, default: Any = None) -> Any:
    """
    获取单个设置值
    
    Args:
        key: 设置键
        default: 默认值
        
    Returns:
        设置值
    """
    global _cache_loaded
    
    if not _cache_loaded:
        await load_settings_cache()
    
    return _settings_cache.get(key, default)


async def get_settings_by_group(group: str) -> Dict[str, Any]:
    """
    获取指定分组的设置
    
    Args:
        group: 分组名称
        
    Returns:
        设置字典
    """
    global _cache_loaded
    
    if not _cache_loaded:
        await load_settings_cache()
    
    result = {}
    for key, config in DEFAULT_SETTINGS.items():
        if config.get("group") == group:
            result[key] = {
                "value": _settings_cache.get(key, config["value"]),
                "type": config["type"],
                "description": config["description"],
                **{k: v for k, v in config.items() if k not in ["value", "type", "description"]}
            }
    
    return result


async def get_all_settings_grouped() -> Dict[str, Dict[str, Any]]:
    """
    获取所有设置（按分组）
    
    Returns:
        分组设置字典
    """
    global _cache_loaded
    
    if not _cache_loaded:
        await load_settings_cache()
    
    result: Dict[str, Dict[str, Any]] = {}
    
    for key, config in DEFAULT_SETTINGS.items():
        group = config.get("group", "其他")
        
        if group not in result:
            result[group] = {}
        
        result[group][key] = {
            "value": _settings_cache.get(key, config["value"]),
            "type": config["type"],
            "description": config["description"],
            **{k: v for k, v in config.items() if k not in ["value", "type", "description", "group"]}
        }
    
    return result


async def set_setting(key: str, value: Any) -> bool:
    """
    设置单个值
    
    Args:
        key: 设置键
        value: 设置值
        
    Returns:
        是否成功
    """
    global _settings_cache
    
    if key not in DEFAULT_SETTINGS:
        return False
    
    config = DEFAULT_SETTINGS[key]
    
    if config["type"] == "bool":
        str_value = "true" if value else "false"
    elif config["type"] == "int":
        str_value = str(int(value))
    elif config["type"] == "password":
        str_value = str(value) if value else ""
    else:
        str_value = str(value)
    
    success = await AdminDB.set_setting(key, str_value, config.get("description"))
    
    if success:
        _settings_cache[key] = value
    
    return success


async def set_settings(settings: Dict[str, Any]) -> Dict[str, bool]:
    """
    批量设置
    
    Args:
        settings: 设置字典
        
    Returns:
        每个设置的结果
    """
    results = {}
    for key, value in settings.items():
        results[key] = await set_setting(key, value)
    return results


def get_setting_definition(key: str) -> Optional[Dict[str, Any]]:
    """
    获取设置定义
    
    Args:
        key: 设置键
        
    Returns:
        设置定义
    """
    return DEFAULT_SETTINGS.get(key)


def get_all_setting_keys() -> List[str]:
    """
    获取所有设置键
    
    Returns:
        设置键列表
    """
    return list(DEFAULT_SETTINGS.keys())


def get_setting_groups() -> List[str]:
    """
    获取所有设置分组
    
    Returns:
        分组列表
    """
    groups = set()
    for config in DEFAULT_SETTINGS.values():
        if "group" in config:
            groups.add(config["group"])
    return sorted(list(groups))


def validate_setting_value(key: str, value: Any) -> tuple[bool, Optional[str]]:
    """
    验证设置值
    
    Args:
        key: 设置键
        value: 设置值
        
    Returns:
        (是否有效, 错误信息)
    """
    config = DEFAULT_SETTINGS.get(key)
    if not config:
        return False, f"未知的设置项: {key}"
    
    setting_type = config["type"]
    
    if setting_type == "bool":
        if not isinstance(value, bool):
            return False, "值必须是布尔类型"
    
    elif setting_type == "int":
        try:
            int_value = int(value)
        except (ValueError, TypeError):
            return False, "值必须是整数"
        
        if "min" in config and int_value < config["min"]:
            return False, f"值不能小于 {config['min']}"
        if "max" in config and int_value > config["max"]:
            return False, f"值不能大于 {config['max']}"
    
    elif setting_type == "string":
        if not isinstance(value, str):
            return False, "值必须是字符串"
        
        if "options" in config and value not in config["options"]:
            return False, f"值必须是以下选项之一: {', '.join(config['options'])}"
    
    return True, None
