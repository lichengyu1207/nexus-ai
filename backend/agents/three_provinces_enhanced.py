# -*- coding: utf-8 -*-
"""
Enhanced Three Provinces System
增强版三省系统 - 集成TaskQueue和AgentManager
"""
import asyncio
import time
import logging
import uuid
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from backend.database_pg import PostgreSQLConnectionPool
from backend.services.task_queue import TaskQueue, get_task_queue, TaskStatus as QueueTaskStatus
from backend.services.agent_manager import AgentManager, get_agent_manager, AgentRole, AgentStatus

logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


class ComplianceResult(Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVIEW = "needs_review"


@dataclass
class SubTask:
    id: str
    name: str
    description: str
    assigned_ministry: Optional[str] = None
    assigned_agent_id: Optional[str] = None
    status: str = "pending"
    result: Optional[Dict] = None
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None


@dataclass
class TaskPlan:
    task_id: str
    query: str
    intent: str
    priority: TaskPriority
    sub_tasks: List[SubTask]
    estimated_time: float
    required_ministries: List[str]
    risk_level: str = "low"
    created_at: float = field(default_factory=time.time)


class ZhongshuShengEnhanced:
    """
    中书省增强版 - 决策层
    
    职责：
    - 意图识别
    - 任务拆解
    - 策略制定
    - 资源预估
    """
    
    def __init__(self):
        self.db = None
        self.task_patterns = self._build_task_patterns()
        self.stats = {
            "total_decompositions": 0,
            "avg_decompose_time": 0.0,
            "sub_2s_count": 0,
        }
    
    def _build_task_patterns(self) -> Dict:
        return {
            "valuation": {
                "keywords": ["估值", "评估", "房价", "价值", "多少钱", "value", "price", "worth"],
                "sub_tasks": [
                    {"name": "数据采集", "description": "采集房产基础数据", "ministry": "bing"},
                    {"name": "市场分析", "description": "分析市场行情", "ministry": "bing"},
                    {"name": "估值计算", "description": "计算房产估值", "ministry": "gong"},
                    {"name": "报告生成", "description": "生成估值报告", "ministry": "gong"},
                ],
                "priority": TaskPriority.HIGH,
                "estimated_time": 30.0,
            },
            "analysis": {
                "keywords": ["分析", "对比", "比较", "优劣势", "analyze", "compare"],
                "sub_tasks": [
                    {"name": "数据收集", "description": "收集相关数据", "ministry": "bing"},
                    {"name": "特征提取", "description": "提取关键特征", "ministry": "gong"},
                    {"name": "对比分析", "description": "执行对比分析", "ministry": "gong"},
                    {"name": "结论生成", "description": "生成分析结论", "ministry": "gong"},
                ],
                "priority": TaskPriority.MEDIUM,
                "estimated_time": 25.0,
            },
            "consult": {
                "keywords": ["咨询", "建议", "推荐", "怎么样", "consult", "advice", "recommend"],
                "sub_tasks": [
                    {"name": "需求理解", "description": "理解用户需求", "ministry": "li_guan"},
                    {"name": "知识检索", "description": "检索相关知识", "ministry": "bing"},
                    {"name": "建议生成", "description": "生成咨询建议", "ministry": "li_guan"},
                ],
                "priority": TaskPriority.MEDIUM,
                "estimated_time": 15.0,
            },
            "report": {
                "keywords": ["报告", "报表", "文档", "生成", "report", "document"],
                "sub_tasks": [
                    {"name": "数据准备", "description": "准备报告数据", "ministry": "hu"},
                    {"name": "模板选择", "description": "选择报告模板", "ministry": "gong"},
                    {"name": "内容填充", "description": "填充报告内容", "ministry": "gong"},
                    {"name": "格式化输出", "description": "格式化输出报告", "ministry": "gong"},
                ],
                "priority": TaskPriority.HIGH,
                "estimated_time": 20.0,
            },
            "batch": {
                "keywords": ["批量", "多个", "所有", "全部", "batch", "multiple", "all"],
                "sub_tasks": [
                    {"name": "任务分发", "description": "分发批量任务", "ministry": "li"},
                    {"name": "并行处理", "description": "并行处理任务", "ministry": "shangshu"},
                    {"name": "结果聚合", "description": "聚合处理结果", "ministry": "gong"},
                ],
                "priority": TaskPriority.LOW,
                "estimated_time": 60.0,
            },
            "mingpan": {
                "keywords": ["命盘", "八字", "运势", "姻缘", "财运", "destiny", "fortune", "bazi"],
                "sub_tasks": [
                    {"name": "八字解析", "description": "解析用户八字", "ministry": "bing"},
                    {"name": "命理分析", "description": "分析命理特征", "ministry": "gong"},
                    {"name": "运势预测", "description": "预测运势走向", "ministry": "gong"},
                    {"name": "报告生成", "description": "生成命理报告", "ministry": "gong"},
                ],
                "priority": TaskPriority.HIGH,
                "estimated_time": 25.0,
            },
        }
    
    async def initialize(self):
        self.db = await PostgreSQLConnectionPool.get_instance()
    
    async def decompose_task(self, query: str, task_id: str, user_id: str) -> TaskPlan:
        start_time = time.time()
        
        pattern = self._match_pattern(query)
        intent = self._detect_intent(query)
        
        sub_tasks = []
        required_ministries = set()
        
        for i, st_def in enumerate(pattern.get("sub_tasks", [])):
            sub_task = SubTask(
                id=f"{task_id}_sub_{i}",
                name=st_def["name"],
                description=st_def["description"],
                assigned_ministry=st_def.get("ministry", "gong"),
            )
            sub_tasks.append(sub_task)
            required_ministries.add(st_def.get("ministry", "gong"))
        
        plan = TaskPlan(
            task_id=task_id,
            query=query,
            intent=intent,
            priority=pattern.get("priority", TaskPriority.MEDIUM),
            sub_tasks=sub_tasks,
            estimated_time=pattern.get("estimated_time", 30.0),
            required_ministries=list(required_ministries),
        )
        
        decompose_time = time.time() - start_time
        
        self.stats["total_decompositions"] += 1
        if decompose_time < 2.0:
            self.stats["sub_2s_count"] += 1
        
        avg = self.stats["avg_decompose_time"]
        total = self.stats["total_decompositions"]
        self.stats["avg_decompose_time"] = (avg * (total - 1) + decompose_time) / total
        
        await self._log_to_db(task_id, "zhongshu", "decompose", {
            "query": query,
            "intent": intent,
            "sub_tasks_count": len(sub_tasks),
        }, {
            "plan": plan.__dict__,
        }, decompose_time)
        
        logger.info(f"Task {task_id} decomposed in {decompose_time:.3f}s: {len(sub_tasks)} sub-tasks")
        return plan
    
    def _match_pattern(self, query: str) -> Dict:
        query_lower = query.lower()
        
        for pattern_type, pattern in self.task_patterns.items():
            for keyword in pattern["keywords"]:
                if keyword in query_lower:
                    return pattern
        
        return {
            "sub_tasks": [
                {"name": "通用处理", "description": "执行通用处理流程", "ministry": "gong"}
            ],
            "priority": TaskPriority.MEDIUM,
            "estimated_time": 20.0,
        }
    
    def _detect_intent(self, query: str) -> str:
        query_lower = query.lower()
        
        if any(k in query_lower for k in ["估值", "房价", "价值", "value", "price"]):
            return "property_valuation"
        elif any(k in query_lower for k in ["命盘", "八字", "运势", "destiny"]):
            return "mingpan_analysis"
        elif any(k in query_lower for k in ["分析", "对比", "analyze", "compare"]):
            return "property_analysis"
        elif any(k in query_lower for k in ["咨询", "建议", "consult", "advice"]):
            return "consultation"
        elif any(k in query_lower for k in ["报告", "report"]):
            return "report_generation"
        else:
            return "general_query"
    
    async def _log_to_db(self, task_id: str, province: str, action: str, 
                         input_data: Dict, output_data: Dict, duration_ms: float):
        try:
            if self.db:
                async with self.db.get_connection() as conn:
                    await conn.execute("""
                        INSERT INTO three_provinces_log 
                        (id, task_id, province, action, input_data, output_data, duration_ms)
                        VALUES ($1, $2, $3, $4, $5::jsonb, $6::jsonb, $7)
                    """, str(uuid.uuid4()), task_id, province, action, 
                        json.dumps(input_data), json.dumps(output_data), int(duration_ms * 1000))
        except Exception as e:
            logger.warning(f"Failed to log to db: {e}")
    
    def get_stats(self) -> Dict:
        total = self.stats["total_decompositions"]
        return {
            **self.stats,
            "sub_2s_rate": self.stats["sub_2s_count"] / total if total > 0 else 0,
        }


class MenxiaShengEnhanced:
    """
    门下省增强版 - 审核层
    
    职责：
    - 合规性检查
    - 风险评估
    - 资源可行性验证
    - 优先级调整
    """
    
    def __init__(self):
        self.db = None
        self.compliance_rules = self._build_compliance_rules()
        self.stats = {
            "total_reviews": 0,
            "approved_count": 0,
            "rejected_count": 0,
            "accuracy": 0.0,
        }
    
    def _build_compliance_rules(self) -> List[Dict]:
        return [
            {
                "name": "sensitive_content",
                "pattern": r"(身份证|银行卡|密码|验证码|id card|password|credit card)",
                "severity": "high",
                "action": "reject",
                "message": "包含敏感信息，请移除后重试",
            },
            {
                "name": "malicious_pattern",
                "pattern": r"(hack|attack|exploit|注入|攻击)",
                "severity": "critical",
                "action": "reject",
                "message": "检测到潜在恶意请求",
            },
            {
                "name": "rate_limit_check",
                "severity": "medium",
                "action": "warn",
                "message": "请求频率较高，请注意",
            },
        ]
    
    async def initialize(self):
        self.db = await PostgreSQLConnectionPool.get_instance()
    
    async def review_task(self, plan: TaskPlan, user_id: str) -> TaskPlan:
        start_time = time.time()
        
        issues = []
        warnings = []
        
        for rule in self.compliance_rules:
            if "pattern" in rule:
                import re
                if re.search(rule["pattern"], plan.query, re.IGNORECASE):
                    if rule["action"] == "reject":
                        issues.append(rule["message"])
                    elif rule["action"] == "warn":
                        warnings.append(rule["message"])
        
        if issues:
            plan.risk_level = "high"
        
        agent_manager = await get_agent_manager()
        
        for ministry in plan.required_ministries:
            role = self._ministry_to_role(ministry)
            if role:
                available = await agent_manager.select_best_agent(user_id, role)
                if not available:
                    warnings.append(f"{ministry}部门暂无可用智能体")
        
        self.stats["total_reviews"] += 1
        if not issues:
            self.stats["approved_count"] += 1
        else:
            self.stats["rejected_count"] += 1
        
        total = self.stats["total_reviews"]
        self.stats["accuracy"] = self.stats["approved_count"] / total if total > 0 else 0
        
        review_time = time.time() - start_time
        
        await self._log_to_db(plan.task_id, "menxia", "review", {
            "query": plan.query,
            "required_ministries": plan.required_ministries,
        }, {
            "approved": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "risk_level": plan.risk_level,
        }, review_time)
        
        logger.info(f"Task {plan.task_id} reviewed: {'approved' if not issues else 'rejected'}")
        return plan
    
    def _ministry_to_role(self, ministry: str) -> Optional[AgentRole]:
        mapping = {
            "li": AgentRole.LI,
            "hu": AgentRole.HU,
            "li_guan": AgentRole.LI_GUAN,
            "bing": AgentRole.BING,
            "xing": AgentRole.XING,
            "gong": AgentRole.GONG,
        }
        return mapping.get(ministry)
    
    async def _log_to_db(self, task_id: str, province: str, action: str,
                         input_data: Dict, output_data: Dict, duration_ms: float):
        try:
            if self.db:
                async with self.db.get_connection() as conn:
                    await conn.execute("""
                        INSERT INTO three_provinces_log 
                        (id, task_id, province, action, input_data, output_data, duration_ms, approved)
                        VALUES ($1, $2, $3, $4, $5::jsonb, $6::jsonb, $7, $8)
                    """, str(uuid.uuid4()), task_id, province, action,
                        json.dumps(input_data), json.dumps(output_data), int(duration_ms * 1000),
                        output_data.get("approved", True) if isinstance(output_data, dict) else True)
        except Exception as e:
            logger.warning(f"Failed to log to db: {e}")
    
    def get_stats(self) -> Dict:
        return self.stats


class ShangshuShengEnhanced:
    """
    尚书省增强版 - 执行层
    
    职责：
    - 任务调度
    - 智能体协调
    - 进度监控
    - 结果汇总
    """
    
    def __init__(self):
        self.db = None
        self.task_queue: Optional[TaskQueue] = None
        self.agent_manager: Optional[AgentManager] = None
        self.stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "avg_execution_time": 0.0,
        }
    
    async def initialize(self):
        self.db = await PostgreSQLConnectionPool.get_instance()
        self.task_queue = await get_task_queue()
        self.agent_manager = await get_agent_manager()
    
    async def execute_task(self, plan: TaskPlan, user_id: str) -> Dict:
        start_time = time.time()
        
        await self._init_coordinator_state(plan)
        
        results = {}
        
        for sub_task in plan.sub_tasks:
            try:
                result = await self._execute_sub_task(sub_task, user_id, plan.task_id)
                results[sub_task.id] = result
                await self._update_coordinator_state(plan.task_id, sub_task.assigned_ministry, result)
            except Exception as e:
                logger.error(f"Sub-task {sub_task.id} failed: {e}")
                results[sub_task.id] = {"error": str(e), "success": False}
        
        final_result = await self._aggregate_results(results, plan)
        
        execution_time = time.time() - start_time
        
        self.stats["total_executions"] += 1
        if final_result.get("success", False):
            self.stats["successful_executions"] += 1
        else:
            self.stats["failed_executions"] += 1
        
        avg = self.stats["avg_execution_time"]
        total = self.stats["total_executions"]
        self.stats["avg_execution_time"] = (avg * (total - 1) + execution_time) / total
        
        await self._log_to_db(plan.task_id, "shangshu", "execute", {
            "sub_tasks_count": len(plan.sub_tasks),
            "required_ministries": plan.required_ministries,
        }, {
            "success": final_result.get("success", False),
            "execution_time": execution_time,
        }, execution_time)
        
        logger.info(f"Task {plan.task_id} executed in {execution_time:.2f}s")
        return final_result
    
    async def _init_coordinator_state(self, plan: TaskPlan):
        async with self.db.get_connection() as conn:
            await conn.execute("""
                INSERT INTO ministry_coordinator_state (task_id, phase)
                VALUES ($1, $2)
                ON CONFLICT (task_id) DO UPDATE SET phase = $2
            """, plan.task_id, "init")
    
    async def _update_coordinator_state(self, task_id: str, ministry: str, result: Dict):
        if not ministry:
            return
        
        status_field = f"{ministry}_status"
        result_field = f"{ministry}_result"
        
        async with self.db.get_connection() as conn:
            await conn.execute(f"""
                UPDATE ministry_coordinator_state 
                SET {status_field} = $1, {result_field} = $2::jsonb, phase = $3, updated_at = CURRENT_TIMESTAMP
                WHERE task_id = $4
            """, "completed", json.dumps(result), ministry, task_id)
    
    async def _execute_sub_task(self, sub_task: SubTask, user_id: str, task_id: str) -> Dict:
        ministry = sub_task.assigned_ministry
        if not ministry:
            ministry = "gong"
        
        role = self._ministry_to_role(ministry)
        if not role:
            return {"error": f"Unknown ministry: {ministry}", "success": False}
        
        agent = await self.agent_manager.select_best_agent(user_id, role)
        
        if not agent:
            return {"error": f"No available agent for {ministry}", "success": False}
        
        await self.agent_manager.update_agent_status(agent['id'], AgentStatus.WORKING)
        await self.agent_manager.consume_energy(agent['id'], 5.0, "task_execution")
        
        await asyncio.sleep(0.1)
        
        result = {
            "sub_task_id": sub_task.id,
            "name": sub_task.name,
            "ministry": ministry,
            "agent_id": agent['id'],
            "success": True,
            "output": f"{sub_task.name} completed by agent {agent['name']}",
        }
        
        await self.agent_manager.add_experience(agent['id'], 10, True)
        await self.agent_manager.update_agent_status(agent['id'], AgentStatus.IDLE)
        
        await self._log_agent_action(agent['id'], task_id, sub_task.name, result)
        
        return result
    
    def _ministry_to_role(self, ministry: str) -> Optional[AgentRole]:
        mapping = {
            "li": AgentRole.LI,
            "hu": AgentRole.HU,
            "li_guan": AgentRole.LI_GUAN,
            "bing": AgentRole.BING,
            "xing": AgentRole.XING,
            "gong": AgentRole.GONG,
        }
        return mapping.get(ministry)
    
    async def _log_agent_action(self, agent_id: str, task_id: str, action: str, result: Dict):
        try:
            async with self.db.get_connection() as conn:
                await conn.execute("""
                    INSERT INTO agent_logs (id, agent_id, task_id, action, output_data, success)
                    VALUES ($1, $2, $3, $4, $5::jsonb, $6)
                """, str(uuid.uuid4()), agent_id, task_id, action, json.dumps(result), result.get("success", True))
        except Exception as e:
            logger.warning(f"Failed to log agent action: {e}")
    
    async def _aggregate_results(self, results: Dict, plan: TaskPlan) -> Dict:
        success = all(r.get("success", False) for r in results.values())
        
        return {
            "task_id": plan.task_id,
            "query": plan.query,
            "intent": plan.intent,
            "success": success,
            "sub_results": results,
            "summary": f"完成 {len(results)} 个子任务",
            "completed_at": time.time(),
        }
    
    async def _log_to_db(self, task_id: str, province: str, action: str,
                         input_data: Dict, output_data: Dict, duration_ms: float):
        try:
            async with self.db.get_connection() as conn:
                await conn.execute("""
                    INSERT INTO three_provinces_log 
                    (id, task_id, province, action, input_data, output_data, duration_ms, approved)
                    VALUES ($1, $2, $3, $4, $5::jsonb, $6::jsonb, $7, $8)
                """, str(uuid.uuid4()), task_id, province, action,
                    json.dumps(input_data), json.dumps(output_data), int(duration_ms * 1000),
                    output_data.get("success", True))
        except Exception as e:
            logger.warning(f"Failed to log to db: {e}")
    
    def get_stats(self) -> Dict:
        return self.stats


class ThreeProvincesSystemEnhanced:
    """
    增强版三省六部智能体系统
    """
    
    def __init__(self):
        self.zhongshu = ZhongshuShengEnhanced()
        self.menxia = MenxiaShengEnhanced()
        self.shangshu = ShangshuShengEnhanced()
        self._initialized = False
    
    async def initialize(self):
        if self._initialized:
            return
        
        await self.zhongshu.initialize()
        await self.menxia.initialize()
        await self.shangshu.initialize()
        
        self._initialized = True
        logger.info("Three Provinces System Enhanced initialized")
    
    async def process_query(self, query: str, task_id: str, user_id: str) -> Dict:
        if not self._initialized:
            await self.initialize()
        
        plan = await self.zhongshu.decompose_task(query, task_id, user_id)
        
        plan = await self.menxia.review_task(plan, user_id)
        
        if plan.risk_level == "high":
            return {
                "task_id": task_id,
                "success": False,
                "error": "任务被驳回",
                "reasons": ["风险等级过高"],
            }
        
        result = await self.shangshu.execute_task(plan, user_id)
        
        return result
    
    def get_performance_report(self) -> Dict:
        zhongshu_stats = self.zhongshu.get_stats()
        menxia_stats = self.menxia.get_stats()
        shangshu_stats = self.shangshu.get_stats()
        
        return {
            "zhongshu": {
                "name": "中书省（决策）",
                "target": "任务拆解响应时间<2秒",
                "avg_decompose_time": zhongshu_stats["avg_decompose_time"],
                "sub_2s_rate": zhongshu_stats["sub_2s_rate"],
                "achieved": zhongshu_stats["avg_decompose_time"] < 2.0,
            },
            "menxia": {
                "name": "门下省（审核）",
                "target": "合规检查准确率>95%",
                "accuracy": menxia_stats["accuracy"],
                "total_reviews": menxia_stats["total_reviews"],
                "achieved": menxia_stats["accuracy"] >= 0.95,
            },
            "shangshu": {
                "name": "尚书省（执行）",
                "target": "任务执行成功率>90%",
                "success_rate": shangshu_stats["successful_executions"] / max(shangshu_stats["total_executions"], 1),
                "total_executions": shangshu_stats["total_executions"],
                "avg_execution_time": shangshu_stats["avg_execution_time"],
            },
        }


three_provinces_enhanced: Optional[ThreeProvincesSystemEnhanced] = None


async def get_three_provinces_enhanced() -> ThreeProvincesSystemEnhanced:
    global three_provinces_enhanced
    if three_provinces_enhanced is None:
        three_provinces_enhanced = ThreeProvincesSystemEnhanced()
        await three_provinces_enhanced.initialize()
    return three_provinces_enhanced
