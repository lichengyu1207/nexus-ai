# -*- coding: utf-8 -*-
"""
情感分析模块
提供感情问题分析、合盘分析、关系建议等功能
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import re
import logging

from .mingpan_module import mingpan_module

logger = logging.getLogger(__name__)

@dataclass
class ConflictPattern:
    """冲突模式"""
    pattern_type: str
    description: str
    suggestions: List[str] = field(default_factory=list)

@dataclass
class EmotionAnalysisResult:
    """情感分析结果"""
    compatibility_score: int
    compatibility_note: str
    conflicts: List[ConflictPattern] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    similar_cases: List[Dict] = field(default_factory=list)

class ConflictExtractor:
    """冲突提取器"""
    
    def __init__(self):
        self.conflict_patterns = {
            "付出模式不对等": {
                "keywords": ["付出", "计较", "多给", "少给", "不对等", "公平"],
                "suggestions": [
                    "把'我应该多付出'换成'我乐意付出多少'",
                    "主动沟通：'我们一起定义什么是公平'",
                    "观察自己的付出动机：是爱还是期待回报？"
                ]
            },
            "沟通不畅": {
                "keywords": ["沟通", "不说", "冷战", "吵架", "不理解"],
                "suggestions": [
                    "学会'我'字句表达：'我感到...'而不是'你总是...'",
                    "定期进行深度对话，不等到问题积累",
                    "倾听时不急着给建议，先确认理解"
                ]
            },
            "信任问题": {
                "keywords": ["信任", "怀疑", "查手机", "前任", "出轨"],
                "suggestions": [
                    "信任是慢慢建立的，需要时间和一致性",
                    "透明化自己的行踪和社交，减少对方的焦虑",
                    "如果信任已破裂，需要专业咨询介入"
                ]
            },
            "价值观冲突": {
                "keywords": ["价值观", "消费观", "金钱观", "生活方式"],
                "suggestions": [
                    "价值观没有对错，只有匹配与否",
                    "找到共同点，尊重差异点",
                    "在关键决策上寻求折中方案"
                ]
            },
            "家庭介入": {
                "keywords": ["父母", "家人", "婆媳", "岳父母", "家庭"],
                "suggestions": [
                    "建立边界：小家庭优先于原生家庭",
                    "夫妻统一战线，不各自站队",
                    "重要决策夫妻先商量，再告知父母"
                ]
            },
            "距离问题": {
                "keywords": ["异地", "距离", "分开", "见面"],
                "suggestions": [
                    "设定见面的频率和计划",
                    "每天保持联系，分享生活细节",
                    "给异地设定一个结束的时间点"
                ]
            }
        }
    
    def extract(self, text: str) -> List[ConflictPattern]:
        """
        从文本中提取冲突模式
        
        Args:
            text: 用户描述的问题
        
        Returns:
            List[ConflictPattern]: 冲突模式列表
        """
        conflicts = []
        text_lower = text.lower()
        
        for pattern_type, pattern_data in self.conflict_patterns.items():
            matched = False
            for keyword in pattern_data["keywords"]:
                if keyword in text_lower:
                    matched = True
                    break
            
            if matched:
                conflicts.append(ConflictPattern(
                    pattern_type=pattern_type,
                    description=f"检测到{pattern_type}问题",
                    suggestions=pattern_data["suggestions"]
                ))
        
        if not conflicts:
            conflicts.append(ConflictPattern(
                pattern_type="一般情感问题",
                description="需要更多信息来分析具体问题",
                suggestions=[
                    "您可以详细描述一下您遇到的具体困难吗？",
                    "您觉得这段关系中最大的卡点是什么？"
                ]
            ))
        
        return conflicts

class EmotionModule:
    """
    情感分析模块
    
    提供感情问题分析、合盘分析、关系建议
    """
    
    def __init__(self):
        self.conflict_extractor = ConflictExtractor()
    
    def analyze(
        self,
        user_birth: Dict[str, Any],
        partner_birth: Optional[Dict[str, Any]] = None,
        question: str = ""
    ) -> EmotionAnalysisResult:
        """
        执行情感分析
        
        Args:
            user_birth: 用户出生信息
            partner_birth: 伴侣出生信息（可选）
            question: 用户描述的问题
        
        Returns:
            EmotionAnalysisResult: 分析结果
        """
        conflicts = self.conflict_extractor.extract(question)
        
        compatibility_score = 60
        compatibility_note = "需要更多信息来判断"
        
        if partner_birth:
            compatibility = mingpan_module.check_compatibility(
                user_birth, partner_birth
            )
            compatibility_score = compatibility["score"]
            compatibility_note = compatibility["compatibility"]
        
        suggestions = []
        for conflict in conflicts:
            suggestions.extend(conflict.suggestions)
        
        if not suggestions:
            suggestions = [
                "您可以详细描述一下您遇到的具体困难吗？",
                "您觉得这段关系中最大的卡点是什么？"
            ]
        
        return EmotionAnalysisResult(
            compatibility_score=compatibility_score,
            compatibility_note=compatibility_note,
            conflicts=conflicts,
            suggestions=suggestions[:5],
            similar_cases=[]
        )
    
    def analyze_single(
        self,
        user_birth: Dict[str, Any],
        question: str = ""
    ) -> Dict[str, Any]:
        """
        单人情感分析（无伴侣信息）
        
        Args:
            user_birth: 用户出生信息
            question: 用户描述的问题
        
        Returns:
            Dict: 分析结果
        """
        mingpan_result = mingpan_module.analyze(user_birth)
        marriage_info = mingpan_result.get("six_dimensions", {}).get("marriage", {})
        
        conflicts = self.conflict_extractor.extract(question)
        
        suggestions = []
        for conflict in conflicts:
            suggestions.extend(conflict.suggestions)
        
        return {
            "marriage_analysis": marriage_info,
            "conflicts": [
                {
                    "type": c.pattern_type,
                    "description": c.description,
                    "suggestions": c.suggestions
                }
                for c in conflicts
            ],
            "suggestions": suggestions[:5]
        }
    
    def get_relationship_advice(
        self,
        compatibility_score: int,
        conflicts: List[ConflictPattern]
    ) -> str:
        """
        生成关系建议
        
        Args:
            compatibility_score: 合盘分数
            conflicts: 冲突列表
        
        Returns:
            str: 关系建议
        """
        if compatibility_score >= 80:
            base = "你们的匹配度很高，有很好的基础。"
        elif compatibility_score >= 60:
            base = "你们的匹配度中等，需要努力经营。"
        else:
            base = "你们的匹配度偏低，需要更多的理解和包容。"
        
        if conflicts:
            conflict_types = [c.pattern_type for c in conflicts]
            base += f" 主要需要解决的问题是：{'、'.join(conflict_types)}。"
        
        return base

emotion_module = EmotionModule()
