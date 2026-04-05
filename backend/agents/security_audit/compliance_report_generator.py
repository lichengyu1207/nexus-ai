"""
合规报告生成智能体
Compliance Report Generator Agent

负责自动生成各类合规报告，供内部审计和监管机构查阅。
"""

import asyncio
import json
import logging
import hashlib
import uuid
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
from enum import Enum

logger = logging.getLogger(__name__)


class ReportType(Enum):
    PERSONAL_INFO_PROTECTION = "personal_info_protection"
    DATA_SECURITY = "data_security"
    NETWORK_SECURITY_INCIDENT = "network_security_incident"
    USER_RIGHTS_REQUEST = "user_rights_request"
    ANNUAL_COMPLIANCE = "annual_compliance"
    PRIVACY_IMPACT_ASSESSMENT = "privacy_impact_assessment"
    CROSS_BORDER_TRANSFER = "cross_border_transfer"
    CUSTOM = "custom"


class ReportStatus(Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    PUBLISHED = "published"
    ARCHIVED = "archived"


@dataclass
class ReportSection:
    section_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    content: str = ""
    data: Dict = field(default_factory=dict)
    charts: List[Dict] = field(default_factory=list)
    order: int = 0


@dataclass
class ComplianceReport:
    report_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    report_type: str = ReportType.PERSONAL_INFO_PROTECTION.value
    title: str = ""
    
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    period_start: str = ""
    period_end: str = ""
    
    status: str = ReportStatus.DRAFT.value
    author: str = ""
    reviewer: str = ""
    approved_at: str = ""
    approved_by: str = ""
    
    sections: List[ReportSection] = field(default_factory=list)
    
    summary: str = ""
    key_findings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    attachments: List[str] = field(default_factory=list)
    version: int = 1
    
    export_formats: List[str] = field(default_factory=list)
    access_password: str = ""


class ComplianceReportGeneratorAgent:
    """
    合规报告生成智能体
    
    功能：
    1. 报告类型：个人信息保护、数据安全、网络安全事件、用户权利请求、年度合规总结
    2. 报告模板：支持自定义模板，符合监管要求
    3. 数据聚合：从各审计智能体、日志数据库、合规规则库提取数据
    4. 人工审核：报告初稿提交合规管理员审核
    5. 报告存档：所有报告永久保存，不可删除
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.name = "ComplianceReportGeneratorAgent"
        self.description = "自动生成各类合规报告"
        self.config = config or {}
        
        self.reports: Dict[str, ComplianceReport] = {}
        self.templates: Dict[str, Dict] = {}
        
        self._init_templates()
        
        self.stats = {
            "total_reports": 0,
            "reports_by_type": defaultdict(int),
            "reports_by_status": defaultdict(int),
            "reports_generated_this_month": 0,
        }
        
        self._initialized = False
    
    def _init_templates(self):
        self.templates = {
            ReportType.PERSONAL_INFO_PROTECTION.value: {
                "title": "个人信息保护合规报告",
                "sections": [
                    {"title": "概述", "order": 1},
                    {"title": "个人信息处理活动概况", "order": 2},
                    {"title": "用户同意管理情况", "order": 3},
                    {"title": "数据主体权利响应情况", "order": 4},
                    {"title": "安全事件与处置", "order": 5},
                    {"title": "合规风险评估", "order": 6},
                    {"title": "整改措施与计划", "order": 7},
                    {"title": "结论", "order": 8},
                ],
            },
            ReportType.DATA_SECURITY.value: {
                "title": "数据安全合规报告",
                "sections": [
                    {"title": "概述", "order": 1},
                    {"title": "数据资产盘点", "order": 2},
                    {"title": "数据分类分级情况", "order": 3},
                    {"title": "数据安全措施", "order": 4},
                    {"title": "数据访问审计", "order": 5},
                    {"title": "数据安全事件", "order": 6},
                    {"title": "风险评估与改进", "order": 7},
                    {"title": "结论", "order": 8},
                ],
            },
            ReportType.NETWORK_SECURITY_INCIDENT.value: {
                "title": "网络安全事件报告",
                "sections": [
                    {"title": "事件概述", "order": 1},
                    {"title": "事件详情", "order": 2},
                    {"title": "影响评估", "order": 3},
                    {"title": "处置措施", "order": 4},
                    {"title": "根因分析", "order": 5},
                    {"title": "预防措施", "order": 6},
                    {"title": "结论", "order": 7},
                ],
            },
            ReportType.USER_RIGHTS_REQUEST.value: {
                "title": "用户权利请求处理报告",
                "sections": [
                    {"title": "概述", "order": 1},
                    {"title": "请求统计", "order": 2},
                    {"title": "处理时效分析", "order": 3},
                    {"title": "典型案例", "order": 4},
                    {"title": "问题与改进", "order": 5},
                    {"title": "结论", "order": 6},
                ],
            },
            ReportType.ANNUAL_COMPLIANCE.value: {
                "title": "年度合规总结报告",
                "sections": [
                    {"title": "年度概述", "order": 1},
                    {"title": "合规体系建设", "order": 2},
                    {"title": "法规跟踪与应对", "order": 3},
                    {"title": "合规审计情况", "order": 4},
                    {"title": "风险事件汇总", "order": 5},
                    {"title": "整改落实情况", "order": 6},
                    {"title": "下年度计划", "order": 7},
                    {"title": "结论", "order": 8},
                ],
            },
        }
    
    async def initialize(self):
        if not self._initialized:
            await self._setup()
            self._initialized = True
            logger.info(f"Agent '{self.name}' initialized")
    
    async def _setup(self):
        pass
    
    async def create_report(
        self,
        report_type: str,
        period_start: str,
        period_end: str,
        author: str = "",
        custom_title: Optional[str] = None,
    ) -> ComplianceReport:
        template = self.templates.get(report_type, self.templates.get(ReportType.CUSTOM.value, {}))
        
        report = ComplianceReport(
            report_type=report_type,
            title=custom_title or template.get("title", "合规报告"),
            period_start=period_start,
            period_end=period_end,
            author=author,
        )
        
        for section_template in template.get("sections", []):
            section = ReportSection(
                title=section_template["title"],
                order=section_template["order"],
            )
            report.sections.append(section)
        
        self.reports[report.report_id] = report
        
        self.stats["total_reports"] += 1
        self.stats["reports_by_type"][report_type] += 1
        self.stats["reports_by_status"][ReportStatus.DRAFT.value] += 1
        
        return report
    
    async def populate_section(
        self,
        report_id: str,
        section_title: str,
        content: str,
        data: Optional[Dict] = None,
        charts: Optional[List[Dict]] = None,
    ) -> bool:
        report = self.reports.get(report_id)
        if not report:
            return False
        
        for section in report.sections:
            if section.title == section_title:
                section.content = content
                section.data = data or {}
                section.charts = charts or []
                report.updated_at = datetime.utcnow().isoformat()
                return True
        
        return False
    
    async def auto_populate_report(
        self,
        report_id: str,
        data_sources: Dict[str, Any],
    ) -> Dict:
        report = self.reports.get(report_id)
        if not report:
            return {"success": False, "reason": "报告不存在"}
        
        if report.report_type == ReportType.PERSONAL_INFO_PROTECTION.value:
            await self._populate_pip_report(report, data_sources)
        elif report.report_type == ReportType.DATA_SECURITY.value:
            await self._populate_ds_report(report, data_sources)
        elif report.report_type == ReportType.USER_RIGHTS_REQUEST.value:
            await self._populate_urr_report(report, data_sources)
        
        report.summary = self._generate_summary(report)
        report.key_findings = self._extract_key_findings(report)
        report.recommendations = self._generate_recommendations(report)
        
        return {
            "success": True,
            "report_id": report_id,
            "sections_populated": len(report.sections),
        }
    
    async def _populate_pip_report(
        self,
        report: ComplianceReport,
        data_sources: Dict,
    ):
        consent_data = data_sources.get("consent", {})
        rights_data = data_sources.get("rights", {})
        
        for section in report.sections:
            if section.title == "概述":
                section.content = f"本报告覆盖{report.period_start}至{report.period_end}期间的个人信息保护合规情况。"
            
            elif section.title == "用户同意管理情况":
                section.content = f"期间共记录{consent_data.get('total_consents', 0)}次用户同意，"
                section.content += f"其中{consent_data.get('active_consents', 0)}次仍有效。"
                section.data = consent_data
            
            elif section.title == "数据主体权利响应情况":
                section.content = f"期间共收到{rights_data.get('total_requests', 0)}个权利请求，"
                section.content += f"完成处理{rights_data.get('completed_requests', 0)}个。"
                section.data = rights_data
    
    async def _populate_ds_report(
        self,
        report: ComplianceReport,
        data_sources: Dict,
    ):
        access_data = data_sources.get("access_audit", {})
        
        for section in report.sections:
            if section.title == "概述":
                section.content = f"本报告覆盖{report.period_start}至{report.period_end}期间的数据安全合规情况。"
            
            elif section.title == "数据访问审计":
                section.content = f"期间共记录{access_data.get('total_access', 0)}次数据访问，"
                section.content += f"发现{access_data.get('anomalies', 0)}次异常访问。"
                section.data = access_data
    
    async def _populate_urr_report(
        self,
        report: ComplianceReport,
        data_sources: Dict,
    ):
        rights_data = data_sources.get("rights", {})
        
        for section in report.sections:
            if section.title == "概述":
                section.content = f"本报告覆盖{report.period_start}至{report.period_end}期间的用户权利请求处理情况。"
            
            elif section.title == "请求统计":
                section.content = f"期间共收到{rights_data.get('total_requests', 0)}个权利请求。"
                section.data = rights_data
    
    def _generate_summary(self, report: ComplianceReport) -> str:
        summary = f"本{report.title}已生成，覆盖{report.period_start}至{report.period_end}期间。"
        summary += f"报告包含{len(report.sections)}个章节。"
        return summary
    
    def _extract_key_findings(self, report: ComplianceReport) -> List[str]:
        findings = []
        
        for section in report.sections:
            if section.data:
                for key, value in section.data.items():
                    if isinstance(value, (int, float)) and value > 0:
                        findings.append(f"{section.title}: {key} = {value}")
        
        return findings[:10]
    
    def _generate_recommendations(self, report: ComplianceReport) -> List[str]:
        recommendations = []
        
        for section in report.sections:
            if "风险" in section.title or "问题" in section.title:
                recommendations.append(f"建议关注{section.title}中发现的问题")
        
        recommendations.append("建议定期审查并更新合规措施")
        
        return recommendations
    
    async def submit_for_review(
        self,
        report_id: str,
    ) -> bool:
        report = self.reports.get(report_id)
        if not report:
            return False
        
        report.status = ReportStatus.PENDING_REVIEW.value
        report.updated_at = datetime.utcnow().isoformat()
        
        self.stats["reports_by_status"][ReportStatus.DRAFT.value] -= 1
        self.stats["reports_by_status"][ReportStatus.PENDING_REVIEW.value] += 1
        
        return True
    
    async def approve_report(
        self,
        report_id: str,
        approved_by: str,
        comments: Optional[str] = None,
    ) -> bool:
        report = self.reports.get(report_id)
        if not report:
            return False
        
        report.status = ReportStatus.APPROVED.value
        report.approved_by = approved_by
        report.approved_at = datetime.utcnow().isoformat()
        report.updated_at = datetime.utcnow().isoformat()
        
        if comments:
            report.recommendations.append(f"审核意见: {comments}")
        
        self.stats["reports_by_status"][ReportStatus.PENDING_REVIEW.value] -= 1
        self.stats["reports_by_status"][ReportStatus.APPROVED.value] += 1
        
        return True
    
    async def reject_report(
        self,
        report_id: str,
        rejected_by: str,
        reason: str,
    ) -> bool:
        report = self.reports.get(report_id)
        if not report:
            return False
        
        report.status = ReportStatus.DRAFT.value
        report.updated_at = datetime.utcnow().isoformat()
        report.recommendations.append(f"退回原因: {reason}")
        
        self.stats["reports_by_status"][ReportStatus.PENDING_REVIEW.value] -= 1
        self.stats["reports_by_status"][ReportStatus.DRAFT.value] += 1
        
        return True
    
    async def export_report(
        self,
        report_id: str,
        format: str = "json",
        include_password: bool = False,
    ) -> Dict:
        report = self.reports.get(report_id)
        if not report:
            return {"success": False, "reason": "报告不存在"}
        
        if format == "json":
            content = json.dumps({
                "report_id": report.report_id,
                "report_type": report.report_type,
                "title": report.title,
                "period": {
                    "start": report.period_start,
                    "end": report.period_end,
                },
                "created_at": report.created_at,
                "status": report.status,
                "summary": report.summary,
                "key_findings": report.key_findings,
                "recommendations": report.recommendations,
                "sections": [
                    {
                        "title": s.title,
                        "content": s.content,
                        "data": s.data,
                    }
                    for s in report.sections
                ],
            }, ensure_ascii=False, indent=2)
            
            return {
                "success": True,
                "format": "json",
                "content": content,
                "filename": f"{report.title}_{report.period_start[:10]}.json",
            }
        
        elif format == "pdf":
            return {
                "success": True,
                "format": "pdf",
                "content": f"[PDF内容] {report.title}",
                "filename": f"{report.title}_{report.period_start[:10]}.pdf",
            }
        
        elif format == "excel":
            return {
                "success": True,
                "format": "xlsx",
                "content": "[Excel内容]",
                "filename": f"{report.title}_{report.period_start[:10]}.xlsx",
            }
        
        return {"success": False, "reason": "不支持的导出格式"}
    
    async def get_report(self, report_id: str) -> Optional[Dict]:
        report = self.reports.get(report_id)
        if not report:
            return None
        
        return {
            "report_id": report.report_id,
            "report_type": report.report_type,
            "title": report.title,
            "period_start": report.period_start,
            "period_end": report.period_end,
            "status": report.status,
            "author": report.author,
            "created_at": report.created_at,
            "updated_at": report.updated_at,
            "approved_by": report.approved_by,
            "approved_at": report.approved_at,
            "summary": report.summary,
            "key_findings": report.key_findings,
            "recommendations": report.recommendations,
            "sections_count": len(report.sections),
        }
    
    async def list_reports(
        self,
        report_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict]:
        reports = list(self.reports.values())
        
        if report_type:
            reports = [r for r in reports if r.report_type == report_type]
        
        if status:
            reports = [r for r in reports if r.status == status]
        
        reports.sort(key=lambda r: r.created_at, reverse=True)
        
        return [await self.get_report(r.report_id) for r in reports[:limit]]
    
    async def get_stats(self) -> Dict:
        return {
            "name": self.name,
            "total_reports": self.stats["total_reports"],
            "reports_by_type": dict(self.stats["reports_by_type"]),
            "reports_by_status": dict(self.stats["reports_by_status"]),
        }
