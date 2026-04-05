"""
智能体记忆系统 - 记忆服务主类
提供记忆的存储、检索、删除等核心功能
集成向量存储实现语义检索
"""
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from .storage import storage
from .vector_store import vector_store
from .utils import (
    generate_summary,
    calculate_importance,
    extract_preferences,
    categorize_memory,
    extract_tags,
    format_memories_for_prompt,
)
from .retrieval import rank_memories, filter_memories

class MemoryService:
    def __init__(self):
        self.storage = storage
        self.vector_store = vector_store
        self._use_vector = True
    
    async def store(
        self,
        user_id: str,
        agent_name: str,
        input_text: str,
        output_text: str,
        session_id: str = None,
        metadata: Dict[str, Any] = None
    ) -> str:
        summary = generate_summary(f"{input_text} {output_text}")
        
        importance = calculate_importance(input_text, output_text)
        
        category = categorize_memory(f"{input_text} {output_text}")
        
        tags = extract_tags(f"{input_text} {output_text}")
        
        if metadata:
            if 'importance' in metadata:
                importance = metadata['importance']
            if 'category' in metadata:
                category = metadata['category']
            if 'tags' in metadata:
                tags = metadata['tags']
        
        memory_id = await self.storage.insert_memory(
            user_id=user_id,
            agent_name=agent_name,
            session_id=session_id,
            input_text=input_text,
            output_text=output_text,
            summary=summary,
            importance=importance,
            category=category,
            tags=tags
        )
        
        if self._use_vector and summary:
            vector_metadata = {
                "user_id": user_id,
                "agent_name": agent_name,
                "category": category,
                "importance": importance,
                "created_at": datetime.utcnow().isoformat()
            }
            self.vector_store.add_vector(
                memory_id=memory_id,
                text=summary,
                metadata=vector_metadata
            )
        
        await self._update_user_profile(user_id, input_text, output_text)
        
        return memory_id
    
    async def retrieve(
        self,
        user_id: str,
        query: str,
        limit: int = 5,
        threshold: float = 0.3,
        category: str = None
    ) -> List[Dict[str, Any]]:
        vector_results = []
        if self._use_vector:
            vector_results = self.vector_store.search_by_user(
                user_id=user_id,
                query_text=query,
                n_results=limit * 2
            )
        
        keyword_memories = await self.storage.search_memories(user_id, query, limit * 2)
        
        if category:
            keyword_memories = filter_memories(keyword_memories, category=category)
        
        memory_ids_from_vector = {r[0] for r in vector_results}
        keyword_ids = {m['id'] for m in keyword_memories}
        
        all_memory_ids = list(memory_ids_from_vector | keyword_ids)
        
        if not all_memory_ids:
            return []
        
        all_memories = await self.storage.get_memories_by_ids(all_memory_ids)
        
        memory_map = {m['id']: m for m in all_memories}
        
        scored_memories = []
        for memory in all_memories:
            score = memory.get('importance', 5.0)
            
            for vid, vsim, _ in vector_results:
                if vid == memory['id']:
                    score += vsim * 10
                    break
            
            if memory['id'] in keyword_ids:
                score += 3
            
            scored_memories.append((memory, score))
        
        scored_memories.sort(key=lambda x: x[1], reverse=True)
        
        result_memories = []
        for memory, _ in scored_memories[:limit]:
            await self.storage.update_access(memory['id'])
            result_memories.append(memory)
        
        return result_memories
    
    async def retrieve_by_vector(
        self,
        user_id: str,
        query: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        if not self._use_vector:
            return await self.retrieve(user_id, query, limit)
        
        vector_results = self.vector_store.search_by_user(
            user_id=user_id,
            query_text=query,
            n_results=limit
        )
        
        if not vector_results:
            return []
        
        memory_ids = [r[0] for r in vector_results]
        memories = await self.storage.get_memories_by_ids(memory_ids)
        
        for memory in memories:
            await self.storage.update_access(memory['id'])
        
        return memories
    
    async def get_context(
        self,
        user_id: str,
        query: str = None,
        max_memories: int = 10
    ) -> str:
        if query:
            memories = await self.retrieve(user_id, query, limit=max_memories)
        else:
            memories = await self.storage.get_user_memories(user_id, limit=max_memories)
        
        return format_memories_for_prompt(memories)
    
    async def delete(self, user_id: str, memory_id: str) -> bool:
        memory = await self.storage.get_memory(memory_id)
        
        if not memory:
            return False
        
        if memory.get('user_id') != user_id:
            return False
        
        await self.storage.delete_memory(memory_id)
        
        if self._use_vector:
            self.vector_store.delete_vector(memory_id)
        
        return True
    
    async def clear_user(self, user_id: str) -> int:
        count = await self.storage.count_user_memories(user_id)
        
        await self.storage.delete_user_memories(user_id)
        
        if self._use_vector:
            self.vector_store.delete_vectors_by_user(user_id)
        
        return count
    
    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        profile = await self.storage.get_user_profile(user_id)
        
        if profile:
            return {
                'user_id': user_id,
                'profile': {
                    'age': profile.get('age'),
                    'gender': profile.get('gender'),
                    'occupation': profile.get('occupation'),
                    'current_city': profile.get('current_city'),
                    'budget_min': profile.get('budget_min'),
                    'budget_max': profile.get('budget_max'),
                    'house_type_preference': profile.get('house_type_preference'),
                    'commute_preference': profile.get('commute_preference'),
                },
                'preferences': {
                    'house_type_preference': profile.get('house_type_preference'),
                    'commute_preference': profile.get('commute_preference'),
                },
                'updated_at': profile.get('updated_at'),
            }
        
        return {
            'user_id': user_id,
            'profile': {},
            'preferences': {},
            'updated_at': None,
        }
    
    async def update_user_profile(self, user_id: str, updates: Dict[str, Any]) -> bool:
        current = await self.get_user_profile(user_id)
        
        profile = current.get('profile', {})
        profile.update(updates.get('profile', {}))
        
        preferences = current.get('preferences', {})
        preferences.update(updates.get('preferences', {}))
        
        await self.storage.update_user_profile(
            user_id,
            json.dumps(profile, ensure_ascii=False),
            json.dumps(preferences, ensure_ascii=False)
        )
        
        return True
    
    async def _update_user_profile(self, user_id: str, input_text: str, output_text: str):
        new_preferences = extract_preferences(f"{input_text} {output_text}")
        
        if new_preferences:
            current = await self.get_user_profile(user_id)
            preferences = current.get('preferences', {})
            preferences.update(new_preferences)
            
            await self.storage.update_user_profile(
                user_id,
                json.dumps(current.get('profile', {}), ensure_ascii=False),
                json.dumps(preferences, ensure_ascii=False)
            )
    
    async def get_memory_stats(self, user_id: str) -> Dict[str, Any]:
        total = await self.storage.count_user_memories(user_id)
        
        memories = await self.storage.get_user_memories(user_id, limit=100)
        
        categories = {}
        for memory in memories:
            cat = memory.get('category', 'fact')
            categories[cat] = categories.get(cat, 0) + 1
        
        avg_importance = 0
        if memories:
            avg_importance = sum(m.get('importance', 5.0) for m in memories) / len(memories)
        
        vector_stats = self.vector_store.get_stats()
        
        return {
            'total_memories': total,
            'categories': categories,
            'average_importance': round(avg_importance, 2),
            'vector_store': vector_stats,
        }
    
    async def get_recent_activity(self, user_id: str, days: int = 7) -> List[Dict[str, Any]]:
        return await self.storage.get_recent_memories(user_id, days)
    
    def enable_vector_search(self, enabled: bool = True):
        self._use_vector = enabled
    
    def get_vector_stats(self) -> Dict[str, Any]:
        return self.vector_store.get_stats()

memory_service = MemoryService()
