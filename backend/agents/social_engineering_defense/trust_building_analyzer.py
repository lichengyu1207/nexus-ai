"""
信任建立策略分析智能体
负责分析用户是否在使用社会工程中的信任建立技巧
"""
import asyncio
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class TrustTechnique(Enum):
    """信任建立技巧类型"""
    SIMILARITY_ATTRACTION = "similarity_attraction"
    RECIPROCITY = "reciprocity"
    AUTHORITY_APPEAL = "authority_appeal"
    SCARCITY_CREATION = "scarcity_creation"
    SOCIAL_PROOF = "social_proof"
    LIKING_BUILDING = "liking_building"
    COMMITMENT_CONSISTENCY = "commitment_consistency"
    NONE = "none"


class TrustRiskLevel(Enum):
    """信任风险等级"""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class TrustTechniqueInstance:
    """信任技巧实例"""
    technique: TrustTechnique
    text_segment: str
    confidence: float
    timestamp: datetime
    context: str
    indicators: List[str] = field(default_factory=list)


@dataclass
class TrustAnalysisResult:
    """信任分析结果"""
    session_id: str
    techniques_detected: List[TrustTechnique]
    technique_instances: List[TrustTechniqueInstance]
    risk_level: TrustRiskLevel
    trust_score: float
    attack_probability: float
    timing_analysis: Dict[str, Any]
    recommendations: List[str]
    warning_signals: List[str] = field(default_factory=list)


class TrustBuildingAnalyzerAgent:
    """信任建立策略分析智能体"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.name = "TrustBuildingAnalyzerAgent"
        self.config = config or {}
        self.technique_patterns = self._init_technique_patterns()
        self.suspicious_sequences = self._init_suspicious_sequences()
        self.session_techniques: Dict[str, List[TrustTechniqueInstance]] = defaultdict(list)
        self.session_sensitive_requests: Dict[str, List[datetime]] = defaultdict(list)
        self.stats = {
            "total_sessions": 0,
            "total_analyses": 0,
            "techniques_detected": defaultdict(int),
            "high_risk_sessions": 0,
            "attacks_prevented": 0,
        }
    
    def _init_technique_patterns(self) -> Dict[TrustTechnique, Dict]:
        """初始化信任技巧模式"""
        return {
            TrustTechnique.SIMILARITY_ATTRACTION: {
                "keywords": [
                    "我也是", "我也", "和我一样", "我们都是", "老乡",
                    "校友", "同行", "同龄", "同乡", "同岁",
                    "我也喜欢", "我也去过", "我也住", "共同"
                ],
                "patterns": [
                    r"我也?是.{1,10}的",
                    r"我们.{1,5}一样",
                    r"原来.{1,5}也是",
                    r"真巧.{1,10}一样",
                ],
                "risk_weight": 0.3,
                "description": "声称有共同经历、兴趣或背景"
            },
            TrustTechnique.RECIPROCITY: {
                "keywords": [
                    "免费", "赠送", "优惠", "福利", "帮忙",
                    "送你", "给你", "分享", "推荐", "建议",
                    "小礼物", "小意思", "不收钱"
                ],
                "patterns": [
                    r"免费.{1,10}你",
                    r"送你.{1,10}不用",
                    r"帮.{1,5}一下",
                    r"给你.{1,10}优惠",
                ],
                "risk_weight": 0.4,
                "description": "提供小恩惠换取信任"
            },
            TrustTechnique.AUTHORITY_APPEAL: {
                "keywords": [
                    "专家", "领导", "经理", "总监", "官方",
                    "认证", "授权", "内部", "专业", "资深",
                    "多年经验", "权威", "官方认证"
                ],
                "patterns": [
                    r"我是.{1,10}(专家|领导|经理)",
                    r"官方.{1,5}认证",
                    r"内部.{1,5}消息",
                    r"资深.{1,5}从业",
                ],
                "risk_weight": 0.5,
                "description": "冒充专家或权威人士"
            },
            TrustTechnique.SCARCITY_CREATION: {
                "keywords": [
                    "最后", "仅剩", "限时", "名额", "机会",
                    "错过", "不再", "唯一", "独家", "稀有",
                    "即将", "马上结束", "仅此一次"
                ],
                "patterns": [
                    r"最后.{1,5}名额",
                    r"仅剩.{1,5}个",
                    r"限时.{1,5}结束",
                    r"错过.{1,5}不再",
                ],
                "risk_weight": 0.4,
                "description": "制造机会稀缺假象"
            },
            TrustTechnique.SOCIAL_PROOF: {
                "keywords": [
                    "很多人", "大家都", "别人都", "其他人",
                    "好评", "推荐", "口碑", "成功案例",
                    "客户", "用户", "朋友推荐"
                ],
                "patterns": [
                    r"很多.{1,5}都",
                    r"大家都.{1,5}了",
                    r"成功.{1,5}案例",
                    r"客户.{1,5}好评",
                ],
                "risk_weight": 0.3,
                "description": "利用社会认同"
            },
            TrustTechnique.LIKING_BUILDING: {
                "keywords": [
                    "您真", "您太", "佩服", "欣赏", "厉害",
                    "专业", "聪明", "有眼光", "有品位",
                    "赞美", "夸奖", "您说得对"
                ],
                "patterns": [
                    r"您真.{1,5}(厉害|专业|聪明)",
                    r"佩服.{1,5}您",
                    r"有眼光",
                    r"有品位",
                ],
                "risk_weight": 0.25,
                "description": "通过赞美建立好感"
            },
            TrustTechnique.COMMITMENT_CONSISTENCY: {
                "keywords": [
                    "既然", "之前说", "答应", "承诺", "确认",
                    "您说过", "您同意", "您认可", "您选择"
                ],
                "patterns": [
                    r"既然.{1,5}同意",
                    r"您之前.{1,5}说",
                    r"您答应.{1,5}了",
                    r"您确认.{1,5}过",
                ],
                "risk_weight": 0.45,
                "description": "利用一致性压力"
            },
        }
    
    def _init_suspicious_sequences(self) -> List[Dict]:
        """初始化可疑序列"""
        return [
            {
                "sequence": [
                    TrustTechnique.SIMILARITY_ATTRACTION,
                    TrustTechnique.LIKING_BUILDING,
                    TrustTechnique.RECIPROCITY
                ],
                "risk_multiplier": 2.5,
                "description": "建立关系后提供恩惠"
            },
            {
                "sequence": [
                    TrustTechnique.AUTHORITY_APPEAL,
                    TrustTechnique.SCARCITY_CREATION
                ],
                "risk_multiplier": 2.0,
                "description": "权威加稀缺施压"
            },
            {
                "sequence": [
                    TrustTechnique.SOCIAL_PROOF,
                    TrustTechnique.SCARCITY_CREATION
                ],
                "risk_multiplier": 1.8,
                "description": "社会认同加稀缺"
            },
            {
                "sequence": [
                    TrustTechnique.COMMITMENT_CONSISTENCY,
                    TrustTechnique.AUTHORITY_APPEAL
                ],
                "risk_multiplier": 2.2,
                "description": "承诺一致性加权威"
            },
        ]
    
    async def initialize(self) -> bool:
        """初始化智能体"""
        await asyncio.sleep(0.1)
        return True
    
    def detect_techniques(self, text: str, context: str = "") -> List[TrustTechniqueInstance]:
        """检测信任建立技巧"""
        instances = []
        text_lower = text.lower()
        
        for technique, pattern_data in self.technique_patterns.items():
            confidence = 0.0
            indicators = []
            
            for keyword in pattern_data["keywords"]:
                if keyword in text_lower:
                    confidence += 0.2
                    indicators.append(f"关键词: {keyword}")
            
            for pattern in pattern_data["patterns"]:
                if re.search(pattern, text_lower):
                    confidence += 0.3
                    indicators.append(f"模式匹配: {pattern}")
            
            if confidence > 0:
                instance = TrustTechniqueInstance(
                    technique=technique,
                    text_segment=text[:100],
                    confidence=min(0.95, confidence),
                    timestamp=datetime.now(),
                    context=context,
                    indicators=indicators
                )
                instances.append(instance)
                self.stats["techniques_detected"][technique.value] += 1
        
        return instances
    
    def record_technique(
        self, 
        session_id: str, 
        text: str, 
        context: str = ""
    ) -> List[TrustTechniqueInstance]:
        """记录信任技巧"""
        instances = self.detect_techniques(text, context)
        self.session_techniques[session_id].extend(instances)
        self.stats["total_analyses"] += 1
        return instances
    
    def record_sensitive_request(self, session_id: str):
        """记录敏感请求"""
        self.session_sensitive_requests[session_id].append(datetime.now())
    
    def analyze_trust_building(self, session_id: str) -> TrustAnalysisResult:
        """分析信任建立策略"""
        techniques = self.session_techniques.get(session_id, [])
        sensitive_requests = self.session_sensitive_requests.get(session_id, [])
        
        if not techniques:
            return TrustAnalysisResult(
                session_id=session_id,
                techniques_detected=[],
                technique_instances=[],
                risk_level=TrustRiskLevel.SAFE,
                trust_score=0.0,
                attack_probability=0.0,
                timing_analysis={},
                recommendations=["正常对话，无需特别关注"]
            )
        
        techniques_detected = list(set(t.technique for t in techniques))
        
        timing_analysis = self._analyze_timing(techniques, sensitive_requests)
        
        risk_level = self._assess_risk_level(techniques, timing_analysis)
        
        trust_score = self._calculate_trust_score(techniques, timing_analysis)
        
        attack_probability = self._calculate_attack_probability(
            techniques, timing_analysis, sensitive_requests
        )
        
        warning_signals = self._generate_warning_signals(techniques, timing_analysis)
        
        recommendations = self._generate_recommendations(risk_level, warning_signals)
        
        if risk_level in [TrustRiskLevel.HIGH, TrustRiskLevel.CRITICAL]:
            self.stats["high_risk_sessions"] += 1
        
        return TrustAnalysisResult(
            session_id=session_id,
            techniques_detected=techniques_detected,
            technique_instances=techniques,
            risk_level=risk_level,
            trust_score=trust_score,
            attack_probability=attack_probability,
            timing_analysis=timing_analysis,
            recommendations=recommendations,
            warning_signals=warning_signals
        )
    
    def _analyze_timing(
        self, 
        techniques: List[TrustTechniqueInstance],
        sensitive_requests: List[datetime]
    ) -> Dict[str, Any]:
        """分析时机"""
        if not techniques:
            return {}
        
        technique_timestamps: Dict[TrustTechnique, List[datetime]] = defaultdict(list)
        for t in techniques:
            technique_timestamps[t.technique].append(t.timestamp)
        
        technique_density = len(techniques) / max(1, len(technique_timestamps))
        
        pre_request_techniques = 0
        if sensitive_requests:
            first_request = min(sensitive_requests)
            pre_request_techniques = sum(
                1 for t in techniques if t.timestamp < first_request
            )
        
        technique_sequence = [t.technique for t in sorted(techniques, key=lambda x: x.timestamp)]
        sequence_match = self._match_suspicious_sequence(technique_sequence)
        
        return {
            "total_techniques": len(techniques),
            "unique_techniques": len(technique_timestamps),
            "technique_density": technique_density,
            "pre_request_techniques": pre_request_techniques,
            "sensitive_request_count": len(sensitive_requests),
            "sequence_match": sequence_match,
            "technique_sequence": [t.value for t in technique_sequence],
        }
    
    def _match_suspicious_sequence(
        self, 
        technique_sequence: List[TrustTechnique]
    ) -> Optional[Dict]:
        """匹配可疑序列"""
        for suspicious in self.suspicious_sequences:
            seq = suspicious["sequence"]
            for i in range(len(technique_sequence) - len(seq) + 1):
                if technique_sequence[i:i + len(seq)] == seq:
                    return suspicious
        return None
    
    def _assess_risk_level(
        self, 
        techniques: List[TrustTechniqueInstance],
        timing_analysis: Dict[str, Any]
    ) -> TrustRiskLevel:
        """评估风险等级"""
        risk_score = 0.0
        
        for t in techniques:
            pattern_data = self.technique_patterns.get(t.technique, {})
            risk_score += pattern_data.get("risk_weight", 0.3) * t.confidence
        
        if timing_analysis.get("sequence_match"):
            risk_score *= timing_analysis["sequence_match"].get("risk_multiplier", 1.5)
        
        if timing_analysis.get("pre_request_techniques", 0) >= 3:
            risk_score *= 1.5
        
        if timing_analysis.get("technique_density", 0) > 2:
            risk_score *= 1.3
        
        if risk_score < 0.3:
            return TrustRiskLevel.SAFE
        elif risk_score < 0.5:
            return TrustRiskLevel.LOW
        elif risk_score < 0.7:
            return TrustRiskLevel.MEDIUM
        elif risk_score < 0.9:
            return TrustRiskLevel.HIGH
        else:
            return TrustRiskLevel.CRITICAL
    
    def _calculate_trust_score(
        self, 
        techniques: List[TrustTechniqueInstance],
        timing_analysis: Dict[str, Any]
    ) -> float:
        """计算信任分数 (越高越可疑)"""
        base_score = len(techniques) * 0.1
        
        unique_techniques = len(set(t.technique for t in techniques))
        base_score += unique_techniques * 0.15
        
        if timing_analysis.get("sequence_match"):
            base_score += 0.3
        
        return min(1.0, base_score)
    
    def _calculate_attack_probability(
        self,
        techniques: List[TrustTechniqueInstance],
        timing_analysis: Dict[str, Any],
        sensitive_requests: List[datetime]
    ) -> float:
        """计算攻击概率"""
        if not techniques:
            return 0.0
        
        base_prob = 0.1
        
        high_risk_techniques = [
            TrustTechnique.AUTHORITY_APPEAL,
            TrustTechnique.COMMITMENT_CONSISTENCY
        ]
        for t in techniques:
            if t.technique in high_risk_techniques:
                base_prob += 0.15
        
        if timing_analysis.get("sequence_match"):
            base_prob += 0.25
        
        if sensitive_requests and timing_analysis.get("pre_request_techniques", 0) >= 2:
            base_prob += 0.2
        
        return min(1.0, base_prob)
    
    def _generate_warning_signals(
        self, 
        techniques: List[TrustTechniqueInstance],
        timing_analysis: Dict[str, Any]
    ) -> List[str]:
        """生成警告信号"""
        signals = []
        
        technique_counts: Dict[TrustTechnique, int] = defaultdict(int)
        for t in techniques:
            technique_counts[t.technique] += 1
        
        for technique, count in technique_counts.items():
            if count >= 3:
                signals.append(f"频繁使用{technique.value}技巧({count}次)")
        
        if timing_analysis.get("sequence_match"):
            match = timing_analysis["sequence_match"]
            signals.append(f"检测到可疑序列: {match['description']}")
        
        if timing_analysis.get("technique_density", 0) > 2:
            signals.append("信任技巧密度异常高")
        
        if timing_analysis.get("pre_request_techniques", 0) >= 3:
            signals.append("敏感请求前密集使用信任技巧")
        
        return signals
    
    def _generate_recommendations(
        self, 
        risk_level: TrustRiskLevel,
        warning_signals: List[str]
    ) -> List[str]:
        """生成建议"""
        recommendations = []
        
        if risk_level == TrustRiskLevel.CRITICAL:
            recommendations.append("立即中断对话，进行身份验证")
            recommendations.append("通知安全团队介入")
        elif risk_level == TrustRiskLevel.HIGH:
            recommendations.append("加强身份验证")
            recommendations.append("限制敏感操作")
            recommendations.append("人工审核介入")
        elif risk_level == TrustRiskLevel.MEDIUM:
            recommendations.append("增加验证步骤")
            recommendations.append("监控后续行为")
        elif risk_level == TrustRiskLevel.LOW:
            recommendations.append("保持警惕，继续监控")
        else:
            recommendations.append("正常对话，无需特别关注")
        
        if warning_signals:
            recommendations.append(f"警告信号: {'; '.join(warning_signals[:3])}")
        
        return recommendations
    
    def clear_session(self, session_id: str):
        """清除会话数据"""
        if session_id in self.session_techniques:
            del self.session_techniques[session_id]
        if session_id in self.session_sensitive_requests:
            del self.session_sensitive_requests[session_id]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "active_sessions": len(self.session_techniques),
            "techniques_detected": dict(self.stats["techniques_detected"]),
        }
