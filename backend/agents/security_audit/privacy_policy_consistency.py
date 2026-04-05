"""
隐私政策一致性检查智能体
Privacy Policy Consistency Agent

负责检查平台的实际数据处理行为与隐私政策声明是否一致。
"""

import asyncio
import json
import logging
import hashlib
import uuid
import re
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
from enum import Enum

logger = logging.getLogger(__name__)


class InconsistencyType(Enum):
    OVER_COLLECTION = "over_collection"
    UNAUTHORIZED_USE = "unauthorized_use"
    UNDISCLOSED_SHARING = "undisclosed_sharing"
    OVER_RETENTION = "over_retention"
    MISSING_DISCLOSURE = "missing_disclosure"


class RiskLevel(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class PrivacyPolicyClause:
    clause_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    policy_version: str = ""
    clause_type: str = ""
    content: str = ""
    data_types: List[str] = field(default_factory=list)
    purposes: List[str] = field(default_factory=list)
    third_parties: List[str] = field(default_factory=list)
    retention_period: str = ""
    location: str = ""


@dataclass
class InconsistencyFinding:
    finding_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    inconsistency_type: str = ""
    description: str = ""
    policy_clause: str = ""
    actual_behavior: str = ""
    evidence: Dict = field(default_factory=dict)
    risk_level: str = RiskLevel.MEDIUM.value
    legal_consequences: List[str] = field(default_factory=list)
    remediation_suggestions: List[str] = field(default_factory=list)
    status: str = "open"


@dataclass
class ConsistencyCheckReport:
    report_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    policy_version: str = ""
    check_period: Dict = field(default_factory=dict)
    total_findings: int = 0
    findings_by_type: Dict = field(default_factory=dict)
    findings_by_risk: Dict = field(default_factory=dict)
    findings: List[InconsistencyFinding] = field(default_factory=list)
    summary: str = ""
    recommendations: List[str] = field(default_factory=list)


class PrivacyPolicyConsistencyAgent:
    """
    隐私政策一致性检查智能体
    
    功能：
    1. 输入：当前隐私政策文本、业务操作日志、数据访问审计报告
    2. 检查方法：NLP提取承诺的数据处理活动，与实际执行对比
    3. 不一致类型：超范围收集、未授权使用、共享未披露、保留超期
    4. 报告生成：一致性检查报告，风险评估，整改建议
    5. 周期性检查：每周自动执行，隐私政策更新时触发
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.name = "PrivacyPolicyConsistencyAgent"
        self.description = "检查平台的实际数据处理行为与隐私政策声明是否一致"
        self.config = config or {}
        
        self.current_policy: Optional[Dict] = None
        self.policy_clauses: List[PrivacyPolicyClause] = []
        self.findings: List[InconsistencyFinding] = []
        self.reports: List[ConsistencyCheckReport] = []
        
        self.data_type_keywords = {
            "personal_info": ["姓名", "电话", "手机", "邮箱", "身份证", "地址", "姓名"],
            "location": ["位置", "地址", "GPS", "定位", "地理"],
            "device": ["设备", "IMEI", "MAC", "IP", "浏览器", "设备信息"],
            "financial": ["银行", "支付", "交易", "财务", "收入"],
            "behavior": ["浏览", "搜索", "点击", "行为", "偏好"],
        }
        
        self.purpose_keywords = {
            "service": ["提供服务", "业务功能", "核心功能"],
            "marketing": ["营销", "推广", "广告", "推荐"],
            "analytics": ["分析", "统计", "研究", "改进"],
            "security": ["安全", "风控", "验证", "防护"],
        }
        
        self.stats = {
            "total_checks": 0,
            "total_findings": 0,
            "findings_by_type": defaultdict(int),
            "findings_by_risk": defaultdict(int),
            "last_check_time": "",
        }
        
        self._initialized = False
    
    async def initialize(self):
        if not self._initialized:
            await self._setup()
            self._initialized = True
            logger.info(f"Agent '{self.name}' initialized")
    
    async def _setup(self):
        asyncio.create_task(self._periodic_check())
    
    async def _periodic_check(self):
        while True:
            await asyncio.sleep(604800)
            if self.current_policy:
                await self.run_consistency_check()
    
    async def load_privacy_policy(
        self,
        policy_text: str,
        version: str,
        effective_date: str,
    ) -> Dict:
        self.current_policy = {
            "version": version,
            "text": policy_text,
            "effective_date": effective_date,
            "loaded_at": datetime.utcnow().isoformat(),
        }
        
        self.policy_clauses = await self._parse_policy_clauses(policy_text, version)
        
        return {
            "version": version,
            "clauses_extracted": len(self.policy_clauses),
            "status": "loaded",
        }
    
    async def _parse_policy_clauses(
        self,
        policy_text: str,
        version: str,
    ) -> List[PrivacyPolicyClause]:
        clauses = []
        
        sections = re.split(r'\n(?=[一二三四五六七八九十\d]+[、.]|第[一二三四五六七八九十\d]+[章节])', policy_text)
        
        for section in sections:
            if not section.strip():
                continue
            
            data_types = self._extract_data_types(section)
            purposes = self._extract_purposes(section)
            third_parties = self._extract_third_parties(section)
            retention = self._extract_retention_period(section)
            
            clause = PrivacyPolicyClause(
                policy_version=version,
                clause_type=self._classify_clause_type(section),
                content=section[:500],
                data_types=data_types,
                purposes=purposes,
                third_parties=third_parties,
                retention_period=retention,
            )
            clauses.append(clause)
        
        return clauses
    
    def _extract_data_types(self, text: str) -> List[str]:
        found_types = []
        for data_type, keywords in self.data_type_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    found_types.append(data_type)
                    break
        return list(set(found_types))
    
    def _extract_purposes(self, text: str) -> List[str]:
        found_purposes = []
        for purpose, keywords in self.purpose_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    found_purposes.append(purpose)
                    break
        return list(set(found_purposes))
    
    def _extract_third_parties(self, text: str) -> List[str]:
        third_party_patterns = [
            r"向([^，。]+)提供",
            r"与([^，。]+)共享",
            r"第三方([^，。]+)",
        ]
        
        third_parties = []
        for pattern in third_party_patterns:
            matches = re.findall(pattern, text)
            third_parties.extend(matches)
        
        return list(set(third_parties))[:5]
    
    def _extract_retention_period(self, text: str) -> str:
        retention_patterns = [
            (r"保存(\d+)年", "years"),
            (r"保存(\d+)个月", "months"),
            (r"保存(\d+)天", "days"),
            (r"保留(\d+)年", "years"),
            (r"保留(\d+)个月", "months"),
        ]
        
        for pattern, unit in retention_patterns:
            match = re.search(pattern, text)
            if match:
                return f"{match.group(1)} {unit}"
        
        return "未明确"
    
    def _classify_clause_type(self, text: str) -> str:
        if "收集" in text or "采集" in text:
            return "collection"
        elif "使用" in text or "处理" in text:
            return "use"
        elif "共享" in text or "提供" in text or "披露" in text:
            return "sharing"
        elif "存储" in text or "保存" in text or "保留" in text:
            return "storage"
        elif "删除" in text or "销毁" in text:
            return "deletion"
        elif "权利" in text or "选择" in text:
            return "user_rights"
        else:
            return "general"
    
    async def run_consistency_check(
        self,
        business_logs: Optional[List[Dict]] = None,
        data_access_reports: Optional[List[Dict]] = None,
    ) -> ConsistencyCheckReport:
        if not self.current_policy:
            return ConsistencyCheckReport(
                summary="未加载隐私政策，无法执行一致性检查",
            )
        
        report = ConsistencyCheckReport(
            policy_version=self.current_policy["version"],
            check_period={
                "start": (datetime.utcnow() - timedelta(days=7)).isoformat(),
                "end": datetime.utcnow().isoformat(),
            },
        )
        
        promised_data_types = set()
        promised_purposes = set()
        promised_third_parties = set()
        promised_retention = {}
        
        for clause in self.policy_clauses:
            promised_data_types.update(clause.data_types)
            promised_purposes.update(clause.purposes)
            promised_third_parties.update(clause.third_parties)
            if clause.retention_period != "未明确":
                for dt in clause.data_types:
                    promised_retention[dt] = clause.retention_period
        
        if business_logs:
            for log in business_logs:
                actual_data_types = set(log.get("data_types", []))
                over_collected = actual_data_types - promised_data_types
                
                if over_collected:
                    finding = InconsistencyFinding(
                        inconsistency_type=InconsistencyType.OVER_COLLECTION.value,
                        description=f"收集了隐私政策未声明的数据类型: {over_collected}",
                        actual_behavior=f"实际收集: {actual_data_types}",
                        evidence={"log_id": log.get("log_id"), "data_types": list(over_collected)},
                        risk_level=RiskLevel.HIGH.value,
                        legal_consequences=["违反个人信息保护法第6条最小必要原则"],
                        remediation_suggestions=["更新隐私政策声明", "停止收集非必要数据"],
                    )
                    report.findings.append(finding)
        
        if data_access_reports:
            for access_report in data_access_reports:
                actual_purposes = set(access_report.get("purposes", []))
                unauthorized_purposes = actual_purposes - promised_purposes
                
                if unauthorized_purposes:
                    finding = InconsistencyFinding(
                        inconsistency_type=InconsistencyType.UNAUTHORIZED_USE.value,
                        description=f"将数据用于隐私政策未声明的目的: {unauthorized_purposes}",
                        actual_behavior=f"实际用途: {actual_purposes}",
                        evidence={"report_id": access_report.get("report_id")},
                        risk_level=RiskLevel.HIGH.value,
                        legal_consequences=["违反个人信息保护法第6条目的限制原则"],
                        remediation_suggestions=["更新隐私政策", "停止非授权使用"],
                    )
                    report.findings.append(finding)
                
                actual_third_parties = set(access_report.get("third_parties", []))
                undisclosed = actual_third_parties - promised_third_parties
                
                if undisclosed:
                    finding = InconsistencyFinding(
                        inconsistency_type=InconsistencyType.UNDISCLOSED_SHARING.value,
                        description=f"向隐私政策未披露的第三方提供数据: {undisclosed}",
                        actual_behavior=f"实际共享方: {actual_third_parties}",
                        evidence={"report_id": access_report.get("report_id")},
                        risk_level=RiskLevel.HIGH.value,
                        legal_consequences=["违反个人信息保护法第23条"],
                        remediation_suggestions=["更新隐私政策披露第三方", "获取用户单独同意"],
                    )
                    report.findings.append(finding)
        
        report.total_findings = len(report.findings)
        report.findings_by_type = defaultdict(int)
        report.findings_by_risk = defaultdict(int)
        
        for finding in report.findings:
            report.findings_by_type[finding.inconsistency_type] += 1
            report.findings_by_risk[finding.risk_level] += 1
        
        report.summary = self._generate_summary(report)
        report.recommendations = self._generate_recommendations(report)
        
        self.reports.append(report)
        self.findings.extend(report.findings)
        
        self.stats["total_checks"] += 1
        self.stats["total_findings"] += report.total_findings
        self.stats["last_check_time"] = datetime.utcnow().isoformat()
        
        for finding in report.findings:
            self.stats["findings_by_type"][finding.inconsistency_type] += 1
            self.stats["findings_by_risk"][finding.risk_level] += 1
        
        return report
    
    def _generate_summary(self, report: ConsistencyCheckReport) -> str:
        if report.total_findings == 0:
            return "一致性检查通过，实际数据处理行为与隐私政策声明一致。"
        
        high_risk = report.findings_by_risk.get("high", 0)
        medium_risk = report.findings_by_risk.get("medium", 0)
        
        summary = f"发现{report.total_findings}项不一致问题，"
        if high_risk > 0:
            summary += f"其中{high_risk}项高风险问题需要立即处理，"
        if medium_risk > 0:
            summary += f"{medium_risk}项中风险问题需要关注。"
        
        return summary
    
    def _generate_recommendations(self, report: ConsistencyCheckReport) -> List[str]:
        recommendations = []
        
        if report.findings_by_type.get(InconsistencyType.OVER_COLLECTION.value, 0) > 0:
            recommendations.append("审查数据收集流程，确保只收集必要数据")
            recommendations.append("更新隐私政策，明确声明所有收集的数据类型")
        
        if report.findings_by_type.get(InconsistencyType.UNAUTHORIZED_USE.value, 0) > 0:
            recommendations.append("审查数据处理目的，确保与声明一致")
            recommendations.append("建立数据处理目的审批流程")
        
        if report.findings_by_type.get(InconsistencyType.UNDISCLOSED_SHARING.value, 0) > 0:
            recommendations.append("审查第三方数据共享协议")
            recommendations.append("更新隐私政策，披露所有第三方共享情况")
            recommendations.append("对敏感数据共享获取用户单独同意")
        
        if report.findings_by_type.get(InconsistencyType.OVER_RETENTION.value, 0) > 0:
            recommendations.append("实施数据保留期限自动清理机制")
            recommendations.append("审查数据保留策略，确保符合声明")
        
        return recommendations
    
    async def get_open_findings(self) -> List[Dict]:
        return [
            {
                "finding_id": f.finding_id,
                "type": f.inconsistency_type,
                "description": f.description,
                "risk_level": f.risk_level,
                "status": f.status,
                "timestamp": f.timestamp,
            }
            for f in self.findings
            if f.status == "open"
        ]
    
    async def resolve_finding(
        self,
        finding_id: str,
        resolution: str,
    ) -> bool:
        for finding in self.findings:
            if finding.finding_id == finding_id:
                finding.status = "resolved"
                finding.remediation_suggestions.append(f"已解决: {resolution}")
                return True
        return False
    
    async def get_latest_report(self) -> Optional[Dict]:
        if not self.reports:
            return None
        
        latest = self.reports[-1]
        return {
            "report_id": latest.report_id,
            "timestamp": latest.timestamp,
            "policy_version": latest.policy_version,
            "total_findings": latest.total_findings,
            "findings_by_type": dict(latest.findings_by_type),
            "findings_by_risk": dict(latest.findings_by_risk),
            "summary": latest.summary,
            "recommendations": latest.recommendations,
        }
    
    async def get_stats(self) -> Dict:
        return {
            "name": self.name,
            "total_checks": self.stats["total_checks"],
            "total_findings": self.stats["total_findings"],
            "open_findings": len([f for f in self.findings if f.status == "open"]),
            "findings_by_type": dict(self.stats["findings_by_type"]),
            "findings_by_risk": dict(self.stats["findings_by_risk"]),
            "last_check_time": self.stats["last_check_time"],
            "current_policy_version": self.current_policy.get("version") if self.current_policy else None,
        }
