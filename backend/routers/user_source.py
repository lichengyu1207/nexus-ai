"""
用户来源API路由
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional, Dict, Any
from backend.services.user_source import (
    get_user_source, 
    get_source_config, 
    detect_source_from_url,
    UserSource
)
from backend.auth import get_current_user
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/user", tags=["user-source"])


class SourceInfoResponse(BaseModel):
    """用户来源信息响应"""
    source: str = Field(..., description="用户来源类型")
    name: str = Field(..., description="来源名称")
    welcome_message: str = Field(..., description="欢迎消息")
    free_integral: int = Field(..., description="免费积分数量")
    bonus_label: Optional[str] = Field(None, description="奖励标签")
    mascot_emotion: str = Field(..., description="吉祥物表情")
    mascot_message: str = Field(..., description="吉祥物消息")


class PreviewSourceResponse(BaseModel):
    """预览来源信息响应"""
    source: str
    config: Dict[str, Any]


@router.get("/source", response_model=SourceInfoResponse)
async def get_user_source_info(
    current_user: dict = Depends(get_current_user)
):
    """
    获取当前用户的来源信息
    
    返回用户来源配置，用于显示差异化的欢迎消息和吉祥物表情
    """
    user_id = current_user["id"]
    source = await get_user_source(user_id)
    config = get_source_config(source)
    
    return SourceInfoResponse(
        source=source,
        name=config.get("name", "用户"),
        welcome_message=config.get("welcome_message", "欢迎！"),
        free_integral=config.get("free_integral", 3),
        bonus_label=config.get("bonus_label"),
        mascot_emotion=config.get("mascot_emotion", "default"),
        mascot_message=config.get("mascot_message", "开始你的房产分析之旅吧！"),
    )


@router.get("/source/preview")
async def preview_source(
    source: str = Query(..., description="来源类型")
):
    """
    预览指定来源的配置
    
    用于测试不同来源的差异化体验
    """
    config = get_source_config(source)
    
    return PreviewSourceResponse(
        source=source,
        config=config
    )


@router.get("/source/detect")
async def detect_source(
    source: Optional[str] = Query(None, description="URL source参数"),
    ref: Optional[str] = Query(None, description="URL ref参数"),
    utm_source: Optional[str] = Query(None, description="UTM来源参数")
):
    """
    检测用户来源
    
    根据URL参数检测用户来源类型
    """
    params = {}
    if source:
        params["source"] = source
    if ref:
        params["ref"] = ref
    if utm_source:
        params["utm_source"] = utm_source
    
    detected_source = detect_source_from_url(params)
    config = get_source_config(detected_source)
    
    return {
        "detected_source": detected_source,
        "config": config
    }
