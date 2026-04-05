"""
管理后台API路由
提供用户管理、系统统计、系统设置等功能
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import json

from ..auth import (
    get_current_user, 
    require_admin, 
    require_super_admin,
    is_admin,
    is_super_admin,
    has_permission,
)
from ..database import AdminDB
from ..exceptions import ForbiddenException, NotFoundException, ErrorCode

router = APIRouter(prefix="/api/admin", tags=["admin"])


class UserResponse(BaseModel):
    """用户响应模型"""
    id: str
    username: str
    email: str
    full_name: Optional[str]
    avatar_url: Optional[str]
    role: str
    is_admin: bool
    is_active: bool
    permissions: Optional[Dict[str, bool]] = None
    created_at: Optional[str]
    updated_at: Optional[str]


class UserListResponse(BaseModel):
    """用户列表响应"""
    users: List[UserResponse]
    total: int


class RoleUpdateRequest(BaseModel):
    """角色更新请求"""
    role: Optional[str] = None
    is_admin: Optional[bool] = None
    permissions: Optional[Dict[str, bool]] = None


class PermissionUpdateRequest(BaseModel):
    """权限更新请求"""
    permissions: Dict[str, bool]


class SystemStats(BaseModel):
    """系统统计"""
    total_users: int
    admin_users: int
    active_users: int
    total_tasks: int
    completed_tasks: int
    total_reports: int
    total_teams: int
    total_comments: int


class SystemSettings(BaseModel):
    """系统设置"""
    allow_registration: bool = True
    default_analysis_style: str = "balanced"
    max_tasks_per_user: int = 100
    max_teams_per_user: int = 10
    maintenance_mode: bool = False


class SettingsUpdateRequest(BaseModel):
    """设置更新请求"""
    allow_registration: Optional[bool] = None
    default_analysis_style: Optional[str] = None
    max_tasks_per_user: Optional[int] = None
    max_teams_per_user: Optional[int] = None
    maintenance_mode: Optional[bool] = None


@router.get("/users", response_model=UserListResponse)
async def get_users(
    search: Optional[str] = Query(None),
    is_admin: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    admin: dict = Depends(require_admin)
):
    """
    获取用户列表
    
    Args:
        search: 搜索关键词
        is_admin: 是否管理员过滤
        limit: 每页数量
        offset: 偏移量
        admin: 管理员用户
        
    Returns:
        UserListResponse: 用户列表
    """
    users = await AdminDB.get_all_users(
        limit=limit,
        offset=offset,
        search=search,
        is_admin=is_admin
    )
    
    total = await AdminDB.get_users_count(search=search, is_admin=is_admin)
    
    return UserListResponse(
        users=[
            UserResponse(
                id=u["id"],
                username=u["username"],
                email=u["email"],
                full_name=u.get("full_name"),
                avatar_url=u.get("avatar_url"),
                role=u.get("role", "user"),
                is_admin=bool(u.get("is_admin")),
                is_active=bool(u.get("is_active")),
                permissions=json.loads(u.get("permissions", "{}")) if u.get("permissions") else {},
                created_at=u.get("created_at"),
                updated_at=u.get("updated_at")
            )
            for u in users
        ],
        total=total
    )


@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    role_data: RoleUpdateRequest,
    admin: dict = Depends(require_super_admin)
):
    """
    更新用户角色（仅超级管理员）
    
    Args:
        user_id: 用户ID
        role_data: 角色数据
        admin: 超级管理员用户
        
    Returns:
        dict: 更新结果
    """
    if user_id == admin["id"]:
        raise ForbiddenException("不能修改自己的角色")
    
    if role_data.role:
        valid_roles = ["user", "admin", "super_admin"]
        if role_data.role not in valid_roles:
            raise ForbiddenException(f"无效的角色，可选值: {', '.join(valid_roles)}")
        success = await AdminDB.set_user_role(user_id, role_data.role)
    elif role_data.is_admin is not None:
        success = await AdminDB.set_user_admin(user_id, role_data.is_admin)
    else:
        raise ForbiddenException("请提供role或is_admin参数")
    
    if not success:
        raise NotFoundException("用户不存在", ErrorCode.USER_NOT_FOUND)
    
    return {
        "message": "角色已更新",
        "user_id": user_id,
        "role": role_data.role,
        "is_admin": role_data.is_admin
    }


@router.put("/users/{user_id}/permissions")
async def update_user_permissions(
    user_id: str,
    perm_data: PermissionUpdateRequest,
    admin: dict = Depends(require_super_admin)
):
    """
    更新用户权限（仅超级管理员）
    
    Args:
        user_id: 用户ID
        perm_data: 权限数据
        admin: 超级管理员用户
        
    Returns:
        dict: 更新结果
    """
    if user_id == admin["id"]:
        raise ForbiddenException("不能修改自己的权限")
    
    success = await AdminDB.set_user_permissions(user_id, perm_data.permissions)
    
    if not success:
        raise NotFoundException("用户不存在", ErrorCode.USER_NOT_FOUND)
    
    return {
        "message": "权限已更新",
        "user_id": user_id,
        "permissions": perm_data.permissions
    }


@router.put("/users/{user_id}/status")
async def update_user_status(
    user_id: str,
    is_active: bool,
    admin: dict = Depends(require_admin)
):
    """
    更新用户状态（启用/禁用）
    
    Args:
        user_id: 用户ID
        is_active: 是否激活
        admin: 管理员用户
        
    Returns:
        dict: 更新结果
    """
    if user_id == admin["id"]:
        raise ForbiddenException("不能修改自己的状态")
    
    success = await AdminDB.set_user_active(user_id, is_active)
    
    if not success:
        raise NotFoundException("用户不存在", ErrorCode.USER_NOT_FOUND)
    
    return {
        "message": "状态已更新",
        "user_id": user_id,
        "is_active": is_active
    }


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    admin: dict = Depends(require_super_admin)
):
    """
    删除用户（仅超级管理员）
    
    Args:
        user_id: 用户ID
        admin: 超级管理员用户
        
    Returns:
        dict: 删除结果
    """
    if user_id == admin["id"]:
        raise ForbiddenException("不能删除自己")
    
    success = await AdminDB.delete_user(user_id)
    
    if not success:
        raise NotFoundException("用户不存在", ErrorCode.USER_NOT_FOUND)
    
    return {
        "message": "用户已删除",
        "user_id": user_id
    }


@router.get("/stats", response_model=SystemStats)
async def get_system_stats(admin: dict = Depends(require_admin)):
    """
    获取系统统计
    
    Args:
        admin: 管理员用户
        
    Returns:
        SystemStats: 系统统计
    """
    stats = await AdminDB.get_system_stats()
    
    return SystemStats(**stats)


@router.get("/settings", response_model=SystemSettings)
async def get_system_settings(admin: dict = Depends(require_admin)):
    """
    获取系统设置
    
    Args:
        admin: 管理员用户
        
    Returns:
        SystemSettings: 系统设置
    """
    settings = await AdminDB.get_all_settings()
    
    return SystemSettings(
        allow_registration=settings.get("allow_registration", "true") == "true",
        default_analysis_style=settings.get("default_analysis_style", "balanced"),
        max_tasks_per_user=int(settings.get("max_tasks_per_user", "100")),
        max_teams_per_user=int(settings.get("max_teams_per_user", "10")),
        maintenance_mode=settings.get("maintenance_mode", "false") == "true"
    )


@router.put("/settings", response_model=SystemSettings)
async def update_system_settings(
    settings_data: SettingsUpdateRequest,
    admin: dict = Depends(require_admin)
):
    """
    更新系统设置
    
    Args:
        settings_data: 设置数据
        admin: 管理员用户
        
    Returns:
        SystemSettings: 更新后的设置
    """
    if settings_data.allow_registration is not None:
        await AdminDB.set_setting(
            "allow_registration",
            "true" if settings_data.allow_registration else "false",
            "是否允许新用户注册"
        )
    
    if settings_data.default_analysis_style is not None:
        await AdminDB.set_setting(
            "default_analysis_style",
            settings_data.default_analysis_style,
            "默认分析风格"
        )
    
    if settings_data.max_tasks_per_user is not None:
        await AdminDB.set_setting(
            "max_tasks_per_user",
            str(settings_data.max_tasks_per_user),
            "每用户最大任务数"
        )
    
    if settings_data.max_teams_per_user is not None:
        await AdminDB.set_setting(
            "max_teams_per_user",
            str(settings_data.max_teams_per_user),
            "每用户最大团队数"
        )
    
    if settings_data.maintenance_mode is not None:
        await AdminDB.set_setting(
            "maintenance_mode",
            "true" if settings_data.maintenance_mode else "false",
            "维护模式"
        )
    
    return await get_system_settings(admin)
