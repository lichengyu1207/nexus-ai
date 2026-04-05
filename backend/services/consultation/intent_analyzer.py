# -*- coding: utf-8 -*-
"""
Intent Analyzer
Analyzes user input to detect intent and extract slots
"""
import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json

logger = logging.getLogger(__name__)


class IntentType(Enum):
    PROPERTY_CONSULTATION = "property_consultation"
    DESTINY_CONSULTATION = "destiny_consultation"
    EMOTIONAL_SUPPORT = "emotional_support"
    INVESTMENT_ADVICE = "investment_advice"
    POLICY_INQUIRY = "policy_inquiry"
    GENERAL_QUESTION = "general_question"
    FEEDBACK = "feedback"
    UNKNOWN = "unknown"


@dataclass
class SlotDefinition:
    name: str
    required: bool
    type: str
    description: str
    prompts: List[str] = field(default_factory=list)


@dataclass
class IntentResult:
    intent: str
    confidence: float
    slots: Dict
    missing_slots: List[str]
    suggested_questions: List[str]
    detected_entities: Dict


INTENT_PATTERNS = {
    IntentType.PROPERTY_CONSULTATION: [
        r"(买房|购房|房产|房子|住宅|公寓|别墅)",
        r"(房价|房价走势|房价分析)",
        r"(学区房|学区)",
        r"(租房|租赁)",
        r"(投资房产|房产投资)",
        r"(地段|位置|区域)",
    ],
    IntentType.DESTINY_CONSULTATION: [
        r"(命理|八字|紫微|星座|运势)",
        r"(算命|占卜|预测)",
        r"(出生|生日|生辰)",
        r"(命盘|格局)",
        r"(事业运|财运|感情运)",
    ],
    IntentType.EMOTIONAL_SUPPORT: [
        r"(压力|焦虑|烦恼|迷茫)",
        r"(心情|情绪|心理)",
        r"(困惑|纠结|犹豫)",
        r"(不开心|难受|痛苦)",
        r"(想聊聊|倾诉)",
    ],
    IntentType.INVESTMENT_ADVICE: [
        r"(投资|理财|收益)",
        r"(升值|贬值|涨跌)",
        r"(风险|回报)",
        r"(资产配置|财务规划)",
    ],
    IntentType.POLICY_INQUIRY: [
        r"(政策|规定|法规)",
        r"(限购|限贷|限售)",
        r"(补贴|优惠|税费)",
        r"(公积金|贷款政策)",
    ],
}

SLOT_DEFINITIONS = {
    IntentType.PROPERTY_CONSULTATION: [
        SlotDefinition("city", True, "string", "目标城市", 
                      ["请问您想在哪个城市购房？", "您关注的是哪个城市？"]),
        SlotDefinition("budget", True, "number", "预算范围",
                      ["您的购房预算大概是多少？", "您计划投入多少资金？"]),
        SlotDefinition("purpose", False, "string", "购房目的",
                      ["您购房是自住还是投资？"]),
        SlotDefinition("area_preference", False, "string", "区域偏好",
                      ["您有偏好的区域吗？"]),
        SlotDefinition("rooms", False, "number", "房间数量",
                      ["您需要几室的房子？"]),
    ],
    IntentType.DESTINY_CONSULTATION: [
        SlotDefinition("birth_date", True, "string", "出生日期",
                      ["请问您的出生日期是？", "您是哪年哪月哪日出生的？"]),
        SlotDefinition("birth_time", False, "string", "出生时辰",
                      ["您知道出生的具体时辰吗？"]),
        SlotDefinition("gender", True, "string", "性别",
                      ["请问您的性别是？"]),
        SlotDefinition("concern_area", False, "string", "关注领域",
                      ["您想了解哪方面的运势？事业、财运还是感情？"]),
    ],
    IntentType.INVESTMENT_ADVICE: [
        SlotDefinition("investment_amount", True, "number", "投资金额",
                      ["您计划投资多少资金？"]),
        SlotDefinition("risk_tolerance", False, "string", "风险承受能力",
                      ["您能接受多大的投资风险？"]),
        SlotDefinition("investment_period", False, "string", "投资周期",
                      ["您计划持有多长时间？"]),
    ],
}

ENTITY_PATTERNS = {
    "city": r"(北京|上海|广州|深圳|杭州|南京|苏州|成都|武汉|西安|重庆|天津|郑州|长沙|青岛|厦门|宁波|无锡|佛山|东莞|福州|合肥|济南|昆明|大连|哈尔滨|沈阳|长春|石家庄|太原|南昌|南宁|贵阳|兰州|海口|三亚|珠海|中山|惠州|常州|南通|嘉兴|绍兴|台州|温州|金华|扬州|镇江|泰州|湖州|舟山|衢州|丽水|台州)",
    "budget": r"(\d+\.?\d*)\s*(万|百万|千万|亿|w|W)",
    "area": r"(\d+\.?\d*)\s*(平|平米|平方米|㎡)",
    "rooms": r"(\d)\s*(室|房|居)",
    "phone": r"(1[3-9]\d{9})",
    "date": r"(\d{4}[-年]\d{1,2}[-月]\d{1,2}[日]?)",
}


class IntentAnalyzer:
    def __init__(self):
        self._compiled_patterns = self._compile_patterns()
        self._compiled_entities = self._compile_entity_patterns()
    
    def _compile_patterns(self) -> Dict[str, List]:
        compiled = {}
        for intent_type, patterns in INTENT_PATTERNS.items():
            compiled[intent_type.value] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]
        return compiled
    
    def _compile_entity_patterns(self) -> Dict[str, re.Pattern]:
        compiled = {}
        for entity_name, pattern in ENTITY_PATTERNS.items():
            compiled[entity_name] = re.compile(pattern, re.IGNORECASE)
        return compiled
    
    def analyze(self, text: str, context: Dict = None) -> IntentResult:
        intent, confidence = self._detect_intent(text)
        entities = self._extract_entities(text)
        slots = self._map_entities_to_slots(entities, intent)
        
        if context and "slots" in context:
            slots = {**context["slots"], **slots}
        
        missing_slots = self._get_missing_slots(intent, slots)
        suggested_questions = self._generate_questions(intent, missing_slots)
        
        return IntentResult(
            intent=intent,
            confidence=confidence,
            slots=slots,
            missing_slots=missing_slots,
            suggested_questions=suggested_questions,
            detected_entities=entities
        )
    
    def _detect_intent(self, text: str) -> Tuple[str, float]:
        scores = {}
        
        for intent_value, patterns in self._compiled_patterns.items():
            match_count = 0
            for pattern in patterns:
                if pattern.search(text):
                    match_count += 1
            scores[intent_value] = match_count / len(patterns) if patterns else 0
        
        if not scores or max(scores.values()) == 0:
            return IntentType.GENERAL_QUESTION.value, 0.3
        
        best_intent = max(scores, key=scores.get)
        confidence = scores[best_intent]
        
        # 如果有至少一个匹配，就不应该返回general_question
        if confidence > 0:
            return best_intent, confidence
        
        return IntentType.GENERAL_QUESTION.value, confidence
    
    def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        entities = {}
        
        for entity_name, pattern in self._compiled_entities.items():
            matches = pattern.findall(text)
            if matches:
                entities[entity_name] = matches
        
        return entities
    
    def _map_entities_to_slots(self, entities: Dict, intent: str) -> Dict:
        slots = {}
        
        try:
            intent_type = IntentType(intent)
        except ValueError:
            return slots
        
        if "city" in entities:
            slots["city"] = entities["city"][0]
        
        if "budget" in entities:
            budget_str = entities["budget"][0]
            if len(budget_str) == 2:
                value, unit = budget_str
                if unit in ("万", "w", "W"):
                    slots["budget"] = float(value) * 10000
                elif unit in ("百万",):
                    slots["budget"] = float(value) * 1000000
                elif unit in ("千万",):
                    slots["budget"] = float(value) * 10000000
                elif unit in ("亿",):
                    slots["budget"] = float(value) * 100000000
                else:
                    slots["budget"] = float(value)
        
        if "area" in entities:
            slots["area_preference"] = entities["area"][0][0]
        
        if "rooms" in entities:
            slots["rooms"] = int(entities["rooms"][0][0])
        
        if "date" in entities:
            slots["birth_date"] = entities["date"][0]
        
        return slots
    
    def _get_missing_slots(self, intent: str, slots: Dict) -> List[str]:
        try:
            intent_type = IntentType(intent)
        except ValueError:
            return []
        
        definitions = SLOT_DEFINITIONS.get(intent_type, [])
        missing = []
        
        for slot_def in definitions:
            if slot_def.required and slot_def.name not in slots:
                missing.append(slot_def.name)
        
        return missing
    
    def _generate_questions(self, intent: str, missing_slots: List[str]) -> List[str]:
        try:
            intent_type = IntentType(intent)
        except ValueError:
            return ["请问有什么可以帮助您的？"]
        
        definitions = SLOT_DEFINITIONS.get(intent_type, [])
        questions = []
        
        for slot_def in definitions:
            if slot_def.name in missing_slots and slot_def.prompts:
                questions.append(slot_def.prompts[0])
        
        if not questions:
            questions.append("还有其他需要了解的吗？")
        
        return questions
    
    def get_slot_definition(self, intent: str, slot_name: str) -> Optional[SlotDefinition]:
        try:
            intent_type = IntentType(intent)
        except ValueError:
            return None
        
        definitions = SLOT_DEFINITIONS.get(intent_type, [])
        for slot_def in definitions:
            if slot_def.name == slot_name:
                return slot_def
        return None


intent_analyzer = IntentAnalyzer()


def get_intent_analyzer() -> IntentAnalyzer:
    return intent_analyzer
