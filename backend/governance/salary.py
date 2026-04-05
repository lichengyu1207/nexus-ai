"""
薪资管理模块
管理智能体薪资发放、积分扣除等功能
"""
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List

from ..database_pg import get_db

logger = logging.getLogger(__name__)


@dataclass
class SalaryRecord:
    """薪资记录"""
    id: str
    user_id: str
    user_agent_id: str
    agent_name: str
    amount: int
    task_id: Optional[str]
    reason: str
    created_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_agent_id": self.user_agent_id,
            "agent_name": self.agent_name,
            "amount": self.amount,
            "task_id": self.task_id,
            "reason": self.reason,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class FinanceSummary:
    """财务摘要"""
    total_integral: int
    total_spent: int
    total_earned: int
    active_agents: int
    daily_salary_cost: int
    monthly_salary_cost: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_integral": self.total_integral,
            "total_spent": self.total_spent,
            "total_earned": self.total_earned,
            "active_agents": self.active_agents,
            "daily_salary_cost": self.daily_salary_cost,
            "monthly_salary_cost": self.monthly_salary_cost,
        }


class SalaryManager:
    """
    薪资管理器
    
    功能：
    - 扣除智能体薪资
    - 记录薪资日志
    - 查询薪资消耗记录
    - 财务摘要统计
    """
    
    def __init__(self):
        self._initialized = False
    
    async def initialize(self):
        """初始化"""
        self._initialized = True
        logger.info("SalaryManager initialized")
    
    async def deduct_salary(
        self,
        user_id: str,
        user_agent_id: str,
        amount: int,
        task_id: Optional[str] = None,
        reason: str = "任务执行薪资"
    ) -> Dict[str, Any]:
        """
        扣除智能体薪资
        
        Args:
            user_id: 用户ID
            user_agent_id: 用户智能体ID
            amount: 扣除金额
            task_id: 关联任务ID
            reason: 扣除原因
            
        Returns:
            扣除结果
        """
        async with get_db() as db:
            user_row = await db.fetchone(
                "SELECT integral FROM users WHERE id = $1",
                user_id
            )
            
            if not user_row:
                return {"success": False, "error": "用户不存在"}
            
            current_integral = user_row["integral"] or 0
            if current_integral < amount:
                return {"success": False, "error": "积分不足"}
            
            agent_row = await db.fetchone(
                """SELECT ua.*, am.name 
                   FROM user_agents ua
                   JOIN agents_market am ON ua.agent_id = am.id
                   WHERE ua.id = $1 AND ua.user_id = $2""",
                user_agent_id, user_id
            )
            
            agent_name = agent_row["name"] if agent_row else "未知智能体"
            
            now = datetime.utcnow()
            record_id = str(uuid.uuid4())
            
            await db.execute(
                "UPDATE users SET integral = integral - $1 WHERE id = $2",
                amount, user_id
            )
            
            await db.execute(
                """INSERT INTO salary_logs 
                   (id, user_id, user_agent_id, agent_name, amount, task_id, reason, created_at)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
                record_id,
                user_id,
                user_agent_id,
                agent_name,
                amount,
                task_id,
                reason,
                now
            )
            
            await db.execute(
                """INSERT INTO integral_logs (id, user_id, change, action_type, reason, created_at)
                   VALUES ($1, $2, $3, $4, $5, $6)""",
                str(uuid.uuid4()),
                user_id,
                -amount,
                "agent_salary",
                f"智能体薪资：{agent_name} - {reason}",
                now.isoformat()
            )
            
            logger.info(f"Deducted {amount} integral from user {user_id} for agent {agent_name}")
            
            return {
                "success": True,
                "record_id": record_id,
                "amount": amount,
                "agent_name": agent_name,
                "remaining_integral": current_integral - amount,
            }
    
    async def deduct_task_salary(
        self,
        user_id: str,
        task_id: str,
        agents_cost: Dict[str, int]
    ) -> Dict[str, Any]:
        """
        批量扣除任务薪资
        
        Args:
            user_id: 用户ID
            task_id: 任务ID
            agents_cost: 智能体薪资字典 {user_agent_id: cost}
            
        Returns:
            扣除结果
        """
        total_cost = sum(agents_cost.values())
        results = []
        
        async with get_db() as db:
            user_row = await db.fetchone(
                "SELECT integral FROM users WHERE id = $1",
                user_id
            )
            
            if not user_row:
                return {"success": False, "error": "用户不存在"}
            
            current_integral = user_row["integral"] or 0
            if current_integral < total_cost:
                return {"success": False, "error": f"积分不足，需要 {total_cost} 积分"}
            
            for user_agent_id, cost in agents_cost.items():
                result = await self.deduct_salary(
                    user_id=user_id,
                    user_agent_id=user_agent_id,
                    amount=cost,
                    task_id=task_id,
                    reason="任务执行薪资"
                )
                results.append(result)
            
            await db.execute(
                """UPDATE task_records 
                   SET integral_cost = $1, status = $2, completed_at = $3
                   WHERE id = $2""",
                total_cost,
                "completed",
                datetime.utcnow(),
                task_id
            )
            
            return {
                "success": True,
                "total_cost": total_cost,
                "details": results,
            }
    
    async def get_salary_logs(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[SalaryRecord]:
        """
        获取薪资消耗记录
        
        Args:
            user_id: 用户ID
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            薪资记录列表
        """
        async with get_db() as db:
            rows = await db.fetch(
                """SELECT * FROM salary_logs 
                   WHERE user_id = $1 
                   ORDER BY created_at DESC 
                   LIMIT $2 OFFSET $3""",
                user_id, limit, offset
            )
            
            records = []
            for row in rows:
                records.append(SalaryRecord(
                    id=row["id"],
                    user_id=row["user_id"],
                    user_agent_id=row["user_agent_id"],
                    agent_name=row["agent_name"],
                    amount=row["amount"],
                    task_id=row["task_id"],
                    reason=row["reason"],
                    created_at=row["created_at"],
                ))
            
            return records
    
    async def get_finance_summary(self, user_id: str) -> FinanceSummary:
        """
        获取财务摘要
        
        Args:
            user_id: 用户ID
            
        Returns:
            财务摘要
        """
        async with get_db() as db:
            user_row = await db.fetchone(
                "SELECT integral, total_spent_integral FROM users WHERE id = $1",
                user_id
            )
            
            if not user_row:
                return FinanceSummary(
                    total_integral=0,
                    total_spent=0,
                    total_earned=0,
                    active_agents=0,
                    daily_salary_cost=0,
                    monthly_salary_cost=0,
                )
            
            total_integral = user_row["integral"] or 0
            total_spent = user_row["total_spent_integral"] or 0
            
            earned_row = await db.fetchrow(
                """SELECT COALESCE(SUM(ABS(change)), 0) as total_earned 
                   FROM integral_logs 
                   WHERE user_id = $1 AND change > 0""",
                user_id
            )
            total_earned = earned_row["total_earned"] if earned_row else 0
            
            agents_row = await db.fetchrow(
                """SELECT COUNT(*) as count, COALESCE(SUM(salary), 0) as total_salary
                   FROM user_agents 
                   WHERE user_id = $1 AND status = $2""",
                user_id, "active"
            )
            
            active_agents = agents_row["count"] if agents_row else 0
            total_daily_salary = agents_row["total_salary"] if agents_row else 0
            
            return FinanceSummary(
                total_integral=total_integral,
                total_spent=total_spent,
                total_earned=int(total_earned),
                active_agents=active_agents,
                daily_salary_cost=total_daily_salary,
                monthly_salary_cost=total_daily_salary * 30,
            )
    
    async def check_balance(self, user_id: str, required_amount: int) -> Dict[str, Any]:
        """
        检查积分余额
        
        Args:
            user_id: 用户ID
            required_amount: 所需金额
            
        Returns:
            检查结果
        """
        async with get_db() as db:
            user_row = await db.fetchone(
                "SELECT integral FROM users WHERE id = $1",
                user_id
            )
            
            if not user_row:
                return {"sufficient": False, "balance": 0, "required": required_amount}
            
            balance = user_row["integral"] or 0
            
            return {
                "sufficient": balance >= required_amount,
                "balance": balance,
                "required": required_amount,
                "shortage": max(0, required_amount - balance),
            }
    
    async def get_agent_salary_stats(self, user_id: str) -> List[Dict[str, Any]]:
        """
        获取智能体薪资统计
        
        Args:
            user_id: 用户ID
            
        Returns:
            智能体薪资统计列表
        """
        async with get_db() as db:
            rows = await db.fetch(
                """SELECT 
                     ua.id,
                     am.name,
                     am.department,
                     ua.level,
                     ua.salary,
                     COUNT(sl.id) as task_count,
                     COALESCE(SUM(sl.amount), 0) as total_salary_paid
                   FROM user_agents ua
                   JOIN agents_market am ON ua.agent_id = am.id
                   LEFT JOIN salary_logs sl ON ua.id = sl.user_agent_id
                   WHERE ua.user_id = $1 AND ua.status = $2
                   GROUP BY ua.id, am.name, am.department, ua.level, ua.salary
                   ORDER BY total_salary_paid DESC""",
                user_id, "active"
            )
            
            stats = []
            for row in rows:
                stats.append({
                    "id": row["id"],
                    "name": row["name"],
                    "department": row["department"],
                    "level": row["level"],
                    "current_salary": row["salary"],
                    "task_count": row["task_count"],
                    "total_salary_paid": row["total_salary_paid"],
                })
            
            return stats


salary_manager = SalaryManager()
