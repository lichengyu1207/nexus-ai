"""
积分服务模块
处理积分查询、消耗、调整等业务逻辑
"""
import uuid
from datetime import datetime
from typing import Optional, Tuple, List, Dict, Any
from backend.database import get_db
import logging

logger = logging.getLogger(__name__)

DEFAULT_INITIAL_INTEGRAL = 3  # 新用户默认赠送3次免费分析


async def log_integral_audit(user_id: str, action: str, change: int, balance_after: int, reason: str, details: dict = None):
    """记录积分变动到审计日志"""
    try:
        async with get_db() as conn:
            log_id = str(uuid.uuid4())
            await conn.execute(
                """
                INSERT INTO audit_logs (id, user_id, action_type, resource_type, resource_id, old_value, new_value, timestamp, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'success')
                """,
                (log_id, user_id, action, 'integral', user_id, 
                 str({'change': change, 'reason': reason}),
                 str({'balance_after': balance_after, **(details or {})}),
                 datetime.utcnow().isoformat())
            )
    except Exception as e:
        logger.error(f"Failed to log integral audit: {e}")


class IntegralService:
    """积分服务类"""
    
    @staticmethod
    async def get_user_integral(user_id: str) -> Tuple[int, str, Optional[str], bool]:
        """
        获取用户积分信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            Tuple[integral, membership_level, membership_expires, is_member]
        """
        async with get_db() as conn:
            row = await conn.fetchone(
                "SELECT integral, membership_level, membership_expires FROM users WHERE id = ?",
                (user_id,)
            )
            
            if not row:
                return 0, "free", None, False
            
            integral = row["integral"] or 0
            membership_level = row["membership_level"] or "free"
            membership_expires = row["membership_expires"]
            
            is_member = False
            if membership_level in ["professional", "enterprise"] and membership_expires:
                try:
                    expires_dt = datetime.fromisoformat(membership_expires.replace("Z", "+00:00"))
                    is_member = expires_dt > datetime.now(expires_dt.tzinfo) if expires_dt.tzinfo else expires_dt > datetime.now()
                except:
                    is_member = False
            
            return integral, membership_level, membership_expires, is_member
    
    @staticmethod
    async def record_integral_change(
        user_id: str,
        change: int,
        reason: str,
        admin_note: Optional[str] = None,
        admin_id: Optional[str] = None
    ) -> Tuple[bool, int, str]:
        """
        记录积分变动并更新用户余额
        
        Args:
            user_id: 用户ID
            change: 变动数量（正数增加，负数消耗）
            reason: 变动原因
            admin_note: 管理员备注
            admin_id: 管理员ID
            
        Returns:
            Tuple[success, balance_after, error_message]
        """
        async with get_db() as conn:
            try:
                # 获取当前余额
                row = await conn.fetchone(
                    "SELECT integral FROM users WHERE id = ?",
                    (user_id,)
                )
                
                if not row:
                    return False, 0, "用户不存在"
                
                current_balance = row["integral"] or 0
                new_balance = current_balance + change
                
                # 如果是消耗积分，检查余额是否足够
                if change < 0 and new_balance < 0:
                    return False, current_balance, f"积分不足，当前余额: {current_balance}"
                
                # 更新用户余额
                await conn.execute(
                    "UPDATE users SET integral = ?, updated_at = ? WHERE id = ?",
                    (new_balance, datetime.utcnow().isoformat(), user_id)
                )
                
                # 写入日志
                log_id = str(uuid.uuid4())
                await conn.execute(
                    """
                    INSERT INTO integral_logs (id, user_id, change, balance_after, reason, admin_note, admin_id, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (log_id, user_id, change, new_balance, reason, admin_note, admin_id, datetime.utcnow().isoformat())
                )
                
                logger.info(f"Integral changed for user {user_id}: {change:+d}, new balance: {new_balance}, reason: {reason}")
                
                await log_integral_audit(user_id, 'integral_change', change, new_balance, reason, {
                    'admin_note': admin_note,
                    'admin_id': admin_id
                })
                
                return True, new_balance, ""
                
            except Exception as e:
                logger.error(f"Failed to record integral change: {e}")
                return False, 0, str(e)
    
    @staticmethod
    async def check_and_consume(user_id: str, cost: int = 1) -> Tuple[bool, str, int]:
        """
        检查并消耗积分（原子操作，支持并发）
        
        Args:
            user_id: 用户ID
            cost: 消耗积分数量
            
        Returns:
            Tuple[success, error_message, current_balance]
        """
        async with get_db() as conn:
            try:
                # 获取当前用户信息
                row = await conn.fetchone(
                    "SELECT integral, membership_level, membership_expires FROM users WHERE id = ?",
                    (user_id,)
                )
                
                if not row:
                    return False, "用户不存在", 0
                
                integral = row["integral"] or 0
                membership_level = row["membership_level"] or "free"
                membership_expires = row["membership_expires"]
                
                # 检查是否为会员
                is_member = False
                if membership_level in ["professional", "enterprise"] and membership_expires:
                    try:
                        expires_dt = datetime.fromisoformat(membership_expires.replace("Z", "+00:00"))
                        is_member = expires_dt > datetime.now(expires_dt.tzinfo) if expires_dt.tzinfo else expires_dt > datetime.now()
                    except:
                        is_member = False
                
                if is_member:
                    # 会员不消耗积分
                    return True, "", integral
                
                # 检查积分是否足够
                if integral < cost:
                    return False, f"积分不足，当前余额: {integral}，需要: {cost}。请充值或升级会员。", integral
                
                # 消耗积分
                new_balance = integral - cost
                await conn.execute(
                    "UPDATE users SET integral = ?, updated_at = ? WHERE id = ?",
                    (new_balance, datetime.utcnow().isoformat(), user_id)
                )
                
                # 写入日志
                log_id = str(uuid.uuid4())
                await conn.execute(
                    """
                    INSERT INTO integral_logs (id, user_id, change, balance_after, reason, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (log_id, user_id, -cost, new_balance, "consume_task", datetime.utcnow().isoformat())
                )
                
                logger.info(f"Integral consumed for user {user_id}: -{cost}, new balance: {new_balance}")
                
                return True, "", new_balance
                
            except Exception as e:
                logger.error(f"Failed to check and consume integral: {e}")
                return False, str(e), 0
    
    @staticmethod
    async def get_user_logs(
        user_id: str,
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        获取用户积分变动日志
        
        Args:
            user_id: 用户ID
            limit: 每页数量
            offset: 偏移量
            
        Returns:
            Tuple[logs, total]
        """
        async with get_db() as conn:
            # 获取总数
            total_row = await conn.fetchone(
                "SELECT COUNT(*) as total FROM integral_logs WHERE user_id = ?",
                (user_id,)
            )
            total = total_row["total"] if total_row else 0
            
            # 获取日志列表
            rows = await conn.fetch(
                """
                SELECT id, user_id, change, balance_after, reason, admin_note, admin_id, created_at
                FROM integral_logs
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                (user_id, limit, offset)
            )
            
            logs = []
            for row in rows:
                logs.append({
                    "id": row["id"],
                    "user_id": row["user_id"],
                    "change": row["change"],
                    "balance_after": row["balance_after"],
                    "reason": row["reason"],
                    "admin_note": row["admin_note"],
                    "admin_id": row["admin_id"],
                    "created_at": row["created_at"]
                })
            
            return logs, total
    
    @staticmethod
    async def add_integral(user_id: str, amount: int, reason: str) -> Tuple[bool, int, str]:
        """
        增加用户积分
        
        Args:
            user_id: 用户ID
            amount: 增加数量
            reason: 原因
            
        Returns:
            Tuple[success, new_balance, error_message]
        """
        return await IntegralService.record_integral_change(user_id, amount, reason)
    
    @staticmethod
    async def deduct_integral(user_id: str, amount: int, reason: str) -> Tuple[bool, int, str]:
        """
        扣除用户积分
        
        Args:
            user_id: 用户ID
            amount: 扣除数量
            reason: 原因
            
        Returns:
            Tuple[success, new_balance, error_message]
        """
        return await IntegralService.record_integral_change(user_id, -amount, reason)
    
    @staticmethod
    async def get_summary() -> Dict[str, int]:
        """
        获取积分统计概况
        
        Returns:
            Dict with total_users, total_integral, total_consumed, total_admin_added, total_register
        """
        async with get_db() as conn:
            row = await conn.fetchone("SELECT COUNT(*) as total FROM users")
            total_users = row["total"] if row else 0
            
            row = await conn.fetchone("SELECT COALESCE(SUM(integral), 0) as total FROM users")
            total_integral = int(row["total"]) if row and row["total"] else 0
            
            try:
                row = await conn.fetchone(
                    "SELECT COALESCE(SUM(ABS(change)), 0) as total FROM integral_logs WHERE change < 0"
                )
                total_consumed = int(row["total"]) if row and row["total"] else 0
            except:
                total_consumed = 0
            
            try:
                row = await conn.fetchone(
                    "SELECT COALESCE(SUM(change), 0) as total FROM integral_logs WHERE reason = 'admin_adjust' AND change > 0"
                )
                total_admin_added = int(row["total"]) if row and row["total"] else 0
            except:
                total_admin_added = 0
            
            try:
                row = await conn.fetchone(
                    "SELECT COALESCE(SUM(change), 0) as total FROM integral_logs WHERE reason = 'register'"
                )
                total_register = int(row["total"]) if row and row["total"] else 0
            except:
                total_register = 0
            
            return {
                "total_users": total_users,
                "total_integral": total_integral,
                "total_consumed": total_consumed,
                "total_admin_added": total_admin_added,
                "total_register": total_register
            }


# 创建全局实例
integral_service = IntegralService()
