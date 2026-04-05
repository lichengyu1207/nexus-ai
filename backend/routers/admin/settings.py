"""
管理员系统设置API路由
提供系统设置的查看和修改功能
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

from ...auth import require_admin, require_super_admin
from ...utils.settings import (
    get_setting,
    set_setting,
    set_settings,
    get_all_settings_grouped,
    get_settings_by_group,
    get_setting_definition,
    get_setting_groups,
    get_all_setting_keys,
    validate_setting_value,
    clear_settings_cache,
    load_settings_cache,
)
from ...exceptions import BadRequestException, NotFoundException, ErrorCode

router = APIRouter(prefix="/api/admin/settings", tags=["admin-settings"])


class SettingValue(BaseModel):
    """设置值模型"""
    key: str = Field(..., description="设置键")
    value: Any = Field(..., description="设置值")


class SettingsUpdateRequest(BaseModel):
    """批量更新设置请求"""
    settings: Dict[str, Any] = Field(..., description="设置字典")


class SettingResponse(BaseModel):
    """单个设置响应"""
    key: str
    value: Any
    type: str
    description: str
    group: Optional[str] = None
    options: Optional[List[str]] = None
    min: Optional[int] = None
    max: Optional[int] = None


class GroupedSettingsResponse(BaseModel):
    """分组设置响应"""
    groups: Dict[str, Dict[str, SettingResponse]]


class SettingGroupResponse(BaseModel):
    """设置分组响应"""
    group: str
    settings: Dict[str, SettingResponse]


class SettingUpdateResponse(BaseModel):
    """设置更新响应"""
    message: str
    updated: Dict[str, bool]
    errors: Optional[Dict[str, str]] = None


def dict_to_response(key: str, data: dict) -> SettingResponse:
    """将设置字典转换为响应模型"""
    return SettingResponse(
        key=key,
        value=data.get("value"),
        type=data.get("type", "string"),
        description=data.get("description", ""),
        group=data.get("group"),
        options=data.get("options"),
        min=data.get("min"),
        max=data.get("max")
    )


@router.get("", response_model=GroupedSettingsResponse)
async def get_all_settings(admin: dict = Depends(require_admin)):
    """
    获取所有系统设置（按分组）
    
    Args:
        admin: 管理员用户
        
    Returns:
        GroupedSettingsResponse: 分组设置
    """
    grouped = await get_all_settings_grouped()
    
    result = {}
    for group_name, settings in grouped.items():
        result[group_name] = {
            key: dict_to_response(key, data)
            for key, data in settings.items()
        }
    
    return GroupedSettingsResponse(groups=result)


@router.get("/groups")
async def get_groups(admin: dict = Depends(require_admin)):
    """
    获取所有设置分组
    
    Args:
        admin: 管理员用户
        
    Returns:
        dict: 分组列表
    """
    groups = get_setting_groups()
    return {"groups": groups}


@router.get("/keys")
async def get_keys(admin: dict = Depends(require_admin)):
    """
    获取所有设置键
    
    Args:
        admin: 管理员用户
        
    Returns:
        dict: 设置键列表
    """
    keys = get_all_setting_keys()
    return {"keys": keys}


@router.get("/group/{group_name}", response_model=SettingGroupResponse)
async def get_settings_by_group_name(
    group_name: str,
    admin: dict = Depends(require_admin)
):
    """
    获取指定分组的设置
    
    Args:
        group_name: 分组名称
        admin: 管理员用户
        
    Returns:
        SettingGroupResponse: 分组设置
    """
    settings = await get_settings_by_group(group_name)
    
    if not settings:
        raise NotFoundException(f"分组 '{group_name}' 不存在", ErrorCode.NOT_FOUND)
    
    return SettingGroupResponse(
        group=group_name,
        settings={
            key: dict_to_response(key, data)
            for key, data in settings.items()
        }
    )


@router.get("/{key}", response_model=SettingResponse)
async def get_single_setting(
    key: str,
    admin: dict = Depends(require_admin)
):
    """
    获取单个设置
    
    Args:
        key: 设置键
        admin: 管理员用户
        
    Returns:
        SettingResponse: 设置详情
    """
    definition = get_setting_definition(key)
    
    if not definition:
        raise NotFoundException(f"设置 '{key}' 不存在", ErrorCode.NOT_FOUND)
    
    value = await get_setting(key, definition.get("value"))
    
    return dict_to_response(key, {
        "value": value,
        **definition
    })


@router.put("", response_model=SettingUpdateResponse)
async def update_settings(
    request: SettingsUpdateRequest,
    admin: dict = Depends(require_super_admin)
):
    """
    批量更新设置（仅超级管理员）
    
    Args:
        request: 更新请求
        admin: 超级管理员用户
        
    Returns:
        SettingUpdateResponse: 更新结果
    """
    errors = {}
    
    for key, value in request.settings.items():
        is_valid, error_msg = validate_setting_value(key, value)
        if not is_valid:
            errors[key] = error_msg
    
    if errors:
        raise BadRequestException(
            "设置验证失败",
            ErrorCode.VALIDATION_ERROR,
            details=[{"field": k, "message": v} for k, v in errors.items()]
        )
    
    results = await set_settings(request.settings)
    
    failed = {k: v for k, v in results.items() if not v}
    
    return SettingUpdateResponse(
        message=f"已更新 {sum(results.values())} 个设置" + (f"，{len(failed)} 个失败" if failed else ""),
        updated=results,
        errors=failed if failed else None
    )


@router.put("/{key}", response_model=SettingResponse)
async def update_single_setting(
    key: str,
    request: SettingValue,
    admin: dict = Depends(require_super_admin)
):
    """
    更新单个设置（仅超级管理员）
    
    Args:
        key: 设置键
        request: 设置值
        admin: 超级管理员用户
        
    Returns:
        SettingResponse: 更新后的设置
    """
    definition = get_setting_definition(key)
    
    if not definition:
        raise NotFoundException(f"设置 '{key}' 不存在", ErrorCode.NOT_FOUND)
    
    is_valid, error_msg = validate_setting_value(key, request.value)
    if not is_valid:
        raise BadRequestException(error_msg, ErrorCode.VALIDATION_ERROR)
    
    success = await set_setting(key, request.value)
    
    if not success:
        raise BadRequestException("更新设置失败", ErrorCode.OPERATION_FAILED)
    
    return dict_to_response(key, {
        "value": request.value,
        **definition
    })


@router.post("/reload-cache")
async def reload_cache(admin: dict = Depends(require_super_admin)):
    """
    重新加载设置缓存（仅超级管理员）
    
    Args:
        admin: 超级管理员用户
        
    Returns:
        dict: 操作结果
    """
    clear_settings_cache()
    await load_settings_cache()
    
    return {"message": "设置缓存已重新加载"}


@router.get("/check/registration")
async def check_registration():
    """
    检查是否允许注册（公开接口）
    
    Returns:
        dict: 是否允许注册
    """
    allowed = await get_setting("allow_registration", True)
    return {"allow_registration": allowed}


@router.get("/check/maintenance")
async def check_maintenance():
    """
    检查是否维护模式（公开接口）
    
    Returns:
        dict: 是否维护模式
    """
    maintenance = await get_setting("maintenance_mode", False)
    return {"maintenance_mode": maintenance}


@router.get("/public/info")
async def get_public_info():
    """
    获取公开的系统信息
    
    Returns:
        dict: 公开系统信息
    """
    site_name = await get_setting("site_name", "房都督AI")
    site_description = await get_setting("site_description", "智能房产分析与估值系统")
    contact_email = await get_setting("contact_email", "")
    
    return {
        "site_name": site_name,
        "site_description": site_description,
        "contact_email": contact_email
    }
