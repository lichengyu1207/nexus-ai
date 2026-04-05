"""
假冒检测智能体
Impersonation Detector Agent

负责检测用户身份被冒用的情况。
"""

import asyncio
import json
import logging
import uuid
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
from enum import Enum

logger = logging.getLogger(__name__)


class ImpersonationType(Enum):
    ACCOUNT_TAKEOVER = "account_takeover"
    SYNTHETIC_IDENTITY = "synthetic_identity"
    CREDENTIAL_STUFFING = "credential_stuffing"
    PHISHING_VICTIM = "phishing_victim"
    SOCIAL_ENGINEERING = "social_engineering"


class DetectionConfidence(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ImpersonationIndicator:
    indicator_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    indicator_type: str = ""
    description: str = ""
    severity: str = "medium"
    evidence: Dict = field(default_factory=dict)
    detected_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class ImpersonationAlert:
    alert_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    impersonation_type: str = ""
    
    confidence: str = DetectionConfidence.MEDIUM.value
    indicators: List[ImpersonationIndicator] = field(default_factory=list)
    
    risk_score: float = 0.0
    recommended_actions: List[str] = field(default_factory=list)
    
    status: str = "open"
    handled_at: str = ""
    handled_by: str = ""
    
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class ImpersonationDetectorAgent:
    """
    假冒检测智能体
    
    功能：
    1. 登录异常：异地登录、异常时间、新设备
    2. 行为异常：操作模式突变、访问敏感数据
    3. 通信异常：联系信息变更、异常沟通请求
    4. 账户异常：密码重置、权限变更
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.name = "ImpersonationDetectorAgent"
        self.description = "检测用户身份被冒用的情况"
        self.config = config or {}
        
        self.alerts: Dict[str, ImpersonationAlert] = {}
        self.user_baselines: Dict[str, Dict] = {}
        self.user_alerts: Dict[str, List[str]] = defaultdict(list)
        
        self.detection_rules = self._init_detection_rules()
        
        self.stats = {
            "total_detections": 0,
            "alerts_by_type": defaultdict(int),
            "alerts_by_confidence": defaultdict(int),
            "true_positives": 0,
            "false_positives": 0,
        }
        
        self._initialized = False
    
    def _init_detection_rules(self) -> List[Dict]:
        return [
            {
                "rule_id": "RULE-001",
                "name": "异地登录",
                "type": ImpersonationType.ACCOUNT_TAKEOVER.value,
                "condition": "login_location_change",
                "threshold": 500,
                "severity": "high",
            },
            {
                "rule_id": "RULE-002",
                "name": "异常时间登录",
                "type": ImpersonationType.ACCOUNT_TAKEOVER.value,
                "condition": "login_time_anomaly",
                "threshold": 3,
                "severity": "medium",
            },
            {
                "rule_id": "RULE-003",
                "name": "新设备登录",
                "type": ImpersonationType.ACCOUNT_TAKEOVER.value,
                "condition": "new_device",
                "threshold": 1,
                "severity": "medium",
            },
            {
                "rule_id": "RULE-004",
                "name": "行为模式突变",
                "type": ImpersonationType.SOCIAL_ENGINEERING.value,
                "condition": "behavior_change",
                "threshold": 0.5,
                "severity": "high",
            },
            {
                "rule_id": "RULE-005",
                "name": "敏感数据访问",
                "type": ImpersonationType.ACCOUNT_TAKEOVER.value,
                "condition": "sensitive_access",
                "threshold": 1,
                "severity": "high",
            },
            {
                "rule_id": "RULE-006",
                "name": "联系信息变更",
                "type": ImpersonationType.ACCOUNT_TAKEOVER.value,
                "condition": "contact_change",
                "threshold": 1,
                "severity": "high",
            },
            {
                "rule_id": "RULE-007",
                "name": "密码重置请求",
                "type": ImpersonationType.CREDENTIAL_STUFFING.value,
                "condition": "password_reset",
                "threshold": 2,
                "severity": "medium",
            },
            {
                "rule_id": "RULE-008",
                "name": "多次认证失败",
                "type": ImpersonationType.CREDENTIAL_STUFFING.value,
                "condition": "auth_failures",
                "threshold": 3,
                "severity": "high",
            },
        ]
    
    async def initialize(self):
        if not self._initialized:
            await self._setup()
            self._initialized = True
            logger.info(f"Agent '{self.name}' initialized")
    
    async def _setup(self):
        pass
    
    async def update_baseline(
        self,
        user_id: str,
        baseline_data: Dict,
    ) -> bool:
        if user_id not in self.user_baselines:
            self.user_baselines[user_id] = {
                "login_locations": [],
                "login_times": [],
                "devices": [],
                "behavior_patterns": {},
                "created_at": datetime.utcnow().isoformat(),
            }
        
        baseline = self.user_baselines[user_id]
        
        if "login_location" in baseline_data:
            baseline["login_locations"].append(baseline_data["login_location"])
            baseline["login_locations"] = baseline["login_locations"][-20:]
        
        if "login_time" in baseline_data:
            baseline["login_times"].append(baseline_data["login_time"])
            baseline["login_times"] = baseline["login_times"][-50:]
        
        if "device" in baseline_data:
            if baseline_data["device"] not in baseline["devices"]:
                baseline["devices"].append(baseline_data["device"])
        
        if "behavior_pattern" in baseline_data:
            baseline["behavior_patterns"].update(baseline_data["behavior_pattern"])
        
        baseline["updated_at"] = datetime.utcnow().isoformat()
        
        return True
    
    async def detect(
        self,
        user_id: str,
        event_data: Dict,
    ) -> Optional[ImpersonationAlert]:
        self.stats["total_detections"] += 1
        
        indicators = []
        baseline = self.user_baselines.get(user_id, {})
        
        location_indicators = self._check_location_anomaly(user_id, event_data, baseline)
        indicators.extend(location_indicators)
        
        time_indicators = self._check_time_anomaly(user_id, event_data, baseline)
        indicators.extend(time_indicators)
        
        device_indicators = self._check_device_anomaly(user_id, event_data, baseline)
        indicators.extend(device_indicators)
        
        behavior_indicators = self._check_behavior_anomaly(user_id, event_data, baseline)
        indicators.extend(behavior_indicators)
        
        if not indicators:
            return None
        
        impersonation_type = self._determine_impersonation_type(indicators)
        confidence = self._calculate_confidence(indicators)
        risk_score = self._calculate_risk_score(indicators)
        
        alert = ImpersonationAlert(
            user_id=user_id,
            impersonation_type=impersonation_type,
            confidence=confidence,
            indicators=indicators,
            risk_score=risk_score,
            recommended_actions=self._generate_recommendations(indicators, risk_score),
        )
        
        self.alerts[alert.alert_id] = alert
        self.user_alerts[user_id].append(alert.alert_id)
        
        self.stats["alerts_by_type"][impersonation_type] += 1
        self.stats["alerts_by_confidence"][confidence] += 1
        
        return alert
    
    def _check_location_anomaly(
        self,
        user_id: str,
        event_data: Dict,
        baseline: Dict,
    ) -> List[ImpersonationIndicator]:
        indicators = []
        
        current_location = event_data.get("location", "")
        known_locations = baseline.get("login_locations", [])
        
        if current_location and known_locations:
            if current_location not in known_locations:
                indicators.append(ImpersonationIndicator(
                    indicator_type="location_anomaly",
                    description=f"新登录地点: {current_location}",
                    severity="high",
                    evidence={
                        "current_location": current_location,
                        "known_locations": known_locations[-5:],
                    },
                ))
        
        return indicators
    
    def _check_time_anomaly(
        self,
        user_id: str,
        event_data: Dict,
        baseline: Dict,
    ) -> List[ImpersonationIndicator]:
        indicators = []
        
        current_hour = datetime.utcnow().hour
        login_times = baseline.get("login_times", [])
        
        if login_times:
            usual_hours = [datetime.fromisoformat(t).hour for t in login_times if t]
            
            if usual_hours:
                avg_hour = sum(usual_hours) / len(usual_hours)
                
                if abs(current_hour - avg_hour) > 6:
                    indicators.append(ImpersonationIndicator(
                        indicator_type="time_anomaly",
                        description=f"异常登录时间: {current_hour}时",
                        severity="medium",
                        evidence={
                            "current_hour": current_hour,
                            "usual_hours": usual_hours[-10:],
                        },
                    ))
        
        return indicators
    
    def _check_device_anomaly(
        self,
        user_id: str,
        event_data: Dict,
        baseline: Dict,
    ) -> List[ImpersonationIndicator]:
        indicators = []
        
        current_device = event_data.get("device_fingerprint", "")
        known_devices = baseline.get("devices", [])
        
        if current_device and current_device not in known_devices:
            indicators.append(ImpersonationIndicator(
                indicator_type="device_anomaly",
                description="使用新设备登录",
                severity="medium",
                evidence={
                    "current_device": current_device[:16] + "...",
                    "known_devices_count": len(known_devices),
                },
            ))
        
        return indicators
    
    def _check_behavior_anomaly(
        self,
        user_id: str,
        event_data: Dict,
        baseline: Dict,
    ) -> List[ImpersonationIndicator]:
        indicators = []
        
        sensitive_access = event_data.get("sensitive_data_access", False)
        if sensitive_access:
            indicators.append(ImpersonationIndicator(
                indicator_type="sensitive_access",
                description="访问敏感数据",
                severity="high",
                evidence={"access_type": event_data.get("access_type", "unknown")},
            ))
        
        contact_change = event_data.get("contact_info_change", False)
        if contact_change:
            indicators.append(ImpersonationIndicator(
                indicator_type="contact_change",
                description="联系信息变更",
                severity="high",
                evidence={"change_type": event_data.get("change_type", "unknown")},
            ))
        
        auth_failures = event_data.get("recent_auth_failures", 0)
        if auth_failures >= 3:
            indicators.append(ImpersonationIndicator(
                indicator_type="auth_failures",
                description=f"近期认证失败{auth_failures}次",
                severity="high",
                evidence={"failure_count": auth_failures},
            ))
        
        return indicators
    
    def _determine_impersonation_type(
        self,
        indicators: List[ImpersonationIndicator],
    ) -> str:
        indicator_types = [i.indicator_type for i in indicators]
        
        if "auth_failures" in indicator_types:
            return ImpersonationType.CREDENTIAL_STUFFING.value
        
        if "contact_change" in indicator_types:
            return ImpersonationType.ACCOUNT_TAKEOVER.value
        
        if "sensitive_access" in indicator_types:
            return ImpersonationType.ACCOUNT_TAKEOVER.value
        
        if "location_anomaly" in indicator_types or "device_anomaly" in indicator_types:
            return ImpersonationType.ACCOUNT_TAKEOVER.value
        
        return ImpersonationType.SOCIAL_ENGINEERING.value
    
    def _calculate_confidence(
        self,
        indicators: List[ImpersonationIndicator],
    ) -> str:
        high_severity_count = sum(1 for i in indicators if i.severity == "high")
        
        if high_severity_count >= 2 or len(indicators) >= 3:
            return DetectionConfidence.HIGH.value
        elif high_severity_count >= 1 or len(indicators) >= 2:
            return DetectionConfidence.MEDIUM.value
        else:
            return DetectionConfidence.LOW.value
    
    def _calculate_risk_score(
        self,
        indicators: List[ImpersonationIndicator],
    ) -> float:
        score = 0.0
        
        for indicator in indicators:
            if indicator.severity == "high":
                score += 30
            elif indicator.severity == "medium":
                score += 15
            else:
                score += 5
        
        return min(100, score)
    
    def _generate_recommendations(
        self,
        indicators: List[ImpersonationIndicator],
        risk_score: float,
    ) -> List[str]:
        recommendations = []
        
        if risk_score >= 70:
            recommendations.append("立即锁定账户")
            recommendations.append("通知用户验证身份")
        elif risk_score >= 40:
            recommendations.append("要求多因素认证")
            recommendations.append("发送安全提醒")
        else:
            recommendations.append("加强监控")
            recommendations.append("记录观察")
        
        indicator_types = [i.indicator_type for i in indicators]
        
        if "location_anomaly" in indicator_types:
            recommendations.append("验证用户当前位置")
        
        if "device_anomaly" in indicator_types:
            recommendations.append("验证设备所有权")
        
        if "contact_change" in indicator_types:
            recommendations.append("验证联系信息变更")
        
        return recommendations
    
    async def get_alert(self, alert_id: str) -> Optional[Dict]:
        alert = self.alerts.get(alert_id)
        if not alert:
            return None
        
        return {
            "alert_id": alert.alert_id,
            "user_id": alert.user_id,
            "impersonation_type": alert.impersonation_type,
            "confidence": alert.confidence,
            "risk_score": alert.risk_score,
            "indicators": [
                {
                    "type": i.indicator_type,
                    "description": i.description,
                    "severity": i.severity,
                }
                for i in alert.indicators
            ],
            "recommended_actions": alert.recommended_actions,
            "status": alert.status,
            "created_at": alert.created_at,
        }
    
    async def handle_alert(
        self,
        alert_id: str,
        action: str,
        handler: str,
    ) -> bool:
        alert = self.alerts.get(alert_id)
        if not alert:
            return False
        
        alert.status = "handled"
        alert.handled_at = datetime.utcnow().isoformat()
        alert.handled_by = handler
        
        if action == "confirmed":
            self.stats["true_positives"] += 1
        elif action == "false_positive":
            self.stats["false_positives"] += 1
        
        return True
    
    async def get_user_alerts(
        self,
        user_id: str,
        status: Optional[str] = None,
    ) -> List[Dict]:
        alert_ids = self.user_alerts.get(user_id, [])
        
        alerts = []
        for alert_id in alert_ids:
            alert = await self.get_alert(alert_id)
            if alert:
                if status is None or alert["status"] == status:
                    alerts.append(alert)
        
        return alerts
    
    async def get_stats(self) -> Dict:
        return {
            "name": self.name,
            "total_detections": self.stats["total_detections"],
            "alerts_by_type": dict(self.stats["alerts_by_type"]),
            "alerts_by_confidence": dict(self.stats["alerts_by_confidence"]),
            "true_positives": self.stats["true_positives"],
            "false_positives": self.stats["false_positives"],
        }
