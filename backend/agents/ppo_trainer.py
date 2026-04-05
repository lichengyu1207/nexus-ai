"""
PPO算法实现
Proximal Policy Optimization Trainer

用于训练智能体的策略网络，支持离散动作空间
包括损失函数计算、优势估计、更新步骤
"""

import math
import time
import json
import asyncio
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np

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
    nn = object
    F = None
    optim = None

from .experience_collector import Experience, State, Action, Reward


@dataclass
class PPOConfig:
    """PPO配置参数"""
    learning_rate: float = 3e-4
    gamma: float = 0.99
    gae_lambda: float = 0.95
    clip_epsilon: float = 0.2
    value_coef: float = 0.5
    entropy_coef: float = 0.01
    max_grad_norm: float = 0.5
    update_epochs: int = 4
    batch_size: int = 64
    mini_batch_size: int = 16
    
    state_dim: int = 15
    action_dim: int = 50
    hidden_dim: int = 128
    
    device: str = "cpu"


class PolicyNetwork(nn.Module if TORCH_AVAILABLE else object):
    """策略网络 - 输出动作概率分布"""
    
    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        hidden_dim: int = 128
    ):
        if not TORCH_AVAILABLE:
            return
        
        super().__init__()
        
        self.network = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, action_dim)
        )
        
        self._init_weights()
    
    def _init_weights(self):
        if not TORCH_AVAILABLE:
            return
        
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.orthogonal_(module.weight, gain=np.sqrt(2))
                nn.init.constant_(module.bias, 0)
    
    def forward(self, state: "torch.Tensor") -> "torch.Tensor":
        if not TORCH_AVAILABLE:
            return None
        
        logits = self.network(state)
        return logits
    
    def get_action_probs(self, state: "torch.Tensor") -> "torch.Tensor":
        if not TORCH_AVAILABLE:
            return None
        
        logits = self.forward(state)
        probs = F.softmax(logits, dim=-1)
        return probs
    
    def get_action(self, state: "torch.Tensor", deterministic: bool = False) -> Tuple["torch.Tensor", "torch.Tensor"]:
        if not TORCH_AVAILABLE:
            return None, None
        
        logits = self.forward(state)
        probs = F.softmax(logits, dim=-1)
        
        if deterministic:
            action = torch.argmax(probs, dim=-1)
        else:
            dist = Categorical(probs)
            action = dist.sample()
        
        log_prob = F.log_softmax(logits, dim=-1)
        action_log_prob = log_prob.gather(-1, action.unsqueeze(-1)).squeeze(-1)
        
        return action, action_log_prob
    
    def evaluate_actions(
        self,
        state: "torch.Tensor",
        action: "torch.Tensor"
    ) -> Tuple["torch.Tensor", "torch.Tensor"]:
        if not TORCH_AVAILABLE:
            return None, None, None
        
        logits = self.forward(state)
        probs = F.softmax(logits, dim=-1)
        
        dist = Categorical(probs)
        log_prob = dist.log_prob(action)
        entropy = dist.entropy()
        
        return log_prob, entropy


class ValueNetwork(nn.Module if TORCH_AVAILABLE else object):
    """价值网络 - 估计状态价值"""
    
    def __init__(
        self,
        state_dim: int,
        hidden_dim: int = 128
    ):
        if not TORCH_AVAILABLE:
            return
        
        super().__init__()
        
        self.network = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1)
        )
        
        self._init_weights()
    
    def _init_weights(self):
        if not TORCH_AVAILABLE:
            return
        
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.orthogonal_(module.weight, gain=np.sqrt(2))
                nn.init.constant_(module.bias, 0)
    
    def forward(self, state: "torch.Tensor") -> "torch.Tensor":
        if not TORCH_AVAILABLE:
            return None
        
        value = self.network(state)
        return value.squeeze(-1)


class RolloutBuffer:
    """经验回放缓冲区"""
    
    def __init__(self, buffer_size: int = 2048):
        self.buffer_size = buffer_size
        self.states: List[np.ndarray] = []
        self.actions: List[int] = []
        self.rewards: List[float] = []
        self.values: List[float] = []
        self.log_probs: List[float] = []
        self.dones: List[bool] = []
        self.advantages: List[float] = []
        self.returns: List[float] = []
    
    def add(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        value: float,
        log_prob: float,
        done: bool
    ):
        """添加一条经验"""
        self.states.append(state)
        self.actions.append(action)
        self.rewards.append(reward)
        self.values.append(value)
        self.log_probs.append(log_prob)
        self.dones.append(done)
    
    def compute_gae(
        self,
        gamma: float = 0.99,
        gae_lambda: float = 0.95
    ):
        """计算广义优势估计 (GAE)"""
        n = len(self.rewards)
        self.advantages = [0.0] * n
        self.returns = [0.0] * n
        
        last_gae = 0
        last_return = 0
        
        for t in reversed(range(n)):
            if t == n - 1:
                next_value = 0
            else:
                next_value = self.values[t + 1]
            
            delta = self.rewards[t] + gamma * next_value * (1 - self.dones[t]) - self.values[t]
            last_gae = delta + gamma * gae_lambda * (1 - self.dones[t]) * last_gae
            self.advantages[t] = last_gae
            
            last_return = self.rewards[t] + gamma * last_return * (1 - self.dones[t])
            self.returns[t] = last_return
    
    def get_batch(
        self,
        batch_size: int
    ) -> Tuple[np.ndarray, ...]:
        """获取批次数据"""
        indices = np.random.permutation(len(self.states))[:batch_size]
        
        return (
            np.array([self.states[i] for i in indices]),
            np.array([self.actions[i] for i in indices]),
            np.array([self.log_probs[i] for i in indices]),
            np.array([self.advantages[i] for i in indices]),
            np.array([self.returns[i] for i in indices])
        )
    
    def clear(self):
        """清空缓冲区"""
        self.states.clear()
        self.actions.clear()
        self.rewards.clear()
        self.values.clear()
        self.log_probs.clear()
        self.dones.clear()
        self.advantages.clear()
        self.returns.clear()
    
    def __len__(self):
        return len(self.states)
    
    def is_full(self) -> bool:
        return len(self.states) >= self.buffer_size


class PPOTrainer:
    """PPO训练器"""
    
    def __init__(self, config: Optional[PPOConfig] = None):
        self.config = config or PPOConfig()
        
        if not TORCH_AVAILABLE:
            print("警告: PyTorch不可用，PPO训练器将使用简化实现")
            self._use_torch = False
            self._simple_policy = {}
            self._simple_value = {}
        else:
            self._use_torch = True
            self.device = torch.device(self.config.device)
            
            self.policy_network = PolicyNetwork(
                state_dim=self.config.state_dim,
                action_dim=self.config.action_dim,
                hidden_dim=self.config.hidden_dim
            ).to(self.device)
            
            self.value_network = ValueNetwork(
                state_dim=self.config.state_dim,
                hidden_dim=self.config.hidden_dim
            ).to(self.device)
            
            self.optimizer = optim.Adam([
                {'params': self.policy_network.parameters(), 'lr': self.config.learning_rate},
                {'params': self.value_network.parameters(), 'lr': self.config.learning_rate}
            ])
        
        self.buffer = RolloutBuffer(buffer_size=self.config.batch_size * 10)
        
        self.training_stats = {
            "total_steps": 0,
            "total_episodes": 0,
            "policy_losses": [],
            "value_losses": [],
            "entropy_losses": [],
            "total_losses": [],
            "mean_rewards": [],
            "mean_advantages": []
        }
    
    def select_action(
        self,
        state: np.ndarray,
        deterministic: bool = False
    ) -> Tuple[int, float, float]:
        """选择动作"""
        if self._use_torch:
            with torch.no_grad():
                state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
                
                action, log_prob = self.policy_network.get_action(state_tensor, deterministic)
                value = self.value_network(state_tensor)
                
                return (
                    action.item(),
                    log_prob.item(),
                    value.item()
                )
        else:
            state_hash = self._hash_state(state)
            
            if state_hash not in self._simple_policy:
                self._simple_policy[state_hash] = np.random.dirichlet(np.ones(self.config.action_dim))
            
            probs = self._simple_policy[state_hash]
            
            if deterministic:
                action = np.argmax(probs)
            else:
                action = np.random.choice(len(probs), p=probs)
            
            log_prob = np.log(probs[action] + 1e-10)
            
            if state_hash not in self._simple_value:
                self._simple_value[state_hash] = 0.0
            value = self._simple_value[state_hash]
            
            return int(action), float(log_prob), float(value)
    
    def _hash_state(self, state: np.ndarray) -> str:
        """将状态转换为哈希键"""
        return json.dumps(state.tolist()[:5])
    
    def store_transition(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        value: float,
        log_prob: float,
        done: bool
    ):
        """存储状态转移"""
        self.buffer.add(state, action, reward, value, log_prob, done)
    
    def update(self) -> Dict[str, float]:
        """更新策略网络和价值网络"""
        if len(self.buffer) < self.config.mini_batch_size:
            return {"status": "insufficient_data"}
        
        self.buffer.compute_gae(
            gamma=self.config.gamma,
            gae_lambda=self.config.gae_lambda
        )
        
        if self._use_torch:
            return self._update_torch()
        else:
            return self._update_simple()
    
    def _update_torch(self) -> Dict[str, float]:
        """使用PyTorch进行更新"""
        states = torch.FloatTensor(np.array(self.buffer.states)).to(self.device)
        actions = torch.LongTensor(self.buffer.actions).to(self.device)
        old_log_probs = torch.FloatTensor(self.buffer.log_probs).to(self.device)
        advantages = torch.FloatTensor(self.buffer.advantages).to(self.device)
        returns = torch.FloatTensor(self.buffer.returns).to(self.device)
        
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
        
        total_policy_loss = 0
        total_value_loss = 0
        total_entropy_loss = 0
        
        for _ in range(self.config.update_epochs):
            indices = np.random.permutation(len(self.buffer))
            
            for start in range(0, len(self.buffer), self.config.mini_batch_size):
                end = start + self.config.mini_batch_size
                mb_indices = indices[start:end]
                
                mb_states = states[mb_indices]
                mb_actions = actions[mb_indices]
                mb_old_log_probs = old_log_probs[mb_indices]
                mb_advantages = advantages[mb_indices]
                mb_returns = returns[mb_indices]
                
                new_log_probs, entropy = self.policy_network.evaluate_actions(
                    mb_states, mb_actions
                )
                new_values = self.value_network(mb_states)
                
                ratio = torch.exp(new_log_probs - mb_old_log_probs)
                
                surr1 = ratio * mb_advantages
                surr2 = torch.clamp(
                    ratio,
                    1 - self.config.clip_epsilon,
                    1 + self.config.clip_epsilon
                ) * mb_advantages
                policy_loss = -torch.min(surr1, surr2).mean()
                
                value_loss = F.mse_loss(new_values, mb_returns)
                
                entropy_loss = -entropy.mean()
                
                loss = (
                    policy_loss +
                    self.config.value_coef * value_loss +
                    self.config.entropy_coef * entropy_loss
                )
                
                self.optimizer.zero_grad()
                loss.backward()
                nn.utils.clip_grad_norm_(
                    list(self.policy_network.parameters()) +
                    list(self.value_network.parameters()),
                    self.config.max_grad_norm
                )
                self.optimizer.step()
                
                total_policy_loss += policy_loss.item()
                total_value_loss += value_loss.item()
                total_entropy_loss += entropy_loss.item()
        
        n_updates = self.config.update_epochs * (len(self.buffer) // self.config.mini_batch_size)
        
        stats = {
            "policy_loss": total_policy_loss / n_updates,
            "value_loss": total_value_loss / n_updates,
            "entropy_loss": total_entropy_loss / n_updates,
            "mean_reward": np.mean(self.buffer.rewards),
            "mean_advantage": np.mean(self.buffer.advantages),
            "buffer_size": len(self.buffer)
        }
        
        self._update_training_stats(stats)
        self.buffer.clear()
        
        return stats
    
    def _update_simple(self) -> Dict[str, float]:
        """简化版更新（无PyTorch）"""
        self.buffer.compute_gae(
            gamma=self.config.gamma,
            gae_lambda=self.config.gae_lambda
        )
        
        learning_rate = self.config.learning_rate
        
        for i in range(len(self.buffer)):
            state = self.buffer.states[i]
            action = self.buffer.actions[i]
            advantage = self.buffer.advantages[i]
            ret = self.buffer.returns[i]
            
            state_hash = self._hash_state(state)
            
            if state_hash not in self._simple_policy:
                self._simple_policy[state_hash] = np.random.dirichlet(
                    np.ones(self.config.action_dim)
                )
            
            if state_hash not in self._simple_value:
                self._simple_value[state_hash] = 0.0
            
            probs = self._simple_policy[state_hash]
            
            if advantage > 0:
                probs[action] = min(1.0, probs[action] + learning_rate * abs(advantage))
            else:
                probs[action] = max(0.01, probs[action] - learning_rate * abs(advantage))
            
            probs = probs / probs.sum()
            self._simple_policy[state_hash] = probs
            
            self._simple_value[state_hash] += learning_rate * (ret - self._simple_value[state_hash])
        
        stats = {
            "policy_loss": 0.0,
            "value_loss": 0.0,
            "entropy_loss": 0.0,
            "mean_reward": np.mean(self.buffer.rewards) if self.buffer.rewards else 0.0,
            "mean_advantage": np.mean(self.buffer.advantages) if self.buffer.advantages else 0.0,
            "buffer_size": len(self.buffer)
        }
        
        self._update_training_stats(stats)
        self.buffer.clear()
        
        return stats
    
    def _update_training_stats(self, stats: Dict[str, float]):
        """更新训练统计"""
        self.training_stats["total_steps"] += stats.get("buffer_size", 0)
        
        if "policy_loss" in stats:
            self.training_stats["policy_losses"].append(stats["policy_loss"])
        if "value_loss" in stats:
            self.training_stats["value_losses"].append(stats["value_loss"])
        if "entropy_loss" in stats:
            self.training_stats["entropy_losses"].append(stats["entropy_loss"])
        if "mean_reward" in stats:
            self.training_stats["mean_rewards"].append(stats["mean_reward"])
        if "mean_advantage" in stats:
            self.training_stats["mean_advantages"].append(stats["mean_advantage"])
        
        max_history = 1000
        for key in ["policy_losses", "value_losses", "entropy_losses", "mean_rewards", "mean_advantages"]:
            if len(self.training_stats[key]) > max_history:
                self.training_stats[key] = self.training_stats[key][-max_history:]
    
    def train_from_experiences(
        self,
        experiences: List[Experience]
    ) -> Dict[str, float]:
        """从经验列表训练"""
        for exp in experiences:
            if not exp.state or not exp.action or not exp.reward:
                continue
            
            state_vec = exp.state.to_vector()
            
            action_idx = abs(hash(exp.action.action_type)) % self.config.action_dim
            
            reward_val = exp.reward.total if exp.reward else 0.0
            
            _, log_prob, value = self.select_action(state_vec)
            
            self.store_transition(
                state=state_vec,
                action=action_idx,
                reward=reward_val,
                value=value,
                log_prob=log_prob,
                done=exp.done
            )
        
        return self.update()
    
    def save_model(self, path: str):
        """保存模型"""
        if self._use_torch:
            torch.save({
                'policy_network': self.policy_network.state_dict(),
                'value_network': self.value_network.state_dict(),
                'optimizer': self.optimizer.state_dict(),
                'config': self.config.__dict__,
                'training_stats': self.training_stats
            }, path)
        else:
            import pickle
            with open(path, 'wb') as f:
                pickle.dump({
                    'policy': self._simple_policy,
                    'value': self._simple_value,
                    'config': self.config.__dict__,
                    'training_stats': self.training_stats
                }, f)
    
    def load_model(self, path: str):
        """加载模型"""
        if self._use_torch:
            checkpoint = torch.load(path, map_location=self.device)
            self.policy_network.load_state_dict(checkpoint['policy_network'])
            self.value_network.load_state_dict(checkpoint['value_network'])
            self.optimizer.load_state_dict(checkpoint['optimizer'])
            self.training_stats = checkpoint.get('training_stats', self.training_stats)
        else:
            import pickle
            with open(path, 'rb') as f:
                data = pickle.load(f)
                self._simple_policy = data.get('policy', {})
                self._simple_value = data.get('value', {})
                self.training_stats = data.get('training_stats', self.training_stats)
    
    def get_training_summary(self) -> Dict[str, Any]:
        """获取训练摘要"""
        summary = {
            "total_steps": self.training_stats["total_steps"],
            "total_updates": len(self.training_stats["policy_losses"]),
            "buffer_size": len(self.buffer),
            "recent_mean_reward": 0.0,
            "recent_policy_loss": 0.0,
            "recent_value_loss": 0.0
        }
        
        if self.training_stats["mean_rewards"]:
            summary["recent_mean_reward"] = np.mean(self.training_stats["mean_rewards"][-10:])
        
        if self.training_stats["policy_losses"]:
            summary["recent_policy_loss"] = np.mean(self.training_stats["policy_losses"][-10:])
        
        if self.training_stats["value_losses"]:
            summary["recent_value_loss"] = np.mean(self.training_stats["value_losses"][-10:])
        
        return summary


class MultiAgentPPOTrainer:
    """多智能体PPO训练器"""
    
    def __init__(
        self,
        agent_ids: List[str],
        shared_config: Optional[PPOConfig] = None
    ):
        self.agent_ids = agent_ids
        self.shared_config = shared_config or PPOConfig()
        
        self.trainers: Dict[str, PPOTrainer] = {
            agent_id: PPOTrainer(self.shared_config)
            for agent_id in agent_ids
        }
        
        self.shared_buffer: Dict[str, List[Experience]] = {
            agent_id: [] for agent_id in agent_ids
        }
    
    def select_action(
        self,
        agent_id: str,
        state: np.ndarray,
        deterministic: bool = False
    ) -> Tuple[int, float, float]:
        """为指定智能体选择动作"""
        if agent_id not in self.trainers:
            raise ValueError(f"Unknown agent: {agent_id}")
        
        return self.trainers[agent_id].select_action(state, deterministic)
    
    def store_shared_experience(
        self,
        agent_id: str,
        experience: Experience
    ):
        """存储共享经验"""
        if agent_id in self.shared_buffer:
            self.shared_buffer[agent_id].append(experience)
    
    def update_all(self) -> Dict[str, Dict[str, float]]:
        """更新所有智能体"""
        results = {}
        
        for agent_id, trainer in self.trainers.items():
            if self.shared_buffer[agent_id]:
                results[agent_id] = trainer.train_from_experiences(
                    self.shared_buffer[agent_id]
                )
                self.shared_buffer[agent_id].clear()
            else:
                results[agent_id] = trainer.update()
        
        return results
    
    def compute_collaborative_reward(
        self,
        individual_rewards: Dict[str, float],
        task_success: bool
    ) -> Dict[str, float]:
        """计算协作奖励"""
        base_rewards = individual_rewards.copy()
        
        if task_success:
            bonus = 0.2
            for agent_id in base_rewards:
                base_rewards[agent_id] += bonus
        
        return base_rewards
    
    def get_global_summary(self) -> Dict[str, Any]:
        """获取全局训练摘要"""
        summaries = {}
        for agent_id, trainer in self.trainers.items():
            summaries[agent_id] = trainer.get_training_summary()
        
        total_steps = sum(s["total_steps"] for s in summaries.values())
        avg_reward = np.mean([s["recent_mean_reward"] for s in summaries.values()])
        
        return {
            "total_steps": total_steps,
            "avg_reward": avg_reward,
            "agent_summaries": summaries
        }


ppo_trainer = PPOTrainer()
