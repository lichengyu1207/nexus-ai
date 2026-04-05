"""
告警系统
Alert System

实现告警检测、通知、升级等功能
"""
import os
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


@dataclass
class Alert:
    id: int
    alert_type: str
    severity: AlertSeverity
    message: str
    source: str
    status: AlertStatus = AlertStatus.ACTIVE
    created_at: datetime = None
    acknowledged_at: datetime = None
    resolved_at: datetime = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AlertRule:
    name: str
    alert_type: str
    condition: Callable[[Dict], bool]
    severity: AlertSeverity
    message_template: str
    cooldown_minutes: int = 5
    enabled: bool = True
    notify_channels: List[str] = field(default_factory=lambda: ["email", "webhook"])


class AlertManager:
    """
    告警管理器
    负责告警检测、存储、通知和升级
    """
    
    DEFAULT_RULES = [
        AlertRule(
            name="high_cpu",
            alert_type="system",
            condition=lambda m: m.get("cpu_usage", 0) > 90,
            severity=AlertSeverity.HIGH,
            message_template="CPU使用率过高: {cpu_usage}%",
            cooldown_minutes=5
        ),
        AlertRule(
            name="high_memory",
            alert_type="system",
            condition=lambda m: m.get("memory_usage", 0) > 90,
            severity=AlertSeverity.HIGH,
            message_template="内存使用率过高: {memory_usage}%",
            cooldown_minutes=5
        ),
        AlertRule(
            name="low_disk",
            alert_type="system",
            condition=lambda m: m.get("disk_usage", 0) > 95,
            severity=AlertSeverity.CRITICAL,
            message_template="磁盘空间不足: 已使用 {disk_usage}%",
            cooldown_minutes=10
        ),
        AlertRule(
            name="slow_queries",
            alert_type="database",
            condition=lambda m: m.get("slow_queries", 0) > 10,
            severity=AlertSeverity.WARNING,
            message_template="慢查询数量过多: {slow_queries} 条",
            cooldown_minutes=15
        ),
        AlertRule(
            name="high_error_rate",
            alert_type="api",
            condition=lambda m: m.get("error_rate", 0) > 0.05,
            severity=AlertSeverity.HIGH,
            message_template="API错误率过高: {error_rate:.2%}",
            cooldown_minutes=5
        ),
        AlertRule(
            name="agent_down",
            alert_type="agent",
            condition=lambda m: m.get("active_agents", 999) < 5,
            severity=AlertSeverity.CRITICAL,
            message_template="活跃智能体数量过少: {active_agents}",
            cooldown_minutes=10
        ),
        AlertRule(
            name="training_failed",
            alert_type="training",
            condition=lambda m: m.get("training_failed", False),
            severity=AlertSeverity.HIGH,
            message_template="训练任务失败",
            cooldown_minutes=30
        ),
        AlertRule(
            name="defense_anomaly",
            alert_type="defense",
            condition=lambda m: m.get("defense_success_rate", 1) < 0.8,
            severity=AlertSeverity.CRITICAL,
            message_template="防御成功率下降: {defense_success_rate:.2%}",
            cooldown_minutes=5
        ),
    ]
    
    def __init__(self):
        self.rules: List[AlertRule] = list(self.DEFAULT_RULES)
        self._cooldowns: Dict[str, datetime] = {}
        self._notifiers: Dict[str, Callable] = {}
        self._db_path = None
    
    def add_rule(self, rule: AlertRule):
        """添加告警规则"""
        self.rules.append(rule)
        logger.info(f"Added alert rule: {rule.name}")
    
    def register_notifier(self, channel: str, notifier: Callable):
        """注册通知器"""
        self._notifiers[channel] = notifier
        logger.info(f"Registered notifier for channel: {channel}")
    
    async def check_and_alert(self, metrics: Dict[str, Any]) -> List[Alert]:
        """
        检查指标并生成告警
        """
        alerts = []
        
        for rule in self.rules:
            if not rule.enabled:
                continue
            
            if self._is_in_cooldown(rule.name):
                continue
            
            try:
                if rule.condition(metrics):
                    alert = await self._create_alert(rule, metrics)
                    if alert:
                        alerts.append(alert)
                        self._set_cooldown(rule.name, rule.cooldown_minutes)
                        
                        await self._send_notifications(alert, rule.notify_channels)
                        
            except Exception as e:
                logger.error(f"Error checking rule {rule.name}: {e}")
        
        return alerts
    
    def _is_in_cooldown(self, rule_name: str) -> bool:
        """检查是否在冷却期"""
        if rule_name not in self._cooldowns:
            return False
        
        return datetime.now() < self._cooldowns[rule_name]
    
    def _set_cooldown(self, rule_name: str, minutes: int):
        """设置冷却期"""
        self._cooldowns[rule_name] = datetime.now() + timedelta(minutes=minutes)
    
    async def _create_alert(self, rule: AlertRule, metrics: Dict) -> Optional[Alert]:
        """创建告警"""
        try:
            message = rule.message_template.format(**metrics)
        except KeyError:
            message = rule.message_template
        
        alert = Alert(
            id=0,
            alert_type=rule.alert_type,
            severity=rule.severity,
            message=message,
            source=rule.name,
            created_at=datetime.now(),
            metadata=metrics
        )
        
        alert.id = await self._store_alert(alert)
        
        logger.warning(f"Alert created: [{rule.severity.value}] {message}")
        
        return alert
    
    async def _store_alert(self, alert: Alert) -> int:
        """存储告警到数据库"""
        from ..database import get_db_connection
        
        async for conn in get_db_connection():
            try:
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS alerts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        alert_type TEXT,
                        severity TEXT,
                        message TEXT,
                        source TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        acknowledged_at TIMESTAMP,
                        resolved_at TIMESTAMP,
                        metadata TEXT
                    )
                """)
                
                cursor = await conn.execute("""
                    INSERT INTO alerts (alert_type, severity, message, source, metadata)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    alert.alert_type,
                    alert.severity.value,
                    alert.message,
                    alert.source,
                    json.dumps(alert.metadata)
                ))
                
                alert_id = cursor.lastrowid
                return alert_id
                
            finally:
                await conn.close()
                break
        
        return 0
    
    async def _send_notifications(self, alert: Alert, channels: List[str]):
        """发送通知"""
        for channel in channels:
            notifier = self._notifiers.get(channel)
            if notifier:
                try:
                    await notifier(alert)
                    logger.info(f"Notification sent via {channel} for alert {alert.id}")
                except Exception as e:
                    logger.error(f"Failed to send notification via {channel}: {e}")
    
    async def acknowledge_alert(self, alert_id: int) -> bool:
        """确认告警"""
        from ..database import get_db_connection
        
        async for conn in get_db_connection():
            try:
                await conn.execute("""
                    UPDATE alerts
                    SET status = 'acknowledged', acknowledged_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (alert_id,))
                
                return True
            finally:
                await conn.close()
                break
        
        return False
    
    async def resolve_alert(self, alert_id: int) -> bool:
        """解决告警"""
        from ..database import get_db_connection
        
        async for conn in get_db_connection():
            try:
                await conn.execute("""
                    UPDATE alerts
                    SET status = 'resolved', resolved_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (alert_id,))
                
                return True
            finally:
                await conn.close()
                break
        
        return False
    
    async def get_active_alerts(self) -> List[Alert]:
        """获取活跃告警"""
        from ..database import get_db_connection
        
        alerts = []
        
        async for conn in get_db_connection():
            try:
                cursor = await conn.execute("""
                    SELECT id, alert_type, severity, message, source, status, 
                           created_at, acknowledged_at, resolved_at, metadata
                    FROM alerts
                    WHERE status = 'active'
                    ORDER BY created_at DESC
                """)
                
                rows = await cursor.fetchall()
                for row in rows:
                    alerts.append(Alert(
                        id=row[0],
                        alert_type=row[1],
                        severity=AlertSeverity(row[2]),
                        message=row[3],
                        source=row[4],
                        status=AlertStatus(row[5]),
                        created_at=row[6],
                        acknowledged_at=row[7],
                        resolved_at=row[8],
                        metadata=json.loads(row[9]) if row[9] else {}
                    ))
                    
            finally:
                await conn.close()
                break
        
        return alerts
    
    async def cleanup_old_alerts(self, days: int = 30):
        """清理旧告警"""
        from ..database import get_db_connection
        
        async for conn in get_db_connection():
            try:
                await conn.execute("""
                    DELETE FROM alerts
                    WHERE status = 'resolved'
                    AND created_at < datetime('now', ?)
                """, (f"-{days} days",))
                
                logger.info(f"Cleaned up alerts older than {days} days")
                
            finally:
                await conn.close()
                break


class EmailNotifier:
    """邮件通知器"""
    
    def __init__(self, smtp_host: str, smtp_port: int, smtp_user: str, smtp_pass: str):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_pass = smtp_pass
    
    async def __call__(self, alert: Alert):
        """发送邮件通知"""
        try:
            import aiosmtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            message = MIMEMultipart()
            message["From"] = self.smtp_user
            message["To"] = os.getenv("ALERT_EMAIL_TO", "admin@example.com")
            message["Subject"] = f"[{alert.severity.value.upper()}] {alert.alert_type} Alert"
            
            body = f"""
Alert Details:
- Type: {alert.alert_type}
- Severity: {alert.severity.value}
- Message: {alert.message}
- Source: {alert.source}
- Time: {alert.created_at}

Metadata:
{json.dumps(alert.metadata, indent=2)}
            """
            
            message.attach(MIMEText(body, "plain"))
            
            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_pass,
                use_tls=True
            )
            
        except ImportError:
            logger.warning("aiosmtplib not installed, email notification skipped")
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")


class WebhookNotifier:
    """Webhook通知器"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    async def __call__(self, alert: Alert):
        """发送Webhook通知"""
        try:
            import aiohttp
            
            payload = {
                "alert_id": alert.id,
                "alert_type": alert.alert_type,
                "severity": alert.severity.value,
                "message": alert.message,
                "source": alert.source,
                "created_at": alert.created_at.isoformat() if alert.created_at else None,
                "metadata": alert.metadata
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status >= 400:
                        logger.error(f"Webhook returned status {response.status}")
                        
        except ImportError:
            logger.warning("aiohttp not installed, webhook notification skipped")
        except Exception as e:
            logger.error(f"Failed to send webhook notification: {e}")


class SlackNotifier:
    """Slack通知器"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    async def __call__(self, alert: Alert):
        """发送Slack通知"""
        try:
            import aiohttp
            
            color = {
                AlertSeverity.INFO: "#36a64f",
                AlertSeverity.WARNING: "#ffcc00",
                AlertSeverity.HIGH: "#ff6600",
                AlertSeverity.CRITICAL: "#ff0000"
            }.get(alert.severity, "#cccccc")
            
            payload = {
                "attachments": [{
                    "color": color,
                    "title": f"[{alert.severity.value.upper()}] {alert.alert_type}",
                    "text": alert.message,
                    "fields": [
                        {"title": "Source", "value": alert.source, "short": True},
                        {"title": "Time", "value": str(alert.created_at), "short": True}
                    ],
                    "footer": "房都督运维告警"
                }]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload
                ) as response:
                    if response.status >= 400:
                        logger.error(f"Slack webhook returned status {response.status}")
                        
        except ImportError:
            logger.warning("aiohttp not installed, Slack notification skipped")
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")


alert_manager = AlertManager()


async def setup_alert_system():
    """初始化告警系统"""
    webhook_url = os.getenv("ALERT_WEBHOOK_URL")
    if webhook_url:
        alert_manager.register_notifier("webhook", WebhookNotifier(webhook_url))
    
    slack_webhook = os.getenv("SLACK_WEBHOOK_URL")
    if slack_webhook:
        alert_manager.register_notifier("slack", SlackNotifier(slack_webhook))
    
    smtp_host = os.getenv("SMTP_HOST")
    if smtp_host:
        alert_manager.register_notifier("email", EmailNotifier(
            smtp_host=smtp_host,
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            smtp_user=os.getenv("SMTP_USER", ""),
            smtp_pass=os.getenv("SMTP_PASS", "")
        ))
    
    logger.info("Alert system initialized")


async def run_alert_check():
    """运行告警检查"""
    import psutil
    
    metrics = {
        "cpu_usage": psutil.cpu_percent(interval=0.1),
        "memory_usage": psutil.virtual_memory().percent,
        "disk_usage": psutil.disk_usage('/').percent,
    }
    
    try:
        from ..database import get_db_connection
        
        async for conn in get_db_connection():
            try:
                cursor = await conn.execute("""
                    SELECT COUNT(*) FROM slow_queries
                    WHERE timestamp >= datetime('now', '-1 hour')
                    AND duration_ms > 500
                """)
                row = await cursor.fetchone()
                metrics["slow_queries"] = row[0] if row else 0
                
            finally:
                await conn.close()
                break
    except:
        pass
    
    alerts = await alert_manager.check_and_alert(metrics)
    
    return alerts
