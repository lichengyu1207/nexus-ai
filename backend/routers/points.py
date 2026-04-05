"""
积分与会员体系API路由
包含签到、上传数据、邀请好友、积分兑换会员等功能
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date, timedelta
import uuid
import random
import json

from ..database_pg import PostgreSQLConnectionPool, PGConnection
from ..auth import get_current_user, require_admin

router = APIRouter(prefix="/api/points", tags=["points"])

# 签到奖励规则：第1天10，第2天20，第3天30，第4天50，第5天80，第6天120，第7天200
SIGNIN_REWARDS = [10, 20, 30, 50, 80, 120, 200]

# 会员价格（积分）
MEMBERSHIP_PRICES = {
    "experience": {"price": 500, "days": 3, "name": "体验会员"},
    "monthly": {"price": 3000, "days": 30, "name": "月度会员"},
    "quarterly": {"price": 8000, "days": 90, "name": "季度会员"},
    "annual": {"price": 28000, "days": 365, "name": "年度会员"},
}


class UploadDataRequest(BaseModel):
    data_type: str
    data_content: dict


class ExchangeMembershipRequest(BaseModel):
    membership_type: str


async def get_pg_connection():
    """获取PostgreSQL连接"""
    pool = await PostgreSQLConnectionPool.get_instance()
    async with pool.get_connection() as conn:
        yield PGConnection(conn)


# ==================== 签到接口 ====================

@router.get("/signin/status")
async def get_signin_status(current_user: dict = Depends(get_current_user)):
    """获取签到状态"""
    user_id = current_user["id"]
    today = date.today()
    
    pool = await PostgreSQLConnectionPool.get_instance()
    async with pool.get_connection() as raw_conn:
        conn = PGConnection(raw_conn)
        
        # 检查今日是否已签到
        today_record = await conn.fetchrow(
            "SELECT * FROM signin_records WHERE user_id = $1 AND sign_date = $2",
            user_id, today.isoformat()
        )
        
        # 获取连续签到天数
        last_record = await conn.fetchrow(
            "SELECT consecutive_days, sign_date FROM signin_records WHERE user_id = $1 ORDER BY sign_date DESC LIMIT 1",
            user_id
        )
        
        consecutive_days = 0
        if last_record:
            last_date = last_record['sign_date']
            if isinstance(last_date, str):
                last_date = datetime.strptime(last_date, "%Y-%m-%d").date()
            if last_date == today:
                consecutive_days = last_record['consecutive_days']
            elif last_date == today - timedelta(days=1):
                consecutive_days = last_record['consecutive_days']
            else:
                consecutive_days = 0
        
        # 获取本月签到记录
        month_start = today.replace(day=1)
        month_records = await conn.fetch(
            "SELECT sign_date FROM signin_records WHERE user_id = $1 AND sign_date >= $2",
            user_id, month_start.isoformat()
        )
        signed_dates = [str(r['sign_date']) for r in month_records]
        
        # 计算今日奖励
        next_day = consecutive_days + 1 if not today_record else consecutive_days
        today_reward = SIGNIN_REWARDS[(next_day - 1) % 7]
        
        return {
            "today_signed": today_record is not None,
            "consecutive_days": consecutive_days,
            "today_reward": today_reward if not today_record else 0,
            "next_day": next_day if not today_record else consecutive_days,
            "signed_dates": signed_dates,
            "rewards_table": SIGNIN_REWARDS
        }


@router.post("/signin")
async def do_signin(current_user: dict = Depends(get_current_user)):
    """执行签到"""
    user_id = current_user["id"]
    today = date.today()
    
    pool = await PostgreSQLConnectionPool.get_instance()
    async with pool.get_connection() as raw_conn:
        conn = PGConnection(raw_conn)
        
        # 检查今日是否已签到
        today_record = await conn.fetchrow(
            "SELECT * FROM signin_records WHERE user_id = $1 AND sign_date = $2",
            user_id, today.isoformat()
        )
        if today_record:
            raise HTTPException(status_code=400, detail="今日已签到")
        
        # 计算连续天数
        last_record = await conn.fetchrow(
            "SELECT consecutive_days, sign_date FROM signin_records WHERE user_id = $1 ORDER BY sign_date DESC LIMIT 1",
            user_id
        )
        
        consecutive_days = 1
        if last_record:
            last_date = last_record['sign_date']
            if isinstance(last_date, str):
                last_date = datetime.strptime(last_date, "%Y-%m-%d").date()
            if last_date == today - timedelta(days=1):
                consecutive_days = last_record['consecutive_days'] + 1
        
        # 计算奖励
        reward = SIGNIN_REWARDS[(consecutive_days - 1) % 7]
        
        # 插入签到记录
        record_id = str(uuid.uuid4())
        await conn.execute(
            "INSERT INTO signin_records (id, user_id, sign_date, consecutive_days, reward_integral, created_at) VALUES ($1, $2, $3, $4, $5, $6)",
            record_id, user_id, today.isoformat(), consecutive_days, reward, datetime.now()
        )
        
        # 增加用户积分
        await conn.execute(
            "UPDATE users SET integral = integral + $1, total_earned_integral = COALESCE(total_earned_integral, 0) + $2 WHERE id = $3",
            reward, reward, user_id
        )
        
        # 记录积分日志
        log_id = str(uuid.uuid4())
        await conn.execute(
            "INSERT INTO integral_logs (id, user_id, change, reason, description, created_at) VALUES ($1, $2, $3, $4, $5, $6)",
            log_id, user_id, reward, "signin", f"签到奖励（连续{consecutive_days}天）", datetime.now()
        )
        
        return {
            "success": True,
            "reward": reward,
            "consecutive_days": consecutive_days,
            "message": f"签到成功！获得{reward}积分" + (f"，连续签到{consecutive_days}天" if consecutive_days > 1 else "")
        }


# ==================== 会员接口 ====================

@router.get("/membership/prices")
async def get_membership_prices():
    """获取会员价格列表"""
    return MEMBERSHIP_PRICES


@router.get("/membership/status")
async def get_membership_status(current_user: dict = Depends(get_current_user)):
    """获取当前会员状态"""
    user_id = current_user["id"]
    
    pool = await PostgreSQLConnectionPool.get_instance()
    async with pool.get_connection() as raw_conn:
        conn = PGConnection(raw_conn)
        
        membership = await conn.fetchrow(
            "SELECT membership_type, start_date, end_date FROM user_membership WHERE user_id = $1",
            user_id
        )
        
        if not membership:
            return {
                "membership_type": "free",
                "start_date": None,
                "end_date": None,
                "remaining_days": 0,
                "is_active": False
            }
        
        end_date = membership['end_date']
        remaining_days = (end_date - date.today()).days if end_date else 0
        
        return {
            "membership_type": membership['membership_type'],
            "start_date": str(membership['start_date']) if membership['start_date'] else None,
            "end_date": str(end_date) if end_date else None,
            "remaining_days": max(0, remaining_days),
            "is_active": remaining_days > 0
        }


@router.post("/membership/exchange")
async def exchange_membership(
    request: ExchangeMembershipRequest,
    current_user: dict = Depends(get_current_user)
):
    """积分兑换会员"""
    user_id = current_user["id"]
    membership_type = request.membership_type
    
    if membership_type not in MEMBERSHIP_PRICES:
        raise HTTPException(status_code=400, detail="无效的会员类型")
    
    price_info = MEMBERSHIP_PRICES[membership_type]
    cost = price_info["price"]
    days = price_info["days"]
    
    pool = await PostgreSQLConnectionPool.get_instance()
    async with pool.get_connection() as raw_conn:
        conn = PGConnection(raw_conn)
        
        # 检查用户积分
        user = await conn.fetchrow(
            "SELECT integral FROM users WHERE id = $1",
            user_id
        )
        if not user or user['integral'] < cost:
            raise HTTPException(status_code=400, detail=f"积分不足，需要{cost}积分")
        
        # 扣除积分
        await conn.execute(
            "UPDATE users SET integral = integral - $1 WHERE id = $2",
            cost, user_id
        )
        
        # 更新会员状态
        existing = await conn.fetchrow(
            "SELECT end_date FROM user_membership WHERE user_id = $1",
            user_id
        )
        
        start_date = date.today()
        if existing and existing['end_date']:
            existing_end = existing['end_date']
            if existing_end > date.today():
                start_date = existing_end
        
        end_date = start_date + timedelta(days=days)
        
        await conn.execute(
            """INSERT INTO user_membership (user_id, membership_type, start_date, end_date, created_at, updated_at) 
               VALUES ($1, $2, $3, $4, $5, $6) 
               ON CONFLICT(user_id) DO UPDATE SET membership_type = $2, start_date = $3, end_date = $4, updated_at = $6""",
            user_id, membership_type, start_date, end_date, datetime.now(), datetime.now()
        )
        
        # 记录兑换日志
        log_id = str(uuid.uuid4())
        await conn.execute(
            "INSERT INTO membership_exchange_logs (id, user_id, membership_type, cost_integral, exchanged_at) VALUES ($1, $2, $3, $4, $5)",
            log_id, user_id, membership_type, cost, datetime.now()
        )
        
        # 记录积分日志
        await conn.execute(
            "INSERT INTO integral_logs (id, user_id, change, reason, description, created_at) VALUES ($1, $2, $3, $4, $5, $6)",
            str(uuid.uuid4()), user_id, -cost, "exchange_membership", f"兑换{price_info['name']}", datetime.now()
        )
        
        return {
            "success": True,
            "membership_type": membership_type,
            "membership_name": price_info["name"],
            "cost": cost,
            "end_date": str(end_date),
            "message": f"兑换成功！{price_info['name']}有效期至{end_date.strftime('%Y-%m-%d')}"
        }


# ==================== 邀请好友接口 ====================

@router.post("/invite/create")
async def create_invite(current_user: dict = Depends(get_current_user)):
    """生成邀请码"""
    user_id = current_user["id"]
    
    pool = await PostgreSQLConnectionPool.get_instance()
    async with pool.get_connection() as raw_conn:
        conn = PGConnection(raw_conn)
        
        # 检查是否已有邀请码
        existing = await conn.fetchrow(
            "SELECT invite_code FROM invite_records WHERE inviter_id = $1 AND invitee_id IS NULL LIMIT 1",
            user_id
        )
        if existing:
            return {"invite_code": existing['invite_code'], "invite_link": f"https://fangdu.com/register?invite_code={existing['invite_code']}"}
        
        # 生成新邀请码
        invite_code = f"INV-{random.randint(100000, 999999)}"
        record_id = str(uuid.uuid4())
        await conn.execute(
            "INSERT INTO invite_records (id, inviter_id, invite_code, status, created_at) VALUES ($1, $2, $3, $4, $5)",
            record_id, user_id, invite_code, "pending", datetime.now()
        )
        
        return {
            "invite_code": invite_code,
            "invite_link": f"https://fangdu.com/register?invite_code={invite_code}"
        }


@router.get("/invite/stats")
async def get_invite_stats(current_user: dict = Depends(get_current_user)):
    """获取邀请统计"""
    user_id = current_user["id"]
    
    pool = await PostgreSQLConnectionPool.get_instance()
    async with pool.get_connection() as raw_conn:
        conn = PGConnection(raw_conn)
        
        # 获取邀请码
        code_record = await conn.fetchrow(
            "SELECT invite_code FROM invite_records WHERE inviter_id = $1 AND invitee_id IS NULL LIMIT 1",
            user_id
        )
        invite_code = code_record['invite_code'] if code_record else None
        
        # 获取邀请统计
        stats = await conn.fetchrow(
            "SELECT COUNT(*) as count, COALESCE(SUM(reward_inviter), 0) as total FROM invite_records WHERE inviter_id = $1 AND status = 'completed'",
            user_id
        )
        
        return {
            "invite_code": invite_code,
            "invite_link": f"https://fangdu.com/register?invite_code={invite_code}" if invite_code else None,
            "invited_count": stats['count'] if stats else 0,
            "total_reward": float(stats['total']) if stats else 0
        }


# ==================== 微信添加状态 ====================

@router.post("/wechat-added")
async def mark_wechat_added(current_user: dict = Depends(get_current_user)):
    """标记已添加微信"""
    user_id = current_user["id"]
    
    pool = await PostgreSQLConnectionPool.get_instance()
    async with pool.get_connection() as raw_conn:
        conn = PGConnection(raw_conn)
        await conn.execute(
            "UPDATE users SET wechat_added = $1 WHERE id = $2",
            True, user_id
        )
    
    return {"success": True, "message": "感谢添加！"}
