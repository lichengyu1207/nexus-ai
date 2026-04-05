"""
数据安全合规检查智能体
Data Security Audit Agent - 检查数据安全合规情况

依据《数据安全法》等法规
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
import asyncio
import json
import uuid


class SecurityCheckCategory(Enum):
    DATA_CLASSIFICATION = "data_classification"
    ACCESS_CONTROL = "access_control"
    ENCRYPTION = "encryption"
    TRANSMISSION_SECURITY = "transmission_security"
    BACKUP_RECOVERY = "backup_recovery"
    INCIDENT_RESPONSE = "incident_response"
    AUDIT_LOGGING = "audit_logging"
    VULNERABILITY_MANAGEMENT = "vulnerability_management"


class ComplianceStatus(Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIAL = "partial"
    NOT_APPLICABLE = "not_applicable"
    NOT_CHECKED = "not_checked"


class Severity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SecurityCheckItem:
    item_id: str
    category: SecurityCheckCategory
    requirement: str
    legal_reference: str
    check_method: str
    status: ComplianceStatus = ComplianceStatus.NOT_CHECKED
    score: float = 0.0
    findings: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)
    remediation: str = ""
    severity: Severity = Severity.MEDIUM
    checked_at: Optional[datetime] = None


@dataclass
class SecurityAuditResult:
    audit_id: str
    audit_time: datetime
    overall_score: float
    overall_status: ComplianceStatus
    category_scores: Dict[str, float]
    check_items: List[SecurityCheckItem]
    critical_findings: List[str]
    recommendations: List[str]
    compliance_gaps: List[Dict[str, Any]]
    next_audit_date: datetime


class DataClassificationChecker:
    CLASSIFICATION_LEVELS = ["public", "internal", "confidential", "secret"]

    def __init__(self):
        self.classification_registry: Dict[str, Dict] = {}
        self.data_inventory: Dict[str, Dict] = {}

    def register_data_asset(
        self,
        asset_id: str,
        asset_name: str,
        data_types: List[str],
        sensitivity: str,
    ) -> None:
        self.data_inventory[asset_id] = {
            "name": asset_name,
            "data_types": data_types,
            "sensitivity": sensitivity,
            "registered_at": datetime.utcnow().isoformat(),
        }

    def classify_data(self, asset_id: str, level: str, justification: str) -> None:
        if asset_id in self.data_inventory:
            self.data_inventory[asset_id]["classification"] = level
            self.data_inventory[asset_id]["classification_justification"] = justification
            self.data_inventory[asset_id]["classified_at"] = datetime.utcnow().isoformat()

    def check_classification_coverage(self) -> Dict[str, Any]:
        result = {
            "total_assets": len(self.data_inventory),
            "classified_assets": 0,
            "unclassified_assets": [],
            "coverage_rate": 0.0,
        }

        for asset_id, asset in self.data_inventory.items():
            if "classification" in asset:
                result["classified_assets"] += 1
            else:
                result["unclassified_assets"].append(asset_id)

        if result["total_assets"] > 0:
            result["coverage_rate"] = result["classified_assets"] / result["total_assets"]

        return result

    def check_sensitivity_alignment(self) -> Dict[str, Any]:
        result = {"aligned": True, "misalignments": []}

        for asset_id, asset in self.data_inventory.items():
            if "classification" in asset:
                expected_level = self._determine_expected_level(asset.get("sensitivity", ""))
                if asset["classification"] != expected_level:
                    result["aligned"] = False
                    result["misalignments"].append(
                        {
                            "asset_id": asset_id,
                            "current": asset["classification"],
                            "expected": expected_level,
                        }
                    )

        return result

    def _determine_expected_level(self, sensitivity: str) -> str:
        mapping = {
            "low": "internal",
            "medium": "confidential",
            "high": "confidential",
            "critical": "secret",
        }
        return mapping.get(sensitivity, "internal")


class AccessControlChecker:
    def __init__(self):
        self.access_policies: Dict[str, Dict] = {}
        self.role_permissions: Dict[str, List[str]] = {}
        self.access_logs: List[Dict] = []

    def define_role(self, role_name: str, permissions: List[str]) -> None:
        self.role_permissions[role_name] = permissions

    def create_access_policy(
        self, resource: str, allowed_roles: List[str], conditions: Dict = None
    ) -> None:
        self.access_policies[resource] = {
            "allowed_roles": allowed_roles,
            "conditions": conditions or {},
            "created_at": datetime.utcnow().isoformat(),
        }

    def log_access(
        self,
        user_id: str,
        resource: str,
        action: str,
        granted: bool,
        reason: str = None,
    ) -> None:
        self.access_logs.append(
            {
                "user_id": user_id,
                "resource": resource,
                "action": action,
                "granted": granted,
                "reason": reason,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    def check_least_privilege(self) -> Dict[str, Any]:
        result = {"compliant": True, "violations": []}

        for role, permissions in self.role_permissions.items():
            wildcard_permissions = [p for p in permissions if "*" in p]
            if wildcard_permissions:
                result["compliant"] = False
                result["violations"].append(
                    {
                        "role": role,
                        "issue": f"Wildcard permissions found: {wildcard_permissions}",
                    }
                )

        return result

    def check_access_review(self, review_period_days: int = 90) -> Dict[str, Any]:
        result = {
            "review_needed": False,
            "stale_accesses": [],
        }

        cutoff_date = datetime.utcnow() - timedelta(days=review_period_days)

        user_last_access: Dict[str, datetime] = {}
        for log in self.access_logs:
            user_id = log["user_id"]
            access_time = datetime.fromisoformat(log["timestamp"])
            if user_id not in user_last_access or access_time > user_last_access[user_id]:
                user_last_access[user_id] = access_time

        for user_id, last_access in user_last_access.items():
            if last_access < cutoff_date:
                result["review_needed"] = True
                result["stale_accesses"].append(
                    {
                        "user_id": user_id,
                        "last_access": last_access.isoformat(),
                    }
                )

        return result

    def simulate_privilege_escalation(self, user_role: str, target_resource: str) -> Dict[str, Any]:
        result = {
            "vulnerable": False,
            "escalation_path": [],
        }

        if target_resource in self.access_policies:
            allowed_roles = self.access_policies[target_resource]["allowed_roles"]
            if user_role not in allowed_roles:
                result["escalation_path"] = [
                    f"User role '{user_role}' cannot directly access '{target_resource}'"
                ]
            else:
                result["vulnerable"] = True
                result["escalation_path"] = [
                    f"User role '{user_role}' already has access to '{target_resource}'"
                ]

        return result


class EncryptionChecker:
    def __init__(self):
        self.encryption_configs: Dict[str, Dict] = {}
        self.encrypted_resources: Dict[str, Dict] = {}

    def configure_encryption(
        self,
        resource: str,
        algorithm: str,
        key_length: int,
        key_management: str,
    ) -> None:
        self.encryption_configs[resource] = {
            "algorithm": algorithm,
            "key_length": key_length,
            "key_management": key_management,
            "configured_at": datetime.utcnow().isoformat(),
        }

    def register_encrypted_resource(
        self, resource: str, encryption_status: bool, details: Dict = None
    ) -> None:
        self.encrypted_resources[resource] = {
            "encrypted": encryption_status,
            "details": details or {},
            "checked_at": datetime.utcnow().isoformat(),
        }

    def check_encryption_strength(self) -> Dict[str, Any]:
        result = {"compliant": True, "weak_encryptions": []}

        min_key_lengths = {
            "AES": 128,
            "RSA": 2048,
            "DES": 0,
        }

        for resource, config in self.encryption_configs.items():
            algorithm = config["algorithm"].upper()
            key_length = config["key_length"]
            min_length = min_key_lengths.get(algorithm, 128)

            if key_length < min_length:
                result["compliant"] = False
                result["weak_encryptions"].append(
                    {
                        "resource": resource,
                        "algorithm": algorithm,
                        "key_length": key_length,
                        "minimum_required": min_length,
                    }
                )

        return result

    def check_encryption_coverage(self) -> Dict[str, Any]:
        result = {
            "total_resources": len(self.encrypted_resources),
            "encrypted_count": 0,
            "unencrypted_resources": [],
            "coverage_rate": 0.0,
        }

        for resource, status in self.encrypted_resources.items():
            if status["encrypted"]:
                result["encrypted_count"] += 1
            else:
                result["unencrypted_resources"].append(resource)

        if result["total_resources"] > 0:
            result["coverage_rate"] = result["encrypted_count"] / result["total_resources"]

        return result


class BackupRecoveryChecker:
    def __init__(self):
        self.backup_configs: Dict[str, Dict] = {}
        self.backup_records: List[Dict] = []
        self.recovery_tests: List[Dict] = []

    def configure_backup(
        self,
        resource: str,
        frequency: str,
        retention_days: int,
        location: str,
    ) -> None:
        self.backup_configs[resource] = {
            "frequency": frequency,
            "retention_days": retention_days,
            "location": location,
            "configured_at": datetime.utcnow().isoformat(),
        }

    def record_backup(
        self,
        resource: str,
        backup_id: str,
        size_bytes: int,
        success: bool,
    ) -> None:
        self.backup_records.append(
            {
                "resource": resource,
                "backup_id": backup_id,
                "size_bytes": size_bytes,
                "success": success,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    def record_recovery_test(
        self,
        resource: str,
        test_id: str,
        success: bool,
        recovery_time_seconds: int,
    ) -> None:
        self.recovery_tests.append(
            {
                "resource": resource,
                "test_id": test_id,
                "success": success,
                "recovery_time_seconds": recovery_time_seconds,
                "tested_at": datetime.utcnow().isoformat(),
            }
        )

    def check_backup_compliance(self) -> Dict[str, Any]:
        result = {
            "compliant": True,
            "issues": [],
            "backup_status": {},
        }

        for resource, config in self.backup_configs.items():
            recent_backups = [
                b
                for b in self.backup_records
                if b["resource"] == resource
                and datetime.fromisoformat(b["timestamp"])
                > datetime.utcnow() - timedelta(days=1)
            ]

            if not recent_backups:
                result["compliant"] = False
                result["issues"].append(f"No recent backup for {resource}")
                result["backup_status"][resource] = "missing"
            else:
                failed_backups = [b for b in recent_backups if not b["success"]]
                if failed_backups:
                    result["compliant"] = False
                    result["issues"].append(f"Failed backups for {resource}")
                    result["backup_status"][resource] = "failed"
                else:
                    result["backup_status"][resource] = "healthy"

        return result

    def check_recovery_capability(self) -> Dict[str, Any]:
        result = {
            "recovery_tested": True,
            "untested_resources": [],
            "last_tests": {},
        }

        for resource in self.backup_configs.keys():
            resource_tests = [
                t for t in self.recovery_tests if t["resource"] == resource
            ]

            if not resource_tests:
                result["recovery_tested"] = False
                result["untested_resources"].append(resource)
            else:
                last_test = max(resource_tests, key=lambda x: x["tested_at"])
                result["last_tests"][resource] = last_test

        return result


class IncidentResponseChecker:
    def __init__(self):
        self.incident_plan: Dict[str, Any] = {}
        self.incident_contacts: List[Dict] = []
        self.incident_history: List[Dict] = []

    def set_incident_plan(self, plan: Dict[str, Any]) -> None:
        self.incident_plan = {
            **plan,
            "updated_at": datetime.utcnow().isoformat(),
        }

    def add_incident_contact(
        self, name: str, role: str, contact_info: str, availability: str
    ) -> None:
        self.incident_contacts.append(
            {
                "name": name,
                "role": role,
                "contact_info": contact_info,
                "availability": availability,
            }
        )

    def record_incident(
        self,
        incident_id: str,
        incident_type: str,
        severity: str,
        response_time_minutes: int,
        resolution_time_hours: int,
    ) -> None:
        self.incident_history.append(
            {
                "incident_id": incident_id,
                "type": incident_type,
                "severity": severity,
                "response_time_minutes": response_time_minutes,
                "resolution_time_hours": resolution_time_hours,
                "recorded_at": datetime.utcnow().isoformat(),
            }
        )

    def check_incident_plan_exists(self) -> Dict[str, Any]:
        result = {
            "has_plan": bool(self.incident_plan),
            "plan_components": [],
            "missing_components": [],
        }

        required_components = [
            "escalation_procedure",
            "communication_plan",
            "containment_steps",
            "recovery_steps",
            "post_incident_review",
        ]

        for component in required_components:
            if component in self.incident_plan:
                result["plan_components"].append(component)
            else:
                result["missing_components"].append(component)

        return result

    def check_response_capability(self) -> Dict[str, Any]:
        result = {
            "has_contacts": len(self.incident_contacts) > 0,
            "contact_coverage": {},
            "issues": [],
        }

        required_roles = ["primary_responder", "escalation_contact", "executive_contact"]
        covered_roles = {c["role"] for c in self.incident_contacts}

        for role in required_roles:
            result["contact_coverage"][role] = role in covered_roles
            if role not in covered_roles:
                result["issues"].append(f"Missing contact for role: {role}")

        return result


class DataSecurityAuditAgent:
    def __init__(self, agent_id: str = "data_security_audit_001"):
        self.agent_id = agent_id
        self.classification_checker = DataClassificationChecker()
        self.access_checker = AccessControlChecker()
        self.encryption_checker = EncryptionChecker()
        self.backup_checker = BackupRecoveryChecker()
        self.incident_checker = IncidentResponseChecker()

        self.audit_history: List[SecurityAuditResult] = []
        self.check_templates: Dict[str, List[SecurityCheckItem]] = {}

        self._initialize_check_templates()

    def _initialize_check_templates(self) -> None:
        self.check_templates["data_classification"] = [
            SecurityCheckItem(
                item_id="dc_001",
                category=SecurityCheckCategory.DATA_CLASSIFICATION,
                requirement="应对数据进行分类分级标识",
                legal_reference="《数据安全法》第二十一条",
                check_method="检查数据分类分级制度和执行情况",
                severity=Severity.HIGH,
            ),
            SecurityCheckItem(
                item_id="dc_002",
                category=SecurityCheckCategory.DATA_CLASSIFICATION,
                requirement="应建立数据分类分级管理制度",
                legal_reference="《数据安全法》第二十一条",
                check_method="检查制度文件和执行记录",
                severity=Severity.MEDIUM,
            ),
        ]

        self.check_templates["access_control"] = [
            SecurityCheckItem(
                item_id="ac_001",
                category=SecurityCheckCategory.ACCESS_CONTROL,
                requirement="应实施严格的权限管理",
                legal_reference="《数据安全法》第二十七条",
                check_method="检查权限配置和访问日志",
                severity=Severity.HIGH,
            ),
            SecurityCheckItem(
                item_id="ac_002",
                category=SecurityCheckCategory.ACCESS_CONTROL,
                requirement="应遵循最小权限原则",
                legal_reference="《网络安全法》第二十一条",
                check_method="检查权限分配是否合理",
                severity=Severity.MEDIUM,
            ),
            SecurityCheckItem(
                item_id="ac_003",
                category=SecurityCheckCategory.ACCESS_CONTROL,
                requirement="应定期审查访问权限",
                legal_reference="《数据安全法》第二十七条",
                check_method="检查权限审查记录",
                severity=Severity.MEDIUM,
            ),
        ]

        self.check_templates["encryption"] = [
            SecurityCheckItem(
                item_id="en_001",
                category=SecurityCheckCategory.ENCRYPTION,
                requirement="敏感数据应加密存储",
                legal_reference="《数据安全法》第二十七条",
                check_method="检查加密配置和数据存储",
                severity=Severity.HIGH,
            ),
            SecurityCheckItem(
                item_id="en_002",
                category=SecurityCheckCategory.ENCRYPTION,
                requirement="应使用足够强度的加密算法",
                legal_reference="《网络安全法》第二十一条",
                check_method="检查加密算法和密钥长度",
                severity=Severity.HIGH,
            ),
        ]

        self.check_templates["transmission_security"] = [
            SecurityCheckItem(
                item_id="ts_001",
                category=SecurityCheckCategory.TRANSMISSION_SECURITY,
                requirement="数据传输应使用加密通道",
                legal_reference="《数据安全法》第二十七条",
                check_method="检查传输协议配置",
                severity=Severity.HIGH,
            ),
        ]

        self.check_templates["backup_recovery"] = [
            SecurityCheckItem(
                item_id="br_001",
                category=SecurityCheckCategory.BACKUP_RECOVERY,
                requirement="应建立数据备份机制",
                legal_reference="《数据安全法》第二十七条",
                check_method="检查备份配置和记录",
                severity=Severity.HIGH,
            ),
            SecurityCheckItem(
                item_id="br_002",
                category=SecurityCheckCategory.BACKUP_RECOVERY,
                requirement="应定期测试数据恢复能力",
                legal_reference="《网络安全法》第二十一条",
                check_method="检查恢复测试记录",
                severity=Severity.MEDIUM,
            ),
        ]

        self.check_templates["incident_response"] = [
            SecurityCheckItem(
                item_id="ir_001",
                category=SecurityCheckCategory.INCIDENT_RESPONSE,
                requirement="应制定安全事件应急预案",
                legal_reference="《数据安全法》第二十三条",
                check_method="检查预案文件",
                severity=Severity.HIGH,
            ),
            SecurityCheckItem(
                item_id="ir_002",
                category=SecurityCheckCategory.INCIDENT_RESPONSE,
                requirement="应建立应急响应团队",
                legal_reference="《数据安全法》第二十三条",
                check_method="检查响应团队配置",
                severity=Severity.MEDIUM,
            ),
        ]

    async def execute_check(
        self, check_item: SecurityCheckItem
    ) -> SecurityCheckItem:
        executed = SecurityCheckItem(
            item_id=check_item.item_id,
            category=check_item.category,
            requirement=check_item.requirement,
            legal_reference=check_item.legal_reference,
            check_method=check_item.check_method,
            severity=check_item.severity,
        )

        if check_item.category == SecurityCheckCategory.DATA_CLASSIFICATION:
            coverage = self.classification_checker.check_classification_coverage()
            alignment = self.classification_checker.check_sensitivity_alignment()

            if coverage["coverage_rate"] >= 0.9 and alignment["aligned"]:
                executed.status = ComplianceStatus.COMPLIANT
                executed.score = 100
                executed.evidence.append(f"分类覆盖率: {coverage['coverage_rate']:.1%}")
            elif coverage["coverage_rate"] >= 0.7:
                executed.status = ComplianceStatus.PARTIAL
                executed.score = coverage["coverage_rate"] * 100
                executed.findings.append(f"部分数据未分类: {coverage['unclassified_assets']}")
            else:
                executed.status = ComplianceStatus.NON_COMPLIANT
                executed.score = coverage["coverage_rate"] * 100
                executed.findings.append("数据分类覆盖率不足")
                executed.remediation = "建立数据分类分级制度，对所有数据资产进行分类标识"

        elif check_item.category == SecurityCheckCategory.ACCESS_CONTROL:
            least_privilege = self.access_checker.check_least_privilege()
            access_review = self.access_checker.check_access_review()

            if least_privilege["compliant"] and not access_review["review_needed"]:
                executed.status = ComplianceStatus.COMPLIANT
                executed.score = 100
                executed.evidence.append("权限配置符合最小权限原则")
            else:
                executed.status = ComplianceStatus.PARTIAL
                executed.score = 70
                if not least_privilege["compliant"]:
                    executed.findings.append(f"权限违规: {least_privilege['violations']}")
                if access_review["review_needed"]:
                    executed.findings.append(f"存在过期权限: {len(access_review['stale_accesses'])}个")
                executed.remediation = "审查并优化权限配置，清理过期权限"

        elif check_item.category == SecurityCheckCategory.ENCRYPTION:
            strength = self.encryption_checker.check_encryption_strength()
            coverage = self.encryption_checker.check_encryption_coverage()

            if strength["compliant"] and coverage["coverage_rate"] >= 0.9:
                executed.status = ComplianceStatus.COMPLIANT
                executed.score = 100
                executed.evidence.append(f"加密覆盖率: {coverage['coverage_rate']:.1%}")
            else:
                executed.status = ComplianceStatus.NON_COMPLIANT
                executed.score = coverage["coverage_rate"] * 50
                if not strength["compliant"]:
                    executed.findings.append(f"弱加密配置: {strength['weak_encryptions']}")
                if coverage["coverage_rate"] < 0.9:
                    executed.findings.append(f"未加密资源: {coverage['unencrypted_resources']}")
                executed.remediation = "升级加密算法，对所有敏感数据实施加密"

        elif check_item.category == SecurityCheckCategory.BACKUP_RECOVERY:
            backup_status = self.backup_checker.check_backup_compliance()
            recovery_status = self.backup_checker.check_recovery_capability()

            if backup_status["compliant"] and recovery_status["recovery_tested"]:
                executed.status = ComplianceStatus.COMPLIANT
                executed.score = 100
                executed.evidence.append("备份和恢复机制完善")
            else:
                executed.status = ComplianceStatus.PARTIAL
                executed.score = 60
                executed.findings.extend(backup_status["issues"])
                if not recovery_status["recovery_tested"]:
                    executed.findings.append(f"未测试恢复的资源: {recovery_status['untested_resources']}")
                executed.remediation = "完善备份策略，定期测试恢复能力"

        elif check_item.category == SecurityCheckCategory.INCIDENT_RESPONSE:
            plan_status = self.incident_checker.check_incident_plan_exists()
            capability = self.incident_checker.check_response_capability()

            if plan_status["has_plan"] and capability["has_contacts"]:
                executed.status = ComplianceStatus.COMPLIANT
                executed.score = 100
                executed.evidence.append("应急预案和响应团队配置完善")
            else:
                executed.status = ComplianceStatus.PARTIAL
                executed.score = 50
                if plan_status["missing_components"]:
                    executed.findings.append(f"预案缺失组件: {plan_status['missing_components']}")
                if capability["issues"]:
                    executed.findings.extend(capability["issues"])
                executed.remediation = "完善应急预案，配置应急响应团队"

        else:
            executed.status = ComplianceStatus.NOT_APPLICABLE
            executed.score = 0

        executed.checked_at = datetime.utcnow()
        return executed

    async def run_audit(
        self, categories: List[SecurityCheckCategory] = None
    ) -> SecurityAuditResult:
        audit_id = f"sec_audit_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}"

        if categories is None:
            categories = list(SecurityCheckCategory)

        all_checks = []
        for category in categories:
            category_name = category.value
            if category_name in self.check_templates:
                all_checks.extend(self.check_templates[category_name])

        executed_checks = []
        for check in all_checks:
            executed = await self.execute_check(check)
            executed_checks.append(executed)

        category_scores = {}
        for category in categories:
            category_checks = [
                c for c in executed_checks if c.category == category
            ]
            if category_checks:
                avg_score = sum(c.score for c in category_checks) / len(category_checks)
                category_scores[category.value] = round(avg_score, 2)

        overall_score = (
            sum(category_scores.values()) / len(category_scores)
            if category_scores
            else 0
        )

        if overall_score >= 90:
            overall_status = ComplianceStatus.COMPLIANT
        elif overall_score >= 70:
            overall_status = ComplianceStatus.PARTIAL
        else:
            overall_status = ComplianceStatus.NON_COMPLIANT

        critical_findings = [
            f"[{c.item_id}] {c.requirement}: {', '.join(c.findings)}"
            for c in executed_checks
            if c.status == ComplianceStatus.NON_COMPLIANT
            and c.severity in [Severity.HIGH, Severity.CRITICAL]
        ]

        recommendations = []
        for check in executed_checks:
            if check.remediation:
                recommendations.append(f"[{check.item_id}] {check.remediation}")

        compliance_gaps = [
            {
                "category": c.category.value,
                "requirement": c.requirement,
                "current_score": c.score,
                "target_score": 100,
                "gap": 100 - c.score,
                "priority": c.severity.value,
            }
            for c in executed_checks
            if c.status != ComplianceStatus.COMPLIANT
        ]

        result = SecurityAuditResult(
            audit_id=audit_id,
            audit_time=datetime.utcnow(),
            overall_score=round(overall_score, 2),
            overall_status=overall_status,
            category_scores=category_scores,
            check_items=executed_checks,
            critical_findings=critical_findings,
            recommendations=recommendations,
            compliance_gaps=compliance_gaps,
            next_audit_date=datetime.utcnow() + timedelta(days=90),
        )

        self.audit_history.append(result)
        return result

    def get_audit_history(self, limit: int = 10) -> List[SecurityAuditResult]:
        return self.audit_history[-limit:]

    def get_security_metrics(self) -> Dict[str, Any]:
        if not self.audit_history:
            return {"total_audits": 0, "average_score": 0}

        scores = [a.overall_score for a in self.audit_history]
        return {
            "total_audits": len(self.audit_history),
            "average_score": round(sum(scores) / len(scores), 2),
            "latest_score": scores[-1],
            "trend": "上升" if len(scores) >= 2 and scores[-1] > scores[-2] else "稳定",
        }
