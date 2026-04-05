"""
人才市场API路由
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..auth import get_current_user
from ..governance import agent_market, salary_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/market", tags=["market"])


class RecruitRequest(BaseModel):
    """招募请求"""
    agent_id: str = Field(..., description="智能体模板ID")


class UpgradeRequest(BaseModel):
    """升级请求"""
    user_agent_id: str = Field(..., description="用户智能体ID")


class DismissRequest(BaseModel):
    """解雇请求"""
    user_agent_id: str = Field(..., description="用户智能体ID")
    refund_rate: Optional[float] = Field(default=0.3, description="返还比例")


@router.get("/agents")
async def get_available_agents(
    department: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    获取可招募智能体列表
    
    Args:
        department: 部门筛选（可选）
    """
    await agent_market.initialize()
    
    agents = await agent_market.get_available_agents(department)
    
    return {
        "success": True,
        "agents": [agent.to_dict() for agent in agents],
        "count": len(agents),
    }


@router.get("/agents/{agent_id}")
async def get_agent_detail(
    agent_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    获取智能体详情
    """
    await agent_market.initialize()
    
    agent = await agent_market.get_agent_template(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="智能体不存在")
    
    return {
        "success": True,
        "agent": agent.to_dict(),
    }


@router.post("/recruit")
async def recruit_agent(
    request: RecruitRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    招募智能体
    
    需扣除积分
    """
    user_id = current_user["id"]
    
    await agent_market.initialize()
    
    result = await agent_market.recruit_agent(user_id, request.agent_id)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return result


@router.get("/user/agents")
async def get_user_agents(
    current_user: dict = Depends(get_current_user)
):
    """
    获取用户已招募智能体列表
    """
    user_id = current_user["id"]
    
    await agent_market.initialize()
    
    agents = await agent_market.get_user_agents(user_id)
    
    return {
        "success": True,
        "agents": [agent.to_dict() for agent in agents],
        "count": len(agents),
    }


@router.post("/user/agents/upgrade")
async def upgrade_agent(
    request: UpgradeRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    升级智能体
    
    需消耗积分
    """
    user_id = current_user["id"]
    
    await agent_market.initialize()
    
    result = await agent_market.upgrade_agent(user_id, request.user_agent_id)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return result


@router.post("/user/agents/dismiss")
async def dismiss_agent(
    request: DismissRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    解雇智能体
    
    部分积分返还
    """
    user_id = current_user["id"]
    
    await agent_market.initialize()
    
    result = await agent_market.dismiss_agent(
        user_id, 
        request.user_agent_id, 
        request.refund_rate
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return result


@router.get("/user/finance")
async def get_user_finance(
    current_user: dict = Depends(get_current_user)
):
    """
    获取用户财务信息
    """
    user_id = current_user["id"]
    
    await salary_manager.initialize()
    
    summary = await salary_manager.get_finance_summary(user_id)
    stats = await salary_manager.get_agent_salary_stats(user_id)
    
    return {
        "success": True,
        "finance": summary.to_dict(),
        "agent_stats": stats,
    }


@router.get("/user/balance")
async def check_balance(
    required: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    查询积分余额
    """
    user_id = current_user["id"]
    
    await salary_manager.initialize()
    
    if required:
        result = await salary_manager.check_balance(user_id, required)
    else:
        summary = await salary_manager.get_finance_summary(user_id)
        result = {
            "sufficient": True,
            "balance": summary.total_integral,
            "required": 0,
        }
    
    return {
        "success": True,
        **result,
    }
