"""
IP扶持计划 - 管理员接口
包含IP申请审核、IP列表管理、提现管理、佣金规则配置、数据统计等
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timedelta
import uuid
import json
import logging

from backend.database import get_db_connection
from backend.auth import require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/ip", tags=["admin_ip"])

class ReviewApplicationRequest(BaseModel):
    action: str = Field(..., description="approve/reject/trial")
    commission_rate: Optional[float] = Field(None, ge=0, le=100, description="佣金比例")
    notes: Optional[str] = Field(None, max_length=500)

class ProcessWithdrawalRequest(BaseModel):
    action: str = Field(..., description="approve/reject")
    admin_notes: Optional[str] = Field(None, max_length=500)

class UpdateIPRequest(BaseModel):
    name: Optional[str] = None
    contact: Optional[str] = None
    email: Optional[str] = None
    level: Optional[str] = None
    base_commission: Optional[float] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class UpdateCommissionRuleRequest(BaseModel):
    name: Optional[str] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    commission_rate: Optional[float] = None
    bonus_rate: Optional[float] = None
    is_active: Optional[int] = None

@router.get("/applications")
async def get_applications(
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    admin = Depends(require_admin)
):
    """获取IP申请列表"""
    conn = await get_db_connection()
    cursor = await conn.cursor()
    
    try:
        offset = (page - 1) * limit
        
        where_clause = "WHERE 1=1"
        params = []
        
        if status:
            where_clause += " AND status = ?"
            params.append(status)
        
        total = await cursor.execute(f"SELECT COUNT(*) as count FROM ip_partners {where_clause}", params).fetchone()['count']
        
        params.extend([limit, offset])
        applications = await cursor.execute(f'''
            SELECT id, name, contact, email, platform_type, platform_id, platform_name,
                   followers, introduction, status, level, base_commission, created_at, notes
            FROM ip_partners
            {where_clause}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        ''', params).fetchall()
        
        return {
            "total": total,
            "page": page,
            "limit": limit,
            "applications": applications
        }
        
    finally:
        await conn.close()

@router.get("/applications/{application_id}")
async def get_application(application_id: str, admin = Depends(require_admin)):
    """获取申请详情"""
    conn = await get_db_connection()
    cursor = await conn.cursor()
    
    try:
        application = await cursor.execute('''
            SELECT * FROM ip_partners WHERE id = ?
        ''', (application_id,)).fetchone()
        
        if not application:
            raise HTTPException(status_code=404, detail="申请不存在")
        
        return application
        
    finally:
        await conn.close()

@router.post("/applications/{application_id}/review")
async def review_application(
    application_id: str,
    request: ReviewApplicationRequest,
    admin = Depends(require_admin)
):
    """审核IP申请"""
    conn = await get_db_connection()
    cursor = await conn.cursor()
    
    try:
        application = await cursor.execute(
            "SELECT * FROM ip_partners WHERE id = ?",
            (application_id,)
        ).fetchone()
        
        if not application:
            raise HTTPException(status_code=404, detail="申请不存在")
        
        if application['status'] != 'pending':
            raise HTTPException(status_code=400, detail="该申请已处理")
        
        new_status = 'rejected' if request.action == 'reject' else ('trial' if request.action == 'trial' else 'active')
        
        commission = request.commission_rate or application['base_commission'] or 5.0
        
        await cursor.execute('''
            UPDATE ip_partners
            SET status = ?, base_commission = ?, notes = ?, updated_at = ?
            WHERE id = ?
        ''', (new_status, commission, request.notes, datetime.now(), application_id))
        
        await cursor.execute('''
            INSERT INTO ip_operation_logs (id, ip_id, operator_id, operation_type, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (str(uuid.uuid4()), application_id, admin['id'], 'review',
              f"审核结果: {new_status}, 佣金: {commission}%", datetime.now()))
        
        await conn.commit()
        
        return {
            "success": True,
            "message": "审核完成",
            "new_status": new_status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Review application error: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail="审核失败")
    finally:
        await conn.close()

@router.get("")
async def get_ip_list(
    status: Optional[str] = None,
    level: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    admin = Depends(require_admin)
):
    """获取IP列表"""
    conn = await get_db_connection()
    cursor = await conn.cursor()
    
    try:
        offset = (page - 1) * limit
        
        where_clause = "WHERE 1=1"
        params = []
        
        if status:
            where_clause += " AND p.status = ?"
            params.append(status)
        if level:
            where_clause += " AND p.level = ?"
            params.append(level)
        if search:
            where_clause += " AND (p.name LIKE ? OR p.email LIKE ? OR p.contact LIKE ?)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term, search_term])
        
        total = await cursor.execute(f"SELECT COUNT(*) as count FROM ip_partners p {where_clause}", params).fetchone()['count']
        
        params.extend([limit, offset])
        ips = await cursor.execute(f'''
            SELECT p.*, l.level_name, l.color as level_color
            FROM ip_partners p
            LEFT JOIN ip_levels l ON p.level = l.level_code
            {where_clause}
            ORDER BY p.created_at DESC
            LIMIT ? OFFSET ?
        ''', params).fetchall()
        
        return {
            "total": total,
            "page": page,
            "limit": limit,
            "ips": ips
        }
        
    finally:
        await conn.close()

@router.get("/{ip_id}")
async def get_ip_detail(ip_id: str, admin = Depends(require_admin)):
    """获取IP详情"""
    conn = await get_db_connection()
    cursor = await conn.cursor()
    
    try:
        ip = await cursor.execute('''
            SELECT p.*, l.level_name, l.color as level_color
            FROM ip_partners p
            LEFT JOIN ip_levels l ON p.level = l.level_code
            WHERE p.id = ?
        ''', (ip_id,)).fetchone()
        
        if not ip:
            raise HTTPException(status_code=404, detail="IP不存在")
        
        links = await cursor.execute('''
            SELECT * FROM ip_links WHERE ip_id = ? ORDER BY created_at DESC LIMIT 10
        ''', (ip_id,)).fetchall()
        
        recent_commissions = await cursor.execute('''
            SELECT * FROM ip_commissions WHERE ip_id = ? ORDER BY created_at DESC LIMIT 10
        ''', (ip_id,)).fetchall()
        
        recent_withdrawals = await cursor.execute('''
            SELECT * FROM ip_withdrawals WHERE ip_id = ? ORDER BY created_at DESC LIMIT 5
        ''', (ip_id,)).fetchall()
        
        return {
            "ip": ip,
            "links": links,
            "recent_commissions": recent_commissions,
            "recent_withdrawals": recent_withdrawals
        }
        
    finally:
        await conn.close()

@router.put("/{ip_id}")
async def update_ip(ip_id: str, request: UpdateIPRequest, admin = Depends(require_admin)):
    """更新IP信息"""
    conn = await get_db_connection()
    cursor = await conn.cursor()
    
    try:
        updates = []
        params = []
        
        if request.name:
            updates.append("name = ?")
            params.append(request.name)
        if request.contact:
            updates.append("contact = ?")
            params.append(request.contact)
        if request.email:
            updates.append("email = ?")
            params.append(request.email)
        if request.level:
            updates.append("level = ?")
            params.append(request.level)
        if request.base_commission is not None:
            updates.append("base_commission = ?")
            params.append(request.base_commission)
        if request.status:
            updates.append("status = ?")
            params.append(request.status)
        if request.notes:
            updates.append("admin_notes = ?")
            params.append(request.notes)
        
        if not updates:
            return {"success": True, "message": "无更新"}
        
        updates.append("updated_at = ?")
        params.append(datetime.now())
        params.append(ip_id)
        
        result = await cursor.execute(
            f"UPDATE ip_partners SET {', '.join(updates)} WHERE id = ?",
            params
        )
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="IP不存在")
        
        await cursor.execute('''
            INSERT INTO ip_operation_logs (id, ip_id, operator_id, operation_type, notes, created_at)
            VALUES (?, ?, ?, 'update', '管理员更新IP信息', ?)
        ''', (str(uuid.uuid4()), ip_id, admin['id'], datetime.now()))
        
        await conn.commit()
        
        return {"success": True, "message": "更新成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update IP error: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail="更新失败")
    finally:
        await conn.close()

@router.delete("/{ip_id}")
async def delete_ip(ip_id: str, admin = Depends(require_admin)):
    """删除/终止IP"""
    conn = await get_db_connection()
    cursor = await conn.cursor()
    
    try:
        result = await cursor.execute(
            "UPDATE ip_partners SET status = 'terminated', updated_at = ? WHERE id = ?",
            (datetime.now(), ip_id)
        )
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="IP不存在")
        
        await cursor.execute('''
            INSERT INTO ip_operation_logs (id, ip_id, operator_id, operation_type, notes, created_at)
            VALUES (?, ?, ?, 'terminate', '终止合作', ?)
        ''', (str(uuid.uuid4()), ip_id, admin['id'], datetime.now()))
        
        await conn.commit()
        
        return {"success": True, "message": "已终止合作"}
        
    finally:
        await conn.close()

@router.get("/withdrawals")
async def get_withdrawals(
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    admin = Depends(require_admin)
):
    """获取提现申请列表"""
    conn = await get_db_connection()
    cursor = await conn.cursor()
    
    try:
        offset = (page - 1) * limit
        
        where_clause = "WHERE 1=1"
        params = []
        
        if status:
            where_clause += " AND w.status = ?"
            params.append(status)
        
        total = await cursor.execute(f"SELECT COUNT(*) as count FROM ip_withdrawals w {where_clause}", params).fetchone()['count']
        
        params.extend([limit, offset])
        withdrawals = await cursor.execute(f'''
            SELECT w.*, p.name as ip_name, p.contact as ip_contact, p.email as ip_email
            FROM ip_withdrawals w
            JOIN ip_partners p ON w.ip_id = p.id
            {where_clause}
            ORDER BY w.created_at DESC
            LIMIT ? OFFSET ?
        ''', params).fetchall()
        
        return {
            "total": total,
            "page": page,
            "limit": limit,
            "withdrawals": withdrawals
        }
        
    finally:
        await conn.close()

@router.get("/withdrawals/{withdrawal_id}")
async def get_withdrawal_detail(withdrawal_id: str, admin = Depends(require_admin)):
    """获取提现详情"""
    conn = await get_db_connection()
    cursor = await conn.cursor()
    
    try:
        withdrawal = await cursor.execute('''
            SELECT w.*, p.name as ip_name, p.contact as ip_contact, p.email as ip_email,
                   p.balance as ip_balance, p.total_earned as ip_total_earned
            FROM ip_withdrawals w
            JOIN ip_partners p ON w.ip_id = p.id
            WHERE w.id = ?
        ''', (withdrawal_id,)).fetchone()
        
        if not withdrawal:
            raise HTTPException(status_code=404, detail="提现记录不存在")
        
        return withdrawal
        
    finally:
        await conn.close()

@router.post("/withdrawals/{withdrawal_id}/process")
async def process_withdrawal(
    withdrawal_id: str,
    request: ProcessWithdrawalRequest,
    admin = Depends(require_admin)
):
    """处理提现申请"""
    conn = await get_db_connection()
    cursor = await conn.cursor()
    
    try:
        withdrawal = await cursor.execute(
            "SELECT * FROM ip_withdrawals WHERE id = ?",
            (withdrawal_id,)
        ).fetchone()
        
        if not withdrawal:
            raise HTTPException(status_code=404, detail="提现记录不存在")
        
        if withdrawal['status'] != 'pending':
            raise HTTPException(status_code=400, detail="该提现已处理")
        
        new_status = 'completed' if request.action == 'approve' else 'rejected'
        
        await cursor.execute('''
            UPDATE ip_withdrawals
            SET status = ?, admin_notes = ?, processed_at = ?, processed_by = ?
            WHERE id = ?
        ''', (new_status, request.admin_notes, datetime.now(), admin['id'], withdrawal_id))
        
        if request.action == 'reject':
            await cursor.execute('''
                UPDATE ip_partners
                SET balance = balance + ?, frozen_balance = frozen_balance - ?, updated_at = ?
                WHERE id = ?
            ''', (withdrawal['amount'], withdrawal['amount'], datetime.now(), withdrawal['ip_id']))
        
        await cursor.execute('''
            INSERT INTO ip_operation_logs (id, ip_id, operator_id, operation_type, target_type, target_id, notes, created_at)
            VALUES (?, ?, ?, 'withdrawal_process', 'withdrawal', ?, ?, ?)
        ''', (str(uuid.uuid4()), withdrawal['ip_id'], admin['id'], withdrawal_id,
              f"提现处理: {new_status}", datetime.now()))
        
        await conn.commit()
        
        return {
            "success": True,
            "message": "处理完成",
            "new_status": new_status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Process withdrawal error: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail="处理失败")
    finally:
        await conn.close()

@router.get("/commission-rules")
async def get_commission_rules(admin = Depends(require_admin)):
    """获取佣金规则配置"""
    conn = await get_db_connection()
    cursor = await conn.cursor()
    
    try:
        rules = await cursor.execute('''
            SELECT * FROM ip_commission_rules ORDER BY priority ASC
        ''').fetchall()
        
        return {"rules": rules}
    finally:
        await conn.close()

@router.put("/commission-rules/{rule_id}")
async def update_commission_rule(
    rule_id: str,
    request: UpdateCommissionRuleRequest,
    admin = Depends(require_admin)
):
    """更新佣金规则"""
    conn = await get_db_connection()
    cursor = await conn.cursor()
    
    try:
        updates = []
        params = []
        
        if request.name:
            updates.append("name = ?")
            params.append(request.name)
        if request.min_amount is not None:
            updates.append("min_amount = ?")
            params.append(request.min_amount)
        if request.max_amount is not None:
            updates.append("max_amount = ?")
            params.append(request.max_amount)
        if request.commission_rate is not None:
            updates.append("commission_rate = ?")
            params.append(request.commission_rate)
        if request.bonus_rate is not None:
            updates.append("bonus_rate = ?")
            params.append(request.bonus_rate)
        if request.is_active is not None:
            updates.append("is_active = ?")
            params.append(request.is_active)
        
        if not updates:
            return {"success": True, "message": "无更新"}
        
        updates.append("updated_at = ?")
        params.append(datetime.now())
        params.append(rule_id)
        
        result = await cursor.execute(
            f"UPDATE ip_commission_rules SET {', '.join(updates)} WHERE id = ?",
            params
        )
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="规则不存在")
        
        await conn.commit()
        
        return {"success": True, "message": "更新成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update commission rule error: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail="更新失败")
    finally:
        await conn.close()

@router.get("/stats/overview")
async def get_stats_overview(admin = Depends(require_admin)):
    """获取IP统计概览"""
    conn = await get_db_connection()
    cursor = await conn.cursor()
    
    try:
        await cursor.execute("SELECT COUNT(*) as count FROM ip_partners")
        total_ips = (await cursor.fetchone())['count']
        
        await cursor.execute("SELECT COUNT(*) as count FROM ip_partners WHERE status IN ('trial', 'active')")
        active_ips = (await cursor.fetchone())['count']
        
        await cursor.execute("SELECT COUNT(*) as count FROM ip_partners WHERE status = 'pending'")
        pending_applications = (await cursor.fetchone())['count']
        
        await cursor.execute("SELECT COALESCE(SUM(commission_amount), 0) as total FROM ip_commissions")
        total_commission = (await cursor.fetchone())['total']
        
        await cursor.execute("SELECT COALESCE(SUM(commission_amount), 0) as total FROM ip_commissions WHERE status = 'settled'")
        settled_commission = (await cursor.fetchone())['total']
        
        await cursor.execute("SELECT COALESCE(SUM(commission_amount), 0) as total FROM ip_commissions WHERE status = 'pending'")
        pending_commission = (await cursor.fetchone())['total']
        
        await cursor.execute("SELECT COUNT(*) as count FROM ip_referrals")
        total_referrals = (await cursor.fetchone())['count']
        
        await cursor.execute("SELECT COUNT(*) as count FROM ip_withdrawals WHERE status = 'pending'")
        pending_withdrawals = (await cursor.fetchone())['count']
        
        await cursor.execute("SELECT COALESCE(SUM(amount), 0) as total FROM ip_withdrawals WHERE status = 'pending'")
        pending_withdrawal_amount = (await cursor.fetchone())['total']
        
        return {
            "total_ips": total_ips,
            "active_ips": active_ips,
            "pending_applications": pending_applications,
            "total_commission": round(total_commission or 0, 2),
            "settled_commission": round(settled_commission or 0, 2),
            "pending_commission": round(pending_commission or 0, 2),
            "total_referrals": total_referrals,
            "pending_withdrawals": pending_withdrawals,
            "pending_withdrawal_amount": round(pending_withdrawal_amount or 0, 2)
        }
        
    finally:
        await conn.close()

@router.get("/stats/trend")
async def get_stats_trend(
    days: int = Query(30, ge=7, le=90),
    admin = Depends(require_admin)
):
    """获取IP统计趋势"""
    conn = await get_db_connection()
    cursor = await conn.cursor()
    
    try:
        today = datetime.now().date()
        
        dates = []
        new_ips = []
        new_referrals = []
        commissions = []
        
        for i in range(days - 1, -1, -1):
            d = today - timedelta(days=i)
            dates.append(str(d))
            
            count = await cursor.execute('''
                SELECT COUNT(*) as count FROM ip_partners WHERE date(created_at) = ?
            ''', (d,)).fetchone()['count']
            new_ips.append(count)
            
            count = await cursor.execute('''
                SELECT COUNT(*) as count FROM ip_referrals WHERE date(registered_at) = ?
            ''', (d,)).fetchone()['count']
            new_referrals.append(count)
            
            total = await cursor.execute('''
                SELECT COALESCE(SUM(commission_amount), 0) as total 
                FROM ip_commissions WHERE date(created_at) = ?
            ''', (d,)).fetchone()['total']
            commissions.append(round(total, 2))
        
        return {
            "days": days,
            "dates": dates,
            "new_ips": new_ips,
            "new_referrals": new_referrals,
            "commissions": commissions
        }
        
    finally:
        await conn.close()

@router.get("/stats/top-performers")
async def get_top_performers(
    limit: int = Query(10, ge=5, le=50),
    admin = Depends(require_admin)
):
    """获取表现最佳的IP"""
    conn = await get_db_connection()
    cursor = await conn.cursor()
    
    try:
        top_by_earnings = await cursor.execute('''
            SELECT id, name, level, total_earned, total_referrals, balance
            FROM ip_partners
            WHERE status IN ('trial', 'active')
            ORDER BY total_earned DESC
            LIMIT ?
        ''', (limit,)).fetchall()
        
        top_by_referrals = await cursor.execute('''
            SELECT id, name, level, total_earned, total_referrals, balance
            FROM ip_partners
            WHERE status IN ('trial', 'active')
            ORDER BY total_referrals DESC
            LIMIT ?
        ''', (limit,)).fetchall()
        
        month_start = datetime.now().date().replace(day=1)
        top_this_month = await cursor.execute('''
            SELECT p.id, p.name, p.level, 
                   COUNT(r.id) as new_referrals,
                   COALESCE(SUM(c.commission_amount), 0) as month_commission
            FROM ip_partners p
            LEFT JOIN ip_referrals r ON p.id = r.ip_id AND date(r.registered_at) >= ?
            LEFT JOIN ip_commissions c ON p.id = c.ip_id AND date(c.created_at) >= ?
            WHERE p.status IN ('trial', 'active')
            GROUP BY p.id
            ORDER BY month_commission DESC
            LIMIT ?
        ''', (month_start, month_start, limit)).fetchall()
        
        return {
            "top_by_earnings": top_by_earnings,
            "top_by_referrals": top_by_referrals,
            "top_this_month": top_this_month
        }
        
    finally:
        await conn.close()
