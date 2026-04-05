"""
智能体记忆系统 - 记忆整理模块
负责记忆的合并、压缩、遗忘等整理操作
"""
import asyncio
import uuid
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
import aiosqlite

from .storage import SQLiteStorage
from .utils import generate_summary, calculate_importance, categorize_memory, extract_tags
from .retrieval import calculate_freshness_score

DB_PATH = Path(__file__).parent.parent.parent / "data" / "property-ai.db"

class MemoryConsolidator:
    def __init__(self, storage: SQLiteStorage = None):
        self.storage = storage or SQLiteStorage()
    
    async def consolidate_user_memories(self, user_id: str) -> Dict[str, Any]:
        result = {
            "user_id": user_id,
            "memories_processed": 0,
            "memories_merged": 0,
            "memories_forgotten": 0,
            "details": []
        }
        
        memories = await self.storage.get_user_memories(user_id, limit=100)
        result["memories_processed"] = len(memories)
        
        merge_groups = await self._find_similar_memories(memories)
        
        for group in merge_groups:
            if len(group) > 1:
                merged = await self._merge_memories(group, user_id)
                if merged:
                    result["memories_merged"] += 1
                    result["details"].append({
                        "action": "merge",
                        "memory_ids": [m["id"] for m in group],
                        "new_memory_id": merged
                    })
        
        forgotten = await self._forget_old_memories(user_id)
        result["memories_forgotten"] = forgotten
        
        await self._log_consolidation(user_id, result)
        
        return result
    
    async def _find_similar_memories(self, memories: List[Dict]) -> List[List[Dict]]:
        if not memories:
            return []
        
        groups = []
        used = set()
        
        for i, mem1 in enumerate(memories):
            if mem1["id"] in used:
                continue
            
            group = [mem1]
            used.add(mem1["id"])
            
            for j, mem2 in enumerate(memories[i+1:], i+1):
                if mem2["id"] in used:
                    continue
                
                similarity = self._calculate_similarity(mem1, mem2)
                if similarity > 0.7:
                    group.append(mem2)
                    used.add(mem2["id"])
            
            if len(group) > 1:
                groups.append(group)
        
        return groups
    
    def _calculate_similarity(self, mem1: Dict, mem2: Dict) -> float:
        score = 0.0
        
        if mem1.get("category") == mem2.get("category"):
            score += 0.3
        
        tags1 = set(eval(mem1.get("tags", "[]"))) if mem1.get("tags") else set()
        tags2 = set(eval(mem2.get("tags", "[]"))) if mem2.get("tags") else set()
        if tags1 and tags2:
            intersection = len(tags1 & tags2)
            union = len(tags1 | tags2)
            if union > 0:
                score += 0.3 * (intersection / union)
        
        summary1 = mem1.get("summary", "") or ""
        summary2 = mem2.get("summary", "") or ""
        if summary1 and summary2:
            words1 = set(summary1.split())
            words2 = set(summary2.split())
            if words1 and words2:
                intersection = len(words1 & words2)
                union = len(words1 | words2)
                if union > 0:
                    score += 0.4 * (intersection / union)
        
        return score
    
    async def _merge_memories(self, memories: List[Dict], user_id: str) -> Optional[str]:
        if not memories:
            return None
        
        sorted_memories = sorted(memories, key=lambda x: float(x.get("importance", 0)), reverse=True)
        primary = sorted_memories[0]
        
        combined_input = "\n".join([m.get("input_text", "") or "" for m in memories if m.get("input_text")])
        combined_output = "\n".join([m.get("output_text", "") or "" for m in memories if m.get("output_text")])
        
        new_summary = generate_summary(combined_input, combined_output)
        new_importance = max(float(m.get("importance", 5.0)) for m in memories) + 0.5
        new_category = categorize_memory(combined_input, combined_output)
        
        all_tags = set()
        for m in memories:
            tags = eval(m.get("tags", "[]")) if m.get("tags") else []
            all_tags.update(tags)
        new_tags = list(all_tags)[:10]
        
        new_memory_id = await self.storage.insert_memory(
            user_id=user_id,
            agent_name=primary.get("agent_name", "system"),
            session_id=primary.get("session_id", ""),
            input_text=combined_input[:2000],
            output_text=combined_output[:2000],
            summary=new_summary,
            importance=min(new_importance, 10.0),
            category=new_category,
            tags=new_tags
        )
        
        for m in memories:
            await self.storage.delete_memory(m["id"])
        
        return new_memory_id
    
    async def _forget_old_memories(self, user_id: str) -> int:
        forgotten_count = 0
        threshold_date = (datetime.utcnow() - timedelta(days=90)).isoformat()
        
        async with aiosqlite.connect(str(DB_PATH)) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute("""
                SELECT * FROM memory_entries 
                WHERE user_id = ? 
                AND CAST(importance AS REAL) < 3.0 
                AND created_at < ?
                AND access_count < 2
            """, (user_id, threshold_date))
            
            old_memories = await cursor.fetchall()
            
            for memory in old_memories:
                await self.storage.delete_memory(memory["id"])
                forgotten_count += 1
        
        return forgotten_count
    
    async def _log_consolidation(self, user_id: str, result: Dict):
        async with aiosqlite.connect(str(DB_PATH)) as conn:
            await conn.execute("""
                INSERT INTO memory_consolidation_logs 
                (id, user_id, consolidation_type, memories_processed, memories_merged, created_at, details)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()),
                user_id,
                "auto_consolidation",
                result["memories_processed"],
                result["memories_merged"],
                datetime.utcnow().isoformat(),
                json.dumps(result["details"], ensure_ascii=False)
            ))
            await conn.commit()
    
    async def compress_session_memories(self, user_id: str, session_id: str) -> Optional[str]:
        memories = await self.storage.get_user_memories(user_id, limit=50)
        session_memories = [m for m in memories if m.get("session_id") == session_id]
        
        if len(session_memories) < 3:
            return None
        
        combined_input = "\n".join([m.get("input_text", "") or "" for m in session_memories])
        combined_output = "\n".join([m.get("output_text", "") or "" for m in session_memories])
        
        summary = generate_summary(combined_input, combined_output)
        importance = sum(float(m.get("importance", 5.0)) for m in session_memories) / len(session_memories)
        
        compressed_id = await self.storage.insert_memory(
            user_id=user_id,
            agent_name="consolidator",
            session_id=session_id,
            input_text=f"[压缩记忆] 原始对话共 {len(session_memories)} 条",
            output_text=summary,
            summary=f"会话摘要: {summary[:200]}",
            importance=importance,
            category="session_summary",
            tags=["compressed", f"session:{session_id}"]
        )
        
        for m in session_memories:
            await self.storage.delete_memory(m["id"])
        
        return compressed_id
    
    async def boost_important_memories(self, user_id: str):
        async with aiosqlite.connect(str(DB_PATH)) as conn:
            await conn.execute("""
                UPDATE memory_entries 
                SET importance = importance + 0.5
                WHERE user_id = ? AND access_count > 5
            """, (user_id,))
            await conn.commit()
    
    async def get_consolidation_stats(self, user_id: str) -> Dict[str, Any]:
        total_memories = await self.storage.count_user_memories(user_id)
        
        async with aiosqlite.connect(str(DB_PATH)) as conn:
            conn.row_factory = aiosqlite.Row
            
            cursor = await conn.execute("""
                SELECT COUNT(*) as count FROM memory_entries 
                WHERE user_id = ? AND CAST(importance AS REAL) >= 7.0
            """, (user_id,))
            row = await cursor.fetchone()
            important_memories = row["count"] if row else 0
            
            cursor = await conn.execute("""
                SELECT COUNT(*) as count FROM memory_entries 
                WHERE user_id = ? AND access_count > 3
            """, (user_id,))
            row = await cursor.fetchone()
            frequently_accessed = row["count"] if row else 0
            
            cursor = await conn.execute("""
                SELECT consolidation_type, COUNT(*) as count 
                FROM memory_consolidation_logs 
                WHERE user_id = ?
                GROUP BY consolidation_type
            """, (user_id,))
            rows = await cursor.fetchall()
            consolidation_history = [dict(row) for row in rows]
        
        return {
            "total_memories": total_memories,
            "important_memories": important_memories,
            "frequently_accessed": frequently_accessed,
            "consolidation_history": consolidation_history
        }

consolidator = MemoryConsolidator()
