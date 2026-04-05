"""
实时防骗提示智能体
负责在检测到潜在风险时向用户推送实时防骗提示
"""
import asyncio
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional


class AlertTrigger(Enum):
    """提示触发条件"""
    SUSPICIOUS_INTENT = "suspicious_intent"
    URGENCY_DETECTED = "urgency_detected"
    FEAR_TACTICS = "fear_tactics"
    HIGH_RISK_OPERATION = "high_risk_operation"
    IDENTITY_SUSPICIOUS = "identity_suspicious"
    NEW_DEVICE = "new_device"
    UNUSUAL_BEHAVIOR = "unusual_behavior"


class AlertChannel(Enum):
    """提示渠道"""
    IN_APP = "in_app"
    POPUP = "popup"
    SMS = "sms"
    EMAIL = "email"
    VOICE = "voice"


class AlertPriority(Enum):
    """提示优先级"""
    INFO = "info"
    WARNING = "warning"
    DANGER = "danger"
    CRITICAL = "critical"


@dataclass
class ScamAlert:
    """防骗提示"""
    alert_id: str
    trigger: AlertTrigger
    priority: AlertPriority
    title: str
    message: str
    recommended_actions: List[str]
    resources: List[str]
    channels: List[AlertChannel]
    created_at: datetime
    user_id: str
    session_id: str
    acknowledged: bool = False
    user_feedback: Optional[str] = None
    action_taken: Optional[str] = None


@dataclass
class AlertTemplate:
    """提示模板"""
    trigger: AlertTrigger
    title: str
    message_template: str
    recommended_actions: List[str]
    resources: List[str]
    default_priority: AlertPriority
    default_channels: List[AlertChannel]


@dataclass
class AlertResult:
    """提示结果"""
    alert_id: str
    delivered: bool
    channels_used: List[AlertChannel]
    user_response: Optional[str]
    timestamp: datetime


class AntiScamAlertAgent:
    """实时防骗提示智能体"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.name = "AntiScamAlertAgent"
        self.config = config or {}
        self.alert_templates = self._init_alert_templates()
        self.alert_history: Dict[str, List[ScamAlert]] = defaultdict(list)
        self.user_alert_preferences: Dict[str, Dict] = {}
        self.alert_counter = 0
        self.stats = {
            "total_alerts_sent": 0,
            "alerts_by_trigger": defaultdict(int),
            "alerts_by_channel": defaultdict(int),
            "user_acknowledgments": 0,
            "positive_feedback": 0,
            "negative_feedback": 0,
            "alerts_prevented_fraud": 0,
        }
    
    def _init_alert_templates(self) -> Dict[AlertTrigger, AlertTemplate]:
        """初始化提示模板"""
        return {
            AlertTrigger.SUSPICIOUS_INTENT: AlertTemplate(
                trigger=AlertTrigger.SUSPICIOUS_INTENT,
                title="检测到可疑对话意图",
                message_template="系统检测到当前对话可能存在诱导风险。请保持警惕，不要轻易透露个人信息或进行转账操作。",
                recommended_actions=[
                    "核实对方身份",
                    "不要急于做决定",
                    "如有疑问请联系官方客服"
                ],
                resources=["/security/tips/phishing", "/security/report"],
                default_priority=AlertPriority.WARNING,
                default_channels=[AlertChannel.IN_APP, AlertChannel.POPUP]
            ),
            AlertTrigger.URGENCY_DETECTED: AlertTemplate(
                trigger=AlertTrigger.URGENCY_DETECTED,
                title="注意：检测到紧迫感话术",
                message_template="对方正在使用紧迫感话术，这可能是一种社会工程攻击手段。真正的紧急情况通常不会要求立即转账或提供敏感信息。",
                recommended_actions=[
                    "冷静分析，不要被情绪左右",
                    "通过官方渠道核实信息",
                    "如有疑问，请24小时后再做决定"
                ],
                resources=["/security/tips/urgency", "/security/verify"],
                default_priority=AlertPriority.WARNING,
                default_channels=[AlertChannel.IN_APP, AlertChannel.POPUP]
            ),
            AlertTrigger.FEAR_TACTICS: AlertTemplate(
                trigger=AlertTrigger.FEAR_TACTICS,
                title="警告：检测到恐吓话术",
                message_template="对方正在使用恐吓或威胁性语言，这是典型的诈骗手段。请勿因恐惧而做出冲动决定。",
                recommended_actions=[
                    "不要被威胁吓倒",
                    "联系官方机构核实",
                    "如涉及法律问题，请直接联系公安机关"
                ],
                resources=["/security/tips/fear", "/security/report"],
                default_priority=AlertPriority.DANGER,
                default_channels=[AlertChannel.IN_APP, AlertChannel.POPUP, AlertChannel.SMS]
            ),
            AlertTrigger.HIGH_RISK_OPERATION: AlertTemplate(
                trigger=AlertTrigger.HIGH_RISK_OPERATION,
                title="高风险操作提醒",
                message_template="您即将执行的操作风险较高，请再次确认是否为本人意愿，并核实操作对象的身份。",
                recommended_actions=[
                    "再次确认操作内容",
                    "核实收款方信息",
                    "设置冷静期后再操作"
                ],
                resources=["/security/tips/transfer", "/security/verify"],
                default_priority=AlertPriority.DANGER,
                default_channels=[AlertChannel.IN_APP, AlertChannel.POPUP]
            ),
            AlertTrigger.IDENTITY_SUSPICIOUS: AlertTemplate(
                trigger=AlertTrigger.IDENTITY_SUSPICIOUS,
                title="身份验证提醒",
                message_template="系统检测到对方身份可能存在疑问。请通过其他渠道验证对方身份后再继续交流。",
                recommended_actions=[
                    "要求对方提供身份证明",
                    "通过官方渠道核实",
                    "不要轻信自称是客服或管理人员的说法"
                ],
                resources=["/security/tips/identity", "/security/verify"],
                default_priority=AlertPriority.WARNING,
                default_channels=[AlertChannel.IN_APP, AlertChannel.POPUP]
            ),
            AlertTrigger.NEW_DEVICE: AlertTemplate(
                trigger=AlertTrigger.NEW_DEVICE,
                title="新设备登录提醒",
                message_template="检测到您的账户在新设备上登录。如果这不是您本人的操作，请立即修改密码并联系客服。",
                recommended_actions=[
                    "确认是否为本人操作",
                    "检查账户安全设置",
                    "如有异常请立即修改密码"
                ],
                resources=["/security/device", "/security/password"],
                default_priority=AlertPriority.WARNING,
                default_channels=[AlertChannel.IN_APP, AlertChannel.SMS, AlertChannel.EMAIL]
            ),
            AlertTrigger.UNUSUAL_BEHAVIOR: AlertTemplate(
                trigger=AlertTrigger.UNUSUAL_BEHAVIOR,
                title="异常行为检测",
                message_template="检测到账户存在异常行为模式。请确认是否为本人操作，并检查账户安全。",
                recommended_actions=[
                    "检查最近的操作记录",
                    "确认账户安全",
                    "如有异常请联系客服"
                ],
                resources=["/security/activity", "/security/report"],
                default_priority=AlertPriority.WARNING,
                default_channels=[AlertChannel.IN_APP, AlertChannel.EMAIL]
            ),
        }
    
    async def initialize(self) -> bool:
        """初始化智能体"""
        await asyncio.sleep(0.1)
        return True
    
    def trigger_alert(
        self,
        trigger: AlertTrigger,
        user_id: str,
        session_id: str,
        context: Dict[str, Any] = None,
        custom_message: str = None,
        override_priority: AlertPriority = None,
        override_channels: List[AlertChannel] = None
    ) -> ScamAlert:
        """触发提示"""
        template = self.alert_templates.get(trigger)
        
        if not template:
            template = AlertTemplate(
                trigger=trigger,
                title="安全提醒",
                message_template="系统检测到潜在风险，请保持警惕。",
                recommended_actions=["如有疑问请联系客服"],
                resources=[],
                default_priority=AlertPriority.INFO,
                default_channels=[AlertChannel.IN_APP]
            )
        
        self.alert_counter += 1
        alert_id = f"alert_{datetime.now().strftime('%Y%m%d%H%M%S')}_{self.alert_counter}"
        
        message = custom_message or template.message_template
        if context:
            for key, value in context.items():
                message = message.replace(f"{{{key}}}", str(value))
        
        alert = ScamAlert(
            alert_id=alert_id,
            trigger=trigger,
            priority=override_priority or template.default_priority,
            title=template.title,
            message=message,
            recommended_actions=template.recommended_actions,
            resources=template.resources,
            channels=override_channels or template.default_channels,
            created_at=datetime.now(),
            user_id=user_id,
            session_id=session_id
        )
        
        self.alert_history[user_id].append(alert)
        self.stats["total_alerts_sent"] += 1
        self.stats["alerts_by_trigger"][trigger.value] += 1
        
        for channel in alert.channels:
            self.stats["alerts_by_channel"][channel.value] += 1
        
        return alert
    
    def deliver_alert(self, alert: ScamAlert) -> AlertResult:
        """发送提示"""
        channels_used = []
        
        preferences = self.user_alert_preferences.get(alert.user_id, {})
        
        for channel in alert.channels:
            if preferences.get(f"disable_{channel.value}", False):
                continue
            
            delivery_success = self._send_via_channel(alert, channel)
            if delivery_success:
                channels_used.append(channel)
        
        return AlertResult(
            alert_id=alert.alert_id,
            delivered=len(channels_used) > 0,
            channels_used=channels_used,
            user_response=None,
            timestamp=datetime.now()
        )
    
    def _send_via_channel(self, alert: ScamAlert, channel: AlertChannel) -> bool:
        """通过渠道发送"""
        if channel == AlertChannel.IN_APP:
            return True
        elif channel == AlertChannel.POPUP:
            return True
        elif channel == AlertChannel.SMS:
            return True
        elif channel == AlertChannel.EMAIL:
            return True
        elif channel == AlertChannel.VOICE:
            return True
        return False
    
    def record_user_feedback(
        self,
        alert_id: str,
        user_id: str,
        feedback: str,
        action_taken: str = None
    ) -> bool:
        """记录用户反馈"""
        alerts = self.alert_history.get(user_id, [])
        
        for alert in alerts:
            if alert.alert_id == alert_id:
                alert.user_feedback = feedback
                alert.action_taken = action_taken
                alert.acknowledged = True
                
                self.stats["user_acknowledgments"] += 1
                
                if feedback == "helpful":
                    self.stats["positive_feedback"] += 1
                elif feedback == "not_helpful":
                    self.stats["negative_feedback"] += 1
                
                if action_taken == "cancelled_operation":
                    self.stats["alerts_prevented_fraud"] += 1
                
                return True
        
        return False
    
    def set_user_preferences(
        self,
        user_id: str,
        preferences: Dict[str, Any]
    ):
        """设置用户偏好"""
        self.user_alert_preferences[user_id] = preferences
    
    def get_user_alerts(
        self,
        user_id: str,
        limit: int = 20,
        unacknowledged_only: bool = False
    ) -> List[ScamAlert]:
        """获取用户提示"""
        alerts = self.alert_history.get(user_id, [])
        
        if unacknowledged_only:
            alerts = [a for a in alerts if not a.acknowledged]
        
        return alerts[-limit:]
    
    def get_alert_analytics(self, days: int = 7) -> Dict[str, Any]:
        """获取提示分析"""
        cutoff = datetime.now() - timedelta(days=days)
        
        all_alerts = []
        for alerts in self.alert_history.values():
            all_alerts.extend([a for a in alerts if a.created_at > cutoff])
        
        trigger_counts = defaultdict(int)
        for alert in all_alerts:
            trigger_counts[alert.trigger.value] += 1
        
        feedback_counts = defaultdict(int)
        for alert in all_alerts:
            if alert.user_feedback:
                feedback_counts[alert.user_feedback] += 1
        
        return {
            "total_alerts": len(all_alerts),
            "by_trigger": dict(trigger_counts),
            "feedback_distribution": dict(feedback_counts),
            "acknowledgment_rate": sum(1 for a in all_alerts if a.acknowledged) / max(1, len(all_alerts)),
            "prevention_rate": self.stats["alerts_prevented_fraud"] / max(1, self.stats["total_alerts_sent"])
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "alerts_by_trigger": dict(self.stats["alerts_by_trigger"]),
            "alerts_by_channel": dict(self.stats["alerts_by_channel"]),
            "users_with_alerts": len(self.alert_history),
        }
