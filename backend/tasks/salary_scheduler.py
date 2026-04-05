"""
智能体工资扣减定时任务
每小时执行一次，扣除正在工作的智能体工资
"""
import asyncio
import logging
import uuid
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def deduct_agent_salaries():
    """
    扣除智能体工资
    
    扫描所有正在工作的智能体，计算并扣除工资
    若用户积分不足，自动停止智能体工作
    """
    from backend.database_pg import get_db
    
    logger.info("开始执行智能体工资扣减任务...")
    
    async with get_db() as db:
        working_agents = await db.fetch(
            """SELECT ua.id, ua.user_id, ua.level, ua.status, 
                      at.name, at.base_salary, at.department
               FROM user_agents ua
               JOIN agent_templates at ON ua.template_id = at.id
               WHERE ua.status = 'working'
               ORDER BY ua.user_id"""
        )
        
        if not working_agents:
            logger.info("没有正在工作的智能体")
            return
        
        user_groups = {}
        for agent in working_agents:
            user_id = agent["user_id"]
            if user_id not in user_groups:
                user_groups[user_id] = []
            user_groups[user_id].append(agent)
        
        total_deducted = 0
        total_stopped = 0
        
        for user_id, agents in user_groups.items():
            user = await db.fetchone("SELECT integral FROM users WHERE id = $1", user_id)
            if not user:
                continue
            
            current_integral = user["integral"] or 0
            
            for agent in agents:
                salary = int(agent["base_salary"] * (1 + agent["level"] * 0.05))
                
                if current_integral >= salary:
                    await db.execute(
                        "UPDATE users SET integral = integral - $1 WHERE id = $2",
                        salary, user_id
                    )
                    
                    await db.execute(
                        """INSERT INTO salary_logs 
                           (id, user_id, agent_id, salary, deducted_at)
                           VALUES ($1, $2, $3, $4, $5)""",
                        str(uuid.uuid4()),
                        user_id,
                        agent["id"],
                        salary,
                        datetime.utcnow()
                    )
                    
                    current_integral -= salary
                    total_deducted += salary
                    logger.debug(f"扣除工资: {agent['name']} - {salary}积分 (用户: {user_id})")
                else:
                    await db.execute(
                        "UPDATE user_agents SET status = 'idle' WHERE id = $1",
                        agent["id"]
                    )
                    
                    total_stopped += 1
                    logger.info(f"积分不足，停止工作: {agent['name']} (用户: {user_id})")
        
        logger.info(f"工资扣减完成: 总扣减 {total_deducted} 积分, 停止工作 {total_stopped} 个智能体")


async def auto_assign_idle_agents():
    """
    自动分配闲置智能体
    
    将有分配部门但状态为idle的智能体设为working
    """
    from backend.database_pg import get_db
    
    async with get_db() as db:
        idle_agents = await db.fetch(
            """SELECT ua.id, ua.assigned_department, at.name
               FROM user_agents ua
               JOIN agent_templates at ON ua.template_id = at.id
               WHERE ua.status = 'idle' 
               AND ua.assigned_department IS NOT NULL
               AND ua.assigned_department != ''"""
        )
        
        if not idle_agents:
            return
        
        for agent in idle_agents:
            await db.execute(
                "UPDATE user_agents SET status = 'working' WHERE id = $1",
                agent["id"]
            )
            logger.info(f"智能体 {agent['name']} 开始工作 (部门: {agent['assigned_department']})")


async def calculate_user_bonuses():
    """
    计算用户羁绊加成
    
    更新用户的羁绊加成缓存
    """
    from backend.database_pg import get_db
    import json
    
    async with get_db() as db:
        users = await db.fetch("SELECT id FROM users")
        
        for user in users:
            user_id = user["id"]
            
            activated_bonds = await db.fetch(
                """SELECT b.bonus
                   FROM user_bonds ub
                   JOIN bonds b ON ub.bond_id = b.id
                   WHERE ub.user_id = $1""",
                user_id
            )
            
            total_bonus = {
                "work_speed": 0,
                "income_bonus": 0,
                "accuracy_bonus": 0,
            }
            
            for bond in activated_bonds:
                bonus = json.loads(bond["bonus"]) if isinstance(bond["bonus"], str) else bond["bonus"]
                for key, value in bonus.items():
                    if key in total_bonus:
                        total_bonus[key] += value
            
            await db.execute(
                "UPDATE users SET bond_bonus = $1 WHERE id = $2",
                json.dumps(total_bonus), user_id
            )


def setup_salary_scheduler():
    """设置工资扣减定时任务"""
    scheduler.add_job(
        deduct_agent_salaries,
        IntervalTrigger(hours=1),
        id="deduct_agent_salaries",
        name="扣除智能体工资",
        replace_existing=True
    )
    
    scheduler.add_job(
        auto_assign_idle_agents,
        IntervalTrigger(minutes=5),
        id="auto_assign_idle_agents",
        name="自动分配闲置智能体",
        replace_existing=True
    )
    
    scheduler.add_job(
        calculate_user_bonuses,
        IntervalTrigger(hours=1),
        id="calculate_user_bonuses",
        name="计算用户羁绊加成",
        replace_existing=True
    )
    
    if not scheduler.running:
        scheduler.start()
    
    logger.info("智能体工资调度器已启动")


async def shutdown_salary_scheduler():
    """关闭工资调度器"""
    if scheduler.running:
        scheduler.shutdown()
    logger.info("智能体工资调度器已关闭")
