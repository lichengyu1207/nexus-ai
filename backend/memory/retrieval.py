"""
智能体记忆系统 - 检索算法
实现记忆的排序与过滤逻辑
"""
import math
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

def calculate_freshness_score(last_accessed: str, half_life_days: int = 7) -> float:
    if not last_accessed:
        return 0.5
    
    try:
        last = datetime.fromisoformat(last_accessed.replace('Z', '+00:00'))
        now = datetime.utcnow()
        days_since = (now - last.replace(tzinfo=None)).days
        return math.exp(-days_since / half_life_days)
    except:
        return 0.5

def calculate_access_score(access_count: int) -> float:
    return math.log(access_count + 1)

def rank_memories(
    memories: List[Dict[str, Any]],
    query: Optional[str] = None,
    weights: Dict[str, float] = None
) -> List[str]:
    if weights is None:
        weights = {
            'importance': 0.4,
            'freshness': 0.3,
            'access': 0.2,
            'similarity': 0.1,
        }
    
    scored_memories = []
    
    for memory in memories:
        importance = memory.get('importance', 5.0)
        importance_score = importance * 10
        
        freshness_score = calculate_freshness_score(memory.get('last_accessed'))
        
        access_score = calculate_access_score(memory.get('access_count', 0))
        
        similarity_score = memory.get('similarity', 0.5)
        
        total_score = (
            weights['importance'] * importance_score +
            weights['freshness'] * freshness_score * 10 +
            weights['access'] * access_score +
            weights['similarity'] * similarity_score * 10
        )
        
        scored_memories.append({
            'memory_id': memory.get('id'),
            'score': total_score,
            'importance': importance,
            'freshness': freshness_score,
            'access': access_score,
        })
    
    scored_memories.sort(key=lambda x: x['score'], reverse=True)
    
    return [m['memory_id'] for m in scored_memories]

def filter_memories(
    memories: List[Dict[str, Any]],
    category: Optional[str] = None,
    min_importance: Optional[float] = None,
    max_age_days: Optional[int] = None,
    agent_name: Optional[str] = None
) -> List[Dict[str, Any]]:
    filtered = memories
    
    if category:
        filtered = [m for m in filtered if m.get('category') == category]
    
    if min_importance is not None:
        filtered = [m for m in filtered if m.get('importance', 0) >= min_importance]
    
    if max_age_days is not None:
        cutoff = datetime.utcnow() - timedelta(days=max_age_days)
        filtered = [
            m for m in filtered 
            if datetime.fromisoformat(m.get('created_at', '2000-01-01').replace('Z', '+00:00')).replace(tzinfo=None) >= cutoff
        ]
    
    if agent_name:
        filtered = [m for m in filtered if m.get('agent_name') == agent_name]
    
    return filtered

def deduplicate_memories(
    memories: List[Dict[str, Any]],
    similarity_threshold: float = 0.9
) -> List[Dict[str, Any]]:
    if len(memories) <= 1:
        return memories
    
    unique = [memories[0]]
    
    for memory in memories[1:]:
        is_duplicate = False
        
        for existing in unique:
            if _calculate_text_similarity(
                memory.get('summary', ''),
                existing.get('summary', '')
            ) >= similarity_threshold:
                is_duplicate = True
                if memory.get('importance', 0) > existing.get('importance', 0):
                    unique.remove(existing)
                    unique.append(memory)
                break
        
        if not is_duplicate:
            unique.append(memory)
    
    return unique

def _calculate_text_similarity(text1: str, text2: str) -> float:
    if not text1 or not text2:
        return 0.0
    
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1 & words2
    union = words1 | words2
    
    return len(intersection) / len(union)
