# -*- coding: utf-8 -*-
"""
融合模块
整合命盘与房产数据，生成综合决策建议
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import logging

from .mingpan_module import mingpan_module
from .property_module import PropertyModule
from .case_library import case_library

logger = logging.getLogger(__name__)

@dataclass
class FusionResult:
    """融合分析结果"""
    mingpan_summary: Dict[str, Any] = field(default_factory=dict)
    property_summary: Dict[str, Any] = field(default_factory=dict)
    fusion_analysis: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[Dict[str, Any]] = field(default_factory=list)
    action_steps: List[Dict[str, Any]] = field(default_factory=list)
    similar_cases: List[Dict[str, Any]] = field(default_factory=list)

class FusionModule:
    """融合模块"""
    
    def __init__(self, db_connection=None):
        self.property_module = PropertyModule(db_connection) if db_connection else None
    
    async def analyze(
        self,
        user_info: Dict[str, Any],
        question: str = ""
    ) -> FusionResult:
        """
        执行融合分析
        
        Args:
            user_info: 用户信息
                - birth_year: 出生年份
                - birth_month: 出生月份
                - birth_day: 出生日
                - birth_hour: 出生时辰
                - city: 当前城市
                - budget: 预算
                - purpose: 目的（自住/投资）
            question: 用户问题
        
        Returns:
            FusionResult: 融合分析结果
        """
        result = FusionResult()
        
        birth_info = {
            "year": user_info.get("birth_year", 1990),
            "month": user_info.get("birth_month", 1),
            "day": user_info.get("birth_day", 1),
            "hour": user_info.get("birth_hour", 0)
        }
        
        mingpan_result = mingpan_module.analyze(birth_info)
        result.mingpan_summary = {
            "zodiac": mingpan_result.get("zodiac"),
            "day_master_wuxing": mingpan_result.get("day_master_wuxing"),
            "favorable_direction": mingpan_result.get("favorable_direction"),
            "wealth_type": mingpan_result.get("six_dimensions", {}).get("wealth", {}).get("trait"),
            "career_direction": mingpan_result.get("six_dimensions", {}).get("career", {}).get("favorable_direction")
        }
        
        city = user_info.get("city", "苏州")
        budget = user_info.get("budget", 200)
        purpose = user_info.get("purpose", "自住")
        
        result.property_summary = {
            "city": city,
            "budget": budget,
            "purpose": purpose,
            "market_trend": "稳定"
        }
        
        result.fusion_analysis = self._fuse_analysis(
            mingpan_result,
            city,
            budget,
            purpose
        )
        
        result.recommendations = self._generate_recommendations(
            result.mingpan_summary,
            result.property_summary,
            result.fusion_analysis
        )
        
        result.action_steps = self._generate_action_steps(
            result.recommendations
        )
        
        similar_cases = case_library.search_similar_cases(
            zodiac=mingpan_result.get("zodiac"),
            limit=3
        )
        result.similar_cases = [
            {
                "case_id": c.id,
                "question": c.question[:100],
                "decision": c.final_decision,
                "outcome": c.outcome
            }
            for c in similar_cases
        ]
        
        return result
    
    def _fuse_analysis(
        self,
        mingpan_result: Dict,
        city: str,
        budget: int,
        purpose: str
    ) -> Dict[str, Any]:
        """融合分析"""
        favorable_direction = mingpan_result.get("favorable_direction", "中")
        wealth_type = mingpan_result.get("six_dimensions", {}).get("wealth", {}).get("trait", "正财型")
        
        direction_cities = {
            "东": ["杭州", "苏州", "上海", "南京", "无锡"],
            "南": ["广州", "深圳", "厦门", "海口", "珠海"],
            "西": ["成都", "重庆", "西安", "昆明", "贵阳"],
            "北": ["北京", "天津", "沈阳", "哈尔滨", "大连"],
            "中": ["武汉", "长沙", "郑州", "合肥", "南昌"]
        }
        
        recommended_cities = direction_cities.get(favorable_direction, [city])
        is_city_match = city in recommended_cities
        
        if "正财" in wealth_type:
            strategy = "稳健型策略：推荐核心地段、配套成熟的房产"
            risk_level = "低"
        else:
            strategy = "机会型策略：可考虑潜力新区，但需控制杠杆"
            risk_level = "中"
        
        return {
            "city_match": is_city_match,
            "recommended_cities": recommended_cities,
            "strategy": strategy,
            "risk_level": risk_level,
            "timing": "当前市场稳定，可根据个人情况选择时机",
            "budget_fit": budget >= 150 if city in ["上海", "北京", "深圳"] else budget >= 100
        }
    
    def _generate_recommendations(
        self,
        mingpan_summary: Dict,
        property_summary: Dict,
        fusion_analysis: Dict
    ) -> List[Dict[str, Any]]:
        """生成建议"""
        recommendations = []
        
        if not fusion_analysis.get("city_match"):
            recommendations.append({
                "dimension": "城市选择",
                "title": "考虑方位匹配的城市",
                "content": f"根据您的命盘，{mingpan_summary.get('favorable_direction')}方城市更适合您发展",
                "priority": "高"
            })
        
        recommendations.append({
            "dimension": "购房策略",
            "title": fusion_analysis.get("strategy", "稳健型策略"),
            "content": "结合您的财运属性，建议选择符合您风险偏好的房产类型",
            "priority": "高"
        })
        
        if not fusion_analysis.get("budget_fit"):
            recommendations.append({
                "dimension": "预算规划",
                "title": "调整预算或选择区域",
                "content": "当前预算在该城市可能选择有限，建议考虑周边区域或调整预算",
                "priority": "中"
            })
        
        recommendations.append({
            "dimension": "时机判断",
            "title": "把握购房时机",
            "content": fusion_analysis.get("timing", "当前市场稳定"),
            "priority": "中"
        })
        
        return recommendations
    
    def _generate_action_steps(
        self,
        recommendations: List[Dict]
    ) -> List[Dict[str, Any]]:
        """生成行动步骤"""
        steps = []
        
        for i, rec in enumerate(recommendations[:4], 1):
            steps.append({
                "step": i,
                "title": rec.get("title", f"步骤{i}"),
                "action": rec.get("content", ""),
                "timeline": "本周" if i == 1 else ("两周内" if i == 2 else "一个月内"),
                "priority": rec.get("priority", "中")
            })
        
        return steps

fusion_module = FusionModule()
