"""
记忆注意力机制 - 动态激活
根据当前对话上下文动态激活相关记忆片段，减少检索噪声
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import logging
import math
from collections import defaultdict

logger = logging.getLogger(__name__)


class MemoryType(Enum):
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"
    WORKING = "working"


class ActivationLevel(Enum):
    DORMANT = "dormant"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ACTIVE = "active"


@dataclass
class MemoryFragment:
    fragment_id: str
    agent_id: str
    memory_type: MemoryType
    content: str
    embedding: Optional[List[float]] = None
    keywords: List[str] = field(default_factory=list)
    entities: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    importance: float = 0.5
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    decay_rate: float = 0.1
    associations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    _activation_score: float = 0.0
    
    @property
    def activation_level(self) -> ActivationLevel:
        if self._activation_score >= 0.8:
            return ActivationLevel.ACTIVE
        elif self._activation_score >= 0.6:
            return ActivationLevel.HIGH
        elif self._activation_score >= 0.4:
            return ActivationLevel.MEDIUM
        elif self._activation_score >= 0.2:
            return ActivationLevel.LOW
        return ActivationLevel.DORMANT


@dataclass
class ContextState:
    session_id: str
    agent_id: str
    current_topic: Optional[str] = None
    active_entities: List[str] = field(default_factory=list)
    recent_keywords: List[str] = field(default_factory=list)
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    emotional_state: Optional[str] = None
    task_context: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class AttentionWeights:
    relevance_weight: float = 0.4
    recency_weight: float = 0.2
    importance_weight: float = 0.2
    frequency_weight: float = 0.1
    association_weight: float = 0.1


class AttentionCalculator:
    def __init__(self, weights: Optional[AttentionWeights] = None):
        self.weights = weights or AttentionWeights()
        
    def calculate_activation(
        self,
        fragment: MemoryFragment,
        context: ContextState,
        query_embedding: Optional[List[float]] = None
    ) -> float:
        relevance_score = self._calculate_relevance(fragment, context, query_embedding)
        recency_score = self._calculate_recency(fragment)
        importance_score = fragment.importance
        frequency_score = self._calculate_frequency(fragment)
        association_score = self._calculate_association(fragment, context)
        
        activation = (
            relevance_score * self.weights.relevance_weight +
            recency_score * self.weights.recency_weight +
            importance_score * self.weights.importance_weight +
            frequency_score * self.weights.frequency_weight +
            association_score * self.weights.association_weight
        )
        
        return min(activation, 1.0)
        
    def _calculate_relevance(
        self,
        fragment: MemoryFragment,
        context: ContextState,
        query_embedding: Optional[List[float]] = None
    ) -> float:
        keyword_overlap = 0.0
        if fragment.keywords and context.recent_keywords:
            overlap = set(fragment.keywords) & set(context.recent_keywords)
            keyword_overlap = len(overlap) / max(len(context.recent_keywords), 1)
            
        entity_match = 0.0
        if fragment.entities and context.active_entities:
            match = set(fragment.entities) & set(context.active_entities)
            entity_match = len(match) / max(len(context.active_entities), 1)
            
        semantic_similarity = 0.0
        if query_embedding and fragment.embedding:
            semantic_similarity = self._cosine_similarity(query_embedding, fragment.embedding)
            
        return max(keyword_overlap, entity_match, semantic_similarity)
        
    def _calculate_recency(self, fragment: MemoryFragment) -> float:
        if not fragment.last_accessed:
            return 0.0
            
        time_diff = (datetime.now() - fragment.last_accessed).total_seconds()
        hours = time_diff / 3600
        
        recency = math.exp(-fragment.decay_rate * hours)
        return recency
        
    def _calculate_frequency(self, fragment: MemoryFragment) -> float:
        if fragment.access_count == 0:
            return 0.0
            
        max_access = 100
        return min(fragment.access_count / max_access, 1.0)
        
    def _calculate_association(
        self, 
        fragment: MemoryFragment, 
        context: ContextState
    ) -> float:
        if not fragment.associations:
            return 0.0
            
        for entity in context.active_entities:
            if entity in fragment.associations:
                return 1.0
                
        return 0.0
        
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        if len(vec1) != len(vec2):
            return 0.0
            
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        return dot_product / (norm1 * norm2)


class MemoryAttentionEngine:
    def __init__(self):
        self.attention_calculator = AttentionCalculator()
        self._fragments: Dict[str, MemoryFragment] = {}
        self._agent_fragments: Dict[str, List[str]] = defaultdict(list)
        self._active_memories: Dict[str, List[str]] = defaultdict(list)
        self._context_states: Dict[str, ContextState] = {}
        self._activation_threshold = 0.3
        self._max_active_memories = 10
        
    def register_fragment(self, fragment: MemoryFragment):
        self._fragments[fragment.fragment_id] = fragment
        self._agent_fragments[fragment.agent_id].append(fragment.fragment_id)
        
    def update_context(
        self,
        session_id: str,
        agent_id: str,
        message: str,
        entities: List[str] = None,
        keywords: List[str] = None
    ):
        context = self._context_states.get(session_id)
        
        if not context:
            context = ContextState(
                session_id=session_id,
                agent_id=agent_id
            )
            self._context_states[session_id] = context
            
        context.conversation_history.append({
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        
        if entities:
            context.active_entities = list(set(context.active_entities + entities))[-20:]
            
        if keywords:
            context.recent_keywords = list(set(context.recent_keywords + keywords))[-30:]
            
    def activate_memories(
        self,
        session_id: str,
        query: str,
        query_embedding: Optional[List[float]] = None,
        memory_types: Optional[List[MemoryType]] = None
    ) -> List[MemoryFragment]:
        context = self._context_states.get(session_id)
        if not context:
            return []
            
        agent_id = context.agent_id
        fragment_ids = self._agent_fragments.get(agent_id, [])
        
        candidates = []
        for fid in fragment_ids:
            fragment = self._fragments.get(fid)
            if not fragment:
                continue
                
            if memory_types and fragment.memory_type not in memory_types:
                continue
                
            activation = self.attention_calculator.calculate_activation(
                fragment, context, query_embedding
            )
            fragment._activation_score = activation
            
            if activation >= self._activation_threshold:
                candidates.append(fragment)
                
        candidates.sort(key=lambda f: f._activation_score, reverse=True)
        activated = candidates[:self._max_active_memories]
        
        for fragment in activated:
            fragment.access_count += 1
            fragment.last_accessed = datetime.now()
            
        self._active_memories[session_id] = [f.fragment_id for f in activated]
        
        return activated
        
    def spread_activation(self, session_id: str):
        active_ids = self._active_memories.get(session_id, [])
        if not active_ids:
            return
            
        for fid in active_ids:
            fragment = self._fragments.get(fid)
            if not fragment:
                continue
                
            for assoc_id in fragment.associations:
                assoc_fragment = self._fragments.get(assoc_id)
                if assoc_fragment:
                    boost = fragment._activation_score * 0.3
                    assoc_fragment._activation_score = min(
                        assoc_fragment._activation_score + boost, 1.0
                    )
                    
    def decay_inactive_memories(self, decay_factor: float = 0.95):
        for fragment in self._fragments.values():
            if fragment._activation_score > 0:
                fragment._activation_score *= decay_factor
                
    def get_active_memories(self, session_id: str) -> List[MemoryFragment]:
        active_ids = self._active_memories.get(session_id, [])
        return [self._fragments[fid] for fid in active_ids if fid in self._fragments]
        
    def get_memory_by_importance(
        self,
        agent_id: str,
        min_importance: float = 0.7,
        limit: int = 5
    ) -> List[MemoryFragment]:
        fragment_ids = self._agent_fragments.get(agent_id, [])
        fragments = [
            self._fragments[fid] for fid in fragment_ids
            if fid in self._fragments
        ]
        
        filtered = [f for f in fragments if f.importance >= min_importance]
        filtered.sort(key=lambda f: f.importance, reverse=True)
        
        return filtered[:limit]


class ContextualMemoryRetriever:
    def __init__(self, attention_engine: MemoryAttentionEngine):
        self.attention_engine = attention_engine
        self._retrieval_history: List[Dict[str, Any]] = []
        
    async def retrieve(
        self,
        session_id: str,
        query: str,
        query_embedding: Optional[List[float]] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        activated = self.attention_engine.activate_memories(
            session_id, query, query_embedding
        )
        
        self.attention_engine.spread_activation(session_id)
        
        results = []
        for fragment in activated[:top_k]:
            results.append({
                "fragment_id": fragment.fragment_id,
                "content": fragment.content,
                "memory_type": fragment.memory_type.value,
                "activation_score": fragment._activation_score,
                "activation_level": fragment.activation_level.value,
                "importance": fragment.importance,
                "keywords": fragment.keywords,
                "entities": fragment.entities
            })
            
        self._retrieval_history.append({
            "session_id": session_id,
            "query": query,
            "results_count": len(results),
            "timestamp": datetime.now().isoformat()
        })
        
        return results
        
    def get_context_aware_summary(
        self,
        session_id: str
    ) -> Dict[str, Any]:
        active = self.attention_engine.get_active_memories(session_id)
        context = self.attention_engine._context_states.get(session_id)
        
        if not active or not context:
            return {"summary": "", "active_topics": []}
            
        topics = defaultdict(int)
        for fragment in active:
            for keyword in fragment.keywords:
                topics[keyword] += fragment._activation_score
                
        top_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "summary": f"当前关注 {len(active)} 条记忆",
            "active_topics": [t[0] for t in top_topics],
            "active_entities": context.active_entities[-10:],
            "conversation_turns": len(context.conversation_history)
        }


class MemoryAttentionTrainer:
    def __init__(self, attention_engine: MemoryAttentionEngine):
        self.attention_engine = attention_engine
        self._feedback_history: List[Dict[str, Any]] = []
        
    def record_feedback(
        self,
        session_id: str,
        fragment_id: str,
        was_helpful: bool,
        user_action: Optional[str] = None
    ):
        fragment = self.attention_engine._fragments.get(fragment_id)
        if not fragment:
            return
            
        if was_helpful:
            fragment.importance = min(fragment.importance + 0.05, 1.0)
            fragment._activation_score = min(fragment._activation_score + 0.1, 1.0)
        else:
            fragment.importance = max(fragment.importance - 0.02, 0.0)
            
        self._feedback_history.append({
            "session_id": session_id,
            "fragment_id": fragment_id,
            "was_helpful": was_helpful,
            "user_action": user_action,
            "timestamp": datetime.now().isoformat()
        })
        
    def adjust_weights(self):
        if len(self._feedback_history) < 10:
            return
            
        helpful = [f for f in self._feedback_history if f["was_helpful"]]
        not_helpful = [f for f in self._feedback_history if not f["was_helpful"]]
        
        if not helpful:
            return
            
        weights = self.attention_engine.attention_calculator.weights
        
        if len(helpful) > len(not_helpful):
            weights.relevance_weight = min(weights.relevance_weight + 0.02, 0.6)
        else:
            weights.importance_weight = max(weights.importance_weight - 0.02, 0.1)


memory_attention_engine = MemoryAttentionEngine()
contextual_retriever = ContextualMemoryRetriever(memory_attention_engine)
attention_trainer = MemoryAttentionTrainer(memory_attention_engine)


async def activate_relevant_memories(
    session_id: str,
    query: str,
    query_embedding: Optional[List[float]] = None
) -> List[Dict[str, Any]]:
    return await contextual_retriever.retrieve(session_id, query, query_embedding)


def get_attention_engine() -> MemoryAttentionEngine:
    return memory_attention_engine
