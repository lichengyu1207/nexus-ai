"""
整合工作流测试API端点
提供测试和演示功能
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from app.workflow.integrated import integrated_workflow
from app.workflow.graph import get_workflow_mermaid


router = APIRouter()


class TestQueryRequest(BaseModel):
    """测试查询请求"""
    query: str = Field(..., description="用户查询", example="深圳南山区1000万学区房")
    style: str = Field("balanced", description="分析风格")


class TestQueryResponse(BaseModel):
    """测试查询响应"""
    query: str
    style: str
    subtasks: list
    workflow_state: dict
    execution_time: float
    status: str
    timestamp: str


@router.post("/test/integrated-workflow", response_model=TestQueryResponse)
async def test_integrated_workflow(request: TestQueryRequest):
    """
    测试整合工作流
    
    测试场景：
    1. 用户输入"深圳南山区1000万学区房"
    2. Supervisor分解为3个子任务
    3. LangGraph执行工作流
    4. 返回完整结果
    
    Args:
        request: 测试请求
        
    Returns:
        TestQueryResponse: 测试结果
    """
    try:
        result = await integrated_workflow.execute(
            query=request.query,
            style=request.style
        )
        
        return TestQueryResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test/workflow-visualization")
async def get_workflow_visualization():
    """
    获取工作流可视化（Mermaid图）
    
    Returns:
        dict: Mermaid图代码
    """
    return {
        "mermaid": get_workflow_mermaid(),
        "description": "工作流图：需求分析 -> 数据采集 -> 市场分析 -> 报告生成"
    }


@router.get("/test/execution-summary")
async def get_execution_summary():
    """
    获取执行摘要
    
    Returns:
        dict: 执行摘要统计
    """
    return integrated_workflow.get_execution_summary()


@router.post("/test/demo")
async def run_demo():
    """
    运行演示
    
    自动执行预设的测试用例
    
    Returns:
        dict: 演示结果
    """
    demo_queries = [
        "深圳南山区1000万学区房",
        "北京朝阳区投资房产分析",
        "上海浦东新区豪宅市场趋势"
    ]
    
    results = []
    
    for query in demo_queries:
        result = await integrated_workflow.execute(query=query, style="balanced")
        results.append({
            "query": result["query"],
            "status": result["status"],
            "execution_time": result["execution_time"]
        })
    
    return {
        "demo_results": results,
        "summary": integrated_workflow.get_execution_summary()
    }
