#!/usr/bin/env python3
"""
对话系统模块
"""

import json
import os
import sys
import numpy as np
from typing import Dict, Any, List, Tuple

# 添加项目根目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.personality.personality_library import PersonalityLibrary, Personality


class EmotionRecognizer:
    """情绪识别模块"""
    
    def recognize(self, user_input: str) -> str:
        """识别用户情绪"""
        # 简单实现，实际应用中可使用更复杂的NLP模型
        negative_keywords = ["压力", "撑不住", "难过", "伤心", "疲惫", "焦虑", "抑郁", "痛苦"]
        positive_keywords = ["开心", "快乐", "高兴", "兴奋", "满意", "幸福"]
        
        for keyword in negative_keywords:
            if keyword in user_input:
                return "消极"
        
        for keyword in positive_keywords:
            if keyword in user_input:
                return "积极"
        
        return "中性"


class IntentRecognizer:
    """意图识别模块"""
    
    def recognize(self, user_input: str) -> str:
        """识别用户意图"""
        # 简单实现，实际应用中可使用更复杂的NLP模型
        intent_keywords = {
            "倾诉": ["压力", "撑不住", "难过", "伤心", "疲惫"],
            "询问": ["什么", "怎么", "如何", "为什么", "哪里"],
            "请求": ["帮忙", "帮助", "请", "能否", "可以"],
            "感谢": ["谢谢", "感谢", "多谢", "感激"]
        }
        
        for intent, keywords in intent_keywords.items():
            for keyword in keywords:
                if keyword in user_input:
                    return intent
        
        return "其他"


class PersonalityAdapter:
    """人格适配模块"""
    
    def __init__(self, personality_library: PersonalityLibrary):
        self.personality_library = personality_library
        self.personality_weights = {}
        self._init_weights()
    
    def _init_weights(self):
        """初始化人格权重"""
        for name in self.personality_library.list_personalities():
            self.personality_weights[name] = {
                "温和": 0.5,
                "傲气": 0.5,
                "安慰": 0.5,
                "说教": 0.5
            }
    
    def adapt(self, emotion: str, intent: str) -> Tuple[str, Dict[str, float]]:
        """根据情绪和意图适配人格"""
        # 选择人格
        if emotion == "消极" and intent == "倾诉":
            selected_personality = "周瑜"
            # 调整权重
            weights = self.personality_weights.get(selected_personality, {
                "温和": 0.5,
                "傲气": 0.5,
                "安慰": 0.5,
                "说教": 0.5
            })
            # 调高温和维度，降低傲气维度
            weights["温和"] = min(1.0, weights["温和"] + 0.3)
            weights["傲气"] = max(0.0, weights["傲气"] - 0.3)
            weights["安慰"] = min(1.0, weights["安慰"] + 0.2)
            weights["说教"] = max(0.0, weights["说教"] - 0.2)
            self.personality_weights[selected_personality] = weights
            return selected_personality, weights
        elif emotion == "积极":
            selected_personality = "周瑜"
            return selected_personality, self.personality_weights.get(selected_personality, {
                "温和": 0.5,
                "傲气": 0.5,
                "安慰": 0.5,
                "说教": 0.5
            })
        else:
            selected_personality = "陆逊"
            return selected_personality, self.personality_weights.get(selected_personality, {
                "温和": 0.5,
                "傲气": 0.5,
                "安慰": 0.5,
                "说教": 0.5
            })


class ResponseGenerator:
    """回复生成模块"""
    
    def __init__(self, personality_library: PersonalityLibrary):
        self.personality_library = personality_library
    
    def generate_draft(self, user_input: str, personality_name: str, weights: Dict[str, float]) -> str:
        """生成人物风格的草稿"""
        personality = self.personality_library.get_personality(personality_name)
        if not personality:
            return "抱歉，我暂时无法回复您。"
        
        # 基于人格特征和权重生成草稿
        if personality_name == "周瑜":
            if weights.get("安慰", 0.5) >= 0.7:
                return "人生如江流，时急时缓，压力不过是浪花一朵。昔日赤壁之战，某亦曾夜不能寐，然与伯符对饮一曲，便觉天地开阔。不妨放下眼前事，听一曲《高山流水》，心自澄明。"
            else:
                return "大丈夫立于世，当逆流而上。压力如磨刀石，磨得剑锋更利。且看那大江淘尽英雄，是非成败转头空，何须在意眼前烦恼？"
        elif personality_name == "陆逊":
            return "凡事需从长计议，压力乃成长之必经。不妨静心思虑，分轻重缓急，逐一化解。待云开雾散时，便是海阔天空日。"
        else:
            return "我理解您的感受，相信一切都会好起来的。"
    
    def refine_style(self, draft: str, personality_name: str) -> str:
        """通过风格控制模型进行润色"""
        # 简单实现，实际应用中可使用更复杂的风格控制模型
        personality = self.personality_library.get_personality(personality_name)
        if not personality:
            return draft
        
        # 根据人格特征进行润色
        if personality_name == "周瑜":
            # 周瑜的语言风格：多用典故、善用比喻、语气铿锵
            refined = draft.replace("压力不过是浪花一朵", "压力不过是大江中的一朵浪花")
            refined = refined.replace("然与伯符对饮一曲", "然与伯符对饮，抚琴一曲")
            refined = refined.replace("心自澄明", "心境自会澄明如镜")
            return refined
        elif personality_name == "陆逊":
            # 陆逊的语言风格：言辞恳切、逻辑严密、从容不迫
            refined = draft.replace("凡事需从长计议", "凡事当从长计议，不可操之过急")
            refined = refined.replace("不妨静心思虑", "不妨静下心来，仔细思虑")
            refined = refined.replace("待云开雾散时", "待得云开雾散之时")
            return refined
        else:
            return draft
    
    def generate(self, user_input: str, personality_name: str, weights: Dict[str, float]) -> str:
        """生成回复（两阶段）"""
        # 第一阶段：生成人物风格的草稿
        draft = self.generate_draft(user_input, personality_name, weights)
        
        # 第二阶段：通过风格控制模型进行润色
        refined = self.refine_style(draft, personality_name)
        
        return refined


class SystemEvolution:
    """系统演进模块"""
    
    def __init__(self, personality_library: PersonalityLibrary):
        self.personality_library = personality_library
        self.satisfaction_records = {}
        self.style_ratings = {}  # 记录用户对不同风格维度的评分
    
    def record_satisfaction(self, personality_name: str, satisfaction: float, style_ratings: Dict[str, float] = None):
        """记录用户满意度和风格评分"""
        if personality_name not in self.satisfaction_records:
            self.satisfaction_records[personality_name] = []
        self.satisfaction_records[personality_name].append(satisfaction)
        
        if style_ratings:
            if personality_name not in self.style_ratings:
                self.style_ratings[personality_name] = {}
            for style, rating in style_ratings.items():
                if style not in self.style_ratings[personality_name]:
                    self.style_ratings[personality_name][style] = []
                self.style_ratings[personality_name][style].append(rating)
    
    def evolve(self, personality_name: str):
        """根据满意度和风格评分演进系统"""
        if personality_name not in self.satisfaction_records:
            return
        
        # 每10次交互后更新人格向量
        if len(self.satisfaction_records[personality_name]) % 10 == 0:
            print(f"\n触发人格演进: {personality_name}")
            
            # 计算平均满意度
            avg_satisfaction = np.mean(self.satisfaction_records[personality_name])
            print(f"平均满意度: {avg_satisfaction:.2f}")
            
            # 更新风格维度权重
            if personality_name in self.style_ratings:
                for style, ratings in self.style_ratings[personality_name].items():
                    if len(ratings) > 0:
                        avg_rating = np.mean(ratings)
                        # 将1-5星评分映射到0-1的权重调整值
                        weight_adjustment = (avg_rating - 3) / 10  # -0.2到0.2的调整范围
                        print(f"{style} 维度调整: {weight_adjustment:.2f}")
                        
                        # 这里可以实现更复杂的演进逻辑，例如更新人格向量
                        # 实际应用中，需要根据调整值更新人格的相应维度
            
            # 重置记录，开始新的周期
            self.satisfaction_records[personality_name] = []
            if personality_name in self.style_ratings:
                self.style_ratings[personality_name] = {}
        else:
            # 简单的满意度反馈
            avg_satisfaction = np.mean(self.satisfaction_records[personality_name])
            if avg_satisfaction > 0.8:
                print(f"系统演进: 增强 {personality_name} 的安慰维度")


class DialogueSystem:
    """对话系统"""
    
    def __init__(self):
        # 初始化人格库
        self.personality_library = PersonalityLibrary()
        # 初始化各个模块
        self.emotion_recognizer = EmotionRecognizer()
        self.intent_recognizer = IntentRecognizer()
        self.personality_adapter = PersonalityAdapter(self.personality_library)
        self.response_generator = ResponseGenerator(self.personality_library)
        self.system_evolution = SystemEvolution(self.personality_library)
    
    def process(self, user_input: str, personality_name: str = None) -> str:
        """处理用户输入"""
        # 步骤S1: 情绪识别
        emotion = self.emotion_recognizer.recognize(user_input)
        print(f"情绪识别结果: {emotion}")
        
        # 步骤S2: 意图识别
        intent = self.intent_recognizer.recognize(user_input)
        print(f"意图识别结果: {intent}")
        
        # 步骤S3: 人格适配
        if personality_name:
            # 用户指定了人格
            weights = self.personality_adapter.personality_weights.get(personality_name, {
                "温和": 0.5,
                "傲气": 0.5,
                "安慰": 0.5,
                "说教": 0.5
            })
            # 根据情绪和意图调整权重
            if emotion == "消极" and intent == "倾诉":
                weights["温和"] = min(1.0, weights["温和"] + 0.3)
                weights["傲气"] = max(0.0, weights["傲气"] - 0.3)
                weights["安慰"] = min(1.0, weights["安慰"] + 0.2)
                weights["说教"] = max(0.0, weights["说教"] - 0.2)
                self.personality_adapter.personality_weights[personality_name] = weights
            print(f"使用指定人格: {personality_name}, 权重: {weights}")
        else:
            # 系统自动选择人格
            personality_name, weights = self.personality_adapter.adapt(emotion, intent)
            print(f"选择人格: {personality_name}, 权重: {weights}")
        
        # 步骤S4: 生成回复
        response = self.response_generator.generate(user_input, personality_name, weights)
        print(f"生成回复: {response}")
        
        # 步骤S5: 系统演进（这里模拟用户好评）
        self.system_evolution.record_satisfaction(personality_name, 0.9)
        self.system_evolution.evolve(personality_name)
        
        return response
    
    def add_custom_personality(self, personality: Personality):
        """添加自定义人格"""
        return self.personality_library.add_personality(personality)
    
    def list_available_personalities(self):
        """列出可用的人格"""
        return self.personality_library.list_personalities()
    
    def get_personality_details(self, personality_name: str):
        """获取人格详细信息"""
        return self.personality_library.get_personality(personality_name)
