# -*- coding: utf-8 -*-
"""
三省六部API路由
提供中书省、门下省、尚书省的API接口
"""
import uuid
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field

from backend.agents.three_provinces_enhanced import (
    ThreeProvincesSystemEnhanced,
    get_three_provinces_enhanced
)
from backend.services.task_queue import TaskQueue, get_task_queue
from backend.services.agent_manager import AgentManager, get_agent_manager
from backend.services.intent_parser import parse_intent, TaskType
from backend.services.param_extractor import extract_params, generate_questions
from backend.services.task_dag import build_task_dag, infer_dependencies, get_task_dag_info
from backend.services.task_metrics import get_metrics_collector, TaskMetricsCollector

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/three-provinces", tags=["Three Provinces"])


class ParseRequest(BaseModel):
    query: str = Field(..., description="用户自然语言查询")
    user_id: str = Field(..., description="用户ID")
    context: Optional[Dict[str, Any]] = Field(default=None, description="上下文信息")


class ParseResponse(BaseModel):
    task_id: str
    intent: str
    sub_tasks: List[Dict[str, Any]]
    priority: int
    estimated_time: float
    required_ministries: List[str]


class AuditRequest(BaseModel):
    task_id: str
    query: str
    user_id: str


class AuditResponse(BaseModel):
    approved: bool
    risk_level: str
    warnings: List[str]
    issues: List[str]


class ExecuteRequest(BaseModel):
    task_id: str
    query: str
    user_id: str
    priority: int = Field(default=5, ge=1, le=10)


class ExecuteResponse(BaseModel):
    task_id: str
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    progress: float
    result: Optional[Dict[str, Any]] = None


async def get_queue() -> TaskQueue:
    return await get_task_queue()


async def get_manager() -> AgentManager:
    return await get_agent_manager()


async def get_provinces_system() -> ThreeProvincesSystemEnhanced:
    return await get_three_provinces_enhanced()


@router.post("/zhongshu/parse", response_model=ParseResponse)
async def zhongshu_parse(request: ParseRequest):
    """
    中书省接口 - 解析用户请求
    
    接收用户自然语言输入，返回结构化任务计划
    """
    try:
        provinces = await get_provinces_system()
        task_id = str(uuid.uuid4())
        
        plan = await provinces.zhongshu.decompose_task(
            query=request.query,
            task_id=task_id,
            user_id=request.user_id
        )
        
        return ParseResponse(
            task_id=plan.task_id,
            intent=plan.intent,
            sub_tasks=[
                {
                    "id": st.id,
                    "name": st.name,
                    "description": st.description,
                    "ministry": st.assigned_ministry,
                }
                for st in plan.sub_tasks
            ],
            priority=plan.priority.value if hasattr(plan.priority, 'value') else plan.priority,
            estimated_time=plan.estimated_time,
            required_ministries=plan.required_ministries,
        )
        
    except Exception as e:
        logger.error(f"Parse error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/menxia/audit", response_model=AuditResponse)
async def menxia_audit(request: AuditRequest):
    """
    门下省接口 - 审核任务计划
    
    对任务计划进行合规性检查和风险评估
    """
    try:
        provinces = await get_provinces_system()
        
        from backend.agents.three_provinces_enhanced import TaskPlan, TaskPriority
        
        plan = TaskPlan(
            task_id=request.task_id,
            query=request.query,
            intent="unknown",
            priority=TaskPriority.MEDIUM,
            sub_tasks=[],
            estimated_time=30.0,
            required_ministries=["gong"],
        )
        
        reviewed_plan = await provinces.menxia.review_task(
            plan=plan,
            user_id=request.user_id
        )
        
        return AuditResponse(
            approved=reviewed_plan.risk_level != "high",
            risk_level=reviewed_plan.risk_level,
            warnings=[],
            issues=[],
        )
        
    except Exception as e:
        logger.error(f"Audit error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/shangshu/execute", response_model=ExecuteResponse)
async def shangshu_execute(request: ExecuteRequest):
    """
    尚书省接口 - 执行任务
    
    调度六部智能体执行任务
    """
    try:
        provinces = await get_provinces_system()
        
        result = await provinces.process_query(
            query=request.query,
            task_id=request.task_id,
            user_id=request.user_id
        )
        
        return ExecuteResponse(
            task_id=request.task_id,
            success=result.get("success", False),
            result=result,
            error=result.get("error"),
        )
        
    except Exception as e:
        logger.error(f"Execute error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/shangshu/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    查询任务状态
    """
    try:
        queue = await get_queue()
        status = await queue.get_status(task_id)
        
        if status is None:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return TaskStatusResponse(
            task_id=task_id,
            status=status.get("status", "unknown"),
            progress=status.get("progress", 0.0),
            result=status.get("result"),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance")
async def get_performance():
    """
    获取三省系统性能报告
    """
    try:
        provinces = await get_provinces_system()
        return provinces.get_performance_report()
    except Exception as e:
        logger.error(f"Performance error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_system_stats():
    """
    获取系统统计信息
    """
    try:
        queue = await get_queue()
        manager = await get_manager()
        
        queue_stats = await queue.get_queue_stats()
        online_agents = await manager.get_online_agents_count()
        
        return {
            "queue": queue_stats,
            "agents": {
                "online": online_agents,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class BatchParseRequest(BaseModel):
    text: str = Field(..., description="用户自然语言输入")
    user_id: str = Field(..., description="用户ID")


class BatchParseTaskItem(BaseModel):
    type: str
    confidence: float
    span: str
    params: Dict[str, Any]
    missing_params: List[str]
    question: str
    is_complete: bool


class BatchParseResponseModel(BaseModel):
    tasks: List[BatchParseTaskItem]
    dag_info: Optional[Dict[str, Any]] = None


@router.post("/zhongshu/parse_batch", response_model=BatchParseResponseModel)
async def zhongshu_parse_batch(request: BatchParseRequest):
    """
    中书省批量任务解析接口
    
    解析自然语言输入，识别多个任务，提取参数，构建DAG
    """
    try:
        parse_result = parse_intent(request.text)
        
        tasks = []
        raw_tasks = []
        
        for parsed_task in parse_result.tasks:
            task_type = parsed_task.type
            params_result = extract_params(task_type, request.text)
            
            params = {}
            missing_params = []
            
            for key, param in params_result.items():
                if hasattr(param, 'value'):
                    params[key] = param.value
                    if hasattr(param, 'status') and param.status.value == 'missing':
                        missing_params.append(key)
                else:
                    params[key] = param
            
            question = ""
            if missing_params:
                question = generate_questions(missing_params, task_type)
            
            task_item = BatchParseTaskItem(
                type=task_type.value if hasattr(task_type, 'value') else str(task_type),
                confidence=parsed_task.confidence,
                span=parsed_task.span,
                params=params,
                missing_params=missing_params,
                question=question,
                is_complete=len(missing_params) == 0
            )
            tasks.append(task_item)
            
            raw_tasks.append({
                "id": str(uuid.uuid4()),
                "type": task_type.value if hasattr(task_type, 'value') else str(task_type),
                "params": params,
            })
        
        dag_info = None
        if len(raw_tasks) > 1:
            enhanced_tasks = infer_dependencies(raw_tasks)
            dag = build_task_dag(enhanced_tasks)
            dag_info = get_task_dag_info(dag)
        
        return BatchParseResponseModel(
            tasks=tasks,
            dag_info=dag_info
        )
        
    except Exception as e:
        logger.error(f"Batch parse error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class BatchExecuteRequest(BaseModel):
    tasks: List[Dict[str, Any]] = Field(..., description="任务列表")
    user_id: str = Field(..., description="用户ID")
    parent_task_id: Optional[str] = Field(default=None, description="父任务ID")
    max_concurrent: int = Field(default=5, ge=1, le=10, description="最大并发数")


class BatchExecuteResponse(BaseModel):
    parent_task_id: str
    task_ids: List[str]
    status: str
    dag_info: Optional[Dict[str, Any]] = None


class BatchProgressResponse(BaseModel):
    parent_task_id: str
    total: int
    completed: int
    failed: int
    running: int
    pending: int
    progress_percent: float
    tasks: List[Dict[str, Any]]


@router.post("/shangshu/batch", response_model=BatchExecuteResponse)
async def shangshu_batch_execute(request: BatchExecuteRequest):
    """
    尚书省批量任务执行接口
    
    创建批量任务，构建DAG，调度执行
    """
    try:
        parent_task_id = request.parent_task_id or str(uuid.uuid4())
        
        enhanced_tasks = infer_dependencies(request.tasks)
        
        for task in enhanced_tasks:
            if "id" not in task:
                task["id"] = str(uuid.uuid4())
        
        dag = build_task_dag(enhanced_tasks)
        dag_analysis = dag.analyze()
        
        if dag_analysis.has_cycle:
            raise HTTPException(
                status_code=400, 
                detail=f"检测到循环依赖: {dag_analysis.cycle_nodes}"
            )
        
        task_ids = [task["id"] for task in enhanced_tasks]
        
        dag_info = get_task_dag_info(dag)
        
        queue = await get_queue()
        
        for level_idx, level in enumerate(dag_analysis.parallel_groups):
            for task_id in level:
                task_node = dag.nodes[task_id]
                
                await queue.add_task(
                    task_id=task_id,
                    task_type=task_node.task_type,
                    params=task_node.params,
                    priority=task_node.priority.value,
                    user_id=request.user_id,
                    parent_id=parent_task_id,
                    level=level_idx
                )
        
        return BatchExecuteResponse(
            parent_task_id=parent_task_id,
            task_ids=task_ids,
            status="scheduled",
            dag_info=dag_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch execute error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/shangshu/batch/{parent_task_id}/progress", response_model=BatchProgressResponse)
async def get_batch_progress(parent_task_id: str):
    """
    获取批量任务进度
    """
    try:
        queue = await get_queue()
        
        child_tasks = await queue.get_child_tasks(parent_task_id)
        
        if not child_tasks:
            raise HTTPException(status_code=404, detail="Parent task not found")
        
        total = len(child_tasks)
        completed = sum(1 for t in child_tasks if t.get("status") == "completed")
        failed = sum(1 for t in child_tasks if t.get("status") == "failed")
        running = sum(1 for t in child_tasks if t.get("status") == "running")
        pending = sum(1 for t in child_tasks if t.get("status") == "pending")
        
        progress_percent = round((completed / total) * 100, 1) if total > 0 else 0
        
        tasks_info = [
            {
                "id": t.get("id"),
                "type": t.get("type"),
                "status": t.get("status"),
                "progress": t.get("progress", 0),
                "message": t.get("message", "")
            }
            for t in child_tasks
        ]
        
        return BatchProgressResponse(
            parent_task_id=parent_task_id,
            total=total,
            completed=completed,
            failed=failed,
            running=running,
            pending=pending,
            progress_percent=progress_percent,
            tasks=tasks_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get batch progress error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/shangshu/batch/{parent_task_id}/cancel")
async def cancel_batch_tasks(parent_task_id: str):
    """
    取消批量任务
    """
    try:
        queue = await get_queue()
        
        child_tasks = await queue.get_child_tasks(parent_task_id)
        
        if not child_tasks:
            raise HTTPException(status_code=404, detail="Parent task not found")
        
        cancelled_count = 0
        for task in child_tasks:
            if task.get("status") in ["pending", "running"]:
                await queue.cancel_task(task.get("id"))
                cancelled_count += 1
        
        return {
            "parent_task_id": parent_task_id,
            "cancelled_count": cancelled_count,
            "status": "cancelled"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cancel batch tasks error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics")
async def get_metrics():
    """
    获取Prometheus格式的监控指标
    """
    try:
        collector = get_metrics_collector()
        return {"metrics": collector.get_prometheus_metrics()}
    except Exception as e:
        logger.error(f"Get metrics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/dashboard")
async def get_metrics_dashboard():
    """
    获取仪表盘统计数据
    """
    try:
        collector = get_metrics_collector()
        return collector.get_dashboard_stats()
    except Exception as e:
        logger.error(f"Get dashboard stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/grafana")
async def get_grafana_dashboard():
    """
    获取Grafana仪表盘JSON配置
    """
    try:
        collector = get_metrics_collector()
        return collector.get_grafana_dashboard_json()
    except Exception as e:
        logger.error(f"Get Grafana dashboard error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
