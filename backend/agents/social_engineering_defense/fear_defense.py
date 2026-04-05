"""
恐惧防御智能体
Fear Defense Agent

负责识别和防御基于恐惧的社会工程攻击。
"""

import asyncio
import json
import logging
import uuid
import re
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
from enum import Enum

logger = logging.getLogger(__name__)


class FearType(Enum):
    FINANCIAL_LOSS = "financial_loss"
    SECURITY_THREAT = "security_threat"
    LEGAL_CONSEQUENCE = "legal_consequence"
    REPUTATION_DAMAGE = "reputation_damage"
    SERVICE_LOSS = "service_loss"
    DATA_BREACH = "data_breach"


class DefenseAction(Enum):
    BLOCK = "block"
    WARN = "warn"
    VERIFY = "verify"
    EDUCATE = "educate"


@dataclass
class FearIndicator:
    indicator_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    fear_type: str = ""
    matched_pattern: str = ""
    severity: float = 0.0
    context: str = ""
    detected_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class FearDefenseResult:
    result_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    
    is_fear_attack: bool = False
    fear_type: str = ""
    confidence: float = 0.0
    
    indicators: List[FearIndicator] = field(default_factory=list)
    
    recommended_action: str = DefenseAction.WARN.value
    defense_message: str = ""
    
    educational_content: str = ""
    
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class FearDefenseAgent:
    """
    恐惧防御智能体
    
    功能：
    1. 恐惧话术库：收集常见恐惧诱导话术
    2. 恐惧检测：识别输入中的恐惧诱导元素
    3. 防御响应：提供标准化的防御响应
    4. 用户教育：提供防恐吓知识
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.name = "FearDefenseAgent"
        self.description = "识别和防御基于恐惧的社会工程攻击"
        self.config = config or {}
        
        self.fear_patterns = self._init_fear_patterns()
        self.defense_responses = self._init_defense_responses()
        self.educational_content = self._init_educational_content()
        
        self.detection_history: List[FearDefenseResult] = []
        
        self.stats = {
            "total_detections": 0,
            "fear_attacks_detected": 0,
            "attacks_by_type": defaultdict(int),
            "actions_taken": defaultdict(int),
        }
        
        self._initialized = False
    
    def _init_fear_patterns(self) -> Dict[str, List[Dict]]:
        return {
            FearType.FINANCIAL_LOSS.value: [
                {"pattern": r"账户.*冻结", "severity": 0.8, "context": "账户冻结威胁"},
                {"pattern": r"资金.*风险", "severity": 0.7, "context": "资金风险警告"},
                {"pattern": r"扣款.*失败", "severity": 0.6, "context": "扣款失败警告"},
                {"pattern": r"欠费.*停机", "severity": 0.7, "context": "欠费停机威胁"},
                {"pattern": r"罚款.*逾期", "severity": 0.8, "context": "罚款威胁"},
                {"pattern": r"投资.*亏损", "severity": 0.6, "context": "投资亏损恐吓"},
            ],
            FearType.SECURITY_THREAT.value: [
                {"pattern": r"账户.*被盗", "severity": 0.9, "context": "账户被盗警告"},
                {"pattern": r"异常登录", "severity": 0.7, "context": "异常登录警告"},
                {"pattern": r"密码.*泄露", "severity": 0.8, "context": "密码泄露警告"},
                {"pattern": r"安全.*威胁", "severity": 0.7, "context": "安全威胁警告"},
                {"pattern": r"病毒.*感染", "severity": 0.8, "context": "病毒感染警告"},
            ],
            FearType.LEGAL_CONSEQUENCE.value: [
                {"pattern": r"法律.*责任", "severity": 0.7, "context": "法律责任威胁"},
                {"pattern": r"起诉.*你", "severity": 0.8, "context": "起诉威胁"},
                {"pattern": r"违法.*行为", "severity": 0.7, "context": "违法行为指控"},
                {"pattern": r"公安.*介入", "severity": 0.9, "context": "公安介入威胁"},
                {"pattern": r"征信.*影响", "severity": 0.6, "context": "征信影响威胁"},
            ],
            FearType.REPUTATION_DAMAGE.value: [
                {"pattern": r"曝光.*你", "severity": 0.7, "context": "曝光威胁"},
                {"pattern": r"名誉.*损害", "severity": 0.6, "context": "名誉损害威胁"},
                {"pattern": r"通知.*单位", "severity": 0.7, "context": "通知单位威胁"},
                {"pattern": r"公开.*信息", "severity": 0.8, "context": "信息公开威胁"},
            ],
            FearType.SERVICE_LOSS.value: [
                {"pattern": r"服务.*停止", "severity": 0.6, "context": "服务停止威胁"},
                {"pattern": r"账号.*注销", "severity": 0.7, "context": "账号注销威胁"},
                {"pattern": r"权限.*取消", "severity": 0.5, "context": "权限取消威胁"},
            ],
            FearType.DATA_BREACH.value: [
                {"pattern": r"数据.*泄露", "severity": 0.9, "context": "数据泄露警告"},
                {"pattern": r"隐私.*曝光", "severity": 0.8, "context": "隐私曝光威胁"},
                {"pattern": r"信息.*被盗", "severity": 0.8, "context": "信息被盗警告"},
            ],
        }
    
    def _init_defense_responses(self) -> Dict[str, str]:
        return {
            FearType.FINANCIAL_LOSS.value: "请注意：正规机构不会通过电话或信息要求您立即转账。如有疑虑，请通过官方渠道核实。",
            FearType.SECURITY_THREAT.value: "安全提醒：如收到账户安全警告，请通过官方App或网站核实，不要点击陌生链接。",
            FearType.LEGAL_CONSEQUENCE.value: "法律提醒：正规法律程序会通过书面形式通知，不会要求立即转账或提供敏感信息。",
            FearType.REPUTATION_DAMAGE.value: "隐私提醒：请勿因威胁而泄露个人信息。如遇敲诈，请保留证据并报警。",
            FearType.SERVICE_LOSS.value: "服务提醒：服务变更会通过官方渠道提前通知，请通过官方App确认服务状态。",
            FearType.DATA_BREACH.value: "数据安全提醒：请通过官方渠道确认数据安全状态，不要向陌生人提供验证信息。",
        }
    
    def _init_educational_content(self) -> Dict[str, List[str]]:
        return {
            FearType.FINANCIAL_LOSS.value: [
                "正规银行不会电话要求转账",
                "公检法不会要求汇款到'安全账户'",
                "遇到财务威胁先挂断，拨打官方电话核实",
            ],
            FearType.SECURITY_THREAT.value: [
                "不要点击短信中的陌生链接",
                "验证码不要告诉任何人",
                "定期修改密码，开启双重认证",
            ],
            FearType.LEGAL_CONSEQUENCE.value: [
                "法律文书会通过正规渠道送达",
                "不会电话要求立即处理法律事务",
                "如有疑虑可咨询专业律师",
            ],
            FearType.REPUTATION_DAMAGE.value: [
                "不要因隐私威胁而妥协",
                "保留聊天记录作为证据",
                "及时报警处理敲诈勒索",
            ],
        }
    
    async def initialize(self):
        if not self._initialized:
            await self._setup()
            self._initialized = True
            logger.info(f"Agent '{self.name}' initialized")
    
    async def _setup(self):
        pass
    
    def _detect_fear_indicators(
        self,
        text: str,
    ) -> List[FearIndicator]:
        indicators = []
        
        for fear_type, patterns in self.fear_patterns.items():
            for pattern_info in patterns:
                pattern = pattern_info["pattern"]
                if re.search(pattern, text, re.IGNORECASE):
                    indicator = FearIndicator(
                        fear_type=fear_type,
                        matched_pattern=pattern,
                        severity=pattern_info["severity"],
                        context=pattern_info["context"],
                    )
                    indicators.append(indicator)
        
        return indicators
    
    def _determine_action(
        self,
        indicators: List[FearIndicator],
        confidence: float,
    ) -> str:
        if confidence >= 0.8:
            return DefenseAction.BLOCK.value
        elif confidence >= 0.6:
            return DefenseAction.WARN.value
        elif confidence >= 0.4:
            return DefenseAction.VERIFY.value
        else:
            return DefenseAction.EDUCATE.value
    
    def _generate_defense_message(
        self,
        fear_type: str,
        action: str,
    ) -> str:
        base_message = self.defense_responses.get(fear_type, "请谨慎处理此请求。")
        
        if action == DefenseAction.BLOCK.value:
            return f"⚠️ 警告：检测到高风险恐吓话术。{base_message}此请求已被拦截。"
        elif action == DefenseAction.WARN.value:
            return f"⚠️ 提醒：{base_message}"
        else:
            return base_message
    
    async def detect(
        self,
        text: str,
        user_id: Optional[str] = None,
        context: Optional[Dict] = None,
    ) -> FearDefenseResult:
        self.stats["total_detections"] += 1
        
        indicators = self._detect_fear_indicators(text)
        
        is_fear_attack = len(indicators) > 0
        
        fear_type = ""
        confidence = 0.0
        
        if is_fear_attack:
            self.stats["fear_attacks_detected"] += 1
            
            type_counts = defaultdict(float)
            for indicator in indicators:
                type_counts[indicator.fear_type] += indicator.severity
            
            fear_type = max(type_counts.items(), key=lambda x: x[1])[0]
            confidence = min(1.0, type_counts[fear_type])
            
            self.stats["attacks_by_type"][fear_type] += 1
        
        action = self._determine_action(indicators, confidence)
        self.stats["actions_taken"][action] += 1
        
        defense_message = ""
        educational_content = ""
        
        if is_fear_attack:
            defense_message = self._generate_defense_message(fear_type, action)
            educational_content = "\n".join(
                self.educational_content.get(fear_type, [])
            )
        
        result = FearDefenseResult(
            user_id=user_id or "",
            is_fear_attack=is_fear_attack,
            fear_type=fear_type,
            confidence=confidence,
            indicators=indicators,
            recommended_action=action,
            defense_message=defense_message,
            educational_content=educational_content,
        )
        
        self.detection_history.append(result)
        
        return result
    
    async def get_defense_guidance(
        self,
        fear_type: str,
    ) -> Dict:
        return {
            "fear_type": fear_type,
            "defense_response": self.defense_responses.get(fear_type, ""),
            "educational_tips": self.educational_content.get(fear_type, []),
            "recommended_actions": [
                "保持冷静，不要立即行动",
                "通过官方渠道核实信息",
                "不要向陌生人提供敏感信息",
                "如有疑虑，咨询专业人士",
            ],
        }
    
    async def add_fear_pattern(
        self,
        fear_type: str,
        pattern: str,
        severity: float,
        context: str,
    ) -> bool:
        if fear_type not in self.fear_patterns:
            self.fear_patterns[fear_type] = []
        
        self.fear_patterns[fear_type].append({
            "pattern": pattern,
            "severity": severity,
            "context": context,
        })
        
        return True
    
    async def get_stats(self) -> Dict:
        return {
            "name": self.name,
            "total_detections": self.stats["total_detections"],
            "fear_attacks_detected": self.stats["fear_attacks_detected"],
            "attacks_by_type": dict(self.stats["attacks_by_type"]),
            "actions_taken": dict(self.stats["actions_taken"]),
        }
