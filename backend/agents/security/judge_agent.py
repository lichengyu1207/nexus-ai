"""
判官智能体 JudgeAgent
负责攻击判断、强化学习决策和海马体检索

功能：
- 接收巡捕发来的异常特征
- 从海马体检索历史相似攻击
- 结合强化学习策略，决定处置动作
- 将决策发送给牢头智能体
"""

import json
import time
import uuid
import asyncio
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import random

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None
    nn = None
    optim = None

from .patrol_agent import ThreatLevel, AttackType, TrafficFeatures, AnomalyReport


class SecurityAction(Enum):
    """安全动作"""
    ALLOW = 0
    CAPTCHA = 1
    RATE_LIMIT = 2
    BLOCK_IP = 3
    BLOCK_DEVICE = 4
    ESCALATE = 5


@dataclass
class SecurityDecision:
    """安全决策"""
    decision_id: str
    timestamp: float
    action: SecurityAction
    confidence: float
    target_ips: List[str] = field(default_factory=list)
    target_devices: List[str] = field(default_factory=list)
    rate_limit: int = 0
    reason: str = ""
    similar_attacks: List[Dict] = field(default_factory=list)
    model_confidence: float = 0.0
    history_confidence: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            "decision_id": self.decision_id,
            "timestamp": self.timestamp,
            "action": self.action.name,
            "confidence": self.confidence,
            "target_ips": self.target_ips,
            "target_devices": self.target_devices,
            "rate_limit": self.rate_limit,
            "reason": self.reason,
            "similar_attacks": self.similar_attacks,
            "model_confidence": self.model_confidence,
            "history_confidence": self.history_confidence
        }


@dataclass
class SecurityExperience:
    """安全经验"""
    state: np.ndarray
    action: int
    reward: float
    next_state: np.ndarray
    done: bool
    info: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "state": self.state.tolist(),
            "action": self.action,
            "reward": self.reward,
            "next_state": self.next_state.tolist(),
            "done": self.done,
            "info": self.info
        }


class ReplayBuffer:
    """经验回放池"""
    
    def __init__(self, capacity: int = 10000):
        self.capacity = capacity
        self.buffer: deque = deque(maxlen=capacity)
    
    def push(self, experience: SecurityExperience):
        self.buffer.append(experience)
    
    def sample(self, batch_size: int) -> List[SecurityExperience]:
        return random.sample(self.buffer, min(batch_size, len(self.buffer)))
    
    def __len__(self) -> int:
        return len(self.buffer)


if TORCH_AVAILABLE:
    class DQNetwork(nn.Module):
        """深度Q网络"""
        
        def __init__(
            self,
            state_dim: int = 20,
            action_dim: int = 6,
            hidden_dims: List[int] = [256, 128, 64]
        ):
            super(DQNetwork, self).__init__()
            
            layers = []
            prev_dim = state_dim
            
            for hidden_dim in hidden_dims:
                layers.append(nn.Linear(prev_dim, hidden_dim))
                layers.append(nn.ReLU())
                layers.append(nn.Dropout(0.1))
                prev_dim = hidden_dim
            
            layers.append(nn.Linear(prev_dim, action_dim))
            
            self.network = nn.Sequential(*layers)
        
        def forward(self, state):
            return self.network(state)


class SimpleRLAgent:
    """简化版强化学习智能体（无torch依赖）"""
    
    def __init__(
        self,
        state_dim: int = 20,
        action_dim: int = 6,
        epsilon_start: float = 1.0,
        epsilon_end: float = 0.01,
        epsilon_decay: float = 0.995,
        buffer_size: int = 10000,
        batch_size: int = 32
    ):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.epsilon = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay
        self.batch_size = batch_size
        
        self.q_table: Dict[str, np.ndarray] = {}
        self.buffer = ReplayBuffer(buffer_size)
        self.training_step = 0
        self.learning_rate = 0.1
        self.gamma = 0.99
    
    def _state_to_key(self, state: np.ndarray) -> str:
        discretized = (state * 10).astype(int)
        return str(tuple(discretized[:5]))
    
    def select_action(self, state: np.ndarray, training: bool = True) -> int:
        if training and random.random() < self.epsilon:
            return random.randint(0, self.action_dim - 1)
        
        key = self._state_to_key(state)
        if key not in self.q_table:
            return random.randint(0, self.action_dim - 1)
        
        return int(np.argmax(self.q_table[key]))
    
    def get_action_confidence(self, state: np.ndarray) -> Tuple[int, float, np.ndarray]:
        key = self._state_to_key(state)
        
        if key not in self.q_table:
            action = random.randint(0, self.action_dim - 1)
            probs = np.ones(self.action_dim) / self.action_dim
            return action, 1.0 / self.action_dim, probs
        
        q_values = self.q_table[key]
        exp_q = np.exp(q_values - np.max(q_values))
        probs = exp_q / exp_q.sum()
        
        action = int(np.argmax(q_values))
        confidence = probs[action]
        
        return action, confidence, probs
    
    def train_step(self) -> Optional[float]:
        if len(self.buffer) < self.batch_size:
            return None
        
        experiences = self.buffer.sample(self.batch_size)
        total_loss = 0.0
        
        for exp in experiences:
            key = self._state_to_key(exp.state)
            if key not in self.q_table:
                self.q_table[key] = np.zeros(self.action_dim)
            
            next_key = self._state_to_key(exp.next_state)
            if next_key not in self.q_table:
                self.q_table[next_key] = np.zeros(self.action_dim)
            
            current_q = self.q_table[key][exp.action]
            max_next_q = np.max(self.q_table[next_key]) if not exp.done else 0
            target_q = exp.reward + self.gamma * max_next_q
            
            loss = (target_q - current_q) ** 2
            total_loss += loss
            
            self.q_table[key][exp.action] += self.learning_rate * (target_q - current_q)
        
        self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay)
        self.training_step += 1
        
        return total_loss / len(experiences)


class SecurityRLAgent:
    """安全强化学习智能体"""
    
    def __init__(
        self,
        state_dim: int = 20,
        action_dim: int = 6,
        learning_rate: float = 0.001,
        gamma: float = 0.99,
        epsilon_start: float = 1.0,
        epsilon_end: float = 0.01,
        epsilon_decay: float = 0.995,
        buffer_size: int = 10000,
        batch_size: int = 32,
        target_update_freq: int = 100
    ):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.gamma = gamma
        self.epsilon = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay
        self.batch_size = batch_size
        self.target_update_freq = target_update_freq
        
        if TORCH_AVAILABLE:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.policy_net = DQNetwork(state_dim, action_dim).to(self.device)
            self.target_net = DQNetwork(state_dim, action_dim).to(self.device)
            self.target_net.load_state_dict(self.policy_net.state_dict())
            self.optimizer = optim.Adam(self.policy_net.parameters(), lr=learning_rate)
            self._use_torch = True
        else:
            self._simple_agent = SimpleRLAgent(
                state_dim=state_dim,
                action_dim=action_dim,
                epsilon_start=epsilon_start,
                epsilon_end=epsilon_end,
                epsilon_decay=epsilon_decay,
                buffer_size=buffer_size,
                batch_size=batch_size
            )
            self._use_torch = False
        
        self.buffer = ReplayBuffer(buffer_size)
        self.update_count = 0
        self.training_step = 0
    
    def select_action(self, state: np.ndarray, training: bool = True) -> int:
        if self._use_torch:
            if training and random.random() < self.epsilon:
                return random.randint(0, self.action_dim - 1)
            
            with torch.no_grad():
                state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
                q_values = self.policy_net(state_tensor)
                return q_values.argmax(1).item()
        else:
            return self._simple_agent.select_action(state, training)
    
    def get_action_confidence(self, state: np.ndarray) -> Tuple[int, float, np.ndarray]:
        if self._use_torch:
            with torch.no_grad():
                state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
                q_values = self.policy_net(state_tensor)
                
                probs = torch.softmax(q_values, dim=1)
                action = q_values.argmax(1).item()
                confidence = probs[0, action].item()
                
                return action, confidence, probs[0].cpu().numpy()
        else:
            return self._simple_agent.get_action_confidence(state)
    
    def train_step(self) -> Optional[float]:
        if len(self.buffer) < self.batch_size:
            return None
        
        if not self._use_torch:
            return self._simple_agent.train_step()
        
        experiences = self.buffer.sample(self.batch_size)
        
        states = torch.FloatTensor(np.array([e.state for e in experiences])).to(self.device)
        actions = torch.LongTensor([e.action for e in experiences]).to(self.device)
        rewards = torch.FloatTensor([e.reward for e in experiences]).to(self.device)
        next_states = torch.FloatTensor(np.array([e.next_state for e in experiences])).to(self.device)
        dones = torch.FloatTensor([e.done for e in experiences]).to(self.device)
        
        current_q = self.policy_net(states).gather(1, actions.unsqueeze(1))
        
        with torch.no_grad():
            next_q = self.target_net(next_states).max(1)[0]
            target_q = rewards + (1 - dones) * self.gamma * next_q
        
        loss = nn.MSELoss()(current_q.squeeze(), target_q)
        
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.policy_net.parameters(), 1.0)
        self.optimizer.step()
        
        self.update_count += 1
        
        if self.update_count % self.target_update_freq == 0:
            self.target_net.load_state_dict(self.policy_net.state_dict())
        
        self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay)
        
        self.training_step += 1
        
        return loss.item()
    
    def save_model(self, path: str):
        if self._use_torch:
            torch.save({
                'policy_net': self.policy_net.state_dict(),
                'target_net': self.target_net.state_dict(),
                'optimizer': self.optimizer.state_dict(),
                'epsilon': self.epsilon,
                'training_step': self.training_step
            }, path)
    
    def load_model(self, path: str):
        if self._use_torch:
            checkpoint = torch.load(path, map_location=self.device)
            self.policy_net.load_state_dict(checkpoint['policy_net'])
            self.target_net.load_state_dict(checkpoint['target_net'])
            self.optimizer.load_state_dict(checkpoint['optimizer'])
            self.epsilon = checkpoint['epsilon']
            self.training_step = checkpoint['training_step']


class HippocampusClient:
    """海马体客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    async def retrieve_similar_attacks(
        self,
        feature_vector: np.ndarray,
        top_k: int = 5
    ) -> List[Dict]:
        """检索相似攻击"""
        try:
            from ..hippocampus import hippocampus_service
            
            results = await hippocampus_service.search_similar(
                query_vector=feature_vector.tolist(),
                collection="security_attacks",
                top_k=top_k
            )
            
            return results
        except Exception as e:
            print(f"海马体检索失败: {e}")
            return []
    
    async def store_attack_pattern(
        self,
        feature_vector: np.ndarray,
        metadata: Dict
    ) -> bool:
        """存储攻击模式"""
        try:
            from ..hippocampus import hippocampus_service
            
            await hippocampus_service.store_memory(
                content=json.dumps(metadata),
                memory_type="attack_pattern",
                embedding=feature_vector.tolist(),
                metadata=metadata
            )
            
            return True
        except Exception as e:
            print(f"存储攻击模式失败: {e}")
            return False


class JudgeAgent:
    """判官智能体"""
    
    ACTION_COSTS = {
        SecurityAction.ALLOW: 0,
        SecurityAction.CAPTCHA: 1,
        SecurityAction.RATE_LIMIT: 2,
        SecurityAction.BLOCK_IP: 3,
        SecurityAction.BLOCK_DEVICE: 4,
        SecurityAction.ESCALATE: 5
    }
    
    def __init__(
        self,
        agent_id: str = "judge_001",
        model_path: Optional[str] = None
    ):
        self.agent_id = agent_id
        
        self.rl_agent = SecurityRLAgent()
        self.hippocampus = HippocampusClient()
        
        if model_path:
            self.rl_agent.load_model(model_path)
        
        self._decision_history: deque = deque(maxlen=1000)
        self._pending_decisions: Dict[str, SecurityDecision] = {}
        self._action_handlers: List[callable] = []
        
        self._running = False
        self._task = None
    
    def _map_threat_to_action(self, threat_level: ThreatLevel, attack_type: AttackType) -> SecurityAction:
        """映射威胁等级到动作"""
        action_map = {
            ThreatLevel.LOW: SecurityAction.ALLOW,
            ThreatLevel.MEDIUM: SecurityAction.RATE_LIMIT,
            ThreatLevel.HIGH: SecurityAction.BLOCK_IP,
            ThreatLevel.CRITICAL: SecurityAction.ESCALATE
        }
        
        base_action = action_map.get(threat_level, SecurityAction.ALLOW)
        
        if attack_type == AttackType.DDOS:
            if threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
                return SecurityAction.ESCALATE
            return SecurityAction.RATE_LIMIT
        
        if attack_type == AttackType.CC:
            return SecurityAction.RATE_LIMIT
        
        if attack_type == AttackType.SQL_INJECTION:
            return SecurityAction.BLOCK_IP
        
        if attack_type == AttackType.XSS:
            return SecurityAction.BLOCK_IP
        
        if attack_type == AttackType.BRUTE_FORCE:
            return SecurityAction.BLOCK_IP
        
        if attack_type == AttackType.CRAWLER:
            return SecurityAction.CAPTCHA
        
        return base_action
    
    async def _send_action(self, decision: SecurityDecision):
        """发送动作"""
        for handler in self._action_handlers:
            try:
                await handler(decision)
            except Exception as e:
                print(f"动作处理器错误: {e}")
    
    async def decide(self, report: AnomalyReport) -> SecurityDecision:
        """做出决策"""
        feature_vector = report.features.to_vector()
        
        similar_attacks = await self.hippocampus.retrieve_similar_attacks(feature_vector)
        
        action_idx, model_confidence, action_probs = self.rl_agent.get_action_confidence(feature_vector)
        
        history_confidence = 0.0
        if similar_attacks:
            history_confidence = sum(a.get("similarity", 0) for a in similar_attacks) / len(similar_attacks)
        
        if history_confidence > 0.7 and similar_attacks:
            best_historical = max(similar_attacks, key=lambda x: x.get("effectiveness", 0))
            if best_historical.get("effectiveness", 0) > 0.8:
                historical_action = best_historical.get("action", "ALLOW")
                try:
                    action_idx = SecurityAction[historical_action].value
                except KeyError:
                    pass
        
        threat_action = self._map_threat_to_action(report.threat_level, report.suspected_attack)
        
        if report.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
            action_idx = threat_action.value
            confidence = 0.9
        else:
            confidence = 0.6 * model_confidence + 0.4 * history_confidence
        
        action = SecurityAction(action_idx)
        
        rate_limit = 0
        if action == SecurityAction.RATE_LIMIT:
            base_rate = 10
            if report.threat_level == ThreatLevel.MEDIUM:
                rate_limit = base_rate
            elif report.threat_level == ThreatLevel.HIGH:
                rate_limit = base_rate // 2
            else:
                rate_limit = base_rate * 2
        
        decision = SecurityDecision(
            decision_id=str(uuid.uuid4()),
            timestamp=time.time(),
            action=action,
            confidence=confidence,
            target_ips=report.source_ips[:10] if action in [SecurityAction.BLOCK_IP, SecurityAction.RATE_LIMIT] else [],
            rate_limit=rate_limit,
            reason=f"检测到{report.suspected_attack.value}攻击，威胁等级{report.threat_level.value}",
            similar_attacks=[{"attack_type": a.get("attack_type"), "similarity": a.get("similarity")} for a in similar_attacks[:3]],
            model_confidence=model_confidence,
            history_confidence=history_confidence
        )
        
        self._decision_history.append(decision)
        self._pending_decisions[decision.decision_id] = decision
        
        await self._send_action(decision)
        
        return decision
    
    def compute_reward(
        self,
        decision: SecurityDecision,
        effect: Dict
    ) -> float:
        """计算奖励"""
        reward = 0.0
        
        if effect.get("attack_blocked", False):
            reward += 10.0
        
        if effect.get("false_positive", False):
            reward -= 20.0
        
        if effect.get("user_complaint", False):
            reward -= 50.0
        
        if effect.get("service_down", False):
            reward -= 100.0
        
        if decision.action == SecurityAction.CAPTCHA:
            if effect.get("captcha_passed", False):
                reward += 1.0
            elif effect.get("captcha_abandoned", False):
                reward -= 2.0
        
        if decision.action == SecurityAction.ALLOW:
            if effect.get("was_attack", False):
                reward -= 30.0
        
        return reward
    
    async def learn_from_experience(
        self,
        decision_id: str,
        effect: Dict,
        next_features: Optional[TrafficFeatures] = None
    ):
        """从经验中学习"""
        if decision_id not in self._pending_decisions:
            return
        
        decision = self._pending_decisions[decision_id]
        
        reward = self.compute_reward(decision, effect)
        
        state = np.zeros(20)
        if decision.similar_attacks:
            pass
        
        next_state = next_features.to_vector() if next_features else np.zeros(20)
        done = effect.get("attack_ended", True)
        
        experience = SecurityExperience(
            state=state,
            action=decision.action.value,
            reward=reward,
            next_state=next_state,
            done=done,
            info={
                "decision_id": decision_id,
                "effect": effect
            }
        )
        
        self.rl_agent.buffer.push(experience)
        
        loss = self.rl_agent.train_step()
        
        del self._pending_decisions[decision_id]
        
        return loss
    
    async def run_training(self):
        """后台训练"""
        while self._running:
            try:
                if len(self.rl_agent.buffer) >= self.rl_agent.batch_size:
                    loss = self.rl_agent.train_step()
                    if loss:
                        print(f"训练损失: {loss:.4f}")
                
                await asyncio.sleep(10)
            except Exception as e:
                print(f"训练错误: {e}")
                await asyncio.sleep(1)
    
    def start(self):
        """启动"""
        self._running = True
        self._task = asyncio.create_task(self.run_training())
    
    def stop(self):
        """停止"""
        self._running = False
        if self._task:
            self._task.cancel()
    
    def get_status(self) -> Dict:
        """获取状态"""
        return {
            "agent_id": self.agent_id,
            "running": self._running,
            "epsilon": self.rl_agent.epsilon,
            "buffer_size": len(self.rl_agent.buffer),
            "training_step": self.rl_agent.training_step,
            "pending_decisions": len(self._pending_decisions),
            "decision_history_size": len(self._decision_history)
        }


judge_agent = JudgeAgent()
