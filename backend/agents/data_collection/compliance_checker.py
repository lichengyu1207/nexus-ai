"""
数据采集合规检查器
确保所有数据采集行为符合法律法规和伦理要求
"""
import asyncio
import json
import logging
import re
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ViolationSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ComplianceStatus(str, Enum):
    COMPLIANT = "compliant"
    WARNING = "warning"
    VIOLATION = "violation"
    BLOCKED = "blocked"


class ComplianceRule(BaseModel):
    rule_id: str
    name: str
    description: str
    rule_type: str
    pattern: Optional[str] = None
    check_function: Optional[str] = None
    severity: ViolationSeverity = ViolationSeverity.MEDIUM
    enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.now)


class ViolationRecord(BaseModel):
    violation_id: str = Field(default_factory=lambda: str(uuid4()))
    rule_id: str
    agent_id: str
    severity: ViolationSeverity
    description: str
    context: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolution_note: Optional[str] = None


class ComplianceCheckResult(BaseModel):
    check_id: str = Field(default_factory=lambda: str(uuid4()))
    status: ComplianceStatus
    violations: List[ViolationRecord] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    checked_at: datetime = Field(default_factory=datetime.now)


class PrivacyDataPattern:
    PATTERNS = {
        "id_card_cn": (r'\b\d{17}[\dXx]\b', "Chinese ID Card"),
        "phone_cn": (r'\b1[3-9]\d{9}\b', "Chinese Phone Number"),
        "email": (r'\b[\w\.-]+@[\w\.-]+\.\w+\b', "Email Address"),
        "credit_card": (r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', "Credit Card"),
        "passport": (r'\b[A-Z]{1,2}\d{6,9}\b', "Passport Number"),
        "bank_account": (r'\b\d{16,19}\b', "Bank Account"),
        "address_cn": (r'[\u4e00-\u9fa5]+省[\u4e00-\u9fa5]+市[\u4e00-\u9fa5]+区', "Chinese Address"),
    }


class RobotsTxtChecker:
    def __init__(self):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl = timedelta(hours=24)
    
    async def check_allowed(self, url: str, user_agent: str = "*") -> bool:
        from urllib.parse import urlparse
        
        parsed = urlparse(url)
        domain = parsed.netloc
        path = parsed.path
        
        if domain not in self.cache:
            await self._fetch_robots_txt(domain)
        
        robots_rules = self.cache.get(domain, {}).get("rules", {})
        
        disallowed_paths = robots_rules.get(user_agent, {}).get("disallow", [])
        disallowed_paths.extend(robots_rules.get("*", {}).get("disallow", []))
        
        for disallowed in disallowed_paths:
            if disallowed and path.startswith(disallowed):
                return False
        
        return True
    
    async def _fetch_robots_txt(self, domain: str):
        self.cache[domain] = {
            "rules": {
                "*": {"disallow": ["/admin", "/private", "/api/internal"]},
            },
            "fetched_at": datetime.now()
        }
    
    def get_crawl_delay(self, domain: str, user_agent: str = "*") -> int:
        rules = self.cache.get(domain, {}).get("rules", {})
        delay = rules.get(user_agent, {}).get("crawl-delay")
        if delay is None:
            delay = rules.get("*", {}).get("crawl-delay", 1)
        return delay


class CopyrightChecker:
    def __init__(self):
        self.authorized_sources: Set[str] = set()
        self.copyrighted_patterns: List[str] = [
            r"版权所有",
            r"©\s*\d{4}",
            r"Copyright",
            r"All Rights Reserved",
            r"未经授权禁止转载"
        ]
    
    def authorize_source(self, source_id: str):
        self.authorized_sources.add(source_id)
    
    def check_content(self, content: str, source_id: Optional[str] = None) -> ComplianceCheckResult:
        violations = []
        warnings = []
        
        if source_id and source_id in self.authorized_sources:
            return ComplianceCheckResult(status=ComplianceStatus.COMPLIANT)
        
        for pattern in self.copyrighted_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                warnings.append(f"Potential copyright notice found: {pattern}")
        
        if warnings:
            return ComplianceCheckResult(
                status=ComplianceStatus.WARNING,
                warnings=warnings
            )
        
        return ComplianceCheckResult(status=ComplianceStatus.COMPLIANT)


class DataCollectionComplianceChecker:
    DEFAULT_RULES = [
        {
            "rule_id": "no_pii_collection",
            "name": "No PII Collection",
            "description": "Do not collect personally identifiable information without consent",
            "rule_type": "content_check",
            "severity": "critical"
        },
        {
            "rule_id": "respect_robots_txt",
            "name": "Respect Robots.txt",
            "description": "Must respect website robots.txt directives",
            "rule_type": "source_check",
            "severity": "high"
        },
        {
            "rule_id": "no_copyright_violation",
            "name": "No Copyright Violation",
            "description": "Do not collect copyrighted content without authorization",
            "rule_type": "content_check",
            "severity": "high"
        },
        {
            "rule_id": "rate_limiting",
            "name": "Rate Limiting",
            "description": "Must not overwhelm target servers",
            "rule_type": "behavior_check",
            "severity": "medium"
        },
        {
            "rule_id": "no_sensitive_data",
            "name": "No Sensitive Data",
            "description": "Do not collect sensitive personal data",
            "rule_type": "content_check",
            "severity": "critical"
        }
    ]
    
    def __init__(
        self,
        energy_manager: Optional[Any] = None,
        rule_update_callback: Optional[callable] = None
    ):
        self.energy_manager = energy_manager
        self.rule_update_callback = rule_update_callback
        
        self.rules: Dict[str, ComplianceRule] = {}
        self._load_default_rules()
        
        self.robots_checker = RobotsTxtChecker()
        self.copyright_checker = CopyrightChecker()
        
        self.violation_history: List[ViolationRecord] = []
        self.agent_violation_counts: Dict[str, int] = {}
        
        self.max_violations_before_penalty = 3
        self.severe_penalty_threshold = 1
        
        self.logger = logging.getLogger(__name__)
    
    def _load_default_rules(self):
        for rule_data in self.DEFAULT_RULES:
            rule = ComplianceRule(**rule_data)
            self.rules[rule.rule_id] = rule
    
    async def check_collection(
        self,
        agent_id: str,
        source_config: Dict[str, Any],
        content: Optional[str] = None
    ) -> ComplianceCheckResult:
        violations = []
        warnings = []
        
        source_type = source_config.get("type", "unknown")
        source_url = source_config.get("url", "")
        
        if source_type == "web" and source_url:
            allowed = await self.robots_checker.check_allowed(source_url)
            if not allowed:
                violation = ViolationRecord(
                    rule_id="respect_robots_txt",
                    agent_id=agent_id,
                    severity=ViolationSeverity.HIGH,
                    description=f"URL not allowed by robots.txt: {source_url}",
                    context={"url": source_url}
                )
                violations.append(violation)
        
        if content:
            pii_violations = self._check_pii(content, agent_id)
            violations.extend(pii_violations)
            
            sensitive_violations = self._check_sensitive_data(content, agent_id)
            violations.extend(sensitive_violations)
            
            copyright_result = self.copyright_checker.check_content(content)
            if copyright_result.status == ComplianceStatus.WARNING:
                warnings.extend(copyright_result.warnings)
        
        status = ComplianceStatus.COMPLIANT
        if violations:
            critical = any(v.severity == ViolationSeverity.CRITICAL for v in violations)
            if critical:
                status = ComplianceStatus.BLOCKED
            else:
                status = ComplianceStatus.VIOLATION
        elif warnings:
            status = ComplianceStatus.WARNING
        
        result = ComplianceCheckResult(
            status=status,
            violations=violations,
            warnings=warnings
        )
        
        if violations:
            await self._handle_violations(agent_id, violations)
        
        return result
    
    def _check_pii(self, content: str, agent_id: str) -> List[ViolationRecord]:
        violations = []
        
        for pattern_name, (pattern, description) in PrivacyDataPattern.PATTERNS.items():
            matches = re.findall(pattern, content)
            if matches:
                violation = ViolationRecord(
                    rule_id="no_pii_collection",
                    agent_id=agent_id,
                    severity=ViolationSeverity.CRITICAL,
                    description=f"Found {description}: {len(matches)} matches",
                    context={
                        "pattern_type": pattern_name,
                        "match_count": len(matches)
                    }
                )
                violations.append(violation)
        
        return violations
    
    def _check_sensitive_data(self, content: str, agent_id: str) -> List[ViolationRecord]:
        sensitive_keywords = [
            "密码", "password", "secret", "token", "api_key",
            "私钥", "private_key", "银行卡", "credit_card"
        ]
        
        violations = []
        content_lower = content.lower()
        
        for keyword in sensitive_keywords:
            if keyword in content_lower:
                violation = ViolationRecord(
                    rule_id="no_sensitive_data",
                    agent_id=agent_id,
                    severity=ViolationSeverity.CRITICAL,
                    description=f"Found sensitive keyword: {keyword}",
                    context={"keyword": keyword}
                )
                violations.append(violation)
                break
        
        return violations
    
    async def _handle_violations(
        self,
        agent_id: str,
        violations: List[ViolationRecord]
    ):
        self.violation_history.extend(violations)
        
        if agent_id not in self.agent_violation_counts:
            self.agent_violation_counts[agent_id] = 0
        self.agent_violation_counts[agent_id] += len(violations)
        
        for violation in violations:
            self.logger.warning(
                f"Compliance violation by {agent_id}: "
                f"{violation.rule_id} - {violation.description}"
            )
        
        if self.energy_manager:
            await self._apply_penalty(agent_id, violations)
    
    async def _apply_penalty(
        self,
        agent_id: str,
        violations: List[ViolationRecord]
    ):
        total_penalty = 0.0
        
        for violation in violations:
            penalty_map = {
                ViolationSeverity.LOW: 10,
                ViolationSeverity.MEDIUM: 50,
                ViolationSeverity.HIGH: 100,
                ViolationSeverity.CRITICAL: 500
            }
            total_penalty += penalty_map.get(violation.severity, 10)
        
        violation_count = self.agent_violation_counts.get(agent_id, 0)
        if violation_count > self.max_violations_before_penalty:
            total_penalty *= (1 + (violation_count - self.max_violations_before_penalty) * 0.5)
        
        await self.energy_manager.consume(
            agent_id,
            total_penalty,
            "compliance_violation_penalty"
        )
        
        self.logger.warning(
            f"Applied penalty of {total_penalty} energy to {agent_id} "
            f"for {len(violations)} violations"
        )
    
    def add_rule(self, rule: ComplianceRule):
        self.rules[rule.rule_id] = rule
        self.logger.info(f"Added compliance rule: {rule.name}")
    
    def update_rule(self, rule_id: str, updates: Dict[str, Any]) -> bool:
        if rule_id not in self.rules:
            return False
        
        rule = self.rules[rule_id]
        for key, value in updates.items():
            if hasattr(rule, key):
                setattr(rule, key, value)
        
        self.logger.info(f"Updated compliance rule: {rule_id}")
        return True
    
    def remove_rule(self, rule_id: str) -> bool:
        if rule_id in self.rules:
            del self.rules[rule_id]
            self.logger.info(f"Removed compliance rule: {rule_id}")
            return True
        return False
    
    async def resolve_violation(
        self,
        violation_id: str,
        resolution_note: str
    ) -> bool:
        for violation in self.violation_history:
            if violation.violation_id == violation_id:
                violation.resolved = True
                violation.resolved_at = datetime.now()
                violation.resolution_note = resolution_note
                return True
        return False
    
    def get_robots_checker(self) -> RobotsTxtChecker:
        return self.robots_checker
    
    def authorize_source(self, source_id: str):
        self.copyright_checker.authorize_source(source_id)
    
    def get_statistics(self) -> Dict[str, Any]:
        unresolved = [v for v in self.violation_history if not v.resolved]
        
        by_severity = {}
        for severity in ViolationSeverity:
            by_severity[severity.value] = len([
                v for v in self.violation_history if v.severity == severity
            ])
        
        by_rule = {}
        for rule_id in self.rules:
            by_rule[rule_id] = len([
                v for v in self.violation_history if v.rule_id == rule_id
            ])
        
        return {
            "total_rules": len(self.rules),
            "enabled_rules": len([r for r in self.rules.values() if r.enabled]),
            "total_violations": len(self.violation_history),
            "unresolved_violations": len(unresolved),
            "violations_by_severity": by_severity,
            "violations_by_rule": by_rule,
            "agents_with_violations": len(self.agent_violation_counts)
        }
    
    def get_violation_history(
        self,
        agent_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        violations = self.violation_history
        
        if agent_id:
            violations = [v for v in violations if v.agent_id == agent_id]
        
        return [
            {
                "violation_id": v.violation_id,
                "rule_id": v.rule_id,
                "agent_id": v.agent_id,
                "severity": v.severity.value,
                "description": v.description,
                "timestamp": v.timestamp.isoformat(),
                "resolved": v.resolved
            }
            for v in violations[-limit:]
        ]
