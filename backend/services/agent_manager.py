# -*- coding: utf-8 -*-
"""
AgentManager - 智能体生命周期管理器
负责智能体的创建、分配、升级、能量管理
"""
import asyncio
import uuid
import logging
import random
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum

from backend.database_pg import PostgreSQLConnectionPool

logger = logging.getLogger(__name__)


class AgentRole(str, Enum):
    LI = "li"
    HU = "hu"
    LI_GUAN = "li_guan"
    BING = "bing"
    XING = "xing"
    GONG = "gong"
    ZHONGSHU = "zhongshu"
    MENXIA = "menxia"
    SHANGSHU = "shangshu"


class AgentStatus(str, Enum):
    IDLE = "idle"
    WORKING = "working"
    LEARNING = "learning"
    RESTING = "resting"
    REPRODUCING = "reproducing"
    DYING = "dying"
    DEAD = "dead"


ROLE_NAMES = {
    AgentRole.LI: "吏部",
    AgentRole.HU: "户部",
    AgentRole.LI_GUAN: "礼部",
    AgentRole.BING: "兵部",
    AgentRole.XING: "刑部",
    AgentRole.GONG: "工部",
    AgentRole.ZHONGSHU: "中书省",
    AgentRole.MENXIA: "门下省",
    AgentRole.SHANGSHU: "尚书省",
}

ROLE_CAPABILITIES = {
    AgentRole.LI: ["team_management", "resource_allocation", "agent_evaluation"],
    AgentRole.HU: ["points_management", "asset_tracking", "budget_analysis"],
    AgentRole.LI_GUAN: ["consultation", "emotional_support", "response_generation"],
    AgentRole.BING: ["data_collection", "source_management", "web_crawling"],
    AgentRole.XING: ["risk_assessment", "anomaly_detection", "compliance_audit"],
    AgentRole.GONG: ["report_generation", "data_analysis", "visualization"],
    AgentRole.ZHONGSHU: ["task_decomposition", "intent_recognition", "strategy_planning"],
    AgentRole.MENXIA: ["compliance_check", "risk_review", "approval_workflow"],
    AgentRole.SHANGSHU: ["task_execution", "resource_scheduling", "progress_monitoring"],
}

ENERGY_COSTS = {
    "base_metabolism": 0.1,
    "working": 0.5,
    "learning": 0.3,
    "resting": -0.2,
    "reproducing": 50.0,
}


class AgentManager:
    """
    智能体生命周期管理器
    
    Features:
    - 智能体招募/解雇
    - 能量系统管理
    - 等级升级
    - 状态追踪
    - 默认智能体群初始化
    """
    
    _instance: Optional['AgentManager'] = None
    _lock = asyncio.Lock()
    
    def __init__(self):
        self._db = None
        self._initialized = False
        self._agents_cache: Dict[str, Dict] = {}
    
    @classmethod
    async def get_instance(cls) -> 'AgentManager':
        if cls._instance is None:
            async with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
                    await cls._instance._initialize()
        return cls._instance
    
    async def _initialize(self):
        if self._initialized:
            return
        self._db = await PostgreSQLConnectionPool.get_instance()
        self._initialized = True
        logger.info("AgentManager initialized")
    
    async def recruit_agent(
        self,
        user_id: str,
        role: AgentRole,
        name: Optional[str] = None,
        level: int = 1,
        capabilities: Optional[List[str]] = None
    ) -> Dict:
        """
        招募新智能体
        
        Args:
            user_id: 用户ID
            role: 智能体角色
            name: 名称 (可选, 自动生成)
            level: 初始等级
            capabilities: 能力列表 (可选, 使用默认)
        
        Returns:
            智能体信息
        """
        agent_id = str(uuid.uuid4())
        
        if name is None:
            name = f"{ROLE_NAMES[role]}_{random.randint(1000, 9999)}"
        
        if capabilities is None:
            capabilities = ROLE_CAPABILITIES.get(role, [])
        
        gene_pool = {
            "efficiency": random.uniform(0.7, 1.0),
            "accuracy": random.uniform(0.7, 1.0),
            "creativity": random.uniform(0.5, 1.0),
            "cooperation": random.uniform(0.6, 1.0),
        }
        
        async with self._db.get_connection() as conn:
            await conn.execute("""
                INSERT INTO agents (id, user_id, name, role, level, capabilities, gene_pool)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, agent_id, user_id, name, role.value, level, capabilities, gene_pool)
            
            await self._log_energy_change(conn, agent_id, 0, 100.0, "initial_recruitment")
        
        agent = {
            "id": agent_id,
            "user_id": user_id,
            "name": name,
            "role": role.value,
            "level": level,
            "energy": 100.0,
            "status": AgentStatus.IDLE.value,
            "capabilities": capabilities,
            "gene_pool": gene_pool,
        }
        
        self._agents_cache[agent_id] = agent
        logger.info(f"Agent recruited: {name} ({role.value}) for user {user_id}")
        
        return agent
    
    async def dismiss_agent(self, agent_id: str) -> bool:
        """解雇智能体"""
        async with self._db.get_connection() as conn:
            result = await conn.execute("""
                UPDATE agents SET status = $1 WHERE id = $2
            """, AgentStatus.DEAD.value, agent_id)
            
            if result == "UPDATE 0":
                return False
        
        if agent_id in self._agents_cache:
            del self._agents_cache[agent_id]
        
        logger.info(f"Agent dismissed: {agent_id}")
        return True
    
    async def get_agent(self, agent_id: str) -> Optional[Dict]:
        """获取智能体信息"""
        if agent_id in self._agents_cache:
            return self._agents_cache[agent_id]
        
        async with self._db.get_connection() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM agents WHERE id = $1
            """, agent_id)
            
            if row is None:
                return None
            
            agent = dict(row)
            self._agents_cache[agent_id] = agent
            return agent
    
    async def get_user_agents(
        self, 
        user_id: str,
        role: Optional[AgentRole] = None,
        status: Optional[AgentStatus] = None
    ) -> List[Dict]:
        """获取用户的智能体列表"""
        async with self._db.get_connection() as conn:
            query = "SELECT * FROM agents WHERE user_id = $1"
            params = [user_id]
            
            if role:
                query += f" AND role = ${len(params) + 1}"
                params.append(role.value)
            
            if status:
                query += f" AND status = ${len(params) + 1}"
                params.append(status.value)
            
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]
    
    async def update_agent_status(
        self, 
        agent_id: str, 
        status: AgentStatus
    ) -> bool:
        """更新智能体状态"""
        async with self._db.get_connection() as conn:
            result = await conn.execute("""
                UPDATE agents SET status = $1 WHERE id = $2
            """, status.value, agent_id)
            
            if result == "UPDATE 0":
                return False
        
        if agent_id in self._agents_cache:
            self._agents_cache[agent_id]["status"] = status.value
        
        return True
    
    async def consume_energy(
        self, 
        agent_id: str, 
        amount: float,
        reason: str = "task_execution"
    ) -> float:
        """
        消耗智能体能量
        
        Args:
            agent_id: 智能体ID
            amount: 消耗量
            reason: 消耗原因
        
        Returns:
            剩余能量
        """
        async with self._db.get_connection() as conn:
            row = await conn.fetchrow("""
                SELECT energy FROM agents WHERE id = $1 FOR UPDATE
            """, agent_id)
            
            if row is None:
                raise ValueError(f"Agent {agent_id} not found")
            
            old_energy = row['energy']
            new_energy = max(0, old_energy - amount)
            
            await conn.execute("""
                UPDATE agents SET energy = $1 WHERE id = $2
            """, new_energy, agent_id)
            
            await self._log_energy_change(conn, agent_id, old_energy, new_energy, reason)
        
        if agent_id in self._agents_cache:
            self._agents_cache[agent_id]["energy"] = new_energy
        
        logger.debug(f"Agent {agent_id} consumed {amount} energy ({reason}), remaining: {new_energy}")
        return new_energy
    
    async def restore_energy(
        self, 
        agent_id: str, 
        amount: Optional[float] = None
    ) -> float:
        """恢复智能体能量"""
        async with self._db.get_connection() as conn:
            row = await conn.fetchrow("""
                SELECT energy, max_energy FROM agents WHERE id = $1 FOR UPDATE
            """, agent_id)
            
            if row is None:
                raise ValueError(f"Agent {agent_id} not found")
            
            old_energy = row['energy']
            max_energy = row['max_energy']
            
            if amount is None:
                new_energy = max_energy
            else:
                new_energy = min(max_energy, old_energy + amount)
            
            await conn.execute("""
                UPDATE agents SET energy = $1, status = $2 WHERE id = $3
            """, new_energy, AgentStatus.IDLE.value, agent_id)
            
            await self._log_energy_change(conn, agent_id, old_energy, new_energy, "rest")
        
        if agent_id in self._agents_cache:
            self._agents_cache[agent_id]["energy"] = new_energy
            self._agents_cache[agent_id]["status"] = AgentStatus.IDLE.value
        
        return new_energy
    
    async def upgrade_agent(self, agent_id: str) -> bool:
        """升级智能体"""
        async with self._db.get_connection() as conn:
            row = await conn.fetchrow("""
                SELECT level, experience FROM agents WHERE id = $1 FOR UPDATE
            """, agent_id)
            
            if row is None:
                return False
            
            current_level = row['level']
            experience = row['experience']
            
            if current_level >= 10:
                return False
            
            required_exp = current_level * 100
            if experience < required_exp:
                return False
            
            new_level = current_level + 1
            new_max_energy = 100 + (new_level - 1) * 10
            
            await conn.execute("""
                UPDATE agents 
                SET level = $1, max_energy = $2, experience = experience - $3
                WHERE id = $4
            """, new_level, new_max_energy, required_exp, agent_id)
        
        if agent_id in self._agents_cache:
            self._agents_cache[agent_id]["level"] = new_level
            self._agents_cache[agent_id]["max_energy"] = new_max_energy
        
        logger.info(f"Agent {agent_id} upgraded to level {new_level}")
        return True
    
    async def add_experience(
        self, 
        agent_id: str, 
        amount: int,
        task_success: bool = True
    ) -> bool:
        """添加经验值"""
        async with self._db.get_connection() as conn:
            await conn.execute("""
                UPDATE agents 
                SET experience = experience + $1,
                    total_tasks_completed = total_tasks_completed + 1
                WHERE id = $2
            """, amount, agent_id)
        
        if agent_id in self._agents_cache:
            self._agents_cache[agent_id]["experience"] = self._agents_cache[agent_id].get("experience", 0) + amount
        
        return True
    
    async def select_best_agent(
        self,
        user_id: str,
        role: AgentRole,
        min_energy: float = 20.0
    ) -> Optional[Dict]:
        """
        选择最佳智能体
        
        Args:
            user_id: 用户ID
            role: 所需角色
            min_energy: 最低能量要求
        
        Returns:
            最佳智能体或None
        """
        agents = await self.get_user_agents(user_id, role, AgentStatus.IDLE)
        
        eligible = [a for a in agents if a['energy'] >= min_energy]
        
        if not eligible:
            return None
        
        eligible.sort(key=lambda a: (
            -a['level'],
            -a['energy'],
            -a.get('success_rate', 0)
        ))
        
        return eligible[0]
    
    async def init_default_agents(self, user_id: str) -> List[Dict]:
        """
        为新用户初始化默认智能体群
        
        Args:
            user_id: 用户ID
        
        Returns:
            创建的智能体列表
        """
        default_roles = [
            AgentRole.ZHONGSHU,
            AgentRole.MENXIA,
            AgentRole.SHANGSHU,
            AgentRole.LI,
            AgentRole.BING,
            AgentRole.GONG,
        ]
        
        created_agents = []
        
        for role in default_roles:
            agent = await self.recruit_agent(user_id, role)
            created_agents.append(agent)
        
        async with self._db.get_connection() as conn:
            await conn.execute("""
                INSERT INTO user_default_agents (user_id, default_agent_ids)
                VALUES ($1, $2)
                ON CONFLICT (user_id) DO UPDATE SET default_agent_ids = $2
            """, user_id, {a['role']: a['id'] for a in created_agents})
        
        logger.info(f"Initialized {len(created_agents)} default agents for user {user_id}")
        return created_agents
    
    async def get_agent_stats(self, agent_id: str) -> Dict:
        """获取智能体统计信息"""
        async with self._db.get_connection() as conn:
            stats = await conn.fetchrow("""
                SELECT 
                    a.*,
                    COUNT(al.id) as total_actions,
                    AVG(al.duration_ms) FILTER (WHERE al.success = true) as avg_duration_ms,
                    COUNT(al.id) FILTER (WHERE al.success = true) as successful_actions,
                    COUNT(al.id) FILTER (WHERE al.success = false) as failed_actions
                FROM agents a
                LEFT JOIN agent_logs al ON a.id = al.agent_id
                WHERE a.id = $1
                GROUP BY a.id
            """, agent_id)
            
            if stats is None:
                return {}
            
            return dict(stats)
    
    async def _log_energy_change(
        self,
        conn,
        agent_id: str,
        energy_before: float,
        energy_after: float,
        reason: str
    ):
        """记录能量变化"""
        await conn.execute("""
            INSERT INTO agent_energy_log (agent_id, energy_before, energy_after, energy_delta, reason)
            VALUES ($1, $2, $3, $4, $5)
        """, agent_id, energy_before, energy_after, energy_after - energy_before, reason)
    
    async def get_online_agents_count(self) -> int:
        """获取在线智能体数量"""
        async with self._db.get_connection() as conn:
            count = await conn.fetchval("""
                SELECT COUNT(*) FROM agents 
                WHERE status NOT IN ($1, $2)
            """, AgentStatus.DEAD.value, AgentStatus.DYING.value)
            return count


agent_manager: Optional[AgentManager] = None


async def get_agent_manager() -> AgentManager:
    global agent_manager
    if agent_manager is None:
        agent_manager = await AgentManager.get_instance()
    elif not agent_manager._initialized:
        await agent_manager._initialize()
    return agent_manager
