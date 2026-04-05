"""
签到功能接口
包含签到状态、执行签到、签到日历等接口
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date, timedelta
import uuid
import logging

from ..auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/signin", tags=["签到"])

TOKEN_MULTIPLIER = 100


class SigninStatusResponse(BaseModel):
    today_signed: bool
    current_streak: int
    max_streak: int
    total_days: int
    today_reward: float
    next_reward: float
    signed_dates: List[str]
    makeup_cards: int = 0


class SigninResponse(BaseModel):
    success: bool
    reward_integral: float
    reward_tokens: int
    consecutive_days: int
    new_balance: float
    new_tokens: int
    message: str


class CalendarResponse(BaseModel):
    month: str
    signed_dates: List[str]
    total_days: int


def calculate_reward(consecutive_days: int) -> float:
    if consecutive_days >= 30:
        return 3.0
    elif consecutive_days >= 14:
        return 2.0
    elif consecutive_days >= 7:
        return 1.5
    else:
        return 1.0


@router.get("/status", response_model=SigninStatusResponse)
async def get_signin_status(
    current_user: dict = Depends(get_current_user)
):
    from ..database import get_db
    
    user_id = current_user.get("id")
    today = date.today()
    
    async with get_db() as conn:
        try:
            result = await conn.fetchval(
                "SELECT 1 FROM signin_records WHERE user_id = $1 AND sign_date = $2",
                user_id, today.isoformat()
            )
            today_signed = result is not None
            
            rows = await conn.fetch(
                "SELECT sign_date FROM signin_records WHERE user_id = $1 ORDER BY sign_date DESC",
                user_id
            )
            sign_dates = [date.fromisoformat(row['sign_date']) for row in rows] if rows else []
            
            total_days = len(sign_dates)
            current_streak = 0
            max_streak = 0
            
            if total_days > 0:
                current_streak = 1
                for i in range(1, len(sign_dates)):
                    if sign_dates[i-1] == sign_dates[i] + timedelta(days=1):
                        current_streak += 1
                    else:
                        break
                
                temp_streak = 1
                max_streak = 1
                for i in range(1, len(sign_dates)):
                    if sign_dates[i-1] == sign_dates[i] + timedelta(days=1):
                        temp_streak += 1
                        max_streak = max(max_streak, temp_streak)
                    else:
                        temp_streak = 1
            
            next_streak = current_streak + 1 if not today_signed else current_streak
            today_reward = calculate_reward(next_streak)
            next_reward = calculate_reward(next_streak + 1)
            
            month_start = today.replace(day=1)
            if today.month == 12:
                month_end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                month_end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
            
            rows = await conn.fetch(
                "SELECT sign_date FROM signin_records WHERE user_id = $1 AND sign_date >= $2 AND sign_date <= $3 ORDER BY sign_date",
                user_id, month_start.isoformat(), month_end.isoformat()
            )
            signed_dates = [row['sign_date'] for row in rows] if rows else []
            
            return SigninStatusResponse(
                today_signed=today_signed,
                current_streak=current_streak,
                max_streak=max_streak,
                total_days=total_days,
                today_reward=today_reward,
                next_reward=next_reward,
                signed_dates=signed_dates,
                makeup_cards=0
            )
        except Exception as e:
            logger.error(f"Get signin status error: {e}")
            raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=SigninResponse)
async def do_signin(
    current_user: dict = Depends(get_current_user)
):
    from ..database import get_db
    
    user_id = current_user.get("id")
    today = date.today()
    
    async with get_db() as conn:
        try:
            result = await conn.fetchval(
                "SELECT 1 FROM signin_records WHERE user_id = $1 AND sign_date = $2",
                user_id, today.isoformat()
            )
            
            if result:
                raise HTTPException(status_code=400, detail="今日已签到")
            
            rows = await conn.fetch(
                "SELECT sign_date FROM signin_records WHERE user_id = $1 ORDER BY sign_date DESC",
                user_id
            )
            sign_dates = [date.fromisoformat(row['sign_date']) for row in rows] if rows else []
            
            current_streak = 0
            if sign_dates:
                if sign_dates[0] == today - timedelta(days=1):
                    current_streak = 1
                    for i in range(1, len(sign_dates)):
                        if sign_dates[i-1] == sign_dates[i] + timedelta(days=1):
                            current_streak += 1
                        else:
                            break
            
            new_streak = current_streak + 1
            reward_integral = calculate_reward(new_streak)
            reward_tokens = int(reward_integral * TOKEN_MULTIPLIER)
            
            user = await conn.fetchrow(
                "SELECT integral FROM users WHERE id = $1",
                user_id
            )
            
            if not user:
                raise HTTPException(status_code=404, detail="用户不存在")
            
            old_balance = float(user['integral'] or 0)
            new_balance = old_balance + reward_integral
            new_tokens = int(new_balance * TOKEN_MULTIPLIER)
            
            await conn.execute(
                "UPDATE users SET integral = $1 WHERE id = $2",
                new_balance, user_id
            )
            
            signin_id = str(uuid.uuid4())
            await conn.execute(
                "INSERT INTO signin_records (id, user_id, sign_date, reward_integral, consecutive_days) VALUES ($1, $2, $3, $4, $5)",
                signin_id, user_id, today.isoformat(), reward_integral, new_streak
            )
            
            log_id = str(uuid.uuid4())
            await conn.execute(
                "INSERT INTO integral_logs (id, user_id, change, balance_after, token_change, token_balance_after, reason, action_type, resource_id, resource_type, created_at) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)",
                log_id, user_id, reward_integral, new_balance, reward_tokens, new_tokens,
                f"签到奖励(连续{new_streak}天)", "signin", signin_id, "signin", datetime.now().isoformat()
            )
            
            message = f"签到成功！连续签到{new_streak}天"
            if new_streak == 7:
                message += "，获得周奖励！"
            elif new_streak == 30:
                message += "，获得月奖励！"
            
            return SigninResponse(
                success=True,
                reward_integral=reward_integral,
                reward_tokens=reward_tokens,
                consecutive_days=new_streak,
                new_balance=new_balance,
                new_tokens=new_tokens,
                message=message
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Signin error: {e}")
            raise HTTPException(status_code=500, detail=str(e))


@router.get("/calendar", response_model=CalendarResponse)
async def get_signin_calendar(
    month: Optional[str] = Query(None, description="月份，格式：YYYY-MM"),
    current_user: dict = Depends(get_current_user)
):
    from ..database import get_db
    
    user_id = current_user.get("id")
    
    if month:
        try:
            year, m = map(int, month.split('-'))
            month_date = date(year, m, 1)
        except:
            month_date = date.today().replace(day=1)
    else:
        month_date = date.today().replace(day=1)
    
    if month_date.month == 12:
        month_end = month_date.replace(year=month_date.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        month_end = month_date.replace(month=month_date.month + 1, day=1) - timedelta(days=1)
    
    async with get_db() as conn:
        try:
            rows = await conn.fetch(
                "SELECT sign_date FROM signin_records WHERE user_id = $1 AND sign_date >= $2 AND sign_date <= $3 ORDER BY sign_date",
                user_id, month_date.isoformat(), month_end.isoformat()
            )
            signed_dates = [row['sign_date'] for row in rows] if rows else []
            
            return CalendarResponse(
                month=month_date.strftime("%Y-%m"),
                signed_dates=signed_dates,
                total_days=len(signed_dates)
            )
        except Exception as e:
            logger.error(f"Get calendar error: {e}")
            raise HTTPException(status_code=500, detail=str(e))


@router.get("/rewards")
async def get_signin_rewards():
    rewards = [
        {"day": 1, "base_reward": 1.0, "bonus_reward": 0.0, "total_reward": 1.0, "description": "连续签到1天"},
        {"day": 3, "base_reward": 1.0, "bonus_reward": 0.0, "total_reward": 1.0, "description": "连续签到3天"},
        {"day": 7, "base_reward": 1.5, "bonus_reward": 0.5, "total_reward": 2.0, "description": "连续签到7天，获得周奖励"},
        {"day": 14, "base_reward": 2.0, "bonus_reward": 0.0, "total_reward": 2.0, "description": "连续签到14天"},
        {"day": 30, "base_reward": 3.0, "bonus_reward": 1.0, "total_reward": 4.0, "description": "连续签到30天，获得月奖励"}
    ]
    return {"rewards": rewards}


@router.post("/makeup")
async def makeup_signin(
    sign_date: str = Query(..., description="补签日期"),
    current_user: dict = Depends(get_current_user)
):
    from ..database import get_db
    
    user_id = current_user.get("id")
    
    try:
        target_date = date.fromisoformat(sign_date)
    except:
        raise HTTPException(status_code=400, detail="无效的日期格式")
    
    today = date.today()
    if target_date >= today:
        raise HTTPException(status_code=400, detail="不能补签今天或未来的日期")
    
    if target_date < today - timedelta(days=7):
        raise HTTPException(status_code=400, detail="只能补签最近7天内的日期")
    
    async with get_db() as conn:
        try:
            result = await conn.fetchval(
                "SELECT 1 FROM signin_records WHERE user_id = $1 AND sign_date = $2",
                user_id, sign_date
            )
            
            if result:
                raise HTTPException(status_code=400, detail="该日期已签到")
            
            reward_integral = 1.0
            reward_tokens = int(reward_integral * TOKEN_MULTIPLIER)
            
            user = await conn.fetchrow(
                "SELECT integral FROM users WHERE id = $1",
                user_id
            )
            
            if not user:
                raise HTTPException(status_code=404, detail="用户不存在")
            
            old_balance = float(user['integral'] or 0)
            new_balance = old_balance + reward_integral
            new_tokens = int(new_balance * TOKEN_MULTIPLIER)
            
            signin_id = str(uuid.uuid4())
            await conn.execute(
                "INSERT INTO signin_records (id, user_id, sign_date, reward_integral, consecutive_days) VALUES ($1, $2, $3, $4, 0)",
                signin_id, user_id, sign_date, reward_integral
            )
            
            await conn.execute(
                "UPDATE users SET integral = $1 WHERE id = $2",
                new_balance, user_id
            )
            
            log_id = str(uuid.uuid4())
            await conn.execute(
                "INSERT INTO integral_logs (id, user_id, change, balance_after, token_change, token_balance_after, reason, action_type, resource_id, resource_type, created_at) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)",
                log_id, user_id, reward_integral, new_balance, reward_tokens, new_tokens,
                f"补签奖励({sign_date})", "makeup_signin", signin_id, "signin", datetime.now().isoformat()
            )
            
            return {
                "success": True,
                "reward_integral": reward_integral,
                "reward_tokens": reward_tokens,
                "new_balance": new_balance,
                "new_tokens": new_tokens,
                "message": f"补签成功！获得{reward_integral}积分"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Makeup signin error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
