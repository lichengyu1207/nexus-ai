"""
对抗鲁棒训练模块
Adversarial Robust Training Module

实现分布鲁棒优化(DRO)和对抗样本生成
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import random


@dataclass
class AdversarialConfig:
    epsilon: float = 0.1
    pgd_steps: int = 5
    pgd_alpha: float = 0.02
    wasserstein_radius: float = 0.1
    dro_beta: float = 1.0
    entropy_weight: float = 0.01


class AdversarialGenerator:
    
    def __init__(
        self,
        defense_agent,
        config: Optional[AdversarialConfig] = None
    ):
        self.defense_agent = defense_agent
        self.config = config or AdversarialConfig()
    
    def generate_fgsm_perturbation(
        self,
        state: torch.Tensor,
        target_action: Optional[int] = None
    ) -> torch.Tensor:
        state_tensor = state.clone().detach().requires_grad_(True)
        
        with torch.enable_grad():
            if hasattr(self.defense_agent, 'policy'):
                action_logits, value = self.defense_agent.policy.get_action(state_tensor)
            else:
                action_logits, value = self.defense_agent.policy(state_tensor)
            
            if target_action is not None:
                loss = -F.cross_entropy(action_logits, torch.tensor([target_action]))
            else:
                predicted = torch.argmax(action_logits, dim=-1)
                loss = -F.cross_entropy(action_logits, predicted)
        
        loss.backward()
        
        perturbation = self.config.epsilon * state_tensor.grad.sign()
        
        return perturbation.detach()
    
    def generate_pgd_perturbation(
        self,
        state: torch.Tensor,
        target_action: Optional[int] = None,
        random_start: bool = True
    ) -> torch.Tensor:
        if random_start:
            adv_state = state + torch.empty_like(state).uniform_(-self.config.epsilon, self.config.epsilon)
        else:
            adv_state = state.clone()
        
        adv_state = adv_state.detach().requires_grad_(True)
        
        for _ in range(self.config.pgd_steps):
            adv_state.requires_grad_(True)
            
            with torch.enable_grad():
                if hasattr(self.defense_agent, 'policy'):
                    action_logits, value = self.defense_agent.policy.get_action(adv_state)
                else:
                    action_logits, value = self.defense_agent.policy(adv_state)
                
                if target_action is not None:
                    loss = -F.cross_entropy(action_logits, torch.tensor([target_action]))
                else:
                    predicted = torch.argmax(action_logits, dim=-1)
                    loss = -F.cross_entropy(action_logits, predicted)
            
            loss.backward()
            
            grad = adv_state.grad.data
            adv_state = adv_state.detach() + self.config.pgd_alpha * grad.sign()
            
            perturbation = torch.clamp(adv_state - state, -self.config.epsilon, self.config.epsilon)
            adv_state = torch.clamp(state + perturbation, 0.0, 1.0)
        
        return (adv_state - state).detach()
    
    def generate_random_perturbation(self, state: torch.Tensor) -> torch.Tensor:
        perturbation = torch.randn_like(state) * self.config.epsilon * 0.5
        return torch.clamp(perturbation, -self.config.epsilon, self.config.epsilon)
    
    def generate_adversarial_attack(
        self,
        base_attack: np.ndarray,
        diversity_factor: float = 0.1
    ) -> np.ndarray:
        perturbation = np.random.normal(0, diversity_factor, size=len(base_attack))
        adv_attack = base_attack + perturbation
        return np.clip(adv_attack, 0, 1)
    
    def generate_diverse_attacks(
        self,
        base_state: torch.Tensor,
        n_samples: int = 10
    ) -> List[torch.Tensor]:
        adversarial_states = []
        
        fgsm_state = base_state + self.generate_fgsm_perturbation(base_state)
        adversarial_states.append(torch.clamp(fgsm_state, 0, 1))
        
        pgd_state = base_state + self.generate_pgd_perturbation(base_state)
        adversarial_states.append(torch.clamp(pgd_state, 0, 1))
        
        for _ in range(n_samples - 2):
            random_state = base_state + self.generate_random_perturbation(base_state)
            adversarial_states.append(torch.clamp(random_state, 0, 1))
        
        return adversarial_states


class PrioritizedReplayBuffer:
    
    def __init__(
        self,
        capacity: int = 100000,
        alpha: float = 0.6,
        beta: float = 0.4,
        beta_increment: float = 0.001,
        epsilon: float = 1e-6
    ):
        self.capacity = capacity
        self.alpha = alpha
        self.beta = beta
        self.beta_increment = beta_increment
        self.epsilon = epsilon
        
        self.buffer: List[Dict] = []
        self.priorities: List[float] = []
        self.max_priority = 1.0
    
    def store(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        next_state: np.ndarray,
        done: bool,
        info: Optional[Dict] = None
    ):
        experience = {
            "state": state,
            "action": action,
            "reward": reward,
            "next_state": next_state,
            "done": done,
            "info": info or {}
        }
        
        if len(self.buffer) >= self.capacity:
            self.buffer.pop(0)
            self.priorities.pop(0)
        
        self.buffer.append(experience)
        self.priorities.append(self.max_priority)
    
    def sample(self, batch_size: int) -> Tuple[Dict, np.ndarray, np.ndarray]:
        if len(self.buffer) < batch_size:
            batch_size = len(self.buffer)
        
        priorities = np.array(self.priorities)
        probabilities = priorities ** self.alpha
        probabilities /= probabilities.sum()
        
        indices = np.random.choice(len(self.buffer), batch_size, replace=False, p=probabilities)
        
        weights = (len(self.buffer) * probabilities[indices]) ** (-self.beta)
        weights /= weights.max()
        
        self.beta = min(1.0, self.beta + self.beta_increment)
        
        experiences = [self.buffer[i] for i in indices]
        
        batch = {
            "states": np.array([e["state"] for e in experiences]),
            "actions": np.array([e["action"] for e in experiences]),
            "rewards": np.array([e["reward"] for e in experiences]),
            "next_states": np.array([e["next_state"] for e in experiences]),
            "dones": np.array([e["done"] for e in experiences])
        }
        
        return batch, indices, weights
    
    def update_priorities(self, indices: np.ndarray, td_errors: np.ndarray):
        for idx, td_error in zip(indices, td_errors):
            priority = (abs(td_error) + self.epsilon) ** self.alpha
            self.priorities[idx] = priority
            self.max_priority = max(self.max_priority, priority)
    
    def __len__(self) -> int:
        return len(self.buffer)
    
    def clear(self):
        self.buffer.clear()
        self.priorities.clear()
        self.max_priority = 1.0


class MultiAgentReplayBuffer:
    
    def __init__(
        self,
        n_agents: int,
        capacity: int = 100000,
        alpha: float = 0.6,
        beta: float = 0.4
    ):
        self.n_agents = n_agents
        self.capacity = capacity
        self.alpha = alpha
        self.beta = beta
        
        self.buffers = [
            PrioritizedReplayBuffer(capacity, alpha, beta)
            for _ in range(n_agents)
        ]
    
    def store(
        self,
        states: List[np.ndarray],
        actions: List[int],
        rewards: List[float],
        next_states: List[np.ndarray],
        dones: List[bool]
    ):
        for i, buffer in enumerate(self.buffers):
            buffer.store(states[i], actions[i], rewards[i], next_states[i], dones[i])
    
    def sample(self, batch_size: int) -> List[Tuple[Dict, np.ndarray, np.ndarray]]:
        return [buffer.sample(batch_size) for buffer in self.buffers]
    
    def update_priorities(self, agent_idx: int, indices: np.ndarray, td_errors: np.ndarray):
        self.buffers[agent_idx].update_priorities(indices, td_errors)
    
    def __len__(self) -> int:
        return min(len(buffer) for buffer in self.buffers)


class RobustTrainer:
    
    def __init__(
        self,
        defense_agent,
        attack_agent,
        config: Optional[AdversarialConfig] = None,
        device: str = "cpu"
    ):
        self.defense_agent = defense_agent
        self.attack_agent = attack_agent
        self.config = config or AdversarialConfig()
        self.device = device
        
        self.adv_generator = AdversarialGenerator(defense_agent, config)
        self.replay_buffer = PrioritizedReplayBuffer()
        
        self.robustness_history: List[Dict] = []
        self.total_steps = 0
    
    def compute_robust_loss(
        self,
        states: torch.Tensor,
        actions: torch.Tensor,
        returns: torch.Tensor,
        advantages: torch.Tensor
    ) -> Tuple[torch.Tensor, Dict]:
        batch_size = states.size(0)
        
        n_adv_samples = 3
        total_policy_loss = 0.0
        total_value_loss = 0.0
        
        for _ in range(n_adv_samples):
            adv_states = states + self.adv_generator.generate_random_perturbation(states)
            adv_states = torch.clamp(adv_states, 0, 1)
            
            if hasattr(self.defense_agent, 'policy'):
                action_logits, values, _, _, _ = self.defense_agent.policy(adv_states)
            else:
                action_logits, values = self.defense_agent.policy(adv_states)
            
            dist = torch.distributions.Categorical(logits=action_logits)
            log_probs = dist.log_prob(actions)
            
            policy_loss = -(log_probs * advantages).mean()
            value_loss = F.mse_loss(values.squeeze(), returns)
            
            total_policy_loss += policy_loss.item()
            total_value_loss += value_loss.item()
        
        robust_policy_loss = total_policy_loss / n_adv_samples
        robust_value_loss = total_value_loss / n_adv_samples
        
        loss = torch.tensor(robust_policy_loss + 0.5 * robust_value_loss, requires_grad=True)
        
        metrics = {
            "robust_policy_loss": robust_policy_loss,
            "robust_value_loss": robust_value_loss,
            "n_adv_samples": n_adv_samples
        }
        
        return loss, metrics
    
    def train_step(
        self,
        env,
        n_episodes: int = 10,
        adv_ratio: float = 0.3
    ) -> Dict:
        total_reward = 0.0
        total_adv_reward = 0.0
        n_adv_episodes = int(n_episodes * adv_ratio)
        n_normal_episodes = n_episodes - n_adv_episodes
        
        for _ in range(n_normal_episodes):
            states, _ = env.reset()
            defender_state = states["defender"]
            
            episode_reward = 0.0
            done = False
            
            while not done:
                action, log_prob, value = self.defense_agent.select_action(defender_state)
                
                states, rewards, done, info = env.step(0, 0.0, action)
                
                self.replay_buffer.store(
                    defender_state, action, rewards["defender"],
                    states["defender"], done
                )
                
                episode_reward += rewards["defender"]
                defender_state = states["defender"]
            
            total_reward += episode_reward
        
        for _ in range(n_adv_episodes):
            states, _ = env.reset()
            defender_state = states["defender"]
            
            state_tensor = torch.FloatTensor(defender_state).unsqueeze(0).to(self.device)
            perturbation = self.adv_generator.generate_pgd_perturbation(state_tensor)
            adv_state = (state_tensor + perturbation).squeeze(0).cpu().numpy()
            
            episode_reward = 0.0
            done = False
            
            while not done:
                action, log_prob, value = self.defense_agent.select_action(adv_state)
                
                states, rewards, done, info = env.step(0, 0.0, action)
                
                self.replay_buffer.store(
                    adv_state, action, rewards["defender"],
                    states["defender"], done
                )
                
                episode_reward += rewards["defender"]
                adv_state = states["defender"]
            
            total_adv_reward += episode_reward
        
        self.total_steps += n_episodes
        
        metrics = {
            "total_steps": self.total_steps,
            "avg_reward": total_reward / max(n_normal_episodes, 1),
            "avg_adv_reward": total_adv_reward / max(n_adv_episodes, 1),
            "buffer_size": len(self.replay_buffer)
        }
        
        self.robustness_history.append(metrics)
        
        return metrics
    
    def evaluate_robustness(
        self,
        env,
        n_episodes: int = 10,
        epsilon_range: List[float] = [0.0, 0.05, 0.1, 0.2]
    ) -> Dict:
        results = {}
        
        for epsilon in epsilon_range:
            total_reward = 0.0
            total_tpr = 0.0
            total_fpr = 0.0
            
            for _ in range(n_episodes):
                states, _ = env.reset()
                defender_state = states["defender"]
                
                if epsilon > 0:
                    state_tensor = torch.FloatTensor(defender_state).unsqueeze(0).to(self.device)
                    perturbation = torch.randn_like(state_tensor) * epsilon
                    defender_state = torch.clamp(state_tensor + perturbation, 0, 1).squeeze(0).cpu().numpy()
                
                episode_reward = 0.0
                done = False
                true_positives = 0
                false_positives = 0
                total_attacks = 0
                
                while not done:
                    action, _, _ = self.defense_agent.select_action(defender_state, deterministic=True)
                    
                    attack_action = random.randint(0, 7)
                    attack_intensity = random.random()
                    
                    states, rewards, done, info = env.step(attack_action, attack_intensity, action)
                    
                    episode_reward += rewards["defender"]
                    defender_state = states["defender"]
                    
                    if attack_action > 0:
                        total_attacks += 1
                        if info.get("defense_effect", {}).get("blocked"):
                            true_positives += 1
                    
                    if info.get("defense_effect", {}).get("false_positive"):
                        false_positives += 1
                
                total_reward += episode_reward
                if total_attacks > 0:
                    total_tpr += true_positives / total_attacks
                total_fpr += false_positives / max(1, len(env.get_history()))
            
            results[f"epsilon_{epsilon}"] = {
                "avg_reward": total_reward / n_episodes,
                "avg_tpr": total_tpr / n_episodes,
                "avg_fpr": total_fpr / n_episodes
            }
        
        return results
    
    def get_robustness_metrics(self) -> Dict:
        if not self.robustness_history:
            return {}
        
        recent = self.robustness_history[-10:]
        
        return {
            "avg_reward": np.mean([h["avg_reward"] for h in recent]),
            "avg_adv_reward": np.mean([h["avg_adv_reward"] for h in recent]),
            "total_steps": self.total_steps,
            "buffer_size": len(self.replay_buffer)
        }


class WassersteinRobustOptimizer:
    
    def __init__(
        self,
        agent,
        radius: float = 0.1,
        beta: float = 1.0,
        n_samples: int = 10
    ):
        self.agent = agent
        self.radius = radius
        self.beta = beta
        self.n_samples = n_samples
    
    def sample_worst_case_distribution(
        self,
        states: torch.Tensor
    ) -> torch.Tensor:
        batch_size = states.size(0)
        
        worst_case_states = []
        
        for i in range(batch_size):
            state = states[i:i+1]
            
            min_value = float('inf')
            worst_state = state
            
            for _ in range(self.n_samples):
                perturbation = torch.randn_like(state) * self.radius
                perturbed_state = torch.clamp(state + perturbation, 0, 1)
                
                with torch.no_grad():
                    if hasattr(self.agent, 'policy'):
                        _, value = self.agent.policy.get_action(perturbed_state)
                    else:
                        _, value = self.agent.policy(perturbed_state)
                
                if value.item() < min_value:
                    min_value = value.item()
                    worst_state = perturbed_state
            
            worst_case_states.append(worst_state)
        
        return torch.cat(worst_case_states, dim=0)
    
    def compute_robust_value(
        self,
        states: torch.Tensor
    ) -> torch.Tensor:
        worst_case_states = self.sample_worst_case_distribution(states)
        
        if hasattr(self.agent, 'policy'):
            _, values = self.agent.policy.get_action(worst_case_states)
        else:
            _, values = self.agent.policy(worst_case_states)
        
        return values
