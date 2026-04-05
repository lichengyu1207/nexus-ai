"""
智能体记忆系统 - 存储层
封装所有SQLite操作
优化：使用连接池减少连接开销
"""
import aiosqlite
import uuid
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path
import asyncio
from contextlib import asynccontextmanager

DB_PATH = Path(__file__).parent.parent.parent / "data" / "property-ai.db"

class SQLiteStorage:
    _instance = None
    _lock = asyncio.Lock()
    _pool = None
    _max_connections = 5
    
    def __new__(cls, db_path: str = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.db_path = db_path or str(DB_PATH)
        return cls._instance
    
    @classmethod
    async def get_pool(cls):
        if cls._pool is None:
            async with cls._lock:
                if cls._pool is None:
                    cls._pool = await aiosqlite.connect(cls._instance.db_path)
                    cls._pool.row_factory = aiosqlite.Row
        return cls._pool
    
    @asynccontextmanager
    async def get_connection(self):
        conn = await self.get_pool()
        try:
            yield conn
        except Exception:
            await conn.rollback()
            raise
    
    async def insert_memory(
        self,
        user_id: str,
        agent_name: str,
        session_id: str,
        input_text: str,
        output_text: str,
        summary: str,
        importance: float,
        category: str,
        tags: List[str]
    ) -> str:
        memory_id = str(uuid.uuid4())
        tags_json = json.dumps(tags) if tags else "[]"
        
        async with self.get_connection() as conn:
            await conn.execute("""
                INSERT INTO memory_entries 
                (id, user_id, agent_name, session_id, input_text, output_text, 
                 summary, importance, category, tags, created_at, last_accessed, access_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
            """, (
                memory_id, user_id, agent_name, session_id, input_text, output_text,
                summary, importance, category, tags_json, datetime.utcnow().isoformat(),
                datetime.utcnow().isoformat()
            ))
            await conn.commit()
        
        return memory_id
    
    async def get_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        async with self.get_connection() as conn:
            cursor = await conn.execute(
                "SELECT * FROM memory_entries WHERE id = ?", (memory_id,)
            )
            row = await cursor.fetchone()
            
            if row:
                return dict(row)
            return None
    
    async def get_memories_by_ids(self, memory_ids: List[str]) -> List[Dict[str, Any]]:
        if not memory_ids:
            return []
        
        placeholders = ",".join("?" * len(memory_ids))
        async with self.get_connection() as conn:
            cursor = await conn.execute(
                f"SELECT * FROM memory_entries WHERE id IN ({placeholders})", memory_ids
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def get_user_memories(
        self, 
        user_id: str, 
        limit: int = 50, 
        offset: int = 0,
        category: str = None
    ) -> List[Dict[str, Any]]:
        async with self.get_connection() as conn:
            if category:
                cursor = await conn.execute("""
                    SELECT * FROM memory_entries 
                    WHERE user_id = ? AND category = ?
                    ORDER BY created_at DESC 
                    LIMIT ? OFFSET ?
                """, (user_id, category, limit, offset))
            else:
                cursor = await conn.execute("""
                    SELECT * FROM memory_entries 
                    WHERE user_id = ?
                    ORDER BY created_at DESC 
                    LIMIT ? OFFSET ?
                """, (user_id, limit, offset))
            
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def search_memories(
        self,
        user_id: str,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        async with self.get_connection() as conn:
            cursor = await conn.execute("""
                SELECT * FROM memory_entries 
                WHERE user_id = ? AND (
                    summary LIKE ? OR 
                    input_text LIKE ? OR 
                    output_text LIKE ? OR
                    category LIKE ?
                )
                ORDER BY importance DESC, created_at DESC
                LIMIT ?
            """, (user_id, f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%", limit))
            
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def update_access(self, memory_id: str) -> None:
        async with self.get_connection() as conn:
            await conn.execute("""
                UPDATE memory_entries 
                SET last_accessed = ?, access_count = access_count + 1
                WHERE id = ?
            """, (datetime.utcnow().isoformat(), memory_id))
            await conn.commit()
    
    async def delete_memory(self, memory_id: str) -> bool:
        async with self.get_connection() as conn:
            cursor = await conn.execute(
                "DELETE FROM memory_entries WHERE id = ?", (memory_id,)
            )
            await conn.commit()
            return cursor.rowcount > 0
    
    async def delete_user_memories(self, user_id: str) -> int:
        async with self.get_connection() as conn:
            cursor = await conn.execute(
                "DELETE FROM memory_entries WHERE user_id = ?", (user_id,)
            )
            await conn.commit()
            return cursor.rowcount
    
    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        async with self.get_connection() as conn:
            cursor = await conn.execute(
                "SELECT * FROM user_profiles WHERE user_id = ?", (user_id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    async def update_user_profile(self, user_id: str, preferences: Dict[str, Any]) -> None:
        prefs_json = json.dumps(preferences)
        async with self.get_connection() as conn:
            await conn.execute("""
                INSERT INTO user_profiles (user_id, preferences, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    preferences = ?,
                    updated_at = ?
            """, (user_id, prefs_json, datetime.utcnow().isoformat(),
                  prefs_json, datetime.utcnow().isoformat()))
            await conn.commit()
    
    async def close(self):
        if self._pool:
            await self._pool.close()
            self._pool = None


storage = SQLiteStorage()
