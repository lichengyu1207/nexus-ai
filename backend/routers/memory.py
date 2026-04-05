"""
智能体记忆系统 - 记忆管理API
提供记忆的CRUD接口
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from ..auth import get_current_user
from ..memory.service import memory_service

router = APIRouter(prefix="/memory", tags=["memory"])

class MemoryCreate(BaseModel):
    agent_name: str
    input_text: str
    output_text: str
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class MemorySearch(BaseModel):
    query: str
    limit: int = 5
    category: Optional[str] = None

class ProfileUpdate(BaseModel):
    profile: Optional[Dict[str, Any]] = None
    preferences: Optional[Dict[str, Any]] = None

@router.get("")
async def get_memories(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    category: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["id"]
    
    from ..memory.storage import storage
    memories = await storage.get_user_memories(user_id, limit, offset, category)
    
    total = await storage.count_user_memories(user_id)
    
    return {
        "memories": memories,
        "total": total,
        "limit": limit,
        "offset": offset,
    }

@router.get("/search")
async def search_memories(
    query: str,
    limit: int = Query(5, ge=1, le=20),
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["id"]
    
    memories = await memory_service.retrieve(user_id, query, limit)
    
    return {
        "query": query,
        "results": memories,
        "count": len(memories),
    }

@router.get("/profile")
async def get_profile(
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["id"]
    
    profile = await memory_service.get_user_profile(user_id)
    
    return profile

@router.put("/profile")
async def update_profile(
    data: ProfileUpdate,
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["id"]
    
    await memory_service.update_user_profile(user_id, {
        "profile": data.profile or {},
        "preferences": data.preferences or {},
    })
    
    return {"message": "用户画像更新成功"}

@router.get("/stats")
async def get_stats(
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["id"]
    
    stats = await memory_service.get_memory_stats(user_id)
    
    return stats

@router.get("/context")
async def get_context(
    query: Optional[str] = None,
    max_memories: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["id"]
    
    context = await memory_service.get_context(user_id, query, max_memories)
    
    return {
        "context": context,
        "query": query,
    }

@router.get("/graph")
async def get_memory_graph(
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["id"]
    
    from ..memory.storage import storage
    memories = await storage.get_user_memories(user_id, limit=100)
    
    nodes = []
    edges = []
    
    node_map = {}
    
    for memory in memories:
        node_id = memory["id"]
        
        node = {
            "id": node_id,
            "label": memory.get("summary", "")[:30],
            "category": memory.get("category", "fact"),
            "importance": memory.get("importance", 5.0),
            "created_at": memory.get("created_at"),
        }
        nodes.append(node)
        node_map[node_id] = node
        
        agent_name = memory.get("agent_name")
        if agent_name:
            agent_node_id = f"agent_{agent_name}"
            if agent_node_id not in node_map:
                agent_node = {
                    "id": agent_node_id,
                    "label": agent_name,
                    "category": "agent",
                    "importance": 10.0,
                }
                nodes.append(agent_node)
                node_map[agent_node_id] = agent_node
            
            edges.append({
                "source": node_id,
                "target": agent_node_id,
                "type": "created_by",
            })
    
    return {
        "nodes": nodes,
        "edges": edges,
    }

@router.post("")
async def create_memory(
    data: MemoryCreate,
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["id"]
    
    memory_id = await memory_service.store(
        user_id=user_id,
        agent_name=data.agent_name,
        input_text=data.input_text,
        output_text=data.output_text,
        session_id=data.session_id,
        metadata=data.metadata,
    )
    
    return {
        "memory_id": memory_id,
        "message": "记忆存储成功",
    }

@router.get("/{memory_id}")
async def get_memory(
    memory_id: str,
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["id"]
    
    from ..memory.storage import storage
    memory = await storage.get_memory(memory_id)
    
    if not memory:
        raise HTTPException(status_code=404, detail="记忆不存在")
    
    if memory.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="无权访问此记忆")
    
    await storage.update_access(memory_id)
    
    return memory

@router.delete("/{memory_id}")
async def delete_memory(
    memory_id: str,
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["id"]
    
    success = await memory_service.delete(user_id, memory_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="记忆不存在或无权删除")
    
    return {"message": "记忆删除成功"}

@router.delete("")
async def clear_memories(
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["id"]
    
    count = await memory_service.clear_user(user_id)
    
    return {
        "message": f"已清空 {count} 条记忆",
        "deleted_count": count,
    }

@router.post("/consolidate")
async def consolidate_memories(
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["id"]
    
    from ..memory.consolidation import consolidator
    result = await consolidator.consolidate_user_memories(user_id)
    
    return {
        "message": "记忆整理完成",
        "result": result,
    }

@router.post("/consolidate/session/{session_id}")
async def compress_session(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["id"]
    
    from ..memory.consolidation import consolidator
    compressed_id = await consolidator.compress_session_memories(user_id, session_id)
    
    if compressed_id:
        return {
            "message": "会话记忆压缩成功",
            "compressed_memory_id": compressed_id,
        }
    else:
        return {
            "message": "会话记忆数量不足，无需压缩",
            "compressed_memory_id": None,
        }

@router.get("/consolidate/stats")
async def get_consolidation_stats(
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["id"]
    
    from ..memory.consolidation import consolidator
    stats = await consolidator.get_consolidation_stats(user_id)
    
    return stats

@router.get("/admin/metrics")
async def get_system_metrics(
    current_user: dict = Depends(get_current_user)
):
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    from ..memory.storage import storage
    from ..memory.vector_store import vector_store
    import aiosqlite
    from pathlib import Path
    from datetime import datetime, timedelta
    
    db_path = Path(__file__).parent.parent.parent / "data" / "property-ai.db"
    
    async with aiosqlite.connect(str(db_path)) as conn:
        conn.row_factory = aiosqlite.Row
        
        cursor = await conn.execute("SELECT COUNT(*) FROM memory_entries")
        total_memories = (await cursor.fetchone())[0]
        
        cursor = await conn.execute("SELECT COUNT(DISTINCT user_id) FROM memory_entries")
        total_users = (await cursor.fetchone())[0]
        
        cursor = await conn.execute("""
            SELECT COUNT(*) FROM memory_entries
            WHERE created_at > datetime('now', '-1 day')
        """)
        daily_new = (await cursor.fetchone())[0]
        
        cursor = await conn.execute("""
            SELECT COUNT(*) FROM memory_entries
            WHERE created_at > datetime('now', '-7 days')
        """)
        weekly_new = (await cursor.fetchone())[0]
        
        cursor = await conn.execute("""
            SELECT category, COUNT(*) as count 
            FROM memory_entries 
            GROUP BY category
        """)
        category_distribution = dict(await cursor.fetchall())
        
        cursor = await conn.execute("""
            SELECT AVG(importance) FROM memory_entries
        """)
        avg_importance = (await cursor.fetchone())[0] or 0
        
        cursor = await conn.execute("""
            SELECT COUNT(*) FROM memory_entries
            WHERE last_accessed > datetime('now', '-7 days')
        """)
        active_memories = (await cursor.fetchone())[0]
    
    vector_stats = vector_store.get_stats()
    
    return {
        "total_memories": total_memories,
        "total_users_with_memories": total_users,
        "daily_new_memories": daily_new,
        "weekly_new_memories": weekly_new,
        "category_distribution": category_distribution,
        "average_importance": round(avg_importance, 2),
        "active_memories_7d": active_memories,
        "vector_store": vector_stats,
        "collected_at": datetime.utcnow().isoformat(),
    }
