"""
业务智能体局部规则库
Business Agent Local Rules Engine

为各部智能体设计局部规则，指导日常行为
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


class RulePriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class RuleState(Enum):
    INACTIVE = "inactive"
    ACTIVE = "active"
    TRIGGERED = "triggered"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


class TriggerType(Enum):
    USER_BEHAVIOR = "user_behavior"
    TASK_EVENT = "task_event"
    TIME_BASED = "time_based"
    THRESHOLD = "threshold"
    PATTERN = "pattern"
    EXTERNAL = "external"


@dataclass
class RuleCondition:
    condition_id: str
    field: str
    operator: str
    value: Any
    weight: float = 1.0
    
    def evaluate(self, context: Dict) -> bool:
        actual_value = self._get_nested_value(context, self.field)
        
        if actual_value is None:
            return False
        
        if self.operator == "eq":
            return actual_value == self.value
        elif self.operator == "ne":
            return actual_value != self.value
        elif self.operator == "gt":
            return actual_value > self.value
        elif self.operator == "gte":
            return actual_value >= self.value
        elif self.operator == "lt":
            return actual_value < self.value
        elif self.operator == "lte":
            return actual_value <= self.value
        elif self.operator == "contains":
            return self.value in actual_value if isinstance(actual_value, (list, str)) else False
        elif self.operator == "not_contains":
            return self.value not in actual_value if isinstance(actual_value, (list, str)) else True
        elif self.operator == "in":
            return actual_value in self.value
        elif self.operator == "regex":
            import re
            return bool(re.match(self.value, str(actual_value)))
        
        return False
    
    def _get_nested_value(self, data: Dict, path: str) -> Any:
        keys = path.split(".")
        value = data
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
        return value
    
    def to_dict(self) -> Dict:
        return {
            "condition_id": self.condition_id,
            "field": self.field,
            "operator": self.operator,
            "value": self.value,
            "weight": self.weight
        }


@dataclass
class RuleAction:
    action_id: str
    action_type: str
    target: str
    parameters: Dict
    energy_cost: float = 0.0
    timeout: float = 30.0
    
    def to_dict(self) -> Dict:
        return {
            "action_id": self.action_id,
            "action_type": self.action_type,
            "target": self.target,
            "parameters": self.parameters,
            "energy_cost": self.energy_cost,
            "timeout": self.timeout
        }


@dataclass
class BusinessRule:
    rule_id: str
    name: str
    description: str
    department: str
    trigger_type: TriggerType
    conditions: List[RuleCondition]
    actions: List[RuleAction]
    priority: RulePriority = RulePriority.NORMAL
    state: RuleState = RuleState.INACTIVE
    cooldown: float = 60.0
    max_executions: int = 100
    execution_count: int = 0
    last_triggered: Optional[float] = None
    last_executed: Optional[float] = None
    success_count: int = 0
    failure_count: int = 0
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    metadata: Dict = field(default_factory=dict)
    
    def evaluate(self, context: Dict) -> bool:
        if self.state == RuleState.INACTIVE:
            return False
        
        if self.execution_count >= self.max_executions:
            return False
        
        if self.last_triggered:
            if time.time() - self.last_triggered < self.cooldown:
                return False
        
        condition_results = [cond.evaluate(context) for cond in self.conditions]
        
        return all(condition_results)
    
    def trigger(self) -> bool:
        if self.state not in [RuleState.ACTIVE, RuleState.COMPLETED]:
            return False
        
        self.state = RuleState.TRIGGERED
        self.last_triggered = time.time()
        return True
    
    def start_execution(self):
        self.state = RuleState.EXECUTING
    
    def complete_execution(self, success: bool):
        self.execution_count += 1
        self.last_executed = time.time()
        
        if success:
            self.success_count += 1
            self.state = RuleState.COMPLETED
        else:
            self.failure_count += 1
            self.state = RuleState.FAILED
    
    def activate(self):
        self.state = RuleState.ACTIVE
    
    def deactivate(self):
        self.state = RuleState.INACTIVE
    
    def get_success_rate(self) -> float:
        total = self.success_count + self.failure_count
        if total == 0:
            return 0.0
        return self.success_count / total
    
    def to_dict(self) -> Dict:
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "description": self.description,
            "department": self.department,
            "trigger_type": self.trigger_type.value,
            "conditions": [c.to_dict() for c in self.conditions],
            "actions": [a.to_dict() for a in self.actions],
            "priority": self.priority.value,
            "state": self.state.value,
            "cooldown": self.cooldown,
            "max_executions": self.max_executions,
            "execution_count": self.execution_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": self.get_success_rate(),
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


class RuleFSM:
    """
    规则有限状态机
    
    管理单个规则的状态转换
    """
    
    TRANSITIONS = {
        RuleState.INACTIVE: [RuleState.ACTIVE],
        RuleState.ACTIVE: [RuleState.TRIGGERED, RuleState.INACTIVE],
        RuleState.TRIGGERED: [RuleState.EXECUTING, RuleState.ACTIVE, RuleState.FAILED],
        RuleState.EXECUTING: [RuleState.COMPLETED, RuleState.FAILED],
        RuleState.COMPLETED: [RuleState.ACTIVE, RuleState.INACTIVE],
        RuleState.FAILED: [RuleState.ACTIVE, RuleState.INACTIVE],
    }
    
    def __init__(self, rule: BusinessRule):
        self.rule = rule
        self.transition_history: List[Dict] = []
    
    def can_transition_to(self, new_state: RuleState) -> bool:
        return new_state in self.TRANSITIONS.get(self.rule.state, [])
    
    def transition(self, new_state: RuleState, reason: str = "") -> bool:
        if not self.can_transition_to(new_state):
            return False
        
        old_state = self.rule.state
        self.rule.state = new_state
        
        self.transition_history.append({
            "from_state": old_state.value,
            "to_state": new_state.value,
            "reason": reason,
            "timestamp": time.time()
        })
        
        return True
    
    def get_history(self) -> List[Dict]:
        return self.transition_history.copy()


class LocalRulesEngine:
    """
    局部规则引擎
    
    为各部智能体设计局部规则，指导日常行为
    规则可配置，支持热更新
    """
    
    def __init__(
        self,
        blackboard: Optional[Any] = None,
        communication_bus: Optional[Any] = None,
        memory_agent: Optional[Any] = None,
    ):
        self.blackboard = blackboard
        self.communication_bus = communication_bus
        self.memory_agent = memory_agent
        
        self.rules: Dict[str, BusinessRule] = {}
        self.rule_fsms: Dict[str, RuleFSM] = {}
        self.department_rules: Dict[str, List[str]] = defaultdict(list)
        
        self.execution_queue: asyncio.Queue = asyncio.Queue()
        self.action_handlers: Dict[str, Callable] = {}
        
        self._lock = threading.RLock()
        self._running = False
        self._executor_task: Optional[asyncio.Task] = None
        
        self._register_default_action_handlers()
        self._init_default_rules()
        
        self.stats = {
            "rules_registered": 0,
            "rules_triggered": 0,
            "rules_executed": 0,
            "rules_succeeded": 0,
            "rules_failed": 0,
            "avg_execution_time_ms": 0.0,
        }
    
    def _register_default_action_handlers(self):
        self.action_handlers["notify"] = self._handle_notify_action
        self.action_handlers["create_task"] = self._handle_create_task_action
        self.action_handlers["update_cache"] = self._handle_update_cache_action
        self.action_handlers["send_message"] = self._handle_send_message_action
        self.action_handlers["log_event"] = self._handle_log_event_action
        self.action_handlers["adjust_parameter"] = self._handle_adjust_parameter_action
        self.action_handlers["trigger_alert"] = self._handle_trigger_alert_action
    
    def _init_default_rules(self):
        self._init_li_bu_rules()
        self._init_hu_bu_rules()
        self._init_li_bu_consult_rules()
        self._init_bing_bu_rules()
        self._init_xing_bu_rules()
        self._init_gong_bu_rules()
    
    def _init_li_bu_consult_rules(self):
        self.register_rule(BusinessRule(
            rule_id="libu_faq_auto_generate",
            name="FAQ自动生成",
            description="用户反复询问同一问题时自动生成FAQ",
            department="li_bu_consult",
            trigger_type=TriggerType.PATTERN,
            conditions=[
                RuleCondition(
                    condition_id="cond_same_question",
                    field="user.question_repeat_count",
                    operator="gte",
                    value=3
                )
            ],
            actions=[
                RuleAction(
                    action_id="action_generate_faq",
                    action_type="create_task",
                    target="gong_bu",
                    parameters={"task_type": "faq_generation"},
                    energy_cost=5.0
                ),
                RuleAction(
                    action_id="action_store_faq",
                    action_type="update_cache",
                    target="hu_bu",
                    parameters={"cache_type": "faq"},
                    energy_cost=1.0
                )
            ],
            priority=RulePriority.NORMAL,
            cooldown=300.0
        ))
        
        self.register_rule(BusinessRule(
            rule_id="libu_quick_summary",
            name="快速摘要生成",
            description="用户表现出不耐烦时生成快速摘要",
            department="li_bu_consult",
            trigger_type=TriggerType.USER_BEHAVIOR,
            conditions=[
                RuleCondition(
                    condition_id="cond_impatient",
                    field="user.impatience_score",
                    operator="gte",
                    value=0.7
                ),
                RuleCondition(
                    condition_id="cond_multiple_prompts",
                    field="user.prompt_count",
                    operator="gte",
                    value=3
                )
            ],
            actions=[
                RuleAction(
                    action_id="action_request_summary",
                    action_type="send_message",
                    target="gong_bu",
                    parameters={"message_type": "quick_summary_request"},
                    energy_cost=3.0
                )
            ],
            priority=RulePriority.HIGH,
            cooldown=60.0
        ))
    
    def _init_gong_bu_rules(self):
        self.register_rule(BusinessRule(
            rule_id="gongbu_prefetch_report",
            name="报告预生成",
            description="同一小区被多次请求分析时自动预生成报告",
            department="gong_bu",
            trigger_type=TriggerType.PATTERN,
            conditions=[
                RuleCondition(
                    condition_id="cond_community_requests",
                    field="community.request_count",
                    operator="gte",
                    value=3
                ),
                RuleCondition(
                    condition_id="cond_time_window",
                    field="community.request_window_hours",
                    operator="lte",
                    value=24
                )
            ],
            actions=[
                RuleAction(
                    action_id="action_prefetch",
                    action_type="create_task",
                    target="gong_bu",
                    parameters={"task_type": "prefetch_report"},
                    energy_cost=10.0
                ),
                RuleAction(
                    action_id="action_cache",
                    action_type="update_cache",
                    target="hu_bu",
                    parameters={"cache_type": "report"},
                    energy_cost=2.0
                )
            ],
            priority=RulePriority.NORMAL,
            cooldown=600.0
        ))
        
        self.register_rule(BusinessRule(
            rule_id="gongbu_request_data",
            name="请求补充数据",
            description="分析时间过长时请求兵部补充数据",
            department="gong_bu",
            trigger_type=TriggerType.THRESHOLD,
            conditions=[
                RuleCondition(
                    condition_id="cond_analysis_time",
                    field="task.elapsed_time_seconds",
                    operator="gt",
                    value=120
                )
            ],
            actions=[
                RuleAction(
                    action_id="action_request_data",
                    action_type="send_message",
                    target="bing_bu",
                    parameters={"message_type": "data_supplement_request"},
                    energy_cost=5.0
                )
            ],
            priority=RulePriority.HIGH,
            cooldown=120.0
        ))
    
    def _init_hu_bu_rules(self):
        self.register_rule(BusinessRule(
            rule_id="hubu_seven_day_reward",
            name="连续签到奖励",
            description="用户连续签到7天自动发放奖励",
            department="hu_bu",
            trigger_type=TriggerType.USER_BEHAVIOR,
            conditions=[
                RuleCondition(
                    condition_id="cond_consecutive_days",
                    field="user.consecutive_checkin_days",
                    operator="eq",
                    value=7
                )
            ],
            actions=[
                RuleAction(
                    action_id="action_grant_reward",
                    action_type="adjust_parameter",
                    target="user",
                    parameters={"field": "points", "delta": 100},
                    energy_cost=0.0
                ),
                RuleAction(
                    action_id="action_notify",
                    action_type="send_message",
                    target="li_bu_consult",
                    parameters={"message_type": "congratulation"},
                    energy_cost=1.0
                )
            ],
            priority=RulePriority.NORMAL,
            cooldown=86400.0
        ))
        
        self.register_rule(BusinessRule(
            rule_id="hubu_abnormal_points",
            name="积分异常风控",
            description="用户积分异常波动时通知刑部",
            department="hu_bu",
            trigger_type=TriggerType.THRESHOLD,
            conditions=[
                RuleCondition(
                    condition_id="cond_points_change",
                    field="user.points_change_rate",
                    operator="gt",
                    value=0.5
                ),
                RuleCondition(
                    condition_id="cond_time_window",
                    field="user.change_window_minutes",
                    operator="lte",
                    value=60
                )
            ],
            actions=[
                RuleAction(
                    action_id="action_alert_xingbu",
                    action_type="send_message",
                    target="xing_bu",
                    parameters={"message_type": "risk_alert"},
                    energy_cost=2.0
                )
            ],
            priority=RulePriority.HIGH,
            cooldown=300.0
        ))
    
    def _init_bing_bu_rules(self):
        self.register_rule(BusinessRule(
            rule_id="bingbu_failover",
            name="数据源故障切换",
            description="数据源连续失败3次自动切换备用源",
            department="bing_bu",
            trigger_type=TriggerType.THRESHOLD,
            conditions=[
                RuleCondition(
                    condition_id="cond_fail_count",
                    field="datasource.consecutive_failures",
                    operator="gte",
                    value=3
                )
            ],
            actions=[
                RuleAction(
                    action_id="action_switch_source",
                    action_type="adjust_parameter",
                    target="datasource",
                    parameters={"action": "switch_to_backup"},
                    energy_cost=5.0
                ),
                RuleAction(
                    action_id="action_report_libu",
                    action_type="send_message",
                    target="li_bu",
                    parameters={"message_type": "datasource_alert"},
                    energy_cost=1.0
                )
            ],
            priority=RulePriority.CRITICAL,
            cooldown=300.0
        ))
        
        self.register_rule(BusinessRule(
            rule_id="bingbu_new_source_bid",
            name="新数据源评估",
            description="检测到新数据源时发起竞标评估",
            department="bing_bu",
            trigger_type=TriggerType.EXTERNAL,
            conditions=[
                RuleCondition(
                    condition_id="cond_new_source",
                    field="datasource.is_new",
                    operator="eq",
                    value=True
                )
            ],
            actions=[
                RuleAction(
                    action_id="action_create_bid",
                    action_type="create_task",
                    target="task_market",
                    parameters={"task_type": "datasource_evaluation"},
                    energy_cost=10.0
                )
            ],
            priority=RulePriority.NORMAL,
            cooldown=3600.0
        ))
    
    def _init_xing_bu_rules(self):
        self.register_rule(BusinessRule(
            rule_id="xingbu_auto_limit",
            name="可疑操作限流",
            description="检测到可疑操作时自动限流",
            department="xing_bu",
            trigger_type=TriggerType.THRESHOLD,
            conditions=[
                RuleCondition(
                    condition_id="cond_suspicious_score",
                    field="user.suspicious_score",
                    operator="gte",
                    value=0.8
                )
            ],
            actions=[
                RuleAction(
                    action_id="action_limit",
                    action_type="adjust_parameter",
                    target="user",
                    parameters={"action": "rate_limit", "duration": 300},
                    energy_cost=0.0
                ),
                RuleAction(
                    action_id="action_notify_verify",
                    action_type="send_message",
                    target="li_bu_consult",
                    parameters={"message_type": "verification_request"},
                    energy_cost=2.0
                )
            ],
            priority=RulePriority.CRITICAL,
            cooldown=60.0
        ))
        
        self.register_rule(BusinessRule(
            rule_id="xingbu_freeze_agent",
            name="智能体冻结",
            description="多个用户投诉同一智能体时自动冻结",
            department="xing_bu",
            trigger_type=TriggerType.THRESHOLD,
            conditions=[
                RuleCondition(
                    condition_id="cond_complaint_count",
                    field="agent.complaint_count",
                    operator="gte",
                    value=3
                ),
                RuleCondition(
                    condition_id="cond_time_window",
                    field="agent.complaint_window_hours",
                    operator="lte",
                    value=24
                )
            ],
            actions=[
                RuleAction(
                    action_id="action_freeze",
                    action_type="adjust_parameter",
                    target="agent",
                    parameters={"action": "freeze"},
                    energy_cost=0.0
                ),
                RuleAction(
                    action_id="action_trigger_review",
                    action_type="create_task",
                    target="li_bu",
                    parameters={"task_type": "agent_review"},
                    energy_cost=5.0
                )
            ],
            priority=RulePriority.CRITICAL,
            cooldown=3600.0
        ))
    
    def _init_li_bu_rules(self):
        self.register_rule(BusinessRule(
            rule_id="libu_low_energy_training",
            name="低能量智能体培训",
            description="智能体能量持续下降时发起培训",
            department="li_bu",
            trigger_type=TriggerType.THRESHOLD,
            conditions=[
                RuleCondition(
                    condition_id="cond_energy_decline",
                    field="agent.energy_decline_rate",
                    operator="gte",
                    value=0.3
                ),
                RuleCondition(
                    condition_id="cond_time_window",
                    field="agent.decline_window_hours",
                    operator="lte",
                    value=24
                )
            ],
            actions=[
                RuleAction(
                    action_id="action_training",
                    action_type="create_task",
                    target="memory_agent",
                    parameters={"task_type": "skill_transfer"},
                    energy_cost=20.0
                )
            ],
            priority=RulePriority.HIGH,
            cooldown=7200.0
        ))
        
        self.register_rule(BusinessRule(
            rule_id="libu_task_strategy_adjust",
            name="任务策略调整",
            description="某类任务频繁失败时调整分配策略",
            department="li_bu",
            trigger_type=TriggerType.PATTERN,
            conditions=[
                RuleCondition(
                    condition_id="cond_failure_rate",
                    field="task_type.failure_rate",
                    operator="gte",
                    value=0.3
                ),
                RuleCondition(
                    condition_id="cond_sample_size",
                    field="task_type.recent_count",
                    operator="gte",
                    value=10
                )
            ],
            actions=[
                RuleAction(
                    action_id="action_adjust",
                    action_type="adjust_parameter",
                    target="task_market",
                    parameters={"action": "adjust_allocation"},
                    energy_cost=5.0
                )
            ],
            priority=RulePriority.HIGH,
            cooldown=1800.0
        ))
    
    def register_rule(self, rule: BusinessRule) -> bool:
        with self._lock:
            if rule.rule_id in self.rules:
                logger.warning(f"Rule already exists: {rule.rule_id}")
                return False
            
            self.rules[rule.rule_id] = rule
            self.rule_fsms[rule.rule_id] = RuleFSM(rule)
            self.department_rules[rule.department].append(rule.rule_id)
            
            rule.activate()
            
            self.stats["rules_registered"] += 1
        
        logger.info(f"Rule registered: {rule.rule_id} ({rule.name})")
        return True
    
    def unregister_rule(self, rule_id: str) -> bool:
        with self._lock:
            if rule_id not in self.rules:
                return False
            
            rule = self.rules[rule_id]
            del self.rules[rule_id]
            del self.rule_fsms[rule_id]
            
            if rule_id in self.department_rules[rule.department]:
                self.department_rules[rule.department].remove(rule_id)
        
        logger.info(f"Rule unregistered: {rule_id}")
        return True
    
    def update_rule(self, rule_id: str, updates: Dict) -> bool:
        with self._lock:
            if rule_id not in self.rules:
                return False
            
            rule = self.rules[rule_id]
            
            if "conditions" in updates:
                rule.conditions = [
                    RuleCondition(**c) if isinstance(c, dict) else c
                    for c in updates["conditions"]
                ]
            
            if "actions" in updates:
                rule.actions = [
                    RuleAction(**a) if isinstance(a, dict) else a
                    for a in updates["actions"]
                ]
            
            for key in ["name", "description", "priority", "cooldown", "max_executions"]:
                if key in updates:
                    setattr(rule, key, updates[key])
            
            rule.updated_at = time.time()
        
        logger.info(f"Rule updated: {rule_id}")
        return True
    
    async def start(self):
        self._running = True
        self._executor_task = asyncio.create_task(self._execution_loop())
        logger.info("Local rules engine started")
    
    async def stop(self):
        self._running = False
        if self._executor_task:
            self._executor_task.cancel()
            try:
                await self._executor_task
            except asyncio.CancelledError:
                pass
        logger.info("Local rules engine stopped")
    
    async def _execution_loop(self):
        while self._running:
            try:
                task = await asyncio.wait_for(
                    self.execution_queue.get(),
                    timeout=1.0
                )
                await self._execute_rule_task(task)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in execution loop: {e}")
    
    async def evaluate_context(
        self,
        context: Dict,
        department: Optional[str] = None,
    ) -> List[BusinessRule]:
        """
        评估上下文，返回触发的规则
        
        Args:
            context: 上下文数据
            department: 部门筛选
            
        Returns:
            List[BusinessRule]: 触发的规则列表
        """
        triggered_rules = []
        
        with self._lock:
            rule_ids = (
                self.department_rules.get(department, [])
                if department
                else list(self.rules.keys())
            )
            
            for rule_id in rule_ids:
                rule = self.rules[rule_id]
                
                if rule.evaluate(context):
                    if rule.trigger():
                        triggered_rules.append(rule)
                        self.stats["rules_triggered"] += 1
        
        for rule in triggered_rules:
            await self.execution_queue.put({
                "rule": rule,
                "context": context,
                "timestamp": time.time()
            })
        
        return triggered_rules
    
    async def _execute_rule_task(self, task: Dict):
        rule = task["rule"]
        context = task["context"]
        
        fsm = self.rule_fsms[rule.rule_id]
        fsm.transition(RuleState.EXECUTING, "Starting execution")
        
        start_time = time.time()
        success = True
        
        try:
            for action in rule.actions:
                action_success = await self._execute_action(action, context)
                if not action_success:
                    success = False
                    break
            
            rule.complete_execution(success)
            fsm.transition(
                RuleState.COMPLETED if success else RuleState.FAILED,
                "Execution completed" if success else "Execution failed"
            )
            
            if success:
                self.stats["rules_succeeded"] += 1
            else:
                self.stats["rules_failed"] += 1
            
            self.stats["rules_executed"] += 1
            
            execution_time = (time.time() - start_time) * 1000
            old_avg = self.stats["avg_execution_time_ms"]
            count = self.stats["rules_executed"]
            self.stats["avg_execution_time_ms"] = (
                old_avg * (count - 1) + execution_time
            ) / count
            
        except Exception as e:
            logger.error(f"Error executing rule {rule.rule_id}: {e}")
            rule.complete_execution(False)
            fsm.transition(RuleState.FAILED, str(e))
            self.stats["rules_failed"] += 1
    
    async def _execute_action(self, action: RuleAction, context: Dict) -> bool:
        handler = self.action_handlers.get(action.action_type)
        
        if handler is None:
            logger.warning(f"No handler for action type: {action.action_type}")
            return False
        
        try:
            result = await handler(action, context)
            return result
        except Exception as e:
            logger.error(f"Error executing action {action.action_id}: {e}")
            return False
    
    async def _handle_notify_action(self, action: RuleAction, context: Dict) -> bool:
        logger.info(f"Notify action: {action.parameters}")
        return True
    
    async def _handle_create_task_action(self, action: RuleAction, context: Dict) -> bool:
        logger.info(f"Create task action: target={action.target}, params={action.parameters}")
        return True
    
    async def _handle_update_cache_action(self, action: RuleAction, context: Dict) -> bool:
        logger.info(f"Update cache action: target={action.target}, params={action.parameters}")
        return True
    
    async def _handle_send_message_action(self, action: RuleAction, context: Dict) -> bool:
        if self.communication_bus:
            try:
                await self.communication_bus.send(
                    to=action.target,
                    message={
                        "type": action.parameters.get("message_type"),
                        "context": context,
                        "timestamp": time.time()
                    }
                )
                return True
            except Exception as e:
                logger.error(f"Failed to send message: {e}")
                return False
        return True
    
    async def _handle_log_event_action(self, action: RuleAction, context: Dict) -> bool:
        logger.info(f"Log event: {action.parameters}")
        return True
    
    async def _handle_adjust_parameter_action(self, action: RuleAction, context: Dict) -> bool:
        logger.info(f"Adjust parameter: target={action.target}, params={action.parameters}")
        return True
    
    async def _handle_trigger_alert_action(self, action: RuleAction, context: Dict) -> bool:
        logger.warning(f"Alert triggered: {action.parameters}")
        return True
    
    def get_rule(self, rule_id: str) -> Optional[BusinessRule]:
        return self.rules.get(rule_id)
    
    def get_department_rules(self, department: str) -> List[BusinessRule]:
        rule_ids = self.department_rules.get(department, [])
        return [self.rules[rid] for rid in rule_ids if rid in self.rules]
    
    def get_all_rules(self) -> List[BusinessRule]:
        return list(self.rules.values())
    
    def get_stats(self) -> Dict:
        with self._lock:
            return {
                **self.stats,
                "active_rules": sum(1 for r in self.rules.values() if r.state == RuleState.ACTIVE),
                "rules_by_department": {
                    dept: len(rules)
                    for dept, rules in self.department_rules.items()
                }
            }
