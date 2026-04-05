"""
实训模式API端点
提供任务复制、模板管理、报告对比功能
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import copy
from app.api.v1.schemas.training import (
    TaskForkRequest, TaskForkResponse,
    TemplateMarkRequest, TemplateResponse,
    ComparisonResult, AgentParameterConfig
)
from app.services.comparator import comparator


router = APIRouter()

# 模拟数据库存储
_tasks_db = {}
_task_forks_db = {}


def get_current_user_id() -> str:
    """获取当前用户ID（模拟）"""
    return "user-123"


def check_teacher_permission(user_id: str) -> bool:
    """检查教师权限（模拟）"""
    # 实际项目中应从数据库查询用户角色
    return True


# ========== 实训API ==========

@router.post("/tasks/{task_id}/fork", response_model=TaskForkResponse)
async def fork_task(
    task_id: str,
    fork_request: TaskForkRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    复制任务
    
    Args:
        task_id: 原任务ID
        fork_request: 复制请求（包含参数覆盖）
        user_id: 当前用户ID
        
    Returns:
        TaskForkResponse: 复制结果
    """
    try:
        # 检查原任务是否存在
        if task_id not in _tasks_db:
            raise HTTPException(status_code=404, detail="Task not found")
        
        original_task = _tasks_db[task_id]
        
        # 检查权限：只能复制模板或自己的任务
        is_template = original_task.get("is_template", False)
        is_owner = original_task.get("user_id") == user_id
        
        if not (is_template or is_owner):
            raise HTTPException(status_code=403, detail="Can only fork templates or own tasks")
        
        # 创建新任务ID
        forked_task_id = str(uuid.uuid4())
        created_at = datetime.utcnow().isoformat()
        
        # 深拷贝原任务
        forked_task = copy.deepcopy(original_task)
        
        # 更新任务信息
        forked_task["task_id"] = forked_task_id
        forked_task["parent_task_id"] = task_id
        forked_task["user_id"] = user_id
        forked_task["created_at"] = created_at
        forked_task["status"] = "PENDING"
        forked_task["is_template"] = False
        forked_task["result"] = None
        
        # 应用参数覆盖
        if fork_request.overrides:
            if "agent_configs" not in forked_task:
                forked_task["agent_configs"] = {}
            
            for agent_name, params in fork_request.overrides.items():
                if agent_name not in forked_task["agent_configs"]:
                    forked_task["agent_configs"][agent_name] = {}
                
                forked_task["agent_configs"][agent_name].update(params)
        
        # 保存新任务
        _tasks_db[forked_task_id] = forked_task
        
        # 记录复制关系
        fork_record = {
            "id": str(uuid.uuid4()),
            "original_task_id": task_id,
            "forked_task_id": forked_task_id,
            "user_id": user_id,
            "overrides": fork_request.overrides,
            "created_at": created_at
        }
        _task_forks_db[fork_record["id"]] = fork_record
        
        return TaskForkResponse(
            original_task_id=task_id,
            forked_task_id=forked_task_id,
            message="Task forked successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates", response_model=List[TemplateResponse])
async def list_templates(
    user_id: str = Depends(get_current_user_id),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """
    列出所有模板
    
    Args:
        user_id: 当前用户ID
        skip: 跳过数量
        limit: 返回数量
        
    Returns:
        List[TemplateResponse]: 模板列表
    """
    try:
        # 检查教师权限
        if not check_teacher_permission(user_id):
            raise HTTPException(status_code=403, detail="Only teachers can view templates")
        
        # 查找所有模板
        templates = []
        for task in _tasks_db.values():
            if task.get("is_template", False):
                # 计算复制次数
                fork_count = sum(
                    1 for f in _task_forks_db.values()
                    if f["original_task_id"] == task["task_id"]
                )
                
                template = TemplateResponse(
                    task_id=task["task_id"],
                    query=task.get("query", ""),
                    style=task.get("style", "balanced"),
                    created_at=task.get("created_at", ""),
                    created_by=task.get("user_id", ""),
                    fork_count=fork_count,
                    expected_results=task.get("expected_results")
                )
                templates.append(template)
        
        # 分页
        return templates[skip:skip + limit]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/tasks/{task_id}/template")
async def mark_as_template(
    task_id: str,
    template_request: TemplateMarkRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    将任务标记为模板
    
    Args:
        task_id: 任务ID
        template_request: 模板标记请求
        user_id: 当前用户ID
        
    Returns:
        dict: 操作结果
    """
    try:
        # 检查教师权限
        if not check_teacher_permission(user_id):
            raise HTTPException(status_code=403, detail="Only teachers can create templates")
        
        # 检查任务是否存在
        if task_id not in _tasks_db:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # 检查是否是任务所有者
        task = _tasks_db[task_id]
        if task["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Can only mark own tasks as template")
        
        # 更新任务
        task["is_template"] = template_request.is_template
        if template_request.expected_results:
            task["expected_results"] = template_request.expected_results
        
        return {
            "task_id": task_id,
            "is_template": template_request.is_template,
            "message": "Template status updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}/compare/{forked_task_id}", response_model=ComparisonResult)
async def compare_reports(
    task_id: str,
    forked_task_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    对比两个任务的报告
    
    Args:
        task_id: 原任务ID
        forked_task_id: 复制任务ID
        user_id: 当前用户ID
        
    Returns:
        ComparisonResult: 对比结果
    """
    try:
        # 检查任务是否存在
        if task_id not in _tasks_db:
            raise HTTPException(status_code=404, detail="Original task not found")
        
        if forked_task_id not in _tasks_db:
            raise HTTPException(status_code=404, detail="Forked task not found")
        
        original_task = _tasks_db[task_id]
        forked_task = _tasks_db[forked_task_id]
        
        # 检查权限
        if original_task["user_id"] != user_id and forked_task["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to compare these tasks")
        
        # 执行对比
        result = comparator.compare(original_task, forked_task)
        
        return ComparisonResult(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}/forks")
async def list_task_forks(
    task_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    列出任务的所有复制版本
    
    Args:
        task_id: 任务ID
        user_id: 当前用户ID
        
    Returns:
        List: 复制版本列表
    """
    try:
        # 检查任务是否存在
        if task_id not in _tasks_db:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # 查找所有复制版本
        forks = []
        for fork in _task_forks_db.values():
            if fork["original_task_id"] == task_id:
                forked_task = _tasks_db.get(fork["forked_task_id"])
                if forked_task:
                    forks.append({
                        "fork_id": fork["id"],
                        "task_id": fork["forked_task_id"],
                        "user_id": fork["user_id"],
                        "created_at": fork["created_at"],
                        "status": forked_task.get("status"),
                        "overrides": fork.get("overrides")
                    })
        
        return forks
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}/parameters", response_model=Dict[str, AgentParameterConfig])
async def get_task_parameters(
    task_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    获取任务的代理参数配置
    
    Args:
        task_id: 任务ID
        user_id: 当前用户ID
        
    Returns:
        Dict: 代理参数配置
    """
    try:
        # 检查任务是否存在
        if task_id not in _tasks_db:
            raise HTTPException(status_code=404, detail="Task not found")
        
        task = _tasks_db[task_id]
        
        # 返回代理配置
        agent_configs = task.get("agent_configs", {})
        
        result = {}
        for agent_name, config in agent_configs.items():
            result[agent_name] = AgentParameterConfig(**config)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
