"""
实训模式相关Pydantic模型
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime


class TaskForkRequest(BaseModel):
    """复制任务请求"""
    overrides: Optional[Dict[str, Dict[str, Any]]] = Field(
        None,
        description="代理参数覆盖，格式：{agent_name: {param: value}}"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "overrides": {
                    "market_analyst": {
                        "system_prompt": "你是一位进取的市场分析师",
                        "temperature": 0.8
                    }
                }
            }
        }


class TaskForkResponse(BaseModel):
    """复制任务响应"""
    original_task_id: str = Field(..., description="原任务ID")
    forked_task_id: str = Field(..., description="复制的新任务ID")
    message: str = Field(..., description="操作消息")


class TemplateMarkRequest(BaseModel):
    """标记模板请求"""
    is_template: bool = Field(True, description="是否为模板")
    expected_results: Optional[Dict[str, Any]] = Field(
        None,
        description="期望结果（用于评分）"
    )


class ComparisonResult(BaseModel):
    """对比结果"""
    original_task_id: str = Field(..., description="原任务ID")
    forked_task_id: str = Field(..., description="复制任务ID")
    similarities: List[Dict[str, Any]] = Field(..., description="相同点列表")
    differences: List[Dict[str, Any]] = Field(..., description="不同点列表")
    metrics_changes: Dict[str, Any] = Field(..., description="指标变化")
    text_similarity: float = Field(..., description="文本相似度（0-1）")
    score: Optional[float] = Field(None, description="评分（0-100）")


class TemplateResponse(BaseModel):
    """模板响应"""
    task_id: str = Field(..., description="任务ID")
    query: str = Field(..., description="查询内容")
    style: str = Field(..., description="分析风格")
    created_at: str = Field(..., description="创建时间")
    created_by: str = Field(..., description="创建者")
    fork_count: int = Field(0, description="复制次数")
    expected_results: Optional[Dict[str, Any]] = Field(None, description="期望结果")


class AgentParameterConfig(BaseModel):
    """代理参数配置"""
    system_prompt: Optional[str] = Field(None, description="系统提示词")
    temperature: Optional[float] = Field(None, description="温度参数", ge=0.0, le=2.0)
    memory_weight: Optional[float] = Field(None, description="记忆权重", ge=0.0, le=1.0)
    risk_preference: Optional[float] = Field(None, description="风险偏好", ge=0.0, le=1.0)
    custom_params: Optional[Dict[str, Any]] = Field(None, description="自定义参数")
