from fastapi import APIRouter
from app.api import tasks, tools, agents, datasets, audit, monitoring

router = APIRouter()

# 注册子路由
router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
router.include_router(tools.router, prefix="/tools", tags=["tools"])
router.include_router(agents.router, prefix="/agents", tags=["agents"])
router.include_router(datasets.router, prefix="/datasets", tags=["datasets"])
router.include_router(audit.router, prefix="/audit", tags=["audit"])
router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])
