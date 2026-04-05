# -*- coding: utf-8 -*-
"""
Report Template Engine
Dynamic report generation with persona-based styling
"""
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import json
import re
from datetime import datetime

logger = logging.getLogger(__name__)


class ReportSection(Enum):
    SUMMARY = "summary"
    ANALYSIS = "analysis"
    RECOMMENDATIONS = "recommendations"
    DATA_SOURCES = "data_sources"
    RISK_ASSESSMENT = "risk_assessment"
    CASE_REFERENCES = "case_references"
    DISCLAIMER = "disclaimer"


@dataclass
class ReportSectionContent:
    section_id: str
    title: str
    content: str
    order: int
    is_collapsible: bool = False
    data_source_refs: List[str] = field(default_factory=list)


@dataclass
class ReportTemplate:
    template_id: str
    template_name: str
    intent_type: str
    sections: List[ReportSectionContent]
    persona_style: str
    metadata: Dict = field(default_factory=dict)


class ReportTemplateEngine:
    def __init__(self):
        self._templates = self._load_templates()
        self._style_configs = self._load_style_configs()
        self._variable_resolvers = self._load_variable_resolvers()
    
    def _load_templates(self) -> Dict[str, ReportTemplate]:
        return {
            "property_consultation": ReportTemplate(
                template_id="prop_001",
                template_name="房产咨询报告",
                intent_type="property_consultation",
                sections=[
                    ReportSectionContent("summary", "咨询摘要", "", 1),
                    ReportSectionContent("market_analysis", "市场分析", "", 2),
                    ReportSectionContent("area_analysis", "区域分析", "", 3),
                    ReportSectionContent("recommendations", "购房建议", "", 4),
                    ReportSectionContent("risk_assessment", "风险评估", "", 5, True),
                    ReportSectionContent("data_sources", "数据来源", "", 6, True),
                    ReportSectionContent("disclaimer", "免责声明", "", 7, True)
                ],
                persona_style="balanced"
            ),
            "destiny_consultation": ReportTemplate(
                template_id="dest_001",
                template_name="命理咨询报告",
                intent_type="destiny_consultation",
                sections=[
                    ReportSectionContent("summary", "咨询摘要", "", 1),
                    ReportSectionContent("destiny_chart", "命盘解读", "", 2),
                    ReportSectionContent("life_analysis", "人生运势", "", 3),
                    ReportSectionContent("recommendations", "建议指导", "", 4),
                    ReportSectionContent("case_references", "案例参考", "", 5, True),
                    ReportSectionContent("disclaimer", "免责声明", "", 6, True)
                ],
                persona_style="balanced"
            ),
            "investment_advice": ReportTemplate(
                template_id="inv_001",
                template_name="投资建议报告",
                intent_type="investment_advice",
                sections=[
                    ReportSectionContent("summary", "投资摘要", "", 1),
                    ReportSectionContent("market_outlook", "市场展望", "", 2),
                    ReportSectionContent("investment_analysis", "投资分析", "", 3),
                    ReportSectionContent("risk_assessment", "风险评估", "", 4),
                    ReportSectionContent("recommendations", "投资建议", "", 5),
                    ReportSectionContent("data_sources", "数据来源", "", 6, True),
                    ReportSectionContent("disclaimer", "免责声明", "", 7, True)
                ],
                persona_style="analytical"
            ),
            "emotional_support": ReportTemplate(
                template_id="emo_001",
                template_name="情感支持报告",
                intent_type="emotional_support",
                sections=[
                    ReportSectionContent("summary", "咨询摘要", "", 1),
                    ReportSectionContent("situation_analysis", "情况分析", "", 2),
                    ReportSectionContent("emotional_guidance", "情感指导", "", 3),
                    ReportSectionContent("action_plan", "行动计划", "", 4),
                    ReportSectionContent("resources", "资源推荐", "", 5, True),
                    ReportSectionContent("disclaimer", "温馨提示", "", 6, True)
                ],
                persona_style="empathetic"
            ),
            "general_question": ReportTemplate(
                template_id="gen_001",
                template_name="综合咨询报告",
                intent_type="general_question",
                sections=[
                    ReportSectionContent("summary", "咨询摘要", "", 1),
                    ReportSectionContent("analysis", "问题分析", "", 2),
                    ReportSectionContent("recommendations", "建议方案", "", 3),
                    ReportSectionContent("next_steps", "后续步骤", "", 4),
                    ReportSectionContent("disclaimer", "免责声明", "", 5, True)
                ],
                persona_style="balanced"
            )
        }
    
    def _load_style_configs(self) -> Dict[str, Dict]:
        return {
            "zhouyu": {
                "title_style": "bold_direct",
                "paragraph_style": "concise",
                "list_style": "bullet_points",
                "emphasis_words": ["关键", "核心", "重点"],
                "avoid_words": ["可能", "也许", "大概"],
                "title_prefix": "【",
                "title_suffix": "】",
                "conclusion_style": "decisive"
            },
            "luxun": {
                "title_style": "professional",
                "paragraph_style": "detailed",
                "list_style": "numbered",
                "emphasis_words": ["值得注意的是", "需要关注", "建议考虑"],
                "avoid_words": ["一定", "必然", "绝对"],
                "title_prefix": "",
                "title_suffix": "",
                "conclusion_style": "balanced"
            }
        }
    
    def _load_variable_resolvers(self) -> Dict[str, callable]:
        return {
            "user_name": lambda ctx: ctx.get("user_profile", {}).get("name", "阁下" if ctx.get("persona") == "zhouyu" else "您"),
            "city": lambda ctx: ctx.get("slots", {}).get("city", "您关注的城市"),
            "budget": lambda ctx: f"{ctx.get('slots', {}).get('budget', 0):,.0f}元",
            "current_date": lambda ctx: datetime.now().strftime("%Y年%m月%d日"),
            "persona_name": lambda ctx: ctx.get("persona_config", {}).get("display_name", "顾问")
        }
    
    def get_template(self, intent: str) -> Optional[ReportTemplate]:
        return self._templates.get(intent, self._templates.get("general_question"))
    
    def render_section(
        self,
        section: ReportSectionContent,
        content_data: Dict,
        persona_name: str,
        context: Dict
    ) -> ReportSectionContent:
        style_config = self._style_configs.get(persona_name, self._style_configs["luxun"])
        
        rendered_content = self._apply_style(
            content_data.get("content", ""),
            style_config
        )
        
        rendered_content = self._resolve_variables(rendered_content, context)
        
        title = section.title
        if style_config.get("title_prefix"):
            title = f"{style_config['title_prefix']}{title}{style_config['title_suffix']}"
        
        return ReportSectionContent(
            section_id=section.section_id,
            title=title,
            content=rendered_content,
            order=section.order,
            is_collapsible=section.is_collapsible,
            data_source_refs=content_data.get("data_sources", [])
        )
    
    def _apply_style(self, content: str, style_config: Dict) -> str:
        for avoid_word in style_config.get("avoid_words", []):
            content = content.replace(avoid_word, "")
        
        if style_config.get("paragraph_style") == "concise":
            sentences = re.split(r'[。！？]', content)
            sentences = [s.strip() for s in sentences if s.strip()]
            if len(sentences) > 5:
                sentences = sentences[:5]
            content = "。".join(sentences) + "。"
        
        return content
    
    def _resolve_variables(self, content: str, context: Dict) -> str:
        pattern = r'\{\{(\w+)\}\}'
        
        def replace_var(match):
            var_name = match.group(1)
            resolver = self._variable_resolvers.get(var_name)
            if resolver:
                return resolver(context)
            return match.group(0)
        
        return re.sub(pattern, replace_var, content)
    
    def generate_report_title(
        self,
        intent: str,
        slots: Dict,
        persona_name: str
    ) -> str:
        style_config = self._style_configs.get(persona_name, self._style_configs["luxun"])
        
        title_templates = {
            "property_consultation": {
                "zhouyu": "{city}房产决策之道",
                "luxun": "{city}房产市场分析报告"
            },
            "destiny_consultation": {
                "zhouyu": "命理玄机解读",
                "luxun": "个人命理分析报告"
            },
            "investment_advice": {
                "zhouyu": "投资良机分析",
                "luxun": "投资建议分析报告"
            },
            "emotional_support": {
                "zhouyu": "人生解惑指引",
                "luxun": "情感支持咨询报告"
            },
            "general_question": {
                "zhouyu": "咨询解答",
                "luxun": "综合咨询报告"
            }
        }
        
        intent_templates = title_templates.get(intent, title_templates["general_question"])
        title_template = intent_templates.get(persona_name, intent_templates.get("luxun"))
        
        city = slots.get("city", "")
        title = title_template.format(city=city)
        
        return title
    
    def generate_disclaimer(self, intent: str, persona_name: str) -> str:
        disclaimers = {
            "property_consultation": {
                "zhouyu": "此分析仅供参考，阁下当审时度势，自行决策。",
                "luxun": "本报告基于公开数据分析，仅供参考，不构成投资建议。实际决策请咨询专业人士。"
            },
            "destiny_consultation": {
                "zhouyu": "命理之说，信则有，不信则无。阁下当以理性待之。",
                "luxun": "命理分析仅供参考，人生道路还需自己把握。如有困扰，建议寻求专业心理咨询。"
            },
            "investment_advice": {
                "zhouyu": "投资有风险，决策需谨慎。此建议仅供参考。",
                "luxun": "投资有风险，入市需谨慎。本报告不构成投资建议，请根据自身情况审慎决策。"
            },
            "emotional_support": {
                "zhouyu": "人生起伏乃常事，阁下当保持乐观心态。",
                "luxun": "如果您持续感到困扰，建议寻求专业心理咨询师的帮助。全国心理援助热线：400-161-9995"
            }
        }
        
        intent_disclaimers = disclaimers.get(intent, disclaimers["property_consultation"])
        return intent_disclaimers.get(persona_name, intent_disclaimers.get("luxun"))
    
    def assemble_report(
        self,
        template: ReportTemplate,
        sections_data: Dict[str, Dict],
        persona_name: str,
        context: Dict
    ) -> Dict:
        rendered_sections = []
        
        for section in template.sections:
            section_data = sections_data.get(section.section_id, {})
            rendered = self.render_section(section, section_data, persona_name, context)
            rendered_sections.append(rendered)
        
        rendered_sections.sort(key=lambda s: s.order)
        
        title = self.generate_report_title(
            template.intent_type,
            context.get("slots", {}),
            persona_name
        )
        
        report_content = {
            "title": title,
            "template_id": template.template_id,
            "intent_type": template.intent_type,
            "persona": persona_name,
            "generated_at": datetime.now().isoformat(),
            "sections": [
                {
                    "id": s.section_id,
                    "title": s.title,
                    "content": s.content,
                    "order": s.order,
                    "is_collapsible": s.is_collapsible,
                    "data_sources": s.data_source_refs
                }
                for s in rendered_sections
            ]
        }
        
        return report_content


report_template_engine = ReportTemplateEngine()


def get_report_template_engine() -> ReportTemplateEngine:
    return report_template_engine
