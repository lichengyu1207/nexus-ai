"""
用户行为基线智能体
负责为每个用户建立和维护正常行为基线
"""
import asyncio
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class BehaviorCategory(Enum):
    """行为类别"""
    TIME_PATTERN = "time_pattern"
    OPERATION_TYPE = "operation_type"
    LANGUAGE_FEATURE = "language_feature"
    INTERACTION_TARGET = "interaction_target"
    DEVICE_PATTERN = "device_pattern"
    LOCATION_PATTERN = "location_pattern"


class DeviationLevel(Enum):
    """偏离等级"""
    NORMAL = "normal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class TimePattern:
    """时间模式"""
    active_hours: Set[int]
    peak_hours: List[int]
    avg_session_duration: float
    avg_sessions_per_day: float
    typical_intervals: List[float]


@dataclass
class OperationPattern:
    """操作模式"""
    frequent_operations: Dict[str, int]
    operation_sequence: List[str]
    avg_operations_per_session: float
    sensitive_operation_rate: float


@dataclass
class LanguagePattern:
    """语言模式"""
    avg_message_length: float
    vocabulary_size: int
    common_phrases: List[str]
    emotion_baseline: float
    formality_level: float


@dataclass
class UserBehaviorBaseline:
    """用户行为基线"""
    user_id: str
    time_pattern: TimePattern
    operation_pattern: OperationPattern
    language_pattern: LanguagePattern
    interaction_targets: Dict[str, int]
    device_fingerprints: Set[str]
    last_updated: datetime
    sample_count: int
    confidence: float


@dataclass
class DeviationResult:
    """偏离检测结果"""
    category: BehaviorCategory
    level: DeviationLevel
    deviation_score: float
    description: str
    current_value: Any
    baseline_value: Any
    timestamp: datetime


@dataclass
class BaselineCheckResult:
    """基线检查结果"""
    user_id: str
    overall_deviation: DeviationLevel
    deviations: List[DeviationResult]
    risk_score: float
    requires_verification: bool
    recommendations: List[str]


class UserBehaviorBaselineAgent:
    """用户行为基线智能体"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.name = "UserBehaviorBaselineAgent"
        self.config = config or {}
        self.user_baselines: Dict[str, UserBehaviorBaseline] = {}
        self.user_sessions: Dict[str, List[Dict]] = defaultdict(list)
        self.deviation_thresholds = self._init_thresholds()
        self.stats = {
            "total_users": 0,
            "baselines_created": 0,
            "baselines_updated": 0,
            "deviations_detected": 0,
            "critical_deviations": 0,
            "verifications_triggered": 0,
        }
    
    def _init_thresholds(self) -> Dict[str, Dict]:
        """初始化阈值"""
        return {
            "time_deviation": {
                "low": 1.5,
                "medium": 2.5,
                "high": 4.0,
                "critical": 6.0
            },
            "operation_deviation": {
                "low": 0.3,
                "medium": 0.5,
                "high": 0.7,
                "critical": 0.9
            },
            "language_deviation": {
                "low": 0.2,
                "medium": 0.4,
                "high": 0.6,
                "critical": 0.8
            },
            "session_duration_deviation": {
                "low": 2.0,
                "medium": 3.0,
                "high": 5.0,
                "critical": 8.0
            },
        }
    
    async def initialize(self) -> bool:
        """初始化智能体"""
        await asyncio.sleep(0.1)
        return True
    
    def record_behavior(
        self,
        user_id: str,
        session_id: str,
        operation: str,
        message: str = "",
        target_agent: str = "",
        device_fingerprint: str = "",
        location: str = "",
        emotion_score: float = 0.5
    ):
        """记录用户行为"""
        behavior_data = {
            "timestamp": datetime.now(),
            "session_id": session_id,
            "operation": operation,
            "message": message,
            "message_length": len(message),
            "target_agent": target_agent,
            "device_fingerprint": device_fingerprint,
            "location": location,
            "emotion_score": emotion_score,
            "hour": datetime.now().hour,
        }
        
        self.user_sessions[user_id].append(behavior_data)
    
    def create_baseline(self, user_id: str) -> UserBehaviorBaseline:
        """创建用户基线"""
        sessions = self.user_sessions.get(user_id, [])
        
        if len(sessions) < 10:
            return self._create_default_baseline(user_id)
        
        time_pattern = self._build_time_pattern(sessions)
        operation_pattern = self._build_operation_pattern(sessions)
        language_pattern = self._build_language_pattern(sessions)
        interaction_targets = self._build_interaction_targets(sessions)
        device_fingerprints = self._build_device_fingerprints(sessions)
        
        baseline = UserBehaviorBaseline(
            user_id=user_id,
            time_pattern=time_pattern,
            operation_pattern=operation_pattern,
            language_pattern=language_pattern,
            interaction_targets=interaction_targets,
            device_fingerprints=device_fingerprints,
            last_updated=datetime.now(),
            sample_count=len(sessions),
            confidence=min(1.0, len(sessions) / 100)
        )
        
        self.user_baselines[user_id] = baseline
        self.stats["baselines_created"] += 1
        self.stats["total_users"] = len(self.user_baselines)
        
        return baseline
    
    def _create_default_baseline(self, user_id: str) -> UserBehaviorBaseline:
        """创建默认基线"""
        return UserBehaviorBaseline(
            user_id=user_id,
            time_pattern=TimePattern(
                active_hours=set(range(8, 22)),
                peak_hours=[9, 10, 14, 15, 16],
                avg_session_duration=300,
                avg_sessions_per_day=3,
                typical_intervals=[3600, 7200]
            ),
            operation_pattern=OperationPattern(
                frequent_operations={"query": 50, "view": 30, "download": 10},
                operation_sequence=["query", "view", "download"],
                avg_operations_per_session=5,
                sensitive_operation_rate=0.1
            ),
            language_pattern=LanguagePattern(
                avg_message_length=50,
                vocabulary_size=200,
                common_phrases=["查询", "了解", "咨询"],
                emotion_baseline=0.5,
                formality_level=0.6
            ),
            interaction_targets={"valuation_agent": 30, "document_agent": 20},
            device_fingerprints=set(),
            last_updated=datetime.now(),
            sample_count=0,
            confidence=0.1
        )
    
    def _build_time_pattern(self, sessions: List[Dict]) -> TimePattern:
        """构建时间模式"""
        hours = [s["hour"] for s in sessions]
        hour_counts = defaultdict(int)
        for h in hours:
            hour_counts[h] += 1
        
        active_hours = {h for h, c in hour_counts.items() if c >= 2}
        peak_hours = sorted(hour_counts.keys(), key=lambda x: hour_counts[x], reverse=True)[:3]
        
        session_durations: Dict[str, List[float]] = defaultdict(list)
        for s in sessions:
            session_durations[s["session_id"]].append(s["timestamp"])
        
        durations = []
        for sid, timestamps in session_durations.items():
            if len(timestamps) > 1:
                duration = (max(timestamps) - min(timestamps)).total_seconds()
                durations.append(duration)
        
        avg_duration = sum(durations) / len(durations) if durations else 300
        
        session_dates = set(s["timestamp"].date() for s in sessions)
        sessions_per_day = len(sessions) / max(1, len(session_dates))
        
        intervals = []
        sorted_sessions = sorted(sessions, key=lambda x: x["timestamp"])
        for i in range(1, len(sorted_sessions)):
            interval = (sorted_sessions[i]["timestamp"] - sorted_sessions[i - 1]["timestamp"]).total_seconds()
            if interval < 86400:
                intervals.append(interval)
        
        typical_intervals = sorted(intervals)[:5] if intervals else [3600, 7200]
        
        return TimePattern(
            active_hours=active_hours if active_hours else set(range(8, 22)),
            peak_hours=peak_hours if peak_hours else [9, 10, 14],
            avg_session_duration=avg_duration,
            avg_sessions_per_day=sessions_per_day,
            typical_intervals=typical_intervals
        )
    
    def _build_operation_pattern(self, sessions: List[Dict]) -> OperationPattern:
        """构建操作模式"""
        operation_counts: Dict[str, int] = defaultdict(int)
        for s in sessions:
            operation_counts[s["operation"]] += 1
        
        frequent_operations = dict(sorted(operation_counts.items(), key=lambda x: x[1], reverse=True)[:10])
        
        session_ops: Dict[str, List[str]] = defaultdict(list)
        for s in sessions:
            session_ops[s["session_id"]].append(s["operation"])
        
        operation_sequence = []
        if session_ops:
            first_session = min(session_ops.items(), key=lambda x: min(sessions, key=lambda s: s["session_id"] == x[0])["timestamp"])
            operation_sequence = first_session[1][:5]
        
        total_ops = len(sessions)
        session_ids = set(s["session_id"] for s in sessions)
        avg_ops_per_session = total_ops / max(1, len(session_ids))
        
        sensitive_ops = {"delete", "export", "transfer", "modify_sensitive", "permission_change"}
        sensitive_count = sum(1 for s in sessions if s["operation"] in sensitive_ops)
        sensitive_rate = sensitive_count / max(1, total_ops)
        
        return OperationPattern(
            frequent_operations=frequent_operations,
            operation_sequence=operation_sequence,
            avg_operations_per_session=avg_ops_per_session,
            sensitive_operation_rate=sensitive_rate
        )
    
    def _build_language_pattern(self, sessions: List[Dict]) -> LanguagePattern:
        """构建语言模式"""
        messages = [s["message"] for s in sessions if s["message"]]
        
        if not messages:
            return LanguagePattern(
                avg_message_length=50,
                vocabulary_size=200,
                common_phrases=["查询", "了解", "咨询"],
                emotion_baseline=0.5,
                formality_level=0.6
            )
        
        avg_length = sum(len(m) for m in messages) / len(messages)
        
        all_words: Set[str] = set()
        for m in messages:
            all_words.update(m.lower().split())
        vocabulary_size = len(all_words)
        
        phrase_counts: Dict[str, int] = defaultdict(int)
        for m in messages:
            words = m.split()
            for i in range(len(words) - 1):
                phrase = " ".join(words[i:i + 2])
                phrase_counts[phrase] += 1
        
        common_phrases = sorted(phrase_counts.keys(), key=lambda x: phrase_counts[x], reverse=True)[:10]
        
        emotion_scores = [s["emotion_score"] for s in sessions if "emotion_score" in s]
        emotion_baseline = sum(emotion_scores) / len(emotion_scores) if emotion_scores else 0.5
        
        formal_indicators = sum(1 for m in messages if any(w in m for w in ["请", "您好", "感谢", "麻烦"]))
        formality_level = formal_indicators / max(1, len(messages))
        
        return LanguagePattern(
            avg_message_length=avg_length,
            vocabulary_size=vocabulary_size,
            common_phrases=common_phrases,
            emotion_baseline=emotion_baseline,
            formality_level=formality_level
        )
    
    def _build_interaction_targets(self, sessions: List[Dict]) -> Dict[str, int]:
        """构建交互目标"""
        targets: Dict[str, int] = defaultdict(int)
        for s in sessions:
            if s.get("target_agent"):
                targets[s["target_agent"]] += 1
        return dict(targets)
    
    def _build_device_fingerprints(self, sessions: List[Dict]) -> Set[str]:
        """构建设备指纹"""
        return {s["device_fingerprint"] for s in sessions if s.get("device_fingerprint")}
    
    def check_deviation(
        self,
        user_id: str,
        current_behavior: Dict
    ) -> BaselineCheckResult:
        """检查偏离"""
        if user_id not in self.user_baselines:
            self.create_baseline(user_id)
        
        baseline = self.user_baselines[user_id]
        deviations = []
        
        time_deviation = self._check_time_deviation(baseline, current_behavior)
        if time_deviation:
            deviations.append(time_deviation)
        
        operation_deviation = self._check_operation_deviation(baseline, current_behavior)
        if operation_deviation:
            deviations.append(operation_deviation)
        
        language_deviation = self._check_language_deviation(baseline, current_behavior)
        if language_deviation:
            deviations.append(language_deviation)
        
        device_deviation = self._check_device_deviation(baseline, current_behavior)
        if device_deviation:
            deviations.append(device_deviation)
        
        overall_deviation = self._calculate_overall_deviation(deviations)
        risk_score = self._calculate_risk_score(deviations)
        requires_verification = overall_deviation in [DeviationLevel.HIGH, DeviationLevel.CRITICAL]
        recommendations = self._generate_recommendations(deviations, overall_deviation)
        
        if deviations:
            self.stats["deviations_detected"] += 1
        if overall_deviation == DeviationLevel.CRITICAL:
            self.stats["critical_deviations"] += 1
        if requires_verification:
            self.stats["verifications_triggered"] += 1
        
        return BaselineCheckResult(
            user_id=user_id,
            overall_deviation=overall_deviation,
            deviations=deviations,
            risk_score=risk_score,
            requires_verification=requires_verification,
            recommendations=recommendations
        )
    
    def _check_time_deviation(
        self,
        baseline: UserBehaviorBaseline,
        current: Dict
    ) -> Optional[DeviationResult]:
        """检查时间偏离"""
        current_hour = current.get("hour", datetime.now().hour)
        
        if current_hour not in baseline.time_pattern.active_hours:
            return DeviationResult(
                category=BehaviorCategory.TIME_PATTERN,
                level=DeviationLevel.MEDIUM,
                deviation_score=0.5,
                description=f"非活跃时段访问: {current_hour}时",
                current_value=current_hour,
                baseline_value=list(baseline.time_pattern.active_hours),
                timestamp=datetime.now()
            )
        
        return None
    
    def _check_operation_deviation(
        self,
        baseline: UserBehaviorBaseline,
        current: Dict
    ) -> Optional[DeviationResult]:
        """检查操作偏离"""
        current_op = current.get("operation", "")
        
        if current_op not in baseline.operation_pattern.frequent_operations:
            sensitive_ops = {"delete", "export", "transfer", "permission_change"}
            if current_op in sensitive_ops:
                return DeviationResult(
                    category=BehaviorCategory.OPERATION_TYPE,
                    level=DeviationLevel.HIGH,
                    deviation_score=0.7,
                    description=f"首次执行敏感操作: {current_op}",
                    current_value=current_op,
                    baseline_value=list(baseline.operation_pattern.frequent_operations.keys()),
                    timestamp=datetime.now()
                )
        
        return None
    
    def _check_language_deviation(
        self,
        baseline: UserBehaviorBaseline,
        current: Dict
    ) -> Optional[DeviationResult]:
        """检查语言偏离"""
        message = current.get("message", "")
        if not message:
            return None
        
        current_length = len(message)
        baseline_length = baseline.language_pattern.avg_message_length
        
        if baseline_length > 0:
            deviation = abs(current_length - baseline_length) / baseline_length
            thresholds = self.deviation_thresholds["language_deviation"]
            
            level = DeviationLevel.NORMAL
            if deviation >= thresholds["critical"]:
                level = DeviationLevel.CRITICAL
            elif deviation >= thresholds["high"]:
                level = DeviationLevel.HIGH
            elif deviation >= thresholds["medium"]:
                level = DeviationLevel.MEDIUM
            elif deviation >= thresholds["low"]:
                level = DeviationLevel.LOW
            
            if level != DeviationLevel.NORMAL:
                return DeviationResult(
                    category=BehaviorCategory.LANGUAGE_FEATURE,
                    level=level,
                    deviation_score=deviation,
                    description=f"消息长度偏离基线: {current_length} vs {baseline_length:.0f}",
                    current_value=current_length,
                    baseline_value=baseline_length,
                    timestamp=datetime.now()
                )
        
        return None
    
    def _check_device_deviation(
        self,
        baseline: UserBehaviorBaseline,
        current: Dict
    ) -> Optional[DeviationResult]:
        """检查设备偏离"""
        current_device = current.get("device_fingerprint", "")
        
        if current_device and baseline.device_fingerprints:
            if current_device not in baseline.device_fingerprints:
                return DeviationResult(
                    category=BehaviorCategory.DEVICE_PATTERN,
                    level=DeviationLevel.HIGH,
                    deviation_score=0.6,
                    description="检测到新设备访问",
                    current_value=current_device,
                    baseline_value=list(baseline.device_fingerprints),
                    timestamp=datetime.now()
                )
        
        return None
    
    def _calculate_overall_deviation(
        self, 
        deviations: List[DeviationResult]
    ) -> DeviationLevel:
        """计算整体偏离等级"""
        if not deviations:
            return DeviationLevel.NORMAL
        
        severity_order = {
            DeviationLevel.NORMAL: 0,
            DeviationLevel.LOW: 1,
            DeviationLevel.MEDIUM: 2,
            DeviationLevel.HIGH: 3,
            DeviationLevel.CRITICAL: 4,
        }
        
        max_level = max(deviations, key=lambda x: severity_order[x.level])
        
        if len(deviations) >= 3:
            level_value = min(4, severity_order[max_level.level] + 1)
            return list(severity_order.keys())[level_value]
        
        return max_level.level
    
    def _calculate_risk_score(self, deviations: List[DeviationResult]) -> float:
        """计算风险分数"""
        if not deviations:
            return 0.0
        
        severity_weights = {
            DeviationLevel.NORMAL: 0.0,
            DeviationLevel.LOW: 0.1,
            DeviationLevel.MEDIUM: 0.3,
            DeviationLevel.HIGH: 0.6,
            DeviationLevel.CRITICAL: 0.9,
        }
        
        total_score = sum(
            severity_weights.get(d.level, 0.1) * d.deviation_score
            for d in deviations
        )
        
        return min(1.0, total_score)
    
    def _generate_recommendations(
        self,
        deviations: List[DeviationResult],
        overall: DeviationLevel
    ) -> List[str]:
        """生成建议"""
        recommendations = []
        
        for d in deviations:
            recommendations.append(f"{d.category.value}: {d.description}")
        
        if overall == DeviationLevel.CRITICAL:
            recommendations.append("立即触发多因素身份验证")
            recommendations.append("通知安全团队")
        elif overall == DeviationLevel.HIGH:
            recommendations.append("要求额外身份验证")
            recommendations.append("限制敏感操作")
        elif overall == DeviationLevel.MEDIUM:
            recommendations.append("加强监控")
        
        return recommendations
    
    def update_baseline(self, user_id: str):
        """更新用户基线"""
        if user_id in self.user_baselines:
            self.create_baseline(user_id)
            self.stats["baselines_updated"] += 1
    
    def reset_baseline(self, user_id: str):
        """重置用户基线"""
        if user_id in self.user_baselines:
            del self.user_baselines[user_id]
            self.stats["baselines_created"] -= 1
    
    def get_baseline(self, user_id: str) -> Optional[UserBehaviorBaseline]:
        """获取用户基线"""
        return self.user_baselines.get(user_id)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "active_users": len(self.user_sessions),
        }
