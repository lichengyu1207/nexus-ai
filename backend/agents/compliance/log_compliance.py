"""
日志合规检查智能体
Log Compliance Checker Agent - 检查日志管理是否符合合规要求
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
import asyncio
import json
import uuid


class ComplianceCategory(Enum):
    LOG_COMPLETENESS = "log_completeness"
    LOG_RETENTION = "log_retention"
    LOG_INTEGRITY = "log_integrity"
    LOG_ACCESS_CONTROL = "log_access_control"
    LOG_DESENSITIZATION = "log_desensitization"
    LOG_BACKUP = "log_backup"


class ComplianceLevel(Enum):
    COMPLIANT = "compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    NON_COMPLIANT = "non_compliant"
    NOT_APPLICABLE = "not_applicable"


@dataclass
class ComplianceItem:
    item_id: str
    category: ComplianceCategory
    requirement: str
    legal_reference: str
    check_method: str
    status: ComplianceLevel = ComplianceLevel.NOT_APPLICABLE
    score: float = 0.0
    findings: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)
    remediation: str = ""
    checked_at: Optional[datetime] = None


@dataclass
class ComplianceCheckResult:
    check_id: str
    check_time: datetime
    overall_score: float
    overall_status: ComplianceLevel
    items: List[ComplianceItem]
    summary: str
    recommendations: List[str]
    next_check_date: datetime


class LogCompletenessChecker:
    REQUIRED_LOG_TYPES = [
        "user_login",
        "user_logout",
        "data_access",
        "data_modification",
        "permission_change",
        "system_event",
        "security_event",
    ]

    def __init__(self):
        self.log_type_registry: Dict[str, Dict] = {}
        self.log_samples: Dict[str, List[Dict]] = {}

    def register_log_type(
        self, log_type: str, description: str, required_fields: List[str]
    ) -> None:
        self.log_type_registry[log_type] = {
            "description": description,
            "required_fields": required_fields,
            "registered_at": datetime.utcnow().isoformat(),
        }

    def record_log_sample(self, log_type: str, sample: Dict) -> None:
        if log_type not in self.log_samples:
            self.log_samples[log_type] = []
        self.log_samples[log_type].append(sample)

    def check_completeness(self) -> Dict[str, Any]:
        result = {
            "compliant": True,
            "coverage_rate": 0.0,
            "missing_log_types": [],
            "incomplete_logs": [],
        }

        registered_types = set(self.log_type_registry.keys())
        required_types = set(self.REQUIRED_LOG_TYPES)

        missing = required_types - registered_types
        if missing:
            result["compliant"] = False
            result["missing_log_types"] = list(missing)

        for log_type, samples in self.log_samples.items():
            if log_type in self.log_type_registry:
                required_fields = set(
                    self.log_type_registry[log_type]["required_fields"]
                )
                for sample in samples[:10]:
                    sample_fields = set(sample.keys())
                    missing_fields = required_fields - sample_fields
                    if missing_fields:
                        result["incomplete_logs"].append(
                            {
                                "log_type": log_type,
                                "missing_fields": list(missing_fields),
                            }
                        )
                        result["compliant"] = False

        if required_types:
            result["coverage_rate"] = len(registered_types & required_types) / len(
                required_types
            )

        return result

    def check_critical_operations_logged(self) -> Dict[str, Any]:
        critical_operations = [
            "user_authentication",
            "sensitive_data_access",
            "permission_modification",
            "system_configuration_change",
            "data_export",
        ]

        result = {
            "all_logged": True,
            "unlogged_operations": [],
            "logging_details": {},
        }

        for op in critical_operations:
            if op in self.log_samples and len(self.log_samples[op]) > 0:
                result["logging_details"][op] = {
                    "logged": True,
                    "sample_count": len(self.log_samples[op]),
                }
            else:
                result["all_logged"] = False
                result["unlogged_operations"].append(op)
                result["logging_details"][op] = {"logged": False, "sample_count": 0}

        return result


class LogRetentionChecker:
    DEFAULT_RETENTION_DAYS = {
        "security_event": 365,
        "user_access": 180,
        "system_event": 90,
        "application_log": 30,
    }

    def __init__(self):
        self.retention_policies: Dict[str, Dict] = {}
        self.log_storage: Dict[str, Dict] = {}

    def set_retention_policy(
        self, log_type: str, retention_days: int, legal_basis: str = ""
    ) -> None:
        self.retention_policies[log_type] = {
            "retention_days": retention_days,
            "legal_basis": legal_basis,
            "set_at": datetime.utcnow().isoformat(),
        }

    def register_log_storage(
        self, log_type: str, storage_location: str, oldest_log_date: datetime
    ) -> None:
        self.log_storage[log_type] = {
            "location": storage_location,
            "oldest_log_date": oldest_log_date,
            "registered_at": datetime.utcnow().isoformat(),
        }

    def check_retention_compliance(self) -> Dict[str, Any]:
        result = {
            "compliant": True,
            "issues": [],
            "retention_status": {},
        }

        for log_type, policy in self.retention_policies.items():
            required_days = policy["retention_days"]
            storage_info = self.log_storage.get(log_type, {})
            oldest_date = storage_info.get("oldest_log_date")

            if oldest_date:
                actual_days = (datetime.utcnow() - oldest_date).days
                compliant = actual_days >= required_days

                result["retention_status"][log_type] = {
                    "required_days": required_days,
                    "actual_days": actual_days,
                    "compliant": compliant,
                }

                if not compliant:
                    result["compliant"] = False
                    result["issues"].append(
                        f"{log_type}日志保留期不足: 要求{required_days}天, 实际{actual_days}天"
                    )
            else:
                result["compliant"] = False
                result["issues"].append(f"{log_type}日志存储信息未注册")
                result["retention_status"][log_type] = {
                    "required_days": required_days,
                    "actual_days": 0,
                    "compliant": False,
                }

        for log_type, default_days in self.DEFAULT_RETENTION_DAYS.items():
            if log_type not in self.retention_policies:
                result["issues"].append(f"{log_type}未设置保留策略")

        return result

    def check_legal_requirements(self) -> Dict[str, Any]:
        result = {
            "meets_pipl_requirement": True,
            "meets_data_security_law": True,
            "issues": [],
        }

        pipl_required_days = 180
        security_law_required_days = 180

        for log_type, policy in self.retention_policies.items():
            if log_type in ["user_access", "security_event"]:
                if policy["retention_days"] < pipl_required_days:
                    result["meets_pipl_requirement"] = False
                    result["issues"].append(
                        f"{log_type}保留期不满足PIPL要求({pipl_required_days}天)"
                    )

        return result


class LogIntegrityChecker:
    def __init__(self):
        self.hash_chains: Dict[str, List[str]] = {}
        self.verification_records: List[Dict] = []

    def register_hash_chain(self, chain_id: str, hashes: List[str]) -> None:
        self.hash_chains[chain_id] = hashes

    def verify_hash_chain(self, chain_id: str) -> Dict[str, Any]:
        result = {
            "chain_id": chain_id,
            "valid": True,
            "issues": [],
            "verified_at": datetime.utcnow().isoformat(),
        }

        hashes = self.hash_chains.get(chain_id, [])
        if not hashes:
            result["valid"] = False
            result["issues"].append("Hash chain not found")
            return result

        for i in range(1, len(hashes)):
            expected = self._compute_chain_hash(hashes[i - 1])
            if hashes[i] != expected:
                result["valid"] = False
                result["issues"].append(f"Hash mismatch at position {i}")

        self.verification_records.append(result)
        return result

    def _compute_chain_hash(self, previous_hash: str) -> str:
        import hashlib

        return hashlib.sha256(previous_hash.encode()).hexdigest()

    def check_tamper_evidence(self) -> Dict[str, Any]:
        result = {
            "all_chains_valid": True,
            "invalid_chains": [],
            "last_verification": None,
        }

        for chain_id in self.hash_chains.keys():
            verification = self.verify_hash_chain(chain_id)
            if not verification["valid"]:
                result["all_chains_valid"] = False
                result["invalid_chains"].append(chain_id)

        if self.verification_records:
            result["last_verification"] = self.verification_records[-1]["verified_at"]

        return result


class LogAccessControlChecker:
    def __init__(self):
        self.access_policies: Dict[str, Dict] = {}
        self.access_logs: List[Dict] = []

    def set_access_policy(
        self, log_type: str, allowed_roles: List[str], conditions: Dict = None
    ) -> None:
        self.access_policies[log_type] = {
            "allowed_roles": allowed_roles,
            "conditions": conditions or {},
            "set_at": datetime.utcnow().isoformat(),
        }

    def log_access_attempt(
        self,
        user_id: str,
        log_type: str,
        action: str,
        granted: bool,
        reason: str = None,
    ) -> None:
        self.access_logs.append(
            {
                "user_id": user_id,
                "log_type": log_type,
                "action": action,
                "granted": granted,
                "reason": reason,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    def check_access_control(self) -> Dict[str, Any]:
        result = {
            "has_policies": len(self.access_policies) > 0,
            "policy_coverage": {},
            "unauthorized_attempts": [],
        }

        critical_log_types = ["security_event", "user_access", "permission_change"]
        for log_type in critical_log_types:
            has_policy = log_type in self.access_policies
            result["policy_coverage"][log_type] = has_policy

        for access in self.access_logs:
            if not access["granted"]:
                result["unauthorized_attempts"].append(
                    {
                        "user_id": access["user_id"],
                        "log_type": access["log_type"],
                        "timestamp": access["timestamp"],
                    }
                )

        return result

    def check_audit_trail(self) -> Dict[str, Any]:
        result = {
            "has_audit_trail": len(self.access_logs) > 0,
            "total_access_records": len(self.access_logs),
            "unique_users": len(set(a["user_id"] for a in self.access_logs)),
            "access_by_action": {},
        }

        for access in self.access_logs:
            action = access["action"]
            result["access_by_action"][action] = (
                result["access_by_action"].get(action, 0) + 1
            )

        return result


class LogDesensitizationChecker:
    SENSITIVE_PATTERNS = {
        "id_card": r"\d{17}[\dXx]",
        "phone": r"1[3-9]\d{9}",
        "email": r"[\w.-]+@[\w.-]+\.\w+",
        "bank_card": r"\d{16,19}",
    }

    def __init__(self):
        self.desensitization_rules: Dict[str, Dict] = {}
        self.sample_logs: List[str] = []

    def set_desensitization_rule(
        self, data_type: str, pattern: str, replacement: str
    ) -> None:
        self.desensitization_rules[data_type] = {
            "pattern": pattern,
            "replacement": replacement,
            "set_at": datetime.utcnow().isoformat(),
        }

    def add_sample_log(self, log_content: str) -> None:
        self.sample_logs.append(log_content)

    def check_desensitization(self) -> Dict[str, Any]:
        import re

        result = {
            "compliant": True,
            "sensitive_data_found": [],
            "rules_coverage": {},
        }

        for data_type, pattern in self.SENSITIVE_PATTERNS.items():
            has_rule = data_type in self.desensitization_rules
            result["rules_coverage"][data_type] = has_rule

        for i, log in enumerate(self.sample_logs[:100]):
            for data_type, pattern in self.SENSITIVE_PATTERNS.items():
                matches = re.findall(pattern, log)
                if matches:
                    result["sensitive_data_found"].append(
                        {
                            "log_index": i,
                            "data_type": data_type,
                            "match_count": len(matches),
                        }
                    )
                    result["compliant"] = False

        return result


class LogComplianceCheckerAgent:
    def __init__(self, agent_id: str = "log_compliance_001"):
        self.agent_id = agent_id
        self.completeness_checker = LogCompletenessChecker()
        self.retention_checker = LogRetentionChecker()
        self.integrity_checker = LogIntegrityChecker()
        self.access_checker = LogAccessControlChecker()
        self.desensitization_checker = LogDesensitizationChecker()

        self.check_history: List[ComplianceCheckResult] = []
        self._initialize_default_settings()

    def _initialize_default_settings(self) -> None:
        for log_type in LogCompletenessChecker.REQUIRED_LOG_TYPES:
            self.completeness_checker.register_log_type(
                log_type,
                f"{log_type}日志",
                ["timestamp", "user_id", "action", "details"],
            )

        for log_type, days in LogRetentionChecker.DEFAULT_RETENTION_DAYS.items():
            self.retention_checker.set_retention_policy(
                log_type, days, "符合法规要求"
            )

        for data_type, pattern in LogDesensitizationChecker.SENSITIVE_PATTERNS.items():
            self.desensitization_checker.set_desensitization_rule(
                data_type, pattern, "******"
            )

    async def check_completeness(self) -> ComplianceItem:
        item = ComplianceItem(
            item_id="comp_001",
            category=ComplianceCategory.LOG_COMPLETENESS,
            requirement="应记录所有关键操作日志",
            legal_reference="《个人信息保护法》第55条",
            check_method="检查日志类型覆盖率和字段完整性",
        )

        result = self.completeness_checker.check_completeness()
        critical_ops = self.completeness_checker.check_critical_operations_logged()

        if result["compliant"] and critical_ops["all_logged"]:
            item.status = ComplianceLevel.COMPLIANT
            item.score = 100
        elif result["coverage_rate"] >= 0.7:
            item.status = ComplianceLevel.PARTIALLY_COMPLIANT
            item.score = result["coverage_rate"] * 100
            item.findings.append(f"日志覆盖率: {result['coverage_rate']:.1%}")
            item.findings.extend(result["missing_log_types"])
        else:
            item.status = ComplianceLevel.NON_COMPLIANT
            item.score = result["coverage_rate"] * 100
            item.findings.append("日志记录不完整")
            item.remediation = "完善日志记录机制，确保所有关键操作被记录"

        item.evidence.append(f"覆盖率: {result['coverage_rate']:.1%}")
        item.checked_at = datetime.utcnow()
        return item

    async def check_retention(self) -> ComplianceItem:
        item = ComplianceItem(
            item_id="ret_001",
            category=ComplianceCategory.LOG_RETENTION,
            requirement="日志应保留至少6个月",
            legal_reference="《个人信息保护法》第55条",
            check_method="检查日志保留策略和实际保留期限",
        )

        result = self.retention_checker.check_retention_compliance()
        legal_result = self.retention_checker.check_legal_requirements()

        if result["compliant"] and legal_result["meets_pipl_requirement"]:
            item.status = ComplianceLevel.COMPLIANT
            item.score = 100
        else:
            item.status = ComplianceLevel.NON_COMPLIANT
            item.score = 50
            item.findings.extend(result["issues"])
            item.findings.extend(legal_result["issues"])
            item.remediation = "调整日志保留策略，确保满足法规要求"

        item.checked_at = datetime.utcnow()
        return item

    async def check_integrity(self) -> ComplianceItem:
        item = ComplianceItem(
            item_id="int_001",
            category=ComplianceCategory.LOG_INTEGRITY,
            requirement="日志应具备防篡改机制",
            legal_reference="《数据安全法》第27条",
            check_method="检查日志完整性校验机制",
        )

        result = self.integrity_checker.check_tamper_evidence()

        if result["all_chains_valid"]:
            item.status = ComplianceLevel.COMPLIANT
            item.score = 100
            item.evidence.append("所有哈希链验证通过")
        else:
            item.status = ComplianceLevel.NON_COMPLIANT
            item.score = 0
            item.findings.append(f"存在无效哈希链: {result['invalid_chains']}")
            item.remediation = "建立日志哈希链机制，确保日志不可篡改"

        item.checked_at = datetime.utcnow()
        return item

    async def check_access_control(self) -> ComplianceItem:
        item = ComplianceItem(
            item_id="acc_001",
            category=ComplianceCategory.LOG_ACCESS_CONTROL,
            requirement="日志访问应有权限管控",
            legal_reference="《数据安全法》第27条",
            check_method="检查日志访问控制策略",
        )

        result = self.access_checker.check_access_control()
        audit_result = self.access_checker.check_audit_trail()

        if result["has_policies"] and audit_result["has_audit_trail"]:
            item.status = ComplianceLevel.COMPLIANT
            item.score = 100
            item.evidence.append("已设置访问控制策略")
            item.evidence.append(f"访问记录数: {audit_result['total_access_records']}")
        elif result["has_policies"]:
            item.status = ComplianceLevel.PARTIALLY_COMPLIANT
            item.score = 70
            item.findings.append("缺少访问审计记录")
        else:
            item.status = ComplianceLevel.NON_COMPLIANT
            item.score = 0
            item.findings.append("未设置日志访问控制策略")
            item.remediation = "建立日志访问控制机制，记录所有访问行为"

        item.checked_at = datetime.utcnow()
        return item

    async def check_desensitization(self) -> ComplianceItem:
        item = ComplianceItem(
            item_id="des_001",
            category=ComplianceCategory.LOG_DESENSITIZATION,
            requirement="日志中的敏感信息应脱敏处理",
            legal_reference="《个人信息保护法》第51条",
            check_method="检查日志脱敏规则和执行情况",
        )

        result = self.desensitization_checker.check_desensitization()

        if result["compliant"]:
            item.status = ComplianceLevel.COMPLIANT
            item.score = 100
            item.evidence.append("未发现敏感数据泄露")
        else:
            item.status = ComplianceLevel.NON_COMPLIANT
            item.score = 50
            item.findings.append(
                f"发现{len(result['sensitive_data_found'])}处敏感数据"
            )
            item.remediation = "实施日志脱敏处理，防止敏感信息泄露"

        item.checked_at = datetime.utcnow()
        return item

    async def run_full_check(self) -> ComplianceCheckResult:
        check_id = f"log_check_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        items = []
        items.append(await self.check_completeness())
        items.append(await self.check_retention())
        items.append(await self.check_integrity())
        items.append(await self.check_access_control())
        items.append(await self.check_desensitization())

        scores = [item.score for item in items if item.status != ComplianceLevel.NOT_APPLICABLE]
        overall_score = sum(scores) / len(scores) if scores else 0

        if overall_score >= 90:
            overall_status = ComplianceLevel.COMPLIANT
        elif overall_score >= 70:
            overall_status = ComplianceLevel.PARTIALLY_COMPLIANT
        else:
            overall_status = ComplianceLevel.NON_COMPLIANT

        summary = self._generate_summary(items, overall_score)
        recommendations = [
            item.remediation for item in items if item.remediation
        ]

        result = ComplianceCheckResult(
            check_id=check_id,
            check_time=datetime.utcnow(),
            overall_score=round(overall_score, 2),
            overall_status=overall_status,
            items=items,
            summary=summary,
            recommendations=recommendations,
            next_check_date=datetime.utcnow() + timedelta(days=30),
        )

        self.check_history.append(result)
        return result

    def _generate_summary(
        self, items: List[ComplianceItem], score: float
    ) -> str:
        compliant = sum(
            1 for i in items if i.status == ComplianceLevel.COMPLIANT
        )
        non_compliant = sum(
            1 for i in items if i.status == ComplianceLevel.NON_COMPLIANT
        )
        partial = sum(
            1 for i in items if i.status == ComplianceLevel.PARTIALLY_COMPLIANT
        )

        return (
            f"日志合规检查共{len(items)}项，"
            f"合规{compliant}项，部分合规{partial}项，不合规{non_compliant}项。"
            f"总体评分{score:.1f}分。"
        )

    def get_check_history(self, limit: int = 10) -> List[ComplianceCheckResult]:
        return self.check_history[-limit:]

    def get_compliance_metrics(self) -> Dict[str, Any]:
        if not self.check_history:
            return {"total_checks": 0, "average_score": 0}

        scores = [c.overall_score for c in self.check_history]
        return {
            "total_checks": len(self.check_history),
            "average_score": round(sum(scores) / len(scores), 2),
            "latest_score": scores[-1],
            "trend": "上升" if len(scores) >= 2 and scores[-1] > scores[-2] else "稳定",
        }
