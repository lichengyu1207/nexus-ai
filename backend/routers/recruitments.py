"""
招募管理API路由
处理团队招募相关功能
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..auth import get_current_user
from ..database_pg import get_db

logger = logging.getLogger(__name__)
router = APIRouter(tags=["recruitments"])


class RecruitmentCreate(BaseModel):
    """创建招募请求"""
    teamId: str = Field(..., description="团队ID")
    title: str = Field(..., description="招募标题")
    description: str = Field(..., description="招募描述")
    requiredSkills: list[str] = Field(..., description="所需技能")
    budget: float = Field(..., description="预算")
    deadline: str = Field(..., description="截止日期")


class RecruitmentUpdate(BaseModel):
    """更新招募请求"""
    title: Optional[str] = None
    description: Optional[str] = None
    requiredSkills: Optional[list[str]] = None
    budget: Optional[float] = None
    deadline: Optional[str] = None
    status: Optional[str] = None


class BidCreate(BaseModel):
    """创建投标请求"""
    proposal: str = Field(..., description="投标方案")
    price: float = Field(..., description="投标价格")
    estimatedDays: int = Field(..., description="预计完成天数")


@router.post("/recruitments")
async def create_recruitment(
    request: RecruitmentCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    创建招募
    """
    user_id = current_user["id"]
    
    async with get_db() as db:
        # 检查团队是否存在
        team = await db.fetchone(
            "SELECT id FROM teams WHERE id = $1 AND user_id = $2",
            request.teamId, user_id
        )
        
        if not team:
            raise HTTPException(status_code=404, detail="团队不存在")
        
        # 创建招募
        recruitment_id = str(hash(f"{user_id}_{request.teamId}_{request.title}"))
        
        await db.execute(
            """INSERT INTO recruitments 
               (id, user_id, team_id, title, description, required_skills, budget, deadline, status, created_at)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW())""",
            recruitment_id,
            user_id,
            request.teamId,
            request.title,
            request.description,
            request.requiredSkills,
            request.budget,
            request.deadline,
            "open"
        )
        
        # 获取团队名称
        team_name = await db.fetchval(
            "SELECT name FROM teams WHERE id = $1",
            request.teamId
        )
        
        return {
            "id": recruitment_id,
            "teamId": request.teamId,
            "teamName": team_name,
            "title": request.title,
            "description": request.description,
            "requiredSkills": request.requiredSkills,
            "budget": request.budget,
            "deadline": request.deadline,
            "status": "open",
            "bidsCount": 0,
            "createdAt": "now"
        }


@router.get("/recruitments/{recruitment_id}")
async def get_recruitment(
    recruitment_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    获取招募详情
    """
    user_id = current_user["id"]
    
    async with get_db() as db:
        recruitment = await db.fetchone(
            """SELECT r.*, t.name as team_name 
               FROM recruitments r
               JOIN teams t ON r.team_id = t.id
               WHERE r.id = $1 AND r.user_id = $2""",
            recruitment_id, user_id
        )
        
        if not recruitment:
            raise HTTPException(status_code=404, detail="招募不存在")
        
        # 获取投标数量
        bids_count = await db.fetchval(
            "SELECT COUNT(*) FROM bids WHERE recruitment_id = $1",
            recruitment_id
        )
        
        return {
            "id": recruitment["id"],
            "teamId": recruitment["team_id"],
            "teamName": recruitment["team_name"],
            "title": recruitment["title"],
            "description": recruitment["description"],
            "requiredSkills": recruitment["required_skills"],
            "budget": recruitment["budget"],
            "deadline": recruitment["deadline"],
            "status": recruitment["status"],
            "bidsCount": bids_count,
            "createdAt": recruitment["created_at"].isoformat()
        }


@router.get("/teams/{team_id}/recruitments")
async def get_team_recruitments(
    team_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    获取团队的招募列表
    """
    user_id = current_user["id"]
    
    async with get_db() as db:
        # 检查团队是否存在
        team = await db.fetchone(
            "SELECT id FROM teams WHERE id = $1 AND user_id = $2",
            team_id, user_id
        )
        
        if not team:
            raise HTTPException(status_code=404, detail="团队不存在")
        
        # 获取招募列表
        recruitments = await db.fetch(
            """SELECT r.*, t.name as team_name 
               FROM recruitments r
               JOIN teams t ON r.team_id = t.id
               WHERE r.team_id = $1 AND r.user_id = $2
               ORDER BY r.created_at DESC""",
            team_id, user_id
        )
        
        result = []
        for recruitment in recruitments:
            # 获取投标数量
            bids_count = await db.fetchval(
                "SELECT COUNT(*) FROM bids WHERE recruitment_id = $1",
                recruitment["id"]
            )
            
            result.append({
                "id": recruitment["id"],
                "teamId": recruitment["team_id"],
                "teamName": recruitment["team_name"],
                "title": recruitment["title"],
                "description": recruitment["description"],
                "requiredSkills": recruitment["required_skills"],
                "budget": recruitment["budget"],
                "deadline": recruitment["deadline"],
                "status": recruitment["status"],
                "bidsCount": bids_count,
                "createdAt": recruitment["created_at"].isoformat()
            })
        
        return {"recruitments": result}


@router.post("/recruitments/{recruitment_id}/bids")
async def submit_bid(
    recruitment_id: str,
    request: BidCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    提交投标
    """
    user_id = current_user["id"]
    
    async with get_db() as db:
        # 检查招募是否存在
        recruitment = await db.fetchone(
            "SELECT id, status FROM recruitments WHERE id = $1",
            recruitment_id
        )
        
        if not recruitment:
            raise HTTPException(status_code=404, detail="招募不存在")
        
        if recruitment["status"] != "open":
            raise HTTPException(status_code=400, detail="招募已关闭")
        
        # 创建投标
        bid_id = str(hash(f"{user_id}_{recruitment_id}_{request.price}"))
        
        await db.execute(
            """INSERT INTO bids 
               (id, recruitment_id, user_id, proposal, price, estimated_days, status, created_at)
               VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())""",
            bid_id,
            recruitment_id,
            user_id,
            request.proposal,
            request.price,
            request.estimatedDays,
            "pending"
        )
        
        # 获取用户信息
        user = await db.fetchone(
            "SELECT name, avatar FROM users WHERE id = $1",
            user_id
        )
        
        return {
            "id": bid_id,
            "recruitmentId": recruitment_id,
            "talentId": user_id,
            "talentName": user["name"] if user else "未知用户",
            "talentAvatar": user["avatar"] if user else None,
            "proposal": request.proposal,
            "price": request.price,
            "estimatedDays": request.estimatedDays,
            "status": "pending",
            "createdAt": "now"
        }


@router.get("/recruitments/{recruitment_id}/bids")
async def get_recruitment_bids(
    recruitment_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    获取招募的投标列表
    """
    user_id = current_user["id"]
    
    async with get_db() as db:
        # 检查招募是否存在且属于当前用户
        recruitment = await db.fetchone(
            "SELECT id FROM recruitments WHERE id = $1 AND user_id = $2",
            recruitment_id, user_id
        )
        
        if not recruitment:
            raise HTTPException(status_code=404, detail="招募不存在")
        
        # 获取投标列表
        bids = await db.fetch(
            """SELECT b.*, u.name as talent_name, u.avatar as talent_avatar 
               FROM bids b
               JOIN users u ON b.user_id = u.id
               WHERE b.recruitment_id = $1
               ORDER BY b.created_at DESC""",
            recruitment_id
        )
        
        result = []
        for bid in bids:
            result.append({
                "id": bid["id"],
                "recruitmentId": bid["recruitment_id"],
                "talentId": bid["user_id"],
                "talentName": bid["talent_name"],
                "talentAvatar": bid["talent_avatar"],
                "proposal": bid["proposal"],
                "price": bid["price"],
                "estimatedDays": bid["estimated_days"],
                "status": bid["status"],
                "createdAt": bid["created_at"].isoformat()
            })
        
        return {"bids": result}


@router.put("/bids/{bid_id}/accept")
async def accept_bid(
    bid_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    接受投标
    """
    user_id = current_user["id"]
    
    async with get_db() as db:
        # 检查投标是否存在且招募属于当前用户
        bid = await db.fetchone(
            """SELECT b.*, r.user_id as recruitment_owner 
               FROM bids b
               JOIN recruitments r ON b.recruitment_id = r.id
               WHERE b.id = $1""",
            bid_id
        )
        
        if not bid:
            raise HTTPException(status_code=404, detail="投标不存在")
        
        if bid["recruitment_owner"] != user_id:
            raise HTTPException(status_code=403, detail="无权操作")
        
        if bid["status"] != "pending":
            raise HTTPException(status_code=400, detail="投标已处理")
        
        # 接受投标
        await db.execute(
            "UPDATE bids SET status = 'accepted' WHERE id = $1",
            bid_id
        )
        
        # 关闭招募
        await db.execute(
            "UPDATE recruitments SET status = 'closed' WHERE id = $1",
            bid["recruitment_id"]
        )
        
        # 创建任务
        task_id = str(hash(f"{user_id}_{bid_id}_{bid['recruitment_id']}"))
        
        recruitment = await db.fetchone(
            "SELECT title, description FROM recruitments WHERE id = $1",
            bid["recruitment_id"]
        )
        
        await db.execute(
            """INSERT INTO tasks 
               (id, user_id, title, description, status, created_at)
               VALUES ($1, $2, $3, $4, $5, NOW())""",
            task_id,
            user_id,
            recruitment["title"],
            recruitment["description"],
            "pending"
        )
        
        # 获取投标详情
        updated_bid = await db.fetchone(
            """SELECT b.*, u.name as talent_name, u.avatar as talent_avatar 
               FROM bids b
               JOIN users u ON b.user_id = u.id
               WHERE b.id = $1""",
            bid_id
        )
        
        return {
            "success": True,
            "task": {
                "id": task_id,
                "title": recruitment["title"],
                "status": "pending"
            },
            "bid": {
                "id": updated_bid["id"],
                "recruitmentId": updated_bid["recruitment_id"],
                "talentId": updated_bid["user_id"],
                "talentName": updated_bid["talent_name"],
                "talentAvatar": updated_bid["talent_avatar"],
                "proposal": updated_bid["proposal"],
                "price": updated_bid["price"],
                "estimatedDays": updated_bid["estimated_days"],
                "status": "accepted",
                "createdAt": updated_bid["created_at"].isoformat()
            }
        }


@router.put("/bids/{bid_id}/reject")
async def reject_bid(
    bid_id: str,
    reason: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    拒绝投标
    """
    user_id = current_user["id"]
    
    async with get_db() as db:
        # 检查投标是否存在且招募属于当前用户
        bid = await db.fetchone(
            """SELECT b.*, r.user_id as recruitment_owner 
               FROM bids b
               JOIN recruitments r ON b.recruitment_id = r.id
               WHERE b.id = $1""",
            bid_id
        )
        
        if not bid:
            raise HTTPException(status_code=404, detail="投标不存在")
        
        if bid["recruitment_owner"] != user_id:
            raise HTTPException(status_code=403, detail="无权操作")
        
        if bid["status"] != "pending":
            raise HTTPException(status_code=400, detail="投标已处理")
        
        # 拒绝投标
        await db.execute(
            "UPDATE bids SET status = 'rejected' WHERE id = $1",
            bid_id
        )
        
        return {"success": True}


@router.get("/talents/recommended")
async def get_recommended_talents(
    skills: Optional[str] = None,
    teamId: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    获取推荐人才
    """
    # 模拟数据
    talents = [
        {
            "id": "1",
            "name": "张三",
            "matchScore": 95,
            "skills": [
                {"name": "数据分析", "proficiency": 90, "successRate": 95}
            ],
            "rating": 4.8,
            "completedTasks": 120,
            "isAvailable": True
        },
        {
            "id": "2",
            "name": "李四",
            "matchScore": 88,
            "skills": [
                {"name": "前端开发", "proficiency": 85, "successRate": 90}
            ],
            "rating": 4.6,
            "completedTasks": 85,
            "isAvailable": True
        }
    ]
    
    return {"talents": talents}


@router.post("/talents/{talent_id}/invite")
async def invite_talent(
    talent_id: str,
    teamId: str,
    message: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    邀请人才
    """
    # 模拟数据
    return {
        "success": True,
        "invitationId": str(hash(f"{current_user['id']}_{talent_id}_{teamId}"))
    }


@router.get("/skills/{skill_id}/talents")
async def get_skill_talents(
    skill_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    获取具有特定技能的人才
    """
    # 模拟数据
    talents = [
        {
            "id": "1",
            "name": "张三",
            "matchScore": 95,
            "skills": [
                {"name": "数据分析", "proficiency": 90, "successRate": 95}
            ],
            "rating": 4.8,
            "completedTasks": 120,
            "isAvailable": True
        }
    ]
    
    return {"talents": talents}
