"""
心跳上报 API 主入口
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .agents import router as agents_router
from ..config.settings import settings

logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("Heartbeat API starting up...")
    logger.info(f"Redis URL: {settings.redis_url}")
    logger.info(f"Heartbeat interval: {settings.heartbeat_interval}s")
    logger.info(f"Heartbeat TTL: {settings.heartbeat_ttl}s")
    
    yield
    
    logger.info("Heartbeat API shutting down...")


app = FastAPI(
    title="智能体心跳上报 API",
    description="房都督平台智能体集群健康管理服务",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agents_router)


@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "智能体心跳上报服务",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "heartbeat.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
