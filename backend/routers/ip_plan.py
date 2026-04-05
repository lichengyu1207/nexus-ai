"""
房产IP扶持计划API
"""
from fastapi import APIRouter, Depends, Query, Request
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid
import logging
import secrets

from backend.auth import get_current_user_optional, get_current_user, require_admin
from ..database import get_db_connection

router = APIRouter(prefix="/api/ip", tags=["ip-plan"])
logger = logging.getLogger(__name__)


def generate_referral_code():
    """生成推广码"""
    return secrets.token_urlsafe(8).upper()


def get_client_ip(request: Request) -> str:
    """获取客户端IP"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"


# ============================================
# 公共接口（无需登录）
# ============================================

@router.post("/apply")
async def apply_for_ip(
    data: Dict[str, Any],
    request: Request,
    user: Optional[dict] = Depends(get_current_user_optional)
):
    """提交IP申请"""
    conn = await get_db_connection()
    try:
        ip_id = str(uuid.uuid4())
        name = data.get("name", "")
        contact = data.get("contact", "")
        platform = data.get("platform", "")
        platform_id = data.get("platform_id", "")
        followers = data.get("followers", 0)
        user_id = user.get("id") if user else None
        referral_code = generate_referral_code()
        
        await conn.execute("""
            INSERT INTO ip_partners 
            (id, user_id, name, contact, platform, platform_id, followers, referral_code, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending')
        """, (ip_id, user_id, name, contact, platform, platform_id, followers, referral_code))
        await conn.commit()
        
        return {
            "success": True,
            "message": "申请已提交，请等待审核",
            "ip_id": ip_id
        }
    except Exception as e:
        logger.error(f"IP apply error: {e}")
        return {"success": False, "message": str(e)}
    finally:
        await conn.close()


@router.get("/check")
async def check_referral_code(ref: str = Query(...)):
    """验证推广链接"""
    conn = await get_db_connection()
    try:
        cursor = await conn.execute("""
            SELECT id, name, status FROM ip_partners 
            WHERE referral_code = ? AND status = 'active'
        """, (ref,))
        ip = await cursor.fetchone()
        
        if ip:
            return {
                "valid": True,
                "ip_id": ip["id"],
                "ip_name": ip["name"]
            }
        return {"valid": False}
    finally:
        await conn.close()


# ============================================
# IP端接口（需IP身份认证）
# ============================================

async def get_current_ip(user: dict = Depends(get_current_user)):
    """获取当前IP身份"""
    conn = await get_db_connection()
    try:
        cursor = await conn.execute("""
            SELECT * FROM ip_partners WHERE user_id = ? AND status = 'active'
        """, (user["id"],))
        ip = await cursor.fetchone()
        if not ip:
            return None
        return dict(ip)
    finally:
        await conn.close()


@router.get("/dashboard")
async def get_ip_dashboard(user: dict = Depends(get_current_user)):
    """获取IP仪表盘数据"""
    conn = await get_db_connection()
    try:
        cursor = await conn.execute("""
            SELECT * FROM ip_partners WHERE user_id = ?
        """, (user["id"],))
        ip = await cursor.fetchone()
        
        if not ip:
            return {"error": "您还不是IP合作伙伴"}
        
        cursor = await conn.execute("""
            SELECT COUNT(*) as total FROM ip_referrals WHERE ip_id = ?
        """, (ip["id"],))
        total_referrals = (await cursor.fetchone())["total"]
        
        cursor = await conn.execute("""
            SELECT COUNT(*) as valid FROM ip_referrals 
            WHERE ip_id = ? AND status != 'pending'
        """, (ip["id"],))
        valid_referrals = (await cursor.fetchone())["valid"]
        
        cursor = await conn.execute("""
            SELECT COALESCE(SUM(commission_amount), 0) as total 
            FROM ip_referrals WHERE ip_id = ? AND status = 'paid'
        """, (ip["id"],))
        total_commission = (await cursor.fetchone())["total"]
        
        cursor = await conn.execute("""
            SELECT id, user_id, referred_at, status, commission_amount
            FROM ip_referrals WHERE ip_id = ?
            ORDER BY referred_at DESC LIMIT 10
        """, (ip["id"],))
        
        recent = []
        async for row in cursor:
            recent.append({
                "id": row["id"],
                "user_id": row["user_id"],
                "referred_at": row["referred_at"],
                "status": row["status"],
                "commission_amount": row["commission_amount"]
            })
        
        return {
            "ip_info": {
                "id": ip["id"],
                "name": ip["name"],
                "status": ip["status"],
                "commission_rate": ip["commission_rate"],
                "referral_code": ip["referral_code"],
                "available_commission": ip["available_commission"],
                "total_commission": ip["total_commission"]
            },
            "total_referrals": total_referrals,
            "valid_referrals": valid_referrals,
            "total_commission": total_commission,
            "available_commission": ip["available_commission"],
            "recent_referrals": recent
        }
    finally:
        await conn.close()


@router.get("/referrals")
async def get_ip_referrals(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    user: dict = Depends(get_current_user)
):
    """获取推广记录列表"""
    conn = await get_db_connection()
    try:
        cursor = await conn.execute("""
            SELECT id FROM ip_partners WHERE user_id = ?
        """, (user["id"],))
        ip = await cursor.fetchone()
        if not ip:
            return {"error": "您还不是IP合作伙伴"}
        
        where_clause = "WHERE ip_id = ?"
        params = [ip["id"]]
        
        if status:
            where_clause += " AND status = ?"
            params.append(status)
        
        cursor = await conn.execute(f"""
            SELECT COUNT(*) as total FROM ip_referrals {where_clause}
        """, params)
        total = (await cursor.fetchone())["total"]
        
        offset = (page - 1) * page_size
        cursor = await conn.execute(f"""
            SELECT r.*, u.email as user_email
            FROM ip_referrals r
            LEFT JOIN users u ON r.user_id = u.id
            {where_clause}
            ORDER BY r.referred_at DESC
            LIMIT ? OFFSET ?
        """, params + [page_size, offset])
        
        referrals = []
        async for row in cursor:
            referrals.append({
                "id": row["id"],
                "user_id": row["user_id"],
                "user_email": row["user_email"],
                "referred_at": row["referred_at"],
                "order_amount": row["order_amount"],
                "commission_amount": row["commission_amount"],
                "status": row["status"]
            })
        
        return {
            "referrals": referrals,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    finally:
        await conn.close()


@router.get("/commissions")
async def get_ip_commissions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: dict = Depends(get_current_user)
):
    """获取佣金明细"""
    conn = await get_db_connection()
    try:
        cursor = await conn.execute("""
            SELECT id FROM ip_partners WHERE user_id = ?
        """, (user["id"],))
        ip = await cursor.fetchone()
        if not ip:
            return {"error": "您还不是IP合作伙伴"}
        
        cursor = await conn.execute("""
            SELECT COUNT(*) as total FROM ip_referrals 
            WHERE ip_id = ? AND commission_amount > 0
        """, (ip["id"],))
        total = (await cursor.fetchone())["total"]
        
        offset = (page - 1) * page_size
        cursor = await conn.execute("""
            SELECT r.*, u.email as user_email
            FROM ip_referrals r
            LEFT JOIN users u ON r.user_id = u.id
            WHERE r.ip_id = ? AND r.commission_amount > 0
            ORDER BY r.paid_at DESC
            LIMIT ? OFFSET ?
        """, (ip["id"], page_size, offset))
        
        commissions = []
        async for row in cursor:
            commissions.append({
                "id": row["id"],
                "user_email": row["user_email"],
                "order_amount": row["order_amount"],
                "commission_amount": row["commission_amount"],
                "status": row["status"],
                "paid_at": row["paid_at"]
            })
        
        return {
            "commissions": commissions,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    finally:
        await conn.close()


@router.post("/withdraw")
async def submit_withdrawal(
    data: Dict[str, Any],
    user: dict = Depends(get_current_user)
):
    """提交提现申请"""
    conn = await get_db_connection()
    try:
        cursor = await conn.execute("""
            SELECT * FROM ip_partners WHERE user_id = ? AND status = 'active'
        """, (user["id"],))
        ip = await cursor.fetchone()
        
        if not ip:
            return {"error": "您还不是活跃的IP合作伙伴"}
        
        amount = data.get("amount", 0)
        if amount <= 0:
            return {"error": "提现金额必须大于0"}
        
        if amount > ip["available_commission"]:
            return {"error": "可提现余额不足"}
        
        withdrawal_id = str(uuid.uuid4())
        account_type = data.get("account_type", "wechat")
        account_info = data.get("account_info", "")
        
        await conn.execute("""
            INSERT INTO ip_withdrawals 
            (id, ip_id, amount, account_type, account_info, status)
            VALUES (?, ?, ?, ?, ?, 'pending')
        """, (withdrawal_id, ip["id"], amount, account_type, account_info))
        
        await conn.execute("""
            UPDATE ip_partners 
            SET available_commission = available_commission - ?
            WHERE id = ?
        """, (amount, ip["id"]))
        
        await conn.commit()
        
        return {
            "success": True,
            "withdrawal_id": withdrawal_id,
            "message": "提现申请已提交，请等待审核"
        }
    except Exception as e:
        logger.error(f"Withdrawal error: {e}")
        return {"success": False, "error": str(e)}
    finally:
        await conn.close()


@router.get("/withdrawals")
async def get_withdrawals(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: dict = Depends(get_current_user)
):
    """查询提现记录"""
    conn = await get_db_connection()
    try:
        cursor = await conn.execute("""
            SELECT id FROM ip_partners WHERE user_id = ?
        """, (user["id"],))
        ip = await cursor.fetchone()
        if not ip:
            return {"error": "您还不是IP合作伙伴"}
        
        cursor = await conn.execute("""
            SELECT COUNT(*) as total FROM ip_withdrawals WHERE ip_id = ?
        """, (ip["id"],))
        total = (await cursor.fetchone())["total"]
        
        offset = (page - 1) * page_size
        cursor = await conn.execute("""
            SELECT * FROM ip_withdrawals WHERE ip_id = ?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, (ip["id"], page_size, offset))
        
        withdrawals = []
        async for row in cursor:
            withdrawals.append({
                "id": row["id"],
                "amount": row["amount"],
                "account_type": row["account_type"],
                "status": row["status"],
                "admin_notes": row["admin_notes"],
                "processed_at": row["processed_at"],
                "created_at": row["created_at"]
            })
        
        return {
            "withdrawals": withdrawals,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    finally:
        await conn.close()


# ============================================
# 管理员接口
# ============================================

@router.get("/admin/list")
async def admin_list_ips(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    admin: dict = Depends(require_admin)
):
    """管理员获取IP列表"""
    conn = await get_db_connection()
    try:
        where_clause = ""
        params = []
        
        if status:
            where_clause = "WHERE status = ?"
            params.append(status)
        
        cursor = await conn.execute(f"""
            SELECT COUNT(*) as total FROM ip_partners {where_clause}
        """, params)
        total = (await cursor.fetchone())["total"]
        
        offset = (page - 1) * page_size
        cursor = await conn.execute(f"""
            SELECT p.*, u.email as user_email
            FROM ip_partners p
            LEFT JOIN users u ON p.user_id = u.id
            {where_clause}
            ORDER BY p.created_at DESC
            LIMIT ? OFFSET ?
        """, params + [page_size, offset])
        
        ips = []
        async for row in cursor:
            ips.append({
                "id": row["id"],
                "user_id": row["user_id"],
                "user_email": row["user_email"],
                "name": row["name"],
                "contact": row["contact"],
                "platform": row["platform"],
                "platform_id": row["platform_id"],
                "followers": row["followers"],
                "status": row["status"],
                "commission_rate": row["commission_rate"],
                "referral_code": row["referral_code"],
                "available_commission": row["available_commission"],
                "total_commission": row["total_commission"],
                "created_at": row["created_at"]
            })
        
        return {
            "ips": ips,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    finally:
        await conn.close()


@router.get("/admin/{ip_id}")
async def admin_get_ip(
    ip_id: str,
    admin: dict = Depends(require_admin)
):
    """管理员获取IP详情"""
    conn = await get_db_connection()
    try:
        cursor = await conn.execute("""
            SELECT p.*, u.email as user_email
            FROM ip_partners p
            LEFT JOIN users u ON p.user_id = u.id
            WHERE p.id = ?
        """, (ip_id,))
        ip = await cursor.fetchone()
        
        if not ip:
            return {"error": "IP不存在"}
        
        cursor = await conn.execute("""
            SELECT COUNT(*) as total FROM ip_referrals WHERE ip_id = ?
        """, (ip_id,))
        total_referrals = (await cursor.fetchone())["total"]
        
        return {
            "ip": dict(ip),
            "total_referrals": total_referrals
        }
    finally:
        await conn.close()


@router.put("/admin/{ip_id}")
async def admin_update_ip(
    ip_id: str,
    data: Dict[str, Any],
    admin: dict = Depends(require_admin)
):
    """管理员更新IP信息"""
    conn = await get_db_connection()
    try:
        updates = []
        params = []
        
        if "status" in data:
            updates.append("status = ?")
            params.append(data["status"])
        if "commission_rate" in data:
            updates.append("commission_rate = ?")
            params.append(data["commission_rate"])
        if "notes" in data:
            updates.append("notes = ?")
            params.append(data["notes"])
        
        if not updates:
            return {"success": False, "error": "没有要更新的字段"}
        
        updates.append("updated_at = ?")
        params.append(datetime.utcnow().isoformat())
        params.append(ip_id)
        
        await conn.execute(f"""
            UPDATE ip_partners SET {', '.join(updates)} WHERE id = ?
        """, params)
        await conn.commit()
        
        return {"success": True}
    finally:
        await conn.close()


@router.get("/admin/withdrawals/list")
async def admin_list_withdrawals(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    admin: dict = Depends(require_admin)
):
    """管理员获取提现申请列表"""
    conn = await get_db_connection()
    try:
        where_clause = ""
        params = []
        
        if status:
            where_clause = "WHERE w.status = ?"
            params.append(status)
        
        cursor = await conn.execute(f"""
            SELECT COUNT(*) as total FROM ip_withdrawals w {where_clause}
        """, params)
        total = (await cursor.fetchone())["total"]
        
        offset = (page - 1) * page_size
        cursor = await conn.execute(f"""
            SELECT w.*, p.name as ip_name, p.contact as ip_contact
            FROM ip_withdrawals w
            LEFT JOIN ip_partners p ON w.ip_id = p.id
            {where_clause}
            ORDER BY w.created_at DESC
            LIMIT ? OFFSET ?
        """, params + [page_size, offset])
        
        withdrawals = []
        async for row in cursor:
            withdrawals.append({
                "id": row["id"],
                "ip_id": row["ip_id"],
                "ip_name": row["ip_name"],
                "ip_contact": row["ip_contact"],
                "amount": row["amount"],
                "account_type": row["account_type"],
                "account_info": row["account_info"],
                "status": row["status"],
                "admin_notes": row["admin_notes"],
                "created_at": row["created_at"],
                "processed_at": row["processed_at"]
            })
        
        return {
            "withdrawals": withdrawals,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    finally:
        await conn.close()


@router.put("/admin/withdrawals/{withdrawal_id}")
async def admin_process_withdrawal(
    withdrawal_id: str,
    data: Dict[str, Any],
    admin: dict = Depends(require_admin)
):
    """管理员处理提现申请"""
    conn = await get_db_connection()
    try:
        cursor = await conn.execute("""
            SELECT * FROM ip_withdrawals WHERE id = ?
        """, (withdrawal_id,))
        withdrawal = await cursor.fetchone()
        
        if not withdrawal:
            return {"error": "提现记录不存在"}
        
        new_status = data.get("status")
        admin_notes = data.get("admin_notes", "")
        
        if new_status == "rejected":
            await conn.execute("""
                UPDATE ip_partners 
                SET available_commission = available_commission + ?
                WHERE id = ?
            """, (withdrawal["amount"], withdrawal["ip_id"]))
        
        await conn.execute("""
            UPDATE ip_withdrawals 
            SET status = ?, admin_notes = ?, processed_at = ?
            WHERE id = ?
        """, (new_status, admin_notes, datetime.utcnow().isoformat(), withdrawal_id))
        
        await conn.commit()
        
        return {"success": True}
    finally:
        await conn.close()


@router.get("/admin/stats")
async def admin_get_stats(admin: dict = Depends(require_admin)):
    """管理员获取IP计划统计"""
    conn = await get_db_connection()
    try:
        cursor = await conn.execute("""
            SELECT COUNT(*) as total FROM ip_partners
        """)
        total_ips = (await cursor.fetchone())["total"]
        
        cursor = await conn.execute("""
            SELECT COUNT(*) as total FROM ip_partners WHERE status = 'active'
        """)
        active_ips = (await cursor.fetchone())["total"]
        
        cursor = await conn.execute("""
            SELECT COUNT(*) as total FROM ip_referrals
        """)
        total_referrals = (await cursor.fetchone())["total"]
        
        cursor = await conn.execute("""
            SELECT COALESCE(SUM(commission_amount), 0) as total 
            FROM ip_referrals WHERE status = 'paid'
        """)
        total_commission = (await cursor.fetchone())["total"]
        
        cursor = await conn.execute("""
            SELECT COALESCE(SUM(amount), 0) as total 
            FROM ip_withdrawals WHERE status = 'completed'
        """)
        total_withdrawn = (await cursor.fetchone())["total"]
        
        return {
            "total_ips": total_ips,
            "active_ips": active_ips,
            "total_referrals": total_referrals,
            "total_commission": total_commission,
            "total_withdrawn": total_withdrawn
        }
    finally:
        await conn.close()
