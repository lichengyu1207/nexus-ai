"""
用户反馈API
收集和处理用户反馈
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid
import logging

from ..auth import get_current_user
from ..database import get_db_connection

router = APIRouter(prefix="/api/feedback", tags=["feedback"])
logger = logging.getLogger(__name__)


@router.post("/submit")
async def submit_feedback(
    data: Dict[str, Any],
    user: dict = Depends(get_current_user)
):
    """提交用户反馈"""
    conn = await get_db_connection()
    try:
        feedback_id = str(uuid.uuid4())
        
        feedback_type = data.get("type", "general")
        content = data.get("content", "")
        title = data.get("title", "")
        
        if not content:
            return {"error": "反馈内容不能为空"}
        
        await conn.execute("""
            INSERT INTO user_feedback (id, user_id, type, title, content, status)
            VALUES (?, ?, ?, ?, ?, 'pending')
        """, (feedback_id, user["id"], feedback_type, title, content))
        await conn.commit()
        
        logger.info(f"用户反馈提交: {feedback_id} - {feedback_type}")
        
        return {
            "success": True,
            "id": feedback_id,
            "message": "感谢您的反馈！我们会认真处理。"
        }
    finally:
        await conn.close()


@router.get("/list")
async def list_feedback(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    feedback_type: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """获取反馈列表"""
    conn = await get_db_connection()
    try:
        where_clauses = []
        params = []
        
        if status:
            where_clauses.append("status = ?")
            params.append(status)
        if feedback_type:
            where_clauses.append("type = ?")
            params.append(feedback_type)
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        cursor = await conn.execute(f"""
            SELECT COUNT(*) as total FROM user_feedback WHERE {where_sql}
        """, params)
        total = (await cursor.fetchone())["total"]
        
        offset = (page - 1) * page_size
        cursor = await conn.execute(f"""
            SELECT f.id, f.user_id, f.type, f.title, f.content, f.status, f.created_at, f.updated_at,
                   u.email as user_email
            FROM user_feedback f
            LEFT JOIN users u ON f.user_id = u.id
            WHERE {where_sql}
            ORDER BY f.created_at DESC
            LIMIT ? OFFSET ?
        """, params + [page_size, offset])
        
        feedback_list = []
        async for row in cursor:
            feedback_list.append({
                "id": row["id"],
                "user_id": row["user_id"],
                "user_email": row["user_email"],
                "type": row["type"],
                "title": row["title"],
                "content": row["content"],
                "status": row["status"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            })
        
        return {
            "feedback": feedback_list,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    finally:
        await conn.close()


@router.put("/{feedback_id}/status")
async def update_feedback_status(
    feedback_id: str,
    data: Dict[str, Any],
    user: dict = Depends(get_current_user)
):
    """更新反馈状态"""
    conn = await get_db_connection()
    try:
        status = data.get("status")
        
        if status not in ["pending", "processing", "resolved", "closed"]:
            return {"error": "无效的状态"}
        
        await conn.execute("""
            UPDATE user_feedback SET status = ?, updated_at = ?
            WHERE id = ?
        """, (status, datetime.utcnow().isoformat(), feedback_id))
        await conn.commit()
        
        return {"success": True}
    finally:
        await conn.close()


@router.get("/stats")
async def feedback_stats(user: dict = Depends(get_current_user)):
    """反馈统计"""
    conn = await get_db_connection()
    try:
        cursor = await conn.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN status = 'processing' THEN 1 ELSE 0 END) as processing,
                SUM(CASE WHEN status = 'resolved' THEN 1 ELSE 0 END) as resolved
            FROM user_feedback
        """)
        stats = await cursor.fetchone()
        
        cursor = await conn.execute("""
            SELECT type, COUNT(*) as count
            FROM user_feedback
            GROUP BY type
            ORDER BY count DESC
        """)
        by_type = []
        async for row in cursor:
            by_type.append({"type": row["type"], "count": row["count"]})
        
        return {
            "total": stats["total"],
            "pending": stats["pending"],
            "processing": stats["processing"],
            "resolved": stats["resolved"],
            "by_type": by_type
        }
    finally:
        await conn.close()
