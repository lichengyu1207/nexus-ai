"""
优先经验回放PER (Prioritized Experience Replay)
加速强化学习收敛，支持多步学习
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Tuple, Generic, TypeVar
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np
import logging
import random
import math

logger = logging.getLogger(__name__)

T = TypeVar('T')


class PriorityMethod(Enum):
    PROPORTIONAL = "proportional"
    RANK_BASED = "rank_based"
    GREEDY = "greedy"


@dataclass
class Experience:
    state: Any
    action: Any
    reward: float
    next_state: Any
    done: bool
    priority: float = 1.0
    td_error: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def experience_id(self) -> str:
        return f"exp_{hash(str(self.state))}_{self.timestamp.timestamp()}"


@dataclass
class MultiStepExperience:
    states: List[Any]
    actions: List[Any]
    rewards: List[float]
    next_state: Any
    done: bool
    n_steps: int
    gamma: float = 0.99
    priority: float = 1.0
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def discounted_reward(self) -> float:
        total = 0.0
        for i, r in enumerate(self.rewards):
            total += (self.gamma ** i) * r
        return total


class SumTree:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.tree = np.zeros(2 * capacity - 1)
        self.data = np.zeros(capacity, dtype=object)
        self.write = 0
        self.n_entries = 0
        
    def _propagate(self, idx: int, change: float):
        parent = (idx - 1) // 2
        self.tree[parent] += change
        if parent != 0:
            self._propagate(parent, change)
            
    def _retrieve(self, idx: int, s: float) -> int:
        left = 2 * idx + 1
        right = left + 1
        
        if left >= len(self.tree):
            return idx
            
        if s <= self.tree[left]:
            return self._retrieve(left, s)
        else:
            return self._retrieve(right, s - self.tree[left])
            
    def total(self) -> float:
        return self.tree[0]
    
    def add(self, priority: float, data: Any):
        idx = self.write + self.capacity - 1
        
        self.data[self.write] = data
        self.update(idx, priority)
        
        self.write += 1
        if self.write >= self.capacity:
            self.write = 0
            
        if self.n_entries < self.capacity:
            self.n_entries += 1
            
    def update(self, idx: int, priority: float):
        change = priority - self.tree[idx]
        self.tree[idx] = priority
        self._propagate(idx, change)
        
    def get(self, s: float) -> Tuple[int, float, Any]:
        idx = self._retrieve(0, s)
        data_idx = idx - self.capacity + 1
        
        return idx, self.tree[idx], self.data[data_idx]


class PrioritizedReplayBuffer:
    def __init__(
        self,
        capacity: int = 100000,
        alpha: float = 0.6,
        beta_start: float = 0.4,
        beta_frames: int = 100000,
        epsilon: float = 1e-6,
        method: PriorityMethod = PriorityMethod.PROPORTIONAL
    ):
        self.capacity = capacity
        self.alpha = alpha
        self.beta_start = beta_start
        self.beta_frames = beta_frames
        self.epsilon = epsilon
        self.method = method
        
        self.tree = SumTree(capacity)
        self.frame = 0
        self.max_priority = 1.0
        
    def add(self, experience: Experience):
        priority = self.max_priority ** self.alpha
        self.tree.add(priority, experience)
        
    def add_batch(self, experiences: List[Experience]):
        for exp in experiences:
            self.add(exp)
            
    def sample(self, batch_size: int) -> Tuple[List[Experience], np.ndarray, List[int]]:
        self.frame += 1
        
        experiences = []
        indices = []
        priorities = []
        
        segment = self.tree.total() / batch_size
        
        beta = min(
            1.0, 
            self.beta_start + self.frame * (1.0 - self.beta_start) / self.beta_frames
        )
        
        for i in range(batch_size):
            a = segment * i
            b = segment * (i + 1)
            
            s = random.uniform(a, b)
            
            idx, priority, experience = self.tree.get(s)
            
            experiences.append(experience)
            indices.append(idx)
            priorities.append(priority)
            
        priorities = np.array(priorities)
        
        sampling_probabilities = priorities / self.tree.total()
        
        is_weights = np.power(self.tree.n_entries * sampling_probabilities, -beta)
        is_weights /= is_weights.max()
        
        return experiences, is_weights, indices
        
    def update_priorities(self, indices: List[int], td_errors: np.ndarray):
        for idx, td_error in zip(indices, td_errors):
            priority = self._calculate_priority(td_error)
            self.tree.update(idx, priority)
            
            if priority > self.max_priority:
                self.max_priority = priority
                
    def _calculate_priority(self, td_error: float) -> float:
        if self.method == PriorityMethod.PROPORTIONAL:
            return (abs(td_error) + self.epsilon) ** self.alpha
        elif self.method == PriorityMethod.RANK_BASED:
            return 1.0 / (self.tree.n_entries + 1)
        else:
            return abs(td_error) + self.epsilon
            
    def __len__(self) -> int:
        return self.tree.n_entries


class MultiStepBuffer:
    def __init__(self, n_steps: int = 3, gamma: float = 0.99):
        self.n_steps = n_steps
        self.gamma = gamma
        self.buffer: List[Experience] = []
        
    def add(self, experience: Experience) -> Optional[MultiStepExperience]:
        self.buffer.append(experience)
        
        if len(self.buffer) >= self.n_steps:
            return self._create_multi_step()
            
        return None
        
    def _create_multi_step(self) -> MultiStepExperience:
        states = [e.state for e in self.buffer[:self.n_steps]]
        actions = [e.action for e in self.buffer[:self.n_steps]]
        rewards = [e.reward for e in self.buffer[:self.n_steps]]
        
        last_exp = self.buffer[self.n_steps - 1]
        
        multi_step = MultiStepExperience(
            states=states,
            actions=actions,
            rewards=rewards,
            next_state=last_exp.next_state,
            done=last_exp.done,
            n_steps=self.n_steps,
            gamma=self.gamma
        )
        
        self.buffer = self.buffer[1:]
        
        return multi_step
        
    def flush(self) -> List[MultiStepExperience]:
        results = []
        while self.buffer:
            if len(self.buffer) >= self.n_steps:
                results.append(self._create_multi_step())
            else:
                remaining = len(self.buffer)
                states = [e.state for e in self.buffer]
                actions = [e.action for e in self.buffer]
                rewards = [e.reward for e in self.buffer]
                
                last_exp = self.buffer[-1]
                results.append(MultiStepExperience(
                    states=states,
                    actions=actions,
                    rewards=rewards,
                    next_state=last_exp.next_state,
                    done=last_exp.done,
                    n_steps=remaining,
                    gamma=self.gamma
                ))
                self.buffer = []
                
        return results


class NStepPrioritizedReplay:
    def __init__(
        self,
        capacity: int = 100000,
        n_steps: int = 3,
        gamma: float = 0.99,
        alpha: float = 0.6,
        beta_start: float = 0.4,
        beta_frames: int = 100000
    ):
        self.replay_buffer = PrioritizedReplayBuffer(
            capacity=capacity,
            alpha=alpha,
            beta_start=beta_start,
            beta_frames=beta_frames
        )
        self.n_step_buffer = MultiStepBuffer(n_steps=n_steps, gamma=gamma)
        self.n_steps = n_steps
        self.gamma = gamma
        
    def add(self, experience: Experience):
        multi_step = self.n_step_buffer.add(experience)
        
        if multi_step:
            exp = Experience(
                state=multi_step.states[0],
                action=multi_step.actions[0],
                reward=multi_step.discounted_reward,
                next_state=multi_step.next_state,
                done=multi_step.done,
                metadata={
                    "n_steps": multi_step.n_steps,
                    "intermediate_rewards": multi_step.rewards
                }
            )
            self.replay_buffer.add(exp)
            
    def sample(self, batch_size: int) -> Tuple[List[Experience], np.ndarray, List[int]]:
        return self.replay_buffer.sample(batch_size)
        
    def update_priorities(self, indices: List[int], td_errors: np.ndarray):
        self.replay_buffer.update_priorities(indices, td_errors)
        
    def flush(self):
        multi_steps = self.n_step_buffer.flush()
        for ms in multi_steps:
            exp = Experience(
                state=ms.states[0],
                action=ms.actions[0],
                reward=ms.discounted_reward,
                next_state=ms.next_state,
                done=ms.done,
                metadata={"n_steps": ms.n_steps}
            )
            self.replay_buffer.add(exp)
            
    def __len__(self) -> int:
        return len(self.replay_buffer)


class HindsightExperienceReplay:
    def __init__(
        self,
        replay_buffer: PrioritizedReplayBuffer,
        k: int = 4,
        strategy: str = "future"
    ):
        self.replay_buffer = replay_buffer
        self.k = k
        self.strategy = strategy
        
    def add_episode(
        self,
        trajectory: List[Tuple[Any, Any, float, Any, bool, Any]],
        goal: Any,
        achieved_goals: List[Any]
    ):
        for t, (state, action, reward, next_state, done, info) in enumerate(trajectory):
            exp = Experience(
                state={"observation": state, "goal": goal},
                action=action,
                reward=reward,
                next_state={"observation": next_state, "goal": goal},
                done=done,
                metadata=info
            )
            self.replay_buffer.add(exp)
            
            for _ in range(self.k):
                future_goal = self._sample_future_goal(t, achieved_goals)
                if future_goal is not None:
                    new_reward = self._compute_reward(next_state, future_goal)
                    her_exp = Experience(
                        state={"observation": state, "goal": future_goal},
                        action=action,
                        reward=new_reward,
                        next_state={"observation": next_state, "goal": future_goal},
                        done=new_reward == 0,
                        metadata={"her": True}
                    )
                    self.replay_buffer.add(her_exp)
                    
    def _sample_future_goal(self, t: int, achieved_goals: List[Any]) -> Optional[Any]:
        if self.strategy == "future":
            future_indices = [i for i in range(t, len(achieved_goals))]
            if not future_indices:
                return None
            idx = random.choice(future_indices)
            return achieved_goals[idx]
        elif self.strategy == "episode":
            return random.choice(achieved_goals)
        return None
        
    def _compute_reward(self, state: Any, goal: Any) -> float:
        return -1.0 if not self._goal_reached(state, goal) else 0.0
        
    def _goal_reached(self, state: Any, goal: Any) -> bool:
        return state == goal


class EpisodeBuffer:
    def __init__(self, capacity: int = 1000):
        self.capacity = capacity
        self.episodes: List[List[Experience]] = []
        self.total_experiences = 0
        
    def add_episode(self, episode: List[Experience]):
        if len(self.episodes) >= self.capacity:
            removed = self.episodes.pop(0)
            self.total_experiences -= len(removed)
            
        self.episodes.append(episode)
        self.total_experiences += len(episode)
        
    def sample_episode(self) -> List[Experience]:
        return random.choice(self.episodes)
        
    def sample_episodes(self, n: int) -> List[List[Experience]]:
        return random.sample(self.episodes, min(n, len(self.episodes)))
        
    def __len__(self) -> int:
        return len(self.episodes)


class ReplayBufferStats:
    def __init__(self):
        self.additions = 0
        self.samples = 0
        self.priority_updates = 0
        self.mean_td_error = 0.0
        self.max_td_error = 0.0
        
    def record_addition(self, td_error: float = 0.0):
        self.additions += 1
        self._update_td_stats(td_error)
        
    def record_sample(self, batch_size: int):
        self.samples += batch_size
        
    def record_priority_update(self, td_errors: np.ndarray):
        self.priority_updates += len(td_errors)
        if len(td_errors) > 0:
            self._update_td_stats(float(np.mean(np.abs(td_errors))))
            
    def _update_td_stats(self, td_error: float):
        self.mean_td_error = 0.99 * self.mean_td_error + 0.01 * abs(td_error)
        self.max_td_error = max(self.max_td_error, abs(td_error))
        
    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_additions": self.additions,
            "total_samples": self.samples,
            "total_priority_updates": self.priority_updates,
            "mean_td_error": round(self.mean_td_error, 4),
            "max_td_error": round(self.max_td_error, 4)
        }


def create_prioritized_replay(
    capacity: int = 100000,
    n_steps: int = 3,
    alpha: float = 0.6,
    beta_start: float = 0.4
) -> NStepPrioritizedReplay:
    return NStepPrioritizedReplay(
        capacity=capacity,
        n_steps=n_steps,
        alpha=alpha,
        beta_start=beta_start
    )
