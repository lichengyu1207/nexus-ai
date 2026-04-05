"""
多元化智能体招募API路由
包含招募、图鉴、羁绊等功能
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..auth import get_current_user
from ..governance.recruit import recruit_system, RecruitResult, RecruitStats

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/recruit", tags=["recruit"])


class RecruitRequest(BaseModel):
    """招募请求"""
    recruit_type: str = Field(default="basic", description="招募类型: basic/premium")


class AgentUpgradeRequest(BaseModel):
    """智能体升级请求"""
    user_agent_id: str = Field(..., description="用户智能体ID")


class AssignDepartmentRequest(BaseModel):
    """分配部门请求"""
    user_agent_id: str = Field(..., description="用户智能体ID")
    department: str = Field(..., description="目标部门")


class LearnSkillRequest(BaseModel):
    """学习技能请求"""
    user_agent_id: str = Field(..., description="用户智能体ID")
    skill_slot: int = Field(..., ge=1, le=3, description="技能槽位(1-3)")


@router.get("/probability")
async def get_probability_info(
    recruit_type: str = "basic"
):
    """
    获取招募概率信息
    
    Args:
        recruit_type: 招募类型 (basic/premium)
    """
    await recruit_system.initialize()
    info = await recruit_system.get_probability_info(recruit_type)
    return {"success": True, **info}


@router.post("/basic")
async def basic_recruit(
    current_user: dict = Depends(get_current_user)
):
    """
    基础招募（100积分）
    
    概率: N 60%, R 30%, SR 8%, SSR 1.5%, UR 0.5%
    保底: 10次SR保底, 50次SSR保底
    """
    user_id = current_user["id"]
    
    await recruit_system.initialize()
    result: RecruitResult = await recruit_system.recruit(user_id, "basic")
    
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    
    return result.to_dict()


@router.post("/premium")
async def premium_recruit(
    current_user: dict = Depends(get_current_user)
):
    """
    高级招募（1000积分）
    
    概率: N 30%, R 40%, SR 20%, SSR 8%, UR 2%
    保底: 10次SR保底, 50次SSR保底
    """
    user_id = current_user["id"]
    
    await recruit_system.initialize()
    result: RecruitResult = await recruit_system.recruit(user_id, "premium")
    
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    
    return result.to_dict()


@router.get("/stats")
async def get_recruit_stats(
    current_user: dict = Depends(get_current_user)
):
    """
    获取用户招募统计
    
    包含:
    - 总招募次数
    - SR保底进度
    - SSR保底进度
    """
    user_id = current_user["id"]
    
    await recruit_system.initialize()
    stats: RecruitStats = await recruit_system.get_recruit_stats(user_id)
    
    return {"success": True, "stats": stats.to_dict()}


@router.get("/templates")
async def get_all_templates():
    """
    获取所有智能体模板（图鉴）
    
    返回所有可招募的智能体模板信息
    """
    await recruit_system.initialize()
    templates = await recruit_system.get_all_templates()
    
    return {
        "success": True,
        "templates": templates,
        "count": len(templates),
    }


@router.get("/agents")
async def get_user_agents(
    current_user: dict = Depends(get_current_user)
):
    """
    获取用户所有智能体
    """
    user_id = current_user["id"]
    
    await recruit_system.initialize()
    agents = await recruit_system.get_user_agents(user_id)
    
    return {
        "success": True,
        "agents": agents,
        "count": len(agents),
    }


@router.get("/bonds")
async def get_user_bonds(
    current_user: dict = Depends(get_current_user)
):
    """
    获取用户已激活的羁绊
    """
    user_id = current_user["id"]
    
    await recruit_system.initialize()
    bonds = await recruit_system.get_user_bonds(user_id)
    
    return {
        "success": True,
        "bonds": bonds,
        "count": len(bonds),
    }


@router.post("/agents/upgrade")
async def upgrade_agent(
    request: AgentUpgradeRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    升级智能体
    
    消耗积分提升等级
    """
    user_id = current_user["id"]
    
    await recruit_system.initialize()
    result = await recruit_system.upgrade_agent(user_id, request.user_agent_id)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.post("/agents/assign")
async def assign_department(
    request: AssignDepartmentRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    分配智能体到部门
    """
    user_id = current_user["id"]
    
    from ..database_pg import get_db
    
    async with get_db() as db:
        agent = await db.fetchone(
            "SELECT id FROM user_agents WHERE id = $1 AND user_id = $2",
            request.user_agent_id, user_id
        )
        
        if not agent:
            raise HTTPException(status_code=404, detail="智能体不存在")
        
        await db.execute(
            "UPDATE user_agents SET assigned_department = $1 WHERE id = $2",
            request.department, request.user_agent_id
        )
        
        return {
            "success": True,
            "department": request.department,
            "message": f"智能体已分配到 {request.department}",
        }


@router.get("/rarity-info")
async def get_rarity_info():
    """
    获取稀有度信息
    
    包含各稀有度的颜色、等级上限等
    """
    return {
        "success": True,
        "rarities": {
            "N": {
                "name": "普通",
                "color": "#9e9e9e",
                "level_cap": 30,
                "probability_basic": 0.60,
                "probability_premium": 0.30,
            },
            "R": {
                "name": "稀有",
                "color": "#3498db",
                "level_cap": 50,
                "probability_basic": 0.30,
                "probability_premium": 0.40,
            },
            "SR": {
                "name": "史诗",
                "color": "#9b59b6",
                "level_cap": 70,
                "probability_basic": 0.08,
                "probability_premium": 0.20,
            },
            "SSR": {
                "name": "传说",
                "color": "#f39c12",
                "level_cap": 90,
                "probability_basic": 0.015,
                "probability_premium": 0.08,
            },
            "UR": {
                "name": "神话",
                "color": "#e74c3c",
                "level_cap": 100,
                "probability_basic": 0.005,
                "probability_premium": 0.02,
            },
        },
        "guarantee": {
            "sr_guarantee": 10,
            "ssr_guarantee": 50,
        },
    }


@router.get("/agents/{user_agent_id}")
async def get_agent_detail(
    user_agent_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    获取单个智能体详情
    
    包含等级、技能、突破信息等
    """
    user_id = current_user["id"]
    
    await recruit_system.initialize()
    detail = await recruit_system.get_agent_detail(user_id, user_agent_id)
    
    if not detail:
        raise HTTPException(status_code=404, detail="智能体不存在")
    
    return {"success": True, "agent": detail}


@router.post("/agents/learn-skill")
async def learn_skill(
    request: LearnSkillRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    学习/升级技能
    
    消耗积分提升技能等级
    - 技能1: 1级解锁
    - 技能2: 20级解锁
    - 技能3: 50级解锁
    """
    user_id = current_user["id"]
    
    await recruit_system.initialize()
    result = await recruit_system.learn_skill(user_id, request.user_agent_id, request.skill_slot)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.post("/agents/breakthrough")
async def breakthrough_agent(
    request: AgentUpgradeRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    突破稀有度
    
    满级后可突破，提升稀有度和等级上限
    - N→R: 5000积分
    - R→SR: 10000积分
    - SR→SSR: 30000积分
    - SSR→UR: 100000积分
    """
    user_id = current_user["id"]
    
    await recruit_system.initialize()
    result = await recruit_system.breakthrough(user_id, request.user_agent_id)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.get("/all-bonds")
async def get_all_bonds(
    current_user: dict = Depends(get_current_user)
):
    """
    获取所有羁绊（含激活状态）
    
    返回所有羁绊列表，包含当前用户是否已激活
    """
    user_id = current_user["id"]
    
    await recruit_system.initialize()
    bonds = await recruit_system.get_all_bonds(user_id)
    
    return {
        "success": True,
        "bonds": bonds,
        "total": len(bonds),
        "activated": sum(1 for b in bonds if b["is_activated"]),
    }
