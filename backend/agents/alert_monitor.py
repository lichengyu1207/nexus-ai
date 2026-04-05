"""
监控告警模块
配置实际的告警通知机制
"""

import os
import json
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class AlertMonitor:
    """告警监控器"""
    
    def __init__(self, config_file: str = None):
        self.config_file = config_file or os.path.join(
            os.path.dirname(__file__), "..", "data", "alert_config.json"
        )
        self.config = self._load_config()
        self.alert_history = []
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        from backend.config.system_config import get as get_config
        
        # 从系统配置中获取告警配置
        alert_config = get_config("alert", {
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
        })
        
        # 合并默认配置
        default_config = {
            "smtp": alert_config.get("smtp", {
                "server": "smtp.example.com",
                "port": 587,
                "username": "alert@example.com",
                "password": "your_password",
                "from_email": "alert@example.com"
            }),
            "recipients": alert_config.get("recipients", ["admin@example.com"]),
            "alert_levels": {
                "warning": {
                    "enabled": True,
                    "subject": "【预警】房都督模型路由系统",
                    "threshold": get_config("budget.warning_threshold", 80.0)
                },
                "critical": {
                    "enabled": True,
                    "subject": "【严重】房都督模型路由系统",
                    "threshold": get_config("budget.degradation_threshold", 95.0)
                }
            },
            "alert_interval": alert_config.get("alert_interval", 3600),
            "enabled": alert_config.get("enabled", True)
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as f:
                    file_config = json.load(f)
                    # 合并文件配置和默认配置
                    default_config.update(file_config)
        except Exception as e:
            logger.error(f"加载告警配置失败: {e}")
        
        # 保存配置
        self._save_config(default_config)
        return default_config
    
    def _save_config(self, config: Dict[str, Any]):
        """保存配置"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存告警配置失败: {e}")
    
    def check_alert(self, current_cost: float, daily_limit: float):
        """检查是否需要发送告警
        
        Args:
            current_cost: 当前日累计成本
            daily_limit: 日预算上限
        """
        if not self.config["enabled"]:
            return
        
        # 计算成本比例
        cost_ratio = (current_cost / daily_limit) * 100
        
        # 检查预警
        if cost_ratio >= self.config["alert_levels"]["warning"]["threshold"] and \
           cost_ratio < self.config["alert_levels"]["critical"]["threshold"]:
            self._send_alert("warning", current_cost, daily_limit, cost_ratio)
        
        # 检查严重告警
        elif cost_ratio >= self.config["alert_levels"]["critical"]["threshold"]:
            self._send_alert("critical", current_cost, daily_limit, cost_ratio)
    
    def _send_alert(self, level: str, current_cost: float, daily_limit: float, cost_ratio: float):
        """发送告警
        
        Args:
            level: 告警级别
            current_cost: 当前日累计成本
            daily_limit: 日预算上限
            cost_ratio: 成本比例
        """
        # 检查是否在告警间隔内
        if not self._should_send_alert(level):
            return
        
        # 获取告警配置
        alert_config = self.config["alert_levels"][level]
        if not alert_config["enabled"]:
            return
        
        # 构建告警消息
        subject = alert_config["subject"]
        message = self._build_alert_message(level, current_cost, daily_limit, cost_ratio)
        
        # 发送邮件
        if self._send_email(subject, message):
            # 记录告警历史
            self._record_alert(level, current_cost, daily_limit, cost_ratio)
            logger.info(f"发送 {level} 告警成功")
        else:
            logger.error(f"发送 {level} 告警失败")
    
    def _should_send_alert(self, level: str) -> bool:
        """检查是否应该发送告警
        
        Args:
            level: 告警级别
            
        Returns:
            是否应该发送告警
        """
        # 检查告警历史
        alert_interval = self.config["alert_interval"]
        now = datetime.now().timestamp()
        
        for alert in reversed(self.alert_history):
            if alert["level"] == level and now - alert["timestamp"] < alert_interval:
                return False
        
        return True
    
    def _build_alert_message(self, level: str, current_cost: float, daily_limit: float, cost_ratio: float) -> str:
        """构建告警消息
        
        Args:
            level: 告警级别
            current_cost: 当前日累计成本
            daily_limit: 日预算上限
            cost_ratio: 成本比例
            
        Returns:
            告警消息
        """
        message = f"尊敬的管理员：\n\n"
        message += f"房都督模型路由系统检测到 {level} 告警：\n\n"
        message += f"当前日累计成本：¥{current_cost:.2f}\n"
        message += f"日预算上限：¥{daily_limit:.2f}\n"
        message += f"成本比例：{cost_ratio:.1f}%\n\n"
        
        if level == "warning":
            message += "系统已触发预警，请关注成本变化。\n"
        elif level == "critical":
            message += "系统已触发严重告警，已启动降级策略，所有请求将路由至轻量模型。\n"
        
        message += "\n请及时处理，谢谢！\n"
        message += f"\n告警时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        message += "房都督模型路由系统"
        
        return message
    
    def _send_email(self, subject: str, message: str) -> bool:
        """发送邮件
        
        Args:
            subject: 邮件主题
            message: 邮件内容
            
        Returns:
            是否发送成功
        """
        try:
            # 获取SMTP配置
            smtp_config = self.config["smtp"]
            recipients = self.config["recipients"]
            
            # 创建邮件
            msg = MIMEMultipart()
            msg["From"] = smtp_config["from_email"]
            msg["To"] = ", ".join(recipients)
            msg["Subject"] = subject
            
            # 添加邮件内容
            msg.attach(MIMEText(message, "plain", "utf-8"))
            
            # 发送邮件
            with smtplib.SMTP(smtp_config["server"], smtp_config["port"]) as server:
                server.starttls()
                server.login(smtp_config["username"], smtp_config["password"])
                server.send_message(msg)
            
            return True
        except Exception as e:
            logger.error(f"发送邮件失败: {e}")
            return False
    
    def _record_alert(self, level: str, current_cost: float, daily_limit: float, cost_ratio: float):
        """记录告警历史
        
        Args:
            level: 告警级别
            current_cost: 当前日累计成本
            daily_limit: 日预算上限
            cost_ratio: 成本比例
        """
        alert = {
            "timestamp": datetime.now().timestamp(),
            "level": level,
            "current_cost": current_cost,
            "daily_limit": daily_limit,
            "cost_ratio": cost_ratio
        }
        
        self.alert_history.append(alert)
        
        # 保留最近100条告警记录
        if len(self.alert_history) > 100:
            self.alert_history = self.alert_history[-100:]
    
    def get_alert_history(self) -> List[Dict[str, Any]]:
        """获取告警历史
        
        Returns:
            告警历史
        """
        return self.alert_history
    
    def update_config(self, config: Dict[str, Any]):
        """更新配置
        
        Args:
            config: 新配置
        """
        self.config.update(config)
        self._save_config(self.config)
        logger.info("更新告警配置成功")
    
    def get_config(self) -> Dict[str, Any]:
        """获取配置
        
        Returns:
            配置
        """
        return self.config


# 全局监控器实例
alert_monitor: Optional[AlertMonitor] = None


def get_alert_monitor() -> AlertMonitor:
    """获取告警监控器实例"""
    global alert_monitor
    if alert_monitor is None:
        alert_monitor = AlertMonitor()
    return alert_monitor


def check_alert(current_cost: float, daily_limit: float):
    """检查是否需要发送告警"""
    monitor = get_alert_monitor()
    monitor.check_alert(current_cost, daily_limit)


def update_alert_config(config: Dict[str, Any]):
    """更新告警配置"""
    monitor = get_alert_monitor()
    monitor.update_config(config)


def get_alert_history() -> List[Dict[str, Any]]:
    """获取告警历史"""
    monitor = get_alert_monitor()
    return monitor.get_alert_history()
