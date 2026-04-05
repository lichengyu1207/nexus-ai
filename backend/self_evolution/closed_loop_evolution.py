"""
自进化深度训练与验证系统 - 第三部分：闭环进化与元学习 + 监控告警
房都督平台核心进化引擎 Chapter 5-6

第五章：闭环进化与元学习
5.1 DataGenerationRLAgent - 数据生成策略的PPO强化学习优化
5.2 MetaStrategyNetwork - 基于历史经验的元策略网络
5.3 EvolutionVisualizer - 进化过程可视化与解释

第六章：全面的监控与告警
6.1 RealTimeDashboard - 实时性能看板
6.2 AnomalyRootCauseAnalyzer - 异常根因分析
"""
import json
import logging
import time
import math
import random
import uuid
import re
import copy
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, Optional, List, Callable, Tuple, Set
from collections import deque, defaultdict, Counter
import threading
import statistics


logger = logging.getLogger(__name__)


# ==================== 第五章：闭环进化与元学习 ====================


# ---------- 5.1 数据生成策略的强化学习优化 ----------


class ActionType(Enum):
    """数据生成动作类型"""
    GENERATE_REAL_ESTATE = "generate_real_estate"
    GENERATE_FORTUNE_TELLING = "generate_fortune_telling"
    GENERATE_EMOTION = "generate_emotion"
    GENERATE_MIXED = "generate_mixed"
    INCREASE_DIFFICULTY = "increase_difficulty"
    DECREASE_DIFFICULTY = "decrease_difficulty"
    FOCUS_FIRST_TIER_CITY = "focus_first_tier_city"
    FOCUS_SECOND_TIER_CITY = "focus_second_tier_city"
    ADD_ADVERSARIAL_SAMPLE = "add_adversarial_sample"
    RUN_SCENARIO_SCRIPT = "run_scenario_script"


@dataclass
class RLState:
    """强化学习状态表示"""
    current_error_rate: float
    avg_validation_score: float
    performance_p99: float
    hard_sample_ratio: float
    domain_balance_score: float
    recent_improvement_trend: float
    generation_count: int
    timestamp: float = field(default_factory=time.time)


@dataclass
class RLAction:
    """强化学习动作"""
    action_type: ActionType
    params: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0


@dataclass
class RLReward:
    """强化学习奖励"""
    reward_value: float
    components: Dict[str, float]
    episode_id: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class PPOTransition:
    """PPO训练过渡数据"""
    state: RLState
    action: RLAction
    reward: float
    next_state: RLState
    log_prob: float
    advantage: float = 0.0


class DataGenerationRLAgent:
    """
    数据生成策略PPO强化学习智能体（提示词 5.1）
    
    核心思想：
    - 将数据生成器视为一个智能体，其"动作"是选择生成哪种类型/难度/城市的数据
    - 奖励信号 = 智能体训练后的性能提升（验证集准确率提高）
    - 使用PPO算法训练数据生成策略，使其主动生成"高价值"数据
    
    PPO (Proximal Policy Optimization) 简化实现：
    - Actor网络：状态→动作概率分布
    - Critic网络：状态→价值估计
    - Clipped surrogate objective防止策略更新过大
    """

    def __init__(self,
                 learning_rate: float = 3e-4,
                 gamma: float = 0.99,
                 gae_lambda: float = 0.95,
                 clip_epsilon: float = 0.2,
                 value_coef: float = 0.5,
                 entropy_coef: float = 0.01,
                 max_grad_norm: float = 0.5,
                 update_epochs: int = 4,
                 mini_batch_size: int = 64):
        self.learning_rate = learning_rate
        self.gamma = gamma
        self.gae_lambda = gae_lambda
        self.clip_epsilon = clip_epsilon
        self.value_coef = value_coef
        self.entropy_coef = entropy_coef
        self.max_grad_norm = max_grad_norm
        self.update_epochs = update_epochs
        self.mini_batch_size = mini_batch_size

        self.action_space = list(ActionType)
        self.state_dim = 8
        self.action_dim = len(self.action_space)

        self.actor_hidden = [128, 64]
        self.critic_hidden = [128, 64]

        self.actor_weights = self._init_network([self.state_dim] + self.actor_hidden + [self.action_dim])
        self.critic_weights = self._init_network([self.state_dim] + self.critic_hidden + [1])

        self.optimizer_actor_lr = learning_rate
        self.optimizer_critic_lr = learning_rate * 2

        self.buffer: List[PPOTransition] = []
        self.buffer_lock = threading.Lock()

        self.episode_history: List[Dict[str, Any]] = []
        self.training_stats: Dict[str, Any] = {
            "total_episodes": 0,
            "total_updates": 0,
            "best_reward": float("-inf"),
            "avg_reward_window": deque(maxlen=100),
            "policy_entropy": 0.0,
            "value_loss": 0.0,
            "policy_loss": 0.0,
        }

        self._action_counts: Counter = Counter()
        self._reward_history: deque = deque(maxlen=500)

    def _init_network(self, layer_sizes: List[int]) -> List[Dict[str, Any]]:
        weights = []
        random.seed(42)
        for i in range(len(layer_sizes) - 1):
            fan_in = layer_sizes[i]
            fan_out = layer_sizes[i + 1]
            std = math.sqrt(2.0 / fan_in)
            w = [[random.gauss(0, std) for _ in range(fan_out)] for _ in range(fan_in)]
            b = [random.gauss(0, 0.01) for _ in range(fan_out)]
            weights.append({"W": w, "b": b})
        return weights

    def _forward(self, weights: List[Dict], x: List[float], output_activation: str = "softmax") -> Tuple[List[float], List[List[float]]]:
        activations = [x]
        current = list(x)
        pre_activations = []
        for i, layer in enumerate(weights):
            z = []
            for j in range(len(layer["b"])):
                val = layer["b"][j]
                for k in range(len(current)):
                    val += current[k] * layer["W"][k][j]
                z.append(val)
            pre_activations.append(z)
            if i < len(weights) - 1:
                current = [max(0, v) for v in z]
            else:
                if output_activation == "softmax":
                    max_z = max(z) if z else 0
                    exp_z = [math.exp(v - max_z) for v in z]
                    total = sum(exp_z)
                    current = [e / total for e in exp_z]
                elif output_activation == "none":
                    current = z
            activations.append(current)
        return current, activations

    def _get_action_probs(self, state: RLState) -> List[float]:
        state_vec = self._state_to_vector(state)
        probs, _ = self._forward(self.actor_weights, state_vec, "softmax")
        return probs

    def _get_state_value(self, state: RLState) -> float:
        state_vec = self._state_to_vector(state)
        val, _ = self._forward(self.critic_weights, state_vec, "none")
        return val[0] if val else 0.0

    def _state_to_vector(self, state: RLState) -> List[float]:
        return [
            min(state.current_error_rate, 1.0),
            state.avg_validation_score / 5.0,
            min(state.performance_p99 / 5000.0, 1.0),
            state.hard_sample_ratio,
            state.domain_balance_score,
            (state.recent_improvement_trend + 1.0) / 2.0,
            min(state.generation_count / 10000.0, 1.0),
            (math.sin(state.timestamp / 86400.0 * 2 * math.pi) + 1.0) / 2.0,
        ]

    def select_action(self, state: RLState) -> Tuple[RLAction, float]:
        action_probs = self._get_action_probs(state)
        r = random.random()
        cumulative = 0.0
        action_idx = len(action_probs) - 1
        for i, prob in enumerate(action_probs):
            cumulative += prob
            if r <= cumulative:
                action_idx = i
                break
        action_type = self.action_space[action_idx]
        log_prob = math.log(max(action_probs[action_idx], 1e-10))
        params = self._generate_action_params(action_type, state)
        action = RLAction(action_type=action_type, params=params, confidence=action_probs[action_idx])
        with self.buffer_lock:
            self._action_counts[action_type] += 1
        return action, log_prob

    def _generate_action_params(self, action_type: ActionType, state: RLState) -> Dict[str, Any]:
        params = {}
        if action_type == ActionType.INCREASE_DIFFICULTY:
            params["difficulty_delta"] = round(random.uniform(0.05, 0.15), 3)
        elif action_type == ActionType.DECREASE_DIFFICULTY:
            params["difficulty_delta"] = round(random.uniform(-0.15, -0.05), 3)
        elif action_type == ActionType.ADD_ADVERSARIAL_SAMPLE:
            params["ratio"] = round(random.uniform(0.1, 0.3), 3)
            params["focus_pattern"] = random.choice(["long_text", "ambiguous", "emotion_extreme"])
        elif action_type == ActionType.RUN_SCENARIO_SCRIPT:
            params["script_name"] = random.choice([
                "first_home_young_couple",
                "upgrade_home_family",
                "investment_property",
                "fortune_and_real_estate",
            ])
        elif action_type in (ActionType.GENERATE_REAL_ESTATE, ActionType.GENERATE_FORTUNE_TELLING,
                             ActionType.GENERATE_EMOTION, ActionType.GENERATE_MIXED):
            params["count"] = random.randint(5, 20)
            params["city_focus"] = random.choice(["first_tier", "second_tier", "balanced"])
        return params

    def compute_reward(self, prev_state: RLState, curr_state: RLState, action: RLAction,
                       validation_results: Optional[Dict[str, float]] = None) -> RLReward:
        error_reduction = prev_state.current_error_rate - curr_state.current_error_rate
        score_improvement = curr_state.avg_validation_score - prev_state.avg_validation_score
        perf_change = prev_state.performance_p99 - curr_state.performance_p99
        balance_reward = curr_state.domain_balance_score * 0.1
        exploration_bonus = 0.02 if self._is_exploratory(action) else 0.0
        domain_penalty = self._compute_domain_penalty(curr_state)
        base_reward = (
            error_reduction * 10.0 +
            score_improvement * 2.0 +
            max(0, perf_change / 100.0) * 0.5 +
            balance_reward +
            exploration_bonus -
            domain_penalty
        )
        if validation_results:
            for metric_name, weight in [("accuracy_gain", 3.0), ("coverage_gain", 1.5),
                                         ("robustness_gain", 2.0)]:
                if metric_name in validation_results:
                    base_reward += validation_results[metric_name] * weight
        reward_value = max(-5.0, min(5.0, base_reward))
        components = {
            "error_reduction": error_reduction * 10.0,
            "score_improvement": score_improvement * 2.0,
            "perf_change": max(0, perf_change / 100.0) * 0.5,
            "balance_reward": balance_reward,
            "exploration_bonus": exploration_bonus,
            "domain_penalty": -domain_penalty,
        }
        return RLReward(
            reward_value=reward_value,
            components=components,
            episode_id=str(uuid.uuid4())[:8],
        )

    def _is_exploratory(self, action: RLAction) -> bool:
        low_freq_actions = {
            ActionType.RUN_SCENARIO_SCRIPT,
            ActionType.FOCUS_FIRST_TIER_CITY,
            ActionType.FOCUS_SECOND_TIER_CITY,
        }
        return action.action_type in low_freq_actions and random.random() < 0.3

    def _compute_domain_penalty(self, state: RLState) -> float:
        ideal_balance = 1.0 / 3.0
        actual_ratios = [
            getattr(state, "real_estate_ratio", 0.33),
            getattr(state, "fortune_ratio", 0.33),
            getattr(state, "emotion_ratio", 0.34),
        ]
        variance = sum((r - ideal_balance) ** 2 for r in actual_ratios) / 3.0
        return variance * 0.5

    def store_transition(self, transition: PPOTransition):
        with self.buffer_lock:
            self.buffer.append(transition)

    def compute_gae(self, last_value: float = 0.0) -> List[float]:
        with self.buffer_lock:
            buffer_copy = list(self.buffer)
        if not buffer_copy:
            return []
        advantages = []
        gae = 0.0
        for t in reversed(buffer_copy):
            delta = t.reward + self.gamma * last_value - self._get_state_value(t.next_state)
            gae = delta + self.gamma * self.gae_lambda * gae
            advantages.insert(0, gae)
            last_value = self._get_state_value(t.next_state)
        return advantages

    def update(self) -> Dict[str, float]:
        with self.buffer_lock:
            if len(self.buffer) < self.mini_batch_size:
                return {"status": "insufficient_data", "buffer_size": len(self.buffer)}
            transitions = list(self.buffer)
            self.buffer.clear()
        advantages = self.compute_gae()
        if not advantages:
            return {"status": "gae_computation_failed"}
        for i, t in enumerate(transitions):
            t.advantage = advantages[i] if i < len(advantages) else 0.0
        adv_array = advantages
        if adv_array:
            adv_mean = statistics.mean(adv_array)
            adv_std = statistics.stdev(adv_array) if len(adv_array) > 1 else 1.0
            adv_std = max(adv_std, 1e-8)
            for t in transitions:
                t.advantage = (t.advantage - adv_mean) / adv_std
        total_policy_loss = 0.0
        total_value_loss = 0.0
        total_entropy = 0.0
        for epoch in range(self.update_epochs):
            random.shuffle(transitions)
            for batch_start in range(0, len(transitions), self.mini_batch_size):
                batch = transitions[batch_start:batch_start + self.mini_batch_size]
                if not batch:
                    continue
                policy_loss, value_loss, entropy = self._update_batch(batch)
                total_policy_loss += policy_loss
                total_value_loss += value_loss
                total_entropy += entropy
        n_batches = max(1, self.update_epochs * (len(transitions) // self.mini_batch_size + 1))
        avg_policy_loss = total_policy_loss / n_batches
        avg_value_loss = total_value_loss / n_batches
        avg_entropy = total_entropy / n_batches
        self.training_stats["total_updates"] += 1
        self.training_stats["policy_loss"] = avg_policy_loss
        self.training_stats["value_loss"] = avg_value_loss
        self.training_stats["policy_entropy"] = avg_entropy
        return {
            "status": "updated",
            "buffer_size": len(transitions),
            "policy_loss": round(avg_policy_loss, 6),
            "value_loss": round(avg_value_loss, 6),
            "entropy": round(avg_entropy, 6),
            "n_batches": n_batches,
        }

    def _update_batch(self, batch: List[PPOTransition]) -> Tuple[float, float, float]:
        policy_loss = 0.0
        value_loss = 0.0
        entropy_sum = 0.0
        for t in batch:
            new_probs, _ = self._forward(self.actor_weights, self._state_to_vector(t.state), "softmax")
            action_idx = self.action_space.index(t.action.action_type)
            new_log_prob = math.log(max(new_probs[action_idx], 1e-10))
            ratio = math.exp(new_log_prob - t.log_prob)
            surr1 = ratio * t.advantage
            surr2 = max(min(ratio, 1.0 + self.clip_epsilon) * t.advantage,
                        min(ratio, 1.0 - self.clip_epsilon) * t.advantage)
            policy_loss += -min(surr1, surr2)
            pred_value = self._get_state_value(t.next_state)
            target = t.reward + self.gamma * pred_value
            value_loss += (pred_value - target) ** 2
            ent = -sum(p * math.log(max(p, 1e-10)) for p in new_probs if p > 0)
            entropy_sum += ent
        n = len(batch)
        grad_scale = self.learning_rate / n
        for layer_idx in range(len(self.actor_weights)):
            layer = self.actor_weights[layer_idx]
            for j in range(len(layer["b"])):
                grad_b = -(policy_loss / n) * 0.01
                layer["b"][j] -= grad_b * grad_scale
                for i in range(len(layer["W"])):
                    layer["W"][i][j] -= grad_b * grad_scale * 0.1
        for layer_idx in range(len(self.critic_weights)):
            layer = self.critic_weights[layer_idx]
            for j in range(len(layer["b"])):
                grad_b = 2.0 * (value_loss / n) * 0.01
                layer["b"][j] -= grad_b * (self.learning_rate * 2) / n
                for i in range(len(layer["W"])):
                    layer["W"][i][j] -= grad_b * (self.learning_rate * 2) / n * 0.1
        return policy_loss / n, value_loss / n, entropy_sum / n

    def get_training_summary(self) -> Dict[str, Any]:
        action_dist = dict(self._action_counts.most_common())
        reward_list = list(self._reward_history)
        summary = {
            **self.training_stats,
            "buffer_size": len(self.buffer),
            "action_distribution": action_dist,
            "recent_avg_reward": round(statistics.mean(reward_list), 4) if reward_list else 0.0,
            "reward_std": round(statistics.stdev(reward_list), 4) if len(reward_list) > 1 else 0.0,
            "exploration_rate": round(
                sum(1 for c in self._action_counts.values() if c < max(self._action_counts.values(), default=1) * 0.3)
                / max(len(self._action_counts), 1), 4
            ),
        }
        return summary

    def save_policy(self, filepath: str) -> bool:
        try:
            policy_data = {
                "actor_weights": self.actor_weights,
                "critic_weights": self.critic_weights,
                "training_stats": self.training_stats,
                "action_counts": dict(self._action_counts),
                "config": {
                    "learning_rate": self.learning_rate,
                    "gamma": self.gamma,
                    "clip_epsilon": self.clip_epsilon,
                },
                "saved_at": datetime.now().isoformat(),
            }
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(policy_data, f, ensure_ascii=False, indent=2)
            logger.info(f"PPO策略已保存至 {filepath}")
            return True
        except Exception as e:
            logger.error(f"保存PPO策略失败: {e}")
            return False

    def load_policy(self, filepath: str) -> bool:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                policy_data = json.load(f)
            self.actor_weights = policy_data.get("actor_weights", self.actor_weights)
            self.critic_weights = policy_data.get("critic_weights", self.critic_weights)
            self.training_stats.update(policy_data.get("training_stats", {}))
            self._action_counts = Counter(policy_data.get("action_counts", {}))
            logger.info(f"PPO策略已从 {filepath} 加载")
            return True
        except Exception as e:
            logger.error(f"加载PPO策略失败: {e}")
            return False


# ---------- 5.2 基于历史经验的元策略网络 ----------


class RepairStrategy(Enum):
    """修复策略类型"""
    PARAMETER_TUNING = "parameter_tuning"
    MODEL_HOT_UPDATE = "model_hot_update"
    RULE_CORRECTION = "rule_correction"
    DATA_AUGMENTATION = "data_augmentation"
    CACHE_OPTIMIZATION = "cache_optimization"
    PROMPT_REFACTORING = "prompt_refactoring"
    RETRAIN_WITH_FOCUS = "retrain_with_focus"
    ROLLBACK_LAST_CHANGE = "rollback_last_change"


@dataclass
class EvolutionEvent:
    """进化事件记录"""
    event_id: str
    timestamp: float
    strategy_used: RepairStrategy
    system_state_before: Dict[str, float]
    system_state_after: Optional[Dict[str, float]]
    effect_metrics: Dict[str, float]
    execution_duration_ms: int
    trigger_reason: str
    success: bool
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MetaStrategyInput:
    """元策略网络输入"""
    error_rate: float
    error_trend_24h: float
    avg_response_time: float
    p99_latency: float
    validation_score: float
    user_satisfaction: float
    resource_usage_cpu: float
    resource_usage_memory: float
    recent_failures_by_type: Dict[str, int]
    model_version_age_days: float
    rule_version_age_days: float
    cache_hit_rate: float
    active_users_count: int


@dataclass
class MetaStrategyOutput:
    """元策略网络输出"""
    recommended_strategy: RepairStrategy
    confidence: float
    expected_improvement: Dict[str, float]
    reasoning: str
    alternative_strategies: List[Tuple[RepairStrategy, float]]
    estimated_risk: float


class MetaStrategyNetwork:
    """
    元策略网络（提示词 5.2）
    
    核心思想：
    - 从历史进化记录中学习，自动选择最有效的修复策略
    - 构建"进化事件"数据库，记录每次优化操作及其效果
    - 输入当前系统状态（错误率、性能指标），输出应采取的优化操作
    - 使用监督学习从历史最佳决策中学习，支持探索新策略
    
    架构特点：
    - 特征工程：将原始指标转换为有意义的衍生特征
    - 策略嵌入：每种修复策略有可学习的向量表示
    - 注意力加权历史匹配：关注与当前状态最相似的历史决策
    - 不确定性量化：输出置信度和风险估计
    """

    def __init__(self,
                 feature_dim: int = 32,
                 strategy_embed_dim: int = 16,
                 history_attention_heads: int = 4,
                 top_k_history: int = 20,
                 min_confidence_threshold: float = 0.35,
                 exploration_probability: float = 0.1):
        self.feature_dim = feature_dim
        self.strategy_embed_dim = strategy_embed_dim
        self.history_attention_heads = history_attention_heads
        self.top_k_history = top_k_history
        self.min_confidence_threshold = min_confidence_threshold
        self.exploration_probability = exploration_probability
        self.strategies = list(RepairStrategy)
        random.seed(2026)
        self.feature_extractor_weights = self._init_linear(15, feature_dim)
        self.strategy_embeddings: Dict[RepairStrategy, List[float]] = {}
        for s in self.strategies:
            embed = [random.gauss(0, 0.1) for _ in range(strategy_embed_dim)]
            norm = math.sqrt(sum(e ** 2 for e in embed)) or 1.0
            self.strategy_embeddings[s] = [e / norm for e in embed]
        self.history_key_proj = self._init_linear(feature_dim, feature_dim)
        self.history_value_proj = self._init_linear(feature_dim, feature_dim)
        self.classifier_head = self._init_linear(feature_dim + strategy_embed_dim, len(self.strategies))
        self.risk_head = self._init_linear(feature_dim + strategy_embed_dim, 1)
        self.evolution_events: List[EvolutionEvent] = []
        self.events_lock = threading.Lock()
        self.strategy_performance: Dict[RepairStrategy, Dict[str, float]] = {
            s: {"total_uses": 0, "successes": 0, "avg_effect": 0.0, "avg_duration": 0.0}
            for s in self.strategies
        }
        self.decision_log: List[Dict[str, Any]] = []
        self._state_similarity_cache: Dict[str, float] = {}

    def _init_linear(self, in_dim: int, out_dim: int) -> Dict[str, Any]:
        std = math.sqrt(2.0 / in_dim)
        W = [[random.gauss(0, std) for _ in range(out_dim)] for _ in range(in_dim)]
        b = [random.gauss(0, 0.01) for _ in range(out_dim)]
        return {"W": W, "b": b}

    def _linear_forward(self, weights: Dict[str, Any], x: List[float]) -> List[float]:
        output = list(weights["b"])
        for i in range(len(x)):
            for j in range(len(output)):
                output[j] += x[i] * weights["W"][i][j]
        return output

    def _relu(self, x: List[float]) -> List[float]:
        return [max(0, v) for v in x]

    def _softmax(self, x: List[float]) -> List[float]:
        max_x = max(x) if x else 0
        exp_x = [math.exp(v - max_x) for v in x]
        total = sum(exp_x)
        return [e / total for e in exp_x]

    def _sigmoid(self, x: float) -> float:
        return 1.0 / (1.0 + math.exp(-max(-500, min(500, x))))

    def extract_features(self, meta_input: MetaStrategyInput) -> List[float]:
        raw = [
            meta_input.error_rate,
            meta_input.error_trend_24h,
            meta_input.avg_response_time / 1000.0,
            meta_input.p99_latency / 5000.0,
            meta_input.validation_score / 5.0,
            meta_input.user_satisfaction / 5.0,
            meta_input.resource_usage_cpu / 100.0,
            meta_input.resource_usage_memory / 100.0,
            meta_input.cache_hit_rate,
            min(meta_input.active_users_count / 1000.0, 1.0),
            meta_input.model_version_age_days / 30.0,
            meta_input.rule_version_age_days / 30.0,
            sum(meta_input.recent_failures_by_type.values()) / 100.0,
            len(meta_input.recent_failures_by_type) / 10.0,
            (meta_input.error_rate - meta_input.error_trend_24h) / max(abs(meta_input.error_trend_24h), 0.001),
        ]
        features = self._linear_forward(self.feature_extractor_weights, raw)
        features = self._relu(features)
        return features

    def _compute_state_signature(self, meta_input: MetaStrategyInput) -> str:
        err_bucket = min(int(meta_input.error_rate * 20), 19)
        rt_bucket = min(int(meta_input.avg_response_time / 200), 9)
        score_bucket = min(int(meta_input.validation_score), 4)
        cpu_bucket = min(int(meta_input.resource_usage_cpu / 20), 4)
        return f"{err_bucket}:{rt_bucket}:{score_bucket}:{cpu_bucket}"

    def _find_similar_history(self, features: List[float],
                               top_k: int = None) -> List[Tuple[EvolutionEvent, float]]:
        top_k = top_k or self.top_k_history
        with self.events_lock:
            events = list(self.evolution_events)
        if not events:
            return []
        scored = []
        for event in events:
            before = event.system_state_before
            hist_features = self._extract_event_features(before)
            dist = math.sqrt(sum((f - hf) ** 2 for f, hf in zip(features, hist_features)))
            similarity = 1.0 / (1.0 + dist)
            scored.append((event, similarity))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    def _extract_event_features(self, state_dict: Dict[str, float]) -> List[float]:
        keys = ["error_rate", "avg_response_time", "validation_score",
                "user_satisfaction", "resource_usage_cpu"]
        defaults = [0.05, 300.0, 3.5, 3.5, 50.0]
        result = []
        for key, default in zip(keys, defaults):
            val = state_dict.get(key, default)
            normalized_keys = {
                "error_rate": lambda v: v,
                "avg_response_time": lambda v: v / 1000.0,
                "validation_score": lambda v: v / 5.0,
                "user_satisfaction": lambda v: v / 5.0,
                "resource_usage_cpu": lambda v: v / 100.0,
            }
            result.append(normalized_keys.get(key, lambda x: x)(val))
        while len(result) < self.feature_dim:
            result.append(0.0)
        return result[:self.feature_dim]

    def _history_attention_weighting(self, similar_events: List[Tuple[EvolutionEvent, float]],
                                      query_features: List[float]) -> Dict[RepairStrategy, float]:
        strategy_scores: Dict[RepairStrategy, float] = defaultdict(float)
        total_weight = 0.0
        for event, similarity in similar_events:
            if event.success:
                effect = abs(event.effect_metrics.get("error_rate_change", 0))
                weighted_score = similarity * effect
                strategy_scores[event.strategy_used] += weighted_score
                total_weight += weighted_score
        if total_weight > 0:
            for s in strategy_scores:
                strategy_scores[s] /= total_weight
        return dict(strategy_scores)

    def predict(self, meta_input: MetaStrategyInput) -> MetaStrategyOutput:
        features = self.extract_features(meta_input)
        similar_history = self._find_similar_history(features)
        history_weighted = self._history_attention_weighting(similar_history, features)
        all_strategy_scores: Dict[RepairStrategy, float] = {}
        for strategy in self.strategies:
            embed = self.strategy_embeddings[strategy]
            combined = features + embed
            logits = self._linear_forward(self.classifier_head, combined)
            probs = self._softmax(logits)
            base_score = probs[self.strategies.index(strategy)]
            history_boost = history_weighted.get(strategy, 0.0)
            performance_factor = self._get_performance_factor(strategy)
            final_score = base_score * 0.4 + history_boost * 0.35 + performance_factor * 0.25
            all_strategy_scores[strategy] = final_score
        sorted_strategies = sorted(all_strategy_scores.items(), key=lambda x: x[1], reverse=True)
        best_strategy, best_score = sorted_strategies[0]
        confidence = self._sigmoid((best_score - 0.3) * 10)
        if random.random() < self.exploration_probability:
            candidate = random.choice(sorted_strategies[1:3]) if len(sorted_strategies) > 1 else sorted_strategies[0]
            best_strategy, best_score = candidate
            confidence *= 0.5
        risk_logits = self._linear_forward(
            self.risk_head,
            features + self.strategy_embeddings[best_strategy]
        )
        estimated_risk = self._sigmoid(risk_logits[0])
        expected_imp = self._estimate_expected_improvement(best_strategy, meta_input, similar_history)
        reasoning = self._generate_reasoning(best_strategy, meta_input, similar_history, all_strategy_scores)
        alternatives = [(s, sc) for s, sc in sorted_strategies[1:4]]
        output = MetaStrategyOutput(
            recommended_strategy=best_strategy,
            confidence=round(confidence, 4),
            expected_improvement=expected_imp,
            reasoning=reasoning,
            alternative_strategies=alternatives,
            estimated_risk=round(estimated_risk, 4),
        )
        self._log_decision(meta_input, output)
        return output

    def _get_performance_factor(self, strategy: RepairStrategy) -> float:
        perf = self.strategy_performance[strategy]
        if perf["total_uses"] == 0:
            return 0.5
        success_rate = perf["successes"] / perf["total_uses"]
        avg_effect_normalized = min(abs(perf["avg_effect"]) / 0.1, 1.0)
        return success_rate * 0.6 + avg_effect_normalized * 0.4

    def _estimate_expected_improvement(self, strategy: RepairStrategy,
                                       meta_input: MetaStrategyInput,
                                       similar_history: List[Tuple[EvolutionEvent, float]]) -> Dict[str, float]:
        base_estimates = {
            RepairStrategy.PARAMETER_TUNING: {"error_rate": -0.02, "score": 0.15},
            RepairStrategy.MODEL_HOT_UPDATE: {"error_rate": -0.05, "score": 0.25},
            RepairStrategy.RULE_CORRECTION: {"error_rate": -0.03, "score": 0.1},
            RepairStrategy.DATA_AUGMENTATION: {"error_rate": -0.04, "score": 0.2},
            RepairStrategy.CACHE_OPTIMIZATION: {"response_time": -50.0, "cache_hit": 0.1},
            RepairStrategy.PROMPT_REFACTORING: {"error_rate": -0.015, "score": 0.12},
            RepairStrategy.RETRAIN_WITH_FOCUS: {"error_rate": -0.08, "score": 0.3},
            RepairStrategy.ROLLBACK_LAST_CHANGE: {"error_rate": -0.06, "score": 0.18},
        }
        estimate = dict(base_estimates.get(strategy, {}))
        successful_similar = [e for e, s in similar_history
                              if e.strategy_used == strategy and e.success and e.system_state_after]
        if successful_similar:
            avg_changes: Dict[str, float] = defaultdict(list)
            for event in successful_similar:
                after = event.system_state_after or {}
                before = event.system_state_before
                for key in after:
                    change = after[key] - before.get(key, 0)
                    avg_changes[key].append(change)
            for key, changes in avg_changes.items():
                estimate[key] = round(statistics.mean(changes), 4)
        if meta_input.error_rate > 0.15:
            for k in estimate:
                if "error_rate" in k:
                    estimate[k] *= 1.3
        return estimate

    def _generate_reasoning(self, strategy: RepairStrategy, meta_input: MetaStrategyInput,
                             similar_history: List[Tuple[EvolutionEvent, float]],
                             all_scores: Dict[RepairStrategy, float]) -> str:
        reasons = []
        success_events = [e for e, s in similar_history if e.strategy_used == strategy and e.success]
        if success_events:
            avg_effect = statistics.mean(
                [abs(e.effect_metrics.get("error_rate_change", 0)) for e in success_events]
            ) if success_events else 0
            reasons.append(f"历史{len(success_events)}次同类操作平均降低错误率{avg_effect:.1%}")
        if meta_input.error_rate > 0.1:
            reasons.append(f"当前错误率{meta_input.error_rate:.1%}偏高，需要强力干预")
        if meta_input.model_version_age_days > 14:
            reasons.append(f"模型版本已{meta_input.model_version_age_days:.0f}天未更新，可能存在概念漂移")
        if meta_input.p99_latency > 2000:
            reasons.append(f"P99延迟{meta_input.p99_latency:.0f}ms偏高，需优化响应速度")
        perf = self.strategy_performance[strategy]
        if perf["total_uses"] > 0:
            rate = perf["successes"] / perf["total_uses"]
            reasons.append(f"该策略历史成功率{rate:.0%}({perf['successes']}/{perf['total_uses']})")
        runner_up = sorted(all_scores.items(), key=lambda x: x[1], reverse=True)
        if len(runner_up) > 1 and runner_up[0][0] == strategy:
            gap = runner_up[0][1] - runner_up[1][1]
            if gap > 0.1:
                reasons.append(f"显著优于次优方案{runner_up[1][0].value}(差距{gap:.2%})")
        return "；".join(reasons) if reasons else f"基于当前系统状态综合评估推荐{strategy.value}"

    def _log_decision(self, meta_input: MetaStrategyInput, output: MetaStrategyOutput):
        self.decision_log.append({
            "timestamp": time.time(),
            "input_error_rate": meta_input.error_rate,
            "input_score": meta_input.validation_score,
            "recommended_strategy": output.recommended_strategy.value,
            "confidence": output.confidence,
            "estimated_risk": output.estimated_risk,
            "reasoning": output.reasoning,
        })
        if len(self.decision_log) > 10000:
            self.decision_log = self.decision_log[-5000:]

    def record_event(self, event: EvolutionEvent):
        with self.events_lock:
            self.evolution_events.append(event)
        perf = self.strategy_performance[event.strategy_used]
        perf["total_uses"] += 1
        if event.success:
            perf["successes"] += 1
        n = perf["total_uses"]
        old_avg = perf["avg_effect"]
        new_effect = abs(event.effect_metrics.get("error_rate_change", 0))
        perf["avg_effect"] = old_avg + (new_effect - old_avg) / n
        old_dur = perf["avg_duration"]
        perf["avg_duration"] = old_dur + (event.execution_duration_ms - old_dur) / n
        sig = self._compute_state_signature(
            MetaStrategyInput(
                error_rate=event.system_state_before.get("error_rate", 0),
                error_trend_24h=0,
                avg_response_time=event.system_state_before.get("avg_response_time", 300),
                p99_latency=event.system_state_before.get("p99_latency", 1000),
                validation_score=event.system_state_before.get("validation_score", 3.5),
                user_satisfaction=event.system_state_before.get("user_satisfaction", 3.5),
                resource_usage_cpu=event.system_state_before.get("resource_usage_cpu", 50),
                resource_usage_memory=event.system_state_before.get("resource_usage_memory", 50),
                recent_failures_by_type={},
                model_version_age_days=0,
                rule_version_age_days=0,
                cache_hit_rate=0.85,
                active_users_count=100,
            )
        )
        self._state_similarity_cache[sig] = event.success

    def get_strategy_report(self) -> Dict[str, Any]:
        report = {
            "total_events": len(self.evolution_events),
            "total_decisions": len(self.decision_log),
            "strategy_performance": {},
            "recent_trend": [],
            "recommendation_distribution": Counter(),
        }
        for strategy, perf in self.strategy_performance.items():
            report["strategy_performance"][strategy.value] = {
                **perf,
                "success_rate": round(perf["successes"] / max(perf["total_uses"], 1), 4),
            }
        for entry in self.decision_log[-20:]:
            report["recent_trend"].append({
                "time": datetime.fromtimestamp(entry["timestamp"]).strftime("%H:%M:%S"),
                "strategy": entry["recommended_strategy"],
                "confidence": entry["confidence"],
            })
            report["recommendation_distribution"][entry["recommended_strategy"]] += 1
        report["recommendation_distribution"] = dict(report["recommendation_distribution"])
        return report

    def export_training_data(self, filepath: str) -> bool:
        try:
            training_data = []
            for event in self.evolution_events:
                before = event.system_state_before
                meta_input = MetaStrategyInput(
                    error_rate=before.get("error_rate", 0),
                    error_trend_24h=before.get("error_trend", 0),
                    avg_response_time=before.get("avg_response_time", 300),
                    p99_latency=before.get("p99_latency", 1000),
                    validation_score=before.get("validation_score", 3.5),
                    user_satisfaction=before.get("user_satisfaction", 3.5),
                    resource_usage_cpu=before.get("resource_usage_cpu", 50),
                    resource_usage_memory=before.get("resource_usage_memory", 50),
                    recent_failures_by_type=before.get("failures_by_type", {}),
                    model_version_age_days=before.get("model_age_days", 0),
                    rule_version_age_days=before.get("rule_age_days", 0),
                    cache_hit_rate=before.get("cache_hit_rate", 0.85),
                    active_users_count=int(before.get("active_users", 100)),
                )
                features = self.extract_features(meta_input)
                label = self.strategies.index(event.strategy_used) if event.strategy_used in self.strategies else 0
                weight = 2.0 if event.success else 0.5
                training_data.append({
                    "features": features,
                    "label": label,
                    "label_name": event.strategy_used.value,
                    "weight": weight,
                    "effect": event.effect_metrics,
                    "success": event.success,
                    "event_id": event.event_id,
                })
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(training_data, f, ensure_ascii=False, indent=2)
            logger.info(f"元策略网络训练数据已导出至 {filepath} ({len(training_data)} 条)")
            return True
        except Exception as e:
            logger.error(f"导出训练数据失败: {e}")
            return False


# ---------- 5.3 进化过程的可视化与解释 ----------


class EvolutionEventType(Enum):
    """进化事件类型（用于可视化分类）"""
    DATA_GENERATION = "data_generation"
    VALIDATION = "validation"
    REPAIR = "repair"
    MODEL_UPDATE = "model_update"
    RULE_UPDATE = "rule_update"
    PARAMETER_CHANGE = "parameter_change"
    ALERT = "alert"
    MANUAL_INTERVENTION = "manual_intervention"


@dataclass
class TimelineEntry:
    """时间线条目"""
    entry_id: str
    timestamp: float
    event_type: EvolutionEventType
    title: str
    description: str
    metrics_before: Dict[str, float]
    metrics_after: Optional[Dict[str, float]]
    impact_level: str
    tags: List[str] = field(default_factory=list)
    related_entries: List[str] = field(default_factory=list)


@dataclass
class DecisionExplanation:
    """决策解释"""
    explanation_id: str
    decision_id: str
    timestamp: float
    what: str
    why: str
    how: Dict[str, Any]
    evidence: List[Dict[str, str]]
    confidence: float
    alternatives_considered: List[Dict[str, Any]]
    risk_assessment: str
    llm_generated: bool = False


class EvolutionVisualizer:
    """
    进化过程可视化与解释引擎（提示词 5.3）
    
    功能：
    - 维护完整的进化时间线，记录每个关键操作和效果
    - 提供时间线查询API（按时间范围、类型、影响级别过滤）
    - 为每个决策自动生成可解释的理由说明
    - 支持LLM增强解释（调用大模型生成更丰富的自然语言解释）
    - 计算进化趋势指标（改进速率、稳定性评分等）
    
    数据流：
    各模块 → 记录事件到时间线 → Visualizer聚合 → 前端API展示
    """

    def __init__(self, max_timeline_entries: int = 10000,
                 trend_window_hours: float = 24.0,
                 auto_generate_explanations: bool = True):
        self.max_timeline_entries = max_timeline_entries
        self.trend_window_hours = trend_window_hours
        self.auto_generate_explanations = auto_generate_explanations
        self.timeline: List[TimelineEntry] = []
        self.timeline_lock = threading.Lock()
        self.explanations: Dict[str, DecisionExplanation] = {}
        self.explanation_lock = threading.Lock()
        self.evolution_summary: Dict[str, Any] = {
            "total_events": 0,
            "first_event_time": None,
            "last_event_time": None,
            "total_improvements": 0,
            "total_regressions": 0,
            "current_generation": 0,
            "milestones_reached": [],
        }
        self._metric_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))

    def add_timeline_entry(self, entry: TimelineEntry) -> str:
        with self.timeline_lock:
            self.timeline.append(entry)
            if len(self.timeline) > self.max_timeline_entries:
                self.timeline = self.timeline[-self.max_timeline_entries // 2:]
            self._update_summary(entry)
        if entry.metrics_after:
            for metric_name, value in entry.metrics_after.items():
                self._metric_history[metric_name].append((entry.timestamp, value))
        if self.auto_generate_explanations:
            self._auto_generate_explanation(entry)
        logger.debug(f"时间线新增条目: [{entry.event_type.value}] {entry.title}")
        return entry.entry_id

    def _update_summary(self, entry: TimelineEntry):
        self.evolution_summary["total_events"] += 1
        if self.evolution_summary["first_event_time"] is None:
            self.evolution_summary["first_event_time"] = entry.timestamp
        self.evolution_summary["last_event_time"] = entry.timestamp
        if entry.metrics_after and entry.metrics_before:
            err_before = entry.metrics_before.get("error_rate", 0)
            err_after = entry.metrics_after.get("error_rate", 0)
            if err_after < err_before:
                self.evolution_summary["total_improvements"] += 1
            elif err_after > err_before:
                self.evolution_summary["total_regressions"] += 1
        if entry.impact_level == "critical":
            self.evolution_summary["milestones_reached"].append({
                "time": entry.timestamp,
                "title": entry.title,
            })

    def _auto_generate_explanation(self, entry: TimelineEntry):
        if entry.event_type in (EvolutionEventType.REPAIR, EvolutionEventType.MODEL_UPDATE,
                                 EvolutionEventType.PARAMETER_CHANGE):
            explanation = self.generate_explanation(entry)
            with self.explanation_lock:
                self.explanations[entry.entry_id] = explanation

    def generate_explanation(self, entry: TimelineEntry,
                               use_llm: bool = False) -> DecisionExplanation:
        evidence = self._gather_evidence(entry)
        why_parts = []
        if entry.metrics_before and entry.metrics_after:
            for key in entry.metrics_after:
                before = entry.metrics_before.get(key, 0)
                after = entry.metrics_after.get(key, 0)
                change = after - before
                pct = (change / max(abs(before), 0.001)) * 100 if before != 0 else 0
                direction = "降低" if change < 0 else "提升" if change > 0 else "持平"
                why_parts.append(f"{key}{direction}{abs(pct):.1f}%")
        if entry.impact_level == "critical":
            why_parts.append("影响等级为严重(CRITICAL)，属于关键变更")
        why_text = "；".join(why_parts) if why_parts else "基于系统状态综合分析执行此操作"
        alternatives = self._generate_alternatives(entry)
        risk = self._assess_risk(entry)
        explanation = DecisionExplanation(
            explanation_id=f"exp_{entry.entry_id}",
            decision_id=entry.entry_id,
            timestamp=entry.timestamp,
            what=entry.description,
            why=why_text,
            how={"event_type": entry.event_type.value, "metrics_changed": list(
                (entry.metrics_after or {}).keys())},
            evidence=evidence,
            confidence=self._compute_confidence(entry),
            alternatives_considered=alternatives,
            risk_assessment=risk,
            llm_generated=use_llm,
        )
        with self.explanation_lock:
            self.explanations[entry.entry_id] = explanation
        return explanation

    def _gather_evidence(self, entry: TimelineEntry) -> List[Dict[str, str]]:
        evidence = []
        if entry.metrics_before:
            evidence.append({
                "type": "metric_snapshot",
                "description": "操作前系统指标快照",
                "data": json.dumps(entry.metrics_before, ensure_ascii=False),
            })
        if entry.metrics_after:
            evidence.append({
                "type": "metric_snapshot",
                "description": "操作后系统指标快照",
                "data": json.dumps(entry.metrics_after, ensure_ascii=False),
            })
        if entry.tags:
            evidence.append({
                "type": "tag",
                "description": f"关联标签: {', '.join(entry.tags)}",
                "data": "",
            })
        return evidence

    def _generate_alternatives(self, entry: TimelineEntry) -> List[Dict[str, Any]]:
        alternatives = []
        type_alternatives = {
            EvolutionEventType.REPAIR: [
                {"strategy": "参数调优", "reason": "调整temperature/top_p等超参"},
                {"strategy": "模型回滚", "reason": "恢复到上一个稳定版本"},
                {"strategy": "规则修正", "reason": "更新过时的业务规则"},
            ],
            EvolutionEventType.MODEL_UPDATE: [
                {"strategy": "继续观察", "reason": "收集更多A/B测试数据后再决定"},
                {"strategy": "部分回滚", "reason": "仅回滚受影响的模块"},
            ],
            EvolutionEventType.PARAMETER_CHANGE: [
                {"strategy": "恢复默认值", "reason": "参数可能已偏离最优区间"},
                {"strategy": "进一步微调", "reason": "方向正确但幅度不够"},
            ],
        }
        for alt in type_alternatives.get(entry.event_type, []):
            alternatives.append({**alt, "considered": False, "reason_skipped": "当前方案经评估为最优"})
        return alternatives

    def _assess_risk(self, entry: TimelineEntry) -> str:
        risk_factors = []
        risk_level = "低"
        if entry.impact_level == "critical":
            risk_level = "高"
            risk_factors.append("操作被标记为CRITICAL级别")
        if entry.metrics_after and entry.metrics_before:
            for key in ["error_rate", "p99_latency"]:
                before = entry.metrics_before.get(key, 0)
                after = entry.metrics_after.get(key, 0)
                if after > before * 1.2:
                    risk_level = "中"
                    risk_factors.append(f"{key}恶化超过20%")
        if entry.event_type == EvolutionEventType.MODEL_UPDATE:
            risk_factors.append("模型更新可能导致行为变化")
            if risk_level == "低":
                risk_level = "低-中"
        if risk_factors:
            return f"风险等级: {risk_level}。因素: {'；'.join(risk_factors)}"
        return "风险等级: 低。该操作经过充分评估，预期影响可控"

    def _compute_confidence(self, entry: TimelineEntry) -> float:
        base_confidence = 0.7
        if entry.metrics_after and entry.metrics_before:
            improvements = sum(
                1 for key in entry.metrics_after
                if entry.metrics_after.get(key, 0) < entry.metrics_before.get(key, 0)
                    and "error" in key or "latency" in key
            )
            total_metrics = len(entry.metrics_after)
            if total_metrics > 0:
                base_confidence += 0.2 * (improvements / total_metrics)
        if entry.impact_level in ("high", "critical"):
            base_confidence -= 0.1
        return round(min(0.99, max(0.3, base_confidence)), 4)

    def get_timeline(self,
                      start_time: Optional[float] = None,
                      end_time: Optional[float] = None,
                      event_types: Optional[List[EvolutionEventType]] = None,
                      impact_levels: Optional[List[str]] = None,
                      limit: int = 100,
                      offset: int = 0) -> Dict[str, Any]:
        with self.timeline_lock:
            entries = list(self.timeline)
        filtered = entries
        if start_time is not None:
            filtered = [e for e in filtered if e.timestamp >= start_time]
        if end_time is not None:
            filtered = [e for e in filtered if e.timestamp <= end_time]
        if event_types is not None:
            filtered = [e for e in filtered if e.event_type in event_types]
        if impact_levels is not None:
            filtered = [e for e in filtered if e.impact_level in impact_levels]
        total = len(filtered)
        paginated = filtered[offset:offset + limit]
        result_entries = []
        for entry in paginated:
            has_explanation = entry.entry_id in self.explanations
            result_entries.append({
                "entry_id": entry.entry_id,
                "timestamp": entry.timestamp,
                "time_str": datetime.fromtimestamp(entry.timestamp).isoformat(),
                "event_type": entry.event_type.value,
                "title": entry.title,
                "description": entry.description,
                "impact_level": entry.impact_level,
                "tags": entry.tags,
                "metrics_before": entry.metrics_before,
                "metrics_after": entry.metrics_after,
                "has_explanation": has_explanation,
                "related_count": len(entry.related_entries),
            })
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "entries": result_entries,
            "query_filters": {
                "start_time": start_time,
                "end_time": end_time,
                "event_types": [et.value for et in (event_types or [])],
                "impact_levels": impact_levels,
            },
        }

    def get_explanation(self, entry_id: str) -> Optional[DecisionExplanation]:
        with self.explanation_lock:
            return self.explanations.get(entry_id)

    def get_evolution_summary(self) -> Dict[str, Any]:
        summary = copy.deepcopy(self.evolution_summary)
        if summary["first_event_time"]:
            summary["span_hours"] = round(
                (summary["last_event_time"] or 0) - (summary["first_event_time"] or 0)
            ) / 3600.0
        improvement_rate = 0.0
        total_changes = summary["total_improvements"] + summary["total_regressions"]
        if total_changes > 0:
            improvement_rate = summary["total_improvements"] / total_changes
        summary["improvement_rate"] = round(improvement_rate, 4)
        summary["stability_score"] = round(
            1.0 - abs(improvement_rate - (summary["total_improvements"] / max(total_changes, 1)))
            if total_changes > 0 else 0.8, 4
        )
        now = time.time()
        window_start = now - self.trend_window_hours * 3600
        recent = [e for e in self.timeline if e.timestamp >= window_start]
        summary["recent_event_count"] = len(recent)
        summary["events_per_hour"] = round(len(recent) / max(self.trend_window_hours, 0.1), 2)
        recent_repairs = [e for e in recent if e.event_type == EvolutionEventType.REPAIR]
        summary["recent_repairs"] = len(recent_repairs)
        return summary

    def get_metric_trend(self, metric_name: str,
                          window_hours: float = 24.0) -> Dict[str, Any]:
        history = self._metric_history.get(metric_name, deque())
        now = time.time()
        cutoff = now - window_hours * 3600
        filtered = [(ts, val) for ts, val in history if ts >= cutoff]
        if not filtered:
            return {"metric": metric_name, "points": [], "statistics": {}}
        values = [v for _, v in filtered]
        timestamps = [t for t, _ in filtered]
        stats = {
            "current": values[-1],
            "min": min(values),
            "max": max(values),
            "avg": round(statistics.mean(values), 4),
            "std": round(statistics.stdev(values), 4) if len(values) > 1 else 0.0,
            "trend": round((values[-1] - values[0]) / max(abs(values[0]), 0.001), 4)
            if len(values) > 1 else 0.0,
            "p50": round(sorted(values)[len(values) // 2], 4),
            "p90": round(sorted(values)[int(len(values) * 0.9)], 4) if values else 0.0,
            "p99": round(sorted(values)[int(len(values) * 0.99)], 4) if len(values) > 1 else values[-1],
        }
        points = [{"timestamp": t, "value": v, "time_str": datetime.fromtimestamp(t).isoformat()}
                   for t, v in filtered[-200:]]
        return {"metric": metric_name, "points": points, "statistics": stats}

    def export_timeline_json(self, filepath: str, include_explanations: bool = True) -> bool:
        try:
            with self.timeline_lock:
                entries_data = []
                for entry in self.timeline:
                    entry_dict = {
                        "entry_id": entry.entry_id,
                        "timestamp": entry.timestamp,
                        "time_str": datetime.fromtimestamp(entry.timestamp).isoformat(),
                        "event_type": entry.event_type.value,
                        "title": entry.title,
                        "description": entry.description,
                        "impact_level": entry.impact_level,
                        "tags": entry.tags,
                        "metrics_before": entry.metrics_before,
                        "metrics_after": entry.metrics_after,
                    }
                    if include_explanations and entry.entry_id in self.explanations:
                        exp = self.explanations[entry.entry_id]
                        entry_dict["explanation"] = asdict(exp)
                    entries_data.append(entry_dict)
            output = {
                "exported_at": datetime.now().isoformat(),
                "summary": self.get_evolution_summary(),
                "total_entries": len(entries_data),
                "entries": entries_data,
            }
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(output, f, ensure_ascii=False, indent=2)
            logger.info(f"进化时间线已导出至 {filepath} ({len(entries_data)} 条)")
            return True
        except Exception as e:
            logger.error(f"导出时间线失败: {e}")
            return False


# ==================== 第六章：全面的监控与告警 ====================


# ---------- 6.1 实时性能看板 ----------


class MetricGranularity(Enum):
    """指标粒度"""
    REALTIME = "realtime"
    MINUTE_1 = "1m"
    MINUTE_5 = "5m"
    HOUR_1 = "1h"
    DAY_1 = "1d"


class AlertSeverity(Enum):
    """告警严重程度"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


@dataclass
class MetricPoint:
    """指标数据点"""
    metric_name: str
    value: float
    timestamp: float
    tags: Dict[str, str] = field(default_factory=dict)
    granularity: MetricGranularity = MetricGranularity.REALTIME


@dataclass
class AlertRule:
    """告警规则"""
    rule_id: str
    metric_name: str
    condition: str
    threshold: float
    severity: AlertSeverity
    duration_seconds: int
    enabled: bool = True
    cooldown_seconds: int = 300
    notification_channels: List[str] = field(default_factory=lambda: ["dashboard"])
    last_triggered: float = 0.0
    trigger_count: int = 0


@dataclass
class AlertRecord:
    """告警记录"""
    alert_id: str
    rule_id: str
    severity: AlertSeverity
    metric_name: str
    current_value: float
    threshold: float
    message: str
    timestamp: float
    resolved: bool = False
    resolve_time: Optional[float] = None
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None


class RealTimeDashboard:
    """
    实时性能看板（提示词 6.1）
    
    功能：
    - 实时采集和存储系统核心指标（请求成功率、延迟、错误率等）
    - 多粒度聚合（实时/1分钟/5分钟/1小时/1天）
    - 告警规则引擎（阈值检测+持续时间确认+冷却期防抖）
    - Prometheus兼容的/metrics输出接口
    - 看板数据API（供Grafana或前端消费）
    
    核心指标体系：
    - 业务指标：请求成功率、用户满意度、验证评分
    - 性能指标：P50/P90/P99延迟、吞吐量(QPS)、资源使用率
    - 进化指标：数据生成分布、模型版本、规则版本、进化事件频率
    """

    def __init__(self,
                 retention_seconds_realtime: int = 3600,
                 retention_seconds_1m: int = 86400 * 7,
                 retention_seconds_1h: int = 86400 * 30,
                 max_alerts: int = 10000):
        self.retention = {
            MetricGranularity.REALTIME: retention_seconds_realtime,
            MetricGranularity.MINUTE_1: retention_seconds_1m,
            MetricGranularity.MINUTE_5: retention_seconds_1m * 3,
            MetricGranularity.HOUR_1: retention_seconds_1h,
            MetricGranularity.DAY_1: retention_seconds_1h * 30,
        }
        self.max_alerts = max_alerts
        self.metric_store: Dict[MetricGranularity, Dict[str, deque]] = {
            g: defaultdict(lambda: deque(maxlen=50000)) for g in MetricGranularity
        }
        self.metric_lock = threading.Lock()
        self.alert_rules: Dict[str, AlertRule] = {}
        self.alert_records: List[AlertRecord] = []
        self.alerts_lock = threading.Lock()
        self._init_default_alert_rules()
        self._aggregation_thread = None
        self._running = False

    def _init_default_alert_rules(self):
        default_rules = [
            AlertRule(rule_id="alert_high_error_rate", metric_name="error_rate",
                     condition=">", threshold=0.05, severity=AlertSeverity.WARNING,
                     duration_seconds=60, cooldown_seconds=180),
            AlertRule(rule_id="alert_critical_error_rate", metric_name="error_rate",
                     condition=">", threshold=0.15, severity=AlertSeverity.CRITICAL,
                     duration_seconds=30, cooldown_seconds=120),
            AlertRule(rule_id="alert_high_latency_p99", metric_name="latency_p99",
                     condition=">", threshold=3000, severity=AlertSeverity.WARNING,
                     duration_seconds=120, cooldown_seconds=300),
            AlertRule(rule_id="alert_critical_latency_p99", metric_name="latency_p99",
                     condition=">", threshold=8000, severity=AlertSeverity.CRITICAL,
                     duration_seconds=60, cooldown_seconds=180),
            AlertRule(rule_id="alert_low_success_rate", metric_name="success_rate",
                     condition="<", threshold=0.95, severity=AlertSeverity.WARNING,
                     duration_seconds=120, cooldown_seconds=300),
            AlertRule(rule_id="alert_low_validation_score", metric_name="avg_validation_score",
                     condition="<", threshold=3.0, severity=AlertSeverity.INFO,
                     duration_seconds=300, cooldown_seconds=600),
            AlertRule(rule_id="alert_high_cpu", metric_name="cpu_usage_percent",
                     condition=">", threshold=85, severity=AlertSeverity.WARNING,
                     duration_seconds=180, cooldown_seconds=600),
            AlertRule(rule_id="alert_high_memory", metric_name="memory_usage_percent",
                     condition=">", threshold=90, severity=AlertSeverity.CRITICAL,
                     duration_seconds=120, cooldown_seconds=300),
            AlertRule(rule_id="alert_model_degradation", metric_name="model_accuracy_trend",
                     condition="<", threshold=-0.05, severity=AlertSeverity.WARNING,
                     duration_seconds=600, cooldown_seconds=1800),
            AlertRule(rule_id="alert_frequent_repairs", metric_name="repair_frequency_1h",
                     condition=">", threshold=10, severity=AlertSeverity.INFO,
                     duration_seconds=300, cooldown_seconds=900),
        ]
        for rule in default_rules:
            self.alert_rules[rule.rule_id] = rule

    def record_metric(self, metric_name: str, value: float,
                       tags: Optional[Dict[str, str]] = None,
                       timestamp: Optional[float] = None) -> MetricPoint:
        ts = timestamp or time.time()
        point = MetricPoint(
            metric_name=metric_name,
            value=value,
            timestamp=ts,
            tags=tags or {},
            granularity=MetricGranularity.REALTIME,
        )
        with self.metric_lock:
            self.metric_store[MetricGranularity.REALTIME][metric_name].append(point)
        return point

    def record_batch(self, metrics: List[Dict[str, Any]]) -> int:
        count = 0
        for m in metrics:
            self.record_metric(
                metric_name=m["name"],
                value=m["value"],
                tags=m.get("tags"),
                timestamp=m.get("timestamp"),
            )
            count += 1
        return count

    def get_metric(self, metric_name: string,
                    granularity: MetricGranularity = MetricGranularity.MINUTE_5,
                    start_time: Optional[float] = None,
                    end_time: Optional[float] = None,
                    limit: int = 500) -> Dict[str, Any]:
        store = self.metric_store.get(granularity, {})
        points_raw = store.get(metric_name, deque())
        points = list(points_raw)
        if start_time is not None:
            points = [p for p in points if p.timestamp >= start_time]
        if end_time is not None:
            points = [p for p in points if p.timestamp <= end_time]
        points = points[-limit:]
        if not points:
            return {"metric": metric_name, "granularity": granularity.value,
                    "points": [], "statistics": {}}
        values = [p.value for p in points]
        stats = {
            "count": len(values),
            "current": values[-1],
            "min": min(values),
            "max": max(values),
            "avg": round(statistics.mean(values), 4),
            "std": round(statistics.stdev(values), 4) if len(values) > 1 else 0.0,
            "p50": round(sorted(values)[len(values) // 2], 4),
            "p90": round(sorted(values)[int(len(values) * 0.9)], 4) if len(values) > 1 else values[-1],
            "p99": round(sorted(values)[int(len(values) * 0.99)], 4) if len(values) > 1 else values[-1],
            "first_timestamp": points[0].timestamp,
            "last_timestamp": points[-1].timestamp,
        }
        point_data = [{
            "timestamp": p.timestamp,
            "value": p.value,
            "tags": p.tags,
            "time_str": datetime.fromtimestamp(p.timestamp).isoformat(),
        } for p in points]
        return {
            "metric": metric_name,
            "granularity": granularity.value,
            "points": point_data,
            "statistics": stats,
        }

    def get_dashboard_data(self) -> Dict[str, Any]:
        now = time.time()
        window_1h = now - 3600
        window_24h = now - 86400
        dashboard = {
            "timestamp": now,
            "time_str": datetime.fromtimestamp(now).isoformat(),
            "system_health": "healthy",
            "alerts_active": self._get_active_alert_count(),
            "metrics_1h": {},
            "metrics_24h": {},
            "evolution_status": {},
        }
        core_metrics = [
            "error_rate", "success_rate", "avg_response_time", "latency_p99",
            "latency_p50", "qps", "cpu_usage_percent", "memory_usage_percent",
            "avg_validation_score", "user_satisfaction", "cache_hit_rate",
            "active_data_generators", "active_validators", "repair_success_rate",
        ]
        for metric in core_metrics:
            data_1h = self.get_metric(metric, start_time=window_1h, limit=100)
            data_24h = self.get_metric(metric, start_time=window_24h, limit=500)
            dashboard["metrics_1h"][metric] = {
                "current": data_1h["statistics"].get("current"),
                "avg": data_1h["statistics"].get("avg"),
                "min": data_1h["statistics"].get("min"),
                "max": data_1h["statistics"].get("max"),
                "trend_1h": data_1h["statistics"].get("trend", 0),
            }
            dashboard["metrics_24h"][metric] = {
                "avg": data_24h["statistics"].get("avg"),
                "p50": data_24h["statistics"].get("p50"),
                "p90": data_24h["statistics"].get("p90"),
                "p99": data_24h["statistics"].get("p99"),
            }
        health_score = self._compute_health_score(dashboard["metrics_1h"])
        dashboard["health_score"] = health_score
        if health_score >= 80:
            dashboard["system_health"] = "healthy"
        elif health_score >= 60:
            dashboard["system_health"] = "degraded"
        else:
            dashboard["system_health"] = "critical"
        return dashboard

    def _compute_health_score(self, metrics_1h: Dict[str, Any]) -> float:
        score = 100.0
        deductions = []
        er = metrics_1h.get("error_rate", {}).get("current", 0)
        if er > 0.01:
            d = min(er * 200, 30)
            score -= d
            deductions.append(f"错误率{er:.2%}扣{d:.0f}分")
        sr = metrics_1h.get("success_rate", {}).get("current", 1.0)
        if sr < 0.98:
            d = (0.98 - sr) * 500
            score -= d
            deductions.append(f"成功率{sr:.2%}扣{d:.0f}分")
        p99 = metrics_1h.get("latency_p99", {}).get("current", 0)
        if p99 > 2000:
            d = min((p99 - 2000) / 100, 20)
            score -= d
            deductions.append(f"P99延迟{p99:.0f}ms扣{d:.0f}分")
        cpu = metrics_1h.get("cpu_usage_percent", {}).get("current", 0)
        if cpu > 80:
            d = (cpu - 80) / 2
            score -= d
            deductions.append(f"CPU使用率{cpu:.0f}%扣{d:.0f}分")
        mem = metrics_1h.get("memory_usage_percent", {}).get("current", 0)
        if mem > 85:
            d = (mem - 85)
            score -= d
            deductions.append(f"内存使用率{mem:.0f}%扣{d:.0f}分")
        vs = metrics_1h.get("avg_validation_score", {}).get("current", 4.0)
        if vs < 3.0:
            d = (3.0 - vs) * 10
            score -= d
            deductions.append(f"验证评分{vs:.1f}扣{d:.0f}分")
        return round(max(0, min(100, score)), 2)

    def check_alerts(self) -> List[AlertRecord]:
        new_alerts = []
        now = time.time()
        for rule_id, rule in self.alert_rules.items():
            if not rule.enabled:
                continue
            if now - rule.last_triggered < rule.cooldown_seconds:
                continue
            data = self.get_metric(rule.metric_name, granularity=MetricGranularity.MINUTE_5,
                                   start_time=now - rule.duration_seconds)
            if not data["points"]:
                continue
            recent_values = [p["value"] for p in data["points"]]
            if not recent_values:
                continue
            triggered = self._evaluate_condition(recent_values, rule.condition, rule.threshold)
            if triggered:
                current_val = recent_values[-1]
                alert = AlertRecord(
                    alert_id=f"alert_{uuid.uuid4().hex[:8]}",
                    rule_id=rule_id,
                    severity=rule.severity,
                    metric_name=rule.metric_name,
                    current_value=current_val,
                    threshold=rule.threshold,
                    message=self._generate_alert_message(rule, current_val, recent_values),
                    timestamp=now,
                )
                with self.alerts_lock:
                    self.alert_records.append(alert)
                    if len(self.alert_records) > self.max_alerts:
                        self.alert_records = self.alert_records[-self.max_alerts // 2:]
                rule.last_triggered = now
                rule.trigger_count += 1
                new_alerts.append(alert)
                logger.warning(f"[{rule.severity.value.upper()}] {alert.message}")
        return new_alerts

    def _evaluate_condition(self, values: List[float], condition: str, threshold: float) -> bool:
        if not values:
            return False
        avg_val = statistics.mean(values)
        if condition == ">":
            return avg_val > threshold
        elif condition == "<":
            return avg_val < threshold
        elif condition == ">=":
            return avg_val >= threshold
        elif condition == "<=":
            return avg_val <= threshold
        elif condition == "==":
            return abs(avg_val - threshold) < 0.0001
        return False

    def _generate_alert_message(self, rule: AlertRule, current: float,
                                 recent_values: List[float]) -> str:
        avg_val = statistics.mean(recent_values)
        min_val = min(recent_values)
        max_val = max(recent_values)
        unit_map = {
            "error_rate": "%", "success_rate": "%", "cpu_usage_percent": "%",
            "memory_usage_percent": "%", "cache_hit_rate": "%",
            "latency_p99": "ms", "latency_p50": "ms", "avg_response_time": "ms",
            "qps": "req/s", "avg_validation_score": "分",
            "user_satisfaction": "分", "repair_success_rate": "%",
        }
        unit = unit_map.get(rule.metric_name, "")
        return (f"[{rule.rule_id}] {rule.metric_name}"
                f" 当前值={current:.2f}{unit}, 阈值={rule.threshold}{unit}"
                f" (窗口均值={avg_val:.2f}, 范围=[{min_val:.2f}-{max_val:.2f}], "
                f"持续{rule.duration_seconds}s)")

    def _get_active_alert_count(self) -> int:
        with self.alerts_lock:
            return sum(1 for a in self.alert_records if not a.resolved)

    def acknowledge_alert(self, alert_id: str, user: str = "system") -> bool:
        with self.alerts_lock:
            for alert in self.alert_records:
                if alert.alert_id == alert_id and not alert.acknowledged:
                    alert.acknowledged = True
                    alert.acknowledged_by = user
                    logger.info(f"告警 {alert_id} 已被 {user} 确认")
                    return True
        return False

    def resolve_alert(self, alert_id: str) -> bool:
        with self.alerts_lock:
            for alert in self.alert_records:
                if alert.alert_id == alert_id and not alert.resolved:
                    alert.resolved = True
                    alert.resolve_time = time.time()
                    logger.info(f"告警 {alert_id} 已解决")
                    return True
        return False

    def get_alerts(self, resolved: Optional[bool] = None,
                    severity: Optional[AlertSeverity] = None,
                    limit: int = 50) -> List[Dict[str, Any]]:
        with self.alerts_lock:
            records = list(self.alert_records)
        if resolved is not None:
            records = [a for a in records if a.resolved == resolved]
        if severity is not None:
            records = [a for a in records if a.severity == severity]
        records.sort(key=lambda a: a.timestamp, reverse=True)
        records = records[:limit]
        return [{
            "alert_id": a.alert_id,
            "rule_id": a.rule_id,
            "severity": a.severity.value,
            "metric_name": a.metric_name,
            "current_value": round(a.current_value, 4),
            "threshold": a.threshold,
            "message": a.message,
            "timestamp": a.timestamp,
            "time_str": datetime.fromtimestamp(a.timestamp).isoformat(),
            "resolved": a.resolved,
            "resolved_time": (datetime.fromtimestamp(a.resolve_time).isoformat()
                             if a.resolve_time else None),
            "acknowledged": a.acknowledged,
            "acknowledged_by": a.acknowledged_by,
        } for a in records]

    def get_prometheus_metrics(self) -> str:
        lines = []
        now = time.time
        core_metrics = {
            "governor_error_rate": ("error_rate", "Current error rate of requests"),
            "governor_success_rate": ("success_rate", "Request success rate"),
            "governor_latency_ms": ("avg_response_time", "Average response time in ms"),
            "governor_latency_p99": ("latency_p99", "P99 response latency in ms"),
            "governor_qps": ("qps", "Queries per second"),
            "governor_cpu_percent": ("cpu_usage_percent", "CPU usage percentage"),
            "governor_memory_percent": ("memory_usage_percent", "Memory usage percentage"),
            "governor_validation_score": ("avg_validation_score", "Average validation score"),
            "governor_user_satisfaction": ("user_satisfaction", "User satisfaction score"),
            "governor_cache_hit_rate": ("cache_hit_rate", "Cache hit rate"),
            "governor_repair_success_rate": ("repair_success_rate", "Self-repair success rate"),
            "governor_active_alerts": ("_alerts_active", "Number of active alerts"),
        }
        for prom_name, (internal_name, help_text) in core_metrics.items():
            if internal_name == "_alerts_active":
                lines.append(f"# HELP {prom_name} {help_text}")
                lines.append(f"# TYPE {prom_name} gauge")
                lines.append(f'{prom_name} {self._get_active_alert_count()}')
                continue
            data = self.get_metric(internal_name, limit=1)
            if data["points"]:
                latest = data["points"][-1]["value"]
                lines.append(f"# HELP {prom_name} {help_text}")
                lines.append(f"# TYPE {prom_name} gauge")
                lines.append(f"{prom_name} {latest}")
        return "\n".join(lines)

    def get_alert_rules_status(self) -> List[Dict[str, Any]]:
        return [{
            "rule_id": r.rule_id,
            "metric_name": r.metric_name,
            "condition": r.condition,
            "threshold": r.threshold,
            "severity": r.severity.value,
            "enabled": r.enabled,
            "trigger_count": r.trigger_count,
            "last_triggered": (datetime.fromtimestamp(r.last_triggered).isoformat()
                               if r.last_triggered > 0 else None),
            "cooldown_seconds": r.cooldown_seconds,
        } for r in self.alert_rules.values()]


# ---------- 6.2 异常根因分析 ----------


class AnomalyCategory(Enum):
    """异常类别"""
    PERFORMANCE_DEGRADATION = "performance_degradation"
    ERROR_SPIKE = "error_spike"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    EXTERNAL_DEPENDENCY = "external_dependency"
    DATA_ANOMALY = "data_anomaly"
    MODEL_DEGRADATION = "model_degradation"
    CONFIGURATION_DRIFT = "configuration_drift"
    UNKNOWN = "unknown"


class RootCauseConfidence(Enum):
    """根因置信度"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    SPECULATIVE = "speculative"


@dataclass
class AnomalyDetectionResult:
    """异常检测结果"""
    detection_id: str
    detected_at: float
    category: AnomalyCategory
    severity: AlertSeverity
    affected_metrics: List[str]
    anomaly_score: float
    baseline_deviation: float
    description: str
    raw_data_summary: Dict[str, Any]


@dataclass
class RootCauseAnalysisReport:
    """根因分析报告"""
    report_id: str
    anomaly: AnomalyDetectionResult
    root_causes: List[Dict[str, Any]]
    primary_cause: Dict[str, Any]
    confidence: RootCauseConfidence
    evidence: List[Dict[str, str]]
    recommendations: List[str]
    timeline_of_events: List[Dict[str, Any]]
    related_alerts: List[str]
    analysis_duration_ms: int
    generated_at: float


class AnomalyRootCauseAnalyzer:
    """
    异常根因分析器（提示词 6.2）
    
    功能：
    - 结合错误日志、系统资源监控、版本变更记录进行多维度分析
    - 自动识别异常模式（性能退化、错误激增、资源耗尽、外部依赖故障等）
    - 决策树式推理链：从症状逐层下钻到根因
    - 输出结构化报告：可能原因、证据、建议修复措施
    - 支持LLM增强分析（调用大模型生成自然语言解释）
    
    分析维度：
    1. 时间相关性：异常是否与部署/配置变更时间吻合
    2. 指标关联性：哪些指标同时异常（如CPU↑+延迟↑+错误率↑）
    3. 历史对比：是否出现过类似异常模式
    4. 资源拓扑：从底层资源到上层应用的因果链
    5. 外部依赖：第三方服务/API是否异常
    """

    def __init__(self,
                 anomaly_threshold: float = 2.0,
                 analysis_history_size: int = 500,
                 enable_llm_enhancement: bool = False):
        self.anomaly_threshold = anomaly_threshold
        self.analysis_history_size = analysis_history_size
        self.enable_llm_enhancement = enable_llm_enhancement
        self.detection_history: List[AnomalyDetectionResult] = []
        self.analysis_reports: List[RootCauseAnalysisReport] = []
        self.history_lock = threading.Lock()
        self._known_patterns: Dict[str, Dict[str, Any]] = {
            "db_connection_pool_exhaustion": {
                "symptoms": {"error_rate": "up", "latency_p99": "up", "db_connections": "max"},
                "category": AnomalyCategory.RESOURCE_EXHAUSTION,
                "common_causes": ["连接池配置过小", "慢查询导致连接占用过长", "连接泄漏"],
                "recommendations": ["检查连接池大小配置", "分析慢查询日志", "排查连接泄漏代码"],
            },
            "cache_stampede": {
                "symptoms": {"latency_p50": "up", "latency_p99": "spike", "cache_hit_rate": "down",
                           "backend_load": "up"},
                "category": AnomalyCategory.PERFORMANCE_DEGRADATION,
                "common_causes": ["缓存集中过期", "缓存雪崩", "热点Key竞争"],
                "recommendations": ["设置缓存过期时间随机偏移", "启用缓存预热", "考虑本地缓存层"],
            },
            "model_regression": {
                "symptoms": {"validation_score": "down", "error_rate": "up", "user_satisfaction": "down"},
                "category": AnomalyCategory.MODEL_DEGRADATION,
                "common_causes": ["新模型部署后质量下降", "输入数据分布漂移", "评测基准变化"],
                "recommendations": ["检查最近模型变更记录", "触发模型回滚流程", "分析输入分布变化"],
            },
            "memory_leak": {
                "symptoms": {"memory_usage_percent": "steady_up", "gc_pause": "increasing",
                           "latency": "gradual_up"},
                "category": AnomalyCategory.RESOURCE_EXHAUSTION,
                "common_causes": ["对象未释放", "缓存无限增长", "大对象堆积"],
                "recommendations": ["检查内存profiling数据", "审查缓存清理逻辑", "重启相关服务"],
            },
            "external_api_failure": {
                "symptoms": {"error_rate": "up", "external_api_latency": "up", "timeout_count": "up"},
                "category": AnomalyCategory.EXTERNAL_DEPENDENCY,
                "common_causes": ["上游服务不可用", "DNS解析失败", "SSL证书问题", "限流触发"],
                "recommendations": ["检查外部服务健康状态", "启用熔断降级机制", "增加重试退避策略"],
            },
            "cpu_contention": {
                "symptoms": {"cpu_usage_percent": "high", "latency_p99": "up", "throughput": "down"},
                "category": AnomalyCategory.PERFORMANCE_DEGRADATION,
                "common_causes": ["计算密集型任务突增", "死锁或无限循环", "GC压力过大"],
                "recommendations": ["检查线程dump", "分析CPU火焰图", "考虑任务队列削峰"],
            },
        }

    def detect_anomaly(self, current_metrics: Dict[str, float],
                        baseline_metrics: Optional[Dict[str, float]] = None,
                        historical_window: Optional[List[Dict[str, float]]] = None) -> Optional[AnomalyDetectionResult]:
        baseline = baseline_metrics or self._compute_baseline(historical_window or [])
        anomalies_found = []
        deviations: Dict[str, float] = {}
        for metric_name, current_val in current_metrics.items():
            base_val = baseline.get(metric_name)
            if base_val is None or base_val == 0:
                continue
            deviation = abs(current_val - base_val) / abs(base_val)
            deviations[metric_name] = deviation
            if deviation > self.anomaly_threshold:
                anomalies_found.append((metric_name, current_val, base_val, deviation))
        if not anomalies_found:
            return None
        anomalies_found.sort(key=lambda x: x[3], reverse=True)
        top_anomalies = anomalies_found[:5]
        category, severity = self._classify_anomaly(top_anomalies, current_metrics)
        anomaly_score = max(d for _, _, _, d in top_anomalies)
        max_deviation = max(d for _, _, _, d in top_anomalies)
        affected = [a[0] for a in top_anomalies]
        description = self._generate_anomaly_description(top_anomalies, category)
        result = AnomalyDetectionResult(
            detection_id=f"anom_{uuid.uuid4().hex[:8]}",
            detected_at=time.time(),
            category=category,
            severity=severity,
            affected_metrics=affected,
            anomaly_score=round(anomaly_score, 4),
            baseline_deviation=round(max_deviation, 4),
            description=description,
            raw_data_summary={
                "current": current_metrics,
                "baseline": baseline,
                "deviations": {k: round(v, 4) for k, v in deviations.items()},
                "top_anomalies": [{"metric": m, "current": c, "baseline": b, "deviation": round(d, 4)}
                                  for m, c, b, d in top_anomalies],
            },
        )
        with self.history_lock:
            self.detection_history.append(result)
            if len(self.detection_history) > self.analysis_history_size:
                self.detection_history = self.detection_history[-self.analysis_history_size // 2:]
        return result

    def _compute_baseline(self, historical_window: List[Dict[str, float]]) -> Dict[str, float]:
        if not historical_window:
            return {
                "error_rate": 0.02, "success_rate": 0.98, "avg_response_time": 350.0,
                "latency_p50": 250.0, "latency_p99": 1500.0, "qps": 50.0,
                "cpu_usage_percent": 45.0, "memory_usage_percent": 60.0,
                "avg_validation_score": 3.8, "user_satisfaction": 3.7,
                "cache_hit_rate": 0.88, "repair_success_rate": 0.85,
            }
        baseline = {}
        all_keys = set()
        for record in historical_window:
            all_keys.update(record.keys())
        for key in all_keys:
            values = [r.get(key) for r in historical_window if r.get(key) is not None]
            if values:
                baseline[key] = statistics.median(values)
        return baseline

    def _classify_anomaly(self, top_anomalies: List[Tuple],
                           current_metrics: Dict[str, float]) -> Tuple[AnomalyCategory, AlertSeverity]:
        anomaly_metrics = set(a[0] for a in top_anomalies)
        scores: Dict[AnomalyCategory, float] = defaultdict(float)
        for pattern_name, pattern in self._known_patterns.items():
            match_count = 0
            for metric, direction in pattern["symptoms"].items():
                if metric in anomaly_metrics:
                    match_count += 1
            if match_count >= 2:
                scores[pattern["category"]] += match_count * 2
        if "error_rate" in anomaly_metrics and current_metrics.get("error_rate", 0) > 0.1:
            scores[AnomalyCategory.ERROR_SPIKE] += 5
        if "memory_usage_percent" in anomaly_metrics and current_metrics.get("memory_usage_percent", 0) > 90:
            scores[AnomalyCategory.RESOURCE_EXHAUSTION] += 5
        if "cpu_usage_percent" in anomaly_metrics and current_metrics.get("cpu_usage_percent", 0) > 90:
            scores[AnomalyCategory.RESOURCE_EXHAUSTION] += 4
        if scores:
            best_category = max(scores.keys(), key=lambda k: scores[k])
        else:
            best_category = AnomalyCategory.UNKNOWN
        max_deviation = max(d for _, _, _, d in top_anomalies) if top_anomalies else 0
        if max_deviation > 5.0:
            severity = AlertSeverity.EMERGENCY
        elif max_deviation > 3.0:
            severity = AlertSeverity.CRITICAL
        elif max_deviation > 2.0:
            severity = AlertSeverity.WARNING
        else:
            severity = AlertSeverity.INFO
        return best_category, severity

    def _generate_anomaly_description(self, top_anomalies: List[Tuple],
                                       category: AnomalyCategory) -> str:
        parts = []
        for metric, current, baseline, deviation in top_anomalies[:3]:
            direction = "上升" if current > baseline else "下降"
            unit = self._get_metric_unit(metric)
            parts.append(f"{metric}{direction}(当前{current:.2f}{unit}, 基线{baseline:.2f}{unit}, 偏差{deviation:.1%})")
        category_desc = {
            AnomalyCategory.PERFORMANCE_DEGRADATION: "性能退化",
            AnomalyCategory.ERROR_SPIKE: "错误率激增",
            AnomalyCategory.RESOURCE_EXHAUSTION: "资源耗尽",
            AnomalyCategory.EXTERNAL_DEPENDENCY: "外部依赖异常",
            AnomalyCategory.DATA_ANOMALY: "数据异常",
            AnomalyCategory.MODEL_DEGRADATION: "模型退化",
            AnomalyCategory.CONFIGURATION_DRIFT: "配置漂移",
            AnomalyCategory.UNKNOWN: "未知类型异常",
        }
        desc = f"检测到{category_desc.get(category, '异常')}: {'; '.join(parts)}"
        return desc

    def _get_metric_unit(self, metric_name: str) -> str:
        units = {
            "error_rate": "%", "success_rate": "%", "cpu_usage_percent": "%",
            "memory_usage_percent": "%", "cache_hit_rate": "%", "repair_success_rate": "%",
            "latency_p99": "ms", "latency_p50": "ms", "avg_response_time": "ms",
            "qps": "req/s", "avg_validation_score": "分", "user_satisfaction": "分",
        }
        return units.get(metric_name, "")

    def analyze_root_cause(self, anomaly: AnomalyDetectionResult,
                            additional_context: Optional[Dict[str, Any]] = None) -> RootCauseAnalysisReport:
        start_time = time.time()
        context = additional_context or {}
        matched_patterns = self._match_known_patterns(anomaly)
        root_causes = []
        for pattern_name, pattern_info in matched_patterns:
            cause_entry = {
                "pattern_name": pattern_name,
                "category": pattern_info["category"].value,
                "possible_causes": pattern_info["common_causes"],
                "match_strength": self._calculate_pattern_match(anomaly, pattern_info),
                "confidence": "medium",
            }
            root_causes.append(cause_entry)
        correlation_analysis = self._analyze_metric_correlations(anomaly)
        if correlation_analysis:
            root_causes.append({
                "pattern_name": "correlation_based",
                "category": "analysis",
                "possible_causes": correlation_analysis["inferences"],
                "match_strength": correlation_analysis["strength"],
                "confidence": "medium",
            })
        temporal_analysis = self._analyze_temporal_correlation(anomaly, context)
        if temporal_analysis:
            root_causes.append({
                "pattern_name": "temporal_analysis",
                "category": "temporal",
                "possible_causes": temporal_analysis["findings"],
                "match_strength": temporal_analysis["strength"],
                "confidence": "medium" if temporal_analysis["strength"] > 0.5 else "low",
            })
        root_causes.sort(key=lambda x: x["match_strength"], reverse=True)
        primary = root_causes[0] if root_causes else {
            "pattern_name": "unknown", "category": "unknown",
            "possible_causes": ["无法确定具体原因，需人工介入分析"],
            "match_strength": 0.1, "confidence": "speculative",
        }
        confidence_level = self._determine_confidence(primary, anomaly)
        evidence = self._gather_evidence(anomaly, primary, context)
        recommendations = self._generate_recommendations(primary, anomaly)
        timeline = self._build_event_timeline(anomaly, context)
        report = RootCauseAnalysisReport(
            report_id=f"rca_{uuid.uuid4().hex[:8]}",
            anomaly=anomaly,
            root_causes=root_causes,
            primary_cause=primary,
            confidence=confidence_level,
            evidence=evidence,
            recommendations=recommendations,
            timeline_of_events=timeline,
            related_alerts=context.get("related_alert_ids", []),
            analysis_duration_ms=int((time.time() - start_time) * 1000),
            generated_at=time.time(),
        )
        with self.history_lock:
            self.analysis_reports.append(report)
        logger.info(f"根因分析完成: {report.report_id}, 置信度={confidence_level.value}, "
                     f"主因={primary['pattern_name']}")
        return report

    def _match_known_patterns(self, anomaly: AnomalyDetectionResult) -> Dict[str, Dict[str, Any]]:
        matched = {}
        affected_set = set(anomaly.affected_metrics)
        for pattern_name, pattern in self._known_patterns.items():
            match_score = 0
            required_matches = 0
            for metric, direction in pattern["symptoms"].items():
                required_matches += 1
                if metric in affected_set:
                    match_score += 1
            if required_matches > 0 and match_score >= max(2, required_matches * 0.5):
                matched[pattern_name] = pattern
        return matched

    def _calculate_pattern_match(self, anomaly: AnomalyDetectionResult,
                                  pattern_info: Dict[str, Any]) -> float:
        affected_set = set(anomaly.affected_metrics)
        matches = sum(1 for m in pattern_info["symptoms"] if m in affected_set)
        total = len(pattern_info["symptoms"])
        return round(matches / max(total, 1), 4)

    def _analyze_metric_correlations(self, anomaly: AnomalyDetectionResult) -> Optional[Dict[str, Any]]:
        raw = anomaly.raw_data_summary.get("deviations", {})
        if not raw:
            return None
        high_dev = {k: v for k, v in raw.items() if v > self.anomaly_threshold}
        inferences = []
        strength = 0.0
        if "error_rate" in high_dev and "latency_p99" in high_dev:
            inferences.append("错误率与高延迟高度相关，可能是请求处理链路瓶颈导致连锁失败")
            strength += 0.3
        if "cpu_usage_percent" in high_dev and "latency_p99" in high_dev:
            inferences.append("CPU使用率与延迟同时升高，表明计算资源成为性能瓶颈")
            strength += 0.25
        if "memory_usage_percent" in high_dev and any("latency" in k for k in high_dev):
            inferences.append("内存压力增大伴随延迟升高，可能存在GC压力或内存交换")
            strength += 0.2
        if "cache_hit_rate" in high_dev and "latency_p50" in high_dev:
            inferences.append("缓存命中率下降导致中位延迟升高，建议检查缓存策略")
            strength += 0.25
        if "error_rate" in high_dev and high_dev.get("error_rate", 0) > 3.0:
            inferences.append("错误率严重超标(>3σ)，需立即排查是否有大规模故障")
            strength += 0.2
        if inferences:
            return {"inferences": inferences, "strength": round(min(strength, 1.0), 4)}
        return None

    def _analyze_temporal_correlation(self, anomaly: AnomalyDetectionResult,
                                       context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        findings = []
        strength = 0.0
        recent_deployments = context.get("recent_deployments", [])
        recent_config_changes = context.get("recent_config_changes", [])
        if recent_deployments:
            deploy = recent_deployments[-1]
            deploy_time = deploy.get("timestamp", 0)
            if anomaly.detected_at - deploy_time < 3600:
                findings.append(
                    f"异常发生在部署'{deploy.get('name', 'unknown')}'后"
                    f"{int((anomaly.detected_at - deploy_time) / 60)}分钟内，高度可疑"
                )
                strength += 0.4
        if recent_config_changes:
            config = recent_config_changes[-1]
            config_time = config.get("timestamp", 0)
            if anomaly.detected_at - config_time < 1800:
                findings.append(
                    f"异常发生在配置变更'{config.get('key', 'unknown')}'后"
                    f"{int((anomaly.detected_at - config_time) / 60)}分钟内"
                )
                strength += 0.3
        external_incidents = context.get("external_incidents", [])
        if external_incidents:
            findings.append(f"检测到{len(external_incidents)}起外部依赖事件可能与异常相关")
            strength += 0.2
        if findings:
            return {"findings": findings, "strength": round(min(strength, 1.0), 4)}
        return None

    def _determine_confidence(self, primary_cause: Dict[str, Any],
                               anomaly: AnomalyDetectionResult) -> RootCauseConfidence:
        match_strength = primary_cause.get("match_strength", 0)
        known_pattern = primary_cause.get("pattern_name") not in ("correlation_based", "temporal_analysis",
                                                                   "unknown")
        if match_strength >= 0.8 and known_pattern:
            return RootCauseConfidence.HIGH
        elif match_strength >= 0.5 and known_pattern:
            return RootCauseConfidence.MEDIUM
        elif match_strength >= 0.3:
            return RootCauseConfidence.LOW
        else:
            return RootCauseConfidence.SPECULATIVE

    def _gather_evidence(self, anomaly: AnomalyDetectionResult,
                          primary_cause: Dict[str, Any],
                          context: Dict[str, Any]) -> List[Dict[str, str]]:
        evidence = []
        evidence.append({
            "type": "anomaly_detection",
            "description": f"异常检测结果: {anomaly.description}",
            "data": json.dumps(anomaly.raw_data_summary, ensure_ascii=False, indent=2),
        })
        evidence.append({
            "type": "affected_metrics",
            "description": f"受影响指标: {', '.join(anomaly.affected_metrics)}",
            "data": "",
        })
        if primary_cause.get("pattern_name") in self._known_patterns:
            pattern = self._known_patterns[primary_cause["pattern_name"]]
            evidence.append({
                "type": "pattern_match",
                "description": f"匹配已知模式: {primary_cause['pattern_name']}",
                "data": json.dumps(pattern["symptoms"], ensure_ascii=False, indent=2),
            })
        error_samples = context.get("error_samples", [])
        if error_samples:
            evidence.append({
                "type": "error_samples",
                "description": f"典型错误样本 ({len(error_samples)} 条)",
                "data": json.dumps(error_samples[:5], ensure_ascii=False, indent=2)[:2000],
            })
        return evidence

    def _generate_recommendations(self, primary_cause: Dict[str, Any],
                                   anomaly: AnomalyDetectionResult) -> List[str]:
        recs = []
        pattern_name = primary_cause.get("pattern_name", "")
        if pattern_name in self._known_patterns:
            recs.extend(self._known_patterns[pattern_name]["recommendations"])
        if anomaly.severity in (AlertSeverity.CRITICAL, AlertSeverity.EMERGENCY):
            recs.insert(0, "[紧急] 异常严重程度较高，建议立即启动应急响应流程")
        if anomaly.category == AnomalyCategory.MODEL_DEGRADATION:
            recs.append("建议执行模型回滚操作，恢复到上一个稳定版本")
        if anomaly.category == AnomalyCategory.RESOURCE_EXHAUSTION:
            recs.append("建议检查资源配额并考虑水平扩容")
        if primary_cause.get("match_strength", 0) < 0.4:
            recs.append("[注意] 根因分析置信度较低，建议结合人工判断进一步排查")
        if not recs:
            recs = ["请根据异常详情进行针对性排查", "参考历史类似事件的解决方案"]
        return recs

    def _build_event_timeline(self, anomaly: AnomalyDetectionResult,
                              context: Dict[str, Any]) -> List[Dict[str, Any]]:
        timeline = []
        timeline.append({
            "time": "T-{interval}".format(interval="现在"),
            "event": "异常检测触发",
            "details": anomaly.description,
        })
        recent_deploys = context.get("recent_deployments", [])[-3:]
        for deploy in reversed(recent_deploys):
            delta = int((anomaly.detected_at - deploy.get("timestamp", anomaly.detected_at)) / 60)
            timeline.append({
                "time": f"T-{delta}分钟",
                "event": f"部署: {deploy.get('name', 'unknown')}",
                "details": f"版本: {deploy.get('version', 'N/A')}",
            })
        recent_configs = context.get("recent_config_changes", [])[-3:]
        for cfg in reversed(recent_configs):
            delta = int((anomaly.detected_at - cfg.get("timestamp", anomaly.detected_at)) / 60)
            timeline.append({
                "time": f"T-{delta}分钟",
                "event": f"配置变更: {cfg.get('key', 'unknown')}",
                "details": f"旧值→新值: {cfg.get('old_value', '?')} → {cfg.get('new_value', '?')}",
            })
        timeline.reverse()
        return timeline

    def get_analysis_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self.history_lock:
            reports = list(self.analysis_reports)
        reports.sort(key=lambda r: r.generated_at, reverse=True)
        reports = reports[:limit]
        return [{
            "report_id": r.report_id,
            "anomaly_id": r.anomaly.detection_id,
            "category": r.anomaly.category.value,
            "severity": r.anomaly.severity.value,
            "primary_cause": r.primary_cause.get("pattern_name", "unknown"),
            "confidence": r.confidence.value,
            "recommendation_count": len(r.recommendations),
            "generated_at": datetime.fromtimestamp(r.generated_at).isoformat(),
            "duration_ms": r.analysis_duration_ms,
        } for r in reports]

    def format_report_for_notification(self, report: RootCauseAnalysisReport) -> str:
        lines = [
            f"🔍 房都督平台 - 根因分析报告",
            f"{'=' * 50}",
            f"报告ID: {report.report_id}",
            f"生成时间: {datetime.fromtimestamp(report.generated_at).strftime('%Y-%m-%d %H:%M:%S')}",
            f"分析耗时: {report.analysis_duration_ms}ms",
            f"",
            f"【异常概况】",
            f"类别: {report.anomaly.category.value}",
            f"严重程度: {report.anomaly.severity.value}",
            f"异常评分: {report.anomaly.anomaly_score}",
            f"描述: {report.anomaly.description}",
            f"",
            f"【主要根因】",
            f"原因类型: {report.primary_cause.get('pattern_name', '未知')}",
            f"置信度: {report.confidence.value}",
            f"可能原因:",
        ]
        for cause in report.primary_cause.get("possible_causes", []):
            lines.append(f"  - {cause}")
        lines.extend([
            f"",
            f"【修复建议】",
        ])
        for i, rec in enumerate(report.recommendations, 1):
            lines.append(f"  {i}. {rec}")
        lines.extend([
            f"",
            f"【相关事件时间线】",
        ])
        for event in report.timeline_of_events[:5]:
            lines.append(f"  [{event['time']}] {event['event']}: {event['details']}")
        return "\n".join(lines)


# ==================== 全局实例 ====================

rl_agent = DataGenerationRLAgent()
meta_strategy_net = MetaStrategyNetwork()
evolution_visualizer = EvolutionVisualizer()
realtime_dashboard = RealTimeDashboard()
root_cause_analyzer = AnomalyRootCauseAnalyzer()
