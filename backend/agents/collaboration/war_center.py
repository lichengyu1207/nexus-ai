"""
战时指挥中心模块
War Command Center Module

实现攻击检测、模式切换、建议融合和实时通信
"""

import os
import json
import time
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import threading
import queue
import random
import numpy as np

import torch
import torch.nn as nn
import torch.nn.functional as F

logger = logging.getLogger(__name__)


class SystemState(Enum):
    PEACETIME = "peacetime"
    WARTIME = "wartime"
    TRANSITIONING = "transitioning"


@dataclass
class AttackSignature:
    attack_id: str
    attack_type: str
    source_ip: str
    target_port: int
    intensity: float
    pattern: List[float]
    timestamp: datetime
    confidence: float


@dataclass
class DefenseAdvice:
    agent_id: str
    action: int
    confidence: float
    reasoning: str
    contribution_score: float
    timestamp: datetime


@dataclass
class FusedDecision:
    action: int
    confidence: float
    source_advices: List[DefenseAdvice]
    fusion_method: str
    timestamp: datetime


class AttackDetector:
    
    def __init__(
        self,
        threshold: float = 0.7,
        window_size: int = 100,
        anomaly_threshold: float = 3.0
    ):
        self.threshold = threshold
        self.window_size = window_size
        self.anomaly_threshold = anomaly_threshold
        
        self.baseline_stats: Dict[str, float] = {}
        self.recent_patterns: deque = deque(maxlen=window_size)
        self.attack_history: List[AttackSignature] = []
        
        self.detector_model = self._build_detector_model()
    
    def _build_detector_model(self) -> nn.Module:
        return nn.Sequential(
            nn.Linear(13, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Linear(16, 1),
            nn.Sigmoid()
        )
    
    def update_baseline(self, traffic_stats: Dict[str, float]):
        for key, value in traffic_stats.items():
            if key not in self.baseline_stats:
                self.baseline_stats[key] = {"mean": value, "std": 0, "count": 1}
            else:
                stats = self.baseline_stats[key]
                new_count = stats["count"] + 1
                new_mean = (stats["mean"] * stats["count"] + value) / new_count
                new_std = np.sqrt(
                    ((stats["count"] - 1) * stats["std"] ** 2 +
                     (value - stats["mean"]) ** 2) / new_count
                )
                self.baseline_stats[key] = {
                    "mean": new_mean,
                    "std": max(new_std, 0.01),
                    "count": new_count
                }
    
    def detect_anomaly(self, current_stats: Dict[str, float]) -> Tuple[bool, float, List[str]]:
        anomalies = []
        total_score = 0.0
        
        for key, value in current_stats.items():
            if key in self.baseline_stats:
                stats = self.baseline_stats[key]
                z_score = abs(value - stats["mean"]) / max(stats["std"], 0.01)
                
                if z_score > self.anomaly_threshold:
                    anomalies.append(key)
                    total_score += z_score
        
        anomaly_score = total_score / max(len(current_stats), 1)
        is_anomaly = len(anomalies) > 0 and anomaly_score > self.threshold
        
        return is_anomaly, anomaly_score, anomalies
    
    def detect_attack_pattern(self, state: np.ndarray) -> Tuple[bool, float, str]:
        state_tensor = torch.FloatTensor(state).unsqueeze(0)
        
        with torch.no_grad():
            attack_prob = self.detector_model(state_tensor).item()
        
        self.recent_patterns.append(state)
        
        attack_type = self._classify_attack_type(state)
        
        is_attack = attack_prob > self.threshold
        
        return is_attack, attack_prob, attack_type
    
    def _classify_attack_type(self, state: np.ndarray) -> str:
        if len(state) < 13:
            return "unknown"
        
        request_rate = state[0] if len(state) > 0 else 0
        error_rate = state[1] if len(state) > 1 else 0
        unique_ips = state[2] if len(state) > 2 else 0
        
        if request_rate > 0.8 and unique_ips > 0.7:
            return "ddos"
        elif error_rate > 0.6:
            return "injection"
        elif request_rate > 0.5 and unique_ips < 0.3:
            return "slow_loris"
        else:
            return "mixed"
    
    def record_attack(self, signature: AttackSignature):
        self.attack_history.append(signature)
    
    def get_recent_attacks(self, hours: int = 24) -> List[AttackSignature]:
        cutoff = datetime.now() - timedelta(hours=hours)
        return [a for a in self.attack_history if a.timestamp > cutoff]


class ModeSwitcher:
    
    def __init__(
        self,
        transition_timeout_ms: float = 100,
        min_attack_duration_s: float = 5.0
    ):
        self.transition_timeout_ms = transition_timeout_ms
        self.min_attack_duration_s = min_attack_duration_s
        
        self.current_state = SystemState.PEACETIME
        self.state_history: List[Tuple[SystemState, datetime]] = []
        self.transition_callbacks: Dict[SystemState, List[Callable]] = {
            SystemState.PEACETIME: [],
            SystemState.WARTIME: [],
            SystemState.TRANSITIONING: []
        }
        
        self.attack_start_time: Optional[datetime] = None
        self.consecutive_attacks = 0
        self.attack_threshold = 3
    
    def register_callback(self, state: SystemState, callback: Callable):
        self.transition_callbacks[state].append(callback)
    
    async def switch_to_wartime(self) -> bool:
        if self.current_state == SystemState.WARTIME:
            return True
        
        start_time = time.time()
        self.current_state = SystemState.TRANSITIONING
        self._notify_callbacks(SystemState.TRANSITIONING)
        
        try:
            for callback in self.transition_callbacks[SystemState.WARTIME]:
                if asyncio.iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()
            
            self.current_state = SystemState.WARTIME
            self.attack_start_time = datetime.now()
            self.state_history.append((SystemState.WARTIME, datetime.now()))
            self._notify_callbacks(SystemState.WARTIME)
            
            duration_ms = (time.time() - start_time) * 1000
            logger.info(f"Switched to wartime mode in {duration_ms:.2f}ms")
            
            return duration_ms < self.transition_timeout_ms
            
        except Exception as e:
            logger.error(f"Failed to switch to wartime: {e}")
            self.current_state = SystemState.PEACETIME
            return False
    
    async def switch_to_peacetime(self) -> bool:
        if self.current_state == SystemState.PEACETIME:
            return True
        
        if self.attack_start_time:
            duration = (datetime.now() - self.attack_start_time).total_seconds()
            if duration < self.min_attack_duration_s:
                logger.info(f"Attack duration {duration:.1f}s < minimum {self.min_attack_duration_s}s")
                return False
        
        self.current_state = SystemState.TRANSITIONING
        self._notify_callbacks(SystemState.TRANSITIONING)
        
        try:
            for callback in self.transition_callbacks[SystemState.PEACETIME]:
                if asyncio.iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()
            
            self.current_state = SystemState.PEACETIME
            self.attack_start_time = None
            self.consecutive_attacks = 0
            self.state_history.append((SystemState.PEACETIME, datetime.now()))
            self._notify_callbacks(SystemState.PEACETIME)
            
            logger.info("Switched to peacetime mode")
            return True
            
        except Exception as e:
            logger.error(f"Failed to switch to peacetime: {e}")
            return False
    
    def _notify_callbacks(self, state: SystemState):
        for callback in self.transition_callbacks[state]:
            try:
                callback()
            except Exception as e:
                logger.error(f"Callback error: {e}")
    
    def process_detection(self, is_attack: bool, confidence: float) -> bool:
        if is_attack and confidence > 0.7:
            self.consecutive_attacks += 1
            if self.consecutive_attacks >= self.attack_threshold:
                return True
        else:
            self.consecutive_attacks = max(0, self.consecutive_attacks - 1)
        
        return False
    
    def get_status(self) -> Dict:
        return {
            "current_state": self.current_state.value,
            "consecutive_attacks": self.consecutive_attacks,
            "attack_threshold": self.attack_threshold,
            "attack_start_time": self.attack_start_time.isoformat() if self.attack_start_time else None,
            "state_history_count": len(self.state_history)
        }


class AdviceFuser:
    
    def __init__(
        self,
        n_advices: int = 8,
        action_dim: int = 8,
        min_consensus: float = 0.5
    ):
        self.n_advices = n_advices
        self.action_dim = action_dim
        self.min_consensus = min_consensus
        
        self.advice_weights: Dict[str, float] = {}
        self.fusion_history: List[FusedDecision] = []
        self.feedback_history: deque = deque(maxlen=100)
    
    def fuse_weighted_average(self, advices: List[DefenseAdvice]) -> FusedDecision:
        if not advices:
            return FusedDecision(
                action=0,
                confidence=0.0,
                source_advices=[],
                fusion_method="none",
                timestamp=datetime.now()
            )
        
        action_probs = torch.zeros(self.action_dim)
        total_weight = 0.0
        
        for advice in advices:
            weight = self.advice_weights.get(advice.agent_id, advice.contribution_score)
            action_probs[advice.action] += advice.confidence * weight
            total_weight += weight
        
        if total_weight > 0:
            action_probs /= total_weight
        
        best_action = torch.argmax(action_probs).item()
        confidence = action_probs[best_action].item()
        
        return FusedDecision(
            action=best_action,
            confidence=confidence,
            source_advices=advices,
            fusion_method="weighted_average",
            timestamp=datetime.now()
        )
    
    def fuse_voting(self, advices: List[DefenseAdvice]) -> FusedDecision:
        if not advices:
            return FusedDecision(
                action=0,
                confidence=0.0,
                source_advices=[],
                fusion_method="none",
                timestamp=datetime.now()
            )
        
        votes = torch.zeros(self.action_dim)
        weighted_votes = torch.zeros(self.action_dim)
        
        for advice in advices:
            weight = self.advice_weights.get(advice.agent_id, advice.contribution_score)
            votes[advice.action] += 1
            weighted_votes[advice.action] += weight
        
        best_action = torch.argmax(weighted_votes).item()
        vote_ratio = votes[best_action].item() / len(advices)
        
        return FusedDecision(
            action=best_action,
            confidence=vote_ratio,
            source_advices=advices,
            fusion_method="voting",
            timestamp=datetime.now()
        )
    
    def fuse_confidence_weighted(self, advices: List[DefenseAdvice]) -> FusedDecision:
        if not advices:
            return FusedDecision(
                action=0,
                confidence=0.0,
                source_advices=[],
                fusion_method="none",
                timestamp=datetime.now()
            )
        
        action_scores = torch.zeros(self.action_dim)
        total_confidence = 0.0
        
        for advice in advices:
            weight = advice.confidence * self.advice_weights.get(
                advice.agent_id, advice.contribution_score
            )
            action_scores[advice.action] += weight
            total_confidence += advice.confidence
        
        best_action = torch.argmax(action_scores).item()
        confidence = action_scores[best_action].item() / max(total_confidence, 0.01)
        
        return FusedDecision(
            action=best_action,
            confidence=confidence,
            source_advices=advices,
            fusion_method="confidence_weighted",
            timestamp=datetime.now()
        )
    
    def fuse_median(self, advices: List[DefenseAdvice]) -> FusedDecision:
        if not advices:
            return FusedDecision(
                action=0,
                confidence=0.0,
                source_advices=[],
                fusion_method="none",
                timestamp=datetime.now()
            )
        
        sorted_advices = sorted(advices, key=lambda a: a.action)
        median_idx = len(sorted_advices) // 2
        median_advice = sorted_advices[median_idx]
        
        return FusedDecision(
            action=median_advice.action,
            confidence=median_advice.confidence,
            source_advices=advices,
            fusion_method="median",
            timestamp=datetime.now()
        )
    
    def fuse(self, advices: List[DefenseAdvice], method: str = "confidence_weighted") -> FusedDecision:
        if method == "weighted_average":
            decision = self.fuse_weighted_average(advices)
        elif method == "voting":
            decision = self.fuse_voting(advices)
        elif method == "confidence_weighted":
            decision = self.fuse_confidence_weighted(advices)
        elif method == "median":
            decision = self.fuse_median(advices)
        else:
            decision = self.fuse_confidence_weighted(advices)
        
        self.fusion_history.append(decision)
        return decision
    
    def update_weights(self, feedback: Dict[str, float]):
        for agent_id, score in feedback.items():
            current = self.advice_weights.get(agent_id, 1.0)
            alpha = 0.1
            self.advice_weights[agent_id] = (1 - alpha) * current + alpha * score
            self.advice_weights[agent_id] = max(0.1, min(2.0, self.advice_weights[agent_id]))
        
        self.feedback_history.append({
            "timestamp": datetime.now().isoformat(),
            "feedback": feedback
        })
    
    def get_weights(self) -> Dict[str, float]:
        return self.advice_weights.copy()
    
    def get_fusion_stats(self) -> Dict:
        if not self.fusion_history:
            return {}
        
        recent = self.fusion_history[-100:]
        
        method_counts = {}
        for decision in recent:
            method = decision.fusion_method
            method_counts[method] = method_counts.get(method, 0) + 1
        
        return {
            "total_fusions": len(self.fusion_history),
            "recent_fusions": len(recent),
            "method_distribution": method_counts,
            "current_weights": self.get_weights()
        }


class WarBus:
    
    def __init__(self, max_queue_size: int = 10000):
        self.max_queue_size = max_queue_size
        
        self.advice_queue = queue.Queue(maxsize=max_queue_size)
        self.decision_queue = queue.Queue(maxsize=max_queue_size)
        self.feedback_queue = queue.Queue(maxsize=max_queue_size)
        
        self.subscribers: Dict[str, List[Callable]] = {
            "advice": [],
            "decision": [],
            "feedback": [],
            "alert": []
        }
        
        self.message_history: deque = deque(maxlen=1000)
        self.running = False
        self._worker_thread: Optional[threading.Thread] = None
    
    def subscribe(self, channel: str, callback: Callable):
        if channel in self.subscribers:
            self.subscribers[channel].append(callback)
    
    def unsubscribe(self, channel: str, callback: Callable):
        if channel in self.subscribers:
            try:
                self.subscribers[channel].remove(callback)
            except ValueError:
                pass
    
    def publish_advice(self, advice: DefenseAdvice):
        message = {
            "type": "advice",
            "data": advice,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            self.advice_queue.put_nowait(message)
            self.message_history.append(message)
        except queue.Full:
            logger.warning("Advice queue full, dropping message")
    
    def publish_decision(self, decision: FusedDecision):
        message = {
            "type": "decision",
            "data": decision,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            self.decision_queue.put_nowait(message)
            self.message_history.append(message)
        except queue.Full:
            logger.warning("Decision queue full, dropping message")
    
    def publish_feedback(self, feedback: Dict[str, float]):
        message = {
            "type": "feedback",
            "data": feedback,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            self.feedback_queue.put_nowait(message)
            self.message_history.append(message)
        except queue.Full:
            logger.warning("Feedback queue full, dropping message")
    
    def publish_alert(self, alert: Dict):
        message = {
            "type": "alert",
            "data": alert,
            "timestamp": datetime.now().isoformat()
        }
        
        for callback in self.subscribers["alert"]:
            try:
                callback(message)
            except Exception as e:
                logger.error(f"Alert callback error: {e}")
        
        self.message_history.append(message)
    
    def start(self):
        if self.running:
            return
        
        self.running = True
        self._worker_thread = threading.Thread(target=self._process_messages, daemon=True)
        self._worker_thread.start()
        logger.info("WarBus started")
    
    def stop(self):
        self.running = False
        if self._worker_thread:
            self._worker_thread.join(timeout=5)
        logger.info("WarBus stopped")
    
    def _process_messages(self):
        while self.running:
            try:
                if not self.advice_queue.empty():
                    message = self.advice_queue.get_nowait()
                    for callback in self.subscribers["advice"]:
                        try:
                            callback(message)
                        except Exception as e:
                            logger.error(f"Advice callback error: {e}")
                
                if not self.decision_queue.empty():
                    message = self.decision_queue.get_nowait()
                    for callback in self.subscribers["decision"]:
                        try:
                            callback(message)
                        except Exception as e:
                            logger.error(f"Decision callback error: {e}")
                
                if not self.feedback_queue.empty():
                    message = self.feedback_queue.get_nowait()
                    for callback in self.subscribers["feedback"]:
                        try:
                            callback(message)
                        except Exception as e:
                            logger.error(f"Feedback callback error: {e}")
                
                time.sleep(0.001)
                
            except Exception as e:
                logger.error(f"Message processing error: {e}")
    
    def get_stats(self) -> Dict:
        return {
            "running": self.running,
            "advice_queue_size": self.advice_queue.qsize(),
            "decision_queue_size": self.decision_queue.qsize(),
            "feedback_queue_size": self.feedback_queue.qsize(),
            "message_history_size": len(self.message_history),
            "subscribers": {k: len(v) for k, v in self.subscribers.items()}
        }


class WarCenter:
    
    def __init__(
        self,
        agent_cluster,
        config: Optional[Dict] = None
    ):
        self.agent_cluster = agent_cluster
        self.config = config or {}
        
        self.detector = AttackDetector()
        self.mode_switcher = ModeSwitcher()
        self.advice_fuser = AdviceFuser()
        self.war_bus = WarBus()
        
        self.mode_switcher.register_callback(
            SystemState.WARTIME,
            self._on_wartime_activation
        )
        self.mode_switcher.register_callback(
            SystemState.PEACETIME,
            self._on_peacetime_activation
        )
        
        self.war_bus.subscribe("decision", self._on_decision)
        self.war_bus.subscribe("feedback", self._on_feedback)
        
        self.collaboration_history: List[Dict] = []
        self.performance_metrics = {
            "wartime_activations": 0,
            "successful_defenses": 0,
            "failed_defenses": 0,
            "avg_response_time_ms": 0.0
        }
    
    async def _on_wartime_activation(self):
        logger.info("Wartime mode activated - switching agents")
        self.agent_cluster.set_wartime_mode()
        self.performance_metrics["wartime_activations"] += 1
        
        self.war_bus.publish_alert({
            "alert_type": "wartime_activation",
            "message": "System switched to wartime mode",
            "timestamp": datetime.now().isoformat()
        })
    
    async def _on_peacetime_activation(self):
        logger.info("Peacetime mode activated - switching agents")
        self.agent_cluster.set_peacetime_mode()
        
        self.war_bus.publish_alert({
            "alert_type": "peacetime_activation",
            "message": "System switched to peacetime mode",
            "timestamp": datetime.now().isoformat()
        })
    
    def _on_decision(self, message: Dict):
        decision = message["data"]
        logger.info(f"Decision made: action={decision.action}, confidence={decision.confidence:.2f}")
    
    def _on_feedback(self, message: Dict):
        feedback = message["data"]
        self.advice_fuser.update_weights(feedback)
        
        for agent_id, score in feedback.items():
            for attacker in self.agent_cluster.attackers:
                if attacker.agent_id == agent_id:
                    attacker.update_contribution(score)
    
    async def process_state(self, state: np.ndarray, traffic_stats: Dict[str, float]) -> Dict:
        start_time = time.time()
        
        self.detector.update_baseline(traffic_stats)
        is_anomaly, anomaly_score, anomalies = self.detector.detect_anomaly(traffic_stats)
        is_attack, attack_prob, attack_type = self.detector.detect_attack_pattern(state)
        
        should_switch = self.mode_switcher.process_detection(is_attack, attack_prob)
        
        if should_switch and self.mode_switcher.current_state != SystemState.WARTIME:
            await self.mode_switcher.switch_to_wartime()
        
        result = {
            "is_anomaly": is_anomaly,
            "anomaly_score": anomaly_score,
            "is_attack": is_attack,
            "attack_prob": attack_prob,
            "attack_type": attack_type,
            "system_state": self.mode_switcher.current_state.value,
            "processing_time_ms": (time.time() - start_time) * 1000
        }
        
        if self.mode_switcher.current_state == SystemState.WARTIME:
            state_tensor = torch.FloatTensor(state).unsqueeze(0)
            advices = self.agent_cluster.get_all_advices(state_tensor)
            
            defense_advices = []
            for advice_dict in advices:
                if advice_dict["top_advices"]:
                    top = advice_dict["top_advices"][0]
                    defense_advices.append(DefenseAdvice(
                        agent_id=advice_dict["agent_id"],
                        action=top["action"],
                        confidence=top["confidence"],
                        reasoning=f"Based on attack pattern: {attack_type}",
                        contribution_score=advice_dict["contribution_score"],
                        timestamp=datetime.now()
                    ))
            
            fused_decision = self.advice_fuser.fuse(defense_advices)
            
            self.war_bus.publish_decision(fused_decision)
            
            result["advices"] = [a.__dict__ for a in defense_advices]
            result["fused_decision"] = {
                "action": fused_decision.action,
                "confidence": fused_decision.confidence,
                "fusion_method": fused_decision.fusion_method
            }
            
            self.collaboration_history.append({
                "timestamp": datetime.now().isoformat(),
                "state": state.tolist(),
                "advices": result["advices"],
                "decision": result["fused_decision"]
            })
        
        return result
    
    async def report_defense_result(self, success: bool, feedback: Dict[str, float]):
        if success:
            self.performance_metrics["successful_defenses"] += 1
        else:
            self.performance_metrics["failed_defenses"] += 1
        
        self.war_bus.publish_feedback(feedback)
        
        if self.mode_switcher.current_state == SystemState.WARTIME:
            await self.mode_switcher.switch_to_peacetime()
    
    def start(self):
        self.war_bus.start()
        logger.info("War Center started")
    
    def stop(self):
        self.war_bus.stop()
        logger.info("War Center stopped")
    
    def get_status(self) -> Dict:
        return {
            "system_state": self.mode_switcher.current_state.value,
            "mode_switcher": self.mode_switcher.get_status(),
            "advice_fuser": self.advice_fuser.get_fusion_stats(),
            "war_bus": self.war_bus.get_stats(),
            "performance_metrics": self.performance_metrics,
            "collaboration_history_count": len(self.collaboration_history),
            "agent_cluster": self.agent_cluster.get_cluster_status()
        }
