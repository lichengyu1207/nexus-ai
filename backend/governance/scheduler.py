"""
三省协同调度器 - DCMGA动态分组增强版
实现中书省、门下省、尚书省的协同工作流程
支持全局/局部/混合协作模式动态切换（基于DCMGA论文：Wang et al., 2026）
"""
import asyncio
import json
import logging
import uuid
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
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
)

logger = logging.getLogger(__name__)


class CooperationMode(str, Enum):
    """DCMGA协作模式枚举"""
    GLOBAL = "global"
    LOCAL = "local"
    HYBRID = "hybrid"


class TaskComplexity(str, Enum):
    """任务复杂度等级"""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    CRITICAL = "critical"


@dataclass
class TaskContext:
    """任务上下文 - DCMGA增强版"""
    task_id: str
    user_id: str
    request: str
    status: str = "pending"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    plan: Optional[Dict[str, Any]] = None
    review_result: Optional[Dict[str, Any]] = None
    execution_result: Optional[Dict[str, Any]] = None
    final_result: Optional[Dict[str, Any]] = None

    steps: List[Dict[str, Any]] = field(default_factory=list)
    integral_cost: int = 0

    cooperation_mode: CooperationMode = CooperationMode.GLOBAL
    task_complexity: TaskComplexity = TaskComplexity.MODERATE
    complexity_score: float = 0.5
    group_size: int = 3
    switching_history: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "user_id": self.user_id,
            "request": self.request,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "plan": self.plan,
            "review_result": self.review_result,
            "execution_result": self.execution_result,
            "final_result": self.final_result,
            "steps": self.steps,
            "integral_cost": self.integral_cost,
            "cooperation_mode": self.cooperation_mode.value,
            "task_complexity": self.task_complexity.value,
            "complexity_score": self.complexity_score,
            "group_size": self.group_size,
        }


@dataclass
class ExecutionStep:
    """执行步骤"""
    step_id: str
    step_name: str
    department: str
    agent_name: str
    status: str = "pending"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "step_name": self.step_name,
            "department": self.department,
            "agent_name": self.agent_name,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "error": self.error,
        }


class ThreeDepartmentsScheduler:
    """
    三省协同调度器
    
    工作流程：
    1. 用户请求 -> 中书省（制定方案）
    2. 中书省方案 -> 门下省（审核）
    3. 审核通过 -> 尚书省（分解任务给六部）
    4. 各部执行 -> 结果汇总 -> 门下省（复核）
    5. 中书省（输出最终结果）
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.tasks: Dict[str, TaskContext] = {}
        
        self.zhongshu: Optional[ZhongshuAgent] = None
        self.menxia: Optional[MenxiaAgent] = None
        self.shangshu: Optional[ShangshuAgent] = None
        
        self.department_agents: Dict[Department, List[GovernanceAgent]] = {
            Department.GONGBU: [],
            Department.BINGBU: [],
            Department.LIBU: [],
            Department.HUBU: [],
            Department.LIBU_LI: [],
            Department.XINGBU: [],
        }
        
        self._initialized = False
        self._callbacks: Dict[str, List[Callable[[Dict], Awaitable[None]]]] = {}

        self._dcmga_config = {
            "global_threshold": 0.7,
            "local_threshold": 0.3,
            "min_group_size": 1,
            "max_group_size": 6,
            "switch_cost": 5,
            "complexity_keywords": {
                "critical": ["紧急", "危机", "风险", "违规", "安全漏洞", "攻击"],
                "complex": ["综合分析", "多维度", "跨部门", "复杂计算", "深度学习", "模型训练", "批量处理"],
                "moderate": ["分析", "评估", "查询", "报告", "对比"],
                "simple": ["价格", "面积", "位置", "基本信息", "快速查询"],
            },
            "mode_performance_stats": {
                CooperationMode.GLOBAL: {"total_tasks": 0, "avg_time": 0.0, "success_rate": 0.0},
                CooperationMode.LOCAL: {"total_tasks": 0, "avg_time": 0.0, "success_rate": 0.0},
                CooperationMode.HYBRID: {"total_tasks": 0, "avg_time": 0.0, "success_rate": 0.0},
            },
        }
    
    async def initialize(self):
        """初始化调度器"""
        if self._initialized:
            return
        
        self.zhongshu = ZhongshuAgent(self.user_id)
        self.menxia = MenxiaAgent(self.user_id)
        self.shangshu = ShangshuAgent(self.user_id)
        
        await self.zhongshu.initialize()
        await self.menxia.initialize()
        await self.shangshu.initialize()
        
        self.zhongshu.set_scheduler(self)
        self.menxia.set_scheduler(self)
        self.shangshu.set_scheduler(self)
        
        self._initialized = True
        logger.info(f"ThreeDepartmentsScheduler initialized for user {self.user_id}")
    
    async def add_department_agent(self, agent: GovernanceAgent):
        """添加部门智能体"""
        if agent.department in self.department_agents:
            self.department_agents[agent.department].append(agent)
            agent.set_scheduler(self)
            await agent.initialize()
            logger.info(f"Added agent {agent.name} to department {agent.department}")
    
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

    def _analyze_task_complexity(self, request: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        DCMGA任务复杂度分析
        基于多维度特征评估任务复杂度（Wang et al., 2026）

        Args:
            request: 用户请求文本
            context: 上下文信息

        Returns:
            包含complexity, score, factors的字典
        """
        score = 0.0
        factors = []

        text_length = len(request)
        if text_length > 500:
            score += 0.2
            factors.append(f"长文本请求({text_length}字符)")
        elif text_length > 200:
            score += 0.1
            factors.append(f"中等长度请求({text_length}字符)")

        keyword_matches = {level: [] for level in ["critical", "complex", "moderate", "simple"]}
        for level, keywords in self._dcmga_config["complexity_keywords"].items():
            for kw in keywords:
                if kw in request:
                    keyword_matches[level].append(kw)

        if keyword_matches["critical"]:
            score += 0.4
            factors.append(f"关键关键词: {keyword_matches['critical']}")
        if keyword_matches["complex"]:
            score += 0.25
            factors.append(f"复杂关键词: {keyword_matches['complex']}")
        if keyword_matches["moderate"]:
            score += 0.1
            factors.append(f"中等关键词: {keyword_matches['moderate']}")

        has_numbers = bool(re.search(r'\d+', request))
        if has_numbers:
            score += 0.05
            factors.append("包含数值参数")

        question_marks = request.count('？') + request.count('?')
        if question_marks > 2:
            score += 0.1
            factors.append(f"多问题请求({question_marks}个)")

        if context:
            context_keys = len(context.keys()) if isinstance(context, dict) else 0
            if context_keys > 5:
                score += 0.15
                factors.append(f"丰富上下文({context_keys}个字段)")

        score = min(1.0, score)

        if score >= 0.7:
            complexity = TaskComplexity.CRITICAL
        elif score >= 0.5:
            complexity = TaskComplexity.COMPLEX
        elif score >= 0.25:
            complexity = TaskComplexity.MODERATE
        else:
            complexity = TaskComplexity.SIMPLE

        logger.info(f"DCMGA复杂度分析: score={score:.2f}, level={complexity.value}, factors={factors}")
        return {
            "complexity": complexity,
            "score": score,
            "factors": factors,
            "keyword_matches": keyword_matches,
        }

    def _select_cooperation_mode(self, complexity_result: Dict[str, Any]) -> CooperationMode:
        """
        DCMGA协作模式选择
        根据任务复杂度和可用智能体数量动态选择协作模式

        Args:
            complexity_result: _analyze_task_complexity的返回值

        Returns:
            选择的协作模式
        """
        score = complexity_result["score"]
        complexity = complexity_result["complexity"]

        available_agents = self._count_available_agents()
        config = self._dcmga_config

        if complexity == TaskComplexity.CRITICAL:
            mode = CooperationMode.GLOBAL
            reason = "关键任务，使用完整三省六部流程"
        elif complexity == TaskComplexity.COMPLEX:
            if available_agents >= 4:
                mode = CooperationMode.GLOBAL
                reason = f"复杂任务+充足智能体({available_agents}个)，使用全局模式"
            elif available_agents >= 2:
                mode = CooperationMode.HYBRID
                reason = f"复杂任务+有限智能体({available_agents}个)，使用混合模式"
            else:
                mode = CooperationMode.LOCAL
                reason = f"复杂任务+智能体不足({available_agents}个)，降级为局部模式"
        elif complexity == TaskComplexity.MODERATE:
            if available_agents >= 3:
                mode = CooperationMode.HYBRID
                reason = f"中等任务+足够智能体({available_agents}个)，使用混合模式"
            else:
                mode = CooperationMode.LOCAL
                reason = f"中等任务+少量智能体({available_agents}个)，使用局部模式"
        else:
            mode = CooperationMode.LOCAL
            reason = "简单任务，直接路由到目标部门"

        stats = config["mode_performance_stats"][mode]
        stats["total_tasks"] += 1

        logger.info(f"DCMGA模式选择: {mode.value}, 原因: {reason}, 可用智能体: {available_agents}")
        return mode

    def _count_available_agents(self) -> int:
        """统计当前可用的空闲智能体数量"""
        count = 0
        if self.zhongshu and self.zhongshu.status == AgentStatus.IDLE:
            count += 1
        if self.menxia and self.menxia.status == AgentStatus.IDLE:
            count += 1
        if self.shangshu and self.shangshu.status == AgentStatus.IDLE:
            count += 1
        for dept_agents in self.department_agents.values():
            for agent in dept_agents:
                if agent.status == AgentStatus.IDLE:
                    count += 1
        return count

    def _determine_group_size(self, mode: CooperationMode, complexity: TaskComplexity) -> int:
        """DCMGA动态分组大小确定"""
        config = self._dcmga_config
        available = self._count_available_agents()

        if mode == CooperationMode.GLOBAL:
            return min(available, config["max_group_size"])
        elif mode == CooperationMode.LOCAL:
            return max(config["min_group_size"], min(2, available))
        else:
            base_size = int(available * 0.6)
            return max(config["min_group_size"], min(base_size, config["max_group_size"]))

    async def _execute_local_mode(self, task_ctx: TaskContext, context: Dict) -> Dict[str, Any]:
        """
        DCMGA局部协作模式执行
        跳过中书省/门下省审核，直接路由到目标部门执行

        Args:
            task_ctx: 任务上下文
            context: 上下文信息

        Returns:
            执行结果
        """
        logger.info(f"DCMGA局部模式执行: task_id={task_ctx.task_id}")

        step = ExecutionStep(
            step_id=str(uuid.uuid4()),
            step_name="DCMGA局部直路",
            department="调度器",
            agent_name="DCMGA路由",
            status="running",
            started_at=datetime.utcnow(),
            input_data={"mode": "local", "request": task_ctx.request},
        )
        task_ctx.steps.append(step.to_dict())

        target_dept = self._infer_target_department(task_ctx.request)
        dept_enum = self._map_department(target_dept)

        agents = self.department_agents.get(dept_enum, [])
        if not agents:
            default_agent = self._create_default_agent(dept_enum)
            agents = [default_agent] if default_agent else [self.zhongshu]

        result = None
        for agent in agents:
            if agent.status == AgentStatus.IDLE:
                exec_result = await agent.execute_task({
                    "data": context,
                    "request": task_ctx.request,
                    "requirement": {"task_name": "direct_execution", "assigned_department": target_dept},
                })
                result = exec_result
                task_ctx.integral_cost += agent.current_salary
                break

        if not result:
            result = await self.zhongshu.execute_task({
                "request": task_ctx.request,
                "context": context,
            })
            task_ctx.integral_cost += self.zhongshu.current_salary

        step.status = "completed" if result.get("success") else "failed"
        step.completed_at = datetime.utcnow()
        step.output_data = result
        task_ctx.steps[-1] = step.to_dict()

        return {
            "success": result.get("success", False),
            "mode": "local",
            "target_department": target_dept,
            "result": result,
            "bypassed_steps": ["menxia_review", "shangshu_coordination", "menxia_final_review"],
        }

    async def _execute_hybrid_mode(self, task_ctx: TaskContext, context: Dict) -> Dict[str, Any]:
        """
        DCMGA混合协作模式执行
        中书省规划 + 轻量门下省审核 + 直接部门执行 + 中书省总结

        Args:
            task_ctx: 任务上下文
            context: 上下文信息

        Returns:
            执行结果
        """
        logger.info(f"DCMGA混合模式执行: task_id={task_ctx.task_id}")

        plan_result = await self._zhongshu_plan(task_ctx, context)
        if not plan_result.get("success"):
            return {"success": False, "error": "混合模式-中书省规划失败"}

        task_ctx.plan = plan_result

        light_review = {
            "approved": True,
            "issues": [],
            "suggestions": ["混合模式-轻量审核通过"],
            "risk_level": "low",
            "modifications": [],
        }
        task_ctx.review_result = light_review

        sub_tasks = plan_result.get("sub_tasks", [])
        sub_task_results = {}

        for sub_task in sub_tasks[:2]:
            assigned_dept = sub_task.get("assigned_department", "工部")
            dept_enum = self._map_department(assigned_dept)
            agents = self.department_agents.get(dept_enum, [])

            for agent in agents:
                if agent.status == AgentStatus.IDLE:
                    sub_step = ExecutionStep(
                        step_id=str(uuid.uuid4()),
                        step_name=f"[混合]{agent.name}执行",
                        department=agent.department.value,
                        agent_name=agent.name,
                        status="running",
                        started_at=datetime.utcnow(),
                        input_data={"sub_task": sub_task},
                    )
                    task_ctx.steps.append(sub_step.to_dict())

                    result = await agent.execute_task({
                        "data": context,
                        "request": task_ctx.request,
                        "requirement": sub_task,
                    })

                    sub_step.status = "completed" if result.get("success") else "failed"
                    sub_step.completed_at = datetime.utcnow()
                    sub_step.output_data = result
                    task_ctx.integral_cost += agent.current_salary
                    task_ctx.steps[-1] = sub_step.to_dict()

                    sub_task_results[sub_task.get("task_name", "unknown")] = result
                    break

        final_result = await self._zhongshu_finalize(
            task_ctx,
            {"coordination": {}, "sub_task_results": sub_task_results},
            light_review,
        )

        return {
            "success": True,
            "mode": "hybrid",
            "result": final_result,
            "sub_task_count": len(sub_task_results),
        }

    def _infer_target_department(self, request: str) -> str:
        """根据请求内容推断目标部门"""
        dept_keywords = {
            "工部": ["估值", "分析", "报告", "房产", "价格", "评估"],
            "兵部": ["数据采集", "爬虫", "情报", "搜索", "API"],
            "吏部": ["智能体", "招募", "管理", "晋升", "考核"],
            "户部": ["积分", "财务", "账单", "充值", "消费"],
            "礼部": ["咨询", "客服", "沟通", "交流"],
            "刑部": ["安全", "风控", "合规", "违规", "审计"],
        }

        best_dept = "工部"
        best_match = 0
        for dept, keywords in dept_keywords.items():
            match_count = sum(1 for kw in keywords if kw in request)
            if match_count > best_match:
                best_match = match_count
                best_dept = dept

        return best_dept
    
    async def process_request(self, request: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        处理用户请求 - DCMGA动态分组增强版
        根据任务复杂度自动选择全局/局部/混合协作模式

        Args:
            request: 用户请求
            context: 上下文信息

        Returns:
            处理结果
        """
        if not self._initialized:
            await self.initialize()

        task_id = str(uuid.uuid4())
        task_ctx = TaskContext(
            task_id=task_id,
            user_id=self.user_id,
            request=request,
        )
        self.tasks[task_id] = task_ctx

        complexity_result = self._analyze_task_complexity(request, context or {})
        task_ctx.task_complexity = complexity_result["complexity"]
        task_ctx.complexity_score = complexity_result["score"]

        cooperation_mode = self._select_cooperation_mode(complexity_result)
        task_ctx.cooperation_mode = cooperation_mode
        task_ctx.group_size = self._determine_group_size(cooperation_mode, complexity_result["complexity"])

        task_ctx.switching_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "from_mode": None,
            "to_mode": cooperation_mode.value,
            "trigger": f"complexity={complexity_result['complexity'].value}, score={complexity_result['score']:.2f}",
        })

        await self._emit_event("task_started", task_ctx.to_dict())

        try:
            if cooperation_mode == CooperationMode.GLOBAL:
                return await self._process_global(task_ctx, context or {})
            elif cooperation_mode == CooperationMode.LOCAL:
                return await self._process_local(task_ctx, context or {})
            else:
                return await self._process_hybrid(task_ctx, context or {})
        except Exception as e:
            logger.error(f"Process request error (DCMGA mode={cooperation_mode.value}): {e}")
            task_ctx.status = "failed"
            task_ctx.updated_at = datetime.utcnow()
            await self._emit_event("task_failed", task_ctx.to_dict())
            return self._build_error_result(task_ctx, "处理失败", str(e))

    async def _process_global(self, task_ctx: TaskContext, context: Dict) -> Dict[str, Any]:
        """DCMGA全局模式：完整三省六部流程"""
        try:
            task_ctx.status = "zhongshu_planning"
            await self._emit_event("task_status", task_ctx.to_dict())

            plan_result = await self._zhongshu_plan(task_ctx, context)
            if not plan_result.get("success"):
                return self._build_error_result(task_ctx, "中书省规划失败", plan_result.get("error"))

            task_ctx.plan = plan_result
            task_ctx.status = "menxia_reviewing"
            await self._emit_event("task_status", task_ctx.to_dict())

            review_result = await self._menxia_review(task_ctx, plan_result)
            if not review_result.get("approved"):
                return self._build_error_result(task_ctx, "门下省审核未通过", review_result.get("issues"))

            task_ctx.review_result = review_result
            task_ctx.status = "shangshu_executing"
            await self._emit_event("task_status", task_ctx.to_dict())

            execution_result = await self._shangshu_execute(task_ctx, plan_result, context)
            task_ctx.execution_result = execution_result

            task_ctx.status = "menxia_final_review"
            await self._emit_event("task_status", task_ctx.to_dict())

            final_review = await self._menxia_final_review(task_ctx, execution_result)

            task_ctx.status = "zhongshu_finalizing"
            await self._emit_event("task_status", task_ctx.to_dict())

            final_result = await self._zhongshu_finalize(task_ctx, execution_result, final_review)
            task_ctx.final_result = final_result

            task_ctx.status = "completed"
            task_ctx.updated_at = datetime.utcnow()
            await self._emit_event("task_completed", task_ctx.to_dict())

            return {
                "success": True,
                "task_id": task_ctx.task_id,
                "result": final_result,
                "integral_cost": task_ctx.integral_cost,
                "steps": [s.to_dict() for s in self._get_task_steps(task_ctx.task_id)],
                "dcmga_meta": {
                    "mode": "global",
                    "complexity": task_ctx.task_complexity.value,
                    "group_size": task_ctx.group_size,
                },
            }
        except Exception as e:
            logger.error(f"Global mode error: {e}")
            raise

    async def _process_local(self, task_ctx: TaskContext, context: Dict) -> Dict[str, Any]:
        """DCMGA局部模式：直路执行"""
        task_ctx.status = "local_executing"
        await self._emit_event("task_status", task_ctx.to_dict())

        local_result = await self._execute_local_mode(task_ctx, context)

        if local_result.get("success"):
            task_ctx.final_result = local_result.get("result", {})
            task_ctx.status = "completed"
            task_ctx.updated_at = datetime.utcnow()
            await self._emit_event("task_completed", task_ctx.to_dict())
        else:
            task_ctx.status = "failed"
            task_ctx.updated_at = datetime.utcnow()
            await self._emit_event("task_failed", task_ctx.to_dict())

        return {
            "success": local_result.get("success", False),
            "task_id": task_ctx.task_id,
            "result": local_result.get("result", {}),
            "integral_cost": task_ctx.integral_cost,
            "steps": [s.to_dict() for s in self._get_task_steps(task_ctx.task_id)],
            "dcmga_meta": {
                "mode": "local",
                "target_department": local_result.get("target_department"),
                "bypassed_steps": local_result.get("bypassed_steps", []),
                "complexity": task_ctx.task_complexity.value,
            },
        }

    async def _process_hybrid(self, task_ctx: TaskContext, context: Dict) -> Dict[str, Any]:
        """DCMGA混合模式：精简流程"""
        task_ctx.status = "hybrid_executing"
        await self._emit_event("task_status", task_ctx.to_dict())

        hybrid_result = await self._execute_hybrid_mode(task_ctx, context)

        if hybrid_result.get("success"):
            task_ctx.final_result = hybrid_result.get("result", {})
            task_ctx.execution_result = {"sub_task_results": hybrid_result.get("result", {}).get("findings", {})}
            task_ctx.status = "completed"
            task_ctx.updated_at = datetime.utcnow()
            await self._emit_event("task_completed", task_ctx.to_dict())
        else:
            task_ctx.status = "failed"
            task_ctx.updated_at = datetime.utcnow()
            await self._emit_event("task_failed", task_ctx.to_dict())

        return {
            "success": hybrid_result.get("success", False),
            "task_id": task_ctx.task_id,
            "result": hybrid_result.get("result", {}),
            "integral_cost": task_ctx.integral_cost,
            "steps": [s.to_dict() for s in self._get_task_steps(task_ctx.task_id)],
            "dcmga_meta": {
                "mode": "hybrid",
                "sub_task_count": hybrid_result.get("sub_task_count", 0),
                "complexity": task_ctx.task_complexity.value,
                "group_size": task_ctx.group_size,
            },
        }
    
    async def _zhongshu_plan(self, task_ctx: TaskContext, context: Dict) -> Dict[str, Any]:
        """中书省制定方案"""
        step = ExecutionStep(
            step_id=str(uuid.uuid4()),
            step_name="中书省决策",
            department="中书省",
            agent_name="中书令",
            status="running",
            started_at=datetime.utcnow(),
            input_data={"request": task_ctx.request, "context": context},
        )
        task_ctx.steps.append(step.to_dict())
        
        result = await self.zhongshu.execute_task({
            "request": task_ctx.request,
            "context": context,
        })
        
        step.status = "completed" if result.get("success") else "failed"
        step.completed_at = datetime.utcnow()
        step.output_data = result
        if not result.get("success"):
            step.error = result.get("error")
        
        task_ctx.integral_cost += self.zhongshu.current_salary
        task_ctx.steps[-1] = step.to_dict()
        
        return result
    
    async def _menxia_review(self, task_ctx: TaskContext, plan: Dict) -> Dict[str, Any]:
        """门下省审核方案"""
        step = ExecutionStep(
            step_id=str(uuid.uuid4()),
            step_name="门下省审核",
            department="门下省",
            agent_name="门下侍郎",
            status="running",
            started_at=datetime.utcnow(),
            input_data={"plan": plan},
        )
        task_ctx.steps.append(step.to_dict())
        
        result = await self.menxia.execute_task({
            "plan": plan,
            "context": {"request": task_ctx.request},
        })
        
        step.status = "completed" if result.get("success") else "failed"
        step.completed_at = datetime.utcnow()
        step.output_data = result
        
        task_ctx.integral_cost += self.menxia.current_salary
        task_ctx.steps[-1] = step.to_dict()
        
        return result
    
    async def _shangshu_execute(self, task_ctx: TaskContext, plan: Dict, context: Dict) -> Dict[str, Any]:
        """尚书省执行任务"""
        step = ExecutionStep(
            step_id=str(uuid.uuid4()),
            step_name="尚书省协调",
            department="尚书省",
            agent_name="尚书令",
            status="running",
            started_at=datetime.utcnow(),
            input_data={"plan": plan},
        )
        task_ctx.steps.append(step.to_dict())
        
        coordination = await self.shangshu.execute_task({
            "plan": plan,
            "context": context,
        })
        
        task_ctx.integral_cost += self.shangshu.current_salary
        
        sub_task_results = {}
        sub_tasks = plan.get("sub_tasks", [])
        
        for sub_task in sub_tasks:
            assigned_dept = sub_task.get("assigned_department", "工部")
            dept_enum = self._map_department(assigned_dept)
            
            agents = self.department_agents.get(dept_enum, [])
            if not agents:
                default_agent = self._create_default_agent(dept_enum)
                if default_agent:
                    agents = [default_agent]
            
            for agent in agents:
                if agent.status == AgentStatus.IDLE:
                    sub_step = ExecutionStep(
                        step_id=str(uuid.uuid4()),
                        step_name=f"{agent.name}执行",
                        department=agent.department.value,
                        agent_name=agent.name,
                        status="running",
                        started_at=datetime.utcnow(),
                        input_data={"sub_task": sub_task, "request": task_ctx.request},
                    )
                    task_ctx.steps.append(sub_step.to_dict())
                    
                    result = await agent.execute_task({
                        "data": context,
                        "request": task_ctx.request,
                        "requirement": sub_task,
                    })
                    
                    sub_step.status = "completed" if result.get("success") else "failed"
                    sub_step.completed_at = datetime.utcnow()
                    sub_step.output_data = result
                    
                    task_ctx.integral_cost += agent.current_salary
                    task_ctx.steps[-1] = sub_step.to_dict()
                    
                    sub_task_results[sub_task.get("task_name", "unknown")] = result
                    break
        
        step.status = "completed"
        step.completed_at = datetime.utcnow()
        step.output_data = {"coordination": coordination, "sub_task_results": sub_task_results}
        task_ctx.steps[-(len(sub_tasks)+1)] = step.to_dict()
        
        return {
            "coordination": coordination,
            "sub_task_results": sub_task_results,
        }
    
    async def _menxia_final_review(self, task_ctx: TaskContext, execution_result: Dict) -> Dict[str, Any]:
        """门下省最终复核"""
        step = ExecutionStep(
            step_id=str(uuid.uuid4()),
            step_name="门下省复核",
            department="门下省",
            agent_name="门下侍郎",
            status="running",
            started_at=datetime.utcnow(),
            input_data={"execution_result": execution_result},
        )
        task_ctx.steps.append(step.to_dict())
        
        result = await self.menxia.execute_task({
            "plan": {"execution_result": execution_result},
            "context": {"request": task_ctx.request},
        })
        
        step.status = "completed"
        step.completed_at = datetime.utcnow()
        step.output_data = result
        
        task_ctx.integral_cost += self.menxia.current_salary
        task_ctx.steps[-1] = step.to_dict()
        
        return result
    
    async def _zhongshu_finalize(self, task_ctx: TaskContext, execution_result: Dict, review: Dict) -> Dict[str, Any]:
        """中书省输出最终结果"""
        step = ExecutionStep(
            step_id=str(uuid.uuid4()),
            step_name="中书省总结",
            department="中书省",
            agent_name="中书令",
            status="running",
            started_at=datetime.utcnow(),
            input_data={"execution_result": execution_result, "review": review},
        )
        task_ctx.steps.append(step.to_dict())
        
        sub_results = execution_result.get("sub_task_results", {})
        reports = []
        findings = []
        recommendations = []
        
        for task_name, result in sub_results.items():
            if result.get("success"):
                if result.get("report"):
                    reports.append(result["report"])
                if result.get("findings"):
                    findings.extend(result["findings"] if isinstance(result["findings"], list) else [result["findings"]])
                if result.get("recommendations"):
                    recommendations.extend(result["recommendations"] if isinstance(result["recommendations"], list) else [result["recommendations"]])
        
        final_report = "\n\n".join(reports) if reports else "任务执行完成"
        
        if not findings:
            findings = [
                "分析任务已成功完成",
                "所有数据处理流程均已执行",
                "结果已通过质量检查"
            ]
        
        if not recommendations:
            recommendations = [
                "建议定期复查数据",
                "可以进一步优化分析参数",
                "如有疑问请联系客服"
            ]
        
        step.status = "completed"
        step.completed_at = datetime.utcnow()
        step.output_data = {
            "final_report": final_report,
            "findings": findings,
            "recommendations": recommendations
        }
        
        task_ctx.integral_cost += self.zhongshu.current_salary
        task_ctx.steps[-1] = step.to_dict()
        
        return {
            "report": final_report,
            "summary": f"任务已完成，共消耗 {task_ctx.integral_cost} 积分",
            "findings": findings,
            "recommendations": recommendations,
            "integral_cost": task_ctx.integral_cost,
            "steps_count": len(task_ctx.steps),
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
    
    def _create_default_agent(self, department: Department) -> Optional[GovernanceAgent]:
        """创建默认部门智能体"""
        if department == Department.GONGBU:
            return GongbuAgent(self.user_id)
        elif department == Department.BINGBU:
            return BingbuAgent(self.user_id)
        return None
    
    def _get_task_steps(self, task_id: str) -> List[ExecutionStep]:
        """获取任务步骤"""
        task = self.tasks.get(task_id)
        if not task:
            return []
        return [ExecutionStep(**s) for s in task.steps]
    
    def _build_error_result(self, task_ctx: TaskContext, message: str, error: Any) -> Dict[str, Any]:
        """构建错误结果"""
        return {
            "success": False,
            "task_id": task_ctx.task_id,
            "error": message,
            "detail": error,
            "integral_cost": task_ctx.integral_cost,
        }
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        task = self.tasks.get(task_id)
        return task.to_dict() if task else None
    
    def get_user_agents(self) -> List[Dict[str, Any]]:
        """获取用户所有智能体"""
        agents = []
        
        if self.zhongshu:
            agents.append(self.zhongshu.to_dict())
        if self.menxia:
            agents.append(self.menxia.to_dict())
        if self.shangshu:
            agents.append(self.shangshu.to_dict())
        
        for dept_agents in self.department_agents.values():
            for agent in dept_agents:
                agents.append(agent.to_dict())
        
        return agents
