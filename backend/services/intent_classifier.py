# -*- coding: utf-8 -*-
"""
意图分类器
基于规则的轻量级分类器，用于识别用户问题类型
"""
from typing import Tuple, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import re
import logging

logger = logging.getLogger(__name__)

class IntentType(str, Enum):
    """意图类型"""
    PROPERTY = "property"       # 房产类
    MINGPAN = "mingpan"         # 命盘类
    MIXED = "mixed"             # 复合类
    EMOTION = "emotion"         # 情感类
    GENERAL = "general"         # 通用类

@dataclass
class IntentResult:
    """意图识别结果"""
    intent: IntentType
    confidence: float
    keywords: List[str]
    sub_intent: Optional[str] = None

class IntentClassifier:
    """
    意图分类器
    
    基于关键词和规则的用户问题分类
    """
    
    def __init__(self):
        self.property_keywords = [
            "买房", "卖房", "房价", "房子", "房产", "楼盘", "小区",
            "首付", "贷款", "公积金", "商贷", "学区房", "二手房",
            "新房", "户型", "地段", "板块", "区域", "城市",
            "预算", "总价", "单价", "平米", "投资", "自住"
        ]
        
        self.mingpan_keywords = [
            "命盘", "八字", "运势", "财运", "事业运", "姻缘",
            "流年", "大运", "五行", "生肖", "属相", "命理",
            "算命", "看相", "紫微", "天机", "文昌", "武曲",
            "财星", "官星", "桃花", "贵人", "煞星"
        ]
        
        self.emotion_keywords = [
            "感情", "恋爱", "婚姻", "对象", "男朋友", "女朋友",
            "老公", "老婆", "前任", "分手", "复合", "正缘",
            "合盘", "配对", "姻缘", "夫妻", "情侣", "暗恋"
        ]
        
        self.mixed_indicators = [
            "命盘.*买房", "买房.*命盘", "适合.*城市.*命",
            "结合.*命盘", "命盘.*房产", "房产.*命盘",
            "换城市.*换房", "换房.*换城市"
        ]
    
    def classify(self, text: str) -> IntentResult:
        """
        分类用户输入
        
        Args:
            text: 用户输入文本
        
        Returns:
            IntentResult: 分类结果
        """
        text_lower = text.lower()
        found_keywords = []
        
        # 检查复合意图
        for pattern in self.mixed_indicators:
            if re.search(pattern, text_lower):
                return IntentResult(
                    intent=IntentType.MIXED,
                    confidence=0.9,
                    keywords=["复合问题"],
                    sub_intent="命盘+房产"
                )
        
        # 计算各类型得分
        property_score = 0
        property_matched = []
        for kw in self.property_keywords:
            if kw in text_lower:
                property_score += 1
                property_matched.append(kw)
        
        mingpan_score = 0
        mingpan_matched = []
        for kw in self.mingpan_keywords:
            if kw in text_lower:
                mingpan_score += 1
                mingpan_matched.append(kw)
        
        emotion_score = 0
        emotion_matched = []
        for kw in self.emotion_keywords:
            if kw in text_lower:
                emotion_score += 1
                emotion_matched.append(kw)
        
        # 判断意图
        scores = {
            IntentType.PROPERTY: property_score,
            IntentType.MINGPAN: mingpan_score,
            IntentType.EMOTION: emotion_score
        }
        
        max_type = max(scores, key=scores.get)
        max_score = scores[max_type]
        
        # 如果有多个类型都有匹配，判断为复合类型
        non_zero_count = sum(1 for s in scores.values() if s > 0)
        if non_zero_count >= 2:
            matched_types = [t.value for t, s in scores.items() if s > 0]
            return IntentResult(
                intent=IntentType.MIXED,
                confidence=0.8,
                keywords=sum([list(set(v)) for v in [property_matched, mingpan_matched, emotion_matched] if v], []),
                sub_intent="+".join(matched_types)
            )
        
        if max_score == 0:
            return IntentResult(
                intent=IntentType.GENERAL,
                confidence=0.5,
                keywords=[]
            )
        
        # 确定关键词
        if max_type == IntentType.PROPERTY:
            found_keywords = property_matched
        elif max_type == IntentType.MINGPAN:
            found_keywords = mingpan_matched
        else:
            found_keywords = emotion_matched
        
        confidence = min(0.5 + max_score * 0.1, 0.95)
        
        return IntentResult(
            intent=max_type,
            confidence=confidence,
            keywords=found_keywords
        )
    
    def extract_entities(self, text: str) -> Dict[str, any]:
        """
        提取实体信息
        
        Args:
            text: 用户输入文本
        
        Returns:
            Dict: 提取的实体信息
        """
        entities = {}
        
        # 提取出生时间
        birth_patterns = [
            r'(\d{4})[年\-\/](\d{1,2})[月\-\/](\d{1,2})',  # 1999年12月17日
            r'(\d{4})(\d{2})(\d{2})',  # 19991217
        ]
        for pattern in birth_patterns:
            match = re.search(pattern, text)
            if match:
                entities['birth_year'] = int(match.group(1))
                entities['birth_month'] = int(match.group(2))
                entities['birth_day'] = int(match.group(3))
                break
        
        # 提取城市
        city_patterns = [
            r'在(\w+)[市县]',  # 在苏州市
            r'(\w+)[市县]的',  # 苏州市的
            r'去(\w+)',  # 去南京
            r'回(\w+)',  # 回老家
        ]
        cities = ['苏州', '南京', '杭州', '上海', '广州', '深圳', '北京', '成都', '武汉', '长沙']
        for city in cities:
            if city in text:
                entities['city'] = city
                break
        
        # 提取预算
        budget_patterns = [
            r'(\d+)万',  # 200万
            r'(\d+)百万',  # 2百万
            r'预算(\d+)',  # 预算200
        ]
        for pattern in budget_patterns:
            match = re.search(pattern, text)
            if match:
                entities['budget'] = int(match.group(1))
                break
        
        # 提取年龄
        age_match = re.search(r'(\d{1,2})岁', text)
        if age_match:
            entities['age'] = int(age_match.group(1))
        
        return entities
    
    def get_sub_category(self, text: str, intent: IntentType) -> Optional[str]:
        """
        获取子分类
        
        Args:
            text: 用户输入文本
            intent: 主意图
        
        Returns:
            子分类名称
        """
        text_lower = text.lower()
        
        if intent == IntentType.PROPERTY:
            if "买" in text_lower:
                return "购房咨询"
            elif "卖" in text_lower:
                return "售房咨询"
            elif "投资" in text_lower:
                return "投资分析"
            elif "学区" in text_lower:
                return "学区房咨询"
            else:
                return "房产咨询"
        
        elif intent == IntentType.MINGPAN:
            if "财运" in text_lower or "钱" in text_lower:
                return "财运分析"
            elif "事业" in text_lower or "工作" in text_lower:
                return "事业分析"
            elif "姻缘" in text_lower or "感情" in text_lower:
                return "姻缘分析"
            elif "健康" in text_lower:
                return "健康分析"
            else:
                return "命盘解读"
        
        elif intent == IntentType.EMOTION:
            if "分手" in text_lower:
                return "分手挽回"
            elif "复合" in text_lower:
                return "复合咨询"
            elif "正缘" in text_lower:
                return "正缘判断"
            elif "合盘" in text_lower or "配对" in text_lower:
                return "合盘分析"
            else:
                return "情感咨询"
        
        return None

# 全局分类器实例
intent_classifier = IntentClassifier()
