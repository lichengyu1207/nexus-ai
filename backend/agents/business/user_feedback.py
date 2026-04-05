"""
用户反馈回路
User Feedback Loop

让业务智能体实时适应用户
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

logger = logging.getLogger(__name__)


class FeedbackType(Enum):
    LIKE = "like"
    DISLIKE = "dislike"
    COMPLAINT = "complaint"
    SHARE = "share"
    RATING = "rating"
    COMMENT = "comment"
    BEHAVIOR = "behavior"


class FeedbackSeverity(Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    CRITICAL = "critical"


@dataclass
class UserFeedback:
    feedback_id: str
    user_id: str
    agent_id: str
    task_id: str
    feedback_type: FeedbackType
    severity: FeedbackSeverity
    content: Optional[str]
    rating: Optional[float]
    metadata: Dict
    created_at: float
    processed: bool = False
    
    def to_dict(self) -> Dict:
        return {
            "feedback_id": self.feedback_id,
            "user_id": self.user_id,
            "agent_id": self.agent_id,
            "task_id": self.task_id,
            "feedback_type": self.feedback_type.value,
            "severity": self.severity.value,
            "content": self.content,
            "rating": self.rating,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "processed": self.processed
        }


@dataclass
class UserPreferenceModel:
    user_id: str
    preferences: Dict
    interaction_history: List[Dict]
    feedback_summary: Dict
    preferred_agents: List[str]
    preferred_styles: Dict
    last_updated: float
    
    def to_dict(self) -> Dict:
        return {
            "user_id": self.user_id,
            "preferences": self.preferences,
            "interaction_history": self.interaction_history[-100:],
            "feedback_summary": self.feedback_summary,
            "preferred_agents": self.preferred_agents,
            "preferred_styles": self.preferred_styles,
            "last_updated": self.last_updated
        }


class UserFeedbackLoop:
    """
    用户反馈回路
    
    让业务智能体实时适应用户：
    1. 反馈采集：点赞、点踩、投诉、分享
    2. 反馈处理：奖励/扣除能量，触发诊断
    3. 个性化适应：维护用户偏好模型
    4. 长期适应：强化学习学习用户偏好
    """
    
    ENERGY_REWARDS = {
        FeedbackType.LIKE: 5,
        FeedbackType.DISLIKE: -5,
        FeedbackType.COMPLAINT: -20,
        FeedbackType.SHARE: 10,
        FeedbackType.RATING: 0,
    }
    
    SEVERITY_MULTIPLIERS = {
        FeedbackSeverity.POSITIVE: 1.0,
        FeedbackSeverity.NEUTRAL: 0.5,
        FeedbackSeverity.NEGATIVE: 1.5,
        FeedbackSeverity.CRITICAL: 2.0,
    }
    
    def __init__(
        self,
        memory_agent: Optional[Any] = None,
        blackboard: Optional[Any] = None,
        communication_bus: Optional[Any] = None,
    ):
        self.memory_agent = memory_agent
        self.blackboard = blackboard
        self.communication_bus = communication_bus
        
        self.feedbacks: Dict[str, UserFeedback] = {}
        self.user_preferences: Dict[str, UserPreferenceModel] = {}
        
        self.agent_feedback_queue: Dict[str, asyncio.Queue] = defaultdict(asyncio.Queue)
        self.feedback_handlers: Dict[FeedbackType, Callable] = {}
        
        self._lock = threading.RLock()
        self._running = False
        self._processing_task: Optional[asyncio.Task] = None
        
        self._register_default_handlers()
        
        self.stats = {
            "total_feedbacks": 0,
            "positive_feedbacks": 0,
            "negative_feedbacks": 0,
            "complaints": 0,
            "avg_response_time_ms": 0.0,
            "users_tracked": 0,
            "personalization_rate": 0.0,
        }
    
    def _register_default_handlers(self):
        self.feedback_handlers[FeedbackType.LIKE] = self._handle_like
        self.feedback_handlers[FeedbackType.DISLIKE] = self._handle_dislike
        self.feedback_handlers[FeedbackType.COMPLAINT] = self._handle_complaint
        self.feedback_handlers[FeedbackType.SHARE] = self._handle_share
        self.feedback_handlers[FeedbackType.RATING] = self._handle_rating
    
    async def start(self):
        self._running = True
        self._processing_task = asyncio.create_task(self._processing_loop())
        logger.info("User feedback loop started")
    
    async def stop(self):
        self._running = False
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
        logger.info("User feedback loop stopped")
    
    async def _processing_loop(self):
        while self._running:
            try:
                for agent_id, queue in list(self.agent_feedback_queue.items()):
                    try:
                        feedback = await asyncio.wait_for(
                            queue.get(),
                            timeout=0.1
                        )
                        await self._process_feedback(feedback)
                    except asyncio.TimeoutError:
                        continue
                
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in processing loop: {e}")
                await asyncio.sleep(5)
    
    async def submit_feedback(
        self,
        user_id: str,
        agent_id: str,
        task_id: str,
        feedback_type: FeedbackType,
        content: Optional[str] = None,
        rating: Optional[float] = None,
        metadata: Optional[Dict] = None,
    ) -> UserFeedback:
        feedback_id = f"fb_{uuid.uuid4().hex[:8]}"
        
        severity = self._determine_severity(feedback_type, rating)
        
        feedback = UserFeedback(
            feedback_id=feedback_id,
            user_id=user_id,
            agent_id=agent_id,
            task_id=task_id,
            feedback_type=feedback_type,
            severity=severity,
            content=content,
            rating=rating,
            metadata=metadata or {},
            created_at=time.time(),
        )
        
        with self._lock:
            self.feedbacks[feedback_id] = feedback
            self.stats["total_feedbacks"] += 1
            
            if severity == FeedbackSeverity.POSITIVE:
                self.stats["positive_feedbacks"] += 1
            elif severity in [FeedbackSeverity.NEGATIVE, FeedbackSeverity.CRITICAL]:
                self.stats["negative_feedbacks"] += 1
            
            if feedback_type == FeedbackType.COMPLAINT:
                self.stats["complaints"] += 1
        
        await self.agent_feedback_queue[agent_id].put(feedback)
        
        await self._update_user_preference(user_id, agent_id, feedback)
        
        if self.memory_agent:
            await self._store_feedback(feedback)
        
        logger.debug(f"Feedback submitted: {feedback_id} from user {user_id}")
        
        return feedback
    
    def _determine_severity(
        self,
        feedback_type: FeedbackType,
        rating: Optional[float],
    ) -> FeedbackSeverity:
        if feedback_type == FeedbackType.LIKE:
            return FeedbackSeverity.POSITIVE
        elif feedback_type == FeedbackType.COMPLAINT:
            return FeedbackSeverity.CRITICAL
        elif feedback_type == FeedbackType.DISLIKE:
            return FeedbackSeverity.NEGATIVE
        elif feedback_type == FeedbackType.RATING:
            if rating is not None:
                if rating >= 4:
                    return FeedbackSeverity.POSITIVE
                elif rating <= 2:
                    return FeedbackSeverity.NEGATIVE
        elif feedback_type == FeedbackType.SHARE:
            return FeedbackSeverity.POSITIVE
        
        return FeedbackSeverity.NEUTRAL
    
    async def _process_feedback(self, feedback: UserFeedback):
        start_time = time.time()
        
        handler = self.feedback_handlers.get(feedback.feedback_type)
        if handler:
            await handler(feedback)
        
        feedback.processed = True
        
        processing_time = (time.time() - start_time) * 1000
        old_avg = self.stats["avg_response_time_ms"]
        count = self.stats["total_feedbacks"]
        self.stats["avg_response_time_ms"] = (
            old_avg * (count - 1) + processing_time
        ) / count
    
    async def _handle_like(self, feedback: UserFeedback):
        energy_reward = self.ENERGY_REWARDS[FeedbackType.LIKE]
        await self._apply_energy_change(feedback.agent_id, energy_reward, "user_like")
    
    async def _handle_dislike(self, feedback: UserFeedback):
        energy_penalty = self.ENERGY_REWARDS[FeedbackType.DISLIKE]
        await self._apply_energy_change(feedback.agent_id, energy_penalty, "user_dislike")
    
    async def _handle_complaint(self, feedback: UserFeedback):
        energy_penalty = self.ENERGY_REWARDS[FeedbackType.COMPLAINT]
        await self._apply_energy_change(feedback.agent_id, energy_penalty, "user_complaint")
        
        await self._trigger_self_diagnosis(feedback.agent_id, feedback)
    
    async def _handle_share(self, feedback: UserFeedback):
        energy_reward = self.ENERGY_REWARDS[FeedbackType.SHARE]
        await self._apply_energy_change(feedback.agent_id, energy_reward, "user_share")
    
    async def _handle_rating(self, feedback: UserFeedback):
        if feedback.rating is not None:
            normalized_rating = feedback.rating / 5.0
            energy_change = (normalized_rating - 0.5) * 10
            await self._apply_energy_change(
                feedback.agent_id,
                energy_change,
                f"rating_{feedback.rating}"
            )
    
    async def _apply_energy_change(
        self,
        agent_id: str,
        amount: float,
        reason: str,
    ):
        logger.info(f"Energy change for agent {agent_id}: {amount} ({reason})")
    
    async def _trigger_self_diagnosis(
        self,
        agent_id: str,
        feedback: UserFeedback,
    ):
        logger.warning(f"Self-diagnosis triggered for agent {agent_id} due to complaint")
        
        if self.communication_bus:
            await self.communication_bus.send(
                to=agent_id,
                message={
                    "type": "self_diagnosis_request",
                    "feedback": feedback.to_dict(),
                    "timestamp": time.time()
                }
            )
    
    async def _update_user_preference(
        self,
        user_id: str,
        agent_id: str,
        feedback: UserFeedback,
    ):
        with self._lock:
            if user_id not in self.user_preferences:
                self.user_preferences[user_id] = UserPreferenceModel(
                    user_id=user_id,
                    preferences={},
                    interaction_history=[],
                    feedback_summary=defaultdict(int),
                    preferred_agents=[],
                    preferred_styles={},
                    last_updated=time.time()
                )
                self.stats["users_tracked"] += 1
            
            pref_model = self.user_preferences[user_id]
            
            pref_model.interaction_history.append({
                "agent_id": agent_id,
                "feedback_type": feedback.feedback_type.value,
                "timestamp": feedback.created_at,
            })
            
            pref_model.feedback_summary[feedback.feedback_type.value] += 1
            
            if feedback.feedback_type in [FeedbackType.LIKE, FeedbackType.SHARE]:
                if agent_id not in pref_model.preferred_agents:
                    pref_model.preferred_agents.append(agent_id)
            elif feedback.feedback_type in [FeedbackType.DISLIKE, FeedbackType.COMPLAINT]:
                if agent_id in pref_model.preferred_agents:
                    pref_model.preferred_agents.remove(agent_id)
            
            pref_model.last_updated = time.time()
    
    async def _store_feedback(self, feedback: UserFeedback):
        if self.memory_agent:
            try:
                await self.memory_agent.store({
                    "type": "user_feedback",
                    "feedback": feedback.to_dict(),
                    "timestamp": time.time()
                })
            except Exception as e:
                logger.error(f"Failed to store feedback: {e}")
    
    def get_feedback(self, feedback_id: str) -> Optional[UserFeedback]:
        return self.feedbacks.get(feedback_id)
    
    def get_user_feedbacks(
        self,
        user_id: str,
        limit: int = 50,
    ) -> List[UserFeedback]:
        user_feedbacks = [
            f for f in self.feedbacks.values()
            if f.user_id == user_id
        ]
        user_feedbacks.sort(key=lambda x: x.created_at, reverse=True)
        return user_feedbacks[:limit]
    
    def get_agent_feedbacks(
        self,
        agent_id: str,
        limit: int = 50,
    ) -> List[UserFeedback]:
        agent_feedbacks = [
            f for f in self.feedbacks.values()
            if f.agent_id == agent_id
        ]
        agent_feedbacks.sort(key=lambda x: x.created_at, reverse=True)
        return agent_feedbacks[:limit]
    
    def get_user_preference(self, user_id: str) -> Optional[UserPreferenceModel]:
        return self.user_preferences.get(user_id)
    
    def get_agent_preference_for_user(
        self,
        agent_id: str,
        user_id: str,
    ) -> Dict:
        pref_model = self.user_preferences.get(user_id)
        if not pref_model:
            return {}
        
        agent_feedbacks = [
            f for f in self.feedbacks.values()
            if f.agent_id == agent_id and f.user_id == user_id
        ]
        
        if not agent_feedbacks:
            return {}
        
        likes = sum(1 for f in agent_feedbacks if f.feedback_type == FeedbackType.LIKE)
        dislikes = sum(1 for f in agent_feedbacks if f.feedback_type == FeedbackType.DISLIKE)
        
        return {
            "total_interactions": len(agent_feedbacks),
            "likes": likes,
            "dislikes": dislikes,
            "satisfaction_ratio": likes / (likes + dislikes) if (likes + dislikes) > 0 else 0.5,
            "is_preferred": agent_id in pref_model.preferred_agents,
        }
    
    def get_stats(self) -> Dict:
        with self._lock:
            return {
                **self.stats,
                "total_feedbacks_stored": len(self.feedbacks),
                "pending_feedbacks": sum(
                    queue.qsize() for queue in self.agent_feedback_queue.values()
                ),
            }
