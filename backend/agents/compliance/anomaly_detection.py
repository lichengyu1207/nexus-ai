"""
异常模式检测智能体
从日志和审计数据中发现异常行为
"""
import asyncio
import json
import logging
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class AnomalyType(str, Enum):
    ACCESS_PATTERN = "access_pattern"
    FREQUENCY_ANOMALY = "frequency_anomaly"
    PERMISSION_VIOLATION = "permission_violation"
    DATA_EXFILTRATION = "data_exfiltration"
    BRUTE_FORCE = "brute_force"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    UNUSUAL_TIME = "unusual_time"
    GEO_ANOMALY = "geo_anomaly"
    BEHAVIOR_DEVIATION = "behavior_deviation"


class AnomalySeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AnomalyEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    anomaly_type: AnomalyType
    severity: AnomalySeverity
    description: str
    detected_at: datetime = Field(default_factory=datetime.now)
    source_data: Dict[str, Any] = Field(default_factory=dict)
    indicators: List[str] = Field(default_factory=list)
    affected_entities: List[str] = Field(default_factory=list)
    confidence: float = 0.5
    status: str = "new"
    assigned_to: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolution: Optional[str] = None


class BaselineProfile(BaseModel):
    entity_id: str
    entity_type: str
    metrics: Dict[str, float] = Field(default_factory=dict)
    patterns: Dict[str, Any] = Field(default_factory=dict)
    time_distribution: Dict[int, int] = Field(default_factory=dict)
    last_updated: datetime = Field(default_factory=datetime.now)


class DetectionRule(BaseModel):
    rule_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    anomaly_type: AnomalyType
    condition: str
    threshold: float
    severity: AnomalySeverity
    enabled: bool = True
    false_positive_rate: float = 0.0


class FrequencyAnalyzer:
    def __init__(
        self,
        window_minutes: int = 60,
        threshold_multiplier: float = 3.0
    ):
        self.window_minutes = window_minutes
        self.threshold_multiplier = threshold_multiplier
        
        self.frequency_history: Dict[str, List[datetime]] = defaultdict(list)
        self.baselines: Dict[str, Tuple[float, float]] = {}
    
    def record_event(self, entity_id: str, event_time: Optional[datetime] = None):
        event_time = event_time or datetime.now()
        self.frequency_history[entity_id].append(event_time)
        
        cutoff = event_time - timedelta(minutes=self.window_minutes)
        self.frequency_history[entity_id] = [
            t for t in self.frequency_history[entity_id] if t > cutoff
        ]
    
    def check_anomaly(
        self,
        entity_id: str,
        current_count: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        events = self.frequency_history.get(entity_id, [])
        count = current_count or len(events)
        
        if entity_id not in self.baselines:
            return None
        
        mean, std = self.baselines[entity_id]
        
        if std == 0:
            threshold = mean * self.threshold_multiplier
        else:
            threshold = mean + std * self.threshold_multiplier
        
        if count > threshold:
            return {
                "type": AnomalyType.FREQUENCY_ANOMALY,
                "current_count": count,
                "baseline_mean": mean,
                "baseline_std": std,
                "threshold": threshold,
                "deviation": (count - mean) / std if std > 0 else count - mean
            }
        
        return None
    
    def update_baseline(self, entity_id: str):
        events = self.frequency_history.get(entity_id, [])
        
        if len(events) < 10:
            return
        
        counts = []
        for i in range(24):
            hour_start = datetime.now() - timedelta(hours=i+1)
            hour_end = datetime.now() - timedelta(hours=i)
            count = len([e for e in events if hour_start <= e < hour_end])
            counts.append(count)
        
        if counts:
            mean = sum(counts) / len(counts)
            variance = sum((c - mean) ** 2 for c in counts) / len(counts)
            std = variance ** 0.5
            
            self.baselines[entity_id] = (mean, std)


class PatternAnalyzer:
    SUSPICIOUS_PATTERNS = {
        AnomalyType.BRUTE_FORCE: [
            (r"login.*failed", 10),
            (r"authentication.*failed", 10),
            (r"invalid.*password", 10),
        ],
        AnomalyType.PRIVILEGE_ESCALATION: [
            (r"permission.*denied", 5),
            (r"unauthorized.*access", 3),
            (r"role.*change", 2),
        ],
        AnomalyType.DATA_EXFILTRATION: [
            (r"export.*data", 5),
            (r"download.*large", 3),
            (r"bulk.*query", 5),
        ],
    }
    
    def __init__(self):
        self.pattern_counts: Dict[str, Counter] = defaultdict(Counter)
        self.entity_patterns: Dict[str, Dict[str, List[datetime]]] = defaultdict(lambda: defaultdict(list))
    
    def analyze(
        self,
        entity_id: str,
        event_data: Dict[str, Any],
        time_window: int = 300
    ) -> List[Dict[str, Any]]:
        anomalies = []
        
        event_str = json.dumps(event_data, ensure_ascii=False).lower()
        
        for anomaly_type, patterns in self.SUSPICIOUS_PATTERNS.items():
            for pattern, threshold in patterns:
                import re
                
                if re.search(pattern, event_str, re.IGNORECASE):
                    pattern_key = f"{anomaly_type.value}:{pattern}"
                    
                    self.entity_patterns[entity_id][pattern_key].append(datetime.now())
                    
                    cutoff = datetime.now() - timedelta(seconds=time_window)
                    recent = [
                        t for t in self.entity_patterns[entity_id][pattern_key]
                        if t > cutoff
                    ]
                    self.entity_patterns[entity_id][pattern_key] = recent
                    
                    if len(recent) >= threshold:
                        anomalies.append({
                            "type": anomaly_type,
                            "pattern": pattern,
                            "count": len(recent),
                            "threshold": threshold,
                            "time_window_seconds": time_window
                        })
        
        return anomalies


class TimeAnalyzer:
    NORMAL_HOURS = range(9, 18)
    
    def __init__(self):
        self.user_time_profiles: Dict[str, Dict[int, int]] = defaultdict(lambda: defaultdict(int))
    
    def record_activity(self, user_id: str, activity_time: Optional[datetime] = None):
        activity_time = activity_time or datetime.now()
        hour = activity_time.hour
        
        self.user_time_profiles[user_id][hour] += 1
    
    def check_time_anomaly(
        self,
        user_id: str,
        activity_time: Optional[datetime] = None
    ) -> Optional[Dict[str, Any]]:
        activity_time = activity_time or datetime.now()
        hour = activity_time.hour
        
        profile = self.user_time_profiles.get(user_id)
        
        if not profile or sum(profile.values()) < 10:
            return None
        
        total_activities = sum(profile.values())
        hour_ratio = profile.get(hour, 0) / total_activities
        
        if hour_ratio < 0.01 and hour not in self.NORMAL_HOURS:
            return {
                "type": AnomalyType.UNUSUAL_TIME,
                "hour": hour,
                "hour_ratio": hour_ratio,
                "is_off_hours": True
            }
        
        return None


class BehaviorAnalyzer:
    def __init__(self):
        self.user_behaviors: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "common_actions": Counter(),
            "common_resources": Counter(),
            "session_patterns": [],
        })
    
    def record_behavior(
        self,
        user_id: str,
        action: str,
        resource: str
    ):
        profile = self.user_behaviors[user_id]
        profile["common_actions"][action] += 1
        profile["common_resources"][resource] += 1
    
    def check_deviation(
        self,
        user_id: str,
        action: str,
        resource: str
    ) -> Optional[Dict[str, Any]]:
        profile = self.user_behaviors.get(user_id)
        
        if not profile:
            return None
        
        total_actions = sum(profile["common_actions"].values())
        
        if total_actions < 10:
            return None
        
        action_ratio = profile["common_actions"].get(action, 0) / total_actions
        
        if action_ratio < 0.01:
            return {
                "type": AnomalyType.BEHAVIOR_DEVIATION,
                "action": action,
                "action_ratio": action_ratio,
                "resource": resource
            }
        
        return None


class AnomalyDetectionAgent:
    def __init__(
        self,
        agent_id: str,
        name: str = "AnomalyDetection",
        alert_dispatcher: Optional[Any] = None
    ):
        self.agent_id = agent_id
        self.name = name
        self.alert_dispatcher = alert_dispatcher
        
        self.frequency_analyzer = FrequencyAnalyzer()
        self.pattern_analyzer = PatternAnalyzer()
        self.time_analyzer = TimeAnalyzer()
        self.behavior_analyzer = BehaviorAnalyzer()
        
        self.detected_anomalies: List[AnomalyEvent] = []
        self.detection_rules: Dict[str, DetectionRule] = {}
        
        self._init_default_rules()
        
        self._running = False
        
        self.logger = logging.getLogger(f"{__name__}.{agent_id}")
    
    def _init_default_rules(self):
        default_rules = [
            DetectionRule(
                name="高频访问检测",
                anomaly_type=AnomalyType.FREQUENCY_ANOMALY,
                condition="requests_per_minute > baseline * 3",
                threshold=3.0,
                severity=AnomalySeverity.MEDIUM
            ),
            DetectionRule(
                name="暴力破解检测",
                anomaly_type=AnomalyType.BRUTE_FORCE,
                condition="failed_logins > 10 in 5 minutes",
                threshold=10.0,
                severity=AnomalySeverity.HIGH
            ),
            DetectionRule(
                name="权限提升检测",
                anomaly_type=AnomalyType.PRIVILEGE_ESCALATION,
                condition="permission_denied > 5 in 10 minutes",
                threshold=5.0,
                severity=AnomalySeverity.HIGH
            ),
            DetectionRule(
                name="数据外泄检测",
                anomaly_type=AnomalyType.DATA_EXFILTRATION,
                condition="bulk_export > 3 in 1 hour",
                threshold=3.0,
                severity=AnomalySeverity.CRITICAL
            ),
        ]
        
        for rule in default_rules:
            self.detection_rules[rule.rule_id] = rule
    
    async def initialize(self):
        self.logger.info(f"AnomalyDetectionAgent {self.agent_id} initialized")
    
    async def analyze_event(
        self,
        event_data: Dict[str, Any],
        entity_id: str,
        event_type: Optional[str] = None
    ) -> List[AnomalyEvent]:
        anomalies = []
        
        self.frequency_analyzer.record_event(entity_id)
        freq_anomaly = self.frequency_analyzer.check_anomaly(entity_id)
        
        if freq_anomaly:
            anomaly = AnomalyEvent(
                anomaly_type=AnomalyType.FREQUENCY_ANOMALY,
                severity=AnomalySeverity.MEDIUM,
                description=f"检测到异常频率: 当前{freq_anomaly['current_count']}次, 基线{freq_anomaly['baseline_mean']:.1f}次",
                source_data=event_data,
                indicators=[f"频率偏离: {freq_anomaly['deviation']:.2f}"],
                affected_entities=[entity_id],
                confidence=min(1.0, freq_anomaly['deviation'] / 5)
            )
            anomalies.append(anomaly)
        
        pattern_anomalies = self.pattern_analyzer.analyze(entity_id, event_data)
        for pa in pattern_anomalies:
            severity = AnomalySeverity.HIGH if pa["count"] >= pa["threshold"] * 2 else AnomalySeverity.MEDIUM
            
            anomaly = AnomalyEvent(
                anomaly_type=AnomalyType(pa["type"]),
                severity=severity,
                description=f"检测到可疑模式: {pa['pattern']}",
                source_data=event_data,
                indicators=[f"模式匹配次数: {pa['count']}"],
                affected_entities=[entity_id],
                confidence=min(1.0, pa["count"] / pa["threshold"] / 2)
            )
            anomalies.append(anomaly)
        
        time_anomaly = self.time_analyzer.check_time_anomaly(entity_id)
        if time_anomaly:
            anomaly = AnomalyEvent(
                anomaly_type=AnomalyType.UNUSUAL_TIME,
                severity=AnomalySeverity.LOW,
                description=f"检测到非正常时间活动: {time_anomaly['hour']}点",
                source_data=event_data,
                indicators=[f"活动时间: {time_anomaly['hour']}:00"],
                affected_entities=[entity_id],
                confidence=0.6
            )
            anomalies.append(anomaly)
        
        if event_type:
            resource = event_data.get("resource", "unknown")
            behavior_anomaly = self.behavior_analyzer.check_deviation(
                entity_id, event_type, resource
            )
            
            if behavior_anomaly:
                anomaly = AnomalyEvent(
                    anomaly_type=AnomalyType.BEHAVIOR_DEVIATION,
                    severity=AnomalySeverity.LOW,
                    description=f"检测到异常行为: {behavior_anomaly['action']}",
                    source_data=event_data,
                    indicators=[f"行为比例: {behavior_anomaly['action_ratio']:.4f}"],
                    affected_entities=[entity_id],
                    confidence=0.5
                )
                anomalies.append(anomaly)
        
        for anomaly in anomalies:
            self.detected_anomalies.append(anomaly)
            
            if self.alert_dispatcher and anomaly.severity in [AnomalySeverity.HIGH, AnomalySeverity.CRITICAL]:
                await self.alert_dispatcher.dispatch({
                    "type": "anomaly_detected",
                    "anomaly": anomaly.dict()
                })
        
        return anomalies
    
    async def batch_analyze(
        self,
        events: List[Dict[str, Any]]
    ) -> List[AnomalyEvent]:
        all_anomalies = []
        
        for event in events:
            entity_id = event.get("user_id") or event.get("agent_id") or "unknown"
            event_type = event.get("type") or event.get("action")
            
            anomalies = await self.analyze_event(event, entity_id, event_type)
            all_anomalies.extend(anomalies)
        
        return all_anomalies
    
    async def get_anomalies(
        self,
        severity: Optional[AnomalySeverity] = None,
        anomaly_type: Optional[AnomalyType] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[AnomalyEvent]:
        results = []
        
        for anomaly in reversed(self.detected_anomalies):
            if severity and anomaly.severity != severity:
                continue
            if anomaly_type and anomaly.anomaly_type != anomaly_type:
                continue
            if status and anomaly.status != status:
                continue
            
            results.append(anomaly)
            
            if len(results) >= limit:
                break
        
        return results
    
    async def resolve_anomaly(
        self,
        event_id: str,
        resolution: str
    ) -> bool:
        for anomaly in self.detected_anomalies:
            if anomaly.event_id == event_id:
                anomaly.status = "resolved"
                anomaly.resolution = resolution
                anomaly.resolved_at = datetime.now()
                return True
        
        return False
    
    async def update_baselines(self):
        for entity_id in self.frequency_analyzer.frequency_history:
            self.frequency_analyzer.update_baseline(entity_id)
        
        self.logger.info("Baselines updated")
    
    async def get_statistics(self) -> Dict[str, Any]:
        by_type = Counter(a.anomaly_type.value for a in self.detected_anomalies)
        by_severity = Counter(a.severity.value for a in self.detected_anomalies)
        by_status = Counter(a.status for a in self.detected_anomalies)
        
        unresolved = len([a for a in self.detected_anomalies if a.status == "new"])
        critical_unresolved = len([
            a for a in self.detected_anomalies
            if a.status == "new" and a.severity == AnomalySeverity.CRITICAL
        ])
        
        return {
            "total_anomalies": len(self.detected_anomalies),
            "unresolved": unresolved,
            "critical_unresolved": critical_unresolved,
            "by_type": dict(by_type),
            "by_severity": dict(by_severity),
            "by_status": dict(by_status),
            "rules_count": len(self.detection_rules)
        }
    
    async def start_monitoring(self):
        self._running = True
        asyncio.create_task(self._monitoring_loop())
    
    async def stop_monitoring(self):
        self._running = False
    
    async def _monitoring_loop(self):
        while self._running:
            try:
                await self.update_baselines()
                await asyncio.sleep(3600)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)
