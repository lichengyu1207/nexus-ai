"""
多智能体联合训练系统
Multi-Agent Joint Training System

实现多智能体协同优化训练
"""

import os
import json
import logging
import time
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import random

logger = logging.getLogger(__name__)


@dataclass
class CollaborativeTask:
    """协同任务"""
    task_id: str
    task_description: str
    task_type: str
    required_agents: List[str]
    agent_assignments: Dict[str, str]
    execution_order: List[str]
    success: bool = False
    total_time: float = 0.0
    agent_results: Dict[str, Dict] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class MultiAgentTrainingConfig:
    """多智能体训练配置"""
    learning_rate: float = 0.0001
    batch_size: int = 32
    epochs: int = 10
    gamma: float = 0.99
    epsilon: float = 0.1
    target_update_freq: int = 100
    buffer_size: int = 10000
    model_save_dir: str = "./models/multi_agent"
    use_centralized_training: bool = True


class MultiAgentTrainer:
    """
    多智能体联合训练器
    
    训练目标：
    1. 优化智能体协同效率
    2. 降低通信延迟
    3. 提高任务完成率
    4. 减少资源消耗
    """
    
    AGENT_TYPES = [
        "zhongshu",
        "menshang",
        "shangshu",
        "li_bu",
        "hu_bu",
        "li_bu_consult",
        "bing_bu",
        "xing_bu",
        "gong_bu",
    ]
    
    def __init__(self, config: Optional[MultiAgentTrainingConfig] = None):
        self.config = config or MultiAgentTrainingConfig()
        os.makedirs(self.config.model_save_dir, exist_ok=True)
        
        self.training_data: List[CollaborativeTask] = []
        self.validation_data: List[CollaborativeTask] = []
        
        self.agent_models: Dict[str, Any] = {}
        self.shared_memory: Dict[str, List] = defaultdict(list)
        
        self.training_history: List[Dict] = []
        
        self.collaboration_patterns: Dict[str, Dict] = {
            "valuation_analysis": {
                "agents": ["zhongshu", "bing_bu", "gong_bu"],
                "order": ["zhongshu", "bing_bu", "gong_bu"],
                "timeout": 30.0,
            },
            "market_report": {
                "agents": ["zhongshu", "bing_bu", "gong_bu", "li_bu_consult"],
                "order": ["zhongshu", "bing_bu", "gong_bu", "li_bu_consult"],
                "timeout": 45.0,
            },
            "risk_assessment": {
                "agents": ["zhongshu", "xing_bu", "gong_bu"],
                "order": ["zhongshu", "xing_bu", "gong_bu"],
                "timeout": 25.0,
            },
            "investment_consultation": {
                "agents": ["zhongshu", "gong_bu", "li_bu_consult"],
                "order": ["zhongshu", "gong_bu", "li_bu_consult"],
                "timeout": 35.0,
            },
        }
        
        self.agent_capabilities: Dict[str, List[str]] = {
            "zhongshu": ["task_decomposition", "scheduling", "coordination"],
            "menshang": ["compliance_check", "audit", "approval"],
            "shangshu": ["execution", "resource_management", "reporting"],
            "li_bu": ["team_management", "resource_allocation", "training"],
            "hu_bu": ["points_management", "asset_tracking", "statistics"],
            "li_bu_consult": ["consultation", "response_generation", "user_guidance"],
            "bing_bu": ["data_collection", "validation", "update"],
            "xing_bu": ["risk_assessment", "anomaly_detection", "compliance"],
            "gong_bu": ["analysis", "report_generation", "visualization"],
        }
        
        self.performance_metrics: Dict[str, Dict] = defaultdict(lambda: {
            "success_count": 0,
            "failure_count": 0,
            "total_time": 0.0,
            "avg_reward": 0.0,
        })
        
        logger.info("MultiAgentTrainer initialized")
    
    def load_training_data(self, data: List[Dict]):
        """加载训练数据"""
        examples = []
        for item in data:
            example = CollaborativeTask(
                task_id=item.get("task_id", ""),
                task_description=item.get("task_description", ""),
                task_type=item.get("task_type", ""),
                required_agents=item.get("required_agents", []),
                agent_assignments=item.get("agent_assignments", {}),
                execution_order=item.get("execution_order", []),
                success=item.get("success", False),
                total_time=item.get("total_time", 0.0),
                agent_results=item.get("agent_results", {}),
            )
            examples.append(example)
        
        split_idx = int(len(examples) * 0.85)
        self.training_data = examples[:split_idx]
        self.validation_data = examples[split_idx:]
        
        logger.info(f"Loaded {len(self.training_data)} training tasks, {len(self.validation_data)} validation tasks")
    
    def train(self) -> Dict:
        """训练多智能体系统"""
        if not self.training_data:
            logger.warning("No training data available")
            return {"success": False, "error": "No training data"}
        
        logger.info(f"Starting multi-agent training with {len(self.training_data)} tasks")
        
        total_reward = 0.0
        successful_tasks = 0
        
        for task in self.training_data:
            task_reward = self._calculate_task_reward(task)
            total_reward += task_reward
            
            if task.success:
                successful_tasks += 1
            
            self._update_agent_models(task, task_reward)
        
        avg_reward = total_reward / len(self.training_data)
        success_rate = successful_tasks / len(self.training_data)
        
        training_result = {
            "success": True,
            "total_tasks": len(self.training_data),
            "successful_tasks": successful_tasks,
            "success_rate": success_rate,
            "avg_reward": avg_reward,
        }
        
        self.training_history.append({
            "timestamp": time.time(),
            "tasks": len(self.training_data),
            "success_rate": success_rate,
            "avg_reward": avg_reward,
        })
        
        logger.info(f"Training completed: success_rate={success_rate:.2%}, avg_reward={avg_reward:.4f}")
        return training_result
    
    def _calculate_task_reward(self, task: CollaborativeTask) -> float:
        """计算任务奖励"""
        reward = 0.0
        
        if task.success:
            reward += 1.0
        else:
            reward -= 0.5
        
        if task.total_time < 10:
            reward += 0.5
        elif task.total_time > 30:
            reward -= 0.3
        
        agent_count = len(task.required_agents)
        if agent_count <= 3:
            reward += 0.2
        elif agent_count > 5:
            reward -= 0.1
        
        failed_agents = sum(
            1 for r in task.agent_results.values()
            if not r.get("success", False)
        )
        if failed_agents == 0:
            reward += 0.3
        else:
            reward -= failed_agents * 0.2
        
        return reward
    
    def _update_agent_models(self, task: CollaborativeTask, reward: float):
        """更新智能体模型"""
        for agent_type in task.required_agents:
            if agent_type not in self.agent_models:
                self.agent_models[agent_type] = {
                    "total_tasks": 0,
                    "total_reward": 0.0,
                    "success_count": 0,
                }
            
            self.agent_models[agent_type]["total_tasks"] += 1
            self.agent_models[agent_type]["total_reward"] += reward
            
            agent_result = task.agent_results.get(agent_type, {})
            if agent_result.get("success", False):
                self.agent_models[agent_type]["success_count"] += 1
    
    def allocate_task(
        self,
        task_description: str,
        task_type: str,
        context: Optional[Dict] = None
    ) -> Dict:
        """分配任务"""
        pattern = self.collaboration_patterns.get(task_type)
        
        if pattern:
            agents = pattern["agents"]
            order = pattern["order"]
            timeout = pattern["timeout"]
        else:
            agents = self._select_agents_for_task(task_description)
            order = agents
            timeout = 30.0
        
        assignments = {}
        for agent in agents:
            capabilities = self.agent_capabilities.get(agent, [])
            assignments[agent] = random.choice(capabilities) if capabilities else "execute"
        
        result = {
            "task_id": f"task_{int(time.time() * 1000)}",
            "task_description": task_description,
            "task_type": task_type,
            "agents": agents,
            "execution_order": order,
            "timeout": timeout,
            "assignments": assignments,
        }
        
        logger.debug(f"Allocated task: type={task_type}, agents={agents}")
        return result
    
    def _select_agents_for_task(self, task_description: str) -> List[str]:
        """为任务选择智能体"""
        task_lower = task_description.lower()
        
        agents = ["zhongshu"]
        
        if any(kw in task_lower for kw in ["估值", "分析", "报告"]):
            agents.append("gong_bu")
        
        if any(kw in task_lower for kw in ["数据", "采集", "收集"]):
            agents.append("bing_bu")
        
        if any(kw in task_lower for kw in ["咨询", "建议", "解答"]):
            agents.append("li_bu_consult")
        
        if any(kw in task_lower for kw in ["风险", "合规", "审核"]):
            agents.append("xing_bu")
        
        if any(kw in task_lower for kw in ["积分", "资产"]):
            agents.append("hu_bu")
        
        return agents
    
    async def execute_collaborative_task(
        self,
        task_description: str,
        task_type: str,
        context: Optional[Dict] = None
    ) -> Dict:
        """执行协同任务"""
        allocation = self.allocate_task(task_description, task_type, context)
        
        start_time = time.time()
        agent_results = {}
        
        for agent_type in allocation["execution_order"]:
            agent_result = await self._execute_agent_task(
                agent_type,
                task_description,
                context
            )
            agent_results[agent_type] = agent_result
            
            if not agent_result.get("success", False):
                logger.warning(f"Agent {agent_type} failed in task")
        
        total_time = time.time() - start_time
        success = all(r.get("success", False) for r in agent_results.values())
        
        task = CollaborativeTask(
            task_id=allocation["task_id"],
            task_description=task_description,
            task_type=task_type,
            required_agents=allocation["agents"],
            agent_assignments=allocation["assignments"],
            execution_order=allocation["execution_order"],
            success=success,
            total_time=total_time,
            agent_results=agent_results,
        )
        
        self.training_data.append(task)
        
        result = {
            "task_id": allocation["task_id"],
            "success": success,
            "total_time": total_time,
            "agent_results": agent_results,
        }
        
        logger.info(f"Task completed: id={allocation['task_id']}, success={success}, time={total_time:.2f}s")
        return result
    
    async def _execute_agent_task(
        self,
        agent_type: str,
        task_description: str,
        context: Optional[Dict]
    ) -> Dict:
        """执行单个智能体任务"""
        await asyncio.sleep(random.uniform(0.1, 0.5))
        
        success_probability = 0.9
        if agent_type in self.agent_models:
            model = self.agent_models[agent_type]
            if model["total_tasks"] > 0:
                success_probability = model["success_count"] / model["total_tasks"]
        
        success = random.random() < success_probability
        
        result = {
            "agent_type": agent_type,
            "success": success,
            "execution_time": random.uniform(0.5, 3.0),
            "output": f"Agent {agent_type} processed task" if success else None,
            "error": None if success else "Execution failed",
        }
        
        return result
    
    def evaluate(self, test_data: List[Dict]) -> Dict:
        """评估系统"""
        tasks = []
        for item in test_data:
            task = CollaborativeTask(
                task_id=item.get("task_id", ""),
                task_description=item.get("task_description", ""),
                task_type=item.get("task_type", ""),
                required_agents=item.get("required_agents", []),
                agent_assignments=item.get("agent_assignments", {}),
                execution_order=item.get("execution_order", []),
                success=item.get("success", False),
                total_time=item.get("total_time", 0.0),
                agent_results=item.get("agent_results", {}),
            )
            tasks.append(task)
        
        if not tasks:
            return {"error": "No test data"}
        
        success_count = sum(1 for t in tasks if t.success)
        success_rate = success_count / len(tasks)
        
        avg_time = sum(t.total_time for t in tasks) / len(tasks)
        
        agent_success_rates = defaultdict(lambda: {"success": 0, "total": 0})
        for task in tasks:
            for agent_type, result in task.agent_results.items():
                agent_success_rates[agent_type]["total"] += 1
                if result.get("success", False):
                    agent_success_rates[agent_type]["success"] += 1
        
        agent_metrics = {}
        for agent, stats in agent_success_rates.items():
            if stats["total"] > 0:
                agent_metrics[agent] = {
                    "success_rate": stats["success"] / stats["total"],
                    "total_tasks": stats["total"],
                }
        
        result = {
            "success_rate": success_rate,
            "avg_execution_time": avg_time,
            "total_tasks": len(tasks),
            "agent_metrics": agent_metrics,
        }
        
        logger.info(f"Evaluation result: success_rate={success_rate:.2%}")
        return result
    
    def get_statistics(self) -> Dict:
        """获取训练统计"""
        return {
            "training_data_count": len(self.training_data),
            "validation_data_count": len(self.validation_data),
            "agent_models": self.agent_models,
            "training_history": self.training_history,
            "collaboration_patterns": len(self.collaboration_patterns),
        }


_global_trainer: Optional[MultiAgentTrainer] = None


def get_multi_agent_trainer() -> MultiAgentTrainer:
    """获取全局训练器实例"""
    global _global_trainer
    if _global_trainer is None:
        _global_trainer = MultiAgentTrainer()
    return _global_trainer
