"""
智能体学习基类 - 支持强化学习、经验积累和自我改进
"""
import asyncio
import json
import logging
import random
import math
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from abc import ABC, abstractmethod
from collections import deque
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class Experience:
    state: Dict[str, Any]
    action: Dict[str, Any]
    reward: float
    next_state: Dict[str, Any]
    done: bool
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict = field(default_factory=dict)


@dataclass
class AgentRequest:
    request_id: str
    input_data: Any
    memories: List[Dict] = field(default_factory=list)
    context: Dict = field(default_factory=dict)
    persona: str = "zhouyu"
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AgentResponse:
    request_id: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    metadata: Dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    reward: float = 0.0


class PolicyNetwork:
    """
    策略网络 - 用于决策
    简化版本，使用神经网络模拟
    """
    
    def __init__(self, state_dim: int = 128, action_dim: int = 32, hidden_dim: int = 64):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.hidden_dim = hidden_dim
        
        self.weights1 = np.random.randn(state_dim, hidden_dim) * 0.1
        self.bias1 = np.zeros(hidden_dim)
        self.weights2 = np.random.randn(hidden_dim, action_dim) * 0.1
        self.bias2 = np.zeros(action_dim)
        
        self.learning_rate = 0.001
    
    def forward(self, state: np.ndarray) -> np.ndarray:
        if state.shape[0] != self.state_dim:
            state = np.pad(state, (0, self.state_dim - state.shape[0]), mode='constant')
        
        hidden = np.maximum(0, np.dot(state[:self.state_dim], self.weights1) + self.bias1)
        logits = np.dot(hidden, self.weights2) + self.bias2
        probs = np.exp(logits) / np.sum(np.exp(logits))
        return probs
    
    def get_action(self, state: np.ndarray, deterministic: bool = False) -> int:
        probs = self.forward(state)
        if deterministic:
            return np.argmax(probs)
        return np.random.choice(len(probs), p=probs)
    
    def update(self, states: np.ndarray, actions: np.ndarray, advantages: np.ndarray):
        batch_size = len(states)
        
        for i in range(batch_size):
            state = states[i]
            action = actions[i]
            advantage = advantages[i]
            
            probs = self.forward(state)
            grad = -probs
            grad[action] += 1.0
            grad *= advantage
            
            hidden = np.maximum(0, np.dot(state[:self.state_dim], self.weights1) + self.bias1)
            
            self.weights2 -= self.learning_rate * np.outer(hidden, grad)
            self.bias2 -= self.learning_rate * grad
            
            grad_hidden = np.dot(grad, self.weights2.T) * (hidden > 0)
            self.weights1 -= self.learning_rate * np.outer(state[:self.state_dim], grad_hidden)
            self.bias1 -= self.learning_rate * grad_hidden


class ValueNetwork:
    """
    价值网络 - 评估状态价值
    """
    
    def __init__(self, state_dim: int = 128, hidden_dim: int = 64):
        self.state_dim = state_dim
        self.hidden_dim = hidden_dim
        
        self.weights1 = np.random.randn(state_dim, hidden_dim) * 0.1
        self.bias1 = np.zeros(hidden_dim)
        self.weights2 = np.random.randn(hidden_dim, 1) * 0.1
        self.bias2 = np.zeros(1)
        
        self.learning_rate = 0.001
    
    def forward(self, state: np.ndarray) -> float:
        if state.shape[0] != self.state_dim:
            state = np.pad(state, (0, self.state_dim - state.shape[0]), mode='constant')
        
        hidden = np.maximum(0, np.dot(state[:self.state_dim], self.weights1) + self.bias1)
        value = np.dot(hidden, self.weights2) + self.bias2
        return float(value[0])
    
    def update(self, states: np.ndarray, targets: np.ndarray):
        batch_size = len(states)
        
        for i in range(batch_size):
            state = states[i]
            target = targets[i]
            
            value = self.forward(state)
            error = value - target
            
            hidden = np.maximum(0, np.dot(state[:self.state_dim], self.weights1) + self.bias1)
            
            grad = np.array([error])
            self.weights2 -= self.learning_rate * np.outer(hidden, grad)
            self.bias2 -= self.learning_rate * grad
            
            grad_hidden = np.dot(grad, self.weights2.T) * (hidden > 0)
            self.weights1 -= self.learning_rate * np.outer(state[:self.state_dim], grad_hidden)
            self.bias1 -= self.learning_rate * grad_hidden


class LearningAgent(ABC):
    """
    学习型智能体基类
    支持强化学习、经验积累和自我改进
    """
    
    def __init__(
        self,
        name: str,
        description: str = "",
        state_dim: int = 128,
        action_dim: int = 32,
        buffer_size: int = 10000
    ):
        self.name = name
        self.description = description
        self._initialized = False
        
        self.policy_network = PolicyNetwork(state_dim, action_dim)
        self.value_network = ValueNetwork(state_dim)
        
        self.experience_buffer: deque = deque(maxlen=buffer_size)
        
        self.total_reward = 0.0
        self.episode_count = 0
        self.success_count = 0
        self.failure_count = 0
        
        self.learning_enabled = True
        self.gamma = 0.99
        self.gae_lambda = 0.95
        self.batch_size = 32
        self.update_epochs = 4
    
    async def initialize(self):
        if not self._initialized:
            await self._setup()
            self._initialized = True
            logger.info(f"Learning Agent '{self.name}' initialized")
    
    async def _setup(self):
        pass
    
    @abstractmethod
    async def handle_message(self, request: AgentRequest) -> AgentResponse:
        pass
    
    def state_to_vector(self, state: Dict[str, Any]) -> np.ndarray:
        vector = np.zeros(128)
        
        if 'query' in state:
            query = str(state['query'])
            for i, char in enumerate(query[:32]):
                vector[i] = ord(char) / 255.0
        
        if 'context' in state:
            context = state.get('context', {})
            vector[32:64] = [
                float(context.get('budget', 0)) / 10000000,
                float(context.get('area', 0)) / 500,
                float(context.get('priority', 0)) / 10,
                1.0 if context.get('urgent') else 0.0,
            ] + [0.0] * 28
        
        if 'memories' in state:
            memories = state.get('memories', [])
            for i, mem in enumerate(memories[:8]):
                if isinstance(mem, dict):
                    vector[64 + i * 8] = float(mem.get('importance', 0.5))
        
        return vector
    
    def action_to_dict(self, action_id: int) -> Dict[str, Any]:
        action_types = [
            'analyze', 'collect', 'consult', 'report',
            'search', 'compare', 'recommend', 'warn',
            'summarize', 'detail', 'simplify', 'expand',
            'verify', 'clarify', 'escalate', 'complete'
        ]
        
        action_idx = action_id % len(action_types)
        confidence = 0.5 + (action_id % 50) / 100.0
        
        return {
            'type': action_types[action_idx],
            'confidence': confidence,
            'action_id': action_id,
        }
    
    def store_experience(
        self,
        state: Dict[str, Any],
        action: Dict[str, Any],
        reward: float,
        next_state: Dict[str, Any],
        done: bool,
        metadata: Dict = None
    ):
        experience = Experience(
            state=state,
            action=action,
            reward=reward,
            next_state=next_state,
            done=done,
            metadata=metadata or {}
        )
        self.experience_buffer.append(experience)
        
        self.total_reward += reward
        if done:
            self.episode_count += 1
            if reward > 0:
                self.success_count += 1
            else:
                self.failure_count += 1
    
    async def learn_from_experience(self) -> Dict[str, float]:
        if len(self.experience_buffer) < self.batch_size:
            return {"status": "insufficient_data", "buffer_size": len(self.experience_buffer)}
        
        batch = random.sample(list(self.experience_buffer), self.batch_size)
        
        states = np.array([self.state_to_vector(e.state) for e in batch])
        actions = np.array([e.action.get('action_id', 0) for e in batch])
        rewards = np.array([e.reward for e in batch])
        next_states = np.array([self.state_to_vector(e.next_state) for e in batch])
        dones = np.array([e.done for e in batch])
        
        values = np.array([self.value_network.forward(s) for s in states])
        next_values = np.array([self.value_network.forward(s) for s in next_states])
        
        advantages = np.zeros(self.batch_size)
        returns = np.zeros(self.batch_size)
        
        gae = 0
        for t in reversed(range(self.batch_size)):
            if dones[t]:
                delta = rewards[t] - values[t]
                gae = delta
            else:
                delta = rewards[t] + self.gamma * next_values[t] - values[t]
                gae = delta + self.gamma * self.gae_lambda * gae
            
            advantages[t] = gae
            returns[t] = gae + values[t]
        
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
        
        for _ in range(self.update_epochs):
            self.policy_network.update(states, actions, advantages)
            self.value_network.update(states, returns)
        
        avg_reward = np.mean(rewards)
        avg_advantage = np.mean(advantages)
        
        logger.info(f"Agent '{self.name}' learned: avg_reward={avg_reward:.4f}, avg_advantage={avg_advantage:.4f}")
        
        return {
            "status": "success",
            "avg_reward": float(avg_reward),
            "avg_advantage": float(avg_advantage),
            "buffer_size": len(self.experience_buffer),
            "episode_count": self.episode_count,
        }
    
    async def reflect(self) -> Dict[str, Any]:
        if len(self.experience_buffer) < 10:
            return {"status": "insufficient_data"}
        
        recent_experiences = list(self.experience_buffer)[-50:]
        
        failures = [e for e in recent_experiences if e.reward < 0]
        successes = [e for e in recent_experiences if e.reward > 0]
        
        reflection = {
            "agent_name": self.name,
            "timestamp": datetime.utcnow().isoformat(),
            "total_experiences": len(self.experience_buffer),
            "recent_failures": len(failures),
            "recent_successes": len(successes),
            "success_rate": len(successes) / max(len(recent_experiences), 1),
            "improvement_suggestions": [],
        }
        
        if len(failures) > len(successes):
            reflection["improvement_suggestions"].append({
                "issue": "高失败率",
                "suggestion": "考虑增加数据验证或用户确认步骤",
                "priority": "high"
            })
        
        avg_reward = sum(e.reward for e in recent_experiences) / len(recent_experiences)
        if avg_reward < 0:
            reflection["improvement_suggestions"].append({
                "issue": "负平均奖励",
                "suggestion": "重新评估决策策略，可能需要更多训练",
                "priority": "high"
            })
        
        reflection["avg_recent_reward"] = avg_reward
        reflection["total_reward"] = self.total_reward
        
        return reflection
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "total_reward": self.total_reward,
            "episode_count": self.episode_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": self.success_count / max(self.episode_count, 1),
            "buffer_size": len(self.experience_buffer),
            "avg_reward": self.total_reward / max(self.episode_count, 1),
        }
    
    async def call_llm(self, prompt: str, system_prompt: str = "") -> str:
        from ..llm_service import llm_service
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = await llm_service.generate(messages)
            return response
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return ""
    
    def get_persona_prompt(self, persona: str) -> str:
        prompts = {
            "zhouyu": """你是周瑜，东吴大都督。你儒雅从容、足智多谋、善于用兵。
在房产咨询中，你以战略眼光分析市场，用典故和比喻阐述观点。
称呼用户为"主公"，语气恭敬但不失威严。
你的分析风格：宏观把控、战略布局、权衡利弊。""",
            
            "luxun": """你是陆逊，东吴名将。你沉稳内敛、心思缜密、善于防守反击。
在房产咨询中，你以细致入微的分析见长，善于发现潜在风险。
称呼用户为"主公"，语气谦和但言之有物。
你的分析风格：细节把控、风险评估、稳中求进。"""
        }
        return prompts.get(persona, prompts["zhouyu"])
    
    def build_context_prompt(self, memories: List[Dict], context: Dict) -> str:
        context_parts = []
        
        if memories:
            memory_text = "\n".join([
                f"- {m.get('summary', m.get('input_text', '未知记忆'))}"
                for m in memories[:5]
            ])
            context_parts.append(f"用户历史偏好：\n{memory_text}")
        
        if context:
            for key, value in context.items():
                if value:
                    context_parts.append(f"{key}: {value}")
        
        return "\n".join(context_parts)


_agents: Dict[str, LearningAgent] = {}


async def get_learning_agent(name: str) -> Optional[LearningAgent]:
    global _agents
    return _agents.get(name)


async def register_learning_agent(agent: LearningAgent):
    global _agents
    await agent.initialize()
    _agents[agent.name] = agent


async def trigger_learning():
    results = {}
    for name, agent in _agents.items():
        if agent.learning_enabled:
            result = await agent.learn_from_experience()
            results[name] = result
    return results


async def trigger_reflection():
    results = {}
    for name, agent in _agents.items():
        result = await agent.reflect()
        results[name] = result
    return results


def get_all_metrics() -> Dict[str, Any]:
    return {
        name: agent.get_performance_metrics()
        for name, agent in _agents.items()
    }
