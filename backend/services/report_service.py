# -*- coding: utf-8 -*-
"""
报告生成服务
整合所有模块，生成四种类型的报告
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import logging

from .intent_classifier import intent_classifier, IntentType
from .mingpan_module import mingpan_module
from .emotion_module import emotion_module
from .fusion_module import fusion_module
from .report_template import report_generator
from .case_library import case_library

logger = logging.getLogger(__name__)

@dataclass
class ReportRequest:
    """报告请求"""
    user_id: str
    question: str
    birth_year: Optional[int] = None
    birth_month: Optional[int] = None
    birth_day: Optional[int] = None
    birth_hour: Optional[int] = None
    city: Optional[str] = None
    budget: Optional[int] = None
    purpose: Optional[str] = None
    partner_birth_year: Optional[int] = None
    partner_birth_month: Optional[int] = None
    partner_birth_day: Optional[int] = None

class ReportService:
    """报告生成服务"""
    
    def __init__(self):
        self.intent_classifier = intent_classifier
        self.mingpan_module = mingpan_module
        self.emotion_module = emotion_module
        self.fusion_module = fusion_module
        self.report_generator = report_generator
        self.case_library = case_library
    
    async def generate_report(self, request: ReportRequest) -> Dict[str, Any]:
        """
        生成报告
        
        Args:
            request: 报告请求
        
        Returns:
            Dict: 报告结果
        """
        intent_result = self.intent_classifier.classify(request.question)
        entities = self.intent_classifier.extract_entities(request.question)
        sub_category = self.intent_classifier.get_sub_category(
            request.question,
            intent_result.intent
        )
        
        user_info = {
            "birth_year": request.birth_year or entities.get("birth_year"),
            "birth_month": request.birth_month or entities.get("birth_month"),
            "birth_day": request.birth_day or entities.get("birth_day"),
            "birth_hour": request.birth_hour or 0,
            "city": request.city or entities.get("city"),
            "budget": request.budget or entities.get("budget"),
            "purpose": request.purpose or "自住",
            "question": request.question,
            "zodiac": None
        }
        
        analysis = {}
        recommendations = []
        action_steps = []
        
        if intent_result.intent == IntentType.PROPERTY:
            result = await self._analyze_property(user_info)
            analysis = result.get("analysis", {})
            recommendations = result.get("recommendations", [])
            action_steps = result.get("action_steps", [])
            report_type = "property"
            
        elif intent_result.intent == IntentType.MINGPAN:
            result = self._analyze_mingpan(user_info)
            analysis = result.get("analysis", {})
            recommendations = result.get("recommendations", [])
            action_steps = result.get("action_steps", [])
            report_type = "mingpan"
            
        elif intent_result.intent == IntentType.EMOTION:
            result = self._analyze_emotion(request, user_info)
            analysis = result.get("analysis", {})
            recommendations = result.get("recommendations", [])
            action_steps = result.get("action_steps", [])
            report_type = "emotion"
            
        elif intent_result.intent == IntentType.MIXED:
            result = await self._analyze_mixed(user_info)
            analysis = result.get("analysis", {})
            recommendations = result.get("recommendations", [])
            action_steps = result.get("action_steps", [])
            report_type = "combined"
            
        else:
            result = self._analyze_general(user_info)
            analysis = result.get("analysis", {})
            recommendations = result.get("recommendations", [])
            action_steps = result.get("action_steps", [])
            report_type = "combined"
        
        if user_info.get("birth_year"):
            birth_info = {
                "year": user_info["birth_year"],
                "month": user_info.get("birth_month", 1),
                "day": user_info.get("birth_day", 1),
                "hour": user_info.get("birth_hour", 0)
            }
            mingpan_result = self.mingpan_module.analyze(birth_info)
            user_info["zodiac"] = mingpan_result.get("zodiac")
        
        similar_cases = self.case_library.search_similar_cases(
            zodiac=user_info.get("zodiac"),
            limit=3
        )
        
        case_references = [
            {
                "title": f"案例{c.id}",
                "situation": c.question[:100] if len(c.question) > 100 else c.question,
                "decision": c.final_decision,
                "outcome": c.outcome
            }
            for c in similar_cases
        ]
        
        report = self.report_generator.generate_report(
            report_type=report_type,
            user_info=user_info,
            analysis=analysis,
            recommendations=recommendations,
            action_steps=action_steps,
            case_references=case_references
        )
        
        markdown_output = self.report_generator.format_report_markdown(report)
        
        return {
            "report_id": report.report_id,
            "report_type": report_type,
            "intent": intent_result.intent.value,
            "confidence": intent_result.confidence,
            "sub_category": sub_category,
            "user_info": user_info,
            "analysis": analysis,
            "recommendations": recommendations,
            "action_steps": action_steps,
            "similar_cases": case_references,
            "markdown": markdown_output,
            "generated_at": report.generated_at
        }
    
    async def _analyze_property(self, user_info: Dict) -> Dict[str, Any]:
        """房产分析"""
        return {
            "analysis": {
                "pattern": {"summary": "房产咨询"},
                "wealth": {"summary": "预算分析"},
                "career": {"summary": "城市选择"},
                "market": {"trend": "稳定"}
            },
            "recommendations": [
                {
                    "title": "板块选择",
                    "content": f"根据您的预算{user_info.get('budget', '未知')}万，推荐关注核心板块",
                    "timeline": "近期",
                    "reason": "配套成熟，保值性强"
                }
            ],
            "action_steps": [
                {"step": 1, "action": "实地考察意向板块", "timeline": "本周"},
                {"step": 2, "action": "对比同价位房源", "timeline": "两周内"}
            ]
        }
    
    def _analyze_mingpan(self, user_info: Dict) -> Dict[str, Any]:
        """命盘分析"""
        birth_info = {
            "year": user_info.get("birth_year", 1990),
            "month": user_info.get("birth_month", 1),
            "day": user_info.get("birth_day", 1),
            "hour": user_info.get("birth_hour", 0)
        }
        
        result = self.mingpan_module.analyze(birth_info)
        six_dim = result.get("six_dimensions", {})
        
        return {
            "analysis": six_dim,
            "recommendations": [
                {
                    "title": "事业方向",
                    "content": f"适合往{result.get('favorable_direction')}方发展",
                    "reason": six_dim.get("career", {}).get("advice", "")
                },
                {
                    "title": "财运建议",
                    "content": six_dim.get("wealth", {}).get("advice", ""),
                    "reason": six_dim.get("wealth", {}).get("summary", "")
                }
            ],
            "action_steps": [
                {"step": 1, "action": "明确自己的优势和方向", "timeline": "本周"},
                {"step": 2, "action": "制定阶段性目标", "timeline": "两周内"}
            ]
        }
    
    def _analyze_emotion(self, request: ReportRequest, user_info: Dict) -> Dict[str, Any]:
        """情感分析"""
        user_birth = {
            "year": user_info.get("birth_year", 1990),
            "month": user_info.get("birth_month", 1),
            "day": user_info.get("birth_day", 1),
            "hour": user_info.get("birth_hour", 0)
        }
        
        partner_birth = None
        if request.partner_birth_year:
            partner_birth = {
                "year": request.partner_birth_year,
                "month": request.partner_birth_month or 1,
                "day": request.partner_birth_day or 1,
                "hour": 0
            }
        
        if partner_birth:
            compatibility = self.mingpan_module.check_compatibility(user_birth, partner_birth)
        else:
            compatibility = {"score": 60, "compatibility": "需要提供双方出生信息进行合盘分析"}
        
        emotion_result = self.emotion_module.analyze(user_birth, request.question)
        
        return {
            "analysis": {
                "compatibility": compatibility,
                "marriage": emotion_result.get("marriage_analysis", {}),
                "conflicts": emotion_result.get("conflicts", [])
            },
            "recommendations": [
                {
                    "title": "关系建议",
                    "content": self.emotion_module.get_relationship_advice(
                        compatibility.get("score", 60),
                        []
                    ),
                    "reason": "基于合盘分析"
                }
            ] + [
                {
                    "title": f"解决{s.get('type', '问题')}",
                    "content": s.get("suggestions", [""])[0] if s.get("suggestions") else "",
                    "reason": s.get("type", "")
                }
                for s in emotion_result.get("conflicts", [])[:2]
            ],
            "action_steps": [
                {"step": 1, "action": "坦诚沟通当前困扰", "timeline": "本周"},
                {"step": 2, "action": "尝试新的相处模式", "timeline": "持续"}
            ]
        }
    
    async def _analyze_mixed(self, user_info: Dict) -> Dict[str, Any]:
        """融合分析"""
        result = await self.fusion_module.analyze(user_info, user_info.get("question", ""))
        
        return {
            "analysis": result.fusion_analysis,
            "recommendations": result.recommendations,
            "action_steps": result.action_steps
        }
    
    def _analyze_general(self, user_info: Dict) -> Dict[str, Any]:
        """通用分析"""
        return {
            "analysis": {
                "pattern": {"summary": "综合分析"},
                "suggestion": "建议先明确您最关心的问题方向"
            },
            "recommendations": [
                {
                    "title": "明确方向",
                    "content": "您可以告诉我您最关心的是事业、感情、还是房产方面的问题",
                    "reason": "更精准的分析需要明确的问题"
                }
            ],
            "action_steps": [
                {"step": 1, "action": "思考您最想解决的问题", "timeline": "现在"}
            ]
        }

report_service = ReportService()
