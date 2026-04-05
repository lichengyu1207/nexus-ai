"""
评估器模块
Evaluator Module

实现防御性能指标、博弈论指标、实时性指标评估
"""

import json
import time
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import deque
import random
import logging

import torch
import torch.nn as nn

logger = logging.getLogger(__name__)


@dataclass
class EvaluationConfig:
    n_eval_episodes: int = 100
    n_attack_types: int = 7
    target_tpr: float = 0.98
    target_fpr: float = 0.01
    target_latency_ms: float = 5.0
    target_service_availability: float = 0.999
    convergence_threshold: float = 0.01
    nash_equilibrium_samples: int = 1000


class DefenseMetrics:
    
    def __init__(self):
        self.true_positives = 0
        self.false_positives = 0
        self.true_negatives = 0
        self.false_negatives = 0
        
        self.total_attacks = 0
        self.blocked_attacks = 0
        self.missed_attacks = 0
        
        self.service_down_events = 0
        self.total_timesteps = 0
        
        self.response_times: List[float] = []
        self.error_rates: List[float] = []
    
    def update(
        self,
        attack_occurred: bool,
        attack_blocked: bool,
        false_positive: bool,
        service_available: bool,
        response_time: float,
        error_rate: float
    ):
        self.total_timesteps += 1
        
        if attack_occurred:
            self.total_attacks += 1
            if attack_blocked:
                self.true_positives += 1
                self.blocked_attacks += 1
            else:
                self.false_negatives += 1
                self.missed_attacks += 1
        else:
            if false_positive:
                self.false_positives += 1
            else:
                self.true_negatives += 1
        
        if not service_available:
            self.service_down_events += 1
        
        self.response_times.append(response_time)
        self.error_rates.append(error_rate)
    
    def get_tpr(self) -> float:
        if self.true_positives + self.false_negatives == 0:
            return 0.0
        return self.true_positives / (self.true_positives + self.false_negatives)
    
    def get_fpr(self) -> float:
        if self.false_positives + self.true_negatives == 0:
            return 0.0
        return self.false_positives / (self.false_positives + self.true_negatives)
    
    def get_precision(self) -> float:
        if self.true_positives + self.false_positives == 0:
            return 0.0
        return self.true_positives / (self.true_positives + self.false_positives)
    
    def get_f1_score(self) -> float:
        precision = self.get_precision()
        recall = self.get_tpr()
        if precision + recall == 0:
            return 0.0
        return 2 * precision * recall / (precision + recall)
    
    def get_accuracy(self) -> float:
        total = self.true_positives + self.true_negatives + self.false_positives + self.false_negatives
        if total == 0:
            return 0.0
        return (self.true_positives + self.true_negatives) / total
    
    def get_block_rate(self) -> float:
        if self.total_attacks == 0:
            return 0.0
        return self.blocked_attacks / self.total_attacks
    
    def get_service_availability(self) -> float:
        if self.total_timesteps == 0:
            return 1.0
        return 1.0 - (self.service_down_events / self.total_timesteps)
    
    def get_avg_response_time(self) -> float:
        if not self.response_times:
            return 0.0
        return np.mean(self.response_times)
    
    def get_p99_response_time(self) -> float:
        if not self.response_times:
            return 0.0
        return np.percentile(self.response_times, 99)
    
    def get_avg_error_rate(self) -> float:
        if not self.error_rates:
            return 0.0
        return np.mean(self.error_rates)
    
    def to_dict(self) -> Dict:
        return {
            "tpr": self.get_tpr(),
            "fpr": self.get_fpr(),
            "precision": self.get_precision(),
            "f1_score": self.get_f1_score(),
            "accuracy": self.get_accuracy(),
            "block_rate": self.get_block_rate(),
            "service_availability": self.get_service_availability(),
            "avg_response_time_ms": self.get_avg_response_time(),
            "p99_response_time_ms": self.get_p99_response_time(),
            "avg_error_rate": self.get_avg_error_rate(),
            "total_attacks": self.total_attacks,
            "blocked_attacks": self.blocked_attacks,
            "missed_attacks": self.missed_attacks,
            "false_positives": self.false_positives
        }


class GameTheoryMetrics:
    
    def __init__(self, n_actions: int = 8):
        self.n_actions = n_actions
        self.payoff_history: List[Dict] = []
        self.strategy_history: List[np.ndarray] = []
    
    def record_payoff(
        self,
        attacker_strategy: np.ndarray,
        defender_strategy: np.ndarray,
        attacker_payoff: float,
        defender_payoff: float
    ):
        self.payoff_history.append({
            "attacker_strategy": attacker_strategy.copy(),
            "defender_strategy": defender_strategy.copy(),
            "attacker_payoff": attacker_payoff,
            "defender_payoff": defender_payoff
        })
    
    def record_strategy(self, strategy: np.ndarray, role: str):
        self.strategy_history.append({
            "strategy": strategy.copy(),
            "role": role
        })
    
    def compute_exploitability(
        self,
        current_strategy: np.ndarray,
        best_response_payoff: float,
        current_payoff: float
    ) -> float:
        return best_response_payoff - current_payoff
    
    def compute_nash_distance(
        self,
        attacker_strategy: np.ndarray,
        defender_strategy: np.ndarray,
        payoff_matrix: Optional[np.ndarray] = None
    ) -> float:
        if payoff_matrix is None:
            payoff_matrix = self._estimate_payoff_matrix()
        
        attacker_value = np.dot(attacker_strategy, np.dot(payoff_matrix, defender_strategy))
        
        best_response_value = np.max(np.dot(payoff_matrix, defender_strategy))
        
        exploitability = best_response_value - attacker_value
        
        return float(exploitability)
    
    def _estimate_payoff_matrix(self) -> np.ndarray:
        payoff_matrix = np.zeros((self.n_actions, self.n_actions))
        
        for record in self.payoff_history[-100:]:
            a_strat = record["attacker_strategy"]
            d_strat = record["defender_strategy"]
            payoff = record["attacker_payoff"]
            
            for i, a_prob in enumerate(a_strat):
                for j, d_prob in enumerate(d_strat):
                    payoff_matrix[i, j] += payoff * a_prob * d_prob
        
        n = len(self.payoff_history[-100:])
        if n > 0:
            payoff_matrix /= n
        
        return payoff_matrix
    
    def compute_strategy_diversity(self, strategies: List[np.ndarray]) -> float:
        if len(strategies) < 2:
            return 0.0
        
        distances = []
        for i in range(len(strategies)):
            for j in range(i + 1, len(strategies)):
                dist = np.linalg.norm(strategies[i] - strategies[j])
                distances.append(dist)
        
        return float(np.mean(distances)) if distances else 0.0
    
    def compute_strategy_entropy(self, strategy: np.ndarray) -> float:
        strategy = np.clip(strategy, 1e-10, 1.0)
        entropy = -np.sum(strategy * np.log(strategy))
        max_entropy = np.log(len(strategy))
        return float(entropy / max_entropy) if max_entropy > 0 else 0.0
    
    def to_dict(self) -> Dict:
        recent_strategies = [s["strategy"] for s in self.strategy_history[-10:]]
        
        return {
            "n_payoff_records": len(self.payoff_history),
            "n_strategy_records": len(self.strategy_history),
            "strategy_diversity": self.compute_strategy_diversity(recent_strategies),
            "avg_strategy_entropy": float(np.mean([
                self.compute_strategy_entropy(s) for s in recent_strategies
            ])) if recent_strategies else 0.0
        }


class TrainingMetrics:
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        
        self.episode_rewards: deque = deque(maxlen=window_size)
        self.episode_lengths: deque = deque(maxlen=window_size)
        self.policy_losses: deque = deque(maxlen=window_size)
        self.value_losses: deque = deque(maxlen=window_size)
        
        self.convergence_history: List[float] = []
        self.best_reward = float('-inf')
    
    def record_episode(self, reward: float, length: int):
        self.episode_rewards.append(reward)
        self.episode_lengths.append(length)
        
        if reward > self.best_reward:
            self.best_reward = reward
    
    def record_loss(self, policy_loss: float, value_loss: float):
        self.policy_losses.append(policy_loss)
        self.value_losses.append(value_loss)
    
    def get_avg_reward(self) -> float:
        if not self.episode_rewards:
            return 0.0
        return float(np.mean(self.episode_rewards))
    
    def get_reward_std(self) -> float:
        if not self.episode_rewards:
            return 0.0
        return float(np.std(self.episode_rewards))
    
    def get_avg_length(self) -> float:
        if not self.episode_lengths:
            return 0.0
        return float(np.mean(self.episode_lengths))
    
    def get_avg_policy_loss(self) -> float:
        if not self.policy_losses:
            return 0.0
        return float(np.mean(self.policy_losses))
    
    def get_avg_value_loss(self) -> float:
        if not self.value_losses:
            return 0.0
        return float(np.mean(self.value_losses))
    
    def check_convergence(self, threshold: float = 0.01) -> bool:
        if len(self.episode_rewards) < self.window_size:
            return False
        
        recent_mean = np.mean(list(self.episode_rewards)[-50:])
        previous_mean = np.mean(list(self.episode_rewards)[-100:-50])
        
        improvement = abs(recent_mean - previous_mean)
        
        self.convergence_history.append(improvement)
        
        return improvement < threshold
    
    def to_dict(self) -> Dict:
        return {
            "avg_reward": self.get_avg_reward(),
            "reward_std": self.get_reward_std(),
            "best_reward": self.best_reward,
            "avg_episode_length": self.get_avg_length(),
            "avg_policy_loss": self.get_avg_policy_loss(),
            "avg_value_loss": self.get_avg_value_loss(),
            "converged": self.check_convergence(),
            "total_episodes": len(self.episode_rewards)
        }


class RealTimeMetrics:
    
    def __init__(self, window_size: int = 1000):
        self.window_size = window_size
        
        self.decision_latencies: deque = deque(maxlen=window_size)
        self.throughput_samples: deque = deque(maxlen=window_size)
        
        self.total_decisions = 0
        self.total_time = 0.0
    
    def record_decision(self, latency_ms: float):
        self.decision_latencies.append(latency_ms)
        self.total_decisions += 1
    
    def record_throughput(self, qps: float, duration_s: float):
        self.throughput_samples.append(qps)
        self.total_time += duration_s
    
    def get_avg_latency(self) -> float:
        if not self.decision_latencies:
            return 0.0
        return float(np.mean(self.decision_latencies))
    
    def get_p50_latency(self) -> float:
        if not self.decision_latencies:
            return 0.0
        return float(np.percentile(self.decision_latencies, 50))
    
    def get_p95_latency(self) -> float:
        if not self.decision_latencies:
            return 0.0
        return float(np.percentile(self.decision_latencies, 95))
    
    def get_p99_latency(self) -> float:
        if not self.decision_latencies:
            return 0.0
        return float(np.percentile(self.decision_latencies, 99))
    
    def get_max_latency(self) -> float:
        if not self.decision_latencies:
            return 0.0
        return float(np.max(self.decision_latencies))
    
    def get_avg_throughput(self) -> float:
        if not self.throughput_samples:
            return 0.0
        return float(np.mean(self.throughput_samples))
    
    def get_max_throughput(self) -> float:
        if not self.throughput_samples:
            return 0.0
        return float(np.max(self.throughput_samples))
    
    def meets_latency_target(self, target_ms: float = 5.0) -> bool:
        return self.get_p99_latency() <= target_ms
    
    def to_dict(self) -> Dict:
        return {
            "avg_latency_ms": self.get_avg_latency(),
            "p50_latency_ms": self.get_p50_latency(),
            "p95_latency_ms": self.get_p95_latency(),
            "p99_latency_ms": self.get_p99_latency(),
            "max_latency_ms": self.get_max_latency(),
            "avg_throughput_qps": self.get_avg_throughput(),
            "max_throughput_qps": self.get_max_throughput(),
            "total_decisions": self.total_decisions,
            "meets_latency_target": self.meets_latency_target()
        }


class Evaluator:
    
    def __init__(
        self,
        defense_agent,
        attack_agent,
        env,
        config: Optional[EvaluationConfig] = None,
        device: str = "cpu"
    ):
        self.defense_agent = defense_agent
        self.attack_agent = attack_agent
        self.env = env
        self.config = config or EvaluationConfig()
        self.device = device
        
        self.defense_metrics = DefenseMetrics()
        self.game_theory_metrics = GameTheoryMetrics()
        self.training_metrics = TrainingMetrics()
        self.realtime_metrics = RealTimeMetrics()
        
        self.evaluation_history: List[Dict] = []
        self.best_model_path: Optional[str] = None
        self.best_tpr = 0.0
    
    def evaluate_defense(
        self,
        n_episodes: Optional[int] = None,
        deterministic: bool = True
    ) -> Dict:
        n_episodes = n_episodes or self.config.n_eval_episodes
        
        self.defense_metrics = DefenseMetrics()
        
        for episode in range(n_episodes):
            states, _ = self.env.reset()
            defender_state = states["defender"]
            
            done = False
            episode_reward = 0.0
            
            while not done:
                start_time = time.time()
                
                action, _, _ = self.defense_agent.select_action(
                    defender_state, deterministic=deterministic
                )
                
                latency_ms = (time.time() - start_time) * 1000
                self.realtime_metrics.record_decision(latency_ms)
                
                attack_action = random.randint(0, 7)
                attack_intensity = random.random()
                
                states, rewards, done, info = self.env.step(
                    attack_action, attack_intensity, action
                )
                
                attack_occurred = attack_action > 0
                attack_blocked = info.get("defense_effect", {}).get("blocked", False)
                false_positive = info.get("defense_effect", {}).get("false_positive", False)
                service_available = not self.env.state.is_service_down()
                response_time = self.env.state.response_time_ms
                error_rate = self.env.state.error_rate
                
                self.defense_metrics.update(
                    attack_occurred, attack_blocked, false_positive,
                    service_available, response_time, error_rate
                )
                
                episode_reward += rewards["defender"]
                defender_state = states["defender"]
            
            self.training_metrics.record_episode(episode_reward, self.env.state.time_step)
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "n_episodes": n_episodes,
            "defense": self.defense_metrics.to_dict(),
            "realtime": self.realtime_metrics.to_dict(),
            "training": self.training_metrics.to_dict()
        }
        
        self.evaluation_history.append(results)
        
        return results
    
    def evaluate_by_attack_type(self, n_episodes_per_type: int = 20) -> Dict:
        results = {}
        
        attack_types = {
            1: "DDoS",
            2: "CC",
            3: "SQL_INJECTION",
            4: "MIXED",
            5: "LOW_AND_SLOW",
            6: "DNS_AMPLIFICATION",
            7: "SYN_FLOOD"
        }
        
        for attack_type, attack_name in attack_types.items():
            metrics = DefenseMetrics()
            
            for _ in range(n_episodes_per_type):
                states, _ = self.env.reset()
                defender_state = states["defender"]
                
                done = False
                
                while not done:
                    action, _, _ = self.defense_agent.select_action(
                        defender_state, deterministic=True
                    )
                    
                    states, rewards, done, info = self.env.step(
                        attack_type, random.uniform(0.5, 1.0), action
                    )
                    
                    attack_occurred = True
                    attack_blocked = info.get("defense_effect", {}).get("blocked", False)
                    false_positive = info.get("defense_effect", {}).get("false_positive", False)
                    service_available = not self.env.state.is_service_down()
                    response_time = self.env.state.response_time_ms
                    error_rate = self.env.state.error_rate
                    
                    metrics.update(
                        attack_occurred, attack_blocked, false_positive,
                        service_available, response_time, error_rate
                    )
                    
                    defender_state = states["defender"]
            
            results[attack_name] = metrics.to_dict()
        
        return results
    
    def evaluate_game_theory(self, n_samples: int = 100) -> Dict:
        attacker_strategies = []
        defender_strategies = []
        attacker_payoffs = []
        defender_payoffs = []
        
        for _ in range(n_samples):
            states, _ = self.env.reset()
            defender_state = states["defender"]
            attacker_state = states["attacker"]
            
            attack_action, attack_intensity, _, _ = self.attack_agent.select_action(attacker_state)
            defense_action, _, _ = self.defense_agent.select_action(defender_state)
            
            attacker_strategy = np.zeros(8)
            attacker_strategy[attack_action] = 1.0
            
            defender_strategy = np.zeros(8)
            defender_strategy[defense_action] = 1.0
            
            states, rewards, done, info = self.env.step(
                attack_action, attack_intensity, defense_action
            )
            
            attacker_strategies.append(attacker_strategy)
            defender_strategies.append(defender_strategy)
            attacker_payoffs.append(rewards["attacker"])
            defender_payoffs.append(rewards["defender"])
            
            self.game_theory_metrics.record_payoff(
                attacker_strategy, defender_strategy,
                rewards["attacker"], rewards["defender"]
            )
        
        avg_attacker_strategy = np.mean(attacker_strategies, axis=0)
        avg_defender_strategy = np.mean(defender_strategies, axis=0)
        
        nash_distance = self.game_theory_metrics.compute_nash_distance(
            avg_attacker_strategy, avg_defender_strategy
        )
        
        return {
            "avg_attacker_strategy": avg_attacker_strategy.tolist(),
            "avg_defender_strategy": avg_defender_strategy.tolist(),
            "avg_attacker_payoff": float(np.mean(attacker_payoffs)),
            "avg_defender_payoff": float(np.mean(defender_payoffs)),
            "nash_distance": nash_distance,
            "attacker_entropy": self.game_theory_metrics.compute_strategy_entropy(avg_attacker_strategy),
            "defender_entropy": self.game_theory_metrics.compute_strategy_entropy(avg_defender_strategy)
        }
    
    def check_targets(self) -> Dict:
        defense_dict = self.defense_metrics.to_dict()
        realtime_dict = self.realtime_metrics.to_dict()
        
        results = {
            "tpr_target_met": defense_dict["tpr"] >= self.config.target_tpr,
            "fpr_target_met": defense_dict["fpr"] <= self.config.target_fpr,
            "latency_target_met": realtime_dict["p99_latency_ms"] <= self.config.target_latency_ms,
            "availability_target_met": defense_dict["service_availability"] >= self.config.target_service_availability
        }
        
        results["all_targets_met"] = all(results.values())
        
        return results
    
    def save_best_model(self, path: str) -> bool:
        current_tpr = self.defense_metrics.get_tpr()
        
        if current_tpr > self.best_tpr:
            self.best_tpr = current_tpr
            self.best_model_path = path
            
            if hasattr(self.defense_agent, 'policy'):
                torch.save(self.defense_agent.policy.state_dict(), path)
            
            logger.info(f"New best model saved with TPR: {current_tpr:.4f}")
            return True
        
        return False
    
    def generate_report(self) -> Dict:
        defense = self.defense_metrics.to_dict()
        realtime = self.realtime_metrics.to_dict()
        training = self.training_metrics.to_dict()
        game_theory = self.game_theory_metrics.to_dict()
        targets = self.check_targets()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "tpr": defense["tpr"],
                "fpr": defense["fpr"],
                "f1_score": defense["f1_score"],
                "service_availability": defense["service_availability"],
                "p99_latency_ms": realtime["p99_latency_ms"],
                "all_targets_met": targets["all_targets_met"]
            },
            "defense_metrics": defense,
            "realtime_metrics": realtime,
            "training_metrics": training,
            "game_theory_metrics": game_theory,
            "target_compliance": targets,
            "evaluation_history_count": len(self.evaluation_history),
            "best_tpr": self.best_tpr,
            "best_model_path": self.best_model_path
        }
    
    def get_status(self) -> Dict:
        return {
            "config": {
                "n_eval_episodes": self.config.n_eval_episodes,
                "target_tpr": self.config.target_tpr,
                "target_fpr": self.config.target_fpr,
                "target_latency_ms": self.config.target_latency_ms
            },
            "current_metrics": {
                "tpr": self.defense_metrics.get_tpr(),
                "fpr": self.defense_metrics.get_fpr(),
                "avg_latency_ms": self.realtime_metrics.get_avg_latency(),
                "converged": self.training_metrics.check_convergence()
            },
            "best_tpr": self.best_tpr,
            "total_evaluations": len(self.evaluation_history)
        }
