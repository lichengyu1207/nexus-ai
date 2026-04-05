# -*- coding: utf-8 -*-
"""
Emotion Detector
Detects user emotion from text input
"""
import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json

logger = logging.getLogger(__name__)


class EmotionType(Enum):
    NEUTRAL = "neutral"
    ANXIOUS = "anxious"
    EXCITED = "excited"
    CONFUSED = "confused"
    FRUSTRATED = "frustrated"
    HOPEFUL = "hopeful"
    SAD = "sad"
    ANGRY = "angry"


@dataclass
class EmotionResult:
    emotion: str
    score: float
    confidence: float
    keywords: List[str]
    suggested_response_style: str


EMOTION_PATTERNS = {
    EmotionType.ANXIOUS: {
        "keywords": ["焦虑", "担心", "紧张", "不安", "害怕", "恐惧", "压力", "着急", "忧虑", "忐忑", "恐慌", "心慌", "烦躁"],
        "patterns": [
            r"(怎么办|如何是好)",
            r"(会不会|是不是).{0,10}(问题|风险)",
            r"(很担心|非常担心)",
            r"(睡不着|失眠)",
            r"(压力很大|压力大)"
        ],
        "intensity_modifiers": ["非常", "很", "特别", "极其", "相当"]
    },
    EmotionType.EXCITED: {
        "keywords": ["兴奋", "激动", "期待", "开心", "高兴", "喜悦", "振奋", "憧憬", "向往", "热情"],
        "patterns": [
            r"(太好了|太棒了)",
            r"(迫不及待|跃跃欲试)",
            r"(终于|总算)",
            r"(机会来了|时机到了)"
        ],
        "intensity_modifiers": ["非常", "特别", "超级", "极其"]
    },
    EmotionType.CONFUSED: {
        "keywords": ["困惑", "迷茫", "不解", "疑惑", "糊涂", "不懂", "不明白", "搞不懂", "不清楚", "纳闷"],
        "patterns": [
            r"(为什么|怎么回事)",
            r"(不理解|搞不懂)",
            r"(到底是|究竟)",
            r"(怎么办|如何选择)"
        ],
        "intensity_modifiers": ["很", "非常", "特别"]
    },
    EmotionType.FRUSTRATED: {
        "keywords": ["沮丧", "失望", "挫败", "无奈", "灰心", "泄气", "气馁", "受挫", "打击"],
        "patterns": [
            r"(又失败了|又没成功)",
            r"(总是|老是).{0,10}(不行|失败)",
            r"(没办法|无能为力)",
            r"(白费|徒劳)"
        ],
        "intensity_modifiers": ["很", "非常", "特别", "极其"]
    },
    EmotionType.HOPEFUL: {
        "keywords": ["希望", "期待", "憧憬", "向往", "盼望", "渴望", "梦想", "愿景", "目标"],
        "patterns": [
            r"(希望能|想要)",
            r"(计划|打算)",
            r"(未来|前景)",
            r"(相信|信任)"
        ],
        "intensity_modifiers": ["非常", "特别", "很"]
    },
    EmotionType.SAD: {
        "keywords": ["难过", "伤心", "悲伤", "痛苦", "难受", "心酸", "心碎", "悲痛", "哀伤"],
        "patterns": [
            r"(失去了|没了)",
            r"(离开|分别)",
            r"(无法接受|难以接受)",
            r"(太惨了|太可怜)"
        ],
        "intensity_modifiers": ["非常", "特别", "极其", "很"]
    },
    EmotionType.ANGRY: {
        "keywords": ["生气", "愤怒", "恼火", "烦躁", "不满", "抱怨", "讨厌", "厌恶", "憎恨"],
        "patterns": [
            r"(太过分了|太离谱了)",
            r"(怎么能|怎么可以)",
            r"(简直|真是).{0,10}(过分|离谱)",
            r"(受够了|忍无可忍)"
        ],
        "intensity_modifiers": ["非常", "特别", "极其", "超级"]
    }
}

RESPONSE_STYLES = {
    EmotionType.ANXIOUS: "calming",
    EmotionType.EXCITED: "encouraging",
    EmotionType.CONFUSED: "clarifying",
    EmotionType.FRUSTRATED: "supportive",
    EmotionType.HOPEFUL: "affirming",
    EmotionType.SAD: "empathetic",
    EmotionType.ANGRY: "validating",
    EmotionType.NEUTRAL: "professional"
}


class EmotionDetector:
    def __init__(self):
        self._compiled_patterns = self._compile_patterns()
    
    def _compile_patterns(self) -> Dict[EmotionType, List]:
        compiled = {}
        for emotion_type, config in EMOTION_PATTERNS.items():
            patterns = []
            for pattern in config["patterns"]:
                patterns.append(re.compile(pattern, re.IGNORECASE))
            compiled[emotion_type] = patterns
        return compiled
    
    def detect(self, text: str) -> EmotionResult:
        scores = {}
        detected_keywords = {}
        
        for emotion_type, config in EMOTION_PATTERNS.items():
            keyword_score = 0
            matched_keywords = []
            
            for keyword in config["keywords"]:
                if keyword in text:
                    keyword_score += 1
                    matched_keywords.append(keyword)
            
            pattern_score = 0
            for pattern in self._compiled_patterns[emotion_type]:
                if pattern.search(text):
                    pattern_score += 1
            
            intensity_bonus = 0
            for modifier in config["intensity_modifiers"]:
                if modifier in text:
                    intensity_bonus += 0.2
            
            total_score = (keyword_score * 0.5 + pattern_score * 1.0) * (1 + intensity_bonus)
            scores[emotion_type] = total_score
            detected_keywords[emotion_type] = matched_keywords
        
        if not scores or max(scores.values()) == 0:
            return EmotionResult(
                emotion=EmotionType.NEUTRAL.value,
                score=0.0,
                confidence=1.0,
                keywords=[],
                suggested_response_style=RESPONSE_STYLES[EmotionType.NEUTRAL]
            )
        
        best_emotion = max(scores, key=scores.get)
        best_score = scores[best_emotion]
        
        total_score = sum(scores.values())
        confidence = best_score / total_score if total_score > 0 else 0.5
        
        normalized_score = min(best_score / 5.0, 1.0)
        
        return EmotionResult(
            emotion=best_emotion.value,
            score=normalized_score,
            confidence=confidence,
            keywords=detected_keywords[best_emotion],
            suggested_response_style=RESPONSE_STYLES[best_emotion]
        )
    
    def get_emotion_trend(self, emotions: List[EmotionResult]) -> Dict:
        if not emotions:
            return {"trend": "stable", "dominant_emotion": "neutral"}
        
        emotion_counts = {}
        total_score = {}
        
        for result in emotions:
            emotion = result.emotion
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
            total_score[emotion] = total_score.get(emotion, 0) + result.score
        
        dominant = max(emotion_counts, key=emotion_counts.get)
        
        if len(emotions) >= 2:
            recent = emotions[-1]
            previous = emotions[-2]
            
            if recent.score > previous.score + 0.2:
                trend = "intensifying"
            elif recent.score < previous.score - 0.2:
                trend = "improving"
            else:
                trend = "stable"
        else:
            trend = "stable"
        
        return {
            "trend": trend,
            "dominant_emotion": dominant,
            "emotion_distribution": emotion_counts,
            "average_scores": {k: v / emotion_counts[k] for k, v in total_score.items()}
        }
    
    def should_provide_support(self, result: EmotionResult) -> bool:
        support_needed_emotions = [
            EmotionType.ANXIOUS.value,
            EmotionType.FRUSTRATED.value,
            EmotionType.SAD.value,
            EmotionType.ANGRY.value
        ]
        
        return result.emotion in support_needed_emotions and result.score > 0.3
    
    def get_support_message(self, emotion: str, persona_name: str = "zhouyu") -> str:
        support_messages = {
            "zhouyu": {
                EmotionType.ANXIOUS.value: "阁下不必忧虑，此事我已深思熟虑。让我们一同分析，定能找到破局之道！",
                EmotionType.FRUSTRATED.value: "挫折乃成功之母！阁下莫要灰心，且听我分析局势，必能找到转机。",
                EmotionType.SAD.value: "人生起伏乃常事，阁下且放宽心。让我为您分析，或许能找到新的方向。",
                EmotionType.ANGRY.value: "阁下息怒！愤怒容易蒙蔽判断。让我们冷静分析，找出最佳对策。"
            },
            "luxun": {
                EmotionType.ANXIOUS.value: "我理解您的担忧，这是很正常的情绪。让我们一起分析情况，找到最适合的解决方案。",
                EmotionType.FRUSTRATED.value: "遇到挫折确实让人沮丧，但这也是成长的机会。让我们重新审视问题，寻找突破口。",
                EmotionType.SAD.value: "我理解您的心情，这段时间确实不容易。让我们一起梳理现状，看看有什么可以改善的。",
                EmotionType.ANGRY.value: "我能感受到您的不满，这种情况确实让人困扰。让我们冷静下来，一起想办法解决。"
            }
        }
        
        return support_messages.get(persona_name, support_messages.get("zhouyu", {})).get(
            emotion, "我理解您的感受，让我来帮助您分析。"
        )


emotion_detector = EmotionDetector()


def get_emotion_detector() -> EmotionDetector:
    return emotion_detector
