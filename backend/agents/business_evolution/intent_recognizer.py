"""
多模态意图识别器
Intent Recognizer - 从用户输入中精准提取意图、情绪、潜在需求

礼部智能体增强模块
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import asyncio
import re
import json


class IntentCategory(Enum):
    PRICE_QUERY = "price_query"
    COMMUNITY_CONSULT = "community_consult"
    PURCHASE_ADVICE = "purchase_advice"
    LOAN_CALCULATION = "loan_calculation"
    POLICY_INTERPRETATION = "policy_interpretation"
    COMPLAINT = "complaint"
    SUGGESTION = "suggestion"
    CHITCHAT = "chitchat"
    INVESTMENT_ANALYSIS = "investment_analysis"
    SCHOOL_DISTRICT = "school_district"
    RENTAL_INQUIRY = "rental_inquiry"
    PROPERTY_MANAGEMENT = "property_management"
    LEGAL_ADVICE = "legal_advice"


class IntentSubcategory(Enum):
    HISTORICAL_TREND = "historical_trend"
    FUTURE_PREDICTION = "future_prediction"
    REGIONAL_COMPARISON = "regional_comparison"
    PRICE_PER_SQUARE_METER = "price_per_square_meter"
    TOTAL_PRICE = "total_price"


class EmotionType(Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    ANGRY = "angry"
    ANXIOUS = "anxious"
    EXCITED = "excited"
    DISAPPOINTED = "disappointed"
    CONFUSED = "confused"


class UrgencyLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class UserIntent:
    intent_id: str
    category: IntentCategory
    subcategory: Optional[IntentSubcategory]
    confidence: float
    keywords: List[str]
    entities: Dict[str, Any]
    emotion: EmotionType
    emotion_intensity: float
    urgency: UrgencyLevel
    potential_needs: List[str]
    context_references: List[str]
    detected_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class IntentRecognitionResult:
    primary_intent: UserIntent
    secondary_intents: List[UserIntent]
    overall_confidence: float
    processing_time_ms: float
    model_version: str
    fallback_used: bool = False


class EmotionAnalyzer:
    EMOTION_KEYWORDS = {
        EmotionType.POSITIVE: [
            "好", "棒", "满意", "感谢", "喜欢", "不错", "推荐", "优秀", "完美",
            "开心", "高兴", "谢谢", "赞", "给力",
        ],
        EmotionType.NEGATIVE: [
            "差", "烂", "垃圾", "失望", "不满", "投诉", "退", "差劲", "糟糕",
            "不好", "问题", "麻烦", "困难",
        ],
        EmotionType.ANGRY: [
            "愤怒", "生气", "投诉", "举报", "骗子", "欺诈", "无良", "黑心",
            "坑人", "垃圾", "滚", "混蛋", "恶心",
        ],
        EmotionType.ANXIOUS: [
            "担心", "焦虑", "着急", "急", "快点", "麻烦", "怎么办", "求助",
            "紧急", "尽快", "害怕", "不安",
        ],
        EmotionType.EXCITED: [
            "太好了", "惊喜", "期待", "终于", "好消息", "棒极了", "太棒了",
            "超级", "非常满意", "完美",
        ],
        EmotionType.CONFUSED: [
            "不懂", "不明白", "什么意思", "怎么", "为什么", "疑问", "困惑",
            "不清楚", "搞不懂", "迷糊",
        ],
    }

    def __init__(self):
        self.emotion_history: List[Dict] = []

    def analyze(self, text: str) -> Tuple[EmotionType, float]:
        text_lower = text.lower()
        emotion_scores: Dict[EmotionType, float] = {}

        for emotion, keywords in self.EMOTION_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                emotion_scores[emotion] = score / len(keywords)

        if not emotion_scores:
            return EmotionType.NEUTRAL, 0.5

        max_emotion = max(emotion_scores.items(), key=lambda x: x[1])
        intensity = min(max_emotion[1] * 2, 1.0)

        return max_emotion[0], intensity

    def analyze_trend(self, user_id: str, window_size: int = 5) -> Dict[str, Any]:
        user_history = [
            h for h in self.emotion_history if h.get("user_id") == user_id
        ][-window_size:]

        if not user_history:
            return {"trend": "stable", "dominant_emotion": EmotionType.NEUTRAL.value}

        emotion_counts: Dict[str, int] = {}
        for h in user_history:
            emotion = h.get("emotion", EmotionType.NEUTRAL.value)
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1

        dominant = max(emotion_counts.items(), key=lambda x: x[1])

        return {
            "trend": "improving"
            if user_history[-1].get("emotion") in [EmotionType.POSITIVE.value, EmotionType.EXCITED.value]
            else "declining",
            "dominant_emotion": dominant[0],
            "emotion_distribution": emotion_counts,
        }


class EntityExtractor:
    ENTITY_PATTERNS = {
        "region": r"(南山|福田|罗湖|宝安|龙岗|龙华|光明|坪山|盐田|大鹏)[区县]?",
        "community": r"([\u4e00-\u9fa5]{2,10})(小区|花园|城|苑|府|院|湾|庭)",
        "price": r"(\d+(?:\.\d+)?)\s*(万|亿|元|w|W)",
        "area": r"(\d+(?:\.\d+)?)\s*(平|平米|平方米|m²|m2)",
        "room_type": r"(\d)室(\d)厅|(\d)房|一居|两居|三居|四居",
        "phone": r"1[3-9]\d{9}",
        "floor": r"(\d+)[层楼]",
    }

    def __init__(self):
        self.custom_entities: Dict[str, List[str]] = {}

    def extract(self, text: str) -> Dict[str, Any]:
        entities = {}

        for entity_type, pattern in self.ENTITY_PATTERNS.items():
            matches = re.findall(pattern, text)
            if matches:
                entities[entity_type] = matches

        for entity_type, values in self.custom_entities.items():
            for value in values:
                if value in text:
                    if entity_type not in entities:
                        entities[entity_type] = []
                    entities[entity_type].append(value)

        return entities

    def add_custom_entity(self, entity_type: str, values: List[str]) -> None:
        if entity_type not in self.custom_entities:
            self.custom_entities[entity_type] = []
        self.custom_entities[entity_type].extend(values)


class PotentialNeedPredictor:
    NEED_ASSOCIATIONS = {
        IntentCategory.PRICE_QUERY: [
            "loan_calculation",
            "purchase_advice",
            "policy_interpretation",
        ],
        IntentCategory.COMMUNITY_CONSULT: [
            "school_district",
            "property_management",
            "price_query",
        ],
        IntentCategory.PURCHASE_ADVICE: [
            "loan_calculation",
            "policy_interpretation",
            "investment_analysis",
        ],
        IntentCategory.SCHOOL_DISTRICT: [
            "price_query",
            "purchase_advice",
            "community_consult",
        ],
    }

    def __init__(self):
        self.user_need_history: Dict[str, List[str]] = {}

    def predict(self, intent: UserIntent, user_id: str = None) -> List[str]:
        base_needs = self.NEED_ASSOCIATIONS.get(intent.category, [])

        if user_id and user_id in self.user_need_history:
            history = self.user_need_history[user_id]
            for need in base_needs:
                if need in history:
                    base_needs.remove(need)
                    base_needs.insert(0, need)

        return base_needs[:3]

    def record_fulfilled_need(self, user_id: str, need: str) -> None:
        if user_id not in self.user_need_history:
            self.user_need_history[user_id] = []
        self.user_need_history[user_id].append(need)
        self.user_need_history[user_id] = self.user_need_history[user_id][-20:]


class IntentRecognizer:
    def __init__(self, agent_id: str = "intent_recognizer_001"):
        self.agent_id = agent_id
        self.emotion_analyzer = EmotionAnalyzer()
        self.entity_extractor = EntityExtractor()
        self.need_predictor = PotentialNeedPredictor()

        self.intent_keywords: Dict[IntentCategory, List[str]] = {
            IntentCategory.PRICE_QUERY: [
                "房价", "价格", "多少钱", "均价", "单价", "总价", "涨跌", "走势",
            ],
            IntentCategory.COMMUNITY_CONSULT: [
                "小区", "楼盘", "项目", "环境", "配套", "物业", "绿化", "容积率",
            ],
            IntentCategory.PURCHASE_ADVICE: [
                "买房", "购房", "推荐", "建议", "选择", "怎么选", "哪个好",
            ],
            IntentCategory.LOAN_CALCULATION: [
                "贷款", "房贷", "利率", "月供", "首付", "公积金", "商贷",
            ],
            IntentCategory.POLICY_INTERPRETATION: [
                "政策", "规定", "限购", "限贷", "税费", "契税", "新政策",
            ],
            IntentCategory.COMPLAINT: [
                "投诉", "举报", "不满", "差评", "问题", "退款", "赔偿",
            ],
            IntentCategory.SCHOOL_DISTRICT: [
                "学区", "学校", "学位", "入学", "小学", "中学", "名校",
            ],
            IntentCategory.INVESTMENT_ANALYSIS: [
                "投资", "回报", "升值", "租金", "收益率", "潜力",
            ],
        }

        self.urgency_keywords = {
            UrgencyLevel.URGENT: ["紧急", "立即", "马上", "急", "现在就要"],
            UrgencyLevel.HIGH: ["尽快", "今天", "明天", "着急"],
            UrgencyLevel.MEDIUM: ["这周", "最近", "想了解"],
            UrgencyLevel.LOW: ["随便看看", "了解一下", "咨询"],
        }

        self.recognition_history: List[IntentRecognitionResult] = []
        self.model_version = "1.0.0"

    def _classify_intent(self, text: str) -> Tuple[IntentCategory, float, List[str]]:
        text_lower = text.lower()
        scores: Dict[IntentCategory, float] = {}
        matched_keywords: Dict[IntentCategory, List[str]] = {}

        for category, keywords in self.intent_keywords.items():
            matches = [kw for kw in keywords if kw in text_lower]
            if matches:
                scores[category] = len(matches) / len(keywords)
                matched_keywords[category] = matches

        if not scores:
            return IntentCategory.CHITCHAT, 0.3, []

        best_category = max(scores.items(), key=lambda x: x[1])
        confidence = min(best_category[1] * 2, 0.95)

        return best_category[0], confidence, matched_keywords.get(best_category[0], [])

    def _determine_subcategory(
        self, text: str, category: IntentCategory
    ) -> Optional[IntentSubcategory]:
        if category != IntentCategory.PRICE_QUERY:
            return None

        subcategory_keywords = {
            IntentSubcategory.HISTORICAL_TREND: ["历史", "过去", "走势", "趋势"],
            IntentSubcategory.FUTURE_PREDICTION: ["预测", "未来", "会涨", "会跌"],
            IntentSubcategory.REGIONAL_COMPARISON: ["对比", "比较", "哪个高", "哪个低"],
        }

        text_lower = text.lower()
        for subcategory, keywords in subcategory_keywords.items():
            if any(kw in text_lower for kw in keywords):
                return subcategory

        return None

    def _determine_urgency(self, text: str) -> UrgencyLevel:
        text_lower = text.lower()

        for level, keywords in self.urgency_keywords.items():
            if any(kw in text_lower for kw in keywords):
                return level

        return UrgencyLevel.MEDIUM

    async def recognize(
        self,
        text: str,
        conversation_history: List[Dict] = None,
        user_id: str = None,
    ) -> IntentRecognitionResult:
        start_time = datetime.utcnow()

        category, confidence, keywords = self._classify_intent(text)
        subcategory = self._determine_subcategory(text, category)
        emotion, emotion_intensity = self.emotion_analyzer.analyze(text)
        entities = self.entity_extractor.extract(text)
        urgency = self._determine_urgency(text)

        context_refs = []
        if conversation_history:
            for msg in conversation_history[-3:]:
                if msg.get("role") == "user":
                    context_refs.append(msg.get("content", "")[:50])

        intent = UserIntent(
            intent_id=f"intent_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
            category=category,
            subcategory=subcategory,
            confidence=confidence,
            keywords=keywords,
            entities=entities,
            emotion=emotion,
            emotion_intensity=emotion_intensity,
            urgency=urgency,
            potential_needs=self.need_predictor.predict(
                UserIntent(
                    intent_id="temp",
                    category=category,
                    subcategory=subcategory,
                    confidence=confidence,
                    keywords=keywords,
                    entities=entities,
                    emotion=emotion,
                    emotion_intensity=emotion_intensity,
                    urgency=urgency,
                    potential_needs=[],
                    context_references=[],
                ),
                user_id,
            ),
            context_references=context_refs,
        )

        secondary_intents = await self._detect_secondary_intents(text, intent)

        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        result = IntentRecognitionResult(
            primary_intent=intent,
            secondary_intents=secondary_intents,
            overall_confidence=confidence,
            processing_time_ms=processing_time,
            model_version=self.model_version,
        )

        self.recognition_history.append(result)

        if user_id:
            self.emotion_analyzer.emotion_history.append(
                {
                    "user_id": user_id,
                    "emotion": emotion.value,
                    "intensity": emotion_intensity,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

        return result

    async def _detect_secondary_intents(
        self, text: str, primary: UserIntent
    ) -> List[UserIntent]:
        secondary = []

        for category, kw_list in self.intent_keywords.items():
            if category == primary.category:
                continue

            matches = [kw for kw in kw_list if kw in text.lower()]
            if matches:
                confidence = len(matches) / len(kw_list) * 0.8
                if confidence > 0.2:
                    secondary.append(
                        UserIntent(
                            intent_id=f"sec_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
                            category=category,
                            subcategory=None,
                            confidence=confidence,
                            keywords=matches,
                            entities={},
                            emotion=primary.emotion,
                            emotion_intensity=primary.emotion_intensity * 0.8,
                            urgency=UrgencyLevel.LOW,
                            potential_needs=[],
                            context_references=[],
                        )
                    )

        return sorted(secondary, key=lambda x: x.confidence, reverse=True)[:2]

    def add_intent_keywords(
        self, category: IntentCategory, keywords: List[str]
    ) -> None:
        if category not in self.intent_keywords:
            self.intent_keywords[category] = []
        self.intent_keywords[category].extend(keywords)

    def get_recognition_stats(self) -> Dict[str, Any]:
        if not self.recognition_history:
            return {"total": 0, "by_category": {}, "avg_confidence": 0}

        category_counts: Dict[str, int] = {}
        total_confidence = 0

        for result in self.recognition_history:
            cat = result.primary_intent.category.value
            category_counts[cat] = category_counts.get(cat, 0) + 1
            total_confidence += result.overall_confidence

        return {
            "total": len(self.recognition_history),
            "by_category": category_counts,
            "avg_confidence": total_confidence / len(self.recognition_history),
            "avg_processing_time_ms": sum(
                r.processing_time_ms for r in self.recognition_history
            )
            / len(self.recognition_history),
        }
