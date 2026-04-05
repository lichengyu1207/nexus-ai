"""
学习引擎调度器
Learning Engine Scheduler

负责：
- 定期从经验池采样，触发训练任务
- 管理模型版本，支持A/B测试
- 将更新后的模型部署到智能体
"""

import json
import time
import uuid
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import os
import shutil

from .experience_collector import experience_collector, Experience
from .ppo_trainer import PPOTrainer, PPOConfig, MultiAgentPPOTrainer
from .reflection_module import reflection_module, ReflectionResult


class TrainingStatus(Enum):
    """训练状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DeploymentStatus(Enum):
    """部署状态"""
    STAGING = "staging"
    ACTIVE = "active"
    ROLLED_BACK = "rolled_back"
    DEPRECATED = "deprecated"


@dataclass
class ModelVersion:
    """模型版本"""
    version_id: str
    agent_id: str
    model_path: str
    created_at: float
    metrics: Dict[str, float]
    status: DeploymentStatus = DeploymentStatus.STAGING
    parent_version: Optional[str] = None
    description: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "version_id": self.version_id,
            "agent_id": self.agent_id,
            "model_path": self.model_path,
            "created_at": self.created_at,
            "metrics": self.metrics,
            "status": self.status.value,
            "parent_version": self.parent_version,
            "description": self.description
        }


@dataclass
class TrainingJob:
    """训练任务"""
    job_id: str
    agent_id: str
    status: TrainingStatus
    config: Dict[str, Any]
    created_at: float
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    model_version: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "job_id": self.job_id,
            "agent_id": self.agent_id,
            "status": self.status.value,
            "config": self.config,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "result": self.result,
            "error": self.error,
            "model_version": self.model_version
        }


class ModelRegistry:
    """模型注册表"""
    
    def __init__(self, base_path: str = "./models"):
        self.base_path = base_path
        self._versions: Dict[str, List[ModelVersion]] = {}
        self._active_versions: Dict[str, str] = {}
        
        os.makedirs(base_path, exist_ok=True)
    
    def register_version(
        self,
        agent_id: str,
        model_path: str,
        metrics: Dict[str, float],
        parent_version: Optional[str] = None,
        description: str = ""
    ) -> ModelVersion:
        """注册新模型版本"""
        version_id = f"v{int(time.time() * 1000)}"
        
        version = ModelVersion(
            version_id=version_id,
            agent_id=agent_id,
            model_path=model_path,
            created_at=time.time(),
            metrics=metrics,
            parent_version=parent_version,
            description=description
        )
        
        if agent_id not in self._versions:
            self._versions[agent_id] = []
        
        self._versions[agent_id].append(version)
        
        return version
    
    def get_version(self, agent_id: str, version_id: str) -> Optional[ModelVersion]:
        """获取指定版本"""
        versions = self._versions.get(agent_id, [])
        for v in versions:
            if v.version_id == version_id:
                return v
        return None
    
    def get_latest_version(self, agent_id: str) -> Optional[ModelVersion]:
        """获取最新版本"""
        versions = self._versions.get(agent_id, [])
        if not versions:
            return None
        return versions[-1]
    
    def get_active_version(self, agent_id: str) -> Optional[ModelVersion]:
        """获取当前激活版本"""
        active_id = self._active_versions.get(agent_id)
        if not active_id:
            return self.get_latest_version(agent_id)
        return self.get_version(agent_id, active_id)
    
    def activate_version(self, agent_id: str, version_id: str) -> bool:
        """激活指定版本"""
        version = self.get_version(agent_id, version_id)
        if not version:
            return False
        
        if agent_id in self._active_versions:
            old_version_id = self._active_versions[agent_id]
            old_version = self.get_version(agent_id, old_version_id)
            if old_version:
                old_version.status = DeploymentStatus.DEPRECATED
        
        version.status = DeploymentStatus.ACTIVE
        self._active_versions[agent_id] = version_id
        
        return True
    
    def rollback(self, agent_id: str) -> Optional[str]:
        """回滚到上一个版本"""
        versions = self._versions.get(agent_id, [])
        if len(versions) < 2:
            return None
        
        current_id = self._active_versions.get(agent_id)
        if not current_id:
            return None
        
        current_idx = -1
        for i, v in enumerate(versions):
            if v.version_id == current_id:
                current_idx = i
                break
        
        if current_idx <= 0:
            return None
        
        current_version = versions[current_idx]
        current_version.status = DeploymentStatus.ROLLED_BACK
        
        previous_version = versions[current_idx - 1]
        previous_version.status = DeploymentStatus.ACTIVE
        self._active_versions[agent_id] = previous_version.version_id
        
        return previous_version.version_id
    
    def list_versions(self, agent_id: str, limit: int = 10) -> List[ModelVersion]:
        """列出所有版本"""
        versions = self._versions.get(agent_id, [])
        return versions[-limit:]
    
    def cleanup_old_versions(
        self,
        agent_id: str,
        keep_count: int = 5
    ) -> int:
        """清理旧版本"""
        versions = self._versions.get(agent_id, [])
        if len(versions) <= keep_count:
            return 0
        
        to_remove = versions[:-keep_count]
        removed_count = 0
        
        for version in to_remove:
            if version.status != DeploymentStatus.ACTIVE:
                try:
                    if os.path.exists(version.model_path):
                        os.remove(version.model_path)
                    removed_count += 1
                except Exception:
                    pass
        
        self._versions[agent_id] = versions[-keep_count:]
        
        return removed_count


class ABTestingManager:
    """A/B测试管理器"""
    
    def __init__(self):
        self._experiments: Dict[str, Dict[str, Any]] = {}
        self._traffic_split: Dict[str, Dict[str, float]] = {}
        self._results: Dict[str, Dict[str, List[float]]] = {}
    
    def create_experiment(
        self,
        experiment_id: str,
        agent_id: str,
        version_a: str,
        version_b: str,
        traffic_split: float = 0.5
    ) -> Dict[str, Any]:
        """创建A/B测试实验"""
        experiment = {
            "experiment_id": experiment_id,
            "agent_id": agent_id,
            "version_a": version_a,
            "version_b": version_b,
            "traffic_split": traffic_split,
            "status": "running",
            "created_at": time.time(),
            "metrics_a": [],
            "metrics_b": []
        }
        
        self._experiments[experiment_id] = experiment
        self._traffic_split[agent_id] = {
            version_a: traffic_split,
            version_b: 1 - traffic_split
        }
        self._results[experiment_id] = {
            "a": [],
            "b": []
        }
        
        return experiment
    
    def get_version_for_request(
        self,
        agent_id: str
    ) -> Optional[str]:
        """为请求分配版本"""
        if agent_id not in self._traffic_split:
            return None
        
        splits = self._traffic_split[agent_id]
        versions = list(splits.keys())
        probabilities = list(splits.values())
        
        import random
        return random.choices(versions, weights=probabilities, k=1)[0]
    
    def record_result(
        self,
        experiment_id: str,
        version: str,
        metric_value: float
    ):
        """记录实验结果"""
        if experiment_id not in self._results:
            return
        
        bucket = "a" if version == self._experiments[experiment_id]["version_a"] else "b"
        self._results[experiment_id][bucket].append(metric_value)
    
    def get_experiment_stats(
        self,
        experiment_id: str
    ) -> Optional[Dict[str, Any]]:
        """获取实验统计"""
        if experiment_id not in self._experiments:
            return None
        
        experiment = self._experiments[experiment_id]
        results = self._results[experiment_id]
        
        import numpy as np
        
        stats = {
            "experiment_id": experiment_id,
            "status": experiment["status"],
            "sample_size_a": len(results["a"]),
            "sample_size_b": len(results["b"]),
            "mean_a": np.mean(results["a"]) if results["a"] else 0,
            "mean_b": np.mean(results["b"]) if results["b"] else 0,
            "std_a": np.std(results["a"]) if len(results["a"]) > 1 else 0,
            "std_b": np.std(results["b"]) if len(results["b"]) > 1 else 0
        }
        
        if results["a"] and results["b"]:
            stats["improvement"] = (stats["mean_b"] - stats["mean_a"]) / stats["mean_a"] if stats["mean_a"] != 0 else 0
        
        return stats
    
    def end_experiment(
        self,
        experiment_id: str,
        winner: Optional[str] = None
    ) -> Dict[str, Any]:
        """结束实验"""
        if experiment_id not in self._experiments:
            return {"status": "not_found"}
        
        experiment = self._experiments[experiment_id]
        experiment["status"] = "completed"
        experiment["winner"] = winner
        experiment["completed_at"] = time.time()
        
        agent_id = experiment["agent_id"]
        if agent_id in self._traffic_split:
            del self._traffic_split[agent_id]
        
        return experiment


class LearningEngine:
    """学习引擎调度器"""
    
    def __init__(
        self,
        model_base_path: str = "./models",
        min_experiences: int = 100,
        training_interval: int = 3600,
        reflection_interval: int = 86400
    ):
        self.model_registry = ModelRegistry(model_base_path)
        self.ab_testing = ABTestingManager()
        
        self.min_experiences = min_experiences
        self.training_interval = training_interval
        self.reflection_interval = reflection_interval
        
        self._trainers: Dict[str, PPOTrainer] = {}
        self._training_jobs: Dict[str, TrainingJob] = {}
        self._job_queue: asyncio.Queue = asyncio.Queue()
        
        self._running = False
        self._scheduler_task: Optional[asyncio.Task] = None
        
        self._agent_callbacks: Dict[str, Callable] = {}
        
        self._metrics_history: Dict[str, List[Dict]] = {}
    
    def register_agent(
        self,
        agent_id: str,
        config: Optional[PPOConfig] = None,
        on_model_update: Optional[Callable] = None
    ):
        """注册智能体"""
        self._trainers[agent_id] = PPOTrainer(config or PPOConfig())
        
        if on_model_update:
            self._agent_callbacks[agent_id] = on_model_update
    
    async def start(self):
        """启动学习引擎"""
        if self._running:
            return
        
        self._running = True
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        
        asyncio.create_task(self._job_worker())
        
        print("[LearningEngine] 学习引擎已启动")
    
    async def stop(self):
        """停止学习引擎"""
        self._running = False
        
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
        
        print("[LearningEngine] 学习引擎已停止")
    
    async def _scheduler_loop(self):
        """调度器主循环"""
        last_training: Dict[str, float] = {}
        last_reflection: Dict[str, float] = {}
        
        while self._running:
            try:
                for agent_id in self._trainers:
                    now = time.time()
                    
                    if agent_id not in last_training:
                        last_training[agent_id] = now
                    
                    if now - last_training[agent_id] >= self.training_interval:
                        await self._check_and_schedule_training(agent_id)
                        last_training[agent_id] = now
                    
                    if agent_id not in last_reflection:
                        last_reflection[agent_id] = now
                    
                    if now - last_reflection[agent_id] >= self.reflection_interval:
                        await self._schedule_reflection(agent_id)
                        last_reflection[agent_id] = now
                
                await asyncio.sleep(60)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[LearningEngine] 调度器错误: {e}")
                await asyncio.sleep(60)
    
    async def _check_and_schedule_training(self, agent_id: str):
        """检查并调度训练"""
        stats = experience_collector.get_buffer_stats()
        
        if stats["size"] >= self.min_experiences:
            await self.schedule_training(agent_id)
    
    async def schedule_training(
        self,
        agent_id: str,
        priority: int = 1
    ) -> str:
        """调度训练任务"""
        job_id = f"train_{agent_id}_{int(time.time() * 1000)}"
        
        job = TrainingJob(
            job_id=job_id,
            agent_id=agent_id,
            status=TrainingStatus.PENDING,
            config={
                "priority": priority,
                "min_experiences": self.min_experiences
            },
            created_at=time.time()
        )
        
        self._training_jobs[job_id] = job
        await self._job_queue.put((priority, job_id))
        
        print(f"[LearningEngine] 已调度训练任务: {job_id}")
        
        return job_id
    
    async def _schedule_reflection(self, agent_id: str):
        """调度反思任务"""
        try:
            result = await reflection_module.scheduled_reflection(
                agent_id,
                timedelta(seconds=self.reflection_interval)
            )
            
            print(f"[LearningEngine] 完成定时反思: {result.analysis}")
            
            if result.suggestions:
                await self._process_reflection_suggestions(agent_id, result)
                
        except Exception as e:
            print(f"[LearningEngine] 反思任务失败: {e}")
    
    async def _process_reflection_suggestions(
        self,
        agent_id: str,
        result: ReflectionResult
    ):
        """处理反思建议"""
        if result.training_samples:
            trainer = self._trainers.get(agent_id)
            if trainer:
                for sample in result.training_samples:
                    print(f"[LearningEngine] 处理训练样本: {sample.get('type', 'unknown')}")
    
    async def _job_worker(self):
        """训练任务工作器"""
        while self._running:
            try:
                try:
                    priority, job_id = await asyncio.wait_for(
                        self._job_queue.get(),
                        timeout=10.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                job = self._training_jobs.get(job_id)
                if not job:
                    continue
                
                await self._execute_training_job(job)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[LearningEngine] 任务执行错误: {e}")
    
    async def _execute_training_job(self, job: TrainingJob):
        """执行训练任务"""
        job.status = TrainingStatus.RUNNING
        job.started_at = time.time()
        
        try:
            trainer = self._trainers.get(job.agent_id)
            if not trainer:
                raise ValueError(f"未注册的智能体: {job.agent_id}")
            
            experiences = await experience_collector.get_experiences_by_agent(
                job.agent_id,
                limit=500
            )
            
            if len(experiences) < self.min_experiences:
                job.status = TrainingStatus.CANCELLED
                job.error = f"经验不足: {len(experiences)} < {self.min_experiences}"
                return
            
            result = trainer.train_from_experiences(experiences)
            
            job.result = result
            job.status = TrainingStatus.COMPLETED
            job.completed_at = time.time()
            
            model_path = await self._save_model(job.agent_id, trainer, result)
            
            version = self.model_registry.register_version(
                agent_id=job.agent_id,
                model_path=model_path,
                metrics=result,
                description=f"训练任务 {job.job_id}"
            )
            
            job.model_version = version.version_id
            
            await self._deploy_model(job.agent_id, version)
            
            print(f"[LearningEngine] 训练任务完成: {job.job_id}, 结果: {result}")
            
        except Exception as e:
            job.status = TrainingStatus.FAILED
            job.error = str(e)
            job.completed_at = time.time()
            print(f"[LearningEngine] 训练任务失败: {job.job_id}, 错误: {e}")
    
    async def _save_model(
        self,
        agent_id: str,
        trainer: PPOTrainer,
        metrics: Dict[str, float]
    ) -> str:
        """保存模型"""
        model_dir = os.path.join(self.model_registry.base_path, agent_id)
        os.makedirs(model_dir, exist_ok=True)
        
        model_path = os.path.join(
            model_dir,
            f"model_{int(time.time() * 1000)}.pt"
        )
        
        trainer.save_model(model_path)
        
        return model_path
    
    async def _deploy_model(
        self,
        agent_id: str,
        version: ModelVersion
    ):
        """部署模型"""
        self.model_registry.activate_version(agent_id, version.version_id)
        
        if agent_id in self._agent_callbacks:
            callback = self._agent_callbacks[agent_id]
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(version)
                else:
                    callback(version)
            except Exception as e:
                print(f"[LearningEngine] 模型更新回调失败: {e}")
    
    async def trigger_immediate_training(
        self,
        agent_id: str
    ) -> str:
        """立即触发训练"""
        return await self.schedule_training(agent_id, priority=10)
    
    async def rollback_model(
        self,
        agent_id: str
    ) -> Optional[str]:
        """回滚模型"""
        previous_version_id = self.model_registry.rollback(agent_id)
        
        if previous_version_id:
            print(f"[LearningEngine] 已回滚到版本: {previous_version_id}")
            
            previous_version = self.model_registry.get_version(agent_id, previous_version_id)
            if previous_version:
                trainer = self._trainers.get(agent_id)
                if trainer:
                    try:
                        trainer.load_model(previous_version.model_path)
                    except Exception as e:
                        print(f"[LearningEngine] 加载回滚模型失败: {e}")
        
        return previous_version_id
    
    def create_ab_experiment(
        self,
        agent_id: str,
        version_a: str,
        version_b: str,
        traffic_split: float = 0.5
    ) -> Dict[str, Any]:
        """创建A/B测试"""
        experiment_id = f"exp_{agent_id}_{int(time.time() * 1000)}"
        
        return self.ab_testing.create_experiment(
            experiment_id=experiment_id,
            agent_id=agent_id,
            version_a=version_a,
            version_b=version_b,
            traffic_split=traffic_split
        )
    
    def get_model_for_inference(
        self,
        agent_id: str,
        use_ab_test: bool = False
    ) -> Optional[ModelVersion]:
        """获取推理用模型"""
        if use_ab_test:
            version_id = self.ab_testing.get_version_for_request(agent_id)
            if version_id:
                return self.model_registry.get_version(agent_id, version_id)
        
        return self.model_registry.get_active_version(agent_id)
    
    def get_training_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """获取训练状态"""
        job = self._training_jobs.get(job_id)
        if not job:
            return None
        
        return job.to_dict()
    
    def get_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """获取智能体学习状态"""
        trainer = self._trainers.get(agent_id)
        trainer_summary = trainer.get_training_summary() if trainer else {}
        
        active_version = self.model_registry.get_active_version(agent_id)
        version_history = self.model_registry.list_versions(agent_id)
        
        buffer_stats = experience_collector.get_buffer_stats()
        
        reflection_summary = reflection_module.get_reflection_summary(agent_id)
        
        return {
            "agent_id": agent_id,
            "trainer": trainer_summary,
            "active_model": active_version.to_dict() if active_version else None,
            "model_versions": len(version_history),
            "experience_buffer": buffer_stats,
            "reflection": reflection_summary
        }
    
    def get_global_status(self) -> Dict[str, Any]:
        """获取全局状态"""
        return {
            "running": self._running,
            "registered_agents": list(self._trainers.keys()),
            "pending_jobs": self._job_queue.qsize(),
            "total_jobs": len(self._training_jobs),
            "recent_jobs": [
                job.to_dict() for job in
                sorted(self._training_jobs.values(), key=lambda j: j.created_at, reverse=True)[:10]
            ]
        }


learning_engine = LearningEngine()
