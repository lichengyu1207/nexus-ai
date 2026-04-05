"""
强化学习经验采集器
Experience Collector for Reinforcement Learning

在智能体执行任务时记录状态、动作、奖励、下一状态
将经验存入记忆系统的 experience_replay 表中
"""

import json
import time
import uuid
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import numpy as np


class ExperienceState(Enum):
    PENDING = "pending"
    COLLECTED = "collected"
    PROCESSED = "processed"


@dataclass
class State:
    """状态表示"""
    task_id: str
    agent_id: str
    context: Dict[str, Any]
    user_input: str
    memory_retrieval: List[Dict[str, Any]]
    system_state: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    
    def to_vector(self) -> np.ndarray:
        """将状态转换为向量表示（用于神经网络输入）"""
        features = []
        
        features.append(hash(self.task_id) % 10000 / 10000.0)
        features.append(hash(self.agent_id) % 10000 / 10000.0)
        features.append(len(self.context))
        features.append(len(self.user_input) / 1000.0)
        features.append(len(self.memory_retrieval) / 10.0)
        features.append(self.system_state.get("load", 0.5))
        features.append(self.system_state.get("queue_length", 0) / 100.0)
        
        context_features = self._extract_context_features(self.context)
        features.extend(context_features)
        
        return np.array(features, dtype=np.float32)
    
    def _extract_context_features(self, context: Dict) -> List[float]:
        """从上下文中提取特征"""
        features = []
        
        if "city" in context:
            features.append(hash(context["city"]) % 10000 / 10000.0)
        else:
            features.append(0.0)
            
        if "property_type" in context:
            features.append(hash(context["property_type"]) % 10000 / 10000.0)
        else:
            features.append(0.0)
            
        if "price_range" in context:
            features.append(context["price_range"].get("min", 0) / 10000000.0)
            features.append(context["price_range"].get("max", 0) / 10000000.0)
        else:
            features.extend([0.0, 0.0])
            
        features.append(context.get("urgency", 0.5))
        features.append(context.get("complexity", 0.5))
        
        return features
    
    def to_dict(self) -> Dict:
        return {
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "context": self.context,
            "user_input": self.user_input,
            "memory_retrieval": self.memory_retrieval,
            "system_state": self.system_state,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "State":
        return cls(
            task_id=data["task_id"],
            agent_id=data["agent_id"],
            context=data["context"],
            user_input=data["user_input"],
            memory_retrieval=data["memory_retrieval"],
            system_state=data["system_state"],
            timestamp=data.get("timestamp", time.time())
        )


@dataclass
class Action:
    """动作表示"""
    action_id: str
    action_type: str
    tool_name: Optional[str]
    parameters: Dict[str, Any]
    content_generated: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    
    def to_vector(self, action_space_size: int = 50) -> np.ndarray:
        """将动作转换为one-hot向量"""
        vector = np.zeros(action_space_size, dtype=np.float32)
        
        action_hash = hash(self.action_type)
        if self.tool_name:
            action_hash = hash(f"{self.action_type}_{self.tool_name}")
        
        index = abs(action_hash) % action_space_size
        vector[index] = 1.0
        
        return vector
    
    def to_dict(self) -> Dict:
        return {
            "action_id": self.action_id,
            "action_type": self.action_type,
            "tool_name": self.tool_name,
            "parameters": self.parameters,
            "content_generated": self.content_generated,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Action":
        return cls(
            action_id=data["action_id"],
            action_type=data["action_type"],
            tool_name=data.get("tool_name"),
            parameters=data.get("parameters", {}),
            content_generated=data.get("content_generated"),
            timestamp=data.get("timestamp", time.time())
        )


@dataclass
class Reward:
    """奖励表示"""
    total: float
    components: Dict[str, float]
    explanation: str
    timestamp: float = field(default_factory=time.time)
    
    @classmethod
    def calculate(
        cls,
        task_success: bool,
        user_feedback: Optional[str] = None,
        task_duration: float = 0.0,
        duration_threshold: float = 30.0,
        quality_score: float = 0.5
    ) -> "Reward":
        """计算奖励值"""
        components = {}
        
        if task_success:
            components["task_success"] = 1.0
        else:
            components["task_success"] = -0.5
        
        if user_feedback == "like":
            components["user_feedback"] = 0.3
        elif user_feedback == "dislike":
            components["user_feedback"] = -0.3
        else:
            components["user_feedback"] = 0.0
        
        if task_duration > duration_threshold:
            overtime_ratio = (task_duration - duration_threshold) / duration_threshold
            components["efficiency"] = -0.1 * min(overtime_ratio, 1.0)
        else:
            components["efficiency"] = 0.1
        
        components["quality"] = (quality_score - 0.5) * 0.4
        
        total = sum(components.values())
        
        explanation_parts = []
        if task_success:
            explanation_parts.append("任务成功")
        else:
            explanation_parts.append("任务失败")
        
        if user_feedback:
            explanation_parts.append(f"用户反馈: {user_feedback}")
        
        if task_duration > duration_threshold:
            explanation_parts.append(f"超时({task_duration:.1f}s > {duration_threshold}s)")
        
        explanation = "; ".join(explanation_parts)
        
        return cls(total=total, components=components, explanation=explanation)
    
    def to_dict(self) -> Dict:
        return {
            "total": self.total,
            "components": self.components,
            "explanation": self.explanation,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Reward":
        return cls(
            total=data["total"],
            components=data["components"],
            explanation=data["explanation"],
            timestamp=data.get("timestamp", time.time())
        )


@dataclass
class Experience:
    """经验元组"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    state: Optional[State] = None
    action: Optional[Action] = None
    reward: Optional[Reward] = None
    next_state: Optional[State] = None
    done: bool = False
    agent_id: str = ""
    task_id: str = ""
    episode_id: str = ""
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "state": self.state.to_dict() if self.state else None,
            "action": self.action.to_dict() if self.action else None,
            "reward": self.reward.to_dict() if self.reward else None,
            "next_state": self.next_state.to_dict() if self.next_state else None,
            "done": self.done,
            "agent_id": self.agent_id,
            "task_id": self.task_id,
            "episode_id": self.episode_id,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Experience":
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            state=State.from_dict(data["state"]) if data.get("state") else None,
            action=Action.from_dict(data["action"]) if data.get("action") else None,
            reward=Reward.from_dict(data["reward"]) if data.get("reward") else None,
            next_state=State.from_dict(data["next_state"]) if data.get("next_state") else None,
            done=data.get("done", False),
            agent_id=data.get("agent_id", ""),
            task_id=data.get("task_id", ""),
            episode_id=data.get("episode_id", ""),
            timestamp=data.get("timestamp", time.time()),
            metadata=data.get("metadata", {})
        )


class ExperienceCollector:
    """经验采集器"""
    
    def __init__(
        self,
        buffer_size: int = 10000,
        batch_size: int = 32,
        priority_replay: bool = True
    ):
        self.buffer_size = buffer_size
        self.batch_size = batch_size
        self.priority_replay = priority_replay
        
        self._buffer: List[Experience] = []
        self._current_episode: Dict[str, List[Experience]] = {}
        self._pending_states: Dict[str, State] = {}
        self._pending_actions: Dict[str, Action] = {}
    
    async def start_episode(self, agent_id: str, task_id: str) -> str:
        """开始一个新的回合"""
        episode_id = str(uuid.uuid4())
        
        self._current_episode[episode_id] = []
        
        await self._log_event("episode_start", {
            "episode_id": episode_id,
            "agent_id": agent_id,
            "task_id": task_id,
            "timestamp": time.time()
        })
        
        return episode_id
    
    async def collect_state(
        self,
        episode_id: str,
        task_id: str,
        agent_id: str,
        context: Dict[str, Any],
        user_input: str,
        memory_retrieval: List[Dict[str, Any]],
        system_state: Dict[str, Any]
    ) -> State:
        """采集状态"""
        state = State(
            task_id=task_id,
            agent_id=agent_id,
            context=context,
            user_input=user_input,
            memory_retrieval=memory_retrieval,
            system_state=system_state
        )
        
        self._pending_states[f"{episode_id}_{task_id}"] = state
        
        return state
    
    async def collect_action(
        self,
        episode_id: str,
        task_id: str,
        action_type: str,
        tool_name: Optional[str] = None,
        parameters: Optional[Dict] = None,
        content_generated: Optional[str] = None
    ) -> Action:
        """采集动作"""
        action = Action(
            action_id=str(uuid.uuid4()),
            action_type=action_type,
            tool_name=tool_name,
            parameters=parameters or {},
            content_generated=content_generated
        )
        
        self._pending_actions[f"{episode_id}_{task_id}"] = action
        
        return action
    
    async def collect_reward(
        self,
        episode_id: str,
        task_id: str,
        task_success: bool,
        user_feedback: Optional[str] = None,
        task_duration: float = 0.0,
        duration_threshold: float = 30.0,
        quality_score: float = 0.5
    ) -> Reward:
        """采集奖励"""
        reward = Reward.calculate(
            task_success=task_success,
            user_feedback=user_feedback,
            task_duration=task_duration,
            duration_threshold=duration_threshold,
            quality_score=quality_score
        )
        
        state_key = f"{episode_id}_{task_id}"
        action_key = f"{episode_id}_{task_id}"
        
        state = self._pending_states.get(state_key)
        action = self._pending_actions.get(action_key)
        
        if state and action:
            experience = Experience(
                state=state,
                action=action,
                reward=reward,
                next_state=None,
                done=True,
                agent_id=state.agent_id,
                task_id=task_id,
                episode_id=episode_id,
                metadata={
                    "task_success": task_success,
                    "user_feedback": user_feedback,
                    "task_duration": task_duration
                }
            )
            
            await self.store_experience(experience)
            
            if episode_id in self._current_episode:
                self._current_episode[episode_id].append(experience)
            
            if state_key in self._pending_states:
                del self._pending_states[state_key]
            if action_key in self._pending_actions:
                del self._pending_actions[action_key]
        
        return reward
    
    async def collect_transition(
        self,
        episode_id: str,
        state: State,
        action: Action,
        reward: Reward,
        next_state: Optional[State] = None,
        done: bool = False
    ) -> Experience:
        """采集完整的状态转移"""
        experience = Experience(
            state=state,
            action=action,
            reward=reward,
            next_state=next_state,
            done=done,
            agent_id=state.agent_id,
            task_id=state.task_id,
            episode_id=episode_id
        )
        
        await self.store_experience(experience)
        
        if episode_id in self._current_episode:
            self._current_episode[episode_id].append(experience)
        
        return experience
    
    async def store_experience(self, experience: Experience) -> bool:
        """存储经验到缓冲区和数据库"""
        if len(self._buffer) >= self.buffer_size:
            self._buffer.pop(0)
        
        self._buffer.append(experience)
        
        try:
            await self._store_to_database(experience)
            return True
        except Exception as e:
            print(f"存储经验到数据库失败: {e}")
            return False
    
    async def _store_to_database(self, experience: Experience):
        """存储经验到数据库"""
        from ..database import get_db_connection
        
        async for conn in get_db_connection():
            try:
                await conn.execute("""
                    INSERT INTO experience_replay 
                    (id, agent_id, task_id, episode_id, state, action, reward, next_state, done, priority, metadata, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, CURRENT_TIMESTAMP)
                """, (
                    experience.id,
                    experience.agent_id,
                    experience.task_id,
                    experience.episode_id,
                    json.dumps(experience.state.to_dict()) if experience.state else None,
                    json.dumps(experience.action.to_dict()) if experience.action else None,
                    json.dumps(experience.reward.to_dict()) if experience.reward else None,
                    json.dumps(experience.next_state.to_dict()) if experience.next_state else None,
                    1 if experience.done else 0,
                    abs(experience.reward.total) if experience.reward else 1.0,
                    json.dumps(experience.metadata)
                ))
                await conn.commit()
            finally:
                await conn.close()
    
    async def end_episode(self, episode_id: str, success: bool = True):
        """结束回合"""
        if episode_id in self._current_episode:
            experiences = self._current_episode[episode_id]
            
            for i, exp in enumerate(experiences):
                if i < len(experiences) - 1:
                    exp.next_state = experiences[i + 1].state
                else:
                    exp.done = True
            
            del self._current_episode[episode_id]
        
        await self._log_event("episode_end", {
            "episode_id": episode_id,
            "success": success,
            "timestamp": time.time()
        })
    
    def sample_batch(self, batch_size: Optional[int] = None) -> List[Experience]:
        """从缓冲区采样一批经验"""
        batch_size = batch_size or self.batch_size
        
        if len(self._buffer) < batch_size:
            return self._buffer.copy()
        
        if self.priority_replay:
            priorities = np.array([
                abs(exp.reward.total) if exp.reward else 1.0
                for exp in self._buffer
            ])
            probabilities = priorities / priorities.sum()
            
            indices = np.random.choice(
                len(self._buffer),
                size=batch_size,
                replace=False,
                p=probabilities
            )
            
            return [self._buffer[i] for i in indices]
        else:
            indices = np.random.choice(len(self._buffer), size=batch_size, replace=False)
            return [self._buffer[i] for i in indices]
    
    def get_episode_experiences(self, episode_id: str) -> List[Experience]:
        """获取指定回合的所有经验"""
        return self._current_episode.get(episode_id, [])
    
    async def get_experiences_by_agent(
        self,
        agent_id: str,
        limit: int = 100
    ) -> List[Experience]:
        """从数据库获取指定智能体的经验"""
        from ..database import get_db_connection
        
        async for conn in get_db_connection():
            try:
                rows = await conn.fetch("""
                    SELECT id, agent_id, task_id, episode_id, state, action, reward, next_state, done, created_at, metadata
                    FROM experience_replay
                    WHERE agent_id = $1
                    ORDER BY created_at DESC
                    LIMIT $2
                """, agent_id, limit)
                
                return [
                    Experience.from_dict({
                        "id": row["id"],
                        "agent_id": row["agent_id"],
                        "task_id": row["task_id"],
                        "episode_id": row["episode_id"],
                        "state": json.loads(row["state"]) if row["state"] else None,
                        "action": json.loads(row["action"]) if row["action"] else None,
                        "reward": json.loads(row["reward"]) if row["reward"] else None,
                        "next_state": json.loads(row["next_state"]) if row["next_state"] else None,
                        "done": bool(row["done"]),
                        "timestamp": row["created_at"].timestamp() if row["created_at"] else time.time(),
                        "metadata": json.loads(row["metadata"]) if row["metadata"] else {}
                    })
                    for row in rows
                ]
            finally:
                await conn.close()
    
    def get_buffer_stats(self) -> Dict[str, Any]:
        """获取缓冲区统计信息"""
        if not self._buffer:
            return {
                "size": 0,
                "capacity": self.buffer_size,
                "avg_reward": 0.0,
                "success_rate": 0.0
            }
        
        rewards = [exp.reward.total for exp in self._buffer if exp.reward]
        successes = [exp.metadata.get("task_success", False) for exp in self._buffer]
        
        return {
            "size": len(self._buffer),
            "capacity": self.buffer_size,
            "avg_reward": np.mean(rewards) if rewards else 0.0,
            "success_rate": np.mean(successes) if successes else 0.0,
            "pending_episodes": len(self._current_episode),
            "pending_states": len(self._pending_states),
            "pending_actions": len(self._pending_actions)
        }
    
    async def clear_buffer(self):
        """清空缓冲区"""
        self._buffer.clear()
        self._current_episode.clear()
        self._pending_states.clear()
        self._pending_actions.clear()
    
    async def _log_event(self, event_type: str, data: Dict):
        """记录事件日志"""
        print(f"[ExperienceCollector] {event_type}: {json.dumps(data, ensure_ascii=False)}")


class ExperienceCollectorMiddleware:
    """经验采集中间件，用于自动采集智能体交互经验"""
    
    def __init__(self, collector: ExperienceCollector):
        self.collector = collector
        self._active_episodes: Dict[str, str] = {}
    
    async def before_task(
        self,
        agent_id: str,
        task_id: str,
        context: Dict[str, Any],
        user_input: str,
        memory_result: List[Dict]
    ) -> str:
        """任务执行前的钩子"""
        episode_id = await self.collector.start_episode(agent_id, task_id)
        self._active_episodes[task_id] = episode_id
        
        await self.collector.collect_state(
            episode_id=episode_id,
            task_id=task_id,
            agent_id=agent_id,
            context=context,
            user_input=user_input,
            memory_retrieval=memory_result,
            system_state={"load": 0.5, "queue_length": 0}
        )
        
        return episode_id
    
    async def after_action(
        self,
        task_id: str,
        action_type: str,
        tool_name: Optional[str] = None,
        parameters: Optional[Dict] = None,
        content: Optional[str] = None
    ):
        """动作执行后的钩子"""
        episode_id = self._active_episodes.get(task_id)
        if not episode_id:
            return
        
        await self.collector.collect_action(
            episode_id=episode_id,
            task_id=task_id,
            action_type=action_type,
            tool_name=tool_name,
            parameters=parameters,
            content_generated=content
        )
    
    async def after_task(
        self,
        task_id: str,
        success: bool,
        user_feedback: Optional[str] = None,
        duration: float = 0.0,
        quality_score: float = 0.5
    ):
        """任务完成后的钩子"""
        episode_id = self._active_episodes.get(task_id)
        if not episode_id:
            return
        
        await self.collector.collect_reward(
            episode_id=episode_id,
            task_id=task_id,
            task_success=success,
            user_feedback=user_feedback,
            task_duration=duration,
            quality_score=quality_score
        )
        
        await self.collector.end_episode(episode_id, success=success)
        
        if task_id in self._active_episodes:
            del self._active_episodes[task_id]


experience_collector = ExperienceCollector()
experience_middleware = ExperienceCollectorMiddleware(experience_collector)
