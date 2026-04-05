"""
配置管理路由
处理配置变更请求和管理
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
from pydantic import BaseModel

from backend.config.config_manager import (
    get_config_manager,
    submit_config_change,
    rollback_config,
    get_current_config
)

router = APIRouter(prefix="/api/config", tags=["config"])


class ConfigChangeRequest(BaseModel):
    """配置变更请求"""
    config_data: Dict[str, Any]
    description: str = ""


class RollbackRequest(BaseModel):
    """回滚请求"""
    version_id: str
    reason: str


class ConfigVersionResponse(BaseModel):
    """配置版本响应"""
    version_id: str
    config_data: Dict[str, Any]
    created_at: str
    status: str
    description: str
    change_summary: Dict[str, Any]


class RollbackResponse(BaseModel):
    """回滚响应"""
    rollback_id: str
    target_version_id: str
    status: str
    started_at: str
    completed_at: str = None
    error_message: str = None


class ConfigStatusResponse(BaseModel):
    """配置状态响应"""
    current_version: str = None
    config_data: Dict[str, Any] = None
    versions: List[ConfigVersionResponse] = []


@router.post("/change", response_model=ConfigVersionResponse)
async def submit_config_change_endpoint(request: ConfigChangeRequest):
    """提交配置变更"""
    try:
        version = await submit_config_change(request.config_data, request.description)
        return ConfigVersionResponse(
            version_id=version.version_id,
            config_data=version.config_data,
            created_at=version.created_at.isoformat(),
            status=version.status.value,
            description=version.description,
            change_summary=version.change_summary
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit config change: {str(e)}")


@router.post("/rollback", response_model=RollbackResponse)
async def rollback_config_endpoint(request: RollbackRequest):
    """回滚配置"""
    try:
        rollback = await rollback_config(request.version_id, request.reason)
        return RollbackResponse(
            rollback_id=rollback.rollback_id,
            target_version_id=rollback.target_version_id,
            status=rollback.status.value,
            started_at=rollback.started_at.isoformat(),
            completed_at=rollback.completed_at.isoformat() if rollback.completed_at else None,
            error_message=rollback.error_message
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to rollback config: {str(e)}")


@router.get("/status", response_model=ConfigStatusResponse)
async def get_config_status():
    """获取配置状态"""
    manager = get_config_manager()
    current_version = manager.get_current_version()
    versions = manager.list_versions()
    
    version_responses = []
    for version in versions:
        version_responses.append(ConfigVersionResponse(
            version_id=version.version_id,
            config_data=version.config_data,
            created_at=version.created_at.isoformat(),
            status=version.status.value,
            description=version.description,
            change_summary=version.change_summary
        ))
    
    return ConfigStatusResponse(
        current_version=current_version.version_id if current_version else None,
        config_data=current_version.config_data if current_version else None,
        versions=version_responses
    )


@router.get("/current")
async def get_current_config_endpoint():
    """获取当前配置"""
    config = get_current_config()
    if config is None:
        raise HTTPException(status_code=404, detail="No current config found")
    return config


@router.get("/versions")
async def list_config_versions():
    """列出所有配置版本"""
    manager = get_config_manager()
    versions = manager.list_versions()
    return [
        {
            "version_id": v.version_id,
            "created_at": v.created_at.isoformat(),
            "status": v.status.value,
            "description": v.description
        }
        for v in versions
    ]


@router.get("/rollback-history")
async def get_rollback_history():
    """获取回滚历史"""
    manager = get_config_manager()
    history = manager.get_rollback_history()
    return [
        {
            "rollback_id": r.rollback_id,
            "target_version_id": r.target_version_id,
            "status": r.status.value,
            "started_at": r.started_at.isoformat(),
            "completed_at": r.completed_at.isoformat() if r.completed_at else None,
            "error_message": r.error_message
        }
        for r in history
    ]
