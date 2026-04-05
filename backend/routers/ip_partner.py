"""
IP扶持计划 - IP端接口
包含仪表盘、链接管理、推广用户、佣金明细、提现申请、内容工具等
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timedelta
import uuid
import json
import logging
import random
import string

from backend.database import get_db_connection, get_db
from backend.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ip", tags=["ip_partner"])

async def get_ip_partner(user_id: str):
    """获取用户的IP合作伙伴信息"""
    async with get_db() as conn:
        cursor = await conn.cursor()
        
        await cursor.execute('''
            SELECT p.*, l.level_name, l.commission_bonus as level_bonus, l.color as level_color
            FROM ip_partners p
            LEFT JOIN ip_levels l ON p.level = l.level_code
            WHERE p.user_id = ? AND p.status IN ('trial', 'active')
        ''', (user_id,))
        partner = await cursor.fetchone()
        
        return dict(partner) if partner else None

async def require_ip_partner(current_user = Depends(get_current_user)):
    """验证用户是否为IP创作者"""
    partner = await get_ip_partner(current_user['id'])
    if not partner:
        raise HTTPException(status_code=403, detail="您不是IP创作者或账号未激活，请先申请成为IP创作者")
    return partner

class GenerateLinkRequest(BaseModel):
    link_type: str = Field(..., description="链接类型: short_url/qrcode/poster")
    channel: Optional[str] = Field(None, description="推广渠道: wechat/zhihu/douyin等")
    description: Optional[str] = Field(None, max_length=200)

class WithdrawRequest(BaseModel):
    amount: float = Field(..., gt=0, description="提现金额")
    account_type: str = Field(..., description="账户类型: wechat/alipay/bank")
    account_name: str = Field(..., description="账户名")
    account_info: str = Field(..., description="账户信息")

class SaveDraftRequest(BaseModel):
    title: str
    content: str
    content_type: str = Field(default="article")
    tags: Optional[str] = None

@router.get("/dashboard")
async def get_dashboard(partner = Depends(require_ip_partner)):
    """获取IP仪表盘数据"""
    async with get_db() as conn:
        cursor = await conn.cursor()
        
        today = datetime.now().date()
        month_start = today.replace(day=1)
        
        await cursor.execute('''
            SELECT COUNT(*) as count FROM ip_referrals 
            WHERE ip_id = ? AND date(registered_at) = ?
        ''', (partner['id'], today))
        today_new = (await cursor.fetchone())['count']
        
        await cursor.execute('''
            SELECT COALESCE(SUM(commission_amount), 0) as total
            FROM ip_commissions
            WHERE ip_id = ? AND date(created_at) = ?
        ''', (partner['id'], today))
        today_commission = (await cursor.fetchone())['total']
        
        await cursor.execute('''
            SELECT COUNT(*) as count FROM ip_referrals 
            WHERE ip_id = ? AND date(registered_at) >= ?
        ''', (partner['id'], month_start))
        month_new = (await cursor.fetchone())['count']
        
        await cursor.execute('''
            SELECT COALESCE(SUM(commission_amount), 0) as total
            FROM ip_commissions
            WHERE ip_id = ? AND date(created_at) >= ?
        ''', (partner['id'], month_start))
        month_commission = (await cursor.fetchone())['total']
        
        await cursor.execute('''
            SELECT COALESCE(SUM(commission_amount), 0) as total
            FROM ip_commissions
            WHERE ip_id = ? AND status = 'pending'
        ''', (partner['id'],))
        pending_commission = (await cursor.fetchone())['total']
        
        trend_dates = []
        trend_users = []
        trend_commission = []
        
        for i in range(29, -1, -1):
            d = today - timedelta(days=i)
            trend_dates.append(str(d))
            
            await cursor.execute('''
                SELECT COUNT(*) as count FROM ip_referrals 
                WHERE ip_id = ? AND date(registered_at) = ?
            ''', (partner['id'], d))
            count = (await cursor.fetchone())['count']
            trend_users.append(count)
            
            await cursor.execute('''
                SELECT COALESCE(SUM(commission_amount), 0) as total
                FROM ip_commissions
                WHERE ip_id = ? AND date(created_at) = ?
            ''', (partner['id'], d))
            comm = (await cursor.fetchone())['total']
            trend_commission.append(round(comm, 2))
        
        await cursor.execute('''
            SELECT COALESCE(SUM(click_count), 0) as total
            FROM ip_links WHERE ip_id = ?
        ''', (partner['id'],))
        total_clicks = (await cursor.fetchone())['total']
        
        total_registers = partner['total_referrals']
        
        await cursor.execute('''
            SELECT COUNT(*) as count FROM ip_referrals 
            WHERE ip_id = ? AND total_orders > 0
        ''', (partner['id'],))
        total_orders = (await cursor.fetchone())['count']
        
        conversion_rate = round(total_orders / total_registers * 100, 2) if total_registers > 0 else 0
        
        await cursor.execute('''
            SELECT r.id, r.registered_at, r.total_orders, r.total_amount, r.status,
                   u.email, u.username
            FROM ip_referrals r
            LEFT JOIN users u ON r.user_id = u.id
            WHERE r.ip_id = ?
            ORDER BY r.registered_at DESC
            LIMIT 5
        ''', (partner['id'],))
        recent_referrals = [dict(r) for r in await cursor.fetchall()]
        
        for r in recent_referrals:
            if r['email']:
                email = r['email']
                r['email'] = email[:3] + '***' + email.split('@')[-1] if '@' in email else email[:3] + '***'
        
        return {
            "basic": {
                "id": partner['id'],
                "name": partner['name'],
                "level": partner['level'],
                "level_name": partner['level_name'] or '青铜创作者',
                "level_color": partner['level_color'] or '#CD7F32',
                "base_commission": partner['base_commission'],
                "balance": partner['balance'],
                "frozen_balance": partner['frozen_balance'],
                "total_earned": partner['total_earned'],
                "total_referrals": partner['total_referrals'],
                "status": partner['status']
            },
            "today": {
                "new_users": today_new,
                "commission": round(today_commission, 2)
            },
            "month": {
                "new_users": month_new,
                "commission": round(month_commission, 2)
            },
            "pending_commission": round(pending_commission, 2),
            "trend": {
                "dates": trend_dates,
                "new_users": trend_users,
                "commission": trend_commission
            },
            "funnel": {
                "clicks": total_clicks,
                "registers": total_registers,
                "orders": total_orders,
                "conversion_rate": conversion_rate
            },
            "recent_referrals": recent_referrals
        }


@router.get("/links")
async def get_links(partner = Depends(require_ip_partner)):
    """获取推广链接列表"""
    conn = get_db_connection()
    conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
    cursor = conn.cursor()
    
    try:
        links = cursor.execute('''
            SELECT * FROM ip_links
            WHERE ip_id = ?
            ORDER BY created_at DESC
        ''', (partner['id'],)).fetchall()
        
        return {"links": links}
    finally:
        conn.close()

@router.post("/links")
async def generate_link(request: GenerateLinkRequest, partner = Depends(require_ip_partner)):
    """生成推广链接"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        code = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        
        while cursor.execute("SELECT id FROM ip_links WHERE code = ?", (code,)).fetchone():
            code = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        
        base_url = "https://fangtanai.com/r"
        url = f"{base_url}/{code}"
        
        link_id = str(uuid.uuid4())
        
        cursor.execute('''
            INSERT INTO ip_links (id, ip_id, link_type, url, code, channel, description, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (link_id, partner['id'], request.link_type, url, code, 
              request.channel, request.description, datetime.now()))
        
        conn.commit()
        
        return {
            "success": True,
            "link": {
                "id": link_id,
                "link_type": request.link_type,
                "url": url,
                "code": code,
                "channel": request.channel,
                "description": request.description
            }
        }
        
    except Exception as e:
        logger.error(f"Generate link error: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail="生成链接失败")
    finally:
        conn.close()

@router.delete("/links/{link_id}")
async def delete_link(link_id: str, partner = Depends(require_ip_partner)):
    """删除推广链接"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        result = cursor.execute(
            "UPDATE ip_links SET is_active = 0 WHERE id = ? AND ip_id = ?",
            (link_id, partner['id'])
        )
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="链接不存在")
        
        conn.commit()
        return {"success": True}
        
    finally:
        conn.close()

@router.get("/referrals")
async def get_referrals(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    partner = Depends(require_ip_partner)
):
    """获取推广用户列表"""
    conn = get_db_connection()
    conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
    cursor = conn.cursor()
    
    try:
        offset = (page - 1) * limit
        
        where_clause = "WHERE ip_id = ?"
        params = [partner['id']]
        
        if start_date:
            where_clause += " AND date(registered_at) >= ?"
            params.append(start_date)
        if end_date:
            where_clause += " AND date(registered_at) <= ?"
            params.append(end_date)
        
        total = cursor.execute(f"SELECT COUNT(*) as count FROM ip_referrals {where_clause}", params).fetchone()['count']
        
        params.extend([limit, offset])
        referrals = cursor.execute(f'''
            SELECT r.*, u.email, u.username
            FROM ip_referrals r
            LEFT JOIN users u ON r.user_id = u.id
            {where_clause}
            ORDER BY r.registered_at DESC
            LIMIT ? OFFSET ?
        ''', params).fetchall()
        
        for r in referrals:
            if r['email']:
                email = r['email']
                r['email'] = email[:3] + '***' + email.split('@')[-1] if '@' in email else email[:3] + '***'
        
        return {
            "total": total,
            "page": page,
            "limit": limit,
            "referrals": referrals
        }
        
    finally:
        conn.close()

@router.get("/commissions")
async def get_commissions(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    partner = Depends(require_ip_partner)
):
    """获取佣金明细"""
    conn = get_db_connection()
    conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
    cursor = conn.cursor()
    
    try:
        offset = (page - 1) * limit
        
        where_clause = "WHERE ip_id = ?"
        params = [partner['id']]
        
        if status:
            where_clause += " AND status = ?"
            params.append(status)
        
        total = cursor.execute(f"SELECT COUNT(*) as count FROM ip_commissions {where_clause}", params).fetchone()['count']
        
        params.extend([limit, offset])
        commissions = cursor.execute(f'''
            SELECT * FROM ip_commissions
            {where_clause}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        ''', params).fetchall()
        
        return {
            "total": total,
            "page": page,
            "limit": limit,
            "commissions": commissions
        }
        
    finally:
        conn.close()

@router.post("/withdraw")
async def apply_withdraw(request: WithdrawRequest, partner = Depends(require_ip_partner)):
    """申请提现"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        min_withdraw = 10.0
        if request.amount < min_withdraw:
            raise HTTPException(status_code=400, detail=f"最低提现金额为{min_withdraw}元")
        
        if request.amount > partner['balance']:
            raise HTTPException(status_code=400, detail="余额不足")
        
        fee = round(request.amount * 0.01, 2)
        actual_amount = round(request.amount - fee, 2)
        
        withdrawal_id = str(uuid.uuid4())
        
        cursor.execute('''
            INSERT INTO ip_withdrawals (
                id, ip_id, amount, fee, actual_amount, 
                account_type, account_name, account_info, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)
        ''', (withdrawal_id, partner['id'], request.amount, fee, actual_amount,
              request.account_type, request.account_name, request.account_info, datetime.now()))
        
        cursor.execute('''
            UPDATE ip_partners 
            SET balance = balance - ?, frozen_balance = frozen_balance + ?, updated_at = ?
            WHERE id = ?
        ''', (request.amount, request.amount, datetime.now(), partner['id']))
        
        conn.commit()
        
        return {
            "success": True,
            "withdrawal_id": withdrawal_id,
            "amount": request.amount,
            "fee": fee,
            "actual_amount": actual_amount,
            "message": "提现申请已提交，请等待审核"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Withdraw error: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail="提现申请失败")
    finally:
        conn.close()

@router.get("/withdrawals")
async def get_withdrawals(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    partner = Depends(require_ip_partner)
):
    """获取提现记录"""
    conn = get_db_connection()
    conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
    cursor = conn.cursor()
    
    try:
        offset = (page - 1) * limit
        
        total = cursor.execute(
            "SELECT COUNT(*) as count FROM ip_withdrawals WHERE ip_id = ?",
            (partner['id'],)
        ).fetchone()['count']
        
        withdrawals = cursor.execute('''
            SELECT * FROM ip_withdrawals
            WHERE ip_id = ?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        ''', (partner['id'], limit, offset)).fetchall()
        
        return {
            "total": total,
            "page": page,
            "limit": limit,
            "withdrawals": withdrawals
        }
        
    finally:
        conn.close()

@router.get("/content/drafts")
async def get_drafts(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    partner = Depends(require_ip_partner)
):
    """获取内容草稿列表"""
    conn = get_db_connection()
    conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
    cursor = conn.cursor()
    
    try:
        offset = (page - 1) * limit
        
        total = cursor.execute(
            "SELECT COUNT(*) as count FROM ip_content_drafts WHERE ip_id = ?",
            (partner['id'],)
        ).fetchone()['count']
        
        drafts = cursor.execute('''
            SELECT id, title, content_type, status, view_count, tags, created_at, updated_at
            FROM ip_content_drafts
            WHERE ip_id = ?
            ORDER BY updated_at DESC
            LIMIT ? OFFSET ?
        ''', (partner['id'], limit, offset)).fetchall()
        
        return {
            "total": total,
            "page": page,
            "limit": limit,
            "drafts": drafts
        }
        
    finally:
        conn.close()

@router.post("/content/drafts")
async def save_draft(request: SaveDraftRequest, partner = Depends(require_ip_partner)):
    """保存内容草稿"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        draft_id = str(uuid.uuid4())
        
        cursor.execute('''
            INSERT INTO ip_content_drafts (
                id, ip_id, title, content, content_type, tags, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (draft_id, partner['id'], request.title, request.content,
              request.content_type, request.tags, datetime.now(), datetime.now()))
        
        conn.commit()
        
        return {
            "success": True,
            "draft_id": draft_id,
            "message": "草稿保存成功"
        }
        
    except Exception as e:
        logger.error(f"Save draft error: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail="保存失败")
    finally:
        conn.close()

@router.get("/content/drafts/{draft_id}")
async def get_draft(draft_id: str, partner = Depends(require_ip_partner)):
    """获取草稿详情"""
    conn = get_db_connection()
    conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
    cursor = conn.cursor()
    
    try:
        draft = cursor.execute('''
            SELECT * FROM ip_content_drafts
            WHERE id = ? AND ip_id = ?
        ''', (draft_id, partner['id'])).fetchone()
        
        if not draft:
            raise HTTPException(status_code=404, detail="草稿不存在")
        
        return draft
        
    finally:
        conn.close()

@router.put("/content/drafts/{draft_id}")
async def update_draft(draft_id: str, request: SaveDraftRequest, partner = Depends(require_ip_partner)):
    """更新草稿"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        result = cursor.execute('''
            UPDATE ip_content_drafts
            SET title = ?, content = ?, content_type = ?, tags = ?, updated_at = ?
            WHERE id = ? AND ip_id = ?
        ''', (request.title, request.content, request.content_type, 
              request.tags, datetime.now(), draft_id, partner['id']))
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="草稿不存在")
        
        conn.commit()
        
        return {"success": True, "message": "更新成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update draft error: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail="更新失败")
    finally:
        conn.close()

@router.delete("/content/drafts/{draft_id}")
async def delete_draft(draft_id: str, partner = Depends(require_ip_partner)):
    """删除草稿"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        result = cursor.execute(
            "DELETE FROM ip_content_drafts WHERE id = ? AND ip_id = ?",
            (draft_id, partner['id'])
        )
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="草稿不存在")
        
        conn.commit()
        
        return {"success": True}
        
    finally:
        conn.close()

@router.get("/profile")
async def get_profile(partner = Depends(require_ip_partner)):
    """获取IP个人资料"""
    conn = get_db_connection()
    conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
    cursor = conn.cursor()
    
    try:
        profile = cursor.execute('''
            SELECT id, name, contact, email, avatar, platform_type, platform_id,
                   platform_name, followers, introduction, level, status,
                   base_commission, total_earned, balance, total_referrals,
                   contract_signed, created_at
            FROM ip_partners
            WHERE id = ?
        ''', (partner['id'],)).fetchone()
        
        level_info = cursor.execute(
            "SELECT level_name, color FROM ip_levels WHERE level_code = ?",
            (profile['level'],)
        ).fetchone()
        
        if level_info:
            profile['level_name'] = level_info['level_name']
            profile['level_color'] = level_info['color']
        
        return profile
        
    finally:
        conn.close()

@router.put("/profile")
async def update_profile(
    contact: Optional[str] = None,
    introduction: Optional[str] = None,
    avatar: Optional[str] = None,
    partner = Depends(require_ip_partner)
):
    """更新IP个人资料"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        updates = []
        params = []
        
        if contact:
            updates.append("contact = ?")
            params.append(contact)
        if introduction:
            updates.append("introduction = ?")
            params.append(introduction)
        if avatar:
            updates.append("avatar = ?")
            params.append(avatar)
        
        if not updates:
            return {"success": True, "message": "无更新"}
        
        updates.append("updated_at = ?")
        params.append(datetime.now())
        params.append(partner['id'])
        
        cursor.execute(
            f"UPDATE ip_partners SET {', '.join(updates)} WHERE id = ?",
            params
        )
        
        conn.commit()
        
        return {"success": True, "message": "更新成功"}
        
    except Exception as e:
        logger.error(f"Update profile error: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail="更新失败")
    finally:
        conn.close()
