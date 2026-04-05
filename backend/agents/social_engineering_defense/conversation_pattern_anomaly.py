"""
对话模式异常检测智能体
负责检测对话模式中的异常行为
"""
import asyncio
import math
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class AnomalyType(Enum):
    """异常类型"""
    LENGTH_ANOMALY = "length_anomaly"
    TOPIC_SWITCH_ANOMALY = "topic_switch_anomaly"
    RESPONSE_TIME_ANOMALY = "response_time_anomaly"
    EMOTION_SPIKE_ANOMALY = "emotion_spike_anomaly"
    REPETITION_ANOMALY = "repetition_anomaly"
    PATTERN_DEVIATION = "pattern_deviation"
    FREQUENCY_ANOMALY = "frequency_anomaly"
    NONE = "none"


class AnomalySeverity(Enum):
    """异常严重程度"""
    NORMAL = "normal"
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    CRITICAL = "critical"


@dataclass
class ConversationMetrics:
    """对话指标"""
    message_count: int
    total_length: int
    avg_message_length: float
    topic_switches: int
    avg_response_time: float
    response_time_variance: float
    emotion_scores: List[float]
    unique_words: int
    repetition_ratio: float
    session_duration: float


@dataclass
class AnomalyInstance:
    """异常实例"""
    anomaly_type: AnomalyType
    severity: AnomalySeverity
    deviation_score: float
    description: str
    timestamp: datetime
    metrics: Dict[str, Any]
    context: str


@dataclass
class AnomalyDetectionResult:
    """异常检测结果"""
    session_id: str
    overall_severity: AnomalySeverity
    anomalies: List[AnomalyInstance]
    baseline_metrics: ConversationMetrics
    current_metrics: ConversationMetrics
    risk_score: float
    action_required: str
    recommendations: List[str]


class ConversationPatternAnomalyAgent:
    """对话模式异常检测智能体"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.name = "ConversationPatternAnomalyAgent"
        self.config = config or {}
        self.global_baselines = self._init_global_baselines()
        self.user_baselines: Dict[str, ConversationMetrics] = {}
        self.session_metrics: Dict[str, List[Dict]] = defaultdict(list)
        self.session_anomalies: Dict[str, List[AnomalyInstance]] = defaultdict(list)
        self.anomaly_thresholds = self._init_thresholds()
        self.stats = {
            "total_sessions": 0,
            "total_messages": 0,
            "anomalies_detected": 0,
            "anomaly_types": defaultdict(int),
            "severe_sessions": 0,
            "baselines_updated": 0,
        }
    
    def _init_global_baselines(self) -> Dict[str, ConversationMetrics]:
        """初始化全局基线"""
        return {
            "consultation": ConversationMetrics(
                message_count=8,
                total_length=800,
                avg_message_length=100,
                topic_switches=2,
                avg_response_time=30,
                response_time_variance=15,
                emotion_scores=[0.5],
                unique_words=200,
                repetition_ratio=0.1,
                session_duration=240
            ),
            "complaint": ConversationMetrics(
                message_count=12,
                total_length=1500,
                avg_message_length=125,
                topic_switches=4,
                avg_response_time=45,
                response_time_variance=25,
                emotion_scores=[0.7],
                unique_words=350,
                repetition_ratio=0.15,
                session_duration=480
            ),
            "transaction": ConversationMetrics(
                message_count=5,
                total_length=400,
                avg_message_length=80,
                topic_switches=1,
                avg_response_time=20,
                response_time_variance=10,
                emotion_scores=[0.3],
                unique_words=100,
                repetition_ratio=0.08,
                session_duration=120
            ),
        }
    
    def _init_thresholds(self) -> Dict[str, Dict]:
        """初始化阈值"""
        return {
            "length_deviation": {
                "mild": 1.5,
                "moderate": 2.0,
                "severe": 3.0,
                "critical": 5.0
            },
            "topic_switch_rate": {
                "mild": 3,
                "moderate": 5,
                "severe": 8,
                "critical": 12
            },
            "response_time_deviation": {
                "mild": 2.0,
                "moderate": 3.0,
                "severe": 5.0,
                "critical": 10.0
            },
            "emotion_spike": {
                "mild": 0.3,
                "moderate": 0.5,
                "severe": 0.7,
                "critical": 0.9
            },
            "repetition_ratio": {
                "mild": 0.2,
                "moderate": 0.35,
                "severe": 0.5,
                "critical": 0.7
            },
        }
    
    async def initialize(self) -> bool:
        """初始化智能体"""
        await asyncio.sleep(0.1)
        return True
    
    def record_message(
        self,
        session_id: str,
        user_id: str,
        message: str,
        response_time: float = 0,
        emotion_score: float = 0.5,
        topic: str = ""
    ):
        """记录消息"""
        self.stats["total_messages"] += 1
        
        message_data = {
            "timestamp": datetime.now(),
            "length": len(message),
            "response_time": response_time,
            "emotion_score": emotion_score,
            "topic": topic,
            "words": set(message.lower().split()),
        }
        
        self.session_metrics[session_id].append(message_data)
    
    def calculate_session_metrics(
        self, 
        session_id: str,
        scenario: str = "consultation"
    ) -> ConversationMetrics:
        """计算会话指标"""
        messages = self.session_metrics.get(session_id, [])
        
        if not messages:
            return self.global_baselines.get(scenario, self.global_baselines["consultation"])
        
        total_length = sum(m["length"] for m in messages)
        avg_length = total_length / len(messages)
        
        response_times = [m["response_time"] for m in messages if m["response_time"] > 0]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        variance = sum((r - avg_response_time) ** 2 for r in response_times) / len(response_times) if response_times else 0
        
        topics = [m["topic"] for m in messages if m["topic"]]
        topic_switches = sum(1 for i in range(1, len(topics)) if topics[i] != topics[i - 1])
        
        emotion_scores = [m["emotion_score"] for m in messages]
        
        all_words: set = set()
        word_counts: Dict[str, int] = defaultdict(int)
        total_words = 0
        
        for m in messages:
            for word in m["words"]:
                all_words.add(word)
                word_counts[word] += 1
                total_words += 1
        
        repetition_ratio = 1 - (len(all_words) / max(1, total_words)) if total_words > 0 else 0
        
        duration = (messages[-1]["timestamp"] - messages[0]["timestamp"]).total_seconds() if len(messages) > 1 else 0
        
        return ConversationMetrics(
            message_count=len(messages),
            total_length=total_length,
            avg_message_length=avg_length,
            topic_switches=topic_switches,
            avg_response_time=avg_response_time,
            response_time_variance=math.sqrt(variance),
            emotion_scores=emotion_scores,
            unique_words=len(all_words),
            repetition_ratio=repetition_ratio,
            session_duration=duration
        )
    
    def detect_anomalies(
        self,
        session_id: str,
        user_id: str,
        scenario: str = "consultation"
    ) -> List[AnomalyInstance]:
        """检测异常"""
        current_metrics = self.calculate_session_metrics(session_id, scenario)
        baseline = self.user_baselines.get(user_id, self.global_baselines.get(scenario, self.global_baselines["consultation"]))
        
        anomalies = []
        
        length_anomaly = self._detect_length_anomaly(current_metrics, baseline)
        if length_anomaly:
            anomalies.append(length_anomaly)
        
        topic_anomaly = self._detect_topic_anomaly(current_metrics, baseline)
        if topic_anomaly:
            anomalies.append(topic_anomaly)
        
        time_anomaly = self._detect_response_time_anomaly(current_metrics, baseline)
        if time_anomaly:
            anomalies.append(time_anomaly)
        
        emotion_anomaly = self._detect_emotion_anomaly(current_metrics)
        if emotion_anomaly:
            anomalies.append(emotion_anomaly)
        
        repetition_anomaly = self._detect_repetition_anomaly(current_metrics, baseline)
        if repetition_anomaly:
            anomalies.append(repetition_anomaly)
        
        for anomaly in anomalies:
            self.session_anomalies[session_id].append(anomaly)
            self.stats["anomaly_types"][anomaly.anomaly_type.value] += 1
        
        if anomalies:
            self.stats["anomalies_detected"] += 1
        
        return anomalies
    
    def _detect_length_anomaly(
        self, 
        current: ConversationMetrics,
        baseline: ConversationMetrics
    ) -> Optional[AnomalyInstance]:
        """检测长度异常"""
        if baseline.avg_message_length == 0:
            return None
        
        deviation = abs(current.avg_message_length - baseline.avg_message_length) / baseline.avg_message_length
        thresholds = self.anomaly_thresholds["length_deviation"]
        
        severity = AnomalySeverity.NORMAL
        if deviation >= thresholds["critical"]:
            severity = AnomalySeverity.CRITICAL
        elif deviation >= thresholds["severe"]:
            severity = AnomalySeverity.SEVERE
        elif deviation >= thresholds["moderate"]:
            severity = AnomalySeverity.MODERATE
        elif deviation >= thresholds["mild"]:
            severity = AnomalySeverity.MILD
        
        if severity == AnomalySeverity.NORMAL:
            return None
        
        return AnomalyInstance(
            anomaly_type=AnomalyType.LENGTH_ANOMALY,
            severity=severity,
            deviation_score=deviation,
            description=f"消息长度偏离基线{deviation:.2f}倍",
            timestamp=datetime.now(),
            metrics={
                "current_avg": current.avg_message_length,
                "baseline_avg": baseline.avg_message_length
            },
            context=f"当前平均长度: {current.avg_message_length:.1f}, 基线: {baseline.avg_message_length:.1f}"
        )
    
    def _detect_topic_anomaly(
        self,
        current: ConversationMetrics,
        baseline: ConversationMetrics
    ) -> Optional[AnomalyInstance]:
        """检测话题切换异常"""
        switch_rate = current.topic_switches / max(1, current.message_count)
        baseline_rate = baseline.topic_switches / max(1, baseline.message_count)
        
        thresholds = self.anomaly_thresholds["topic_switch_rate"]
        
        severity = AnomalySeverity.NORMAL
        if current.topic_switches >= thresholds["critical"]:
            severity = AnomalySeverity.CRITICAL
        elif current.topic_switches >= thresholds["severe"]:
            severity = AnomalySeverity.SEVERE
        elif current.topic_switches >= thresholds["moderate"]:
            severity = AnomalySeverity.MODERATE
        elif current.topic_switches >= thresholds["mild"]:
            severity = AnomalySeverity.MILD
        
        if severity == AnomalySeverity.NORMAL:
            return None
        
        return AnomalyInstance(
            anomaly_type=AnomalyType.TOPIC_SWITCH_ANOMALY,
            severity=severity,
            deviation_score=current.topic_switches,
            description=f"话题切换次数异常: {current.topic_switches}次",
            timestamp=datetime.now(),
            metrics={
                "current_switches": current.topic_switches,
                "baseline_switches": baseline.topic_switches
            },
            context=f"切换率: {switch_rate:.2f}, 基线率: {baseline_rate:.2f}"
        )
    
    def _detect_response_time_anomaly(
        self,
        current: ConversationMetrics,
        baseline: ConversationMetrics
    ) -> Optional[AnomalyInstance]:
        """检测响应时间异常"""
        if baseline.avg_response_time == 0:
            return None
        
        deviation = abs(current.avg_response_time - baseline.avg_response_time) / baseline.avg_response_time
        thresholds = self.anomaly_thresholds["response_time_deviation"]
        
        severity = AnomalySeverity.NORMAL
        if deviation >= thresholds["critical"]:
            severity = AnomalySeverity.CRITICAL
        elif deviation >= thresholds["severe"]:
            severity = AnomalySeverity.SEVERE
        elif deviation >= thresholds["moderate"]:
            severity = AnomalySeverity.MODERATE
        elif deviation >= thresholds["mild"]:
            severity = AnomalySeverity.MILD
        
        if severity == AnomalySeverity.NORMAL:
            return None
        
        return AnomalyInstance(
            anomaly_type=AnomalyType.RESPONSE_TIME_ANOMALY,
            severity=severity,
            deviation_score=deviation,
            description=f"响应时间偏离基线{deviation:.2f}倍",
            timestamp=datetime.now(),
            metrics={
                "current_avg": current.avg_response_time,
                "baseline_avg": baseline.avg_response_time
            },
            context=f"当前平均: {current.avg_response_time:.1f}秒, 基线: {baseline.avg_response_time:.1f}秒"
        )
    
    def _detect_emotion_anomaly(
        self, 
        current: ConversationMetrics
    ) -> Optional[AnomalyInstance]:
        """检测情感异常"""
        if len(current.emotion_scores) < 2:
            return None
        
        spikes = []
        for i in range(1, len(current.emotion_scores)):
            spike = abs(current.emotion_scores[i] - current.emotion_scores[i - 1])
            if spike > 0.3:
                spikes.append(spike)
        
        if not spikes:
            return None
        
        max_spike = max(spikes)
        thresholds = self.anomaly_thresholds["emotion_spike"]
        
        severity = AnomalySeverity.NORMAL
        if max_spike >= thresholds["critical"]:
            severity = AnomalySeverity.CRITICAL
        elif max_spike >= thresholds["severe"]:
            severity = AnomalySeverity.SEVERE
        elif max_spike >= thresholds["moderate"]:
            severity = AnomalySeverity.MODERATE
        elif max_spike >= thresholds["mild"]:
            severity = AnomalySeverity.MILD
        
        if severity == AnomalySeverity.NORMAL:
            return None
        
        return AnomalyInstance(
            anomaly_type=AnomalyType.EMOTION_SPIKE_ANOMALY,
            severity=severity,
            deviation_score=max_spike,
            description=f"检测到情感剧烈波动: {max_spike:.2f}",
            timestamp=datetime.now(),
            metrics={
                "spike_count": len(spikes),
                "max_spike": max_spike
            },
            context=f"情感波动次数: {len(spikes)}, 最大波动: {max_spike:.2f}"
        )
    
    def _detect_repetition_anomaly(
        self,
        current: ConversationMetrics,
        baseline: ConversationMetrics
    ) -> Optional[AnomalyInstance]:
        """检测重复异常"""
        thresholds = self.anomaly_thresholds["repetition_ratio"]
        
        severity = AnomalySeverity.NORMAL
        if current.repetition_ratio >= thresholds["critical"]:
            severity = AnomalySeverity.CRITICAL
        elif current.repetition_ratio >= thresholds["severe"]:
            severity = AnomalySeverity.SEVERE
        elif current.repetition_ratio >= thresholds["moderate"]:
            severity = AnomalySeverity.MODERATE
        elif current.repetition_ratio >= thresholds["mild"]:
            severity = AnomalySeverity.MILD
        
        if severity == AnomalySeverity.NORMAL:
            return None
        
        return AnomalyInstance(
            anomaly_type=AnomalyType.REPETITION_ANOMALY,
            severity=severity,
            deviation_score=current.repetition_ratio,
            description=f"重复率异常: {current.repetition_ratio:.2%}",
            timestamp=datetime.now(),
            metrics={
                "current_ratio": current.repetition_ratio,
                "baseline_ratio": baseline.repetition_ratio
            },
            context=f"当前重复率: {current.repetition_ratio:.2%}, 基线: {baseline.repetition_ratio:.2%}"
        )
    
    def analyze_session(
        self,
        session_id: str,
        user_id: str,
        scenario: str = "consultation"
    ) -> AnomalyDetectionResult:
        """分析会话"""
        anomalies = self.detect_anomalies(session_id, user_id, scenario)
        current_metrics = self.calculate_session_metrics(session_id, scenario)
        baseline = self.user_baselines.get(user_id, self.global_baselines.get(scenario, self.global_baselines["consultation"]))
        
        overall_severity = self._calculate_overall_severity(anomalies)
        risk_score = self._calculate_risk_score(anomalies)
        action_required = self._determine_action(overall_severity)
        recommendations = self._generate_recommendations(anomalies, overall_severity)
        
        if overall_severity in [AnomalySeverity.SEVERE, AnomalySeverity.CRITICAL]:
            self.stats["severe_sessions"] += 1
        
        return AnomalyDetectionResult(
            session_id=session_id,
            overall_severity=overall_severity,
            anomalies=anomalies,
            baseline_metrics=baseline,
            current_metrics=current_metrics,
            risk_score=risk_score,
            action_required=action_required,
            recommendations=recommendations
        )
    
    def _calculate_overall_severity(
        self, 
        anomalies: List[AnomalyInstance]
    ) -> AnomalySeverity:
        """计算整体严重程度"""
        if not anomalies:
            return AnomalySeverity.NORMAL
        
        severity_order = {
            AnomalySeverity.NORMAL: 0,
            AnomalySeverity.MILD: 1,
            AnomalySeverity.MODERATE: 2,
            AnomalySeverity.SEVERE: 3,
            AnomalySeverity.CRITICAL: 4,
        }
        
        max_severity = max(anomalies, key=lambda x: severity_order[x.severity])
        
        if len(anomalies) >= 3:
            severity_level = min(4, severity_order[max_severity.severity] + 1)
            return list(severity_order.keys())[severity_level]
        
        return max_severity.severity
    
    def _calculate_risk_score(self, anomalies: List[AnomalyInstance]) -> float:
        """计算风险分数"""
        if not anomalies:
            return 0.0
        
        severity_weights = {
            AnomalySeverity.NORMAL: 0.0,
            AnomalySeverity.MILD: 0.15,
            AnomalySeverity.MODERATE: 0.35,
            AnomalySeverity.SEVERE: 0.6,
            AnomalySeverity.CRITICAL: 0.9,
        }
        
        base_score = sum(
            severity_weights.get(a.severity, 0.1) * a.deviation_score
            for a in anomalies
        )
        
        return min(1.0, base_score / max(1, len(anomalies)) * 2)
    
    def _determine_action(self, severity: AnomalySeverity) -> str:
        """确定行动"""
        actions = {
            AnomalySeverity.NORMAL: "继续正常对话",
            AnomalySeverity.MILD: "记录观察",
            AnomalySeverity.MODERATE: "标记会话，人工抽检",
            AnomalySeverity.SEVERE: "中断对话，要求重新验证身份",
            AnomalySeverity.CRITICAL: "立即中断，通知安全团队",
        }
        return actions.get(severity, "继续监控")
    
    def _generate_recommendations(
        self,
        anomalies: List[AnomalyInstance],
        severity: AnomalySeverity
    ) -> List[str]:
        """生成建议"""
        recommendations = []
        
        for anomaly in anomalies:
            recommendations.append(f"处理{anomaly.anomaly_type.value}: {anomaly.description}")
        
        if severity == AnomalySeverity.CRITICAL:
            recommendations.append("立即触发安全验证流程")
            recommendations.append("通知安全团队介入")
        elif severity == AnomalySeverity.SEVERE:
            recommendations.append("要求用户进行身份验证")
            recommendations.append("限制敏感操作")
        elif severity == AnomalySeverity.MODERATE:
            recommendations.append("加强监控频率")
            recommendations.append("准备人工介入")
        
        return recommendations[:5]
    
    def update_user_baseline(self, user_id: str, session_id: str):
        """更新用户基线"""
        metrics = self.calculate_session_metrics(session_id)
        
        if user_id in self.user_baselines:
            old = self.user_baselines[user_id]
            
            self.user_baselines[user_id] = ConversationMetrics(
                message_count=int(old.message_count * 0.7 + metrics.message_count * 0.3),
                total_length=int(old.total_length * 0.7 + metrics.total_length * 0.3),
                avg_message_length=old.avg_message_length * 0.7 + metrics.avg_message_length * 0.3,
                topic_switches=int(old.topic_switches * 0.7 + metrics.topic_switches * 0.3),
                avg_response_time=old.avg_response_time * 0.7 + metrics.avg_response_time * 0.3,
                response_time_variance=old.response_time_variance * 0.7 + metrics.response_time_variance * 0.3,
                emotion_scores=metrics.emotion_scores[-10:],
                unique_words=int(old.unique_words * 0.7 + metrics.unique_words * 0.3),
                repetition_ratio=old.repetition_ratio * 0.7 + metrics.repetition_ratio * 0.3,
                session_duration=old.session_duration * 0.7 + metrics.session_duration * 0.3
            )
        else:
            self.user_baselines[user_id] = metrics
        
        self.stats["baselines_updated"] += 1
    
    def clear_session(self, session_id: str):
        """清除会话数据"""
        if session_id in self.session_metrics:
            del self.session_metrics[session_id]
        if session_id in self.session_anomalies:
            del self.session_anomalies[session_id]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "active_sessions": len(self.session_metrics),
            "user_baselines_count": len(self.user_baselines),
            "anomaly_types": dict(self.stats["anomaly_types"]),
        }
