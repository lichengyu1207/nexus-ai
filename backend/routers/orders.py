from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

from backend.database import get_db
from backend.auth import get_current_user
from backend.services.integral import IntegralService

router = APIRouter(prefix="/api/orders", tags=["orders"])

class OrderCreate(BaseModel):
    plan_id: str
    payment_method: Optional[str] = "wechat"

class OrderResponse(BaseModel):
    id: str
    plan_id: str
    plan_name: str
    amount: int
    original_amount: int
    discount_reason: Optional[str]
    status: str
    qr_code_url: Optional[str]
    created_at: str

@router.post("/create", response_model=OrderResponse)
async def create_order(order: OrderCreate, user = Depends(get_current_user)):
    async with get_db() as conn:
        cursor = await conn.cursor()
        
        await cursor.execute("SELECT * FROM plans WHERE id = ? AND is_active = 1", (order.plan_id,))
        plan = await cursor.fetchone()
        if not plan:
            raise HTTPException(404, "Plan not found")
        
        plan = dict(plan)
        
        original_amount = plan["price_regular"]
        amount = original_amount
        discount_reason = None
        
        if user.get("source") == "laohai" and plan.get("price_laohai"):
            amount = plan["price_laohai"]
            discount_reason = "粉丝专属价"
        elif user.get("membership_level") and user["membership_level"] != "free" and plan.get("price_member"):
            amount = plan["price_member"]
            discount_reason = "会员价"
        elif not user.get("has_used_first_order") and plan.get("price_new_user"):
            amount = plan["price_new_user"]
            discount_reason = "新用户首单"
        
        order_id = f"order_{uuid.uuid4().hex[:12]}"
        
        await cursor.execute("""
            INSERT INTO orders (id, user_id, plan_id, amount, original_amount, discount_reason, status, payment_method, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, ?)
        """, (
            order_id, user["id"], order.plan_id, amount, original_amount, discount_reason,
            order.payment_method, datetime.utcnow().isoformat()
        ))
        
        await conn.commit()
        
        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=pay_{order_id}"
        
        return OrderResponse(
            id=order_id,
            plan_id=order.plan_id,
            plan_name=plan["name"],
            amount=amount,
            original_amount=original_amount,
            discount_reason=discount_reason,
            status="pending",
            qr_code_url=qr_url,
            created_at=datetime.utcnow().isoformat()
        )

@router.get("/{order_id}/status")
async def get_order_status(order_id: str, user = Depends(get_current_user)):
    async with get_db() as conn:
        cursor = await conn.cursor()
        
        await cursor.execute("SELECT * FROM orders WHERE id = ? AND user_id = ?", (order_id, user["id"]))
        order = await cursor.fetchone()
        if not order:
            raise HTTPException(404, "Order not found")
        
        return dict(order)

@router.post("/{order_id}/simulate-pay")
async def simulate_payment(order_id: str, user = Depends(get_current_user)):
    async with get_db() as conn:
        cursor = await conn.cursor()
        
        await cursor.execute("SELECT * FROM orders WHERE id = ? AND user_id = ?", (order_id, user["id"]))
        order = await cursor.fetchone()
        if not order:
            raise HTTPException(404, "Order not found")
        
        order = dict(order)
        if order["status"] != "pending":
            raise HTTPException(400, "Order already processed")
        
        await cursor.execute("SELECT * FROM plans WHERE id = ?", (order["plan_id"],))
        plan = await cursor.fetchone()
        plan = dict(plan)
        
        await cursor.execute("""
            UPDATE orders SET status = 'paid', paid_at = ? WHERE id = ?
        """, (datetime.utcnow().isoformat(), order_id))
        
        if plan["type"] == "integral" and plan.get("credits"):
            await IntegralService.record_integral_change(
                user_id=user["id"],
                change=plan["credits"],
                reason="purchase",
                admin_note=f"购买套餐: {plan['name']}"
            )
        elif plan["type"] == "professional":
            await cursor.execute("""
                UPDATE users SET membership_level = 'professional', 
                membership_expires = datetime('now', '+30 days')
                WHERE id = ?
            """, (user["id"],))
        elif plan["type"] == "enterprise":
            await cursor.execute("""
                UPDATE users SET membership_level = 'enterprise',
                membership_expires = datetime('now', '+30 days')
                WHERE id = ?
            """, (user["id"],))
        
        if order.get("discount_reason") == "新用户首单":
            await cursor.execute("UPDATE users SET has_used_first_order = 1 WHERE id = ?", (user["id"],))
        
        await conn.commit()
        
        return {"status": "paid", "message": "Payment successful"}
