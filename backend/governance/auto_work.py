"""
智能体自主工作系统 - 任务调度器和执行器
实现空闲检测、任务分配、任务执行、积分结算
"""
import asyncio
import json
import logging
import random
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from backend.database_pg import get_db

logger = logging.getLogger(__name__)


@dataclass
class TaskAssignment:
    """任务分配结果"""
    success: bool
    task_id: Optional[str] = None
    agent_id: Optional[str] = None
    user_id: Optional[str] = None
    task_type: Optional[str] = None
    error: Optional[str] = None


@dataclass
class TaskResult:
    """任务执行结果"""
    success: bool
    task_id: str
    agent_id: str
    user_id: str
    reward_earned: int = 0
    duration_seconds: int = 0
    result_data: Optional[Dict] = None
    error: Optional[str] = None


TASK_TYPE_DEPARTMENTS = {
    "data_collect": ["兵部"],
    "data_clean": ["工部"],
    "report_generate": ["工部"],
    "knowledge_base": ["礼部"],
    "market_monitor": ["刑部"],
    "user_profile": ["吏部"],
    "policy_parse": ["刑部", "礼部"],
    "price_predict": ["工部", "户部"],
    "sentiment_analyze": ["礼部"],
    "data_validate": ["工部", "兵部"],
}

TASK_DURATION_RANGE = {
    "data_collect": (30, 120),
    "data_clean": (10, 30),
    "report_generate": (60, 180),
    "knowledge_base": (20, 60),
    "market_monitor": (30, 90),
    "user_profile": (15, 45),
    "policy_parse": (20, 60),
    "price_predict": (120, 300),
    "sentiment_analyze": (30, 90),
    "data_validate": (10, 30),
}


class AutoTaskScheduler:
    """
    自主任务调度器
    
    功能：
    - 扫描空闲智能体
    - 匹配未分配任务
    - 分配策略：按智能体等级匹配任务优先级
    """
    
    def __init__(self):
        self._initialized = False
    
    async def initialize(self):
        if self._initialized:
            return
        self._initialized = True
        logger.info("AutoTaskScheduler initialized")
    
    async def scan_and_assign(self) -> int:
        """
        扫描空闲智能体并分配任务
        
        Returns:
            分配成功的任务数
        """
        if not self._initialized:
            await self.initialize()
        
        assigned_count = 0
        
        async with get_db() as db:
            idle_agents = await db.fetch(
                """SELECT ua.id, ua.user_id, ua.level, ua.rarity, ua.department, 
                          ua.auto_work_enabled, ua.daily_auto_work_seconds, ua.daily_auto_work_limit,
                          ua.efficiency_bonus, ua.auto_work_last_time, at.name, at.skills
                   FROM user_agents ua
                   JOIN agent_templates at ON ua.template_id = at.id
                   WHERE ua.status = 'idle'
                   AND ua.auto_work_enabled = TRUE
                   AND (ua.daily_auto_work_seconds IS NULL OR ua.daily_auto_work_seconds < ua.daily_auto_work_limit)
                   ORDER BY ua.level DESC, ua.auto_work_last_time ASC NULLS FIRST"""
            )
            
            if not idle_agents:
                return 0
            
            for agent in idle_agents:
                task = await self._find_suitable_task(db, agent)
                
                if task:
                    assignment = await self._assign_task(db, agent, task)
                    if assignment.success:
                        assigned_count += 1
                        logger.info(f"Assigned task {task['id']} to agent {agent['id']}")
        
        return assigned_count
    
    async def _find_suitable_task(self, db, agent: Dict) -> Optional[Dict]:
        """为智能体找到合适的任务"""
        agent_dept = agent["department"]
        agent_level = agent["level"] or 1
        
        suitable_types = []
        for task_type, depts in TASK_TYPE_DEPARTMENTS.items():
            if agent_dept in depts:
                suitable_types.append(task_type)
        
        if not suitable_types:
            suitable_types = list(TASK_TYPE_DEPARTMENTS.keys())
        
        task = await db.fetchrow(
            """SELECT * FROM auto_tasks 
               WHERE status = 'pending' 
               AND task_type IN (SELECT unnest(?))
               ORDER BY priority DESC, created_at ASC
               LIMIT 1""",
            (suitable_types,)
        )
        
        return dict(task) if task else None
    
    async def _assign_task(self, db, agent: Dict, task: Dict) -> TaskAssignment:
        """分配任务给智能体"""
        try:
            now = datetime.utcnow()
            
            await db.execute(
                """UPDATE auto_tasks 
                   SET status = 'assigned', 
                       assigned_agent_id = ?, 
                       user_id = ?,
                       started_at = ?
                   WHERE id = ? AND status = 'pending'""",
                (agent["id"], agent["user_id"], now, task["id"])
            )
            
            await db.execute(
                """UPDATE user_agents 
                   SET status = 'working',
                       auto_work_last_time = ?
                   WHERE id = ?""",
                (now, agent["id"])
            )
            
            return TaskAssignment(
                success=True,
                task_id=task["id"],
                agent_id=agent["id"],
                user_id=agent["user_id"],
                task_type=task["task_type"],
            )
        except Exception as e:
            logger.error(f"Failed to assign task: {e}")
            return TaskAssignment(success=False, error=str(e))
    
    async def get_user_auto_work_stats(self, user_id: str) -> Dict[str, Any]:
        """获取用户自主工作统计"""
        async with get_db() as db:
            agents = await db.fetch(
                """SELECT ua.id, at.name, ua.level, ua.rarity, ua.department, 
                          ua.auto_work_enabled, ua.daily_auto_work_seconds, ua.daily_auto_work_limit,
                          ua.total_auto_work_reward, ua.efficiency_bonus
                   FROM user_agents ua
                   JOIN agent_templates at ON ua.template_id = at.id
                   WHERE ua.user_id = ?""",
                (user_id,)
            )
            
            total_reward = 0
            total_work_seconds = 0
            total_limit = 0
            enabled_count = 0
            working_count = 0
            
            agent_stats = []
            for agent in agents:
                total_reward += agent["total_auto_work_reward"] or 0
                total_work_seconds += agent["daily_auto_work_seconds"] or 0
                total_limit += agent["daily_auto_work_limit"] or 3600
                if agent["auto_work_enabled"]:
                    enabled_count += 1
                
                agent_stats.append({
                    "id": agent["id"],
                    "name": agent["name"],
                    "level": agent["level"],
                    "rarity": agent["rarity"],
                    "department": agent["department"],
                    "auto_work_enabled": agent["auto_work_enabled"],
                    "daily_work_seconds": agent["daily_auto_work_seconds"] or 0,
                    "daily_limit": agent["daily_auto_work_limit"] or 3600,
                    "total_reward": agent["total_auto_work_reward"] or 0,
                    "efficiency_bonus": agent["efficiency_bonus"] or 0,
                })
            
            return {
                "total_reward": total_reward,
                "total_work_seconds": total_work_seconds,
                "total_limit": total_limit,
                "enabled_count": enabled_count,
                "working_count": working_count,
                "agents": agent_stats,
            }


class TaskExecutor:
    """
    任务执行器
    
    功能：
    - 执行已分配的任务
    - 计算积分收益
    - 记录工作日志
    """
    
    def __init__(self):
        self._initialized = False
    
    async def initialize(self):
        if self._initialized:
            return
        self._initialized = True
        logger.info("TaskExecutor initialized")
    
    async def execute_assigned_tasks(self) -> int:
        """
        执行所有已分配的任务
        
        Returns:
            执行完成的任务数
        """
        if not self._initialized:
            await self.initialize()
        
        completed_count = 0
        
        try:
            async with get_db() as db:
                assigned_tasks = await db.fetch(
                    """SELECT t.*, ua.level, ua.rarity, ua.efficiency_bonus, ua.user_id
                       FROM auto_tasks t
                       JOIN user_agents ua ON t.assigned_agent_id = ua.id
                       WHERE t.status = 'assigned'
                       AND t.started_at < ?""",
                    (datetime.utcnow() - timedelta(seconds=5),)
                )
                
                for task in assigned_tasks:
                    result = await self._execute_task(db, dict(task))
                    if result.success:
                        completed_count += 1
        except Exception as e:
            logger.error(f"Error executing assigned tasks: {e}")
        
        return completed_count
    
    async def _execute_task(self, db, task: Dict) -> TaskResult:
        """执行单个任务"""
        task_id = task["id"]
        agent_id = task["assigned_agent_id"]
        user_id = task["user_id"]
        task_type = task["task_type"]
        base_reward = task["base_reward"]
        resource_cost = task["resource_cost"]
        
        try:
            duration_range = TASK_DURATION_RANGE.get(task_type, (30, 60))
            duration_seconds = random.randint(duration_range[0], duration_range[1])
            
            level = task["level"] or 1
            efficiency_bonus = task["efficiency_bonus"] or 0
            level_bonus = 0.05 * level
            
            total_bonus = 1 + level_bonus + efficiency_bonus
            reward = int(base_reward * total_bonus) - resource_cost
            reward = max(reward, 1)
            
            result_data = await self._simulate_task_execution(task_type, duration_seconds)
            
            now = datetime.utcnow()
            
            await db.execute(
                """UPDATE auto_tasks 
                   SET status = 'completed',
                       completed_at = ?,
                       result = ?,
                       reward_earned = ?
                   WHERE id = ?""",
                (now, json.dumps(result_data, ensure_ascii=False), reward, task_id)
            )
            
            await db.execute(
                """UPDATE user_agents 
                   SET status = 'idle',
                       daily_auto_work_seconds = COALESCE(daily_auto_work_seconds, 0) + ?,
                       total_auto_work_reward = COALESCE(total_auto_work_reward, 0) + ?
                   WHERE id = ?""",
                (duration_seconds, reward, agent_id)
            )
            
            await db.execute(
                """UPDATE users SET integral = COALESCE(integral, 0) + ? WHERE id = ?""",
                (reward, user_id)
            )
            
            await db.execute(
                """INSERT INTO integral_logs 
                   (id, user_id, change, reason, reference_id, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (str(uuid.uuid4()), user_id, reward, "auto_work", task_id, now)
            )
            
            await db.execute(
                """INSERT INTO agent_work_logs 
                   (id, agent_id, user_id, task_id, task_type, start_time, end_time, 
                    duration_seconds, reward_earned, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (str(uuid.uuid4()), agent_id, user_id, task_id, task_type,
                 task["started_at"], now, duration_seconds, reward, "completed")
            )
            
            logger.info(f"Task {task_id} completed, reward: {reward}")
            
            return TaskResult(
                success=True,
                task_id=task_id,
                agent_id=agent_id,
                user_id=user_id,
                reward_earned=reward,
                duration_seconds=duration_seconds,
                result_data=result_data,
            )
        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")
            
            await db.execute(
                """UPDATE auto_tasks 
                   SET status = 'failed', error_message = ?, completed_at = ?
                   WHERE id = ?""",
                (str(e), datetime.utcnow(), task_id)
            )
            
            await db.execute(
                "UPDATE user_agents SET status = 'idle' WHERE id = ?",
                (agent_id,)
            )
            
            return TaskResult(
                success=False,
                task_id=task_id,
                agent_id=agent_id,
                user_id=user_id,
                error=str(e),
            )
    
    async def _simulate_task_execution(self, task_type: str, duration: int) -> Dict:
        """模拟任务执行结果"""
        results = {
            "data_collect": {
                "records_collected": random.randint(10, 100),
                "sources": ["公开数据源A", "公开数据源B"],
            },
            "data_clean": {
                "records_cleaned": random.randint(50, 200),
                "duplicates_removed": random.randint(5, 20),
            },
            "report_generate": {
                "report_id": str(uuid.uuid4()),
                "areas_covered": random.randint(1, 5),
            },
            "knowledge_base": {
                "qa_pairs_added": random.randint(5, 20),
                "topics": ["房产政策", "市场动态"],
            },
            "market_monitor": {
                "alerts_generated": random.randint(0, 3),
                "market_status": "正常",
            },
            "user_profile": {
                "profile_updated": True,
                "new_insights": random.randint(1, 5),
            },
            "policy_parse": {
                "policies_parsed": random.randint(1, 3),
                "key_points": random.randint(5, 15),
            },
            "price_predict": {
                "prediction_accuracy": random.uniform(0.85, 0.95),
                "areas_predicted": random.randint(3, 10),
            },
            "sentiment_analyze": {
                "posts_analyzed": random.randint(50, 200),
                "sentiment_score": random.uniform(-1, 1),
            },
            "data_validate": {
                "records_validated": random.randint(100, 500),
                "anomalies_found": random.randint(0, 10),
            },
        }
        
        return results.get(task_type, {"status": "completed"})


auto_task_scheduler = AutoTaskScheduler()
task_executor = TaskExecutor()
