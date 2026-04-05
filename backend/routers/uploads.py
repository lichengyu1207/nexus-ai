"""
用户上传房产数据获取积分API路由
实现众包数据采集、审核流程、积分奖励闭环
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
from ..services.notification_service import notification_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/uploads", tags=["用户上传"])


class DataTypeResponse(BaseModel):
    id: str
    name: str
    display_name: str
    base_reward: int
    max_reward: int
    unit: str
    description: Optional[str]


class UploadCreate(BaseModel):
    data_type_id: str
    raw_data: Dict[str, Any]


class UploadReview(BaseModel):
    action: str
    reward_tokens: Optional[int] = None
    review_notes: Optional[str] = None


@router.get("/data-types")
async def get_data_types():
    """
    获取数据类型列表
    
    返回所有可上传的数据类型及其奖励规则
    """
    conn = await get_db_connection()
    try:
        cursor = await conn.execute(
            "SELECT id, name, display_name, base_reward, max_reward, unit, description FROM data_types WHERE is_active = 1"
        )
        rows = await cursor.fetchall()
        
        return {
            "data_types": [
                {
                    "id": row["id"],
                    "name": row["name"],
                    "display_name": row["display_name"],
                    "base_reward": row["base_reward"],
                    "max_reward": row["max_reward"],
                    "unit": row["unit"],
                    "description": row["description"]
                }
                for row in rows
            ]
        }
    finally:
        await conn.close()


@router.post("")
async def create_upload(
    request: UploadCreate,
    user: dict = Depends(get_current_user)
):
    """
    上传房产数据
    
    用户提交房产相关数据，等待管理员审核
    """
    conn = await get_db_connection()
    try:
        cursor = await conn.execute(
            "SELECT id, display_name FROM data_types WHERE id = ?",
            (request.data_type_id,)
        )
        data_type = await cursor.fetchone()
        if not data_type:
            raise HTTPException(status_code=400, detail="无效的数据类型")
        
        upload_id = str(uuid.uuid4())
        
        await conn.execute(
            """
            INSERT INTO user_uploads (id, user_id, data_type_id, raw_data, status, submitted_at)
            VALUES (?, ?, ?, ?, 'pending', ?)
            """,
            (upload_id, user["id"], request.data_type_id, json.dumps(request.raw_data), datetime.utcnow().isoformat())
        )
        await conn.commit()
        
        logger.info(f"Upload created: {upload_id} by user {user['id']}")
        
        return {
            "id": upload_id,
            "status": "pending",
            "message": "数据已提交，等待审核"
        }
        
    finally:
        await conn.close()


@router.get("")
async def get_user_uploads(
    status: Optional[str] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: dict = Depends(get_current_user)
):
    """
    获取用户上传记录
    
    查看自己的上传历史
    """
    conn = await get_db_connection()
    try:
        where_clause = "user_id = ?"
        params = [user["id"]]
        
        if status:
            where_clause += " AND status = ?"
            params.append(status)
        
        count_cursor = await conn.execute(
            f"SELECT COUNT(*) as total FROM user_uploads WHERE {where_clause}",
            params
        )
        total_row = await count_cursor.fetchone()
        total = total_row["total"] if total_row else 0
        
        cursor = await conn.execute(
            f"""
            SELECT u.id, u.data_type_id, u.raw_data, u.status, u.reward_tokens, u.reward_integral, 
                   u.submitted_at, u.reviewed_at, u.review_notes,
                   dt.display_name as data_type_name
            FROM user_uploads u
            LEFT JOIN data_types dt ON u.data_type_id = dt.id
            WHERE {where_clause}
            ORDER BY u.submitted_at DESC
            LIMIT ? OFFSET ?
            """,
            params + [limit, offset]
        )
        rows = await cursor.fetchall()
        
        uploads = []
        for row in rows:
            upload = {
                "id": row["id"],
                "data_type_id": row["data_type_id"],
                "data_type_name": row["data_type_name"],
                "raw_data": json.loads(row["raw_data"]) if row["raw_data"] else {},
                "status": row["status"],
                "reward_tokens": row["reward_tokens"],
                "reward_integral": row["reward_integral"],
                "submitted_at": row["submitted_at"],
                "reviewed_at": row["reviewed_at"],
                "review_notes": row["review_notes"]
            }
            uploads.append(upload)
        
        return {
            "uploads": uploads,
            "total": total,
            "limit": limit,
            "offset": offset
        }
        
    finally:
        await conn.close()


@router.get("/stats")
async def get_user_upload_stats(
    user: dict = Depends(get_current_user)
):
    """
    获取用户上传统计
    
    显示上传总数、待审数、已通过数、获得积分等
    """
    conn = await get_db_connection()
    try:
        cursor = await conn.execute(
            """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved,
                SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) as rejected,
                SUM(COALESCE(reward_integral, 0)) as total_reward
            FROM user_uploads
            WHERE user_id = ?
            """,
            (user["id"],)
        )
        stats = await cursor.fetchone()
        
        return {
            "total_uploads": stats["total"] or 0,
            "pending": stats["pending"] or 0,
            "approved": stats["approved"] or 0,
            "rejected": stats["rejected"] or 0,
            "total_reward_integral": round(stats["total_reward"] or 0, 2)
        }
        
    finally:
        await conn.close()


@router.get("/admin/pending")
async def admin_get_pending_uploads(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    data_type: Optional[str] = Query(default=None),
    admin: dict = Depends(get_current_admin_user)
):
    """
    获取待审核上传列表（管理员）
    
    管理员查看所有待审核的用户上传数据
    """
    conn = await get_db_connection()
    try:
        where_clause = "u.status = 'pending'"
        params = []
        
        if data_type:
            where_clause += " AND u.data_type_id = ?"
            params.append(data_type)
        
        count_cursor = await conn.execute(
            f"SELECT COUNT(*) as total FROM user_uploads u WHERE {where_clause}",
            params
        )
        total_row = await count_cursor.fetchone()
        total = total_row["total"] if total_row else 0
        
        cursor = await conn.execute(
            f"""
            SELECT u.id, u.user_id, u.data_type_id, u.raw_data, u.submitted_at,
                   dt.display_name as data_type_name,
                   usr.username, usr.email
            FROM user_uploads u
            LEFT JOIN data_types dt ON u.data_type_id = dt.id
            LEFT JOIN users usr ON u.user_id = usr.id
            WHERE {where_clause}
            ORDER BY u.submitted_at ASC
            LIMIT ? OFFSET ?
            """,
            params + [limit, offset]
        )
        rows = await cursor.fetchall()
        
        uploads = []
        for row in rows:
            uploads.append({
                "id": row["id"],
                "user_id": row["user_id"],
                "username": row["username"],
                "email": row["email"],
                "data_type_id": row["data_type_id"],
                "data_type_name": row["data_type_name"],
                "raw_data": json.loads(row["raw_data"]) if row["raw_data"] else {},
                "submitted_at": row["submitted_at"]
            })
        
        return {
            "uploads": uploads,
            "total": total,
            "limit": limit,
            "offset": offset
        }
        
    finally:
        await conn.close()


@router.post("/admin/{upload_id}/review")
async def admin_review_upload(
    upload_id: str,
    request: UploadReview,
    admin: dict = Depends(get_current_admin_user)
):
    """
    审核上传数据（管理员）
    
    管理员审核用户上传的数据
    通过则发放积分，拒绝则记录原因
    """
    conn = await get_db_connection()
    try:
        cursor = await conn.execute(
            "SELECT u.*, dt.base_reward, dt.max_reward, dt.display_name FROM user_uploads u LEFT JOIN data_types dt ON u.data_type_id = dt.id WHERE u.id = ?",
            (upload_id,)
        )
        upload = await cursor.fetchone()
        
        if not upload:
            raise HTTPException(status_code=404, detail="上传记录不存在")
        
        if upload["status"] != "pending":
            raise HTTPException(status_code=400, detail="该记录已审核")
        
        user_id = upload["user_id"]
        data_type_name = upload["display_name"]
        
        if request.action == "approve":
            reward_tokens = request.reward_tokens or upload["base_reward"] or 10
            max_reward = upload["max_reward"] or 50
            
            if reward_tokens > max_reward:
                raise HTTPException(status_code=400, detail=f"奖励Token不能超过{max_reward}")
            
            reward_integral = round(reward_tokens / 100.0, 2)
            
            await conn.execute("BEGIN IMMEDIATE TRANSACTION")
            
            cursor = await conn.execute(
                "SELECT integral FROM users WHERE id = ?",
                (user_id,)
            )
            user_row = await cursor.fetchone()
            current_integral = float(user_row["integral"] or 0)
            new_integral = current_integral + reward_integral
            
            await conn.execute(
                "UPDATE users SET integral = ?, updated_at = ? WHERE id = ?",
                (new_integral, datetime.utcnow().isoformat(), user_id)
            )
            
            reward_log_id = str(uuid.uuid4())
            await conn.execute(
                """
                INSERT INTO reward_logs (id, user_id, upload_id, reward_tokens, reward_integral, reason, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (reward_log_id, user_id, upload_id, reward_tokens, reward_integral, f"{data_type_name}审核通过", datetime.utcnow().isoformat())
            )
            
            await conn.execute(
                """
                UPDATE user_uploads 
                SET status = 'approved', reward_tokens = ?, reward_integral = ?, reviewed_at = ?, reviewed_by = ?, review_notes = ?
                WHERE id = ?
                """,
                (reward_tokens, reward_integral, datetime.utcnow().isoformat(), admin["id"], request.review_notes, upload_id)
            )
            
            await conn.commit()
            
            try:
                await notification_service.send_notification(
                    user_id=user_id,
                    type="reward",
                    title="数据审核通过",
                    content=f"您上传的{data_type_name}数据已审核通过，获得{reward_integral:.2f}积分奖励！",
                    metadata={"upload_id": upload_id, "reward_tokens": reward_tokens}
                )
            except Exception as e:
                logger.warning(f"Failed to send notification: {e}")
            
            logger.info(f"Upload approved: {upload_id}, reward={reward_integral}")
            
            return {
                "success": True,
                "action": "approved",
                "reward_tokens": reward_tokens,
                "reward_integral": reward_integral,
                "message": f"审核通过，已发放{reward_integral:.2f}积分"
            }
            
        elif request.action == "reject":
            await conn.execute(
                """
                UPDATE user_uploads 
                SET status = 'rejected', reviewed_at = ?, reviewed_by = ?, review_notes = ?
                WHERE id = ?
                """,
                (datetime.utcnow().isoformat(), admin["id"], request.review_notes or "审核未通过", upload_id)
            )
            await conn.commit()
            
            try:
                await notification_service.send_notification(
                    user_id=user_id,
                    type="system",
                    title="数据审核结果",
                    content=f"您上传的{data_type_name}数据未通过审核。原因：{request.review_notes or '不符合要求'}",
                    metadata={"upload_id": upload_id}
                )
            except Exception as e:
                logger.warning(f"Failed to send notification: {e}")
            
            logger.info(f"Upload rejected: {upload_id}")
            
            return {
                "success": True,
                "action": "rejected",
                "message": "已拒绝"
            }
        
        else:
            raise HTTPException(status_code=400, detail="无效的审核操作")
            
    except HTTPException:
        raise
    except Exception as e:
        await conn.rollback()
        logger.error(f"Review failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await conn.close()


@router.get("/admin/history")
async def admin_get_upload_history(
    status: Optional[str] = Query(default=None),
    data_type: Optional[str] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    admin: dict = Depends(get_current_admin_user)
):
    """
    获取审核历史（管理员）
    
    查看所有已审核的记录
    """
    conn = await get_db_connection()
    try:
        where_clauses = ["u.status != 'pending'"]
        params = []
        
        if status:
            where_clauses.append("u.status = ?")
            params.append(status)
        if data_type:
            where_clauses.append("u.data_type_id = ?")
            params.append(data_type)
        
        where_sql = " AND ".join(where_clauses)
        
        count_cursor = await conn.execute(
            f"SELECT COUNT(*) as total FROM user_uploads u WHERE {where_sql}",
            params
        )
        total_row = await count_cursor.fetchone()
        total = total_row["total"] if total_row else 0
        
        cursor = await conn.execute(
            f"""
            SELECT u.id, u.user_id, u.data_type_id, u.raw_data, u.status, u.reward_tokens, u.reward_integral,
                   u.submitted_at, u.reviewed_at, u.review_notes,
                   dt.display_name as data_type_name,
                   usr.username, usr.email,
                   reviewer.username as reviewer_name
            FROM user_uploads u
            LEFT JOIN data_types dt ON u.data_type_id = dt.id
            LEFT JOIN users usr ON u.user_id = usr.id
            LEFT JOIN users reviewer ON u.reviewed_by = reviewer.id
            WHERE {where_sql}
            ORDER BY u.reviewed_at DESC
            LIMIT ? OFFSET ?
            """,
            params + [limit, offset]
        )
        rows = await cursor.fetchall()
        
        uploads = []
        for row in rows:
            uploads.append({
                "id": row["id"],
                "user_id": row["user_id"],
                "username": row["username"],
                "email": row["email"],
                "data_type_id": row["data_type_id"],
                "data_type_name": row["data_type_name"],
                "raw_data": json.loads(row["raw_data"]) if row["raw_data"] else {},
                "status": row["status"],
                "reward_tokens": row["reward_tokens"],
                "reward_integral": row["reward_integral"],
                "submitted_at": row["submitted_at"],
                "reviewed_at": row["reviewed_at"],
                "review_notes": row["review_notes"],
                "reviewer_name": row["reviewer_name"]
            })
        
        return {
            "uploads": uploads,
            "total": total,
            "limit": limit,
            "offset": offset
        }
        
    finally:
        await conn.close()


@router.get("/admin/stats")
async def admin_get_upload_stats(
    admin: dict = Depends(get_current_admin_user)
):
    """
    获取上传统计（管理员）
    
    返回总数、待审数、通过率、各类型占比等
    """
    conn = await get_db_connection()
    try:
        cursor = await conn.execute(
            """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved,
                SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) as rejected,
                SUM(COALESCE(reward_integral, 0)) as total_reward
            FROM user_uploads
            """
        )
        summary = await cursor.fetchone()
        
        cursor = await conn.execute(
            """
            SELECT dt.display_name, COUNT(*) as count
            FROM user_uploads u
            LEFT JOIN data_types dt ON u.data_type_id = dt.id
            GROUP BY dt.display_name
            ORDER BY count DESC
            """
        )
        by_type = await cursor.fetchall()
        
        cursor = await conn.execute(
            """
            SELECT DATE(submitted_at) as date, COUNT(*) as count
            FROM user_uploads
            WHERE submitted_at >= date('now', '-30 days')
            GROUP BY DATE(submitted_at)
            ORDER BY date DESC
            """
        )
        daily = await cursor.fetchall()
        
        total = summary["total"] or 0
        approved = summary["approved"] or 0
        approval_rate = round(approved / total * 100, 1) if total > 0 else 0
        
        return {
            "summary": {
                "total": total,
                "pending": summary["pending"] or 0,
                "approved": approved,
                "rejected": summary["rejected"] or 0,
                "approval_rate": approval_rate,
                "total_reward_integral": round(summary["total_reward"] or 0, 2)
            },
            "by_type": [
                {"type": row["display_name"], "count": row["count"]}
                for row in by_type
            ],
            "daily_trend": [
                {"date": row["date"], "count": row["count"]}
                for row in daily
            ]
        }
        
    finally:
        await conn.close()
