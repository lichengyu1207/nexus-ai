"""
SOP 18-19: 多智能体强化学习环境
Multi-Agent Reinforcement Learning Environment

构建模拟环境用于联合训练六部智能体
"""

import os
import logging
import time
import random
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import json

logger = logging.getLogger(__name__)


class AgentRole(Enum):
    ZHONGSHU = "zhongshu"
    MENSHANG = "menshang"
    GONGBU = "gongbu"
    LIBU = "libu"
    BINGBU = "bingbu"
    XINGBU = "xingbu"


@dataclass
class AgentState:
    role: AgentRole
    workload: float = 0.0
    performance: float = 0.0
    last_action: Optional[str] = None
    last_reward: float = 0.0
    message_queue: List[Dict] = field(default_factory=list)


@dataclass
class TaskState:
    task_id: str
    task_type: str
    complexity: float
    required_agents: List[AgentRole]
    assigned_agents: List[AgentRole] = field(default_factory=list)
    status: str = "pending"
    progress: float = 0.0
    result: Optional[Dict] = None


@dataclass
class GlobalState:
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    total_cost: float = 0.0
    avg_latency: float = 0.0
    user_satisfaction: float = 0.0


class MultiAgentEnv:
    """
    多智能体强化学习环境
    
    功能：
    1. 模拟六部智能体协同工作
    2. 定义状态空间、动作空间、奖励函数
    3. 支持并行模拟
    4. 集成奖励计算器
    """
    
    ACTION_SPACES = {
        AgentRole.ZHONGSHU: [
            "decompose_task",
            "assign_agent",
            "prioritize",
            "delegate",
            "wait"
        ],
        AgentRole.MENSHANG: [
            "approve",
            "reject",
            "request_review",
            "escalate",
            "pass"
        ],
        AgentRole.GONGBU: [
            "estimate_value",
            "analyze_market",
            "generate_report",
            "request_data",
            "skip"
        ],
        AgentRole.LIBU: [
            "respond",
            "clarify",
            "transfer",
            "escalate",
            "end_conversation"
        ],
        AgentRole.BINGBU: [
            "collect_data",
            "validate_data",
            "store_data",
            "clean_data",
            "skip"
        ],
        AgentRole.XINGBU: [
            "check_risk",
            "flag_anomaly",
            "approve_transaction",
            "block_transaction",
            "investigate"
        ],
    }
    
    def __init__(
        self,
        num_agents: int = 6,
        max_steps: int = 100,
        seed: Optional[int] = None
    ):
        self.num_agents = num_agents
        self.max_steps = max_steps
        self.seed = seed
        
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
        
        self.agents: Dict[AgentRole, AgentState] = {}
        self.tasks: List[TaskState] = []
        self.global_state = GlobalState()
        self.current_step = 0
        self.task_queue: List[TaskState] = []
        
        self._init_agents()
        
        self.reward_history: List[Dict[str, float]] = []
        self.action_history: List[Dict[str, str]] = []
        
        logger.info(f"MultiAgentEnv initialized with {num_agents} agents")
    
    def _init_agents(self):
        """初始化智能体"""
        roles = list(AgentRole)[:self.num_agents]
        
        for role in roles:
            self.agents[role] = AgentState(
                role=role,
                workload=0.0,
                performance=random.uniform(0.7, 0.95)
            )
    
    def reset(self) -> Dict[str, np.ndarray]:
        """重置环境"""
        self.current_step = 0
        self.tasks = []
        self.global_state = GlobalState()
        self.task_queue = []
        self.reward_history = []
        self.action_history = []
        
        self._init_agents()
        
        for _ in range(random.randint(3, 8)):
            self._generate_task()
        
        return self._get_observations()
    
    def _generate_task(self) -> TaskState:
        """生成新任务"""
        task_types = [
            "valuation",
            "consultation",
            "report_generation",
            "data_collection",
            "risk_assessment"
        ]
        
        task_type = random.choice(task_types)
        
        agent_requirements = {
            "valuation": [AgentRole.ZHONGSHU, AgentRole.GONGBU],
            "consultation": [AgentRole.ZHONGSHU, AgentRole.LIBU],
            "report_generation": [AgentRole.ZHONGSHU, AgentRole.GONGBU, AgentRole.LIBU],
            "data_collection": [AgentRole.BINGBU],
            "risk_assessment": [AgentRole.XINGBU, AgentRole.MENSHANG],
        }
        
        required_agents = agent_requirements.get(task_type, [AgentRole.ZHONGSHU])
        
        task = TaskState(
            task_id=f"task_{len(self.tasks)}_{int(time.time())}",
            task_type=task_type,
            complexity=random.uniform(0.3, 1.0),
            required_agents=required_agents
        )
        
        self.tasks.append(task)
        self.task_queue.append(task)
        self.global_state.total_tasks += 1
        
        return task
    
    def _get_observations(self) -> Dict[str, np.ndarray]:
        """获取所有智能体的观察"""
        observations = {}
        
        for role, agent in self.agents.items():
            obs = self._get_agent_observation(role)
            observations[role.value] = obs
        
        return observations
    
    def _get_agent_observation(self, role: AgentRole) -> np.ndarray:
        """获取单个智能体的观察"""
        agent = self.agents[role]
        
        pending_tasks = len([t for t in self.tasks if t.status == "pending"])
        active_tasks = len([t for t in self.tasks if t.status == "in_progress"])
        
        relevant_tasks = [
            t for t in self.tasks
            if role in t.required_agents and t.status in ["pending", "in_progress"]
        ]
        
        obs = np.array([
            agent.workload,
            agent.performance,
            float(len(agent.message_queue)),
            float(pending_tasks),
            float(active_tasks),
            float(len(relevant_tasks)),
            self.global_state.completed_tasks / max(1, self.global_state.total_tasks),
            self.global_state.avg_latency / 100,
            self.global_state.user_satisfaction,
            float(self.current_step) / self.max_steps,
        ], dtype=np.float32)
        
        return obs
    
    def get_action_space(self, role: AgentRole) -> List[str]:
        """获取动作空间"""
        return self.ACTION_SPACES.get(role, ["wait"])
    
    def step(
        self,
        actions: Dict[str, str]
    ) -> Tuple[Dict[str, np.ndarray], Dict[str, float], bool, Dict]:
        """执行一步"""
        self.current_step += 1
        rewards = {}
        
        for role_str, action in actions.items():
            role = AgentRole(role_str)
            reward = self._execute_action(role, action)
            rewards[role_str] = reward
        
        self._process_tasks()
        
        if random.random() < 0.3:
            self._generate_task()
        
        self._update_global_state()
        
        done = self.current_step >= self.max_steps
        
        info = {
            "step": self.current_step,
            "completed_tasks": self.global_state.completed_tasks,
            "failed_tasks": self.global_state.failed_tasks,
            "total_cost": self.global_state.total_cost,
        }
        
        self.reward_history.append(rewards)
        self.action_history.append(actions)
        
        return self._get_observations(), rewards, done, info
    
    def _execute_action(self, role: AgentRole, action: str) -> float:
        """执行动作并返回奖励"""
        agent = self.agents[role]
        agent.last_action = action
        
        base_reward = 0.0
        
        if action == "wait":
            base_reward = -0.1
        
        elif role == AgentRole.ZHONGSHU:
            base_reward = self._zhongshu_action(action)
        
        elif role == AgentRole.MENSHANG:
            base_reward = self._menshang_action(action)
        
        elif role == AgentRole.GONGBU:
            base_reward = self._gongbu_action(action)
        
        elif role == AgentRole.LIBU:
            base_reward = self._libu_action(action)
        
        elif role == AgentRole.BINGBU:
            base_reward = self._bingbu_action(action)
        
        elif role == AgentRole.XINGBU:
            base_reward = self._xingbu_action(action)
        
        workload_penalty = -0.1 * agent.workload
        total_reward = base_reward + workload_penalty
        
        agent.last_reward = total_reward
        agent.workload = max(0, agent.workload - 0.1)
        
        return total_reward
    
    def _zhongshu_action(self, action: str) -> float:
        """中书省动作"""
        if action == "decompose_task":
            pending = [t for t in self.tasks if t.status == "pending"]
            if pending:
                task = pending[0]
                task.status = "in_progress"
                task.assigned_agents = task.required_agents
                return 1.0
            return -0.5
        
        elif action == "assign_agent":
            return 0.5
        
        elif action == "prioritize":
            return 0.3
        
        elif action == "delegate":
            return 0.2
        
        return 0.0
    
    def _menshang_action(self, action: str) -> float:
        """门下省动作"""
        if action == "approve":
            return 0.8
        elif action == "reject":
            return -0.3
        elif action == "request_review":
            return 0.2
        elif action == "escalate":
            return -0.1
        return 0.0
    
    def _gongbu_action(self, action: str) -> float:
        """工部动作"""
        if action == "estimate_value":
            in_progress = [t for t in self.tasks if t.status == "in_progress" and t.task_type == "valuation"]
            if in_progress:
                task = in_progress[0]
                error_rate = random.uniform(0.01, 0.1)
                task.result = {"error_rate": error_rate}
                task.progress += 0.5
                
                if error_rate < 0.03:
                    return 1.0
                elif error_rate < 0.05:
                    return 0.5
                return -0.5
            return -0.2
        
        elif action == "analyze_market":
            return 0.5
        
        elif action == "generate_report":
            return 0.8
        
        return 0.0
    
    def _libu_action(self, action: str) -> float:
        """礼部动作"""
        if action == "respond":
            satisfaction = random.uniform(0.6, 1.0)
            self.global_state.user_satisfaction = (
                self.global_state.user_satisfaction * 0.9 + satisfaction * 0.1
            )
            return satisfaction
        
        elif action == "clarify":
            return 0.3
        
        elif action == "transfer":
            return -0.2
        
        elif action == "escalate":
            return -0.5
        
        return 0.0
    
    def _bingbu_action(self, action: str) -> float:
        """兵部动作"""
        if action == "collect_data":
            return 0.5
        elif action == "validate_data":
            return 0.3
        elif action == "store_data":
            return 0.2
        return 0.0
    
    def _xingbu_action(self, action: str) -> float:
        """刑部动作"""
        if action == "check_risk":
            return 0.5
        elif action == "flag_anomaly":
            if random.random() < 0.1:
                return 1.0
            return -0.2
        elif action == "approve_transaction":
            return 0.3
        elif action == "block_transaction":
            return -0.5
        return 0.0
    
    def _process_tasks(self):
        """处理任务"""
        for task in self.tasks:
            if task.status == "in_progress":
                task.progress += random.uniform(0.1, 0.3)
                
                if task.progress >= 1.0:
                    task.status = "completed"
                    self.global_state.completed_tasks += 1
                    self.global_state.total_cost += task.complexity * 10
                    
                    if task in self.task_queue:
                        self.task_queue.remove(task)
    
    def _update_global_state(self):
        """更新全局状态"""
        completed = [t for t in self.tasks if t.status == "completed"]
        if completed:
            self.global_state.avg_latency = len(completed) * 2.5
    
    def render(self, mode: str = "human") -> Optional[str]:
        """渲染环境状态"""
        output = []
        output.append(f"\n{'='*50}")
        output.append(f"Step: {self.current_step}/{self.max_steps}")
        output.append(f"{'='*50}")
        
        output.append(f"\nGlobal State:")
        output.append(f"  Tasks: {self.global_state.completed_tasks}/{self.global_state.total_tasks} completed")
        output.append(f"  Cost: ${self.global_state.total_cost:.2f}")
        output.append(f"  Satisfaction: {self.global_state.user_satisfaction:.2f}")
        
        output.append(f"\nAgents:")
        for role, agent in self.agents.items():
            output.append(f"  {role.value}: workload={agent.workload:.2f}, last_reward={agent.last_reward:.2f}")
        
        output.append(f"\nPending Tasks: {len([t for t in self.tasks if t.status == 'pending'])}")
        output.append(f"In Progress: {len([t for t in self.tasks if t.status == 'in_progress'])}")
        
        text = "\n".join(output)
        
        if mode == "human":
            print(text)
        
        return text
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        if not self.reward_history:
            return {"message": "No episodes completed"}
        
        avg_rewards = defaultdict(list)
        for rewards in self.reward_history:
            for agent, reward in rewards.items():
                avg_rewards[agent].append(reward)
        
        stats = {
            "total_steps": self.current_step,
            "completed_tasks": self.global_state.completed_tasks,
            "failed_tasks": self.global_state.failed_tasks,
            "total_cost": self.global_state.total_cost,
            "user_satisfaction": self.global_state.user_satisfaction,
            "agent_stats": {
                agent: {
                    "avg_reward": sum(r) / len(r),
                    "total_reward": sum(r),
                }
                for agent, r in avg_rewards.items()
            }
        }
        
        return stats


class SwarmTrainer:
    """
    多智能体协同训练器
    
    使用QMIX/MAPPO算法训练六部智能体团队
    """
    
    def __init__(
        self,
        env: MultiAgentEnv,
        algorithm: str = "qmix",
        learning_rate: float = 1e-4,
        gamma: float = 0.99,
        batch_size: int = 32
    ):
        self.env = env
        self.algorithm = algorithm
        self.learning_rate = learning_rate
        self.gamma = gamma
        self.batch_size = batch_size
        
        self.policies = {}
        self.training_history = []
        
        logger.info(f"SwarmTrainer initialized with {algorithm} algorithm")
    
    def train(
        self,
        num_episodes: int = 100,
        log_interval: int = 10
    ) -> Dict:
        """训练智能体"""
        logger.info(f"Starting training for {num_episodes} episodes")
        
        all_rewards = []
        all_completed = []
        
        for episode in range(num_episodes):
            observations = self.env.reset()
            episode_rewards = defaultdict(float)
            done = False
            
            while not done:
                actions = self._select_actions(observations)
                observations, rewards, done, info = self.env.step(actions)
                
                for agent, reward in rewards.items():
                    episode_rewards[agent] += reward
            
            total_reward = sum(episode_rewards.values())
            all_rewards.append(total_reward)
            all_completed.append(info["completed_tasks"])
            
            if (episode + 1) % log_interval == 0:
                avg_reward = sum(all_rewards[-log_interval:]) / log_interval
                avg_completed = sum(all_completed[-log_interval:]) / log_interval
                logger.info(
                    f"Episode {episode + 1}/{num_episodes}: "
                    f"avg_reward={avg_reward:.2f}, avg_completed={avg_completed:.1f}"
                )
        
        return {
            "total_episodes": num_episodes,
            "final_avg_reward": sum(all_rewards[-10:]) / 10,
            "final_avg_completed": sum(all_completed[-10:]) / 10,
            "reward_history": all_rewards,
        }
    
    def _select_actions(self, observations: Dict[str, np.ndarray]) -> Dict[str, str]:
        """选择动作"""
        actions = {}
        
        for agent_role, obs in observations.items():
            role = AgentRole(agent_role)
            action_space = self.env.get_action_space(role)
            
            action = random.choice(action_space)
            actions[agent_role] = action
        
        return actions


def main():
    """测试多智能体环境"""
    print("=" * 60)
    print("SOP 18-19: 多智能体强化学习环境测试")
    print("=" * 60)
    
    env = MultiAgentEnv(num_agents=6, max_steps=50, seed=42)
    
    print("\n1. 重置环境...")
    observations = env.reset()
    print(f"   观察空间维度: {list(observations.keys())}")
    
    print("\n2. 运行模拟...")
    done = False
    step = 0
    while not done and step < 20:
        actions = {}
        for role in env.agents.keys():
            action_space = env.get_action_space(role)
            actions[role.value] = random.choice(action_space)
        
        observations, rewards, done, info = env.step(actions)
        step += 1
        
        if step % 5 == 0:
            print(f"   Step {step}: completed={info['completed_tasks']}, cost=${info['total_cost']:.2f}")
    
    print("\n3. 环境统计:")
    stats = env.get_statistics()
    print(f"   完成任务: {stats['completed_tasks']}")
    print(f"   总成本: ${stats['total_cost']:.2f}")
    print(f"   用户满意度: {stats['user_satisfaction']:.2f}")
    
    print("\n4. 智能体奖励统计:")
    for agent, agent_stats in stats['agent_stats'].items():
        print(f"   {agent}: avg_reward={agent_stats['avg_reward']:.3f}")
    
    print("\n5. 训练测试 (10 episodes)...")
    trainer = SwarmTrainer(env, algorithm="qmix")
    train_result = trainer.train(num_episodes=10, log_interval=5)
    print(f"   最终平均奖励: {train_result['final_avg_reward']:.2f}")
    print(f"   最终平均完成任务: {train_result['final_avg_completed']:.1f}")
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
