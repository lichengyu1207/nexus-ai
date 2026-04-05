"""
主入口文件
FastAPI应用
提供烦恼橡皮擦的核心功能
"""

from fastapi import FastAPI, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import json
import random
import uuid

from memory import init_db, save_memory, get_recent_memories
from personality import get_response, get_agent_info
from report import generate_report, save_report, get_report
from config import settings

# 初始化FastAPI应用
app = FastAPI(
    title=settings.app_name,
    description="情感陪伴应用，让烦恼随风而去",
    version=settings.app_version,
    debug=settings.debug,
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")


# 数据模型
class ChatRequest(BaseModel):
    message: str
    agent: str


class ChatResponse(BaseModel):
    reply: str
    report_id: str


# 初始化数据库
init_db()


@app.get("/")
async def root():
    """
    根路径
    返回前端页面
    """
    return FileResponse("static/index.html")


@app.get("/trilogy")
async def trilogy():
    """
    三部曲演示页面
    返回三部曲动画演示页面
    """
    return FileResponse("static/trilogy.html")


@app.get("/theater")
async def theater():
    """
    智能体工作剧场页面
    返回智能体工作剧场演示页面
    """
    return FileResponse("static/theater.html")


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, background_tasks: BackgroundTasks):
    """
    聊天接口
    
    Args:
        request: 聊天请求，包含用户消息和智能体
        background_tasks: 后台任务
    
    Returns:
        聊天响应，包含智能体回复和报告ID
    """
    # 获取历史记忆
    recent_memories = get_recent_memories(limit=3)
    
    # 生成智能体回复
    reply = get_response(request.agent, request.message, recent_memories)
    
    # 存储记忆
    save_memory(request.message, reply, request.agent)
    
    # 生成报告
    report = generate_report(request.message, recent_memories)
    report_id = save_report(report)
    
    return ChatResponse(
        reply=reply,
        report_id=report_id
    )


@app.get("/report/{report_id}")
async def get_report_endpoint(report_id: str):
    """
    获取报告接口
    
    Args:
        report_id: 报告ID
    
    Returns:
        报告JSON
    """
    report = get_report(report_id)
    if report:
        return report
    else:
        # 生成模拟报告
        mock_report = {
            "report_id": report_id,
            "title": "烦恼分析报告",
            "summary": "您最近提到了工作压力相关的烦恼",
            "emotion_trend": "从记录看，情绪波动较大，但整体向稳",
            "suggestions": [
                "尝试深呼吸5分钟，缓解工作压力",
                "与同事或上级沟通，寻求支持",
                "设定小目标，逐步完成工作任务"
            ],
            "chart_data": {
                "labels": ["Day1", "Day2", "Day3"],
                "values": [4, 5, 3]
            },
            "generated_at": "2026-03-21"
        }
        return mock_report


@app.get("/agents")
async def get_agents():
    """
    获取智能体列表
    
    Returns:
        智能体列表
    """
    agents = [
        get_agent_info("zhouyu"),
        get_agent_info("luxun")
    ]
    return agents


@app.get("/health")
async def health_check():
    """
    健康检查
    
    Returns:
        健康状态
    """
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload
    )
