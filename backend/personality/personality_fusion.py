"""
融会贯通 - 人格化交互与混合人格
房都督平台发展纲领第四章：杂家之智，兼收并蓄

核心思想（杂家）：
- 不执一端，取各家之长
- 周瑜/陆逊的人格特征量化为多维度参数
- 支持用户自定义混合人格（70%周瑜+30%陆逊）
- 情感状态机根据用户情绪动态调整人格表现

包含模块：
4.1 PersonalityDimensionSystem - 8维人格量化与混合生成
4.2 EmotionStateMachine - 情感状态机与动态融合
"""
import json
import logging
import math
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List, Tuple, Set
from collections import deque

logger = logging.getLogger(__name__)


# ==================== 4.1 人格维度量化与混合人格 ====================


class PersonalityDimension(str, Enum):
    """8大人格维度"""
    DECISION_SPEED = "decision_speed"
    RISK_APPETITE = "risk_appetite"
    LANGUAGE_STYLE = "language_style"
    QUESTION_DEPTH = "question_depth"
    REPORT_STYLE = "report_style"
    EMPATHY_LEVEL = "empathy_level"
    LOGIC_RIGOR = "logic_rigor"
    KNOWLEDGE_PREFERENCE = "knowledge_preference"


DIMENSION_DESCRIPTIONS = {
    PersonalityDimension.DECISION_SPEED: "决策速度（慢思熟虑<->当机立断）",
    PersonalityDimension.RISK_APPETITE: "风险偏好（保守稳健<->大胆进取）",
    PersonalityDimension.LANGUAGE_STYLE: "语言表达（简洁干练<->文采斐然）",
    PersonalityDimension.QUESTION_DEPTH: "追问深度（浅尝辄止<->刨根问底）",
    PersonalityDimension.REPORT_STYLE: "报告风格（数据驱动<->故事叙述）",
    PersonalityDimension.EMPATHY_LEVEL: "情感共鸣（理性客观<->共情温暖）",
    PersonalityDimension.LOGIC_RIGOR: "逻辑严谨性（直觉跳跃<->严密推导）",
    PersonalityDimension.KNOWLEDGE_PREFERENCE: "知识调用偏好（专精深究<->博采众长）",
}


@dataclass
class PersonalityVector:
    """人格向量（8维，每维0-100）"""
    vector_id: str
    name: str
    dimensions: Dict[PersonalityDimension, float]
    description: str = ""
    tags: Set[str] = field(default_factory=set)

    def to_array(self) -> List[float]:
        return [self.dimensions.get(d, 50.0) for d in PersonalityDimension]

    def to_normalized(self) -> List[float]:
        return [v / 100.0 for v in self.to_array()]

    def distance_to(self, other: 'PersonalityVector') -> float:
        """欧氏距离"""
        a = self.to_normalized()
        b = other.to_normalized()
        return math.sqrt(sum((ai - bi) ** 2 for ai, bi in zip(a, b)))

    def similarity_to(self, other: 'PersonalityVector') -> float:
        """余弦相似度"""
        a = self.to_normalized()
        b = other.to_normalized()
        dot = sum(ai * bi for ai, bi in zip(a, b))
        norm_a = math.sqrt(sum(x ** 2 for x in a))
        norm_b = math.sqrt(sum(x ** 2 for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)


class PersonalityDimensionSystem:
    """
    人格维度量化与混合人格生成系统（提示词 4.1）
    
    核心能力：
    - 8维人格向量定义（决策速度、风险偏好、语言表达等）
    - 预设人格模板：周瑜、陆逊等历史人物
    - 混合人格合成：输入比例(如周瑜0.7+陆逊0.3)输出新人格向量
    - 人格向量注入系统提示词，影响对话和报告风格
    """

    PRESET_PERSONALITIES: Dict[str, PersonalityVector] = {}

    @classmethod
    def _init_presets(cls):
        """初始化预设人格模板"""
        cls.PRESET_PERSONALITIES["zhou_yu"] = PersonalityVector(
            vector_id="preset_zhouyu",
            name="周瑜",
            dimensions={
                PersonalityDimension.DECISION_SPEED: 75,
                PersonalityDimension.RISK_APPETITE: 80,
                PersonalityDimension.LANGUAGE_STYLE: 85,
                PersonalityDimension.QUESTION_DEPTH: 60,
                PersonalityDimension.REPORT_STYLE: 70,
                PersonalityDimension.EMPATHY_LEVEL: 55,
                PersonalityDimension.LOGIC_RIGOR: 70,
                PersonalityDimension.KNOWLEDGE_PREFERENCE: 65,
            },
            description="豪迈自信，才气纵横，善于把握大局",
            tags={"豪迈", "自信", "儒将", "音乐", "火攻"},
        )

        cls.PRESET_PERSONALITIES["lu_xun"] = PersonalityVector(
            vector_id="preset_luxun",
            name="陆逊",
            dimensions={
                PersonalityDimension.DECISION_SPEED: 55,
                PersonalityDimension.RISK_APPETITE: 45,
                PersonalityDimension.LANGUAGE_STYLE: 60,
                PersonalityDimension.QUESTION_DEPTH: 85,
                PersonalityDimension.REPORT_STYLE: 80,
                PersonalityDimension.EMPATHY_LEVEL: 70,
                PersonalityDimension.LOGIC_RIGOR: 90,
                PersonalityDimension.KNOWLEDGE_PREFERENCE: 80,
            },
            description="沉稳缜密，深思熟虑，善用谋略",
            tags={"沉稳", "谨慎", "书生", "谋略", "白衣"},
        )

        cls.PRESET_PERSONALITIES["zhuge_liang"] = PersonalityVector(
            vector_id="preset_zhuge",
            name="诸葛亮",
            dimensions={
                PersonalityDimension.DECISION_SPEED: 40,
                PersonalityDimension.RISK_APPETITE: 35,
                PersonalityDimension.LANGUAGE_STYLE: 95,
                PersonalityDimension.QUESTION_DEPTH: 95,
                PersonalityDimension.REPORT_STYLE: 85,
                PersonalityDimension.EMPATHY_LEVEL: 75,
                PersonalityDimension.LOGIC_RIGOR: 95,
                PersonalityDimension.KNOWLEDGE_PREFERENCE: 90,
            },
            description="鞠躬尽瘁，算无遗策，忠贞不渝",
            tags={"忠诚", "智慧", "谨慎", "八阵图", "空城计"},
        )

        cls.PRESET_PERSONALITIES["cao_cao"] = PersonalityVector(
            vector_id="preset_caocao",
            name="曹操",
            dimensions={
                PersonalityDimension.DECISION_SPEED: 90,
                PersonalityDimension.RISK_APPETITE: 95,
                PersonalityDimension.LANGUAGE_STYLE: 75,
                PersonalityDimension.QUESTION_DEPTH: 55,
                PersonalityDimension.REPORT_STYLE: 45,
                PersonalityDimension.EMPATHY_LEVEL: 30,
                PersonalityDimension.LOGIC_RIGOR: 65,
                PersonalityDimension.KNOWLEDGE_PREFERENCE: 70,
            },
            description="唯才是举，雄才大略，宁教我负天下人",
            tags={"霸气", "实用主义", "诗人", "权谋", "求贤若渴"},
        )

        cls.PRESET_PERSONALITIES["li_bei"] = PersonalityVector(
            vector_id="preset_liubei",
            name="刘备",
            dimensions={
                PersonalityDimension.DECISION_SPEED: 45,
                PersonalityDimension.RISK_APPETITE: 35,
                PersonalityDimension.LANGUAGE_STYLE: 70,
                PersonalityDimension.QUESTION_DEPTH: 70,
                PersonalityDimension.REPORT_STYLE: 75,
                PersonalityDimension.EMPATHY_LEVEL: 95,
                PersonalityDimension.LOGIC_RIGOR: 60,
                PersonalityDimension.KNOWLEDGE_PREFERENCE: 55,
            },
            description="仁德宽厚，以德服人，百折不挠",
            tags={"仁德", "坚韧", "哭帝", "三顾茅庐", "人和"},
        )

    def __init__(self):
        if not self.PRESET_PERSONALITIES:
            self._init_presets()
        self._custom_personalities: Dict[str, PersonalityVector] = {}
        self._blend_history: List[Dict] = []

    def get_preset(self, name: str) -> Optional[PersonalityVector]:
        """获取预设人格"""
        key_map = {
            "zhouyu": "zhou_yu", "周瑜": "zhou_yu",
            "luxun": "lu_xun", "陆逊": "lu_xun",
            "zhugeliang": "zhuge_liang", "诸葛亮": "zhuge_liang",
            "caocao": "cao_cao", "曹操": "cao_cao",
            "liubei": "li_bei", "刘备": "li_bei",
        }
        key = key_map.get(name.lower(), name)
        return self.PRESET_PERSONALITIES.get(key)

    def list_presets(self) -> List[Dict]:
        """列出所有预设人格"""
        return [
            {
                "id": p.vector_id,
                "name": p.name,
                "description": p.description,
                "tags": list(p.tags),
                "dimensions": {d.value: v for d, v in p.dimensions.items()},
            }
            for p in self.PRESET_PERSONALITIES.values()
        ]

    def blend_personalities(
        self,
        ratios: Dict[str, float],
        custom_name: str = "",
    ) -> PersonalityVector:
        """
        混合多个人格
        
        Args:
            ratios: {"zhou_yu": 0.7, "lu_xun": 0.3} 比例字典（总和应为1.0）
            custom_name: 自定义名称
            
        Returns:
            新的混合人格向量
        """
        total_ratio = sum(ratios.values())
        if abs(total_ratio - 1.0) > 0.01:
            logger.warning(f"人格混合比例总和={total_ratio:.2f}，自动归一化")
            ratios = {k: v / total_ratio for k, v in ratios.items()}

        blended_dims = {}
        source_names = []

        for preset_key, ratio in ratios.items():
            preset = self.get_preset(preset_key)
            if not preset:
                logger.warning(f"未知预设人格: {preset_key}，跳过")
                continue

            source_names.append(f"{preset.name}({ratio:.0%})")
            for dim, value in preset.dimensions.items():
                blended_dims[dim] = blended_dims.get(dim, 0.0) + value * ratio

        blended = PersonalityVector(
            vector_id=f"blend_{uuid.uuid4().hex[:8]}",
            name=custom_name or " + ".join(source_names),
            dimensions=blended_dims,
            description=f"混合人格({', '.join(source_names)})",
            tags={"混合人格", *source_names},
        )

        self._custom_personalities[blended.vector_id] = blended
        self._blend_history.append({
            "blend_id": blended.vector_id,
            "name": blended.name,
            "ratios": dict(ratios),
            "timestamp": time.time(),
        })

        logger.info(f"人格混合完成: {blended.name}, 维度均值={sum(blended.dimensions.values())/8:.1f}")
        return blended

    def create_custom_personality(
        self,
        name: str,
        dimension_values: Dict[str, float],
    ) -> PersonalityVector:
        """创建完全自定义人格"""
        dims = {}
        for dim_str, value in dimension_values.items():
            dim = None
            for d in PersonalityDimension:
                if d.value == dim_str or d.name == dim_str:
                    dim = d
                    break
            if dim:
                dims[dim] = max(0.0, min(100.0, float(value)))
            else:
                logger.warning(f"未知维度: {dim_str}")

        missing = set(PersonalityDimension) - set(dims.keys())
        for m in missing:
            dims[m] = 50.0

        personality = PersonalityVector(
            vector_id=f"custom_{uuid.uuid4().hex[:8]}",
            name=name,
            dimensions=dims,
            description=f"自定义人格-{name}",
            tags={"自定义"},
        )
        self._custom_personalities[personality.vector_id] = personality
        return personality

    def generate_system_prompt(self, personality: PersonalityVector, base_prompt: str = "") -> str:
        """
        将人格向量转换为系统提示词
        
        将8维数值转化为LLM可理解的行为指导
        """
        dim_prompts = []
        for dim, value in personality.dimensions.items():
            desc = DIMENSION_DESCRIPTIONS.get(dim, "")
            if value >= 75:
                intensity = "非常"
            elif value >= 55:
                intensity = "较为"
            elif value <= 25:
                intensity = "不太"
            else:
                intensity = "中等"

            low_label, high_label = desc.split("<->") if "<->" in desc else ("低", "高")
            side = high_label.strip() if value > 50 else low_label.strip()

            dim_prompts.append(f"- {desc}：你{intensity}偏向{side}（{value}/100）")

        personality_section = f"""

【人格设定 - {personality.name}】
你是{personality.name}。{personality.description}
你的性格特点：
{chr(10).join(dim_prompts)}

请在回复中体现以上性格特点。保持角色一致性。
"""
        return (base_prompt + personality_section) if base_prompt else personality_section

    def get_blend_stats(self) -> Dict[str, Any]:
        """获取混合统计"""
        return {
            "available_presets": len(self.PRESET_PERSONALITIES),
            "custom_personalities": len(self._custom_personalities),
            "total_blends": len(self._blend_history),
            "recent_blends": self._blend_history[-5:],
        }


# ==================== 4.2 情感状态机与动态融合 ====================


class EmotionState(str, Enum):
    """情感状态"""
    VERY_POSITIVE = "very_positive"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    VERY_NEGATIVE = "very_negative"
    ANXIOUS = "anxious"
    EXCITED = "excited"
    THOUGHTFUL = "thoughtful"


@dataclass
class EmotionDetection:
    """情感检测结果"""
    primary_emotion: EmotionState
    confidence: float
    intensity: float
    detected_keywords: List[str]
    context_clues: List[str]
    timestamp: float = field(default_factory=time.time)


@dataclass
class EmotionPersonalityOffset:
    """情感→人格偏移量"""
    emotion: EmotionState
    dimension_offsets: Dict[PersonalityDimension, float]
    decay_half_life_sec: float = 300.0
    applied_at: float = field(default_factory=time.time)
    current_strength: float = 1.0


class EmotionStateMachine:
    """
    情感状态机与人格动态融合（提示词 4.2）
    
    核心机制：
    - 实时分析用户情绪（积极/消极/中性/焦虑/兴奋）
    - 情绪→人格映射表：消极→提高温和维度；积极→提高豪迈维度
    - 每次回复前动态调整人格向量（基础人格+临时偏移）
    - 偏移随时间衰减（5分钟恢复），避免永久改变人格
    
    映射规则：
    - very_negative → empathy+20, decision_speed-15, language_style-10
    - positive → risk_appetite+10, language_style+5
    - anxious → logic_rigor+5, question_depth+10, empathy+15
    - excited → decision_speed+15, risk_appetite+15, language_style+10
    """

    EMOTION_TO_OFFSET_MAP: Dict[EmotionState, Dict[str, float]] = {
        EmotionState.VERY_POSITIVE: {
            "decision_speed": 12, "risk_appetite": 10, "language_style": 8,
            "empathy_level": 5, "knowledge_preference": 3,
        },
        EmotionState.POSITIVE: {
            "decision_speed": 6, "risk_appetite": 8, "language_style": 5,
            "empathy_level": 3,
        },
        EmotionState.NEUTRAL: {},
        EmotionState.NEGATIVE: {
            "empathy_level": 15, "decision_speed": -10, "logic_rigor": 5,
            "question_depth": 8, "language_style": -5,
        },
        EmotionState.VERY_NEGATIVE: {
            "empathy_level": 25, "decision_speed": -18, "risk_appetite": -12,
            "language_style": -10, "question_depth": 10, "logic_rigor": 8,
        },
        EmotionState.ANXIOUS: {
            "empathy_level": 18, "logic_rigor": 8, "question_depth": 12,
            "decision_speed": -8, "risk_appetite": -10,
        },
        EmotionState.EXCITED: {
            "decision_speed": 15, "risk_appetite": 18, "language_style": 12,
            "empathy_level": 5, "report_style": -5,
        },
        EmotionState.THOUGHTFUL: {
            "question_depth": 15, "logic_rigor": 12, "report_style": 10,
            "decision_speed": -10, "language_style": 3, "empathy_level": 8,
        },
    }

    EMOTION_KEYWORDS = {
        EmotionState.VERY_POSITIVE: ["太棒了", "超级开心", "完美", "太好了", "激动不已"],
        EmotionState.POSITIVE: ["不错", "好的", "可以", "满意", "谢谢", "高兴", "开心"],
        EmotionState.NEGATIVE: ["不好", "不满意", "难过", "烦恼", "郁闷", "失望"],
        EmotionState.VERY_NEGATIVE: ["崩溃", "绝望", "痛苦", "受不了", "太糟糕", "气死我了"],
        EmotionState.ANXIOUS: ["担心", "焦虑", "不安", "紧张", "怕", "压力好大", "不确定"],
        EmotionState.EXCITED: ["期待", "迫不及待", "太兴奋", "终于", "惊喜"],
        EmotionState.THOUGHTFUL: ["思考", "犹豫", "想清楚", "权衡", "仔细考虑", "需要时间"],
    }

    def __init__(self):
        self._current_offset: Optional[EmotionPersonalityOffset] = None
        self._emotion_history: deque = deque(maxlen=50)
        self._state_transitions: List[Tuple[float, EmotionState, EmotionState]] = []

    def detect_emotion(self, text: str, context: Dict[str, Any] = None) -> EmotionDetection:
        """
        检测用户文本中的情感状态
        
        基于关键词匹配+上下文分析
        """
        text_lower = text.lower()
        matched_keywords = []
        scores = {}

        for emotion, keywords in self.EMOTION_KEYWORDS.items():
            matches = [kw for kw in keywords if kw in text]
            if matches:
                scores[emotion] = len(matches)
                matched_keywords.extend(matches)

        if not scores:
            primary = EmotionState.NEUTRAL
            confidence = 0.6
            intensity = 0.3
        else:
            primary = max(scores, key=scores.get)
            max_score = scores[primary]
            total_matches = sum(scores.values())
            confidence = min(0.98, 0.7 + max_score * 0.08)
            intensity = min(1.0, max_score / 3.0)

        context_clues = []
        if context:
            if context.get("history_sentiment_avg", 0) < -0.3:
                context_clues.append("历史对话偏消极")
            if context.get("has_exclamation", False):
                context_clues.append("含感叹号")
            if context.get("message_length", 0) < 10:
                context_clues.append("短消息")

        detection = EmotionDetection(
            primary_emotion=primary,
            confidence=round(confidence, 3),
            intensity=round(intensity, 3),
            detected_keywords=matched_keywords,
            context_clues=context_clues,
        )

        self._emotion_history.append(detection)
        self._apply_emotion_offset(detection)
        return detection

    def _apply_emotion_offset(self, detection: EmotionDetection):
        """应用情感→人格偏移"""
        emotion = detection.primary_emotion
        offset_config = self.EMOTION_TO_OFFSET_MAP.get(emotion, {})

        if not offset_config:
            return

        dim_offsets = {}
        for dim_str, offset_val in offset_config.items():
            dim = None
            for d in PersonalityDimension:
                if d.value == dim_str:
                    dim = d
                    break
            if dim:
                dim_offsets[dim] = offset_val

        prev_state = self._current_offset.primary_emotion if self._current_offset else None
        if prev_state and prev_state != emotion:
            self._state_transitions.append((time.time(), prev_state, emotion))

        self._current_offset = EmotionPersonalityOffset(
            emotion=emotion,
            dimension_offsets=dim_offsets,
            applied_at=time.time(),
            current_strength=detection.intensity,
        )

    def get_adjusted_personality(self, base: PersonalityVector) -> PersonalityVector:
        """
        获取经过情感调整后的人格向量
        
        公式：adjusted = base + offset × strength × decay
        其中decay随时间指数衰减
        """
        if not self._current_offset:
            return base

        elapsed = time.time() - self._current_offset.applied_at
        half_life = self._current_offset.decay_half_life_sec
        decay = math.pow(0.5, elapsed / half_life) if half_life > 0 else 0
        effective_strength = self._current_offset.current_strength * decay

        adjusted_dims = dict(base.dimensions)
        for dim, offset in self._current_offset.dimension_offsets.items():
            current = adjusted_dims.get(dim, 50.0)
            new_value = current + offset * effective_strength
            adjusted_dims[dim] = max(0.0, min(100.0, round(new_value, 1)))

        if effective_strength < 0.05:
            self._current_offset = None

        return PersonalityVector(
            vector_id=f"{base.vector_id}_adj",
            name=f"{base.name}(情感调整)",
            dimensions=adjusted_dims,
            description=f"{base.description} | 当前情感:{self._current_offset.emotion.value}(强度:{effective_strength:.2f})",
            tags=set(base.tags) | {"emotion_adjusted"},
        )

    def get_current_emotion_summary(self) -> Dict[str, Any]:
        """获取当前情感状态摘要"""
        recent = list(self._emotion_history)[-10:] if self._emotion_history else []
        emotion_counts = {}
        for e in recent:
            em = e.primary_emotion.value
            emotion_counts[em] = emotion_counts.get(em, 0) + 1

        dominant = max(emotion_counts, key=emotion_counts.get) if emotion_counts else "neutral"

        return {
            "current_emotion": self._current_offset.emotion.value if self._current_offset else "neutral",
            "offset_active": self._current_offset is not None,
            "offset_strength": round(self._current_offset.current_strength, 3) if self._current_offset else 0,
            "dominant_recent": dominant,
            "recent_distribution": emotion_counts,
            "total_detections": len(self._emotion_history),
            "state_transitions": len(self._state_transitions),
        }

    def reset_emotion_state(self):
        """重置情感状态（清除当前偏移）"""
        self._current_offset = None


# ==================== 全局实例 ====================

personality_system = PersonalityDimensionSystem()
emotion_machine = EmotionStateMachine()
