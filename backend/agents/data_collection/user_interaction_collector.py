"""
用户交互数据采集智能体
采集用户与平台的交互数据（咨询记录、任务请求、反馈）
"""
import asyncio
import hashlib
import json
import re
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

from pydantic import BaseModel, Field

from .data_collector import DataCollectorAgent, CollectionResult


class InteractionType(str, Enum):
    CONSULTATION = "consultation"
    TASK_REQUEST = "task_request"
    FEEDBACK = "feedback"
    BEHAVIOR_LOG = "behavior_log"
    COMPLAINT = "complaint"


class FeedbackType(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class UserInteractionSample(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    interaction_type: InteractionType
    user_id_hash: str
    session_id: str
    content: Dict[str, Any]
    feedback: Optional[FeedbackType] = None
    feedback_detail: Optional[str] = None
    behavior_metrics: Dict[str, Any] = Field(default_factory=dict)
    privacy_level: str = "anonymized"
    importance_score: float = 0.5
    collected_at: datetime = Field(default_factory=datetime.now)
    tags: List[str] = Field(default_factory=list)


class PrivacyProtector:
    SENSITIVE_PATTERNS = [
        (r'\b\d{17}[\dXx]\b', '[ID_CARD]'),
        (r'\b1[3-9]\d{9}\b', '[PHONE]'),
        (r'\b[\w\.-]+@[\w\.-]+\.\w+\b', '[EMAIL]'),
        (r'\b[\u4e00-\u9fa5]{2,4}\b', '[NAME]'),
        (r'\b\d{4}[-\s]?\d{1,2}[-\s]?\d{1,2}\b', '[DATE]'),
    ]
    
    @classmethod
    def hash_identifier(cls, identifier: str, salt: str = "fangdudu") -> str:
        return hashlib.sha256(f"{salt}{identifier}".encode()).hexdigest()[:16]
    
    @classmethod
    def anonymize_content(cls, content: str) -> str:
        anonymized = content
        for pattern, replacement in cls.SENSITIVE_PATTERNS:
            anonymized = re.sub(pattern, replacement, anonymized)
        return anonymized
    
    @classmethod
    def anonymize_dict(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        result = {}
        for key, value in data.items():
            if isinstance(value, str):
                result[key] = cls.anonymize_content(value)
            elif isinstance(value, dict):
                result[key] = cls.anonymize_dict(value)
            elif isinstance(value, list):
                result[key] = [
                    cls.anonymize_content(item) if isinstance(item, str) else item
                    for item in value
                ]
            else:
                result[key] = value
        return result


class ImportanceEvaluator:
    def __init__(self):
        self.high_value_patterns = [
            r"投诉",
            r"不满意",
            r"错误",
            r"问题",
            r"建议",
        ]
        self.repeat_question_threshold = 3
        self.user_question_history: Dict[str, List[str]] = {}
    
    def evaluate_importance(
        self,
        interaction_type: InteractionType,
        content: Dict[str, Any],
        user_id_hash: str,
        feedback: Optional[FeedbackType] = None
    ) -> float:
        score = 0.5
        
        if feedback == FeedbackType.NEGATIVE:
            score += 0.3
        elif feedback == FeedbackType.POSITIVE:
            score += 0.1
        
        if interaction_type == InteractionType.COMPLAINT:
            score += 0.4
        
        content_str = json.dumps(content, ensure_ascii=False)
        for pattern in self.high_value_patterns:
            if re.search(pattern, content_str):
                score += 0.1
        
        if interaction_type == InteractionType.CONSULTATION:
            question_key = self._extract_question_key(content)
            if question_key:
                if user_id_hash not in self.user_question_history:
                    self.user_question_history[user_id_hash] = []
                
                similar_count = sum(
                    1 for q in self.user_question_history[user_id_hash]
                    if self._similarity(question_key, q) > 0.8
                )
                
                if similar_count >= self.repeat_question_threshold:
                    score += 0.2
                
                self.user_question_history[user_id_hash].append(question_key)
        
        return min(1.0, score)
    
    def _extract_question_key(self, content: Dict[str, Any]) -> Optional[str]:
        if "query" in content:
            return content["query"][:50]
        if "question" in content:
            return content["question"][:50]
        return None
    
    def _similarity(self, text1: str, text2: str) -> float:
        words1 = set(text1)
        words2 = set(text2)
        if not words1 or not words2:
            return 0.0
        intersection = words1 & words2
        union = words1 | words2
        return len(intersection) / len(union)


class UserInteractionCollectorAgent(DataCollectorAgent):
    def __init__(
        self,
        agent_id: str,
        name: str = "UserInteractionCollector",
        event_bus: Optional[Any] = None,
        sample_repository: Optional[Any] = None,
        **kwargs
    ):
        super().__init__(
            agent_id=agent_id,
            name=name,
            source_type="user_interaction",
            **kwargs
        )
        self.event_bus = event_bus
        self.sample_repository = sample_repository
        self.privacy_protector = PrivacyProtector()
        self.importance_evaluator = ImportanceEvaluator()
        self._event_handlers: Dict[str, callable] = {}
        self._collection_buffer: List[UserInteractionSample] = []
        self._buffer_size = 100
        self._flush_interval = 60
    
    async def initialize(self):
        await super().initialize()
        self._register_event_handlers()
        self.logger.info(f"UserInteractionCollector {self.agent_id} initialized")
    
    def _register_event_handlers(self):
        if self.event_bus:
            self.event_bus.subscribe("user.consultation", self._handle_consultation)
            self.event_bus.subscribe("user.task_request", self._handle_task_request)
            self.event_bus.subscribe("user.feedback", self._handle_feedback)
            self.event_bus.subscribe("user.behavior", self._handle_behavior)
            self.event_bus.subscribe("user.complaint", self._handle_complaint)
    
    async def collect(self) -> CollectionResult:
        try:
            if self._collection_buffer:
                samples = self._collection_buffer.copy()
                self._collection_buffer.clear()
                
                stored_count = 0
                for sample in samples:
                    if await self._store_sample(sample):
                        stored_count += 1
                
                return CollectionResult(
                    success=True,
                    data={"samples_stored": stored_count},
                    metadata={"buffer_flushed": True}
                )
            
            return CollectionResult(
                success=True,
                data={"samples_stored": 0},
                metadata={"buffer_empty": True}
            )
        except Exception as e:
            self.logger.error(f"Error collecting user interactions: {e}")
            return CollectionResult(
                success=False,
                error=str(e)
            )
    
    async def _handle_consultation(self, event: Dict[str, Any]):
        try:
            user_id = event.get("user_id", "anonymous")
            session_id = event.get("session_id", str(uuid4()))
            query = event.get("query", "")
            response = event.get("response", "")
            feedback = event.get("feedback")
            
            sample = UserInteractionSample(
                interaction_type=InteractionType.CONSULTATION,
                user_id_hash=self.privacy_protector.hash_identifier(user_id),
                session_id=session_id,
                content={
                    "query": self.privacy_protector.anonymize_content(query),
                    "response_summary": response[:200] if response else "",
                    "timestamp": datetime.now().isoformat()
                },
                feedback=FeedbackType(feedback) if feedback else None,
                behavior_metrics={
                    "response_time": event.get("response_time", 0),
                    "query_length": len(query)
                },
                tags=["consultation", "user_query"]
            )
            
            sample.importance_score = self.importance_evaluator.evaluate_importance(
                sample.interaction_type,
                sample.content,
                sample.user_id_hash,
                sample.feedback
            )
            
            await self._add_to_buffer(sample)
            
        except Exception as e:
            self.logger.error(f"Error handling consultation event: {e}")
    
    async def _handle_task_request(self, event: Dict[str, Any]):
        try:
            user_id = event.get("user_id", "anonymous")
            session_id = event.get("session_id", str(uuid4()))
            task_type = event.get("task_type", "unknown")
            task_params = event.get("params", {})
            result = event.get("result")
            feedback = event.get("feedback")
            
            sample = UserInteractionSample(
                interaction_type=InteractionType.TASK_REQUEST,
                user_id_hash=self.privacy_protector.hash_identifier(user_id),
                session_id=session_id,
                content={
                    "task_type": task_type,
                    "params": self.privacy_protector.anonymize_dict(task_params),
                    "result_summary": str(result)[:200] if result else None,
                    "success": event.get("success", False)
                },
                feedback=FeedbackType(feedback) if feedback else None,
                behavior_metrics={
                    "execution_time": event.get("execution_time", 0),
                    "task_complexity": event.get("complexity", "medium")
                },
                tags=["task_request", task_type]
            )
            
            sample.importance_score = self.importance_evaluator.evaluate_importance(
                sample.interaction_type,
                sample.content,
                sample.user_id_hash,
                sample.feedback
            )
            
            await self._add_to_buffer(sample)
            
        except Exception as e:
            self.logger.error(f"Error handling task request event: {e}")
    
    async def _handle_feedback(self, event: Dict[str, Any]):
        try:
            user_id = event.get("user_id", "anonymous")
            session_id = event.get("session_id", str(uuid4()))
            feedback_type = event.get("feedback_type", "neutral")
            target_id = event.get("target_id")
            detail = event.get("detail", "")
            
            feedback_enum = FeedbackType.POSITIVE if feedback_type == "positive" else (
                FeedbackType.NEGATIVE if feedback_type == "negative" else FeedbackType.NEUTRAL
            )
            
            sample = UserInteractionSample(
                interaction_type=InteractionType.FEEDBACK,
                user_id_hash=self.privacy_protector.hash_identifier(user_id),
                session_id=session_id,
                content={
                    "target_id": target_id,
                    "feedback_type": feedback_type,
                    "detail": self.privacy_protector.anonymize_content(detail) if detail else None
                },
                feedback=feedback_enum,
                feedback_detail=detail,
                tags=["feedback", feedback_type]
            )
            
            sample.importance_score = self.importance_evaluator.evaluate_importance(
                sample.interaction_type,
                sample.content,
                sample.user_id_hash,
                sample.feedback
            )
            
            await self._add_to_buffer(sample)
            
        except Exception as e:
            self.logger.error(f"Error handling feedback event: {e}")
    
    async def _handle_behavior(self, event: Dict[str, Any]):
        try:
            user_id = event.get("user_id", "anonymous")
            session_id = event.get("session_id", str(uuid4()))
            action = event.get("action", "")
            target = event.get("target", "")
            duration = event.get("duration", 0)
            
            sample = UserInteractionSample(
                interaction_type=InteractionType.BEHAVIOR_LOG,
                user_id_hash=self.privacy_protector.hash_identifier(user_id),
                session_id=session_id,
                content={
                    "action": action,
                    "target": target,
                    "page": event.get("page", "")
                },
                behavior_metrics={
                    "duration": duration,
                    "scroll_depth": event.get("scroll_depth", 0),
                    "click_count": event.get("click_count", 0)
                },
                tags=["behavior", action]
            )
            
            sample.importance_score = self.importance_evaluator.evaluate_importance(
                sample.interaction_type,
                sample.content,
                sample.user_id_hash
            )
            
            await self._add_to_buffer(sample)
            
        except Exception as e:
            self.logger.error(f"Error handling behavior event: {e}")
    
    async def _handle_complaint(self, event: Dict[str, Any]):
        try:
            user_id = event.get("user_id", "anonymous")
            session_id = event.get("session_id", str(uuid4()))
            complaint_type = event.get("complaint_type", "general")
            description = event.get("description", "")
            
            sample = UserInteractionSample(
                interaction_type=InteractionType.COMPLAINT,
                user_id_hash=self.privacy_protector.hash_identifier(user_id),
                session_id=session_id,
                content={
                    "complaint_type": complaint_type,
                    "description": self.privacy_protector.anonymize_content(description),
                    "related_task": event.get("related_task")
                },
                feedback=FeedbackType.NEGATIVE,
                tags=["complaint", complaint_type, "high_priority"]
            )
            
            sample.importance_score = 1.0
            
            await self._add_to_buffer(sample)
            
            await self._trigger_review(sample)
            
        except Exception as e:
            self.logger.error(f"Error handling complaint event: {e}")
    
    async def _add_to_buffer(self, sample: UserInteractionSample):
        self._collection_buffer.append(sample)
        self.collected_count += 1
        
        if len(self._collection_buffer) >= self._buffer_size:
            await self.collect()
    
    async def _store_sample(self, sample: UserInteractionSample) -> bool:
        if self.sample_repository:
            try:
                await self.sample_repository.store({
                    "id": sample.id,
                    "type": "user_interaction",
                    "interaction_type": sample.interaction_type.value,
                    "user_id_hash": sample.user_id_hash,
                    "session_id": sample.session_id,
                    "content": sample.content,
                    "feedback": sample.feedback.value if sample.feedback else None,
                    "behavior_metrics": sample.behavior_metrics,
                    "importance_score": sample.importance_score,
                    "tags": sample.tags,
                    "collected_at": sample.collected_at.isoformat(),
                    "source_agent_id": self.agent_id
                })
                return True
            except Exception as e:
                self.logger.error(f"Error storing sample: {e}")
                return False
        return True
    
    async def _trigger_review(self, sample: UserInteractionSample):
        self.logger.warning(
            f"Complaint received - Type: {sample.content.get('complaint_type')}, "
            f"Session: {sample.session_id}"
        )
    
    async def get_statistics(self) -> Dict[str, Any]:
        return {
            "total_collected": self.collected_count,
            "buffer_size": len(self._collection_buffer),
            "interaction_breakdown": {
                "consultation": sum(
                    1 for s in self._collection_buffer
                    if s.interaction_type == InteractionType.CONSULTATION
                ),
                "task_request": sum(
                    1 for s in self._collection_buffer
                    if s.interaction_type == InteractionType.TASK_REQUEST
                ),
                "feedback": sum(
                    1 for s in self._collection_buffer
                    if s.interaction_type == InteractionType.FEEDBACK
                ),
                "behavior": sum(
                    1 for s in self._collection_buffer
                    if s.interaction_type == InteractionType.BEHAVIOR_LOG
                ),
                "complaint": sum(
                    1 for s in self._collection_buffer
                    if s.interaction_type == InteractionType.COMPLAINT
                )
            }
        }
