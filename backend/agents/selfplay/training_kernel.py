"""
刑部智能体自博弈对抗训练内核
Ministry of Justice Self-Play Adversarial Training Kernel

实现完整的攻防对抗训练系统，包括：
- 攻击智能体 (AttackAgent)
- 防御智能体 (DefenseAgent with VAE)
- 高级对抗环境 (CyberBattleEnv)
- QMIX多智能体协同
- 对抗鲁棒训练
- 部署模块
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
from collections import deque

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.distributions import Categorical, Normal


class AttackType(Enum):
    """攻击类型"""
    NONE = 0
    DDOS = 1
    CC = 2
    SQL_INJECTION = 3
    MIXED = 4
    LOW_AND_SLOW = 5
    DNS_AMPLIFICATION = 6
    SYN_FLOOD = 7


class DefenseAction(Enum):
    """防御动作"""
    ALLOW = 0
    RATE_LIMIT = 1
    CAPTCHA = 2
    BLOCK_IP = 3
    BLOCK_DEVICE = 4
    TRAFFIC_SCRUBBING = 5
    SWITCH_HIGH_DEFENSE = 6
    CHALLENGE = 7


class NetworkState:
    """网络状态"""
    
    def __init__(
        self,
        bandwidth_mbps: float = 1000.0,
        cpu_capacity: float = 100.0,
        max_connections: int = 10000,
        max_qps: int = 100000
    ):
        self.bandwidth_total = bandwidth_mbps
        self.cpu_total = cpu_capacity
        self.max_connections = max_connections
        self.max_qps = max_qps
        
        self.bandwidth_used = 0.0
        self.cpu_used = 0.0
        self.active_connections = 0
        self.current_qps = 0
        
        self.response_time_ms = 10.0
        self.error_rate = 0.0
        self.packet_loss_rate = 0.0
        
        self.attack_detected = False
        self.attack_type = 0
        self.attack_intensity = 0.0
        
        self.defense_active = False
        self.defense_action = 0
        
        self.time_step = 0
        self.max_steps = 100
    
    def to_vector(self) -> np.ndarray:
        """转换为状态向量"""
        return np.array([
            self.bandwidth_used / self.bandwidth_total,
            self.cpu_used / self.cpu_total,
            self.active_connections / self.max_connections,
            self.current_qps / self.max_qps,
            self.response_time_ms / 1000.0,
            self.error_rate,
            self.packet_loss_rate,
            float(self.attack_detected),
            self.attack_type / 7.0,
            self.attack_intensity,
            float(self.defense_active),
            self.defense_action / 7.0,
            self.time_step / self.max_steps
        ], dtype=np.float32)
    
    def reset(self):
        """重置状态"""
        self.bandwidth_used = 0.0
        self.cpu_used = 0.0
        self.active_connections = 0
        self.current_qps = 0
        self.response_time_ms = 10.0
        self.error_rate = 0.0
        self.packet_loss_rate = 0.0
        self.attack_detected = False
        self.attack_type = 0
        self.attack_intensity = 0.0
        self.defense_active = False
        self.defense_action = 0
        self.time_step = 0
    
    def is_service_down(self) -> bool:
        """检查服务是否不可用"""
        return (
            self.cpu_used >= self.cpu_total * 0.99 or
            self.response_time_ms > 5000 or
            self.error_rate > 0.5
        )


class CyberBattleEnv:
    """高级网络攻防对抗环境"""
    
    STATE_DIM = 13
    ATTACK_ACTION_DIM = 8
    DEFENSE_ACTION_DIM = 8
    
    def __init__(
        self,
        bandwidth_mbps: float = 1000.0,
        cpu_capacity: float = 100.0,
        max_connections: int = 10000,
        max_qps: int = 100000,
        max_steps: int = 100
    ):
        self.state = NetworkState(
            bandwidth_mbps=bandwidth_mbps,
            cpu_capacity=cpu_capacity,
            max_connections=max_connections,
            max_qps=max_qps
        )
        self.max_steps = max_steps
        
        self._attack_history: List[Dict] = []
        self._defense_history: List[Dict] = []
        self._episode_history: List[Dict] = []
    
    def reset(self) -> Tuple[Dict[str, np.ndarray], Dict]:
        """重置环境"""
        self.state.reset()
        self._attack_history.clear()
        self._defense_history.clear()
        self._episode_history.clear()
        
        states = {
            "attacker": self._get_attacker_state(),
            "defender": self._get_defender_state()
        }
        
        return states, {"initial": True}
    
    def _get_attacker_state(self) -> np.ndarray:
        """获取攻击者视角状态"""
        return np.array([
            self.state.bandwidth_used / self.state.bandwidth_total,
            self.state.cpu_used / self.state.cpu_total,
            self.state.active_connections / self.state.max_connections,
            self.state.current_qps / self.state.max_qps,
            self.state.response_time_ms / 1000.0,
            float(self.state.defense_active),
            self.state.defense_action / 7.0,
            self.state.time_step / self.max_steps
        ], dtype=np.float32)
    
    def _get_defender_state(self) -> np.ndarray:
        """获取防御者视角状态"""
        return self.state.to_vector()
    
    def step(
        self,
        attack_action: int,
        attack_intensity: float,
        defense_action: int
    ) -> Tuple[Dict[str, np.ndarray], Dict[str, float], bool, Dict]:
        """执行一步攻防"""
        self.state.time_step += 1
        
        attack_effect = self._apply_attack(attack_action, attack_intensity)
        defense_effect = self._apply_defense(defense_action, attack_effect)
        
        attacker_reward = self._compute_attacker_reward(attack_effect, defense_effect)
        defender_reward = self._compute_defender_reward(attack_effect, defense_effect)
        
        done = self.state.is_service_down() or self.state.time_step >= self.max_steps
        
        self._episode_history.append({
            "step": self.state.time_step,
            "attack_action": attack_action,
            "attack_intensity": attack_intensity,
            "defense_action": defense_action,
            "attacker_reward": attacker_reward,
            "defender_reward": defender_reward,
            "state": {
                "bandwidth_used": self.state.bandwidth_used,
                "cpu_used": self.state.cpu_used,
                "response_time": self.state.response_time_ms
            }
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
            "service_down": self.state.is_service_down()
        }
        
        return states, rewards, done, info
    
    def _apply_attack(self, action: int, intensity: float) -> Dict:
        """应用攻击效果"""
        effect = {
            "type": action,
            "intensity": intensity,
            "success": False,
            "resource_cost": 0.0
        }
        
        if action == 0:
            return effect
        
        attack_configs = {
            1: {"bandwidth_impact": 0.8, "cpu_impact": 0.1, "qps_increase": 50000, "cost": 5.0},
            2: {"bandwidth_impact": 0.3, "cpu_impact": 0.7, "qps_increase": 10000, "cost": 3.0},
            3: {"bandwidth_impact": 0.1, "cpu_impact": 0.5, "qps_increase": 100, "cost": 2.0},
            4: {"bandwidth_impact": 0.5, "cpu_impact": 0.5, "qps_increase": 30000, "cost": 8.0},
            5: {"bandwidth_impact": 0.2, "cpu_impact": 0.3, "qps_increase": 500, "cost": 1.0},
            6: {"bandwidth_impact": 0.9, "cpu_impact": 0.2, "qps_increase": 80000, "cost": 10.0},
            7: {"bandwidth_impact": 0.6, "cpu_impact": 0.4, "qps_increase": 40000, "cost": 6.0},
        }
        
        if action in attack_configs:
            config = attack_configs[action]
            
            self.state.bandwidth_used += config["bandwidth_impact"] * intensity * self.state.bandwidth_total
            self.state.cpu_used += config["cpu_impact"] * intensity * self.state.cpu_total
            self.state.current_qps += config["qps_increase"] * intensity
            self.state.active_connections += int(config["qps_increase"] * intensity * 0.1)
            
            self.state.attack_type = action
            self.state.attack_intensity = intensity
            self.state.attack_detected = True
            
            base_response = 10.0
            self.state.response_time_ms = base_response + (
                self.state.bandwidth_used / self.state.bandwidth_total * 100 +
                self.state.cpu_used / self.state.cpu_total * 200
            )
            
            if self.state.cpu_used > self.state.cpu_total * 0.8:
                self.state.error_rate = min(0.5, (self.state.cpu_used / self.state.cpu_total - 0.8) * 2)
            
            effect["success"] = True
            effect["resource_cost"] = config["cost"] * intensity
        
        return effect
    
    def _apply_defense(self, action: int, attack_effect: Dict) -> Dict:
        """应用防御效果"""
        effect = {
            "action": action,
            "blocked": False,
            "false_positive": False,
            "mitigation_ratio": 0.0
        }
        
        self.state.defense_active = True
        self.state.defense_action = action
        
        attack_type = attack_effect.get("type", 0)
        attack_intensity = attack_effect.get("intensity", 0.0)
        
        defense_matrix = {
            0: {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0, 6: 0.0, 7: 0.0},
            1: {1: 0.3, 2: 0.5, 3: 0.1, 4: 0.3, 5: 0.4, 6: 0.2, 7: 0.3},
            2: {1: 0.2, 2: 0.7, 3: 0.3, 4: 0.4, 5: 0.6, 6: 0.1, 7: 0.3},
            3: {1: 0.6, 2: 0.4, 3: 0.5, 4: 0.5, 5: 0.3, 6: 0.5, 7: 0.6},
            4: {1: 0.7, 2: 0.5, 3: 0.6, 4: 0.6, 5: 0.4, 6: 0.6, 7: 0.7},
            5: {1: 0.8, 2: 0.6, 3: 0.4, 4: 0.7, 5: 0.5, 6: 0.9, 7: 0.8},
            6: {1: 0.95, 2: 0.9, 3: 0.8, 4: 0.95, 5: 0.85, 6: 0.95, 7: 0.95},
            7: {1: 0.5, 2: 0.6, 3: 0.7, 4: 0.5, 5: 0.5, 6: 0.4, 7: 0.5},
        }
        
        if attack_type > 0:
            mitigation = defense_matrix.get(action, {}).get(attack_type, 0.0)
            mitigation *= (1.0 - 0.1 * random.random())
            
            effect["mitigation_ratio"] = mitigation
            
            if random.random() < mitigation:
                effect["blocked"] = True
                
                self.state.bandwidth_used *= (1 - mitigation * 0.8)
                self.state.cpu_used *= (1 - mitigation * 0.7)
                self.state.current_qps = int(self.state.current_qps * (1 - mitigation * 0.9))
                self.state.active_connections = int(self.state.active_connections * (1 - mitigation * 0.8))
                
                self.state.response_time_ms = max(10, self.state.response_time_ms * (1 - mitigation * 0.5))
                self.state.error_rate *= (1 - mitigation * 0.6)
        
        if action in [3, 4] and attack_type == 0:
            effect["false_positive"] = True
        
        return effect
    
    def _compute_attacker_reward(self, attack_effect: Dict, defense_effect: Dict) -> float:
        """计算攻击者奖励"""
        reward = 0.0
        
        if self.state.is_service_down():
            reward += 100.0
        
        if self.state.response_time_ms > 100:
            reward += 10.0 * (self.state.response_time_ms / 100)
        elif self.state.response_time_ms > 50:
            reward += 5.0
        
        if attack_effect.get("success"):
            if not defense_effect.get("blocked"):
                reward += 20.0 * attack_effect.get("intensity", 0)
            else:
                reward -= 10.0
        
        if defense_effect.get("false_positive"):
            reward += 20.0
        
        reward -= attack_effect.get("resource_cost", 0) * 0.1
        
        return reward
    
    def _compute_defender_reward(self, attack_effect: Dict, defense_effect: Dict) -> float:
        """计算防御者奖励"""
        reward = 0.0
        
        if defense_effect.get("blocked"):
            reward += 10.0 * attack_effect.get("intensity", 0)
        
        if self.state.response_time_ms < 50:
            reward += 5.0
        elif self.state.response_time_ms < 100:
            reward += 2.0
        elif self.state.response_time_ms > 500:
            reward -= 10.0
        
        if defense_effect.get("false_positive"):
            reward -= 20.0
        
        if self.state.is_service_down():
            reward -= 100.0
        
        if self.state.error_rate > 0.1:
            reward -= 10.0 * self.state.error_rate
        
        return reward
    
    def get_history(self) -> List[Dict]:
        return self._episode_history


class VAEFeatureExtractor(nn.Module):
    """VAE特征提取器"""
    
    def __init__(self, input_dim: int, latent_dim: int = 32, hidden_dim: int = 64):
        super().__init__()
        
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim)
        )
        
        self.fc_mu = nn.Linear(hidden_dim, latent_dim)
        self.fc_logvar = nn.Linear(hidden_dim, latent_dim)
        
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, input_dim)
        )
    
    def encode(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        h = self.encoder(x)
        return self.fc_mu(h), self.fc_logvar(h)
    
    def reparameterize(self, mu: torch.Tensor, logvar: torch.Tensor) -> torch.Tensor:
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        return mu + eps * std
    
    def decode(self, z: torch.Tensor) -> torch.Tensor:
        return self.decoder(z)
    
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        mu, logvar = self.encode(x)
        z = self.reparameterize(mu, logvar)
        return self.decode(z), mu, logvar
    
    def get_latent(self, x: torch.Tensor) -> torch.Tensor:
        mu, _ = self.encode(x)
        return mu
    
    def reconstruction_loss(self, x: torch.Tensor, recon_x: torch.Tensor) -> torch.Tensor:
        return F.mse_loss(recon_x, x, reduction='sum')
    
    def kl_loss(self, mu: torch.Tensor, logvar: torch.Tensor) -> torch.Tensor:
        return -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp())


class AttackPolicyNetwork(nn.Module):
    """攻击策略网络"""
    
    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        hidden_dim: int = 256,
        latent_dim: int = 32
    ):
        super().__init__()
        
        self.features = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU()
        )
        
        self.action_head = nn.Linear(hidden_dim, action_dim)
        self.intensity_head = nn.Sequential(
            nn.Linear(hidden_dim, 1),
            nn.Sigmoid()
        )
        
        self.value_head = nn.Linear(hidden_dim, 1)
    
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        features = self.features(x)
        action_logits = self.action_head(features)
        intensity = self.intensity_head(features)
        value = self.value_head(features)
        return action_logits, intensity, value


class DefensePolicyNetwork(nn.Module):
    """防御策略网络（含VAE）"""
    
    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        hidden_dim: int = 256,
        latent_dim: int = 32
    ):
        super().__init__()
        
        self.vae = VAEFeatureExtractor(state_dim, latent_dim)
        
        self.features = nn.Sequential(
            nn.Linear(latent_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU()
        )
        
        self.action_head = nn.Linear(hidden_dim, action_dim)
        self.value_head = nn.Linear(hidden_dim, 1)
    
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        recon, mu, logvar = self.vae(x)
        
        features = self.features(mu)
        action_logits = self.action_head(features)
        value = self.value_head(features)
        
        return action_logits, value, recon, mu, logvar
    
    def get_action(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        with torch.no_grad():
            latent = self.vae.get_latent(x)
            features = self.features(latent)
            action_logits = self.action_head(features)
            value = self.value_head(features)
        return action_logits, value


class AttackAgent:
    """攻击智能体"""
    
    def __init__(
        self,
        agent_id: str,
        state_dim: int,
        action_dim: int,
        device: str = "cpu",
        lr: float = 3e-4
    ):
        self.agent_id = agent_id
        self.device = device
        
        self.policy = AttackPolicyNetwork(state_dim, action_dim).to(device)
        self.optimizer = optim.Adam(self.policy.parameters(), lr=lr)
        
        self.buffer = []
        self.version = 1
        self.total_games = 0
        self.wins = 0
        self.total_reward = 0.0
    
    def select_action(
        self,
        state: np.ndarray,
        deterministic: bool = False
    ) -> Tuple[int, float, float, float]:
        """选择攻击动作"""
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            action_logits, intensity, value = self.policy(state_tensor)
            
            dist = Categorical(logits=action_logits)
            
            if deterministic:
                action = torch.argmax(action_logits, dim=-1)
            else:
                action = dist.sample()
            
            log_prob = dist.log_prob(action)
            
            intensity_value = intensity.item()
        
        return action.item(), intensity_value, log_prob.item(), value.item()
    
    def store_experience(
        self,
        state: np.ndarray,
        action: int,
        intensity: float,
        log_prob: float,
        value: float,
        reward: float,
        done: bool
    ):
        """存储经验"""
        self.buffer.append({
            "state": state,
            "action": action,
            "intensity": intensity,
            "log_prob": log_prob,
            "value": value,
            "reward": reward,
            "done": done
        })
    
    def update(self, gamma: float = 0.99, clip_epsilon: float = 0.2, epochs: int = 10) -> Dict:
        """更新策略"""
        if len(self.buffer) < 10:
            return {}
        
        returns = []
        advantages = []
        gae = 0.0
        
        for i in reversed(range(len(self.buffer))):
            if i == len(self.buffer) - 1:
                next_value = 0.0
            else:
                next_value = self.buffer[i + 1]["value"]
            
            delta = self.buffer[i]["reward"] + gamma * next_value * (1 - self.buffer[i]["done"]) - self.buffer[i]["value"]
            gae = delta + gamma * 0.95 * (1 - self.buffer[i]["done"]) * gae
            
            advantages.insert(0, gae)
            returns.insert(0, gae + self.buffer[i]["value"])
        
        states = torch.FloatTensor(np.array([e["state"] for e in self.buffer])).to(self.device)
        actions = torch.LongTensor([e["action"] for e in self.buffer]).to(self.device)
        old_log_probs = torch.FloatTensor([e["log_prob"] for e in self.buffer]).to(self.device)
        advantages_tensor = torch.FloatTensor(advantages).to(self.device)
        returns_tensor = torch.FloatTensor(returns).to(self.device)
        
        advantages_tensor = (advantages_tensor - advantages_tensor.mean()) / (advantages_tensor.std() + 1e-8)
        
        total_loss = 0.0
        
        for _ in range(epochs):
            action_logits, intensity, values = self.policy(states)
            
            dist = Categorical(logits=action_logits)
            log_probs = dist.log_prob(actions)
            
            ratio = torch.exp(log_probs - old_log_probs)
            
            surr1 = ratio * advantages_tensor
            surr2 = torch.clamp(ratio, 1 - clip_epsilon, 1 + clip_epsilon) * advantages_tensor
            
            policy_loss = -torch.min(surr1, surr2).mean()
            value_loss = F.mse_loss(values.squeeze(), returns_tensor)
            
            loss = policy_loss + 0.5 * value_loss
            
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()
            
            total_loss += loss.item()
        
        self.buffer.clear()
        self.version += 1
        
        return {"loss": total_loss / epochs}
    
    def record_game(self, reward: float, won: bool):
        self.total_games += 1
        self.total_reward += reward
        if won:
            self.wins += 1
    
    def get_status(self) -> Dict:
        return {
            "agent_id": self.agent_id,
            "version": self.version,
            "total_games": self.total_games,
            "wins": self.wins,
            "win_rate": self.wins / self.total_games if self.total_games > 0 else 0.0,
            "avg_reward": self.total_reward / self.total_games if self.total_games > 0 else 0.0
        }


class DefenseAgent:
    """防御智能体（含VAE）"""
    
    def __init__(
        self,
        agent_id: str,
        state_dim: int,
        action_dim: int,
        device: str = "cpu",
        lr: float = 3e-4,
        vae_weight: float = 0.1
    ):
        self.agent_id = agent_id
        self.device = device
        self.vae_weight = vae_weight
        
        self.policy = DefensePolicyNetwork(state_dim, action_dim).to(device)
        self.optimizer = optim.Adam(self.policy.parameters(), lr=lr)
        
        self.buffer = []
        self.version = 1
        self.total_games = 0
        self.wins = 0
        self.total_reward = 0.0
        
        self.tpr_history = []
        self.fpr_history = []
    
    def select_action(
        self,
        state: np.ndarray,
        deterministic: bool = False
    ) -> Tuple[int, float, float]:
        """选择防御动作"""
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            action_logits, value = self.policy.get_action(state_tensor)
            
            dist = Categorical(logits=action_logits)
            
            if deterministic:
                action = torch.argmax(action_logits, dim=-1)
            else:
                action = dist.sample()
            
            log_prob = dist.log_prob(action)
        
        return action.item(), log_prob.item(), value.item()
    
    def store_experience(
        self,
        state: np.ndarray,
        action: int,
        log_prob: float,
        value: float,
        reward: float,
        done: bool
    ):
        """存储经验"""
        self.buffer.append({
            "state": state,
            "action": action,
            "log_prob": log_prob,
            "value": value,
            "reward": reward,
            "done": done
        })
    
    def update(
        self,
        gamma: float = 0.99,
        clip_epsilon: float = 0.2,
        epochs: int = 10
    ) -> Dict:
        """更新策略"""
        if len(self.buffer) < 10:
            return {}
        
        returns = []
        advantages = []
        gae = 0.0
        
        for i in reversed(range(len(self.buffer))):
            if i == len(self.buffer) - 1:
                next_value = 0.0
            else:
                next_value = self.buffer[i + 1]["value"]
            
            delta = self.buffer[i]["reward"] + gamma * next_value * (1 - self.buffer[i]["done"]) - self.buffer[i]["value"]
            gae = delta + gamma * 0.95 * (1 - self.buffer[i]["done"]) * gae
            
            advantages.insert(0, gae)
            returns.insert(0, gae + self.buffer[i]["value"])
        
        states = torch.FloatTensor(np.array([e["state"] for e in self.buffer])).to(self.device)
        actions = torch.LongTensor([e["action"] for e in self.buffer]).to(self.device)
        old_log_probs = torch.FloatTensor([e["log_prob"] for e in self.buffer]).to(self.device)
        advantages_tensor = torch.FloatTensor(advantages).to(self.device)
        returns_tensor = torch.FloatTensor(returns).to(self.device)
        
        advantages_tensor = (advantages_tensor - advantages_tensor.mean()) / (advantages_tensor.std() + 1e-8)
        
        total_loss = 0.0
        total_vae_loss = 0.0
        
        for _ in range(epochs):
            action_logits, values, recon, mu, logvar = self.policy(states)
            
            dist = Categorical(logits=action_logits)
            log_probs = dist.log_prob(actions)
            
            ratio = torch.exp(log_probs - old_log_probs)
            
            surr1 = ratio * advantages_tensor
            surr2 = torch.clamp(ratio, 1 - clip_epsilon, 1 + clip_epsilon) * advantages_tensor
            
            policy_loss = -torch.min(surr1, surr2).mean()
            value_loss = F.mse_loss(values.squeeze(), returns_tensor)
            
            recon_loss = self.policy.vae.reconstruction_loss(states, recon)
            kl_loss = self.policy.vae.kl_loss(mu, logvar)
            vae_loss = recon_loss + 0.001 * kl_loss
            
            loss = policy_loss + 0.5 * value_loss + self.vae_weight * vae_loss
            
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()
            
            total_loss += loss.item()
            total_vae_loss += vae_loss.item()
        
        self.buffer.clear()
        self.version += 1
        
        return {
            "loss": total_loss / epochs,
            "vae_loss": total_vae_loss / epochs
        }
    
    def record_game(self, reward: float, won: bool, tpr: float = 0.0, fpr: float = 0.0):
        self.total_games += 1
        self.total_reward += reward
        if won:
            self.wins += 1
        
        if tpr > 0:
            self.tpr_history.append(tpr)
        if fpr > 0:
            self.fpr_history.append(fpr)
    
    def get_status(self) -> Dict:
        return {
            "agent_id": self.agent_id,
            "version": self.version,
            "total_games": self.total_games,
            "wins": self.wins,
            "win_rate": self.wins / self.total_games if self.total_games > 0 else 0.0,
            "avg_reward": self.total_reward / self.total_games if self.total_games > 0 else 0.0,
            "avg_tpr": np.mean(self.tpr_history) if self.tpr_history else 0.0,
            "avg_fpr": np.mean(self.fpr_history) if self.fpr_history else 0.0
        }


class QMIXNetwork(nn.Module):
    """QMIX混合网络"""
    
    def __init__(
        self,
        state_dim: int,
        n_agents: int,
        mixing_hidden_dim: int = 64
    ):
        super().__init__()
        
        self.n_agents = n_agents
        
        self.hyper_w1 = nn.Sequential(
            nn.Linear(state_dim, mixing_hidden_dim),
            nn.ReLU(),
            nn.Linear(mixing_hidden_dim, n_agents * mixing_hidden_dim)
        )
        
        self.hyper_w2 = nn.Sequential(
            nn.Linear(state_dim, mixing_hidden_dim),
            nn.ReLU(),
            nn.Linear(mixing_hidden_dim, mixing_hidden_dim)
        )
        
        self.hyper_b1 = nn.Linear(state_dim, mixing_hidden_dim)
        self.hyper_b2 = nn.Sequential(
            nn.Linear(state_dim, mixing_hidden_dim),
            nn.ReLU(),
            nn.Linear(mixing_hidden_dim, 1)
        )
    
    def forward(self, agent_qs: torch.Tensor, states: torch.Tensor) -> torch.Tensor:
        batch_size = agent_qs.size(0)
        
        w1 = torch.abs(self.hyper_w1(states))
        w1 = w1.view(-1, self.n_agents, -1)
        
        b1 = self.hyper_b1(states)
        
        hidden = F.elu(torch.bmm(agent_qs.unsqueeze(1), w1).squeeze(1) + b1)
        
        w2 = torch.abs(self.hyper_w2(states))
        w2 = w2.view(-1, -1)
        
        b2 = self.hyper_b2(states)
        
        q_tot = torch.bmm(hidden.unsqueeze(1), w2.unsqueeze(2)).squeeze() + b2.squeeze()
        
        return q_tot


class SelfPlayTrainingKernel:
    """自博弈训练内核"""
    
    def __init__(
        self,
        env: CyberBattleEnv,
        n_attackers: int = 8,
        n_defenders: int = 8,
        device: str = "cpu"
    ):
        self.env = env
        self.n_attackers = n_attackers
        self.n_defenders = n_defenders
        self.device = device
        
        self.attacker_population: List[AttackAgent] = []
        self.defender_population: List[DefenseAgent] = []
        
        self._init_populations()
        
        self.total_episodes = 0
        self.training_history: List[Dict] = []
        self.champion: Optional[DefenseAgent] = None
    
    def _init_populations(self):
        """初始化种群"""
        attacker_state_dim = 8
        defender_state_dim = 13
        
        for i in range(self.n_attackers):
            attacker = AttackAgent(
                agent_id=f"attacker_{i}",
                state_dim=attacker_state_dim,
                action_dim=self.env.ATTACK_ACTION_DIM,
                device=self.device
            )
            self.attacker_population.append(attacker)
        
        for i in range(self.n_defenders):
            defender = DefenseAgent(
                agent_id=f"defender_{i}",
                state_dim=defender_state_dim,
                action_dim=self.env.DEFENSE_ACTION_DIM,
                device=self.device
            )
            self.defender_population.append(defender)
    
    def run_episode(
        self,
        attacker: AttackAgent,
        defender: DefenseAgent,
        max_steps: int = 100
    ) -> Dict:
        """运行一局对战"""
        states, info = self.env.reset()
        
        attacker_state = states["attacker"]
        defender_state = states["defender"]
        
        total_attacker_reward = 0.0
        total_defender_reward = 0.0
        
        true_positives = 0
        false_positives = 0
        total_attacks = 0
        
        for step in range(max_steps):
            attack_action, intensity, attack_log_prob, attack_value = attacker.select_action(attacker_state)
            defense_action, defense_log_prob, defense_value = defender.select_action(defender_state)
            
            states, rewards, done, info = self.env.step(attack_action, intensity, defense_action)
            
            attacker.store_experience(
                attacker_state, attack_action, intensity,
                attack_log_prob, attack_value, rewards["attacker"], done
            )
            
            defender.store_experience(
                defender_state, defense_action,
                defense_log_prob, defense_value, rewards["defender"], done
            )
            
            total_attacker_reward += rewards["attacker"]
            total_defender_reward += rewards["defender"]
            
            if attack_action > 0:
                total_attacks += 1
                if info.get("defense_effect", {}).get("blocked"):
                    true_positives += 1
            
            if info.get("defense_effect", {}).get("false_positive"):
                false_positives += 1
            
            attacker_state = states["attacker"]
            defender_state = states["defender"]
            
            if done:
                break
        
        attacker_won = total_attacker_reward > total_defender_reward
        
        tpr = true_positives / total_attacks if total_attacks > 0 else 0.0
        fpr = false_positives / (step + 1 - total_attacks) if (step + 1 - total_attacks) > 0 else 0.0
        
        attacker.record_game(total_attacker_reward, attacker_won)
        defender.record_game(total_defender_reward, not attacker_won, tpr, fpr)
        
        self.total_episodes += 1
        
        return {
            "episode": self.total_episodes,
            "attacker_id": attacker.agent_id,
            "defender_id": defender.agent_id,
            "attacker_reward": total_attacker_reward,
            "defender_reward": total_defender_reward,
            "attacker_won": attacker_won,
            "steps": step + 1,
            "tpr": tpr,
            "fpr": fpr
        }
    
    def train_step(self, update_interval: int = 10) -> Dict:
        """训练一步"""
        attacker = random.choice(self.attacker_population)
        defender = random.choice(self.defender_population)
        
        episode_result = self.run_episode(attacker, defender)
        
        metrics = {}
        
        if self.total_episodes % update_interval == 0:
            attacker_metrics = attacker.update()
            defender_metrics = defender.update()
            
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
        """评估智能体"""
        best_defender = max(self.defender_population, key=lambda a: a.wins / max(a.total_games, 1))
        best_attacker = max(self.attacker_population, key=lambda a: a.wins / max(a.total_games, 1))
        
        attacker_wins = 0
        defender_wins = 0
        total_tpr = 0.0
        total_fpr = 0.0
        
        for _ in range(num_games):
            result = self.run_episode(best_attacker, best_defender)
            
            if result["attacker_won"]:
                attacker_wins += 1
            else:
                defender_wins += 1
            
            total_tpr += result["tpr"]
            total_fpr += result["fpr"]
        
        return {
            "attacker_wins": attacker_wins,
            "defender_wins": defender_wins,
            "attacker_win_rate": attacker_wins / num_games,
            "defender_win_rate": defender_wins / num_games,
            "avg_tpr": total_tpr / num_games,
            "avg_fpr": total_fpr / num_games,
            "best_attacker_id": best_attacker.agent_id,
            "best_defender_id": best_defender.agent_id
        }
    
    def save_champion(self, path: str):
        """保存冠军模型"""
        best_defender = max(self.defender_population, key=lambda a: a.wins / max(a.total_games, 1))
        torch.save(best_defender.policy.state_dict(), path)
        self.champion = best_defender
    
    def get_status(self) -> Dict:
        """获取状态"""
        return {
            "total_episodes": self.total_episodes,
            "n_attackers": self.n_attackers,
            "n_defenders": self.n_defenders,
            "attacker_population": [a.get_status() for a in self.attacker_population],
            "defender_population": [a.get_status() for a in self.defender_population],
            "has_champion": self.champion is not None
        }


cyber_env = CyberBattleEnv()
training_kernel = SelfPlayTrainingKernel(cyber_env)
