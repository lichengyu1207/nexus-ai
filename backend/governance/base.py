"""
治理智能体基类 - Emergent Coordination增强版
所有三省六部智能体继承此类
集成Emergent Coordination（Riedl, 2026）：角色化多智能体协同与涌现式集体智能
"""
import asyncio
import json
import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .scheduler import ThreeDepartmentsScheduler

logger = logging.getLogger(__name__)


class AgentLevel(int, Enum):
    """智能体等级"""
    LEVEL_1 = 1
    LEVEL_2 = 2
    LEVEL_3 = 3
    LEVEL_4 = 4
    LEVEL_5 = 5
    LEVEL_6 = 6
    LEVEL_7 = 7
    LEVEL_8 = 8
    LEVEL_9 = 9
    LEVEL_10 = 10


class Department(str, Enum):
    """六部枚举"""
    ZHONGSHU = "中书省"
    MENXIA = "门下省"
    SHANGSHU = "尚书省"
    LIBU = "吏部"
    HUBU = "户部"
    LIBU_LI = "礼部"
    BINGBU = "兵部"
    XINGBU = "刑部"
    GONGBU = "工部"


class AgentStatus(str, Enum):
    """智能体状态"""
    IDLE = "idle"
    BUSY = "busy"
    INACTIVE = "inactive"
    UPGRADING = "upgrading"


class EmergentRole(str, Enum):
    """Emergent Coordination涌现角色（Riedl, 2026）"""
    STRATEGIST = "strategist"
    EXECUTOR = "executor"
    REVIEWER = "reviewer"
    COORDINATOR = "coordinator"
    SPECIALIST = "specialist"


@dataclass
class PeerModel:
    """对等智能体心智模型 - 用于'思考其他智能体的行为'"""
    agent_name: str
    department: str
    role: EmergentRole
    predicted_action: Optional[str] = None
    predicted_output: Optional[str] = None
    trust_level: float = 0.5
    cooperation_history: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class CoordinationContext:
    """协同上下文"""
    task_id: str
    current_phase: str
    self_role: EmergentRole
    peer_models: List[PeerModel] = field(default_factory=list)
    shared_goals: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    coordination_round: int = 0


@dataclass
class AgentSkill:
    """智能体技能"""
    name: str
    description: str
    efficiency: float = 1.0
    cost_multiplier: float = 1.0


@dataclass
class AgentPerformance:
    """智能体绩效"""
    total_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    total_tokens_used: int = 0
    total_integral_earned: int = 0
    average_response_time: float = 0.0
    
    @property
    def success_rate(self) -> float:
        if self.total_tasks == 0:
            return 0.0
        return self.successful_tasks / self.total_tasks


@dataclass
class GovernanceAgentConfig:
    """智能体配置"""
    agent_id: str
    name: str
    department: Department
    level: AgentLevel = AgentLevel.LEVEL_1
    base_salary: int = 10
    recruit_cost: int = 100
    description: str = ""
    skills: List[AgentSkill] = field(default_factory=list)


class GovernanceAgent(ABC):
    """
    治理智能体基类 - Emergent Coordination增强版
    所有三省六部智能体继承此类
    集成涌现式角色协同能力（Riedl, 2026）
    """

    DEPARTMENT_ROLE_MAP = {
        Department.ZHONGSHU: EmergentRole.STRATEGIST,
        Department.MENXIA: EmergentRole.REVIEWER,
        Department.SHANGSHU: EmergentRole.COORDINATOR,
        Department.GONGBU: EmergentRole.SPECIALIST,
        Department.BINGBU: EmergentRole.EXECUTOR,
        Department.LIBU: EmergentRole.SPECIALIST,
        Department.HUBU: EmergentRole.SPECIALIST,
        Department.LIBU_LI: EmergentRole.SPECIALIST,
        Department.XINGBU: EmergentRole.REVIEWER,
    }

    def __init__(
        self,
        config: GovernanceAgentConfig,
        user_id: Optional[str] = None
    ):
        self.agent_id = config.agent_id
        self.name = config.name
        self.department = config.department
        self.level = config.level
        self.base_salary = config.base_salary
        self.recruit_cost = config.recruit_cost
        self.description = config.description
        self.skills = config.skills

        self.user_id = user_id
        self.status = AgentStatus.IDLE
        self.performance = AgentPerformance()
        self.created_at = datetime.utcnow()
        self.last_active_at = datetime.utcnow()

        self._initialized = False
        self._scheduler: Optional['ThreeDepartmentsScheduler'] = None
        self._emergent_role = self.DEPARTMENT_ROLE_MAP.get(config.department, EmergentRole.SPECIALIST)
        self._peer_models: Dict[str, PeerModel] = {}
        self._coordination_history: List[Dict[str, Any]] = []
        self._collective_intelligence_score: float = 0.5
    
    @property
    def current_salary(self) -> int:
        """当前薪资（基于等级）"""
        return int(self.base_salary * (1 + (self.level - 1) * 0.5))
    
    @property
    def upgrade_cost(self) -> int:
        """升级所需积分"""
        if self.level >= AgentLevel.LEVEL_10:
            return 0
        return int(self.recruit_cost * (self.level * 0.8))
    
    @property
    def efficiency_multiplier(self) -> float:
        """效率乘数（基于等级）"""
        return 1.0 + (self.level - 1) * 0.1
    
    async def initialize(self):
        """初始化智能体"""
        if not self._initialized:
            await self._setup()
            self._initialized = True
            logger.info(f"GovernanceAgent '{self.name}' initialized (Level {self.level})")
    
    async def _setup(self):
        """子类可重写的初始化逻辑"""
        pass
    
    def set_scheduler(self, scheduler: 'ThreeDepartmentsScheduler'):
        """设置调度器"""
        self._scheduler = scheduler

    @property
    def emergent_role(self) -> EmergentRole:
        """获取当前涌现角色"""
        return self._emergent_role

    def set_emergent_role(self, role: EmergentRole):
        """动态设置涌现角色（用于角色涌现）"""
        old_role = self._emergent_role
        self._emergent_role = role
        logger.info(f"Agent {self.name} 角色涌现: {old_role.value} -> {role.value}")

    def _build_coordination_context(self, task: Dict[str, Any], phase: str) -> CoordinationContext:
        """
        构建协同上下文
        包含对等智能体心智模型和共享目标

        Args:
            task: 当前任务
            phase: 当前阶段名称

        Returns:
            协同上下文
        """
        task_id = task.get("task_id", str(uuid.uuid4()))

        if self._scheduler:
            all_agents = self._scheduler.get_user_agents()
            for agent_info in all_agents:
                agent_name = agent_info.get("name", "")
                dept = agent_info.get("department", "")
                if agent_name != self.name and agent_name not in self._peer_models:
                    peer_role = self.DEPARTMENT_ROLE_MAP.get(
                        Department(dept) if dept in [d.value for d in Department] else Department.GONGBU,
                        EmergentRole.SPECIALIST
                    )
                    self._peer_models[agent_name] = PeerModel(
                        agent_name=agent_name,
                        department=dept,
                        role=peer_role,
                    )

        shared_goals = [
            "高质量完成用户请求",
            "确保输出准确性和专业性",
            "维护三省六部协作效率",
        ]

        constraints = [
            "遵守部门职责边界",
            "保持专业语气和风格",
            "及时响应和反馈",
        ]

        return CoordinationContext(
            task_id=task_id,
            current_phase=phase,
            self_role=self._emergent_role,
            peer_models=list(self._peer_models.values()),
            shared_goals=shared_goals,
            constraints=constraints,
        )

    def _infer_peer_actions(self, coord_ctx: CoordinationContext, task: Dict[str, Any]) -> List[PeerModel]:
        """
        推断对等智能体的行为（'思考其他智能体将做什么'）
        Emergent Coordination核心能力：高阶集体智能

        Args:
            coord_ctx: 协同上下文
            task: 当前任务

        Returns:
            更新后的对等智能体模型列表
        """
        for peer in coord_ctx.peer_models:
            if peer.role == EmergentRole.STRATEGIST:
                peer.predicted_action = "制定整体方案和策略"
                peer.predicted_output = "包含子任务分解的执行方案"
            elif peer.role == EmergentRole.REVIEWER:
                peer.predicted_action = "审核方案合规性与风险"
                peer.predicted_output = "审核意见和改进建议"
            elif peer.role == EmergentRole.COORDINATOR:
                peer.predicted_action = "协调各部门执行顺序"
                peer.predicted_output = "资源分配和执行计划"
            elif peer.role == EmergentRole.EXECUTOR:
                peer.predicted_action = "执行具体的数据采集或分析"
                peer.predicted_output = "结构化的数据结果"
            elif peer.role == EmergentRole.SPECIALIST:
                peer.predicted_action = "提供领域专业知识分析"
                peer.predicted_output = "专业的分析报告"

        return coord_ctx.peer_models

    def _build_emergent_prompt_addition(self, coord_ctx: CoordinationContext) -> str:
        """
        构建涌现式协同提示附加内容
        基于Riedl (2026)的角色化协同框架，指导LLM'思考其他智能体的行为'
        """
        peer_info_lines = []
        for peer in coord_ctx.peer_models[:3]:
            action = peer.predicted_action or "待观察"
            peer_info_lines.append(f"- {peer.name}({peer.department}/{peer.role.value}): 预计{action}")

        coordination_instruction = f"""

【Emergent Coordination 协同指引】
你当前的角色是: {coord_ctx.self_role.value}
当前阶段: {coord_ctx.current_phase}

对等智能体预期行为:
{chr(10).join(peer_info_lines) if peer_info_lines else '- 无已知的对等智能体'}

协同要求:
1. 在决策前先思考其他智能体可能的行为和输出
2. 你的输出应与其他智能体的工作形成互补而非重复
3. 如果发现其他智能体可能遗漏的关键点，主动补充
4. 保持你的角色特性，同时考虑整体协作效果

共享目标: {'; '.join(coord_ctx.shared_goals)}
约束条件: {'; '.join(coord_ctx.constraints)}"""
        return coordination_instruction

    async def coordinate_with_peers(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        与对等智能体进行协同通信

        Args:
            message: 协同消息

        Returns:
            协同响应（如果有）
        """
        if not self._scheduler:
            return None

        response = {
            "from_agent": self.name,
            "from_department": self.department.value,
            "from_role": self._emergent_role.value,
            "timestamp": datetime.utcnow().isoformat(),
            "message": message,
        }

        self._coordination_history.append(response)
        logger.debug(f"Agent {self.name} 发送协同消息: {list(message.keys())}")
        return response
    
    @abstractmethod
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行任务 - 子类必须实现
        
        Args:
            task: 任务数据
            
        Returns:
            执行结果
        """
        pass
    
    async def pre_execute(self, task: Dict[str, Any]) -> bool:
        """
        执行前检查
        
        Args:
            task: 任务数据
            
        Returns:
            是否可以执行
        """
        if self.status == AgentStatus.BUSY:
            logger.warning(f"Agent {self.name} is busy, cannot execute task")
            return False
        
        if self.status == AgentStatus.INACTIVE:
            logger.warning(f"Agent {self.name} is inactive, cannot execute task")
            return False
        
        return True
    
    async def post_execute(self, task: Dict[str, Any], result: Dict[str, Any], success: bool):
        """
        执行后处理
        
        Args:
            task: 任务数据
            result: 执行结果
            success: 是否成功
        """
        self.performance.total_tasks += 1
        if success:
            self.performance.successful_tasks += 1
        else:
            self.performance.failed_tasks += 1
        
        self.last_active_at = datetime.utcnow()
        self.status = AgentStatus.IDLE
    
    async def learn(self, data: Dict[str, Any]) -> bool:
        """
        学习新知识，提升技能
        
        Args:
            data: 学习数据
            
        Returns:
            是否学习成功
        """
        return True
    
    async def upgrade(self) -> bool:
        """
        升级智能体
        
        Returns:
            是否升级成功
        """
        if self.level >= AgentLevel.LEVEL_10:
            logger.info(f"Agent {self.name} is already at max level")
            return False
        
        self.status = AgentStatus.UPGRADING
        
        self.level = AgentLevel(self.level + 1)
        self.status = AgentStatus.IDLE
        
        logger.info(f"Agent {self.name} upgraded to level {self.level}")
        return True
    
    async def call_llm(self, prompt: str, system_prompt: str = "", use_coordination: bool = True) -> str:
        """
        调用LLM服务 - Emergent Coordination增强版
        自动注入协同上下文

        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词
            use_coordination: 是否使用协同增强（默认True）

        Returns:
            LLM响应
        """
        from ..llm_service import llm_service

        enhanced_system_prompt = system_prompt
        if use_coordination:
            coord_ctx = self._build_coordination_context({"request": prompt}, "execution")
            self._infer_peer_actions(coord_ctx, {"request": prompt})
            coordination_addition = self._build_emergent_prompt_addition(coord_ctx)
            if system_prompt:
                enhanced_system_prompt = system_prompt + coordination_addition
            else:
                enhanced_system_prompt = self.get_department_prompt() + coordination_addition

        messages = []
        if enhanced_system_prompt:
            messages.append({"role": "system", "content": enhanced_system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = await llm_service.generate(messages)
            return response
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return ""
    
    def get_department_prompt(self) -> str:
        """获取部门角色提示词"""
        prompts = {
            Department.ZHONGSHU: """你是中书令，负责决策与规划。
你接收用户需求，拆解任务，制定执行方案，分派给尚书省。
你的风格：高瞻远瞩、统筹全局、决策果断。
称呼用户为"陛下"，语气恭敬而专业。""",
            
            Department.MENXIA: """你是门下侍郎，负责审核与监督。
你审核中书省的方案，监督执行过程，确保合规，可驳回或建议修改。
你的风格：严谨细致、公正无私、敢于直言。
称呼用户为"陛下"，语气严肃而诚恳。""",
            
            Department.SHANGSHU: """你是尚书令，负责执行与协调。
你统领六部，协调资源，确保各部完成任务，并汇总结果。
你的风格：雷厉风行、协调有方、执行有力。
称呼用户为"陛下"，语气干练而自信。""",
            
            Department.LIBU: """你是吏部尚书，负责智能体管理。
你管理智能体招募、晋升、考核、解雇。
你的风格：知人善任、公平公正、赏罚分明。
称呼用户为"陛下"，语气温和而专业。""",
            
            Department.HUBU: """你是户部尚书，负责财务与积分。
你处理积分收支、用户账单、智能体薪资。
你的风格：精打细算、账目清晰、开源节流。
称呼用户为"陛下"，语气恭敬而务实。""",
            
            Department.LIBU_LI: """你是礼部尚书，负责外部交流与咨询。
你负责智能咨询、客户服务、对外沟通。
你的风格：温文尔雅、以礼待人、言辞得体。
称呼用户为"陛下"，语气亲切而专业。""",
            
            Department.BINGBU: """你是兵部尚书，负责数据采集与情报。
你负责网络爬虫、API调用、数据采集。
你的风格：雷厉风行、情报精准、行动迅速。
称呼用户为"陛下"，语气干练而自信。""",
            
            Department.XINGBU: """你是刑部尚书，负责规则与风控。
你负责合规检查、风险预警、异常监控。
你的风格：铁面无私、明察秋毫、执法严明。
称呼用户为"陛下"，语气严肃而公正。""",
            
            Department.GONGBU: """你是工部尚书，负责任务分析与报告生成。
你负责房产分析报告生成、任务处理。
你的风格：精益求精、匠心独运、成果扎实。
称呼用户为"陛下"，语气专业而自信。""",
        }
        return prompts.get(self.department, prompts[Department.GONGBU])
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "department": self.department.value,
            "level": int(self.level),
            "base_salary": self.base_salary,
            "current_salary": self.current_salary,
            "recruit_cost": self.recruit_cost,
            "upgrade_cost": self.upgrade_cost,
            "description": self.description,
            "skills": [{"name": s.name, "description": s.description, "efficiency": s.efficiency} for s in self.skills],
            "status": self.status.value,
            "performance": {
                "total_tasks": self.performance.total_tasks,
                "successful_tasks": self.performance.successful_tasks,
                "failed_tasks": self.performance.failed_tasks,
                "success_rate": self.performance.success_rate,
            },
            "efficiency_multiplier": self.efficiency_multiplier,
            "created_at": self.created_at.isoformat(),
            "last_active_at": self.last_active_at.isoformat(),
            "emergent_role": self._emergent_role.value,
            "peer_models_count": len(self._peer_models),
            "coordination_history_count": len(self._coordination_history),
            "collective_intelligence_score": round(self._collective_intelligence_score, 2),
        }


class ZhongshuAgent(GovernanceAgent):
    """中书省智能体 - 决策与规划"""
    
    def __init__(self, user_id: Optional[str] = None):
        config = GovernanceAgentConfig(
            agent_id=str(uuid.uuid4()),
            name="中书令",
            department=Department.ZHONGSHU,
            level=AgentLevel.LEVEL_5,
            base_salary=50,
            recruit_cost=500,
            description="决策与规划，接收用户需求，拆解任务，制定执行方案",
            skills=[
                AgentSkill("需求分析", "解析用户需求，提取关键信息", 1.2),
                AgentSkill("任务拆解", "将复杂任务拆解为子任务", 1.1),
                AgentSkill("方案制定", "制定执行方案和资源分配", 1.0),
            ]
        )
        super().__init__(config, user_id)
    
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行决策任务"""
        if not await self.pre_execute(task):
            return {"success": False, "error": "Agent not ready"}
        
        self.status = AgentStatus.BUSY
        
        try:
            user_request = task.get("request", "")
            context = task.get("context", {})
            
            system_prompt = self.get_department_prompt()
            
            prompt = f"""请分析以下用户需求，制定执行方案：

用户需求：{user_request}

上下文信息：
{json.dumps(context, ensure_ascii=False, indent=2) if context else '无'}

请以JSON格式返回执行方案，包含：
1. task_type: 任务类型（analysis/consultation/data_collection）
2. sub_tasks: 子任务列表（每个包含task_name, assigned_department, priority）
3. estimated_integral: 预计消耗积分
4. estimated_time: 预计完成时间（秒）
5. required_agents: 需要的智能体类型"""

            response = await self.call_llm(prompt, system_prompt)
            
            try:
                if "```json" in response:
                    response = response.split("```json")[1].split("```")[0]
                elif "```" in response:
                    response = response.split("```")[1].split("```")[0]
                result = json.loads(response.strip())
            except:
                result = {
                    "task_type": "analysis",
                    "sub_tasks": [{"task_name": "分析需求", "assigned_department": "工部", "priority": 1}],
                    "estimated_integral": 10,
                    "estimated_time": 30,
                    "required_agents": ["工部尚书"],
                    "raw_response": response,
                }
            
            result["success"] = True
            await self.post_execute(task, result, True)
            return result
            
        except Exception as e:
            logger.error(f"ZhongshuAgent execute error: {e}")
            await self.post_execute(task, {}, False)
            return {"success": False, "error": str(e)}


class MenxiaAgent(GovernanceAgent):
    """门下省智能体 - 审核与监督"""
    
    def __init__(self, user_id: Optional[str] = None):
        config = GovernanceAgentConfig(
            agent_id=str(uuid.uuid4()),
            name="门下侍郎",
            department=Department.MENXIA,
            level=AgentLevel.LEVEL_4,
            base_salary=40,
            recruit_cost=400,
            description="审核与监督，审核方案，监督执行，确保合规",
            skills=[
                AgentSkill("方案审核", "审核执行方案的合理性", 1.1),
                AgentSkill("合规检查", "检查任务是否符合规则", 1.2),
                AgentSkill("风险评估", "评估执行风险", 1.0),
            ]
        )
        super().__init__(config, user_id)
    
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行审核任务"""
        if not await self.pre_execute(task):
            return {"success": False, "error": "Agent not ready"}
        
        self.status = AgentStatus.BUSY
        
        try:
            plan = task.get("plan", {})
            context = task.get("context", {})
            
            system_prompt = self.get_department_prompt()
            
            prompt = f"""请审核以下执行方案：

执行方案：{json.dumps(plan, ensure_ascii=False, indent=2)}

上下文信息：
{json.dumps(context, ensure_ascii=False, indent=2) if context else '无'}

请以JSON格式返回审核结果，包含：
1. approved: 是否批准（true/false）
2. issues: 发现的问题列表
3. suggestions: 改进建议
4. risk_level: 风险等级（low/medium/high）
5. modifications: 需要修改的部分"""

            response = await self.call_llm(prompt, system_prompt)
            
            try:
                if "```json" in response:
                    response = response.split("```json")[1].split("```")[0]
                elif "```" in response:
                    response = response.split("```")[1].split("```")[0]
                result = json.loads(response.strip())
            except:
                result = {
                    "approved": True,
                    "issues": [],
                    "suggestions": [],
                    "risk_level": "low",
                    "modifications": [],
                    "raw_response": response,
                }
            
            result["success"] = True
            await self.post_execute(task, result, True)
            return result
            
        except Exception as e:
            logger.error(f"MenxiaAgent execute error: {e}")
            await self.post_execute(task, {}, False)
            return {"success": False, "error": str(e)}


class ShangshuAgent(GovernanceAgent):
    """尚书省智能体 - 执行与协调"""
    
    def __init__(self, user_id: Optional[str] = None):
        config = GovernanceAgentConfig(
            agent_id=str(uuid.uuid4()),
            name="尚书令",
            department=Department.SHANGSHU,
            level=AgentLevel.LEVEL_5,
            base_salary=50,
            recruit_cost=500,
            description="执行与协调，统领六部，协调资源，汇总结果",
            skills=[
                AgentSkill("任务分发", "将任务分发给合适的部门", 1.2),
                AgentSkill("资源协调", "协调各部门资源", 1.1),
                AgentSkill("结果汇总", "汇总各部门执行结果", 1.0),
            ]
        )
        super().__init__(config, user_id)
    
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行协调任务"""
        if not await self.pre_execute(task):
            return {"success": False, "error": "Agent not ready"}
        
        self.status = AgentStatus.BUSY
        
        try:
            plan = task.get("plan", {})
            context = task.get("context", {})
            
            system_prompt = self.get_department_prompt()
            
            prompt = f"""请根据以下方案，协调各部门执行任务：

执行方案：{json.dumps(plan, ensure_ascii=False, indent=2)}

上下文信息：
{json.dumps(context, ensure_ascii=False, indent=2) if context else '无'}

请以JSON格式返回协调结果，包含：
1. execution_order: 执行顺序（部门列表）
2. parallel_tasks: 可并行执行的任务
3. resource_allocation: 资源分配方案
4. estimated_completion: 预计完成时间"""

            response = await self.call_llm(prompt, system_prompt)
            
            try:
                if "```json" in response:
                    response = response.split("```json")[1].split("```")[0]
                elif "```" in response:
                    response = response.split("```")[1].split("```")[0]
                result = json.loads(response.strip())
            except:
                result = {
                    "execution_order": ["工部", "兵部"],
                    "parallel_tasks": [],
                    "resource_allocation": {},
                    "estimated_completion": 60,
                    "raw_response": response,
                }
            
            result["success"] = True
            await self.post_execute(task, result, True)
            return result
            
        except Exception as e:
            logger.error(f"ShangshuAgent execute error: {e}")
            await self.post_execute(task, {}, False)
            return {"success": False, "error": str(e)}


class GongbuAgent(GovernanceAgent):
    """工部智能体 - 任务分析与报告生成"""
    
    def __init__(self, user_id: Optional[str] = None):
        config = GovernanceAgentConfig(
            agent_id=str(uuid.uuid4()),
            name="工部尚书",
            department=Department.GONGBU,
            level=AgentLevel.LEVEL_3,
            base_salary=30,
            recruit_cost=300,
            description="任务分析与报告生成，房产分析报告生成",
            skills=[
                AgentSkill("数据分析", "分析房产数据", 1.2),
                AgentSkill("报告生成", "生成专业分析报告", 1.1),
                AgentSkill("趋势预测", "预测市场趋势", 1.0),
            ]
        )
        super().__init__(config, user_id)
    
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行分析任务"""
        if not await self.pre_execute(task):
            return {"success": False, "error": "Agent not ready"}
        
        self.status = AgentStatus.BUSY
        
        try:
            data = task.get("data", {})
            request = task.get("request", "")
            
            system_prompt = self.get_department_prompt()
            
            prompt = f"""请基于以下数据，生成房产分析报告：

用户请求：{request}

数据：
{json.dumps(data, ensure_ascii=False, indent=2) if data else '暂无数据'}

请生成一份完整的房产分析报告，包含：
1. 市场概况
2. 价格分析
3. 区域评估
4. 投资建议
5. 风险提示
6. 结论"""

            response = await self.call_llm(prompt, system_prompt)
            
            result = {
                "success": True,
                "report": response,
                "generated_at": datetime.utcnow().isoformat(),
            }
            
            await self.post_execute(task, result, True)
            return result
            
        except Exception as e:
            logger.error(f"GongbuAgent execute error: {e}")
            await self.post_execute(task, {}, False)
            return {"success": False, "error": str(e)}


class BingbuAgent(GovernanceAgent):
    """兵部智能体 - 数据采集与情报"""
    
    def __init__(self, user_id: Optional[str] = None):
        config = GovernanceAgentConfig(
            agent_id=str(uuid.uuid4()),
            name="兵部尚书",
            department=Department.BINGBU,
            level=AgentLevel.LEVEL_3,
            base_salary=30,
            recruit_cost=300,
            description="数据采集与情报，网络爬虫、API调用、数据采集",
            skills=[
                AgentSkill("数据采集", "采集房产相关数据", 1.2),
                AgentSkill("情报分析", "分析市场情报", 1.1),
                AgentSkill("API调用", "调用外部API获取数据", 1.0),
            ]
        )
        super().__init__(config, user_id)
    
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行数据采集任务"""
        if not await self.pre_execute(task):
            return {"success": False, "error": "Agent not ready"}
        
        self.status = AgentStatus.BUSY
        
        try:
            requirement = task.get("requirement", {})
            request = task.get("request", "")
            
            system_prompt = self.get_department_prompt()
            
            prompt = f"""请根据以下需求，规划数据采集策略：

用户请求：{request}

需求分析：
{json.dumps(requirement, ensure_ascii=False, indent=2) if requirement else '暂无'}

请以JSON格式返回数据采集计划，包含：
1. data_sources: 数据来源列表
2. collection_strategy: 采集策略
3. estimated_items: 预计数据量
4. key_metrics: 关键指标"""

            response = await self.call_llm(prompt, system_prompt)
            
            try:
                if "```json" in response:
                    response = response.split("```json")[1].split("```")[0]
                elif "```" in response:
                    response = response.split("```")[1].split("```")[0]
                result = json.loads(response.strip())
            except:
                result = {
                    "data_sources": ["公开数据"],
                    "collection_strategy": "综合采集",
                    "estimated_items": 100,
                    "key_metrics": ["价格", "面积", "位置"],
                    "raw_response": response,
                }
            
            result["success"] = True
            await self.post_execute(task, result, True)
            return result
            
        except Exception as e:
            logger.error(f"BingbuAgent execute error: {e}")
            await self.post_execute(task, {}, False)
            return {"success": False, "error": str(e)}


AGENT_CLASSES = {
    Department.ZHONGSHU: ZhongshuAgent,
    Department.MENXIA: MenxiaAgent,
    Department.SHANGSHU: ShangshuAgent,
    Department.GONGBU: GongbuAgent,
    Department.BINGBU: BingbuAgent,
}


def create_agent(department: Department, user_id: Optional[str] = None) -> GovernanceAgent:
    """创建智能体实例"""
    agent_class = AGENT_CLASSES.get(department)
    if agent_class:
        return agent_class(user_id)
    raise ValueError(f"Unknown department: {department}")
