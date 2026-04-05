"""
反击边界控制器
Counter Strike Boundary

确保所有反击行动在法律和伦理范围内
"""

import asyncio
import time
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from collections import defaultdict, deque
import structlog

logger = structlog.get_logger()


class RuleType(Enum):
    FORBIDDEN = "forbidden"
    RESTRICTED = "restricted"
    ALLOWED = "allowed"
    CONDITIONAL = "conditional"


class ViolationSeverity(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class BoundaryRule:
    rule_id: str
    rule_type: RuleType
    name: str
    description: str
    conditions: Dict[str, Any]
    actions: List[str]
    created_at: datetime
    active: bool
    
    def to_dict(self) -> Dict:
        return {
            "rule_id": self.rule_id,
            "rule_type": self.rule_type.value,
            "name": self.name,
            "description": self.description,
            "conditions": self.conditions,
            "actions": self.actions,
            "created_at": self.created_at.isoformat(),
            "active": self.active
        }


class CounterStrikeBoundary:
    def __init__(
        self,
        boundary_id: str = "boundary_001",
        communication_bus: Optional[Any] = None
    ):
        self.boundary_id = boundary_id
        self.communication_bus = communication_bus
        
        self.rules: Dict[str, BoundaryRule] = {}
        self.violation_history: deque = deque(maxlen=500)
        self.action_audit: deque = deque(maxlen=1000)
        
        self._load_default_rules()
        
        self.stats = {
            "total_checks": 0,
            "actions_allowed": 0,
            "actions_blocked": 0,
            "violations_detected": 0
        }
        
    def _load_default_rules(self):
        default_rules = [
            {
                "rule_type": RuleType.FORBIDDEN,
                "name": "禁止破坏性反击",
                "description": "不得实施破坏性反击（如DDoS反击）",
                "conditions": {"action_type": ["ddos", "destructive"]},
                "actions": ["block"]
            },
            {
                "rule_type": RuleType.FORBIDDEN,
                "name": "禁止攻击第三方",
                "description": "不得攻击无关第三方",
                "conditions": {"target_type": "third_party"},
                "actions": ["block"]
            },
            {
                "rule_type": RuleType.FORBIDDEN,
                "name": "禁止侵犯隐私",
                "description": "不得侵犯用户隐私",
                "conditions": {"involves_pii": True, "consent": False},
                "actions": ["block"]
            },
            {
                "rule_type": RuleType.RESTRICTED,
                "name": "限制反击范围",
                "description": "反击仅限于确认的攻击源",
                "conditions": {"attribution_confidence": {"min": 0.7}},
                "actions": ["require_approval"]
            },
            {
                "rule_type": RuleType.ALLOWED,
                "name": "允许限流反击",
                "description": "允许对攻击IP实施限流",
                "conditions": {"action_type": "rate_limit"},
                "actions": ["allow"]
            },
            {
                "rule_type": RuleType.ALLOWED,
                "name": "允许发送警示",
                "description": "允许发送警示信息",
                "conditions": {"action_type": "warning"},
                "actions": ["allow"]
            },
            {
                "rule_type": RuleType.ALLOWED,
                "name": "允许通知上游",
                "description": "允许通知上游ISP",
                "conditions": {"action_type": "upstream_notification"},
                "actions": ["allow"]
            },
            {
                "rule_type": RuleType.CONDITIONAL,
                "name": "条件性蜜罐部署",
                "description": "在确认攻击后可部署蜜罐",
                "conditions": {
                    "action_type": "honeypot",
                    "attack_confirmed": True
                },
                "actions": ["allow_with_logging"]
            }
        ]
        
        for rule_data in default_rules:
            rule = BoundaryRule(
                rule_id=self._generate_rule_id(),
                rule_type=rule_data["rule_type"],
                name=rule_data["name"],
                description=rule_data["description"],
                conditions=rule_data["conditions"],
                actions=rule_data["actions"],
                created_at=datetime.now(),
                active=True
            )
            self.rules[rule.rule_id] = rule
            
    async def check_action_allowed(self, action: Any) -> bool:
        self.stats["total_checks"] += 1
        
        action_dict = action.to_dict() if hasattr(action, 'to_dict') else action
        
        action_type = action_dict.get("action_type", "unknown")
        target_ip = action_dict.get("target_ip", "")
        target_identity = action_dict.get("target_identity", "")
        
        for rule in self.rules.values():
            if not rule.active:
                continue
                
            match = self._check_rule_match(rule, action_dict)
            
            if match:
                if rule.rule_type == RuleType.FORBIDDEN:
                    self._record_violation(action_dict, rule, ViolationSeverity.HIGH)
                    self.stats["actions_blocked"] += 1
                    return False
                    
                elif rule.rule_type == RuleType.RESTRICTED:
                    if "require_approval" in rule.actions:
                        if not action_dict.get("approved", False):
                            self._record_violation(action_dict, rule, ViolationSeverity.MEDIUM)
                            return False
                            
                elif rule.rule_type == RuleType.CONDITIONAL:
                    if not self._check_conditions(rule.conditions, action_dict):
                        self.stats["actions_blocked"] += 1
                        return False
                        
        self._audit_action(action_dict, allowed=True)
        self.stats["actions_allowed"] += 1
        
        return True
        
    def _check_rule_match(self, rule: BoundaryRule, action: Dict) -> bool:
        conditions = rule.conditions
        
        if "action_type" in conditions:
            expected = conditions["action_type"]
            actual = action.get("action_type", "")
            
            if isinstance(expected, list):
                if actual in expected:
                    return True
            elif actual == expected:
                return True
                
        if "target_type" in conditions:
            if action.get("target_type") == conditions["target_type"]:
                return True
                
        if "involves_pii" in conditions:
            if action.get("involves_pii", False) == conditions["involves_pii"]:
                return True
                
        return False
        
    def _check_conditions(self, conditions: Dict, action: Dict) -> bool:
        for key, expected in conditions.items():
            actual = action.get(key)
            
            if isinstance(expected, dict):
                if "min" in expected:
                    if actual is None or actual < expected["min"]:
                        return False
                elif "max" in expected:
                    if actual is None or actual > expected["max"]:
                        return False
            elif actual != expected:
                return False
                
        return True
        
    def _record_violation(
        self,
        action: Dict,
        rule: BoundaryRule,
        severity: ViolationSeverity
    ):
        violation = {
            "violation_id": self._generate_violation_id(),
            "action": action,
            "rule": rule.to_dict(),
            "severity": severity.value,
            "timestamp": datetime.now().isoformat()
        }
        
        self.violation_history.append(violation)
        self.stats["violations_detected"] += 1
        
        logger.warning(
            f"Boundary violation detected: rule={rule.name}, "
            f"action={action.get('action_type')}, severity={severity.value}"
        )
        
        if self.communication_bus:
            asyncio.create_task(
                self.communication_bus.publish("boundary_violation", violation)
            )
            
    def _audit_action(self, action: Dict, allowed: bool):
        audit_record = {
            "audit_id": self._generate_audit_id(),
            "action": action,
            "allowed": allowed,
            "timestamp": datetime.now().isoformat()
        }
        
        self.action_audit.append(audit_record)
        
    async def add_rule(
        self,
        rule_type: RuleType,
        name: str,
        description: str,
        conditions: Dict,
        actions: List[str]
    ) -> BoundaryRule:
        rule = BoundaryRule(
            rule_id=self._generate_rule_id(),
            rule_type=rule_type,
            name=name,
            description=description,
            conditions=conditions,
            actions=actions,
            created_at=datetime.now(),
            active=True
        )
        
        self.rules[rule.rule_id] = rule
        
        logger.info(f"Added boundary rule: {name}")
        
        return rule
        
    async def remove_rule(self, rule_id: str) -> bool:
        if rule_id in self.rules:
            del self.rules[rule_id]
            return True
        return False
        
    async def toggle_rule(self, rule_id: str, active: bool) -> bool:
        if rule_id in self.rules:
            self.rules[rule_id].active = active
            return True
        return False
        
    async def get_rule(self, rule_id: str) -> Optional[Dict]:
        rule = self.rules.get(rule_id)
        return rule.to_dict() if rule else None
        
    async def get_all_rules(self) -> List[Dict]:
        return [r.to_dict() for r in self.rules.values()]
        
    async def get_violations(self, limit: int = 50) -> List[Dict]:
        return list(self.violation_history)[-limit:]
        
    async def get_audit_log(self, limit: int = 100) -> List[Dict]:
        return list(self.action_audit)[-limit:]
        
    def _generate_rule_id(self) -> str:
        return f"rule_{int(time.time() * 1000)}"
        
    def _generate_violation_id(self) -> str:
        return f"viol_{int(time.time() * 1000)}_{hashlib.md5(str(time.time()).encode()).hexdigest()[:6]}"
        
    def _generate_audit_id(self) -> str:
        return f"audit_{int(time.time() * 1000)}"
        
    def get_stats(self) -> Dict:
        return {
            **self.stats,
            "total_rules": len(self.rules),
            "active_rules": sum(1 for r in self.rules.values() if r.active),
            "violation_count": len(self.violation_history)
        }
