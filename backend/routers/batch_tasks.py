"""
批量任务创建 API 模块

功能：接收批量任务请求，"""
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, validator
from enum import Enum
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database_pg import get_db
from backend.services.intent_parser import parse_intent_to_dict, TaskType
from backend.services.param_extractor import extract_params_to_dict, get_missing_params


router = APIRouter(prefix="/api/tasks", tags=["batch-tasks"])


class TaskInputMode(str, Enum):
    NATURAL_LANGUAGE = "natural_language"
    STRUCTURED = "structured"
    NATURAL = "natural"


class StructuredTaskInput(BaseModel):
    task_type: str = Field(..., description="任务类型")
    params: Dict[str, Any] = Field(default_factory=dict, description="任务参数")
    priority: int = Field(default=5, ge=1, le=10, description="优先级 1-10")


class NaturalLanguageInput(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000, description="自然语言输入")
    auto_submit: bool = Field(default=False, description="是否自动提交")


class BatchTaskRequest(BaseModel):
    mode: TaskInputMode = Field(default=TaskInputMode.NATURAL_LANGUAGE, description="输入模式")
    natural_language: Optional[NaturalLanguageInput] = Field(None, description="自然语言输入")
    structured_tasks: Optional[List[StructuredTaskInput]] = Field(None, description="结构化任务列表")
    skip_invalid: bool = Field(default=True, description="是否跳过无效任务")
    input: Optional[str] = Field(None, description="自然语言输入(简化格式)")
    input_type: Optional[str] = Field(None, description="输入类型(简化格式)")
    tasks: Optional[List[Dict[str, Any]]] = Field(None, description="结构化任务列表(简化格式)")
    
    @validator('structured_tasks')
    def validate_structured_tasks(cls, v, values):
        if values.get('mode') == TaskInputMode.STRUCTURED and not v:
            raise ValueError('结构化模式下必须提供任务列表')
        return v


class ParsedTaskOutput(BaseModel):
    type: str
    confidence: float
    span: str
    params: Dict[str, Any]
    missing_params: List[str]
    question: str
    is_complete: bool


class BatchParseResponse(BaseModel):
    success: bool
    tasks: List[ParsedTaskOutput]
    original_text: str
    can_submit: bool


class BatchTaskResponse(BaseModel):
    success: bool
    parent_task_id: Optional[str] = None
    task_ids: List[str]
    total: int
    message: str


@router.post("/parse", response_model=BatchParseResponse)
async def parse_batch_tasks(request: BatchTaskRequest):
    """
    解析批量任务
    
    将自然语言或结构化输入解析为任务列表
    """
    text = None
    
    if request.input:
        text = request.input
    elif request.natural_language:
        text = request.natural_language.text
    elif request.input_type == "natural" and request.input:
        text = request.input
    
    if text:
        result = parse_intent_to_dict(text)
        
        parsed_tasks = []
        all_complete = True
        
        for task in result["tasks"]:
            task_type = TaskType(task["type"])
            params_result = extract_params_to_dict(task_type, task["span"])
            
            parsed_task = ParsedTaskOutput(
                type=task["type"],
                confidence=task["confidence"],
                span=task["span"],
                params=params_result["params"],
                missing_params=params_result["missing_params"],
                question=params_result["question"],
                is_complete=params_result["is_complete"]
            )
            
            if not parsed_task.is_complete:
                all_complete = False
            
            parsed_tasks.append(parsed_task)
        
        return BatchParseResponse(
            success=True,
            tasks=parsed_tasks,
            original_text=text,
            can_submit=all_complete
        )
    
    elif request.mode == TaskInputMode.STRUCTURED and request.structured_tasks:
        parsed_tasks = []
        all_complete = True
        
        for task_input in request.structured_tasks:
            task_type = TaskType(task_input.task_type)
            params_result = extract_params_to_dict(task_type, str(task_input.params))
            
            parsed_task = ParsedTaskOutput(
                type=task_input.task_type,
                confidence=1.0,
                span=str(task_input.params),
                params=task_input.params,
                missing_params=params_result["missing_params"],
                question=params_result["question"],
                is_complete=params_result["is_complete"]
            )
            
            if not parsed_task.is_complete:
                all_complete = False
            
            parsed_tasks.append(parsed_task)
        
        return BatchParseResponse(
            success=True,
            tasks=parsed_tasks,
            original_text="",
            can_submit=all_complete
        )
    
    raise HTTPException(status_code=400, detail="无效的请求参数")


@router.post("/batch", response_model=BatchTaskResponse)
async def create_batch_tasks(
    request: BatchTaskRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    创建批量任务
    
    接收解析后的任务列表，创建任务记录并返回任务ID
    """
    from backend.models.task import AgentTask
    import uuid
    
    if request.mode == TaskInputMode.NATURAL_LANGUAGE and request.natural_language:
        text = request.natural_language.text
        result = parse_intent_to_dict(text)
        
        task_ids = []
        parent_id = str(uuid.uuid4())
        
        for task in result["tasks"]:
            task_type = TaskType(task["type"])
            params_result = extract_params_to_dict(task_type, task["span"])
            
            if params_result["missing_params"] and not request.skip_invalid:
                continue
            
            task_id = str(uuid.uuid4())
            new_task = AgentTask(
                id=task_id,
                query=task["span"],
                style=task["type"],
                status="queued",
                progress=0,
                result={},
                parent_task_id=parent_id
            )
            
            db.add(new_task)
            task_ids.append(task_id)
        
        parent_task = AgentTask(
            id=parent_id,
            query=f"批量任务 ({len(task_ids)}个子任务)",
            style="batch",
            status="queued",
            progress=0,
            result={"child_task_ids": task_ids}
        )
        db.add(parent_task)
        
        await db.commit()
        
        return BatchTaskResponse(
            success=True,
            parent_task_id=parent_id,
            task_ids=task_ids,
            total=len(task_ids),
            message=f"成功创建 {len(task_ids)} 个任务"
        )
    
    elif request.mode == TaskInputMode.STRUCTURED and request.structured_tasks:
        task_ids = []
        parent_id = str(uuid.uuid4())
        
        for task_input in request.structured_tasks:
            task_id = str(uuid.uuid4())
            new_task = AgentTask(
                id=task_id,
                query=str(task_input.params),
                style=task_input.task_type,
                status="queued",
                progress=0,
                result={},
                parent_task_id=parent_id
            )
            
            db.add(new_task)
            task_ids.append(task_id)
        
        parent_task = AgentTask(
            id=parent_id,
            query=f"批量任务 ({len(task_ids)}个子任务)",
            style="batch",
            status="queued",
            progress=0,
            result={"child_task_ids": task_ids}
        )
        db.add(parent_task)
        
        await db.commit()
        
        return BatchTaskResponse(
            success=True,
            parent_task_id=parent_id,
            task_ids=task_ids,
            total=len(task_ids),
            message=f"成功创建 {len(task_ids)} 个任务"
        )
    
    raise HTTPException(status_code=400, detail="无效的请求参数")


@router.post("/batch/{parent_task_id}/cancel")
async def cancel_batch_tasks(
    parent_task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    取消批量任务
    
    取消父任务下的所有未完成子任务
    """
    from backend.models.task import AgentTask
    from sqlalchemy import text
    
    result = await db.execute(
        text("""
            UPDATE agent_tasks 
            SET status = 'cancelled', updated_at = NOW()
            WHERE parent_task_id = :parent_id 
            AND status IN ('queued', 'planning', 'reviewing', 'executing')
        """),
        {"parent_id": parent_task_id}
    )
    
    await db.execute(
        text("""
            UPDATE agent_tasks 
            SET status = 'cancelled', updated_at = NOW()
            WHERE id = :parent_id
        """),
        {"parent_id": parent_task_id}
    )
    
    await db.commit()
    
    return {"success": True, "cancelled_count": result.rowcount, "message": f"已取消 {result.rowcount} 个任务"}
