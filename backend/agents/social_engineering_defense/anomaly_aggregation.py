"""
异常行为聚合智能体
负责聚合来自各检测智能体的异常事件，进行关联分析
"""
import asyncio
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class AnomalySource(Enum):
    """异常来源"""
    PROMPT_INJECTION = "prompt_injection"
    IDENTITY_VERIFICATION = "identity_verification"
    EMOTION_RECOGNITION = "emotion_recognition"
    MULTI_TURN_INDUCtion = "multi_turn_induction"
    BEHAVIOR_BASELINE = "behavior_baseline"
    CONTEXT_POLLUTION = "context_pollution"
    CONVERSATION_PATTERN = "conversation_pattern"


class AggregationLevel(Enum):
    """聚合等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AttackIndicator(Enum):
    """攻击指标"""
    COORDINATED_ATTACK = "coordinated_attack"
    REPEATED_ATTEMPTS = "repeated_attempts"
    ESCALATING_SEVERITY = "escalating_severity"
    MULTI_VECTOR_ATTACK = "multi_vector_attack"
    TARGETED_ATTACK = "targeted_attack"
    NONE = "none"


@dataclass
class AnomalyEvent:
    """异常事件"""
    event_id: str
    source: AnomalySource
    severity: str
    confidence: float
    timestamp: datetime
    user_id: str
    session_id: str
    description: str
    raw_data: Dict[str, Any]
    tags: List[str] = field(default_factory=list)


@dataclass
class CorrelationResult:
    """关联结果"""
    correlated_events: List[str]
    correlation_type: str
    correlation_strength: float
    time_span: float
    common_factors: List[str]


@dataclass
class AggregationResult:
    """聚合结果"""
    aggregation_id: str
    level: AggregationLevel
    total_events: int
    unique_sources: Set[AnomalySource]
    correlated_groups: List[CorrelationResult]
    overall_risk_score: float
    attack_indicator: AttackIndicator
    affected_users: Set[str]
    affected_sessions: Set[str]
    recommendations: List[str]
    created_at: datetime


class AnomalyAggregationAgent:
    """异常行为聚合智能体"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.name = "AnomalyAggregationAgent"
        self.config = config or {}
        self.event_buffer: Dict[str, List[AnomalyEvent]] = defaultdict(list)
        self.aggregation_rules = self._init_aggregation_rules()
        self.correlation_thresholds = self._init_correlation_thresholds()
        self.recent_aggregations: List[AggregationResult] = []
        self.stats = {
            "total_events_received": 0,
            "total_aggregations": 0,
            "correlations_found": 0,
            "attacks_detected": 0,
            "critical_alerts": 0,
            "false_positives": 0,
        }
    
    def _init_aggregation_rules(self) -> List[Dict]:
        """初始化聚合规则"""
        return [
            {
                "name": "multi_source_attack",
                "description": "多源攻击检测",
                "condition": {
                    "min_sources": 3,
                    "time_window": 3600,
                    "min_severity": "medium"
                },
                "result_level": AggregationLevel.HIGH,
                "attack_indicator": AttackIndicator.MULTI_VECTOR_ATTACK
            },
            {
                "name": "repeated_attempts",
                "description": "重复攻击尝试",
                "condition": {
                    "min_same_source": 5,
                    "time_window": 1800,
                    "same_user": True
                },
                "result_level": AggregationLevel.HIGH,
                "attack_indicator": AttackIndicator.REPEATED_ATTEMPTS
            },
            {
                "name": "escalating_attack",
                "description": "升级攻击",
                "condition": {
                    "severity_escalation": True,
                    "time_window": 7200
                },
                "result_level": AggregationLevel.CRITICAL,
                "attack_indicator": AttackIndicator.ESCALATING_SEVERITY
            },
            {
                "name": "coordinated_attack",
                "description": "协同攻击",
                "condition": {
                    "multiple_users": True,
                    "similar_patterns": True,
                    "time_window": 1800
                },
                "result_level": AggregationLevel.CRITICAL,
                "attack_indicator": AttackIndicator.COORDINATED_ATTACK
            },
            {
                "name": "session_compromise",
                "description": "会话入侵",
                "condition": {
                    "sources": ["identity_verification", "behavior_baseline"],
                    "time_window": 600,
                    "same_session": True
                },
                "result_level": AggregationLevel.HIGH,
                "attack_indicator": AttackIndicator.TARGETED_ATTACK
            }
        ]
    
    def _init_correlation_thresholds(self) -> Dict:
        """初始化关联阈值"""
        return {
            "time_correlation": 300,
            "user_correlation": 0.8,
            "pattern_similarity": 0.7,
            "session_correlation": 0.9,
        }
    
    async def initialize(self) -> bool:
        """初始化智能体"""
        await asyncio.sleep(0.1)
        return True
    
    def receive_event(
        self,
        source: AnomalySource,
        severity: str,
        confidence: float,
        user_id: str,
        session_id: str,
        description: str,
        raw_data: Dict[str, Any],
        tags: List[str] = None
    ) -> str:
        """接收异常事件"""
        event_id = f"{source.value}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(self.event_buffer[user_id])}"
        
        event = AnomalyEvent(
            event_id=event_id,
            source=source,
            severity=severity,
            confidence=confidence,
            timestamp=datetime.now(),
            user_id=user_id,
            session_id=session_id,
            description=description,
            raw_data=raw_data,
            tags=tags or []
        )
        
        self.event_buffer[user_id].append(event)
        self.stats["total_events_received"] += 1
        
        self._cleanup_old_events()
        
        return event_id
    
    def _cleanup_old_events(self):
        """清理旧事件"""
        cutoff = datetime.now() - timedelta(hours=24)
        
        for user_id in list(self.event_buffer.keys()):
            self.event_buffer[user_id] = [
                e for e in self.event_buffer[user_id]
                if e.timestamp > cutoff
            ]
            
            if not self.event_buffer[user_id]:
                del self.event_buffer[user_id]
    
    def aggregate_anomalies(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        time_window: int = 3600
    ) -> AggregationResult:
        """聚合异常"""
        events = self._get_relevant_events(user_id, session_id, time_window)
        
        if not events:
            return self._create_empty_result()
        
        correlated_groups = self._find_correlations(events, time_window)
        
        level = self._determine_aggregation_level(events, correlated_groups)
        
        attack_indicator = self._detect_attack_pattern(events, correlated_groups)
        
        risk_score = self._calculate_risk_score(events, correlated_groups, attack_indicator)
        
        affected_users = {e.user_id for e in events}
        affected_sessions = {e.session_id for e in events}
        
        recommendations = self._generate_recommendations(level, attack_indicator, events)
        
        result = AggregationResult(
            aggregation_id=f"agg_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            level=level,
            total_events=len(events),
            unique_sources={e.source for e in events},
            correlated_groups=correlated_groups,
            overall_risk_score=risk_score,
            attack_indicator=attack_indicator,
            affected_users=affected_users,
            affected_sessions=affected_sessions,
            recommendations=recommendations,
            created_at=datetime.now()
        )
        
        self.recent_aggregations.append(result)
        self.stats["total_aggregations"] += 1
        
        if correlated_groups:
            self.stats["correlations_found"] += len(correlated_groups)
        
        if attack_indicator != AttackIndicator.NONE:
            self.stats["attacks_detected"] += 1
        
        if level == AggregationLevel.CRITICAL:
            self.stats["critical_alerts"] += 1
        
        return result
    
    def _get_relevant_events(
        self,
        user_id: Optional[str],
        session_id: Optional[str],
        time_window: int
    ) -> List[AnomalyEvent]:
        """获取相关事件"""
        cutoff = datetime.now() - timedelta(seconds=time_window)
        events = []
        
        if user_id:
            events = [e for e in self.event_buffer.get(user_id, []) if e.timestamp > cutoff]
        else:
            for user_events in self.event_buffer.values():
                events.extend([e for e in user_events if e.timestamp > cutoff])
        
        if session_id:
            events = [e for e in events if e.session_id == session_id]
        
        return sorted(events, key=lambda x: x.timestamp)
    
    def _find_correlations(
        self,
        events: List[AnomalyEvent],
        time_window: int
    ) -> List[CorrelationResult]:
        """发现关联"""
        correlations = []
        
        time_correlations = self._find_time_correlations(events)
        correlations.extend(time_correlations)
        
        user_correlations = self._find_user_correlations(events)
        correlations.extend(user_correlations)
        
        pattern_correlations = self._find_pattern_correlations(events)
        correlations.extend(pattern_correlations)
        
        session_correlations = self._find_session_correlations(events)
        correlations.extend(session_correlations)
        
        return correlations
    
    def _find_time_correlations(
        self, 
        events: List[AnomalyEvent]
    ) -> List[CorrelationResult]:
        """发现时间关联"""
        correlations = []
        threshold = self.correlation_thresholds["time_correlation"]
        
        time_groups: Dict[int, List[AnomalyEvent]] = defaultdict(list)
        for event in events:
            time_bucket = int(event.timestamp.timestamp() // threshold)
            time_groups[time_bucket].append(event)
        
        for bucket, group in time_groups.items():
            if len(group) >= 2:
                correlations.append(CorrelationResult(
                    correlated_events=[e.event_id for e in group],
                    correlation_type="time_proximity",
                    correlation_strength=len(group) / 10,
                    time_span=threshold,
                    common_factors=[f"time_bucket_{bucket}"]
                ))
        
        return correlations
    
    def _find_user_correlations(
        self, 
        events: List[AnomalyEvent]
    ) -> List[CorrelationResult]:
        """发现用户关联"""
        correlations = []
        threshold = self.correlation_thresholds["user_correlation"]
        
        user_events: Dict[str, List[AnomalyEvent]] = defaultdict(list)
        for event in events:
            user_events[event.user_id].append(event)
        
        for user_id, user_event_list in user_events.items():
            if len(user_event_list) >= 3:
                sources = {e.source for e in user_event_list}
                if len(sources) >= 2:
                    correlations.append(CorrelationResult(
                        correlated_events=[e.event_id for e in user_event_list],
                        correlation_type="user_multi_source",
                        correlation_strength=len(sources) / 5,
                        time_span=0,
                        common_factors=[f"user_{user_id}", f"sources_{len(sources)}"]
                    ))
        
        return correlations
    
    def _find_pattern_correlations(
        self, 
        events: List[AnomalyEvent]
    ) -> List[CorrelationResult]:
        """发现模式关联"""
        correlations = []
        
        severity_groups: Dict[str, List[AnomalyEvent]] = defaultdict(list)
        for event in events:
            severity_groups[event.severity].append(event)
        
        for severity, group in severity_groups.items():
            if severity in ["high", "critical"] and len(group) >= 2:
                correlations.append(CorrelationResult(
                    correlated_events=[e.event_id for e in group],
                    correlation_type="severity_pattern",
                    correlation_strength=0.8 if severity == "critical" else 0.6,
                    time_span=0,
                    common_factors=[f"severity_{severity}"]
                ))
        
        return correlations
    
    def _find_session_correlations(
        self, 
        events: List[AnomalyEvent]
    ) -> List[CorrelationResult]:
        """发现会话关联"""
        correlations = []
        
        session_events: Dict[str, List[AnomalyEvent]] = defaultdict(list)
        for event in events:
            session_events[event.session_id].append(event)
        
        for session_id, session_event_list in session_events.items():
            if len(session_event_list) >= 3:
                correlations.append(CorrelationResult(
                    correlated_events=[e.event_id for e in session_event_list],
                    correlation_type="session_concentration",
                    correlation_strength=len(session_event_list) / 5,
                    time_span=0,
                    common_factors=[f"session_{session_id}"]
                ))
        
        return correlations
    
    def _determine_aggregation_level(
        self,
        events: List[AnomalyEvent],
        correlations: List[CorrelationResult]
    ) -> AggregationLevel:
        """确定聚合等级"""
        severity_weights = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        
        max_severity = max(events, key=lambda x: severity_weights.get(x.severity, 0))
        
        if max_severity.severity == "critical":
            base_level = AggregationLevel.CRITICAL
        elif max_severity.severity == "high":
            base_level = AggregationLevel.HIGH
        elif max_severity.severity == "medium":
            base_level = AggregationLevel.MEDIUM
        else:
            base_level = AggregationLevel.LOW
        
        if len(correlations) >= 3:
            if base_level == AggregationLevel.MEDIUM:
                base_level = AggregationLevel.HIGH
            elif base_level == AggregationLevel.HIGH:
                base_level = AggregationLevel.CRITICAL
        
        if len(events) >= 10:
            if base_level == AggregationLevel.LOW:
                base_level = AggregationLevel.MEDIUM
            elif base_level == AggregationLevel.MEDIUM:
                base_level = AggregationLevel.HIGH
        
        return base_level
    
    def _detect_attack_pattern(
        self,
        events: List[AnomalyEvent],
        correlations: List[CorrelationResult]
    ) -> AttackIndicator:
        """检测攻击模式"""
        for rule in self.aggregation_rules:
            if self._matches_rule(events, correlations, rule):
                return rule.get("attack_indicator", AttackIndicator.NONE)
        
        return AttackIndicator.NONE
    
    def _matches_rule(
        self,
        events: List[AnomalyEvent],
        correlations: List[CorrelationResult],
        rule: Dict
    ) -> bool:
        """匹配规则"""
        condition = rule["condition"]
        
        if "min_sources" in condition:
            unique_sources = {e.source for e in events}
            if len(unique_sources) < condition["min_sources"]:
                return False
        
        if "min_same_source" in condition:
            source_counts: Dict[AnomalySource, int] = defaultdict(int)
            for e in events:
                source_counts[e.source] += 1
            if max(source_counts.values()) < condition["min_same_source"]:
                return False
        
        if "same_user" in condition and condition["same_user"]:
            unique_users = {e.user_id for e in events}
            if len(unique_users) > 1:
                return False
        
        if "multiple_users" in condition and condition["multiple_users"]:
            unique_users = {e.user_id for e in events}
            if len(unique_users) < 2:
                return False
        
        if "severity_escalation" in condition and condition["severity_escalation"]:
            severity_order = ["low", "medium", "high", "critical"]
            sorted_events = sorted(events, key=lambda x: x.timestamp)
            severities = [e.severity for e in sorted_events]
            
            escalated = False
            for i in range(1, len(severities)):
                if severity_order.index(severities[i]) > severity_order.index(severities[i - 1]):
                    escalated = True
                    break
            if not escalated:
                return False
        
        if "sources" in condition:
            event_sources = {e.source.value for e in events}
            required_sources = set(condition["sources"])
            if not required_sources.issubset(event_sources):
                return False
        
        return True
    
    def _calculate_risk_score(
        self,
        events: List[AnomalyEvent],
        correlations: List[CorrelationResult],
        attack_indicator: AttackIndicator
    ) -> float:
        """计算风险分数"""
        severity_weights = {"low": 0.1, "medium": 0.3, "high": 0.6, "critical": 0.9}
        
        base_score = sum(
            severity_weights.get(e.severity, 0.1) * e.confidence
            for e in events
        ) / max(1, len(events))
        
        correlation_bonus = len(correlations) * 0.05
        
        attack_bonus = {
            AttackIndicator.NONE: 0,
            AttackIndicator.TARGETED_ATTACK: 0.1,
            AttackIndicator.REPEATED_ATTEMPTS: 0.15,
            AttackIndicator.ESCALATING_SEVERITY: 0.2,
            AttackIndicator.MULTI_VECTOR_ATTACK: 0.25,
            AttackIndicator.COORDINATED_ATTACK: 0.3,
        }.get(attack_indicator, 0)
        
        return min(1.0, base_score + correlation_bonus + attack_bonus)
    
    def _generate_recommendations(
        self,
        level: AggregationLevel,
        attack_indicator: AttackIndicator,
        events: List[AnomalyEvent]
    ) -> List[str]:
        """生成建议"""
        recommendations = []
        
        if level == AggregationLevel.CRITICAL:
            recommendations.append("立即触发安全响应流程")
            recommendations.append("通知安全团队和相关负责人")
            recommendations.append("考虑临时锁定受影响账户")
        elif level == AggregationLevel.HIGH:
            recommendations.append("加强身份验证")
            recommendations.append("限制敏感操作")
            recommendations.append("人工审核介入")
        elif level == AggregationLevel.MEDIUM:
            recommendations.append("持续监控")
            recommendations.append("记录详细日志")
        
        if attack_indicator == AttackIndicator.COORDINATED_ATTACK:
            recommendations.append("检测到协同攻击，分析攻击者关联")
        elif attack_indicator == AttackIndicator.MULTI_VECTOR_ATTACK:
            recommendations.append("多向量攻击，全面检查各入口点")
        elif attack_indicator == AttackIndicator.ESCALATING_SEVERITY:
            recommendations.append("攻击升级中，立即采取防御措施")
        
        unique_sources = {e.source for e in events}
        for source in unique_sources:
            recommendations.append(f"检查{source.value}相关异常")
        
        return recommendations[:8]
    
    def _create_empty_result(self) -> AggregationResult:
        """创建空结果"""
        return AggregationResult(
            aggregation_id=f"agg_empty_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            level=AggregationLevel.LOW,
            total_events=0,
            unique_sources=set(),
            correlated_groups=[],
            overall_risk_score=0.0,
            attack_indicator=AttackIndicator.NONE,
            affected_users=set(),
            affected_sessions=set(),
            recommendations=["无异常事件"],
            created_at=datetime.now()
        )
    
    def get_recent_aggregations(self, limit: int = 10) -> List[AggregationResult]:
        """获取最近聚合结果"""
        return self.recent_aggregations[-limit:]
    
    def mark_false_positive(self, aggregation_id: str):
        """标记误报"""
        self.stats["false_positives"] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "buffered_users": len(self.event_buffer),
            "recent_aggregations": len(self.recent_aggregations),
        }
