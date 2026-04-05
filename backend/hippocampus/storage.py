"""
海马体记忆中枢系统 - 存储层
分层存储：工作记忆、短期记忆、长期记忆
"""
import uuid
import json
import math
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_pg import get_db
from .encoder import MemoryUnit, memory_encoder

WORKING_MEMORY_TTL = 3600
SHORT_TERM_DAYS = 7
LONG_TERM_THRESHOLD = 0.6
FORGET_THRESHOLD = 0.2
MAX_WORKING_MEMORY = 50

class HippocampusStorage:
    def __init__(self):
        self._redis_client = None
    
    async def _get_redis(self):
        if self._redis_client is None:
            try:
                from backend.cache.redis_client import redis_client
                self._redis_client = redis_client
            except:
                pass
        return self._redis_client
    
    async def store(self, memory: MemoryUnit) -> str:
        def parse_datetime(dt_str):
            if not dt_str:
                return None
            if isinstance(dt_str, datetime):
                return dt_str
            try:
                return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
            except:
                return datetime.utcnow()
        
        async with get_db() as db:
            await db.execute("""
                INSERT INTO hippocampus_memories 
                (id, user_id, type, content, summary, importance, timestamp, 
                 source, agents, entities, context, access_count, last_access, 
                 embedding_id, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
                ON CONFLICT (id) DO UPDATE SET
                    content = EXCLUDED.content,
                    summary = EXCLUDED.summary,
                    importance = EXCLUDED.importance,
                    agents = EXCLUDED.agents,
                    entities = EXCLUDED.entities,
                    context = EXCLUDED.context,
                    access_count = EXCLUDED.access_count,
                    last_access = EXCLUDED.last_access,
                    updated_at = EXCLUDED.updated_at
            """, (
                memory.id,
                memory.user_id,
                memory.type,
                memory.content,
                memory.summary,
                memory.importance,
                parse_datetime(memory.timestamp),
                memory.source,
                json.dumps(memory.agents, ensure_ascii=False),
                json.dumps(memory.entities, ensure_ascii=False),
                json.dumps(memory.context, ensure_ascii=False),
                memory.access_count,
                parse_datetime(memory.last_access),
                memory.embedding_id or None,
                parse_datetime(memory.created_at),
                parse_datetime(memory.updated_at),
            ))
            
            await self._store_entities(memory)
        
        return memory.id
    
    async def batch_store(self, memories: List[MemoryUnit]) -> List[str]:
        memory_ids = []
        for memory in memories:
            memory_id = await self.store(memory)
            memory_ids.append(memory_id)
        return memory_ids
    
    async def _store_entities(self, memory: MemoryUnit):
        async with get_db() as db:
            for entity_name in memory.entities:
                existing = await db.fetchone(
                    "SELECT id, frequency FROM memory_entities WHERE name = $1",
                    entity_name
                )
                
                if existing:
                    await db.execute("""
                        UPDATE memory_entities 
                        SET frequency = $1, last_seen = $2
                        WHERE name = $3
                    """, existing[1] + 1, datetime.utcnow(), entity_name)
                    
                    entity_id = existing[0]
                else:
                    entity_id = str(uuid.uuid4())
                    await db.execute("""
                        INSERT INTO memory_entities (id, name, type, frequency, last_seen)
                        VALUES ($1, $2, $3, $4, $5)
                    """, entity_id, entity_name, 'general', 1, datetime.utcnow())
                
                await db.execute("""
                    INSERT INTO memory_entity_map (memory_id, entity_id)
                    VALUES ($1, $2)
                    ON CONFLICT DO NOTHING
                """, memory.id, entity_id)
    
    async def get(self, memory_id: str) -> Optional[MemoryUnit]:
        async with get_db() as db:
            row = await db.fetchone(
                "SELECT * FROM hippocampus_memories WHERE id = $1",
                memory_id
            )
            
            if row:
                return self._row_to_memory(row)
        return None
    
    async def get_by_ids(self, memory_ids: List[str]) -> List[MemoryUnit]:
        if not memory_ids:
            return []
        
        async with get_db() as db:
            placeholders = ','.join([f'${i+1}' for i in range(len(memory_ids))])
            rows = await db.fetch(
                f"SELECT * FROM hippocampus_memories WHERE id IN ({placeholders})",
                *memory_ids
            )
            
            return [self._row_to_memory(row) for row in rows]
    
    async def get_user_memories(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        memory_type: str = None,
        min_importance: float = None,
        days: int = None
    ) -> List[MemoryUnit]:
        async with get_db() as db:
            conditions = ["user_id = $1"]
            params = [user_id]
            param_idx = 2
            
            if memory_type:
                conditions.append(f"type = ${param_idx}")
                params.append(memory_type)
                param_idx += 1
            
            if min_importance is not None:
                conditions.append(f"importance >= ${param_idx}")
                params.append(min_importance)
                param_idx += 1
            
            if days is not None:
                conditions.append(f"timestamp >= NOW() - INTERVAL '{days} days'")
            
            where_clause = " AND ".join(conditions)
            
            params.extend([limit, offset])
            
            rows = await db.fetch(
                f"""
                SELECT * FROM hippocampus_memories 
                WHERE {where_clause}
                ORDER BY timestamp DESC
                LIMIT ${param_idx} OFFSET ${param_idx + 1}
                """,
                *params
            )
            
            return [self._row_to_memory(row) for row in rows]
    
    async def search(
        self,
        user_id: str,
        query: str,
        limit: int = 10
    ) -> List[MemoryUnit]:
        async with get_db() as db:
            rows = await db.fetch("""
                SELECT * FROM hippocampus_memories 
                WHERE user_id = $1 AND (
                    content ILIKE $2 OR summary ILIKE $2
                )
                ORDER BY importance DESC, timestamp DESC
                LIMIT $3
            """, user_id, f"%{query}%", limit)
            
            return [self._row_to_memory(row) for row in rows]
    
    async def search_by_entity(
        self,
        user_id: str,
        entity_name: str,
        limit: int = 10
    ) -> List[MemoryUnit]:
        async with get_db() as db:
            rows = await db.fetch("""
                SELECT hm.* FROM hippocampus_memories hm
                JOIN memory_entity_map mem ON hm.id = mem.memory_id
                JOIN memory_entities me ON mem.entity_id = me.id
                WHERE hm.user_id = $1 AND me.name = $2
                ORDER BY hm.importance DESC, hm.timestamp DESC
                LIMIT $3
            """, user_id, entity_name, limit)
            
            return [self._row_to_memory(row) for row in rows]
    
    async def search_by_time(
        self,
        user_id: str,
        start_time: datetime,
        end_time: datetime,
        limit: int = 50
    ) -> List[MemoryUnit]:
        async with get_db() as db:
            rows = await db.fetch("""
                SELECT * FROM hippocampus_memories 
                WHERE user_id = $1 AND timestamp BETWEEN $2 AND $3
                ORDER BY timestamp DESC
                LIMIT $4
            """, user_id, start_time, end_time, limit)
            
            return [self._row_to_memory(row) for row in rows]
    
    async def update_access(self, memory_id: str):
        async with get_db() as db:
            await db.execute("""
                UPDATE hippocampus_memories 
                SET access_count = access_count + 1,
                    last_access = $1,
                    updated_at = $1
                WHERE id = $2
            """, datetime.utcnow(), memory_id)
    
    async def update_importance(self, memory_id: str, importance: float):
        async with get_db() as db:
            await db.execute("""
                UPDATE hippocampus_memories 
                SET importance = $1, updated_at = $2
                WHERE id = $3
            """, importance, datetime.utcnow(), memory_id)
    
    async def delete(self, memory_id: str) -> bool:
        async with get_db() as db:
            await db.execute(
                "DELETE FROM memory_entity_map WHERE memory_id = $1",
                memory_id
            )
            
            await db.execute(
                "DELETE FROM memory_relations WHERE memory_id1 = $1 OR memory_id2 = $1",
                memory_id
            )
            
            result = await db.execute(
                "DELETE FROM hippocampus_memories WHERE id = $1",
                memory_id
            )
            
            return True
    
    async def delete_user_memories(self, user_id: str) -> int:
        async with get_db() as db:
            count_row = await db.fetchone(
                "SELECT COUNT(*) FROM hippocampus_memories WHERE user_id = $1",
                user_id
            )
            count = count_row[0] if count_row else 0
            
            memory_ids = await db.fetch(
                "SELECT id FROM hippocampus_memories WHERE user_id = $1",
                user_id
            )
            
            for row in memory_ids:
                await db.execute(
                    "DELETE FROM memory_entity_map WHERE memory_id = $1",
                    row[0]
                )
                await db.execute(
                    "DELETE FROM memory_relations WHERE memory_id1 = $1 OR memory_id2 = $1",
                    row[0]
                )
            
            await db.execute(
                "DELETE FROM hippocampus_memories WHERE user_id = $1",
                user_id
            )
            
            return count
    
    async def count_user_memories(self, user_id: str) -> int:
        async with get_db() as db:
            row = await db.fetchone(
                "SELECT COUNT(*) FROM hippocampus_memories WHERE user_id = $1",
                user_id
            )
            return row[0] if row else 0
    
    async def get_memories_for_consolidation(
        self,
        user_id: str = None,
        limit: int = 100
    ) -> List[MemoryUnit]:
        async with get_db() as db:
            if user_id:
                rows = await db.fetch("""
                    SELECT * FROM hippocampus_memories 
                    WHERE user_id = $1
                    ORDER BY access_count DESC, importance DESC
                    LIMIT $2
                """, user_id, limit)
            else:
                rows = await db.fetch("""
                    SELECT * FROM hippocampus_memories 
                    ORDER BY access_count DESC, importance DESC
                    LIMIT $1
                """, limit)
            
            return [self._row_to_memory(row) for row in rows]
    
    async def get_low_importance_memories(
        self,
        threshold: float = FORGET_THRESHOLD,
        days_old: int = 30,
        limit: int = 100
    ) -> List[MemoryUnit]:
        async with get_db() as db:
            rows = await db.fetch("""
                SELECT * FROM hippocampus_memories 
                WHERE importance < $1 
                AND timestamp < NOW() - INTERVAL '1 day' * $2
                AND access_count < 3
                ORDER BY importance ASC, timestamp ASC
                LIMIT $3
            """, threshold, days_old, limit)
            
            return [self._row_to_memory(row) for row in rows]
    
    async def store_relation(
        self,
        memory_id1: str,
        memory_id2: str,
        relation_type: str = "associative",
        strength: float = 0.5
    ) -> str:
        relation_id = str(uuid.uuid4())
        
        async with get_db() as db:
            await db.execute("""
                INSERT INTO memory_relations (id, memory_id1, memory_id2, relation_type, strength)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT DO NOTHING
            """, relation_id, memory_id1, memory_id2, relation_type, strength)
        
        return relation_id
    
    async def get_relations(
        self,
        memory_id: str,
        relation_type: str = None
    ) -> List[Dict[str, Any]]:
        async with get_db() as db:
            if relation_type:
                rows = await db.fetch("""
                    SELECT * FROM memory_relations 
                    WHERE (memory_id1 = $1 OR memory_id2 = $1) AND relation_type = $2
                    ORDER BY strength DESC
                """, memory_id, relation_type)
            else:
                rows = await db.fetch("""
                    SELECT * FROM memory_relations 
                    WHERE memory_id1 = $1 OR memory_id2 = $1
                    ORDER BY strength DESC
                """, memory_id)
            
            return [dict(row) for row in rows]
    
    async def get_memory_stats(self, user_id: str = None) -> Dict[str, Any]:
        async with get_db() as db:
            if user_id:
                total_row = await db.fetchone(
                    "SELECT COUNT(*) FROM hippocampus_memories WHERE user_id = $1",
                    user_id
                )
                type_rows = await db.fetch("""
                    SELECT type, COUNT(*) as count 
                    FROM hippocampus_memories 
                    WHERE user_id = $1
                    GROUP BY type
                """, user_id)
                avg_importance_row = await db.fetchone(
                    "SELECT AVG(importance) FROM hippocampus_memories WHERE user_id = $1",
                    user_id
                )
            else:
                total_row = await db.fetchone("SELECT COUNT(*) FROM hippocampus_memories")
                type_rows = await db.fetch("""
                    SELECT type, COUNT(*) as count 
                    FROM hippocampus_memories 
                    GROUP BY type
                """)
                avg_importance_row = await db.fetchone(
                    "SELECT AVG(importance) FROM hippocampus_memories"
                )
            
            return {
                'total_memories': total_row[0] if total_row else 0,
                'by_type': {row[0]: row[1] for row in type_rows},
                'average_importance': float(avg_importance_row[0]) if avg_importance_row and avg_importance_row[0] else 0.0,
            }
    
    def _row_to_memory(self, row) -> MemoryUnit:
        row_dict = dict(row) if hasattr(row, 'keys') else dict(row._row) if hasattr(row, '_row') else {}
        
        def datetime_to_str(dt):
            if dt is None:
                return ''
            if isinstance(dt, str):
                return dt
            if hasattr(dt, 'isoformat'):
                return dt.isoformat()
            return str(dt)
        
        return MemoryUnit(
            id=row_dict.get('id', ''),
            user_id=row_dict.get('user_id', ''),
            type=row_dict.get('type', 'episodic'),
            content=row_dict.get('content', ''),
            summary=row_dict.get('summary', ''),
            importance=float(row_dict.get('importance', 0.5)),
            timestamp=datetime_to_str(row_dict.get('timestamp', '')),
            source=row_dict.get('source', ''),
            agents=self._parse_json(row_dict.get('agents', '[]')),
            entities=self._parse_json(row_dict.get('entities', '[]')),
            context=self._parse_json(row_dict.get('context', '{}')),
            access_count=row_dict.get('access_count', 0),
            last_access=datetime_to_str(row_dict.get('last_access', '')),
            embedding_id=row_dict.get('embedding_id', ''),
            created_at=datetime_to_str(row_dict.get('created_at', '')),
            updated_at=datetime_to_str(row_dict.get('updated_at', '')),
        )
    
    def _parse_json(self, value):
        if isinstance(value, str):
            try:
                return json.loads(value)
            except:
                return [] if value.startswith('[') else {}
        return value or ([] if isinstance(value, str) and value.startswith('[') else {})

hippocampus_storage = HippocampusStorage()
