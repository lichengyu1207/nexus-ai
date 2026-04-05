"""
合规报告生成智能体
Compliance Report Agent - 自动生成各类合规审计报告
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
import asyncio
import json
import uuid


class ReportType(Enum):
    PRIVACY_AUDIT = "privacy_audit"
    DATA_SECURITY_AUDIT = "data_security_audit"
    LOG_AUDIT = "log_audit"
    ANNUAL_SUMMARY = "annual_summary"
    QUARTERLY_SUMMARY = "quarterly_summary"
    REGULATORY_INQUIRY = "regulatory_inquiry"
    INCIDENT_REPORT = "incident_report"


class ReportStatus(Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class ComplianceRating(Enum):
    EXCELLENT = "excellent"
    COMPLIANT = "compliant"
    NEEDS_IMPROVEMENT = "needs_improvement"
    NON_COMPLIANT = "non_compliant"


@dataclass
class ReportSection:
    section_id: str
    title: str
    content: str
    subsections: List["ReportSection"] = field(default_factory=list)
    attachments: List[str] = field(default_factory=list)
    tables: List[Dict] = field(default_factory=list)


@dataclass
class ComplianceReport:
    report_id: str
    report_type: ReportType
    title: str
    period_start: datetime
    period_end: datetime
    status: ReportStatus
    rating: ComplianceRating
    overall_score: float
    sections: List[ReportSection]
    findings: List[Dict]
    recommendations: List[str]
    created_at: datetime
    created_by: str
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    version: int = 1


class ReportTemplate:
    def __init__(self, template_name: str, report_type: ReportType):
        self.template_name = template_name
        self.report_type = report_type
        self.sections: List[Dict] = []

    def add_section(
        self,
        title: str,
        content_template: str,
        required_data: List[str] = None,
    ) -> None:
        self.sections.append(
            {
                "title": title,
                "content_template": content_template,
                "required_data": required_data or [],
            }
        )

    def render(self, data: Dict[str, Any]) -> List[ReportSection]:
        rendered_sections = []

        for section_def in self.sections:
            content = section_def["content_template"]
            for key in section_def.get("required_data", []):
                if key in data:
                    placeholder = f"{{{key}}}"
                    content = content.replace(placeholder, str(data[key]))

            rendered_sections.append(
                ReportSection(
                    section_id=f"sec_{uuid.uuid4().hex[:6]}",
                    title=section_def["title"],
                    content=content,
                )
            )

        return rendered_sections


class PrivacyAuditTemplate(ReportTemplate):
    def __init__(self):
        super().__init__("个人信息保护合规审计报告", ReportType.PRIVACY_AUDIT)

        self.add_section(
            "审计概况",
            """本报告依据《个人信息保护法》《个人信息保护合规审计要求》等法规标准，对{company_name}的个人信息处理活动进行合规审计。

审计范围：{audit_scope}
审计期间：{period_start} 至 {period_end}
审计方法：{audit_methods}
审计团队：{audit_team}""",
            ["company_name", "audit_scope", "period_start", "period_end", "audit_methods", "audit_team"],
        )

        self.add_section(
            "合法性基础审查",
            """审查个人信息处理的合法性基础，包括同意、合同履行、法定义务等情形。

审查发现：
{legal_basis_findings}

合规评分：{legal_basis_score}分""",
            ["legal_basis_findings", "legal_basis_score"],
        )

        self.add_section(
            "告知同意审查",
            """审查隐私政策的完整性和告知同意机制的有效性。

审查发现：
{consent_findings}

合规评分：{consent_score}分""",
            ["consent_findings", "consent_score"],
        )

        self.add_section(
            "安全保障措施审查",
            """审查个人信息安全保护措施的实施情况。

审查发现：
{security_findings}

合规评分：{security_score}分""",
            ["security_findings", "security_score"],
        )

        self.add_section(
            "审计结论",
            """总体合规评分：{overall_score}分
合规评级：{compliance_rating}

主要问题：
{main_issues}

整改建议：
{recommendations}""",
            ["overall_score", "compliance_rating", "main_issues", "recommendations"],
        )


class DataSecurityAuditTemplate(ReportTemplate):
    def __init__(self):
        super().__init__("数据安全合规审计报告", ReportType.DATA_SECURITY_AUDIT)

        self.add_section(
            "审计概况",
            """本报告依据《数据安全法》《网络安全法》等法规标准，对{company_name}的数据安全保护情况进行审计。

审计范围：{audit_scope}
审计期间：{period_start} 至 {period_end}""",
            ["company_name", "audit_scope", "period_start", "period_end"],
        )

        self.add_section(
            "数据分类分级",
            """数据分类分级实施情况：

分类覆盖率：{classification_coverage}
分级覆盖率：{grading_coverage}

发现的问题：
{classification_issues}""",
            ["classification_coverage", "grading_coverage", "classification_issues"],
        )

        self.add_section(
            "访问控制",
            """访问控制措施审查：

权限管理评分：{access_control_score}
最小权限原则遵循情况：{least_privilege_status}

发现的问题：
{access_control_issues}""",
            ["access_control_score", "least_privilege_status", "access_control_issues"],
        )

        self.add_section(
            "加密与传输安全",
            """加密措施审查：

存储加密覆盖率：{storage_encryption_coverage}
传输加密覆盖率：{transmission_encryption_coverage}

发现的问题：
{encryption_issues}""",
            ["storage_encryption_coverage", "transmission_encryption_coverage", "encryption_issues"],
        )


class AnnualSummaryTemplate(ReportTemplate):
    def __init__(self):
        super().__init__("年度合规总结报告", ReportType.ANNUAL_SUMMARY)

        self.add_section(
            "年度概况",
            """报告年度：{report_year}
报告期间：{period_start} 至 {period_end}

本年度合规工作概述：
{annual_summary}""",
            ["report_year", "period_start", "period_end", "annual_summary"],
        )

        self.add_section(
            "合规指标统计",
            """年度合规指标：

总审计次数：{total_audits}
平均合规评分：{average_score}
发现问题数：{total_issues}
已整改问题数：{resolved_issues}
整改完成率：{resolution_rate}""",
            ["total_audits", "average_score", "total_issues", "resolved_issues", "resolution_rate"],
        )

        self.add_section(
            "风险事件统计",
            """年度风险事件统计：

风险事件总数：{total_risks}
按等级分布：
{risks_by_level}

按类别分布：
{risks_by_category}""",
            ["total_risks", "risks_by_level", "risks_by_category"],
        )

        self.add_section(
            "法规更新跟踪",
            """本年度跟踪的法规更新：

{regulation_updates}

对业务的影响分析：
{regulation_impact}""",
            ["regulation_updates", "regulation_impact"],
        )

        self.add_section(
            "下年度工作计划",
            """下年度合规工作重点：

{next_year_plan}

资源需求：
{resource_needs}""",
            ["next_year_plan", "resource_needs"],
        )


class ComplianceReportAgent:
    def __init__(self, agent_id: str = "compliance_report_001"):
        self.agent_id = agent_id
        self.templates: Dict[ReportType, ReportTemplate] = {}
        self.reports: List[ComplianceReport] = []
        self.report_counter = 0

        self._initialize_templates()

    def _initialize_templates(self) -> None:
        self.templates[ReportType.PRIVACY_AUDIT] = PrivacyAuditTemplate()
        self.templates[ReportType.DATA_SECURITY_AUDIT] = DataSecurityAuditTemplate()
        self.templates[ReportType.ANNUAL_SUMMARY] = AnnualSummaryTemplate()

    def generate_report(
        self,
        report_type: ReportType,
        title: str,
        period_start: datetime,
        period_end: datetime,
        data: Dict[str, Any],
        findings: List[Dict] = None,
        recommendations: List[str] = None,
    ) -> ComplianceReport:
        self.report_counter += 1
        report_id = f"report_{datetime.utcnow().strftime('%Y%m%d')}_{self.report_counter:04d}"

        template = self.templates.get(report_type)
        if template:
            sections = template.render(data)
        else:
            sections = [
                ReportSection(
                    section_id="sec_001",
                    title="报告内容",
                    content=json.dumps(data, ensure_ascii=False, indent=2),
                )
            ]

        overall_score = data.get("overall_score", 0)
        rating = self._determine_rating(overall_score)

        report = ComplianceReport(
            report_id=report_id,
            report_type=report_type,
            title=title,
            period_start=period_start,
            period_end=period_end,
            status=ReportStatus.DRAFT,
            rating=rating,
            overall_score=overall_score,
            sections=sections,
            findings=findings or [],
            recommendations=recommendations or [],
            created_at=datetime.utcnow(),
            created_by=self.agent_id,
        )

        self.reports.append(report)
        return report

    def _determine_rating(self, score: float) -> ComplianceRating:
        if score >= 90:
            return ComplianceRating.EXCELLENT
        elif score >= 80:
            return ComplianceRating.COMPLIANT
        elif score >= 60:
            return ComplianceRating.NEEDS_IMPROVEMENT
        else:
            return ComplianceRating.NON_COMPLIANT

    def generate_privacy_audit_report(
        self,
        audit_data: Dict[str, Any],
        period_start: datetime,
        period_end: datetime,
    ) -> ComplianceReport:
        findings = []

        if audit_data.get("legal_basis_score", 100) < 80:
            findings.append(
                {
                    "category": "合法性基础",
                    "severity": "high",
                    "description": "部分个人信息处理活动缺乏合法依据",
                    "evidence": audit_data.get("legal_basis_evidence", []),
                }
            )

        if audit_data.get("consent_score", 100) < 80:
            findings.append(
                {
                    "category": "告知同意",
                    "severity": "medium",
                    "description": "同意机制存在不完善之处",
                    "evidence": audit_data.get("consent_evidence", []),
                }
            )

        recommendations = []
        if audit_data.get("legal_basis_score", 100) < 100:
            recommendations.append("完善个人信息处理的合法性基础文档")
        if audit_data.get("consent_score", 100) < 100:
            recommendations.append("优化同意机制，确保用户知情权")
        if audit_data.get("security_score", 100) < 100:
            recommendations.append("加强安全保护措施，提升加密覆盖率")

        return self.generate_report(
            report_type=ReportType.PRIVACY_AUDIT,
            title=f"个人信息保护合规审计报告 ({period_start.strftime('%Y年%m月')})",
            period_start=period_start,
            period_end=period_end,
            data=audit_data,
            findings=findings,
            recommendations=recommendations,
        )

    def generate_data_security_report(
        self,
        audit_data: Dict[str, Any],
        period_start: datetime,
        period_end: datetime,
    ) -> ComplianceReport:
        findings = []

        if audit_data.get("classification_coverage", 1.0) < 0.9:
            findings.append(
                {
                    "category": "数据分类分级",
                    "severity": "high",
                    "description": "数据分类分级覆盖率不足",
                    "evidence": [f"覆盖率: {audit_data.get('classification_coverage', 0):.1%}"],
                }
            )

        if audit_data.get("storage_encryption_coverage", 1.0) < 0.9:
            findings.append(
                {
                    "category": "加密措施",
                    "severity": "high",
                    "description": "敏感数据存储加密覆盖率不足",
                    "evidence": [f"覆盖率: {audit_data.get('storage_encryption_coverage', 0):.1%}"],
                }
            )

        recommendations = []
        if audit_data.get("classification_coverage", 1.0) < 1.0:
            recommendations.append("完善数据分类分级制度，提高覆盖率")
        if audit_data.get("access_control_score", 100) < 100:
            recommendations.append("优化访问控制策略，遵循最小权限原则")
        if audit_data.get("storage_encryption_coverage", 1.0) < 1.0:
            recommendations.append("扩大加密覆盖范围，确保敏感数据加密存储")

        return self.generate_report(
            report_type=ReportType.DATA_SECURITY_AUDIT,
            title=f"数据安全合规审计报告 ({period_start.strftime('%Y年%m月')})",
            period_start=period_start,
            period_end=period_end,
            data=audit_data,
            findings=findings,
            recommendations=recommendations,
        )

    def generate_annual_summary(
        self,
        year: int,
        metrics: Dict[str, Any],
        regulation_updates: List[Dict] = None,
    ) -> ComplianceReport:
        period_start = datetime(year, 1, 1)
        period_end = datetime(year, 12, 31)

        data = {
            "report_year": year,
            "period_start": period_start.strftime("%Y-%m-%d"),
            "period_end": period_end.strftime("%Y-%m-%d"),
            "annual_summary": metrics.get("summary", ""),
            "total_audits": metrics.get("total_audits", 0),
            "average_score": metrics.get("average_score", 0),
            "total_issues": metrics.get("total_issues", 0),
            "resolved_issues": metrics.get("resolved_issues", 0),
            "resolution_rate": f"{metrics.get('resolution_rate', 0):.1%}",
            "total_risks": metrics.get("total_risks", 0),
            "risks_by_level": self._format_risks_by_level(metrics.get("risks_by_level", {})),
            "risks_by_category": self._format_risks_by_category(
                metrics.get("risks_by_category", {})
            ),
            "regulation_updates": self._format_regulation_updates(regulation_updates or []),
            "regulation_impact": metrics.get("regulation_impact", ""),
            "next_year_plan": metrics.get("next_year_plan", ""),
            "resource_needs": metrics.get("resource_needs", ""),
        }

        return self.generate_report(
            report_type=ReportType.ANNUAL_SUMMARY,
            title=f"{year}年度合规工作总结报告",
            period_start=period_start,
            period_end=period_end,
            data=data,
            findings=[],
            recommendations=metrics.get("recommendations", []),
        )

    def _format_risks_by_level(self, risks: Dict[str, int]) -> str:
        lines = []
        for level, count in risks.items():
            lines.append(f"  - {level.upper()}: {count}件")
        return "\n".join(lines) if lines else "  无"

    def _format_risks_by_category(self, risks: Dict[str, int]) -> str:
        lines = []
        for category, count in risks.items():
            lines.append(f"  - {category}: {count}件")
        return "\n".join(lines) if lines else "  无"

    def _format_regulation_updates(self, updates: List[Dict]) -> str:
        if not updates:
            return "  本年度无重大法规更新"

        lines = []
        for update in updates:
            lines.append(f"  - {update.get('title', '未知')} ({update.get('date', '')})")
        return "\n".join(lines)

    def submit_for_review(self, report_id: str) -> Optional[ComplianceReport]:
        report = self.get_report(report_id)
        if report and report.status == ReportStatus.DRAFT:
            report.status = ReportStatus.PENDING_REVIEW
        return report

    def approve_report(
        self, report_id: str, approver: str
    ) -> Optional[ComplianceReport]:
        report = self.get_report(report_id)
        if report and report.status == ReportStatus.PENDING_REVIEW:
            report.status = ReportStatus.APPROVED
            report.approved_by = approver
            report.approved_at = datetime.utcnow()
        return report

    def publish_report(self, report_id: str) -> Optional[ComplianceReport]:
        report = self.get_report(report_id)
        if report and report.status == ReportStatus.APPROVED:
            report.status = ReportStatus.PUBLISHED
        return report

    def get_report(self, report_id: str) -> Optional[ComplianceReport]:
        return next((r for r in self.reports if r.report_id == report_id), None)

    def get_reports_by_type(self, report_type: ReportType) -> List[ComplianceReport]:
        return [r for r in self.reports if r.report_type == report_type]

    def get_reports_by_period(
        self, start: datetime, end: datetime
    ) -> List[ComplianceReport]:
        return [
            r
            for r in self.reports
            if r.period_start >= start and r.period_end <= end
        ]

    def export_report(self, report_id: str, format: str = "json") -> Optional[str]:
        report = self.get_report(report_id)
        if not report:
            return None

        if format == "json":
            return self._export_json(report)
        elif format == "markdown":
            return self._export_markdown(report)
        else:
            return self._export_json(report)

    def _export_json(self, report: ComplianceReport) -> str:
        data = {
            "report_id": report.report_id,
            "report_type": report.report_type.value,
            "title": report.title,
            "period": {
                "start": report.period_start.isoformat(),
                "end": report.period_end.isoformat(),
            },
            "status": report.status.value,
            "rating": report.rating.value,
            "overall_score": report.overall_score,
            "sections": [
                {
                    "section_id": s.section_id,
                    "title": s.title,
                    "content": s.content,
                }
                for s in report.sections
            ],
            "findings": report.findings,
            "recommendations": report.recommendations,
            "created_at": report.created_at.isoformat(),
            "created_by": report.created_by,
            "approved_by": report.approved_by,
            "approved_at": report.approved_at.isoformat() if report.approved_at else None,
        }
        return json.dumps(data, ensure_ascii=False, indent=2)

    def _export_markdown(self, report: ComplianceReport) -> str:
        lines = [
            f"# {report.title}",
            "",
            f"**报告编号**: {report.report_id}",
            f"**报告类型**: {report.report_type.value}",
            f"**审计期间**: {report.period_start.strftime('%Y-%m-%d')} 至 {report.period_end.strftime('%Y-%m-%d')}",
            f"**合规评级**: {report.rating.value}",
            f"**总体评分**: {report.overall_score}分",
            f"**报告状态**: {report.status.value}",
            "",
        ]

        for section in report.sections:
            lines.extend(
                [
                    f"## {section.title}",
                    "",
                    section.content,
                    "",
                ]
            )

        if report.findings:
            lines.extend(["## 审计发现", ""])
            for finding in report.findings:
                lines.extend(
                    [
                        f"### {finding.get('category', '未知')}",
                        f"- **严重程度**: {finding.get('severity', '未知')}",
                        f"- **描述**: {finding.get('description', '')}",
                        "",
                    ]
                )

        if report.recommendations:
            lines.extend(["## 整改建议", ""])
            for i, rec in enumerate(report.recommendations, 1):
                lines.append(f"{i}. {rec}")
            lines.append("")

        lines.extend(
            [
                "---",
                f"*报告生成时间: {report.created_at.strftime('%Y-%m-%d %H:%M:%S')}*",
                f"*报告生成者: {report.created_by}*",
            ]
        )

        return "\n".join(lines)

    def compare_reports(
        self, report_id1: str, report_id2: str
    ) -> Optional[Dict[str, Any]]:
        report1 = self.get_report(report_id1)
        report2 = self.get_report(report_id2)

        if not report1 or not report2:
            return None

        return {
            "report1": {
                "id": report1.report_id,
                "period": f"{report1.period_start.strftime('%Y-%m-%d')} - {report1.period_end.strftime('%Y-%m-%d')}",
                "score": report1.overall_score,
                "rating": report1.rating.value,
            },
            "report2": {
                "id": report2.report_id,
                "period": f"{report2.period_start.strftime('%Y-%m-%d')} - {report2.period_end.strftime('%Y-%m-%d')}",
                "score": report2.overall_score,
                "rating": report2.rating.value,
            },
            "comparison": {
                "score_change": report2.overall_score - report1.overall_score,
                "rating_change": f"{report1.rating.value} -> {report2.rating.value}",
                "findings_change": len(report2.findings) - len(report1.findings),
            },
        }
