"""
用户申诉API路由
处理Token消耗相关的申诉
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import json
import logging

from backend.auth import get_current_user, get_current_admin_user
from ..database import get_db_connection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/complaints", tags=["用户申诉"])


class ComplaintCreate(BaseModel):
    type: str = Field(..., description="申诉类型: token_refund/quality/other")
    related_id: Optional[str] = Field(None, description="关联记录ID（如消费记录ID）")
    description: str = Field(..., min_length=10, max_length=2000, description="申诉描述")
    screenshots: Optional[List[str]] = Field(default=None, description="截图URL列表")


class ComplaintReply(BaseModel):
    complaint_id: str = Field(..., description="申诉ID")
    reply: str = Field(..., min_length=1, max_length=2000, description="管理员回复")
    action: Optional[str] = Field(default="reply", description="操作: reply/refund/reject")


class ComplaintResolve(BaseModel):
    complaint_id: str = Field(..., description="申诉ID")
    action: str = Field(..., description="处理动作: refund/reject")
    refund_integral: Optional[float] = Field(None, ge=0, description="退款积分（action=refund时必填）")
    reply: str = Field(..., min_length=1, description="处理说明")


@router.post("")
async def create_complaint(
    request: ComplaintCreate,
    user: dict = Depends(get_current_user)
):
    """
    提交申诉
    
    用户对Token消耗或服务质量有异议时提交申诉
    """
    conn = await get_db_connection()
    try:
        if request.related_id:
            cursor = await conn.execute(
                "SELECT id FROM token_consumption_logs WHERE id = ? AND user_id = ?",
                (request.related_id, user["id"])
            )
            if not await cursor.fetchone():
                raise HTTPException(status_code=404, detail="关联记录不存在")
        
        complaint_id = str(uuid.uuid4())
        
        await conn.execute(
            """
            INSERT INTO complaints (id, user_id, type, related_id, description, screenshots, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)
            """,
            (
                complaint_id,
                user["id"],
                request.type,
                request.related_id,
                request.description,
                json.dumps(request.screenshots) if request.screenshots else None,
                datetime.utcnow().isoformat()
            )
        )
        await conn.commit()
        
        logger.info(f"Complaint created: {complaint_id} by user {user['id']}")
        
        return {
            "success": True,
            "complaint_id": complaint_id,
            "message": "申诉已提交，我们会尽快处理"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create complaint: {e}")
        raise HTTPException(status_code=500, detail="提交申诉失败")
    finally:
        await conn.close()


@router.get("")
async def get_my_complaints(
    status: Optional[str] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: dict = Depends(get_current_user)
):
    """
    获取我的申诉列表
    """
    conn = await get_db_connection()
    try:
        if status:
            count_cursor = await conn.execute(
                "SELECT COUNT(*) as total FROM complaints WHERE user_id = ? AND status = ?",
                (user["id"], status)
            )
            cursor = await conn.execute(
                """
                SELECT id, type, related_id, description, status, admin_reply, created_at, handled_at
                FROM complaints 
                WHERE user_id = ? AND status = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                (user["id"], status, limit, offset)
            )
        else:
            count_cursor = await conn.execute(
                "SELECT COUNT(*) as total FROM complaints WHERE user_id = ?",
                (user["id"],)
            )
            cursor = await conn.execute(
                """
                SELECT id, type, related_id, description, status, admin_reply, created_at, handled_at
                FROM complaints 
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                (user["id"], limit, offset)
            )
        
        total_row = await count_cursor.fetchone()
        total = total_row["total"] if total_row else 0
        
        rows = await cursor.fetchall()
        
        complaints = []
        for row in rows:
            complaints.append({
                "id": row["id"],
                "type": row["type"],
                "related_id": row["related_id"],
                "description": row["description"],
                "status": row["status"],
                "admin_reply": row["admin_reply"],
                "created_at": row["created_at"],
                "handled_at": row["handled_at"]
            })
        
        return {
            "complaints": complaints,
            "total": total,
            "limit": limit,
            "offset": offset
        }
        
    finally:
        await conn.close()


@router.get("/{complaint_id}")
async def get_complaint_detail(
    complaint_id: str,
    user: dict = Depends(get_current_user)
):
    """
    获取申诉详情
    """
    conn = await get_db_connection()
    try:
        cursor = await conn.execute(
            """
            SELECT c.*, u.username as handler_name
            FROM complaints c
            LEFT JOIN users u ON c.handled_by = u.id
            WHERE c.id = ? AND c.user_id = ?
            """,
            (complaint_id, user["id"])
        )
        row = await cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="申诉不存在")
        
        result = {
            "id": row["id"],
            "type": row["type"],
            "related_id": row["related_id"],
            "description": row["description"],
            "screenshots": json.loads(row["screenshots"]) if row["screenshots"] else [],
            "status": row["status"],
            "admin_reply": row["admin_reply"],
            "handler_name": row["handler_name"],
            "created_at": row["created_at"],
            "handled_at": row["handled_at"]
        }
        
        if row["related_id"]:
            log_cursor = await conn.execute(
                """
                SELECT action_type, total_tokens, cost_integral, created_at
                FROM token_consumption_logs WHERE id = ?
                """,
                (row["related_id"],)
            )
            log_row = await log_cursor.fetchone()
            if log_row:
                result["related_log"] = {
                    "action_type": log_row["action_type"],
                    "total_tokens": log_row["total_tokens"],
                    "cost_integral": log_row["cost_integral"],
                    "created_at": log_row["created_at"]
                }
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get complaint detail: {e}")
        raise HTTPException(status_code=500, detail="获取详情失败")
    finally:
        await conn.close()


@router.post("/admin/resolve")
async def resolve_complaint(
    request: ComplaintResolve,
    admin: dict = Depends(get_current_admin_user)
):
    """
    处理申诉（管理员）
    
    支持两种处理方式：
    - refund: 退还积分
    - reject: 拒绝申诉
    """
    conn = await get_db_connection()
    try:
        cursor = await conn.execute(
            "SELECT * FROM complaints WHERE id = ?",
            (request.complaint_id,)
        )
        complaint = await cursor.fetchone()
        
        if not complaint:
            raise HTTPException(status_code=404, detail="申诉不存在")
        
        if complaint["status"] != "pending":
            raise HTTPException(status_code=400, detail="该申诉已处理")
        
        if request.action == "refund":
            if not request.refund_integral or request.refund_integral <= 0:
                raise HTTPException(status_code=400, detail="退款积分必须大于0")
            
            await conn.execute("BEGIN IMMEDIATE TRANSACTION")
            
            cursor = await conn.execute(
                "SELECT integral FROM users WHERE id = ?",
                (complaint["user_id"],)
            )
            user_row = await cursor.fetchone()
            current_integral = float(user_row["integral"] or 0)
            new_integral = current_integral + request.refund_integral
            
            await conn.execute(
                "UPDATE users SET integral = ?, updated_at = ? WHERE id = ?",
                (new_integral, datetime.utcnow().isoformat(), complaint["user_id"])
            )
            
            refund_log_id = str(uuid.uuid4())
            await conn.execute(
                """
                INSERT INTO refund_logs (id, consumption_id, user_id, refund_tokens, refund_integral, reason, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    refund_log_id,
                    complaint["related_id"],
                    complaint["user_id"],
                    int(request.refund_integral * 100),
                    request.refund_integral,
                    f"申诉退款: {request.reply}",
                    datetime.utcnow().isoformat()
                )
            )
            
            await conn.execute(
                """
                UPDATE complaints 
                SET status = 'resolved', admin_reply = ?, handled_by = ?, handled_at = ?
                WHERE id = ?
                """,
                (request.reply, admin["id"], datetime.utcnow().isoformat(), request.complaint_id)
            )
            
            await conn.commit()
            
            from ..services.notification_service import notification_service
            try:
                await notification_service.send_notification(
                    user_id=complaint["user_id"],
                    title="申诉处理结果",
                    content=f"您的申诉已处理，已退还 {request.refund_integral:.2f} 积分。处理说明：{request.reply}",
                    notification_type="refund"
                )
            except Exception as e:
                logger.warning(f"Failed to send notification: {e}")
            
            logger.info(f"Complaint resolved with refund: {request.complaint_id}, refund={request.refund_integral}")
            
            return {
                "success": True,
                "action": "refund",
                "refund_integral": request.refund_integral,
                "message": "申诉已处理，积分已退还"
            }
            
        elif request.action == "reject":
            await conn.execute(
                """
                UPDATE complaints 
                SET status = 'rejected', admin_reply = ?, handled_by = ?, handled_at = ?
                WHERE id = ?
                """,
                (request.reply, admin["id"], datetime.utcnow().isoformat(), request.complaint_id)
            )
            await conn.commit()
            
            from ..services.notification_service import notification_service
            try:
                await notification_service.send_notification(
                    user_id=complaint["user_id"],
                    title="申诉处理结果",
                    content=f"您的申诉已处理。处理说明：{request.reply}",
                    notification_type="system"
                )
            except Exception as e:
                logger.warning(f"Failed to send notification: {e}")
            
            logger.info(f"Complaint rejected: {request.complaint_id}")
            
            return {
                "success": True,
                "action": "reject",
                "message": "申诉已拒绝"
            }
        
        else:
            raise HTTPException(status_code=400, detail="无效的处理动作")
            
    except HTTPException:
        raise
    except Exception as e:
        await conn.rollback()
        logger.error(f"Failed to resolve complaint: {e}")
        raise HTTPException(status_code=500, detail="处理申诉失败")
    finally:
        await conn.close()


@router.get("/admin/list")
async def admin_list_complaints(
    status: Optional[str] = Query(default=None),
    type: Optional[str] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    admin: dict = Depends(get_current_admin_user)
):
    """
    获取申诉列表（管理员）
    """
    conn = await get_db_connection()
    try:
        where_clauses = ["1=1"]
        params = []
        
        if status:
            where_clauses.append("c.status = ?")
            params.append(status)
        if type:
            where_clauses.append("c.type = ?")
            params.append(type)
        
        where_sql = " AND ".join(where_clauses)
        
        count_cursor = await conn.execute(
            f"SELECT COUNT(*) as total FROM complaints c WHERE {where_sql}",
            params
        )
        total_row = await count_cursor.fetchone()
        total = total_row["total"] if total_row else 0
        
        cursor = await conn.execute(
            f"""
            SELECT c.*, u.username, u.email
            FROM complaints c
            LEFT JOIN users u ON c.user_id = u.id
            WHERE {where_sql}
            ORDER BY c.created_at DESC
            LIMIT ? OFFSET ?
            """,
            params + [limit, offset]
        )
        rows = await cursor.fetchall()
        
        complaints = []
        for row in rows:
            complaints.append({
                "id": row["id"],
                "user_id": row["user_id"],
                "username": row["username"],
                "email": row["email"],
                "type": row["type"],
                "related_id": row["related_id"],
                "description": row["description"][:200] + "..." if len(row["description"] or "") > 200 else row["description"],
                "status": row["status"],
                "created_at": row["created_at"],
                "handled_at": row["handled_at"]
            })
        
        return {
            "complaints": complaints,
            "total": total,
            "limit": limit,
            "offset": offset
        }
        
    finally:
        await conn.close()


@router.get("/admin/stats")
async def admin_complaint_stats(
    admin: dict = Depends(get_current_admin_user)
):
    """
    获取申诉统计（管理员）
    """
    conn = await get_db_connection()
    try:
        cursor = await conn.execute(
            """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN status = 'resolved' THEN 1 ELSE 0 END) as resolved,
                SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) as rejected
            FROM complaints
            """
        )
        stats = await cursor.fetchone()
        
        cursor = await conn.execute(
            """
            SELECT type, COUNT(*) as count
            FROM complaints
            GROUP BY type
            ORDER BY count DESC
            """
        )
        by_type = await cursor.fetchall()
        
        return {
            "total": stats["total"] or 0,
            "pending": stats["pending"] or 0,
            "resolved": stats["resolved"] or 0,
            "rejected": stats["rejected"] or 0,
            "by_type": [
                {"type": row["type"], "count": row["count"]}
                for row in by_type
            ]
        }
        
    finally:
        await conn.close()
