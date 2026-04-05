"""
Token计价与动态消耗服务
实现基于文本长度的精确计费系统
1积分 = 100 Token
"""
import uuid
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple

from ..database import get_db_connection
from ..utils.token_counter import (
    count_tokens,
    tokens_to_integral,
    integral_to_tokens,
    TokenCalculator
)

logger = logging.getLogger(__name__)


class TokenService:
    """Token计价服务"""
    
    INTEGRAL_TO_TOKEN_RATIO = 100
    
    def __init__(self):
        self.calculator = TokenCalculator()
    
    async def get_user_balance(self, user_id: str) -> Dict[str, Any]:
        """
        获取用户Token余额
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict: 包含积分和Token余额
        """
        conn = await get_db_connection()
        try:
            row = await conn.fetchrow(
                "SELECT integral FROM users WHERE id = $1",
                user_id
            )
            
            if not row:
                return {"integral": 0.0, "token_balance": 0}
            
            integral = float(row["integral"] or 0)
            token_balance = int(integral * self.INTEGRAL_TO_TOKEN_RATIO)
            
            return {
                "integral": round(integral, 2),
                "token_balance": token_balance
            }
        except Exception as e:
            logger.error(f"Error getting user balance: {e}")
            return {"integral": 0.0, "token_balance": 0}
        finally:
            await conn.close()
    
    async def preview_consumption(
        self,
        text: str,
        action_type: str = "dialogue"
    ) -> Dict[str, Any]:
        """
        预览Token消耗
        
        Args:
            text: 输入文本
            action_type: 操作类型
            
        Returns:
            Dict: 预估消耗信息
        """
        rule = await self._get_pricing_rule(action_type)
        
        input_tokens = count_tokens(text) if text else 0
        
        if rule and rule.get("pricing_type") == "fixed":
            total_tokens = rule.get("fixed_cost", 5)
        else:
            input_mult = rule.get("input_multiplier", 1.0) if rule else 1.0
            total_tokens = int(input_tokens * input_mult)
        
        cost_integral = tokens_to_integral(max(1, total_tokens))
        
        return {
            "input_tokens": input_tokens,
            "estimated_total_tokens": max(1, total_tokens),
            "estimated_cost_integral": cost_integral,
            "action_type": action_type,
            "pricing_type": rule.get("pricing_type", "dynamic") if rule else "dynamic"
        }
    
    async def consume_tokens(
        self,
        user_id: str,
        action_type: str,
        input_text: str = "",
        output_text: str = "",
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        消耗Token（核心接口）
        
        Args:
            user_id: 用户ID
            action_type: 操作类型
            input_text: 输入文本
            output_text: 输出文本
            metadata: 额外元数据
            
        Returns:
            Dict: 消耗结果
        """
        rule = await self._get_pricing_rule(action_type)
        
        input_tokens = count_tokens(input_text) if input_text else 0
        output_tokens = count_tokens(output_text) if output_text else 0
        
        if rule and rule.get("pricing_type") == "fixed":
            total_tokens = rule.get("fixed_cost", 5)
        else:
            input_mult = rule.get("input_multiplier", 1.0) if rule else 1.0
            output_mult = rule.get("output_multiplier", 0.5) if rule else 0.5
            total_tokens = int(input_tokens * input_mult + output_tokens * output_mult)
        
        total_tokens = max(1, total_tokens)
        cost_integral = tokens_to_integral(total_tokens)
        
        conn = await get_db_connection()
        try:
            await conn.execute("BEGIN")
            
            row = await conn.fetchrow(
                "SELECT integral FROM users WHERE id = $1",
                user_id
            )
            
            if not row:
                await conn.execute("ROLLBACK")
                return {
                    "success": False,
                    "error": "用户不存在",
                    "cost_integral": 0,
                    "balance_after": 0
                }
            
            current_integral = float(row["integral"] or 0)
            
            if current_integral < cost_integral:
                await conn.execute("ROLLBACK")
                return {
                    "success": False,
                    "error": f"积分不足，当前余额: {current_integral:.2f}积分，需要: {cost_integral:.2f}积分",
                    "cost_integral": cost_integral,
                    "balance_after": current_integral
                }
            
            new_balance = current_integral - cost_integral
            
            await conn.execute(
                "UPDATE users SET integral = $1, updated_at = $2 WHERE id = $3",
                new_balance, datetime.utcnow().isoformat(), user_id
            )
            
            log_id = str(uuid.uuid4())
            await conn.execute(
                """
                INSERT INTO token_consumption_logs 
                (id, user_id, action_type, input_tokens, output_tokens, total_tokens, cost_integral, metadata, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                log_id, user_id, action_type, input_tokens, output_tokens, total_tokens, cost_integral,
                json.dumps(metadata) if metadata else None, datetime.utcnow().isoformat()
            )
            
            await conn.execute("COMMIT")
            
            logger.info(f"Token consumed: user={user_id}, action={action_type}, tokens={total_tokens}, cost={cost_integral}")
            
            return {
                "success": True,
                "cost_integral": cost_integral,
                "total_tokens": total_tokens,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "balance_after": round(new_balance, 2),
                "consumption_id": log_id
            }
            
        except Exception as e:
            await conn.execute("ROLLBACK")
            logger.error(f"Token consumption failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "cost_integral": 0,
                "balance_after": 0
            }
        finally:
            await conn.close()
    
    async def get_consumption_history(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
        action_type: str = None
    ) -> Dict[str, Any]:
        """
        获取消费记录
        
        Args:
            user_id: 用户ID
            limit: 每页数量
            offset: 偏移量
            action_type: 操作类型筛选
            
        Returns:
            Dict: 消费记录列表和总数
        """
        conn = await get_db_connection()
        try:
            if action_type:
                total_row = await conn.fetchrow(
                    "SELECT COUNT(*) as total FROM token_consumption_logs WHERE user_id = $1 AND action_type = $2",
                    user_id, action_type
                )
                rows = await conn.fetch(
                    """
                    SELECT id, action_type, input_tokens, output_tokens, total_tokens, 
                         cost_integral, metadata, created_at
                    FROM token_consumption_logs 
                    WHERE user_id = $1 AND action_type = $2
                    ORDER BY created_at DESC
                    LIMIT $3 OFFSET $4
                    """,
                    user_id, action_type, limit, offset
                )
            else:
                total_row = await conn.fetchrow(
                    "SELECT COUNT(*) as total FROM token_consumption_logs WHERE user_id = $1",
                    user_id
                )
                rows = await conn.fetch(
                    """
                    SELECT id, action_type, input_tokens, output_tokens, total_tokens, 
                         cost_integral, metadata, created_at
                    FROM token_consumption_logs 
                    WHERE user_id = $1
                    ORDER BY created_at DESC
                    LIMIT $2 OFFSET $3
                    """,
                    user_id, limit, offset
                )
            
            total = total_row["total"] if total_row else 0
            
            records = []
            for row in rows:
                record = {
                    "id": row["id"],
                    "action_type": row["action_type"],
                    "input_tokens": row["input_tokens"],
                    "output_tokens": row["output_tokens"],
                    "total_tokens": row["total_tokens"],
                    "cost_integral": row["cost_integral"],
                    "created_at": row["created_at"]
                }
                if row["metadata"]:
                    try:
                        record["metadata"] = json.loads(row["metadata"])
                    except:
                        record["metadata"] = {}
                records.append(record)
            
            return {
                "records": records,
                "total": total,
                "limit": limit,
                "offset": offset
            }
        finally:
            await conn.close()
    
    async def _get_pricing_rule(self, action_type: str) -> Optional[Dict[str, Any]]:
        """从数据库获取定价规则"""
        conn = await get_db_connection()
        try:
            row = await conn.fetchrow(
                "SELECT * FROM token_pricing_rules WHERE action_type = $1 AND is_active = 1",
                action_type
            )
            
            if row:
                return {
                    "pricing_type": row["pricing_type"],
                    "fixed_cost": row["fixed_cost"],
                    "input_multiplier": row["input_multiplier"],
                    "output_multiplier": row["output_multiplier"],
                    "description": row["description"]
                }
            return None
        except Exception as e:
            logger.error(f"Error getting pricing rule: {e}")
            return None
        finally:
            await conn.close()
    
    async def get_all_pricing_rules(self) -> List[Dict[str, Any]]:
        """获取所有定价规则"""
        conn = await get_db_connection()
        try:
            rows = await conn.fetch(
                "SELECT * FROM token_pricing_rules ORDER BY action_type"
            )
            
            rules = []
            for row in rows:
                rules.append({
                    "id": row["id"],
                    "action_type": row["action_type"],
                    "pricing_type": row["pricing_type"],
                    "fixed_cost": row["fixed_cost"],
                    "input_multiplier": row["input_multiplier"],
                    "output_multiplier": row["output_multiplier"],
                    "description": row["description"],
                    "is_active": bool(row["is_active"])
                })
            
            return rules
        finally:
            await conn.close()
    
    async def update_pricing_rule(
        self,
        action_type: str,
        pricing_type: str = None,
        fixed_cost: int = None,
        input_multiplier: float = None,
        output_multiplier: float = None,
        description: str = None
    ) -> bool:
        """更新定价规则"""
        conn = await get_db_connection()
        try:
            updates = []
            params = []
            
            if pricing_type is not None:
                updates.append("pricing_type = ?")
                params.append(pricing_type)
            if fixed_cost is not None:
                updates.append("fixed_cost = ?")
                params.append(fixed_cost)
            if input_multiplier is not None:
                updates.append("input_multiplier = ?")
                params.append(input_multiplier)
            if output_multiplier is not None:
                updates.append("output_multiplier = ?")
                params.append(output_multiplier)
            if description is not None:
                updates.append("description = ?")
                params.append(description)
            
            updates.append("updated_at = ?")
            params.append(datetime.utcnow().isoformat())
            
            params.append(action_type)
            
            await conn.execute(
                f"UPDATE token_pricing_rules SET {', '.join(updates)} WHERE action_type = ?",
                params
            )
            await conn.commit()
            
            return True
        except Exception as e:
            logger.error(f"Failed to update pricing rule: {e}")
            return False
        finally:
            await conn.close()
    
    async def get_consumption_stats(
        self,
        start_date: str = None,
        end_date: str = None
    ) -> Dict[str, Any]:
        """
        获取消耗统计（管理员）
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            Dict: 统计数据
        """
        conn = await get_db_connection()
        try:
            where_clause = "1=1"
            params = []
            param_idx = 1
            
            if start_date:
                where_clause += f" AND created_at >= ${param_idx}"
                params.append(start_date)
                param_idx += 1
            if end_date:
                where_clause += f" AND created_at <= ${param_idx}"
                params.append(end_date)
            
            summary = await conn.fetchrow(
                f"""
                SELECT 
                    COUNT(*) as total_records,
                    SUM(total_tokens) as total_tokens,
                    SUM(cost_integral) as total_cost,
                    COUNT(DISTINCT user_id) as unique_users
                FROM token_consumption_logs 
                WHERE {where_clause}
                """,
                *params
            )
            
            by_action = await conn.fetch(
                f"""
                SELECT 
                    action_type,
                    COUNT(*) as count,
                    SUM(total_tokens) as tokens,
                    SUM(cost_integral) as cost
                FROM token_consumption_logs 
                WHERE {where_clause}
                GROUP BY action_type
                ORDER BY cost DESC
                """,
                *params
            )
            
            daily = await conn.fetch(
                f"""
                SELECT 
                    DATE(created_at) as date,
                    SUM(total_tokens) as tokens,
                    SUM(cost_integral) as cost,
                    COUNT(*) as count
                FROM token_consumption_logs 
                WHERE {where_clause}
                GROUP BY DATE(created_at)
                ORDER BY date DESC
                LIMIT 30
                """,
                *params
            )
            
            return {
                "summary": {
                    "total_records": summary["total_records"] or 0,
                    "total_tokens": summary["total_tokens"] or 0,
                    "total_cost": round(summary["total_cost"] or 0, 2),
                    "unique_users": summary["unique_users"] or 0
                },
                "by_action": [
                    {
                        "action_type": row["action_type"],
                        "count": row["count"],
                        "tokens": row["tokens"],
                        "cost": round(row["cost"] or 0, 2)
                    }
                    for row in by_action
                ],
                "daily_trend": [
                    {
                        "date": row["date"],
                        "tokens": row["tokens"],
                        "cost": round(row["cost"] or 0, 2),
                        "count": row["count"]
                    }
                    for row in daily
                ]
            }
        finally:
            await conn.close()
    
    async def reserve_tokens(
        self,
        user_id: str,
        action_type: str,
        estimated_tokens: int,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        预扣Token（两阶段消耗第一阶段）
        
        Args:
            user_id: 用户ID
            action_type: 操作类型
            estimated_tokens: 估算Token数
            metadata: 额外元数据
            
        Returns:
            Dict: 预扣结果
        """
        cost_integral = tokens_to_integral(estimated_tokens)
        
        conn = await get_db_connection()
        try:
            row = await conn.fetchrow(
                "SELECT integral FROM users WHERE id = $1",
                user_id
            )
            
            if not row:
                return {
                    "success": False,
                    "error": "用户不存在"
                }
            
            current_integral = float(row["integral"] or 0)
            
            if current_integral < cost_integral:
                return {
                    "success": False,
                    "error": f"积分不足，当前余额: {current_integral:.2f}积分，需要: {cost_integral:.2f}积分",
                    "current_balance": current_integral,
                    "required": cost_integral
                }
            
            new_balance = current_integral - cost_integral
            
            await conn.execute(
                "UPDATE users SET integral = $1, updated_at = $2 WHERE id = $3",
                new_balance, datetime.utcnow().isoformat(), user_id
            )
            
            reservation_id = str(uuid.uuid4())
            await conn.execute(
                """
                INSERT INTO token_consumption_logs 
                (id, user_id, action_type, input_tokens, output_tokens, total_tokens, cost_integral, metadata, status, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'pending', $9)
                """,
                reservation_id,
                user_id,
                action_type,
                estimated_tokens,
                0,
                estimated_tokens,
                cost_integral,
                json.dumps(metadata) if metadata else None,
                datetime.utcnow().isoformat()
            )
            
            logger.info(f"Tokens reserved: user={user_id}, reservation={reservation_id}, tokens={estimated_tokens}")
            
            return {
                "success": True,
                "reservation_id": reservation_id,
                "cost_integral": cost_integral,
                "estimated_tokens": estimated_tokens,
                "balance_after": round(new_balance, 2)
            }
            
        except Exception as e:
            logger.error(f"Token reservation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            await conn.close()
    
    async def confirm_consumption(
        self,
        reservation_id: str,
        actual_tokens: int = None,
        input_text: str = "",
        output_text: str = ""
    ) -> Dict[str, Any]:
        """
        确认消耗（两阶段消耗第二阶段）
        
        Args:
            reservation_id: 预扣记录ID
            actual_tokens: 实际Token数（可选）
            input_text: 输入文本（用于计算实际Token）
            output_text: 输出文本（用于计算实际Token）
            
        Returns:
            Dict: 确认结果
        """
        conn = await get_db_connection()
        try:
            reservation = await conn.fetchrow(
                "SELECT * FROM token_consumption_logs WHERE id = $1 AND status = 'pending'",
                reservation_id
            )
            
            if not reservation:
                return {
                    "success": False,
                    "error": "预扣记录不存在或已确认"
                }
            
            user_id = reservation["user_id"]
            reserved_tokens = reservation["total_tokens"]
            reserved_cost = reservation["cost_integral"]
            
            if actual_tokens is None:
                input_tokens = count_tokens(input_text) if input_text else 0
                output_tokens = count_tokens(output_text) if output_text else 0
                rule = await self._get_pricing_rule(reservation["action_type"])
                
                if rule and rule.get("pricing_type") != "fixed":
                    input_mult = rule.get("input_multiplier", 1.0)
                    output_mult = rule.get("output_multiplier", 0.5)
                    actual_tokens = int(input_tokens * input_mult + output_tokens * output_mult)
                else:
                    actual_tokens = reserved_tokens
            else:
                input_tokens = reservation["input_tokens"]
                output_tokens = 0
            
            actual_cost = tokens_to_integral(max(1, actual_tokens))
            
            await conn.execute(
                """
                UPDATE token_consumption_logs 
                SET status = 'committed', 
                    input_tokens = $1, 
                    output_tokens = $2, 
                    total_tokens = $3,
                    cost_integral = $4
                WHERE id = $5
                """,
                input_tokens, output_tokens, actual_tokens, actual_cost, reservation_id
            )
            
            cost_diff = actual_cost - reserved_cost
            if abs(cost_diff) > 0.001:
                user_row = await conn.fetchrow(
                    "SELECT integral FROM users WHERE id = $1",
                    user_id
                )
                current_integral = float(user_row["integral"] or 0)
                
                if cost_diff > 0:
                    if current_integral < cost_diff:
                        return {
                            "success": False,
                            "error": f"补扣积分不足，需要补扣: {cost_diff:.2f}积分"
                        }
                    new_balance = current_integral - cost_diff
                else:
                    new_balance = current_integral - cost_diff
                
                await conn.execute(
                    "UPDATE users SET integral = $1, updated_at = $2 WHERE id = $3",
                    new_balance, datetime.utcnow().isoformat(), user_id
                )
            else:
                user_row = await conn.fetchrow(
                    "SELECT integral FROM users WHERE id = $1",
                    user_id
                )
                new_balance = float(user_row["integral"] or 0)
            
            logger.info(f"Consumption confirmed: reservation={reservation_id}, actual_tokens={actual_tokens}")
            
            return {
                "success": True,
                "reservation_id": reservation_id,
                "actual_tokens": actual_tokens,
                "actual_cost": actual_cost,
                "adjustment": round(cost_diff, 2),
                "balance_after": round(new_balance, 2)
            }
            
        except Exception as e:
            logger.error(f"Confirm consumption failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            await conn.close()
    
    async def rollback_reservation(
        self,
        reservation_id: str,
        reason: str = "业务失败"
    ) -> Dict[str, Any]:
        """
        回滚预扣（业务失败时退还）
        
        Args:
            reservation_id: 预扣记录ID
            reason: 回滚原因
            
        Returns:
            Dict: 回滚结果
        """
        from .notification_service import notification_service
        
        conn = await get_db_connection()
        try:
            await conn.execute("BEGIN")
            
            reservation = await conn.fetchrow(
                "SELECT * FROM token_consumption_logs WHERE id = $1 AND status = 'pending'",
                reservation_id
            )
            
            if not reservation:
                await conn.execute("ROLLBACK")
                return {
                    "success": False,
                    "error": "预扣记录不存在或已处理"
                }
            
            user_id = reservation["user_id"]
            refund_tokens = reservation["total_tokens"]
            refund_integral = reservation["cost_integral"]
            
            await conn.execute(
                "UPDATE token_consumption_logs SET status = 'refunded' WHERE id = $1",
                reservation_id
            )
            
            user_row = await conn.fetchrow(
                "SELECT integral FROM users WHERE id = $1",
                user_id
            )
            current_integral = float(user_row["integral"] or 0)
            new_balance = current_integral + refund_integral
            
            await conn.execute(
                "UPDATE users SET integral = $1, updated_at = $2 WHERE id = $3",
                new_balance, datetime.utcnow().isoformat(), user_id
            )
            
            refund_log_id = str(uuid.uuid4())
            await conn.execute(
                """
                INSERT INTO refund_logs (id, consumption_id, user_id, refund_tokens, refund_integral, reason, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                refund_log_id, reservation_id, user_id, refund_tokens, refund_integral, reason, datetime.utcnow().isoformat()
            )
            
            await conn.execute("COMMIT")
            
            try:
                await notification_service.send_refund_notification(
                    user_id=user_id,
                    refund_integral=refund_integral,
                    refund_tokens=refund_tokens,
                    reason=reason
                )
            except Exception as e:
                logger.warning(f"Failed to send refund notification: {e}")
            
            logger.info(f"Reservation rolled back: reservation={reservation_id}, refund={refund_integral}")
            
            return {
                "success": True,
                "reservation_id": reservation_id,
                "refund_tokens": refund_tokens,
                "refund_integral": refund_integral,
                "balance_after": round(new_balance, 2),
                "reason": reason
            }
            
        except Exception as e:
            await conn.execute("ROLLBACK")
            logger.error(f"Rollback reservation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            await conn.close()
    
    async def auto_rollback_pending(self, timeout_minutes: int = 30) -> int:
        """
        自动回滚长时间pending的记录
        
        Args:
            timeout_minutes: 超时分钟数
            
        Returns:
            int: 回滚数量
        """
        conn = await get_db_connection()
        try:
            pending_rows = await conn.fetch(
                """
                SELECT id FROM token_consumption_logs 
                WHERE status = 'pending' 
                AND EXTRACT(EPOCH FROM (now() - created_at::timestamp)) / 60 > $1
                """,
                timeout_minutes
            )
        except Exception as e:
            logger.error(f"Auto rollback query failed: {e}")
            return 0
        finally:
            await conn.close()
        
        rolled_back = 0
        for row in pending_rows:
            result = await self.rollback_reservation(
                row["id"],
                "系统自动退还（长时间未确认）"
            )
            if result.get("success"):
                rolled_back += 1
        
        if rolled_back > 0:
            logger.info(f"Auto rolled back {rolled_back} pending reservations")
        
        return rolled_back


token_service = TokenService()
