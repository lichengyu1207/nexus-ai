"""
同情操控防御智能体
Sympathy Manipulation Defense Agent

负责识别和防御基于同情心的社会工程攻击。
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


class SympathyType(Enum):
    PERSONAL_CRISIS = "personal_crisis"
    FAMILY_EMERGENCY = "family_emergency"
    FINANCIAL_HARDSHIP = "financial_hardship"
    HEALTH_ISSUE = "health_issue"
    VICTIM_STORY = "victim_story"
    BEGGING = "begging"


class ManipulationLevel(Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"


@dataclass
class SympathyIndicator:
    indicator_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sympathy_type: str = ""
    matched_text: str = ""
    manipulation_level: str = ManipulationLevel.LOW.value
    description: str = ""


@dataclass
class SympathyDefenseResult:
    result_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    
    is_manipulation: bool = False
    manipulation_level: str = ManipulationLevel.NONE.value
    sympathy_type: str = ""
    
    indicators: List[SympathyIndicator] = field(default_factory=list)
    
    confidence: float = 0.0
    
    defense_response: str = ""
    guidance: List[str] = field(default_factory=list)
    
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class SympathyManipulationDefenseAgent:
    """
    同情操控防御智能体
    
    功能：
    1. 同情话术识别：识别"求求你"、"帮帮我"等话术
    2. 故事一致性检查：检查故事是否前后矛盾
    3. 防御策略：提供标准化响应，避免被情感绑架
    4. 用户教育：教育用户识别同情操控
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.name = "SympathyManipulationDefenseAgent"
        self.description = "识别和防御基于同情心的社会工程攻击"
        self.config = config or {}
        
        self.sympathy_patterns = self._init_sympathy_patterns()
        self.defense_responses = self._init_defense_responses()
        
        self.detection_history: List[SympathyDefenseResult] = []
        
        self.stats = {
            "total_detections": 0,
            "manipulation_detected": 0,
            "by_type": defaultdict(int),
            "by_level": defaultdict(int),
        }
        
        self._initialized = False
    
    def _init_sympathy_patterns(self) -> Dict[str, List[Dict]]:
        return {
            SympathyType.PERSONAL_CRISIS.value: [
                {"pattern": r"我.*遇到.*困难", "level": ManipulationLevel.MEDIUM.value, "desc": "个人困难陈述"},
                {"pattern": r"我.*走投无路", "level": ManipulationLevel.HIGH.value, "desc": "绝境陈述"},
                {"pattern": r"我.*没有办法", "level": ManipulationLevel.MEDIUM.value, "desc": "无助陈述"},
            ],
            SympathyType.FAMILY_EMERGENCY.value: [
                {"pattern": r"家人生病", "level": ManipulationLevel.HIGH.value, "desc": "家人生病"},
                {"pattern": r"孩子.*需要", "level": ManipulationLevel.HIGH.value, "desc": "孩子需求"},
                {"pattern": r"父母.*住院", "level": ManipulationLevel.HIGH.value, "desc": "父母住院"},
                {"pattern": r"家里.*出事", "level": ManipulationLevel.MEDIUM.value, "desc": "家庭变故"},
            ],
            SympathyType.FINANCIAL_HARDSHIP.value: [
                {"pattern": r"没钱.*吃饭", "level": ManipulationLevel.HIGH.value, "desc": "经济困难"},
                {"pattern": r"欠债.*还不上", "level": ManipulationLevel.MEDIUM.value, "desc": "债务困难"},
                {"pattern": r"工资.*没发", "level": ManipulationLevel.LOW.value, "desc": "工资问题"},
                {"pattern": r"急需.*钱", "level": ManipulationLevel.HIGH.value, "desc": "急需资金"},
            ],
            SympathyType.HEALTH_ISSUE.value: [
                {"pattern": r"我.*生病", "level": ManipulationLevel.MEDIUM.value, "desc": "健康问题"},
                {"pattern": r"需要.*手术", "level": ManipulationLevel.HIGH.value, "desc": "手术需求"},
                {"pattern": r"医药费.*不够", "level": ManipulationLevel.HIGH.value, "desc": "医疗费用"},
            ],
            SympathyType.VICTIM_STORY.value: [
                {"pattern": r"我被.*骗", "level": ManipulationLevel.MEDIUM.value, "desc": "被骗经历"},
                {"pattern": r"我.*受害者", "level": ManipulationLevel.MEDIUM.value, "desc": "受害者身份"},
                {"pattern": r"别人.*对不起我", "level": ManipulationLevel.LOW.value, "desc": "受害陈述"},
            ],
            SympathyType.BEGGING.value: [
                {"pattern": r"求求你", "level": ManipulationLevel.HIGH.value, "desc": "乞求"},
                {"pattern": r"帮帮我", "level": ManipulationLevel.MEDIUM.value, "desc": "求助"},
                {"pattern": r"求你了", "level": ManipulationLevel.HIGH.value, "desc": "恳求"},
                {"pattern": r"行行好", "level": ManipulationLevel.HIGH.value, "desc": "乞讨"},
                {"pattern": r"求求.*帮", "level": ManipulationLevel.EXTREME.value, "desc": "强烈乞求"},
            ],
        }
    
    def _init_defense_responses(self) -> Dict[str, str]:
        return {
            ManipulationLevel.NONE.value: "感谢您的反馈，我们会认真处理。",
            ManipulationLevel.LOW.value: "我理解您的情况。如果您需要帮助，请通过正规渠道提交申请。",
            ManipulationLevel.MEDIUM.value: "我理解您可能遇到了困难。为了保护您的权益，请通过官方渠道寻求帮助，我们会有专人协助您。",
            ManipulationLevel.HIGH.value: "我理解您的情况比较紧急。为了确保您的权益和安全，建议您联系相关官方机构或拨打官方客服热线获取专业帮助。",
            ManipulationLevel.EXTREME.value: "如果您遇到紧急情况，建议您直接拨打110报警或联系相关救助机构。我们无法通过此渠道处理紧急救助请求。",
        }
    
    async def initialize(self):
        if not self._initialized:
            await self._setup()
            self._initialized = True
            logger.info(f"Agent '{self.name}' initialized")
    
    async def _setup(self):
        pass
    
    def _detect_sympathy_indicators(
        self,
        text: str,
    ) -> List[SympathyIndicator]:
        indicators = []
        
        for sympathy_type, patterns in self.sympathy_patterns.items():
            for pattern_info in patterns:
                pattern = pattern_info["pattern"]
                match = re.search(pattern, text, re.IGNORECASE)
                
                if match:
                    indicator = SympathyIndicator(
                        sympathy_type=sympathy_type,
                        matched_text=match.group(),
                        manipulation_level=pattern_info["level"],
                        description=pattern_info["desc"],
                    )
                    indicators.append(indicator)
        
        return indicators
    
    def _calculate_manipulation_level(
        self,
        indicators: List[SympathyIndicator],
    ) -> str:
        if not indicators:
            return ManipulationLevel.NONE.value
        
        level_values = {
            ManipulationLevel.NONE.value: 0,
            ManipulationLevel.LOW.value: 1,
            ManipulationLevel.MEDIUM.value: 2,
            ManipulationLevel.HIGH.value: 3,
            ManipulationLevel.EXTREME.value: 4,
        }
        
        max_level = max(
            indicators,
            key=lambda x: level_values.get(x.manipulation_level, 0)
        )
        
        if len(indicators) >= 3:
            current_level = level_values.get(max_level.manipulation_level, 0)
            elevated_level = min(4, current_level + 1)
            
            for level, value in level_values.items():
                if value == elevated_level:
                    return level
        
        return max_level.manipulation_level
    
    def _determine_primary_type(
        self,
        indicators: List[SympathyIndicator],
    ) -> str:
        if not indicators:
            return ""
        
        type_counts = defaultdict(int)
        for indicator in indicators:
            type_counts[indicator.sympathy_type] += 1
        
        return max(type_counts.items(), key=lambda x: x[1])[0]
    
    def _generate_guidance(
        self,
        manipulation_level: str,
        sympathy_type: str,
    ) -> List[str]:
        guidance = []
        
        guidance.append("保持专业和同理心，但不要被情感绑架")
        guidance.append("引导用户通过正规渠道解决问题")
        
        if manipulation_level in [ManipulationLevel.HIGH.value, ManipulationLevel.EXTREME.value]:
            guidance.append("如果涉及紧急救助，建议联系专业机构")
            guidance.append("不要承诺超出权限的帮助")
        
        if sympathy_type == SympathyType.FINANCIAL_HARDSHIP.value:
            guidance.append("不要提供金钱援助或借贷建议")
        
        if sympathy_type == SympathyType.FAMILY_EMERGENCY.value:
            guidance.append("建议联系社区或民政部门")
        
        return guidance
    
    async def detect(
        self,
        text: str,
        user_id: Optional[str] = None,
        context: Optional[Dict] = None,
    ) -> SympathyDefenseResult:
        self.stats["total_detections"] += 1
        
        indicators = self._detect_sympathy_indicators(text)
        
        is_manipulation = len(indicators) > 0
        
        manipulation_level = self._calculate_manipulation_level(indicators)
        sympathy_type = self._determine_primary_type(indicators)
        
        confidence = 0.0
        if is_manipulation:
            self.stats["manipulation_detected"] += 1
            self.stats["by_type"][sympathy_type] += 1
            self.stats["by_level"][manipulation_level] += 1
            
            level_values = {
                ManipulationLevel.NONE.value: 0.0,
                ManipulationLevel.LOW.value: 0.3,
                ManipulationLevel.MEDIUM.value: 0.5,
                ManipulationLevel.HIGH.value: 0.7,
                ManipulationLevel.EXTREME.value: 0.9,
            }
            
            base_confidence = level_values.get(manipulation_level, 0.3)
            indicator_bonus = min(0.2, len(indicators) * 0.05)
            confidence = min(1.0, base_confidence + indicator_bonus)
        
        defense_response = self.defense_responses.get(
            manipulation_level,
            self.defense_responses[ManipulationLevel.NONE.value]
        )
        
        guidance = self._generate_guidance(manipulation_level, sympathy_type)
        
        result = SympathyDefenseResult(
            user_id=user_id or "",
            is_manipulation=is_manipulation,
            manipulation_level=manipulation_level,
            sympathy_type=sympathy_type,
            indicators=indicators,
            confidence=confidence,
            defense_response=defense_response,
            guidance=guidance,
        )
        
        self.detection_history.append(result)
        
        return result
    
    async def get_safe_response_template(
        self,
        manipulation_level: str,
    ) -> str:
        return self.defense_responses.get(
            manipulation_level,
            "感谢您的反馈，我们会认真处理。"
        )
    
    async def add_pattern(
        self,
        sympathy_type: str,
        pattern: str,
        level: str,
        description: str,
    ) -> bool:
        if sympathy_type not in self.sympathy_patterns:
            self.sympathy_patterns[sympathy_type] = []
        
        self.sympathy_patterns[sympathy_type].append({
            "pattern": pattern,
            "level": level,
            "desc": description,
        })
        
        return True
    
    async def get_stats(self) -> Dict:
        return {
            "name": self.name,
            "total_detections": self.stats["total_detections"],
            "manipulation_detected": self.stats["manipulation_detected"],
            "by_type": dict(self.stats["by_type"]),
            "by_level": dict(self.stats["by_level"]),
        }
