"""
安全与冗余机制模块
Security and Redundancy Module

实现建议验证、恶意检测、冗余设计和健康监控
"""

import os
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import random
import numpy as np

import torch

logger = logging.getLogger(__name__)


class AdviceValidator:
    
    def __init__(
        self,
        history_window: int = 100,
        similarity_threshold: float = 0.8,
        consistency_threshold: float = 0.7
    ):
        self.history_window = history_window
        self.similarity_threshold = similarity_threshold
        self.consistency_threshold = consistency_threshold
        
        self.advice_history: List[Dict] = []
        self.success_patterns: Dict[int, List[float]] = {}
    
    def validate_advice(
        self,
        advice: Dict,
        current_state: np.ndarray,
        historical_context: Optional[List[Dict]] = None
    ) -> Tuple[bool, float, str]:
        is_valid = True
        confidence = advice.get("confidence", 0.0)
        reason = "OK"
        
        similarity_score = self._check_similarity(advice, current_state)
        if similarity_score < self.similarity_threshold:
            is_valid = False
            confidence *= similarity_score
            reason = f"Low similarity: {similarity_score:.2f}"
        
        consistency_score = self._check_consistency(advice, historical_context)
        if consistency_score < self.consistency_threshold:
            is_valid = False
            confidence *= consistency_score
            reason = f"Low consistency: {consistency_score:.2f}"
        
        action = advice.get("action", 0)
        if action in self.success_patterns:
            pattern = self.success_patterns[action]
            if len(pattern) > 0:
                success_rate = np.mean(pattern[-10:]) if len(pattern) >= 10 else np.mean(pattern)
                confidence *= (0.5 + 0.5 * success_rate)
        
        return is_valid, confidence, reason
    
    def _check_similarity(self, advice: Dict, current_state: np.ndarray) -> float:
        action = advice.get("action", 0)
        
        similar_states = []
        for hist in self.advice_history[-self.history_window:]:
            if hist.get("advice", {}).get("action") == action:
                similar_states.append(hist.get("state"))
        
        if not similar_states:
            return 1.0
        
        similarities = []
        for hist_state in similar_states:
            if isinstance(hist_state, np.ndarray) and isinstance(current_state, np.ndarray):
                if hist_state.shape == current_state.shape:
                    sim = np.dot(hist_state, current_state) / (
                        np.linalg.norm(hist_state) * np.linalg.norm(current_state) + 1e-8
                    )
                    similarities.append(sim)
        
        return np.mean(similarities) if similarities else 1.0
    
    def _check_consistency(self, advice: Dict, historical_context: Optional[List[Dict]]) -> float:
        if not historical_context:
            return 1.0
        
        action = advice.get("action", 0)
        recent_actions = [ctx.get("action") for ctx in historical_context[-10:]]
        
        if not recent_actions:
            return 1.0
        
        same_action_count = sum(1 for a in recent_actions if a == action)
        consistency = same_action_count / len(recent_actions)
        
        return consistency
    
    def record_advice_outcome(
        self,
        advice: Dict,
        state: np.ndarray,
        outcome: bool
    ):
        self.advice_history.append({
            "advice": advice,
            "state": state.tolist() if isinstance(state, np.ndarray) else state,
            "outcome": outcome,
            "timestamp": datetime.now().isoformat()
        })
        
        action = advice.get("action", 0)
        if action not in self.success_patterns:
            self.success_patterns[action] = []
        
        self.success_patterns[action].append(1.0 if outcome else 0.0)
        
        if len(self.success_patterns[action]) > 100:
            self.success_patterns[action] = self.success_patterns[action][-100:]
    
    def get_validation_stats(self) -> Dict:
        return {
            "history_size": len(self.advice_history),
            "success_patterns": {
                k: np.mean(v) if v else 0.0
                for k, v in self.success_patterns.items()
            }
        }


class MaliciousDetector:
    
    def __init__(
        self,
        deviation_threshold: float = 2.0,
        history_window: int = 50,
        min_samples: int = 5
    ):
        self.deviation_threshold = deviation_threshold
        self.history_window = history_window
        self.min_samples = min_samples
        
        self.agent_stats: Dict[str, Dict] = {}
        self.malicious_agents: List[str] = []
    
    def detect_malicious(
        self,
        agent_id: str,
        advice: Dict,
        expected_range: Optional[Tuple[float, float]] = None
    ) -> Tuple[bool, float]:
        if agent_id not in self.agent_stats:
            self.agent_stats[agent_id] = {
                "advices": [],
                "deviations": [],
                "malicious_score": 0.0
            }
        
        stats = self.agent_stats[agent_id]
        stats["advices"].append(advice)
        
        if len(stats["advices"]) > self.history_window:
            stats["advices"] = stats["advices"][-self.history_window:]
        
        if expected_range:
            min_expected, max_expected = expected_range
            confidence = advice.get("confidence", 0.5)
            
            deviation = 0.0
            if confidence < min_expected:
                deviation = (min_expected - confidence) / min_expected
            elif confidence > max_expected:
                deviation = (confidence - max_expected) / max_expected
            
            stats["deviations"].append(deviation)
            
            if len(stats["deviations"]) > self.history_window:
                stats["deviations"] = stats["deviations"][-self.history_window:]
        
        recent_deviations = stats["deviations"][-self.min_samples:]
        if len(recent_deviations) >= self.min_samples:
            avg_deviation = np.mean(recent_deviations)
            
            if avg_deviation > self.deviation_threshold:
                stats["malicious_score"] = min(1.0, avg_deviation / self.deviation_threshold)
                
                if agent_id not in self.malicious_agents:
                    self.malicious_agents.append(agent_id)
                    logger.warning(f"Agent {agent_id} flagged as potentially malicious")
                
                return True, stats["malicious_score"]
        
        if agent_id in self.malicious_agents:
            self.malicious_agents.remove(agent_id)
        
        return False, stats.get("malicious_score", 0.0)
    
    def get_agent_trust_score(self, agent_id: str) -> float:
        if agent_id in self.malicious_agents:
            return 0.0
        
        stats = self.agent_stats.get(agent_id, {})
        return 1.0 - stats.get("malicious_score", 0.0)
    
    def get_malicious_report(self) -> Dict:
        return {
            "malicious_agents": self.malicious_agents,
            "agent_stats": {
                k: {
                    "advice_count": len(v["advices"]),
                    "avg_deviation": np.mean(v["deviations"]) if v["deviations"] else 0.0,
                    "malicious_score": v["malicious_score"]
                }
                for k, v in self.agent_stats.items()
            }
        }


class RedundancyManager:
    
    def __init__(
        self,
        min_attackers: int = 3,
        min_defenders: int = 2,
        health_check_interval: int = 10
    ):
        self.min_attackers = min_attackers
        self.min_defenders = min_defenders
        self.health_check_interval = health_check_interval
        
        self.agent_health: Dict[str, Dict] = {}
        self.last_check_time: Dict[str, float] = {}
    
    def register_agent(self, agent_id: str, role: str):
        self.agent_health[agent_id] = {
            "role": role,
            "status": "healthy",
            "last_heartbeat": time.time(),
            "failure_count": 0,
            "recovery_count": 0
        }
    
    def heartbeat(self, agent_id: str):
        if agent_id in self.agent_health:
            self.agent_health[agent_id]["last_heartbeat"] = time.time()
            self.agent_health[agent_id]["status"] = "healthy"
    
    def check_health(self) -> Dict[str, str]:
        current_time = time.time()
        status_report = {}
        
        for agent_id, health in self.agent_health.items():
            time_since_heartbeat = current_time - health["last_heartbeat"]
            
            if time_since_heartbeat > self.health_check_interval:
                if health["status"] == "healthy":
                    health["failure_count"] += 1
                
                health["status"] = "unhealthy"
                status_report[agent_id] = "unhealthy"
            else:
                if health["status"] == "unhealthy":
                    health["recovery_count"] += 1
                health["status"] = "healthy"
                status_report[agent_id] = "healthy"
        
        return status_report
    
    def get_healthy_agents(self, role: Optional[str] = None) -> List[str]:
        self.check_health()
        
        healthy = []
        for agent_id, health in self.agent_health.items():
            if health["status"] == "healthy":
                if role is None or health["role"] == role:
                    healthy.append(agent_id)
        
        return healthy
    
    def has_sufficient_redundancy(self) -> Tuple[bool, Dict]:
        healthy_attackers = len(self.get_healthy_agents("attacker"))
        healthy_defenders = len(self.get_healthy_agents("defender"))
        
        sufficient = (
            healthy_attackers >= self.min_attackers and
            healthy_defenders >= self.min_defenders
        )
        
        return sufficient, {
            "attackers": healthy_attackers,
            "defenders": healthy_defenders,
            "min_attackers": self.min_attackers,
            "min_defenders": self.min_defenders
        }
    
    def get_redundancy_status(self) -> Dict:
        sufficient, counts = self.has_sufficient_redundancy()
        
        return {
            "sufficient": sufficient,
            "healthy_attackers": counts["attackers"],
            "healthy_defenders": counts["defenders"],
            "total_agents": len(self.agent_health),
            "agent_details": self.agent_health
        }


class ConsensusEngine:
    
    def __init__(
        self,
        consensus_threshold: float = 0.5,
        min_participants: int = 3
    ):
        self.consensus_threshold = consensus_threshold
        self.min_participants = min_participants
    
    def reach_consensus(
        self,
        advices: List[Dict],
        weights: Optional[Dict[str, float]] = None
    ) -> Tuple[int, float, Dict]:
        if len(advices) < self.min_participants:
            if advices:
                return advices[0].get("action", 0), 1.0, {"method": "single"}
            return 0, 0.0, {"method": "none"}
        
        action_votes: Dict[int, float] = {}
        
        for advice in advices:
            action = advice.get("action", 0)
            confidence = advice.get("confidence", 0.5)
            agent_id = advice.get("agent_id", "")
            
            weight = 1.0
            if weights and agent_id in weights:
                weight = weights[agent_id]
            
            vote_weight = confidence * weight
            
            if action not in action_votes:
                action_votes[action] = 0.0
            action_votes[action] += vote_weight
        
        if not action_votes:
            return 0, 0.0, {"method": "no_votes"}
        
        total_votes = sum(action_votes.values())
        if total_votes == 0:
            return 0, 0.0, {"method": "zero_votes"}
        
        best_action = max(action_votes.keys(), key=lambda k: action_votes[k])
        consensus_ratio = action_votes[best_action] / total_votes
        
        return best_action, consensus_ratio, {
            "method": "consensus",
            "consensus_ratio": consensus_ratio,
            "action_votes": {k: v / total_votes for k, v in action_votes.items()},
            "participants": len(advices)
        }
    
    def check_consensus_quality(self, consensus_result: Dict) -> Tuple[bool, str]:
        consensus_ratio = consensus_result.get("consensus_ratio", 0)
        participants = consensus_result.get("participants", 0)
        
        if participants < self.min_participants:
            return False, f"Insufficient participants: {participants} < {self.min_participants}"
        
        if consensus_ratio < self.consensus_threshold:
            return False, f"Low consensus: {consensus_ratio:.2f} < {self.consensus_threshold}"
        
        return True, "Consensus achieved"


class SecurityManager:
    
    def __init__(
        self,
        agent_cluster,
        redundancy_config: Optional[Dict] = None
    ):
        self.agent_cluster = agent_cluster
        
        config = redundancy_config or {}
        self.validator = AdviceValidator(
            history_window=config.get("history_window", 100),
            similarity_threshold=config.get("similarity_threshold", 0.8)
        )
        
        self.malicious_detector = MaliciousDetector(
            deviation_threshold=config.get("deviation_threshold", 2.0)
        )
        
        self.redundancy_manager = RedundancyManager(
            min_attackers=config.get("min_attackers", 3),
            min_defenders=config.get("min_defenders", 2)
        )
        
        self.consensus_engine = ConsensusEngine(
            consensus_threshold=config.get("consensus_threshold", 0.5)
        )
        
        for attacker in agent_cluster.attackers:
            self.redundancy_manager.register_agent(attacker.agent_id, "attacker")
        
        for defender in agent_cluster.defenders:
            self.redundancy_manager.register_agent(defender.agent_id, "defender")
        
        self.security_log: List[Dict] = []
    
    def validate_and_filter_advices(
        self,
        advices: List[Dict],
        state: np.ndarray,
        historical_context: Optional[List[Dict]] = None
    ) -> List[Dict]:
        valid_advices = []
        
        for advice in advices:
            agent_id = advice.get("agent_id", "")
            
            is_malicious, malicious_score = self.malicious_detector.detect_malicious(
                agent_id, advice
            )
            
            if is_malicious:
                self._log_security_event(
                    "malicious_detected",
                    {"agent_id": agent_id, "score": malicious_score}
                )
                continue
            
            is_valid, adjusted_confidence, reason = self.validator.validate_advice(
                advice, state, historical_context
            )
            
            if is_valid:
                advice["confidence"] = adjusted_confidence
                advice["validated"] = True
                valid_advices.append(advice)
            else:
                self._log_security_event(
                    "advice_rejected",
                    {"agent_id": agent_id, "reason": reason}
                )
        
        return valid_advices
    
    def secure_fuse(
        self,
        advices: List[Dict],
        state: np.ndarray
    ) -> Tuple[int, float, Dict]:
        valid_advices = self.validate_and_filter_advices(advices, state)
        
        if not valid_advices:
            return 0, 0.0, {"method": "no_valid_advices"}
        
        weights = {}
        for advice in valid_advices:
            agent_id = advice.get("agent_id", "")
            weights[agent_id] = self.malicious_detector.get_agent_trust_score(agent_id)
        
        action, confidence, consensus_info = self.consensus_engine.reach_consensus(
            valid_advices, weights
        )
        
        sufficient, redundancy_info = self.redundancy_manager.has_sufficient_redundancy()
        
        return action, confidence, {
            "consensus": consensus_info,
            "redundancy": redundancy_info,
            "valid_advices_count": len(valid_advices),
            "original_count": len(advices)
        }
    
    def record_outcome(
        self,
        state: np.ndarray,
        advices: List[Dict],
        final_action: int,
        success: bool
    ):
        for advice in advices:
            self.validator.record_advice_outcome(
                advice, state,
                advice.get("action") == final_action and success
            )
    
    def heartbeat(self, agent_id: str):
        self.redundancy_manager.heartbeat(agent_id)
    
    def get_security_status(self) -> Dict:
        return {
            "redundancy": self.redundancy_manager.get_redundancy_status(),
            "malicious_detection": self.malicious_detector.get_malicious_report(),
            "validation_stats": self.validator.get_validation_stats(),
            "security_log_count": len(self.security_log)
        }
    
    def _log_security_event(self, event_type: str, details: Dict):
        self.security_log.append({
            "type": event_type,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        
        if len(self.security_log) > 1000:
            self.security_log = self.security_log[-1000:]
