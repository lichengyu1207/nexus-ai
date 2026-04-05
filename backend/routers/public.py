"""
系统配置和公共API路由
"""
from fastapi import APIRouter
from typing import Dict, Any

router = APIRouter(tags=["public"])

@router.get("/api/config")
async def get_config() -> Dict[str, Any]:
    """获取系统公开配置"""
    return {
        "site_name": "房产AI估值系统",
        "site_description": "专业的房产估值分析平台",
        "version": "1.0.0",
        "features": {
            "ai_valuation": True,
            "map_visualization": True,
            "team_collaboration": True,
            "report_export": True
        },
        "contact": {
            "email": "support@example.com",
            "phone": "400-123-4567"
        },
        "social": {
            "wechat": "property_ai",
            "weibo": "@房产AI估值"
        }
    }

@router.get("/api/banners")
async def get_banners() -> list:
    """获取首页轮播图"""
    return [
        {
            "id": "1",
            "title": "AI智能估值",
            "description": "基于大数据和AI技术的精准房产估值",
            "image": "/images/banner1.jpg",
            "link": "/valuation",
            "order": 1
        },
        {
            "id": "2", 
            "title": "团队协作",
            "description": "邀请团队成员，共享估值报告",
            "image": "/images/banner2.jpg",
            "link": "/teams",
            "order": 2
        },
        {
            "id": "3",
            "title": "专业报告",
            "description": "一键生成专业估值分析报告",
            "image": "/images/banner3.jpg",
            "link": "/reports",
            "order": 3
        }
    ]
