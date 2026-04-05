"""
涌现智能设计模块
Emergence Intelligence Design Module

实现局部规则、动态奖励场和涌现行为分析
"""

import os
import json
import time
import logging
import threading
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import deque, defaultdict
import random
import math

import numpy as np

logger = logging.getLogger(__name__)


class DefenseState(Enum):
    NORMAL = "normal"
    SUSPICIOUS = "suspicious"
    ATTACKING = "attacking"
    DEFENDING = "defending"
    COOLDOWN = "cooldown"


class RuleAction(Enum):
    OBSERVE = "observe"
    ALERT = "alert"
    LIMIT_RATE = "limit_rate"
    BLOCK = "block"
    COORDINATE = "coordinate"
    ESCALATE = "escalate"


@dataclass
class LocalRule:
    rule_id: str
    name: str
    condition: Callable[[Dict], bool]
    action: RuleAction
    priority: int = 0
    cooldown_seconds: float = 1.0
    enabled: bool = True
    trigger_count: int = 0
    last_triggered: float = 0
    
    def to_dict(self) -> Dict:
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "action": self.action.value,
            "priority": self.priority,
            "cooldown_seconds": self.cooldown_seconds,
            "enabled": self.enabled,
            "trigger_count": self.trigger_count,
            "last_triggered": self.last_triggered
        }


class DefenseLocalRules:
    
    def __init__(
        self,
        agent_id: str,
        blackboard,
        communication,
        rate_threshold: float = 100.0,
        suspicion_threshold: float = 3.0,
        coordination_threshold: int = 3,
        block_duration: float = 300.0
    ):
        self.agent_id = agent_id
        self.blackboard = blackboard
        self.communication = communication
        
        self.rate_threshold = rate_threshold
        self.suspicion_threshold = suspicion_threshold
        self.coordination_threshold = coordination_threshold
        self.block_duration = block_duration
        
        self.state = DefenseState.NORMAL
        self.state_history: deque = deque(maxlen=1000)
        
        self.rules: Dict[str, LocalRule] = {}
        self._init_default_rules()
        
        self.ip_tracking: Dict[str, Dict] = {}
        self.neighbor_reports: Dict[str, List[Dict]] = defaultdict(list)
        self.active_blocks: Dict[str, float] = {}
        
        self.stats = {
            "observations": 0,
            "alerts": 0,
            "rate_limits": 0,
            "blocks": 0,
            "coordinations": 0
        }
        
        self._running = False
        self._rule_thread = None
    
    def _init_default_rules(self):
        self.add_rule(LocalRule(
            rule_id="rule_high_rate",
            name="High Request Rate Detection",
            condition=lambda ctx: ctx.get("request_rate", 0) > self.rate_threshold,
            action=RuleAction.LIMIT_RATE,
            priority=10
        ))
        
        self.add_rule(LocalRule(
            rule_id="rule_sustained_suspicion",
            name="Sustained Suspicious Activity",
            condition=lambda ctx: ctx.get("suspicion_duration", 0) > self.suspicion_threshold,
            action=RuleAction.ALERT,
            priority=20
        ))
        
        self.add_rule(LocalRule(
            rule_id="rule_neighbor_consensus",
            name="Neighbor Consensus Attack",
            condition=lambda ctx: ctx.get("neighbor_reports", 0) >= self.coordination_threshold,
            action=RuleAction.BLOCK,
            priority=30
        ))
        
        self.add_rule(LocalRule(
            rule_id="rule_escalate_attack",
            name="Escalate Confirmed Attack",
            condition=lambda ctx: ctx.get("confirmed_attack", False),
            action=RuleAction.ESCALATE,
            priority=40
        ))
    
    def add_rule(self, rule: LocalRule):
        self.rules[rule.rule_id] = rule
        logger.info(f"Added rule {rule.rule_id}: {rule.name}")
    
    def remove_rule(self, rule_id: str) -> bool:
        if rule_id in self.rules:
            del self.rules[rule_id]
            return True
        return False
    
    def update_rule(self, rule_id: str, updates: Dict) -> bool:
        rule = self.rules.get(rule_id)
        if not rule:
            return False
        
        for key, value in updates.items():
            if hasattr(rule, key):
                setattr(rule, key, value)
        
        return True
    
    def evaluate(self, Context: Dict) -> List[Tuple[LocalRule, Dict]]:
        triggered_rules = []
        current_time = time.time()
        
        sorted_rules = sorted(self.rules.values(), key=lambda r: r.priority, reverse=True)
        
        for rule in sorted_rules:
            if not rule.enabled:
                continue
            
            if current_time - rule.last_triggered < rule.cooldown_seconds:
                continue
            
            try:
                if rule.condition(Context):
                    triggered_rules.append((rule, Context))
                    rule.trigger_count += 1
                    rule.last_triggered = current_time
            except Exception as e:
                logger.error(f"Error evaluating rule {rule.rule_id}: {e}")
        
        return triggered_rules
    
    def execute_action(self, rule: LocalRule, Context: Dict) -> Dict:
        action = rule.action
        result = {"rule_id": rule.rule_id, "action": action.value, "success": False}
        
        if action == RuleAction.OBSERVE:
            result["success"] = self._observe(Context)
            self.stats["observations"] += 1
        
        elif action == RuleAction.ALERT:
            result["success"] = self._alert(Context)
            self.stats["alerts"] += 1
        
        elif action == RuleAction.LIMIT_RATE:
            result["success"] = self._limit_rate(Context)
            self.stats["rate_limits"] += 1
        
        elif action == RuleAction.BLOCK:
            result["success"] = self._block(Context)
            self.stats["blocks"] += 1
        
        elif action == RuleAction.COORDINATE:
            result["success"] = self._coordinate(Context)
            self.stats["coordinations"] += 1
        
        elif action == RuleAction.ESCALATE:
            result["success"] = self._escalate(Context)
        
        self._record_state_change(rule, Context, result)
        
        return result
    
    def _observe(self, Context: Dict) -> bool:
        ip = Context.get("source_ip")
        if ip:
            if ip not in self.ip_tracking:
                self.ip_tracking[ip] = {
                    "first_seen": time.time(),
                    "request_count": 0,
                    "suspicion_level": 0
                }
            self.ip_tracking[ip]["request_count"] += 1
        return True
        return False
    
    def _alert(self, Context: Dict) -> bool:
        ip = Context.get("source_ip")
        if ip:
            self.state = DefenseState.SUSPICIOUS
            
            self.blackboard.write(
                f"alert:{ip}:{self.agent_id}",
                {
                    "agent_id": self.agent_id,
                    "source_ip": ip,
                    "timestamp": time.time(),
                    "context": Context
                },
                ttl=300)
            
            if self.communication:
                self.communication.broadcast(
                    MessageType.ALERT,
                    {
                        "alert_type": "suspicious_activity",
                        "source_ip": ip,
                        "reporter": self.agent_id
                    }
                )
            return True
        return False
    
    def _limit_rate(self, Context: Dict) -> bool:
        ip = Context.get("source_ip")
        if ip:
            self.state = DefenseState.DEFENDING
            
            self.blackboard.write(
                f"rate_limit:{ip}",
                {
                    "agent_id": self.agent_id,
                    "limit": self.rate_threshold * 0.5,
                    "timestamp": time.time()
                },
                ttl=60
            )
            return True
        return False
    
    def _block(self, Context: Dict) -> bool:
        ip = Context.get("source_ip")
        if ip:
            self.state = DefenseState.DEFENDING
            self.active_blocks[ip] = time.time() + self.block_duration
            
            self.blackboard.write(
                f"block:{ip}",
                {
                    "agent_id": self.agent_id,
                    "source_ip": ip,
                    "duration": self.block_duration,
                    "timestamp": time.time(),
                    "coordinated": True
                },
                ttl=int(self.block_duration))
            
            if self.communication:
                self.communication.broadcast(
                    MessageType.ALERT,
                {
                    "alert_type": "ip_blocked",
                    "source_ip": ip,
                    "reporter": self.agent_id,
                    "coordinated": True
                }
            )
            return True
        return False
    
    def _coordinate(self, Context: Dict) -> bool:
        ip = Context.get("source_ip")
        if ip:
            self.state = DefenseState.SUSPICIOUS
            
            if self.communication:
                self.communication.broadcast(
                    MessageType.COORDINATION,
                {
                    "coordination_type": "request_observation",
                    "source_ip": ip,
                    "requester": self.agent_id,
                    "context": Context
                }
            )
            return True
        return False
    
    def _escalate(self, Context: Dict) -> bool:
        ip = Context.get("source_ip")
        if ip:
            self.state = DefenseState.ATTACKING
            
            self.blackboard.write(
                "escalation:attack_detected",
                {
                    "agent_id": self.agent_id,
                    "source_ip": ip,
                    "severity": "high",
                    "timestamp": time.time(),
                    "context": Context
                })
            return True
        return False
    
    def _record_state_change(self, rule: LocalRule, Context: Dict, result: Dict):
        self.state_history.append({
            "timestamp": time.time(),
            "old_state": self.state.value,
            "rule_triggered": rule.rule_id,
            "action": rule.action.value,
            "success": result["success"],
            "context": Context
        })
    
    def receive_neighbor_report(self, from_agent: str, report: Dict):
        ip = report.get("source_ip")
        if ip:
            self.neighbor_reports[ip].append({
                "from_agent": from_agent,
                "timestamp": time.time(),
                "report": report
            })
            
            if len(self.neighbor_reports[ip]) >= self.coordination_threshold:
                self.evaluate({
                    "source_ip": ip,
                    "neighbor_reports": len(self.neighbor_reports[ip]),
                    "confirmed_attack": True
                })
    
    def process_request(self, source_ip: str, request_data: Dict) -> List[Dict]:
        ip_data = self.ip_tracking.get(source_ip, {
            "first_seen": time.time(),
            "request_count": 0,
            "suspicion_level": 0
        })
        
        ip_data["request_count"] += 1
        time_window = 60
        request_rate = ip_data["request_count"] / max(1, time.time() - ip_data["first_seen"])
        
        suspicion_duration = 0
        if ip_data["suspicion_level"] > 0:
            suspicion_duration = time.time() - ip_data.get("suspicion_start", time.time())
        
        Context = {
            "source_ip": source_ip,
            "request_rate": request_rate,
            "request_count": ip_data["request_count"],
            "suspicion_level": ip_data["suspicion_level"],
            "suspicion_duration": suspicion_duration,
            "neighbor_reports": len(self.neighbor_reports.get(source_ip, [])),
            "confirmed_attack": source_ip in self.active_blocks
        }
        
        triggered = self.evaluate(Context)
        
        results = []
        for rule, ctx in triggered:
            result = self.execute_action(rule, ctx)
            results.append(result)
        
        self.ip_tracking[source_ip] = ip_data
        
        return results
    
    def get_state(self) -> Dict:
        return {
            "agent_id": self.agent_id,
            "current_state": self.state.value,
            "rules": {rid: r.to_dict() for rid, r in self.rules.items()},
            "tracked_ips": len(self.ip_tracking),
            "active_blocks": len(self.active_blocks),
            "stats": self.stats.copy()
        }


class DynamicRewardField:
    
    def __init__(
        self,
        blackboard,
        base_reward: float = 1.0,
        penalty_weight: float = 0.5,
        bonus_weight: float = 0.3
    ):
        self.blackboard = blackboard
        self.base_reward = base_reward
        self.penalty_weight = penalty_weight
        self.bonus_weight = bonus_weight
        
        self.global_goals: Dict[str, Dict] = {}
        self.agent_rewards: Dict[str, float] = {}
        self.reward_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        self._init_default_goals()
    
    def _init_default_goals(self):
        self.set_global_goal(
            "defense_success_rate",
            target=0.98,
            weight=1.0,
            description="防御成功率应高于98%"
        )
        self.set_global_goal(
            "response_time",
            target=0.005,
            weight=0.8,
            description="平均响应时间应低于5ms",
            is_lower_better=True
        ),
        self.set_global_goal(
            "false_positive_rate",
            target=0.01,
            weight=0.6,
            description="误报率应低于1%",
            is_lower_better=True
        )
    
    def set_global_goal(
        self,
        goal_name: str,
        target: float,
        weight: float = 1.0,
        description: str = "",
        is_lower_better: bool = False
    ):
        self.global_goals[goal_name] = {
            "name": goal_name,
            "target": target,
            "weight": weight,
            "description": description,
            "is_lower_better": is_lower_better,
            "current_value": None,
            "last_updated": time.time()
        }
        
        self.blackboard.write(
            f"goal:{goal_name}",
            self.global_goals[goal_name]
        )
        
        logger.info(f"Set global goal: {goal_name} = {target}")
    
    def update_goal_progress(self, goal_name: str, current_value: float):
        if goal_name not in self.global_goals:
            return
        
        self.global_goals[goal_name]["current_value"] = current_value
        self.global_goals[goal_name]["last_updated"] = time.time()
        
        self.blackboard.write(
            f"goal:{goal_name}:progress",
            {"current_value": current_value, "timestamp": time.time()}
        )
    
    def calculate_reward(
        self,
        agent_id: str,
        action: str,
        outcome: Dict,
        context: Dict
    ) -> float:
        reward = self.base_reward
        
        success = outcome.get("success", False)
        if success:
            reward += self.bonus_weight
        else:
            reward -= self.penalty_weight
        
        goal_alignment = self._calculate_goal_alignment(action, outcome, context)
        reward += goal_alignment * self.bonus_weight
        
        if agent_id not in self.agent_rewards:
            self.agent_rewards[agent_id] = 0.0
        
        self.agent_rewards[agent_id] += reward
        self.reward_history[agent_id].append({
            "timestamp": time.time(),
            "action": action,
            "reward": reward,
            "outcome": outcome
        })
        
        return reward
    
    def _calculate_goal_alignment(self, action: str, outcome: Dict, context: Dict) -> float:
        alignment_score = 0.0
        total_weight = 0.0
        
        for goal_name, goal in self.global_goals.items():
            if goal["current_value"] is None:
                continue
            
            weight = goal["weight"]
            total_weight += weight
            
            target = goal["target"]
            current = goal["current_value"]
            
            if goal["is_lower_better"]:
                if current <= target:
                    alignment_score += weight
                else:
                    deviation = (current - target) / target
                    alignment_score += weight * max(0, 1 - deviation)
            else:
                if current >= target:
                    alignment_score += weight
                else:
                    deviation = (target - current) / target
                    alignment_score += weight * max(0, 1 - deviation)
        
        return alignment_score / max(total_weight, 1)
    
    def get_agent_reward(self, agent_id: str) -> float:
        return self.agent_rewards.get(agent_id, 0.0)
    
    def get_agent_reward_history(self, agent_id: str, limit: int = 100) -> List[Dict]:
        history = list(self.reward_history.get(agent_id, []))
        return history[-limit:]
    
    def get_top_performers(self, limit: int = 10) -> List[Tuple[str, float]]:
        sorted_agents = sorted(
            self.agent_rewards.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_agents[:limit]
    
    def get_goal_status(self) -> Dict:
        return {
            "goals": self.global_goals.copy(),
            "agent_count": len(self.agent_rewards),
            "total_rewards_distributed": sum(self.agent_rewards.values())
        }


class EmergenceAnalyzer:
    
    def __init__(
        self,
        blackboard,
        memory_system=None,
        pattern_threshold: int = 5,
        analysis_window: int = 3600
    ):
        self.blackboard = blackboard
        self.memory_system = memory_system
        self.pattern_threshold = pattern_threshold
        self.analysis_window = analysis_window
        
        self.communication_logs: deque = deque(maxlen=10000)
        self.state_changes: deque = deque(maxlen=10000)
        self.task_participations: deque = deque(maxlen=10000)
        
        self.interaction_graph: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self.detected_patterns: Dict[str, Dict] = {}
        
        self._running = False
        self._analysis_thread = None
    
    def start(self):
        self._running = True
        self._analysis_thread = threading.Thread(target=self._analysis_loop, daemon=True)
        self._analysis_thread.start()
        logger.info("Emergence Analyzer started")
    
    def stop(self):
        self._running = False
        logger.info("Emergence Analyzer stopped")
    
    def _analysis_loop(self):
        while self._running:
            try:
                self._analyze_patterns()
                time.sleep(10)
            except Exception as e:
                logger.error(f"Error in analysis loop: {e}")
                time.sleep(1)
    
    def record_communication(self, message: Dict):
        self.communication_logs.append({
            **message,
            "recorded_at": time.time()
        })
        
        from_agent = message.get("from_agent")
        to_agent = message.get("to_agent")
        
        if from_agent and to_agent:
            self.interaction_graph[from_agent][to_agent] += 1
    
    def record_state_change(self, agent_id: str, old_state: str, new_state: str, context: Dict = None):
        self.state_changes.append({
            "agent_id": agent_id,
            "old_state": old_state,
            "new_state": new_state,
            "context": context or {},
            "recorded_at": time.time()
        })
    
    def record_task_participation(self, task_id: str, agent_ids: List[str], outcome: str):
        self.task_participations.append({
            "task_id": task_id,
            "agent_ids": agent_ids,
            "outcome": outcome,
            "recorded_at": time.time()
        })
    
    def _analyze_patterns(self):
        cutoff = time.time() - self.analysis_window
        
        recent_communications = [
            c for c in self.communication_logs
 if c.get("recorded_at", 0) > cutoff
        ]
        recent_states = [
            s for s in self.state_changes
 if s.get("recorded_at", 0) > cutoff
        ]
        recent_tasks = [
            t for t in self.task_participations
 if t.get("recorded_at", 0) > cutoff
        ]
        
        patterns = []
        patterns.extend(self._detect_chain_patterns(recent_communications))
        patterns.extend(self._detect_team_patterns(recent_tasks))
        patterns.extend(self._detect_state_patterns(recent_states))
        
        for pattern in patterns:
            pattern_id = self._generate_pattern_id(pattern)
            if pattern_id not in self.detected_patterns:
                self.detected_patterns[pattern_id] = {
                    "pattern": pattern,
                    "first_detected": time.time(),
                    "occurrence_count": 1
                }
                self._store_emergence_pattern(pattern)
            else:
                self.detected_patterns[pattern_id]["occurrence_count"] += 1
    
    def _detect_chain_patterns(self, communications: List[Dict]) -> List[Dict]:
        patterns = []
        
        chains = defaultdict(list)
        for comm in communications:
            if comm.get("to_agent"):
                key = (comm["from_agent"], comm["to_agent"])
                chains[key].append(comm)
        
        for (from_agent, to_agent), comms in chains.items():
            if len(comms) >= self.pattern_threshold:
                patterns.append({
                    "type": "communication_chain",
                    "from": from_agent,
                    "to": to_agent,
                    "frequency": len(comms),
                    "message_types": list(set(c.get("message_type") for c in comms if c.get("message_type")))
                })
        
        return patterns
    
    def _detect_team_patterns(self, tasks: List[Dict]) -> List[Dict]:
        patterns = []
        
        team_compositions = defaultdict(list)
        for task in tasks:
            team_key = tuple(sorted(task["agent_ids"]))
            team_compositions[team_key].append(task)
        
        for team, team_tasks in team_compositions.items():
            if len(team_tasks) >= self.pattern_threshold:
                success_rate = sum(1 for t in team_tasks if t["outcome"] == "success") / len(team_tasks)
                patterns.append({
                    "type": "stable_team",
                    "members": list(team),
                    "task_count": len(team_tasks),
                    "success_rate": success_rate
                })
        
        return patterns
    
    def _detect_state_patterns(self, states: List[Dict]) -> List[Dict]:
        patterns = []
        
        state_sequences = defaultdict(list)
        for i, state in enumerate(states[:-1]):
            next_state = states[i + 1]
            if state["agent_id"] == next_state["agent_id"]:
                key = (state["new_state"], next_state["new_state"])
                state_sequences[(state["agent_id"], key)].append(state)
        
        for (agent_id, (old, new)), seq in state_sequences.items():
            if len(seq) >= self.pattern_threshold:
                patterns.append({
                    "type": "state_transition_pattern",
                    "agent_id": agent_id,
                    "from_state": old,
                    "to_state": new,
                    "frequency": len(seq)
                })
        
        return patterns
    
    def _generate_pattern_id(self, pattern: Dict) -> str:
        pattern_str = json.dumps(pattern, sort_keys=True)
        return hashlib.md5(pattern_str.encode()).hexdigest()[:16]
    
    def _store_emergence_pattern(self, pattern: Dict):
        if self.memory_system:
            try:
                self.memory_system.store_episodic(
                    event_type="emergence_pattern",
                    content=pattern,
                    importance=0.8
                )
            except Exception as e:
                logger.error(f"Failed to store emergence pattern: {e}")
        
        self.blackboard.write(
            f"emergence:pattern:{self._generate_pattern_id(pattern)}",
            pattern,
            ttl=86400)
    
    def get_interaction_graph(self) -> Dict:
        return {
            "nodes": list(set(
                list(self.interaction_graph.keys()) +
                [t for targets in self.interaction_graph.values() for t in targets]
            )),
            "edges": [
                {"source": s, "target": t, "weight": w}
                for s, targets in self.interaction_graph.items()
                for t, w in targets.items()
            ]
        }
    
    def get_detected_patterns(self) -> List[Dict]:
        return [
            {
                "pattern_id": pid,
                **pdata
            }
            for pid, pdata in self.detected_patterns.items()
        ]
    
    def get_stats(self) -> Dict:
        return {
            "communication_logs": len(self.communication_logs),
            "state_changes": len(self.state_changes),
            "task_participations": len(self.task_participations),
            "detected_patterns": len(self.detected_patterns),
            "unique_agents": len(set(
                list(self.interaction_graph.keys()) +
                [t for targets in self.interaction_graph.values() for t in targets]
            ))
        }
