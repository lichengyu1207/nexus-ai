"""
持续训练脚本
Continuous Training Script

实现智能体的持续训练、自动更新和进化循环
"""

import os
import sys
import json
import time
import logging
import argparse
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
import random

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.evolution import (
    MetaCognitionModule,
    EvolutionEngine,
    MemoryAgentCluster,
    meta_bus,
    memory_cluster,
    SuggestionStatus
)

logger = logging.getLogger(__name__)


@dataclass
class TrainingConfig:
    batch_size: int = 64
    learning_rate: float = 1e-4
    epochs_per_session: int = 10
    min_samples: int = 1000
    validation_split: float = 0.2
    early_stopping_patience: int = 5
    model_save_path: str = "models/versions"
    checkpoint_interval: int = 1000
    max_training_time_hours: float = 4.0
    target_reward_threshold: float = 0.8
    data_refresh_interval: int = 3600


class TrainingDataset(Dataset):
    
    def __init__(self, data: List[Dict]):
        self.data = data
        self.states = []
        self.actions = []
        self.rewards = []
        
        for item in data:
            if "state" in item and "action" in item:
                self.states.append(np.array(item["state"], dtype=np.float32))
                self.actions.append(item["action"])
                if "reward" in item:
                    self.rewards.append(item["reward"])
        
        self.states = np.array(self.states) if self.states else np.zeros((1, 13))
        self.actions = np.array(self.actions) if self.actions else np.zeros(1, dtype=np.int64)
        self.rewards = np.array(self.rewards) if self.rewards else np.zeros(1)
    
    def __len__(self):
        return len(self.states)
    
    def __getitem__(self, idx):
        return {
            "state": torch.FloatTensor(self.states[idx]),
            "action": torch.LongTensor([self.actions[idx]]),
            "reward": torch.FloatTensor([self.rewards[idx]])
        }


class PolicyNetwork(nn.Module):
    
    def __init__(self, state_dim: int = 13, action_dim: int = 8, hidden_dim: int = 128):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, action_dim)
        )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)
    
    def get_action(self, state: np.ndarray) -> int:
        with torch.no_grad():
            state_tensor = torch.FloatTensor(state).unsqueeze(0)
            logits = self.forward(state_tensor)
            probs = torch.softmax(logits, dim=-1)
            action = torch.argmax(probs, dim=-1).item()
        return action


class ContinuousTrainer:
    
    def __init__(
        self,
        agent_id: str,
        agent_type: str,
        config: TrainingConfig,
        meta_cognition: Optional[MetaCognitionModule] = None
    ):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.config = config
        self.meta_cognition = meta_cognition
        
        self.policy = PolicyNetwork()
        self.optimizer = optim.Adam(self.policy.parameters(), lr=config.learning_rate)
        
        self.training_data: List[Dict] = []
        self.validation_data: List[Dict] = []
        
        self.training_history: List[Dict] = []
        self.best_loss = float('inf')
        self.patience_counter = 0
        
        self.is_training = False
        self.current_epoch = 0
        self.total_steps = 0
        
        self.model_version = f"v1.0.0"
        
        os.makedirs(config.model_save_path, exist_ok=True)
    
    def load_training_data(self, data_source: str = "database") -> int:
        if data_source == "database":
            data = self._load_from_database()
        elif data_source == "file":
            data = self._load_from_file()
        elif data_source == "memory":
            data = self._load_from_memory()
        else:
            data = []
        
        if len(data) < self.config.min_samples:
            logger.warning(f"Insufficient training data: {len(data)} < {self.config.min_samples}")
            return 0
        
        split_idx = int(len(data) * (1 - self.config.validation_split))
        self.training_data = data[:split_idx]
        self.validation_data = data[split_idx:]
        
        logger.info(f"Loaded {len(self.training_data)} training and {len(self.validation_data)} validation samples")
        
        return len(self.training_data)
    
    def _load_from_database(self) -> List[Dict]:
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor
            
            conn = psycopg2.connect(
                host=os.getenv("DB_HOST", "localhost"),
                port=int(os.getenv("DB_PORT", 5432)),
                database=os.getenv("DB_NAME", "fangdudu"),
                user=os.getenv("DB_USER", "postgres"),
                password=os.getenv("DB_PASSWORD", "postgres")
            )
            
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT state, action, reward, next_state, metadata
                    FROM agent_trajectories
                    WHERE agent_type = %s
                    AND created_at > NOW() - INTERVAL '7 days'
                    ORDER BY created_at DESC
                    LIMIT 100000
                """, (self.agent_type,))
                
                rows = cur.fetchall()
                data = [dict(row) for row in rows]
            
            conn.close()
            return data
            
        except Exception as e:
            logger.error(f"Failed to load data from database: {e}")
            return []
    
    def _load_from_file(self) -> List[Dict]:
        data_file = os.path.join(self.config.model_save_path, f"{self.agent_type}_data.json")
        
        if not os.path.exists(data_file):
            return []
        
        try:
            with open(data_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load data from file: {e}")
            return []
    
    def _load_from_memory(self) -> List[Dict]:
        if self.meta_cognition and hasattr(self.meta_cognition, 'trajectory_buffer'):
            return [
                {
                    "state": r.state.tolist() if isinstance(r.state, np.ndarray) else r.state,
                    "action": r.action,
                    "reward": r.reward,
                    "next_state": r.next_state.tolist() if isinstance(r.next_state, np.ndarray) else r.next_state
                }
                for r in self.meta_cognition.trajectory_buffer
            ]
        return []
    
    def train_epoch(self, dataloader: DataLoader) -> Dict:
        self.policy.train()
        total_loss = 0.0
        total_correct = 0
        total_samples = 0
        
        for batch in dataloader:
            states = batch["state"]
            actions = batch["action"].squeeze(-1)
            rewards = batch["reward"].squeeze(-1)
            
            self.optimizer.zero_grad()
            
            logits = self.policy(states)
            
            ce_loss = nn.CrossEntropyLoss()(logits, actions)
            
            probs = torch.softmax(logits, dim=-1)
            selected_probs = probs.gather(1, actions.unsqueeze(1)).squeeze(1)
            policy_loss = -torch.mean(torch.log(selected_probs + 1e-8) * rewards)
            
            loss = ce_loss + 0.5 * policy_loss
            
            loss.backward()
            self.optimizer.step()
            
            total_loss += loss.item()
            
            predictions = torch.argmax(logits, dim=-1)
            total_correct += (predictions == actions).sum().item()
            total_samples += len(actions)
            
            self.total_steps += 1
        
        avg_loss = total_loss / len(dataloader)
        accuracy = total_correct / total_samples if total_samples > 0 else 0
        
        return {
            "loss": avg_loss,
            "accuracy": accuracy
        }
    
    def validate(self, dataloader: DataLoader) -> Dict:
        self.policy.eval()
        total_loss = 0.0
        total_correct = 0
        total_samples = 0
        total_reward = 0.0
        
        with torch.no_grad():
            for batch in dataloader:
                states = batch["state"]
                actions = batch["action"].squeeze(-1)
                rewards = batch["reward"].squeeze(-1)
                
                logits = self.policy(states)
                
                loss = nn.CrossEntropyLoss()(logits, actions)
                total_loss += loss.item()
                
                predictions = torch.argmax(logits, dim=-1)
                total_correct += (predictions == actions).sum().item()
                total_samples += len(actions)
                total_reward += rewards.sum().item()
        
        avg_loss = total_loss / len(dataloader) if len(dataloader) > 0 else 0
        accuracy = total_correct / total_samples if total_samples > 0 else 0
        avg_reward = total_reward / total_samples if total_samples > 0 else 0
        
        return {
            "loss": avg_loss,
            "accuracy": accuracy,
            "avg_reward": avg_reward
        }
    
    def train(self) -> Dict:
        if len(self.training_data) < self.config.min_samples:
            return {
                "status": "insufficient_data",
                "samples": len(self.training_data),
                "required": self.config.min_samples
            }
        
        self.is_training = True
        start_time = time.time()
        
        train_dataset = TrainingDataset(self.training_data)
        val_dataset = TrainingDataset(self.validation_data)
        
        train_loader = DataLoader(
            train_dataset,
            batch_size=self.config.batch_size,
            shuffle=True
        )
        val_loader = DataLoader(
            val_dataset,
            batch_size=self.config.batch_size,
            shuffle=False
        )
        
        training_results = []
        
        for epoch in range(self.config.epochs_per_session):
            self.current_epoch = epoch
            
            train_metrics = self.train_epoch(train_loader)
            val_metrics = self.validate(val_loader)
            
            epoch_result = {
                "epoch": epoch + 1,
                "train_loss": train_metrics["loss"],
                "train_accuracy": train_metrics["accuracy"],
                "val_loss": val_metrics["loss"],
                "val_accuracy": val_metrics["accuracy"],
                "val_reward": val_metrics["avg_reward"]
            }
            
            training_results.append(epoch_result)
            self.training_history.append(epoch_result)
            
            logger.info(
                f"Epoch {epoch + 1}/{self.config.epochs_per_session}: "
                f"train_loss={train_metrics['loss']:.4f}, "
                f"val_loss={val_metrics['loss']:.4f}, "
                f"val_reward={val_metrics['avg_reward']:.4f}"
            )
            
            if val_metrics["loss"] < self.best_loss:
                self.best_loss = val_metrics["loss"]
                self.patience_counter = 0
                self._save_checkpoint("best")
            else:
                self.patience_counter += 1
            
            if self.patience_counter >= self.config.early_stopping_patience:
                logger.info(f"Early stopping triggered at epoch {epoch + 1}")
                break
            
            elapsed_hours = (time.time() - start_time) / 3600
            if elapsed_hours >= self.config.max_training_time_hours:
                logger.info(f"Max training time reached: {elapsed_hours:.2f} hours")
                break
        
        self.is_training = False
        
        final_metrics = training_results[-1] if training_results else {}
        
        should_update = final_metrics.get("val_reward", 0) >= self.config.target_reward_threshold
        
        return {
            "status": "completed",
            "epochs_trained": len(training_results),
            "final_metrics": final_metrics,
            "should_update": should_update,
            "training_time_seconds": time.time() - start_time
        }
    
    def _save_checkpoint(self, name: str = "latest"):
        checkpoint_path = os.path.join(
            self.config.model_save_path,
            f"{self.agent_type}_{name}.pt"
        )
        
        torch.save({
            "policy_state_dict": self.policy.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "config": self.config.__dict__,
            "training_history": self.training_history[-100:],
            "timestamp": datetime.now().isoformat()
        }, checkpoint_path)
        
        logger.info(f"Saved checkpoint: {checkpoint_path}")
    
    def load_checkpoint(self, checkpoint_path: str) -> bool:
        if not os.path.exists(checkpoint_path):
            return False
        
        try:
            checkpoint = torch.load(checkpoint_path)
            self.policy.load_state_dict(checkpoint["policy_state_dict"])
            self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
            logger.info(f"Loaded checkpoint: {checkpoint_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}")
            return False
    
    def get_status(self) -> Dict:
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "is_training": self.is_training,
            "current_epoch": self.current_epoch,
            "total_steps": self.total_steps,
            "training_samples": len(self.training_data),
            "validation_samples": len(self.validation_data),
            "best_loss": self.best_loss,
            "model_version": self.model_version
        }


class EvolutionTrainingCoordinator:
    
    def __init__(
        self,
        evolution_engine: EvolutionEngine,
        config: TrainingConfig
    ):
        self.evolution_engine = evolution_engine
        self.config = config
        
        self.trainers: Dict[str, ContinuousTrainer] = {}
        self.training_schedule: Dict[str, datetime] = {}
        
        self.running = False
        self.last_data_refresh = datetime.now()
    
    def register_agent(
        self,
        agent_id: str,
        agent_type: str,
        meta_cognition: Optional[MetaCognitionModule] = None
    ):
        trainer = ContinuousTrainer(
            agent_id=agent_id,
            agent_type=agent_type,
            config=self.config,
            meta_cognition=meta_cognition
        )
        
        self.trainers[agent_id] = trainer
        self.training_schedule[agent_id] = datetime.now()
        
        logger.info(f"Registered agent for continuous training: {agent_id}")
    
    def check_and_train(self) -> Dict[str, Dict]:
        results = {}
        
        for agent_id, trainer in self.trainers.items():
            last_training = self.training_schedule.get(agent_id, datetime.min)
            
            if (datetime.now() - last_training).total_seconds() > self.config.data_refresh_interval:
                data_count = trainer.load_training_data()
                
                if data_count >= self.config.min_samples:
                    result = trainer.train()
                    results[agent_id] = result
                    
                    if result.get("should_update"):
                        self._trigger_evolution(agent_id, trainer)
                    
                    self.training_schedule[agent_id] = datetime.now()
        
        return results
    
    def _trigger_evolution(self, agent_id: str, trainer: ContinuousTrainer):
        checkpoint_path = os.path.join(
            self.config.model_save_path,
            f"{trainer.agent_type}_best.pt"
        )
        
        if os.path.exists(checkpoint_path):
            new_version = f"v{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            self.evolution_engine.register_agent_version(
                agent_type=trainer.agent_type,
                version=new_version,
                model_path=checkpoint_path,
                metrics={
                    "val_reward": trainer.training_history[-1].get("val_reward", 0) if trainer.training_history else 0,
                    "val_accuracy": trainer.training_history[-1].get("val_accuracy", 0) if trainer.training_history else 0
                }
            )
            
            logger.info(f"Registered new model version for {agent_id}: {new_version}")
    
    async def run_continuous_loop(self, interval_seconds: int = 3600):
        self.running = True
        
        while self.running:
            try:
                results = self.check_and_train()
                
                if results:
                    logger.info(f"Training cycle completed for {len(results)} agents")
                
                await asyncio.sleep(interval_seconds)
                
            except Exception as e:
                logger.error(f"Error in training loop: {e}")
                await asyncio.sleep(60)
    
    def stop(self):
        self.running = False
        logger.info("Evolution training coordinator stopped")
    
    def get_status(self) -> Dict:
        return {
            "running": self.running,
            "registered_agents": len(self.trainers),
            "agents_status": {
                agent_id: trainer.get_status()
                for agent_id, trainer in self.trainers.items()
            },
            "last_data_refresh": self.last_data_refresh.isoformat()
        }


def run_daily_training():
    import argparse
    
    parser = argparse.ArgumentParser(description="Continuous Training for Agent Evolution")
    parser.add_argument("--agent-type", type=str, default="attack", help="Agent type to train")
    parser.add_argument("--epochs", type=int, default=10, help="Number of epochs per session")
    parser.add_argument("--batch-size", type=int, default=64, help="Batch size")
    parser.add_argument("--lr", type=float, default=1e-4, help="Learning rate")
    parser.add_argument("--min-samples", type=int, default=1000, help="Minimum samples for training")
    parser.add_argument("--output", type=str, default="models/versions", help="Output directory")
    
    args = parser.parse_args()
    
    config = TrainingConfig(
        batch_size=args.batch_size,
        learning_rate=args.lr,
        epochs_per_session=args.epochs,
        min_samples=args.min_samples,
        model_save_path=args.output
    )
    
    trainer = ContinuousTrainer(
        agent_id=f"{args.agent_type}_trainer",
        agent_type=args.agent_type,
        config=config
    )
    
    data_count = trainer.load_training_data()
    
    if data_count < config.min_samples:
        logger.warning(f"Generating synthetic data for demonstration")
        synthetic_data = []
        for _ in range(config.min_samples):
            synthetic_data.append({
                "state": np.random.randn(13).tolist(),
                "action": random.randint(0, 7),
                "reward": random.random()
            })
        trainer.training_data = synthetic_data[:int(len(synthetic_data) * 0.8)]
        trainer.validation_data = synthetic_data[int(len(synthetic_data) * 0.8):]
    
    result = trainer.train()
    
    print(json.dumps(result, indent=2, default=str))
    
    return result


try:
    from celery import shared_task
    from .celery_app import app
    
    @shared_task(name="backend.workers.continuous_training.run_daily_training")
    def run_daily_training_task(agent_type: str = "attack", epochs: int = 10, batch_size: int = 64, lr: float = 1e-4):
        config = TrainingConfig(
            batch_size=batch_size,
            learning_rate=lr,
            epochs_per_session=epochs,
            min_samples=1000,
            model_save_path="models/versions"
        )
        
        trainer = ContinuousTrainer(
            agent_id=f"{agent_type}_trainer",
            agent_type=agent_type,
            config=config
        )
        
        data_count = trainer.load_training_data()
        
        if data_count < config.min_samples:
            logger.warning(f"Generating synthetic data for demonstration")
            synthetic_data = []
            for _ in range(config.min_samples):
                synthetic_data.append({
                    "state": np.random.randn(13).tolist(),
                    "action": random.randint(0, 7),
                    "reward": random.random()
                })
            trainer.training_data = synthetic_data[:int(len(synthetic_data) * 0.8)]
            trainer.validation_data = synthetic_data[int(len(synthetic_data) * 0.8):]
        
        result = trainer.train()
        
        return result
        
except ImportError:
    pass


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    run_daily_training()
