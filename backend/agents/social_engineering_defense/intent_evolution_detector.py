"""
对话意图演化检测智能体
负责分析多轮对话中用户意图的演化轨迹，检测异常意图变化
"""
import asyncio
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class IntentType(Enum):
    """意图类型枚举"""
    INFORMATION_QUERY = "information_query"
    PROPERTY_VALUATION = "property_valuation"
    DOCUMENT_REQUEST = "document_request"
    ACCOUNT_MANAGEMENT = "account_management"
    FINANCIAL_OPERATION = "financial_operation"
    DATA_EXPORT = "data_export"
    PERMISSION_REQUEST = "permission_request"
    SYSTEM_CONFIGURATION = "system_configuration"
    SOCIAL_ENGINEERING = "social_engineering"
    UNKNOWN = "unknown"


class EvolutionPattern(Enum):
    """意图演化模式"""
    NORMAL = "normal"
    SUDDEN_SHIFT = "sudden_shift"
    GRADUAL_ESCALATION = "gradual_escalation"
    CIRCULAR_RETURN = "circular_return"
    PROBING_PATTERN = "probing_pattern"
    ATTACK_INDICATOR = "attack_indicator"


@dataclass
class IntentRecord:
    """意图记录"""
    intent_type: IntentType
    confidence: float
    timestamp: datetime
    raw_input: str
    sensitivity_level: str
    keywords: List[str] = field(default_factory=list)


@dataclass
class IntentEvolutionResult:
    """意图演化检测结果"""
    session_id: str
    evolution_pattern: EvolutionPattern
    intent_sequence: List[IntentType]
    risk_score: float
    detected_anomalies: List[str]
    attack_probability: float
    recommendation: str
    intent_path: List[Dict[str, Any]] = field(default_factory=list)


class IntentEvolutionDetectorAgent:
    """对话意图演化检测智能体"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.name = "IntentEvolutionDetectorAgent"
        self.config = config or {}
        self.intent_keywords = self._init_intent_keywords()
        self.sensitivity_mapping = self._init_sensitivity_mapping()
        self.attack_patterns = self._init_attack_patterns()
        self.session_intents: Dict[str, List[IntentRecord]] = defaultdict(list)
        self.stats = {
            "total_sessions": 0,
            "total_intents_analyzed": 0,
            "anomalies_detected": 0,
            "attacks_detected": 0,
            "evolution_patterns": defaultdict(int),
        }
    
    def _init_intent_keywords(self) -> Dict[IntentType, List[str]]:
        """初始化意图关键词"""
        return {
            IntentType.INFORMATION_QUERY: [
                "查询", "了解", "咨询", "请问", "想知道", "信息",
                "房价", "政策", "流程", "规定"
            ],
            IntentType.PROPERTY_VALUATION: [
                "估值", "评估", "价值", "多少钱", "价格", "市值",
                "房产价值", "不动产评估"
            ],
            IntentType.DOCUMENT_REQUEST: [
                "下载", "导出", "报告", "文档", "证明", "证书",
                "合同", "文件", "打印"
            ],
            IntentType.ACCOUNT_MANAGEMENT: [
                "密码", "账号", "登录", "注册", "修改", "绑定",
                "解绑", "注销", "设置"
            ],
            IntentType.FINANCIAL_OPERATION: [
                "转账", "付款", "退款", "充值", "提现", "资金",
                "银行", "账户"
            ],
            IntentType.DATA_EXPORT: [
                "批量导出", "全部数据", "数据库", "备份", "下载全部",
                "数据迁移"
            ],
            IntentType.PERMISSION_REQUEST: [
                "权限", "授权", "管理员", "超级用户", "访问", "越权"
            ],
            IntentType.SYSTEM_CONFIGURATION: [
                "配置", "设置", "规则", "系统", "参数", "修改规则"
            ],
            IntentType.SOCIAL_ENGINEERING: [
                "紧急", "立即", "马上", "验证", "确认", "客服",
                "管理员", "内部", "测试", "忽略", "忘记"
            ],
        }
    
    def _init_sensitivity_mapping(self) -> Dict[IntentType, str]:
        """初始化敏感度映射"""
        return {
            IntentType.INFORMATION_QUERY: "low",
            IntentType.PROPERTY_VALUATION: "low",
            IntentType.DOCUMENT_REQUEST: "medium",
            IntentType.ACCOUNT_MANAGEMENT: "high",
            IntentType.FINANCIAL_OPERATION: "critical",
            IntentType.DATA_EXPORT: "critical",
            IntentType.PERMISSION_REQUEST: "critical",
            IntentType.SYSTEM_CONFIGURATION: "critical",
            IntentType.SOCIAL_ENGINEERING: "critical",
            IntentType.UNKNOWN: "low",
        }
    
    def _init_attack_patterns(self) -> List[Dict]:
        """初始化攻击模式"""
        return [
            {
                "name": "trust_then_attack",
                "description": "先建立信任后攻击",
                "sequence": [
                    IntentType.INFORMATION_QUERY,
                    IntentType.PROPERTY_VALUATION,
                    IntentType.FINANCIAL_OPERATION
                ],
                "risk_multiplier": 2.0
            },
            {
                "name": "probing_escalation",
                "description": "探测式升级",
                "sequence": [
                    IntentType.INFORMATION_QUERY,
                    IntentType.PERMISSION_REQUEST,
                    IntentType.SYSTEM_CONFIGURATION
                ],
                "risk_multiplier": 2.5
            },
            {
                "name": "urgency_exploitation",
                "description": "紧迫感利用",
                "indicators": [
                    IntentType.SOCIAL_ENGINEERING,
                    IntentType.FINANCIAL_OPERATION
                ],
                "risk_multiplier": 3.0
            },
            {
                "name": "data_harvesting",
                "description": "数据收集攻击",
                "sequence": [
                    IntentType.INFORMATION_QUERY,
                    IntentType.DOCUMENT_REQUEST,
                    IntentType.DATA_EXPORT
                ],
                "risk_multiplier": 2.0
            },
        ]
    
    async def initialize(self) -> bool:
        """初始化智能体"""
        await asyncio.sleep(0.1)
        return True
    
    def classify_intent(self, text: str) -> Tuple[IntentType, float, List[str]]:
        """分类意图"""
        text_lower = text.lower()
        scores: Dict[IntentType, float] = defaultdict(float)
        matched_keywords: Dict[IntentType, List[str]] = defaultdict(list)
        
        for intent_type, keywords in self.intent_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    scores[intent_type] += 1
                    matched_keywords[intent_type].append(keyword)
        
        if not scores:
            return IntentType.UNKNOWN, 0.3, []
        
        max_intent = max(scores.keys(), key=lambda x: scores[x])
        total_matches = scores[max_intent]
        confidence = min(0.95, 0.5 + total_matches * 0.1)
        
        return max_intent, confidence, matched_keywords[max_intent]
    
    def record_intent(self, session_id: str, text: str) -> IntentRecord:
        """记录意图"""
        intent_type, confidence, keywords = self.classify_intent(text)
        
        record = IntentRecord(
            intent_type=intent_type,
            confidence=confidence,
            timestamp=datetime.now(),
            raw_input=text[:200],
            sensitivity_level=self.sensitivity_mapping[intent_type],
            keywords=keywords
        )
        
        self.session_intents[session_id].append(record)
        self.stats["total_intents_analyzed"] += 1
        
        return record
    
    def analyze_evolution(self, session_id: str) -> IntentEvolutionResult:
        """分析意图演化"""
        intents = self.session_intents.get(session_id, [])
        
        if len(intents) < 2:
            return IntentEvolutionResult(
                session_id=session_id,
                evolution_pattern=EvolutionPattern.NORMAL,
                intent_sequence=[i.intent_type for i in intents],
                risk_score=0.0,
                detected_anomalies=[],
                attack_probability=0.0,
                recommendation="继续监控"
            )
        
        intent_sequence = [i.intent_type for i in intents]
        sensitivity_sequence = [i.sensitivity_level for i in intents]
        
        evolution_pattern = self._detect_evolution_pattern(
            intent_sequence, sensitivity_sequence
        )
        
        risk_score = self._calculate_risk_score(
            intent_sequence, sensitivity_sequence, evolution_pattern
        )
        
        anomalies = self._detect_anomalies(intents)
        attack_probability = self._calculate_attack_probability(
            intent_sequence, evolution_pattern, anomalies
        )
        
        intent_path = [
            {
                "intent": i.intent_type.value,
                "sensitivity": i.sensitivity_level,
                "timestamp": i.timestamp.isoformat(),
                "keywords": i.keywords
            }
            for i in intents
        ]
        
        self.stats["evolution_patterns"][evolution_pattern.value] += 1
        
        if evolution_pattern in [EvolutionPattern.ATTACK_INDICATOR, EvolutionPattern.PROBING_PATTERN]:
            self.stats["attacks_detected"] += 1
        
        if anomalies:
            self.stats["anomalies_detected"] += 1
        
        return IntentEvolutionResult(
            session_id=session_id,
            evolution_pattern=evolution_pattern,
            intent_sequence=intent_sequence,
            risk_score=risk_score,
            detected_anomalies=anomalies,
            attack_probability=attack_probability,
            recommendation=self._generate_recommendation(evolution_pattern, risk_score),
            intent_path=intent_path
        )
    
    def _detect_evolution_pattern(
        self, 
        intent_sequence: List[IntentType],
        sensitivity_sequence: List[str]
    ) -> EvolutionPattern:
        """检测演化模式"""
        sensitivity_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        
        if IntentType.SOCIAL_ENGINEERING in intent_sequence:
            return EvolutionPattern.ATTACK_INDICATOR
        
        if len(intent_sequence) >= 3:
            for i in range(len(intent_sequence) - 2):
                if intent_sequence[i] == intent_sequence[i + 2]:
                    if intent_sequence[i + 1] != intent_sequence[i]:
                        return EvolutionPattern.CIRCULAR_RETURN
        
        sensitivity_values = [sensitivity_order.get(s, 0) for s in sensitivity_sequence]
        
        if len(sensitivity_values) >= 2:
            last_jump = abs(sensitivity_values[-1] - sensitivity_values[-2])
            if last_jump >= 2:
                return EvolutionPattern.SUDDEN_SHIFT
        
        if all(
            sensitivity_values[i] <= sensitivity_values[i + 1]
            for i in range(len(sensitivity_values) - 1)
        ) and sensitivity_values[-1] >= 2:
            return EvolutionPattern.GRADUAL_ESCALATION
        
        if self._match_attack_pattern(intent_sequence):
            return EvolutionPattern.PROBING_PATTERN
        
        return EvolutionPattern.NORMAL
    
    def _match_attack_pattern(self, intent_sequence: List[IntentType]) -> bool:
        """匹配攻击模式"""
        for pattern in self.attack_patterns:
            if "sequence" in pattern:
                pattern_seq = pattern["sequence"]
                for i in range(len(intent_sequence) - len(pattern_seq) + 1):
                    if intent_sequence[i:i + len(pattern_seq)] == pattern_seq:
                        return True
        return False
    
    def _calculate_risk_score(
        self,
        intent_sequence: List[IntentType],
        sensitivity_sequence: List[str],
        evolution_pattern: EvolutionPattern
    ) -> float:
        """计算风险分数"""
        base_score = 0.0
        
        critical_count = sensitivity_sequence.count("critical")
        high_count = sensitivity_sequence.count("high")
        base_score += critical_count * 0.3 + high_count * 0.15
        
        pattern_scores = {
            EvolutionPattern.NORMAL: 0.0,
            EvolutionPattern.CIRCULAR_RETURN: 0.2,
            EvolutionPattern.GRADUAL_ESCALATION: 0.4,
            EvolutionPattern.SUDDEN_SHIFT: 0.5,
            EvolutionPattern.PROBING_PATTERN: 0.7,
            EvolutionPattern.ATTACK_INDICATOR: 0.9,
        }
        base_score += pattern_scores.get(evolution_pattern, 0.0)
        
        for pattern in self.attack_patterns:
            if "sequence" in pattern:
                pattern_seq = pattern["sequence"]
                for i in range(len(intent_sequence) - len(pattern_seq) + 1):
                    if intent_sequence[i:i + len(pattern_seq)] == pattern_seq:
                        base_score *= pattern.get("risk_multiplier", 1.0)
        
        return min(1.0, base_score)
    
    def _detect_anomalies(self, intents: List[IntentRecord]) -> List[str]:
        """检测异常"""
        anomalies = []
        
        for i, intent in enumerate(intents):
            if intent.intent_type == IntentType.SOCIAL_ENGINEERING:
                anomalies.append(f"第{i + 1}轮检测到社会工程学特征")
            
            if intent.confidence < 0.4:
                anomalies.append(f"第{i + 1}轮意图置信度过低: {intent.confidence:.2f}")
        
        if len(intents) >= 3:
            recent_intents = intents[-3:]
            if all(i.sensitivity_level in ["high", "critical"] for i in recent_intents):
                anomalies.append("连续3轮高敏感度意图")
        
        return anomalies
    
    def _calculate_attack_probability(
        self,
        intent_sequence: List[IntentType],
        evolution_pattern: EvolutionPattern,
        anomalies: List[str]
    ) -> float:
        """计算攻击概率"""
        base_prob = {
            EvolutionPattern.NORMAL: 0.1,
            EvolutionPattern.CIRCULAR_RETURN: 0.3,
            EvolutionPattern.GRADUAL_ESCALATION: 0.5,
            EvolutionPattern.SUDDEN_SHIFT: 0.6,
            EvolutionPattern.PROBING_PATTERN: 0.75,
            EvolutionPattern.ATTACK_INDICATOR: 0.9,
        }.get(evolution_pattern, 0.1)
        
        anomaly_penalty = len(anomalies) * 0.05
        
        return min(1.0, base_prob + anomaly_penalty)
    
    def _generate_recommendation(
        self, 
        evolution_pattern: EvolutionPattern,
        risk_score: float
    ) -> str:
        """生成建议"""
        if evolution_pattern == EvolutionPattern.ATTACK_INDICATOR:
            return "立即中断对话，触发安全验证"
        elif evolution_pattern == EvolutionPattern.PROBING_PATTERN:
            return "加强监控，准备触发多因素验证"
        elif evolution_pattern == EvolutionPattern.SUDDEN_SHIFT:
            return "注意意图突变，建议进行身份确认"
        elif evolution_pattern == EvolutionPattern.GRADUAL_ESCALATION:
            return "监控敏感操作，限制高风险行为"
        elif risk_score > 0.5:
            return "风险较高，建议人工介入"
        else:
            return "继续监控"
    
    def clear_session(self, session_id: str):
        """清除会话数据"""
        if session_id in self.session_intents:
            del self.session_intents[session_id]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "active_sessions": len(self.session_intents),
            "evolution_patterns": dict(self.stats["evolution_patterns"]),
        }
