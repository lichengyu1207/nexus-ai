# -*- coding: utf-8 -*-
"""
Consultation Context Manager
Manages session context with Redis caching
"""
import json
import time
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
import redis.asyncio as redis
import os

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

@dataclass
class Message:
    role: str
    content: str
    timestamp: float = field(default_factory=time.time)
    intent: Optional[str] = None
    slots: Dict = field(default_factory=dict)
    emotion: Optional[str] = None

@dataclass
class ConsultationContext:
    session_id: str
    user_id: str
    gene_id: Optional[str] = None
    gene_name: str = "zhouyu"
    status: str = "active"
    intent: Optional[str] = None
    intent_confidence: float = 0.0
    slots: Dict = field(default_factory=dict)
    detected_issues: List = field(default_factory=list)
    emotion_state: Optional[str] = None
    emotion_score: float = 0.0
    current_stage: str = "init"
    message_count: int = 0
    messages: List[Message] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    
    def add_message(self, role: str, content: str, intent: str = None, 
                    slots: Dict = None, emotion: str = None):
        msg = Message(
            role=role,
            content=content,
            intent=intent,
            slots=slots or {},
            emotion=emotion
        )
        self.messages.append(msg)
        self.message_count = len(self.messages)
        self.updated_at = time.time()
        return msg
    
    def get_recent_messages(self, n: int = 10) -> List[Dict]:
        return [asdict(m) for m in self.messages[-n:]]
    
    def to_dict(self) -> Dict:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "gene_id": self.gene_id,
            "gene_name": self.gene_name,
            "status": self.status,
            "intent": self.intent,
            "intent_confidence": self.intent_confidence,
            "slots": self.slots,
            "detected_issues": self.detected_issues,
            "emotion_state": self.emotion_state,
            "emotion_score": self.emotion_score,
            "current_stage": self.current_stage,
            "message_count": self.message_count,
            "messages": [asdict(m) for m in self.messages],
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ConsultationContext":
        messages = [Message(**m) for m in data.pop("messages", [])]
        return cls(messages=messages, **data)


class ContextManager:
    _instance: Optional["ContextManager"] = None
    _redis: Optional[redis.Redis] = None
    
    CONTEXT_PREFIX = "consultation:context:"
    CONTEXT_TTL = 86400
    
    def __init__(self):
        self._local_cache: Dict[str, ConsultationContext] = {}
    
    @classmethod
    async def get_instance(cls) -> "ContextManager":
        if cls._instance is None:
            cls._instance = cls()
            await cls._instance._initialize()
        return cls._instance
    
    async def _initialize(self):
        try:
            self._redis = redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
            await self._redis.ping()
            logger.info("ContextManager connected to Redis")
        except Exception as e:
            logger.warning(f"Redis connection failed, using local cache: {e}")
            self._redis = None
    
    def _get_key(self, session_id: str) -> str:
        return f"{self.CONTEXT_PREFIX}{session_id}"
    
    async def create_context(self, session_id: str, user_id: str, 
                             gene_id: str = None, gene_name: str = "zhouyu") -> ConsultationContext:
        context = ConsultationContext(
            session_id=session_id,
            user_id=user_id,
            gene_id=gene_id,
            gene_name=gene_name
        )
        await self.save_context(context)
        return context
    
    async def get_context(self, session_id: str) -> Optional[ConsultationContext]:
        if session_id in self._local_cache:
            return self._local_cache[session_id]
        
        if self._redis:
            try:
                key = self._get_key(session_id)
                data = await self._redis.get(key)
                if data:
                    context = ConsultationContext.from_dict(json.loads(data))
                    self._local_cache[session_id] = context
                    return context
            except Exception as e:
                logger.warning(f"Failed to get context from Redis: {e}")
        
        return None
    
    async def save_context(self, context: ConsultationContext):
        context.updated_at = time.time()
        self._local_cache[context.session_id] = context
        
        if self._redis:
            try:
                key = self._get_key(context.session_id)
                await self._redis.setex(
                    key,
                    self.CONTEXT_TTL,
                    json.dumps(context.to_dict())
                )
            except Exception as e:
                logger.warning(f"Failed to save context to Redis: {e}")
    
    async def delete_context(self, session_id: str):
        if session_id in self._local_cache:
            del self._local_cache[session_id]
        
        if self._redis:
            try:
                key = self._get_key(session_id)
                await self._redis.delete(key)
            except Exception as e:
                logger.warning(f"Failed to delete context from Redis: {e}")
    
    async def add_message(self, session_id: str, role: str, content: str,
                          intent: str = None, slots: Dict = None, 
                          emotion: str = None) -> Optional[Message]:
        context = await self.get_context(session_id)
        if not context:
            return None
        
        msg = context.add_message(role, content, intent, slots, emotion)
        await self.save_context(context)
        return msg
    
    async def update_slots(self, session_id: str, slots: Dict):
        context = await self.get_context(session_id)
        if context:
            context.slots.update(slots)
            await self.save_context(context)
    
    async def update_stage(self, session_id: str, stage: str):
        context = await self.get_context(session_id)
        if context:
            context.current_stage = stage
            await self.save_context(context)
    
    async def update_intent(self, session_id: str, intent: str, confidence: float):
        context = await self.get_context(session_id)
        if context:
            context.intent = intent
            context.intent_confidence = confidence
            await self.save_context(context)
    
    async def update_emotion(self, session_id: str, emotion: str, score: float):
        context = await self.get_context(session_id)
        if context:
            context.emotion_state = emotion
            context.emotion_score = score
            await self.save_context(context)
    
    async def update_slots(self, session_id: str, slots: Dict):
        context = await self.get_context(session_id)
        if context:
            context.slots.update(slots)
            await self.save_context(context)
    
    async def add_detected_issue(self, session_id: str, issue: Dict):
        context = await self.get_context(session_id)
        if context:
            context.detected_issues.append(issue)
            await self.save_context(context)
    
    async def switch_gene(self, session_id: str, gene_id: str, gene_name: str):
        context = await self.get_context(session_id)
        if context:
            context.gene_id = gene_id
            context.gene_name = gene_name
            await self.save_context(context)
    
    async def get_context_summary(self, session_id: str) -> Dict:
        context = await self.get_context(session_id)
        if not context:
            return {}
        
        return {
            "session_id": context.session_id,
            "user_id": context.user_id,
            "gene_name": context.gene_name,
            "status": context.status,
            "intent": context.intent,
            "slots": context.slots,
            "current_stage": context.current_stage,
            "message_count": context.message_count,
            "emotion_state": context.emotion_state,
            "duration_seconds": int(time.time() - context.created_at)
        }


context_manager: Optional[ContextManager] = None


async def get_context_manager() -> ContextManager:
    global context_manager
    if context_manager is None:
        context_manager = await ContextManager.get_instance()
    return context_manager
