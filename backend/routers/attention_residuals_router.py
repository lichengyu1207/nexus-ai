# -*- coding: utf-8 -*-
"""
Attention Residuals API Router
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

router = APIRouter(prefix="/api/memory", tags=["Attention Residuals"])


class MemoryStoreRequest(BaseModel):
    user_id: str
    content: str
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    importance: float = 0.5
    memory_type: str = "general"


class MemoryRetrieveRequest(BaseModel):
    user_id: str
    query_text: Optional[str] = None
    query_embedding: Optional[List[float]] = None
    limit: int = 100
    memory_type: Optional[str] = None
    min_importance: float = 0.0


class AttentionRetrieveRequest(BaseModel):
    user_id: str
    query_embedding: List[float]
    top_k: int = 100


class SessionCreateRequest(BaseModel):
    user_id: str
    session_type: str = "consultation"


class SessionEndRequest(BaseModel):
    summary: Optional[str] = None
    key_topics: Optional[List[str]] = None


async def get_memory_service_dep():
    from backend.services.attention_residuals.memory_service import (
        get_memory_service, init_memory_service
    )
    from backend.database_pg import PostgreSQLConnectionPool
    
    service = get_memory_service()
    if not service:
        pool = await PostgreSQLConnectionPool.get_instance()
        if pool._pool is None:
            await pool._initialize()
        service = await init_memory_service(pool._pool)
    return service


@router.post("/store")
async def store_memory(
    request: MemoryStoreRequest,
    service = Depends(get_memory_service_dep)
):
    memory = await service.store_memory(
        user_id=request.user_id,
        content=request.content,
        session_id=request.session_id,
        metadata=request.metadata,
        importance=request.importance,
        memory_type=request.memory_type
    )
    return {"success": True, "memory_id": memory.id, "memory": memory.to_dict()}


@router.post("/retrieve")
async def retrieve_memories(
    request: MemoryRetrieveRequest,
    service = Depends(get_memory_service_dep)
):
    memories = await service.retrieve_memories(
        user_id=request.user_id,
        query_embedding=request.query_embedding,
        limit=request.limit,
        memory_type=request.memory_type,
        min_importance=request.min_importance
    )
    return {
        "memories": [m.to_dict() for m in memories],
        "total": len(memories)
    }


@router.post("/attention")
async def attention_retrieve(
    request: AttentionRetrieveRequest,
    service = Depends(get_memory_service_dep)
):
    memories, attention_result = await service.attention_retrieve(
        user_id=request.user_id,
        query_embedding=request.query_embedding,
        top_k=request.top_k
    )
    return {
        "memories": [m.to_dict() for m in memories],
        "attention": attention_result,
        "total": len(memories)
    }


@router.get("/{memory_id}")
async def get_memory(
    memory_id: str,
    service = Depends(get_memory_service_dep)
):
    memory = await service.get_memory(memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    return memory.to_dict()


@router.put("/{memory_id}")
async def update_memory(
    memory_id: str,
    updates: Dict[str, Any],
    service = Depends(get_memory_service_dep)
):
    memory = await service.update_memory(memory_id, updates)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    return memory.to_dict()


@router.delete("/{memory_id}")
async def delete_memory(
    memory_id: str,
    service = Depends(get_memory_service_dep)
):
    success = await service.delete_memory(memory_id)
    if not success:
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"success": True, "message": "Memory deleted"}


@router.post("/session")
async def create_session(
    request: SessionCreateRequest,
    service = Depends(get_memory_service_dep)
):
    session = await service.create_session(
        user_id=request.user_id,
        session_type=request.session_type
    )
    return {"success": True, "session_id": session.id, "session": session.to_dict()}


@router.put("/session/{session_id}")
async def end_session(
    session_id: str,
    request: SessionEndRequest,
    service = Depends(get_memory_service_dep)
):
    await service.end_session(
        session_id=session_id,
        summary=request.summary,
        key_topics=request.key_topics
    )
    return {"success": True, "message": "Session ended"}


@router.get("/profile/{user_id}")
async def get_user_profile(
    user_id: str,
    service = Depends(get_memory_service_dep)
):
    profile = await service.get_user_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile.to_dict()


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "attention_residuals",
        "timestamp": datetime.utcnow().isoformat()
    }
