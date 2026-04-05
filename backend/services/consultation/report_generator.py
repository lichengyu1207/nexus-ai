# -*- coding: utf-8 -*-
"""
Report Generator
Generates consultation reports with multi-source data fusion
"""
import logging
import uuid
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime

from backend.database_pg import PostgreSQLConnectionPool
from backend.services.consultation.report_template_engine import (
    ReportTemplateEngine, get_report_template_engine, ReportTemplate
)
from backend.services.consultation.persona_engine import (
    PersonaEngine, get_persona_engine, PersonaConfig
)
from backend.services.consultation.thinking_gene_service import ThinkingGeneService

logger = logging.getLogger(__name__)


class ReportStatus(Enum):
    DRAFT = "draft"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    REVOKED = "revoked"


@dataclass
class DataSource:
    source_id: str
    source_type: str
    source_name: str
    retrieved_at: str
    data_summary: str


@dataclass
class ReportGenerationRequest:
    session_id: str
    user_id: str
    intent: str
    slots: Dict
    messages: List[Dict]
    persona_name: str
    gene_dimensions: Dict
    skill_results: List[Dict] = field(default_factory=list)
    case_references: List[str] = field(default_factory=list)


@dataclass
class ReportGenerationResult:
    report_id: str
    status: str
    title: str
    content: Dict
    quality_score: float
    objectivity_score: float
    generation_time_ms: int
    error_message: Optional[str] = None


class ReportGenerator:
    def __init__(self, db: PostgreSQLConnectionPool = None):
        self.db = db
        self.template_engine = get_report_template_engine()
        self._quality_rules = self._load_quality_rules()
        self._objectivity_checker = self._load_objectivity_checker()
    
    def _load_quality_rules(self) -> Dict:
        return {
            "min_sections": 3,
            "min_content_length": 100,
            "required_sections": ["summary", "recommendations"],
            "max_consecutive_sentences": 5,
            "min_data_sources": 1
        }
    
    def _load_objectivity_checker(self) -> Dict:
        return {
            "absolute_words": ["一定", "必然", "绝对", "肯定", "百分之百", "必然", "肯定"],
            "replacements": {
                "一定": "可能",
                "必然": "很有可能",
                "绝对": "比较",
                "肯定": "应该",
                "百分之百": "大概率"
            },
            "subjective_phrases": [
                "我觉得", "我认为", "我确信", "我保证"
            ]
        }
    
    async def generate_report(
        self,
        request: ReportGenerationRequest
    ) -> ReportGenerationResult:
        start_time = time.time()
        report_id = str(uuid.uuid4())
        
        try:
            template = self.template_engine.get_template(request.intent)
            if not template:
                template = self.template_engine.get_template("general_question")
            
            sections_data = await self._generate_sections(request)
            
            context = {
                "slots": request.slots,
                "persona": request.persona_name,
                "user_profile": {},
                "persona_config": {"display_name": request.persona_name}
            }
            
            report_content = self.template_engine.assemble_report(
                template, sections_data, request.persona_name, context
            )
            
            report_content["data_sources"] = self._format_data_sources(
                request.skill_results
            )
            
            if request.case_references:
                report_content["case_references"] = request.case_references
            
            quality_score = self._calculate_quality_score(report_content)
            objectivity_score = self._calculate_objectivity_score(report_content)
            
            if objectivity_score < 0.7:
                report_content = self._apply_objectivity_fixes(report_content)
                objectivity_score = self._calculate_objectivity_score(report_content)
            
            generation_time = int((time.time() - start_time) * 1000)
            
            await self._save_report(
                report_id, request, report_content, quality_score, objectivity_score
            )
            
            return ReportGenerationResult(
                report_id=report_id,
                status=ReportStatus.COMPLETED.value,
                title=report_content["title"],
                content=report_content,
                quality_score=quality_score,
                objectivity_score=objectivity_score,
                generation_time_ms=generation_time
            )
            
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            generation_time = int((time.time() - start_time) * 1000)
            
            return ReportGenerationResult(
                report_id=report_id,
                status=ReportStatus.FAILED.value,
                title="报告生成失败",
                content={},
                quality_score=0,
                objectivity_score=0,
                generation_time_ms=generation_time,
                error_message=str(e)
            )
    
    async def _generate_sections(
        self,
        request: ReportGenerationRequest
    ) -> Dict[str, Dict]:
        sections = {}
        
        sections["summary"] = self._generate_summary(request)
        
        if request.intent == "property_consultation":
            sections["market_analysis"] = self._generate_market_analysis(request)
            sections["area_analysis"] = self._generate_area_analysis(request)
            sections["recommendations"] = self._generate_property_recommendations(request)
            sections["risk_assessment"] = self._generate_risk_assessment(request)
        
        elif request.intent == "destiny_consultation":
            sections["destiny_chart"] = self._generate_destiny_chart(request)
            sections["life_analysis"] = self._generate_life_analysis(request)
            sections["recommendations"] = self._generate_destiny_recommendations(request)
        
        elif request.intent == "investment_advice":
            sections["market_outlook"] = self._generate_market_outlook(request)
            sections["investment_analysis"] = self._generate_investment_analysis(request)
            sections["risk_assessment"] = self._generate_investment_risk(request)
            sections["recommendations"] = self._generate_investment_recommendations(request)
        
        elif request.intent == "emotional_support":
            sections["situation_analysis"] = self._generate_situation_analysis(request)
            sections["emotional_guidance"] = self._generate_emotional_guidance(request)
            sections["action_plan"] = self._generate_action_plan(request)
        
        else:
            sections["analysis"] = self._generate_general_analysis(request)
            sections["recommendations"] = self._generate_general_recommendations(request)
        
        sections["disclaimer"] = {
            "content": self.template_engine.generate_disclaimer(
                request.intent, request.persona_name
            )
        }
        
        return sections
    
    def _generate_summary(self, request: ReportGenerationRequest) -> Dict:
        if request.persona_name == "zhouyu":
            content = f"阁下咨询{request.intent.replace('_', '')}事宜，经我深入分析，现呈报告如下。"
        else:
            content = f"本报告基于您的咨询需求，结合市场数据和专业分析，为您提供参考建议。"
        
        return {"content": content}
    
    def _generate_market_analysis(self, request: ReportGenerationRequest) -> Dict:
        city = request.slots.get("city", "您关注的城市")
        budget = request.slots.get("budget", 0)
        
        if request.persona_name == "zhouyu":
            content = f"{city}房产市场，经我观察，正处于关键时期。阁下预算{budget/10000:.0f}万，当审时度势，把握良机。"
        else:
            content = f"根据最新市场数据，{city}房产市场整体保持稳定。您的预算为{budget/10000:.0f}万元，建议关注性价比较高的区域。"
        
        return {
            "content": content,
            "data_sources": ["market_data_api"]
        }
    
    def _generate_area_analysis(self, request: ReportGenerationRequest) -> Dict:
        city = request.slots.get("city", "")
        area = request.slots.get("area_preference", "")
        
        if request.persona_name == "zhouyu":
            content = f"{city}{area}区域，位置优越，发展潜力巨大。阁下若有意，当果断出手！"
        else:
            content = f"{city}{area}区域配套设施完善，交通便利，适合居住。建议实地考察后再做决定。"
        
        return {"content": content}
    
    def _generate_property_recommendations(self, request: ReportGenerationRequest) -> Dict:
        city = request.slots.get("city", "")
        budget = request.slots.get("budget", 0)
        
        if request.persona_name == "zhouyu":
            recommendations = [
                f"建议阁下重点关注{city}核心区域的新盘",
                "时机已到，可考虑出手",
                "切记把握政策窗口期"
            ]
        else:
            recommendations = [
                f"建议您关注{city}性价比较高的区域",
                "可以先租房观察市场走势",
                "建议多对比几个楼盘后再做决定"
            ]
        
        return {
            "content": "\n".join([f"{i+1}. {r}" for i, r in enumerate(recommendations)])
        }
    
    def _generate_risk_assessment(self, request: ReportGenerationRequest) -> Dict:
        risks = [
            "市场波动风险：房产价格可能受政策影响",
            "流动性风险：房产变现周期较长",
            "政策风险：限购限贷政策可能调整"
        ]
        
        return {
            "content": "\n".join([f"• {r}" for r in risks])
        }
    
    def _generate_destiny_chart(self, request: ReportGenerationRequest) -> Dict:
        birth_date = request.slots.get("birth_date", "")
        
        return {
            "content": f"根据您的出生日期{birth_date}，您的命盘格局显示：事业运旺盛，财运平稳，感情运需耐心等待。"
        }
    
    def _generate_life_analysis(self, request: ReportGenerationRequest) -> Dict:
        return {
            "content": "从命理角度分析，您目前正处于事业上升期，适合积极进取。感情方面需要更多耐心。"
        }
    
    def _generate_destiny_recommendations(self, request: ReportGenerationRequest) -> Dict:
        if request.persona_name == "zhouyu":
            recommendations = [
                "阁下当把握机遇，积极进取",
                "贵人运佳，可多结交益友",
                "财运平稳，不宜冒险投资"
            ]
        else:
            recommendations = [
                "建议保持积极心态，把握机会",
                "可以多参加社交活动，拓展人脉",
                "投资方面建议保守为主"
            ]
        
        return {
            "content": "\n".join([f"{i+1}. {r}" for i, r in enumerate(recommendations)])
        }
    
    def _generate_market_outlook(self, request: ReportGenerationRequest) -> Dict:
        return {
            "content": "当前市场整体稳定，短期内大幅波动的可能性较低。建议关注政策动向。"
        }
    
    def _generate_investment_analysis(self, request: ReportGenerationRequest) -> Dict:
        amount = request.slots.get("investment_amount", 0)
        
        return {
            "content": f"根据您的投资金额{amount/10000:.0f}万元，建议分散投资，降低风险。"
        }
    
    def _generate_investment_risk(self, request: ReportGenerationRequest) -> Dict:
        risks = [
            "市场风险：价格波动可能导致损失",
            "政策风险：政策变化影响投资收益",
            "流动性风险：资产变现可能受限"
        ]
        
        return {
            "content": "\n".join([f"• {r}" for r in risks])
        }
    
    def _generate_investment_recommendations(self, request: ReportGenerationRequest) -> Dict:
        return {
            "content": "1. 建议分散投资，不要把所有资金投入单一资产\n2. 关注政策动向，及时调整策略\n3. 保持合理预期，避免盲目追高"
        }
    
    def _generate_situation_analysis(self, request: ReportGenerationRequest) -> Dict:
        return {
            "content": "根据您的描述，您目前可能面临一些压力和困扰。这是很正常的情绪反应。"
        }
    
    def _generate_emotional_guidance(self, request: ReportGenerationRequest) -> Dict:
        if request.persona_name == "zhouyu":
            return {
                "content": "人生起伏乃常事，阁下不必过于忧虑。保持乐观心态，积极面对挑战！"
            }
        else:
            return {
                "content": "每个人都会遇到困难和挫折，重要的是如何面对。建议您：\n1. 保持规律作息\n2. 适当运动\n3. 与亲友交流"
            }
    
    def _generate_action_plan(self, request: ReportGenerationRequest) -> Dict:
        return {
            "content": "建议您制定一个具体的行动计划：\n1. 明确当前面临的主要问题\n2. 列出可能的解决方案\n3. 逐步实施并调整"
        }
    
    def _generate_general_analysis(self, request: ReportGenerationRequest) -> Dict:
        return {
            "content": "根据您的咨询内容，我进行了综合分析。"
        }
    
    def _generate_general_recommendations(self, request: ReportGenerationRequest) -> Dict:
        return {
            "content": "如有更多问题，欢迎继续咨询。"
        }
    
    def _format_data_sources(self, skill_results: List[Dict]) -> List[Dict]:
        sources = []
        for result in skill_results:
            sources.append({
                "skill_name": result.get("skill_name", ""),
                "invoked_at": result.get("invoked_at", ""),
                "status": result.get("status", "")
            })
        return sources
    
    def _calculate_quality_score(self, content: Dict) -> float:
        score = 1.0
        
        sections = content.get("sections", [])
        if len(sections) < self._quality_rules["min_sections"]:
            score -= 0.2
        
        required_found = 0
        for section in sections:
            if section.get("id") in self._quality_rules["required_sections"]:
                required_found += 1
        
        if required_found < len(self._quality_rules["required_sections"]):
            score -= 0.2
        
        total_content_length = sum(
            len(s.get("content", "")) for s in sections
        )
        if total_content_length < self._quality_rules["min_content_length"]:
            score -= 0.3
        
        return max(score, 0)
    
    def _calculate_objectivity_score(self, content: Dict) -> float:
        score = 1.0
        text = json.dumps(content, ensure_ascii=False)
        
        for word in self._objectivity_checker["absolute_words"]:
            count = text.count(word)
            score -= count * 0.05
        
        for phrase in self._objectivity_checker["subjective_phrases"]:
            if phrase in text:
                score -= 0.1
        
        return max(score, 0)
    
    def _apply_objectivity_fixes(self, content: Dict) -> Dict:
        text = json.dumps(content, ensure_ascii=False)
        
        for old, new in self._objectivity_checker["replacements"].items():
            text = text.replace(old, new)
        
        return json.loads(text)
    
    async def _save_report(
        self,
        report_id: str,
        request: ReportGenerationRequest,
        content: Dict,
        quality_score: float,
        objectivity_score: float
    ):
        if not self.db:
            return
        
        async with self.db.get_connection() as conn:
            await conn.execute("""
                INSERT INTO consultation_reports 
                (id, session_id, user_id, title, content, persona, gene_dimensions,
                 quality_score, objectivity_score, version, is_latest)
                VALUES ($1, $2, $3, $4, $5::jsonb, $6, $7::jsonb, $8, $9, 1, true)
            """, report_id, request.session_id, request.user_id,
                content.get("title", ""), content, request.persona_name,
                request.gene_dimensions, quality_score, objectivity_score)
            
            await conn.execute("""
                UPDATE consultation_sessions 
                SET report_id = $1, status = 'completed'
                WHERE id = $2
            """, report_id, request.session_id)


report_generator: Optional[ReportGenerator] = None


async def get_report_generator(db: PostgreSQLConnectionPool = None) -> ReportGenerator:
    global report_generator
    if report_generator is None:
        report_generator = ReportGenerator(db)
    return report_generator
