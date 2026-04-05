"""
活体强化模块
Living Enhancement Module

实现情感认知模型、抗污染记忆系统、元认知增强与经验蒸馏
"""

import asyncio
import copy
import hashlib
import json
import logging
import random
import threading
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class EmotionType(Enum):
    """情感类型"""
    TRUST = "trust"
    URGENCY = "urgency"
    EMPATHY = "empathy"
    CURIOSITY = "curiosity"
    SATISFACTION = "satisfaction"
    FRUSTRATION = "frustration"


class EventType(Enum):
    """事件类型"""
    USER_PRAISE = "user_praise"
    USER_COMPLAINT = "user_complaint"
    TASK_SUCCESS = "task_success"
    TASK_FAILURE = "task_failure"
    DEADLINE_APPROACH = "deadline_approach"
    USER_EMOTION_DETECTED = "user_emotion_detected"
    COLLABORATION_SUCCESS = "collaboration_success"
    COLLABORATION_CONFLICT = "collaboration_conflict"


class MemorySource(Enum):
    """记忆来源"""
    USER_INPUT = "user_input"
    API_RESPONSE = "api_response"
    AGENT_GENERATED = "agent_generated"
    SYSTEM_EVENT = "system_event"
    EXTERNAL_DATA = "external_data"


@dataclass
class EmotionState:
    """情感状态"""
    trust: float = 0.5
    urgency: float = 0.0
    empathy: float = 0.5
    curiosity: float = 0.5
    satisfaction: float = 0.5
    frustration: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_vector(self) -> List[float]:
        return [self.trust, self.urgency, self.empathy, self.curiosity, self.satisfaction, self.frustration]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "trust": self.trust,
            "urgency": self.urgency,
            "empathy": self.empathy,
            "curiosity": self.curiosity,
            "satisfaction": self.satisfaction,
            "frustration": self.frustration,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class EmotionEvent:
    """情感事件"""
    event_id: str
    event_type: EventType
    emotion_changes: Dict[str, float]
    trigger: str
    context: Dict[str, Any]
    timestamp: datetime


@dataclass
class ValidatedMemory:
    """验证后的记忆"""
    memory_id: str
    content: str
    source: MemorySource
    source_reliability: float
    cross_validated: bool
    validation_sources: List[str]
    confidence: float
    created_at: datetime
    access_count: int = 0
    last_accessed: Optional[datetime] = None


@dataclass
class ExperienceTuple:
    """经验元组"""
    experience_id: str
    state: Dict[str, Any]
    action: Dict[str, Any]
    reward: float
    failure_reason: Optional[str]
    success: bool
    improvement_suggestion: Optional[str]
    created_at: datetime


@dataclass
class DistilledRule:
    """蒸馏规则"""
    rule_id: str
    pattern: str
    action: str
    confidence: float
    occurrence_count: int
    success_rate: float
    created_at: datetime
    last_applied: Optional[datetime] = None


class EmotionModule:
    """情感模块"""
    
    def __init__(self, decay_rate: float = 0.001):
        self.decay_rate = decay_rate
        self.current_state = EmotionState()
        self.emotion_history: deque = deque(maxlen=1000)
        self.event_handlers: Dict[EventType, Callable] = {}
        self._lock = threading.Lock()
        self.stats = {
            "total_events": 0,
            "emotion_updates": 0,
            "by_event_type": defaultdict(int),
        }
        
        self._init_handlers()
    
    def _init_handlers(self):
        """初始化事件处理器"""
        self.event_handlers = {
            EventType.USER_PRAISE: self._handle_praise,
            EventType.USER_COMPLAINT: self._handle_complaint,
            EventType.TASK_SUCCESS: self._handle_task_success,
            EventType.TASK_FAILURE: self._handle_task_failure,
            EventType.DEADLINE_APPROACH: self._handle_deadline,
            EventType.USER_EMOTION_DETECTED: self._handle_user_emotion,
            EventType.COLLABORATION_SUCCESS: self._handle_collab_success,
            EventType.COLLABORATION_CONFLICT: self._handle_collab_conflict,
        }
    
    def update_emotion(self, event_type: EventType, context: Dict[str, Any] = None):
        """更新情感"""
        self.stats["total_events"] += 1
        self.stats["by_event_type"][event_type.value] += 1
        
        handler = self.event_handlers.get(event_type)
        if handler:
            changes = handler(context or {})
            self._apply_changes(changes, event_type, context)
    
    def _handle_praise(self, context: Dict[str, Any]) -> Dict[str, float]:
        return {
            "trust": 0.1,
            "satisfaction": 0.15,
            "frustration": -0.1,
        }
    
    def _handle_complaint(self, context: Dict[str, Any]) -> Dict[str, float]:
        return {
            "trust": -0.1,
            "satisfaction": -0.15,
            "frustration": 0.1,
        }
    
    def _handle_task_success(self, context: Dict[str, Any]) -> Dict[str, float]:
        return {
            "satisfaction": 0.1,
            "curiosity": 0.05,
            "frustration": -0.05,
        }
    
    def _handle_task_failure(self, context: Dict[str, Any]) -> Dict[str, float]:
        return {
            "satisfaction": -0.1,
            "frustration": 0.1,
            "curiosity": 0.1,
        }
    
    def _handle_deadline(self, context: Dict[str, Any]) -> Dict[str, float]:
        urgency_boost = context.get("urgency_boost", 0.2)
        return {
            "urgency": urgency_boost,
        }
    
    def _handle_user_emotion(self, context: Dict[str, Any]) -> Dict[str, float]:
        user_emotion = context.get("user_emotion", "neutral")
        empathy_change = 0.0
        
        if user_emotion in ["sad", "angry", "frustrated"]:
            empathy_change = 0.15
        elif user_emotion in ["happy", "excited"]:
            empathy_change = 0.05
        
        return {
            "empathy": empathy_change,
        }
    
    def _handle_collab_success(self, context: Dict[str, Any]) -> Dict[str, float]:
        return {
            "trust": 0.05,
            "satisfaction": 0.1,
        }
    
    def _handle_collab_conflict(self, context: Dict[str, Any]) -> Dict[str, float]:
        return {
            "trust": -0.05,
            "frustration": 0.05,
        }
    
    def _apply_changes(
        self,
        changes: Dict[str, float],
        event_type: EventType,
        context: Dict[str, Any]
    ):
        """应用情感变化"""
        with self._lock:
            for attr, delta in changes.items():
                current_value = getattr(self.current_state, attr, 0.5)
                new_value = max(0.0, min(1.0, current_value + delta))
                setattr(self.current_state, attr, new_value)
            
            self.current_state.timestamp = datetime.now()
            self.stats["emotion_updates"] += 1
            
            event = EmotionEvent(
                event_id=f"emo_{int(time.time())}_{uuid.uuid4().hex[:8]}",
                event_type=event_type,
                emotion_changes=changes,
                trigger=str(event_type.value),
                context=context or {}
            )
            self.emotion_history.append(event)
    
    def decay(self):
        """情感衰减"""
        with self._lock:
            for attr in ["trust", "urgency", "empathy", "curiosity", "satisfaction", "frustration"]:
                current_value = getattr(self.current_state, attr, 0.5)
                if attr == "frustration":
                    new_value = max(0.0, current_value - self.decay_rate * 2)
                elif attr == "urgency":
                    new_value = max(0.0, current_value - self.decay_rate * 3)
                else:
                    new_value = max(0.0, min(1.0, current_value - self.decay_rate * 0.5 + 0.0005))
                setattr(self.current_state, attr, new_value)
    
    def get_emotion_vector(self) -> List[float]:
        """获取情感向量"""
        with self._lock:
            return self.current_state.to_vector()
    
    def get_state(self) -> EmotionState:
        """获取情感状态"""
        with self._lock:
            return EmotionState(**self.current_state.to_dict())


class AntiPollutionMemorySystem:
    """抗污染记忆系统"""
    
    def __init__(self, min_sources: int = 2, confidence_threshold: float = 0.5):
        self.min_sources = min_sources
        self.confidence_threshold = confidence_threshold
        self.memories: Dict[str, ValidatedMemory] = {}
        self.source_reliability: Dict[str, float] = {
            MemorySource.USER_INPUT.value: 0.5,
            MemorySource.API_RESPONSE.value: 0.9,
            MemorySource.AGENT_GENERATED.value: 0.7,
            MemorySource.SYSTEM_EVENT.value: 0.95,
            MemorySource.EXTERNAL_DATA.value: 0.6,
        }
        self.user_risk_scores: Dict[str, float] = {}
        self._lock = threading.Lock()
        self.stats = {
            "total_memories": 0,
            "rejected_memories": 0,
            "validated_memories": 0,
            "cleaned_memories": 0,
        }
    
    def set_user_risk(self, user_id: str, risk_score: float):
        """设置用户风险分数"""
        self.user_risk_scores[user_id] = risk_score
    
    def validate_source(
        self,
        content: str,
        source: MemorySource,
        source_id: str,
        user_id: str = None
    ) -> Tuple[bool, float]:
        """验证来源"""
        base_reliability = self.source_reliability.get(source.value, 0.5)
        
        if source == MemorySource.USER_INPUT:
            if user_id:
                user_risk = self.user_risk_scores.get(user_id, 0.0)
                if user_risk > 80:
                    return False, 0.0
                base_reliability *= (1 - user_risk / 100)
        
        return True, base_reliability
    
    async def store_memory(
        self,
        content: str,
        source: MemorySource,
        source_id: str,
        user_id: str = None,
        additional_sources: List[str] = None
    ) -> Optional[ValidatedMemory]:
        """存储记忆"""
        is_valid, reliability = self.validate_source(content, source, source_id, user_id)
        
        if not is_valid:
            self.stats["rejected_memories"] += 1
            logger.warning(f"Memory rejected from source {source.value}")
            return None
        
        cross_validated = False
        validation_sources = [source_id]
        
        if additional_sources and len(additional_sources) >= self.min_sources - 1:
            cross_validated = True
            validation_sources.extend(additional_sources)
            reliability = min(1.0, reliability + 0.2)
        
        confidence = reliability
        if cross_validated:
            confidence = min(1.0, confidence + 0.1)
        
        memory_id = f"mem_{int(time.time())}_{hashlib.md5(content.encode()).hexdigest()[:8]}"
        
        memory = ValidatedMemory(
            memory_id=memory_id,
            content=content,
            source=source,
            source_reliability=reliability,
            cross_validated=cross_validated,
            validation_sources=validation_sources,
            confidence=confidence,
            created_at=datetime.now()
        )
        
        with self._lock:
            self.memories[memory_id] = memory
            self.stats["total_memories"] += 1
            if cross_validated:
                self.stats["validated_memories"] += 1
        
        return memory
    
    def retrieve_memory(
        self,
        query: str,
        min_confidence: float = None
    ) -> List[Tuple[ValidatedMemory, float]]:
        """检索记忆"""
        min_conf = min_confidence or self.confidence_threshold
        
        results = []
        with self._lock:
            for memory in self.memories.values():
                if memory.confidence >= min_conf:
                    relevance = self._calculate_relevance(query, memory.content)
                    if relevance > 0.1:
                        memory.access_count += 1
                        memory.last_accessed = datetime.now()
                        results.append((memory, relevance))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:10]
    
    def _calculate_relevance(self, query: str, content: str) -> float:
        """计算相关性"""
        query_words = set(query.lower().split())
        content_words = set(content.lower().split())
        
        if not query_words:
            return 0.0
        
        intersection = query_words & content_words
        return len(intersection) / len(query_words)
    
    async def cleanup_memories(self, days: int = 30, min_access: int = 5):
        """清理记忆"""
        cutoff = datetime.now() - timedelta(days=days)
        
        with self._lock:
            to_remove = []
            
            for memory_id, memory in self.memories.items():
                if (memory.confidence < 0.3 and 
                    memory.access_count < min_access and
                    memory.created_at < cutoff):
                    to_remove.append(memory_id)
            
            for memory_id in to_remove:
                del self.memories[memory_id]
            
            self.stats["cleaned_memories"] += len(to_remove)
        
        return len(to_remove)
    
    def get_memory_with_confidence(
        self,
        memory_id: str
    ) -> Tuple[Optional[ValidatedMemory], float]:
        """获取记忆及置信度"""
        with self._lock:
            memory = self.memories.get(memory_id)
            if memory:
                return memory, memory.confidence
            return None, 0.0


class ExperiencePool:
    """经验池"""
    
    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.experiences: deque = deque(maxlen=max_size)
        self.failure_patterns: Dict[str, int] = defaultdict(int)
        self.success_patterns: Dict[str, int] = defaultdict(int)
        self._lock = threading.Lock()
        self.stats = {
            "total_experiences": 0,
            "success_count": 0,
            "failure_count": 0,
        }
    
    def add_experience(
        self,
        state: Dict[str, Any],
        action: Dict[str, Any],
        reward: float,
        failure_reason: str = None,
        improvement_suggestion: str = None
    ) -> ExperienceTuple:
        """添加经验"""
        success = reward > 0 and failure_reason is None
        
        experience = ExperienceTuple(
            experience_id=f"exp_{int(time.time())}_{uuid.uuid4().hex[:8]}",
            state=state,
            action=action,
            reward=reward,
            failure_reason=failure_reason,
            success=success,
            improvement_suggestion=improvement_suggestion,
            created_at=datetime.now()
        )
        
        with self._lock:
            self.experiences.append(experience)
            self.stats["total_experiences"] += 1
            
            if success:
                self.stats["success_count"] += 1
                pattern = self._extract_pattern(state, action)
                self.success_patterns[pattern] += 1
            else:
                self.stats["failure_count"] += 1
                if failure_reason:
                    self.failure_patterns[failure_reason] += 1
        
        return experience
    
    def _extract_pattern(
        self,
        state: Dict[str, Any],
        action: Dict[str, Any]
    ) -> str:
        """提取模式"""
        state_key = str(sorted(state.keys())[:3])
        action_key = str(sorted(action.keys())[:3])
        return f"{state_key}:{action_key}"
    
    def get_similar_experiences(
        self,
        state: Dict[str, Any],
        limit: int = 10
    ) -> List[ExperienceTuple]:
        """获取相似经验"""
        results = []
        
        with self._lock:
            for exp in self.experiences:
                similarity = self._calculate_similarity(state, exp.state)
                if similarity > 0.5:
                    results.append((exp, similarity))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return [exp for exp, _ in results[:limit]]
    
    def _calculate_similarity(
        self,
        state1: Dict[str, Any],
        state2: Dict[str, Any]
    ) -> float:
        """计算相似度"""
        keys1 = set(state1.keys())
        keys2 = set(state2.keys())
        
        if not keys1 or not keys2:
            return 0.0
        
        common_keys = keys1 & keys2
        if not common_keys:
            return 0.0
        
        similarity = len(common_keys) / max(len(keys1), len(keys2))
        return similarity
    
    def get_failure_patterns(self, top_n: int = 10) -> List[Tuple[str, int]]:
        """获取失败模式"""
        with self._lock:
            sorted_patterns = sorted(
                self.failure_patterns.items(),
                key=lambda x: x[1],
                reverse=True
            )
            return sorted_patterns[:top_n]


class Distiller:
    """经验蒸馏器"""
    
    def __init__(self, experience_pool: ExperiencePool):
        self.experience_pool = experience_pool
        self.distilled_rules: Dict[str, DistilledRule] = {}
        self._lock = threading.Lock()
        self.stats = {
            "total_distillations": 0,
            "rules_created": 0,
            "rules_applied": 0,
        }
    
    async def distill_rules(self) -> List[DistilledRule]:
        """蒸馏规则"""
        self.stats["total_distillations"] += 1
        
        failure_patterns = self.experience_pool.get_failure_patterns()
        success_patterns = sorted(
            self.experience_pool.success_patterns.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        new_rules = []
        
        for pattern, count in failure_patterns:
            if count >= 3:
                rule = self._create_rule_from_failure(pattern, count)
                if rule:
                    new_rules.append(rule)
        
        for pattern, count in success_patterns:
            if count >= 5:
                rule = self._create_rule_from_success(pattern, count)
                if rule:
                    new_rules.append(rule)
        
        with self._lock:
            for rule in new_rules:
                self.distilled_rules[rule.rule_id] = rule
                self.stats["rules_created"] += 1
        
        return new_rules
    
    def _create_rule_from_failure(
        self,
        pattern: str,
        count: int
    ) -> Optional[DistilledRule]:
        """从失败模式创建规则"""
        rule_id = f"rule_fail_{hashlib.md5(pattern.encode()).hexdigest()[:8]}"
        
        return DistilledRule(
            rule_id=rule_id,
            pattern=pattern,
            action=f"avoid_{pattern}",
            confidence=min(0.9, count / 10),
            occurrence_count=count,
            success_rate=0.0,
            created_at=datetime.now()
        )
    
    def _create_rule_from_success(
        self,
        pattern: str,
        count: int
    ) -> Optional[DistilledRule]:
        """从成功模式创建规则"""
        rule_id = f"rule_success_{hashlib.md5(pattern.encode()).hexdigest()[:8]}"
        
        return DistilledRule(
            rule_id=rule_id,
            pattern=pattern,
            action=f"apply_{pattern}",
            confidence=min(0.9, count / 20),
            occurrence_count=count,
            success_rate=count / (count + 5),
            created_at=datetime.now()
        )
    
    def get_applicable_rules(
        self,
        state: Dict[str, Any]
    ) -> List[DistilledRule]:
        """获取适用规则"""
        applicable = []
        
        with self._lock:
            for rule in self.distilled_rules.values():
                if self._is_applicable(rule, state):
                    applicable.append(rule)
        
        applicable.sort(key=lambda x: x.confidence, reverse=True)
        return applicable[:5]
    
    def _is_applicable(
        self,
        rule: DistilledRule,
        state: Dict[str, Any]
    ) -> bool:
        """判断规则是否适用"""
        return True
    
    def broadcast_rules(self, agents: List[Any]):
        """广播规则"""
        with self._lock:
            rules_list = list(self.distilled_rules.values())
        
        for agent in agents:
            if hasattr(agent, 'receive_rules'):
                agent.receive_rules(rules_list)
        
        self.stats["rules_applied"] += len(agents)


class MetaCognitionEnhanced:
    """增强元认知模块"""
    
    def __init__(self):
        self.experience_pool = ExperiencePool()
        self.distiller = Distiller(self.experience_pool)
        self.self_diagnosis_history: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        self.stats = {
            "total_diagnoses": 0,
            "issues_detected": 0,
            "improvements_suggested": 0,
        }
    
    async def analyze_failure(
        self,
        state: Dict[str, Any],
        action: Dict[str, Any],
        reward: float,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """分析失败"""
        failure_reason = self._identify_failure_reason(state, action, reward, context)
        improvement = self._generate_improvement(failure_reason, context)
        
        self.experience_pool.add_experience(
            state=state,
            action=action,
            reward=reward,
            failure_reason=failure_reason,
            improvement_suggestion=improvement
        )
        
        return {
            "failure_reason": failure_reason,
            "improvement_suggestion": improvement,
            "similar_failures": len([
                e for e in self.experience_pool.experiences
                if e.failure_reason == failure_reason
            ])
        }
    
    def _identify_failure_reason(
        self,
        state: Dict[str, Any],
        action: Dict[str, Any],
        reward: float,
        context: Dict[str, Any]
    ) -> str:
        """识别失败原因"""
        if reward < -0.5:
            return "severe_negative_outcome"
        elif action.get("type") == "invalid":
            return "invalid_action"
        elif state.get("blocked", False):
            return "blocked_state"
        else:
            return "unknown_failure"
    
    def _generate_improvement(
        self,
        failure_reason: str,
        context: Dict[str, Any]
    ) -> str:
        """生成改进建议"""
        improvements = {
            "severe_negative_outcome": "Review action selection policy",
            "invalid_action": "Validate action before execution",
            "blocked_state": "Check state constraints before acting",
            "unknown_failure": "Gather more diagnostic information",
        }
        return improvements.get(failure_reason, "No specific improvement available")
    
    async def run_distillation(self) -> List[DistilledRule]:
        """运行蒸馏"""
        return await self.distiller.distill_rules()
    
    def get_relevant_experience(
        self,
        state: Dict[str, Any]
    ) -> List[ExperienceTuple]:
        """获取相关经验"""
        return self.experience_pool.get_similar_experiences(state)


class LivingEnhancementSystem:
    """活体强化系统主控"""
    
    def __init__(self):
        self.emotion_module = EmotionModule()
        self.anti_pollution_memory = AntiPollutionMemorySystem()
        self.meta_cognition = MetaCognitionEnhanced()
        
        self._running = False
        self._decay_task = None
    
    async def start(self):
        """启动系统"""
        self._running = True
        self._decay_task = asyncio.create_task(self._periodic_decay())
    
    def stop(self):
        """停止系统"""
        self._running = False
        if self._decay_task:
            self._decay_task.cancel()
    
    async def _periodic_decay(self):
        """定期衰减"""
        while self._running:
            self.emotion_module.decay()
            await asyncio.sleep(1)
    
    def update_emotion(self, event_type: EventType, context: Dict[str, Any] = None):
        """更新情感"""
        self.emotion_module.update_emotion(event_type, context)
    
    def get_emotion_vector(self) -> List[float]:
        """获取情感向量"""
        return self.emotion_module.get_emotion_vector()
    
    async def store_memory(
        self,
        content: str,
        source: MemorySource,
        source_id: str,
        user_id: str = None,
        additional_sources: List[str] = None
    ) -> Optional[ValidatedMemory]:
        """存储记忆"""
        return await self.anti_pollution_memory.store_memory(
            content, source, source_id, user_id, additional_sources
        )
    
    def retrieve_memory(
        self,
        query: str,
        min_confidence: float = None
    ) -> List[Tuple[ValidatedMemory, float]]:
        """检索记忆"""
        return self.anti_pollution_memory.retrieve_memory(query, min_confidence)
    
    async def analyze_failure(
        self,
        state: Dict[str, Any],
        action: Dict[str, Any],
        reward: float,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """分析失败"""
        return await self.meta_cognition.analyze_failure(state, action, reward, context)
    
    async def run_distillation(self) -> List[DistilledRule]:
        """运行蒸馏"""
        return await self.meta_cognition.run_distillation()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "emotion_module": self.emotion_module.stats,
            "anti_pollution_memory": self.anti_pollution_memory.stats,
            "meta_cognition": self.meta_cognition.stats,
            "experience_pool": self.meta_cognition.experience_pool.stats,
            "distiller": self.meta_cognition.distiller.stats,
        }
