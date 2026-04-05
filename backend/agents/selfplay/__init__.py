"""
自博弈对抗训练系统
Self-Play Adversarial Training System

通过让智能体相互攻防，在持续对抗中进化策略
"""

import json
import time
import uuid
import asyncio
import numpy as np
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import random
import math

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    import torch.optim as optim
    from torch.distributions import Categorical, Normal
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None
    nn = None
    F = None
    optim = None
    Categorical = None
    Normal = None


class AgentRole(Enum):
    """智能体角色"""
    ATTACKER = "attacker"
    DEFENDER = "defender"
    NEUTRAL = "neutral"


class AttackType(Enum):
    """攻击类型"""
    NONE = 0
    LOW_CC = 1
    HIGH_DDoS = 2
    SQL_INJECTION = 3
    MIXED = 4


class DefenseAction(Enum):
    """防御动作"""
    ALLOW = 0
    RATE_LIMIT = 1
    CAPTCHA = 2
    BLOCK_IP = 3
    SWITCH_HIGH_DEFENSE = 4


@dataclass
class GameState:
    """游戏状态"""
    attacker_resources: float = 100.0
    attacker_attack_type: int = 0
    attacker_intensity: float = 0.0
    
    defender_load: float = 0.0
    defender_cpu: float = 0.0
    defender_bandwidth: float = 100.0
    defender_active_connections: int = 0
    
    network_qps: float = 0.0
    network_error_rate: float = 0.0
    network_latency: float = 0.0
    
    attack_success_count: int = 0
    defense_success_count: int = 0
    false_positive_count: int = 0
    
    time_step: int = 0
    max_steps: int = 100
    
    def to_vector(self) -> np.ndarray:
        return np.array([
            self.attacker_resources / 100.0,
            self.attacker_attack_type / 4.0,
            self.attacker_intensity,
            self.defender_load,
            self.defender_cpu,
            self.defender_bandwidth / 100.0,
            self.defender_active_connections / 10000.0,
            self.network_qps / 10000.0,
            self.network_error_rate,
            self.network_latency / 1000.0,
            self.attack_success_count / 10.0,
            self.defense_success_count / 10.0,
            self.false_positive_count / 10.0,
            self.time_step / self.max_steps
        ], dtype=np.float32)
    
    def to_dict(self) -> Dict:
        return {
            "attacker_resources": self.attacker_resources,
            "attacker_attack_type": self.attacker_attack_type,
            "attacker_intensity": self.attacker_intensity,
            "defender_load": self.defender_load,
            "defender_cpu": self.defender_cpu,
            "defender_bandwidth": self.defender_bandwidth,
            "defender_active_connections": self.defender_active_connections,
            "network_qps": self.network_qps,
            "network_error_rate": self.network_error_rate,
            "network_latency": self.network_latency,
            "attack_success_count": self.attack_success_count,
            "defense_success_count": self.defense_success_count,
            "false_positive_count": self.false_positive_count,
            "time_step": self.time_step
        }


class SelfPlayEnvironment(ABC):
    """自博弈对战环境基类"""
    
    @abstractmethod
    def reset(self) -> Tuple[Dict[str, np.ndarray], Dict]:
        pass
    
    @abstractmethod
    def step(self, actions: Dict[str, int]) -> Tuple[Dict[str, np.ndarray], Dict[str, float], bool, Dict]:
        pass
    
    @abstractmethod
    def get_state_dim(self) -> int:
        pass
    
    @abstractmethod
    def get_action_dim(self, role: AgentRole) -> int:
        pass
    
    @abstractmethod
    def render(self, mode: str = 'human') -> Optional[np.ndarray]:
        pass


class NetworkSecurityEnv(SelfPlayEnvironment):
    """网络安全攻防环境"""
    
    STATE_DIM = 14
    ATTACKER_ACTION_DIM = 5
    DEFENDER_ACTION_DIM = 5
    
    def __init__(
        self,
        max_steps: int = 100,
        bandwidth: float = 100.0,
        cpu_capacity: float = 100.0,
        attack_resource: float = 100.0
    ):
        self.max_steps = max_steps
        self.bandwidth = bandwidth
        self.cpu_capacity = cpu_capacity
        self.attack_resource = attack_resource
        
        self._state: Optional[GameState] = None
        self._history: List[Dict] = []
    
    def reset(self) -> Tuple[Dict[str, np.ndarray], Dict]:
        self._state = GameState(
            attacker_resources=self.attack_resource,
            max_steps=self.max_steps
        )
        self._history = []
        
        states = {
            "attacker": self._get_attacker_state(),
            "defender": self._get_defender_state()
        }
        
        info = {"initial_state": self._state.to_dict()}
        
        return states, info
    
    def _get_attacker_state(self) -> np.ndarray:
        return np.array([
            self._state.attacker_resources / 100.0,
            self._state.defender_load,
            self._state.defender_cpu,
            self._state.network_qps / 10000.0,
            self._state.network_error_rate,
            self._state.defense_success_count / 10.0,
            self._state.time_step / self.max_steps
        ], dtype=np.float32)
    
    def _get_defender_state(self) -> np.ndarray:
        return np.array([
            self._state.defender_load,
            self._state.defender_cpu,
            self._state.defender_bandwidth / 100.0,
            self._state.defender_active_connections / 10000.0,
            self._state.network_qps / 10000.0,
            self._state.network_error_rate,
            self._state.network_latency / 1000.0,
            self._state.attack_success_count / 10.0,
            self._state.false_positive_count / 10.0,
            self._state.time_step / self.max_steps
        ], dtype=np.float32)
    
    def step(self, actions: Dict[str, int]) -> Tuple[Dict[str, np.ndarray], Dict[str, float], bool, Dict]:
        attacker_action = actions.get("attacker", 0)
        defender_action = actions.get("defender", 0)
        
        attack_effect = self._process_attack(attacker_action)
        defense_effect = self._process_defense(defender_action, attack_effect)
        
        attacker_reward = self._calculate_attacker_reward(attack_effect, defense_effect)
        defender_reward = self._calculate_defender_reward(attack_effect, defense_effect)
        
        self._state.time_step += 1
        
        done = self._check_done()
        
        self._history.append({
            "time_step": self._state.time_step,
            "attacker_action": attacker_action,
            "defender_action": defender_action,
            "attack_effect": attack_effect,
            "defense_effect": defense_effect,
            "attacker_reward": attacker_reward,
            "defender_reward": defender_reward,
            "state": self._state.to_dict()
        })
        
        states = {
            "attacker": self._get_attacker_state(),
            "defender": self._get_defender_state()
        }
        
        rewards = {
            "attacker": attacker_reward,
            "defender": defender_reward
        }
        
        info = {
            "attack_effect": attack_effect,
            "defense_effect": defense_effect,
            "state": self._state.to_dict()
        }
        
        return states, rewards, done, info
    
    def _process_attack(self, action: int) -> Dict:
        effect = {
            "type": action,
            "intensity": 0.0,
            "resource_cost": 0.0,
            "success": False
        }
        
        if action == 0:
            return effect
        
        attack_params = {
            1: {"intensity": 0.3, "cost": 2.0, "qps_increase": 100},
            2: {"intensity": 0.8, "cost": 10.0, "qps_increase": 500},
            3: {"intensity": 0.5, "cost": 5.0, "qps_increase": 50},
            4: {"intensity": 0.6, "cost": 8.0, "qps_increase": 300}
        }
        
        if action in attack_params:
            params = attack_params[action]
            
            if self._state.attacker_resources >= params["cost"]:
                effect["intensity"] = params["intensity"]
                effect["resource_cost"] = params["cost"]
                
                self._state.attacker_resources -= params["cost"]
                self._state.attacker_attack_type = action
                self._state.attacker_intensity = params["intensity"]
                
                self._state.network_qps += params["qps_increase"]
                self._state.defender_load = min(1.0, self._state.defender_load + params["intensity"] * 0.3)
                self._state.defender_cpu = min(1.0, self._state.defender_cpu + params["intensity"] * 0.2)
                self._state.defender_active_connections += int(params["qps_increase"] * 10)
                
                if action == 3:
                    self._state.network_error_rate = min(1.0, self._state.network_error_rate + 0.1)
                
                effect["success"] = True
        
        return effect
    
    def _process_defense(self, action: int, attack_effect: Dict) -> Dict:
        effect = {
            "type": action,
            "blocked": False,
            "false_positive": False,
            "service_impact": 0.0
        }
        
        attack_type = attack_effect.get("type", 0)
        attack_intensity = attack_effect.get("intensity", 0.0)
        
        defense_matrix = {
            0: {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0},
            1: {1: 0.6, 2: 0.2, 3: 0.3, 4: 0.4},
            2: {1: 0.8, 2: 0.3, 3: 0.5, 4: 0.5},
            3: {1: 0.9, 2: 0.7, 3: 0.6, 4: 0.8},
            4: {1: 0.95, 2: 0.95, 3: 0.9, 4: 0.95}
        }
        
        if attack_type > 0:
            block_rate = defense_matrix.get(action, {}).get(attack_type, 0.0)
            
            if random.random() < block_rate:
                effect["blocked"] = True
                self._state.defense_success_count += 1
                self._state.network_qps = max(0, self._state.network_qps - attack_intensity * 200)
                self._state.defender_load = max(0, self._state.defender_load - attack_intensity * 0.2)
            else:
                self._state.attack_success_count += 1
        
        if action in [3, 4] and attack_type == 0:
            effect["false_positive"] = True
            self._state.false_positive_count += 1
        
        if action == 4:
            effect["service_impact"] = 0.1
            self._state.defender_bandwidth *= 0.95
        
        self._state.network_latency = self._state.defender_load * 100 + attack_intensity * 50
        
        return effect
    
    def _calculate_attacker_reward(self, attack_effect: Dict, defense_effect: Dict) -> float:
        reward = 0.0
        
        if defense_effect.get("service_impact", 0) > 0.5:
            reward += 100.0
        
        if self._state.defender_load > 0.8:
            reward += 10.0
        elif self._state.defender_load > 0.5:
            reward += 5.0
        
        if attack_effect.get("success"):
            if not defense_effect.get("blocked"):
                reward += 20.0
            else:
                reward -= 10.0
        
        reward -= attack_effect.get("resource_cost", 0) * 0.1
        
        if self._state.attacker_resources <= 0:
            reward -= 50.0
        
        return reward
    
    def _calculate_defender_reward(self, attack_effect: Dict, defense_effect: Dict) -> float:
        reward = 0.0
        
        if defense_effect.get("blocked"):
            reward += 10.0
        
        if self._state.defender_load < 0.5:
            reward += 1.0
        elif self._state.defender_load > 0.9:
            reward -= 10.0
        
        if defense_effect.get("false_positive"):
            reward -= 20.0
        
        if self._state.defender_cpu > 0.95:
            reward -= 50.0
        
        if self._state.network_error_rate > 0.3:
            reward -= 20.0
        
        if defense_effect.get("type") == 4:
            reward -= 5.0
        
        return reward
    
    def _check_done(self) -> bool:
        if self._state.time_step >= self.max_steps:
            return True
        
        if self._state.defender_cpu >= 1.0:
            return True
        
        if self._state.attacker_resources <= 0:
            return True
        
        return False
    
    def get_state_dim(self) -> int:
        return self.STATE_DIM
    
    def get_action_dim(self, role: AgentRole) -> int:
        if role == AgentRole.ATTACKER:
            return self.ATTACKER_ACTION_DIM
        return self.DEFENDER_ACTION_DIM
    
    def render(self, mode: str = 'human') -> Optional[np.ndarray]:
        if self._state is None:
            return None
        
        print(f"Step {self._state.time_step}/{self.max_steps}")
        print(f"  Attacker: resources={self._state.attacker_resources:.1f}, type={self._state.attacker_attack_type}")
        print(f"  Defender: load={self._state.defender_load:.2f}, cpu={self._state.defender_cpu:.2f}")
        print(f"  Network: qps={self._state.network_qps:.0f}, error={self._state.network_error_rate:.2%}")
        
        return None
    
    def get_history(self) -> List[Dict]:
        return self._history


if TORCH_AVAILABLE:
    class ActorCriticNetwork(nn.Module):
        """Actor-Critic策略网络"""
        
        def __init__(
            self,
            state_dim: int,
            action_dim: int,
            hidden_dims: List[int] = [256, 128],
            continuous: bool = False
        ):
            super().__init__()
            
            self.state_dim = state_dim
            self.action_dim = action_dim
            self.continuous = continuous
            
            layers = []
            prev_dim = state_dim
            
            for hidden_dim in hidden_dims:
                layers.append(nn.Linear(prev_dim, hidden_dim))
                layers.append(nn.ReLU())
                layers.append(nn.LayerNorm(hidden_dim))
                prev_dim = hidden_dim
            
            self.feature_net = nn.Sequential(*layers)
            
            self.actor_head = nn.Sequential(
                nn.Linear(prev_dim, prev_dim // 2),
                nn.ReLU(),
                nn.Linear(prev_dim // 2, action_dim)
            )
            
            self.critic_head = nn.Sequential(
                nn.Linear(prev_dim, prev_dim // 2),
                nn.ReLU(),
                nn.Linear(prev_dim // 2, 1)
            )
            
            if continuous:
                self.log_std = nn.Parameter(torch.zeros(action_dim))
        
        def forward(self, state: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
            features = self.feature_net(state)
            action_logits = self.actor_head(features)
            value = self.critic_head(features)
            return action_logits, value
        
        def get_action(self, state: torch.Tensor, deterministic: bool = False) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
            action_logits, value = self.forward(state)
            
            if self.continuous:
                mean = torch.tanh(action_logits)
                std = torch.exp(self.log_std)
                dist = Normal(mean, std)
                
                if deterministic:
                    action = mean
                else:
                    action = dist.sample()
                
                log_prob = dist.log_prob(action).sum(dim=-1)
            else:
                dist = Categorical(logits=action_logits)
                
                if deterministic:
                    action = torch.argmax(action_logits, dim=-1)
                else:
                    action = dist.sample()
                
                log_prob = dist.log_prob(action)
            
            return action, log_prob, value.squeeze(-1)
        
        def evaluate_actions(self, state: torch.Tensor, action: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
            action_logits, value = self.forward(state)
            
            if self.continuous:
                mean = torch.tanh(action_logits)
                std = torch.exp(self.log_std)
                dist = Normal(mean, std)
                log_prob = dist.log_prob(action).sum(dim=-1)
                entropy = dist.entropy().sum(dim=-1)
            else:
                dist = Categorical(logits=action_logits)
                log_prob = dist.log_prob(action)
                entropy = dist.entropy()
            
            return log_prob, entropy, value.squeeze(-1)
else:
    class ActorCriticNetwork:
        """简化版Actor-Critic网络（无torch依赖）"""
        
        def __init__(self, state_dim: int, action_dim: int, hidden_dims: List[int] = [256, 128], continuous: bool = False):
            self.state_dim = state_dim
            self.action_dim = action_dim
            self.continuous = continuous
            self._q_table: Dict[str, np.ndarray] = {}
        
        def get_action(self, state, deterministic: bool = False):
            action = random.randint(0, self.action_dim - 1)
            log_prob = -np.log(self.action_dim)
            value = 0.0
            return action, log_prob, value


class RolloutBuffer:
    """经验回放缓冲区"""
    
    def __init__(self, buffer_size: int = 10000, gamma: float = 0.99, gae_lambda: float = 0.95):
        self.buffer_size = buffer_size
        self.gamma = gamma
        self.gae_lambda = gae_lambda
        
        self.states: List[np.ndarray] = []
        self.actions: List[int] = []
        self.rewards: List[float] = []
        self.values: List[float] = []
        self.log_probs: List[float] = []
        self.dones: List[bool] = []
        
        self.advantages: List[float] = []
        self.returns: List[float] = []
    
    def store(self, state: np.ndarray, action: int, reward: float, value: float, log_prob: float, done: bool):
        self.states.append(state)
        self.actions.append(action)
        self.rewards.append(reward)
        self.values.append(value)
        self.log_probs.append(log_prob)
        self.dones.append(done)
        
        if len(self.states) > self.buffer_size:
            self.states.pop(0)
            self.actions.pop(0)
            self.rewards.pop(0)
            self.values.pop(0)
            self.log_probs.pop(0)
            self.dones.pop(0)
    
    def compute_gae(self):
        self.advantages = []
        self.returns = []
        
        gae = 0.0
        next_value = 0.0
        
        for t in reversed(range(len(self.rewards))):
            if t == len(self.rewards) - 1:
                next_value = 0.0
            else:
                next_value = self.values[t + 1]
            
            delta = self.rewards[t] + self.gamma * next_value * (1 - self.dones[t]) - self.values[t]
            gae = delta + self.gamma * self.gae_lambda * (1 - self.dones[t]) * gae
            
            self.advantages.insert(0, gae)
            self.returns.insert(0, gae + self.values[t])
    
    def clear(self):
        self.states.clear()
        self.actions.clear()
        self.rewards.clear()
        self.values.clear()
        self.log_probs.clear()
        self.dones.clear()
        self.advantages.clear()
        self.returns.clear()
    
    def __len__(self) -> int:
        return len(self.states)


class PPOTrainer:
    """PPO训练器"""
    
    def __init__(
        self,
        actor_critic: ActorCriticNetwork,
        lr: float = 3e-4,
        gamma: float = 0.99,
        gae_lambda: float = 0.95,
        clip_epsilon: float = 0.2,
        value_coef: float = 0.5,
        entropy_coef: float = 0.01,
        max_grad_norm: float = 0.5,
        ppo_epochs: int = 10,
        batch_size: int = 64
    ):
        self.actor_critic = actor_critic
        self.gamma = gamma
        self.gae_lambda = gae_lambda
        self.clip_epsilon = clip_epsilon
        self.value_coef = value_coef
        self.entropy_coef = entropy_coef
        self.max_grad_norm = max_grad_norm
        self.ppo_epochs = ppo_epochs
        self.batch_size = batch_size
        
        if TORCH_AVAILABLE:
            self.optimizer = optim.Adam(actor_critic.parameters(), lr=lr)
        
        self.training_step = 0
    
    def update(self, buffer: RolloutBuffer) -> Dict[str, float]:
        if not TORCH_AVAILABLE:
            return {"total_loss": 0.0, "policy_loss": 0.0, "value_loss": 0.0, "entropy": 0.0}
        
        buffer.compute_gae()
        
        total_loss = 0.0
        total_policy_loss = 0.0
        total_value_loss = 0.0
        total_entropy = 0.0
        
        states = torch.FloatTensor(np.array(buffer.states))
        actions = torch.LongTensor(buffer.actions)
        old_log_probs = torch.FloatTensor(buffer.log_probs)
        advantages = torch.FloatTensor(buffer.advantages)
        returns = torch.FloatTensor(buffer.returns)
        
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
        
        for _ in range(self.ppo_epochs):
            indices = np.random.permutation(len(buffer.states))
            
            for start in range(0, len(buffer.states), self.batch_size):
                end = start + self.batch_size
                idx = indices[start:end]
                
                batch_states = states[idx]
                batch_actions = actions[idx]
                batch_old_log_probs = old_log_probs[idx]
                batch_advantages = advantages[idx]
                batch_returns = returns[idx]
                
                log_probs, entropy, values = self.actor_critic.evaluate_actions(batch_states, batch_actions)
                
                ratio = torch.exp(log_probs - batch_old_log_probs)
                
                surr1 = ratio * batch_advantages
                surr2 = torch.clamp(ratio, 1 - self.clip_epsilon, 1 + self.clip_epsilon) * batch_advantages
                policy_loss = -torch.min(surr1, surr2).mean()
                
                value_loss = F.mse_loss(values, batch_returns)
                
                loss = policy_loss + self.value_coef * value_loss - self.entropy_coef * entropy.mean()
                
                self.optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.actor_critic.parameters(), self.max_grad_norm)
                self.optimizer.step()
                
                total_loss += loss.item()
                total_policy_loss += policy_loss.item()
                total_value_loss += value_loss.item()
                total_entropy += entropy.mean().item()
        
        self.training_step += 1
        
        n_updates = self.ppo_epochs * (len(buffer.states) // self.batch_size + 1)
        
        return {
            "total_loss": total_loss / n_updates,
            "policy_loss": total_policy_loss / n_updates,
            "value_loss": total_value_loss / n_updates,
            "entropy": total_entropy / n_updates
        }
    
    def save(self, path: str):
        if TORCH_AVAILABLE:
            torch.save({
                "actor_critic": self.actor_critic.state_dict(),
                "optimizer": self.optimizer.state_dict(),
                "training_step": self.training_step
            }, path)
    
    def load(self, path: str):
        if TORCH_AVAILABLE:
            checkpoint = torch.load(path)
            self.actor_critic.load_state_dict(checkpoint["actor_critic"])
            self.optimizer.load_state_dict(checkpoint["optimizer"])
            self.training_step = checkpoint["training_step"]


class SelfPlayAgent:
    """自博弈智能体"""
    
    def __init__(
        self,
        agent_id: str,
        role: AgentRole,
        state_dim: int,
        action_dim: int,
        device: str = "cpu"
    ):
        self.agent_id = agent_id
        self.role = role
        self.device = device
        
        self.policy = ActorCriticNetwork(state_dim, action_dim)
        self.buffer = RolloutBuffer()
        self.trainer = PPOTrainer(self.policy)
        
        self.version = 1
        self.total_games = 0
        self.wins = 0
        self.total_reward = 0.0
    
    def select_action(self, state: np.ndarray, deterministic: bool = False) -> Tuple[int, float, float]:
        action, log_prob, value = self.policy.get_action(state, deterministic)
        
        if TORCH_AVAILABLE and isinstance(action, torch.Tensor):
            action = action.item()
        if TORCH_AVAILABLE and isinstance(log_prob, torch.Tensor):
            log_prob = log_prob.item()
        if TORCH_AVAILABLE and isinstance(value, torch.Tensor):
            value = value.item()
        
        return int(action), float(log_prob), float(value)
    
    def store_experience(self, state: np.ndarray, action: int, reward: float, value: float, log_prob: float, done: bool):
        self.buffer.store(state, action, reward, value, log_prob, done)
    
    def update_policy(self) -> Dict[str, float]:
        if len(self.buffer) < 10:
            return {}
        
        metrics = self.trainer.update(self.buffer)
        self.buffer.clear()
        self.version += 1
        
        return metrics
    
    def record_game(self, reward: float, won: bool):
        self.total_games += 1
        self.total_reward += reward
        if won:
            self.wins += 1
    
    def get_win_rate(self) -> float:
        if self.total_games == 0:
            return 0.0
        return self.wins / self.total_games
    
    def get_avg_reward(self) -> float:
        if self.total_games == 0:
            return 0.0
        return self.total_reward / self.total_games
    
    def save_model(self, path: str):
        self.trainer.save(path)
    
    def load_model(self, path: str):
        self.trainer.load(path)
    
    def get_status(self) -> Dict:
        return {
            "agent_id": self.agent_id,
            "role": self.role.value,
            "version": self.version,
            "total_games": self.total_games,
            "wins": self.wins,
            "win_rate": self.get_win_rate(),
            "avg_reward": self.get_avg_reward(),
            "buffer_size": len(self.buffer)
        }


class SelfPlayTrainer:
    """自博弈训练控制器"""
    
    def __init__(self, env: SelfPlayEnvironment, population_size: int = 8, device: str = "cpu"):
        self.env = env
        self.population_size = population_size
        self.device = device
        
        self.attacker_population: List[SelfPlayAgent] = []
        self.defender_population: List[SelfPlayAgent] = []
        
        self.opponent_pool: List[Dict] = []
        self.champion: Optional[SelfPlayAgent] = None
        
        self._init_population()
        
        self.total_episodes = 0
        self.training_history: List[Dict] = []
    
    def _init_population(self):
        attacker_state_dim = 7
        defender_state_dim = 10
        
        for i in range(self.population_size):
            attacker = SelfPlayAgent(
                agent_id=f"attacker_{i}",
                role=AgentRole.ATTACKER,
                state_dim=attacker_state_dim,
                action_dim=self.env.get_action_dim(AgentRole.ATTACKER),
                device=self.device
            )
            self.attacker_population.append(attacker)
            
            defender = SelfPlayAgent(
                agent_id=f"defender_{i}",
                role=AgentRole.DEFENDER,
                state_dim=defender_state_dim,
                action_dim=self.env.get_action_dim(AgentRole.DEFENDER),
                device=self.device
            )
            self.defender_population.append(defender)
    
    def run_episode(self, attacker: SelfPlayAgent, defender: SelfPlayAgent, max_steps: int = 100) -> Dict:
        states, info = self.env.reset()
        
        attacker_state = states["attacker"]
        defender_state = states["defender"]
        
        total_attacker_reward = 0.0
        total_defender_reward = 0.0
        
        for step in range(max_steps):
            attacker_action, attacker_log_prob, attacker_value = attacker.select_action(attacker_state)
            defender_action, defender_log_prob, defender_value = defender.select_action(defender_state)
            
            actions = {
                "attacker": attacker_action,
                "defender": defender_action
            }
            
            next_states, rewards, done, info = self.env.step(actions)
            
            attacker.store_experience(
                attacker_state, attacker_action, rewards["attacker"],
                attacker_value, attacker_log_prob, done
            )
            
            defender.store_experience(
                defender_state, defender_action, rewards["defender"],
                defender_value, defender_log_prob, done
            )
            
            total_attacker_reward += rewards["attacker"]
            total_defender_reward += rewards["defender"]
            
            attacker_state = next_states["attacker"]
            defender_state = next_states["defender"]
            
            if done:
                break
        
        attacker_won = total_attacker_reward > total_defender_reward
        defender_won = not attacker_won
        
        attacker.record_game(total_attacker_reward, attacker_won)
        defender.record_game(total_defender_reward, defender_won)
        
        self.total_episodes += 1
        
        return {
            "episode": self.total_episodes,
            "attacker_id": attacker.agent_id,
            "defender_id": defender.agent_id,
            "attacker_reward": total_attacker_reward,
            "defender_reward": total_defender_reward,
            "attacker_won": attacker_won,
            "steps": step + 1
        }
    
    def train_step(self, update_interval: int = 10) -> Dict:
        attacker = random.choice(self.attacker_population)
        defender = random.choice(self.defender_population)
        
        episode_result = self.run_episode(attacker, defender)
        
        metrics = {}
        
        if self.total_episodes % update_interval == 0:
            attacker_metrics = attacker.update_policy()
            defender_metrics = defender.update_policy()
            
            metrics = {
                "attacker": attacker_metrics,
                "defender": defender_metrics
            }
        
        self.training_history.append(episode_result)
        
        return {
            "episode_result": episode_result,
            "training_metrics": metrics
        }
    
    def evaluate(self, num_games: int = 10) -> Dict:
        best_defender = max(self.defender_population, key=lambda a: a.get_win_rate())
        best_attacker = max(self.attacker_population, key=lambda a: a.get_win_rate())
        
        attacker_wins = 0
        defender_wins = 0
        total_attacker_reward = 0.0
        total_defender_reward = 0.0
        
        for _ in range(num_games):
            result = self.run_episode(best_attacker, best_defender)
            
            if result["attacker_won"]:
                attacker_wins += 1
            else:
                defender_wins += 1
            
            total_attacker_reward += result["attacker_reward"]
            total_defender_reward += result["defender_reward"]
        
        return {
            "attacker_wins": attacker_wins,
            "defender_wins": defender_wins,
            "attacker_win_rate": attacker_wins / num_games,
            "defender_win_rate": defender_wins / num_games,
            "avg_attacker_reward": total_attacker_reward / num_games,
            "avg_defender_reward": total_defender_reward / num_games,
            "best_attacker_id": best_attacker.agent_id,
            "best_defender_id": best_defender.agent_id
        }
    
    def save_champion(self, path: str):
        best_defender = max(self.defender_population, key=lambda a: a.get_win_rate())
        best_defender.save_model(path)
        self.champion = best_defender
    
    def get_status(self) -> Dict:
        return {
            "total_episodes": self.total_episodes,
            "population_size": self.population_size,
            "attacker_population": [a.get_status() for a in self.attacker_population],
            "defender_population": [a.get_status() for a in self.defender_population],
            "opponent_pool_size": len(self.opponent_pool),
            "has_champion": self.champion is not None
        }


selfplay_env = NetworkSecurityEnv()
selfplay_trainer = SelfPlayTrainer(selfplay_env)

try:
    from backend.agents.selfplay.training_kernel import (
        CyberBattleEnv as AdvancedCyberBattleEnv,
        VAEFeatureExtractor,
        AttackPolicyNetwork,
        DefensePolicyNetwork,
        AttackAgent as AdvancedAttackAgent,
        DefenseAgent as AdvancedDefenseAgent,
        QMIXNetwork,
        SelfPlayTrainingKernel,
        NetworkState
    )
except ImportError:
    AdvancedCyberBattleEnv = None
    VAEFeatureExtractor = None
    AttackPolicyNetwork = None
    DefensePolicyNetwork = None
    AdvancedAttackAgent = None
    AdvancedDefenseAgent = None
    QMIXNetwork = None
    SelfPlayTrainingKernel = None
    NetworkState = None

try:
    from backend.agents.selfplay.robust_training import (
        AdversarialConfig,
        AdversarialGenerator,
        PrioritizedReplayBuffer,
        MultiAgentReplayBuffer,
        RobustTrainer,
        WassersteinRobustOptimizer
    )
except ImportError:
    AdversarialConfig = None
    AdversarialGenerator = None
    PrioritizedReplayBuffer = None
    MultiAgentReplayBuffer = None
    RobustTrainer = None
    WassersteinRobustOptimizer = None

try:
    from backend.agents.selfplay.deployment import (
        DeploymentConfig,
        ModelQuantizer,
        ONNXExporter,
        TorchScriptExporter,
        InferenceCache,
        AsyncInferenceService,
        DeploymentModule
    )
except ImportError:
    DeploymentConfig = None
    ModelQuantizer = None
    ONNXExporter = None
    TorchScriptExporter = None
    InferenceCache = None
    AsyncInferenceService = None
    DeploymentModule = None

try:
    from backend.agents.selfplay.evaluator import (
        EvaluationConfig,
        DefenseMetrics,
        GameTheoryMetrics,
        TrainingMetrics,
        RealTimeMetrics,
        Evaluator
    )
except ImportError:
    EvaluationConfig = None
    DefenseMetrics = None
    GameTheoryMetrics = None
    TrainingMetrics = None
    RealTimeMetrics = None
    Evaluator = None

__all__ = [
    "AgentRole",
    "AttackType",
    "DefenseAction",
    "GameState",
    "SelfPlayEnvironment",
    "NetworkSecurityEnv",
    "ActorCriticNetwork",
    "RolloutBuffer",
    "PPOTrainer",
    "SelfPlayAgent",
    "SelfPlayTrainer",
    "selfplay_env",
    "selfplay_trainer",
    "TORCH_AVAILABLE",
    "AdvancedCyberBattleEnv",
    "VAEFeatureExtractor",
    "AttackPolicyNetwork",
    "DefensePolicyNetwork",
    "AdvancedAttackAgent",
    "AdvancedDefenseAgent",
    "QMIXNetwork",
    "SelfPlayTrainingKernel",
    "NetworkState",
    "AdversarialConfig",
    "AdversarialGenerator",
    "PrioritizedReplayBuffer",
    "MultiAgentReplayBuffer",
    "RobustTrainer",
    "WassersteinRobustOptimizer",
    "DeploymentConfig",
    "ModelQuantizer",
    "ONNXExporter",
    "TorchScriptExporter",
    "InferenceCache",
    "AsyncInferenceService",
    "DeploymentModule",
    "EvaluationConfig",
    "DefenseMetrics",
    "GameTheoryMetrics",
    "TrainingMetrics",
    "RealTimeMetrics",
    "Evaluator"
]
