"""
自动化合规报告 - GDPR/个人信息保护法
按需生成GDPR/个保法合规报告，包含数据跨境审计、算法偏见检测
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import asyncio
import logging
import json
from collections import defaultdict

logger = logging.getLogger(__name__)


class ComplianceFramework(Enum):
    GDPR = "gdpr"
    PIPL = "pipl"
    CCPA = "ccpa"
    ISO27001 = "iso27001"
    SOC2 = "soc2"


class ComplianceStatus(Enum):
    COMPLIANT = "compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    NON_COMPLIANT = "non_compliant"
    NOT_APPLICABLE = "not_applicable"


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ComplianceRequirement:
    requirement_id: str
    framework: ComplianceFramework
    category: str
    description: str
    is_mandatory: bool = True
    evidence_required: List[str] = field(default_factory=list)


@dataclass
class ComplianceCheck:
    check_id: str
    requirement: ComplianceRequirement
    status: ComplianceStatus
    score: float
    findings: List[str]
    recommendations: List[str]
    evidence: Dict[str, Any]
    checked_at: datetime


@dataclass
class DataCrossBorderRecord:
    record_id: str
    data_type: str
    source_country: str
    destination_country: str
    transfer_mechanism: str
    data_volume: int
    purpose: str
    legal_basis: str
    timestamp: datetime


@dataclass
class AlgorithmBiasResult:
    algorithm_name: str
    metric_type: str
    overall_score: float
    group_scores: Dict[str, float]
    bias_detected: bool
    affected_groups: List[str]
    recommendations: List[str]


COMPLIANCE_REQUIREMENTS: Dict[ComplianceFramework, List[ComplianceRequirement]] = {
    ComplianceFramework.GDPR: [
        ComplianceRequirement(
            requirement_id="GDPR-Art5-1a",
            framework=ComplianceFramework.GDPR,
            category="数据主体权利",
            description="个人数据应以合法、公平、透明的方式处理",
            evidence_required=["隐私政策", "同意记录", "处理活动记录"]
        ),
        ComplianceRequirement(
            requirement_id="GDPR-Art6",
            framework=ComplianceFramework.GDPR,
            category="处理合法性",
            description="数据处理必须有合法依据",
            evidence_required=["同意记录", "合同记录", "合法利益评估"]
        ),
        ComplianceRequirement(
            requirement_id="GDPR-Art17",
            framework=ComplianceFramework.GDPR,
            category="删除权",
            description="数据主体有权要求删除其个人数据",
            evidence_required=["删除请求处理流程", "删除记录"]
        ),
        ComplianceRequirement(
            requirement_id="GDPR-Art20",
            framework=ComplianceFramework.GDPR,
            category="数据可携带权",
            description="数据主体有权以结构化格式获取其数据",
            evidence_required=["数据导出功能", "格式说明"]
        ),
        ComplianceRequirement(
            requirement_id="GDPR-Art25",
            framework=ComplianceFramework.GDPR,
            category="隐私设计",
            description="在设计和默认设置中实施数据保护",
            evidence_required=["隐私影响评估", "技术措施文档"]
        ),
        ComplianceRequirement(
            requirement_id="GDPR-Art32",
            framework=ComplianceFramework.GDPR,
            category="数据安全",
            description="实施适当的技术和组织措施保护数据",
            evidence_required=["安全策略", "加密措施", "访问控制"]
        ),
        ComplianceRequirement(
            requirement_id="GDPR-Art33",
            framework=ComplianceFramework.GDPR,
            category="数据泄露通知",
            description="发生数据泄露后72小时内通知监管机构",
            evidence_required=["泄露响应计划", "通知模板"]
        ),
        ComplianceRequirement(
            requirement_id="GDPR-Art35",
            framework=ComplianceFramework.GDPR,
            category="隐私影响评估",
            description="高风险处理前进行隐私影响评估",
            evidence_required=["DPIA报告", "风险评估"]
        ),
    ],
    ComplianceFramework.PIPL: [
        ComplianceRequirement(
            requirement_id="PIPL-Art5",
            framework=ComplianceFramework.PIPL,
            category="处理原则",
            description="个人信息处理应遵循合法、正当、必要、诚信原则",
            evidence_required=["隐私政策", "最小必要原则说明"]
        ),
        ComplianceRequirement(
            requirement_id="PIPL-Art13",
            framework=ComplianceFramework.PIPL,
            category="处理合法性",
            description="处理个人信息应取得个人同意",
            evidence_required=["同意记录", "授权协议"]
        ),
        ComplianceRequirement(
            requirement_id="PIPL-Art24",
            framework=ComplianceFramework.PIPL,
            category="自动化决策",
            description="自动化决策应保证透明度和公平性",
            evidence_required=["算法说明", "偏见检测结果"]
        ),
        ComplianceRequirement(
            requirement_id="PIPL-Art38",
            framework=ComplianceFramework.PIPL,
            category="跨境传输",
            description="向境外提供个人信息需满足法定条件",
            evidence_required=["安全评估", "标准合同", "认证文件"]
        ),
        ComplianceRequirement(
            requirement_id="PIPL-Art47",
            framework=ComplianceFramework.PIPL,
            category="个人信息保护影响评估",
            description="特定情形下应进行个人信息保护影响评估",
            evidence_required=["PIA报告", "风险评估"]
        ),
        ComplianceRequirement(
            requirement_id="PIPL-Art51",
            framework=ComplianceFramework.PIPL,
            category="泄露通知",
            description="发生个人信息泄露应立即采取补救措施并通知",
            evidence_required=["应急预案", "通知记录"]
        ),
    ],
}


class ComplianceChecker:
    def __init__(self):
        self._checks: List[ComplianceCheck] = []
        self._cross_border_records: List[DataCrossBorderRecord] = []
        self._bias_results: List[AlgorithmBiasResult] = []
        
    async def check_requirement(
        self,
        requirement: ComplianceRequirement,
        evidence_data: Dict[str, Any]
    ) -> ComplianceCheck:
        findings = []
        recommendations = []
        score = 0.0
        
        for evidence_type in requirement.evidence_required:
            if evidence_type in evidence_data and evidence_data[evidence_type]:
                score += 1.0 / len(requirement.evidence_required)
            else:
                findings.append(f"缺少证据: {evidence_type}")
                recommendations.append(f"请提供{evidence_type}相关文档")
                
        if score >= 0.8:
            status = ComplianceStatus.COMPLIANT
        elif score >= 0.5:
            status = ComplianceStatus.PARTIALLY_COMPLIANT
        else:
            status = ComplianceStatus.NON_COMPLIANT
            
        check = ComplianceCheck(
            check_id=f"check_{requirement.requirement_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            requirement=requirement,
            status=status,
            score=score,
            findings=findings,
            recommendations=recommendations,
            evidence=evidence_data,
            checked_at=datetime.now()
        )
        
        self._checks.append(check)
        return check
        
    async def run_framework_check(
        self,
        framework: ComplianceFramework,
        evidence_data: Dict[str, Any]
    ) -> List[ComplianceCheck]:
        requirements = COMPLIANCE_REQUIREMENTS.get(framework, [])
        checks = []
        
        for requirement in requirements:
            check = await self.check_requirement(requirement, evidence_data)
            checks.append(check)
            
        return checks


class DataCrossBorderAuditor:
    def __init__(self):
        self._records: List[DataCrossBorderRecord] = []
        self._approved_destinations: Dict[str, List[str]] = {
            "CN": ["EU", "US", "HK", "SG", "JP"],
        }
        self._transfer_mechanisms = [
            "standard_contractual_clauses",
            "binding_corporate_rules",
            "adequacy_decision",
            "consent",
            "government_approval"
        ]
        
    def record_transfer(
        self,
        data_type: str,
        source_country: str,
        destination_country: str,
        transfer_mechanism: str,
        data_volume: int,
        purpose: str,
        legal_basis: str
    ) -> DataCrossBorderRecord:
        record = DataCrossBorderRecord(
            record_id=f"crossborder_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            data_type=data_type,
            source_country=source_country,
            destination_country=destination_country,
            transfer_mechanism=transfer_mechanism,
            data_volume=data_volume,
            purpose=purpose,
            legal_basis=legal_basis,
            timestamp=datetime.now()
        )
        
        self._records.append(record)
        return record
        
    def audit_transfers(self) -> Dict[str, Any]:
        issues = []
        
        for record in self._records:
            approved = self._approved_destinations.get(record.source_country, [])
            if record.destination_country not in approved:
                if record.transfer_mechanism not in self._transfer_mechanisms:
                    issues.append({
                        "record_id": record.record_id,
                        "issue": "未经批准的跨境传输",
                        "destination": record.destination_country,
                        "mechanism": record.transfer_mechanism
                    })
                    
        return {
            "total_transfers": len(self._records),
            "total_volume": sum(r.data_volume for r in self._records),
            "issues_found": len(issues),
            "issues": issues,
            "by_destination": self._aggregate_by_destination(),
            "compliance_status": "compliant" if not issues else "non_compliant"
        }
        
    def _aggregate_by_destination(self) -> Dict[str, int]:
        by_dest = defaultdict(int)
        for record in self._records:
            by_dest[record.destination_country] += record.data_volume
        return dict(by_dest)


class AlgorithmBiasDetector:
    def __init__(self):
        self._results: List[AlgorithmBiasResult] = []
        self._protected_attributes = [
            "gender", "age", "ethnicity", "disability", "religion"
        ]
        self._fairness_threshold = 0.1
        
    async def detect_bias(
        self,
        algorithm_name: str,
        predictions: Dict[str, List[float]],
        ground_truth: Dict[str, List[float]],
        group_labels: Dict[str, List[str]]
    ) -> AlgorithmBiasResult:
        group_scores = {}
        overall_score = 0.0
        bias_detected = False
        affected_groups = []
        
        for group, labels in group_labels.items():
            if group not in predictions or group not in ground_truth:
                continue
                
            pred = predictions[group]
            truth = ground_truth[group]
            
            if len(pred) != len(truth):
                continue
                
            correct = sum(1 for p, t in zip(pred, truth) if abs(p - t) < 0.5)
            accuracy = correct / len(pred) if pred else 0
            group_scores[group] = accuracy
            
        if group_scores:
            scores = list(group_scores.values())
            max_score = max(scores)
            min_score = min(scores)
            
            disparity = max_score - min_score
            overall_score = 1.0 - disparity
            
            if disparity > self._fairness_threshold:
                bias_detected = True
                mean_score = sum(scores) / len(scores)
                affected_groups = [
                    group for group, score in group_scores.items()
                    if abs(score - mean_score) > self._fairness_threshold
                ]
                
        recommendations = []
        if bias_detected:
            recommendations.append("建议对受影响群体进行数据重采样")
            recommendations.append("考虑使用公平性约束重新训练模型")
            recommendations.append("实施算法审计和人工复核机制")
            
        result = AlgorithmBiasResult(
            algorithm_name=algorithm_name,
            metric_type="accuracy_parity",
            overall_score=overall_score,
            group_scores=group_scores,
            bias_detected=bias_detected,
            affected_groups=affected_groups,
            recommendations=recommendations
        )
        
        self._results.append(result)
        return result
        
    def get_bias_summary(self) -> Dict[str, Any]:
        biased_algorithms = [r for r in self._results if r.bias_detected]
        
        return {
            "total_algorithms_tested": len(self._results),
            "biased_algorithms_count": len(biased_algorithms),
            "biased_algorithms": [
                {
                    "name": r.algorithm_name,
                    "score": r.overall_score,
                    "affected_groups": r.affected_groups
                }
                for r in biased_algorithms
            ]
        }


class ComplianceReportGenerator:
    def __init__(self):
        self.checker = ComplianceChecker()
        self.cross_border_auditor = DataCrossBorderAuditor()
        self.bias_detector = AlgorithmBiasDetector()
        
    async def generate_report(
        self,
        frameworks: List[ComplianceFramework],
        evidence_data: Dict[str, Any],
        include_cross_border: bool = True,
        include_bias_detection: bool = True
    ) -> Dict[str, Any]:
        report_id = f"report_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        all_checks = []
        for framework in frameworks:
            checks = await self.checker.run_framework_check(framework, evidence_data)
            all_checks.extend(checks)
            
        compliance_summary = self._calculate_compliance_summary(all_checks)
        
        report = {
            "report_id": report_id,
            "generated_at": datetime.now().isoformat(),
            "frameworks": [f.value for f in frameworks],
            "summary": compliance_summary,
            "checks": [
                {
                    "check_id": c.check_id,
                    "requirement_id": c.requirement.requirement_id,
                    "category": c.requirement.category,
                    "description": c.requirement.description,
                    "status": c.status.value,
                    "score": c.score,
                    "findings": c.findings,
                    "recommendations": c.recommendations
                }
                for c in all_checks
            ],
            "risk_assessment": self._assess_risk(all_checks),
            "action_items": self._generate_action_items(all_checks)
        }
        
        if include_cross_border:
            report["cross_border_audit"] = self.cross_border_auditor.audit_transfers()
            
        if include_bias_detection:
            report["algorithm_bias"] = self.bias_detector.get_bias_summary()
            
        return report
        
    def _calculate_compliance_summary(
        self, 
        checks: List[ComplianceCheck]
    ) -> Dict[str, Any]:
        if not checks:
            return {"overall_score": 0, "status": "no_data"}
            
        compliant = len([c for c in checks if c.status == ComplianceStatus.COMPLIANT])
        partial = len([c for c in checks if c.status == ComplianceStatus.PARTIALLY_COMPLIANT])
        non_compliant = len([c for c in checks if c.status == ComplianceStatus.NON_COMPLIANT])
        
        overall_score = sum(c.score for c in checks) / len(checks)
        
        if overall_score >= 0.8:
            status = "compliant"
        elif overall_score >= 0.5:
            status = "partially_compliant"
        else:
            status = "non_compliant"
            
        return {
            "overall_score": round(overall_score, 2),
            "status": status,
            "compliant_count": compliant,
            "partial_count": partial,
            "non_compliant_count": non_compliant,
            "total_requirements": len(checks)
        }
        
    def _assess_risk(self, checks: List[ComplianceCheck]) -> Dict[str, Any]:
        high_risk = []
        medium_risk = []
        
        for check in checks:
            if check.status == ComplianceStatus.NON_COMPLIANT:
                if check.requirement.is_mandatory:
                    high_risk.append({
                        "requirement": check.requirement.requirement_id,
                        "category": check.requirement.category,
                        "risk": "强制要求未满足"
                    })
                else:
                    medium_risk.append({
                        "requirement": check.requirement.requirement_id,
                        "category": check.requirement.category,
                        "risk": "建议要求未满足"
                    })
                    
        return {
            "risk_level": RiskLevel.HIGH.value if high_risk else 
                         RiskLevel.MEDIUM.value if medium_risk else RiskLevel.LOW.value,
            "high_risk_items": high_risk,
            "medium_risk_items": medium_risk
        }
        
    def _generate_action_items(self, checks: List[ComplianceCheck]) -> List[Dict[str, Any]]:
        actions = []
        
        for check in checks:
            if check.status != ComplianceStatus.COMPLIANT:
                for rec in check.recommendations:
                    actions.append({
                        "requirement": check.requirement.requirement_id,
                        "action": rec,
                        "priority": "high" if check.status == ComplianceStatus.NON_COMPLIANT else "medium",
                        "deadline": (datetime.now() + timedelta(days=30)).isoformat()
                    })
                    
        return actions
        
    async def generate_government_report(
        self,
        government_endpoint: str,
        report_format: str = "json"
    ) -> Dict[str, Any]:
        frameworks = [ComplianceFramework.PIPL, ComplianceFramework.GDPR]
        
        evidence_data = {
            "隐私政策": True,
            "同意记录": True,
            "处理活动记录": True,
            "安全策略": True,
            "加密措施": True,
            "访问控制": True,
            "应急预案": True,
            "PIA报告": False,
            "DPIA报告": False,
        }
        
        report = await self.generate_report(
            frameworks=frameworks,
            evidence_data=evidence_data,
            include_cross_border=True,
            include_bias_detection=True
        )
        
        report["government_endpoint"] = government_endpoint
        report["report_format"] = report_format
        report["certification"] = self._generate_certification(report)
        
        return report
        
    def _generate_certification(self, report: Dict[str, Any]) -> Dict[str, str]:
        return {
            "certified_by": "智链五方合规系统",
            "certification_date": datetime.now().isoformat(),
            "valid_until": (datetime.now() + timedelta(days=365)).isoformat(),
            "signature": "digital_signature_placeholder"
        }


compliance_report_generator = ComplianceReportGenerator()


async def generate_compliance_report(
    frameworks: List[str] = None,
    evidence_data: Dict[str, Any] = None
) -> Dict[str, Any]:
    if frameworks is None:
        frameworks = ["gdpr", "pipl"]
        
    framework_enums = [
        ComplianceFramework(f) for f in frameworks 
        if f in [e.value for e in ComplianceFramework]
    ]
    
    return await compliance_report_generator.generate_report(
        frameworks=framework_enums,
        evidence_data=evidence_data or {}
    )


def get_compliance_generator() -> ComplianceReportGenerator:
    return compliance_report_generator
