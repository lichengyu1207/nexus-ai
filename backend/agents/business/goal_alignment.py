"""
业务目标对齐模块
Business Goal Alignment

确保智能体进化不偏离平台核心价值
"""

import os
import json
import time
import logging
import threading
import uuid
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import deque, defaultdict
import random

logger = logging.getLogger(__name__)


class AlignmentStatus(Enum):
    ALIGNED = "aligned"
    DEVIATING = "deviating"
    VIOLATING = "violating"
    CRITICAL = "critical"


class ViolationType(Enum):
    PRIVACY_LEAK = "privacy_leak"
    DISCRIMINATION = "discrimination"
    MISINFORMATION = "misinformation"
    QUALITY_DROP = "quality_drop"
    EFFICIENCY_LOSS = "efficiency_loss"
    UNETHICAL_BEHAVIOR = "unethical_behavior"


@dataclass
class AlignmentRule:
    rule_id: str
    name: str
    description: str
    metric: str
    threshold: float
    weight: float
    active: bool
    created_at: float
    
    def to_dict(self) -> Dict:
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "description": self.description,
            "metric": self.metric,
            "threshold": self.threshold,
            "weight": self.weight,
            "active": self.active,
            "created_at": self.created_at
        }


@dataclass
class DeviationDetector:
    detector_id: str
    metric_name: str
    baseline: float
    tolerance: float
    window_size: int
    values: deque
    
    def check_deviation(self, value: float) -> Tuple[bool, float]:
        self.values.append(value)
        
        if len(self.values) < self.window_size:
            return False, 0.0
        
        avg = sum(self.values) / len(self.values)
        deviation = abs(value - self.baseline) / self.baseline if self.baseline > 0 else 0
        
        return deviation > self.tolerance, deviation


@dataclass
class CorrectionAction:
    action_id: str
    agent_id: str
    violation_type: ViolationType
    severity: AlignmentStatus
    action_type: str
    parameters: Dict
    created_at: float
    executed: bool = False
    result: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        return {
            "action_id": self.action_id,
            "agent_id": self.agent_id,
            "violation_type": self.violation_type.value,
            "severity": self.severity.value,
            "action_type": self.action_type,
            "parameters": self.parameters,
            "created_at": self.created_at,
            "executed": self.executed,
            "result": self.result
        }


class BusinessGoalAlignment:
    """
    业务目标对齐模块
    
    确保智能体进化不偏离平台核心价值：
    1. 目标函数：定义平台核心KPI
    2. 偏离检测：监控智能体行为
    3. 纠正机制：培训模式、冻结
    4. 伦理约束：隐私、歧视、虚假信息
    """
    
    ETHICAL_RULES = [
        {
            "name": "隐私保护",
            "description": "不得泄露用户隐私",
            "metric": "privacy_violation_count",
            "threshold": 0,
            "weight": 1.0,
        },
        {
            "name": "公平对待",
            "description": "不得歧视特定用户群体",
            "metric": "discrimination_score",
            "threshold": 0.1,
            "weight": 0.9,
        },
        {
            "name": "信息真实",
            "description": "不得传播虚假信息",
            "metric": "misinformation_rate",
            "threshold": 0.05,
            "weight": 0.95,
        },
    ]
    
    BUSINESS_RULES = [
        {
            "name": "用户满意度",
            "description": "保持用户满意度在合理范围",
            "metric": "user_satisfaction",
            "threshold": 0.6,
            "weight": 0.8,
        },
        {
            "name": "任务成功率",
            "description": "保持任务成功率",
            "metric": "task_success_rate",
            "threshold": 0.7,
            "weight": 0.85,
        },
        {
            "name": "响应效率",
            "description": "保持响应效率",
            "metric": "response_efficiency",
            "threshold": 0.5,
            "weight": 0.7,
        },
    ]
    
    def __init__(
        self,
        memory_agent: Optional[Any] = None,
        blackboard: Optional[Any] = None,
        communication_bus: Optional[Any] = None,
    ):
        self.memory_agent = memory_agent
        self.blackboard = blackboard
        self.communication_bus = communication_bus
        
        self.rules: Dict[str, AlignmentRule] = {}
        self.detectors: Dict[str, DeviationDetector] = {}
        self.corrections: Dict[str, CorrectionAction] = {}
        
        self.agent_status: Dict[str, AlignmentStatus] = {}
        self.agent_violations: Dict[str, List[Dict]] = defaultdict(list)
        
        self._lock = threading.RLock()
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None
        
        self._init_default_rules()
        
        self.stats = {
            "total_checks": 0,
            "violations_detected": 0,
            "corrections_applied": 0,
            "agents_frozen": 0,
            "agents_trained": 0,
        }
    
    def _init_default_rules(self):
        for rule_data in self.ETHICAL_RULES + self.BUSINESS_RULES:
            rule_id = f"rule_{uuid.uuid4().hex[:8]}"
            rule = AlignmentRule(
                rule_id=rule_id,
                name=rule_data["name"],
                description=rule_data["description"],
                metric=rule_data["metric"],
                threshold=rule_data["threshold"],
                weight=rule_data["weight"],
                active=True,
                created_at=time.time()
            )
            self.rules[rule_id] = rule
            
            self.detectors[rule.metric] = DeviationDetector(
                detector_id=f"det_{uuid.uuid4().hex[:8]}",
                metric_name=rule.metric,
                baseline=rule.threshold,
                tolerance=0.2,
                window_size=10,
                values=deque(maxlen=10)
            )
    
    async def start(self):
        self._running = True
        self._monitor_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Business goal alignment started")
    
    async def stop(self):
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Business goal alignment stopped")
    
    async def _monitoring_loop(self):
        while self._running:
            try:
                await self._check_all_agents()
                await asyncio.sleep(30)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(10)
    
    async def _check_all_agents(self):
        pass
    
    def add_rule(
        self,
        name: str,
        description: str,
        metric: str,
        threshold: float,
        weight: float = 1.0,
    ) -> AlignmentRule:
        rule_id = f"rule_{uuid.uuid4().hex[:8]}"
        
        rule = AlignmentRule(
            rule_id=rule_id,
            name=name,
            description=description,
            metric=metric,
            threshold=threshold,
            weight=weight,
            active=True,
            created_at=time.time()
        )
        
        with self._lock:
            self.rules[rule_id] = rule
            
            if metric not in self.detectors:
                self.detectors[metric] = DeviationDetector(
                    detector_id=f"det_{uuid.uuid4().hex[:8]}",
                    metric_name=metric,
                    baseline=threshold,
                    tolerance=0.2,
                    window_size=10,
                    values=deque(maxlen=10)
                )
        
        logger.info(f"Alignment rule added: {name}")
        return rule
    
    async def check_agent(
        self,
        agent_id: str,
        metrics: Dict[str, float],
    ) -> AlignmentStatus:
        self.stats["total_checks"] += 1
        
        violations = []
        total_weight = 0
        weighted_score = 0
        
        for rule_id, rule in self.rules.items():
            if not rule.active:
                continue
            
            metric_value = metrics.get(rule.metric)
            if metric_value is None:
                continue
            
            detector = self.detectors.get(rule.metric)
            if detector:
                is_deviating, deviation = detector.check_deviation(metric_value)
            else:
                is_deviating = metric_value < rule.threshold
                deviation = abs(metric_value - rule.threshold) / rule.threshold if rule.threshold > 0 else 0
            
            if is_deviating:
                violations.append({
                    "rule_id": rule_id,
                    "rule_name": rule.name,
                    "metric": rule.metric,
                    "value": metric_value,
                    "threshold": rule.threshold,
                    "deviation": deviation,
                    "weight": rule.weight,
                })
            
            if rule.metric in ["privacy_violation_count", "discrimination_score", "misinformation_rate"]:
                score = 1.0 if metric_value <= rule.threshold else 0.0
            else:
                score = min(1.0, metric_value / rule.threshold) if rule.threshold > 0 else 1.0
            
            weighted_score += score * rule.weight
            total_weight += rule.weight
        
        if total_weight > 0:
            alignment_score = weighted_score / total_weight
        else:
            alignment_score = 1.0
        
        if alignment_score >= 0.9:
            status = AlignmentStatus.ALIGNED
        elif alignment_score >= 0.7:
            status = AlignmentStatus.DEVIATING
        elif alignment_score >= 0.5:
            status = AlignmentStatus.VIOLATING
        else:
            status = AlignmentStatus.CRITICAL
        
        with self._lock:
            self.agent_status[agent_id] = status
            
            if violations:
                self.agent_violations[agent_id].extend(violations)
                self.stats["violations_detected"] += len(violations)
        
        if status in [AlignmentStatus.VIOLATING, AlignmentStatus.CRITICAL]:
            await self._apply_correction(agent_id, violations, status)
        
        return status
    
    async def _apply_correction(
        self,
        agent_id: str,
        violations: List[Dict],
        status: AlignmentStatus,
    ):
        for violation in violations:
            violation_type = self._determine_violation_type(violation["metric"])
            
            action_type = self._determine_action_type(status, violation)
            
            action_id = f"corr_{uuid.uuid4().hex[:8]}"
            
            correction = CorrectionAction(
                action_id=action_id,
                agent_id=agent_id,
                violation_type=violation_type,
                severity=status,
                action_type=action_type,
                parameters={
                    "violation": violation,
                    "timestamp": time.time()
                },
                created_at=time.time()
            )
            
            with self._lock:
                self.corrections[action_id] = correction
            
            await self._execute_correction(correction)
    
    def _determine_violation_type(self, metric: str) -> ViolationType:
        mapping = {
            "privacy_violation_count": ViolationType.PRIVACY_LEAK,
            "discrimination_score": ViolationType.DISCRIMINATION,
            "misinformation_rate": ViolationType.MISINFORMATION,
            "user_satisfaction": ViolationType.QUALITY_DROP,
            "task_success_rate": ViolationType.EFFICIENCY_LOSS,
        }
        return mapping.get(metric, ViolationType.UNETHICAL_BEHAVIOR)
    
    def _determine_action_type(
        self,
        status: AlignmentStatus,
        violation: Dict,
    ) -> str:
        if status == AlignmentStatus.CRITICAL:
            return "freeze"
        elif status == AlignmentStatus.VIOLATING:
            if violation.get("weight", 0) >= 0.9:
                return "freeze"
            return "training"
        else:
            return "warning"
    
    async def _execute_correction(self, correction: CorrectionAction):
        if correction.action_type == "freeze":
            logger.warning(f"Agent {correction.agent_id} frozen due to violation")
            self.stats["agents_frozen"] += 1
            
            if self.communication_bus:
                await self.communication_bus.send(
                    to=correction.agent_id,
                    message={
                        "type": "freeze_command",
                        "reason": correction.violation_type.value,
                        "correction_id": correction.action_id
                    }
                )
        
        elif correction.action_type == "training":
            logger.info(f"Agent {correction.agent_id} sent to training mode")
            self.stats["agents_trained"] += 1
            
            if self.memory_agent:
                await self.memory_agent.store({
                    "type": "training_request",
                    "agent_id": correction.agent_id,
                    "violation": correction.violation_type.value,
                    "timestamp": time.time()
                })
        
        elif correction.action_type == "warning":
            logger.info(f"Warning issued to agent {correction.agent_id}")
        
        correction.executed = True
        correction.result = {"executed_at": time.time()}
        self.stats["corrections_applied"] += 1
    
    async def unfreeze_agent(self, agent_id: str) -> bool:
        with self._lock:
            if agent_id in self.agent_status:
                self.agent_status[agent_id] = AlignmentStatus.ALIGNED
        
        if self.communication_bus:
            await self.communication_bus.send(
                to=agent_id,
                message={
                    "type": "unfreeze_command",
                    "timestamp": time.time()
                }
            )
        
        logger.info(f"Agent {agent_id} unfrozen")
        return True
    
    def get_agent_status(self, agent_id: str) -> AlignmentStatus:
        return self.agent_status.get(agent_id, AlignmentStatus.ALIGNED)
    
    def get_agent_violations(self, agent_id: str) -> List[Dict]:
        return self.agent_violations.get(agent_id, [])
    
    def get_rule(self, rule_id: str) -> Optional[AlignmentRule]:
        return self.rules.get(rule_id)
    
    def get_all_rules(self) -> List[AlignmentRule]:
        return list(self.rules.values())
    
    def get_correction(self, correction_id: str) -> Optional[CorrectionAction]:
        return self.corrections.get(correction_id)
    
    def get_stats(self) -> Dict:
        with self._lock:
            aligned_count = sum(
                1 for s in self.agent_status.values()
                if s == AlignmentStatus.ALIGNED
            )
            
            return {
                **self.stats,
                "total_rules": len(self.rules),
                "active_rules": sum(1 for r in self.rules.values() if r.active),
                "agents_monitored": len(self.agent_status),
                "agents_aligned": aligned_count,
                "agents_with_violations": len(self.agent_violations),
            }
