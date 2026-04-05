# -*- coding: utf-8 -*-
"""
Attention Residuals 海马体记忆系统 - 数据模型
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
import json


@dataclass
class MemoryEntry:
    id: str
    user_id: str
    content: str
    embedding: Optional[List[float]] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    importance: float = 0.5
    memory_type: str = "general"
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    access_count: int = 0

    @classmethod
    def from_db_row(cls, row: dict) -> "MemoryEntry":
        return cls(
            id=str(row.get("id", "")),
            user_id=str(row.get("user_id", "")),
            content=row.get("content", ""),
            embedding=list(row["embedding"]) if row.get("embedding") else None,
            session_id=str(row["session_id"]) if row.get("session_id") else None,
            metadata=row.get("metadata", {}) or {},
            importance=row.get("importance", 0.5),
            memory_type=row.get("memory_type", "general"),
            created_at=row.get("created_at", datetime.now()),
            last_accessed=row.get("last_accessed", datetime.now()),
            access_count=row.get("access_count", 0)
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "content": self.content,
            "embedding": self.embedding,
            "session_id": self.session_id,
            "metadata": self.metadata,
            "importance": self.importance,
            "memory_type": self.memory_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
            "access_count": self.access_count
        }


@dataclass
class MemoryBlock:
    id: str
    user_id: str
    block_index: int
    memory_ids: List[str] = field(default_factory=list)
    block_vector: Optional[List[float]] = None
    memory_count: int = 0
    avg_importance: float = 0.5
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    @classmethod
    def from_db_row(cls, row: dict) -> "MemoryBlock":
        return cls(
            id=str(row.get("id", "")),
            user_id=str(row.get("user_id", "")),
            block_index=row.get("block_index", 0),
            memory_ids=row.get("memory_ids", []) or [],
            block_vector=list(row["block_vector"]) if row.get("block_vector") else None,
            memory_count=row.get("memory_count", 0),
            avg_importance=row.get("avg_importance", 0.5),
            created_at=row.get("created_at", datetime.now()),
            updated_at=row.get("updated_at", datetime.now())
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "block_index": self.block_index,
            "memory_ids": self.memory_ids,
            "memory_count": self.memory_count,
            "avg_importance": self.avg_importance,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


@dataclass
class MemorySession:
    id: str
    user_id: str
    summary: Optional[str] = None
    key_topics: List[str] = field(default_factory=list)
    turn_count: int = 0
    started_at: datetime = field(default_factory=datetime.now)
    ended_at: Optional[datetime] = None
    session_type: str = "consultation"

    @classmethod
    def from_db_row(cls, row: dict) -> "MemorySession":
        return cls(
            id=str(row.get("id", "")),
            user_id=str(row.get("user_id", "")),
            summary=row.get("summary"),
            key_topics=row.get("key_topics", []) or [],
            turn_count=row.get("turn_count", 0),
            started_at=row.get("started_at", datetime.now()),
            ended_at=row.get("ended_at"),
            session_type=row.get("session_type", "consultation")
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "summary": self.summary,
            "key_topics": self.key_topics,
            "turn_count": self.turn_count,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "session_type": self.session_type
        }


@dataclass
class AttentionLog:
    id: str
    user_id: str
    query_id: Optional[str] = None
    query_text: Optional[str] = None
    block_weights: List[float] = field(default_factory=list)
    selected_memories: List[str] = field(default_factory=list)
    confidence_score: float = 0.0
    aggregation_method: str = "attention_residual"
    created_at: datetime = field(default_factory=datetime.now)

    @classmethod
    def from_db_row(cls, row: dict) -> "AttentionLog":
        return cls(
            id=str(row.get("id", "")),
            user_id=str(row.get("user_id", "")),
            query_id=str(row["query_id"]) if row.get("query_id") else None,
            query_text=row.get("query_text"),
            block_weights=row.get("block_weights", []) or [],
            selected_memories=row.get("selected_memories", []) or [],
            confidence_score=row.get("confidence_score", 0.0),
            aggregation_method=row.get("aggregation_method", "attention_residual"),
            created_at=row.get("created_at", datetime.now())
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "query_id": self.query_id,
            "query_text": self.query_text,
            "block_weights": self.block_weights,
            "selected_memories": self.selected_memories,
            "confidence_score": self.confidence_score,
            "aggregation_method": self.aggregation_method,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


@dataclass
class UserMemoryProfile:
    id: str
    user_id: str
    preference_vector: Optional[List[float]] = None
    topic_weights: Dict[str, float] = field(default_factory=dict)
    total_memories: int = 0
    total_sessions: int = 0
    last_active: datetime = field(default_factory=datetime.now)
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)

    @classmethod
    def from_db_row(cls, row: dict) -> "UserMemoryProfile":
        return cls(
            id=str(row.get("id", "")),
            user_id=str(row.get("user_id", "")),
            preference_vector=list(row["preference_vector"]) if row.get("preference_vector") else None,
            topic_weights=row.get("topic_weights", {}) or {},
            total_memories=row.get("total_memories", 0),
            total_sessions=row.get("total_sessions", 0),
            last_active=row.get("last_active", datetime.now()),
            created_at=row.get("created_at", datetime.now()),
            last_updated=row.get("last_updated", datetime.now())
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "topic_weights": self.topic_weights,
            "total_memories": self.total_memories,
            "total_sessions": self.total_sessions,
            "last_active": self.last_active.isoformat() if self.last_active else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


@dataclass
class AttentionResult:
    context_vector: List[float]
    block_weights: List[float]
    selected_blocks: List[int]
    selected_memories: List[str]
    confidence_score: float
    aggregation_method: str = "attention_residual"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "context_vector": self.context_vector,
            "block_weights": self.block_weights,
            "selected_blocks": self.selected_blocks,
            "selected_memories": self.selected_memories,
            "confidence_score": self.confidence_score,
            "aggregation_method": self.aggregation_method
        }
