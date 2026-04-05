"""
通知API路由
提供用户通知的CRUD操作
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, List
import logging

from ..auth import get_current_user
from ..database import NotificationDB

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


class NotificationResponse(BaseModel):
    """通知响应模型"""
    id: str
    user_id: str
    type: str
    title: Optional[str]
    content: str
    link: Optional[str]
    action_text: Optional[str]
    related_id: Optional[str]
    related_type: Optional[str]
    is_read: bool
    created_at: Optional[str]


class NotificationListResponse(BaseModel):
    """通知列表响应"""
    notifications: List[NotificationResponse]
    unread_count: int
    total: int


@router.get("", response_model=NotificationListResponse)
async def get_notifications(
    is_read: Optional[bool] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user)
):
    """
    获取当前用户的通知列表
    
    Args:
        is_read: 是否已读过滤
        limit: 每页数量
        offset: 偏移量
        current_user: 当前用户
        
    Returns:
        NotificationListResponse: 通知列表
    """
    notifications = await NotificationDB.get_user_notifications(
        user_id=current_user["id"],
        is_read=is_read,
        limit=limit,
        offset=offset
    )
    
    unread_count = await NotificationDB.get_unread_count(current_user["id"])
    total_count = await NotificationDB.get_total_count(current_user["id"], is_read)
    
    return NotificationListResponse(
        notifications=[
            NotificationResponse(
                id=n["id"],
                user_id=n["user_id"],
                type=n["type"],
                title=n.get("title"),
                content=n["content"],
                link=n.get("link"),
                action_text=n.get("action_text"),
                related_id=n.get("related_id"),
                related_type=n.get("related_type"),
                is_read=bool(n["is_read"]),
                created_at=n.get("created_at")
            )
            for n in notifications
        ],
        unread_count=unread_count,
        total=total_count
    )


@router.get("/unread-count")
async def get_unread_count(
    current_user: dict = Depends(get_current_user)
):
    """
    获取未读通知数量
    
    Args:
        current_user: 当前用户
        
    Returns:
        dict: 未读数量
    """
    count = await NotificationDB.get_unread_count(current_user["id"])
    return {"unread_count": count}


@router.put("/{notification_id}/read")
async def mark_as_read(
    notification_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    标记通知为已读
    
    Args:
        notification_id: 通知ID
        current_user: 当前用户
        
    Returns:
        dict: 操作结果
    """
    success = await NotificationDB.mark_as_read(notification_id, current_user["id"])
    
    if not success:
        raise HTTPException(status_code=400, detail="标记失败")
    
    return {"message": "已标记为已读", "notification_id": notification_id}


@router.put("/read-all")
async def mark_all_as_read(
    current_user: dict = Depends(get_current_user)
):
    """
    标记所有通知为已读
    
    Args:
        current_user: 当前用户
        
    Returns:
        dict: 操作结果
    """
    count = await NotificationDB.mark_all_as_read(current_user["id"])
    
    return {"message": f"已标记 {count} 条通知为已读", "count": count}


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    删除通知
    
    Args:
        notification_id: 通知ID
        current_user: 当前用户
        
    Returns:
        dict: 操作结果
    """
    success = await NotificationDB.delete_notification(notification_id, current_user["id"])
    
    if not success:
        raise HTTPException(status_code=400, detail="删除失败")
    
    return {"message": "通知已删除", "notification_id": notification_id}
