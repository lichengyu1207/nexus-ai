"""
管理员后台API路由
"""
import time
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from fastapi import APIRouter, Request, HTTPException, Depends, Query, Body
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, EmailStr, Field

from ..services.admin.auth_service import (
    get_admin_auth_service,
    get_rbac_service,
    AdminAuthService,
    RBACService,
    AdminUser,
    AuthenticationError,
    PermissionDeniedError
)
from ..services.admin.core_services import (
    get_admin_user_service,
    get_admin_audit_service,
    get_admin_config_service,
    AdminUserManagementService,
    AdminAuditService,
    AdminConfigService,
    UserListParams
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["Admin"])


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    admin: Dict[str, Any]


class UserUpdateRequest(BaseModel):
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    status: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ConfigUpdateRequest(BaseModel):
    value: Any
    value_type: str = "string"


class PointsAdjustRequest(BaseModel):
    points: int
    reason: str


async def get_current_admin(
    request: Request,
    auth_service: AdminAuthService = Depends(get_admin_auth_service)
) -> AdminUser:
    """获取当前管理员"""
    auth_header = request.headers.get("Authorization")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未提供认证令牌")
    
    token = auth_header[7:]
    
    admin = await auth_service.validate_token(token)
    
    if not admin:
        raise HTTPException(status_code=401, detail="无效或过期的令牌")
    
    return admin


def require_permission(resource: str, action: str):
    """权限检查装饰器"""
    async def check_permission(
        admin: AdminUser = Depends(get_current_admin),
        rbac: RBACService = Depends(get_rbac_service)
    ):
        if not await rbac.check_permission(admin, resource, action):
            raise HTTPException(
                status_code=403,
                detail=f"没有权限执行此操作: {resource}:{action}"
            )
        return admin
    return check_permission


@router.post("/login", response_model=LoginResponse)
async def admin_login(
    request: LoginRequest,
    req: Request,
    auth_service: AdminAuthService = Depends(get_admin_auth_service)
):
    """管理员登录"""
    try:
        result = await auth_service.authenticate(
            username=request.username,
            password=request.password,
            ip_address=req.client.host if req.client else None,
            user_agent=req.headers.get("User-Agent")
        )
        
        return LoginResponse(**result)
    
    except AuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/logout")
async def admin_logout(
    req: Request,
    admin: AdminUser = Depends(get_current_admin),
    auth_service: AdminAuthService = Depends(get_admin_auth_service)
):
    """管理员登出"""
    auth_header = req.headers.get("Authorization")
    token = auth_header[7:] if auth_header else None
    
    if token:
        await auth_service.logout(token)
    
    return {"status": "logged_out"}


@router.post("/refresh")
async def refresh_token(
    refresh_token: str = Body(..., embed=True),
    auth_service: AdminAuthService = Depends(get_admin_auth_service)
):
    """刷新令牌"""
    try:
        result = await auth_service.refresh_token(refresh_token)
        return result
    except AuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/me")
async def get_current_admin_info(
    admin: AdminUser = Depends(get_current_admin)
):
    """获取当前管理员信息"""
    return {
        "id": admin.id,
        "username": admin.username,
        "email": admin.email,
        "role": admin.role,
        "permissions": admin.permissions,
        "is_superuser": admin.is_superuser
    }


@router.get("/health")
async def admin_health():
    """管理员后台健康检查"""
    return {
        "status": "healthy",
        "service": "admin-backend",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/users")
async def get_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    role: Optional[str] = None,
    status: Optional[str] = None,
    admin: AdminUser = Depends(require_permission("user", "read")),
    user_service: AdminUserManagementService = Depends(get_admin_user_service)
):
    """获取用户列表"""
    params = UserListParams(
        page=page,
        page_size=page_size,
        search=search,
        role=role,
        status=status
    )
    
    result = await user_service.get_user_list(params)
    
    return {
        "users": result.users,
        "total": result.total,
        "page": result.page,
        "page_size": result.page_size,
        "total_pages": result.total_pages
    }


@router.get("/users/{user_id}")
async def get_user_detail(
    user_id: str,
    admin: AdminUser = Depends(require_permission("user", "read")),
    user_service: AdminUserManagementService = Depends(get_admin_user_service)
):
    """获取用户详情"""
    user = await user_service.get_user_detail(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return user


@router.put("/users/{user_id}")
async def update_user(
    user_id: str,
    updates: UserUpdateRequest,
    admin: AdminUser = Depends(require_permission("user", "update")),
    user_service: AdminUserManagementService = Depends(get_admin_user_service)
):
    """更新用户"""
    update_data = updates.dict(exclude_unset=True)
    
    if not update_data:
        raise HTTPException(status_code=400, detail="没有提供更新数据")
    
    try:
        result = await user_service.update_user(user_id, admin, update_data)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    role: str = Body(..., embed=True),
    admin: AdminUser = Depends(require_permission("user", "update")),
    user_service: AdminUserManagementService = Depends(get_admin_user_service)
):
    """更新用户角色"""
    try:
        result = await user_service.update_user_role(user_id, role, admin)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/users/{user_id}/suspend")
async def suspend_user(
    user_id: str,
    reason: str = Body(..., embed=True),
    admin: AdminUser = Depends(require_permission("user", "update")),
    user_service: AdminUserManagementService = Depends(get_admin_user_service)
):
    """暂停用户"""
    result = await user_service.suspend_user(user_id, reason, admin)
    return result


@router.post("/users/{user_id}/activate")
async def activate_user(
    user_id: str,
    admin: AdminUser = Depends(require_permission("user", "update")),
    user_service: AdminUserManagementService = Depends(get_admin_user_service)
):
    """激活用户"""
    result = await user_service.activate_user(user_id, admin)
    return result


@router.post("/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: str,
    new_password: str = Body(..., embed=True),
    admin: AdminUser = Depends(require_permission("user", "update")),
    user_service: AdminUserManagementService = Depends(get_admin_user_service)
):
    """重置用户密码"""
    result = await user_service.reset_user_password(user_id, new_password, admin)
    return {"status": "success", "message": "密码已重置"}


@router.post("/users/{user_id}/points")
async def adjust_user_points(
    user_id: str,
    request: PointsAdjustRequest,
    admin: AdminUser = Depends(require_permission("user", "update")),
    user_service: AdminUserManagementService = Depends(get_admin_user_service)
):
    """调整用户积分"""
    try:
        result = await user_service.adjust_user_points(
            user_id, request.points, request.reason, admin
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/audit-logs")
async def get_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    admin_id: Optional[str] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    admin: AdminUser = Depends(require_permission("audit", "read")),
    audit_service: AdminAuditService = Depends(get_admin_audit_service)
):
    """获取审计日志"""
    result = await audit_service.get_audit_logs(
        page=page,
        page_size=page_size,
        admin_id=admin_id,
        action=action,
        resource_type=resource_type,
        start_date=start_date,
        end_date=end_date
    )
    
    return result


@router.get("/audit-logs/stats")
async def get_audit_stats(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    admin: AdminUser = Depends(require_permission("audit", "read")),
    audit_service: AdminAuditService = Depends(get_admin_audit_service)
):
    """获取审计统计"""
    result = await audit_service.get_audit_stats(start_date, end_date)
    return result


@router.get("/audit-logs/export")
async def export_audit_logs(
    start_date: datetime,
    end_date: datetime,
    format: str = Query("json", regex="^(json|csv)$"),
    admin: AdminUser = Depends(require_permission("audit", "read")),
    audit_service: AdminAuditService = Depends(get_admin_audit_service)
):
    """导出审计日志"""
    content = await audit_service.export_audit_logs(start_date, end_date, format)
    
    if format == "csv":
        return PlainTextResponse(
            content=content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=audit_logs_{start_date.date()}_{end_date.date()}.csv"
            }
        )
    
    return PlainTextResponse(
        content=content,
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=audit_logs_{start_date.date()}_{end_date.date()}.json"
        }
    )


@router.get("/configs")
async def get_configs(
    admin: AdminUser = Depends(require_permission("config", "read")),
    config_service: AdminConfigService = Depends(get_admin_config_service)
):
    """获取所有配置"""
    configs = await config_service.get_all_configs()
    return {"configs": configs}


@router.get("/configs/{key}")
async def get_config(
    key: str,
    admin: AdminUser = Depends(require_permission("config", "read")),
    config_service: AdminConfigService = Depends(get_admin_config_service)
):
    """获取单个配置"""
    config = await config_service.get_config(key)
    
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    return config


@router.put("/configs/{key}")
async def set_config(
    key: str,
    request: ConfigUpdateRequest,
    admin: AdminUser = Depends(require_permission("config", "update")),
    config_service: AdminConfigService = Depends(get_admin_config_service)
):
    """设置配置"""
    result = await config_service.set_config(
        key, request.value, admin, request.value_type
    )
    return result


@router.delete("/configs/{key}")
async def delete_config(
    key: str,
    admin: AdminUser = Depends(require_permission("config", "update")),
    config_service: AdminConfigService = Depends(get_admin_config_service)
):
    """删除配置"""
    result = await config_service.delete_config(key, admin)
    
    if not result:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    return {"status": "deleted"}


@router.get("/roles")
async def get_roles(
    admin: AdminUser = Depends(require_permission("role", "read")),
    rbac: RBACService = Depends(get_rbac_service)
):
    """获取所有角色"""
    roles = await rbac.get_all_roles()
    return {"roles": roles}


@router.get("/permissions")
async def get_permissions(
    admin: AdminUser = Depends(require_permission("role", "read")),
    rbac: RBACService = Depends(get_rbac_service)
):
    """获取所有权限"""
    permissions = await rbac.get_all_permissions()
    return {"permissions": permissions}


def include_router(app):
    """将路由包含到FastAPI应用"""
    app.include_router(router)
