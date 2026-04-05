"""
成本监控模块
实时跟踪调用成本并触发熔断
"""

import os
import json
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class CostMonitor:
    """成本监控器"""
    
    def __init__(self, config_file: str = None):
        self.config_file = config_file or os.path.join(
            os.path.dirname(__file__), "..", "data", "cost_monitor_config.json"
        )
        self.config = self._load_config()
        self.daily_cost = 0.0
        self.last_reset_time = datetime.now()
        self.lock = threading.Lock()
        self._reset_daily_cost()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        default_config = {
            "budget": {
                "daily_limit": 100.0,
                "warning_threshold": 80.0,
                "degradation_threshold": 95.0
            },
            "alert": {
                "enabled": True,
                "email": "admin@example.com"
            }
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
        
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
            logger.error(f"保存配置失败: {e}")
    
    def _reset_daily_cost(self):
        """重置日成本"""
        with self.lock:
            self.daily_cost = 0.0
            self.last_reset_time = datetime.now()
            logger.info("日成本已重置")
    
    def _check_reset(self):
        """检查是否需要重置日成本"""
        now = datetime.now()
        if now.date() > self.last_reset_time.date():
            self._reset_daily_cost()
    
    def add_cost(self, cost: float):
        """添加成本
        
        Args:
            cost: 成本金额
        """
        self._check_reset()
        
        with self.lock:
            self.daily_cost += cost
            logger.info(f"添加成本: ¥{cost:.4f}, 当前日累计: ¥{self.daily_cost:.2f}")
            
            # 检查预算阈值
            if self.daily_cost >= self.config["budget"]["degradation_threshold"]:
                self._trigger_degradation()
            elif self.daily_cost >= self.config["budget"]["warning_threshold"]:
                self._trigger_warning()
    
    def _trigger_warning(self):
        """触发预算预警"""
        logger.warning(f"预算预警: 当前日累计成本 ¥{self.daily_cost:.2f} 接近上限")
        if self.config["alert"]["enabled"]:
            self._send_alert("预算预警", f"当前日累计成本 ¥{self.daily_cost:.2f} 已达到预警阈值")
    
    def _trigger_degradation(self):
        """触发降级策略"""
        logger.error(f"预算超限: 当前日累计成本 ¥{self.daily_cost:.2f} 已达到降级阈值")
        if self.config["alert"]["enabled"]:
            self._send_alert("预算超限", f"当前日累计成本 ¥{self.daily_cost:.2f} 已达到降级阈值，启动降级策略")
    
    def _send_alert(self, subject: str, message: str):
        """发送告警通知
        
        Args:
            subject: 告警主题
            message: 告警消息
        """
        # 这里可以实现邮件发送、短信通知等
        logger.info(f"发送告警: {subject} - {message}")
    
    def get_daily_cost(self) -> float:
        """获取当前日累计成本
        
        Returns:
            当前日累计成本
        """
        self._check_reset()
        with self.lock:
            return self.daily_cost
    
    def is_degraded(self) -> bool:
        """检查是否处于降级状态
        
        Returns:
            是否处于降级状态
        """
        self._check_reset()
        with self.lock:
            return self.daily_cost >= self.config["budget"]["degradation_threshold"]
    
    def is_warning(self) -> bool:
        """检查是否处于预警状态
        
        Returns:
            是否处于预警状态
        """
        self._check_reset()
        with self.lock:
            return self.daily_cost >= self.config["budget"]["warning_threshold"]
    
    def get_config(self) -> Dict[str, Any]:
        """获取配置
        
        Returns:
            配置
        """
        return self.config
    
    def update_config(self, config: Dict[str, Any]):
        """更新配置
        
        Args:
            config: 新配置
        """
        self.config.update(config)
        self._save_config(self.config)
        logger.info("更新成本监控配置成功")


# 全局监控器实例
cost_monitor: Optional[CostMonitor] = None


def get_cost_monitor() -> CostMonitor:
    """获取成本监控器实例"""
    global cost_monitor
    if cost_monitor is None:
        cost_monitor = CostMonitor()
    return cost_monitor


def add_cost(cost: float):
    """添加成本"""
    monitor = get_cost_monitor()
    monitor.add_cost(cost)


def get_daily_cost() -> float:
    """获取当前日累计成本"""
    monitor = get_cost_monitor()
    return monitor.get_daily_cost()


def is_degraded() -> bool:
    """检查是否处于降级状态"""
    monitor = get_cost_monitor()
    return monitor.is_degraded()


def is_warning() -> bool:
    """检查是否处于预警状态"""
    monitor = get_cost_monitor()
    return monitor.is_warning()
