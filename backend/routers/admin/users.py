"""
管理员用户管理API路由
提供用户列表、创建、更新、删除等功能
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import secrets
import string

from ...auth import (
    get_current_user, 
    require_admin, 
    require_super_admin,
    get_password_hash,
    generate_user_id,
)
from ...database import AdminDB, UserDB, get_db_connection
from ...exceptions import ForbiddenException, NotFoundException, BadRequestException, ErrorCode
from ...services.audit_service import log_audit, ActionType, ResourceType, AuditStatus

router = APIRouter(prefix="/api/admin/users", tags=["admin-users"])


def get_client_info(request: Request):
    """获取客户端信息"""
    ip = request.client.host if request.client else None
    forwarded = request.headers.get('x-forwarded-for')
    if forwarded:
        ip = forwarded.split(',')[0].strip()
    user_agent = request.headers.get('user-agent', '')
    return ip, user_agent


class AdminUserCreate(BaseModel):
    """管理员创建用户请求"""
    email: EmailStr = Field(..., description="用户邮箱")
    password: Optional[str] = Field(None, min_length=6, max_length=50, description="密码（不提供则自动生成）")
    full_name: Optional[str] = Field(None, max_length=100, description="用户全名")
    role: str = Field(default="user", description="用户角色")
    send_invite: bool = Field(default=False, description="是否发送邀请邮件")


class AdminUserUpdate(BaseModel):
    """管理员更新用户请求"""
    email: Optional[EmailStr] = Field(None, description="用户邮箱")
    full_name: Optional[str] = Field(None, max_length=100, description="用户全名")
    role: Optional[str] = Field(None, description="用户角色")
    is_active: Optional[bool] = Field(None, description="是否激活")
    permissions: Optional[Dict[str, bool]] = Field(None, description="权限设置")


class AdminUserResponse(BaseModel):
    """管理员用户响应"""
    id: str
    username: str
    email: str
    full_name: Optional[str]
    avatar_url: Optional[str]
    role: str
    is_admin: bool
    is_active: bool
    permissions: Optional[Dict[str, bool]]
    created_at: Optional[str]
    updated_at: Optional[str]
    last_login: Optional[str] = None


class AdminUserListResponse(BaseModel):
    """用户列表响应"""
    users: List[AdminUserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class PasswordResetResponse(BaseModel):
    """密码重置响应"""
    message: str
    new_password: Optional[str] = None


class UserRoleUpdate(BaseModel):
    """角色更新请求"""
    role: str = Field(..., description="新角色")


class UserStatusUpdate(BaseModel):
    """状态更新请求"""
    is_active: bool = Field(..., description="是否激活")


def generate_random_password(length: int = 12) -> str:
    """生成随机密码"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password


def user_to_response(user: dict) -> AdminUserResponse:
    """将用户字典转换为响应模型"""
    permissions = user.get("permissions", "{}")
    if isinstance(permissions, str):
        try:
            permissions = json.loads(permissions)
        except:
            permissions = {}
    
    return AdminUserResponse(
        id=user["id"],
        username=user.get("username", ""),
        email=user["email"],
        full_name=user.get("full_name"),
        avatar_url=user.get("avatar_url"),
        role=user.get("role", "user"),
        is_admin=bool(user.get("is_admin")),
        is_active=bool(user.get("is_active", 1)),
        permissions=permissions,
        created_at=user.get("created_at"),
        updated_at=user.get("updated_at"),
        last_login=user.get("last_login")
    )


@router.get("", response_model=AdminUserListResponse)
async def list_users(
    search: Optional[str] = Query(None, description="搜索关键词"),
    role: Optional[str] = Query(None, description="角色过滤"),
    is_active: Optional[bool] = Query(None, description="状态过滤"),
    is_admin: Optional[bool] = Query(None, description="管理员过滤"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向 asc/desc"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    admin: dict = Depends(require_admin)
):
    """
    获取用户列表
    
    Args:
        search: 搜索关键词（邮箱、用户名、全名）
        role: 角色过滤
        is_active: 状态过滤
        is_admin: 管理员过滤
        sort_by: 排序字段
        sort_order: 排序方向
        page: 页码
        page_size: 每页数量
        admin: 管理员用户
        
    Returns:
        AdminUserListResponse: 用户列表
    """
    offset = (page - 1) * page_size
    
    users = await AdminDB.get_all_users(
        limit=page_size,
        offset=offset,
        search=search,
        is_admin=is_admin
    )
    
    if role:
        users = [u for u in users if u.get("role") == role]
    
    if is_active is not None:
        users = [u for u in users if bool(u.get("is_active", 1)) == is_active]
    
    total = await AdminDB.get_users_count(search=search, is_admin=is_admin)
    
    if role or is_active is not None:
        total = len(users)
    
    total_pages = (total + page_size - 1) // page_size
    
    return AdminUserListResponse(
        users=[user_to_response(u) for u in users],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.post("", response_model=AdminUserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: AdminUserCreate,
    admin: dict = Depends(require_super_admin),
    request: Request = None
):
    """
    创建新用户（仅超级管理员）
    
    Args:
        user_data: 用户数据
        admin: 超级管理员用户
        request: 请求对象
        
    Returns:
        AdminUserResponse: 创建的用户
    """
    admin_id = admin["id"]
    ip, user_agent = get_client_info(request) if request else (None, None)
    
    valid_roles = ["user", "admin", "super_admin"]
    if user_data.role not in valid_roles:
        raise BadRequestException(
            f"无效的角色，可选值: {', '.join(valid_roles)}",
            ErrorCode.VALIDATION_ERROR
        )
    
    existing = await UserDB.get_user_by_email(user_data.email)
    if existing:
        log_audit(
            action_type=ActionType.ADMIN_USER_CREATE,
            user_id=admin_id,
            username=admin.get("email"),
            ip_address=ip,
            user_agent=user_agent,
            resource_type=ResourceType.USER,
            status=AuditStatus.FAILURE,
            error_message="邮箱已被注册",
        )
        raise BadRequestException("该邮箱已被注册", ErrorCode.ALREADY_EXISTS)
    
    password = user_data.password or generate_random_password()
    hashed_password = get_password_hash(password)
    user_id = generate_user_id()
    username = user_data.email.split("@")[0]
    
    is_admin_flag = 1 if user_data.role in ("admin", "super_admin") else 0
    
    await UserDB.create_user(
        user_id=user_id,
        username=username,
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        role=user_data.role
    )
    
    if is_admin_flag:
        await AdminDB.set_user_admin(user_id, True)
        if user_data.role == "super_admin":
            await AdminDB.set_user_role(user_id, "super_admin")
    
    user = await UserDB.get_user_by_id(user_id)
    
    log_audit(
        action_type=ActionType.ADMIN_USER_CREATE,
        user_id=admin_id,
        username=admin.get("email"),
        ip_address=ip,
        user_agent=user_agent,
        resource_type=ResourceType.USER,
        resource_id=user_id,
        new_value={"email": user_data.email, "role": user_data.role, "full_name": user_data.full_name},
        status=AuditStatus.SUCCESS,
    )
    
    if user_data.send_invite:
        pass
    
    return user_to_response(user)


@router.get("/source-stats")
async def get_user_source_stats(admin: dict = Depends(require_admin)):
    """
    获取用户来源统计
    
    Args:
        admin: 管理员用户
        
    Returns:
        dict: 用户来源统计
    """
    conn = await get_db_connection()
    try:
        cursor = await conn.execute("""
            SELECT source, COUNT(*) as count
            FROM users
            GROUP BY source
            ORDER BY count DESC
        """)
        rows = await cursor.fetchall()
        
        stats = []
        for row in rows:
            stats.append({
                "source": row["source"] or "direct",
                "count": row["count"]
            })
        
        return {
            "total": sum(s["count"] for s in stats),
            "sources": stats
        }
    finally:
        await conn.close()


@router.get("/{user_id}", response_model=AdminUserResponse)
async def get_user(
    user_id: str,
    admin: dict = Depends(require_admin)
):
    """
    获取单个用户详情
    
    Args:
        user_id: 用户ID
        admin: 管理员用户
        
    Returns:
        AdminUserResponse: 用户详情
    """
    user = await UserDB.get_user_by_id(user_id)
    
    if not user:
        raise NotFoundException("用户不存在", ErrorCode.USER_NOT_FOUND)
    
    return user_to_response(user)


@router.put("/{user_id}", response_model=AdminUserResponse)
async def update_user(
    user_id: str,
    update_data: AdminUserUpdate,
    admin: dict = Depends(require_super_admin),
    request: Request = None
):
    """
    更新用户信息（仅超级管理员）
    
    Args:
        user_id: 用户ID
        update_data: 更新数据
        admin: 超级管理员用户
        request: 请求对象
        
    Returns:
        AdminUserResponse: 更新后的用户
    """
    admin_id = admin["id"]
    ip, user_agent = get_client_info(request) if request else (None, None)
    
    if user_id == admin_id:
        raise ForbiddenException("不能修改自己的信息")
    
    user = await UserDB.get_user_by_id(user_id)
    if not user:
        raise NotFoundException("用户不存在", ErrorCode.USER_NOT_FOUND)
    
    old_value = {
        "email": user.get("email"),
        "full_name": user.get("full_name"),
        "role": user.get("role"),
        "is_active": bool(user.get("is_active", 1)),
    }
    new_value = {}
    
    if update_data.role:
        valid_roles = ["user", "admin", "super_admin"]
        if update_data.role not in valid_roles:
            raise BadRequestException(
                f"无效的角色，可选值: {', '.join(valid_roles)}",
                ErrorCode.VALIDATION_ERROR
            )
        await AdminDB.set_user_role(user_id, update_data.role)
        new_value["role"] = update_data.role
    
    if update_data.is_active is not None:
        await AdminDB.set_user_active(user_id, update_data.is_active)
        new_value["is_active"] = update_data.is_active
    
    if update_data.permissions is not None:
        await AdminDB.set_user_permissions(user_id, update_data.permissions)
        new_value["permissions"] = update_data.permissions
    
    if update_data.full_name is not None:
        await UserDB.update_profile(user_id, full_name=update_data.full_name)
        new_value["full_name"] = update_data.full_name
    
    if update_data.email is not None:
        existing = await UserDB.get_user_by_email(update_data.email)
        if existing and existing["id"] != user_id:
            raise BadRequestException("该邮箱已被使用", ErrorCode.ALREADY_EXISTS)
        conn = await UserDB._get_connection()
        await conn.execute(
            "UPDATE users SET email = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (update_data.email, user_id)
        )
        await conn.commit()
        new_value["email"] = update_data.email
    
    if new_value:
        log_audit(
            action_type=ActionType.ADMIN_USER_UPDATE,
            user_id=admin_id,
            username=admin.get("email"),
            ip_address=ip,
            user_agent=user_agent,
            resource_type=ResourceType.USER,
            resource_id=user_id,
            old_value=old_value,
            new_value=new_value,
            status=AuditStatus.SUCCESS,
        )
    
    updated_user = await UserDB.get_user_by_id(user_id)
    return user_to_response(updated_user)


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    hard_delete: bool = Query(False, description="是否硬删除"),
    admin: dict = Depends(require_super_admin),
    request: Request = None
):
    """
    删除用户（仅超级管理员）
    
    Args:
        user_id: 用户ID
        hard_delete: 是否硬删除（默认软删除）
        admin: 超级管理员用户
        request: 请求对象
        
    Returns:
        dict: 删除结果
    """
    admin_id = admin["id"]
    ip, user_agent = get_client_info(request) if request else (None, None)
    
    if user_id == admin_id:
        raise ForbiddenException("不能删除自己")
    
    user = await UserDB.get_user_by_id(user_id)
    if not user:
        raise NotFoundException("用户不存在", ErrorCode.USER_NOT_FOUND)
    
    if user.get("role") == "super_admin":
        raise ForbiddenException("不能删除超级管理员")
    
    old_value = {
        "email": user.get("email"),
        "role": user.get("role"),
        "is_active": bool(user.get("is_active", 1)),
    }
    
    if hard_delete:
        success = await AdminDB.delete_user(user_id)
        action = "硬删除"
    else:
        success = await AdminDB.set_user_active(user_id, False)
        action = "软删除（禁用）"
    
    if not success:
        log_audit(
            action_type=ActionType.ADMIN_USER_DELETE,
            user_id=admin_id,
            username=admin.get("email"),
            ip_address=ip,
            user_agent=user_agent,
            resource_type=ResourceType.USER,
            resource_id=user_id,
            status=AuditStatus.FAILURE,
            error_message=f"{action}失败",
        )
        raise BadRequestException("删除失败", ErrorCode.OPERATION_FAILED)
    
    log_audit(
        action_type=ActionType.ADMIN_USER_DELETE,
        user_id=admin_id,
        username=admin.get("email"),
        ip_address=ip,
        user_agent=user_agent,
        resource_type=ResourceType.USER,
        resource_id=user_id,
        old_value=old_value,
        new_value={"action": action, "hard_delete": hard_delete},
        status=AuditStatus.SUCCESS,
    )
    
    return {
        "message": f"用户已{action}",
        "user_id": user_id,
        "hard_delete": hard_delete
    }


@router.post("/{user_id}/reset-password", response_model=PasswordResetResponse)
async def reset_user_password(
    user_id: str,
    send_email: bool = Query(False, description="是否发送邮件通知"),
    admin: dict = Depends(require_super_admin)
):
    """
    重置用户密码（仅超级管理员）
    
    Args:
        user_id: 用户ID
        send_email: 是否发送邮件通知
        admin: 超级管理员用户
        
    Returns:
        PasswordResetResponse: 重置结果
    """
    if user_id == admin["id"]:
        raise ForbiddenException("不能重置自己的密码")
    
    user = await UserDB.get_user_by_id(user_id)
    if not user:
        raise NotFoundException("用户不存在", ErrorCode.USER_NOT_FOUND)
    
    new_password = generate_random_password()
    hashed_password = get_password_hash(new_password)
    
    conn = await UserDB._get_connection()
    await conn.execute(
        "UPDATE users SET hashed_password = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (hashed_password, user_id)
    )
    await conn.commit()
    
    if send_email:
        pass
    
    return PasswordResetResponse(
        message="密码已重置",
        new_password=new_password if not send_email else None
    )


@router.put("/{user_id}/role")
async def update_user_role(
    user_id: str,
    role_data: UserRoleUpdate,
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
    
    valid_roles = ["user", "admin", "super_admin"]
    if role_data.role not in valid_roles:
        raise BadRequestException(
            f"无效的角色，可选值: {', '.join(valid_roles)}",
            ErrorCode.VALIDATION_ERROR
        )
    
    user = await UserDB.get_user_by_id(user_id)
    if not user:
        raise NotFoundException("用户不存在", ErrorCode.USER_NOT_FOUND)
    
    if user.get("role") == "super_admin" and role_data.role != "super_admin":
        super_admins = await AdminDB.get_all_users(limit=1000)
        super_admin_count = sum(1 for u in super_admins if u.get("role") == "super_admin")
        if super_admin_count <= 1:
            raise ForbiddenException("系统必须至少保留一个超级管理员")
    
    success = await AdminDB.set_user_role(user_id, role_data.role)
    
    if not success:
        raise BadRequestException("更新角色失败", ErrorCode.OPERATION_FAILED)
    
    return {
        "message": "角色已更新",
        "user_id": user_id,
        "new_role": role_data.role
    }


@router.put("/{user_id}/status")
async def update_user_status(
    user_id: str,
    status_data: UserStatusUpdate,
    admin: dict = Depends(require_admin)
):
    """
    更新用户状态（启用/禁用）
    
    Args:
        user_id: 用户ID
        status_data: 状态数据
        admin: 管理员用户
        
    Returns:
        dict: 更新结果
    """
    if user_id == admin["id"]:
        raise ForbiddenException("不能修改自己的状态")
    
    user = await UserDB.get_user_by_id(user_id)
    if not user:
        raise NotFoundException("用户不存在", ErrorCode.USER_NOT_FOUND)
    
    if user.get("role") == "super_admin" and not status_data.is_active:
        raise ForbiddenException("不能禁用超级管理员")
    
    success = await AdminDB.set_user_active(user_id, status_data.is_active)
    
    if not success:
        raise BadRequestException("更新状态失败", ErrorCode.OPERATION_FAILED)
    
    return {
        "message": "状态已更新",
        "user_id": user_id,
        "is_active": status_data.is_active
    }


@router.get("/{user_id}/activity")
async def get_user_activity(
    user_id: str,
    admin: dict = Depends(require_admin)
):
    """
    获取用户活动记录
    
    Args:
        user_id: 用户ID
        admin: 管理员用户
        
    Returns:
        dict: 用户活动记录
    """
    from ...database import AuditDB
    
    user = await UserDB.get_user_by_id(user_id)
    if not user:
        raise NotFoundException("用户不存在", ErrorCode.USER_NOT_FOUND)
    
    logs = await AuditDB.get_user_logs(user_id, limit=50)
    
    return {
        "user_id": user_id,
        "email": user["email"],
        "activity": logs
    }
