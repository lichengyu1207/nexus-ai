"""
Token计价系统API路由
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

from backend.auth import get_current_user, get_current_admin_user
from ..services.token_service import token_service

router = APIRouter(prefix="/api/token", tags=["Token计价"])


class TokenPreviewRequest(BaseModel):
    text: str = Field(..., description="输入文本")
    action_type: str = Field(default="dialogue", description="操作类型")


class TokenConsumeRequest(BaseModel):
    action_type: str = Field(..., description="操作类型")
    input_text: str = Field(default="", description="输入文本")
    output_text: str = Field(default="", description="输出文本")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="额外元数据")


class PricingRuleUpdate(BaseModel):
    pricing_type: Optional[str] = Field(None, description="定价类型: fixed/dynamic")
    fixed_cost: Optional[int] = Field(None, description="固定消耗")
    input_multiplier: Optional[float] = Field(None, description="输入乘数")
    output_multiplier: Optional[float] = Field(None, description="输出乘数")
    description: Optional[str] = Field(None, description="规则描述")


class TokenReserveRequest(BaseModel):
    action_type: str = Field(..., description="操作类型")
    estimated_tokens: int = Field(..., ge=1, description="预估Token数量")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="额外元数据")


class TokenConfirmRequest(BaseModel):
    reservation_id: str = Field(..., description="预扣记录ID")
    actual_tokens: Optional[int] = Field(None, ge=1, description="实际Token数量（可选）")
    input_text: Optional[str] = Field(default="", description="输入文本")
    output_text: Optional[str] = Field(default="", description="输出文本")


class TokenRollbackRequest(BaseModel):
    reservation_id: str = Field(..., description="预扣记录ID")
    reason: Optional[str] = Field(default="业务失败", description="回滚原因")


@router.post("/preview")
async def preview_token_cost(
    request: TokenPreviewRequest,
    user: dict = Depends(get_current_user)
):
    """
    预览Token消耗
    
    前端输入框实时显示预计消耗
    """
    result = await token_service.preview_consumption(
        text=request.text,
        action_type=request.action_type
    )
    return result


@router.get("/balance")
async def get_token_balance(
    user: dict = Depends(get_current_user)
):
    """
    获取用户Token余额
    
    返回积分和Token余额
    """
    balance = await token_service.get_user_balance(user["id"])
    return balance


@router.post("/consume")
async def consume_tokens(
    request: TokenConsumeRequest,
    user: dict = Depends(get_current_user)
):
    """
    消耗Token（内部调用）
    
    各业务模块在正式处理时调用，扣除积分并记录日志
    """
    result = await token_service.consume_tokens(
        user_id=user["id"],
        action_type=request.action_type,
        input_text=request.input_text,
        output_text=request.output_text,
        metadata=request.metadata
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "消耗失败")
        )
    
    return result


@router.get("/history")
async def get_consumption_history(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    action_type: Optional[str] = Query(default=None),
    user: dict = Depends(get_current_user)
):
    """
    获取消费记录
    
    用户查看自己的消费历史
    """
    result = await token_service.get_consumption_history(
        user_id=user["id"],
        limit=limit,
        offset=offset,
        action_type=action_type
    )
    return result


@router.get("/rules")
async def get_pricing_rules(
    user: dict = Depends(get_current_user)
):
    """
    获取所有定价规则
    
    用户可查看定价规则
    """
    rules = await token_service.get_all_pricing_rules()
    return {"rules": rules}


@router.put("/rules/{action_type}")
async def update_pricing_rule(
    action_type: str,
    request: PricingRuleUpdate,
    admin: dict = Depends(get_current_admin_user)
):
    """
    更新定价规则（管理员）
    
    仅管理员可修改定价规则
    """
    success = await token_service.update_pricing_rule(
        action_type=action_type,
        pricing_type=request.pricing_type,
        fixed_cost=request.fixed_cost,
        input_multiplier=request.input_multiplier,
        output_multiplier=request.output_multiplier,
        description=request.description
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="更新失败")
    
    return {"success": True, "message": "定价规则已更新"}


@router.get("/stats")
async def get_consumption_stats(
    start_date: Optional[str] = Query(default=None),
    end_date: Optional[str] = Query(default=None),
    admin: dict = Depends(get_current_admin_user)
):
    """
    获取消耗统计（管理员）
    
    返回总消耗、按操作类型分布、每日趋势等
    """
    stats = await token_service.get_consumption_stats(
        start_date=start_date,
        end_date=end_date
    )
    return stats


@router.post("/reserve")
async def reserve_tokens(
    request: TokenReserveRequest,
    user: dict = Depends(get_current_user)
):
    """
    预扣Token（两阶段消耗第一阶段）
    
    在业务执行前预先扣除估算的Token，返回reservation_id
    业务成功后调用/confirm确认，失败则调用/rollback回滚
    """
    result = await token_service.reserve_tokens(
        user_id=user["id"],
        action_type=request.action_type,
        estimated_tokens=request.estimated_tokens,
        metadata=request.metadata
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "预扣失败")
        )
    
    return result


@router.post("/confirm")
async def confirm_consumption(
    request: TokenConfirmRequest,
    user: dict = Depends(get_current_user)
):
    """
    确认消耗（两阶段消耗第二阶段）
    
    业务成功后确认实际消耗，多退少补
    """
    result = await token_service.confirm_consumption(
        reservation_id=request.reservation_id,
        actual_tokens=request.actual_tokens,
        input_text=request.input_text or "",
        output_text=request.output_text or ""
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "确认失败")
        )
    
    return result


@router.post("/rollback")
async def rollback_reservation(
    request: TokenRollbackRequest,
    user: dict = Depends(get_current_user)
):
    """
    回滚预扣（业务失败时退还）
    
    业务失败时退还预扣的Token，并发送站内信通知用户
    """
    result = await token_service.rollback_reservation(
        reservation_id=request.reservation_id,
        reason=request.reason or "业务失败"
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "回滚失败")
        )
    
    return result


@router.get("/action-types")
async def get_action_types():
    """
    获取所有操作类型
    
    返回系统支持的所有操作类型及其说明
    """
    return {
        "action_types": [
            {
                "type": "task_create",
                "name": "创建任务",
                "description": "创建分析任务固定消耗5 token",
                "pricing_type": "fixed"
            },
            {
                "type": "consult_query",
                "name": "咨询对话",
                "description": "输入token + 输出token*0.5",
                "pricing_type": "dynamic"
            },
            {
                "type": "report_generate",
                "name": "报告生成",
                "description": "生成内容token*0.1",
                "pricing_type": "dynamic"
            },
            {
                "type": "export_pdf",
                "name": "导出PDF",
                "description": "固定消耗2 token",
                "pricing_type": "fixed"
            },
            {
                "type": "dialogue",
                "name": "智能咨询",
                "description": "输入token + 输出token*0.3",
                "pricing_type": "dynamic"
            }
        ]
    }
