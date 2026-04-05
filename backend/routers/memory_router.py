"""
海马体记忆系统API路由
Hippocampus Memory System Router

提供记忆存储、检索、管理、联想等接口
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import logging
import time

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/memory", tags=["memory"])


class MemoryCreateRequest(BaseModel):
    content: str
    memory_type: str = "fact"
    user_id: str = "anonymous"
    importance: float = 0.5
    entities: List[str] = []
    context: Dict[str, Any] = {}
    summary: str = ""


class MemorySearchRequest(BaseModel):
    query: str
    user_id: Optional[str] = None
    limit: int = 10


class MemoryAssociateRequest(BaseModel):
    memory_id: str
    limit: int = 5


@router.get("/stats")
async def get_memory_stats() -> Dict[str, Any]:
    """获取记忆系统统计信息"""
    from ..memory import memory_storage
    
    return memory_storage.get_stats()


@router.post("/store")
async def store_memory(request: MemoryCreateRequest) -> Dict[str, Any]:
    """存储新记忆"""
    from ..memory import memory_storage, MemoryType, MemoryUnit
    import uuid
    
    try:
        memory_type = MemoryType(request.memory_type)
    except ValueError:
        memory_type = MemoryType.FACT
    
    memory = MemoryUnit(
        id=str(uuid.uuid4()),
        type=memory_type,
        content=request.content,
        summary=request.summary or request.content[:100],
        importance=request.importance,
        user_id=request.user_id,
        entities=request.entities,
        context=request.context,
    )
    
    success = memory_storage.store_memory(memory)
    
    return {
        "success": success,
        "memory_id": memory.id,
    }


@router.get("/retrieve/{memory_id}")
async def retrieve_memory(memory_id: str) -> Dict[str, Any]:
    """检索单条记忆"""
    from ..memory import memory_storage
    
    memory = memory_storage.retrieve_memory(memory_id)
    
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    return memory.to_dict()


@router.get("/user/{user_id}")
async def retrieve_user_memories(
    user_id: str,
    limit: int = Query(50, ge=1, le=200)
) -> List[Dict[str, Any]]:
    """检索用户的所有记忆"""
    from ..memory import memory_storage
    
    memories = memory_storage.retrieve_by_user(user_id, limit)
    return [m.to_dict() for m in memories]


@router.post("/search")
async def search_memories(request: MemorySearchRequest) -> List[Dict[str, Any]]:
    """搜索记忆"""
    from ..memory import memory_retriever
    
    memories = memory_retriever.retrieve_semantic(
        query=request.query,
        user_id=request.user_id,
        limit=request.limit
    )
    
    return [m.to_dict() for m in memories]


@router.post("/search/keyword")
async def search_by_keyword(
    query: str,
    user_id: Optional[str] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """关键词搜索记忆"""
    from ..memory import memory_storage
    
    memories = memory_storage.short_term_memory.search(query, limit)
    memories.extend(memory_storage.long_term_memory.search(query, limit))
    
    if user_id:
        memories = [m for m in memories if m.user_id == user_id]
    
    return [m.to_dict() for m in memories[:limit]]


@router.post("/search/time")
async def search_by_time(
    start_time: float,
    end_time: float,
    user_id: Optional[str] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """按时间范围搜索记忆"""
    from ..memory import memory_storage
    
    memories = list(memory_storage.long_term_memory._memories.values())
    
    memories = [m for m in memories if start_time <= m.timestamp <= end_time]
    
    if user_id:
        memories = [m for m in memories if m.user_id == user_id]
    
    memories.sort(key=lambda x: x.timestamp, reverse=True)
    
    return [m.to_dict() for m in memories[:limit]]


@router.delete("/{memory_id}")
async def delete_memory(memory_id: str) -> Dict[str, Any]:
    """删除记忆"""
    from ..memory import memory_storage
    
    success = memory_storage.delete_memory(memory_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    return {"success": True, "memory_id": memory_id}


@router.post("/consolidate")
async def consolidate_memories() -> Dict[str, Any]:
    """执行记忆整理（合并、遗忘、晋升）"""
    from ..memory import memory_manager
    
    stats = memory_manager.consolidate()
    
    return {
        "success": True,
        "stats": stats
    }


@router.post("/importance")
async def update_importance(
    memory_id: str,
    delta: float
) -> Dict[str, Any]:
    """更新记忆重要性"""
    from ..memory import memory_manager
    
    success = memory_manager.update_importance(memory_id, delta)
    
    if not success:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    return {"success": True}


@router.post("/associate")
async def get_associations(request: MemoryAssociateRequest) -> List[Dict[str, Any]]:
    """获取相关记忆"""
    from ..memory import memory_associator
    
    related = memory_associator.get_related(request.memory_id, request.limit)
    
    return [
        {
            "memory": m.to_dict(),
            "strength": s,
            "relation_type": t
        }
        for m, s, t in related
    ]


@router.post("/associate/build")
async def build_associations(memory_id: str) -> Dict[str, Any]:
    """为记忆构建联想"""
    from ..memory import memory_associator, memory_storage
    
    memory = memory_storage.retrieve_memory(memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    count = memory_associator.build_associations(memory)
    
    return {
        "success": True,
        "associations_created": count
    }


@router.get("/graph")
async def get_memory_graph(
    user_id: Optional[str] = None,
    limit: int = Query(100, ge=10, le=500)
) -> Dict[str, Any]:
    """获取记忆网络图数据"""
    from ..memory import memory_associator
    
    graph = memory_associator.get_association_graph(user_id)
    
    return graph


@router.post("/batch-store")
async def batch_store_memories(memories: List[MemoryCreateRequest]) -> Dict[str, Any]:
    """批量存储记忆"""
    from ..memory import memory_storage, create_memory, MemoryType
    
    memory_units = []
    for req in memories:
        try:
            memory_type = MemoryType(req.memory_type)
        except ValueError:
            memory_type = MemoryType.FACT
        
        memory = create_memory(
            content=req.content,
            memory_type=memory_type,
            user_id=req.user_id,
            importance=req.importance,
            entities=req.entities,
            context=req.context,
            summary=req.summary,
        )
        memory_units.append(memory)
    
    stored_count = memory_storage.batch_store(memory_units)
    
    return {
        "success": True,
        "total": len(memories),
        "stored": stored_count,
        "memory_ids": [m.id for m in memory_units],
    }


@router.get("/types")
async def get_memory_types() -> List[Dict[str, str]]:
    """获取记忆类型列表"""
    from ..memory import MemoryType
    
    return [
        {"value": t.value, "name": t.name}
        for t in MemoryType
    ]


@router.get("/recent")
async def get_recent_memories(
    user_id: Optional[str] = None,
    hours: int = Query(24, ge=1, le=168),
    limit: int = Query(20, ge=1, le=100)
) -> List[Dict[str, Any]]:
    """获取最近的记忆"""
    from ..memory import memory_storage
    
    cutoff_time = time.time() - (hours * 3600)
    
    memories = list(memory_storage.long_term_memory._memories.values())
    memories.extend(memory_storage.short_term_memory._memories.values())
    
    memories = [m for m in memories if m.timestamp >= cutoff_time]
    
    if user_id:
        memories = [m for m in memories if m.user_id == user_id]
    
    memories.sort(key=lambda x: x.timestamp, reverse=True)
    
    return [m.to_dict() for m in memories[:limit]]
