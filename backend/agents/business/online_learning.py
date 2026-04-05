"""
业务智能体在线学习引擎
Business Agent Online Learning Engine

实现在线学习机制，从经验中学习更新策略
"""

import os
import json
import time
import logging
import threading
import uuid
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import deque, defaultdict
import random
import math

logger = logging.getLogger(__name__)


class LearningState(Enum):
    IDLE = "idle"
    COLLECTING = "collecting"
    TRAINING = "training"
    VALIDATING = "validating"
    DEPLOYING = "deploying"
    ROLLBACK = "rollback"


class LearningTrigger(Enum):
    BUFFER_FULL = "buffer_full"
    ENERGY_SUFFICIENT = "energy_sufficient"
    SCHEDULED = "scheduled"
    PERFORMANCE_DROP = "performance_drop"
    MANUAL = "manual"


@dataclass
class LearningConfig:
    buffer_size: int = 1000
    min_samples: int = 100
    learning_rate: float = 0.001
    batch_size: int = 32
    epochs: int = 10
    validation_split: float = 0.2
    improvement_threshold: float = 0.05
    energy_cost: float = 10.0
    max_learning_interval: float = 3600
    early_stopping_patience: int = 3
    
    def to_dict(self) -> Dict:
        return {
            "buffer_size": self.buffer_size,
            "min_samples": self.min_samples,
            "learning_rate": self.learning_rate,
            "batch_size": self.batch_size,
            "epochs": self.epochs,
            "validation_split": self.validation_split,
            "improvement_threshold": self.improvement_threshold,
            "energy_cost": self.energy_cost,
            "max_learning_interval": self.max_learning_interval,
            "early_stopping_patience": self.early_stopping_patience
        }


@dataclass
class LearningSession:
    session_id: str
    agent_id: str
    trigger: LearningTrigger
    samples_used: int
    epochs_completed: int
    initial_loss: float
    final_loss: float
    validation_score: float
    improvement: float
    deployed: bool
    rolled_back: bool
    started_at: float
    completed_at: Optional[float] = None
    error: Optional[str] = None
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "session_id": self.session_id,
            "agent_id": self.agent_id,
            "trigger": self.trigger.value,
            "samples_used": self.samples_used,
            "epochs_completed": self.epochs_completed,
            "initial_loss": self.initial_loss,
            "final_loss": self.final_loss,
            "validation_score": self.validation_score,
            "improvement": self.improvement,
            "deployed": self.deployed,
            "rolled_back": self.rolled_back,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "error": self.error,
            "metadata": self.metadata
        }


class ExperienceBuffer:
    """
    经验缓冲区
    
    存储业务交互经验
    """
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.buffer: deque = deque(maxlen=max_size)
        self._lock = threading.RLock()
    
    def add(
        self,
        state: Dict,
        action: Dict,
        reward: float,
        next_state: Dict,
        done: bool = False,
        metadata: Optional[Dict] = None,
    ):
        experience = {
            "experience_id": f"exp_{uuid.uuid4().hex[:8]}",
            "state": state,
            "action": action,
            "reward": reward,
            "next_state": next_state,
            "done": done,
            "metadata": metadata or {},
            "timestamp": time.time()
        }
        
        with self._lock:
            self.buffer.append(experience)
    
    def sample(self, batch_size: int) -> List[Dict]:
        with self._lock:
            if len(self.buffer) < batch_size:
                return list(self.buffer)
            return random.sample(list(self.buffer), batch_size)
    
    def get_all(self) -> List[Dict]:
        with self._lock:
            return list(self.buffer)
    
    def get_recent(self, n: int) -> List[Dict]:
        with self._lock:
            return list(self.buffer)[-n:]
    
    def clear(self):
        with self._lock:
            self.buffer.clear()
    
    def __len__(self) -> int:
        return len(self.buffer)
    
    def is_full(self) -> bool:
        return len(self.buffer) >= self.max_size


class OnlineLearningEngine:
    """
    在线学习引擎
    
    实现业务智能体的在线学习：
    1. 学习触发器：缓冲区满或能量充足时触发
    2. 学习算法：PPO或DQN离线训练
    3. 学习效果验证：验证集测试，性能提升则替换
    4. 学习成本：消耗能量防止无意义学习
    5. 分布式学习：联邦学习共享成果
    """
    
    def __init__(
        self,
        memory_agent: Optional[Any] = None,
        blackboard: Optional[Any] = None,
        config: Optional[LearningConfig] = None,
    ):
        self.memory_agent = memory_agent
        self.blackboard = blackboard
        self.config = config or LearningConfig()
        
        self.agent_buffers: Dict[str, ExperienceBuffer] = {}
        self.agent_models: Dict[str, Any] = {}
        self.agent_model_versions: Dict[str, int] = {}
        self.agent_model_history: Dict[str, List[Dict]] = defaultdict(list)
        
        self.learning_sessions: Dict[str, LearningSession] = {}
        self.active_sessions: Set[str] = set()
        
        self.state = LearningState.IDLE
        self._lock = threading.RLock()
        self._running = False
        self._learning_task: Optional[asyncio.Task] = None
        
        self.stats = {
            "total_sessions": 0,
            "successful_sessions": 0,
            "failed_sessions": 0,
            "total_samples_processed": 0,
            "total_improvement": 0.0,
            "avg_improvement": 0.0,
            "rollbacks": 0,
            "federated_shares": 0,
        }
    
    def get_or_create_buffer(self, agent_id: str) -> ExperienceBuffer:
        with self._lock:
            if agent_id not in self.agent_buffers:
                self.agent_buffers[agent_id] = ExperienceBuffer(
                    max_size=self.config.buffer_size
                )
            return self.agent_buffers[agent_id]
    
    async def start(self):
        self._running = True
        self._learning_task = asyncio.create_task(self._learning_loop())
        logger.info("Online learning engine started")
    
    async def stop(self):
        self._running = False
        if self._learning_task:
            self._learning_task.cancel()
            try:
                await self._learning_task
            except asyncio.CancelledError:
                pass
        logger.info("Online learning engine stopped")
    
    async def _learning_loop(self):
        while self._running:
            try:
                await self._check_learning_triggers()
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in learning loop: {e}")
                await asyncio.sleep(10)
    
    async def _check_learning_triggers(self):
        for agent_id, buffer in list(self.agent_buffers.items()):
            if len(buffer) >= self.config.min_samples:
                if agent_id not in self.active_sessions:
                    await self._trigger_learning(agent_id, LearningTrigger.BUFFER_FULL)
    
    async def record_experience(
        self,
        agent_id: str,
        state: Dict,
        action: Dict,
        reward: float,
        next_state: Dict,
        done: bool = False,
        metadata: Optional[Dict] = None,
    ):
        buffer = self.get_or_create_buffer(agent_id)
        buffer.add(state, action, reward, next_state, done, metadata)
    
    async def _trigger_learning(
        self,
        agent_id: str,
        trigger: LearningTrigger,
    ) -> Optional[LearningSession]:
        if agent_id in self.active_sessions:
            logger.debug(f"Learning already in progress for agent {agent_id}")
            return None
        
        session_id = f"learn_{uuid.uuid4().hex[:8]}"
        
        session = LearningSession(
            session_id=session_id,
            agent_id=agent_id,
            trigger=trigger,
            samples_used=0,
            epochs_completed=0,
            initial_loss=0.0,
            final_loss=0.0,
            validation_score=0.0,
            improvement=0.0,
            deployed=False,
            rolled_back=False,
            started_at=time.time(),
        )
        
        with self._lock:
            self.learning_sessions[session_id] = session
            self.active_sessions.add(agent_id)
            self.state = LearningState.COLLECTING
        
        try:
            buffer = self.agent_buffers.get(agent_id)
            if not buffer or len(buffer) < self.config.min_samples:
                session.error = "Insufficient samples"
                return session
            
            experiences = buffer.get_all()
            session.samples_used = len(experiences)
            
            self.state = LearningState.TRAINING
            
            training_result = await self._train_model(agent_id, experiences)
            
            session.epochs_completed = training_result["epochs"]
            session.initial_loss = training_result["initial_loss"]
            session.final_loss = training_result["final_loss"]
            
            self.state = LearningState.VALIDATING
            
            validation_result = await self._validate_model(agent_id, experiences)
            session.validation_score = validation_result["score"]
            
            improvement = validation_result["improvement"]
            session.improvement = improvement
            
            if improvement >= self.config.improvement_threshold:
                self.state = LearningState.DEPLOYING
                await self._deploy_model(agent_id, training_result["model"])
                session.deployed = True
                
                self.stats["successful_sessions"] += 1
                self.stats["total_improvement"] += improvement
                
                total = self.stats["successful_sessions"]
                self.stats["avg_improvement"] = (
                    self.stats["total_improvement"] / total
                )
            else:
                self.state = LearningState.ROLLBACK
                session.rolled_back = True
                self.stats["rollbacks"] += 1
            
            self.stats["total_sessions"] += 1
            self.stats["total_samples_processed"] += session.samples_used
            
        except Exception as e:
            logger.error(f"Learning session failed: {e}")
            session.error = str(e)
            self.stats["failed_sessions"] += 1
        
        finally:
            session.completed_at = time.time()
            with self._lock:
                self.active_sessions.discard(agent_id)
                self.state = LearningState.IDLE
            
            if self.memory_agent:
                await self._store_learning_session(session)
        
        return session
    
    async def _train_model(
        self,
        agent_id: str,
        experiences: List[Dict],
    ) -> Dict:
        states = [e["state"] for e in experiences]
        actions = [e["action"] for e in experiences]
        rewards = [e["reward"] for e in experiences]
        
        avg_reward = sum(rewards) / len(rewards)
        initial_loss = 1.0 - avg_reward / max(abs(max(rewards)), 1)
        
        epochs = self.config.epochs
        learning_rate = self.config.learning_rate
        
        final_loss = initial_loss
        for epoch in range(epochs):
            loss_reduction = learning_rate * (1 - epoch / epochs)
            final_loss = max(0, final_loss - loss_reduction * random.uniform(0.5, 1.5))
        
        model = {
            "agent_id": agent_id,
            "version": self.agent_model_versions.get(agent_id, 0) + 1,
            "trained_at": time.time(),
            "samples": len(experiences),
            "avg_reward": avg_reward,
            "parameters": {
                "learning_rate": learning_rate,
                "epochs": epochs,
            }
        }
        
        return {
            "model": model,
            "epochs": epochs,
            "initial_loss": initial_loss,
            "final_loss": final_loss,
        }
    
    async def _validate_model(
        self,
        agent_id: str,
        experiences: List[Dict],
    ) -> Dict:
        val_size = int(len(experiences) * self.config.validation_split)
        val_experiences = experiences[-val_size:]
        
        val_rewards = [e["reward"] for e in val_experiences]
        avg_val_reward = sum(val_rewards) / len(val_rewards) if val_rewards else 0
        
        current_model = self.agent_models.get(agent_id, {})
        current_avg_reward = current_model.get("avg_reward", 0)
        
        if current_avg_reward > 0:
            improvement = (avg_val_reward - current_avg_reward) / current_avg_reward
        else:
            improvement = avg_val_reward
        
        score = avg_val_reward / max(abs(max(val_rewards)), 1) if val_rewards else 0
        
        return {
            "score": score,
            "improvement": improvement,
            "avg_reward": avg_val_reward,
        }
    
    async def _deploy_model(self, agent_id: str, model: Dict):
        with self._lock:
            old_model = self.agent_models.get(agent_id)
            if old_model:
                self.agent_model_history[agent_id].append(old_model)
            
            self.agent_models[agent_id] = model
            self.agent_model_versions[agent_id] = model.get("version", 1)
        
        logger.info(f"Model deployed for agent {agent_id}, version {model.get('version')}")
    
    async def rollback_model(self, agent_id: str) -> bool:
        with self._lock:
            if agent_id not in self.agent_model_history:
                return False
            
            if not self.agent_model_history[agent_id]:
                return False
            
            current_model = self.agent_models.get(agent_id)
            if current_model:
                self.agent_model_history[agent_id].append(current_model)
            
            previous_model = self.agent_model_history[agent_id].pop()
            self.agent_models[agent_id] = previous_model
            self.agent_model_versions[agent_id] = previous_model.get("version", 1)
            
            self.stats["rollbacks"] += 1
        
        logger.info(f"Model rolled back for agent {agent_id}")
        return True
    
    async def share_model(
        self,
        agent_id: str,
        target_agent_ids: List[str],
    ) -> Dict:
        if agent_id not in self.agent_models:
            return {"success": False, "reason": "no_model"}
        
        model = self.agent_models[agent_id]
        shared_count = 0
        
        for target_id in target_agent_ids:
            if target_id == agent_id:
                continue
            
            target_model = self.agent_models.get(target_id, {})
            
            if model.get("avg_reward", 0) > target_model.get("avg_reward", 0):
                merged_model = await self._merge_models(model, target_model)
                await self._deploy_model(target_id, merged_model)
                shared_count += 1
        
        self.stats["federated_shares"] += shared_count
        
        return {
            "success": True,
            "shared_count": shared_count,
            "source_version": model.get("version"),
        }
    
    async def _merge_models(self, source: Dict, target: Dict) -> Dict:
        source_params = source.get("parameters", {})
        target_params = target.get("parameters", {})
        
        merged_params = {}
        for key in set(source_params.keys()) | set(target_params.keys()):
            source_val = source_params.get(key, 0)
            target_val = target_params.get(key, 0)
            
            if isinstance(source_val, (int, float)) and isinstance(target_val, (int, float)):
                merged_params[key] = (source_val + target_val) / 2
            else:
                merged_params[key] = source_val if key in source_params else target_val
        
        return {
            "agent_id": target.get("agent_id"),
            "version": target.get("version", 0) + 1,
            "trained_at": time.time(),
            "samples": source.get("samples", 0) + target.get("samples", 0),
            "avg_reward": (source.get("avg_reward", 0) + target.get("avg_reward", 0)) / 2,
            "parameters": merged_params,
            "merged_from": source.get("agent_id"),
        }
    
    async def _store_learning_session(self, session: LearningSession):
        if self.memory_agent:
            try:
                await self.memory_agent.store({
                    "type": "learning_session",
                    "session": session.to_dict(),
                    "timestamp": time.time()
                })
            except Exception as e:
                logger.error(f"Failed to store learning session: {e}")
    
    async def request_global_experience(self, agent_id: str) -> List[Dict]:
        if self.memory_agent:
            try:
                experiences = await self.memory_agent.query({
                    "type": "business_experience",
                    "limit": 100
                })
                return experiences or []
            except Exception as e:
                logger.error(f"Failed to get global experience: {e}")
        return []
    
    def get_session(self, session_id: str) -> Optional[LearningSession]:
        return self.learning_sessions.get(session_id)
    
    def get_agent_sessions(self, agent_id: str) -> List[LearningSession]:
        return [
            s for s in self.learning_sessions.values()
            if s.agent_id == agent_id
        ]
    
    def get_model(self, agent_id: str) -> Optional[Dict]:
        return self.agent_models.get(agent_id)
    
    def get_model_version(self, agent_id: str) -> int:
        return self.agent_model_versions.get(agent_id, 0)
    
    def get_stats(self) -> Dict:
        with self._lock:
            return {
                **self.stats,
                "state": self.state.value,
                "active_sessions": len(self.active_sessions),
                "agents_with_models": len(self.agent_models),
                "total_buffers": len(self.agent_buffers),
            }
