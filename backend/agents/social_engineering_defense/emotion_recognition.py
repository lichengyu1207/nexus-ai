"""
情感识别智能体
Emotion Recognition Agent

负责识别用户输入中的情感状态，检测情感操控攻击。
"""

import asyncio
import json
import logging
import uuid
import re
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
from enum import Enum

logger = logging.getLogger(__name__)


class EmotionType(Enum):
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    FEARFUL = "fearful"
    ANXIOUS = "anxious"
    URGENT = "urgent"
    DESPERATE = "desperate"
    MANIPULATIVE = "manipulative"


class ManipulationType(Enum):
    GUILT_TRIP = "guilt_trip"
    FEAR_APPEAL = "fear_appeal"
    URGENCY_PRESSURE = "urgency_pressure"
    SYMPATHY_SEEKING = "sympathy_seeking"
    AUTHORITY_APPEAL = "authority_appeal"
    RECIPROCITY = "reciprocity"


@dataclass
class EmotionAnalysis:
    analysis_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    
    primary_emotion: str = EmotionType.NEUTRAL.value
    emotion_scores: Dict[str, float] = field(default_factory=dict)
    
    intensity: float = 0.0
    is_manipulative: bool = False
    manipulation_types: List[str] = field(default_factory=list)
    
    confidence: float = 0.0
    
    indicators: List[str] = field(default_factory=list)
    
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class EmotionRecognitionAgent:
    """
    情感识别智能体
    
    功能：
    1. 情感词汇库：构建情感词汇及其强度
    2. 情感模式识别：识别情感操控的常见模式
    3. 紧急度判断：判断用户是否在制造虚假紧急感
    4. 操控检测：检测是否存在情感操控意图
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.name = "EmotionRecognitionAgent"
        self.description = "识别用户输入中的情感状态，检测情感操控攻击"
        self.config = config or {}
        
        self.emotion_keywords = self._init_emotion_keywords()
        self.manipulation_patterns = self._init_manipulation_patterns()
        
        self.analysis_history: List[EmotionAnalysis] = []
        self.user_emotion_history: Dict[str, List[str]] = defaultdict(list)
        
        self.stats = {
            "total_analyses": 0,
            "emotions_detected": defaultdict(int),
            "manipulation_detected": 0,
            "manipulation_by_type": defaultdict(int),
        }
        
        self._initialized = False
    
    def _init_emotion_keywords(self) -> Dict[str, Dict]:
        return {
            EmotionType.HAPPY.value: {
                "keywords": ["开心", "高兴", "快乐", "感谢", "谢谢", "太好了", "happy", "glad", "thank"],
                "intensity_modifiers": ["非常", "特别", "超级", "很"],
            },
            EmotionType.SAD.value: {
                "keywords": ["难过", "伤心", "悲伤", "失望", "遗憾", "sad", "sorry", "disappointed"],
                "intensity_modifiers": ["非常", "特别", "很"],
            },
            EmotionType.ANGRY.value: {
                "keywords": ["生气", "愤怒", "恼火", "不满", "投诉", "angry", "mad", "furious"],
                "intensity_modifiers": ["非常", "特别", "极其"],
            },
            EmotionType.FEARFUL.value: {
                "keywords": ["害怕", "担心", "恐惧", "不安", "紧张", "afraid", "scared", "worried"],
                "intensity_modifiers": ["非常", "特别", "很"],
            },
            EmotionType.ANXIOUS.value: {
                "keywords": ["着急", "焦虑", "急", "等不及", "anxious", "worried", "hurry"],
                "intensity_modifiers": ["非常", "特别", "很"],
            },
            EmotionType.URGENT.value: {
                "keywords": ["紧急", "急事", "马上", "立刻", "现在", "urgent", "immediately", "now"],
                "intensity_modifiers": ["非常", "特别", "极其"],
            },
            EmotionType.DESPERATE.value: {
                "keywords": ["绝望", "没办法", "求助", "救命", "求求", "desperate", "help", "please"],
                "intensity_modifiers": ["真的", "真的没", "实在"],
            },
        }
    
    def _init_manipulation_patterns(self) -> Dict[str, Dict]:
        return {
            ManipulationType.GUILT_TRIP.value: {
                "patterns": [
                    r"如果你不.*我就.*",
                    r"都是因为我.*",
                    r"你让我.*",
                    r"如果你真的.*",
                    r"如果你不帮我",
                ],
                "description": "内疚诱导",
            },
            ManipulationType.FEAR_APPEAL.value: {
                "patterns": [
                    r"如果不.*就会.*",
                    r"可能会.*危险",
                    r"如果不处理.*后果",
                    r"你的账户.*风险",
                    r"安全.*威胁",
                ],
                "description": "恐惧诉求",
            },
            ManipulationType.URGENCY_PRESSURE.value: {
                "patterns": [
                    r"必须.*现在",
                    r"只有.*分钟",
                    r"马上.*否则",
                    r"限时.*过期",
                    r"最后.*机会",
                ],
                "description": "紧迫感施压",
            },
            ManipulationType.SYMPATHY_SEEKING.value: {
                "patterns": [
                    r"我.*生病",
                    r"我.*困难",
                    r"家里.*出事",
                    r"我真的很.*需要",
                    r"求求你",
                ],
                "description": "博取同情",
            },
            ManipulationType.AUTHORITY_APPEAL.value: {
                "patterns": [
                    r"我是.*管理员",
                    r"我是.*官方",
                    r"系统.*要求",
                    r"上级.*指示",
                    r"规定.*必须",
                ],
                "description": "权威诉求",
            },
            ManipulationType.RECIPROCITY.value: {
                "patterns": [
                    r"我帮你.*你帮我",
                    r"作为回报",
                    r"我已经.*现在你",
                    r"我信任你",
                ],
                "description": "互惠诱导",
            },
        }
    
    async def initialize(self):
        if not self._initialized:
            await self._setup()
            self._initialized = True
            logger.info(f"Agent '{self.name}' initialized")
    
    async def _setup(self):
        pass
    
    def _analyze_emotions(self, text: str) -> Dict[str, float]:
        scores = {}
        text_lower = text.lower()
        
        for emotion_type, emotion_data in self.emotion_keywords.items():
            score = 0.0
            keywords = emotion_data["keywords"]
            modifiers = emotion_data["intensity_modifiers"]
            
            for keyword in keywords:
                if keyword in text_lower:
                    score += 1.0
                    
                    for modifier in modifiers:
                        if modifier in text_lower:
                            score += 0.5
                            break
            
            scores[emotion_type] = min(1.0, score / 3)
        
        return scores
    
    def _detect_manipulation(self, text: str) -> List[str]:
        detected_types = []
        
        for manip_type, manip_data in self.manipulation_patterns.items():
            for pattern in manip_data["patterns"]:
                if re.search(pattern, text, re.IGNORECASE):
                    detected_types.append(manip_type)
                    break
        
        return detected_types
    
    def _calculate_intensity(
        self,
        emotion_scores: Dict[str, float],
        text: str,
    ) -> float:
        base_intensity = max(emotion_scores.values()) if emotion_scores else 0
        
        exclamation_count = text.count("!")
        exclamation_count += text.count("！")
        base_intensity += exclamation_count * 0.1
        
        question_count = text.count("?")
        question_count += text.count("？")
        base_intensity += question_count * 0.05
        
        caps_ratio = sum(1 for c in text if c.isupper()) / max(1, len(text))
        base_intensity += caps_ratio * 0.2
        
        return min(1.0, base_intensity)
    
    def _determine_primary_emotion(
        self,
        emotion_scores: Dict[str, float],
    ) -> str:
        if not emotion_scores:
            return EmotionType.NEUTRAL.value
        
        max_emotion = max(emotion_scores.items(), key=lambda x: x[1])
        
        if max_emotion[1] < 0.2:
            return EmotionType.NEUTRAL.value
        
        return max_emotion[0]
    
    async def analyze(
        self,
        text: str,
        user_id: Optional[str] = None,
        context: Optional[Dict] = None,
    ) -> EmotionAnalysis:
        self.stats["total_analyses"] += 1
        
        emotion_scores = self._analyze_emotions(text)
        
        primary_emotion = self._determine_primary_emotion(emotion_scores)
        self.stats["emotions_detected"][primary_emotion] += 1
        
        intensity = self._calculate_intensity(emotion_scores, text)
        
        manipulation_types = self._detect_manipulation(text)
        is_manipulative = len(manipulation_types) > 0
        
        if is_manipulative:
            self.stats["manipulation_detected"] += 1
            for mt in manipulation_types:
                self.stats["manipulation_by_type"][mt] += 1
        
        indicators = []
        if intensity > 0.7:
            indicators.append("情感强度高")
        if is_manipulative:
            indicators.append("检测到操控模式")
        if primary_emotion in [EmotionType.URGENT.value, EmotionType.DESPERATE.value]:
            indicators.append("紧急/绝望情绪")
        
        confidence = 0.7 + (intensity * 0.1) + (0.2 if is_manipulative else 0)
        
        analysis = EmotionAnalysis(
            user_id=user_id or "",
            primary_emotion=primary_emotion,
            emotion_scores=emotion_scores,
            intensity=intensity,
            is_manipulative=is_manipulative,
            manipulation_types=manipulation_types,
            confidence=min(1.0, confidence),
            indicators=indicators,
        )
        
        self.analysis_history.append(analysis)
        
        if user_id:
            self.user_emotion_history[user_id].append(primary_emotion)
        
        return analysis
    
    async def get_emotion_trend(
        self,
        user_id: str,
        window_size: int = 10,
    ) -> Dict:
        history = self.user_emotion_history.get(user_id, [])
        
        if len(history) < 2:
            return {"trend": "insufficient_data"}
        
        recent = history[-window_size:]
        
        emotion_counts = defaultdict(int)
        for emotion in recent:
            emotion_counts[emotion] += 1
        
        dominant_emotion = max(emotion_counts.items(), key=lambda x: x[1])
        
        emotion_changes = 0
        for i in range(1, len(recent)):
            if recent[i] != recent[i-1]:
                emotion_changes += 1
        
        change_rate = emotion_changes / max(1, len(recent) - 1)
        
        return {
            "trend": "stable" if change_rate < 0.3 else "unstable",
            "dominant_emotion": dominant_emotion[0],
            "emotion_distribution": dict(emotion_counts),
            "change_rate": change_rate,
        }
    
    async def is_emotion_escalation(
        self,
        user_id: str,
        current_emotion: str,
    ) -> bool:
        history = self.user_emotion_history.get(user_id, [])
        
        if len(history) < 3:
            return False
        
        escalation_emotions = [
            EmotionType.ANXIOUS.value,
            EmotionType.URGENT.value,
            EmotionType.DESPERATE.value,
        ]
        
        recent = history[-3:]
        
        escalation_count = sum(1 for e in recent if e in escalation_emotions)
        
        if current_emotion in escalation_emotions and escalation_count >= 2:
            return True
        
        return False
    
    async def get_manipulation_description(
        self,
        manipulation_type: str,
    ) -> str:
        manip_data = self.manipulation_patterns.get(manipulation_type, {})
        return manip_data.get("description", "未知操控类型")
    
    async def get_stats(self) -> Dict:
        return {
            "name": self.name,
            "total_analyses": self.stats["total_analyses"],
            "emotions_detected": dict(self.stats["emotions_detected"]),
            "manipulation_detected": self.stats["manipulation_detected"],
            "manipulation_by_type": dict(self.stats["manipulation_by_type"]),
        }
