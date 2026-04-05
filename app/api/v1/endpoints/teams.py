"""
团队管理API端点
提供团队的创建、查询、更新、删除功能
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime
import uuid
from app.api.v1.schemas.team import (
    TeamCreate, TeamUpdate, TeamResponse,
    TeamMemberAdd, TeamMemberRoleUpdate, TeamMemberResponse,
    TeamRole
)


router = APIRouter()

# 模拟数据库存储（实际项目中应使用真实数据库）
_teams_db = {}
_team_members_db = {}


def get_current_user_id() -> str:
    """获取当前用户ID（模拟）"""
    # 实际项目中应从JWT token中获取
    return "user-123"


# ========== 团队管理API ==========

@router.post("/teams", response_model=TeamResponse)
async def create_team(team: TeamCreate, user_id: str = Depends(get_current_user_id)):
    """
    创建团队
    
    Args:
        team: 团队创建请求
        user_id: 当前用户ID
        
    Returns:
        TeamResponse: 创建的团队
    """
    try:
        team_id = str(uuid.uuid4())
        created_at = datetime.utcnow().isoformat()
        
        # 创建团队
        team_data = {
            "id": team_id,
            "name": team.name,
            "description": team.description,
            "owner_id": user_id,
            "created_at": created_at,
            "member_count": 1
        }
        
        _teams_db[team_id] = team_data
        
        # 添加创建者为owner
        member_id = str(uuid.uuid4())
        _team_members_db[member_id] = {
            "id": member_id,
            "team_id": team_id,
            "user_id": user_id,
            "role": TeamRole.OWNER,
            "joined_at": created_at
        }
        
        return TeamResponse(**team_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/teams", response_model=List[TeamResponse])
async def list_teams(user_id: str = Depends(get_current_user_id)):
    """
    列出用户所属团队
    
    Args:
        user_id: 当前用户ID
        
    Returns:
        List[TeamResponse]: 团队列表
    """
    try:
        # 查找用户所属的团队
        user_teams = []
        for member in _team_members_db.values():
            if member["user_id"] == user_id:
                team_id = member["team_id"]
                if team_id in _teams_db:
                    user_teams.append(TeamResponse(**_teams_db[team_id]))
        
        return user_teams
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/teams/{team_id}", response_model=TeamResponse)
async def get_team(team_id: str, user_id: str = Depends(get_current_user_id)):
    """
    获取团队详情
    
    Args:
        team_id: 团队ID
        user_id: 当前用户ID
        
    Returns:
        TeamResponse: 团队详情
    """
    try:
        # 检查团队是否存在
        if team_id not in _teams_db:
            raise HTTPException(status_code=404, detail="Team not found")
        
        # 检查用户是否是团队成员
        is_member = any(
            m["team_id"] == team_id and m["user_id"] == user_id
            for m in _team_members_db.values()
        )
        
        if not is_member:
            raise HTTPException(status_code=403, detail="Not a team member")
        
        return TeamResponse(**_teams_db[team_id])
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/teams/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: str,
    team_update: TeamUpdate,
    user_id: str = Depends(get_current_user_id)
):
    """
    更新团队信息（仅owner）
    
    Args:
        team_id: 团队ID
        team_update: 团队更新请求
        user_id: 当前用户ID
        
    Returns:
        TeamResponse: 更新后的团队
    """
    try:
        # 检查团队是否存在
        if team_id not in _teams_db:
            raise HTTPException(status_code=404, detail="Team not found")
        
        # 检查用户是否是owner
        team = _teams_db[team_id]
        if team["owner_id"] != user_id:
            raise HTTPException(status_code=403, detail="Only team owner can update team")
        
        # 更新团队信息
        if team_update.name is not None:
            team["name"] = team_update.name
        if team_update.description is not None:
            team["description"] = team_update.description
        
        return TeamResponse(**team)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/teams/{team_id}")
async def delete_team(team_id: str, user_id: str = Depends(get_current_user_id)):
    """
    删除团队（仅owner）
    
    Args:
        team_id: 团队ID
        user_id: 当前用户ID
        
    Returns:
        dict: 操作结果
    """
    try:
        # 检查团队是否存在
        if team_id not in _teams_db:
            raise HTTPException(status_code=404, detail="Team not found")
        
        # 检查用户是否是owner
        team = _teams_db[team_id]
        if team["owner_id"] != user_id:
            raise HTTPException(status_code=403, detail="Only team owner can delete team")
        
        # 删除团队成员
        members_to_delete = [
            m_id for m_id, m in _team_members_db.items()
            if m["team_id"] == team_id
        ]
        for m_id in members_to_delete:
            del _team_members_db[m_id]
        
        # 删除团队
        del _teams_db[team_id]
        
        return {"message": "Team deleted successfully", "team_id": team_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== 成员管理API ==========

@router.post("/teams/{team_id}/members", response_model=TeamMemberResponse)
async def add_team_member(
    team_id: str,
    member: TeamMemberAdd,
    user_id: str = Depends(get_current_user_id)
):
    """
    添加团队成员
    
    Args:
        team_id: 团队ID
        member: 成员添加请求
        user_id: 当前用户ID
        
    Returns:
        TeamMemberResponse: 添加的成员
    """
    try:
        # 检查团队是否存在
        if team_id not in _teams_db:
            raise HTTPException(status_code=404, detail="Team not found")
        
        # 检查当前用户是否是owner或admin
        current_member = next(
            (m for m in _team_members_db.values() 
             if m["team_id"] == team_id and m["user_id"] == user_id),
            None
        )
        
        if not current_member or current_member["role"] not in [TeamRole.OWNER, TeamRole.ADMIN]:
            raise HTTPException(status_code=403, detail="Only owner or admin can add members")
        
        # 检查用户是否已经是成员
        existing_member = next(
            (m for m in _team_members_db.values()
             if m["team_id"] == team_id and m["user_id"] == member.user_id),
            None
        )
        
        if existing_member:
            raise HTTPException(status_code=400, detail="User is already a team member")
        
        # 添加成员
        member_id = str(uuid.uuid4())
        joined_at = datetime.utcnow().isoformat()
        
        member_data = {
            "id": member_id,
            "team_id": team_id,
            "user_id": member.user_id,
            "role": member.role,
            "joined_at": joined_at
        }
        
        _team_members_db[member_id] = member_data
        
        # 更新团队成员数量
        _teams_db[team_id]["member_count"] += 1
        
        return TeamMemberResponse(**member_data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/teams/{team_id}/members", response_model=List[TeamMemberResponse])
async def list_team_members(
    team_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    列出团队成员
    
    Args:
        team_id: 团队ID
        user_id: 当前用户ID
        
    Returns:
        List[TeamMemberResponse]: 成员列表
    """
    try:
        # 检查团队是否存在
        if team_id not in _teams_db:
            raise HTTPException(status_code=404, detail="Team not found")
        
        # 检查用户是否是团队成员
        is_member = any(
            m["team_id"] == team_id and m["user_id"] == user_id
            for m in _team_members_db.values()
        )
        
        if not is_member:
            raise HTTPException(status_code=403, detail="Not a team member")
        
        # 获取团队成员
        members = [
            TeamMemberResponse(**m)
            for m in _team_members_db.values()
            if m["team_id"] == team_id
        ]
        
        return members
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/teams/{team_id}/members/{member_user_id}")
async def remove_team_member(
    team_id: str,
    member_user_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    移除团队成员
    
    Args:
        team_id: 团队ID
        member_user_id: 要移除的成员ID
        user_id: 当前用户ID
        
    Returns:
        dict: 操作结果
    """
    try:
        # 检查团队是否存在
        if team_id not in _teams_db:
            raise HTTPException(status_code=404, detail="Team not found")
        
        # 检查当前用户是否是owner或admin
        current_member = next(
            (m for m in _team_members_db.values()
             if m["team_id"] == team_id and m["user_id"] == user_id),
            None
        )
        
        if not current_member or current_member["role"] not in [TeamRole.OWNER, TeamRole.ADMIN]:
            raise HTTPException(status_code=403, detail="Only owner or admin can remove members")
        
        # 查找要移除的成员
        member_to_remove = next(
            (m_id for m_id, m in _team_members_db.items()
             if m["team_id"] == team_id and m["user_id"] == member_user_id),
            None
        )
        
        if not member_to_remove:
            raise HTTPException(status_code=404, detail="Member not found")
        
        # 不能移除owner
        if _team_members_db[member_to_remove]["role"] == TeamRole.OWNER:
            raise HTTPException(status_code=400, detail="Cannot remove team owner")
        
        # 移除成员
        del _team_members_db[member_to_remove]
        
        # 更新团队成员数量
        _teams_db[team_id]["member_count"] -= 1
        
        return {"message": "Member removed successfully", "user_id": member_user_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/teams/{team_id}/members/{member_user_id}/role", response_model=TeamMemberResponse)
async def update_member_role(
    team_id: str,
    member_user_id: str,
    role_update: TeamMemberRoleUpdate,
    user_id: str = Depends(get_current_user_id)
):
    """
    更新成员角色
    
    Args:
        team_id: 团队ID
        member_user_id: 成员ID
        role_update: 角色更新请求
        user_id: 当前用户ID
        
    Returns:
        TeamMemberResponse: 更新后的成员
    """
    try:
        # 检查团队是否存在
        if team_id not in _teams_db:
            raise HTTPException(status_code=404, detail="Team not found")
        
        # 检查当前用户是否是owner
        team = _teams_db[team_id]
        if team["owner_id"] != user_id:
            raise HTTPException(status_code=403, detail="Only team owner can update member roles")
        
        # 查找成员
        member_id = next(
            (m_id for m_id, m in _team_members_db.items()
             if m["team_id"] == team_id and m["user_id"] == member_user_id),
            None
        )
        
        if not member_id:
            raise HTTPException(status_code=404, detail="Member not found")
        
        # 更新角色
        _team_members_db[member_id]["role"] = role_update.role
        
        return TeamMemberResponse(**_team_members_db[member_id])
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
