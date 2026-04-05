"""
三省六部智能体API路由
Six Ministry Agents Router

提供礼部、工部、户部、兵部、吏部、刑部智能体的API接口
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any
import logging
import time
import re

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ministry", tags=["ministry"])


class ChatRequest(BaseModel):
    input: str = Field(..., min_length=1, max_length=5000, description="用户输入内容")
    session_id: Optional[str] = Field(None, description="会话ID")
    user_id: str = Field(default="anonymous", max_length=100, description="用户ID")
    user_type: str = Field(default="normal", description="用户类型")
    
    @validator('user_type')
    def validate_user_type(cls, v):
        valid_types = ['newbie', 'normal', 'expert', 'investor']
        if v not in valid_types:
            logger.warning(f"Invalid user_type '{v}', using default 'normal'")
            return 'normal'
        return v
    
    @validator('input')
    def sanitize_input(cls, v):
        if not v or not v.strip():
            raise ValueError('输入内容不能为空')
        return v.strip()


class TaskRequest(BaseModel):
    action: str = Field(..., min_length=1, description="操作类型")
    task_type: Optional[str] = Field(None, description="任务类型")
    data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="任务数据")
    user_id: Optional[str] = Field(None, description="用户ID")
    
    @validator('action')
    def validate_action(cls, v):
        if not v or not v.strip():
            raise ValueError('操作类型不能为空')
        return v.strip()


@router.get("/overview")
async def get_ministry_overview() -> Dict[str, Any]:
    """获取三省六部智能体概览"""
    from ..agents.ministry import get_ministry_agents
    
    agents = get_ministry_agents()
    
    overview = {}
    for name, agent in agents.items():
        status = agent.get_status()
        overview[name] = {
            "name": status["name"],
            "species": status["species"],
            "state": status["state"],
            "energy": status["energy"],
            "tasks_completed": status["stats"]["tasks_completed"],
            "tasks_failed": status["stats"]["tasks_failed"],
        }
    
    return {
        "timestamp": time.time(),
        "ministries": overview
    }


@router.post("/li/chat")
async def li_chat(request: ChatRequest) -> Dict[str, Any]:
    """礼部智能体 - 智能咨询对话"""
    from ..agents.ministry import get_ministry_agents
    
    agents = get_ministry_agents()
    li_agent = agents.get("li")
    
    if not li_agent:
        raise HTTPException(status_code=503, detail="礼部智能体不可用")
    
    task = {
        "action": "chat",
        "input": request.input,
        "session_id": request.session_id,
        "user_id": request.user_id,
        "user_type": request.user_type,
    }
    
    result = await li_agent.handle_task(task)
    return result


@router.post("/li/recognize")
async def li_recognize_intent(text: str) -> Dict[str, Any]:
    """礼部智能体 - 意图识别"""
    from ..agents.ministry import get_ministry_agents
    
    agents = get_ministry_agents()
    li_agent = agents.get("li")
    
    if not li_agent:
        raise HTTPException(status_code=503, detail="礼部智能体不可用")
    
    task = {
        "action": "recognize_intent",
        "text": text,
    }
    
    result = await li_agent.handle_task(task)
    return result


@router.post("/li/recommend")
async def li_get_recommendation(
    session_id: str,
    last_intent: Optional[str] = None,
    silence_seconds: float = 0
) -> Dict[str, Any]:
    """礼部智能体 - 获取主动推荐"""
    from ..agents.ministry import get_ministry_agents
    
    agents = get_ministry_agents()
    li_agent = agents.get("li")
    
    if not li_agent:
        raise HTTPException(status_code=503, detail="礼部智能体不可用")
    
    task = {
        "action": "get_recommendation",
        "session_id": session_id,
        "last_intent": last_intent,
        "silence_seconds": silence_seconds,
    }
    
    result = await li_agent.handle_task(task)
    return result


@router.post("/gong/parse")
async def gong_parse_task(request: TaskRequest) -> Dict[str, Any]:
    """工部智能体 - 任务解析"""
    from ..agents.ministry import get_ministry_agents
    
    agents = get_ministry_agents()
    gong_agent = agents.get("gong")
    
    if not gong_agent:
        raise HTTPException(status_code=503, detail="工部智能体不可用")
    
    task = {
        "action": "parse_task",
        "input": request.data.get("input", "") if request.data else "",
        **request.data
    }
    
    result = await gong_agent.handle_task(task)
    return result


@router.post("/gong/report")
async def gong_generate_report(request: TaskRequest) -> Dict[str, Any]:
    """工部智能体 - 生成报告"""
    from ..agents.ministry import get_ministry_agents
    
    agents = get_ministry_agents()
    gong_agent = agents.get("gong")
    
    if not gong_agent:
        raise HTTPException(status_code=503, detail="工部智能体不可用")
    
    task = {
        "action": "generate_report",
        "report_type": request.data.get("report_type", "standard") if request.data else "standard",
        "data": request.data.get("data", {}) if request.data else {},
        "user_profile": request.data.get("user_profile", {}) if request.data else {},
    }
    
    result = await gong_agent.handle_task(task)
    return result


@router.post("/gong/evaluate")
async def gong_evaluate_quality(request: TaskRequest) -> Dict[str, Any]:
    """工部智能体 - 质量评估"""
    from ..agents.ministry import get_ministry_agents
    
    agents = get_ministry_agents()
    gong_agent = agents.get("gong")
    
    if not gong_agent:
        raise HTTPException(status_code=503, detail="工部智能体不可用")
    
    task = {
        "action": "evaluate_quality",
        "report": request.data.get("report", {}) if request.data else {},
    }
    
    result = await gong_agent.handle_task(task)
    return result


@router.post("/hu/points")
async def hu_calculate_points(
    task_type: str,
    queue_length: int = 0
) -> Dict[str, Any]:
    """户部智能体 - 计算积分"""
    from ..agents.ministry import get_ministry_agents
    
    agents = get_ministry_agents()
    hu_agent = agents.get("hu")
    
    if not hu_agent:
        raise HTTPException(status_code=503, detail="户部智能体不可用")
    
    task = {
        "action": "calculate_points",
        "task_type": task_type,
        "queue_length": queue_length,
    }
    
    result = await hu_agent.handle_task(task)
    return result


@router.post("/hu/activity")
async def hu_plan_activity(user_segment: str = "normal") -> Dict[str, Any]:
    """户部智能体 - 策划活动"""
    from ..agents.ministry import get_ministry_agents
    
    agents = get_ministry_agents()
    hu_agent = agents.get("hu")
    
    if not hu_agent:
        raise HTTPException(status_code=503, detail="户部智能体不可用")
    
    task = {
        "action": "plan_activity",
        "user_segment": user_segment,
    }
    
    result = await hu_agent.handle_task(task)
    return result


@router.post("/hu/level")
async def hu_adjust_level(
    user_id: str,
    points: int = 0,
    activity: int = 0
) -> Dict[str, Any]:
    """户部智能体 - 调整会员等级"""
    from ..agents.ministry import get_ministry_agents
    
    agents = get_ministry_agents()
    hu_agent = agents.get("hu")
    
    if not hu_agent:
        raise HTTPException(status_code=503, detail="户部智能体不可用")
    
    task = {
        "action": "adjust_level",
        "user_id": user_id,
        "points": points,
        "activity": activity,
    }
    
    result = await hu_agent.handle_task(task)
    return result


@router.post("/bing/source")
async def bing_select_source(
    data_type: str = "price",
    urgency: str = "normal"
) -> Dict[str, Any]:
    """兵部智能体 - 选择数据源"""
    from ..agents.ministry import get_ministry_agents
    
    agents = get_ministry_agents()
    bing_agent = agents.get("bing")
    
    if not bing_agent:
        raise HTTPException(status_code=503, detail="兵部智能体不可用")
    
    task = {
        "action": "select_source",
        "data_type": data_type,
        "urgency": urgency,
    }
    
    result = await bing_agent.handle_task(task)
    return result


@router.post("/bing/frequency")
async def bing_adjust_frequency(
    change_rate: float = 0,
    demand_level: str = "normal"
) -> Dict[str, Any]:
    """兵部智能体 - 调整采集频率"""
    from ..agents.ministry import get_ministry_agents
    
    agents = get_ministry_agents()
    bing_agent = agents.get("bing")
    
    if not bing_agent:
        raise HTTPException(status_code=503, detail="兵部智能体不可用")
    
    task = {
        "action": "adjust_frequency",
        "change_rate": change_rate,
        "demand_level": demand_level,
    }
    
    result = await bing_agent.handle_task(task)
    return result


@router.post("/bing/anomaly")
async def bing_detect_anomaly(data: List[float]) -> Dict[str, Any]:
    """兵部智能体 - 异常检测"""
    from ..agents.ministry import get_ministry_agents
    
    agents = get_ministry_agents()
    bing_agent = agents.get("bing")
    
    if not bing_agent:
        raise HTTPException(status_code=503, detail="兵部智能体不可用")
    
    task = {
        "action": "detect_anomaly",
        "data": data,
    }
    
    result = await bing_agent.handle_task(task)
    return result


@router.get("/li2/health")
async def li2_health_check() -> Dict[str, Any]:
    """吏部智能体 - 健康检查"""
    from ..agents.ministry import get_ministry_agents
    
    agents = get_ministry_agents()
    li2_agent = agents.get("li2")
    
    if not li2_agent:
        raise HTTPException(status_code=503, detail="吏部智能体不可用")
    
    task = {"action": "health_check"}
    result = await li2_agent.handle_task(task)
    return result


@router.post("/li2/scale")
async def li2_scale_resources(
    queue_length: int = 0,
    current_load: float = 0.5
) -> Dict[str, Any]:
    """吏部智能体 - 资源调度"""
    from ..agents.ministry import get_ministry_agents
    
    agents = get_ministry_agents()
    li2_agent = agents.get("li2")
    
    if not li2_agent:
        raise HTTPException(status_code=503, detail="吏部智能体不可用")
    
    task = {
        "action": "scale_resources",
        "queue_length": queue_length,
        "current_load": current_load,
    }
    
    result = await li2_agent.handle_task(task)
    return result


@router.get("/li2/reproduction")
async def li2_manage_reproduction() -> Dict[str, Any]:
    """吏部智能体 - 繁殖管理"""
    from ..agents.ministry import get_ministry_agents
    
    agents = get_ministry_agents()
    li2_agent = agents.get("li2")
    
    if not li2_agent:
        raise HTTPException(status_code=503, detail="吏部智能体不可用")
    
    task = {"action": "manage_reproduction"}
    result = await li2_agent.handle_task(task)
    return result


@router.post("/xing/risk")
async def xing_risk_check(request: TaskRequest) -> Dict[str, Any]:
    """刑部智能体 - 风险检查"""
    from ..agents.ministry import get_ministry_agents
    
    agents = get_ministry_agents()
    xing_agent = agents.get("xing")
    
    if not xing_agent:
        raise HTTPException(status_code=503, detail="刑部智能体不可用")
    
    task = {
        "action": "risk_check",
        "user_id": request.user_id,
        "action_type": request.data.get("action_type") if request.data else None,
        "context": request.data.get("context", {}) if request.data else {},
    }
    
    result = await xing_agent.handle_task(task)
    return result


@router.post("/xing/profile")
async def xing_build_profile(
    user_id: str,
    behaviors: List[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """刑部智能体 - 构建用户画像"""
    from ..agents.ministry import get_ministry_agents
    
    agents = get_ministry_agents()
    xing_agent = agents.get("xing")
    
    if not xing_agent:
        raise HTTPException(status_code=503, detail="刑部智能体不可用")
    
    task = {
        "action": "build_profile",
        "user_id": user_id,
        "behaviors": behaviors or [],
    }
    
    result = await xing_agent.handle_task(task)
    return result


@router.post("/xing/audit")
async def xing_audit_action(request: TaskRequest) -> Dict[str, Any]:
    """刑部智能体 - 审计操作"""
    from ..agents.ministry import get_ministry_agents
    
    agents = get_ministry_agents()
    xing_agent = agents.get("xing")
    
    if not xing_agent:
        raise HTTPException(status_code=503, detail="刑部智能体不可用")
    
    task = {
        "action": "audit",
        "action_type": request.data.get("action_type") if request.data else None,
        "user_id": request.user_id,
        "details": request.data.get("details", {}) if request.data else {},
    }
    
    result = await xing_agent.handle_task(task)
    return result


@router.get("/agents/{ministry}")
async def get_ministry_agent_status(ministry: str) -> Dict[str, Any]:
    """获取指定部门智能体状态"""
    from ..agents.ministry import get_ministry_agents
    
    agents = get_ministry_agents()
    
    if ministry not in agents:
        raise HTTPException(status_code=404, detail=f"未找到部门: {ministry}")
    
    agent = agents[ministry]
    return agent.get_status()


@router.post("/agents/{ministry}/energy")
async def adjust_ministry_agent_energy(
    ministry: str,
    amount: float,
    reason: str = "api_adjustment"
) -> Dict[str, Any]:
    """调整指定部门智能体能量"""
    from ..agents.ministry import get_ministry_agents
    
    agents = get_ministry_agents()
    
    if ministry not in agents:
        raise HTTPException(status_code=404, detail=f"未找到部门: {ministry}")
    
    agent = agents[ministry]
    
    if amount >= 0:
        agent.gain_energy(amount, reason)
    else:
        agent.consume_energy(abs(amount), reason)
    
    return {"success": True, "energy": agent.energy_system.get_level()}
