"""
充值管理路由 - PostgreSQL版本
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid
import logging

from backend.database_pg import get_db
from backend.auth import get_current_user, require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/recharge", tags=["recharge"])


class RechargeApplyRequest(BaseModel):
    amount: float
    credits: Optional[int] = None
    plan_id: Optional[str] = None
    notes: Optional[str] = None
    proof_image: Optional[str] = None


class RechargeOrderResponse(BaseModel):
    id: str
    user_id: str
    plan_id: Optional[str]
    amount: float
    credits: Optional[int]
    membership_type: Optional[str]
    membership_days: Optional[int]
    status: str
    admin_notes: Optional[str]
    user_notes: Optional[str]
    created_at: str
    completed_at: Optional[str]


class ProcessOrderRequest(BaseModel):
    action: str
    admin_notes: Optional[str] = None
    plan_id: Optional[str] = None
    credits: Optional[int] = None
    membership_type: Optional[str] = None
    membership_days: Optional[int] = None


@router.post("/apply")
async def apply_recharge(
    request: RechargeApplyRequest,
    user = Depends(get_current_user)
):
    order_id = f"mro_{uuid.uuid4().hex[:12]}"
    now = datetime.utcnow().isoformat()
    
    async with get_db() as conn:
        await conn.execute(
            """
            INSERT INTO manual_recharge_orders 
            (id, user_id, plan_id, amount, credits, status, user_notes, transaction_proof, created_at)
            VALUES ($1, $2, $3, $4, $5, 'pending', $6, $7, $8)
            """,
            order_id, user['id'], request.plan_id, request.amount,
            request.credits, request.notes, request.proof_image, now
        )
    
    return {"order_id": order_id, "message": "充值申请已提交"}


@router.get("/my-orders", response_model=List[RechargeOrderResponse])
async def get_my_orders(user = Depends(get_current_user)):
    async with get_db() as conn:
        rows = await conn.fetch(
            """
            SELECT id, user_id, plan_id, amount, credits, membership_type, 
                   membership_days, status, admin_notes, user_notes, created_at, completed_at
            FROM manual_recharge_orders 
            WHERE user_id = $1 
            ORDER BY created_at DESC
            """,
            user['id']
        )
        
        orders = [
            RechargeOrderResponse(
                id=row['id'],
                user_id=row['user_id'],
                plan_id=row['plan_id'],
                amount=float(row['amount']) if row['amount'] else 0.0,
                credits=row['credits'],
                membership_type=row['membership_type'],
                membership_days=row['membership_days'],
                status=row['status'],
                admin_notes=row['admin_notes'],
                user_notes=row['user_notes'],
                created_at=str(row['created_at']) if row['created_at'] else now,
                completed_at=str(row['completed_at']) if row['completed_at'] else None
            )
            for row in rows
        ]
        
        return orders


@router.get("/admin/orders")
async def admin_get_orders(
    status: Optional[str] = Query(None),
    user_email: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin = Depends(require_admin)
):
    offset = (page - 1) * page_size
    
    async with get_db() as conn:
        base_query = """
            SELECT mro.id, mro.user_id, u.email, u.full_name, mro.plan_id, mro.amount, 
                   mro.credits, mro.membership_type, mro.membership_days, mro.status,
                   mro.admin_notes, mro.user_notes, mro.created_at, mro.completed_at, mro.completed_by
            FROM manual_recharge_orders mro
            LEFT JOIN users u ON mro.user_id = u.id
            WHERE 1=1
        """
        params = []
        param_idx = 1
        
        if status:
            base_query += f" AND mro.status = ${param_idx}"
            params.append(status)
            param_idx += 1
        
        if user_email:
            base_query += f" AND u.email LIKE ${param_idx}"
            params.append(f"%{user_email}%")
            param_idx += 1
        
        count_query = f"SELECT COUNT(*) FROM ({base_query}) as subq"
        total = await conn.fetchval(count_query, *params)
        
        data_query = base_query + f" ORDER BY mro.created_at DESC LIMIT ${param_idx} OFFSET ${param_idx + 1}"
        params.extend([page_size, offset])
        
        rows = await conn.fetch(data_query, *params)
        
        orders = [
            {
                "id": row['id'],
                "user_id": row['user_id'],
                "user_email": row['email'],
                "user_name": row['full_name'],
                "plan_id": row['plan_id'],
                "amount": float(row['amount']) if row['amount'] else 0.0,
                "credits": row['credits'],
                "membership_type": row['membership_type'],
                "membership_days": row['membership_days'],
                "status": row['status'],
                "admin_notes": row['admin_notes'],
                "user_notes": row['user_notes'],
                "created_at": str(row['created_at']) if row['created_at'] else None,
                "completed_at": str(row['completed_at']) if row['completed_at'] else None,
                "completed_by": row['completed_by']
            }
            for row in rows
        ]
        
        return {
            "orders": orders,
            "total": total,
            "page": page,
            "page_size": page_size
        }


@router.post("/admin/orders/{order_id}/process")
async def process_order(
    order_id: str,
    request: ProcessOrderRequest,
    admin = Depends(require_admin)
):
    now = datetime.utcnow().isoformat()
    
    async with get_db() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM manual_recharge_orders WHERE id = $1",
            order_id
        )
        
        if not row:
            raise HTTPException(status_code=404, detail="订单不存在")
        
        user_id = row['user_id']
        
        if request.action == "approve":
            if request.credits:
                await conn.execute(
                    "UPDATE users SET integral = COALESCE(integral, 0) + $1 WHERE id = $2",
                    request.credits, user_id
                )
            
            if request.membership_type and request.membership_days:
                from datetime import timedelta
                expire_date = datetime.utcnow() + timedelta(days=request.membership_days)
                await conn.execute(
                    """
                    UPDATE users 
                    SET membership_type = $1, 
                        membership_expire = $2,
                        membership_start = $3
                    WHERE id = $4
                    """,
                    request.membership_type,
                    expire_date.isoformat(),
                    now,
                    user_id
                )
            
            await conn.execute(
                """
                UPDATE manual_recharge_orders 
                SET status = 'approved', 
                    admin_notes = $1, 
                    completed_at = $2, 
                    completed_by = $3,
                    credits = COALESCE($4, credits),
                    membership_type = COALESCE($5, membership_type),
                    membership_days = COALESCE($6, membership_days)
                WHERE id = $7
                """,
                request.admin_notes, now, admin['id'],
                request.credits, request.membership_type, request.membership_days,
                order_id
            )
            
        elif request.action == "reject":
            await conn.execute(
                """
                UPDATE manual_recharge_orders 
                SET status = 'rejected', 
                    admin_notes = $1, 
                    completed_at = $2, 
                    completed_by = $3
                WHERE id = $4
                """,
                request.admin_notes, now, admin['id'], order_id
            )
        else:
            raise HTTPException(status_code=400, detail="无效的操作类型")
    
    return {"message": f"订单已{request.action}"}
