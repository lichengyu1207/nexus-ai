# -*- coding: utf-8 -*-
"""
Persona Switcher
Handles dynamic persona switching during consultation
"""
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import json
import time

from backend.services.consultation.persona_engine import (
    PersonaEngine, PersonaConfig, get_persona_engine
)
from backend.services.consultation.emotion_detector import (
    EmotionDetector, EmotionResult, get_emotion_detector
)

logger = logging.getLogger(__name__)


class SwitchTrigger(Enum):
    USER_REQUEST = "user_request"
    EMOTION_CHANGE = "emotion_change"
    STAGE_CHANGE = "stage_change"
    AUTO_RECOMMENDATION = "auto_recommendation"


@dataclass
class PersonaSwitchResult:
    old_persona: str
    new_persona: str
    blended_config: Optional[PersonaConfig]
    switch_reason: str
    path_adjustment: str
    transition_message: str


class PersonaSwitcher:
    def __init__(self):
        self.persona_engine = get_persona_engine()
        self.emotion_detector = get_emotion_detector()
        self._switch_history: Dict[str, List[Dict]] = {}
    
    def should_recommend_switch(
        self, 
        current_persona: str, 
        emotion_result: EmotionResult,
        stage: str,
        intent: str
    ) -> Optional[str]:
        if emotion_result.emotion in ["anxious", "sad", "frustrated"]:
            if current_persona == "zhouyu":
                return "luxun"
        
        if intent in ["investment_advice", "quick_decision"]:
            if current_persona == "luxun":
                return "zhouyu"
        
        if stage == "emotional_support":
            if current_persona == "zhouyu":
                return "luxun"
        
        if stage == "final_decision":
            if current_persona == "luxun":
                return "zhouyu"
        
        return None
    
    def switch_persona(
        self,
        session_id: str,
        current_persona: str,
        target_persona: str,
        weight: float = 1.0,
        trigger: SwitchTrigger = SwitchTrigger.USER_REQUEST,
        gene_configs: Dict[str, Dict] = None
    ) -> PersonaSwitchResult:
        old_config = None
        new_config = None
        
        if gene_configs:
            if current_persona in gene_configs:
                old_config = self.persona_engine.create_config(gene_configs[current_persona])
            if target_persona in gene_configs:
                new_config = self.persona_engine.create_config(gene_configs[target_persona])
        
        blended_config = None
        if weight < 1.0 and old_config and new_config:
            blended_config = self.persona_engine.blend_personas(
                [old_config, new_config],
                [1 - weight, weight]
            )
        
        path_adjustment = self._calculate_path_adjustment(current_persona, target_persona, stage="current")
        transition_message = self._generate_transition_message(
            current_persona, target_persona, trigger
        )
        
        switch_record = {
            "timestamp": time.time(),
            "from": current_persona,
            "to": target_persona,
            "weight": weight,
            "trigger": trigger.value,
            "blended": blended_config is not None
        }
        
        if session_id not in self._switch_history:
            self._switch_history[session_id] = []
        self._switch_history[session_id].append(switch_record)
        
        return PersonaSwitchResult(
            old_persona=current_persona,
            new_persona=target_persona,
            blended_config=blended_config,
            switch_reason=self._get_switch_reason(trigger),
            path_adjustment=path_adjustment,
            transition_message=transition_message
        )
    
    def _calculate_path_adjustment(
        self, 
        old_persona: str, 
        new_persona: str,
        stage: str
    ) -> str:
        adjustments = {
            ("zhouyu", "luxun"): {
                "description": "咨询路径将延长，增加信息收集阶段",
                "stages_added": ["detailed_inquiry", "risk_assessment"],
                "estimated_time_increase": "30%"
            },
            ("luxun", "zhouyu"): {
                "description": "咨询路径将缩短，快速进入决策阶段",
                "stages_removed": ["detailed_inquiry"],
                "estimated_time_decrease": "20%"
            }
        }
        
        key = (old_persona, new_persona)
        adjustment = adjustments.get(key, {
            "description": "咨询路径保持不变",
            "changes": []
        })
        
        return adjustment["description"]
    
    def _generate_transition_message(
        self,
        old_persona: str,
        new_persona: str,
        trigger: SwitchTrigger
    ) -> str:
        transition_messages = {
            "zhouyu_to_luxun": {
                SwitchTrigger.USER_REQUEST: "好的，让我换一种更温和的方式来为您分析。",
                SwitchTrigger.EMOTION_CHANGE: "我注意到您可能需要更细致的分析，让我调整一下方式。",
                SwitchTrigger.STAGE_CHANGE: "进入这个阶段，我们需要更谨慎地分析。",
                SwitchTrigger.AUTO_RECOMMENDATION: "根据当前情况，我建议采用更稳健的分析方式。"
            },
            "luxun_to_zhouyu": {
                SwitchTrigger.USER_REQUEST: "好的！让我们换一种更直接的方式来解决问题！",
                SwitchTrigger.EMOTION_CHANGE: "看来您已经准备好了，让我们直接切入重点！",
                SwitchTrigger.STAGE_CHANGE: "现在是做决定的时候了，让我给您明确的建议！",
                SwitchTrigger.AUTO_RECOMMENDATION: "根据当前情况，我建议采用更果断的决策方式。"
            }
        }
        
        key = f"{old_persona}_to_{new_persona}"
        messages = transition_messages.get(key, {})
        return messages.get(trigger, "好的，让我调整一下分析方式。")
    
    def _get_switch_reason(self, trigger: SwitchTrigger) -> str:
        reasons = {
            SwitchTrigger.USER_REQUEST: "用户主动请求切换",
            SwitchTrigger.EMOTION_CHANGE: "检测到情绪变化，自动调整",
            SwitchTrigger.STAGE_CHANGE: "咨询阶段变化，自动调整",
            SwitchTrigger.AUTO_RECOMMENDATION: "系统智能推荐切换"
        }
        return reasons.get(trigger, "未知原因")
    
    def get_switch_history(self, session_id: str) -> List[Dict]:
        return self._switch_history.get(session_id, [])
    
    def get_persona_for_stage(self, stage: str, intent: str) -> str:
        stage_persona_map = {
            "init": "zhouyu",
            "info_collection": "luxun",
            "analysis": "zhouyu",
            "emotional_support": "luxun",
            "decision_making": "zhouyu",
            "final_decision": "zhouyu"
        }
        
        return stage_persona_map.get(stage, "zhouyu")
    
    def calculate_persona_compatibility(
        self, 
        persona: str, 
        emotion: str,
        intent: str
    ) -> float:
        compatibility_matrix = {
            "zhouyu": {
                "anxious": 0.3,
                "excited": 0.9,
                "confused": 0.5,
                "frustrated": 0.4,
                "hopeful": 0.8,
                "sad": 0.3,
                "angry": 0.4,
                "neutral": 0.7
            },
            "luxun": {
                "anxious": 0.9,
                "excited": 0.6,
                "confused": 0.8,
                "frustrated": 0.8,
                "hopeful": 0.7,
                "sad": 0.9,
                "angry": 0.7,
                "neutral": 0.7
            }
        }
        
        intent_bonus = {
            "investment_advice": {"zhouyu": 0.2, "luxun": -0.1},
            "emotional_support": {"zhouyu": -0.2, "luxun": 0.2},
            "property_consultation": {"zhouyu": 0.1, "luxun": 0.1},
            "destiny_consultation": {"zhouyu": 0.1, "luxun": 0.1}
        }
        
        base_score = compatibility_matrix.get(persona, {}).get(emotion, 0.5)
        bonus = intent_bonus.get(intent, {}).get(persona, 0)
        
        return min(max(base_score + bonus, 0), 1)


persona_switcher = PersonaSwitcher()


def get_persona_switcher() -> PersonaSwitcher:
    return persona_switcher
