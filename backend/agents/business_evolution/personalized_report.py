"""
个性化报告生成器
Personalized Report Generator - 生成个性化的房产分析报告

工部智能体增强模块
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
import asyncio
import json
import uuid


class ReportType(Enum):
    BRIEF = "brief"
    STANDARD = "standard"
    DEEP = "deep"
    CUSTOM = "custom"


class ReportStyle(Enum):
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    ZHOUYU = "zhouyu"
    LUXUN = "luxun"
    TECHNICAL = "technical"


class ReportSection(Enum):
    EXECUTIVE_SUMMARY = "executive_summary"
    MARKET_OVERVIEW = "market_overview"
    PRICE_ANALYSIS = "price_analysis"
    LOCATION_ANALYSIS = "location_analysis"
    FACILITY_ANALYSIS = "facility_analysis"
    TRAFFIC_ANALYSIS = "traffic_analysis"
    SCHOOL_DISTRICT = "school_district"
    INVESTMENT_ANALYSIS = "investment_analysis"
    RISK_ASSESSMENT = "risk_assessment"
    RECOMMENDATIONS = "recommendations"
    APPENDIX = "appendix"


@dataclass
class ReportTemplate:
    template_id: str
    name: str
    report_type: ReportType
    sections: List[ReportSection]
    page_count: int
    style: ReportStyle
    is_default: bool = False
    created_by: str = "system"
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ReportContent:
    section: ReportSection
    title: str
    content: str
    data_points: Dict[str, Any]
    charts: List[Dict[str, Any]]
    tables: List[Dict[str, Any]]
    footnotes: List[str] = field(default_factory=list)


@dataclass
class GeneratedReport:
    report_id: str
    template_id: str
    title: str
    report_type: ReportType
    style: ReportStyle
    contents: List[ReportContent]
    generated_at: datetime
    generated_for: str
    parameters: Dict[str, Any]
    version: int = 1
    file_url: Optional[str] = None
    page_count: int = 0


class TemplateLibrary:
    def __init__(self):
        self.templates: Dict[str, ReportTemplate] = {}
        self._initialize_default_templates()

    def _initialize_default_templates(self) -> None:
        brief_template = ReportTemplate(
            template_id="brief_001",
            name="简要版报告",
            report_type=ReportType.BRIEF,
            sections=[
                ReportSection.EXECUTIVE_SUMMARY,
                ReportSection.PRICE_ANALYSIS,
                ReportSection.RECOMMENDATIONS,
            ],
            page_count=5,
            style=ReportStyle.CASUAL,
            is_default=True,
        )

        standard_template = ReportTemplate(
            template_id="standard_001",
            name="标准版报告",
            report_type=ReportType.STANDARD,
            sections=[
                ReportSection.EXECUTIVE_SUMMARY,
                ReportSection.MARKET_OVERVIEW,
                ReportSection.PRICE_ANALYSIS,
                ReportSection.LOCATION_ANALYSIS,
                ReportSection.FACILITY_ANALYSIS,
                ReportSection.RECOMMENDATIONS,
            ],
            page_count=10,
            style=ReportStyle.PROFESSIONAL,
            is_default=True,
        )

        deep_template = ReportTemplate(
            template_id="deep_001",
            name="深度版报告",
            report_type=ReportType.DEEP,
            sections=[
                ReportSection.EXECUTIVE_SUMMARY,
                ReportSection.MARKET_OVERVIEW,
                ReportSection.PRICE_ANALYSIS,
                ReportSection.LOCATION_ANALYSIS,
                ReportSection.FACILITY_ANALYSIS,
                ReportSection.TRAFFIC_ANALYSIS,
                ReportSection.SCHOOL_DISTRICT,
                ReportSection.INVESTMENT_ANALYSIS,
                ReportSection.RISK_ASSESSMENT,
                ReportSection.RECOMMENDATIONS,
                ReportSection.APPENDIX,
            ],
            page_count=20,
            style=ReportStyle.PROFESSIONAL,
            is_default=True,
        )

        self.templates[brief_template.template_id] = brief_template
        self.templates[standard_template.template_id] = standard_template
        self.templates[deep_template.template_id] = deep_template

    def get_template(self, template_id: str) -> Optional[ReportTemplate]:
        return self.templates.get(template_id)

    def get_default_template(self, report_type: ReportType) -> ReportTemplate:
        for template in self.templates.values():
            if template.report_type == report_type and template.is_default:
                return template

        return list(self.templates.values())[0]

    def add_template(self, template: ReportTemplate) -> None:
        self.templates[template.template_id] = template

    def list_templates(self) -> List[ReportTemplate]:
        return list(self.templates.values())


class ContentGenerator:
    STYLE_TEMPLATES = {
        ReportStyle.PROFESSIONAL: {
            "header": "## {title}\n\n",
            "paragraph": "{content}\n\n",
            "list_item": "- {item}\n",
            "emphasis": "**{text}**",
        },
        ReportStyle.CASUAL: {
            "header": "### {title} ###\n\n",
            "paragraph": "{content}\n\n",
            "list_item": "• {item}\n",
            "emphasis": "*{text}*",
        },
        ReportStyle.ZHOUYU: {
            "header": "【{title}】\n\n",
            "paragraph": "{content}\n\n",
            "list_item": "其一，{item}\n",
            "emphasis": "「{text}」",
        },
        ReportStyle.LUXUN: {
            "header": "{title}\n{'─' * 20}\n\n",
            "paragraph": "{content}\n\n",
            "list_item": "· {item}\n",
            "emphasis": "「{text}」",
        },
    }

    def __init__(self):
        self.section_generators: Dict[ReportSection, callable] = {}

    def generate_section(
        self,
        section: ReportSection,
        data: Dict[str, Any],
        style: ReportStyle,
        user_profile: Dict[str, Any] = None,
    ) -> ReportContent:
        generator = self.section_generators.get(section, self._default_generator)
        return generator(section, data, style, user_profile)

    def _default_generator(
        self,
        section: ReportSection,
        data: Dict[str, Any],
        style: ReportStyle,
        user_profile: Dict[str, Any] = None,
    ) -> ReportContent:
        style_template = self.STYLE_TEMPLATES.get(style, self.STYLE_TEMPLATES[ReportStyle.PROFESSIONAL])

        title = self._get_section_title(section)
        content = self._generate_content(section, data, style_template, user_profile)

        return ReportContent(
            section=section,
            title=title,
            content=content,
            data_points=data,
            charts=[],
            tables=[],
        )

    def _get_section_title(self, section: ReportSection) -> str:
        titles = {
            ReportSection.EXECUTIVE_SUMMARY: "执行摘要",
            ReportSection.MARKET_OVERVIEW: "市场概况",
            ReportSection.PRICE_ANALYSIS: "价格分析",
            ReportSection.LOCATION_ANALYSIS: "区位分析",
            ReportSection.FACILITY_ANALYSIS: "配套分析",
            ReportSection.TRAFFIC_ANALYSIS: "交通分析",
            ReportSection.SCHOOL_DISTRICT: "学区分析",
            ReportSection.INVESTMENT_ANALYSIS: "投资分析",
            ReportSection.RISK_ASSESSMENT: "风险评估",
            ReportSection.RECOMMENDATIONS: "建议与结论",
            ReportSection.APPENDIX: "附录",
        }
        return titles.get(section, section.value)

    def _generate_content(
        self,
        section: ReportSection,
        data: Dict[str, Any],
        style_template: Dict[str, str],
        user_profile: Dict[str, Any] = None,
    ) -> str:
        content_parts = []

        if section == ReportSection.EXECUTIVE_SUMMARY:
            content_parts.append(
                style_template["paragraph"].format(
                    content=f"本报告对{data.get('community_name', '目标小区')}进行全面分析。"
                )
            )
            content_parts.append(
                style_template["paragraph"].format(
                    content=f"当前均价：{data.get('avg_price', 'N/A')}元/㎡"
                )
            )

        elif section == ReportSection.PRICE_ANALYSIS:
            content_parts.append(
                style_template["header"].format(title="价格走势")
            )
            content_parts.append(
                style_template["paragraph"].format(
                    content=f"近一年价格变化：{data.get('price_change', 'N/A')}"
                )
            )

        elif section == ReportSection.RECOMMENDATIONS:
            content_parts.append(
                style_template["header"].format(title="综合建议")
            )
            recommendations = data.get("recommendations", [])
            for rec in recommendations[:5]:
                content_parts.append(style_template["list_item"].format(item=rec))

        return "".join(content_parts)

    def register_section_generator(
        self, section: ReportSection, generator: callable
    ) -> None:
        self.section_generators[section] = generator


class ChartGenerator:
    def __init__(self):
        self.chart_templates: Dict[str, Dict] = {}

    def generate_chart(
        self,
        chart_type: str,
        data: Dict[str, Any],
        options: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        chart_id = f"chart_{uuid.uuid4().hex[:8]}"

        chart = {
            "chart_id": chart_id,
            "type": chart_type,
            "data": data,
            "options": options or {},
            "interactive": True,
            "responsive": True,
        }

        return chart

    def generate_price_trend_chart(
        self, price_data: List[Dict]
    ) -> Dict[str, Any]:
        return self.generate_chart(
            "line",
            {
                "labels": [d.get("date") for d in price_data],
                "datasets": [
                    {
                        "label": "均价(元/㎡)",
                        "data": [d.get("price") for d in price_data],
                        "borderColor": "#4CAF50",
                        "fill": False,
                    }
                ],
            },
            {
                "title": "价格走势图",
                "xAxisLabel": "日期",
                "yAxisLabel": "价格",
            },
        )

    def generate_comparison_chart(
        self, comparison_data: List[Dict]
    ) -> Dict[str, Any]:
        return self.generate_chart(
            "bar",
            {
                "labels": [d.get("name") for d in comparison_data],
                "datasets": [
                    {
                        "label": "均价(元/㎡)",
                        "data": [d.get("price") for d in comparison_data],
                        "backgroundColor": "#2196F3",
                    }
                ],
            },
            {
                "title": "区域对比图",
            },
        )


class PersonalizedReportGenerator:
    def __init__(self, agent_id: str = "report_generator_001"):
        self.agent_id = agent_id
        self.template_library = TemplateLibrary()
        self.content_generator = ContentGenerator()
        self.chart_generator = ChartGenerator()

        self.generated_reports: List[GeneratedReport] = []
        self.user_templates: Dict[str, List[str]] = {}

    async def generate(
        self,
        data: Dict[str, Any],
        template_id: str = None,
        report_type: ReportType = None,
        style: ReportStyle = None,
        user_profile: Dict[str, Any] = None,
        user_id: str = None,
    ) -> GeneratedReport:
        if template_id:
            template = self.template_library.get_template(template_id)
        else:
            template = self.template_library.get_default_template(
                report_type or ReportType.STANDARD
            )

        if style:
            template = ReportTemplate(
                template_id=template.template_id,
                name=template.name,
                report_type=template.report_type,
                sections=template.sections,
                page_count=template.page_count,
                style=style,
            )

        personalized_sections = self._personalize_sections(
            template.sections, user_profile
        )

        contents = []
        for section in personalized_sections:
            content = self.content_generator.generate_section(
                section, data, template.style, user_profile
            )

            if section == ReportSection.PRICE_ANALYSIS and "price_history" in data:
                content.charts.append(
                    self.chart_generator.generate_price_trend_chart(
                        data["price_history"]
                    )
                )

            contents.append(content)

        report = GeneratedReport(
            report_id=f"report_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
            template_id=template.template_id,
            title=self._generate_title(data, template),
            report_type=template.report_type,
            style=template.style,
            contents=contents,
            generated_at=datetime.utcnow(),
            generated_for=user_id or "anonymous",
            parameters=data,
            page_count=template.page_count,
        )

        self.generated_reports.append(report)

        return report

    def _personalize_sections(
        self,
        sections: List[ReportSection],
        user_profile: Dict[str, Any] = None,
    ) -> List[ReportSection]:
        if not user_profile:
            return sections

        personalized = list(sections)

        user_type = user_profile.get("user_type", "regular")

        if user_type == "investor":
            if ReportSection.INVESTMENT_ANALYSIS not in personalized:
                personalized.insert(-1, ReportSection.INVESTMENT_ANALYSIS)
            if ReportSection.RISK_ASSESSMENT not in personalized:
                personalized.insert(-1, ReportSection.RISK_ASSESSMENT)

        elif user_type == "first_time_buyer":
            if ReportSection.SCHOOL_DISTRICT not in personalized:
                personalized.insert(-2, ReportSection.SCHOOL_DISTRICT)

        return personalized

    def _generate_title(
        self, data: Dict[str, Any], template: ReportTemplate
    ) -> str:
        community = data.get("community_name", "房产")
        region = data.get("region", "")

        type_names = {
            ReportType.BRIEF: "简要分析报告",
            ReportType.STANDARD: "分析报告",
            ReportType.DEEP: "深度分析报告",
        }

        return f"{community}{type_names.get(template.report_type, '报告')}"

    def save_user_template(
        self, user_id: str, template: ReportTemplate
    ) -> None:
        if user_id not in self.user_templates:
            self.user_templates[user_id] = []

        self.user_templates[user_id].append(template.template_id)
        self.template_library.add_template(template)

    def get_user_templates(self, user_id: str) -> List[ReportTemplate]:
        template_ids = self.user_templates.get(user_id, [])
        return [
            self.template_library.get_template(tid)
            for tid in template_ids
            if self.template_library.get_template(tid)
        ]

    def get_report(self, report_id: str) -> Optional[GeneratedReport]:
        return next(
            (r for r in self.generated_reports if r.report_id == report_id), None
        )

    def compare_versions(
        self, report_id1: str, report_id2: str
    ) -> Optional[Dict[str, Any]]:
        report1 = self.get_report(report_id1)
        report2 = self.get_report(report_id2)

        if not report1 or not report2:
            return None

        return {
            "report1": {
                "id": report1.report_id,
                "generated_at": report1.generated_at.isoformat(),
                "page_count": report1.page_count,
            },
            "report2": {
                "id": report2.report_id,
                "generated_at": report2.generated_at.isoformat(),
                "page_count": report2.page_count,
            },
            "time_difference": (
                report2.generated_at - report1.generated_at
            ).total_seconds(),
        }

    def export_to_markdown(self, report: GeneratedReport) -> str:
        lines = [
            f"# {report.title}",
            "",
            f"*生成时间: {report.generated_at.strftime('%Y-%m-%d %H:%M')}*",
            "",
        ]

        for content in report.contents:
            lines.append(f"## {content.title}")
            lines.append("")
            lines.append(content.content)
            lines.append("")

        return "\n".join(lines)

    def export_to_json(self, report: GeneratedReport) -> str:
        data = {
            "report_id": report.report_id,
            "title": report.title,
            "report_type": report.report_type.value,
            "style": report.style.value,
            "generated_at": report.generated_at.isoformat(),
            "contents": [
                {
                    "section": c.section.value,
                    "title": c.title,
                    "content": c.content,
                    "data_points": c.data_points,
                }
                for c in report.contents
            ],
            "parameters": report.parameters,
        }
        return json.dumps(data, ensure_ascii=False, indent=2)

    def get_generation_stats(self) -> Dict[str, Any]:
        if not self.generated_reports:
            return {"total_reports": 0}

        type_counts: Dict[str, int] = {}
        for report in self.generated_reports:
            rt = report.report_type.value
            type_counts[rt] = type_counts.get(rt, 0) + 1

        return {
            "total_reports": len(self.generated_reports),
            "by_type": type_counts,
            "templates_available": len(self.template_library.templates),
        }
