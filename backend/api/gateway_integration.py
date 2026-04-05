"""
API网关集成模块
将基于分组模型路由的成本优化系统部署到房都督平台的API网关层
"""

import os
import json
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional

from backend.agents.model_router import process_request, get_router_status
from backend.agents.cost_monitor import get_daily_cost, is_degraded, is_warning
from backend.config.system_config import get as get_config

logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="房都督模型路由API",
    description="基于分组模型路由的成本优化系统",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 定义请求模型
class QueryRequest(BaseModel):
    query: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None

# 定义响应模型
class QueryResponse(BaseModel):
    success: bool
    query: str
    task_features: Optional[Dict[str, Any]] = None
    model: Optional[str] = None
    response: Optional[str] = None
    decision_reason: Optional[str] = None
    confidence: Optional[float] = None
    time_taken: Optional[float] = None
    total_delay: Optional[float] = None
    cost: Optional[float] = None
    current_daily_cost: Optional[float] = None
    error: Optional[str] = None

class StatusResponse(BaseModel):
    daily_cost: float
    is_degraded: bool
    is_warning: bool
    models: list

@app.post("/api/query", response_model=QueryResponse)
async def handle_query(request: QueryRequest):
    """处理用户查询"""
    try:
        logger.info(f"接收查询: {request.query}")
        result = process_request(request.query)
        return QueryResponse(**result)
    except Exception as e:
        logger.error(f"处理查询失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status", response_model=StatusResponse)
async def get_status():
    """获取系统状态"""
    try:
        status = get_router_status()
        return StatusResponse(
            daily_cost=status["daily_cost"],
            is_degraded=status["is_degraded"],
            is_warning=is_warning(),
            models=status["models"]
        )
    except Exception as e:
        logger.error(f"获取状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    host = get_config("api.host", "0.0.0.0")
    port = get_config("api.port", 8000)
    uvicorn.run(app, host=host, port=port)
