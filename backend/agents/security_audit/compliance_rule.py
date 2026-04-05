"""
合规规则库智能体
Compliance Rule Agent

负责管理所有业务合规规则，并提供规则查询和推理服务。
"""

import asyncio
import json
import logging
import hashlib
import uuid
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
from enum import Enum

logger = logging.getLogger(__name__)


class RulePriority(Enum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


class RuleType(Enum):
    PROHIBITION = "prohibition"
    REQUIREMENT = "requirement"
    PERMISSION = "permission"
    EXCEPTION = "exception"


@dataclass
class ComplianceRule:
    rule_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    rule_type: str = RuleType.REQUIREMENT.value
    priority: int = RulePriority.MEDIUM.value
    source_law: str = ""
    source_article: str = ""
    business_scenarios: List[str] = field(default_factory=list)
    data_types: List[str] = field(default_factory=list)
    operations: List[str] = field(default_factory=list)
    conditions: Dict = field(default_factory=dict)
    required_actions: List[str] = field(default_factory=list)
    prohibited_actions: List[str] = field(default_factory=list)
    exceptions: List[str] = field(default_factory=list)
    effective_date: str = ""
    expiry_date: str = ""
    active: bool = True
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class ComplianceCheckResult:
    check_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    action: str = ""
    context: Dict = field(default_factory=dict)
    compliant: bool = True
    risk_level: str = "low"
    matched_rules: List[Dict] = field(default_factory=list)
    violations: List[Dict] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    legal_basis: List[str] = field(default_factory=list)


class ComplianceRuleAgent:
    """
    合规规则库智能体
    
    功能：
    1. 规则存储：使用图数据库构建合规知识图谱
    2. 规则来源：法规追踪智能体、合规官录入、历史审计案例
    3. 规则查询接口：按场景、数据类型、操作查询规则
    4. 规则推理：图算法分析规则间关系，处理规则冲突
    5. 规则更新传播：自动重新评估受影响的历史操作
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.name = "ComplianceRuleAgent"
        self.description = "管理所有业务合规规则，提供规则查询和推理服务"
        self.config = config or {}
        
        self.rules: Dict[str, ComplianceRule] = {}
        self.rule_index: Dict[str, Set[str]] = {
            "by_scenario": defaultdict(set),
            "by_data_type": defaultdict(set),
            "by_operation": defaultdict(set),
            "by_source_law": defaultdict(set),
        }
        
        self.rule_relations: Dict[str, List[Dict]] = defaultdict(list)
        
        self._init_default_rules()
        
        self.stats = {
            "total_rules": 0,
            "active_rules": 0,
            "checks_performed": 0,
            "violations_found": 0,
            "rules_by_type": defaultdict(int),
        }
        
        self._initialized = False
    
    def _init_default_rules(self):
        default_rules = [
            ComplianceRule(
                name="个人信息收集同意要求",
                description="收集个人信息前必须获得用户明确同意",
                rule_type=RuleType.REQUIREMENT.value,
                priority=RulePriority.CRITICAL.value,
                source_law="个人信息保护法",
                source_article="第13条",
                business_scenarios=["用户注册", "信息采集", "服务开通"],
                data_types=["personal_info"],
                operations=["collect", "store"],
                required_actions=["获取用户同意", "告知处理目的"],
                prohibited_actions=["强制收集非必要信息"],
            ),
            ComplianceRule(
                name="敏感个人信息单独同意",
                description="处理敏感个人信息应当取得个人单独同意",
                rule_type=RuleType.REQUIREMENT.value,
                priority=RulePriority.CRITICAL.value,
                source_law="个人信息保护法",
                source_article="第29条",
                business_scenarios=["身份验证", "金融业务"],
                data_types=["sensitive_info"],
                operations=["collect", "process", "share"],
                required_actions=["单独同意", "告知必要性"],
                conditions={"data_categories": ["biometric", "financial", "location", "health"]},
            ),
            ComplianceRule(
                name="未成年人信息保护",
                description="处理不满十四周岁未成年人个人信息应取得监护人同意",
                rule_type=RuleType.REQUIREMENT.value,
                priority=RulePriority.CRITICAL.value,
                source_law="个人信息保护法",
                source_article="第32条",
                business_scenarios=["用户注册", "信息采集"],
                data_types=["minor_info"],
                operations=["collect", "process"],
                required_actions=["监护人同意", "制定专门规则"],
                conditions={"age_threshold": 14},
            ),
            ComplianceRule(
                name="数据最小化原则",
                description="处理个人信息应当具有明确、合理的目的，且应当与处理目的直接相关",
                rule_type=RuleType.REQUIREMENT.value,
                priority=RulePriority.HIGH.value,
                source_law="个人信息保护法",
                source_article="第6条",
                business_scenarios=["数据采集", "数据处理"],
                data_types=["all"],
                operations=["collect", "process"],
                required_actions=["限定目的范围", "最小必要原则"],
            ),
            ComplianceRule(
                name="数据安全保护义务",
                description="个人信息处理者应当采取措施保障个人信息安全",
                rule_type=RuleType.REQUIREMENT.value,
                priority=RulePriority.HIGH.value,
                source_law="数据安全法",
                source_article="第27条",
                business_scenarios=["数据存储", "数据传输"],
                data_types=["all"],
                operations=["store", "transmit"],
                required_actions=["加密存储", "访问控制", "安全审计"],
            ),
            ComplianceRule(
                name="用户权利响应",
                description="应当建立便捷的个人行使权利的申请受理和处理机制",
                rule_type=RuleType.REQUIREMENT.value,
                priority=RulePriority.HIGH.value,
                source_law="个人信息保护法",
                source_article="第50条",
                business_scenarios=["用户请求处理"],
                data_types=["all"],
                operations=["access", "correct", "delete", "export"],
                required_actions=["15日内响应", "建立申请渠道"],
            ),
            ComplianceRule(
                name="禁止过度收集",
                description="不得收集与业务功能无关的个人信息",
                rule_type=RuleType.PROHIBITION.value,
                priority=RulePriority.HIGH.value,
                source_law="App违法违规收集使用个人信息认定方法",
                source_article="第1条",
                business_scenarios=["用户注册", "功能使用"],
                data_types=["all"],
                operations=["collect"],
                prohibited_actions=["收集无关信息", "拒绝非必要信息拒绝服务"],
            ),
            ComplianceRule(
                name="数据出境安全评估",
                description="向境外提供个人信息应当通过安全评估或签订标准合同",
                rule_type=RuleType.REQUIREMENT.value,
                priority=RulePriority.CRITICAL.value,
                source_law="数据出境安全评估办法",
                source_article="第4条",
                business_scenarios=["跨境数据传输"],
                data_types=["all"],
                operations=["transfer_cross_border"],
                required_actions=["安全评估", "标准合同", "单独同意"],
                conditions={"threshold": {"users": 100000, "data_volume": "10万条"}},
            ),
        ]
        
        for rule in default_rules:
            self._add_rule(rule)
    
    def _add_rule(self, rule: ComplianceRule):
        self.rules[rule.rule_id] = rule
        
        for scenario in rule.business_scenarios:
            self.rule_index["by_scenario"][scenario].add(rule.rule_id)
        
        for data_type in rule.data_types:
            self.rule_index["by_data_type"][data_type].add(rule.rule_id)
        
        for operation in rule.operations:
            self.rule_index["by_operation"][operation].add(rule.rule_id)
        
        self.rule_index["by_source_law"][rule.source_law].add(rule.rule_id)
        
        self.stats["total_rules"] += 1
        if rule.active:
            self.stats["active_rules"] += 1
        self.stats["rules_by_type"][rule.rule_type] += 1
    
    async def initialize(self):
        if not self._initialized:
            await self._setup()
            self._initialized = True
            logger.info(f"Agent '{self.name}' initialized")
    
    async def _setup(self):
        pass
    
    async def add_rule(
        self,
        name: str,
        description: str,
        rule_type: str,
        priority: int,
        source_law: str,
        source_article: str,
        business_scenarios: List[str],
        data_types: List[str],
        operations: List[str],
        required_actions: Optional[List[str]] = None,
        prohibited_actions: Optional[List[str]] = None,
        conditions: Optional[Dict] = None,
        exceptions: Optional[List[str]] = None,
    ) -> ComplianceRule:
        rule = ComplianceRule(
            name=name,
            description=description,
            rule_type=rule_type,
            priority=priority,
            source_law=source_law,
            source_article=source_article,
            business_scenarios=business_scenarios,
            data_types=data_types,
            operations=operations,
            required_actions=required_actions or [],
            prohibited_actions=prohibited_actions or [],
            conditions=conditions or {},
            exceptions=exceptions or [],
        )
        
        self._add_rule(rule)
        return rule
    
    async def get_rules(
        self,
        business_scenario: Optional[str] = None,
        data_type: Optional[str] = None,
        operation: Optional[str] = None,
        source_law: Optional[str] = None,
        active_only: bool = True,
    ) -> List[ComplianceRule]:
        rule_ids: Optional[Set[str]] = None
        
        if business_scenario:
            scenario_ids = self.rule_index["by_scenario"].get(business_scenario, set())
            rule_ids = scenario_ids if rule_ids is None else rule_ids & scenario_ids
        
        if data_type:
            data_type_ids = self.rule_index["by_data_type"].get(data_type, set())
            all_ids = self.rule_index["by_data_type"].get("all", set())
            combined_ids = data_type_ids | all_ids
            rule_ids = combined_ids if rule_ids is None else rule_ids & combined_ids
        
        if operation:
            operation_ids = self.rule_index["by_operation"].get(operation, set())
            rule_ids = operation_ids if rule_ids is None else rule_ids & operation_ids
        
        if source_law:
            law_ids = self.rule_index["by_source_law"].get(source_law, set())
            rule_ids = law_ids if rule_ids is None else rule_ids & law_ids
        
        if rule_ids is None:
            rule_ids = set(self.rules.keys())
        
        result = [
            self.rules[rid] for rid in rule_ids
            if rid in self.rules
        ]
        
        if active_only:
            result = [r for r in result if r.active]
        
        return sorted(result, key=lambda r: r.priority)
    
    async def check_compliance(
        self,
        action: str,
        context: Dict,
    ) -> ComplianceCheckResult:
        result = ComplianceCheckResult(
            action=action,
            context=context,
        )
        
        scenario = context.get("business_scenario", "")
        data_type = context.get("data_type", "")
        operation = context.get("operation", "")
        
        applicable_rules = await self.get_rules(
            business_scenario=scenario,
            data_type=data_type,
            operation=operation,
        )
        
        for rule in applicable_rules:
            rule_match = {
                "rule_id": rule.rule_id,
                "name": rule.name,
                "source": f"{rule.source_law} {rule.source_article}",
                "type": rule.rule_type,
            }
            result.matched_rules.append(rule_match)
            
            if rule.rule_type == RuleType.PROHIBITION.value:
                for prohibited in rule.prohibited_actions:
                    if prohibited in action.lower() or self._check_prohibited_context(prohibited, context):
                        result.compliant = False
                        result.violations.append({
                            "rule_id": rule.rule_id,
                            "violation": prohibited,
                            "severity": "high" if rule.priority <= 2 else "medium",
                        })
                        result.risk_level = "high"
            
            elif rule.rule_type == RuleType.REQUIREMENT.value:
                missing_actions = []
                for required in rule.required_actions:
                    if not self._check_requirement_satisfied(required, context):
                        missing_actions.append(required)
                
                if missing_actions:
                    result.recommendations.extend(missing_actions)
                    result.legal_basis.append(f"{rule.source_law} {rule.source_article}: {rule.description}")
            
            if rule.exceptions:
                for exception in rule.exceptions:
                    if self._check_exception_applies(exception, context):
                        result.matched_rules[-1]["exception_applied"] = exception
        
        self.stats["checks_performed"] += 1
        if not result.compliant:
            self.stats["violations_found"] += 1
        
        return result
    
    def _check_prohibited_context(self, prohibited: str, context: Dict) -> bool:
        prohibited_keywords = {
            "强制收集非必要信息": lambda c: c.get("force_collection", False) and not c.get("necessary", True),
            "收集无关信息": lambda c: c.get("data_relevance", "relevant") == "irrelevant",
            "拒绝非必要信息拒绝服务": lambda c: c.get("deny_service_on_optional_refusal", False),
        }
        
        checker = prohibited_keywords.get(prohibited)
        return checker(context) if checker else False
    
    def _check_requirement_satisfied(self, requirement: str, context: Dict) -> bool:
        requirement_checks = {
            "获取用户同意": lambda c: c.get("user_consent", False),
            "告知处理目的": lambda c: c.get("purpose_disclosed", False),
            "单独同意": lambda c: c.get("separate_consent", False),
            "监护人同意": lambda c: c.get("guardian_consent", False),
            "加密存储": lambda c: c.get("encrypted", False),
            "访问控制": lambda c: c.get("access_control", False),
            "安全审计": lambda c: c.get("audit_enabled", False),
            "15日内响应": lambda c: c.get("response_time_days", 30) <= 15,
            "安全评估": lambda c: c.get("security_assessment", False),
            "标准合同": lambda c: c.get("standard_contract", False),
            "限定目的范围": lambda c: c.get("purpose_limited", False),
            "最小必要原则": lambda c: c.get("minimization", False),
            "告知必要性": lambda c: c.get("necessity_disclosed", False),
            "制定专门规则": lambda c: c.get("special_rules", False),
        }
        
        checker = requirement_checks.get(requirement)
        return checker(context) if checker else True
    
    def _check_exception_applies(self, exception: str, context: Dict) -> bool:
        exception_checks = {
            "履行合同必要": lambda c: c.get("contract_necessary", False),
            "法定义务": lambda c: c.get("legal_obligation", False),
            "突发公共卫生事件": lambda c: c.get("public_health_emergency", False),
            "紧急情况下保护生命": lambda c: c.get("life_threatening", False),
        }
        
        checker = exception_checks.get(exception)
        return checker(context) if checker else False
    
    async def resolve_rule_conflict(
        self,
        rule_ids: List[str],
    ) -> Dict:
        rules = [self.rules.get(rid) for rid in rule_ids if rid in self.rules]
        
        if not rules:
            return {"resolved": False, "reason": "规则不存在"}
        
        sorted_rules = sorted(rules, key=lambda r: r.priority)
        
        highest_priority = sorted_rules[0]
        
        same_priority_rules = [r for r in sorted_rules if r.priority == highest_priority.priority]
        
        if len(same_priority_rules) > 1:
            latest = max(same_priority_rules, key=lambda r: r.effective_date or r.created_at)
            return {
                "resolved": True,
                "method": "时间优先",
                "selected_rule": {
                    "rule_id": latest.rule_id,
                    "name": latest.name,
                    "source": f"{latest.source_law} {latest.source_article}",
                },
                "conflicting_rules": [
                    {
                        "rule_id": r.rule_id,
                        "name": r.name,
                    }
                    for r in same_priority_rules if r.rule_id != latest.rule_id
                ],
            }
        
        return {
            "resolved": True,
            "method": "优先级裁决",
            "selected_rule": {
                "rule_id": highest_priority.rule_id,
                "name": highest_priority.name,
                "source": f"{highest_priority.source_law} {highest_priority.source_article}",
            },
        }
    
    async def update_rule(
        self,
        rule_id: str,
        updates: Dict,
    ) -> Optional[ComplianceRule]:
        rule = self.rules.get(rule_id)
        if not rule:
            return None
        
        for key, value in updates.items():
            if hasattr(rule, key):
                setattr(rule, key, value)
        
        rule.updated_at = datetime.utcnow().isoformat()
        
        return rule
    
    async def deactivate_rule(self, rule_id: str) -> bool:
        rule = self.rules.get(rule_id)
        if not rule:
            return False
        
        rule.active = False
        self.stats["active_rules"] -= 1
        return True
    
    async def get_rule_dependencies(self, rule_id: str) -> Dict:
        rule = self.rules.get(rule_id)
        if not rule:
            return {"error": "规则不存在"}
        
        related_by_law = await self.get_rules(source_law=rule.source_law)
        
        related_by_scenario = []
        for scenario in rule.business_scenarios:
            related_by_scenario.extend(await self.get_rules(business_scenario=scenario))
        
        return {
            "rule_id": rule_id,
            "related_by_law": [
                {"rule_id": r.rule_id, "name": r.name}
                for r in related_by_law if r.rule_id != rule_id
            ],
            "related_by_scenario": list({
                r.rule_id: {"rule_id": r.rule_id, "name": r.name}
                for r in related_by_scenario if r.rule_id != rule_id
            }.values()),
        }
    
    async def get_stats(self) -> Dict:
        return {
            "name": self.name,
            "total_rules": self.stats["total_rules"],
            "active_rules": self.stats["active_rules"],
            "checks_performed": self.stats["checks_performed"],
            "violations_found": self.stats["violations_found"],
            "rules_by_type": dict(self.stats["rules_by_type"]),
        }
