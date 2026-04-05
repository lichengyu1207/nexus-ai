"""
协作训练模块
Collaboration Training Module

实现多阶段协作训练，包括顾问模式预训练和联合训练
"""

import os
import json
import time
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
import random
import numpy as np

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.distributions import Categorical
from torch.utils.data import DataLoader, TensorDataset

logger = logging.getLogger(__name__)


@dataclass
class TrainingConfig:
    stage1_epochs: int = 100
    stage2_episodes: int = 10000
    stage3_episodes: int = 1000
    
    batch_size: int = 64
    learning_rate: float = 3e-4
    gamma: float = 0.99
    clip_epsilon: float = 0.2
    entropy_weight: float = 0.01
    value_loss_weight: float = 0.5
    
    collaboration_reward_weight: float = 0.3
    advice_quality_threshold: float = 0.7
    
    save_interval: int = 100
    eval_interval: int = 50
    
    model_dir: str = "models/collaboration"
    log_dir: str = "logs/collaboration"


class Stage1Trainer:
    
    def __init__(
        self,
        attack_agents: List,
        external_attack_data: Optional[List[Tuple]] = None,
        config: Optional[TrainingConfig] = None
    ):
        self.attack_agents = attack_agents
        self.external_attack_data = external_attack_data or []
        self.config = config or TrainingConfig()
        
        os.makedirs(self.config.model_dir, exist_ok=True)
        
        self.training_history: List[Dict] = []
    
    def prepare_supervised_data(self) -> Tuple[torch.Tensor, torch.Tensor]:
        if not self.external_attack_data:
            states = torch.randn(1000, 13)
            optimal_defenses = torch.randint(0, 8, (1000,))
        else:
            states = torch.FloatTensor([d[0] for d in self.external_attack_data])
            optimal_defenses = torch.LongTensor([d[1] for d in self.external_attack_data])
        
        return states, optimal_defenses
    
    def train(self) -> Dict:
        logger.info("Starting Stage 1: Pre-training advise heads...")
        
        states, optimal_defenses = self.prepare_supervised_data()
        
        dataset = TensorDataset(states, optimal_defenses)
        dataloader = DataLoader(dataset, batch_size=self.config.batch_size, shuffle=True)
        
        for agent in self.attack_agents:
            agent.freeze_attack_head()
            
            optimizer = torch.optim.Adam(
                agent.advise_head.parameters(),
                lr=self.config.learning_rate
            )
            
            agent_losses = []
            
            for epoch in range(self.config.stage1_epochs):
                epoch_loss = 0.0
                
                for batch_states, batch_defenses in dataloader:
                    features = agent.feature_extractor(batch_states)
                    advise_probs = agent.advise_head(features)
                    
                    log_probs = torch.log(advise_probs.gather(1, batch_defenses.unsqueeze(1)) + 1e-8)
                    loss = -log_probs.mean()
                    
                    optimizer.zero_grad()
                    loss.backward()
                    optimizer.step()
                    
                    epoch_loss += loss.item()
                
                avg_loss = epoch_loss / len(dataloader)
                agent_losses.append(avg_loss)
                
                if epoch % 10 == 0:
                    logger.info(f"Agent {agent.agent_id} - Epoch {epoch}, Loss: {avg_loss:.4f}")
            
            agent.unfreeze_attack_head()
            
            self.training_history.append({
                "agent_id": agent.agent_id,
                "stage": 1,
                "epochs": self.config.stage1_epochs,
                "final_loss": agent_losses[-1],
                "completed_at": datetime.now().isoformat()
            })
        
        return {
            "stage": 1,
            "status": "completed",
            "n_agents": len(self.attack_agents),
            "epochs": self.config.stage1_epochs
        }


class Stage2Trainer:
    
    def __init__(
        self,
        agent_cluster,
        env,
        config: Optional[TrainingConfig] = None
    ):
        self.agent_cluster = agent_cluster
        self.env = env
        self.config = config or TrainingConfig()
        
        os.makedirs(self.config.model_dir, exist_ok=True)
        
        self.training_history: List[Dict] = []
        self.episode_rewards: List[float] = []
    
    def train(self) -> Dict:
        logger.info("Starting Stage 2: Collaborative training...")
        
        for episode in range(self.config.stage2_episodes):
            states, _ = self.env.reset()
            
            episode_data = {
                "attacker_states": [],
                "defender_states": [],
                "attacker_actions": [],
                "defender_actions": [],
                "rewards": [],
                "advices": []
            }
            
            done = False
            total_reward = 0.0
            
            while not done:
                attacker_state = states[0] if isinstance(states, tuple) else states
                defender_state = states[1] if isinstance(states, tuple) else states
                
                attacker_state_tensor = torch.FloatTensor(attacker_state).unsqueeze(0)
                defender_state_tensor = torch.FloatTensor(defender_state).unsqueeze(0)
                
                advices = self.agent_cluster.get_all_advices(attacker_state_tensor)
                episode_data["advices"].append(advices)
                
                attack_action = random.randint(0, 7)
                attack_intensity = random.uniform(0.3, 1.0)
                
                defense_action, _, _ = self.agent_cluster.defenders[0].act(
                    defender_state_tensor,
                    deterministic=False
                )
                
                states, rewards, done, info = self.env.step(
                    attack_action, attack_intensity, defense_action
                )
                
                episode_data["attacker_states"].append(attacker_state)
                episode_data["defender_states"].append(defender_state)
                episode_data["attacker_actions"].append(attack_action)
                episode_data["defender_actions"].append(defense_action)
                episode_data["rewards"].append(rewards)
                
                total_reward += rewards.get("defender", 0)
            
            self.episode_rewards.append(total_reward)
            
            self._update_agents(episode_data, info)
            
            if episode % self.config.save_interval == 0:
                self._save_models(episode)
            
            if episode % self.config.eval_interval == 0:
                eval_result = self._evaluate()
                logger.info(f"Episode {episode}: Avg Reward = {np.mean(self.episode_rewards[-100:]):.2f}, "
                           f"Block Rate = {eval_result['block_rate']:.2%}")
        
        self._save_models(self.config.stage2_episodes)
        
        return {
            "stage": 2,
            "status": "completed",
            "episodes": self.config.stage2_episodes,
            "avg_reward": np.mean(self.episode_rewards[-100:])
        }
    
    def _update_agents(self, episode_data: Dict, info: Dict):
        if len(episode_data["rewards"]) < 2:
            return
        
        states = np.array(episode_data["defender_states"])
        actions = np.array(episode_data["defender_actions"])
        rewards = [r.get("defender", 0) for r in episode_data["rewards"]]
        
        returns = self._compute_returns(rewards)
        
        for defender in self.agent_cluster.defenders:
            defender.train_step(
                states=states,
                actions=actions,
                rewards=returns,
                next_states=np.roll(states, -1, axis=0),
                dones=np.zeros(len(states))
            )
        
        defense_effect = info.get("defense_effect", {})
        if defense_effect.get("blocked"):
            for advice in episode_data["advices"][-1] if episode_data["advices"] else []:
                agent_id = advice["agent_id"]
                for attacker in self.agent_cluster.attackers:
                    if attacker.agent_id == agent_id:
                        attacker.update_contribution(0.1)
    
    def _compute_returns(self, rewards: List[float]) -> List[float]:
        returns = []
        R = 0
        for r in reversed(rewards):
            R = r + self.config.gamma * R
            returns.insert(0, R)
        returns = np.array(returns)
        if len(returns) > 1:
            returns = (returns - returns.mean()) / (returns.std() + 1e-8)
        return returns.tolist()
    
    def _save_models(self, episode: int):
        save_dir = os.path.join(self.config.model_dir, f"episode_{episode}")
        os.makedirs(save_dir, exist_ok=True)
        
        for i, attacker in enumerate(self.agent_cluster.attackers):
            torch.save(
                attacker.state_dict(),
                os.path.join(save_dir, f"attacker_{i}.pt")
            )
        
        for i, defender in enumerate(self.agent_cluster.defenders):
            torch.save(
                defender.state_dict(),
                os.path.join(save_dir, f"defender_{i}.pt")
            )
    
    def _evaluate(self, n_episodes: int = 10) -> Dict:
        total_blocked = 0
        total_attacks = 0
        
        for _ in range(n_episodes):
            states, _ = self.env.reset()
            done = False
            
            while not done:
                defender_state = states[1] if isinstance(states, tuple) else states
                defender_state_tensor = torch.FloatTensor(defender_state).unsqueeze(0)
                
                defense_action, _, _ = self.agent_cluster.defenders[0].act(
                    defender_state_tensor,
                    deterministic=True
                )
                
                states, rewards, done, info = self.env.step(
                    random.randint(0, 7),
                    random.uniform(0.3, 1.0),
                    defense_action
                )
                
                if info.get("attack_active"):
                    total_attacks += 1
                    if info.get("defense_effect", {}).get("blocked"):
                        total_blocked += 1
        
        return {
            "block_rate": total_blocked / max(total_attacks, 1),
            "total_attacks": total_attacks,
            "blocked_attacks": total_blocked
        }


class Stage3Trainer:
    
    def __init__(
        self,
        agent_cluster,
        war_center,
        config: Optional[TrainingConfig] = None
    ):
        self.agent_cluster = agent_cluster
        self.war_center = war_center
        self.config = config or TrainingConfig()
        
        self.online_history: List[Dict] = []
    
    async def train_online(self, real_attack_data: Dict) -> Dict:
        state = real_attack_data.get("state")
        defense_result = real_attack_data.get("result")
        feedback = real_attack_data.get("feedback", {})
        
        if state is not None:
            state_tensor = torch.FloatTensor(state).unsqueeze(0)
            
            advices = self.agent_cluster.get_all_advices(state_tensor)
            
            self.war_center.advice_fuser.update_weights(feedback)
            
            for agent_id, score in feedback.items():
                for attacker in self.agent_cluster.attackers:
                    if attacker.agent_id == agent_id:
                        attacker.update_contribution(score)
        
        self.online_history.append({
            "timestamp": datetime.now().isoformat(),
            "feedback": feedback,
            "result": defense_result
        })
        
        return {"status": "updated", "feedback_processed": len(feedback)}
    
    def fine_tune(self, recent_data: List[Dict]) -> Dict:
        if not recent_data:
            return {"status": "no_data"}
        
        states = []
        optimal_actions = []
        weights = []
        
        for data in recent_data:
            if data.get("result", {}).get("success"):
                states.append(data["state"])
                optimal_actions.append(data["defense_action"])
                weights.append(1.0)
        
        if not states:
            return {"status": "no_successful_data"}
        
        states = torch.FloatTensor(np.array(states))
        optimal_actions = torch.LongTensor(optimal_actions)
        weights = torch.FloatTensor(weights)
        
        for agent in self.agent_cluster.attackers:
            features = agent.feature_extractor(states)
            advise_probs = agent.advise_head(features)
            
            log_probs = torch.log(advise_probs.gather(1, optimal_actions.unsqueeze(1)) + 1e-8)
            loss = -(log_probs.squeeze() * weights).mean()
            
            agent.optimizer.zero_grad()
            loss.backward()
            agent.optimizer.step()
        
        return {
            "status": "fine_tuned",
            "n_samples": len(states)
        }


class CollaborationTrainingPipeline:
    
    def __init__(
        self,
        agent_cluster,
        env,
        war_center,
        config: Optional[TrainingConfig] = None
    ):
        self.agent_cluster = agent_cluster
        self.env = env
        self.war_center = war_center
        self.config = config or TrainingConfig()
        
        self.stage1_trainer = Stage1Trainer(
            agent_cluster.attackers,
            config=config
        )
        
        self.stage2_trainer = Stage2Trainer(
            agent_cluster,
            env,
            config=config
        )
        
        self.stage3_trainer = Stage3Trainer(
            agent_cluster,
            war_center,
            config=config
        )
        
        self.training_log: List[Dict] = []
    
    def run_full_training(self) -> Dict:
        logger.info("Starting full collaboration training pipeline...")
        
        results = {}
        
        logger.info("=== Stage 1: Pre-training advise heads ===")
        stage1_result = self.stage1_trainer.train()
        results["stage1"] = stage1_result
        self.training_log.append({
            "stage": 1,
            "result": stage1_result,
            "timestamp": datetime.now().isoformat()
        })
        
        logger.info("=== Stage 2: Collaborative training ===")
        stage2_result = self.stage2_trainer.train()
        results["stage2"] = stage2_result
        self.training_log.append({
            "stage": 2,
            "result": stage2_result,
            "timestamp": datetime.now().isoformat()
        })
        
        results["status"] = "completed"
        results["completed_at"] = datetime.now().isoformat()
        
        logger.info("Training pipeline completed!")
        
        return results
    
    async def online_update(self, attack_data: Dict) -> Dict:
        return await self.stage3_trainer.train_online(attack_data)
    
    def get_training_status(self) -> Dict:
        return {
            "config": {
                "stage1_epochs": self.config.stage1_epochs,
                "stage2_episodes": self.config.stage2_episodes,
                "stage3_episodes": self.config.stage3_episodes
            },
            "training_log_count": len(self.training_log),
            "agent_cluster_status": self.agent_cluster.get_cluster_status()
        }
