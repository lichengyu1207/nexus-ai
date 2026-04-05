"""
分布式强化学习训练框架
Distributed Reinforcement Learning Training Framework

基于Ray RLlib实现多智能体并行训练
"""

import asyncio
import json
import uuid
import time
import hashlib
import numpy as np
from enum import Enum
from typing import Dict, List, Optional, Any, Set, Tuple, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime
import logging
from collections import defaultdict
import threading
import queue

logger = logging.getLogger(__name__)

try:
    import ray
    from ray import tune
    from ray.rllib.algorithms import ppo, dqn, a3c, impala
    RAY_AVAILABLE = True
except ImportError:
    RAY_AVAILABLE = False
    logger.warning("Ray RLlib not available, using mock implementation")


class AlgorithmType(Enum):
    PPO = "ppo"
    DQN = "dqn"
    A3C = "a3c"
    IMPALA = "impala"
    APPO = "appo"
    MARL = "marl"


class TrainingStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class EnvironmentType(Enum):
    MARKET_SIMULATION = "market_simulation"
    ATTACK_DEFENSE = "attack_defense"
    RESOURCE_ALLOCATION = "resource_allocation"
    PRICING_STRATEGY = "pricing_strategy"
    AGENT_COORDINATION = "agent_coordination"
    CUSTOM = "custom"


@dataclass
class TrainingConfig:
    config_id: str
    algorithm: AlgorithmType
    environment: EnvironmentType
    num_workers: int = 4
    num_envs_per_worker: int = 1
    learning_rate: float = 0.0003
    gamma: float = 0.99
    lambda_: float = 0.95
    clip_param: float = 0.2
    vf_clip_param: float = 10.0
    entropy_coeff: float = 0.01
    train_batch_size: int = 4000
    sgd_minibatch_size: int = 128
    num_sgd_iter: int = 30
    framework: str = "torch"
    num_gpus: float = 0.0
    num_cpus_per_worker: float = 1.0
    num_gpus_per_worker: float = 0.0
    rollout_fragment_length: int = 200
    multiagent_policies: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    custom_config: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "config_id": self.config_id,
            "algorithm": self.algorithm.value,
            "environment": self.environment.value,
            "num_workers": self.num_workers,
            "num_envs_per_worker": self.num_envs_per_worker,
            "learning_rate": self.learning_rate,
            "gamma": self.gamma,
            "lambda_": self.lambda_,
            "clip_param": self.clip_param,
            "vf_clip_param": self.vf_clip_param,
            "entropy_coeff": self.entropy_coeff,
            "train_batch_size": self.train_batch_size,
            "sgd_minibatch_size": self.sgd_minibatch_size,
            "num_sgd_iter": self.num_sgd_iter,
            "framework": self.framework,
            "num_gpus": self.num_gpus,
            "num_cpus_per_worker": self.num_cpus_per_worker,
            "num_gpus_per_worker": self.num_gpus_per_worker,
            "rollout_fragment_length": self.rollout_fragment_length,
            "multiagent_policies": self.multiagent_policies,
            "custom_config": self.custom_config,
        }
    
    def to_rllib_config(self) -> Dict[str, Any]:
        base_config = {
            "train_batch_size": self.train_batch_size,
            "sgd_minibatch_size": self.sgd_minibatch_size,
            "num_sgd_iter": self.num_sgd_iter,
            "lr": self.learning_rate,
            "gamma": self.gamma,
            "lambda": self.lambda_,
            "clip_param": self.clip_param,
            "vf_clip_param": self.vf_clip_param,
            "entropy_coeff": self.entropy_coeff,
            "framework": self.framework,
            "num_workers": self.num_workers,
            "num_envs_per_worker": self.num_envs_per_worker,
            "num_gpus": self.num_gpus,
            "num_cpus_per_worker": self.num_cpus_per_worker,
            "num_gpus_per_worker": self.num_gpus_per_worker,
            "rollout_fragment_length": self.rollout_fragment_length,
        }
        
        if self.multiagent_policies:
            base_config["multiagent"] = {
                "policies": self.multiagent_policies,
                "policy_mapping_fn": lambda agent_id: "default_policy",
            }
        
        base_config.update(self.custom_config)
        return base_config


@dataclass
class TrainingMetrics:
    training_id: str
    iteration: int
    episode_reward_mean: float
    episode_reward_min: float
    episode_reward_max: float
    episode_len_mean: float
    num_episodes: int
    timesteps_total: int
    time_total_s: float
    info: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "training_id": self.training_id,
            "iteration": self.iteration,
            "episode_reward_mean": self.episode_reward_mean,
            "episode_reward_min": self.episode_reward_min,
            "episode_reward_max": self.episode_reward_max,
            "episode_len_mean": self.episode_len_mean,
            "num_episodes": self.num_episodes,
            "timesteps_total": self.timesteps_total,
            "time_total_s": self.time_total_s,
            "info": self.info,
            "timestamp": self.timestamp,
        }


@dataclass
class TrainingJob:
    job_id: str
    config: TrainingConfig
    status: TrainingStatus = TrainingStatus.PENDING
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    current_iteration: int = 0
    total_iterations: int = 100
    metrics_history: List[TrainingMetrics] = field(default_factory=list)
    checkpoint_path: Optional[str] = None
    error_message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "config": self.config.to_dict(),
            "status": self.status.value,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "current_iteration": self.current_iteration,
            "total_iterations": self.total_iterations,
            "metrics_count": len(self.metrics_history),
            "checkpoint_path": self.checkpoint_path,
            "error_message": self.error_message,
            "metadata": self.metadata,
        }
    
    def get_latest_metrics(self) -> Optional[TrainingMetrics]:
        if self.metrics_history:
            return self.metrics_history[-1]
        return None


class MockEnvironment:
    """模拟环境用于无Ray时的训练"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.observation_space = type('Space', (), {
            'shape': (10,),
            'low': np.array([-1.0] * 10),
            'high': np.array([1.0] * 10),
        })()
        self.action_space = type('Space', (), {'n': 5})()
        self._state = None
        self._step_count = 0
        self._max_steps = 100
    
    def reset(self):
        self._state = np.random.randn(10)
        self._step_count = 0
        return self._state
    
    def step(self, action):
        self._step_count += 1
        reward = np.random.randn() * 0.1
        done = self._step_count >= self._max_steps
        self._state = np.random.randn(10)
        return self._state, reward, done, {}


class PriorityExperienceReplay:
    """优先经验回放缓冲区"""
    
    def __init__(self, capacity: int = 100000, alpha: float = 0.6, beta: float = 0.4):
        self.capacity = capacity
        self.alpha = alpha
        self.beta = beta
        self._buffer: List[Tuple[float, Any]] = []
        self._max_priority = 1.0
        self._lock = threading.Lock()
    
    def add(self, experience: Any, priority: float = None) -> None:
        with self._lock:
            if priority is None:
                priority = self._max_priority
            priority = priority ** self.alpha
            if len(self._buffer) >= self.capacity:
                self._buffer.pop(0)
            self._buffer.append((priority, experience))
    
    def sample(self, batch_size: int) -> Tuple[List[Any], List[int], np.ndarray]:
        with self._lock:
            if len(self._buffer) < batch_size:
                return [], [], np.array([])
            
            priorities = np.array([p for p, _ in self._buffer])
            probs = priorities / priorities.sum()
            indices = np.random.choice(len(self._buffer), batch_size, p=probs, replace=False)
            weights = (len(self._buffer) * probs[indices]) ** (-self.beta)
            weights = weights / weights.max()
            experiences = [self._buffer[i][1] for i in indices]
            return experiences, list(indices), weights
    
    def update_priorities(self, indices: List[int], priorities: np.ndarray) -> None:
        with self._lock:
            for idx, priority in zip(indices, priorities):
                if 0 <= idx < len(self._buffer):
                    new_priority = (priority + 1e-6) ** self.alpha
                    self._buffer[idx] = (new_priority, self._buffer[idx][1])
                    self._max_priority = max(self._max_priority, new_priority)
    
    def __len__(self) -> int:
        return len(self._buffer)


class DistributedRLTrainer:
    """分布式强化学习训练器"""
    
    def __init__(self, redis_client: Optional[Any] = None):
        self.redis_client = redis_client
        self._jobs: Dict[str, TrainingJob] = {}
        self._environments: Dict[str, Any] = {}
        self._lock = asyncio.Lock()
        self._running = False
        self._tasks: List[asyncio.Task] = []
        self._per_buffer = PriorityExperienceReplay()
        
        self._initialize_ray()
    
    def _initialize_ray(self) -> None:
        if RAY_AVAILABLE and not ray.is_initialized():
            try:
                ray.init(ignore_reinit_error=True, log_to_driver=False)
                logger.info("Ray initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Ray: {e}")
    
    async def start(self) -> None:
        self._running = True
        self._tasks.append(asyncio.create_task(self._cleanup_completed_jobs()))
        logger.info("DistributedRLTrainer started")
    
    async def stop(self) -> None:
        self._running = False
        for task in self._tasks:
            task.cancel()
        self._tasks.clear()
        logger.info("DistributedRLTrainer stopped")
    
    def register_environment(self, env_type: EnvironmentType, 
                              env_class: Any, config: Dict[str, Any] = None) -> None:
        self._environments[env_type.value] = {
            "class": env_class,
            "config": config or {},
        }
        logger.info(f"Environment registered: {env_type.value}")
    
    async def create_training_job(self, config: TrainingConfig,
                                   total_iterations: int = 100) -> str:
        async with self._lock:
            job_id = str(uuid.uuid4())
            
            job = TrainingJob(
                job_id=job_id,
                config=config,
                total_iterations=total_iterations,
            )
            
            self._jobs[job_id] = job
            logger.info(f"Training job created: {job_id}")
            return job_id
    
    async def start_training(self, job_id: str) -> bool:
        async with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return False
            
            if job.status != TrainingStatus.PENDING:
                return False
            
            job.status = TrainingStatus.RUNNING
            job.started_at = time.time()
            
            asyncio.create_task(self._run_training(job))
            
            logger.info(f"Training started: {job_id}")
            return True
    
    async def _run_training(self, job: TrainingJob) -> None:
        try:
            if RAY_AVAILABLE:
                await self._run_rllib_training(job)
            else:
                await self._run_mock_training(job)
        except Exception as e:
            job.status = TrainingStatus.FAILED
            job.error_message = str(e)
            logger.error(f"Training failed: {job.job_id} - {e}")
    
    async def _run_rllib_training(self, job: TrainingJob) -> None:
        env_config = self._environments.get(job.config.environment.value)
        if not env_config:
            raise ValueError(f"Environment not found: {job.config.environment.value}")
        
        rllib_config = job.config.to_rllib_config()
        
        if job.config.algorithm == AlgorithmType.PPO:
            algo = ppo.PPO(env=env_config["class"], config=rllib_config)
        elif job.config.algorithm == AlgorithmType.DQN:
            algo = dqn.DQN(env=env_config["class"], config=rllib_config)
        else:
            algo = ppo.PPO(env=env_config["class"], config=rllib_config)
        
        for i in range(job.total_iterations):
            if job.status != TrainingStatus.RUNNING:
                break
            
            result = algo.train()
            
            metrics = TrainingMetrics(
                training_id=job.job_id,
                iteration=i + 1,
                episode_reward_mean=result.get("episode_reward_mean", 0),
                episode_reward_min=result.get("episode_reward_min", 0),
                episode_reward_max=result.get("episode_reward_max", 0),
                episode_len_mean=result.get("episode_len_mean", 0),
                num_episodes=result.get("episodes_this_iter", 0),
                timesteps_total=result.get("timesteps_total", 0),
                time_total_s=result.get("time_total_s", 0),
                info=result.get("info", {}),
            )
            
            job.metrics_history.append(metrics)
            job.current_iteration = i + 1
            
            if (i + 1) % 10 == 0:
                checkpoint_path = algo.save()
                job.checkpoint_path = checkpoint_path
        
        if job.current_iteration >= job.total_iterations:
            job.status = TrainingStatus.COMPLETED
            job.completed_at = time.time()
    
    async def _run_mock_training(self, job: TrainingJob) -> None:
        env = MockEnvironment()
        
        for i in range(job.total_iterations):
            if job.status != TrainingStatus.RUNNING:
                break
            
            state = env.reset()
            total_reward = 0
            episode_length = 0
            done = False
            
            while not done:
                action = np.random.randint(0, 5)
                next_state, reward, done, info = env.step(action)
                total_reward += reward
                episode_length += 1
            
            metrics = TrainingMetrics(
                training_id=job.job_id,
                iteration=i + 1,
                episode_reward_mean=total_reward,
                episode_reward_min=total_reward - 1,
                episode_reward_max=total_reward + 1,
                episode_len_mean=episode_length,
                num_episodes=1,
                timesteps_total=(i + 1) * episode_length,
                time_total_s=(i + 1) * 0.1,
            )
            
            job.metrics_history.append(metrics)
            job.current_iteration = i + 1
            
            await asyncio.sleep(0.01)
        
        if job.current_iteration >= job.total_iterations:
            job.status = TrainingStatus.COMPLETED
            job.completed_at = time.time()
    
    async def pause_training(self, job_id: str) -> bool:
        async with self._lock:
            job = self._jobs.get(job_id)
            if not job or job.status != TrainingStatus.RUNNING:
                return False
            
            job.status = TrainingStatus.PAUSED
            return True
    
    async def resume_training(self, job_id: str) -> bool:
        async with self._lock:
            job = self._jobs.get(job_id)
            if not job or job.status != TrainingStatus.PAUSED:
                return False
            
            job.status = TrainingStatus.RUNNING
            asyncio.create_task(self._run_training(job))
            return True
    
    async def cancel_training(self, job_id: str) -> bool:
        async with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return False
            
            job.status = TrainingStatus.CANCELLED
            job.completed_at = time.time()
            return True
    
    async def _cleanup_completed_jobs(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(3600)
                async with self._lock:
                    cutoff_time = time.time() - 86400
                    completed_ids = [
                        job_id for job_id, job in self._jobs.items()
                        if job.completed_at and job.completed_at < cutoff_time
                    ]
                    for job_id in completed_ids:
                        del self._jobs[job_id]
                    if completed_ids:
                        logger.info(f"Cleaned up {len(completed_ids)} completed jobs")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
    
    async def get_job(self, job_id: str) -> Optional[TrainingJob]:
        return self._jobs.get(job_id)
    
    async def get_job_metrics(self, job_id: str, limit: int = 100) -> List[TrainingMetrics]:
        job = self._jobs.get(job_id)
        if not job:
            return []
        return job.metrics_history[-limit:]
    
    async def get_all_jobs(self, status: TrainingStatus = None) -> List[TrainingJob]:
        jobs = list(self._jobs.values())
        if status:
            jobs = [j for j in jobs if j.status == status]
        return jobs
    
    async def get_statistics(self) -> Dict[str, Any]:
        by_status = defaultdict(int)
        by_algorithm = defaultdict(int)
        
        for job in self._jobs.values():
            by_status[job.status.value] += 1
            by_algorithm[job.config.algorithm.value] += 1
        
        return {
            "total_jobs": len(self._jobs),
            "by_status": dict(by_status),
            "by_algorithm": dict(by_algorithm),
            "ray_available": RAY_AVAILABLE,
            "ray_initialized": ray.is_initialized() if RAY_AVAILABLE else False,
        }


class RLTrainingMonitor:
    """RL训练监控器"""
    
    def __init__(self, trainer: DistributedRLTrainer):
        self.trainer = trainer
        self._metrics_history: List[Dict[str, Any]] = []
    
    async def collect_metrics(self) -> Dict[str, Any]:
        stats = await self.trainer.get_statistics()
        metrics = {"timestamp": time.time(), **stats}
        self._metrics_history.append(metrics)
        return metrics
    
    async def get_training_progress(self) -> Dict[str, Any]:
        jobs = await self.trainer.get_all_jobs(TrainingStatus.RUNNING)
        progress = []
        for job in jobs:
            latest = job.get_latest_metrics()
            progress.append({
                "job_id": job.job_id,
                "algorithm": job.config.algorithm.value,
                "iteration": job.current_iteration,
                "total_iterations": job.total_iterations,
                "progress": job.current_iteration / job.total_iterations if job.total_iterations > 0 else 0,
                "episode_reward_mean": latest.episode_reward_mean if latest else 0,
            })
        return {"running_jobs": progress}
    
    async def get_performance_summary(self) -> Dict[str, Any]:
        completed_jobs = await self.trainer.get_all_jobs(TrainingStatus.COMPLETED)
        if not completed_jobs:
            return {"total_completed": 0}
        
        rewards = []
        for job in completed_jobs:
            latest = job.get_latest_metrics()
            if latest:
                rewards.append(latest.episode_reward_mean)
        
        return {
            "total_completed": len(completed_jobs),
            "avg_final_reward": float(np.mean(rewards)) if rewards else 0,
            "max_final_reward": float(max(rewards)) if rewards else 0,
            "min_final_reward": float(min(rewards)) if rewards else 0,
        }
