"""
用户积分API路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from backend.models import (
    UserIntegralResponse,
    IntegralLogListResponse,
    IntegralLogResponse,
    IntegralPackage,
    MembershipPlan
)
from backend.services.integral import IntegralService
from backend.services.user_source import get_user_source, get_source_config
from backend.routers.auth import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/user", tags=["integral"])


INTEGRAL_PACKAGES = [
    IntegralPackage(
        id="starter",
        name="体验包",
        integral=10,
        price=19.0,
        unit_price=1.9,
        description="适合初次体验用户",
        is_popular=False
    ),
    IntegralPackage(
        id="standard",
        name="标准包",
        integral=30,
        price=49.0,
        unit_price=1.63,
        description="最受欢迎的选择",
        is_popular=True
    ),
    IntegralPackage(
        id="professional",
        name="专业包",
        integral=100,
        price=149.0,
        unit_price=1.49,
        description="专业投资者首选",
        is_popular=False
    ),
    IntegralPackage(
        id="enterprise",
        name="企业包",
        integral=500,
        price=599.0,
        unit_price=1.20,
        description="企业级批量分析",
        is_popular=False
    ),
]

MEMBERSHIP_PLANS = [
    MembershipPlan(
        id="professional",
        name="专业版会员",
        price=199.0,
        duration_months=1,
        description="无限次分析，专业数据报告",
        features=[
            "无限次房产分析",
            "详细市场数据报告",
            "专属客服支持",
            "优先功能更新"
        ]
    ),
    MembershipPlan(
        id="enterprise",
        name="企业版会员",
        price=499.0,
        duration_months=1,
        description="企业级服务，定制化报告",
        features=[
            "无限次房产分析",
            "定制化分析报告",
            "API接口调用",
            "专属客户经理",
            "数据导出功能"
        ]
    ),
]

FOUNDER_WECHAT = "svip6763"


@router.get("/integral", response_model=UserIntegralResponse)
async def get_user_integral(
    current_user: dict = Depends(get_current_user)
):
    """
    获取当前用户的积分信息
    
    返回积分余额、会员等级、会员到期时间及最近5条积分变动记录
    同时返回用户来源信息，用于显示差异化福利标识
    """
    user_id = current_user["id"]
    
    integral, membership_level, membership_expires, is_member = await IntegralService.get_user_integral(user_id)
    
    logs, _ = await IntegralService.get_user_logs(user_id, limit=5, offset=0)
    
    source = await get_user_source(user_id)
    source_config = get_source_config(source)
    
    return UserIntegralResponse(
        integral=integral,
        membership_level=membership_level,
        membership_expires=membership_expires,
        is_member=is_member,
        recent_logs=[IntegralLogResponse(**log) for log in logs],
        source=source,
        source_name=source_config.get("name"),
        bonus_label=source_config.get("bonus_label"),
        initial_integral=source_config.get("free_integral", 3)
    )


@router.get("/integral/logs", response_model=IntegralLogListResponse)
async def get_user_integral_logs(
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取当前用户的积分变动日志
    
    支持分页查询
    """
    user_id = current_user["id"]
    
    logs, total = await IntegralService.get_user_logs(user_id, limit=limit, offset=offset)
    
    return IntegralLogListResponse(
        logs=[IntegralLogResponse(**log) for log in logs],
        total=total,
        limit=limit,
        offset=offset
    )


@router.get("/integral/packages")
async def get_integral_packages():
    """
    获取积分套餐列表
    
    返回可购买的积分套餐及会员套餐
    """
    return {
        "integral_packages": [pkg.model_dump() for pkg in INTEGRAL_PACKAGES],
        "membership_plans": [plan.model_dump() for plan in MEMBERSHIP_PLANS],
        "contact": {
            "wechat": FOUNDER_WECHAT,
            "note": "添加客服微信，转账后为您充值"
        }
    }


@router.get("/integral/contact")
async def get_contact_info():
    """
    获取客服联系方式
    
    返回创始人微信号等信息
    """
    return {
        "wechat": FOUNDER_WECHAT,
        "note": "添加客服微信，转账后为您充值",
        "packages": [
            {"name": pkg.name, "integral": pkg.integral, "price": pkg.price}
            for pkg in INTEGRAL_PACKAGES
        ]
    }
