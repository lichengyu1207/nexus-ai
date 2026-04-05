"""
健康检查路由
"""
from fastapi import APIRouter
from datetime import datetime

router = APIRouter()

@router.get("/api/health")
async def health_check():
    """健康检查端点"""
    return {"status": "ok", "service": "healthy", "timestamp": datetime.utcnow().isoformat()}
