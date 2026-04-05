"""
管理员后台充值订单管理API
包含订单列表、详情、审核、批量操作、导出等功能
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
import uuid
import json
import csv
import io
import logging

from backend.database import get_db_connection
from backend.auth import get_current_user, require_admin
from backend.services.risk_engine import risk_engine
from backend.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/recharge", tags=["admin_recharge"])


class ReviewRequest(BaseModel):
    action: str
    actual_integral: Optional[float] = None
    admin_notes: Optional[str] = None
    notify_user: bool = True


class BatchReviewRequest(BaseModel):
    order_ids: List[str]
    action: str
    actual_integral: Optional[float] = None
    admin_notes: Optional[str] = None


def generate_order_no() -> str:
    """生成订单号"""
    now = datetime.now()
    return f"RC{now.strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6].upper()}"


async def log_admin_operation(admin_id: str, operation_type: str, target_type: str, target_id: str, before_data: dict = None, after_data: dict = None):
    """记录管理员操作日志"""
    conn = await get_db_connection()
    try:
        log_id = str(uuid.uuid4())
        await conn.execute(
            "INSERT INTO admin_operation_logs (id, admin_id, operation_type, target_type, target_id, before_data, after_data) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (log_id, admin_id, operation_type, target_type, target_id, json.dumps(before_data) if before_data else None, json.dumps(after_data) if after_data else None)
        )
        await conn.commit()
    finally:
        await conn.close()


@router.get("/orders")
async def get_orders(
    status: Optional[str] = None,
    user_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    risk_level: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    sort_by: str = Query("submitted_at"),
    order: str = Query("desc"),
    current_user: dict = Depends(require_admin)
):
    """获取订单列表"""
    conn = await get_db_connection()
    try:
        conditions = ["1=1"]
        params = []
        
        if status:
            conditions.append("ro.status = ?")
            params.append(status)
        if user_id:
            conditions.append("ro.user_id = ?")
            params.append(user_id)
        if start_date:
            conditions.append("ro.submitted_at >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("ro.submitted_at <= ?")
            params.append(end_date)
        if min_amount is not None:
            conditions.append("ro.amount >= ?")
            params.append(min_amount)
        if max_amount is not None:
            conditions.append("ro.amount <= ?")
            params.append(max_amount)
        if risk_level:
            conditions.append("ro.risk_level = ?")
            params.append(risk_level)
        
        where_clause = " AND ".join(conditions)
        
        valid_sort_fields = ["submitted_at", "amount", "status", "risk_level"]
        if sort_by not in valid_sort_fields:
            sort_by = "submitted_at"
        order_clause = "DESC" if order.lower() == "desc" else "ASC"
        
        count_cursor = await conn.execute(
            f"SELECT COUNT(*) as total FROM recharge_orders ro WHERE {where_clause}",
            params
        )
        total = (await count_cursor.fetchone())["total"]
        
        offset = (page - 1) * limit
        cursor = await conn.execute(
            f"""
            SELECT ro.*, u.email, u.full_name, u.integral as user_integral
            FROM recharge_orders ro
            LEFT JOIN users u ON ro.user_id = u.id
            WHERE {where_clause}
            ORDER BY ro.{sort_by} {order_clause}
            LIMIT ? OFFSET ?
            """,
            params + [limit, offset]
        )
        orders = await cursor.fetchall()
        
        return {
            "total": total,
            "page": page,
            "limit": limit,
            "orders": [dict(row) for row in orders]
        }
    finally:
        await conn.close()


@router.get("/orders/{order_id}")
async def get_order_detail(
    order_id: str,
    current_user: dict = Depends(require_admin)
):
    """获取订单详情"""
    conn = await get_db_connection()
    try:
        cursor = await conn.execute(
            """
            SELECT ro.*, u.email, u.full_name, u.integral as user_integral, u.created_at as user_created_at,
                   processor.email as processor_email, processor.full_name as processor_name
            FROM recharge_orders ro
            LEFT JOIN users u ON ro.user_id = u.id
            LEFT JOIN users processor ON ro.processed_by = processor.id
            WHERE ro.id = ?
            """,
            (order_id,)
        )
        order = await cursor.fetchone()
        
        if not order:
            raise HTTPException(status_code=404, detail="订单不存在")
        
        order_dict = dict(order)
        
        cursor = await conn.execute(
            "SELECT COUNT(*) as count, SUM(amount) as total_amount FROM recharge_orders WHERE user_id = ? AND status = 'approved'",
            (order_dict["user_id"],)
        )
        history = await cursor.fetchone()
        order_dict["user_recharge_count"] = history["count"] or 0
        order_dict["user_total_recharge"] = history["total_amount"] or 0
        
        cursor = await conn.execute(
            "SELECT * FROM admin_operation_logs WHERE target_type = 'order' AND target_id = ? ORDER BY created_at DESC",
            (order_id,)
        )
        logs = await cursor.fetchall()
        order_dict["operation_logs"] = [dict(log) for log in logs]
        
        return order_dict
    finally:
        await conn.close()


@router.post("/orders/{order_id}/review")
async def review_order(
    order_id: str,
    request: ReviewRequest,
    current_user: dict = Depends(require_admin)
):
    """审核订单"""
    admin_id = current_user["id"]
    
    if request.action not in ["approve", "reject", "mark_suspicious"]:
        raise HTTPException(status_code=400, detail="无效的操作类型")
    
    conn = await get_db_connection()
    try:
        await conn.execute("BEGIN IMMEDIATE")
        
        cursor = await conn.execute(
            "SELECT * FROM recharge_orders WHERE id = ? FOR UPDATE",
            (order_id,)
        )
        order = await cursor.fetchone()
        
        if not order:
            await conn.rollback()
            raise HTTPException(status_code=404, detail="订单不存在")
        
        order = dict(order)
        
        if order["status"] != "pending":
            await conn.rollback()
            raise HTTPException(status_code=400, detail=f"订单状态为{order['status']}，无法审核")
        
        before_data = {"status": order["status"], "risk_level": order["risk_level"]}
        
        now = datetime.utcnow().isoformat()
        actual_integral = request.actual_integral if request.actual_integral else order["integral"]
        
        if request.action == "approve":
            await conn.execute(
                "UPDATE recharge_orders SET status = 'approved', actual_integral = ?, processed_at = ?, processed_by = ?, admin_notes = COALESCE(?, admin_notes), updated_at = ? WHERE id = ?",
                (actual_integral, now, admin_id, request.admin_notes, now, order_id)
            )
            
            await conn.execute(
                "UPDATE users SET integral = integral + ? WHERE id = ?",
                (actual_integral, order["user_id"])
            )
            
            log_id = str(uuid.uuid4())
            cursor = await conn.execute("SELECT integral FROM users WHERE id = ?", (order["user_id"],))
            user = await cursor.fetchone()
            balance_after = user["integral"] if user else actual_integral
            
            await conn.execute(
                "INSERT INTO integral_logs (id, user_id, change, balance_after, reason, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (log_id, order["user_id"], actual_integral, balance_after, f"充值订单审核通过: {order['order_no']}", now)
            )
            
            cursor = await conn.execute(
                "SELECT user_id FROM user_behavior_points WHERE user_id = ?",
                (order["user_id"],)
            )
            if not await cursor.fetchone():
                await conn.execute(
                    "INSERT INTO user_behavior_points (user_id, total_points, level) VALUES (?, ?, 1)",
                    (order["user_id"], actual_integral)
                )
            else:
                await conn.execute(
                    "UPDATE user_behavior_points SET total_points = total_points + ?, level = (total_points + ?) / 1000 + 1, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                    (actual_integral, actual_integral, order["user_id"])
                )
            
            after_data = {"status": "approved", "actual_integral": actual_integral}
            
        elif request.action == "reject":
            await conn.execute(
                "UPDATE recharge_orders SET status = 'rejected', processed_at = ?, processed_by = ?, admin_notes = COALESCE(?, admin_notes), updated_at = ? WHERE id = ?",
                (now, admin_id, request.admin_notes, now, order_id)
            )
            after_data = {"status": "rejected"}
            
        elif request.action == "mark_suspicious":
            await conn.execute(
                "UPDATE recharge_orders SET status = 'suspicious', risk_level = 'high', processed_at = ?, processed_by = ?, admin_notes = COALESCE(?, admin_notes), updated_at = ? WHERE id = ?",
                (now, admin_id, request.admin_notes, now, order_id)
            )
            after_data = {"status": "suspicious", "risk_level": "high"}
        
        await conn.commit()
        
        await log_admin_operation(admin_id, f"recharge_{request.action}", "order", order_id, before_data, after_data)
        
        if request.notify_user:
            try:
                notification_service = NotificationService()
                if request.action == "approve":
                    await notification_service.send_notification(
                        user_id=order["user_id"],
                        type="recharge_approved",
                        title="充值审核通过",
                        content=f"您的充值订单 {order['order_no']} 已审核通过，获得 {actual_integral} 积分"
                    )
                elif request.action == "reject":
                    await notification_service.send_notification(
                        user_id=order["user_id"],
                        type="recharge_rejected",
                        title="充值审核拒绝",
                        content=f"您的充值订单 {order['order_no']} 审核未通过，如有疑问请联系客服"
                    )
            except Exception as e:
                logger.error(f"发送通知失败: {e}")
        
        logger.info(f"管理员 {admin_id} {request.action} 订单 {order_id}")
        
        return {"status": "success", "message": f"订单已{request.action}", "order_id": order_id}
        
    except HTTPException:
        raise
    except Exception as e:
        await conn.rollback()
        logger.error(f"审核订单失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await conn.close()


@router.post("/orders/batch-review")
async def batch_review_orders(
    request: BatchReviewRequest,
    current_user: dict = Depends(require_admin)
):
    """批量审核订单"""
    if len(request.order_ids) > 50:
        raise HTTPException(status_code=400, detail="单次最多处理50个订单")
    
    if request.action not in ["approve", "reject"]:
        raise HTTPException(status_code=400, detail="批量操作仅支持approve或reject")
    
    results = []
    for order_id in request.order_ids:
        try:
            review_request = ReviewRequest(
                action=request.action,
                actual_integral=request.actual_integral,
                admin_notes=request.admin_notes,
                notify_user=True
            )
            await review_order(order_id, review_request, current_user)
            results.append({"order_id": order_id, "status": "success"})
        except Exception as e:
            results.append({"order_id": order_id, "status": "failed", "error": str(e)})
    
    success_count = sum(1 for r in results if r["status"] == "success")
    return {
        "total": len(request.order_ids),
        "success": success_count,
        "failed": len(request.order_ids) - success_count,
        "results": results
    }


@router.get("/orders/export")
async def export_orders(
    status: Optional[str] = None,
    user_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    risk_level: Optional[str] = None,
    current_user: dict = Depends(require_admin)
):
    """导出订单为CSV"""
    conn = await get_db_connection()
    try:
        conditions = ["1=1"]
        params = []
        
        if status:
            conditions.append("ro.status = ?")
            params.append(status)
        if user_id:
            conditions.append("ro.user_id = ?")
            params.append(user_id)
        if start_date:
            conditions.append("ro.submitted_at >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("ro.submitted_at <= ?")
            params.append(end_date)
        if min_amount is not None:
            conditions.append("ro.amount >= ?")
            params.append(min_amount)
        if max_amount is not None:
            conditions.append("ro.amount <= ?")
            params.append(max_amount)
        if risk_level:
            conditions.append("ro.risk_level = ?")
            params.append(risk_level)
        
        where_clause = " AND ".join(conditions)
        
        cursor = await conn.execute(
            f"""
            SELECT ro.order_no, ro.amount, ro.integral, ro.status, ro.risk_level, 
                   ro.submitted_at, ro.processed_at, u.email as user_email
            FROM recharge_orders ro
            LEFT JOIN users u ON ro.user_id = u.id
            WHERE {where_clause}
            ORDER BY ro.submitted_at DESC
            """,
            params
        )
        orders = await cursor.fetchall()
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["订单号", "用户邮箱", "金额", "积分", "状态", "风险等级", "提交时间", "处理时间"])
        
        for order in orders:
            writer.writerow([
                order["order_no"],
                order["user_email"] or "",
                order["amount"],
                order["integral"],
                order["status"],
                order["risk_level"],
                order["submitted_at"],
                order["processed_at"] or ""
            ])
        
        output.seek(0)
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=recharge_orders_{datetime.now().strftime('%Y%m%d')}.csv"}
        )
    finally:
        await conn.close()


@router.get("/stats/overview")
async def get_stats_overview(current_user: dict = Depends(require_admin)):
    """获取充值统计概览"""
    conn = await get_db_connection()
    try:
        today = datetime.now().date()
        month_start = today.replace(day=1)
        
        cursor = await conn.execute(
            "SELECT COUNT(*) as count, COALESCE(SUM(amount), 0) as total FROM recharge_orders WHERE DATE(submitted_at) = ?",
            (today.isoformat(),)
        )
        today_stats = await cursor.fetchone()
        
        cursor = await conn.execute(
            "SELECT COUNT(*) as count, COALESCE(SUM(amount), 0) as total FROM recharge_orders WHERE DATE(submitted_at) >= ?",
            (month_start.isoformat(),)
        )
        month_stats = await cursor.fetchone()
        
        cursor = await conn.execute(
            "SELECT COUNT(*) as count, COALESCE(SUM(amount), 0) as total FROM recharge_orders WHERE status = 'approved'"
        )
        total_stats = await cursor.fetchone()
        
        cursor = await conn.execute(
            "SELECT COUNT(*) as count FROM recharge_orders WHERE status = 'pending'"
        )
        pending_stats = await cursor.fetchone()
        
        cursor = await conn.execute(
            """
            SELECT AVG(process_time) as avg_time FROM (
                SELECT JULIANDAY(processed_at) - JULIANDAY(submitted_at) as process_time
                FROM recharge_orders 
                WHERE status = 'approved' AND processed_at IS NOT NULL
                AND DATE(submitted_at) >= ?
            )
            """,
            (month_start.isoformat(),)
        )
        avg_time_result = await cursor.fetchone()
        avg_process_time = avg_time_result["avg_time"] * 24 if avg_time_result and avg_time_result["avg_time"] else 0
        
        return {
            "today": {
                "count": today_stats["count"],
                "amount": today_stats["total"]
            },
            "month": {
                "count": month_stats["count"],
                "amount": month_stats["total"]
            },
            "total": {
                "count": total_stats["count"],
                "amount": total_stats["total"]
            },
            "pending_count": pending_stats["count"],
            "avg_process_time_hours": round(avg_process_time, 2)
        }
    finally:
        await conn.close()


@router.get("/stats/trend")
async def get_stats_trend(
    days: int = Query(30, ge=7, le=90),
    current_user: dict = Depends(require_admin)
):
    """获取充值趋势"""
    conn = await get_db_connection()
    try:
        start_date = datetime.now().date() - timedelta(days=days)
        
        cursor = await conn.execute(
            """
            SELECT DATE(submitted_at) as date, 
                   COUNT(*) as count, 
                   COALESCE(SUM(amount), 0) as amount,
                   SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved_count
            FROM recharge_orders
            WHERE DATE(submitted_at) >= ?
            GROUP BY DATE(submitted_at)
            ORDER BY date
            """,
            (start_date.isoformat(),)
        )
        trend_data = await cursor.fetchall()
        
        return {
            "days": days,
            "data": [{"date": row["date"], "count": row["count"], "amount": row["amount"], "approved_count": row["approved_count"]} for row in trend_data]
        }
    finally:
        await conn.close()


@router.get("/stats/top-users")
async def get_stats_top_users(
    limit: int = Query(10, ge=5, le=50),
    current_user: dict = Depends(require_admin)
):
    """获取充值TOP用户"""
    conn = await get_db_connection()
    try:
        cursor = await conn.execute(
            """
            SELECT u.email, u.full_name, 
                   COUNT(*) as recharge_count, 
                   COALESCE(SUM(ro.amount), 0) as total_amount
            FROM recharge_orders ro
            JOIN users u ON ro.user_id = u.id
            WHERE ro.status = 'approved'
            GROUP BY ro.user_id
            ORDER BY total_amount DESC
            LIMIT ?
            """,
            (limit,)
        )
        top_users = await cursor.fetchall()
        
        return {
            "users": [{"email": row["email"], "full_name": row["full_name"], "recharge_count": row["recharge_count"], "total_amount": row["total_amount"]} for row in top_users]
        }
    finally:
        await conn.close()


@router.get("/stats/distribution")
async def get_stats_distribution(current_user: dict = Depends(require_admin)):
    """获取订单分布统计"""
    conn = await get_db_connection()
    try:
        cursor = await conn.execute(
            "SELECT status, COUNT(*) as count FROM recharge_orders GROUP BY status"
        )
        status_dist = await cursor.fetchall()
        
        cursor = await conn.execute(
            "SELECT risk_level, COUNT(*) as count FROM recharge_orders GROUP BY risk_level"
        )
        risk_dist = await cursor.fetchall()
        
        cursor = await conn.execute(
            """
            SELECT 
                CASE 
                    WHEN amount < 100 THEN '0-100'
                    WHEN amount < 500 THEN '100-500'
                    WHEN amount < 1000 THEN '500-1000'
                    WHEN amount < 5000 THEN '1000-5000'
                    ELSE '5000+'
                END as amount_range,
                COUNT(*) as count
            FROM recharge_orders
            GROUP BY amount_range
            ORDER BY amount_range
            """
        )
        amount_dist = await cursor.fetchall()
        
        return {
            "status_distribution": [{"status": row["status"], "count": row["count"]} for row in status_dist],
            "risk_distribution": [{"risk_level": row["risk_level"], "count": row["count"]} for row in risk_dist],
            "amount_distribution": [{"range": row["amount_range"], "count": row["count"]} for row in amount_dist]
        }
    finally:
        await conn.close()


@router.get("/users/{user_id}/integral")
async def get_user_integral(
    user_id: str,
    current_user: dict = Depends(require_admin)
):
    """获取用户当前积分余额"""
    conn = await get_db_connection()
    try:
        cursor = await conn.execute(
            "SELECT id, email, full_name, integral FROM users WHERE id = ?",
            (user_id,)
        )
        user = await cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        return {
            "user_id": user["id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "integral": user["integral"] or 0
        }
    finally:
        await conn.close()
