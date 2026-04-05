"""
会话记忆与引用
Session Memory Manager - 多轮对话中引用历史信息

礼部智能体增强模块
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import asyncio
import json
import hashlib


class MemoryType(Enum):
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PREFERENCE = "preference"


class MemoryImportance(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class MemoryStatus(Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    FORGOTTEN = "forgotten"
    CONFLICTED = "conflicted"


@dataclass
class MemoryItem:
    memory_id: str
    memory_type: MemoryType
    content: str
    key_entities: Dict[str, Any]
    importance: MemoryImportance
    confidence: float
    source_session_id: str
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    status: MemoryStatus = MemoryStatus.ACTIVE
    expires_at: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    related_memories: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionContext:
    session_id: str
    user_id: str
    started_at: datetime
    last_activity: datetime
    turn_count: int
    topics_discussed: List[str]
    entities_mentioned: Dict[str, Any]
    user_preferences: Dict[str, Any]
    pending_questions: List[str]
    memory_references: List[str]


class HippocampusMemorySystem:
    def __init__(self, max_short_term: int = 100, max_long_term: int = 1000):
        self.max_short_term = max_short_term
        self.max_long_term = max_long_term

        self.short_term_memory: Dict[str, MemoryItem] = {}
        self.long_term_memory: Dict[str, MemoryItem] = {}

        self.consolidation_threshold = 3
        self.forgetting_threshold = timedelta(days=30)

    def store(self, memory: MemoryItem) -> str:
        if memory.memory_type == MemoryType.SHORT_TERM:
            if len(self.short_term_memory) >= self.max_short_term:
                self._evict_short_term()

            self.short_term_memory[memory.memory_id] = memory

            if memory.access_count >= self.consolidation_threshold:
                self._consolidate(memory.memory_id)

        else:
            if len(self.long_term_memory) >= self.max_long_term:
                self._evict_long_term()

            self.long_term_memory[memory.memory_id] = memory

        return memory.memory_id

    def retrieve(
        self,
        query: str,
        memory_type: MemoryType = None,
        limit: int = 5,
    ) -> List[MemoryItem]:
        results = []

        search_pools = []
        if memory_type == MemoryType.SHORT_TERM or memory_type is None:
            search_pools.append(self.short_term_memory)
        if memory_type == MemoryType.LONG_TERM or memory_type is None:
            search_pools.append(self.long_term_memory)

        for pool in search_pools:
            for memory in pool.values():
                if memory.status != MemoryStatus.ACTIVE:
                    continue

                relevance = self._calculate_relevance(query, memory)
                if relevance > 0.3:
                    results.append((memory, relevance))

        results.sort(key=lambda x: x[1], reverse=True)

        retrieved = [r[0] for r in results[:limit]]

        for memory in retrieved:
            memory.last_accessed = datetime.utcnow()
            memory.access_count += 1

        return retrieved

    def retrieve_by_entity(self, entity_type: str, entity_value: str) -> List[MemoryItem]:
        results = []

        for memory in list(self.short_term_memory.values()) + list(
            self.long_term_memory.values()
        ):
            if memory.status != MemoryStatus.ACTIVE:
                continue

            if entity_type in memory.key_entities:
                if str(memory.key_entities[entity_type]).lower() == str(entity_value).lower():
                    results.append(memory)

        return results

    def _calculate_relevance(self, query: str, memory: MemoryItem) -> float:
        query_lower = query.lower()
        content_lower = memory.content.lower()

        word_overlap = len(
            set(query_lower.split()) & set(content_lower.split())
        ) / max(len(query_lower.split()), 1)

        entity_match = 0
        for entity_type, entity_value in memory.key_entities.items():
            if str(entity_value).lower() in query_lower:
                entity_match += 0.2

        recency = 1.0
        age_hours = (datetime.utcnow() - memory.created_at).total_seconds() / 3600
        if age_hours > 24:
            recency = 1.0 / (1 + age_hours / 24)

        importance_weight = memory.importance.value / 4.0

        return word_overlap * 0.4 + entity_match * 0.3 + recency * 0.2 + importance_weight * 0.1

    def _consolidate(self, memory_id: str) -> bool:
        if memory_id not in self.short_term_memory:
            return False

        memory = self.short_term_memory[memory_id]

        consolidated = MemoryItem(
            memory_id=f"lt_{memory_id}",
            memory_type=MemoryType.LONG_TERM,
            content=memory.content,
            key_entities=memory.key_entities,
            importance=memory.importance,
            confidence=memory.confidence,
            source_session_id=memory.source_session_id,
            created_at=memory.created_at,
            last_accessed=datetime.utcnow(),
            access_count=memory.access_count,
            status=MemoryStatus.ACTIVE,
            tags=memory.tags,
            metadata={"consolidated_from": memory_id},
        )

        self.long_term_memory[consolidated.memory_id] = consolidated
        del self.short_term_memory[memory_id]

        return True

    def _evict_short_term(self) -> None:
        if not self.short_term_memory:
            return

        oldest = min(
            self.short_term_memory.items(),
            key=lambda x: x[1].last_accessed,
        )
        del self.short_term_memory[oldest[0]]

    def _evict_long_term(self) -> None:
        if not self.long_term_memory:
            return

        candidates = [
            (mid, m)
            for mid, m in self.long_term_memory.items()
            if m.importance != MemoryImportance.CRITICAL
        ]

        if candidates:
            oldest = min(candidates, key=lambda x: x[1].last_accessed)
            del self.long_term_memory[oldest[0]]

    def forget_expired(self) -> List[str]:
        forgotten_ids = []
        now = datetime.utcnow()

        for memory_id, memory in list(self.short_term_memory.items()):
            if memory.expires_at and memory.expires_at < now:
                memory.status = MemoryStatus.FORGOTTEN
                forgotten_ids.append(memory_id)
                del self.short_term_memory[memory_id]

        return forgotten_ids


class MemoryConflictResolver:
    def __init__(self):
        self.conflict_history: List[Dict] = []

    def detect_conflict(
        self, old_memory: MemoryItem, new_memory: MemoryItem
    ) -> Optional[Dict[str, Any]]:
        conflicts = []

        for entity_type, old_value in old_memory.key_entities.items():
            if entity_type in new_memory.key_entities:
                new_value = new_memory.key_entities[entity_type]
                if str(old_value).lower() != str(new_value).lower():
                    conflicts.append(
                        {
                            "entity_type": entity_type,
                            "old_value": old_value,
                            "new_value": new_value,
                        }
                    )

        if conflicts:
            return {
                "old_memory_id": old_memory.memory_id,
                "new_memory_id": new_memory.memory_id,
                "conflicts": conflicts,
                "detected_at": datetime.utcnow().isoformat(),
            }

        return None

    def resolve(
        self,
        conflict: Dict[str, Any],
        resolution_strategy: str = "newest",
    ) -> MemoryItem:
        self.conflict_history.append(conflict)

        if resolution_strategy == "newest":
            return MemoryItem(
                memory_id=f"resolved_{conflict['new_memory_id']}",
                memory_type=MemoryType.LONG_TERM,
                content=f"Updated: {conflict['conflicts'][0]['new_value']}",
                key_entities={
                    c["entity_type"]: c["new_value"] for c in conflict["conflicts"]
                },
                importance=MemoryImportance.HIGH,
                confidence=0.9,
                source_session_id="conflict_resolution",
                created_at=datetime.utcnow(),
                last_accessed=datetime.utcnow(),
                status=MemoryStatus.ACTIVE,
                metadata={"resolved_from": conflict["old_memory_id"]},
            )

        return None


class SessionMemoryManager:
    def __init__(self, agent_id: str = "session_memory_001"):
        self.agent_id = agent_id
        self.hippocampus = HippocampusMemorySystem()
        self.conflict_resolver = MemoryConflictResolver()

        self.active_sessions: Dict[str, SessionContext] = {}
        self.session_history: List[SessionContext] = []

        self.memory_expiry_short = timedelta(hours=24)
        self.memory_expiry_long = timedelta(days=365)

    def start_session(self, user_id: str) -> SessionContext:
        session_id = f"session_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{hash(user_id) % 10000:04d}"

        context = SessionContext(
            session_id=session_id,
            user_id=user_id,
            started_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            turn_count=0,
            topics_discussed=[],
            entities_mentioned={},
            user_preferences={},
            pending_questions=[],
            memory_references=[],
        )

        self.active_sessions[session_id] = context
        return context

    def end_session(self, session_id: str) -> Optional[SessionContext]:
        session = self.active_sessions.pop(session_id, None)
        if session:
            self.session_history.append(session)
        return session

    def record_interaction(
        self,
        session_id: str,
        user_input: str,
        ai_response: str,
        extracted_entities: Dict[str, Any] = None,
        topic: str = None,
    ) -> Optional[MemoryItem]:
        session = self.active_sessions.get(session_id)
        if not session:
            return None

        session.last_activity = datetime.utcnow()
        session.turn_count += 1

        if topic and topic not in session.topics_discussed:
            session.topics_discussed.append(topic)

        if extracted_entities:
            for entity_type, entity_value in extracted_entities.items():
                session.entities_mentioned[entity_type] = entity_value

        memory = MemoryItem(
            memory_id=f"mem_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
            memory_type=MemoryType.SHORT_TERM,
            content=f"User: {user_input[:100]} | AI: {ai_response[:100]}",
            key_entities=extracted_entities or {},
            importance=self._assess_importance(user_input, extracted_entities),
            confidence=1.0,
            source_session_id=session_id,
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow(),
            expires_at=datetime.utcnow() + self.memory_expiry_short,
            tags=[topic] if topic else [],
        )

        self.hippocampus.store(memory)
        session.memory_references.append(memory.memory_id)

        return memory

    def _assess_importance(
        self, text: str, entities: Dict[str, Any]
    ) -> MemoryImportance:
        critical_keywords = ["预算", "购买", "投资", "贷款", "投诉"]
        high_keywords = ["偏好", "关注", "考虑", "选择"]

        text_lower = text.lower()

        if any(kw in text_lower for kw in critical_keywords):
            return MemoryImportance.CRITICAL

        if any(kw in text_lower for kw in high_keywords):
            return MemoryImportance.HIGH

        if entities and len(entities) >= 2:
            return MemoryImportance.MEDIUM

        return MemoryImportance.LOW

    def recall_relevant(
        self,
        session_id: str,
        query: str,
        include_long_term: bool = True,
    ) -> List[Dict[str, Any]]:
        session = self.active_sessions.get(session_id)

        memories = self.hippocampus.retrieve(
            query,
            memory_type=MemoryType.SHORT_TERM,
            limit=3,
        )

        if include_long_term:
            long_term = self.hippocampus.retrieve(
                query,
                memory_type=MemoryType.LONG_TERM,
                limit=2,
            )
            memories.extend(long_term)

        return [
            {
                "memory_id": m.memory_id,
                "content": m.content,
                "key_entities": m.key_entities,
                "created_at": m.created_at.isoformat(),
                "importance": m.importance.value,
            }
            for m in memories
        ]

    def recall_by_entity(
        self, entity_type: str, entity_value: str
    ) -> List[Dict[str, Any]]:
        memories = self.hippocampus.retrieve_by_entity(entity_type, entity_value)

        return [
            {
                "memory_id": m.memory_id,
                "content": m.content,
                "key_entities": m.key_entities,
                "created_at": m.created_at.isoformat(),
            }
            for m in memories
        ]

    def generate_reference_text(
        self, session_id: str, current_query: str
    ) -> Optional[str]:
        relevant_memories = self.recall_relevant(session_id, current_query)

        if not relevant_memories:
            return None

        entities = {}
        for memory in relevant_memories:
            entities.update(memory.get("key_entities", {}))

        if not entities:
            return None

        references = []
        if "region" in entities:
            references.append(f"您之前提到的{entities['region']}区域")
        if "community" in entities:
            references.append(f"您关注的{entities['community']}小区")
        if "budget" in entities:
            references.append(f"您的预算{entities['budget']}")

        if references:
            return "正如您之前提到的，" + "，".join(references) + "。"

        return None

    def update_preference(
        self, user_id: str, preference_type: str, preference_value: Any
    ) -> None:
        memory = MemoryItem(
            memory_id=f"pref_{user_id}_{preference_type}",
            memory_type=MemoryType.PREFERENCE,
            content=f"{preference_type}: {preference_value}",
            key_entities={preference_type: preference_value},
            importance=MemoryImportance.HIGH,
            confidence=1.0,
            source_session_id="preference_update",
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow(),
            expires_at=datetime.utcnow() + self.memory_expiry_long,
            tags=["preference", user_id],
        )

        self.hippocampus.store(memory)

    def detect_and_resolve_conflict(
        self, new_memory: MemoryItem
    ) -> Optional[MemoryItem]:
        for entity_type, entity_value in new_memory.key_entities.items():
            existing = self.hippocampus.retrieve_by_entity(entity_type, entity_value)

            for old_memory in existing:
                conflict = self.conflict_resolver.detect_conflict(
                    old_memory, new_memory
                )
                if conflict:
                    return self.conflict_resolver.resolve(conflict)

        return None

    def clear_user_memories(
        self, user_id: str, memory_type: MemoryType = None
    ) -> int:
        cleared = 0

        pools = []
        if memory_type == MemoryType.SHORT_TERM or memory_type is None:
            pools.append(self.hippocampus.short_term_memory)
        if memory_type == MemoryType.LONG_TERM or memory_type is None:
            pools.append(self.hippocampus.long_term_memory)

        for pool in pools:
            to_delete = [
                mid
                for mid, m in pool.items()
                if user_id in m.tags or m.source_session_id.startswith(f"session_.*_{user_id}")
            ]
            for mid in to_delete:
                del pool[mid]
                cleared += 1

        return cleared

    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        session = self.active_sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}

        return {
            "session_id": session.session_id,
            "user_id": session.user_id,
            "duration_minutes": (
                datetime.utcnow() - session.started_at
            ).total_seconds()
            / 60,
            "turn_count": session.turn_count,
            "topics_discussed": session.topics_discussed,
            "entities_mentioned": session.entities_mentioned,
            "memory_count": len(session.memory_references),
        }

    def get_memory_stats(self) -> Dict[str, Any]:
        return {
            "short_term_count": len(self.hippocampus.short_term_memory),
            "long_term_count": len(self.hippocampus.long_term_memory),
            "active_sessions": len(self.active_sessions),
            "total_sessions": len(self.session_history),
            "conflicts_resolved": len(self.conflict_resolver.conflict_history),
        }
