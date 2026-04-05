from fastapi import APIRouter
from .endpoints import tasks, websocket, auth, messages, debate, teams, training, test_workflow

api_router = APIRouter()

# 包含认证相关路由
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

# 包含任务相关路由
api_router.include_router(tasks.router, tags=["tasks"])

# 包含WebSocket相关路由
api_router.include_router(websocket.router, tags=["websocket"])

# 包含消息相关路由
api_router.include_router(messages.router, tags=["messages"])

# 包含辩论相关路由
api_router.include_router(debate.router, tags=["debate"])

# 包含团队相关路由
api_router.include_router(teams.router, tags=["teams"])

# 包含实训相关路由
api_router.include_router(training.router, tags=["training"])

# 包含测试工作流路由
api_router.include_router(test_workflow.router, prefix="/test", tags=["test"])
