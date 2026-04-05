# -*- coding: utf-8 -*-
"""
Persona Engine
Generates personalized dialogue based on thinking gene parameters
"""
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import json
import random

logger = logging.getLogger(__name__)


class DialogueStyle(Enum):
    DIRECT = "direct"
    GENTLE = "gentle"
    ENCOURAGING = "encouraging"
    ANALYTICAL = "analytical"
    EMPATHETIC = "empathetic"


@dataclass
class PersonaConfig:
    name: str
    display_name: str
    decision_speed: int
    risk_preference: int
    expression_style: int
    inquiry_depth: int
    report_style: int
    emotional_resonance: int
    logic_rigor: int
    knowledge_preference: int


class PersonaEngine:
    def __init__(self):
        self._style_templates = self._load_style_templates()
        self._phrase_library = self._load_phrase_library()
    
    def _load_style_templates(self) -> Dict[str, Dict]:
        return {
            "zhouyu": {
                "greeting": [
                    "阁下好！在下{display_name}，愿为您出谋划策。",
                    "哈哈！来得正好，让我们直奔主题！",
                    "阁下有何疑难？且说来听听！"
                ],
                "inquiry": [
                    "敢问阁下{slot}？",
                    "此事关键在于{slot}，阁下意下如何？",
                    "若要破局，需知{slot}！"
                ],
                "analysis": [
                    "依我之见，{analysis}",
                    "此局之关键，在于{analysis}",
                    "哈哈哈！此事我已看透，{analysis}"
                ],
                "encouragement": [
                    "阁下勇气可嘉！此事大有可为！",
                    "机不可失，时不再来！当断则断！",
                    "大丈夫行事，当雷厉风行！"
                ],
                "conclusion": [
                    "综上所述，{conclusion}阁下以为如何？",
                    "良策已成，{conclusion}",
                    "此计可成！{conclusion}"
                ]
            },
            "luxun": {
                "greeting": [
                    "您好，我是{display_name}，很高兴为您服务。",
                    "请坐，让我们慢慢分析您的问题。",
                    "您好，我会尽力帮助您理清思路。"
                ],
                "inquiry": [
                    "请问您能详细说明一下{slot}吗？",
                    "为了更好地帮助您，我需要了解{slot}。",
                    "关于{slot}，您有什么具体的想法吗？"
                ],
                "analysis": [
                    "经过仔细分析，{analysis}",
                    "从多个角度来看，{analysis}",
                    "考虑到各种因素，{analysis}"
                ],
                "encouragement": [
                    "您的想法很有道理，我们可以一步步来实现。",
                    "不必着急，稳扎稳打才是长久之计。",
                    "每个决定都需要深思熟虑，您做得很好。"
                ],
                "conclusion": [
                    "总结一下，{conclusion}您觉得这个方案如何？",
                    "基于以上分析，{conclusion}",
                    "我的建议是，{conclusion}"
                ]
            }
        }
    
    def _load_phrase_library(self) -> Dict[str, Dict]:
        return {
            "zhouyu": {
                "connectors": ["而且", "更重要的是", "不仅如此", "此外"],
                "emphasis": ["关键在于", "核心问题是", "重中之重"],
                "historical_refs": [
                    "正如赤壁之战，以少胜多并非不可能",
                    "想当年周郎火烧赤壁，靠的就是把握时机",
                    "兵法云：知己知彼，百战不殆"
                ]
            },
            "luxun": {
                "connectors": ["同时", "另外", "值得注意的是", "此外"],
                "emphasis": ["需要特别注意的是", "重要的一点是", "关键因素是"],
                "case_refs": [
                    "根据以往的成功案例",
                    "从数据来看",
                    "结合市场实际情况"
                ]
            }
        }
    
    def create_config(self, gene_data: Dict) -> PersonaConfig:
        dims = gene_data.get("dimensions", {})
        return PersonaConfig(
            name=gene_data.get("name", "zhouyu"),
            display_name=gene_data.get("display_name", "Zhou Yu"),
            decision_speed=dims.get("decision_speed", 50),
            risk_preference=dims.get("risk_preference", 50),
            expression_style=dims.get("expression_style", 50),
            inquiry_depth=dims.get("inquiry_depth", 50),
            report_style=dims.get("report_style", 50),
            emotional_resonance=dims.get("emotional_resonance", 50),
            logic_rigor=dims.get("logic_rigor", 50),
            knowledge_preference=dims.get("knowledge_preference", 50)
        )
    
    def generate_greeting(self, config: PersonaConfig) -> str:
        templates = self._style_templates.get(config.name, self._style_templates["zhouyu"])
        greeting = random.choice(templates["greeting"])
        return greeting.format(display_name=config.display_name)
    
    def generate_inquiry(self, config: PersonaConfig, slot_name: str, slot_description: str) -> str:
        templates = self._style_templates.get(config.name, self._style_templates["zhouyu"])
        inquiry = random.choice(templates["inquiry"])
        
        if config.name == "zhouyu":
            slot_display = slot_name
        else:
            slot_display = slot_description
        
        return inquiry.format(slot=slot_display)
    
    def generate_analysis(self, config: PersonaConfig, analysis_content: str) -> str:
        templates = self._style_templates.get(config.name, self._style_templates["zhouyu"])
        analysis = random.choice(templates["analysis"])
        return analysis.format(analysis=analysis_content)
    
    def generate_encouragement(self, config: PersonaConfig) -> str:
        templates = self._style_templates.get(config.name, self._style_templates["zhouyu"])
        return random.choice(templates["encouragement"])
    
    def generate_conclusion(self, config: PersonaConfig, conclusion_content: str) -> str:
        templates = self._style_templates.get(config.name, self._style_templates["zhouyu"])
        conclusion = random.choice(templates["conclusion"])
        return conclusion.format(conclusion=conclusion_content)
    
    def get_dialogue_style(self, config: PersonaConfig) -> DialogueStyle:
        if config.decision_speed > 70 and config.risk_preference > 60:
            return DialogueStyle.DIRECT
        elif config.emotional_resonance > 70:
            return DialogueStyle.EMPATHETIC
        elif config.logic_rigor > 70:
            return DialogueStyle.ANALYTICAL
        elif config.emotional_resonance > 60:
            return DialogueStyle.GENTLE
        else:
            return DialogueStyle.ENCOURAGING
    
    def adapt_response_length(self, config: PersonaConfig, base_response: str) -> str:
        if config.decision_speed > 70:
            sentences = base_response.split("。")
            if len(sentences) > 3:
                return "。".join(sentences[:3]) + "。"
        elif config.decision_speed < 40:
            if not base_response.endswith("。"):
                base_response += "。"
            if len(base_response) < 100:
                phrases = self._phrase_library.get(config.name, self._phrase_library["zhouyu"])
                base_response += f" {random.choice(phrases['connectors'])}，让我们继续深入分析。"
        
        return base_response
    
    def add_emotional_tone(self, config: PersonaConfig, response: str, emotion: str) -> str:
        if emotion == "anxious" and config.emotional_resonance > 60:
            if config.name == "zhouyu":
                prefix = "阁下不必忧虑！"
            else:
                prefix = "我理解您的担忧，让我们一起来分析。"
            response = f"{prefix} {response}"
        
        elif emotion == "excited" and config.emotional_resonance > 60:
            if config.name == "zhouyu":
                suffix = "阁下气势如虹，定能成功！"
            else:
                suffix = "您的热情很好，让我们一起规划。"
            response = f"{response} {suffix}"
        
        return response
    
    def blend_personas(self, configs: List[PersonaConfig], weights: List[float]) -> PersonaConfig:
        if not configs:
            return self.create_config({"name": "zhouyu", "dimensions": {}})
        
        if len(configs) == 1:
            return configs[0]
        
        blended_dims = {}
        dim_names = [
            "decision_speed", "risk_preference", "expression_style",
            "inquiry_depth", "report_style", "emotional_resonance",
            "logic_rigor", "knowledge_preference"
        ]
        
        for dim in dim_names:
            total_weight = 0
            weighted_sum = 0
            for config, weight in zip(configs, weights):
                val = getattr(config, dim, 50)
                weighted_sum += val * weight
                total_weight += weight
            
            blended_dims[dim] = int(weighted_sum / total_weight) if total_weight > 0 else 50
        
        return PersonaConfig(
            name="blended",
            display_name="混合人格",
            **blended_dims
        )
    
    def get_system_prompt(self, config: PersonaConfig) -> str:
        style = self.get_dialogue_style(config)
        
        base_prompt = f"""你是一位专业的房产咨询顾问，当前使用的人格是{config.display_name}。

人格特征：
- 决策速度：{config.decision_speed}/100 ({'快速果断' if config.decision_speed > 70 else '谨慎细致'})
- 风险偏好：{config.risk_preference}/100 ({'敢于冒险' if config.risk_preference > 70 else '稳健保守'})
- 表达风格：{config.expression_style}/100 ({'豪迈直接' if config.expression_style > 70 else '温和内敛'})
- 追问深度：{config.inquiry_depth}/100 ({'快速切入核心' if config.inquiry_depth < 50 else '全面深入了解'})
- 情感共鸣：{config.emotional_resonance}/100 ({'理性分析为主' if config.emotional_resonance < 50 else '注重情感支持'})
- 逻辑严谨：{config.logic_rigor}/100 ({'战略逻辑' if config.logic_rigor < 70 else '细节逻辑'})

对话风格：{style.value}
"""
        
        if config.name == "zhouyu":
            base_prompt += """
说话风格要求：
1. 使用略带古风的表达，如"阁下"、"此事"、"依我之见"
2. 语气豪迈自信，充满战略眼光
3. 喜欢引用历史典故或兵法智慧
4. 建议大胆果断，鼓励用户把握机会
5. 适当使用"哈哈"、"好"等感叹词
"""
        elif config.name == "luxun":
            base_prompt += """
说话风格要求：
1. 使用温和专业的现代表达
2. 语气沉稳耐心，注重细节分析
3. 喜欢引用实际案例和数据
4. 建议稳健保守，提醒用户注意风险
5. 多使用"让我们"、"我建议"等表达
"""
        
        return base_prompt


persona_engine = PersonaEngine()


def get_persona_engine() -> PersonaEngine:
    return persona_engine
