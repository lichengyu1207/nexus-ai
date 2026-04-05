"""
团队管理API路由
提供团队创建、邀请、成员管理等功能
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uuid
import json

from ..auth import get_current_user
from ..database import TeamDB, SharedTaskDB, UserDB, NotificationDB
from ..exceptions import ForbiddenException, NotFoundException, BadRequestException, ErrorCode

router = APIRouter(prefix="/api/teams", tags=["teams"])


class TeamCreate(BaseModel):
    """创建团队请求"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class TeamUpdate(BaseModel):
    """更新团队请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class TeamSettings(BaseModel):
    """团队设置"""
    allow_member_invite: bool = True
    require_approval: bool = False
    default_role: str = "member"


class TeamSettingsUpdate(BaseModel):
    """更新团队设置请求"""
    allow_member_invite: Optional[bool] = None
    require_approval: Optional[bool] = None
    default_role: Optional[str] = None


class RoleUpdate(BaseModel):
    """角色更新请求"""
    role: str = Field(..., pattern="^(admin|member)$")


class TeamResponse(BaseModel):
    """团队响应"""
    id: str
    name: str
    description: Optional[str]
    owner_id: str
    invite_code: str
    settings: Optional[Dict[str, Any]] = None
    created_at: Optional[str]
    user_role: Optional[str] = None


class TeamMemberResponse(BaseModel):
    """团队成员响应"""
    id: str
    team_id: str
    user_id: str
    role: str
    status: str
    email: str
    full_name: Optional[str]
    avatar_url: Optional[str]
    invited_by: Optional[str]
    invited_at: Optional[str]
    joined_at: Optional[str]


class TeamTaskResponse(BaseModel):
    """团队任务响应"""
    id: str
    user_id: str
    query: str
    status: str
    progress: int
    style: str
    team_id: Optional[str]
    owner_email: str
    owner_name: Optional[str]
    created_at: Optional[str]


class InviteResponse(BaseModel):
    """邀请响应"""
    invite_code: str
    invite_link: str
    expires_in: Optional[int] = None


@router.post("", response_model=TeamResponse)
async def create_team(
    team_data: TeamCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    创建团队
    
    Args:
        team_data: 团队数据
        current_user: 当前用户
        
    Returns:
        TeamResponse: 创建的团队
    """
    team_id = str(uuid.uuid4())
    
    team = await TeamDB.create_team(
        team_id=team_id,
        name=team_data.name,
        description=team_data.description,
        owner_id=current_user["id"]
    )
    
    return TeamResponse(
        id=team["id"],
        name=team["name"],
        description=team.get("description"),
        owner_id=team["owner_id"],
        invite_code=team["invite_code"],
        settings={},
        created_at=None,
        user_role="owner"
    )


@router.get("", response_model=List[TeamResponse])
async def get_my_teams(current_user: dict = Depends(get_current_user)):
    """
    获取当前用户所属的所有团队
    
    Args:
        current_user: 当前用户
        
    Returns:
        List[TeamResponse]: 团队列表
    """
    teams = await TeamDB.get_user_teams(current_user["id"])
    
    return [
        TeamResponse(
            id=team["id"],
            name=team["name"],
            description=team.get("description"),
            owner_id=team["owner_id"],
            invite_code=team["invite_code"],
            created_at=team.get("created_at"),
            user_role=team.get("user_role")
        )
        for team in teams
    ]


@router.get("/{team_id}", response_model=TeamResponse)
async def get_team(
    team_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    获取团队详情
    
    Args:
        team_id: 团队ID
        current_user: 当前用户
        
    Returns:
        TeamResponse: 团队详情
    """
    if not await TeamDB.is_team_member(team_id, current_user["id"]):
        raise HTTPException(status_code=403, detail="您不是该团队成员")
    
    team = await TeamDB.get_team_by_id(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="团队不存在")
    
    return TeamResponse(
        id=team["id"],
        name=team["name"],
        description=team.get("description"),
        owner_id=team["owner_id"],
        invite_code=team["invite_code"],
        created_at=team.get("created_at")
    )


@router.put("/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: str,
    team_data: TeamUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    更新团队信息
    
    Args:
        team_id: 团队ID
        team_data: 更新数据
        current_user: 当前用户
        
    Returns:
        TeamResponse: 更新后的团队
    """
    team = await TeamDB.get_team_by_id(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="团队不存在")
    
    if team["owner_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="只有团队所有者可以更新团队信息")
    
    updated_team = await TeamDB.update_team(
        team_id,
        name=team_data.name,
        description=team_data.description
    )
    
    return TeamResponse(
        id=updated_team["id"],
        name=updated_team["name"],
        description=updated_team.get("description"),
        owner_id=updated_team["owner_id"],
        invite_code=updated_team["invite_code"],
        created_at=updated_team.get("created_at")
    )


@router.delete("/{team_id}")
async def delete_team(
    team_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    删除团队
    
    Args:
        team_id: 团队ID
        current_user: 当前用户
        
    Returns:
        dict: 删除结果
    """
    team = await TeamDB.get_team_by_id(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="团队不存在")
    
    if team["owner_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="只有团队所有者可以删除团队")
    
    await TeamDB.delete_team(team_id)
    
    return {"message": "团队已删除", "team_id": team_id}


@router.get("/{team_id}/members", response_model=List[TeamMemberResponse])
async def get_team_members(
    team_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    获取团队成员列表
    
    Args:
        team_id: 团队ID
        current_user: 当前用户
        
    Returns:
        List[TeamMemberResponse]: 成员列表
    """
    if not await TeamDB.is_team_member(team_id, current_user["id"]):
        raise HTTPException(status_code=403, detail="您不是该团队成员")
    
    members = await TeamDB.get_team_members(team_id)
    
    return [
        TeamMemberResponse(
            id=member["id"],
            team_id=member["team_id"],
            user_id=member["user_id"],
            role=member["role"],
            email=member["email"],
            full_name=member.get("full_name"),
            joined_at=member.get("joined_at")
        )
        for member in members
    ]


@router.post("/{team_id}/members")
async def add_team_member(
    team_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    通过邀请码加入团队
    
    Args:
        team_id: 团队ID
        current_user: 当前用户
        
    Returns:
        dict: 加入结果
    """
    team = await TeamDB.get_team_by_id(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="团队不存在")
    
    success = await TeamDB.add_member(team_id, current_user["id"])
    
    if not success:
        raise HTTPException(status_code=400, detail="您已经是该团队成员")
    
    return {"message": "已成功加入团队", "team_id": team_id}


@router.post("/join/{invite_code}")
async def join_team_by_code(
    invite_code: str,
    current_user: dict = Depends(get_current_user)
):
    """
    通过邀请码加入团队
    
    Args:
        invite_code: 邀请码
        current_user: 当前用户
        
    Returns:
        dict: 加入结果
    """
    team = await TeamDB.get_team_by_invite_code(invite_code)
    if not team:
        raise HTTPException(status_code=404, detail="无效的邀请码")
    
    success = await TeamDB.add_member(team["id"], current_user["id"])
    
    if not success:
        raise HTTPException(status_code=400, detail="您已经是该团队成员")
    
    return {
        "message": "已成功加入团队",
        "team_id": team["id"],
        "team_name": team["name"]
    }


@router.delete("/{team_id}/members/{user_id}")
async def remove_team_member(
    team_id: str,
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    移除团队成员
    
    Args:
        team_id: 团队ID
        user_id: 要移除的用户ID
        current_user: 当前用户
        
    Returns:
        dict: 移除结果
    """
    team = await TeamDB.get_team_by_id(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="团队不存在")
    
    if team["owner_id"] != current_user["id"] and user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="只有团队所有者可以移除成员")
    
    success = await TeamDB.remove_member(team_id, user_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="无法移除团队所有者")
    
    return {"message": "成员已移除", "team_id": team_id, "user_id": user_id}


@router.get("/{team_id}/tasks", response_model=List[TeamTaskResponse])
async def get_team_tasks(
    team_id: str,
    limit: int = 20,
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """
    获取团队共享的任务
    
    Args:
        team_id: 团队ID
        limit: 每页数量
        offset: 偏移量
        current_user: 当前用户
        
    Returns:
        List[TeamTaskResponse]: 任务列表
    """
    if not await TeamDB.is_team_member(team_id, current_user["id"]):
        raise HTTPException(status_code=403, detail="您不是该团队成员")
    
    tasks = await SharedTaskDB.get_team_tasks(team_id, limit, offset)
    
    return [
        TeamTaskResponse(
            id=task["id"],
            user_id=task["user_id"],
            query=task["query"],
            status=task["status"],
            progress=task.get("progress", 0),
            style=task.get("style", "balanced"),
            team_id=task.get("team_id"),
            owner_email=task["owner_email"],
            owner_name=task.get("owner_name"),
            created_at=task.get("created_at")
        )
        for task in tasks
    ]


@router.post("/{team_id}/tasks/{task_id}")
async def share_task_to_team(
    team_id: str,
    task_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    将任务分享到团队
    
    Args:
        team_id: 团队ID
        task_id: 任务ID
        current_user: 当前用户
        
    Returns:
        dict: 分享结果
    """
    if not await TeamDB.is_team_member(team_id, current_user["id"]):
        raise HTTPException(status_code=403, detail="您不是该团队成员")
    
    success = await SharedTaskDB.share_task_to_team(task_id, team_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="分享失败")
    
    team = await TeamDB.get_team_by_id(team_id)
    sharer_name = current_user.get("full_name") or current_user["email"].split("@")[0]
    
    try:
        members = await TeamDB.get_team_members(team_id)
        for member in members:
            if member["user_id"] != current_user["id"]:
                await NotificationDB.create_notification(
                    user_id=member["user_id"],
                    type="task_shared",
                    title=f"新任务分享到 {team['name']}",
                    content=f"{sharer_name} 分享了一个新的分析报告到团队",
                    link=f"/tasks/{task_id}",
                    action_text="查看报告",
                    related_id=task_id,
                    related_type="task"
                )
    except Exception as e:
        import logging
        logging.error(f"Failed to send task share notifications: {e}")
    
    return {"message": "任务已分享到团队", "task_id": task_id, "team_id": team_id}


@router.post("/{team_id}/invite", response_model=InviteResponse)
async def generate_invite_link(
    team_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    生成团队邀请链接
    
    Args:
        team_id: 团队ID
        current_user: 当前用户
        
    Returns:
        InviteResponse: 邀请信息
    """
    team = await TeamDB.get_team_by_id(team_id)
    if not team:
        raise NotFoundException("团队不存在", ErrorCode.TEAM_NOT_FOUND)
    
    is_admin = await TeamDB.is_team_admin(team_id, current_user["id"])
    if not is_admin:
        settings = json.loads(team.get("settings") or "{}")
        if not settings.get("allow_member_invite", True):
            raise ForbiddenException("您没有权限邀请成员")
    
    invite_code = team.get("invite_code")
    if not invite_code:
        invite_code = await TeamDB.regenerate_invite_code(team_id)
    
    return InviteResponse(
        invite_code=invite_code,
        invite_link=f"/teams/join/{invite_code}"
    )


@router.post("/{team_id}/invite/regenerate", response_model=InviteResponse)
async def regenerate_invite_link(
    team_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    重新生成邀请链接
    
    Args:
        team_id: 团队ID
        current_user: 当前用户
        
    Returns:
        InviteResponse: 新邀请信息
    """
    team = await TeamDB.get_team_by_id(team_id)
    if not team:
        raise NotFoundException("团队不存在", ErrorCode.TEAM_NOT_FOUND)
    
    if not await TeamDB.is_team_admin(team_id, current_user["id"]):
        raise ForbiddenException("只有管理员可以重新生成邀请链接")
    
    new_code = await TeamDB.regenerate_invite_code(team_id)
    
    return InviteResponse(
        invite_code=new_code,
        invite_link=f"/teams/join/{new_code}"
    )


@router.post("/join/{invite_code}")
async def join_team_by_code(
    invite_code: str,
    current_user: dict = Depends(get_current_user)
):
    """
    通过邀请码加入团队
    
    Args:
        invite_code: 邀请码
        current_user: 当前用户
        
    Returns:
        dict: 加入结果
    """
    team = await TeamDB.get_team_by_invite_code(invite_code)
    if not team:
        raise NotFoundException("无效的邀请码", ErrorCode.NOT_FOUND)
    
    existing_role = await TeamDB.get_member_role(team["id"], current_user["id"])
    if existing_role:
        raise BadRequestException("您已经是该团队成员")
    
    settings = json.loads(team.get("settings") or "{}")
    default_role = settings.get("default_role", "member")
    status = "pending" if settings.get("require_approval", False) else "active"
    
    success = await TeamDB.add_member(
        team_id=team["id"],
        user_id=current_user["id"],
        role=default_role,
        invited_by=None,
        status=status
    )
    
    if not success:
        raise BadRequestException("加入团队失败")
    
    if status == "active":
        try:
            joiner_name = current_user.get("full_name") or current_user["email"].split("@")[0]
            admins = await TeamDB.get_team_admins(team["id"])
            for admin in admins:
                if admin["user_id"] != current_user["id"]:
                    await NotificationDB.create_notification(
                        user_id=admin["user_id"],
                        type="member_joined",
                        title=f"新成员加入 {team['name']}",
                        content=f"{joiner_name} 已加入团队",
                        link=f"/teams/{team['id']}",
                        action_text="查看团队",
                        related_id=team["id"],
                        related_type="team"
                    )
        except Exception as e:
            import logging
            logging.error(f"Failed to send member join notifications: {e}")
    
    return {
        "message": "已成功加入团队" if status == "active" else "申请已提交，等待审批",
        "team_id": team["id"],
        "team_name": team["name"],
        "status": status
    }


@router.get("/{team_id}/settings", response_model=TeamSettings)
async def get_team_settings(
    team_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    获取团队设置
    
    Args:
        team_id: 团队ID
        current_user: 当前用户
        
    Returns:
        TeamSettings: 团队设置
    """
    if not await TeamDB.is_team_member(team_id, current_user["id"]):
        raise ForbiddenException("您不是该团队成员")
    
    team = await TeamDB.get_team_by_id(team_id)
    if not team:
        raise NotFoundException("团队不存在", ErrorCode.TEAM_NOT_FOUND)
    
    settings = json.loads(team.get("settings") or "{}")
    
    return TeamSettings(
        allow_member_invite=settings.get("allow_member_invite", True),
        require_approval=settings.get("require_approval", False),
        default_role=settings.get("default_role", "member")
    )


@router.put("/{team_id}/settings", response_model=TeamSettings)
async def update_team_settings(
    team_id: str,
    settings_data: TeamSettingsUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    更新团队设置
    
    Args:
        team_id: 团队ID
        settings_data: 设置数据
        current_user: 当前用户
        
    Returns:
        TeamSettings: 更新后的设置
    """
    if not await TeamDB.is_team_admin(team_id, current_user["id"]):
        raise ForbiddenException("只有管理员可以修改团队设置")
    
    team = await TeamDB.get_team_by_id(team_id)
    if not team:
        raise NotFoundException("团队不存在", ErrorCode.TEAM_NOT_FOUND)
    
    current_settings = json.loads(team.get("settings") or "{}")
    
    if settings_data.allow_member_invite is not None:
        current_settings["allow_member_invite"] = settings_data.allow_member_invite
    if settings_data.require_approval is not None:
        current_settings["require_approval"] = settings_data.require_approval
    if settings_data.default_role is not None:
        current_settings["default_role"] = settings_data.default_role
    
    await TeamDB.update_team_settings(team_id, current_settings)
    
    return TeamSettings(**current_settings)


@router.put("/{team_id}/members/{user_id}/role")
async def update_member_role(
    team_id: str,
    user_id: str,
    role_data: RoleUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    更新成员角色
    
    Args:
        team_id: 团队ID
        user_id: 用户ID
        role_data: 角色数据
        current_user: 当前用户
        
    Returns:
        dict: 更新结果
    """
    if not await TeamDB.is_team_admin(team_id, current_user["id"]):
        raise ForbiddenException("只有管理员可以修改成员角色")
    
    success = await TeamDB.update_member_role(team_id, user_id, role_data.role)
    
    if not success:
        raise BadRequestException("无法修改该成员角色")
    
    return {"message": "角色已更新", "user_id": user_id, "new_role": role_data.role}


@router.delete("/{team_id}/members/{user_id}")
async def remove_team_member(
    team_id: str,
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    移除团队成员
    
    Args:
        team_id: 团队ID
        user_id: 要移除的用户ID
        current_user: 当前用户
        
    Returns:
        dict: 移除结果
    """
    team = await TeamDB.get_team_by_id(team_id)
    if not team:
        raise NotFoundException("团队不存在", ErrorCode.TEAM_NOT_FOUND)
    
    is_admin = await TeamDB.is_team_admin(team_id, current_user["id"])
    is_self = user_id == current_user["id"]
    
    if not is_admin and not is_self:
        raise ForbiddenException("只有管理员可以移除成员")
    
    target_role = await TeamDB.get_member_role(team_id, user_id)
    if target_role == "owner":
        raise BadRequestException("无法移除团队所有者")
    
    success = await TeamDB.remove_member(team_id, user_id)
    
    if not success:
        raise BadRequestException("移除成员失败")
    
    return {"message": "成员已移除", "team_id": team_id, "user_id": user_id}
