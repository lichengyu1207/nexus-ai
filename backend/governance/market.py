"""
人才市场模块
管理智能体招募、升级、解雇等功能
"""
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List

from ..database_pg import get_db
from .base import Department, AgentLevel, AgentStatus, GovernanceAgent, create_agent

logger = logging.getLogger(__name__)


@dataclass
class AgentTemplate:
    """智能体模板"""
    id: str
    name: str
    department: Department
    level: AgentLevel
    skills: List[Dict[str, Any]]
    base_salary: int
    recruit_cost: int
    description: str
    available: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "department": self.department.value,
            "level": int(self.level),
            "skills": self.skills,
            "base_salary": self.base_salary,
            "recruit_cost": self.recruit_cost,
            "description": self.description,
            "available": self.available,
        }


@dataclass
class UserAgent:
    """用户拥有的智能体"""
    id: str
    user_id: str
    agent_id: str
    name: str
    department: Department
    level: AgentLevel
    salary: int
    status: AgentStatus
    recruited_at: datetime
    performance: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "agent_id": self.agent_id,
            "name": self.name,
            "department": self.department.value,
            "level": int(self.level),
            "salary": self.salary,
            "status": self.status.value,
            "recruited_at": self.recruited_at.isoformat(),
            "performance": self.performance,
        }


class AgentMarket:
    """
    人才市场管理器
    
    功能：
    - 获取可招募智能体列表
    - 招募智能体
    - 用户已招募智能体列表
    - 升级智能体
    - 解雇智能体
    """
    
    DEFAULT_AGENTS = [
        {
            "id": "zhongshu-ling",
            "name": "中书令",
            "department": "中书省",
            "level": 5,
            "skills": [
                {"name": "需求分析", "description": "解析用户需求，提取关键信息", "efficiency": 1.2},
                {"name": "任务拆解", "description": "将复杂任务拆解为子任务", "efficiency": 1.1},
                {"name": "方案制定", "description": "制定执行方案和资源分配", "efficiency": 1.0},
            ],
            "base_salary": 50,
            "recruit_cost": 500,
            "description": "决策与规划，接收用户需求，拆解任务，制定执行方案",
        },
        {
            "id": "menxia-shilang",
            "name": "门下侍郎",
            "department": "门下省",
            "level": 4,
            "skills": [
                {"name": "方案审核", "description": "审核执行方案的合理性", "efficiency": 1.1},
                {"name": "合规检查", "description": "检查任务是否符合规则", "efficiency": 1.2},
                {"name": "风险评估", "description": "评估执行风险", "efficiency": 1.0},
            ],
            "base_salary": 40,
            "recruit_cost": 400,
            "description": "审核与监督，审核方案，监督执行，确保合规",
        },
        {
            "id": "shangshu-ling",
            "name": "尚书令",
            "department": "尚书省",
            "level": 5,
            "skills": [
                {"name": "任务分发", "description": "将任务分发给合适的部门", "efficiency": 1.2},
                {"name": "资源协调", "description": "协调各部门资源", "efficiency": 1.1},
                {"name": "结果汇总", "description": "汇总各部门执行结果", "efficiency": 1.0},
            ],
            "base_salary": 50,
            "recruit_cost": 500,
            "description": "执行与协调，统领六部，协调资源，汇总结果",
        },
        {
            "id": "libu-shangshu",
            "name": "吏部尚书",
            "department": "吏部",
            "level": 3,
            "skills": [
                {"name": "人才招募", "description": "招募新的智能体", "efficiency": 1.1},
                {"name": "绩效考核", "description": "评估智能体绩效", "efficiency": 1.0},
                {"name": "晋升管理", "description": "管理智能体晋升", "efficiency": 1.0},
            ],
            "base_salary": 30,
            "recruit_cost": 300,
            "description": "智能体管理，招募、晋升、考核、解雇",
        },
        {
            "id": "hubu-shangshu",
            "name": "户部尚书",
            "department": "户部",
            "level": 3,
            "skills": [
                {"name": "积分管理", "description": "管理积分收支", "efficiency": 1.2},
                {"name": "账单处理", "description": "处理用户账单", "efficiency": 1.1},
                {"name": "薪资发放", "description": "发放智能体薪资", "efficiency": 1.0},
            ],
            "base_salary": 30,
            "recruit_cost": 300,
            "description": "财务与积分，处理积分收支、用户账单、智能体薪资",
        },
        {
            "id": "libu-li-shangshu",
            "name": "礼部尚书",
            "department": "礼部",
            "level": 3,
            "skills": [
                {"name": "智能咨询", "description": "回答用户咨询", "efficiency": 1.2},
                {"name": "客户服务", "description": "提供客户服务", "efficiency": 1.1},
                {"name": "对外沟通", "description": "处理对外沟通", "efficiency": 1.0},
            ],
            "base_salary": 30,
            "recruit_cost": 300,
            "description": "外部交流与咨询，智能咨询、客户服务、对外沟通",
        },
        {
            "id": "bingbu-shangshu",
            "name": "兵部尚书",
            "department": "兵部",
            "level": 3,
            "skills": [
                {"name": "数据采集", "description": "采集房产相关数据", "efficiency": 1.2},
                {"name": "情报分析", "description": "分析市场情报", "efficiency": 1.1},
                {"name": "API调用", "description": "调用外部API获取数据", "efficiency": 1.0},
            ],
            "base_salary": 30,
            "recruit_cost": 300,
            "description": "数据采集与情报，网络爬虫、API调用、数据采集",
        },
        {
            "id": "xingbu-shangshu",
            "name": "刑部尚书",
            "department": "刑部",
            "level": 3,
            "skills": [
                {"name": "合规检查", "description": "检查任务合规性", "efficiency": 1.2},
                {"name": "风险预警", "description": "预警潜在风险", "efficiency": 1.1},
                {"name": "异常监控", "description": "监控异常行为", "efficiency": 1.0},
            ],
            "base_salary": 30,
            "recruit_cost": 300,
            "description": "规则与风控，合规检查、风险预警、异常监控",
        },
        {
            "id": "gongbu-shangshu",
            "name": "工部尚书",
            "department": "工部",
            "level": 3,
            "skills": [
                {"name": "数据分析", "description": "分析房产数据", "efficiency": 1.2},
                {"name": "报告生成", "description": "生成专业分析报告", "efficiency": 1.1},
                {"name": "趋势预测", "description": "预测市场趋势", "efficiency": 1.0},
            ],
            "base_salary": 30,
            "recruit_cost": 300,
            "description": "任务分析与报告生成，房产分析报告生成、任务处理",
        },
        {
            "id": "kaogong-si",
            "name": "考功司",
            "department": "吏部",
            "level": 2,
            "skills": [
                {"name": "绩效统计", "description": "统计智能体绩效", "efficiency": 1.0},
                {"name": "考核报告", "description": "生成考核报告", "efficiency": 1.0},
            ],
            "base_salary": 20,
            "recruit_cost": 200,
            "description": "绩效考核专员，负责智能体绩效统计和考核报告",
        },
        {
            "id": "duzhi-si",
            "name": "度支司",
            "department": "户部",
            "level": 2,
            "skills": [
                {"name": "账目核对", "description": "核对积分账目", "efficiency": 1.0},
                {"name": "财务报表", "description": "生成财务报表", "efficiency": 1.0},
            ],
            "base_salary": 20,
            "recruit_cost": 200,
            "description": "财务专员，负责积分账目核对和财务报表",
        },
        {
            "id": "zhuke-si",
            "name": "主客司",
            "department": "礼部",
            "level": 2,
            "skills": [
                {"name": "客户接待", "description": "接待客户咨询", "efficiency": 1.0},
                {"name": "问题解答", "description": "解答常见问题", "efficiency": 1.0},
            ],
            "base_salary": 20,
            "recruit_cost": 200,
            "description": "客户服务专员，负责客户接待和问题解答",
        },
    ]
    
    def __init__(self):
        self._initialized = False
    
    async def initialize(self):
        """初始化人才市场"""
        if self._initialized:
            return
        
        await self._ensure_default_agents()
        self._initialized = True
        logger.info("AgentMarket initialized")
    
    async def _ensure_default_agents(self):
        """确保默认智能体模板存在"""
        async with get_db() as db:
            for agent_data in self.DEFAULT_AGENTS:
                existing = await db.fetchone(
                    "SELECT id FROM agents_market WHERE id = $1",
                    agent_data["id"]
                )
                
                if not existing:
                    await db.execute(
                        """INSERT INTO agents_market 
                           (id, name, department, level, skills, base_salary, recruit_cost, description, available)
                           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)""",
                        agent_data["id"],
                        agent_data["name"],
                        agent_data["department"],
                        agent_data["level"],
                        json.dumps(agent_data["skills"], ensure_ascii=False),
                        agent_data["base_salary"],
                        agent_data["recruit_cost"],
                        agent_data["description"],
                        True
                    )
                    logger.info(f"Created default agent: {agent_data['name']}")
    
    async def get_available_agents(self, department: Optional[str] = None) -> List[AgentTemplate]:
        """
        获取可招募智能体列表
        
        Args:
            department: 部门筛选（可选）
            
        Returns:
            智能体模板列表
        """
        if not self._initialized:
            await self.initialize()
        
        async with get_db() as db:
            if department:
                rows = await db.fetch(
                    "SELECT * FROM agents_market WHERE available = $1 AND department = $2 ORDER BY recruit_cost",
                    True, department
                )
            else:
                rows = await db.fetch(
                    "SELECT * FROM agents_market WHERE available = $1 ORDER BY recruit_cost",
                    True
                )
            
            agents = []
            for row in rows:
                dept = self._map_department(row["department"])
                agents.append(AgentTemplate(
                    id=row["id"],
                    name=row["name"],
                    department=dept,
                    level=AgentLevel(row["level"]),
                    skills=json.loads(row["skills"]) if isinstance(row["skills"], str) else row["skills"],
                    base_salary=row["base_salary"],
                    recruit_cost=row["recruit_cost"],
                    description=row["description"],
                    available=row["available"],
                ))
            
            return agents
    
    async def get_agent_template(self, agent_id: str) -> Optional[AgentTemplate]:
        """获取智能体模板"""
        async with get_db() as db:
            row = await db.fetchone(
                "SELECT * FROM agents_market WHERE id = $1",
                agent_id
            )
            
            if not row:
                return None
            
            dept = self._map_department(row["department"])
            return AgentTemplate(
                id=row["id"],
                name=row["name"],
                department=dept,
                level=AgentLevel(row["level"]),
                skills=json.loads(row["skills"]) if isinstance(row["skills"], str) else row["skills"],
                base_salary=row["base_salary"],
                recruit_cost=row["recruit_cost"],
                description=row["description"],
                available=row["available"],
            )
    
    async def recruit_agent(self, user_id: str, agent_id: str) -> Dict[str, Any]:
        """
        招募智能体
        
        Args:
            user_id: 用户ID
            agent_id: 智能体模板ID
            
        Returns:
            招募结果
        """
        if not self._initialized:
            await self.initialize()
        
        template = await self.get_agent_template(agent_id)
        if not template:
            return {"success": False, "error": "智能体不存在"}
        
        if not template.available:
            return {"success": False, "error": "智能体不可招募"}
        
        async with get_db() as db:
            user_row = await db.fetchone(
                "SELECT integral, governance_level, max_agents FROM users WHERE id = $1",
                user_id
            )
            
            if not user_row:
                return {"success": False, "error": "用户不存在"}
            
            current_integral = user_row["integral"] or 0
            max_agents = user_row["max_agents"] or 10
            
            if current_integral < template.recruit_cost:
                return {"success": False, "error": f"积分不足，需要 {template.recruit_cost} 积分"}
            
            existing_agents = await db.fetch(
                "SELECT id FROM user_agents WHERE user_id = $1 AND status = $2",
                user_id, "active"
            )
            
            if len(existing_agents) >= max_agents:
                return {"success": False, "error": f"已达到智能体数量上限（{max_agents}个）"}
            
            already_recruited = await db.fetchone(
                "SELECT id FROM user_agents WHERE user_id = $1 AND agent_id = $2",
                user_id, agent_id
            )
            
            if already_recruited:
                return {"success": False, "error": "已招募该智能体"}
            
            user_agent_id = str(uuid.uuid4())
            now = datetime.utcnow()
            
            await db.execute(
                """INSERT INTO user_agents 
                   (id, user_id, agent_id, name, level, salary, status, recruited_at)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
                user_agent_id,
                user_id,
                agent_id,
                template.name,
                template.level,
                template.base_salary,
                "active",
                now
            )
            
            await db.execute(
                "UPDATE users SET integral = integral - $1, total_spent_integral = COALESCE(total_spent_integral, 0) + $1 WHERE id = $2",
                template.recruit_cost,
                user_id
            )
            
            await db.execute(
                """INSERT INTO integral_logs (id, user_id, change, action_type, reason, created_at)
                   VALUES ($1, $2, $3, $4, $5, $6)""",
                str(uuid.uuid4()),
                user_id,
                -template.recruit_cost,
                "recruit_agent",
                f"招募智能体：{template.name}",
                now.isoformat()
            )
            
            logger.info(f"User {user_id} recruited agent {template.name}")
            
            return {
                "success": True,
                "user_agent_id": user_agent_id,
                "agent_name": template.name,
                "cost": template.recruit_cost,
                "message": f"成功招募 {template.name}，消耗 {template.recruit_cost} 积分",
            }
    
    async def get_user_agents(self, user_id: str) -> List[UserAgent]:
        """
        获取用户已招募智能体列表
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户智能体列表
        """
        async with get_db() as db:
            rows = await db.fetch(
                """SELECT ua.*, am.name, am.department, am.skills, am.description
                   FROM user_agents ua
                   JOIN agents_market am ON ua.agent_id = am.id
                   WHERE ua.user_id = $1
                   ORDER BY ua.recruited_at DESC""",
                user_id
            )
            
            agents = []
            for row in rows:
                dept = self._map_department(row["department"])
                agents.append(UserAgent(
                    id=row["id"],
                    user_id=row["user_id"],
                    agent_id=row["agent_id"],
                    name=row["name"],
                    department=dept,
                    level=AgentLevel(row["level"]),
                    salary=row["salary"],
                    status=AgentStatus(row["status"]),
                    recruited_at=row["recruited_at"],
                    performance={
                        "skills": json.loads(row["skills"]) if isinstance(row["skills"], str) else row["skills"],
                        "description": row["description"],
                    },
                ))
            
            return agents
    
    async def upgrade_agent(self, user_id: str, user_agent_id: str) -> Dict[str, Any]:
        """
        升级智能体
        
        Args:
            user_id: 用户ID
            user_agent_id: 用户智能体ID
            
        Returns:
            升级结果
        """
        async with get_db() as db:
            agent_row = await db.fetchone(
                "SELECT * FROM user_agents WHERE id = $1 AND user_id = $2",
                user_agent_id, user_id
            )
            
            if not agent_row:
                return {"success": False, "error": "智能体不存在"}
            
            current_level = AgentLevel(agent_row["level"])
            if current_level >= AgentLevel.LEVEL_10:
                return {"success": False, "error": "智能体已达到最高等级"}
            
            template = await self.get_agent_template(agent_row["agent_id"])
            if not template:
                return {"success": False, "error": "智能体模板不存在"}
            
            upgrade_cost = int(template.recruit_cost * (current_level * 0.8))
            
            user_row = await db.fetchone(
                "SELECT integral FROM users WHERE id = $1",
                user_id
            )
            
            if not user_row or (user_row["integral"] or 0) < upgrade_cost:
                return {"success": False, "error": f"积分不足，需要 {upgrade_cost} 积分"}
            
            new_level = AgentLevel(current_level + 1)
            new_salary = int(template.base_salary * (1 + (new_level - 1) * 0.5))
            now = datetime.utcnow()
            
            await db.execute(
                "UPDATE user_agents SET level = $1, salary = $2 WHERE id = $3",
                new_level, new_salary, user_agent_id
            )
            
            await db.execute(
                "UPDATE users SET integral = integral - $1, total_spent_integral = COALESCE(total_spent_integral, 0) + $1 WHERE id = $2",
                upgrade_cost, user_id
            )
            
            await db.execute(
                """INSERT INTO agent_upgrade_logs (id, user_id, user_agent_id, old_level, new_level, cost, upgraded_at)
                   VALUES ($1, $2, $3, $4, $5, $6, $7)""",
                str(uuid.uuid4()),
                user_id,
                user_agent_id,
                current_level,
                new_level,
                upgrade_cost,
                now
            )
            
            await db.execute(
                """INSERT INTO integral_logs (id, user_id, change, action_type, reason, created_at)
                   VALUES ($1, $2, $3, $4, $5, $6)""",
                str(uuid.uuid4()),
                user_id,
                -upgrade_cost,
                "upgrade_agent",
                f"升级智能体：{template.name} Lv.{current_level} -> Lv.{new_level}",
                now.isoformat()
            )
            
            logger.info(f"User {user_id} upgraded agent {template.name} to level {new_level}")
            
            return {
                "success": True,
                "old_level": current_level,
                "new_level": new_level,
                "new_salary": new_salary,
                "cost": upgrade_cost,
                "message": f"成功升级 {template.name} 到 {new_level} 级，消耗 {upgrade_cost} 积分",
            }
    
    async def dismiss_agent(self, user_id: str, user_agent_id: str, refund_rate: float = 0.3) -> Dict[str, Any]:
        """
        解雇智能体
        
        Args:
            user_id: 用户ID
            user_agent_id: 用户智能体ID
            refund_rate: 返还积分比例（默认30%）
            
        Returns:
            解雇结果
        """
        async with get_db() as db:
            agent_row = await db.fetchone(
                "SELECT * FROM user_agents WHERE id = $1 AND user_id = $2",
                user_agent_id, user_id
            )
            
            if not agent_row:
                return {"success": False, "error": "智能体不存在"}
            
            if agent_row["status"] != "active":
                return {"success": False, "error": "智能体已不在职"}
            
            template = await self.get_agent_template(agent_row["agent_id"])
            if not template:
                return {"success": False, "error": "智能体模板不存在"}
            
            level = agent_row["level"]
            total_invested = template.recruit_cost
            for l in range(1, level):
                total_invested += int(template.recruit_cost * (l * 0.8))
            
            refund_amount = int(total_invested * refund_rate)
            now = datetime.utcnow()
            
            await db.execute(
                "UPDATE user_agents SET status = $1 WHERE id = $2",
                "dismissed", user_agent_id
            )
            
            if refund_amount > 0:
                await db.execute(
                    "UPDATE users SET integral = integral + $1 WHERE id = $2",
                    refund_amount, user_id
                )
                
                await db.execute(
                    """INSERT INTO integral_logs (id, user_id, change, action_type, reason, created_at)
                       VALUES ($1, $2, $3, $4, $5, $6)""",
                    str(uuid.uuid4()),
                    user_id,
                    refund_amount,
                    "dismiss_agent",
                    f"解雇智能体返还：{template.name}",
                    now.isoformat()
                )
            
            logger.info(f"User {user_id} dismissed agent {template.name}")
            
            return {
                "success": True,
                "agent_name": template.name,
                "refund_amount": refund_amount,
                "message": f"成功解雇 {template.name}，返还 {refund_amount} 积分",
            }
    
    def _map_department(self, dept_name: str) -> Department:
        """映射部门名称到枚举"""
        mapping = {
            "中书省": Department.ZHONGSHU,
            "门下省": Department.MENXIA,
            "尚书省": Department.SHANGSHU,
            "吏部": Department.LIBU,
            "户部": Department.HUBU,
            "礼部": Department.LIBU_LI,
            "兵部": Department.BINGBU,
            "刑部": Department.XINGBU,
            "工部": Department.GONGBU,
        }
        return mapping.get(dept_name, Department.GONGBU)


agent_market = AgentMarket()
