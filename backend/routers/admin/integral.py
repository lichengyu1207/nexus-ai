"""
管理员积分管理API路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from typing import Optional
from backend.models import (
    AdminAdjustIntegralRequest,
    IntegralLogListResponse,
    IntegralLogResponse,
    IntegralSummaryResponse,
    UserResponse
)
from backend.services.integral import IntegralService
from backend.auth import get_current_user, require_admin
from backend.database import get_db
import logging
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/users", tags=["admin-integral"])


@router.post("/integral/adjust")
async def admin_adjust_integral(
    request: AdminAdjustIntegralRequest,
    current_user: dict = Depends(require_admin)
):
    """
    管理员调整用户积分
    
    需要管理员权限，会记录管理员ID和备注
    """
    admin_id = current_user["id"]
    
    # 验证用户是否存在
    async with get_db() as conn:
        cursor = await conn.cursor()
        await cursor.execute("SELECT id, email, full_name FROM users WHERE id = ?", (request.user_id,))
        user = await cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
    
    # 记录积分变动
    success, new_balance, error = await IntegralService.record_integral_change(
        user_id=request.user_id,
        change=request.change,
        reason="admin_adjust",
        admin_note=request.reason,
        admin_id=admin_id
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=error)
    
    logger.info(f"Admin {admin_id} adjusted integral for user {request.user_id}: {request.change:+d}, new balance: {new_balance}")
    
    return {
        "success": True,
        "message": f"积分调整成功",
        "user_id": request.user_id,
        "change": request.change,
        "new_balance": new_balance,
        "user_email": user["email"]
    }


@router.get("/{user_id}/integral/logs", response_model=IntegralLogListResponse)
async def get_user_integral_logs_admin(
    user_id: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(require_admin)
):
    """
    管理员查看指定用户的积分变动日志
    """
    # 验证用户是否存在
    async with get_db() as conn:
        cursor = await conn.cursor()
        await cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="用户不存在")
    
    logs, total = await IntegralService.get_user_logs(user_id, limit=limit, offset=offset)
    
    return IntegralLogListResponse(
        logs=[IntegralLogResponse(**log) for log in logs],
        total=total,
        limit=limit,
        offset=offset
    )


@router.get("/integral/summary", response_model=IntegralSummaryResponse)
async def get_integral_summary(
    current_user: dict = Depends(require_admin)
):
    """
    获取积分统计概况
    
    返回总用户数、总发放积分、总消耗积分等统计数据
    """
    summary = await IntegralService.get_summary()
    
    return IntegralSummaryResponse(**summary)


@router.get("/search")
async def search_users(
    q: str = Query(..., min_length=1, description="搜索关键词（邮箱或用户名）"),
    limit: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(require_admin)
):
    """
    搜索用户（用于积分管理）
    
    根据邮箱或用户名搜索用户
    """
    async with get_db() as conn:
        cursor = await conn.cursor()
        await cursor.execute(
            """
            SELECT id, email, full_name, integral, membership_level, membership_expires, created_at
            FROM users
            WHERE email LIKE ? OR full_name LIKE ? OR username LIKE ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (f"%{q}%", f"%{q}%", f"%{q}%", limit)
        )
        rows = await cursor.fetchall()
        
        users = []
        for row in rows:
            users.append({
                "id": row["id"],
                "email": row["email"],
                "full_name": row["full_name"],
                "integral": row["integral"] or 0,
                "membership_level": row["membership_level"] or "free",
                "membership_expires": row["membership_expires"],
                "created_at": row["created_at"]
            })
        
        return {"users": users, "total": len(users)}


@router.get("/integral/top")
async def get_top_users(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(require_admin)
):
    """
    获取高积分用户列表
    
    按积分从高到低排序，用于快速选择VIP客户
    """
    async with get_db() as conn:
        cursor = await conn.cursor()
        
        await cursor.execute(
            """
            SELECT COUNT(*) as total FROM users WHERE integral > 0
            """
        )
        total = (await cursor.fetchone())["total"]
        
        await cursor.execute(
            """
            SELECT id, email, full_name, integral, membership_level, membership_expires, created_at
            FROM users
            WHERE integral > 0
            ORDER BY integral DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset)
        )
        rows = await cursor.fetchall()
        
        users = []
        for row in rows:
            users.append({
                "id": row["id"],
                "email": row["email"],
                "full_name": row["full_name"],
                "integral": row["integral"] or 0,
                "membership_level": row["membership_level"] or "free",
                "membership_expires": row["membership_expires"],
                "is_member": row["membership_level"] != "free" if row["membership_level"] else False,
                "created_at": row["created_at"]
            })
        
        return {"users": users, "total": total}


@router.post("/batch-add")
async def batch_add_integral(
    user_ids: list[str] = Body(..., description="用户ID列表"),
    amount: int = Body(..., gt=0, description="积分数量"),
    reason: str = Body(..., min_length=1, description="添加原因"),
    current_user: dict = Depends(require_admin)
):
    """
    批量添加积分
    
    为多个用户同时添加积分
    """
    from ...database import get_db_connection
    
    success_count = 0
    failed_users = []
    
    conn = await get_db_connection()
    try:
        for user_id in user_ids:
            try:
                await conn.execute(
                    """
                    INSERT INTO integral_logs (id, user_id, amount, transaction_type, description, operator_id, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (str(uuid.uuid4()), user_id, amount, "admin_batch_add", f"管理员批量添加: {reason}", current_user["id"], datetime.now().isoformat())
                )
                await conn.execute(
                    "UPDATE users SET integral = integral + ? WHERE id = ?",
                    (amount, user_id)
                )
                success_count += 1
            except Exception as e:
                failed_users.append({"user_id": user_id, "error": str(e)})
        
        await conn.commit()
    finally:
        await conn.close()
    
    return {
        "success": True,
        "total": len(user_ids),
        "success_count": success_count,
        "failed_count": len(failed_users),
        "failed_users": failed_users
    }


@router.get("/{user_id}/integral")
async def get_user_integral_admin(
    user_id: str,
    current_user: dict = Depends(require_admin)
):
    """
    管理员查看指定用户的积分信息
    """
    async with get_db() as conn:
        cursor = await conn.cursor()
        await cursor.execute(
            """
            SELECT id, email, full_name, integral, membership_level, membership_expires, created_at
            FROM users
            WHERE id = ?
            """,
            (user_id,)
        )
        user = await cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 检查会员是否有效
        is_member = False
        membership_expires = user["membership_expires"]
        if user["membership_level"] in ["professional", "enterprise"] and membership_expires:
            try:
                expires_dt = datetime.fromisoformat(membership_expires.replace("Z", "+00:00"))
                is_member = expires_dt > datetime.now()
            except:
                is_member = False
        
        return {
            "id": user["id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "integral": user["integral"] or 0,
            "membership_level": user["membership_level"] or "free",
            "membership_expires": membership_expires,
            "is_member": is_member,
            "created_at": user["created_at"]
        }
