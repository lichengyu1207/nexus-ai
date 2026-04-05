"""
智能体心跳查询 API
提供 HTTP 接口查询智能体心跳状态
"""
import json
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agents", tags=["agents"])


async def get_redis_client():
    """获取 Redis 客户端"""
    try:
        import redis.asyncio as redis
        from ..config.settings import settings
        
        client = await redis.from_url(settings.redis_url, decode_responses=True)
        return client
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="Redis async client not available"
        )


@router.get("/{agent_id}/heartbeat")
async def get_agent_heartbeat(agent_id: str) -> Dict[str, Any]:
    """
    查询智能体最新心跳
    
    Args:
        agent_id: 智能体 ID
        
    Returns:
        心跳数据
        
    Raises:
        HTTPException: 智能体心跳不存在时返回 404
    """
    client = await get_redis_client()
    try:
        key = f"agent:{agent_id}:heartbeat"
        data = await client.get(key)
        
        if data is None:
            raise HTTPException(
                status_code=404,
                detail=f"Agent heartbeat not found: {agent_id}"
            )
        
        return json.loads(data)
    finally:
        await client.close()


@router.get("/")
async def list_agents(
    prefix: Optional[str] = Query(None, description="智能体 ID 前缀筛选"),
) -> List[Dict[str, Any]]:
    """
    列出所有活跃的智能体
    
    Args:
        prefix: 智能体 ID 前缀筛选
        
    Returns:
        智能体列表及其心跳数据
    """
    client = await get_redis_client()
    try:
        pattern = "agent:*:heartbeat"
        keys = []
        
        async for key in client.scan_iter(match=pattern):
            keys.append(key)
        
        agents = []
        for key in keys:
            data = await client.get(key)
            if data:
                heartbeat = json.loads(data)
                agent_id = heartbeat.get("agent_id", "")
                
                if prefix and not agent_id.startswith(prefix):
                    continue
                
                agents.append({
                    "agent_id": agent_id,
                    "status": "active",
                    "heartbeat": heartbeat,
                })
        
        return agents
    finally:
        await client.close()


@router.get("/{agent_id}/status")
async def get_agent_status(agent_id: str) -> Dict[str, Any]:
    """
    获取智能体状态
    
    Args:
        agent_id: 智能体 ID
        
    Returns:
        状态信息
    """
    client = await get_redis_client()
    try:
        key = f"agent:{agent_id}:heartbeat"
        data = await client.get(key)
        
        if data is None:
            return {
                "agent_id": agent_id,
                "status": "offline",
                "message": "No heartbeat received",
            }
        
        heartbeat = json.loads(data)
        
        return {
            "agent_id": agent_id,
            "status": "active",
            "heartbeat": heartbeat,
        }
    finally:
        await client.close()


@router.delete("/{agent_id}/heartbeat")
async def clear_agent_heartbeat(agent_id: str) -> Dict[str, str]:
    """
    清除智能体心跳（用于测试或强制下线）
    
    Args:
        agent_id: 智能体 ID
        
    Returns:
        操作结果
    """
    client = await get_redis_client()
    try:
        key = f"agent:{agent_id}:heartbeat"
        deleted = await client.delete(key)
        
        if deleted:
            return {"message": f"Heartbeat cleared for agent {agent_id}"}
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Agent heartbeat not found: {agent_id}"
            )
    finally:
        await client.close()


@router.get("/health/check")
async def health_check() -> Dict[str, Any]:
    """
    健康检查接口
    
    Returns:
        服务状态
    """
    client = await get_redis_client()
    try:
        await client.ping()
        
        pattern = "agent:*:heartbeat"
        count = 0
        async for _ in client.scan_iter(match=pattern):
            count += 1
        
        return {
            "status": "healthy",
            "redis": "connected",
            "active_agents": count,
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "redis": "disconnected",
            "error": str(e),
            "active_agents": 0,
        }
    finally:
        await client.close()
