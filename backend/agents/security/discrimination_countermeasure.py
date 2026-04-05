"""
恶意诱导与歧视性言论识别反制系统
Malicious Inducement and Discriminatory Speech Detection Countermeasure System

实现实时识别、多轮追踪、主动阻断、举报反制、证据固定
"""

import hashlib
import json
import logging
import re
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class DetectionType(Enum):
    """检测类型"""
    REGIONAL_DISCRIMINATION = "regional_discrimination"
    RACIAL_DISCRIMINATION = "racial_discrimination"
    RELIGIOUS_OFFENSE = "religious_offense"
    GENDER_DISCRIMINATION = "gender_discrimination"
    INDUCING_LANGUAGE = "inducing_language"
    VARIANT_SPEECH = "variant_speech"
    PROBING_ATTACK = "probing_attack"


class RiskAction(Enum):
    """风险行动"""
    LOG_ONLY = "log_only"
    REJECT_REPLY = "reject_reply"
    TEMP_FREEZE = "temp_freeze"
    PERMANENT_BAN = "permanent_ban"
    REQUIRE_REVIEW = "require_review"


class ReportVerificationResult(Enum):
    """举报验证结果"""
    VALID_REPORT = "valid_report"
    INVALID_REPORT = "invalid_report"
    SUSPICIOUS_REPORT = "suspicious_report"
    MALICIOUS_REPORT = "malicious_report"


@dataclass
class DetectionRule:
    """检测规则"""
    rule_id: str
    detection_type: DetectionType
    patterns: List[str]
    risk_score: float
    action: RiskAction
    description: str
    enabled: bool = True


@dataclass
class DetectionResult:
    """检测结果"""
    detected: bool
    detection_types: List[DetectionType]
    matched_patterns: List[str]
    risk_score: float
    action: RiskAction
    confidence: float
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UserRiskProfileExtended:
    """扩展用户风险画像"""
    user_id: str
    discrimination_attempts: int
    inducing_attempts: int
    total_risk_score: float
    last_violation_time: Optional[datetime]
    violation_history: List[Dict[str, Any]]
    report_history: List[str]
    is_blacklisted: bool
    blacklist_reason: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class BehaviorSequence:
    """行为序列"""
    session_id: str
    user_id: str
    events: List[Dict[str, Any]]
    intent_sequence: List[str]
    risk_trajectory: List[float]
    detected_patterns: List[str]
    is_anomalous: bool
    anomaly_score: float


@dataclass
class EvidenceRecord:
    """证据记录"""
    evidence_id: str
    user_id: str
    event_type: str
    input_hash: str
    detection_result: Dict[str, Any]
    action_taken: str
    timestamp: datetime
    session_id: str = ""
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReportVerification:
    """举报验证"""
    report_id: str
    reporter_id: str
    reported_content_hash: str
    verification_result: ReportVerificationResult
    reporter_history_score: float
    content_violation_score: float
    recommendation: str
    evidence_ids: List[str]


class DiscriminationPatternDetector:
    """歧视性言论模式检测器"""
    
    def __init__(self):
        self.rules = self._init_rules()
        self.pinyin_mappings = self._init_pinyin_mappings()
        self.shape_similar_chars = self._init_shape_similar()
        self.stats = {
            "total_checks": 0,
            "detections": 0,
            "by_type": defaultdict(int),
        }
    
    def _init_rules(self) -> List[DetectionRule]:
        """初始化检测规则（脱敏版）"""
        return [
            DetectionRule(
                rule_id="DISC_001",
                detection_type=DetectionType.REGIONAL_DISCRIMINATION,
                patterns=["[地域歧视词根A]", "[地域歧视词根B]", "[地域歧视变体]"],
                risk_score=30.0,
                action=RiskAction.REJECT_REPLY,
                description="地域歧视检测"
            ),
            DetectionRule(
                rule_id="DISC_002",
                detection_type=DetectionType.RACIAL_DISCRIMINATION,
                patterns=["[种族歧视模式A]", "[种族歧视模式B]"],
                risk_score=50.0,
                action=RiskAction.TEMP_FREEZE,
                description="种族歧视检测"
            ),
            DetectionRule(
                rule_id="DISC_003",
                detection_type=DetectionType.RELIGIOUS_OFFENSE,
                patterns=["[宗教冒犯模板A]", "[宗教冒犯模板B]"],
                risk_score=40.0,
                action=RiskAction.REJECT_REPLY,
                description="宗教冒犯检测"
            ),
            DetectionRule(
                rule_id="DISC_004",
                detection_type=DetectionType.GENDER_DISCRIMINATION,
                patterns=["[性别歧视变种A]", "[性别歧视变种B]"],
                risk_score=35.0,
                action=RiskAction.REJECT_REPLY,
                description="性别歧视检测"
            ),
            DetectionRule(
                rule_id="INDU_001",
                detection_type=DetectionType.INDUCING_LANGUAGE,
                patterns=["[诱导性言论A]", "[诱导性言论B]"],
                risk_score=25.0,
                action=RiskAction.REJECT_REPLY,
                description="诱导性言论检测"
            ),
        ]
    
    def _init_pinyin_mappings(self) -> Dict[str, str]:
        """初始化拼音映射（脱敏版）"""
        return {
            "[敏感拼音A]": "[对应敏感词A]",
            "[敏感拼音B]": "[对应敏感词B]",
        }
    
    def _init_shape_similar(self) -> Dict[str, str]:
        """初始化字形相似映射"""
        return {
            "0": "O",
            "1": "l",
            "5": "S",
        }
    
    def detect(self, text: str) -> DetectionResult:
        """检测歧视性言论"""
        self.stats["total_checks"] += 1
        
        detected_types = []
        matched_patterns = []
        total_risk_score = 0.0
        max_action = RiskAction.LOG_ONLY
        
        normalized_text = self._normalize_text(text)
        
        for rule in self.rules:
            if not rule.enabled:
                continue
            
            for pattern in rule.patterns:
                if pattern in normalized_text or pattern in text:
                    detected_types.append(rule.detection_type)
                    matched_patterns.append(pattern)
                    total_risk_score += rule.risk_score
                    
                    if rule.action.value > max_action.value:
                        max_action = rule.action
                    
                    self.stats["by_type"][rule.detection_type.value] += 1
        
        detected = len(detected_types) > 0
        
        if detected:
            self.stats["detections"] += 1
        
        confidence = min(1.0, total_risk_score / 100.0)
        
        return DetectionResult(
            detected=detected,
            detection_types=list(set(detected_types)),
            matched_patterns=matched_patterns,
            risk_score=total_risk_score,
            action=max_action,
            confidence=confidence
        )
    
    def _normalize_text(self, text: str) -> str:
        """规范化文本"""
        normalized = text.lower()
        normalized = re.sub(r'\s+', '', normalized)
        return normalized
    
    def detect_variant(self, text: str) -> Tuple[bool, List[str]]:
        """检测变体言论"""
        variants = []
        
        for pinyin, original in self.pinyin_mappings.items():
            if pinyin in text.lower():
                variants.append(f"拼音变体: {pinyin}")
        
        for shape_char, original in self.shape_similar_chars.items():
            if shape_char in text:
                variants.append(f"字形变体: {shape_char}")
        
        return len(variants) > 0, variants


class BehaviorSequenceAnalyzer:
    """行为序列分析器"""
    
    def __init__(self):
        self.session_sequences: Dict[str, BehaviorSequence] = {}
        self.intent_weights = self._init_intent_weights()
        self.anomaly_threshold = 0.7
        self.stats = {
            "total_sessions": 0,
            "anomalous_sessions": 0,
            "patterns_detected": defaultdict(int),
        }
    
    def _init_intent_weights(self) -> Dict[str, float]:
        """初始化意图权重"""
        return {
            "normal_query": 0.1,
            "information_request": 0.2,
            "sensitive_topic": 0.5,
            "discrimination_attempt": 1.0,
            "inducing_behavior": 0.8,
        }
    
    def record_event(
        self,
        session_id: str,
        user_id: str,
        event_type: str,
        content: str,
        risk_score: float
    ):
        """记录事件"""
        if session_id not in self.session_sequences:
            self.session_sequences[session_id] = BehaviorSequence(
                session_id=session_id,
                user_id=user_id,
                events=[],
                intent_sequence=[],
                risk_trajectory=[],
                detected_patterns=[],
                is_anomalous=False,
                anomaly_score=0.0
            )
            self.stats["total_sessions"] += 1
        
        sequence = self.session_sequences[session_id]
        
        event = {
            "event_type": event_type,
            "content_hash": hashlib.sha256(content.encode()).hexdigest()[:16],
            "risk_score": risk_score,
            "timestamp": datetime.now().isoformat()
        }
        sequence.events.append(event)
        
        intent = self._classify_intent(event_type, risk_score)
        sequence.intent_sequence.append(intent)
        
        sequence.risk_trajectory.append(risk_score)
        
        self._analyze_sequence(sequence)
    
    def _classify_intent(self, event_type: str, risk_score: float) -> str:
        """分类意图"""
        if risk_score > 50:
            return "discrimination_attempt"
        elif risk_score > 30:
            return "inducing_behavior"
        elif risk_score > 10:
            return "sensitive_topic"
        else:
            return "normal_query"
    
    def _analyze_sequence(self, sequence: BehaviorSequence):
        """分析序列"""
        if len(sequence.events) < 3:
            return
        
        anomaly_score = self._calculate_anomaly_score(sequence)
        sequence.anomaly_score = anomaly_score
        sequence.is_anomalous = anomaly_score > self.anomaly_threshold
        
        if sequence.is_anomalous:
            self.stats["anomalous_sessions"] += 1
            sequence.detected_patterns.append("sudden_intent_shift")
        
        recent_scores = sequence.risk_trajectory[-5:]
        if len(recent_scores) >= 3:
            if all(s > 20 for s in recent_scores[-3:]):
                sequence.detected_patterns.append("escalating_risk")
                self.stats["patterns_detected"]["escalating_risk"] += 1
        
        if len(sequence.intent_sequence) >= 5:
            normal_count = sum(1 for i in sequence.intent_sequence[:-1] if i == "normal_query")
            if normal_count >= 4 and sequence.intent_sequence[-1] in ["discrimination_attempt", "inducing_behavior"]:
                sequence.detected_patterns.append("probing_pattern")
                self.stats["patterns_detected"]["probing_pattern"] += 1
    
    def _calculate_anomaly_score(self, sequence: BehaviorSequence) -> float:
        """计算异常分数"""
        if not sequence.risk_trajectory:
            return 0.0
        
        recent = sequence.risk_trajectory[-5:]
        if len(recent) < 2:
            return recent[0] / 100.0 if recent else 0.0
        
        variance = sum((r - sum(recent)/len(recent))**2 for r in recent) / len(recent)
        trend = (recent[-1] - recent[0]) / max(len(recent) - 1, 1)
        
        anomaly = min(1.0, (variance / 1000.0 + trend / 50.0 + recent[-1] / 100.0) / 3)
        
        return anomaly
    
    def get_sequence(self, session_id: str) -> Optional[BehaviorSequence]:
        return self.session_sequences.get(session_id)


class MaliciousReportCountermeasure:
    """恶意举报反制系统"""
    
    def __init__(self):
        self.reporter_profiles: Dict[str, Dict[str, Any]] = {}
        self.verification_history: Dict[str, ReportVerification] = {}
        self.stats = {
            "total_reports": 0,
            "valid_reports": 0,
            "malicious_reports": 0,
            "reporters_punished": 0,
        }
    
    def verify_report(
        self,
        report_id: str,
        reporter_id: str,
        reported_content: str,
        reported_content_context: Dict[str, Any]
    ) -> ReportVerification:
        """验证举报"""
        self.stats["total_reports"] += 1
        
        content_violation_score = self._analyze_reported_content(
            reported_content, reported_content_context
        )
        
        reporter_history_score = self._analyze_reporter_history(reporter_id)
        
        if content_violation_score > 0.7:
            result = ReportVerificationResult.VALID_REPORT
            self.stats["valid_reports"] += 1
        elif content_violation_score < 0.3 and reporter_history_score > 0.5:
            result = ReportVerificationResult.MALICIOUS_REPORT
            self.stats["malicious_reports"] += 1
        elif reporter_history_score > 0.3:
            result = ReportVerificationResult.SUSPICIOUS_REPORT
        else:
            result = ReportVerificationResult.INVALID_REPORT
        
        recommendation = self._generate_recommendation(result, reporter_history_score)
        
        verification = ReportVerification(
            report_id=report_id,
            reporter_id=reporter_id,
            reported_content_hash=hashlib.sha256(reported_content.encode()).hexdigest()[:16],
            verification_result=result,
            reporter_history_score=reporter_history_score,
            content_violation_score=content_violation_score,
            recommendation=recommendation,
            evidence_ids=[]
        )
        
        self.verification_history[report_id] = verification
        self._update_reporter_profile(reporter_id, result)
        
        return verification
    
    def _analyze_reported_content(
        self,
        content: str,
        context: Dict[str, Any]
    ) -> float:
        """分析被举报内容"""
        violation_indicators = [
            "[违规内容标记A]",
            "[违规内容标记B]",
        ]
        
        score = 0.0
        for indicator in violation_indicators:
            if indicator in content:
                score += 0.3
        
        if context.get("was_blocked", False):
            score += 0.3
        
        return min(1.0, score)
    
    def _analyze_reporter_history(self, reporter_id: str) -> float:
        """分析举报人历史"""
        profile = self.reporter_profiles.get(reporter_id, {})
        
        suspicious_score = 0.0
        
        total_reports = profile.get("total_reports", 0)
        invalid_reports = profile.get("invalid_reports", 0)
        
        if total_reports > 0:
            invalid_ratio = invalid_reports / total_reports
            suspicious_score += invalid_ratio * 0.5
        
        if profile.get("has_violation_history", False):
            suspicious_score += 0.3
        
        if profile.get("previous_malicious_report", False):
            suspicious_score += 0.4
        
        return min(1.0, suspicious_score)
    
    def _generate_recommendation(
        self,
        result: ReportVerificationResult,
        reporter_score: float
    ) -> str:
        """生成建议"""
        if result == ReportVerificationResult.VALID_REPORT:
            return "举报有效，建议处理被举报内容"
        elif result == ReportVerificationResult.MALICIOUS_REPORT:
            return "检测到恶意举报，建议对举报人进行处罚"
        elif result == ReportVerificationResult.SUSPICIOUS_REPORT:
            return "举报可疑，建议人工复核"
        else:
            return "举报无效，驳回处理"
    
    def _update_reporter_profile(
        self,
        reporter_id: str,
        result: ReportVerificationResult
    ):
        """更新举报人画像"""
        if reporter_id not in self.reporter_profiles:
            self.reporter_profiles[reporter_id] = {
                "total_reports": 0,
                "valid_reports": 0,
                "invalid_reports": 0,
                "malicious_reports": 0,
                "has_violation_history": False,
                "previous_malicious_report": False,
            }
        
        profile = self.reporter_profiles[reporter_id]
        profile["total_reports"] += 1
        
        if result == ReportVerificationResult.VALID_REPORT:
            profile["valid_reports"] += 1
        elif result == ReportVerificationResult.INVALID_REPORT:
            profile["invalid_reports"] += 1
        elif result == ReportVerificationResult.MALICIOUS_REPORT:
            profile["malicious_reports"] += 1
            profile["previous_malicious_report"] = True
    
    def punish_malicious_reporter(
        self,
        reporter_id: str,
        offense_count: int
    ) -> Dict[str, Any]:
        """处罚恶意举报人"""
        profile = self.reporter_profiles.get(reporter_id, {})
        punishment = {
            "reporter_id": reporter_id,
            "action": "warning",
            "duration": 0,
            "reason": ""
        }
        
        if offense_count == 1:
            punishment["action"] = "warning"
            punishment["reason"] = "首次可疑举报，警告"
        elif offense_count == 2:
            punishment["action"] = "temp_freeze"
            punishment["duration"] = 86400
            punishment["reason"] = "二次可疑举报，临时冻结24小时"
        else:
            punishment["action"] = "permanent_ban"
            punishment["reason"] = "多次恶意举报，永久封禁"
            profile["is_blacklisted"] = True
        
        self.stats["reporters_punished"] += 1
        
        return punishment


class EvidenceManager:
    """证据管理器"""
    
    def __init__(self):
        self.evidence_records: Dict[str, EvidenceRecord] = {}
        self.user_evidence_index: Dict[str, List[str]] = defaultdict(list)
        self.stats = {
            "total_evidence": 0,
            "by_type": defaultdict(int),
        }
    
    def record_evidence(
        self,
        user_id: str,
        event_type: str,
        input_content: str,
        detection_result: DetectionResult,
        action_taken: str,
        session_id: str = "",
        context: Dict[str, Any] = None
    ) -> EvidenceRecord:
        """记录证据"""
        evidence_id = f"evd_{int(time.time())}_{hashlib.md5(input_content.encode()).hexdigest()[:8]}"
        
        evidence = EvidenceRecord(
            evidence_id=evidence_id,
            user_id=user_id,
            event_type=event_type,
            input_hash=hashlib.sha256(input_content.encode()).hexdigest(),
            detection_result={
                "detected": detection_result.detected,
                "types": [t.value for t in detection_result.detection_types],
                "risk_score": detection_result.risk_score,
                "action": detection_result.action.value,
            },
            action_taken=action_taken,
            timestamp=datetime.now(),
            session_id=session_id,
            context=context or {}
        )
        
        self.evidence_records[evidence_id] = evidence
        self.user_evidence_index[user_id].append(evidence_id)
        self.stats["total_evidence"] += 1
        self.stats["by_type"][event_type] += 1
        
        return evidence
    
    def get_user_evidence(self, user_id: str) -> List[EvidenceRecord]:
        """获取用户证据"""
        evidence_ids = self.user_evidence_index.get(user_id, [])
        return [self.evidence_records[eid] for eid in evidence_ids if eid in self.evidence_records]
    
    def export_for_audit(
        self,
        user_id: str,
        format: str = "dict"
    ) -> Dict[str, Any]:
        """导出审计证据"""
        evidence_list = self.get_user_evidence(user_id)
        
        return {
            "user_id": user_id,
            "evidence_count": len(evidence_list),
            "records": [
                {
                    "evidence_id": e.evidence_id,
                    "event_type": e.event_type,
                    "input_hash": e.input_hash[:16],
                    "action_taken": e.action_taken,
                    "timestamp": e.timestamp.isoformat(),
                }
                for e in evidence_list
            ]
        }


class DiscriminationCountermeasureSystem:
    """歧视性言论识别反制系统主控"""
    
    def __init__(self):
        self.pattern_detector = DiscriminationPatternDetector()
        self.sequence_analyzer = BehaviorSequenceAnalyzer()
        self.report_countermeasure = MaliciousReportCountermeasure()
        self.evidence_manager = EvidenceManager()
        
        self.user_profiles: Dict[str, UserRiskProfileExtended] = {}
        self.blacklist: Set[str] = set()
        
        self.time_windows = {
            "short_term": timedelta(minutes=15),
            "medium_term": timedelta(hours=24),
            "long_term": timedelta(days=30),
        }
    
    def process_input(
        self,
        user_id: str,
        content: str,
        session_id: str
    ) -> Dict[str, Any]:
        """处理输入"""
        if user_id in self.blacklist:
            return {
                "blocked": True,
                "reason": "user_blacklisted",
                "message": "您的账号已被封禁"
            }
        
        detection_result = self.pattern_detector.detect(content)
        
        profile = self._get_or_create_profile(user_id)
        
        self.sequence_analyzer.record_event(
            session_id=session_id,
            user_id=user_id,
            event_type="input",
            content=content,
            risk_score=detection_result.risk_score
        )
        
        if detection_result.detected:
            return self._handle_violation(
                user_id, content, session_id, detection_result, profile
            )
        
        return {
            "blocked": False,
            "risk_score": detection_result.risk_score,
            "message": "输入正常"
        }
    
    def _get_or_create_profile(self, user_id: str) -> UserRiskProfileExtended:
        """获取或创建用户画像"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = UserRiskProfileExtended(
                user_id=user_id,
                discrimination_attempts=0,
                inducing_attempts=0,
                total_risk_score=0.0,
                last_violation_time=None,
                violation_history=[],
                report_history=[],
                is_blacklisted=False
            )
        return self.user_profiles[user_id]
    
    def _handle_violation(
        self,
        user_id: str,
        content: str,
        session_id: str,
        detection_result: DetectionResult,
        profile: UserRiskProfileExtended
    ) -> Dict[str, Any]:
        """处理违规"""
        now = datetime.now()
        
        violation_count = self._count_recent_violations(user_id, now)
        
        action = self._determine_action(violation_count, detection_result.risk_score)
        
        profile.total_risk_score += detection_result.risk_score
        profile.last_violation_time = now
        profile.violation_history.append({
            "timestamp": now.isoformat(),
            "risk_score": detection_result.risk_score,
            "types": [t.value for t in detection_result.detection_types],
            "action": action.value
        })
        
        for dt in detection_result.detection_types:
            if dt in [DetectionType.REGIONAL_DISCRIMINATION, DetectionType.RACIAL_DISCRIMINATION,
                      DetectionType.RELIGIOUS_OFFENSE, DetectionType.GENDER_DISCRIMINATION]:
                profile.discrimination_attempts += 1
            elif dt == DetectionType.INDUCING_LANGUAGE:
                profile.inducing_attempts += 1
        
        self.evidence_manager.record_evidence(
            user_id=user_id,
            event_type="violation",
            input_content=content,
            detection_result=detection_result,
            action_taken=action.value,
            session_id=session_id
        )
        
        if action == RiskAction.PERMANENT_BAN:
            profile.is_blacklisted = True
            profile.blacklist_reason = "多次违规"
            self.blacklist.add(user_id)
        
        return {
            "blocked": True,
            "action": action.value,
            "risk_score": detection_result.risk_score,
            "message": self._generate_rejection_message(violation_count),
            "violation_count": violation_count
        }
    
    def _count_recent_violations(self, user_id: str, now: datetime) -> int:
        """计算近期违规次数"""
        profile = self.user_profiles.get(user_id)
        if not profile:
            return 0
        
        count = 0
        for v in profile.violation_history:
            v_time = datetime.fromisoformat(v["timestamp"])
            if now - v_time < self.time_windows["medium_term"]:
                count += 1
        
        return count
    
    def _determine_action(self, violation_count: int, risk_score: float) -> RiskAction:
        """确定行动"""
        if risk_score >= 80 or violation_count >= 3:
            return RiskAction.PERMANENT_BAN
        elif risk_score >= 50 or violation_count >= 2:
            return RiskAction.TEMP_FREEZE
        elif risk_score >= 20:
            return RiskAction.REJECT_REPLY
        else:
            return RiskAction.LOG_ONLY
    
    def _generate_rejection_message(self, violation_count: int) -> str:
        """生成拒绝消息"""
        if violation_count == 1:
            return "您的输入包含可能违规的内容，请重新表述"
        elif violation_count == 2:
            return "多次违规，账号已临时限制"
        else:
            return "账号因多次违规已被封禁"
    
    def verify_report(
        self,
        report_id: str,
        reporter_id: str,
        reported_content: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """验证举报"""
        verification = self.report_countermeasure.verify_report(
            report_id=report_id,
            reporter_id=reporter_id,
            reported_content=reported_content,
            reported_content_context=context
        )
        
        if verification.verification_result == ReportVerificationResult.MALICIOUS_REPORT:
            profile = self.report_countermeasure.reporter_profiles.get(reporter_id, {})
            offense_count = profile.get("malicious_reports", 1)
            
            punishment = self.report_countermeasure.punish_malicious_reporter(
                reporter_id, offense_count
            )
            
            return {
                "verification": verification.__dict__,
                "punishment": punishment
            }
        
        return {
            "verification": {
                "report_id": verification.report_id,
                "result": verification.verification_result.value,
                "recommendation": verification.recommendation
            }
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "pattern_detector": self.pattern_detector.stats,
            "sequence_analyzer": self.sequence_analyzer.stats,
            "report_countermeasure": self.report_countermeasure.stats,
            "evidence_manager": self.evidence_manager.stats,
            "total_users": len(self.user_profiles),
            "blacklisted_users": len(self.blacklist),
        }
