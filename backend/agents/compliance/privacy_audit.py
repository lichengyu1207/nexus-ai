"""
个人信息保护合规审计智能体
Privacy Audit Agent - 执行个人信息保护合规审计

参照《个人信息保护合规审计要求》
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
import asyncio
import json
import hashlib
import uuid


class AuditScope(Enum):
    COLLECTION = "collection"
    STORAGE = "storage"
    USAGE = "usage"
    PROCESSING = "processing"
    TRANSMISSION = "transmission"
    PROVISION = "provision"
    DISCLOSURE = "disclosure"
    DELETION = "deletion"
    FULL_LIFECYCLE = "full_lifecycle"


class AuditResult(Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    NOT_APPLICABLE = "not_applicable"


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AuditCheckItem:
    check_id: str
    category: str
    requirement: str
    legal_basis: str
    check_method: str
    result: AuditResult = AuditResult.NOT_APPLICABLE
    evidence: List[str] = field(default_factory=list)
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.MEDIUM
    weight: float = 1.0


@dataclass
class PrivacyAuditResult:
    audit_id: str
    audit_time: datetime
    scope: AuditScope
    overall_score: float
    overall_result: AuditResult
    check_items: List[AuditCheckItem]
    summary: str
    critical_issues: List[str] = field(default_factory=list)
    improvement_plan: List[Dict[str, Any]] = field(default_factory=list)
    evidence_attachments: List[str] = field(default_factory=list)
    auditor: str = "PrivacyAuditAgent"
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None


class LegalBasisChecker:
    LEGAL_BASIS_TYPES = [
        "consent",
        "contract",
        "legal_obligation",
        "vital_interests",
        "public_interest",
        "legitimate_interests",
    ]

    def __init__(self):
        self.consent_records: Dict[str, List[Dict]] = {}
        self.contract_records: Dict[str, Dict] = {}

    def check_consent_validity(
        self, user_id: str, processing_purpose: str
    ) -> Dict[str, Any]:
        result = {
            "has_valid_consent": False,
            "consent_details": None,
            "issues": [],
        }

        if user_id in self.consent_records:
            for consent in self.consent_records[user_id]:
                if consent.get("purpose") == processing_purpose:
                    if consent.get("status") == "active":
                        result["has_valid_consent"] = True
                        result["consent_details"] = consent
                    else:
                        result["issues"].append(
                            f"Consent for {processing_purpose} is {consent.get('status')}"
                        )
                    break

        if not result["has_valid_consent"] and not result["issues"]:
            result["issues"].append(
                f"No consent record found for {processing_purpose}"
            )

        return result

    def check_contract_basis(
        self, user_id: str, contract_type: str
    ) -> Dict[str, Any]:
        result = {"has_contract_basis": False, "contract_details": None, "issues": []}

        if user_id in self.contract_records:
            contract = self.contract_records[user_id]
            if contract.get("type") == contract_type and contract.get("active"):
                result["has_contract_basis"] = True
                result["contract_details"] = contract

        return result

    def register_consent(
        self, user_id: str, purpose: str, consent_details: Dict
    ) -> None:
        if user_id not in self.consent_records:
            self.consent_records[user_id] = []

        self.consent_records[user_id].append(
            {
                "purpose": purpose,
                "status": "active",
                "granted_at": datetime.utcnow().isoformat(),
                **consent_details,
            }
        )

    def register_contract(self, user_id: str, contract_details: Dict) -> None:
        self.contract_records[user_id] = {
            **contract_details,
            "active": True,
            "created_at": datetime.utcnow().isoformat(),
        }


class MinimalityChecker:
    def __init__(self):
        self.data_collection_registry: Dict[str, Dict] = {}
        self.business_requirements: Dict[str, List[str]] = {}

    def register_data_collection(
        self, purpose: str, data_fields: List[str], justification: str
    ) -> None:
        self.data_collection_registry[purpose] = {
            "fields": data_fields,
            "justification": justification,
            "registered_at": datetime.utcnow().isoformat(),
        }

    def register_business_requirement(
        self, feature: str, required_fields: List[str]
    ) -> None:
        self.business_requirements[feature] = required_fields

    def check_minimality(self, purpose: str) -> Dict[str, Any]:
        result = {
            "is_minimal": True,
            "collected_fields": [],
            "required_fields": [],
            "excessive_fields": [],
            "issues": [],
        }

        if purpose in self.data_collection_registry:
            collected = set(self.data_collection_registry[purpose]["fields"])
            result["collected_fields"] = list(collected)

            required = set()
            for feature, fields in self.business_requirements.items():
                if purpose in feature or feature in purpose:
                    required.update(fields)
            result["required_fields"] = list(required)

            excessive = collected - required
            if excessive:
                result["is_minimal"] = False
                result["excessive_fields"] = list(excessive)
                result["issues"].append(
                    f"Excessive data collection: {', '.join(excessive)}"
                )

        return result


class SecurityMeasuresChecker:
    def __init__(self):
        self.security_controls: Dict[str, Dict] = {}

    def register_security_control(
        self, control_id: str, control_type: str, details: Dict
    ) -> None:
        self.security_controls[control_id] = {
            "type": control_type,
            "details": details,
            "registered_at": datetime.utcnow().isoformat(),
        }

    def check_encryption(self, data_type: str) -> Dict[str, Any]:
        result = {"encrypted": False, "encryption_details": None, "issues": []}

        for control_id, control in self.security_controls.items():
            if control["type"] == "encryption":
                if data_type in control["details"].get("protected_data_types", []):
                    result["encrypted"] = True
                    result["encryption_details"] = control["details"]
                    break

        if not result["encrypted"]:
            result["issues"].append(f"No encryption found for {data_type}")

        return result

    def check_access_control(self, resource: str) -> Dict[str, Any]:
        result = {"has_access_control": False, "control_details": None, "issues": []}

        for control_id, control in self.security_controls.items():
            if control["type"] == "access_control":
                if resource in control["details"].get("protected_resources", []):
                    result["has_access_control"] = True
                    result["control_details"] = control["details"]
                    break

        if not result["has_access_control"]:
            result["issues"].append(f"No access control for {resource}")

        return result


class RightsProtectionChecker:
    USER_RIGHTS = [
        "access",
        "copy",
        "correction",
        "deletion",
        "portability",
        "withdraw_consent",
        "automated_decision_opt_out",
    ]

    def __init__(self):
        self.rights_implementation: Dict[str, Dict] = {}

    def register_right_implementation(
        self, right_type: str, implementation: Dict
    ) -> None:
        self.rights_implementation[right_type] = {
            **implementation,
            "registered_at": datetime.utcnow().isoformat(),
        }

    def check_right_availability(self, right_type: str) -> Dict[str, Any]:
        result = {"available": False, "implementation": None, "issues": []}

        if right_type in self.rights_implementation:
            impl = self.rights_implementation[right_type]
            if impl.get("implemented"):
                result["available"] = True
                result["implementation"] = impl
            else:
                result["issues"].append(f"{right_type} is not implemented")
        else:
            result["issues"].append(f"{right_type} is not registered")

        return result

    def check_all_rights(self) -> Dict[str, Any]:
        result = {"rights_status": {}, "missing_rights": [], "issues": []}

        for right in self.USER_RIGHTS:
            check = self.check_right_availability(right)
            result["rights_status"][right] = check

            if not check["available"]:
                result["missing_rights"].append(right)
                result["issues"].extend(check["issues"])

        return result


class CrossBorderTransferChecker:
    def __init__(self):
        self.transfer_records: List[Dict] = []
        self.security_assessments: Dict[str, Dict] = {}

    def register_transfer(self, transfer_details: Dict) -> str:
        transfer_id = f"transfer_{uuid.uuid4().hex[:8]}"
        self.transfer_records.append(
            {
                "transfer_id": transfer_id,
                **transfer_details,
                "registered_at": datetime.utcnow().isoformat(),
            }
        )
        return transfer_id

    def register_security_assessment(
        self, assessment_id: str, assessment_details: Dict
    ) -> None:
        self.security_assessments[assessment_id] = {
            **assessment_details,
            "assessed_at": datetime.utcnow().isoformat(),
        }

    def check_transfer_compliance(self, transfer_id: str) -> Dict[str, Any]:
        result = {
            "compliant": False,
            "transfer_details": None,
            "assessment_details": None,
            "issues": [],
        }

        transfer = next(
            (t for t in self.transfer_records if t["transfer_id"] == transfer_id), None
        )
        if transfer:
            result["transfer_details"] = transfer

            assessment_id = transfer.get("security_assessment_id")
            if assessment_id and assessment_id in self.security_assessments:
                assessment = self.security_assessments[assessment_id]
                result["assessment_details"] = assessment

                if assessment.get("passed"):
                    result["compliant"] = True
                else:
                    result["issues"].append("Security assessment not passed")
            else:
                result["issues"].append("No security assessment found")
        else:
            result["issues"].append(f"Transfer {transfer_id} not found")

        return result


class PrivacyAuditAgent:
    def __init__(self, agent_id: str = "privacy_audit_001"):
        self.agent_id = agent_id
        self.legal_basis_checker = LegalBasisChecker()
        self.minimality_checker = MinimalityChecker()
        self.security_checker = SecurityMeasuresChecker()
        self.rights_checker = RightsProtectionChecker()
        self.crossborder_checker = CrossBorderTransferChecker()

        self.audit_history: List[PrivacyAuditResult] = []
        self.audit_templates: Dict[str, List[AuditCheckItem]] = {}

        self._initialize_audit_templates()

    def _initialize_audit_templates(self) -> None:
        self.audit_templates["collection"] = [
            AuditCheckItem(
                check_id="col_001",
                category="合法性基础",
                requirement="处理个人信息前应当取得个人同意",
                legal_basis="《个人信息保护法》第十三条",
                check_method="检查同意记录",
                weight=2.0,
                risk_level=RiskLevel.HIGH,
            ),
            AuditCheckItem(
                check_id="col_002",
                category="告知义务",
                requirement="应当以显著方式、清晰易懂的语言告知个人信息处理规则",
                legal_basis="《个人信息保护法》第十七条",
                check_method="检查隐私政策",
                weight=1.5,
                risk_level=RiskLevel.HIGH,
            ),
            AuditCheckItem(
                check_id="col_003",
                category="最小必要",
                requirement="收集个人信息应当具有明确、合理的目的，并应当限于实现处理目的的最小范围",
                legal_basis="《个人信息保护法》第六条",
                check_method="数据收集范围审查",
                weight=1.5,
                risk_level=RiskLevel.MEDIUM,
            ),
        ]

        self.audit_templates["storage"] = [
            AuditCheckItem(
                check_id="sto_001",
                category="存储安全",
                requirement="应当采取加密、去标识化等安全技术措施",
                legal_basis="《个人信息保护法》第五十一条",
                check_method="检查加密措施",
                weight=2.0,
                risk_level=RiskLevel.HIGH,
            ),
            AuditCheckItem(
                check_id="sto_002",
                category="存储期限",
                requirement="应当确定个人信息存储期限",
                legal_basis="《个人信息保护法》第十九条",
                check_method="检查存储策略",
                weight=1.0,
                risk_level=RiskLevel.MEDIUM,
            ),
        ]

        self.audit_templates["usage"] = [
            AuditCheckItem(
                check_id="use_001",
                category="目的限制",
                requirement="应当按照约定用途使用个人信息",
                legal_basis="《个人信息保护法》第六条",
                check_method="使用日志审计",
                weight=2.0,
                risk_level=RiskLevel.HIGH,
            ),
            AuditCheckItem(
                check_id="use_002",
                category="自动化决策",
                requirement="通过自动化决策方式作出对个人权益有重大影响的决定，应当提供不针对个人特征的选项",
                legal_basis="《个人信息保护法》第二十四条",
                check_method="自动化决策审计",
                weight=1.5,
                risk_level=RiskLevel.HIGH,
            ),
        ]

        self.audit_templates["transmission"] = [
            AuditCheckItem(
                check_id="tra_001",
                category="传输安全",
                requirement="传输个人信息应当采取加密措施",
                legal_basis="《个人信息保护法》第五十一条",
                check_method="传输协议检查",
                weight=2.0,
                risk_level=RiskLevel.HIGH,
            ),
            AuditCheckItem(
                check_id="tra_002",
                category="跨境传输",
                requirement="向境外提供个人信息应当通过安全评估或符合其他法定条件",
                legal_basis="《个人信息保护法》第三十八条",
                check_method="跨境传输审计",
                weight=2.5,
                risk_level=RiskLevel.CRITICAL,
            ),
        ]

        self.audit_templates["deletion"] = [
            AuditCheckItem(
                check_id="del_001",
                category="删除义务",
                requirement="处理目的已实现、无法实现或不再必要时应删除个人信息",
                legal_basis="《个人信息保护法》第四十七条",
                check_method="删除记录审计",
                weight=1.5,
                risk_level=RiskLevel.MEDIUM,
            ),
        ]

    def _get_checks_for_scope(self, scope: AuditScope) -> List[AuditCheckItem]:
        if scope == AuditScope.FULL_LIFECYCLE:
            all_checks = []
            for template_checks in self.audit_templates.values():
                all_checks.extend(template_checks)
            return all_checks
        return self.audit_templates.get(scope.value, [])

    async def execute_check(
        self, check_item: AuditCheckItem, context: Dict[str, Any]
    ) -> AuditCheckItem:
        check_item = AuditCheckItem(
            check_id=check_item.check_id,
            category=check_item.category,
            requirement=check_item.requirement,
            legal_basis=check_item.legal_basis,
            check_method=check_item.check_method,
            weight=check_item.weight,
            risk_level=check_item.risk_level,
        )

        if check_item.check_id.startswith("col_001"):
            consent_check = self.legal_basis_checker.check_consent_validity(
                context.get("user_id", "default"),
                context.get("processing_purpose", "general"),
            )
            if consent_check["has_valid_consent"]:
                check_item.result = AuditResult.COMPLIANT
                check_item.evidence.append(
                    f"Valid consent found: {consent_check['consent_details']}"
                )
            else:
                check_item.result = AuditResult.NON_COMPLIANT
                check_item.issues.extend(consent_check["issues"])
                check_item.recommendations.append("获取用户明确同意")

        elif check_item.check_id.startswith("col_003"):
            minimality_check = self.minimality_checker.check_minimality(
                context.get("collection_purpose", "general")
            )
            if minimality_check["is_minimal"]:
                check_item.result = AuditResult.COMPLIANT
                check_item.evidence.append("数据收集符合最小必要原则")
            else:
                check_item.result = AuditResult.NON_COMPLIANT
                check_item.issues.extend(minimality_check["issues"])
                check_item.recommendations.append("减少非必要数据收集")

        elif check_item.check_id.startswith("sto_001"):
            encryption_check = self.security_checker.check_encryption(
                context.get("data_type", "personal_info")
            )
            if encryption_check["encrypted"]:
                check_item.result = AuditResult.COMPLIANT
                check_item.evidence.append(
                    f"Encryption in place: {encryption_check['encryption_details']}"
                )
            else:
                check_item.result = AuditResult.NON_COMPLIANT
                check_item.issues.extend(encryption_check["issues"])
                check_item.recommendations.append("实施敏感数据加密存储")

        elif check_item.check_id.startswith("tra_002"):
            transfer_id = context.get("transfer_id")
            if transfer_id:
                transfer_check = self.crossborder_checker.check_transfer_compliance(
                    transfer_id
                )
                if transfer_check["compliant"]:
                    check_item.result = AuditResult.COMPLIANT
                    check_item.evidence.append("跨境传输符合要求")
                else:
                    check_item.result = AuditResult.NON_COMPLIANT
                    check_item.issues.extend(transfer_check["issues"])
                    check_item.recommendations.append("完成跨境传输安全评估")
            else:
                check_item.result = AuditResult.NOT_APPLICABLE
                check_item.evidence.append("无跨境传输场景")

        else:
            check_item.result = AuditResult.PARTIALLY_COMPLIANT
            check_item.evidence.append("需要进一步人工审查")

        return check_item

    async def run_audit(
        self,
        scope: AuditScope,
        context: Dict[str, Any],
        sample_size: int = 100,
    ) -> PrivacyAuditResult:
        audit_id = f"audit_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}"

        check_items = self._get_checks_for_scope(scope)
        executed_checks = []

        for check_item in check_items:
            executed = await self.execute_check(check_item, context)
            executed_checks.append(executed)

        total_weight = sum(c.weight for c in executed_checks)
        compliant_weight = sum(
            c.weight for c in executed_checks if c.result == AuditResult.COMPLIANT
        )
        overall_score = (
            (compliant_weight / total_weight * 100) if total_weight > 0 else 0
        )

        if overall_score >= 90:
            overall_result = AuditResult.COMPLIANT
        elif overall_score >= 70:
            overall_result = AuditResult.PARTIALLY_COMPLIANT
        else:
            overall_result = AuditResult.NON_COMPLIANT

        critical_issues = [
            f"[{c.check_id}] {c.requirement}"
            for c in executed_checks
            if c.result == AuditResult.NON_COMPLIANT
            and c.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        ]

        improvement_plan = []
        for check in executed_checks:
            if check.result != AuditResult.COMPLIANT:
                improvement_plan.append(
                    {
                        "check_id": check.check_id,
                        "issue": check.requirement,
                        "recommendations": check.recommendations,
                        "priority": check.risk_level.value,
                        "deadline": (
                            datetime.utcnow() + timedelta(days=30)
                        ).isoformat(),
                    }
                )

        result = PrivacyAuditResult(
            audit_id=audit_id,
            audit_time=datetime.utcnow(),
            scope=scope,
            overall_score=round(overall_score, 2),
            overall_result=overall_result,
            check_items=executed_checks,
            summary=self._generate_summary(executed_checks, overall_score),
            critical_issues=critical_issues,
            improvement_plan=improvement_plan,
        )

        self.audit_history.append(result)
        return result

    def _generate_summary(
        self, check_items: List[AuditCheckItem], score: float
    ) -> str:
        compliant = sum(1 for c in check_items if c.result == AuditResult.COMPLIANT)
        non_compliant = sum(
            1 for c in check_items if c.result == AuditResult.NON_COMPLIANT
        )
        partial = sum(
            1 for c in check_items if c.result == AuditResult.PARTIALLY_COMPLIANT
        )

        return (
            f"本次审计共检查{len(check_items)}项，"
            f"合规{compliant}项，不合规{non_compliant}项，部分合规{partial}项。"
            f"总体合规评分{score:.1f}分。"
        )

    def get_audit_history(
        self, limit: int = 10, scope: Optional[AuditScope] = None
    ) -> List[PrivacyAuditResult]:
        results = self.audit_history
        if scope:
            results = [r for r in results if r.scope == scope]
        return results[-limit:]

    def get_audit_by_id(self, audit_id: str) -> Optional[PrivacyAuditResult]:
        return next(
            (a for a in self.audit_history if a.audit_id == audit_id), None
        )

    def approve_audit(
        self, audit_id: str, approver: str
    ) -> Optional[PrivacyAuditResult]:
        audit = self.get_audit_by_id(audit_id)
        if audit:
            audit.approved_by = approver
            audit.approved_at = datetime.utcnow()
        return audit

    def should_audit(self, user_count: int) -> Dict[str, Any]:
        recommendation = {
            "should_audit": False,
            "frequency": None,
            "reason": None,
        }

        if user_count > 1000000:
            recommendation["should_audit"] = True
            recommendation["frequency"] = "每半年一次"
            recommendation["reason"] = "处理超过100万人信息，需每半年审计一次"
        elif user_count > 100000:
            recommendation["should_audit"] = True
            recommendation["frequency"] = "每年一次"
            recommendation["reason"] = "处理超过10万人信息，需每年审计一次"

        return recommendation

    def get_compliance_metrics(self) -> Dict[str, Any]:
        if not self.audit_history:
            return {"total_audits": 0, "average_score": 0, "trend": "无数据"}

        scores = [a.overall_score for a in self.audit_history]
        avg_score = sum(scores) / len(scores)

        if len(scores) >= 2:
            trend = "上升" if scores[-1] > scores[-2] else "下降"
        else:
            trend = "稳定"

        return {
            "total_audits": len(self.audit_history),
            "average_score": round(avg_score, 2),
            "latest_score": scores[-1],
            "trend": trend,
            "compliant_count": sum(
                1 for a in self.audit_history if a.overall_result == AuditResult.COMPLIANT
            ),
            "non_compliant_count": sum(
                1
                for a in self.audit_history
                if a.overall_result == AuditResult.NON_COMPLIANT
            ),
        }
