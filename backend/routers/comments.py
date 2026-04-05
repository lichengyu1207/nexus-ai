"""
评论API路由
提供报告评论的CRUD操作
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
import uuid
import re
import logging

from ..auth import get_current_user
from ..database import CommentDB, ReportDB, NotificationDB, UserDB

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["comments"])


class CommentCreate(BaseModel):
    """创建评论请求"""
    content: str = Field(..., min_length=1, max_length=2000)
    parent_id: Optional[str] = None


class CommentUpdate(BaseModel):
    """更新评论请求"""
    content: str = Field(..., min_length=1, max_length=2000)


class CommentResponse(BaseModel):
    """评论响应"""
    id: str
    report_id: str
    user_id: str
    content: str
    parent_id: Optional[str]
    mentions: Optional[List[str]]
    email: str
    full_name: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]


class CommentListResponse(BaseModel):
    """评论列表响应"""
    comments: List[CommentResponse]
    total: int


def extract_mentions(content: str) -> List[str]:
    """
    从内容中提取@提及的用户ID
    
    Args:
        content: 评论内容
        
    Returns:
        List[str]: 被提及的用户ID列表
    """
    mention_pattern = r'@(\w+(?:\.\w+)*)'
    mentions = re.findall(mention_pattern, content)
    return list(set(mentions))


@router.post("/reports/{report_id}/comments", response_model=CommentResponse)
async def create_comment(
    report_id: str,
    comment_data: CommentCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    创建评论
    
    Args:
        report_id: 报告ID
        comment_data: 评论数据
        current_user: 当前用户
        
    Returns:
        CommentResponse: 创建的评论
    """
    report = await ReportDB.get_report_by_id(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    
    if comment_data.parent_id:
        parent = await CommentDB.get_comment_by_id(comment_data.parent_id)
        if not parent:
            raise HTTPException(status_code=404, detail="父评论不存在")
        if parent["report_id"] != report_id:
            raise HTTPException(status_code=400, detail="父评论不属于该报告")
    
    mentions = extract_mentions(comment_data.content)
    
    comment_id = str(uuid.uuid4())
    
    comment = await CommentDB.create_comment(
        comment_id=comment_id,
        report_id=report_id,
        user_id=current_user["id"],
        content=comment_data.content,
        parent_id=comment_data.parent_id,
        mentions=mentions if mentions else None
    )
    
    mentioner_name = current_user.get("full_name") or current_user["email"]
    
    if mentions:
        logger.info(f"User {current_user['id']} mentioned users: {mentions} in comment {comment_id}")
        
        for mentioned_user_id in mentions:
            try:
                await NotificationDB.create_mention_notification(
                    user_id=mentioned_user_id,
                    comment_id=comment_id,
                    report_id=report_id,
                    mentioner_name=mentioner_name
                )
            except Exception as e:
                logger.error(f"Failed to create mention notification: {e}")
    
    if comment_data.parent_id:
        try:
            parent = await CommentDB.get_comment_by_id(comment_data.parent_id)
            if parent and parent["user_id"] != current_user["id"]:
                await NotificationDB.create_reply_notification(
                    user_id=parent["user_id"],
                    comment_id=comment_id,
                    report_id=report_id,
                    replier_name=mentioner_name
                )
        except Exception as e:
            logger.error(f"Failed to create reply notification: {e}")
    
    return CommentResponse(
        id=comment["id"],
        report_id=comment["report_id"],
        user_id=comment["user_id"],
        content=comment["content"],
        parent_id=comment.get("parent_id"),
        mentions=comment.get("mentions"),
        email=current_user["email"],
        full_name=current_user.get("full_name"),
        created_at=None,
        updated_at=None
    )


@router.get("/reports/{report_id}/comments", response_model=CommentListResponse)
async def get_comments(
    report_id: str,
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """
    获取报告评论列表
    
    Args:
        report_id: 报告ID
        limit: 每页数量
        offset: 偏移量
        current_user: 当前用户
        
    Returns:
        CommentListResponse: 评论列表
    """
    report = await ReportDB.get_report_by_id(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    
    comments = await CommentDB.get_report_comments(report_id, limit, offset)
    total = await CommentDB.get_comment_count(report_id)
    
    return CommentListResponse(
        comments=[
            CommentResponse(
                id=c["id"],
                report_id=c["report_id"],
                user_id=c["user_id"],
                content=c["content"],
                parent_id=c.get("parent_id"),
                mentions=c.get("mentions"),
                email=c["email"],
                full_name=c.get("full_name"),
                created_at=c.get("created_at"),
                updated_at=c.get("updated_at")
            )
            for c in comments
        ],
        total=total
    )


@router.get("/comments/{comment_id}/replies", response_model=List[CommentResponse])
async def get_replies(
    comment_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    获取评论的回复列表
    
    Args:
        comment_id: 评论ID
        current_user: 当前用户
        
    Returns:
        List[CommentResponse]: 回复列表
    """
    parent = await CommentDB.get_comment_by_id(comment_id)
    if not parent:
        raise HTTPException(status_code=404, detail="评论不存在")
    
    replies = await CommentDB.get_replies(comment_id)
    
    return [
        CommentResponse(
            id=r["id"],
            report_id=r["report_id"],
            user_id=r["user_id"],
            content=r["content"],
            parent_id=r.get("parent_id"),
            mentions=r.get("mentions"),
            email=r["email"],
            full_name=r.get("full_name"),
            created_at=r.get("created_at"),
            updated_at=r.get("updated_at")
        )
        for r in replies
    ]


@router.put("/comments/{comment_id}", response_model=CommentResponse)
async def update_comment(
    comment_id: str,
    comment_data: CommentUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    更新评论
    
    Args:
        comment_id: 评论ID
        comment_data: 更新数据
        current_user: 当前用户
        
    Returns:
        CommentResponse: 更新后的评论
    """
    comment = await CommentDB.get_comment_by_id(comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="评论不存在")
    
    if comment["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="无权修改此评论")
    
    mentions = extract_mentions(comment_data.content)
    
    success = await CommentDB.update_comment(
        comment_id,
        comment_data.content,
        mentions if mentions else None
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="更新失败")
    
    updated = await CommentDB.get_comment_by_id(comment_id)
    
    return CommentResponse(
        id=updated["id"],
        report_id=updated["report_id"],
        user_id=updated["user_id"],
        content=updated["content"],
        parent_id=updated.get("parent_id"),
        mentions=updated.get("mentions"),
        email=updated["email"],
        full_name=updated.get("full_name"),
        created_at=updated.get("created_at"),
        updated_at=updated.get("updated_at")
    )


@router.delete("/comments/{comment_id}")
async def delete_comment(
    comment_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    删除评论
    
    Args:
        comment_id: 评论ID
        current_user: 当前用户
        
    Returns:
        dict: 删除结果
    """
    success = await CommentDB.delete_comment(comment_id, current_user["id"])
    
    if not success:
        raise HTTPException(status_code=400, detail="删除失败或无权删除")
    
    return {"message": "评论已删除", "comment_id": comment_id}


@router.get("/comments/mentions")
async def get_my_mentions(
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
):
    """
    获取当前用户被提及的评论列表
    
    Args:
        limit: 每页数量
        current_user: 当前用户
        
    Returns:
        dict: 提及列表
    """
    mentions = await CommentDB.get_user_mentions(current_user["id"], limit)
    
    return {
        "mentions": [
            {
                "id": m["id"],
                "report_id": m["report_id"],
                "task_id": m.get("task_id"),
                "content": m["content"],
                "email": m["email"],
                "full_name": m.get("full_name"),
                "created_at": m.get("created_at")
            }
            for m in mentions
        ],
        "total": len(mentions)
    }
