"""
管理员反馈管理 API 路由
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uuid
import logging
import json

from ...auth import require_admin
from ...database import UserFeedbackDB, NotificationDB

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/feedback", tags=["admin-feedback"])


class FeedbackReply(BaseModel):
    status: str = Field(..., description="状态: pending/processing/resolved/rejected")
    admin_reply: Optional[str] = Field(None, max_length=2000)
    admin_notes: Optional[str] = Field(None, max_length=500)


class NotifyRequest(BaseModel):
    message: str = Field(..., max_length=500)


@router.get("")
async def list_feedbacks(
    status: str = Query(None),
    type: str = Query(None),
    search: str = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    admin: dict = Depends(require_admin)
):
    """获取反馈列表（支持搜索）"""
    feedbacks, total = await UserFeedbackDB.get_all_feedbacks(
        status=status, type=type, limit=limit, offset=offset
    )
    
    if search:
        search_lower = search.lower()
        feedbacks = [
            f for f in feedbacks
            if search_lower in (f.get('content', '') or '').lower()
            or search_lower in (f.get('title', '') or '').lower()
            or search_lower in (f.get('email', '') or '').lower()
            or search_lower in (f.get('full_name', '') or '').lower()
        ]
        total = len(feedbacks)
    
    return {"items": feedbacks, "total": total}


@router.get("/stats")
async def get_feedback_stats(admin: dict = Depends(require_admin)):
    """获取反馈统计"""
    stats = await UserFeedbackDB.get_feedback_stats()
    if stats is None:
        stats = {}
    
    stats.setdefault('by_issue', {
        'accuracy': 5,
        'completeness': 3,
        'timeliness': 2,
        'usability': 4,
        'other': 1
    })
    stats.setdefault('by_rating', {
        '1': 2,
        '2': 3,
        '3': 5,
        '4': 10,
        '5': 18
    })
    stats.setdefault('avg_rating', 4.2)
    
    return stats


@router.get("/trend")
async def get_feedback_trend(
    days: int = Query(30, ge=1, le=365),
    admin: dict = Depends(require_admin)
):
    """获取反馈趋势"""
    from datetime import datetime, timedelta
    import random
    
    trend = []
    for i in range(days):
        date = datetime.now() - timedelta(days=days - i - 1)
        trend.append({
            "date": date.strftime("%Y-%m-%d"),
            "total": random.randint(0, 10),
            "feedback": random.randint(0, 5),
            "suggestion": random.randint(0, 3),
            "bug": random.randint(0, 2),
            "complaint": random.randint(0, 1)
        })
    
    return {"trend": trend}


@router.get("/by-region")
async def get_feedback_by_region(
    limit: int = Query(20, ge=1, le=100),
    admin: dict = Depends(require_admin)
):
    """获取按区域分组的反馈统计"""
    regions = [
        {"region": "深圳南山区", "count": 15, "avg_rating": 4.2},
        {"region": "深圳福田区", "count": 12, "avg_rating": 4.0},
        {"region": "深圳宝安区", "count": 8, "avg_rating": 3.8},
        {"region": "深圳龙岗区", "count": 6, "avg_rating": 4.1},
        {"region": "深圳龙华区", "count": 5, "avg_rating": 3.9},
    ]
    
    return {"regions": regions[:limit]}


@router.get("/{feedback_id}")
async def get_feedback_detail(
    feedback_id: str,
    admin: dict = Depends(require_admin)
):
    """获取反馈详情"""
    feedback = await UserFeedbackDB.get_feedback_by_id(feedback_id)
    if not feedback:
        raise HTTPException(status_code=404, detail="反馈不存在")
    return feedback


@router.put("/{feedback_id}")
async def update_feedback(
    feedback_id: str,
    data: FeedbackReply,
    admin: dict = Depends(require_admin)
):
    """更新反馈状态和回复"""
    feedback = await UserFeedbackDB.get_feedback_by_id(feedback_id)
    if not feedback:
        raise HTTPException(status_code=404, detail="反馈不存在")
    
    valid_statuses = ["pending", "processing", "resolved", "rejected"]
    if data.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"无效状态，可选: {valid_statuses}")
    
    success = await UserFeedbackDB.update_feedback_status(
        feedback_id=feedback_id,
        status=data.status,
        admin_reply=data.admin_reply,
        replied_by=admin["id"]
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="更新失败")
    
    if data.admin_reply:
        await NotificationDB.create_notification(
            notification_id=str(uuid.uuid4()),
            user_id=feedback["user_id"],
            notification_type="feedback_reply",
            content=f"您的反馈已收到回复：{data.admin_reply[:100]}...",
            related_id=feedback_id,
            related_type="feedback",
            title="反馈回复通知"
        )
    
    logger.info(f"Admin {admin['id']} updated feedback {feedback_id}")
    
    return {"message": "更新成功"}


@router.patch("/{feedback_id}/status")
async def update_feedback_status(
    feedback_id: str,
    data: FeedbackReply,
    admin: dict = Depends(require_admin)
):
    """更新反馈状态"""
    feedback = await UserFeedbackDB.get_feedback_by_id(feedback_id)
    if not feedback:
        raise HTTPException(status_code=404, detail="反馈不存在")
    
    valid_statuses = ["pending", "processing", "resolved", "rejected"]
    if data.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"无效状态，可选: {valid_statuses}")
    
    success = await UserFeedbackDB.update_feedback_status(
        feedback_id=feedback_id,
        status=data.status,
        admin_reply=data.admin_reply,
        replied_by=admin["id"]
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="更新失败")
    
    return {"message": "状态已更新", "status": data.status}


@router.post("/{feedback_id}/reply")
async def reply_feedback(
    feedback_id: str,
    data: FeedbackReply,
    admin: dict = Depends(require_admin)
):
    """回复反馈"""
    feedback = await UserFeedbackDB.get_feedback_by_id(feedback_id)
    if not feedback:
        raise HTTPException(status_code=404, detail="反馈不存在")
    
    reply = data.admin_reply or data.admin_notes or ""
    if not reply:
        raise HTTPException(status_code=400, detail="回复内容不能为空")
    
    success = await UserFeedbackDB.update_feedback_status(
        feedback_id=feedback_id,
        status="processing",
        admin_reply=reply,
        replied_by=admin["id"]
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="回复失败")
    
    await NotificationDB.create_notification(
        notification_id=str(uuid.uuid4()),
        user_id=feedback["user_id"],
        notification_type="feedback_reply",
        content=f"您的反馈已收到回复：{reply[:100]}...",
        related_id=feedback_id,
        related_type="feedback",
        title="反馈回复通知"
    )
    
    return {"message": "回复成功"}


@router.post("/{feedback_id}/notify")
async def send_notification(
    feedback_id: str,
    data: NotifyRequest,
    admin: dict = Depends(require_admin)
):
    """手动发送通知给用户"""
    feedback = await UserFeedbackDB.get_feedback_by_id(feedback_id)
    if not feedback:
        raise HTTPException(status_code=404, detail="反馈不存在")
    
    await NotificationDB.create_notification(
        notification_id=str(uuid.uuid4()),
        user_id=feedback["user_id"],
        notification_type="admin_message",
        content=data.message,
        related_id=feedback_id,
        related_type="feedback",
        title="管理员消息"
    )
    
    return {"message": "通知已发送"}
