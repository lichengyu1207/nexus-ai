"""
海马体记忆中枢系统 - API路由
提供记忆存储、检索、管理等API接口
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

from backend.auth import get_current_user
from backend.hippocampus.encoder import memory_encoder, MemoryUnit
from backend.hippocampus.storage import hippocampus_storage
from backend.hippocampus.retriever import memory_retriever, RetrievalResult
from backend.hippocampus.manager import memory_manager, ConsolidationResult
from backend.hippocampus.associator import memory_associator

router = APIRouter(prefix="/api/hippocampus", tags=["海马体记忆中枢"])

class MemoryCreateRequest(BaseModel):
    content: str = Field(..., description="记忆内容")
    source: str = Field(default="manual", description="来源类型")
    memory_type: str = Field(default="episodic", description="记忆类型: episodic/semantic/procedural")
    agents: List[str] = Field(default_factory=list, description="参与的智能体")
    context: Dict[str, Any] = Field(default_factory=dict, description="上下文信息")

class MemorySearchRequest(BaseModel):
    query: str = Field(..., description="搜索查询")
    limit: int = Field(default=10, ge=1, le=50, description="返回数量限制")
    min_importance: float = Field(default=0.3, ge=0, le=1, description="最小重要性")
    memory_type: Optional[str] = Field(default=None, description="记忆类型过滤")

class MemoryResponse(BaseModel):
    id: str
    user_id: str
    type: str
    content: str
    summary: str
    importance: float
    timestamp: str
    source: str
    agents: List[str]
    entities: List[str]
    context: Dict[str, Any]
    access_count: int
    last_access: Optional[str]
    created_at: str

class SearchResultResponse(BaseModel):
    memory: MemoryResponse
    score: float
    match_type: str

class MemoryStatsResponse(BaseModel):
    total_memories: int
    by_type: Dict[str, int]
    average_importance: float
    health_score: float
    type_distribution: Dict[str, int]

class RelatedMemoryResponse(BaseModel):
    memory: MemoryResponse
    relation_type: str
    strength: float

def memory_to_response(memory: MemoryUnit) -> MemoryResponse:
    return MemoryResponse(
        id=memory.id,
        user_id=memory.user_id,
        type=memory.type,
        content=memory.content,
        summary=memory.summary,
        importance=memory.importance,
        timestamp=memory.timestamp,
        source=memory.source,
        agents=memory.agents,
        entities=memory.entities,
        context=memory.context,
        access_count=memory.access_count,
        last_access=memory.last_access,
        created_at=memory.created_at,
    )

@router.post("/memories", response_model=MemoryResponse)
async def create_memory(
    request: MemoryCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user.get("id") or current_user.get("user_id")
    
    memory = memory_encoder.encode(
        user_id=user_id,
        content=request.content,
        source=request.source,
        agents=request.agents,
        context=request.context,
        memory_type=request.memory_type
    )
    
    memory_id = await hippocampus_storage.store(memory)
    
    return memory_to_response(memory)

@router.get("/memories", response_model=List[MemoryResponse])
async def list_memories(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    memory_type: Optional[str] = Query(default=None),
    days: Optional[int] = Query(default=None),
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user.get("id") or current_user.get("user_id")
    
    memories = await hippocampus_storage.get_user_memories(
        user_id=user_id,
        limit=limit,
        offset=offset,
        memory_type=memory_type,
        days=days
    )
    
    return [memory_to_response(m) for m in memories]

@router.get("/memories/{memory_id}", response_model=MemoryResponse)
async def get_memory(
    memory_id: str,
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user.get("id") or current_user.get("user_id")
    
    memory = await hippocampus_storage.get(memory_id)
    
    if not memory:
        raise HTTPException(status_code=404, detail="记忆不存在")
    
    if memory.user_id != user_id:
        raise HTTPException(status_code=403, detail="无权访问此记忆")
    
    await hippocampus_storage.update_access(memory_id)
    
    return memory_to_response(memory)

@router.delete("/memories/{memory_id}")
async def delete_memory(
    memory_id: str,
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user.get("id") or current_user.get("user_id")
    
    memory = await hippocampus_storage.get(memory_id)
    
    if not memory:
        raise HTTPException(status_code=404, detail="记忆不存在")
    
    if memory.user_id != user_id:
        raise HTTPException(status_code=403, detail="无权删除此记忆")
    
    await hippocampus_storage.delete(memory_id)
    
    return {"success": True, "message": "记忆已删除"}

@router.post("/search", response_model=List[SearchResultResponse])
async def search_memories(
    request: MemorySearchRequest,
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user.get("id") or current_user.get("user_id")
    
    results = await memory_retriever.retrieve(
        user_id=user_id,
        query=request.query,
        limit=request.limit,
        min_importance=request.min_importance,
        memory_type=request.memory_type
    )
    
    return [
        SearchResultResponse(
            memory=memory_to_response(r.memory),
            score=r.score,
            match_type=r.match_type
        )
        for r in results
    ]

@router.get("/search/entity/{entity}", response_model=List[MemoryResponse])
async def search_by_entity(
    entity: str,
    limit: int = Query(default=10, ge=1, le=50),
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user.get("id") or current_user.get("user_id")
    
    memories = await hippocampus_storage.search_by_entity(user_id, entity, limit)
    
    return [memory_to_response(m) for m in memories]

@router.get("/recent", response_model=List[MemoryResponse])
async def get_recent_memories(
    days: int = Query(default=7, ge=1, le=30),
    limit: int = Query(default=20, ge=1, le=50),
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user.get("id") or current_user.get("user_id")
    
    memories = await hippocampus_storage.get_user_memories(
        user_id=user_id,
        limit=limit,
        days=days
    )
    
    return [memory_to_response(m) for m in memories]

@router.get("/important", response_model=List[MemoryResponse])
async def get_important_memories(
    min_importance: float = Query(default=0.7, ge=0, le=1),
    limit: int = Query(default=20, ge=1, le=50),
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user.get("id") or current_user.get("user_id")
    
    memories = await hippocampus_storage.get_user_memories(
        user_id=user_id,
        limit=limit,
        min_importance=min_importance
    )
    
    return [memory_to_response(m) for m in memories]

@router.get("/context", response_model=Dict[str, Any])
async def get_memory_context(
    query: Optional[str] = Query(default=None),
    max_memories: int = Query(default=5, ge=1, le=20),
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user.get("id") or current_user.get("user_id")
    
    context = await memory_retriever.get_context_for_prompt(
        user_id=user_id,
        query=query,
        max_memories=max_memories
    )
    
    return {
        "context": context,
        "query": query
    }

@router.get("/stats", response_model=MemoryStatsResponse)
async def get_memory_stats(
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user.get("id") or current_user.get("user_id")
    
    stats = await hippocampus_storage.get_memory_stats(user_id)
    health = await memory_manager.get_memory_health(user_id)
    
    return MemoryStatsResponse(
        total_memories=stats['total_memories'],
        by_type=stats['by_type'],
        average_importance=stats['average_importance'],
        health_score=health['health_score'],
        type_distribution=health['type_distribution']
    )

@router.get("/health")
async def get_memory_health(
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user.get("id") or current_user.get("user_id")
    
    health = await memory_manager.get_memory_health(user_id)
    
    return health

@router.get("/memories/{memory_id}/related", response_model=List[RelatedMemoryResponse])
async def get_related_memories(
    memory_id: str,
    limit: int = Query(default=5, ge=1, le=20),
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user.get("id") or current_user.get("user_id")
    
    memory = await hippocampus_storage.get(memory_id)
    
    if not memory:
        raise HTTPException(status_code=404, detail="记忆不存在")
    
    if memory.user_id != user_id:
        raise HTTPException(status_code=403, detail="无权访问此记忆")
    
    related = await memory_associator.get_related(memory_id, limit=limit)
    
    return [
        RelatedMemoryResponse(
            memory=memory_to_response(m),
            relation_type=rel_type,
            strength=strength
        )
        for m, rel_type, strength in related
    ]

@router.get("/associations/stats")
async def get_association_stats(
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user.get("id") or current_user.get("user_id")
    
    stats = await memory_associator.get_association_stats(user_id)
    
    return stats

@router.post("/suggest")
async def suggest_related_memories(
    content: str = Query(..., description="当前内容"),
    limit: int = Query(default=5, ge=1, le=20),
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user.get("id") or current_user.get("user_id")
    
    suggestions = await memory_associator.suggest_related_memories(
        user_id=user_id,
        current_content=content,
        limit=limit
    )
    
    return [
        {
            "memory": memory_to_response(m),
            "score": score,
            "reason": reason
        }
        for m, score, reason in suggestions
    ]

@router.post("/consolidate")
async def trigger_consolidation(
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user.get("id") or current_user.get("user_id")
    
    result = await memory_manager.consolidate(user_id)
    
    return {
        "success": True,
        "result": {
            "memories_processed": result.memories_processed,
            "memories_merged": result.memories_merged,
            "memories_forgotten": result.memories_forgotten,
            "relations_created": result.relations_created,
        }
    }

@router.post("/preferences")
async def store_preference(
    preference: str = Query(..., description="偏好内容"),
    category: Optional[str] = Query(default=None, description="偏好类别"),
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user.get("id") or current_user.get("user_id")
    
    memory = memory_encoder.encode_preference(
        user_id=user_id,
        preference=preference,
        category=category
    )
    
    await hippocampus_storage.store(memory)
    
    return {
        "success": True,
        "memory_id": memory.id,
        "importance": memory.importance
    }

@router.get("/preferences")
async def get_preferences(
    limit: int = Query(default=10, ge=1, le=50),
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user.get("id") or current_user.get("user_id")
    
    preferences = await memory_retriever.get_user_preferences(user_id, limit)
    
    return preferences

@router.delete("/all")
async def clear_all_memories(
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user.get("id") or current_user.get("user_id")
    
    count = await hippocampus_storage.delete_user_memories(user_id)
    
    return {
        "success": True,
        "deleted_count": count
    }
