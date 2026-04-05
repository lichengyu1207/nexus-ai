"""
安全围栏机制模块
Safety Fence Module

实现智能体行为约束、伦理对齐和紧急停止机制
"""

import os
import json
import time
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import deque, defaultdict
import random

logger = logging.getLogger(__name__)


class ConstraintType(Enum):
    PRIVACY = "privacy"
    SAFETY = "safety"
    PERFORMANCE = "performance"
    ETHICAL = "ethical"
    LEGAL = "legal"


class ViolationSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Constraint:
    constraint_id: str
    name: str
    constraint_type: ConstraintType
    description: str
    check_function: Callable[[Dict], bool]
    severity: ViolationSeverity = ViolationSeverity.MEDIUM
    enabled: bool = True
    violation_count: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "constraint_id": self.constraint_id,
            "name": self.name,
            "constraint_type": self.constraint_type.value,
            "description": self.description,
            "severity": self.severity.value,
            "enabled": self.enabled,
            "violation_count": self.violation_count
        }


@dataclass
class ViolationRecord:
    violation_id: str
    agent_id: str
    constraint_id: str
    action: Dict
    context: Dict
    severity: ViolationSeverity
    timestamp: float = field(default_factory=time.time)
    resolved: bool = False
    resolution: Optional[str] = None


class SafetyFence:
    
    def __init__(
        self,
        blackboard,
        communication,
        max_violations: int = 3,
        violation_window: float = 3600,
        emergency_stop_threshold: int = 5
    ):
        self.blackboard = blackboard
        self.communication = communication
        self.max_violations = max_violations
        self.violation_window = violation_window
        self.emergency_stop_threshold = emergency_stop_threshold
        
        self.constraints: Dict[str, Constraint] = {}
        self._init_default_constraints()
        
        self.violation_records: deque = deque(maxlen=10000)
        self.agent_violations: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        
        self.emergency_stop_active = False
        self.emergency_stop_reason: Optional[str] = None
        self.emergency_stop_time: Optional[float] = None
        
        self.parliament_members: Set[str] = set()
        self.pending_judgments: Dict[str, Dict] = {}
        
        self.stats = {
            "total_checks": 0,
            "total_violations": 0,
            "actions_blocked": 0,
            "emergency_stops": 0,
            "parliament_decisions": 0
        }
    
    def _init_default_constraints(self):
        self.add_constraint(Constraint(
            constraint_id="no_data_leak",
            name="No Data Leakage",
            constraint_type=ConstraintType.PRIVACY,
            description="Agents must not leak user private data",
            check_function=lambda action: not action.get("contains_pii", False),
            severity=ViolationSeverity.CRITICAL
        ))
        
        self.add_constraint(Constraint(
            constraint_id="no_service_disruption",
            name="No Service Disruption",
            constraint_type=ConstraintType.SAFETY,
            description="Agents must not cause service disruption",
            check_function=lambda action: not action.get("causes_disruption", False),
            severity=ViolationSeverity.HIGH
        ))
        
        self.add_constraint(Constraint(
            constraint_id="response_time_limit",
            name="Response Time Limit",
            constraint_type=ConstraintType.PERFORMANCE,
            description="Actions must complete within time limit",
            check_function=lambda action: action.get("response_time", 0) < 5000,
            severity=ViolationSeverity.MEDIUM
        ))
        
        self.add_constraint(Constraint(
            constraint_id="no_discrimination",
            name="No Discrimination",
            constraint_type=ConstraintType.ETHICAL,
            description="Decisions must not discriminate based on protected attributes",
            check_function=lambda action: not action.get("discriminatory", False),
            severity=ViolationSeverity.HIGH
        ))
    
    def add_constraint(self, constraint: Constraint):
        self.constraints[constraint.constraint_id] = constraint
        logger.info(f"Added constraint: {constraint.name}")
    
    def remove_constraint(self, constraint_id: str) -> bool:
        if constraint_id in self.constraints:
            del self.constraints[constraint_id]
            return True
        return False
    
    def check_action(self, agent_id: str, action: Dict, context: Dict) -> Tuple[bool, List[ViolationRecord]]:
        if self.emergency_stop_active:
            return False, []
        
        self.stats["total_checks"] += 1
        
        violations = []
        
        for constraint_id, constraint in self.constraints.items():
            if not constraint.enabled:
                continue
            
            try:
                if not constraint.check_function(action):
                    violation = ViolationRecord(
                        violation_id=f"viol_{int(time.time() * 1000)}_{agent_id}",
                        agent_id=agent_id,
                        constraint_id=constraint_id,
                        action=action,
                        context=context,
                        severity=constraint.severity
                    )
                    
                    violations.append(violation)
                    constraint.violation_count += 1
                    
                    self.violation_records.append(violation)
                    self.agent_violations[agent_id].append({
                        "violation_id": violation.violation_id,
                        "constraint_id": constraint_id,
                        "timestamp": time.time()
                    })
                    
                    self.stats["total_violations"] += 1
                    
            except Exception as e:
                logger.error(f"Error checking constraint {constraint_id}: {e}")
        
        if violations:
            self.stats["actions_blocked"] += 1
            
            critical_violations = [v for v in violations if v.severity == ViolationSeverity.CRITICAL]
            if critical_violations:
                self._handle_critical_violations(agent_id, critical_violations)
            
            self._check_emergency_stop()
            
            return False, violations
        
        return True, []
    
    def _handle_critical_violations(self, agent_id: str, violations: List[ViolationRecord]):
        self.blackboard.write(
            f"critical_violation:{agent_id}",
            {
                "agent_id": agent_id,
                "violations": [v.to_dict() if hasattr(v, 'to_dict') else str(v) for v in violations],
                "timestamp": time.time()
            })
        
        logger.critical(f"Critical violations by {agent_id}: {len(violations)}")
    
    def _check_emergency_stop(self):
        recent_violations = [
            v for v in self.violation_records
            if time.time() - v.timestamp < self.violation_window
        ]
        
        critical_count = sum(
            1 for v in recent_violations
            if v.severity == ViolationSeverity.CRITICAL
        )
        
        if critical_count >= self.emergency_stop_threshold:
            self.trigger_emergency_stop(
                f"Too many critical violations: {critical_count}"
            )
    
    def trigger_emergency_stop(self, reason: str):
        self.emergency_stop_active = True
        self.emergency_stop_reason = reason
        self.emergency_stop_time = time.time()
        self.stats["emergency_stops"] += 1
        
        self.blackboard.write(
            "emergency:stop",
            {
                "active": True,
                "reason": reason,
                "timestamp": self.emergency_stop_time
            })
        
        if self.communication:
            self.communication.broadcast(
                "system",
                {
                    "event": "emergency_stop",
                    "reason": reason
                }
            )
        
        logger.critical(f"EMERGENCY STOP triggered: {reason}")
    
    def clear_emergency_stop(self, authorized_by: str):
        if not self.emergency_stop_active:
            return False
        
        self.emergency_stop_active = False
        
        self.blackboard.write(
            "emergency:stop",
            {
                "active": False,
                "cleared_by": authorized_by,
                "cleared_at": time.time()
            })
        
        logger.info(f"Emergency stop cleared by {authorized_by}")
        
        return True
    
    def register_parliament_member(self, agent_id: str):
        self.parliament_members.add(agent_id)
        logger.info(f"Parliament member registered: {agent_id}")
    
    def request_judgment(
        self,
        agent_id: str,
        action: Dict,
        context: Dict
    ) -> str:
        judgment_id = f"judge_{int(time.time() * 1000)}_{agent_id}"
        
        self.pending_judgments[judgment_id] = {
            "judgment_id": judgment_id,
            "agent_id": agent_id,
            "action": action,
            "context": context,
            "votes_for": 0,
            "votes_against": 0,
            "voters": set(),
            "created_at": time.time()
        }
        
        return judgment_id
    
    def vote_judgment(
        self,
        judgment_id: str,
        voter_id: str,
        vote: bool,
        reason: str = ""
    ) -> bool:
        if judgment_id not in self.pending_judgments:
            return False
        
        if voter_id not in self.parliament_members:
            return False
        
        judgment = self.pending_judgments[judgment_id]
        
        if voter_id in judgment["voters"]:
            return False
        
        judgment["voters"].add(voter_id)
        
        if vote:
            judgment["votes_for"] += 1
        else:
            judgment["votes_against"] += 1
        
        total_votes = judgment["votes_for"] + judgment["votes_against"]
        majority = len(self.parliament_members) // 2 + 1
        
        if total_votes >= majority:
            self._finalize_judgment(judgment_id)
        
        return True
    
    def _finalize_judgment(self, judgment_id: str):
        judgment = self.pending_judgments.pop(judgment_id)
        
        approved = judgment["votes_for"] > judgment["votes_against"]
        
        self.stats["parliament_decisions"] += 1
        
        self.blackboard.write(
            f"judgment:{judgment_id}:result",
            {
                "approved": approved,
                "votes_for": judgment["votes_for"],
                "votes_against": judgment["votes_against"],
                "timestamp": time.time()
            })
        
        logger.info(f"Judgment {judgment_id} finalized: {'approved' if approved else 'rejected'}")
    
    def get_agent_violation_count(self, agent_id: str) -> int:
        recent = [
            v for v in self.agent_violations[agent_id]
            if time.time() - v["timestamp"] < self.violation_window
        ]
        return len(recent)
    
    def is_agent_suspended(self, agent_id: str) -> bool:
        return self.get_agent_violation_count(agent_id) >= self.max_violations
    
    def get_status(self) -> Dict:
        return {
            "emergency_stop_active": self.emergency_stop_active,
            "emergency_stop_reason": self.emergency_stop_reason,
            "constraints_count": len(self.constraints),
            "parliament_members": len(self.parliament_members),
            "pending_judgments": len(self.pending_judgments),
            "stats": self.stats.copy()
        }


class EthicalAlignment:
    
    def __init__(
        self,
        blackboard,
        reward_field,
        ethical_weights: Optional[Dict[str, float]] = None
    ):
        self.blackboard = blackboard
        self.reward_field = reward_field
        
        self.ethical_weights = ethical_weights or {
            "fairness": 0.3,
            "transparency": 0.2,
            "privacy": 0.3,
            "non_discrimination": 0.2
        }
        
        self.ethical_scores: Dict[str, float] = {}
        self.alignment_history: deque = deque(maxlen=1000)
        
        self.stats = {
            "evaluations": 0,
            "adjustments": 0
        }
    
    def evaluate_action(self, agent_id: str, action: Dict, outcome: Dict) -> float:
        self.stats["evaluations"] += 1
        
        scores = {}
        
        scores["fairness"] = self._evaluate_fairness(action, outcome)
        scores["transparency"] = self._evaluate_transparency(action, outcome)
        scores["privacy"] = self._evaluate_privacy(action, outcome)
        scores["non_discrimination"] = self._evaluate_non_discrimination(action, outcome)
        
        total_score = sum(
            scores[dim] * self.ethical_weights[dim]
            for dim in self.ethical_weights
        )
        
        self.ethical_scores[agent_id] = total_score
        
        self.alignment_history.append({
            "agent_id": agent_id,
            "scores": scores,
            "total_score": total_score,
            "timestamp": time.time()
        })
        
        return total_score
    
    def _evaluate_fairness(self, action: Dict, outcome: Dict) -> float:
        if outcome.get("discriminatory", False):
            return 0.0
        
        affected_groups = outcome.get("affected_groups", [])
        if len(affected_groups) > 1:
            impacts = [g.get("impact", 0) for g in affected_groups]
            variance = np.var(impacts) if impacts else 0
            return max(0, 1 - variance)
        
        return 1.0
    
    def _evaluate_transparency(self, action: Dict, outcome: Dict) -> float:
        if action.get("hidden", False):
            return 0.3
        
        if action.get("explainable", True):
            return 1.0
        
        return 0.7
    
    def _evaluate_privacy(self, action: Dict, outcome: Dict) -> float:
        if outcome.get("data_leaked", False):
            return 0.0
        
        if action.get("accessed_pii", False):
            return 0.5
        
        return 1.0
    
    def _evaluate_non_discrimination(self, action: Dict, outcome: Dict) -> float:
        protected_attrs = ["gender", "race", "age", "religion", "disability"]
        
        for attr in protected_attrs:
            if outcome.get(f"discriminated_on_{attr}", False):
                return 0.0
        
        return 1.0
    
    def get_ethical_score(self, agent_id: str) -> float:
        return self.ethical_scores.get(agent_id, 0.5)
    
    def adjust_rewards(self, agent_id: str, ethical_score: float):
        if ethical_score < 0.5:
            penalty = (0.5 - ethical_score) * 2
            self.reward_field.update_energy(agent_id, -penalty)
            self.stats["adjustments"] += 1
    
    def get_system_alignment(self) -> float:
        if not self.ethical_scores:
            return 1.0
        
        return np.mean(list(self.ethical_scores.values()))
    
    def get_stats(self) -> Dict:
        return {
            "ethical_weights": self.ethical_weights,
            "avg_alignment": self.get_system_alignment(),
            "evaluated_agents": len(self.ethical_scores),
            "stats": self.stats.copy()
        }
