"""
三省六部制增强调度器
集成记忆系统、动态组队、集群/蜂群机制
"""
import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable, Awaitable

from .base import (
    GovernanceAgent,
    Department,
    AgentStatus,
    ZhongshuAgent,
    MenxiaAgent,
    ShangshuAgent,
    GongbuAgent,
    BingbuAgent,
    HubuAgent,
    LibuAgent,
    XingbuAgent,
    LibuLiAgent,
)

logger = logging.getLogger(__name__)


class EnhancedThreeDepartmentsScheduler:
    """
    增强版三省六部制调度器
    
    集成功能：
    1. 记忆系统 - 存储和检索历史任务经验
    2. 动态组队 - 根据任务需求动态组建团队
    3. 集群/蜂群 - 多个智能体协同工作
    4. 注意力机制 - 聚焦关键任务
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.tasks: Dict[str, Dict] = {}
        
        # 三省核心
        self.zhongshu: Optional[ZhongshuAgent] = None
        self.menxia: Optional[MenxiaAgent] = None
        self.shangshu: Optional[ShangshuAgent] = None
        
        # 六部智能体池
        self.department_agents: Dict[Department, List[GovernanceAgent]] = {
            Department.GONGBU: [],
            Department.BINGBU: [],
            Department.LIBU: [],
            Department.HUBU: [],
            Department.LIBU_LI: [],
            Department.XINGBU: [],
        }
        
        # 高级功能模块
        self.memory_system = None
        self.swarm_system = None
        self.attention_system = None
        
        self._initialized = False
        self._callbacks: Dict[str, List[Callable[[Dict], Awaitable[None]]]] = {}
    
    async def initialize(self):
        """初始化调度器及高级功能"""
        if self._initialized:
            return
        
        # 初始化三省核心
        self.zhongshu = ZhongshuAgent(self.user_id)
        self.menxia = MenxiaAgent(self.user_id)
        self.shangshu = ShangshuAgent(self.user_id)
        
        await self.zhongshu.initialize()
        await self.menxia.initialize()
        await self.shangshu.initialize()
        
        self.zhongshu.set_scheduler(self)
        self.menxia.set_scheduler(self)
        self.shangshu.set_scheduler(self)
        
        # 初始化高级功能模块
        await self._init_memory_system()
        await self._init_swarm_system()
        await self._init_attention_system()
        
        # 初始化六部默认智能体
        await self._init_default_department_agents()
        
        self._initialized = True
        logger.info(f"EnhancedThreeDepartmentsScheduler initialized for user {self.user_id}")
    
    async def _init_memory_system(self):
        """初始化记忆系统"""
        try:
            from backend.agents.memory.memory_immunity import MemoryImmunitySystem
            self.memory_system = MemoryImmunitySystem()
            logger.info("Memory system initialized")
        except Exception as e:
            logger.warning(f"Memory system initialization failed: {e}")
            self.memory_system = None
    
    async def _init_swarm_system(self):
        """初始化蜂群系统"""
        try:
            from backend.services.swarm.task_board import TaskBoard
            from backend.services.swarm.config import SwarmConfig
            self.swarm_system = TaskBoard(SwarmConfig())
            logger.info("Swarm system initialized")
        except Exception as e:
            logger.warning(f"Swarm system initialization failed: {e}")
            self.swarm_system = None
    
    async def _init_attention_system(self):
        """初始化注意力系统"""
        try:
            from backend.models.attention_residual import AttentionResidual
            self.attention_system = AttentionResidual()
            logger.info("Attention system initialized")
        except Exception as e:
            logger.warning(f"Attention system initialization failed: {e}")
            self.attention_system = None
    
    async def _init_default_department_agents(self):
        """初始化六部默认智能体"""
        default_agents = [
            (Department.GONGBU, GongbuAgent(self.user_id)),
            (Department.BINGBU, BingbuAgent(self.user_id)),
            (Department.LIBU, LibuAgent(self.user_id)),
            (Department.HUBU, HubuAgent(self.user_id)),
            (Department.LIBU_LI, LibuLiAgent(self.user_id)),
            (Department.XINGBU, XingbuAgent(self.user_id)),
        ]
        
        for dept, agent in default_agents:
            agent.set_scheduler(self)
            await agent.initialize()
            self.department_agents[dept].append(agent)
    
    async def process_request(self, request: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        处理用户请求 - 完整流程
        
        阶段1: 中书省规划 (检索记忆、制定方案)
        阶段2: 门下省审核 (合规检查、方案审核)
        阶段3: 尚书省执行 (动态组队、六部协同)
        阶段4: 门下省复核 (结果验证)
        阶段5: 中书省总结 (存储记忆、输出结果)
        """
        if not self._initialized:
            await self.initialize()
        
        task_id = str(uuid.uuid4())
        task_ctx = {
            "task_id": task_id,
            "user_id": self.user_id,
            "request": request,
            "context": context or {},
            "status": "initialized",
            "steps": [],
            "integral_cost": 0,
            "memory_refs": [],
        }
        self.tasks[task_id] = task_ctx
        
        try:
            # 阶段1: 中书省规划
            task_ctx["status"] = "zhongshu_planning"
            await self._emit_event("task_status", task_ctx)
            
            # 检索记忆
            memory_context = await self._retrieve_memory(request)
            if memory_context:
                task_ctx["memory_refs"].extend(memory_context.get("refs", []))
            
            plan_result = await self._zhongshu_plan(task_ctx, memory_context)
            if not plan_result.get("success"):
                return self._build_error_result(task_ctx, "中书省规划失败", plan_result.get("error"))
            
            task_ctx["plan"] = plan_result
            
            # 阶段2: 门下省审核
            task_ctx["status"] = "menxia_reviewing"
            await self._emit_event("task_status", task_ctx)
            
            review_result = await self._menxia_review(task_ctx, plan_result)
            if not review_result.get("approved"):
                return self._build_error_result(task_ctx, "门下省审核未通过", review_result.get("issues"))
            
            task_ctx["review_result"] = review_result
            
            # 阶段3: 尚书省执行 (动态组队)
            task_ctx["status"] = "shangshu_executing"
            await self._emit_event("task_status", task_ctx)
            
            # 动态组队
            team = await self._dynamic_team_formation(plan_result)
            task_ctx["team"] = team
            
            execution_result = await self._shangshu_execute(task_ctx, plan_result, team)
            task_ctx["execution_result"] = execution_result
            
            # 阶段4: 门下省复核
            task_ctx["status"] = "menxia_final_review"
            await self._emit_event("task_status", task_ctx)
            
            final_review = await self._menxia_final_review(task_ctx, execution_result)
            
            # 阶段5: 中书省总结
            task_ctx["status"] = "zhongshu_finalizing"
            await self._emit_event("task_status", task_ctx)
            
            final_result = await self._zhongshu_finalize(task_ctx, execution_result, final_review)
            
            # 存储记忆
            await self._store_memory(task_ctx, final_result)
            
            task_ctx["status"] = "completed"
            task_ctx["final_result"] = final_result
            await self._emit_event("task_completed", task_ctx)
            
            return {
                "success": True,
                "task_id": task_id,
                "result": final_result,
                "integral_cost": task_ctx["integral_cost"],
                "steps": task_ctx["steps"],
                "memory_refs": task_ctx["memory_refs"],
                "team": task_ctx.get("team", []),
            }
            
        except Exception as e:
            logger.error(f"Process request error: {e}")
            task_ctx["status"] = "failed"
            await self._emit_event("task_failed", task_ctx)
            return self._build_error_result(task_ctx, "处理失败", str(e))
    
    async def _retrieve_memory(self, request: str) -> Optional[Dict]:
        """从记忆系统检索相关经验"""
        if not self.memory_system:
            return None
        
        try:
            # 检索相关记忆
            memories = await self.memory_system.retrieve(
                query=request,
                limit=5,
                min_confidence=0.6
            )
            
            if memories:
                return {
                    "refs": [m.get("memory_id") for m in memories],
                    "context": "\n".join([m.get("summary", "") for m in memories]),
                    "suggestions": [m.get("context", {}).get("suggestions", []) for m in memories]
                }
        except Exception as e:
            logger.warning(f"Memory retrieval failed: {e}")
        
        return None
    
    async def _store_memory(self, task_ctx: Dict, result: Dict):
        """将任务结果存储到记忆系统"""
        if not self.memory_system:
            return
        
        try:
            await self.memory_system.store(
                content=json.dumps({
                    "request": task_ctx["request"],
                    "result": result,
                    "integral_cost": task_ctx["integral_cost"],
                }),
                source_type="agent_generated",
                source_id=f"scheduler_{self.user_id}",
                metadata={
                    "task_id": task_ctx["task_id"],
                    "steps": len(task_ctx["steps"]),
                }
            )
        except Exception as e:
            logger.warning(f"Memory storage failed: {e}")
    
    async def _dynamic_team_formation(self, plan: Dict) -> List[Dict]:
        """动态组队 - 根据任务需求组建最优团队"""
        sub_tasks = plan.get("sub_tasks", [])
        team = []
        
        for sub_task in sub_tasks:
            dept_name = sub_task.get("assigned_department", "工部")
            dept = self._map_department(dept_name)
            
            # 获取该部门可用的智能体
            available_agents = [
                agent for agent in self.department_agents.get(dept, [])
                if agent.status == AgentStatus.IDLE
            ]
            
            # 如果没有可用智能体，创建新的
            if not available_agents:
                new_agent = self._create_department_agent(dept)
                if new_agent:
                    await new_agent.initialize()
                    new_agent.set_scheduler(self)
                    self.department_agents[dept].append(new_agent)
                    available_agents = [new_agent]
            
            # 选择最合适的智能体
            if available_agents:
                best_agent = await self._select_best_agent(available_agents, sub_task)
                team.append({
                    "agent": best_agent,
                    "task": sub_task,
                    "department": dept.value,
                })
        
        return team
    
    async def _select_best_agent(self, agents: List[GovernanceAgent], task: Dict) -> GovernanceAgent:
        """选择最适合任务的智能体"""
        # 简单实现：选择空闲且效率最高的
        best = None
        best_score = -1
        
        for agent in agents:
            if agent.status == AgentStatus.IDLE:
                score = agent.efficiency_multiplier * (1 + agent.performance.success_rate)
                if score > best_score:
                    best_score = score
                    best = agent
        
        return best or agents[0]
    
    async def _zhongshu_plan(self, task_ctx: Dict, memory_context: Optional[Dict]) -> Dict:
        """中书省制定方案"""
        step = {
            "step_id": str(uuid.uuid4()),
            "step_name": "中书省决策",
            "department": "中书省",
            "status": "running",
            "started_at": datetime.utcnow().isoformat(),
        }
        task_ctx["steps"].append(step)
        
        # 合并记忆上下文
        context = task_ctx.get("context", {})
        if memory_context:
            context["memory"] = memory_context
        
        result = await self.zhongshu.execute_task({
            "request": task_ctx["request"],
            "context": context,
        })
        
        step["status"] = "completed" if result.get("success") else "failed"
        step["completed_at"] = datetime.utcnow().isoformat()
        step["output_data"] = result
        
        task_ctx["integral_cost"] += self.zhongshu.current_salary
        
        return result
    
    async def _menxia_review(self, task_ctx: Dict, plan: Dict) -> Dict:
        """门下省审核方案"""
        step = {
            "step_id": str(uuid.uuid4()),
            "step_name": "门下省审核",
            "department": "门下省",
            "status": "running",
            "started_at": datetime.utcnow().isoformat(),
        }
        task_ctx["steps"].append(step)
        
        result = await self.menxia.execute_task({
            "plan": plan,
            "context": {"request": task_ctx["request"]},
        })
        
        step["status"] = "completed"
        step["completed_at"] = datetime.utcnow().isoformat()
        
        task_ctx["integral_cost"] += self.menxia.current_salary
        
        return result
    
    async def _shangshu_execute(self, task_ctx: Dict, plan: Dict, team: List[Dict]) -> Dict:
        """尚书省执行任务 - 六部协同"""
        step = {
            "step_id": str(uuid.uuid4()),
            "step_name": "尚书省协调",
            "department": "尚书省",
            "status": "running",
            "started_at": datetime.utcnow().isoformat(),
        }
        task_ctx["steps"].append(step)
        
        coordination = await self.shangshu.execute_task({
            "plan": plan,
            "context": task_ctx.get("context", {}),
        })
        
        task_ctx["integral_cost"] += self.shangshu.current_salary
        
        # 执行六部任务
        sub_results = {}
        for team_member in team:
            agent = team_member["agent"]
            sub_task = team_member["task"]
            
            sub_step = {
                "step_id": str(uuid.uuid4()),
                "step_name": f"{agent.name}执行",
                "department": team_member["department"],
                "status": "running",
                "started_at": datetime.utcnow().isoformat(),
            }
            task_ctx["steps"].append(sub_step)
            
            result = await agent.execute_task({
                "data": task_ctx.get("context", {}),
                "request": task_ctx["request"],
                "requirement": sub_task,
            })
            
            sub_step["status"] = "completed" if result.get("success") else "failed"
            sub_step["completed_at"] = datetime.utcnow().isoformat()
            
            task_ctx["integral_cost"] += agent.current_salary
            sub_results[sub_task.get("task_name", "unknown")] = result
        
        step["status"] = "completed"
        step["completed_at"] = datetime.utcnow().isoformat()
        
        return {
            "coordination": coordination,
            "sub_task_results": sub_results,
        }
    
    async def _menxia_final_review(self, task_ctx: Dict, execution_result: Dict) -> Dict:
        """门下省最终复核"""
        step = {
            "step_id": str(uuid.uuid4()),
            "step_name": "门下省复核",
            "department": "门下省",
            "status": "running",
            "started_at": datetime.utcnow().isoformat(),
        }
        task_ctx["steps"].append(step)
        
        result = await self.menxia.execute_task({
            "plan": {"execution_result": execution_result},
            "context": {"request": task_ctx["request"]},
        })
        
        step["status"] = "completed"
        step["completed_at"] = datetime.utcnow().isoformat()
        
        task_ctx["integral_cost"] += self.menxia.current_salary
        
        return result
    
    async def _zhongshu_finalize(self, task_ctx: Dict, execution_result: Dict, review: Dict) -> Dict:
        """中书省输出最终结果"""
        step = {
            "step_id": str(uuid.uuid4()),
            "step_name": "中书省总结",
            "department": "中书省",
            "status": "running",
            "started_at": datetime.utcnow().isoformat(),
        }
        task_ctx["steps"].append(step)
        
        sub_results = execution_result.get("sub_task_results", {})
        reports = []
        for task_name, result in sub_results.items():
            if result.get("success") and result.get("report"):
                reports.append(result["report"])
        
        final_report = "\n\n".join(reports) if reports else "任务执行完成"
        
        step["status"] = "completed"
        step["completed_at"] = datetime.utcnow().isoformat()
        
        task_ctx["integral_cost"] += self.zhongshu.current_salary
        
        return {
            "report": final_report,
            "summary": f"任务已完成，共消耗 {task_ctx['integral_cost']} 积分",
            "steps_count": len(task_ctx["steps"]),
        }
    
    def _map_department(self, dept_name: str) -> Department:
        """映射部门名称到枚举"""
        mapping = {
            "工部": Department.GONGBU,
            "兵部": Department.BINGBU,
            "吏部": Department.LIBU,
            "户部": Department.HUBU,
            "礼部": Department.LIBU_LI,
            "刑部": Department.XINGBU,
        }
        return mapping.get(dept_name, Department.GONGBU)
    
    def _create_department_agent(self, department: Department) -> Optional[GovernanceAgent]:
        """创建部门智能体"""
        agent_map = {
            Department.GONGBU: GongbuAgent,
            Department.BINGBU: BingbuAgent,
            Department.LIBU: LibuAgent,
            Department.HUBU: HubuAgent,
            Department.LIBU_LI: LibuLiAgent,
            Department.XINGBU: XingbuAgent,
        }
        
        agent_class = agent_map.get(department)
        if agent_class:
            return agent_class(self.user_id)
        return None
    
    def on_event(self, event_type: str, callback: Callable[[Dict], Awaitable[None]]):
        """注册事件回调"""
        if event_type not in self._callbacks:
            self._callbacks[event_type] = []
        self._callbacks[event_type].append(callback)
    
    async def _emit_event(self, event_type: str, data: Dict):
        """触发事件"""
        callbacks = self._callbacks.get(event_type, [])
        for callback in callbacks:
            try:
                await callback(data)
            except Exception as e:
                logger.error(f"Event callback error: {e}")
    
    def _build_error_result(self, task_ctx: Dict, message: str, error: Any) -> Dict:
        """构建错误结果"""
        return {
            "success": False,
            "task_id": task_ctx["task_id"],
            "error": message,
            "details": str(error) if error else None,
            "integral_cost": task_ctx["integral_cost"],
            "steps": task_ctx["steps"],
        }
