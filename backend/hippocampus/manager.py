"""
海马体记忆中枢系统 - 记忆管理器
执行记忆整理、合并、遗忘等操作（类似睡眠中的记忆巩固）
"""
import math
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from .storage import hippocampus_storage, HippocampusStorage
from .encoder import MemoryUnit, memory_encoder
from .associator import MemoryAssociator

FORGET_THRESHOLD = 0.2
MERGE_SIMILARITY_THRESHOLD = 0.85
CONSOLIDATION_BATCH_SIZE = 100
MIN_ACCESS_FOR_LONG_TERM = 3

@dataclass
class ConsolidationResult:
    user_id: str
    memories_processed: int = 0
    memories_merged: int = 0
    memories_forgotten: int = 0
    relations_created: int = 0
    details: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = []

class MemoryManager:
    def __init__(self, storage: HippocampusStorage = None):
        self.storage = storage or hippocampus_storage
        self.associator = MemoryAssociator(storage)
    
    async def consolidate(self, user_id: str = None) -> ConsolidationResult:
        result = ConsolidationResult(user_id=user_id or "system")
        
        memories = await self.storage.get_memories_for_consolidation(
            user_id=user_id,
            limit=CONSOLIDATION_BATCH_SIZE
        )
        result.memories_processed = len(memories)
        
        merged_count = await self._merge_similar_memories(memories)
        result.memories_merged = merged_count
        
        forgotten_count = await self._forget_low_value_memories()
        result.memories_forgotten = forgotten_count
        
        await self._update_importance_scores(memories)
        
        relations_count = await self.associator.build_associations(user_id)
        result.relations_created = relations_count
        
        return result
    
    async def _merge_similar_memories(self, memories: List[MemoryUnit]) -> int:
        if len(memories) < 2:
            return 0
        
        merged_count = 0
        processed = set()
        
        for i, memory1 in enumerate(memories):
            if memory1.id in processed:
                continue
            
            for j, memory2 in enumerate(memories[i+1:], i+1):
                if memory2.id in processed:
                    continue
                
                similarity = self._calculate_similarity(memory1, memory2)
                
                if similarity >= MERGE_SIMILARITY_THRESHOLD:
                    await self._merge_two_memories(memory1, memory2)
                    processed.add(memory2.id)
                    merged_count += 1
        
        return merged_count
    
    def _calculate_similarity(self, memory1: MemoryUnit, memory2: MemoryUnit) -> float:
        if memory1.user_id != memory2.user_id:
            return 0.0
        
        if memory1.type != memory2.type:
            return 0.0
        
        content_similarity = self._text_similarity(
            memory1.content,
            memory2.content
        )
        
        entity_overlap = 0.0
        if memory1.entities and memory2.entities:
            entities1 = set(memory1.entities)
            entities2 = set(memory2.entities)
            if entities1 and entities2:
                entity_overlap = len(entities1 & entities2) / len(entities1 | entities2)
        
        summary_similarity = 0.0
        if memory1.summary and memory2.summary:
            summary_similarity = self._text_similarity(
                memory1.summary,
                memory2.summary
            )
        
        return content_similarity * 0.5 + entity_overlap * 0.3 + summary_similarity * 0.2
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        if not text1 or not text2:
            return 0.0
        
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union)
    
    async def _merge_two_memories(self, memory1: MemoryUnit, memory2: MemoryUnit):
        merged_content = memory1.content
        if memory2.content and memory2.content not in merged_content:
            merged_content += "\n" + memory2.content
        
        merged_summary = memory1.summary or memory2.summary
        if memory1.summary and memory2.summary:
            if len(memory1.summary) >= len(memory2.summary):
                merged_summary = memory1.summary
            else:
                merged_summary = memory2.summary
        
        merged_importance = max(memory1.importance, memory2.importance)
        
        merged_entities = list(set(memory1.entities + memory2.entities))
        
        merged_agents = list(set(memory1.agents + memory2.agents))
        
        merged_context = {**memory2.context, **memory1.context}
        
        merged_access_count = memory1.access_count + memory2.access_count
        
        memory1.content = merged_content
        memory1.summary = merged_summary
        memory1.importance = merged_importance
        memory1.entities = merged_entities
        memory1.agents = merged_agents
        memory1.context = merged_context
        memory1.access_count = merged_access_count
        memory1.updated_at = datetime.utcnow().isoformat()
        
        await self.storage.store(memory1)
        
        relations = await self.storage.get_relations(memory2.id)
        for rel in relations:
            other_id = rel['memory_id1'] if rel['memory_id2'] == memory2.id else rel['memory_id2']
            if other_id != memory1.id:
                await self.storage.store_relation(
                    memory1.id,
                    other_id,
                    rel['relation_type'],
                    rel['strength']
                )
        
        await self.storage.delete(memory2.id)
    
    async def _forget_low_value_memories(self) -> int:
        memories = await self.storage.get_low_importance_memories(
            threshold=FORGET_THRESHOLD,
            days_old=30,
            limit=CONSOLIDATION_BATCH_SIZE
        )
        
        forgotten_count = 0
        for memory in memories:
            if memory.importance < FORGET_THRESHOLD and memory.access_count < 2:
                await self.storage.delete(memory.id)
                forgotten_count += 1
        
        return forgotten_count
    
    async def _update_importance_scores(self, memories: List[MemoryUnit]):
        for memory in memories:
            new_importance = self._recalculate_importance(memory)
            
            if abs(new_importance - memory.importance) > 0.05:
                await self.storage.update_importance(memory.id, new_importance)
    
    def _recalculate_importance(self, memory: MemoryUnit) -> float:
        base_importance = memory.importance
        
        access_factor = min(memory.access_count / 10, 0.3)
        
        freshness_factor = 0.0
        if memory.last_access:
            try:
                last = datetime.fromisoformat(memory.last_access.replace('Z', '+00:00')).replace(tzinfo=None)
                days_since = (datetime.utcnow() - last).days
                freshness_factor = max(0, 0.2 * math.exp(-days_since / 30))
            except:
                pass
        
        new_importance = base_importance + access_factor + freshness_factor
        
        return min(1.0, max(0.0, new_importance))
    
    async def promote_to_long_term(self, memory_id: str) -> bool:
        memory = await self.storage.get(memory_id)
        
        if not memory:
            return False
        
        if memory.access_count >= MIN_ACCESS_FOR_LONG_TERM or memory.importance >= 0.7:
            memory.importance = max(memory.importance, 0.8)
            memory.updated_at = datetime.utcnow().isoformat()
            await self.storage.store(memory)
            return True
        
        return False
    
    async def get_memory_health(self, user_id: str) -> Dict[str, Any]:
        stats = await self.storage.get_memory_stats(user_id)
        
        memories = await self.storage.get_user_memories(user_id, limit=100)
        
        if memories:
            avg_importance = sum(m.importance for m in memories) / len(memories)
            avg_access = sum(m.access_count for m in memories) / len(memories)
            
            type_distribution = {}
            for m in memories:
                type_distribution[m.type] = type_distribution.get(m.type, 0) + 1
            
            entity_count = sum(len(m.entities) for m in memories)
        else:
            avg_importance = 0
            avg_access = 0
            type_distribution = {}
            entity_count = 0
        
        return {
            'total_memories': stats['total_memories'],
            'average_importance': round(avg_importance, 3),
            'average_access_count': round(avg_access, 2),
            'type_distribution': type_distribution,
            'total_entities': entity_count,
            'health_score': self._calculate_health_score(
                stats['total_memories'],
                avg_importance,
                avg_access
            ),
        }
    
    def _calculate_health_score(
        self,
        total: int,
        avg_importance: float,
        avg_access: float
    ) -> float:
        quantity_score = min(total / 50, 1.0) * 0.3
        
        quality_score = avg_importance * 0.4
        
        activity_score = min(avg_access / 5, 1.0) * 0.3
        
        return round(quantity_score + quality_score + activity_score, 3)
    
    async def cleanup_orphaned_entities(self) -> int:
        async with self.storage.storage.db as db:
            result = await db.execute("""
                DELETE FROM memory_entities 
                WHERE id NOT IN (
                    SELECT DISTINCT entity_id FROM memory_entity_map
                )
            """)
            return result.rowcount if hasattr(result, 'rowcount') else 0

memory_manager = MemoryManager()
