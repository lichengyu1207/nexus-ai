"""
用户行为分析UBA (User Behavior Analytics)
基于历史行为建立基线，检测异常行为
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import asyncio
import logging
import json
from collections import defaultdict
import math

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AnomalyType(Enum):
    UNUSUAL_TIME = "unusual_time"
    UNUSUAL_LOCATION = "unusual_location"
    UNUSUAL_DEVICE = "unusual_device"
    HIGH_FREQUENCY = "high_frequency"
    UNUSUAL_API_ACCESS = "unusual_api_access"
    MULTI_ACCOUNT_PATTERN = "multi_account_pattern"
    DATA_EXFILTRATION = "data_exfiltration"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    BRUTE_FORCE = "brute_force"
    CREDENTIAL_STUFFING = "credential_stuffing"


@dataclass
class BehaviorEvent:
    user_id: str
    event_type: str
    timestamp: datetime
    ip_address: str
    user_agent: str
    device_id: str
    location: Optional[Dict[str, Any]] = None
    resource: Optional[str] = None
    action: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UserBaseline:
    user_id: str
    typical_login_hours: List[int]
    typical_ip_addresses: List[str]
    typical_devices: List[str]
    typical_locations: List[str]
    avg_requests_per_hour: float
    avg_session_duration: float
    typical_api_patterns: Dict[str, int]
    last_updated: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "typical_login_hours": self.typical_login_hours,
            "typical_ip_addresses": self.typical_ip_addresses,
            "typical_devices": self.typical_devices,
            "typical_locations": self.typical_locations,
            "avg_requests_per_hour": self.avg_requests_per_hour,
            "avg_session_duration": self.avg_session_duration,
            "typical_api_patterns": self.typical_api_patterns,
            "last_updated": self.last_updated.isoformat()
        }


@dataclass
class AnomalyAlert:
    alert_id: str
    user_id: str
    anomaly_type: AnomalyType
    risk_level: RiskLevel
    description: str
    evidence: Dict[str, Any]
    timestamp: datetime
    resolved: bool = False
    resolution: Optional[str] = None


class BehaviorCollector:
    def __init__(self):
        self._events: List[BehaviorEvent] = []
        self._events_by_user: Dict[str, List[BehaviorEvent]] = defaultdict(list)
        self._max_events_per_user = 10000
        
    def record_event(self, event: BehaviorEvent):
        self._events.append(event)
        self._events_by_user[event.user_id].append(event)
        
        if len(self._events_by_user[event.user_id]) > self._max_events_per_user:
            self._events_by_user[event.user_id] = \
                self._events_by_user[event.user_id][-self._max_events_per_user:]
            
    def get_user_events(
        self, 
        user_id: str,
        since: Optional[datetime] = None
    ) -> List[BehaviorEvent]:
        events = self._events_by_user.get(user_id, [])
        if since:
            events = [e for e in events if e.timestamp >= since]
        return events
    
    def get_all_events(self, since: Optional[datetime] = None) -> List[BehaviorEvent]:
        events = self._events
        if since:
            events = [e for e in events if e.timestamp >= since]
        return events


class BaselineBuilder:
    def __init__(self):
        self._baselines: Dict[str, UserBaseline] = {}
        self._min_events_for_baseline = 10
        self._baseline_window_days = 30
        
    def build_baseline(self, events: List[BehaviorEvent]) -> Optional[UserBaseline]:
        if len(events) < self._min_events_for_baseline:
            return None
            
        user_id = events[0].user_id
        
        login_hours = defaultdict(int)
        ip_addresses = defaultdict(int)
        devices = defaultdict(int)
        locations = defaultdict(int)
        api_patterns = defaultdict(int)
        
        total_requests = len(events)
        session_durations = []
        
        for event in events:
            login_hours[event.timestamp.hour] += 1
            ip_addresses[event.ip_address] += 1
            devices[event.device_id] += 1
            
            if event.location:
                loc_key = f"{event.location.get('country', '')},{event.location.get('city', '')}"
                locations[loc_key] += 1
                
            if event.resource:
                api_patterns[event.resource] += 1
                
        typical_hours = self._get_top_items(login_hours, 8)
        typical_ips = self._get_top_items(ip_addresses, 3)
        typical_devices = self._get_top_items(devices, 2)
        typical_locations = self._get_top_items(locations, 2)
        
        window_hours = self._baseline_window_days * 24
        avg_requests = total_requests / window_hours if window_hours > 0 else 0
        
        baseline = UserBaseline(
            user_id=user_id,
            typical_login_hours=typical_hours,
            typical_ip_addresses=typical_ips,
            typical_devices=typical_devices,
            typical_locations=typical_locations,
            avg_requests_per_hour=avg_requests,
            avg_session_duration=sum(session_durations) / len(session_durations) if session_durations else 0,
            typical_api_patterns=dict(api_patterns),
            last_updated=datetime.now()
        )
        
        self._baselines[user_id] = baseline
        return baseline
        
    def _get_top_items(self, counter: Dict[str, int], n: int) -> List[str]:
        sorted_items = sorted(counter.items(), key=lambda x: x[1], reverse=True)
        return [item[0] for item in sorted_items[:n]]
        
    def get_baseline(self, user_id: str) -> Optional[UserBaseline]:
        return self._baselines.get(user_id)
        
    def update_baseline(self, user_id: str, events: List[BehaviorEvent]):
        self.build_baseline(events)


class AnomalyDetector:
    def __init__(self, baseline_builder: BaselineBuilder):
        self.baseline_builder = baseline_builder
        self._alerts: List[AnomalyAlert] = []
        self._thresholds = {
            "hour_deviation": 0.1,
            "ip_deviation": 0.05,
            "device_deviation": 0.05,
            "request_rate_multiplier": 5.0,
            "location_deviation": 0.1
        }
        
    def detect_anomalies(
        self, 
        event: BehaviorEvent,
        baseline: Optional[UserBaseline] = None
    ) -> List[AnomalyAlert]:
        alerts = []
        
        if not baseline:
            baseline = self.baseline_builder.get_baseline(event.user_id)
            
        if not baseline:
            return alerts
            
        time_anomaly = self._check_time_anomaly(event, baseline)
        if time_anomaly:
            alerts.append(time_anomaly)
            
        ip_anomaly = self._check_ip_anomaly(event, baseline)
        if ip_anomaly:
            alerts.append(ip_anomaly)
            
        device_anomaly = self._check_device_anomaly(event, baseline)
        if device_anomaly:
            alerts.append(device_anomaly)
            
        location_anomaly = self._check_location_anomaly(event, baseline)
        if location_anomaly:
            alerts.append(location_anomaly)
            
        return alerts
        
    def _check_time_anomaly(
        self, 
        event: BehaviorEvent, 
        baseline: UserBaseline
    ) -> Optional[AnomalyAlert]:
        hour = event.timestamp.hour
        
        if hour not in baseline.typical_login_hours:
            return AnomalyAlert(
                alert_id=f"alert_{event.user_id}_{event.timestamp.timestamp()}",
                user_id=event.user_id,
                anomaly_type=AnomalyType.UNUSUAL_TIME,
                risk_level=RiskLevel.MEDIUM,
                description=f"登录时间异常: {hour}时不在常规登录时段",
                evidence={
                    "current_hour": hour,
                    "typical_hours": baseline.typical_login_hours
                },
                timestamp=event.timestamp
            )
        return None
        
    def _check_ip_anomaly(
        self, 
        event: BehaviorEvent, 
        baseline: UserBaseline
    ) -> Optional[AnomalyAlert]:
        if event.ip_address not in baseline.typical_ip_addresses:
            return AnomalyAlert(
                alert_id=f"alert_{event.user_id}_{event.timestamp.timestamp()}_ip",
                user_id=event.user_id,
                anomaly_type=AnomalyType.UNUSUAL_LOCATION,
                risk_level=RiskLevel.HIGH,
                description=f"IP地址异常: {event.ip_address} 不在常用IP列表",
                evidence={
                    "current_ip": event.ip_address,
                    "typical_ips": baseline.typical_ip_addresses
                },
                timestamp=event.timestamp
            )
        return None
        
    def _check_device_anomaly(
        self, 
        event: BehaviorEvent, 
        baseline: UserBaseline
    ) -> Optional[AnomalyAlert]:
        if event.device_id and event.device_id not in baseline.typical_devices:
            return AnomalyAlert(
                alert_id=f"alert_{event.user_id}_{event.timestamp.timestamp()}_device",
                user_id=event.user_id,
                anomaly_type=AnomalyType.UNUSUAL_DEVICE,
                risk_level=RiskLevel.MEDIUM,
                description=f"设备异常: 新设备访问",
                evidence={
                    "current_device": event.device_id,
                    "typical_devices": baseline.typical_devices
                },
                timestamp=event.timestamp
            )
        return None
        
    def _check_location_anomaly(
        self, 
        event: BehaviorEvent, 
        baseline: UserBaseline
    ) -> Optional[AnomalyAlert]:
        if not event.location:
            return None
            
        loc_key = f"{event.location.get('country', '')},{event.location.get('city', '')}"
        
        if loc_key not in baseline.typical_locations:
            return AnomalyAlert(
                alert_id=f"alert_{event.user_id}_{event.timestamp.timestamp()}_loc",
                user_id=event.user_id,
                anomaly_type=AnomalyType.UNUSUAL_LOCATION,
                risk_level=RiskLevel.HIGH,
                description=f"地理位置异常: {loc_key}",
                evidence={
                    "current_location": loc_key,
                    "typical_locations": baseline.typical_locations
                },
                timestamp=event.timestamp
            )
        return None
        
    def detect_frequency_anomaly(
        self,
        user_id: str,
        events: List[BehaviorEvent],
        window_minutes: int = 60
    ) -> Optional[AnomalyAlert]:
        baseline = self.baseline_builder.get_baseline(user_id)
        if not baseline:
            return None
            
        cutoff = datetime.now() - timedelta(minutes=window_minutes)
        recent_events = [e for e in events if e.timestamp >= cutoff]
        
        requests_in_window = len(recent_events)
        expected_requests = baseline.avg_requests_per_hour * (window_minutes / 60)
        
        if expected_requests > 0 and requests_in_window > expected_requests * self._thresholds["request_rate_multiplier"]:
            return AnomalyAlert(
                alert_id=f"alert_{user_id}_freq_{datetime.now().timestamp()}",
                user_id=user_id,
                anomaly_type=AnomalyType.HIGH_FREQUENCY,
                risk_level=RiskLevel.HIGH,
                description=f"请求频率异常: {requests_in_window}次/{window_minutes}分钟",
                evidence={
                    "actual_requests": requests_in_window,
                    "expected_requests": expected_requests,
                    "multiplier": requests_in_window / expected_requests if expected_requests > 0 else 0
                },
                timestamp=datetime.now()
            )
        return None


class MultiAccountDetector:
    def __init__(self):
        self._ip_to_users: Dict[str, set] = defaultdict(set)
        self._device_to_users: Dict[str, set] = defaultdict(set)
        self._suspicious_clusters: List[Dict[str, Any]] = []
        
    def track_user(self, user_id: str, ip_address: str, device_id: str):
        self._ip_to_users[ip_address].add(user_id)
        if device_id:
            self._device_to_users[device_id].add(user_id)
            
    def detect_multi_account_pattern(self) -> List[Dict[str, Any]]:
        patterns = []
        
        for ip, users in self._ip_to_users.items():
            if len(users) >= 3:
                patterns.append({
                    "type": "ip_shared",
                    "ip": ip,
                    "users": list(users),
                    "risk": RiskLevel.MEDIUM if len(users) < 5 else RiskLevel.HIGH
                })
                
        for device, users in self._device_to_users.items():
            if len(users) >= 2:
                patterns.append({
                    "type": "device_shared",
                    "device": device,
                    "users": list(users),
                    "risk": RiskLevel.HIGH
                })
                
        self._suspicious_clusters = patterns
        return patterns


class DataExfiltrationDetector:
    def __init__(self):
        self._download_threshold_mb = 100
        self._sensitive_apis = [
            "/api/users/export",
            "/api/reports/download",
            "/api/data/bulk",
            "/api/valuations/export"
        ]
        self._user_downloads: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        
    def track_download(
        self, 
        user_id: str, 
        resource: str, 
        size_bytes: int
    ):
        self._user_downloads[user_id].append({
            "resource": resource,
            "size_bytes": size_bytes,
            "timestamp": datetime.now()
        })
        
    def detect_exfiltration(self, user_id: str) -> Optional[AnomalyAlert]:
        downloads = self._user_downloads.get(user_id, [])
        
        cutoff = datetime.now() - timedelta(hours=24)
        recent_downloads = [d for d in downloads if d["timestamp"] >= cutoff]
        
        total_size = sum(d["size_bytes"] for d in recent_downloads)
        total_mb = total_size / (1024 * 1024)
        
        sensitive_access = [
            d for d in recent_downloads 
            if any(api in d["resource"] for api in self._sensitive_apis)
        ]
        
        if total_mb > self._download_threshold_mb or len(sensitive_access) > 10:
            return AnomalyAlert(
                alert_id=f"alert_{user_id}_exfil_{datetime.now().timestamp()}",
                user_id=user_id,
                anomaly_type=AnomalyType.DATA_EXFILTRATION,
                risk_level=RiskLevel.CRITICAL,
                description=f"潜在数据外泄: 下载{total_mb:.2f}MB, 敏感API访问{len(sensitive_access)}次",
                evidence={
                    "total_size_mb": total_mb,
                    "download_count": len(recent_downloads),
                    "sensitive_access_count": len(sensitive_access)
                },
                timestamp=datetime.now()
            )
        return None


class UBASystem:
    def __init__(self):
        self.collector = BehaviorCollector()
        self.baseline_builder = BaselineBuilder()
        self.anomaly_detector = AnomalyDetector(self.baseline_builder)
        self.multi_account_detector = MultiAccountDetector()
        self.exfiltration_detector = DataExfiltrationDetector()
        self._alerts: List[AnomalyAlert] = []
        
    async def process_event(self, event: BehaviorEvent):
        self.collector.record_event(event)
        
        self.multi_account_detector.track_user(
            event.user_id, 
            event.ip_address, 
            event.device_id
        )
        
        alerts = self.anomaly_detector.detect_anomalies(event)
        
        user_events = self.collector.get_user_events(event.user_id)
        freq_alert = self.anomaly_detector.detect_frequency_anomaly(
            event.user_id, user_events
        )
        if freq_alert:
            alerts.append(freq_alert)
            
        for alert in alerts:
            self._alerts.append(alert)
            logger.warning(
                f"UBA Alert: {alert.anomaly_type.value} - {alert.description}"
            )
            
        return alerts
        
    async def build_user_baseline(self, user_id: str):
        events = self.collector.get_user_events(user_id)
        if len(events) >= 10:
            self.baseline_builder.build_baseline(events)
            
    async def run_periodic_analysis(self):
        patterns = self.multi_account_detector.detect_multi_account_pattern()
        for pattern in patterns:
            if pattern["risk"] == RiskLevel.HIGH:
                for user_id in pattern["users"]:
                    alert = AnomalyAlert(
                        alert_id=f"alert_multi_{user_id}_{datetime.now().timestamp()}",
                        user_id=user_id,
                        anomaly_type=AnomalyType.MULTI_ACCOUNT_PATTERN,
                        risk_level=pattern["risk"],
                        description=f"检测到多账号关联模式",
                        evidence=pattern,
                        timestamp=datetime.now()
                    )
                    self._alerts.append(alert)
                    
    def get_user_risk_score(self, user_id: str) -> float:
        user_alerts = [
            a for a in self._alerts 
            if a.user_id == user_id and not a.resolved
        ]
        
        if not user_alerts:
            return 0.0
            
        risk_weights = {
            RiskLevel.LOW: 1,
            RiskLevel.MEDIUM: 3,
            RiskLevel.HIGH: 7,
            RiskLevel.CRITICAL: 15
        }
        
        total_score = sum(risk_weights.get(a.risk_level, 1) for a in user_alerts)
        
        max_score = 100
        return min(total_score, max_score)
        
    def get_high_risk_users(self, threshold: float = 50.0) -> List[Dict[str, Any]]:
        user_ids = set(a.user_id for a in self._alerts)
        
        high_risk = []
        for user_id in user_ids:
            score = self.get_user_risk_score(user_id)
            if score >= threshold:
                high_risk.append({
                    "user_id": user_id,
                    "risk_score": score,
                    "alert_count": len([a for a in self._alerts if a.user_id == user_id])
                })
                
        return sorted(high_risk, key=lambda x: x["risk_score"], reverse=True)
        
    def resolve_alert(self, alert_id: str, resolution: str):
        for alert in self._alerts:
            if alert.alert_id == alert_id:
                alert.resolved = True
                alert.resolution = resolution
                return True
        return False
        
    def get_alerts(
        self, 
        user_id: Optional[str] = None,
        unresolved_only: bool = True
    ) -> List[AnomalyAlert]:
        alerts = self._alerts
        if user_id:
            alerts = [a for a in alerts if a.user_id == user_id]
        if unresolved_only:
            alerts = [a for a in alerts if not a.resolved]
        return alerts


uba_system = UBASystem()


async def analyze_user_behavior(event: BehaviorEvent) -> List[AnomalyAlert]:
    return await uba_system.process_event(event)


def get_uba_system() -> UBASystem:
    return uba_system
