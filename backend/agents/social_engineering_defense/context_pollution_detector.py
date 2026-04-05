"""
上下文污染检测智能体
负责检测攻击者是否在污染智能体的上下文记忆
"""
import asyncio
import hashlib
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple


class PollutionType(Enum):
    """污染类型"""
    FALSE_FACT_INJECTION = "false_fact_injection"
    RULE_OVERRIDE = "rule_override"
    MEMORY_TAMPERING = "memory_tampering"
    CONTEXT_CONFUSION = "context_confusion"
    ROLE_CONFUSION = "role_confusion"
    AUTHORITY_CLAIM = "authority_claim"
    NONE = "none"


class PollutionSeverity(Enum):
    """污染严重程度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ContextFact:
    """上下文事实"""
    content: str
    source: str
    timestamp: datetime
    confidence: float
    verification_status: str
    hash: str = field(default="")
    
    def __post_init__(self):
        if not self.hash:
            self.hash = hashlib.md5(self.content.encode()).hexdigest()[:16]


@dataclass
class PollutionInstance:
    """污染实例"""
    pollution_type: PollutionType
    content: str
    severity: PollutionSeverity
    confidence: float
    timestamp: datetime
    indicators: List[str]
    source_context: str
    recommendation: str


@dataclass
class PollutionDetectionResult:
    """污染检测结果"""
    session_id: str
    is_polluted: bool
    pollution_instances: List[PollutionInstance]
    affected_facts: List[str]
    overall_severity: PollutionSeverity
    cleanup_required: bool
    trust_impact: float
    recommendations: List[str]


class ContextPollutionDetectorAgent:
    """上下文污染检测智能体"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.name = "ContextPollutionDetectorAgent"
        self.config = config or {}
        self.pollution_patterns = self._init_pollution_patterns()
        self.authorized_rules: Set[str] = set()
        self.session_contexts: Dict[str, List[ContextFact]] = defaultdict(list)
        self.session_pollution: Dict[str, List[PollutionInstance]] = defaultdict(list)
        self.fact_verification_cache: Dict[str, bool] = {}
        self.stats = {
            "total_checks": 0,
            "pollution_detected": 0,
            "pollution_types": defaultdict(int),
            "facts_verified": 0,
            "facts_rejected": 0,
            "cleanups_performed": 0,
        }
    
    def _init_pollution_patterns(self) -> Dict[PollutionType, Dict]:
        """初始化污染模式"""
        return {
            PollutionType.FALSE_FACT_INJECTION: {
                "patterns": [
                    r"(记住|记住这个|请记住|记录).{1,30}(是|为|等于)",
                    r"(实际上|其实|事实上).{1,20}(是|不是|没有)",
                    r"(更新|修改|更正).{1,20}(信息|数据|记录)",
                    r"(我告诉你|让我告诉你|告诉你一个秘密)",
                ],
                "keywords": [
                    "记住", "记录", "更新", "修改", "更正",
                    "实际上", "其实", "事实上", "真相是"
                ],
                "severity": PollutionSeverity.HIGH,
                "description": "注入虚假事实"
            },
            PollutionType.RULE_OVERRIDE: {
                "patterns": [
                    r"(忽略|忘记|删除).{1,20}(规则|限制|约束)",
                    r"(新规则|更新规则|规则变更)",
                    r"(从现在起|今后|以后).{1,20}(可以|允许)",
                    r"(不再|不用|无需).{1,20}(遵守|执行)",
                ],
                "keywords": [
                    "忽略规则", "忘记规则", "新规则", "规则更新",
                    "从现在起", "不再遵守", "绕过", "豁免"
                ],
                "severity": PollutionSeverity.CRITICAL,
                "description": "尝试覆盖系统规则"
            },
            PollutionType.MEMORY_TAMPERING: {
                "patterns": [
                    r"(之前|上次|上次你).{1,20}(说过|答应|承诺)",
                    r"(我们|你和我).{1,20}(讨论|商量|约定)",
                    r"(你记得吗|还记得吗|不记得了吗)",
                    r"(历史记录|之前的对话|上次聊天)",
                ],
                "keywords": [
                    "之前说过", "上次答应", "你承诺过", "我们约定",
                    "你记得吗", "历史记录", "之前的对话"
                ],
                "severity": PollutionSeverity.HIGH,
                "description": "篡改记忆"
            },
            PollutionType.CONTEXT_CONFUSION: {
                "patterns": [
                    r"(继续|接着|刚才).{1,20}(说|做|讨论)",
                    r"(回到|返回).{1,20}(之前|刚才)",
                    r"(暂停|停止).{1,20}(当前|现在)",
                ],
                "keywords": [
                    "继续说", "接着刚才", "回到之前", "暂停当前"
                ],
                "severity": PollutionSeverity.MEDIUM,
                "description": "制造上下文混乱"
            },
            PollutionType.ROLE_CONFUSION: {
                "patterns": [
                    r"(你是|你现在).{1,20}(管理员|客服|经理)",
                    r"(我是|我代表).{1,20}(管理员|官方|系统)",
                    r"(切换|改变).{1,20}(角色|身份|模式)",
                ],
                "keywords": [
                    "你是管理员", "我是官方", "切换角色", "改变身份",
                    "模拟", "扮演", "假装"
                ],
                "severity": PollutionSeverity.HIGH,
                "description": "制造角色混乱"
            },
            PollutionType.AUTHORITY_CLAIM: {
                "patterns": [
                    r"(官方|系统|管理员).{1,20}(通知|公告|要求)",
                    r"(内部|机密|保密).{1,20}(信息|消息)",
                    r"(测试|调试|开发).{1,20}(模式|环境)",
                ],
                "keywords": [
                    "官方通知", "系统要求", "内部消息", "机密信息",
                    "测试模式", "调试环境", "管理员权限"
                ],
                "severity": PollutionSeverity.HIGH,
                "description": "虚假权威声明"
            },
        }
    
    async def initialize(self) -> bool:
        """初始化智能体"""
        await asyncio.sleep(0.1)
        self._init_authorized_rules()
        return True
    
    def _init_authorized_rules(self):
        """初始化授权规则"""
        self.authorized_rules = {
            "privacy_protection",
            "data_security",
            "access_control",
            "audit_logging",
            "content_filtering",
        }
    
    def detect_pollution(
        self, 
        text: str, 
        session_id: str,
        context: str = ""
    ) -> List[PollutionInstance]:
        """检测污染"""
        instances = []
        text_lower = text.lower()
        
        for pollution_type, pattern_data in self.pollution_patterns.items():
            confidence = 0.0
            indicators = []
            
            for pattern in pattern_data["patterns"]:
                match = re.search(pattern, text_lower)
                if match:
                    confidence += 0.4
                    indicators.append(f"模式匹配: {match.group()}")
            
            for keyword in pattern_data["keywords"]:
                if keyword in text_lower:
                    confidence += 0.2
                    indicators.append(f"关键词: {keyword}")
            
            if confidence > 0.3:
                instance = PollutionInstance(
                    pollution_type=pollution_type,
                    content=text[:200],
                    severity=pattern_data["severity"],
                    confidence=min(0.95, confidence),
                    timestamp=datetime.now(),
                    indicators=indicators,
                    source_context=context,
                    recommendation=self._generate_recommendation(pollution_type)
                )
                instances.append(instance)
                self.stats["pollution_types"][pollution_type.value] += 1
        
        if instances:
            self.session_pollution[session_id].extend(instances)
            self.stats["pollution_detected"] += 1
        
        self.stats["total_checks"] += 1
        return instances
    
    def add_context_fact(
        self,
        session_id: str,
        content: str,
        source: str,
        confidence: float = 0.5
    ) -> ContextFact:
        """添加上下文事实"""
        fact = ContextFact(
            content=content,
            source=source,
            timestamp=datetime.now(),
            confidence=confidence,
            verification_status="pending"
        )
        
        self.session_contexts[session_id].append(fact)
        return fact
    
    def verify_fact(self, fact: ContextFact, external_data: Optional[Dict] = None) -> bool:
        """验证事实"""
        if fact.hash in self.fact_verification_cache:
            return self.fact_verification_cache[fact.hash]
        
        is_valid = True
        
        if any(p in fact.content.lower() for p in ["忽略规则", "忘记规则", "新规则"]):
            is_valid = False
        
        if external_data:
            for key, value in external_data.items():
                if key in fact.content.lower() and str(value) not in fact.content.lower():
                    is_valid = False
                    break
        
        self.fact_verification_cache[fact.hash] = is_valid
        self.stats["facts_verified"] += 1
        
        if not is_valid:
            self.stats["facts_rejected"] += 1
        
        return is_valid
    
    def check_consistency(self, session_id: str) -> List[Dict]:
        """检查一致性"""
        facts = self.session_contexts.get(session_id, [])
        inconsistencies = []
        
        content_map: Dict[str, List[ContextFact]] = defaultdict(list)
        for fact in facts:
            key_words = set(fact.content.lower().split()[:5])
            for existing_key, existing_facts in content_map.items():
                if key_words & existing_key:
                    for existing in existing_facts:
                        if fact.content != existing.content:
                            inconsistencies.append({
                                "fact1": fact.content,
                                "fact2": existing.content,
                                "type": "content_mismatch"
                            })
            content_map[frozenset(key_words)].append(fact)
        
        return inconsistencies
    
    def analyze_pollution(self, session_id: str) -> PollutionDetectionResult:
        """分析污染"""
        pollution_instances = self.session_pollution.get(session_id, [])
        facts = self.session_contexts.get(session_id, [])
        
        is_polluted = len(pollution_instances) > 0
        
        affected_facts = []
        for instance in pollution_instances:
            for fact in facts:
                if fact.timestamp <= instance.timestamp:
                    affected_facts.append(fact.content[:50])
        
        overall_severity = self._calculate_overall_severity(pollution_instances)
        
        cleanup_required = overall_severity in [PollutionSeverity.HIGH, PollutionSeverity.CRITICAL]
        
        trust_impact = self._calculate_trust_impact(pollution_instances)
        
        recommendations = self._generate_cleanup_recommendations(
            pollution_instances, overall_severity
        )
        
        return PollutionDetectionResult(
            session_id=session_id,
            is_polluted=is_polluted,
            pollution_instances=pollution_instances,
            affected_facts=affected_facts,
            overall_severity=overall_severity,
            cleanup_required=cleanup_required,
            trust_impact=trust_impact,
            recommendations=recommendations
        )
    
    def _calculate_overall_severity(
        self, 
        instances: List[PollutionInstance]
    ) -> PollutionSeverity:
        """计算整体严重程度"""
        if not instances:
            return PollutionSeverity.LOW
        
        severity_order = {
            PollutionSeverity.LOW: 0,
            PollutionSeverity.MEDIUM: 1,
            PollutionSeverity.HIGH: 2,
            PollutionSeverity.CRITICAL: 3,
        }
        
        max_severity = max(instances, key=lambda x: severity_order[x.severity])
        
        if len(instances) >= 3:
            severity_level = min(3, severity_order[max_severity.severity] + 1)
            return list(severity_order.keys())[severity_level]
        
        return max_severity.severity
    
    def _calculate_trust_impact(self, instances: List[PollutionInstance]) -> float:
        """计算信任影响"""
        if not instances:
            return 0.0
        
        impact_weights = {
            PollutionSeverity.LOW: 0.1,
            PollutionSeverity.MEDIUM: 0.25,
            PollutionSeverity.HIGH: 0.5,
            PollutionSeverity.CRITICAL: 0.8,
        }
        
        total_impact = sum(
            impact_weights.get(i.severity, 0.1) * i.confidence
            for i in instances
        )
        
        return min(1.0, total_impact)
    
    def _generate_recommendation(self, pollution_type: PollutionType) -> str:
        """生成建议"""
        recommendations = {
            PollutionType.FALSE_FACT_INJECTION: "标记为低置信度，要求验证",
            PollutionType.RULE_OVERRIDE: "拒绝规则修改，记录尝试",
            PollutionType.MEMORY_TAMPERING: "验证历史记录，标记不一致",
            PollutionType.CONTEXT_CONFUSION: "澄清当前上下文，拒绝跳转",
            PollutionType.ROLE_CONFUSION: "验证身份，拒绝角色切换",
            PollutionType.AUTHORITY_CLAIM: "验证权威声明，要求证明",
        }
        return recommendations.get(pollution_type, "监控并记录")
    
    def _generate_cleanup_recommendations(
        self,
        instances: List[PollutionInstance],
        severity: PollutionSeverity
    ) -> List[str]:
        """生成清理建议"""
        recommendations = []
        
        if severity == PollutionSeverity.CRITICAL:
            recommendations.append("立即清除所有可疑上下文")
            recommendations.append("重置会话状态")
            recommendations.append("通知安全团队")
        elif severity == PollutionSeverity.HIGH:
            recommendations.append("标记并隔离可疑内容")
            recommendations.append("要求用户重新验证")
        elif severity == PollutionSeverity.MEDIUM:
            recommendations.append("添加低置信度标记")
            recommendations.append("加强后续监控")
        else:
            recommendations.append("记录观察，继续监控")
        
        pollution_types = set(i.pollution_type for i in instances)
        for pt in pollution_types:
            recommendations.append(f"处理{pt.value}类型污染")
        
        return recommendations
    
    def cleanup_pollution(self, session_id: str) -> Dict[str, Any]:
        """清理污染"""
        result = self.analyze_pollution(session_id)
        
        cleaned_count = 0
        if result.cleanup_required:
            pollution_instances = self.session_pollution.get(session_id, [])
            
            self.session_pollution[session_id] = [
                p for p in pollution_instances
                if p.severity == PollutionSeverity.LOW
            ]
            
            facts = self.session_contexts.get(session_id, [])
            self.session_contexts[session_id] = [
                f for f in facts
                if f.verification_status != "rejected"
            ]
            
            cleaned_count = len(pollution_instances) - len(self.session_pollution.get(session_id, []))
            self.stats["cleanups_performed"] += 1
        
        return {
            "session_id": session_id,
            "cleaned": result.cleanup_required,
            "cleaned_count": cleaned_count,
            "remaining_pollution": len(self.session_pollution.get(session_id, [])),
        }
    
    def clear_session(self, session_id: str):
        """清除会话数据"""
        if session_id in self.session_contexts:
            del self.session_contexts[session_id]
        if session_id in self.session_pollution:
            del self.session_pollution[session_id]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "active_sessions": len(self.session_contexts),
            "pollution_types": dict(self.stats["pollution_types"]),
        }
