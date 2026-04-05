"""
双模式智能体模块
Dual-Mode Agent Module

实现攻击智能体的双模式（攻击/顾问）和防御智能体的战时增强
"""

import os
import json
import time
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import random

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.distributions import Categorical

logger = logging.getLogger(__name__)


class AgentMode(Enum):
    ATTACK = "attack"
    ADVISE = "advise"
    DEFENSE = "defense"
    WAR_DEFENSE = "war_defense"


@dataclass
class AgentConfig:
    state_dim: int = 13
    action_dim: int = 8
    advise_dim: int = 8
    hidden_dim: int = 256
    learning_rate: float = 3e-4
    gamma: float = 0.99
    epsilon: float = 0.2
    entropy_weight: float = 0.01
    device: str = "cpu"


class SharedFeatureExtractor(nn.Module):
    
    def __init__(self, state_dim: int, hidden_dim: int = 256):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.LayerNorm(hidden_dim // 2),
            nn.ReLU()
        )
    
    def forward(self, state: torch.Tensor) -> torch.Tensor:
        return self.net(state)


class AttackHead(nn.Module):
    
    def __init__(self, hidden_dim: int, action_dim: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(hidden_dim // 2, hidden_dim // 4),
            nn.ReLU(),
            nn.Linear(hidden_dim // 4, action_dim)
        )
    
    def forward(self, features: torch.Tensor) -> torch.Tensor:
        return self.net(features)


class AdviseHead(nn.Module):
    
    def __init__(self, hidden_dim: int, advise_dim: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(hidden_dim // 2, hidden_dim // 4),
            nn.ReLU(),
            nn.Linear(hidden_dim // 4, advise_dim),
            nn.Softmax(dim=-1)
        )
    
    def forward(self, features: torch.Tensor) -> torch.Tensor:
        return self.net(features)


class ValueHead(nn.Module):
    
    def __init__(self, hidden_dim: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(hidden_dim // 2, hidden_dim // 4),
            nn.ReLU(),
            nn.Linear(hidden_dim // 4, 1)
        )
    
    def forward(self, features: torch.Tensor) -> torch.Tensor:
        return self.net(features)


class DualModeAttackAgent(nn.Module):
    
    def __init__(self, config: Optional[AgentConfig] = None):
        super().__init__()
        self.config = config or AgentConfig()
        
        self.feature_extractor = SharedFeatureExtractor(
            self.config.state_dim,
            self.config.hidden_dim
        )
        
        self.attack_head = AttackHead(
            self.config.hidden_dim,
            self.config.action_dim
        )
        
        self.advise_head = AdviseHead(
            self.config.hidden_dim,
            self.config.advise_dim
        )
        
        self.value_head = ValueHead(self.config.hidden_dim)
        
        self.mode = AgentMode.ATTACK
        self.agent_id = f"attacker_{id(self)}"
        
        self.optimizer = torch.optim.Adam(
            self.parameters(),
            lr=self.config.learning_rate
        )
        
        self.stats = {
            "total_games": 0,
            "wins": 0,
            "advise_given": 0,
            "advise_accepted": 0,
            "contribution_score": 1.0
        }
    
    def set_mode(self, mode: AgentMode):
        self.mode = mode
        logger.info(f"Agent {self.agent_id} switched to {mode.value} mode")
    
    def forward(self, state: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        features = self.feature_extractor(state)
        
        attack_logits = self.attack_head(features)
        advise_probs = self.advise_head(features)
        value = self.value_head(features)
        
        return attack_logits, advise_probs, value
    
    def act(self, state: torch.Tensor, deterministic: bool = False) -> Tuple[int, torch.Tensor, torch.Tensor]:
        with torch.no_grad():
            attack_logits, advise_probs, value = self.forward(state)
            
            if self.mode == AgentMode.ATTACK:
                if deterministic:
                    action = torch.argmax(attack_logits, dim=-1)
                else:
                    dist = Categorical(logits=attack_logits)
                    action = dist.sample()
                return action.item(), attack_logits, value
            
            elif self.mode == AgentMode.ADVISE:
                if deterministic:
                    advise = torch.argmax(advise_probs, dim=-1)
                else:
                    dist = Categorical(probs=advise_probs)
                    advise = dist.sample()
                self.stats["advise_given"] += 1
                return advise.item(), advise_probs, value
        
        return 0, attack_logits, value
    
    def get_advise(self, state: torch.Tensor) -> Dict:
        with torch.no_grad():
            _, advise_probs, value = self.forward(state)
            
            top_advices = torch.topk(advise_probs, min(3, advise_probs.size(-1)))
            
            return {
                "agent_id": self.agent_id,
                "advise_probs": advise_probs.cpu().numpy().tolist(),
                "top_advices": [
                    {
                        "action": int(top_advices.indices[0][i].item()),
                        "confidence": float(top_advices.values[0][i].item())
                    }
                    for i in range(len(top_advices.indices[0]))
                ],
                "value_estimate": float(value.item()),
                "contribution_score": self.stats["contribution_score"],
                "timestamp": datetime.now().isoformat()
            }
    
    def update_contribution(self, feedback: float):
        alpha = 0.1
        self.stats["contribution_score"] = (
            (1 - alpha) * self.stats["contribution_score"] +
            alpha * feedback
        )
        self.stats["contribution_score"] = max(0.1, min(2.0, self.stats["contribution_score"]))
    
    def train_attack(self, states, actions, rewards, next_states, dones):
        states = torch.FloatTensor(states)
        actions = torch.LongTensor(actions)
        rewards = torch.FloatTensor(rewards)
        next_states = torch.FloatTensor(next_states)
        dones = torch.FloatTensor(dones)
        
        attack_logits, _, values = self.forward(states)
        
        with torch.no_grad():
            _, _, next_values = self.forward(next_states)
            targets = rewards + self.config.gamma * next_values.squeeze() * (1 - dones)
            advantages = targets - values.squeeze()
        
        dist = Categorical(logits=attack_logits)
        log_probs = dist.log_prob(actions)
        
        policy_loss = -(log_probs * advantages.detach()).mean()
        value_loss = F.mse_loss(values.squeeze(), targets.detach())
        entropy_loss = -dist.entropy().mean() * self.config.entropy_weight
        
        loss = policy_loss + 0.5 * value_loss + entropy_loss
        
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.parameters(), 0.5)
        self.optimizer.step()
        
        return {
            "policy_loss": policy_loss.item(),
            "value_loss": value_loss.item(),
            "entropy": -entropy_loss.item()
        }
    
    def train_advise(self, states, optimal_defenses, weights=None):
        states = torch.FloatTensor(states)
        optimal_defenses = torch.LongTensor(optimal_defenses)
        
        if weights is not None:
            weights = torch.FloatTensor(weights)
        
        _, advise_probs, _ = self.forward(states)
        
        log_probs = torch.log(advise_probs.gather(1, optimal_defenses.unsqueeze(1)) + 1e-8)
        
        if weights is not None:
            loss = -(log_probs.squeeze() * weights).mean()
        else:
            loss = -log_probs.mean()
        
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        
        return {"advise_loss": loss.item()}
    
    def freeze_attack_head(self):
        for param in self.attack_head.parameters():
            param.requires_grad = False
    
    def unfreeze_attack_head(self):
        for param in self.attack_head.parameters():
            param.requires_grad = True
    
    def get_status(self) -> Dict:
        return {
            "agent_id": self.agent_id,
            "mode": self.mode.value,
            "total_games": self.stats["total_games"],
            "wins": self.stats["wins"],
            "win_rate": self.stats["wins"] / max(self.stats["total_games"], 1),
            "advise_given": self.stats["advise_given"],
            "advise_accepted": self.stats["advise_accepted"],
            "contribution_score": self.stats["contribution_score"]
        }


class WarDefenseAgent(nn.Module):
    
    def __init__(self, config: Optional[AgentConfig] = None):
        super().__init__()
        self.config = config or AgentConfig()
        
        self.feature_extractor = SharedFeatureExtractor(
            self.config.state_dim,
            self.config.hidden_dim
        )
        
        self.policy_head = nn.Sequential(
            nn.Linear(self.config.hidden_dim // 2, self.config.hidden_dim // 4),
            nn.ReLU(),
            nn.Linear(self.config.hidden_dim // 4, self.config.action_dim)
        )
        
        self.value_head = ValueHead(self.config.hidden_dim)
        
        self.advice_integrator = nn.Sequential(
            nn.Linear(self.config.hidden_dim // 2 + self.config.advise_dim, self.config.hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(self.config.hidden_dim // 2, self.config.hidden_dim // 4),
            nn.ReLU()
        )
        
        self.war_policy_head = nn.Sequential(
            nn.Linear(self.config.hidden_dim // 4, self.config.action_dim)
        )
        
        self.mode = AgentMode.DEFENSE
        self.agent_id = f"defender_{id(self)}"
        
        self.optimizer = torch.optim.Adam(
            self.parameters(),
            lr=self.config.learning_rate
        )
        
        self.cached_advice: Optional[torch.Tensor] = None
        self.advice_source: Optional[str] = None
        
        self.stats = {
            "total_games": 0,
            "wins": 0,
            "blocked_attacks": 0,
            "missed_attacks": 0,
            "war_mode_activations": 0
        }
    
    def set_mode(self, mode: AgentMode):
        if mode == AgentMode.WAR_DEFENSE and self.mode != AgentMode.WAR_DEFENSE:
            self.stats["war_mode_activations"] += 1
        self.mode = mode
        logger.info(f"Defense Agent {self.agent_id} switched to {mode.value} mode")
    
    def forward(
        self,
        state: torch.Tensor,
        advice: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        features = self.feature_extractor(state)
        
        if self.mode == AgentMode.WAR_DEFENSE and advice is not None:
            integrated = self.advice_integrator(
                torch.cat([features, advice], dim=-1)
            )
            policy_logits = self.war_policy_head(integrated)
        else:
            policy_logits = self.policy_head(features)
        
        value = self.value_head(features)
        
        return policy_logits, value
    
    def act(
        self,
        state: torch.Tensor,
        advice: Optional[torch.Tensor] = None,
        deterministic: bool = False
    ) -> Tuple[int, torch.Tensor, torch.Tensor]:
        with torch.no_grad():
            policy_logits, value = self.forward(state, advice)
            
            if deterministic:
                action = torch.argmax(policy_logits, dim=-1)
            else:
                dist = Categorical(logits=policy_logits)
                action = dist.sample()
            
            return action.item(), policy_logits, value
    
    def set_cached_advice(self, advice: torch.Tensor, source: str):
        self.cached_advice = advice
        self.advice_source = source
    
    def clear_cached_advice(self):
        self.cached_advice = None
        self.advice_source = None
    
    def train_step(
        self,
        states,
        actions,
        rewards,
        next_states,
        dones,
        advices=None
    ):
        states = torch.FloatTensor(states)
        actions = torch.LongTensor(actions)
        rewards = torch.FloatTensor(rewards)
        next_states = torch.FloatTensor(next_states)
        dones = torch.FloatTensor(dones)
        
        if advices is not None:
            advices = torch.FloatTensor(advices)
        
        policy_logits, values = self.forward(states, advices)
        
        with torch.no_grad():
            _, next_values = self.forward(next_states, advices)
            targets = rewards + self.config.gamma * next_values.squeeze() * (1 - dones)
            advantages = targets - values.squeeze()
        
        dist = Categorical(logits=policy_logits)
        log_probs = dist.log_prob(actions)
        
        policy_loss = -(log_probs * advantages.detach()).mean()
        value_loss = F.mse_loss(values.squeeze(), targets.detach())
        entropy_loss = -dist.entropy().mean() * self.config.entropy_weight
        
        loss = policy_loss + 0.5 * value_loss + entropy_loss
        
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.parameters(), 0.5)
        self.optimizer.step()
        
        return {
            "policy_loss": policy_loss.item(),
            "value_loss": value_loss.item(),
            "entropy": -entropy_loss.item()
        }
    
    def get_status(self) -> Dict:
        return {
            "agent_id": self.agent_id,
            "mode": self.mode.value,
            "total_games": self.stats["total_games"],
            "wins": self.stats["wins"],
            "win_rate": self.stats["wins"] / max(self.stats["total_games"], 1),
            "blocked_attacks": self.stats["blocked_attacks"],
            "missed_attacks": self.stats["missed_attacks"],
            "war_mode_activations": self.stats["war_mode_activations"],
            "has_cached_advice": self.cached_advice is not None
        }


class AgentCluster:
    
    def __init__(
        self,
        n_attackers: int = 8,
        n_defenders: int = 8,
        config: Optional[AgentConfig] = None
    ):
        self.config = config or AgentConfig()
        
        self.attackers = [
            DualModeAttackAgent(self.config)
            for _ in range(n_attackers)
        ]
        
        self.defenders = [
            WarDefenseAgent(self.config)
            for _ in range(n_defenders)
        ]
        
        self.mode = AgentMode.ATTACK
    
    def set_wartime_mode(self):
        self.mode = AgentMode.ADVISE
        for attacker in self.attackers:
            attacker.set_mode(AgentMode.ADVISE)
        for defender in self.defenders:
            defender.set_mode(AgentMode.WAR_DEFENSE)
    
    def set_peacetime_mode(self):
        self.mode = AgentMode.ATTACK
        for attacker in self.attackers:
            attacker.set_mode(AgentMode.ATTACK)
        for defender in self.defenders:
            defender.set_mode(AgentMode.DEFENSE)
    
    def get_all_advices(self, state: torch.Tensor) -> List[Dict]:
        return [attacker.get_advise(state) for attacker in self.attackers]
    
    def get_cluster_status(self) -> Dict:
        return {
            "mode": self.mode.value,
            "n_attackers": len(self.attackers),
            "n_defenders": len(self.defenders),
            "attackers": [a.get_status() for a in self.attackers],
            "defenders": [d.get_status() for d in self.defenders]
        }
