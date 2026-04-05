"""
三省六部业务智能体实现
Six Ministry Business Agents Implementation

基于活体智能体基类，实现：
- 礼部（咨询）：意图识别、对话策略、会话记忆、主动推荐
- 工部（分析）：任务解析、个性化报告、质量评估
- 户部（积分）：动态积分、活动策划、会员等级
- 兵部（采集）：数据源选择、自适应采集、异常检测
- 吏部（管理）：健康监控、资源调度、繁殖管理
- 刑部（风控）：风险拦截、行为画像
"""

import os
import json
import time
import uuid
import random
import logging
import threading
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from collections import deque, defaultdict
from enum import Enum

from ..living import (
    LivingAgent, AgentSpecies, AgentState, AgentMessage,
    blackboard, message_bus, agent_registry, GenePool
)

logger = logging.getLogger(__name__)


class IntentType(Enum):
    PRICE_QUERY = "price_query"
    COMMUNITY_CONSULT = "community_consult"
    PURCHASE_ADVICE = "purchase_advice"
    LOAN_CALC = "loan_calc"
    POLICY_INTERPRET = "policy_interpret"
    COMPLAINT = "complaint"
    CHITCHAT = "chitchat"
    AREA_COMPARE = "area_compare"
    SCHOOL_QUERY = "school_query"
    INVESTMENT_ANALYSIS = "investment_analysis"


class EmotionType(Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    ANGRY = "angry"
    ANXIOUS = "anxious"


class UserType(Enum):
    NEWBIE = "newbie"
    NORMAL = "normal"
    EXPERT = "expert"
    INVESTOR = "investor"


class DialogueStyle(Enum):
    ENTHUSIASTIC = "enthusiastic"
    PROFESSIONAL = "professional"
    CONCISE = "concise"
    ZHOUYU = "zhouyu"
    LUXUN = "luxun"


@dataclass
class IntentResult:
    intent: IntentType
    confidence: float
    entities: Dict[str, Any] = field(default_factory=dict)
    emotion: EmotionType = EmotionType.NEUTRAL
    potential_needs: List[str] = field(default_factory=list)


@dataclass
class DialogueContext:
    session_id: str
    user_id: str
    history: List[Dict[str, str]] = field(default_factory=list)
    user_type: UserType = UserType.NORMAL
    preferred_style: DialogueStyle = DialogueStyle.ZHOUYU
    mentioned_entities: Dict[str, List[str]] = field(default_factory=dict)
    last_intent: Optional[IntentType] = None


class IntentRecognizer:
    def __init__(self):
        self.intent_patterns = self._load_intent_patterns()
        self.entity_patterns = self._load_entity_patterns()
        self.emotion_keywords = self._load_emotion_keywords()
    
    def _load_intent_patterns(self) -> Dict[IntentType, List[re.Pattern]]:
        patterns = {}
        
        patterns[IntentType.PRICE_QUERY] = [
            re.compile(r'(房价|均价|价格|多少钱|单价).*?(多少|查询|了解)', re.I),
            re.compile(r'(.*?)(小区|楼盘).*?(房价|均价)', re.I),
            re.compile(r'现在.*?房价.*?怎么样', re.I),
        ]
        
        patterns[IntentType.COMMUNITY_CONSULT] = [
            re.compile(r'(小区|楼盘|社区).*?(介绍|详情|怎么样)', re.I),
            re.compile(r'(想了解|咨询).*?(小区|楼盘)', re.I),
            re.compile(r'(配套|环境|物业).*?(怎么样|如何)', re.I),
        ]
        
        patterns[IntentType.PURCHASE_ADVICE] = [
            re.compile(r'(买房|购房|置业).*?(建议|推荐)', re.I),
            re.compile(r'(想买|准备买).*?(房|房子)', re.I),
            re.compile(r'(预算|首付).*?(万|能买)', re.I),
            re.compile(r'(推荐|建议).*?(区域|小区)', re.I),
        ]
        
        patterns[IntentType.LOAN_CALC] = [
            re.compile(r'(贷款|房贷|月供).*?(计算|多少)', re.I),
            re.compile(r'(公积金|商贷|组合贷)', re.I),
            re.compile(r'(利率|利息).*?(多少|计算)', re.I),
        ]
        
        patterns[IntentType.POLICY_INTERPRET] = [
            re.compile(r'(政策|规定|新政).*?(解读|是什么)', re.I),
            re.compile(r'(首付比例|限购|限贷)', re.I),
            re.compile(r'(契税|税费).*?(多少|政策)', re.I),
        ]
        
        patterns[IntentType.COMPLAINT] = [
            re.compile(r'(投诉|举报|不满|差评)', re.I),
            re.compile(r'(问题|故障|错误).*?(反馈|投诉)', re.I),
        ]
        
        patterns[IntentType.AREA_COMPARE] = [
            re.compile(r'(对比|比较).*?(区域|小区)', re.I),
            re.compile(r'(哪个|哪个好).*?(区域|小区)', re.I),
            re.compile(r'(A区|B区|南山|福田).*?(vs|对比|比较)', re.I),
        ]
        
        patterns[IntentType.SCHOOL_QUERY] = [
            re.compile(r'(学区|学校|学位).*?(查询|了解)', re.I),
            re.compile(r'(小学|中学|幼儿园).*?(学区|对口)', re.I),
        ]
        
        patterns[IntentType.INVESTMENT_ANALYSIS] = [
            re.compile(r'(投资|升值|回报).*?(分析|建议)', re.I),
            re.compile(r'(哪个区域).*?(升值|投资价值)', re.I),
        ]
        
        patterns[IntentType.CHITCHAT] = [
            re.compile(r'(你好|在吗|您好)', re.I),
            re.compile(r'(谢谢|感谢|辛苦)', re.I),
            re.compile(r'(天气|今天|明天)', re.I),
        ]
        
        return patterns
    
    def _load_entity_patterns(self) -> Dict[str, re.Pattern]:
        return {
            "city": re.compile(r'(深圳|广州|北京|上海|杭州|成都|武汉|南京)', re.I),
            "district": re.compile(r'(南山|福田|罗湖|宝安|龙岗|龙华|光明|坪山|盐田)', re.I),
            "price": re.compile(r'(\d+(?:\.\d+)?)\s*(万|w|W)?(?:每平|/㎡|/平)?', re.I),
            "area": re.compile(r'(\d+(?:\.\d+)?)\s*(㎡|平方米|平)', re.I),
            "room_type": re.compile(r'(\d)室(\d)厅|(\d)房|(\d)居', re.I),
            "budget": re.compile(r'预算\s*(\d+(?:\.\d+)?)\s*(万|w)?', re.I),
        }
    
    def _load_emotion_keywords(self) -> Dict[EmotionType, List[str]]:
        return {
            EmotionType.POSITIVE: ['好', '棒', '赞', '满意', '喜欢', '感谢', '谢谢', '太好了'],
            EmotionType.NEGATIVE: ['不好', '差', '失望', '不满', '问题', '麻烦'],
            EmotionType.ANGRY: ['生气', '愤怒', '投诉', '骗子', '垃圾', '什么破', '太差'],
            EmotionType.ANXIOUS: ['着急', '担心', '焦虑', '怕', '会不会', '怎么办'],
        }
    
    def recognize(self, text: str, context: Optional[DialogueContext] = None) -> IntentResult:
        intent_scores: Dict[IntentType, float] = defaultdict(float)
        
        for intent_type, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if pattern.search(text):
                    intent_scores[intent_type] += 1.0
        
        if not intent_scores:
            intent = IntentType.CHITCHAT
            confidence = 0.5
        else:
            intent = max(intent_scores, key=intent_scores.get)
            confidence = min(0.95, intent_scores[intent] / 3.0)
        
        entities = self._extract_entities(text)
        emotion = self._detect_emotion(text)
        potential_needs = self._predict_potential_needs(intent, entities)
        
        return IntentResult(
            intent=intent,
            confidence=confidence,
            entities=entities,
            emotion=emotion,
            potential_needs=potential_needs
        )
    
    def _extract_entities(self, text: str) -> Dict[str, Any]:
        entities = {}
        
        for entity_type, pattern in self.entity_patterns.items():
            matches = pattern.findall(text)
            if matches:
                if entity_type == "price":
                    entities["price"] = [{"value": float(m[0]), "unit": m[1] or "万"} for m in matches]
                elif entity_type == "area":
                    entities["area"] = [float(m[0]) for m in matches]
                elif entity_type == "room_type":
                    for m in matches:
                        if m[0] and m[1]:
                            entities["room_type"] = f"{m[0]}室{m[1]}厅"
                        elif m[2]:
                            entities["room_type"] = f"{m[2]}房"
                else:
                    entities[entity_type] = matches
        
        return entities
    
    def _detect_emotion(self, text: str) -> EmotionType:
        emotion_scores: Dict[EmotionType, int] = defaultdict(int)
        
        for emotion, keywords in self.emotion_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    emotion_scores[emotion] += 1
        
        if not emotion_scores:
            return EmotionType.NEUTRAL
        
        return max(emotion_scores, key=emotion_scores.get)
    
    def _predict_potential_needs(self, intent: IntentType, entities: Dict) -> List[str]:
        needs_map = {
            IntentType.PRICE_QUERY: ["loan_calc", "community_consult", "area_compare"],
            IntentType.COMMUNITY_CONSULT: ["price_query", "school_query", "policy_interpret"],
            IntentType.PURCHASE_ADVICE: ["loan_calc", "policy_interpret", "area_compare"],
            IntentType.LOAN_CALC: ["policy_interpret", "purchase_advice"],
            IntentType.POLICY_INTERPRET: ["purchase_advice", "loan_calc"],
        }
        
        return needs_map.get(intent, [])


class DialogueStrategyEngine:
    def __init__(self):
        self.style_templates = self._load_style_templates()
        self.user_type_strategies = self._load_user_strategies()
    
    def _load_style_templates(self) -> Dict[DialogueStyle, Dict[str, str]]:
        return {
            DialogueStyle.ZHOUYU: {
                "greeting": "主公好，瑜在此恭候多时。请问有何吩咐？",
                "thinking": "主公且稍候，瑜正在为您谋划...",
                "success": "主公，此事瑜已为您安排妥当。",
                "error": "主公恕罪，瑜一时未能参透此中玄机。",
                "recommendation": "主公，瑜有一计，不知当讲不当讲...",
            },
            DialogueStyle.LUXUN: {
                "greeting": "主公，逊在此。有什么可以为您效劳的？",
                "thinking": "主公稍等，逊正在仔细分析...",
                "success": "主公，逊已为您完成分析。",
                "error": "主公恕罪，逊未能完成此任务。",
                "recommendation": "主公，逊有一建议，望您斟酌...",
            },
            DialogueStyle.PROFESSIONAL: {
                "greeting": "您好，我是房都督智能顾问，请问有什么可以帮您？",
                "thinking": "正在为您查询相关信息，请稍候...",
                "success": "查询完成，以下是相关信息。",
                "error": "抱歉，暂时无法获取相关信息。",
                "recommendation": "根据您的需求，我为您推荐以下内容：",
            },
            DialogueStyle.ENTHUSIASTIC: {
                "greeting": "您好呀！很高兴为您服务！有什么想了解的吗？",
                "thinking": "马上为您查询，请稍等一下下~",
                "success": "好啦！信息已经为您准备好了！",
                "error": "哎呀，出了点小问题，我再试试看！",
                "recommendation": "对了！我还有个好推荐给您！",
            },
            DialogueStyle.CONCISE: {
                "greeting": "您好，请说。",
                "thinking": "查询中...",
                "success": "查询完成。",
                "error": "查询失败。",
                "recommendation": "推荐：",
            },
        }
    
    def _load_user_strategies(self) -> Dict[UserType, Dict[str, Any]]:
        return {
            UserType.NEWBIE: {
                "style": DialogueStyle.ENTHUSIASTIC,
                "detail_level": "high",
                "explanation": True,
                "proactive": True,
            },
            UserType.NORMAL: {
                "style": DialogueStyle.PROFESSIONAL,
                "detail_level": "medium",
                "explanation": True,
                "proactive": False,
            },
            UserType.EXPERT: {
                "style": DialogueStyle.CONCISE,
                "detail_level": "low",
                "explanation": False,
                "proactive": False,
            },
            UserType.INVESTOR: {
                "style": DialogueStyle.PROFESSIONAL,
                "detail_level": "high",
                "explanation": True,
                "proactive": True,
                "focus": ["roi", "market_trend", "risk"],
            },
        }
    
    def get_style_for_user(self, user_type: UserType) -> DialogueStyle:
        strategy = self.user_type_strategies.get(user_type, {})
        return strategy.get("style", DialogueStyle.PROFESSIONAL)
    
    def get_template(self, style: DialogueStyle, template_type: str) -> str:
        style_templates = self.style_templates.get(style, {})
        return style_templates.get(template_type, "")
    
    def adapt_style(self, context: DialogueContext, feedback: str = "") -> DialogueStyle:
        if feedback:
            if "太啰嗦" in feedback or "简洁" in feedback:
                return DialogueStyle.CONCISE
            if "详细" in feedback or "解释" in feedback:
                return DialogueStyle.PROFESSIONAL
            if "周瑜" in feedback:
                return DialogueStyle.ZHOUYU
            if "陆逊" in feedback:
                return DialogueStyle.LUXUN
        
        return context.preferred_style


class SessionMemory:
    def __init__(self, session_id: str, user_id: str):
        self.session_id = session_id
        self.user_id = user_id
        self.history: List[Dict[str, str]] = []
        self.key_info: Dict[str, Any] = {}
        self.mentioned_entities: Dict[str, List[str]] = defaultdict(list)
        self.created_at = time.time()
    
    def add_turn(self, role: str, content: str):
        self.history.append({
            "role": role,
            "content": content,
            "timestamp": time.time()
        })
        
        if len(self.history) > 50:
            self.history = self.history[-50:]
    
    def get_recent_context(self, turns: int = 5) -> List[Dict[str, str]]:
        return self.history[-turns:] if len(self.history) >= turns else self.history
    
    def update_key_info(self, key: str, value: Any):
        self.key_info[key] = value
    
    def get_key_info(self, key: str) -> Optional[Any]:
        return self.key_info.get(key)


class ProactiveRecommender:
    def __init__(self):
        self.recommendation_rules = self._load_rules()
    
    def _load_rules(self) -> List[Dict[str, Any]]:
        return [
            {
                "trigger_intent": IntentType.PRICE_QUERY,
                "delay_seconds": 10,
                "recommendation_type": "related_community",
                "template": "主公，查询完房价后，是否需要了解周边小区的情况？"
            },
            {
                "trigger_intent": IntentType.COMMUNITY_CONSULT,
                "delay_seconds": 15,
                "recommendation_type": "area_compare",
                "template": "主公，是否需要对比周边其他小区？"
            },
            {
                "trigger_intent": IntentType.PURCHASE_ADVICE,
                "delay_seconds": 20,
                "recommendation_type": "loan_calc",
                "template": "主公，购房预算确定后，是否需要计算贷款月供？"
            },
        ]
    
    def should_recommend(
        self,
        last_intent: IntentType,
        silence_seconds: float,
        session: SessionMemory
    ) -> Optional[Dict[str, Any]]:
        for rule in self.recommendation_rules:
            if rule["trigger_intent"] == last_intent:
                if silence_seconds >= rule["delay_seconds"]:
                    if not self._already_recommended(session, rule["recommendation_type"]):
                        return {
                            "type": rule["recommendation_type"],
                            "template": rule["template"]
                        }
        
        if silence_seconds >= 30:
            return {
                "type": "engagement",
                "template": "主公，还有什么需要了解的吗？瑜随时为您效劳。"
            }
        
        return None
    
    def _already_recommended(self, session: SessionMemory, rec_type: str) -> bool:
        for turn in session.history[-5:]:
            if rec_type in turn.get("content", ""):
                return True
        return False


class LiAgent(LivingAgent):
    def __init__(self, agent_id: str = None, name: str = "礼部智能体"):
        super().__init__(
            agent_id=agent_id or f"li_{uuid.uuid4().hex[:8]}",
            name=name,
            species=AgentSpecies.LI,
            description="礼部智能体：负责用户咨询、意图识别、对话策略、主动推荐",
            initial_energy=100.0,
            max_energy=200.0,
        )
        
        self.intent_recognizer = IntentRecognizer()
        self.dialogue_engine = DialogueStrategyEngine()
        self.recommender = ProactiveRecommender()
        self.sessions: Dict[str, SessionMemory] = {}
        self._session_lock = threading.Lock()
        
        self._init_genes()
    
    def _init_genes(self):
        super()._init_genes()
        self.gene_pool.set("proactivity", 0.6, 0.1, 0.0, 1.0)
        self.gene_pool.set("empathy", 0.7, 0.1, 0.0, 1.0)
        self.gene_pool.set("response_speed", 0.8, 0.1, 0.0, 1.0)
    
    def get_or_create_session(self, session_id: str, user_id: str = "anonymous") -> SessionMemory:
        with self._session_lock:
            if session_id not in self.sessions:
                self.sessions[session_id] = SessionMemory(session_id, user_id)
            return self.sessions[session_id]
    
    async def handle_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        self.state = AgentState.BUSY
        
        try:
            action = task.get("action", "chat")
            
            if action == "chat":
                result = await self._handle_chat(task)
            elif action == "recognize_intent":
                result = await self._handle_intent_recognition(task)
            elif action == "get_recommendation":
                result = await self._handle_recommendation(task)
            else:
                result = {"success": False, "error": f"Unknown action: {action}"}
            
            if result.get("success"):
                self.gain_energy(5, "task_completed")
                self.stats["tasks_completed"] += 1
            else:
                self.consume_energy(2, "task_failed")
                self.stats["tasks_failed"] += 1
            
            self.state = AgentState.IDLE
            return result
            
        except Exception as e:
            logger.error(f"LiAgent task error: {e}")
            self.state = AgentState.ERROR
            self.consume_energy(5, "task_error")
            self.stats["tasks_failed"] += 1
            return {"success": False, "error": str(e)}
    
    async def _handle_chat(self, task: Dict[str, Any]) -> Dict[str, Any]:
        user_input = task.get("input", "")
        session_id = task.get("session_id", str(uuid.uuid4()))
        user_id = task.get("user_id", "anonymous")
        user_type_str = task.get("user_type", "normal")
        
        try:
            user_type = UserType(user_type_str)
        except ValueError:
            user_type = UserType.NORMAL
        
        session = self.get_or_create_session(session_id, user_id)
        session.add_turn("user", user_input)
        
        intent_result = self.intent_recognizer.recognize(user_input)
        
        style = self.dialogue_engine.get_style_for_user(user_type)
        
        context = DialogueContext(
            session_id=session_id,
            user_id=user_id,
            history=session.history,
            user_type=user_type,
            preferred_style=style,
            mentioned_entities=dict(session.mentioned_entities),
            last_intent=intent_result.intent
        )
        
        for entity_type, values in intent_result.entities.items():
            if isinstance(values, list):
                session.mentioned_entities[entity_type].extend([str(v) for v in values])
            else:
                session.mentioned_entities[entity_type].append(str(values))
        
        response = await self._generate_response(intent_result, context, session)
        
        session.add_turn("assistant", response)
        
        self.record_experience(
            state={"intent": intent_result.intent.value, "emotion": intent_result.emotion.value},
            action="respond",
            reward=1.0 if intent_result.confidence > 0.7 else 0.5,
            next_state={"response_length": len(response)}
        )
        
        return {
            "success": True,
            "response": response,
            "intent": {
                "type": intent_result.intent.value,
                "confidence": intent_result.confidence,
                "entities": intent_result.entities,
                "emotion": intent_result.emotion.value,
            },
            "potential_needs": intent_result.potential_needs,
            "session_id": session_id,
        }
    
    async def _handle_intent_recognition(self, task: Dict[str, Any]) -> Dict[str, Any]:
        text = task.get("text", "")
        intent_result = self.intent_recognizer.recognize(text)
        
        return {
            "success": True,
            "intent": intent_result.intent.value,
            "confidence": intent_result.confidence,
            "entities": intent_result.entities,
            "emotion": intent_result.emotion.value,
            "potential_needs": intent_result.potential_needs,
        }
    
    async def _handle_recommendation(self, task: Dict[str, Any]) -> Dict[str, Any]:
        session_id = task.get("session_id")
        last_intent_str = task.get("last_intent")
        silence_seconds = task.get("silence_seconds", 0)
        
        session = self.sessions.get(session_id)
        if not session:
            return {"success": False, "error": "Session not found"}
        
        try:
            last_intent = IntentType(last_intent_str) if last_intent_str else None
        except ValueError:
            last_intent = None
        
        recommendation = self.recommender.should_recommend(
            last_intent=last_intent,
            silence_seconds=silence_seconds,
            session=session
        )
        
        return {
            "success": True,
            "recommendation": recommendation
        }
    
    async def _generate_response(
        self,
        intent_result: IntentResult,
        context: DialogueContext,
        session: SessionMemory
    ) -> str:
        style = context.preferred_style
        
        greeting = self.dialogue_engine.get_template(style, "greeting")
        
        if intent_result.intent == IntentType.PRICE_QUERY:
            entities = intent_result.entities
            if "district" in entities:
                district = entities["district"][0]
                return f"主公，关于{district}的房价，瑜已为您查询。该区域目前均价约在X万/㎡左右，具体还需看小区和户型。是否需要了解具体小区的详情？"
            return f"主公，请问您想查询哪个区域的房价？瑜可为您详细分析。"
        
        elif intent_result.intent == IntentType.COMMUNITY_CONSULT:
            return f"主公，关于小区咨询，瑜需要了解您关注的具体区域或小区名称，以便为您提供详细信息。"
        
        elif intent_result.intent == IntentType.PURCHASE_ADVICE:
            return f"主公，购房大事，瑜当为您仔细谋划。请问您的预算大概是多少？对区域有什么偏好？"
        
        elif intent_result.intent == IntentType.LOAN_CALC:
            return f"主公，关于贷款计算，请告知您的贷款金额、年限，瑜可为您计算月供和利息。"
        
        elif intent_result.intent == IntentType.POLICY_INTERPRET:
            return f"主公，关于购房政策，目前首套房首付最低20%，二套房30%。具体政策因城市而异，请问您关注哪个城市？"
        
        elif intent_result.intent == IntentType.COMPLAINT:
            return f"主公息怒，瑜深感抱歉。请问具体遇到了什么问题？瑜一定为您妥善处理。"
        
        elif intent_result.intent == IntentType.CHITCHAT:
            return f"主公好，瑜在此恭候。请问有什么可以为您效劳的？"
        
        else:
            return f"主公，瑜已收到您的咨询，正在为您分析中..."
    
    async def _create_child(self, child_id: str, child_genes: GenePool) -> Optional['LiAgent']:
        child = LiAgent(agent_id=child_id, name=f"{self.name}的后代")
        child.gene_pool = child_genes
        return child


class GongAgent(LivingAgent):
    def __init__(self, agent_id: str = None, name: str = "工部智能体"):
        super().__init__(
            agent_id=agent_id or f"gong_{uuid.uuid4().hex[:8]}",
            name=name,
            species=AgentSpecies.GONG,
            description="工部智能体：负责任务解析、个性化报告生成、质量评估",
            initial_energy=100.0,
            max_energy=200.0,
        )
        
        self._init_genes()
    
    def _init_genes(self):
        super()._init_genes()
        self.gene_pool.set("analysis_depth", 0.7, 0.1, 0.0, 1.0)
        self.gene_pool.set("report_detail", 0.8, 0.1, 0.0, 1.0)
    
    async def handle_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        self.state = AgentState.BUSY
        
        try:
            action = task.get("action", "analyze")
            
            if action == "parse_task":
                result = await self._parse_task(task)
            elif action == "generate_report":
                result = await self._generate_report(task)
            elif action == "evaluate_quality":
                result = await self._evaluate_quality(task)
            else:
                result = await self._analyze(task)
            
            if result.get("success"):
                self.gain_energy(10, "task_completed")
                self.stats["tasks_completed"] += 1
            else:
                self.consume_energy(3, "task_failed")
                self.stats["tasks_failed"] += 1
            
            self.state = AgentState.IDLE
            return result
            
        except Exception as e:
            logger.error(f"GongAgent task error: {e}")
            self.state = AgentState.ERROR
            return {"success": False, "error": str(e)}
    
    async def _parse_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        user_input = task.get("input", "")
        
        task_type = self._identify_task_type(user_input)
        params = self._extract_params(user_input)
        missing_params = self._identify_missing_params(task_type, params)
        
        return {
            "success": True,
            "task_type": task_type,
            "params": params,
            "missing_params": missing_params,
            "priority": self._calculate_priority(task),
        }
    
    def _identify_task_type(self, text: str) -> str:
        if "对比" in text or "比较" in text:
            return "area_compare"
        if "分析" in text or "报告" in text:
            return "community_analysis"
        if "预测" in text or "趋势" in text:
            return "price_prediction"
        if "投资" in text or "回报" in text:
            return "investment_analysis"
        return "general_analysis"
    
    def _extract_params(self, text: str) -> Dict[str, Any]:
        params = {}
        
        district_match = re.search(r'(南山|福田|罗湖|宝安|龙岗|龙华)', text)
        if district_match:
            params["district"] = district_match.group(1)
        
        price_match = re.search(r'(\d+(?:\.\d+)?)\s*(万)?', text)
        if price_match:
            params["budget"] = float(price_match.group(1))
        
        area_match = re.search(r'(\d+(?:\.\d+)?)\s*(㎡|平方米|平)', text)
        if area_match:
            params["area"] = float(area_match.group(1))
        
        return params
    
    def _identify_missing_params(self, task_type: str, params: Dict) -> List[str]:
        required = {
            "area_compare": ["district"],
            "community_analysis": ["district"],
            "investment_analysis": ["budget"],
        }
        
        missing = []
        for param in required.get(task_type, []):
            if param not in params:
                missing.append(param)
        
        return missing
    
    def _calculate_priority(self, task: Dict) -> int:
        if task.get("is_premium"):
            return 10
        if task.get("is_urgent"):
            return 8
        return 5
    
    async def _generate_report(self, task: Dict[str, Any]) -> Dict[str, Any]:
        report_type = task.get("report_type", "standard")
        data = task.get("data", {})
        user_profile = task.get("user_profile", {})
        
        report = {
            "title": f"房产分析报告 - {data.get('district', '未知区域')}",
            "generated_at": datetime.now().isoformat(),
            "sections": [
                {"title": "执行摘要", "content": "本报告为您分析该区域的房产市场情况..."},
                {"title": "价格走势", "content": "近三个月价格趋势分析..."},
                {"title": "周边配套", "content": "学校、医院、商业等配套设施..."},
                {"title": "投资建议", "content": "根据您的需求，建议关注..."},
            ],
            "quality_score": 0.85,
        }
        
        return {
            "success": True,
            "report": report,
        }
    
    async def _evaluate_quality(self, task: Dict[str, Any]) -> Dict[str, Any]:
        report = task.get("report", {})
        
        scores = {
            "accuracy": 0.9,
            "completeness": 0.85,
            "timeliness": 0.95,
            "readability": 0.88,
        }
        
        overall = sum(scores.values()) / len(scores)
        
        return {
            "success": True,
            "scores": scores,
            "overall_score": overall,
            "passed": overall >= 0.7,
        }
    
    async def _analyze(self, task: Dict[str, Any]) -> Dict[str, Any]:
        return await self._parse_task(task)
    
    async def _create_child(self, child_id: str, child_genes: GenePool) -> Optional['GongAgent']:
        child = GongAgent(agent_id=child_id, name=f"{self.name}的后代")
        child.gene_pool = child_genes
        return child


class HuAgent(LivingAgent):
    def __init__(self, agent_id: str = None, name: str = "户部智能体"):
        super().__init__(
            agent_id=agent_id or f"hu_{uuid.uuid4().hex[:8]}",
            name=name,
            species=AgentSpecies.HU,
            description="户部智能体：负责动态积分定价、活动策划、会员等级管理",
            initial_energy=100.0,
            max_energy=200.0,
        )
        
        self._init_genes()
    
    def _init_genes(self):
        super()._init_genes()
        self.gene_pool.set("pricing_sensitivity", 0.5, 0.1, 0.0, 1.0)
        self.gene_pool.set("promotion_frequency", 0.6, 0.1, 0.0, 1.0)
    
    async def handle_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        self.state = AgentState.BUSY
        
        try:
            action = task.get("action", "calculate_points")
            
            if action == "calculate_points":
                result = await self._calculate_points(task)
            elif action == "plan_activity":
                result = await self._plan_activity(task)
            elif action == "adjust_level":
                result = await self._adjust_member_level(task)
            else:
                result = {"success": False, "error": f"Unknown action: {action}"}
            
            if result.get("success"):
                self.gain_energy(5, "task_completed")
                self.stats["tasks_completed"] += 1
            
            self.state = AgentState.IDLE
            return result
            
        except Exception as e:
            logger.error(f"HuAgent task error: {e}")
            self.state = AgentState.ERROR
            return {"success": False, "error": str(e)}
    
    async def _calculate_points(self, task: Dict[str, Any]) -> Dict[str, Any]:
        task_type = task.get("task_type", "general")
        queue_length = task.get("queue_length", 0)
        
        base_points = {
            "consultation": 10,
            "report": 20,
            "analysis": 30,
        }
        
        base = base_points.get(task_type, 10)
        
        if queue_length > 100:
            multiplier = 1.5
        elif queue_length < 10:
            multiplier = 0.8
        else:
            multiplier = 1.0
        
        final_points = int(base * multiplier)
        
        return {
            "success": True,
            "base_points": base,
            "multiplier": multiplier,
            "final_points": final_points,
        }
    
    async def _plan_activity(self, task: Dict[str, Any]) -> Dict[str, Any]:
        user_segment = task.get("user_segment", "normal")
        
        activity_templates = {
            "newbie": {
                "name": "新用户欢迎礼",
                "type": "welcome",
                "reward": 50,
                "duration_days": 7,
            },
            "active": {
                "name": "活跃用户专属福利",
                "type": "bonus",
                "reward": 30,
                "duration_days": 3,
            },
            "dormant": {
                "name": "回归用户唤醒礼",
                "type": "recall",
                "reward": 100,
                "duration_days": 14,
            },
        }
        
        activity = activity_templates.get(user_segment, activity_templates["active"])
        
        return {
            "success": True,
            "activity": activity,
        }
    
    async def _adjust_member_level(self, task: Dict[str, Any]) -> Dict[str, Any]:
        user_id = task.get("user_id")
        points = task.get("points", 0)
        activity = task.get("activity", 0)
        
        score = points * 0.6 + activity * 0.4
        
        if score >= 10000:
            level = "platinum"
        elif score >= 5000:
            level = "gold"
        elif score >= 1000:
            level = "silver"
        else:
            level = "bronze"
        
        return {
            "success": True,
            "level": level,
            "score": score,
        }
    
    async def _create_child(self, child_id: str, child_genes: GenePool) -> Optional['HuAgent']:
        child = HuAgent(agent_id=child_id, name=f"{self.name}的后代")
        child.gene_pool = child_genes
        return child


class BingAgent(LivingAgent):
    def __init__(self, agent_id: str = None, name: str = "兵部智能体"):
        super().__init__(
            agent_id=agent_id or f"bing_{uuid.uuid4().hex[:8]}",
            name=name,
            species=AgentSpecies.BING,
            description="兵部智能体：负责数据源选择、自适应采集、异常检测",
            initial_energy=100.0,
            max_energy=200.0,
        )
        
        self._init_genes()
    
    def _init_genes(self):
        super()._init_genes()
        self.gene_pool.set("collection_frequency", 0.7, 0.1, 0.0, 1.0)
        self.gene_pool.set("anomaly_threshold", 0.8, 0.1, 0.0, 1.0)
    
    async def handle_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        self.state = AgentState.BUSY
        
        try:
            action = task.get("action", "collect")
            
            if action == "select_source":
                result = await self._select_data_source(task)
            elif action == "adjust_frequency":
                result = await self._adjust_collection_frequency(task)
            elif action == "detect_anomaly":
                result = await self._detect_data_anomaly(task)
            else:
                result = {"success": True, "message": "Collection task queued"}
            
            if result.get("success"):
                self.gain_energy(8, "task_completed")
                self.stats["tasks_completed"] += 1
            
            self.state = AgentState.IDLE
            return result
            
        except Exception as e:
            logger.error(f"BingAgent task error: {e}")
            self.state = AgentState.ERROR
            return {"success": False, "error": str(e)}
    
    async def _select_data_source(self, task: Dict[str, Any]) -> Dict[str, Any]:
        data_type = task.get("data_type", "price")
        urgency = task.get("urgency", "normal")
        
        sources = {
            "price": ["lianji", "beike", "anjuke"],
            "policy": ["gov_site", "news_portal"],
            "market": ["stats_bureau", "research_report"],
        }
        
        available = sources.get(data_type, sources["price"])
        
        if urgency == "high":
            selected = available[:2]
        else:
            selected = available[:1]
        
        return {
            "success": True,
            "selected_sources": selected,
            "backup_sources": available[len(selected):],
        }
    
    async def _adjust_collection_frequency(self, task: Dict[str, Any]) -> Dict[str, Any]:
        change_rate = task.get("change_rate", 0)
        demand_level = task.get("demand_level", "normal")
        
        base_interval = 3600
        
        if change_rate > 0.1:
            multiplier = 0.5
        elif change_rate < 0.01:
            multiplier = 2.0
        else:
            multiplier = 1.0
        
        if demand_level == "high":
            multiplier *= 0.5
        
        new_interval = int(base_interval * multiplier)
        
        return {
            "success": True,
            "new_interval_seconds": new_interval,
            "multiplier": multiplier,
        }
    
    async def _detect_data_anomaly(self, task: Dict[str, Any]) -> Dict[str, Any]:
        data = task.get("data", [])
        threshold = self.gene_pool.get("anomaly_threshold", 0.8)
        
        anomalies = []
        
        if data:
            mean = sum(data) / len(data)
            std = (sum((x - mean) ** 2 for x in data) / len(data)) ** 0.5
            
            for i, value in enumerate(data):
                z_score = abs(value - mean) / std if std > 0 else 0
                if z_score > 3:
                    anomalies.append({
                        "index": i,
                        "value": value,
                        "z_score": z_score,
                        "type": "statistical"
                    })
        
        return {
            "success": True,
            "anomaly_count": len(anomalies),
            "anomalies": anomalies[:10],
        }
    
    async def _create_child(self, child_id: str, child_genes: GenePool) -> Optional['BingAgent']:
        child = BingAgent(agent_id=child_id, name=f"{self.name}的后代")
        child.gene_pool = child_genes
        return child


class Li2Agent(LivingAgent):
    def __init__(self, agent_id: str = None, name: str = "吏部智能体"):
        super().__init__(
            agent_id=agent_id or f"li2_{uuid.uuid4().hex[:8]}",
            name=name,
            species=AgentSpecies.LI2,
            description="吏部智能体：负责智能体健康监控、资源调度、繁殖管理",
            initial_energy=150.0,
            max_energy=300.0,
        )
        
        self._init_genes()
    
    def _init_genes(self):
        super()._init_genes()
        self.gene_pool.set("monitor_interval", 60, 0.1, 10, 300)
        self.gene_pool.set("scale_threshold", 0.8, 0.1, 0.5, 1.0)
    
    async def handle_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        self.state = AgentState.BUSY
        
        try:
            action = task.get("action", "monitor")
            
            if action == "health_check":
                result = await self._health_check(task)
            elif action == "scale_resources":
                result = await self._scale_resources(task)
            elif action == "manage_reproduction":
                result = await self._manage_reproduction(task)
            else:
                result = {"success": True, "message": "Monitoring active"}
            
            if result.get("success"):
                self.gain_energy(3, "task_completed")
                self.stats["tasks_completed"] += 1
            
            self.state = AgentState.IDLE
            return result
            
        except Exception as e:
            logger.error(f"Li2Agent task error: {e}")
            self.state = AgentState.ERROR
            return {"success": False, "error": str(e)}
    
    async def _health_check(self, task: Dict[str, Any]) -> Dict[str, Any]:
        agents = agent_registry.get_all()
        
        health_report = {
            "total": len(agents),
            "healthy": 0,
            "warning": 0,
            "critical": 0,
            "details": [],
        }
        
        for agent in agents:
            status = agent.get_status()
            energy = status["energy"]
            
            if energy >= 50:
                health_report["healthy"] += 1
                status_level = "healthy"
            elif energy >= 20:
                health_report["warning"] += 1
                status_level = "warning"
            else:
                health_report["critical"] += 1
                status_level = "critical"
            
            health_report["details"].append({
                "agent_id": status["agent_id"],
                "name": status["name"],
                "energy": energy,
                "status": status_level,
            })
        
        return {
            "success": True,
            "health_report": health_report,
        }
    
    async def _scale_resources(self, task: Dict[str, Any]) -> Dict[str, Any]:
        queue_length = task.get("queue_length", 0)
        current_load = task.get("current_load", 0.5)
        
        threshold = self.gene_pool.get("scale_threshold", 0.8)
        
        if current_load > threshold:
            action = "scale_up"
            replicas = 2
        elif current_load < 0.3:
            action = "scale_down"
            replicas = -1
        else:
            action = "maintain"
            replicas = 0
        
        return {
            "success": True,
            "action": action,
            "replicas": replicas,
            "current_load": current_load,
        }
    
    async def _manage_reproduction(self, task: Dict[str, Any]) -> Dict[str, Any]:
        agents = agent_registry.get_all()
        
        reproducible = [a for a in agents if a.can_reproduce()]
        low_energy = [a for a in agents if a.energy_system.get_level() < 20]
        
        recommendations = []
        
        for agent in reproducible[:3]:
            recommendations.append({
                "agent_id": agent.agent_id,
                "action": "reproduce",
                "reason": "High energy and performance",
            })
        
        for agent in low_energy[:2]:
            recommendations.append({
                "agent_id": agent.agent_id,
                "action": "hibernate",
                "reason": "Low energy",
            })
        
        return {
            "success": True,
            "reproducible_count": len(reproducible),
            "low_energy_count": len(low_energy),
            "recommendations": recommendations,
        }
    
    async def _create_child(self, child_id: str, child_genes: GenePool) -> Optional['Li2Agent']:
        child = Li2Agent(agent_id=child_id, name=f"{self.name}的后代")
        child.gene_pool = child_genes
        return child


class XingAgent(LivingAgent):
    def __init__(self, agent_id: str = None, name: str = "刑部智能体"):
        super().__init__(
            agent_id=agent_id or f"xing_{uuid.uuid4().hex[:8]}",
            name=name,
            species=AgentSpecies.XING,
            description="刑部智能体：负责风险拦截、用户行为画像、安全审计",
            initial_energy=120.0,
            max_energy=250.0,
        )
        
        self._init_genes()
    
    def _init_genes(self):
        super()._init_genes()
        self.gene_pool.set("risk_threshold", 0.7, 0.1, 0.5, 0.95)
        self.gene_pool.set("sensitivity", 0.8, 0.1, 0.5, 1.0)
    
    async def handle_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        self.state = AgentState.BUSY
        
        try:
            action = task.get("action", "risk_check")
            
            if action == "risk_check":
                result = await self._risk_check(task)
            elif action == "build_profile":
                result = await self._build_user_profile(task)
            elif action == "audit":
                result = await self._audit_action(task)
            else:
                result = {"success": True, "message": "Security monitoring active"}
            
            if result.get("success"):
                self.gain_energy(5, "task_completed")
                self.stats["tasks_completed"] += 1
            
            self.state = AgentState.IDLE
            return result
            
        except Exception as e:
            logger.error(f"XingAgent task error: {e}")
            self.state = AgentState.ERROR
            return {"success": False, "error": str(e)}
    
    async def _risk_check(self, task: Dict[str, Any]) -> Dict[str, Any]:
        user_id = task.get("user_id")
        action = task.get("action_type")
        context = task.get("context", {})
        
        risk_score = 0.0
        risk_factors = []
        
        ip = context.get("ip", "")
        if self._is_suspicious_ip(ip):
            risk_score += 0.3
            risk_factors.append("suspicious_ip")
        
        frequency = context.get("request_frequency", 0)
        if frequency > 100:
            risk_score += 0.4
            risk_factors.append("high_frequency")
        
        threshold = self.gene_pool.get("risk_threshold", 0.7)
        
        if risk_score >= threshold:
            decision = "block"
        elif risk_score >= threshold * 0.5:
            decision = "challenge"
        else:
            decision = "allow"
        
        return {
            "success": True,
            "risk_score": risk_score,
            "risk_factors": risk_factors,
            "decision": decision,
        }
    
    def _is_suspicious_ip(self, ip: str) -> bool:
        return ip.startswith("10.") or ip in ["127.0.0.1"]
    
    async def _build_user_profile(self, task: Dict[str, Any]) -> Dict[str, Any]:
        user_id = task.get("user_id")
        behaviors = task.get("behaviors", [])
        
        profile = {
            "user_id": user_id,
            "active_hours": self._analyze_active_hours(behaviors),
            "common_actions": self._analyze_common_actions(behaviors),
            "trust_score": self._calculate_trust_score(behaviors),
            "risk_level": "low",
        }
        
        return {
            "success": True,
            "profile": profile,
        }
    
    def _analyze_active_hours(self, behaviors: List) -> List[int]:
        hours = defaultdict(int)
        for b in behaviors:
            if "timestamp" in b:
                hour = datetime.fromtimestamp(b["timestamp"]).hour
                hours[hour] += 1
        
        return sorted([h for h, c in hours.items() if c > len(behaviors) * 0.1])
    
    def _analyze_common_actions(self, behaviors: List) -> List[str]:
        actions = defaultdict(int)
        for b in behaviors:
            action = b.get("action", "unknown")
            actions[action] += 1
        
        return sorted(actions.keys(), key=lambda x: actions[x], reverse=True)[:5]
    
    def _calculate_trust_score(self, behaviors: List) -> float:
        if not behaviors:
            return 0.5
        
        violations = sum(1 for b in behaviors if b.get("violation"))
        return max(0, 1 - violations / len(behaviors))
    
    async def _audit_action(self, task: Dict[str, Any]) -> Dict[str, Any]:
        action_type = task.get("action_type")
        user_id = task.get("user_id")
        details = task.get("details", {})
        
        audit_record = {
            "timestamp": time.time(),
            "action_type": action_type,
            "user_id": user_id,
            "details": details,
            "audited_by": self.agent_id,
        }
        
        self.write_blackboard(
            f"audit/{user_id}/{time.time()}",
            audit_record,
            ttl=86400 * 30
        )
        
        return {
            "success": True,
            "audit_record": audit_record,
        }
    
    async def _create_child(self, child_id: str, child_genes: GenePool) -> Optional['XingAgent']:
        child = XingAgent(agent_id=child_id, name=f"{self.name}的后代")
        child.gene_pool = child_genes
        return child


def create_ministry_agents() -> Dict[str, LivingAgent]:
    agents = {
        "li": LiAgent(),
        "gong": GongAgent(),
        "hu": HuAgent(),
        "bing": BingAgent(),
        "li2": Li2Agent(),
        "xing": XingAgent(),
    }
    
    for agent in agents.values():
        agent_registry.register(agent)
    
    return agents


ministry_agents = None

def get_ministry_agents() -> Dict[str, LivingAgent]:
    global ministry_agents
    if ministry_agents is None:
        ministry_agents = create_ministry_agents()
    return ministry_agents
