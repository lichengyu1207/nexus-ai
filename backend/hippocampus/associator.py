"""
海马体记忆中枢系统 - 记忆联想器
发现记忆间的关联，构建知识图谱
"""
import math
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Set, Tuple
from collections import defaultdict

from .storage import hippocampus_storage, HippocampusStorage
from .encoder import MemoryUnit

RELATION_TYPE_SIMILAR = "similar"
RELATION_TYPE_CAUSAL = "causal"
RELATION_TYPE_SEQUENTIAL = "sequential"
RELATION_TYPE_ASSOCIATIVE = "associative"
RELATION_TYPE_ENTITY = "entity"

ASSOCIATION_THRESHOLD = 0.5
TIME_PROXIMITY_HOURS = 24
MAX_RELATIONS_PER_MEMORY = 10

class MemoryAssociator:
    def __init__(self, storage: HippocampusStorage = None):
        self.storage = storage or hippocampus_storage
    
    async def get_related(
        self,
        memory_id: str,
        limit: int = 5,
        min_strength: float = 0.3
    ) -> List[Tuple[MemoryUnit, str, float]]:
        relations = await self.storage.get_relations(memory_id)
        
        filtered_relations = [
            r for r in relations
            if r.get('strength', 0) >= min_strength
        ]
        
        filtered_relations.sort(key=lambda x: x.get('strength', 0), reverse=True)
        
        filtered_relations = filtered_relations[:limit]
        
        if not filtered_relations:
            return []
        
        related_ids = []
        for rel in filtered_relations:
            other_id = rel['memory_id1'] if rel['memory_id2'] == memory_id else rel['memory_id2']
            related_ids.append((other_id, rel['relation_type'], rel['strength']))
        
        memories = await self.storage.get_by_ids([r[0] for r in related_ids])
        memory_map = {m.id: m for m in memories}
        
        results = []
        for memory_id, rel_type, strength in related_ids:
            if memory_id in memory_map:
                results.append((memory_map[memory_id], rel_type, strength))
        
        return results
    
    async def build_associations(self, user_id: str = None) -> int:
        memories = await self.storage.get_memories_for_consolidation(
            user_id=user_id,
            limit=200
        )
        
        if len(memories) < 2:
            return 0
        
        relations_created = 0
        processed_pairs = set()
        
        for i, memory1 in enumerate(memories):
            for j, memory2 in enumerate(memories[i+1:], i+1):
                pair_key = tuple(sorted([memory1.id, memory2.id]))
                if pair_key in processed_pairs:
                    continue
                
                relation = await self._find_relation(memory1, memory2)
                
                if relation:
                    rel_type, strength = relation
                    await self.storage.store_relation(
                        memory1.id,
                        memory2.id,
                        rel_type,
                        strength
                    )
                    relations_created += 1
                    processed_pairs.add(pair_key)
        
        return relations_created
    
    async def _find_relation(
        self,
        memory1: MemoryUnit,
        memory2: MemoryUnit
    ) -> Optional[Tuple[str, float]]:
        if memory1.user_id != memory2.user_id:
            return None
        
        entity_relation = self._check_entity_overlap(memory1, memory2)
        if entity_relation:
            return entity_relation
        
        time_relation = self._check_time_proximity(memory1, memory2)
        if time_relation:
            return time_relation
        
        content_relation = self._check_content_similarity(memory1, memory2)
        if content_relation:
            return content_relation
        
        return None
    
    def _check_entity_overlap(
        self,
        memory1: MemoryUnit,
        memory2: MemoryUnit
    ) -> Optional[Tuple[str, float]]:
        if not memory1.entities or not memory2.entities:
            return None
        
        entities1 = set(memory1.entities)
        entities2 = set(memory2.entities)
        
        common = entities1 & entities2
        
        if not common:
            return None
        
        overlap_ratio = len(common) / min(len(entities1), len(entities2))
        
        if overlap_ratio >= 0.3:
            strength = min(overlap_ratio * 1.5, 1.0)
            return (RELATION_TYPE_ENTITY, strength)
        
        return None
    
    def _check_time_proximity(
        self,
        memory1: MemoryUnit,
        memory2: MemoryUnit
    ) -> Optional[Tuple[str, float]]:
        try:
            time1 = datetime.fromisoformat(memory1.timestamp.replace('Z', '+00:00')).replace(tzinfo=None)
            time2 = datetime.fromisoformat(memory2.timestamp.replace('Z', '+00:00')).replace(tzinfo=None)
            
            hours_diff = abs((time1 - time2).total_seconds()) / 3600
            
            if hours_diff <= TIME_PROXIMITY_HOURS:
                strength = max(0, 1.0 - hours_diff / TIME_PROXIMITY_HOURS)
                
                if time1 < time2:
                    return (RELATION_TYPE_SEQUENTIAL, strength)
                else:
                    return (RELATION_TYPE_SEQUENTIAL, strength)
        except:
            pass
        
        return None
    
    def _check_content_similarity(
        self,
        memory1: MemoryUnit,
        memory2: MemoryUnit
    ) -> Optional[Tuple[str, float]]:
        if memory1.type != memory2.type:
            return None
        
        similarity = self._text_similarity(memory1.content, memory2.content)
        
        if similarity >= ASSOCIATION_THRESHOLD:
            return (RELATION_TYPE_SIMILAR, similarity)
        
        return None
    
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
    
    async def find_memory_path(
        self,
        start_memory_id: str,
        end_memory_id: str,
        max_depth: int = 3
    ) -> List[List[MemoryUnit]]:
        if start_memory_id == end_memory_id:
            start_memory = await self.storage.get(start_memory_id)
            return [[start_memory]] if start_memory else []
        
        paths = []
        visited = set()
        
        async def dfs(current_id: str, path: List[str], depth: int):
            if depth > max_depth:
                return
            
            if current_id in visited:
                return
            
            visited.add(current_id)
            
            if current_id == end_memory_id:
                memories = await self.storage.get_by_ids(path)
                memory_map = {m.id: m for m in memories}
                ordered_memories = [memory_map[mid] for mid in path if mid in memory_map]
                paths.append(ordered_memories)
                return
            
            relations = await self.storage.get_relations(current_id)
            
            for rel in relations:
                other_id = rel['memory_id1'] if rel['memory_id2'] == current_id else rel['memory_id2']
                
                if other_id not in visited:
                    await dfs(other_id, path + [other_id], depth + 1)
            
            visited.remove(current_id)
        
        await dfs(start_memory_id, [start_memory_id], 0)
        
        return paths
    
    async def get_memory_cluster(
        self,
        memory_id: str,
        max_size: int = 10
    ) -> List[MemoryUnit]:
        cluster = set([memory_id])
        frontier = [memory_id]
        
        while frontier and len(cluster) < max_size:
            current = frontier.pop(0)
            
            relations = await self.storage.get_relations(current)
            
            for rel in relations:
                other_id = rel['memory_id1'] if rel['memory_id2'] == current else rel['memory_id2']
                
                if other_id not in cluster and len(cluster) < max_size:
                    cluster.add(other_id)
                    frontier.append(other_id)
        
        memories = await self.storage.get_by_ids(list(cluster))
        
        return memories
    
    async def get_association_stats(self, user_id: str) -> Dict[str, Any]:
        memories = await self.storage.get_user_memories(user_id, limit=100)
        
        if not memories:
            return {
                'total_memories': 0,
                'total_relations': 0,
                'avg_relations_per_memory': 0,
                'relation_types': {},
                'most_connected_memory': None,
            }
        
        total_relations = 0
        relation_counts = defaultdict(int)
        memory_connections = defaultdict(int)
        
        for memory in memories:
            relations = await self.storage.get_relations(memory.id)
            total_relations += len(relations)
            memory_connections[memory.id] = len(relations)
            
            for rel in relations:
                relation_counts[rel['relation_type']] += 1
        
        avg_relations = total_relations / len(memories) if memories else 0
        
        most_connected_id = max(memory_connections, key=memory_connections.get) if memory_connections else None
        most_connected_memory = None
        if most_connected_id:
            most_connected_memory = await self.storage.get(most_connected_id)
        
        return {
            'total_memories': len(memories),
            'total_relations': total_relations,
            'avg_relations_per_memory': round(avg_relations, 2),
            'relation_types': dict(relation_counts),
            'most_connected_memory': {
                'id': most_connected_id,
                'summary': most_connected_memory.summary if most_connected_memory else None,
                'connections': memory_connections.get(most_connected_id, 0),
            } if most_connected_id else None,
        }
    
    async def suggest_related_memories(
        self,
        user_id: str,
        current_content: str,
        limit: int = 5
    ) -> List[Tuple[MemoryUnit, float, str]]:
        from .encoder import memory_encoder
        
        entities = memory_encoder.extract_entities(current_content)
        
        entity_memories = []
        for entity in entities[:3]:
            memories = await self.storage.search_by_entity(user_id, entity, limit=3)
            for memory in memories:
                entity_memories.append((memory, 0.7, f"包含实体: {entity}"))
        
        keyword_memories = await self.storage.search(user_id, current_content[:100], limit=5)
        keyword_results = [(m, 0.5, "关键词匹配") for m in keyword_memories]
        
        all_results = entity_memories + keyword_results
        
        seen_ids = set()
        unique_results = []
        for memory, score, reason in all_results:
            if memory.id not in seen_ids:
                seen_ids.add(memory.id)
                unique_results.append((memory, score, reason))
        
        unique_results.sort(key=lambda x: x[1], reverse=True)
        
        return unique_results[:limit]

memory_associator = MemoryAssociator()
