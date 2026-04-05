"""
海马体记忆中枢系统 - 检索器
支持语义检索、关键词检索、时序检索、混合检索
"""
import math
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from .storage import hippocampus_storage, HippocampusStorage
from .encoder import MemoryUnit

@dataclass
class RetrievalResult:
    memory: MemoryUnit
    score: float
    match_type: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'memory': self.memory.to_dict(),
            'score': self.score,
            'match_type': self.match_type,
        }

class MemoryRetriever:
    def __init__(self, storage: HippocampusStorage = None):
        self.storage = storage or hippocampus_storage
        self._vector_store = None
    
    def _get_vector_store(self):
        if self._vector_store is None:
            try:
                from backend.memory.vector_store import vector_store
                self._vector_store = vector_store
            except:
                pass
        return self._vector_store
    
    async def retrieve(
        self,
        user_id: str,
        query: str,
        limit: int = 10,
        min_importance: float = 0.3,
        time_range: Tuple[datetime, datetime] = None,
        memory_type: str = None
    ) -> List[RetrievalResult]:
        vector_results = await self._vector_search(user_id, query, limit * 2)
        
        keyword_results = await self._keyword_search(user_id, query, limit * 2)
        
        all_memory_ids = set()
        memory_sources = {}
        
        for memory_id, score in vector_results:
            all_memory_ids.add(memory_id)
            memory_sources[memory_id] = ('vector', score)
        
        for memory_id, score in keyword_results:
            if memory_id in all_memory_ids:
                old_type, old_score = memory_sources[memory_id]
                memory_sources[memory_id] = ('hybrid', max(old_score, score))
            else:
                all_memory_ids.add(memory_id)
                memory_sources[memory_id] = ('keyword', score)
        
        if not all_memory_ids:
            return []
        
        memories = await self.storage.get_by_ids(list(all_memory_ids))
        memory_map = {m.id: m for m in memories}
        
        scored_results = []
        for memory in memories:
            if memory.importance < min_importance:
                continue
            
            if memory_type and memory.type != memory_type:
                continue
            
            if time_range:
                memory_time = datetime.fromisoformat(memory.timestamp.replace('Z', '+00:00')).replace(tzinfo=None)
                if not (time_range[0] <= memory_time <= time_range[1]):
                    continue
            
            match_type, base_score = memory_sources.get(memory.id, ('unknown', 0.5))
            
            final_score = self._calculate_final_score(memory, base_score)
            
            scored_results.append(RetrievalResult(
                memory=memory,
                score=final_score,
                match_type=match_type
            ))
        
        scored_results.sort(key=lambda x: x.score, reverse=True)
        
        results = scored_results[:limit]
        
        for result in results:
            await self.storage.update_access(result.memory.id)
        
        return results
    
    async def _vector_search(
        self,
        user_id: str,
        query: str,
        limit: int
    ) -> List[Tuple[str, float]]:
        vector_store = self._get_vector_store()
        
        if not vector_store:
            return []
        
        try:
            results = vector_store.search_by_user(
                user_id=user_id,
                query_text=query,
                n_results=limit
            )
            
            return [(r[0], r[1]) for r in results]
        except Exception as e:
            print(f"Vector search error: {e}")
            return []
    
    async def _keyword_search(
        self,
        user_id: str,
        query: str,
        limit: int
    ) -> List[Tuple[str, float]]:
        memories = await self.storage.search(user_id, query, limit)
        
        results = []
        for memory in memories:
            score = self._calculate_keyword_score(memory, query)
            results.append((memory.id, score))
        
        return results
    
    def _calculate_keyword_score(self, memory: MemoryUnit, query: str) -> float:
        query_words = set(query.lower().split())
        
        content_words = set(memory.content.lower().split())
        summary_words = set(memory.summary.lower().split()) if memory.summary else set()
        
        content_overlap = len(query_words & content_words) / len(query_words) if query_words else 0
        summary_overlap = len(query_words & summary_words) / len(query_words) if query_words else 0
        
        return max(content_overlap, summary_overlap)
    
    def _calculate_final_score(self, memory: MemoryUnit, base_score: float) -> float:
        weights = {
            'similarity': 0.5,
            'importance': 0.3,
            'freshness': 0.2,
        }
        
        similarity_score = base_score
        
        importance_score = memory.importance
        
        freshness_score = self._calculate_freshness(memory)
        
        final_score = (
            weights['similarity'] * similarity_score +
            weights['importance'] * importance_score +
            weights['freshness'] * freshness_score
        )
        
        return final_score
    
    def _calculate_freshness(self, memory: MemoryUnit, half_life_days: int = 30) -> float:
        try:
            if memory.last_access:
                last = datetime.fromisoformat(memory.last_access.replace('Z', '+00:00')).replace(tzinfo=None)
            elif memory.timestamp:
                last = datetime.fromisoformat(memory.timestamp.replace('Z', '+00:00')).replace(tzinfo=None)
            else:
                return 0.5
            
            now = datetime.utcnow()
            days_since = (now - last).days
            
            return math.exp(-days_since / half_life_days)
        except:
            return 0.5
    
    async def retrieve_by_entity(
        self,
        user_id: str,
        entity: str,
        limit: int = 10
    ) -> List[RetrievalResult]:
        memories = await self.storage.search_by_entity(user_id, entity, limit)
        
        results = []
        for memory in memories:
            score = memory.importance * 0.7 + 0.3
            
            results.append(RetrievalResult(
                memory=memory,
                score=score,
                match_type='entity'
            ))
        
        return results
    
    async def retrieve_by_time(
        self,
        user_id: str,
        start_time: datetime,
        end_time: datetime,
        limit: int = 50
    ) -> List[RetrievalResult]:
        memories = await self.storage.search_by_time(user_id, start_time, end_time, limit)
        
        results = []
        for memory in memories:
            results.append(RetrievalResult(
                memory=memory,
                score=memory.importance,
                match_type='time'
            ))
        
        return results
    
    async def retrieve_recent(
        self,
        user_id: str,
        days: int = 7,
        limit: int = 20
    ) -> List[RetrievalResult]:
        memories = await self.storage.get_user_memories(
            user_id=user_id,
            limit=limit,
            days=days
        )
        
        results = []
        for memory in memories:
            results.append(RetrievalResult(
                memory=memory,
                score=memory.importance,
                match_type='recent'
            ))
        
        return results
    
    async def retrieve_important(
        self,
        user_id: str,
        min_importance: float = 0.7,
        limit: int = 20
    ) -> List[RetrievalResult]:
        memories = await self.storage.get_user_memories(
            user_id=user_id,
            limit=limit,
            min_importance=min_importance
        )
        
        results = []
        for memory in memories:
            results.append(RetrievalResult(
                memory=memory,
                score=memory.importance,
                match_type='important'
            ))
        
        return results
    
    async def retrieve_by_type(
        self,
        user_id: str,
        memory_type: str,
        limit: int = 20
    ) -> List[RetrievalResult]:
        memories = await self.storage.get_user_memories(
            user_id=user_id,
            limit=limit,
            memory_type=memory_type
        )
        
        results = []
        for memory in memories:
            results.append(RetrievalResult(
                memory=memory,
                score=memory.importance,
                match_type='type'
            ))
        
        return results
    
    async def get_context_for_prompt(
        self,
        user_id: str,
        query: str = None,
        max_memories: int = 5
    ) -> str:
        if query:
            results = await self.retrieve(user_id, query, limit=max_memories)
        else:
            results = await self.retrieve_recent(user_id, days=7, limit=max_memories)
        
        if not results:
            return ""
        
        context_parts = ["【历史记忆】"]
        for i, result in enumerate(results, 1):
            memory = result.memory
            if memory.timestamp:
                if isinstance(memory.timestamp, str):
                    time_str = memory.timestamp[:10]
                else:
                    time_str = memory.timestamp.strftime('%Y-%m-%d')
            else:
                time_str = "未知时间"
            context_parts.append(f"{i}. [{time_str}] {memory.summary or memory.content[:100]}")
        
        return "\n".join(context_parts)
    
    async def get_user_preferences(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        results = await self.retrieve_by_type(user_id, 'semantic', limit=limit)
        
        preferences = []
        for result in results:
            memory = result.memory
            if memory.context.get('is_preference'):
                preferences.append({
                    'content': memory.content,
                    'importance': memory.importance,
                    'created_at': memory.created_at,
                })
        
        return preferences

memory_retriever = MemoryRetriever()
