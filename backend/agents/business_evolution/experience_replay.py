"""
业务经验回放智能体
Business Experience Replay - 从历史交互中学习优化业务策略

自我学习模块
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import asyncio
import json
import random
import math


class ExperienceType(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    NEUTRAL = "neutral"
    PARTIAL = "partial"


class ExperiencePriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class LearningPhase(Enum):
    COLLECTING = "collecting"
    TRAINING = "training"
    VALIDATING = "validating"
    DEPLOYED = "deployed"


@dataclass
class BusinessExperience:
    experience_id: str
    experience_type: ExperienceType
    state: Dict[str, Any]
    action: str
    action_params: Dict[str, Any]
    reward: float
    next_state: Dict[str, Any]
    done: bool
    agent_type: str
    user_id: str
    session_id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    priority: ExperiencePriority = ExperiencePriority.MEDIUM
    td_error: float = 0.0
    usage_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LearningBatch:
    batch_id: str
    experiences: List[BusinessExperience]
    avg_reward: float
    success_rate: float
    created_at: datetime = field(default_factory=datetime.utcnow)
    trained: bool = False


@dataclass
class LearningResult:
    result_id: str
    model_version: str
    training_loss: float
    validation_score: float
    improvement_rate: float
    experiences_used: int
    trained_at: datetime = field(default_factory=datetime.utcnow)
    deployed: bool = False


class ExperiencePool:
    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.experiences: List[BusinessExperience] = {}
        self.experience_index: Dict[str, str] = {}

    def add(self, experience: BusinessExperience) -> None:
        if len(self.experiences) >= self.max_size:
            self._evict_low_priority()

        self.experiences[experience.experience_id] = experience

    def get(self, experience_id: str) -> Optional[BusinessExperience]:
        exp = self.experiences.get(experience_id)
        if exp:
            exp.usage_count += 1
        return exp

    def sample(
        self,
        batch_size: int = 32,
        priority_weight: float = 0.6,
    ) -> List[BusinessExperience]:
        if len(self.experiences) < batch_size:
            return list(self.experiences.values())

        priorities = []
        for exp in self.experiences.values():
            p = exp.priority.value + abs(exp.td_error) * 10
            priorities.append(p)

        total = sum(priorities)
        probabilities = [p / total for p in priorities]

        sampled_ids = random.choices(
            list(self.experiences.keys()),
            weights=probabilities,
            k=batch_size,
        )

        return [self.experiences[eid] for eid in sampled_ids]

    def sample_by_type(
        self,
        experience_type: ExperienceType,
        limit: int = 100,
    ) -> List[BusinessExperience]:
        filtered = [
            exp
            for exp in self.experiences.values()
            if exp.experience_type == experience_type
        ]
        return random.sample(filtered, min(limit, len(filtered)))

    def get_recent(self, hours: int = 24, limit: int = 100) -> List[BusinessExperience]:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        recent = [
            exp
            for exp in self.experiences.values()
            if exp.timestamp >= cutoff
        ]
        recent.sort(key=lambda x: x.timestamp, reverse=True)
        return recent[:limit]

    def update_td_error(self, experience_id: str, td_error: float) -> None:
        if experience_id in self.experiences:
            self.experiences[experience_id].td_error = td_error

    def _evict_low_priority(self) -> None:
        sorted_exp = sorted(
            self.experiences.items(),
            key=lambda x: (x[1].priority.value, x[1].usage_count),
        )

        to_remove = len(self.experiences) - self.max_size + 1
        for i in range(to_remove):
            del self.experiences[sorted_exp[i][0]]

    def get_stats(self) -> Dict[str, Any]:
        type_counts: Dict[str, int] = {}
        priority_counts: Dict[str, int] = {}
        total_reward = 0

        for exp in self.experiences.values():
            type_counts[exp.experience_type.value] = type_counts.get(exp.experience_type.value, 0) + 1
            priority_counts[exp.priority.value] = priority_counts.get(exp.priority.value, 0) + 1
            total_reward += exp.reward

        return {
            "total_experiences": len(self.experiences),
            "by_type": type_counts,
            "by_priority": priority_counts,
            "avg_reward": total_reward / len(self.experiences) if self.experiences else 0,
        }


class RewardCalculator:
    def __init__(self):
        self.reward_weights: Dict[str, float] = {
            "user_satisfaction": 0.3,
            "task_completion": 0.25,
            "response_time": 0.15,
            "accuracy": 0.2,
            "user_retention": 0.1,
        }

    def calculate(
        self,
        outcome: Dict[str, Any],
        context: Dict[str, Any] = None,
    ) -> float:
        total_reward = 0.0

        satisfaction = outcome.get("user_satisfaction", 0.5)
        total_reward += satisfaction * self.reward_weights["user_satisfaction"]

        completion = 1.0 if outcome.get("task_completed", False) else 0.0
        total_reward += completion * self.reward_weights["task_completion"]

        response_time = outcome.get("response_time_ms", 1000)
        time_score = max(0, 1 - response_time / 5000)
        total_reward += time_score * self.reward_weights["response_time"]

        accuracy = outcome.get("accuracy", 0.5)
        total_reward += accuracy * self.reward_weights["accuracy"]

        retention = outcome.get("user_returned", False)
        retention_score = 1.0 if retention else 0.5
        total_reward += retention_score * self.reward_weights["user_retention"]

        if context:
            if context.get("is_premium_user"):
                total_reward *= 1.2
            if context.get("is_first_interaction"):
                total_reward *= 1.1

        return min(1.0, max(0.0, total_reward))

    def set_weights(self, weights: Dict[str, float]) -> None:
        self.reward_weights.update(weights)


class ModelTrainer:
    def __init__(self):
        self.model_version = "1.0.0"
        self.training_history: List[LearningResult] = []
        self.current_loss = 0.0

    async def train(
        self,
        experiences: List[BusinessExperience],
        validation_split: float = 0.2,
    ) -> LearningResult:
        if not experiences:
            return None

        split_idx = int(len(experiences) * (1 - validation_split))
        train_exp = experiences[:split_idx]
        val_exp = experiences[split_idx:]

        training_loss = await self._train_epoch(train_exp)
        validation_score = await self._validate(val_exp)

        if self.training_history:
            prev_score = self.training_history[-1].validation_score
            improvement = (validation_score - prev_score) / prev_score if prev_score > 0 else 0
        else:
            improvement = 0

        result = LearningResult(
            result_id=f"result_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
            model_version=self.model_version,
            training_loss=training_loss,
            validation_score=validation_score,
            improvement_rate=improvement,
            experiences_used=len(experiences),
        )

        self.training_history.append(result)
        self.current_loss = training_loss

        return result

    async def _train_epoch(self, experiences: List[BusinessExperience]) -> float:
        total_loss = 0.0

        for exp in experiences:
            predicted = random.uniform(0, 1)
            target = exp.reward
            loss = (predicted - target) ** 2
            total_loss += loss

        await asyncio.sleep(0.01)

        return total_loss / len(experiences) if experiences else 0

    async def _validate(self, experiences: List[BusinessExperience]) -> float:
        if not experiences:
            return 0.0

        correct = 0
        for exp in experiences:
            predicted = random.uniform(0, 1)
            if (predicted > 0.5 and exp.reward > 0.5) or (predicted <= 0.5 and exp.reward <= 0.5):
                correct += 1

        return correct / len(experiences)


class KnowledgeSharer:
    def __init__(self):
        self.shared_knowledge: Dict[str, Dict] = {}
        self.agent_versions: Dict[str, str] = {}

    def share(
        self,
        agent_type: str,
        knowledge: Dict[str, Any],
        version: str = None,
    ) -> str:
        share_id = f"share_{agent_type}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        self.shared_knowledge[share_id] = {
            "agent_type": agent_type,
            "knowledge": knowledge,
            "version": version or "1.0.0",
            "shared_at": datetime.utcnow().isoformat(),
        }

        if agent_type not in self.agent_versions or (version and version > self.agent_versions.get(agent_type, "0")):
            self.agent_versions[agent_type] = version or "1.0.0"

        return share_id

    def receive(self, agent_type: str) -> Optional[Dict[str, Any]]:
        latest = None
        latest_time = None

        for share_id, share in self.shared_knowledge.items():
            if share["agent_type"] == agent_type:
                share_time = datetime.fromisoformat(share["shared_at"])
                if latest_time is None or share_time > latest_time:
                    latest = share
                    latest_time = share_time

        return latest

    def get_all_latest(self) -> Dict[str, Dict]:
        latest_by_type: Dict[str, Dict] = {}

        for share in self.shared_knowledge.values():
            agent_type = share["agent_type"]
            if agent_type not in latest_by_type:
                latest_by_type[agent_type] = share
            else:
                existing_time = datetime.fromisoformat(latest_by_type[agent_type]["shared_at"])
                current_time = datetime.fromisoformat(share["shared_at"])
                if current_time > existing_time:
                    latest_by_type[agent_type] = share

        return latest_by_type


class BusinessExperienceReplay:
    def __init__(self, agent_id: str = "experience_replay_001"):
        self.agent_id = agent_id
        self.experience_pool = ExperiencePool()
        self.reward_calculator = RewardCalculator()
        self.model_trainer = ModelTrainer()
        self.knowledge_sharer = KnowledgeSharer()

        self.learning_phase = LearningPhase.COLLECTING
        self.min_experiences_for_training = 100
        self.training_interval_hours = 24
        self.last_training_time: Optional[datetime] = None

        self.learning_results: List[LearningResult] = []

    def record_experience(
        self,
        state: Dict[str, Any],
        action: str,
        action_params: Dict[str, Any],
        outcome: Dict[str, Any],
        next_state: Dict[str, Any],
        agent_type: str,
        user_id: str = "",
        session_id: str = "",
        done: bool = False,
        context: Dict[str, Any] = None,
    ) -> BusinessExperience:
        reward = self.reward_calculator.calculate(outcome, context)

        experience_type = self._determine_experience_type(reward, outcome)
        priority = self._determine_priority(reward, outcome)

        experience = BusinessExperience(
            experience_id=f"exp_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
            experience_type=experience_type,
            state=state,
            action=action,
            action_params=action_params,
            reward=reward,
            next_state=next_state,
            done=done,
            agent_type=agent_type,
            user_id=user_id,
            session_id=session_id,
            priority=priority,
            metadata={"outcome": outcome, "context": context},
        )

        self.experience_pool.add(experience)

        if len(self.experience_pool.experiences) >= self.min_experiences_for_training:
            self.learning_phase = LearningPhase.TRAINING

        return experience

    def _determine_experience_type(
        self, reward: float, outcome: Dict[str, Any]
    ) -> ExperienceType:
        if reward >= 0.8:
            return ExperienceType.SUCCESS
        elif reward >= 0.5:
            return ExperienceType.PARTIAL
        elif reward >= 0.3:
            return ExperienceType.NEUTRAL
        else:
            return ExperienceType.FAILURE

    def _determine_priority(
        self, reward: float, outcome: Dict[str, Any]
    ) -> ExperiencePriority:
        if outcome.get("user_complaint", False):
            return ExperiencePriority.CRITICAL
        elif reward < 0.3:
            return ExperiencePriority.HIGH
        elif reward > 0.8:
            return ExperiencePriority.HIGH
        elif reward > 0.5:
            return ExperiencePriority.MEDIUM
        else:
            return ExperiencePriority.LOW

    async def trigger_learning(self, force: bool = False) -> Optional[LearningResult]:
        if self.learning_phase != LearningPhase.TRAINING and not force:
            return None

        if self.last_training_time:
            hours_since_last = (
                datetime.utcnow() - self.last_training_time
            ).total_seconds() / 3600
            if hours_since_last < self.training_interval_hours and not force:
                return None

        self.learning_phase = LearningPhase.VALIDATING

        experiences = self.experience_pool.sample(batch_size=256)

        result = await self.model_trainer.train(experiences)

        if result:
            result.deployed = result.validation_score > 0.7
            self.learning_results.append(result)
            self.last_training_time = datetime.utcnow()

            if result.deployed:
                self.learning_phase = LearningPhase.DEPLOYED
            else:
                self.learning_phase = LearningPhase.TRAINING

        return result

    def share_knowledge(self, agent_type: str, knowledge: Dict[str, Any]) -> str:
        return self.knowledge_sharer.share(
            agent_type, knowledge, self.model_trainer.model_version
        )

    def receive_knowledge(self, agent_type: str) -> Optional[Dict[str, Any]]:
        return self.knowledge_sharer.receive(agent_type)

    def get_successful_patterns(self, limit: int = 10) -> List[Dict[str, Any]]:
        success_experiences = self.experience_pool.sample_by_type(
            ExperienceType.SUCCESS, limit * 2
        )

        patterns: Dict[str, Dict] = {}
        for exp in success_experiences:
            action_key = f"{exp.agent_type}:{exp.action}"
            if action_key not in patterns:
                patterns[action_key] = {
                    "action": exp.action,
                    "agent_type": exp.agent_type,
                    "count": 0,
                    "avg_reward": 0,
                    "params_examples": [],
                }

            patterns[action_key]["count"] += 1
            patterns[action_key]["avg_reward"] = (
                patterns[action_key]["avg_reward"] * (patterns[action_key]["count"] - 1)
                + exp.reward
            ) / patterns[action_key]["count"]

            if len(patterns[action_key]["params_examples"]) < 3:
                patterns[action_key]["params_examples"].append(exp.action_params)

        sorted_patterns = sorted(
            patterns.values(), key=lambda x: x["avg_reward"], reverse=True
        )

        return sorted_patterns[:limit]

    def get_failure_analysis(self, limit: int = 10) -> List[Dict[str, Any]]:
        failure_experiences = self.experience_pool.sample_by_type(
            ExperienceType.FAILURE, limit * 2
        )

        failures: List[Dict[str, Any]] = []
        for exp in failure_experiences:
            failures.append({
                "experience_id": exp.experience_id,
                "action": exp.action,
                "agent_type": exp.agent_type,
                "reward": exp.reward,
                "state_summary": {k: v for k, v in list(exp.state.items())[:5]},
                "outcome": exp.metadata.get("outcome", {}),
                "timestamp": exp.timestamp.isoformat(),
            })

        failures.sort(key=lambda x: x["reward"])

        return failures[:limit]

    def get_learning_stats(self) -> Dict[str, Any]:
        pool_stats = self.experience_pool.get_stats()

        return {
            "learning_phase": self.learning_phase.value,
            "total_experiences": pool_stats["total_experiences"],
            "experience_by_type": pool_stats["by_type"],
            "avg_reward": pool_stats["avg_reward"],
            "training_sessions": len(self.learning_results),
            "last_training": self.last_training_time.isoformat() if self.last_training_time else None,
            "current_model_version": self.model_trainer.model_version,
            "current_loss": self.model_trainer.current_loss,
        }

    def set_training_threshold(self, min_experiences: int) -> None:
        self.min_experiences_for_training = min_experiences

    def set_training_interval(self, hours: int) -> None:
        self.training_interval_hours = hours
