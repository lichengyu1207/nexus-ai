# -*- coding: utf-8 -*-
"""
Memory Service - 记忆存储与检索服务
"""
import asyncpg
import uuid
import json
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
import numpy as np

from backend.services.attention_residuals.models import (
    MemoryEntry, MemoryBlock, MemorySession, UserMemoryProfile, AttentionLog
)
from backend.services.attention_residuals.hippocampus_retriever import (
    HippocampusRetriever, get_hippocampus_retriever, init_hippocampus_retriever
)

DATABASE_URL = "postgresql://postgres:147258%40Zxcvbnm@localhost:5432/fangdu"


class MemoryService:
    def __init__(self, db_pool):
        self.db_pool = db_pool
        self.retriever: Optional[HippocampusRetriever] = None

    async def initialize(self):
        self.retriever = init_hippocampus_retriever()

    async def store_memory(
        self,
        user_id: str,
        content: str,
        embedding: Optional[List[float]] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        importance: float = 0.5,
        memory_type: str = "general"
    ) -> MemoryEntry:
        memory_id = str(uuid.uuid4())
        
        async with self.db_pool.acquire() as conn:
            embedding_str = None
            if embedding:
                embedding_str = f"[{','.join(map(str, embedding))}]"
            
            await conn.execute("""
                INSERT INTO memory_entries 
                (id, user_id, session_id, content, embedding, metadata, importance, memory_type)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """, memory_id, user_id, session_id, content, 
                embedding_str, json.dumps(metadata or {}), importance, memory_type)
            
            await conn.execute("""
                INSERT INTO user_memory_profiles (user_id, total_memories)
                VALUES ($1, 1)
                ON CONFLICT (user_id) DO UPDATE SET 
                    total_memories = user_memory_profiles.total_memories + 1,
                    last_updated = NOW()
            """, user_id)
        
        return MemoryEntry(
            id=memory_id,
            user_id=user_id,
            content=content,
            embedding=embedding,
            session_id=session_id,
            metadata=metadata or {},
            importance=importance,
            memory_type=memory_type
        )

    async def retrieve_memories(
        self,
        user_id: str,
        query_embedding: Optional[List[float]] = None,
        limit: int = 100,
        memory_type: Optional[str] = None,
        min_importance: float = 0.0
    ) -> List[MemoryEntry]:
        async with self.db_pool.acquire() as conn:
            conditions = ["user_id = $1"]
            params = [user_id]
            param_idx = 2
            
            if memory_type:
                conditions.append(f"memory_type = ${param_idx}")
                params.append(memory_type)
                param_idx += 1
            
            if min_importance > 0:
                conditions.append(f"importance >= ${param_idx}")
                params.append(min_importance)
                param_idx += 1
            
            where_clause = " AND ".join(conditions)
            
            if query_embedding:
                embedding_str = f"[{','.join(map(str, query_embedding))}]"
                order_clause = f"ORDER BY embedding <=> '{embedding_str}'"
            else:
                order_clause = "ORDER BY importance DESC, created_at DESC"
            
            query = f"""
                SELECT * FROM memory_entries 
                WHERE {where_clause}
                {order_clause}
                LIMIT ${param_idx}
            """
            params.append(limit)
            
            rows = await conn.fetch(query, *params)
            
            memories = []
            for row in rows:
                memories.append(MemoryEntry.from_db_row(dict(row)))
            
            return memories

    async def get_memory(self, memory_id: str) -> Optional[MemoryEntry]:
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM memory_entries WHERE id = $1", memory_id
            )
            if row:
                await conn.execute(
                    "UPDATE memory_entries SET access_count = access_count + 1, last_accessed = NOW() WHERE id = $1",
                    memory_id
                )
                return MemoryEntry.from_db_row(dict(row))
            return None

    async def update_memory(
        self,
        memory_id: str,
        updates: Dict[str, Any]
    ) -> Optional[MemoryEntry]:
        valid_fields = ["content", "importance", "metadata", "memory_type"]
        update_parts = []
        params = []
        param_idx = 1
        
        for field in valid_fields:
            if field in updates:
                if field == "metadata":
                    update_parts.append(f"{field} = ${param_idx}::jsonb")
                    params.append(json.dumps(updates[field]))
                else:
                    update_parts.append(f"{field} = ${param_idx}")
                    params.append(updates[field])
                param_idx += 1
        
        if not update_parts:
            return None
        
        update_parts.append("last_accessed = NOW()")
        params.append(memory_id)
        
        async with self.db_pool.acquire() as conn:
            query = f"UPDATE memory_entries SET {', '.join(update_parts)} WHERE id = ${param_idx} RETURNING *"
            row = await conn.fetchrow(query, *params)
            if row:
                return MemoryEntry.from_db_row(dict(row))
        return None

    async def delete_memory(self, memory_id: str) -> bool:
        async with self.db_pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM memory_entries WHERE id = $1", memory_id
            )
            return "DELETE 1" in result

    async def attention_retrieve(
        self,
        user_id: str,
        query_embedding: List[float],
        top_k: int = 100
    ) -> Tuple[List[MemoryEntry], Dict[str, Any]]:
        memories = await self.retrieve_memories(
            user_id=user_id,
            query_embedding=query_embedding,
            limit=top_k
        )
        
        if not memories or not self.retriever:
            return [], {"block_weights": [], "confidence": 0.0}
        
        result = self.retriever.retrieve(query_embedding, memories)
        
        selected_memories = [
            m for m in memories if m.id in result.selected_memories
        ]
        
        await self._log_attention(
            user_id=user_id,
            query_embedding=query_embedding,
            block_weights=result.block_weights,
            selected_memory_ids=result.selected_memories,
            confidence=result.confidence_score
        )
        
        return selected_memories, result.to_dict()

    async def _log_attention(
        self,
        user_id: str,
        query_embedding: List[float],
        block_weights: List[float],
        selected_memory_ids: List[str],
        confidence: float
    ):
        log_id = str(uuid.uuid4())
        
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO attention_logs 
                (id, user_id, block_weights, selected_memories, confidence_score)
                VALUES ($1, $2, $3, $4, $5)
            """, log_id, user_id, json.dumps(block_weights), 
                json.dumps(selected_memory_ids), confidence)

    async def create_session(
        self,
        user_id: str,
        session_type: str = "consultation"
    ) -> MemorySession:
        session_id = str(uuid.uuid4())
        
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO memory_sessions (id, user_id, session_type)
                VALUES ($1, $2, $3)
            """, session_id, user_id, session_type)
            
            await conn.execute("""
                INSERT INTO user_memory_profiles (user_id, total_sessions)
                VALUES ($1, 1)
                ON CONFLICT (user_id) DO UPDATE SET 
                    total_sessions = user_memory_profiles.total_sessions + 1,
                    last_updated = NOW()
            """, user_id)
        
        return MemorySession(
            id=session_id,
            user_id=user_id,
            session_type=session_type
        )

    async def end_session(
        self,
        session_id: str,
        summary: Optional[str] = None,
        key_topics: Optional[List[str]] = None
    ):
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                UPDATE memory_sessions 
                SET ended_at = NOW(), summary = $2, key_topics = $3
                WHERE id = $1
            """, session_id, summary, json.dumps(key_topics or []))

    async def get_user_profile(self, user_id: str) -> Optional[UserMemoryProfile]:
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM user_memory_profiles WHERE user_id = $1", user_id
            )
            if row:
                return UserMemoryProfile.from_db_row(dict(row))
        return None


_memory_service: Optional[MemoryService] = None


def get_memory_service() -> Optional[MemoryService]:
    return _memory_service


async def init_memory_service(db_pool) -> MemoryService:
    global _memory_service
    _memory_service = MemoryService(db_pool)
    await _memory_service.initialize()
    return _memory_service
