from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import json
from datetime import datetime
import uuid

from backend.database import get_db
from backend.auth import get_current_user, get_current_user_optional, require_admin

router = APIRouter(prefix="/api/plans", tags=["plans"])

class PlanResponse(BaseModel):
    id: str
    name: str
    type: str
    original_price: int
    final_price: int
    discount_reason: Optional[str] = None
    credits: Optional[int] = None
    duration_days: int
    features: List[str]
    is_popular: bool = False

@router.get("", response_model=List[PlanResponse])
async def get_plans(user = Depends(get_current_user_optional)):
    async with get_db() as conn:
        cursor = await conn.cursor()
        
        await cursor.execute("""
            SELECT id, name, type, price_regular, price_member, price_laohai, price_new_user,
                   credits, duration_days, features, sort_order
            FROM plans 
            WHERE is_active = 1 
            ORDER BY sort_order
        """)
        rows = await cursor.fetchall()
        
        plans = []
        for row in rows:
            plan = dict(row)
            
            original_price = plan["price_regular"]
            final_price = original_price
            discount_reason = None
            
            if user:
                if user.get("source") == "laohai" and plan.get("price_laohai"):
                    final_price = plan["price_laohai"]
                    discount_reason = "粉丝专属价"
                elif user.get("membership_level") and user["membership_level"] != "free" and plan.get("price_member"):
                    final_price = plan["price_member"]
                    discount_reason = "会员价"
                elif not user.get("has_used_first_order") and plan.get("price_new_user"):
                    final_price = plan["price_new_user"]
                    discount_reason = "新用户首单"
            
            features = json.loads(plan["features"]) if plan["features"] else []
            
            is_popular = plan["type"] == "professional"
            
            plans.append(PlanResponse(
                id=plan["id"],
                name=plan["name"],
                type=plan["type"],
                original_price=original_price,
                final_price=final_price,
                discount_reason=discount_reason,
                credits=plan.get("credits"),
                duration_days=plan.get("duration_days", 0),
                features=features,
                is_popular=is_popular
            ))
        
        return plans

@router.get("/admin", response_model=List[dict])
async def admin_get_plans(admin = Depends(require_admin)):
    async with get_db() as conn:
        cursor = await conn.cursor()
        await cursor.execute("SELECT * FROM plans ORDER BY sort_order")
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

class PlanUpdate(BaseModel):
    name: str
    type: str
    price_regular: int
    price_member: Optional[int] = None
    price_laohai: Optional[int] = None
    price_new_user: Optional[int] = None
    credits: Optional[int] = None
    duration_days: int = 0
    features: List[str]
    is_active: bool = True

@router.post("/admin")
async def create_plan(plan: PlanUpdate, admin = Depends(require_admin)):
    async with get_db() as conn:
        cursor = await conn.cursor()
        plan_id = f"plan_{uuid.uuid4().hex[:8]}"
        
        await cursor.execute("""
            INSERT INTO plans (id, name, type, price_regular, price_member, price_laohai, price_new_user,
                             credits, duration_days, features, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            plan_id, plan.name, plan.type, plan.price_regular, plan.price_member,
            plan.price_laohai, plan.price_new_user, plan.credits, plan.duration_days,
            json.dumps(plan.features), 1 if plan.is_active else 0
        ))
        await conn.commit()
        
        return {"id": plan_id, "message": "Plan created"}

@router.put("/admin/{plan_id}")
async def update_plan(plan_id: str, plan: PlanUpdate, admin = Depends(require_admin)):
    async with get_db() as conn:
        cursor = await conn.cursor()
        
        await cursor.execute("""
            UPDATE plans SET 
                name = ?, type = ?, price_regular = ?, price_member = ?, price_laohai = ?,
                price_new_user = ?, credits = ?, duration_days = ?, features = ?, is_active = ?,
                updated_at = ?
            WHERE id = ?
        """, (
            plan.name, plan.type, plan.price_regular, plan.price_member, plan.price_laohai,
            plan.price_new_user, plan.credits, plan.duration_days, json.dumps(plan.features),
            1 if plan.is_active else 0, datetime.utcnow().isoformat(), plan_id
        ))
        await conn.commit()
        
        return {"message": "Plan updated"}
