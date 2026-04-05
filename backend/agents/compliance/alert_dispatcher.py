"""
告警推送与处置跟踪智能体
Alert Dispatcher Agent - 将风险告警推送给相关责任人并跟踪处置情况
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
import asyncio
import json
import uuid


class AlertSeverity(Enum):
    P0 = "p0"
    P1 = "p1"
    P2 = "p2"
    P3 = "p3"


class AlertStatus(Enum):
    PENDING = "pending"
    SENT = "sent"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    FALSE_POSITIVE = "false_positive"
    CLOSED = "closed"


class AlertChannel(Enum):
    EMAIL = "email"
    SMS = "sms"
    WECHAT = "wechat"
    DINGTALK = "dingtalk"
    WEBHOOK = "webhook"
    IN_APP = "in_app"


@dataclass
class Alert:
    alert_id: str
    title: str
    description: str
    severity: AlertSeverity
    category: str
    source: str
    affected_entities: List[str]
    status: AlertStatus = AlertStatus.PENDING
    assigned_to: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    deadline: Optional[datetime] = None
    escalation_level: int = 0
    channels_used: List[AlertChannel] = field(default_factory=list)
    response_history: List[Dict] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Responder:
    responder_id: str
    name: str
    email: str
    phone: Optional[str] = None
    wechat_id: Optional[str] = None
    dingtalk_id: Optional[str] = None
    roles: List[str] = field(default_factory=list)
    availability: str = "24/7"
    escalation_order: int = 0


class NotificationChannel:
    def __init__(self, channel_type: AlertChannel):
        self.channel_type = channel_type
        self.enabled = True
        self.config: Dict[str, Any] = {}

    def configure(self, config: Dict[str, Any]) -> None:
        self.config = config

    async def send(
        self, recipient: Responder, alert: Alert
    ) -> Dict[str, Any]:
        result = {
            "channel": self.channel_type.value,
            "recipient": recipient.responder_id,
            "success": False,
            "error": None,
            "sent_at": datetime.utcnow().isoformat(),
        }

        if not self.enabled:
            result["error"] = "Channel disabled"
            return result

        try:
            if self.channel_type == AlertChannel.EMAIL:
                result["success"] = await self._send_email(recipient, alert)
            elif self.channel_type == AlertChannel.SMS:
                result["success"] = await self._send_sms(recipient, alert)
            elif self.channel_type == AlertChannel.WECHAT:
                result["success"] = await self._send_wechat(recipient, alert)
            elif self.channel_type == AlertChannel.DINGTALK:
                result["success"] = await self._send_dingtalk(recipient, alert)
            elif self.channel_type == AlertChannel.WEBHOOK:
                result["success"] = await self._send_webhook(recipient, alert)
            elif self.channel_type == AlertChannel.IN_APP:
                result["success"] = await self._send_in_app(recipient, alert)
        except Exception as e:
            result["error"] = str(e)

        return result

    async def _send_email(self, recipient: Responder, alert: Alert) -> bool:
        return True

    async def _send_sms(self, recipient: Responder, alert: Alert) -> bool:
        if not recipient.phone:
            return False
        return True

    async def _send_wechat(self, recipient: Responder, alert: Alert) -> bool:
        if not recipient.wechat_id:
            return False
        return True

    async def _send_dingtalk(self, recipient: Responder, alert: Alert) -> bool:
        if not recipient.dingtalk_id:
            return False
        return True

    async def _send_webhook(self, recipient: Responder, alert: Alert) -> bool:
        return True

    async def _send_in_app(self, recipient: Responder, alert: Alert) -> bool:
        return True


class EscalationPolicy:
    def __init__(self, policy_name: str):
        self.policy_name = policy_name
        self.levels: List[Dict] = []

    def add_level(
        self,
        level: int,
        responders: List[str],
        timeout_minutes: int,
        channels: List[AlertChannel],
    ) -> None:
        self.levels.append(
            {
                "level": level,
                "responders": responders,
                "timeout_minutes": timeout_minutes,
                "channels": channels,
            }
        )

    def get_next_level(self, current_level: int) -> Optional[Dict]:
        for level_config in self.levels:
            if level_config["level"] > current_level:
                return level_config
        return None

    def get_timeout_for_level(self, level: int) -> int:
        for level_config in self.levels:
            if level_config["level"] == level:
                return level_config["timeout_minutes"]
        return 60


class ResponderRegistry:
    def __init__(self):
        self.responders: Dict[str, Responder] = {}
        self.role_responders: Dict[str, List[str]] = {}

    def register_responder(self, responder: Responder) -> None:
        self.responders[responder.responder_id] = responder

        for role in responder.roles:
            if role not in self.role_responders:
                self.role_responders[role] = []
            self.role_responders[role].append(responder.responder_id)

    def get_responder(self, responder_id: str) -> Optional[Responder]:
        return self.responders.get(responder_id)

    def get_responders_by_role(self, role: str) -> List[Responder]:
        responder_ids = self.role_responders.get(role, [])
        return [self.responders[rid] for rid in responder_ids if rid in self.responders]

    def get_responders_by_category(self, category: str) -> List[Responder]:
        role_mapping = {
            "data_security": ["security_engineer", "data_admin"],
            "privacy_risk": ["privacy_officer", "legal_counsel"],
            "audit_issue": ["auditor", "compliance_officer"],
            "ai_ethics": ["ai_ethics_officer", "data_scientist"],
            "compliance_violation": ["compliance_officer", "legal_counsel"],
        }

        roles = role_mapping.get(category, ["on_call_engineer"])
        responders = []
        for role in roles:
            responders.extend(self.get_responders_by_role(role))
        return list({r.responder_id: r for r in responders}.values())


class AlertDispatcherAgent:
    def __init__(self, agent_id: str = "alert_dispatcher_001"):
        self.agent_id = agent_id
        self.channels: Dict[AlertChannel, NotificationChannel] = {}
        self.escalation_policies: Dict[str, EscalationPolicy] = {}
        self.responder_registry = ResponderRegistry()

        self.alerts: List[Alert] = []
        self.alert_counter = 0

        self._initialize_default_channels()
        self._initialize_default_policies()

    def _initialize_default_channels(self) -> None:
        for channel_type in AlertChannel:
            self.channels[channel_type] = NotificationChannel(channel_type)

    def _initialize_default_policies(self) -> None:
        p0_policy = EscalationPolicy("P0严重告警")
        p0_policy.add_level(1, ["on_call_engineer"], 15, [AlertChannel.SMS, AlertChannel.PHONE])
        p0_policy.add_level(2, ["team_lead"], 30, [AlertChannel.SMS, AlertChannel.EMAIL])
        p0_policy.add_level(3, ["manager"], 60, [AlertChannel.SMS, AlertChannel.EMAIL])
        self.escalation_policies["p0"] = p0_policy

        p1_policy = EscalationPolicy("P1高危告警")
        p1_policy.add_level(1, ["on_call_engineer"], 30, [AlertChannel.EMAIL, AlertChannel.WECHAT])
        p1_policy.add_level(2, ["team_lead"], 60, [AlertChannel.EMAIL, AlertChannel.SMS])
        self.escalation_policies["p1"] = p1_policy

        p2_policy = EscalationPolicy("P2中危告警")
        p2_policy.add_level(1, ["on_call_engineer"], 120, [AlertChannel.EMAIL])
        p2_policy.add_level(2, ["team_lead"], 240, [AlertChannel.EMAIL])
        self.escalation_policies["p2"] = p2_policy

        p3_policy = EscalationPolicy("P3低危告警")
        p3_policy.add_level(1, ["on_call_engineer"], 480, [AlertChannel.EMAIL])
        self.escalation_policies["p3"] = p3_policy

    def create_alert(
        self,
        title: str,
        description: str,
        severity: AlertSeverity,
        category: str,
        source: str,
        affected_entities: List[str],
        metadata: Dict[str, Any] = None,
    ) -> Alert:
        self.alert_counter += 1
        alert_id = f"alert_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{self.alert_counter:04d}"

        deadline = self._calculate_deadline(severity)

        alert = Alert(
            alert_id=alert_id,
            title=title,
            description=description,
            severity=severity,
            category=category,
            source=source,
            affected_entities=affected_entities,
            deadline=deadline,
            metadata=metadata or {},
        )

        self.alerts.append(alert)
        return alert

    def _calculate_deadline(self, severity: AlertSeverity) -> datetime:
        deadlines = {
            AlertSeverity.P0: timedelta(hours=1),
            AlertSeverity.P1: timedelta(hours=4),
            AlertSeverity.P2: timedelta(hours=24),
            AlertSeverity.P3: timedelta(hours=72),
        }
        return datetime.utcnow() + deadlines.get(severity, timedelta(hours=24))

    async def dispatch_alert(self, alert: Alert) -> Dict[str, Any]:
        policy = self.escalation_policies.get(alert.severity.value)
        if not policy:
            policy = self.escalation_policies["p3"]

        level_config = policy.levels[0] if policy.levels else None
        if not level_config:
            return {"success": False, "error": "No escalation level configured"}

        responders = []
        for responder_id in level_config["responders"]:
            responder = self.responder_registry.get_responder(responder_id)
            if not responder:
                responders.extend(
                    self.responder_registry.get_responders_by_category(alert.category)
                )
            else:
                responders.append(responder)

        if not responders:
            responders = self.responder_registry.get_responders_by_role("on_call_engineer")

        results = []
        for responder in responders:
            for channel_type in level_config["channels"]:
                if channel_type in self.channels:
                    channel = self.channels[channel_type]
                    result = await channel.send(responder, alert)
                    results.append(result)
                    alert.channels_used.append(channel_type)

        if results:
            alert.status = AlertStatus.SENT
            alert.escalation_level = 1

        return {
            "success": any(r["success"] for r in results),
            "alert_id": alert.alert_id,
            "dispatch_results": results,
        }

    def acknowledge_alert(
        self, alert_id: str, responder_id: str
    ) -> Optional[Alert]:
        alert = self.get_alert(alert_id)
        if alert and alert.status in [AlertStatus.SENT, AlertStatus.ESCALATED]:
            alert.status = AlertStatus.ACKNOWLEDGED
            alert.acknowledged_at = datetime.utcnow()
            alert.assigned_to = responder_id
            alert.response_history.append(
                {
                    "action": "acknowledged",
                    "responder": responder_id,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
        return alert

    def resolve_alert(
        self, alert_id: str, resolution: str, responder_id: str
    ) -> Optional[Alert]:
        alert = self.get_alert(alert_id)
        if alert:
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.utcnow()
            alert.response_history.append(
                {
                    "action": "resolved",
                    "responder": responder_id,
                    "resolution": resolution,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
        return alert

    def mark_false_positive(
        self, alert_id: str, reason: str, responder_id: str
    ) -> Optional[Alert]:
        alert = self.get_alert(alert_id)
        if alert:
            alert.status = AlertStatus.FALSE_POSITIVE
            alert.resolved_at = datetime.utcnow()
            alert.response_history.append(
                {
                    "action": "false_positive",
                    "responder": responder_id,
                    "reason": reason,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
        return alert

    async def check_escalations(self) -> List[Dict]:
        escalated_alerts = []

        for alert in self.alerts:
            if alert.status not in [AlertStatus.SENT, AlertStatus.ESCALATED]:
                continue

            policy = self.escalation_policies.get(alert.severity.value)
            if not policy:
                continue

            timeout = policy.get_timeout_for_level(alert.escalation_level)
            elapsed = datetime.utcnow() - alert.created_at

            if elapsed.total_seconds() > timeout * 60:
                next_level = policy.get_next_level(alert.escalation_level)
                if next_level:
                    escalation_result = await self._escalate_alert(alert, next_level)
                    escalated_alerts.append(escalation_result)

        return escalated_alerts

    async def _escalate_alert(
        self, alert: Alert, level_config: Dict
    ) -> Dict[str, Any]:
        alert.escalation_level = level_config["level"]
        alert.status = AlertStatus.ESCALATED

        responders = []
        for responder_id in level_config["responders"]:
            responder = self.responder_registry.get_responder(responder_id)
            if responder:
                responders.append(responder)

        results = []
        for responder in responders:
            for channel_type in level_config["channels"]:
                if channel_type in self.channels:
                    result = await self.channels[channel_type].send(responder, alert)
                    results.append(result)

        alert.response_history.append(
            {
                "action": "escalated",
                "level": level_config["level"],
                "timestamp": datetime.utcnow().isoformat(),
                "results": results,
            }
        )

        return {
            "alert_id": alert.alert_id,
            "new_level": level_config["level"],
            "notified_responders": [r.responder_id for r in responders],
        }

    def get_alert(self, alert_id: str) -> Optional[Alert]:
        return next((a for a in self.alerts if a.alert_id == alert_id), None)

    def get_alerts_by_status(self, status: AlertStatus) -> List[Alert]:
        return [a for a in self.alerts if a.status == status]

    def get_alerts_by_severity(self, severity: AlertSeverity) -> List[Alert]:
        return [a for a in self.alerts if a.severity == severity]

    def get_open_alerts(self) -> List[Alert]:
        open_statuses = [
            AlertStatus.PENDING,
            AlertStatus.SENT,
            AlertStatus.ACKNOWLEDGED,
            AlertStatus.IN_PROGRESS,
            AlertStatus.ESCALATED,
        ]
        return [a for a in self.alerts if a.status in open_statuses]

    def get_metrics(self) -> Dict[str, Any]:
        total = len(self.alerts)
        if total == 0:
            return {
                "total_alerts": 0,
                "open_alerts": 0,
                "resolved_alerts": 0,
                "average_resolution_time": 0,
                "closure_rate": 0,
            }

        resolved = [a for a in self.alerts if a.status == AlertStatus.RESOLVED]
        resolution_times = []
        for alert in resolved:
            if alert.resolved_at and alert.created_at:
                delta = alert.resolved_at - alert.created_at
                resolution_times.append(delta.total_seconds() / 60)

        avg_resolution = (
            sum(resolution_times) / len(resolution_times) if resolution_times else 0
        )

        return {
            "total_alerts": total,
            "open_alerts": len(self.get_open_alerts()),
            "resolved_alerts": len(resolved),
            "false_positives": len(
                [a for a in self.alerts if a.status == AlertStatus.FALSE_POSITIVE]
            ),
            "average_resolution_time_minutes": round(avg_resolution, 2),
            "closure_rate": len(resolved) / total,
            "by_severity": {
                severity.value: len([a for a in self.alerts if a.severity == severity])
                for severity in AlertSeverity
            },
            "by_status": {
                status.value: len([a for a in self.alerts if a.status == status])
                for status in AlertStatus
            },
        }

    def generate_report(self, period_days: int = 7) -> Dict[str, Any]:
        cutoff = datetime.utcnow() - timedelta(days=period_days)
        period_alerts = [a for a in self.alerts if a.created_at >= cutoff]

        return {
            "period_days": period_days,
            "total_alerts": len(period_alerts),
            "by_severity": {
                severity.value: len(
                    [a for a in period_alerts if a.severity == severity]
                )
                for severity in AlertSeverity
            },
            "by_category": self._count_by_category(period_alerts),
            "resolution_stats": {
                "resolved": len(
                    [a for a in period_alerts if a.status == AlertStatus.RESOLVED]
                ),
                "false_positive": len(
                    [a for a in period_alerts if a.status == AlertStatus.FALSE_POSITIVE]
                ),
                "pending": len(
                    [a for a in period_alerts if a.status in [AlertStatus.PENDING, AlertStatus.SENT]]
                ),
            },
            "escalation_stats": {
                "escalated_count": len(
                    [a for a in period_alerts if a.escalation_level > 1]
                ),
                "max_escalation_level": max(
                    (a.escalation_level for a in period_alerts), default=0
                ),
            },
            "top_sources": self._get_top_sources(period_alerts),
        }

    def _count_by_category(self, alerts: List[Alert]) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for alert in alerts:
            counts[alert.category] = counts.get(alert.category, 0) + 1
        return counts

    def _get_top_sources(self, alerts: List[Alert], limit: int = 5) -> List[Dict]:
        source_counts: Dict[str, int] = {}
        for alert in alerts:
            source_counts[alert.source] = source_counts.get(alert.source, 0) + 1

        sorted_sources = sorted(source_counts.items(), key=lambda x: x[1], reverse=True)
        return [{"source": s, "count": c} for s, c in sorted_sources[:limit]]
