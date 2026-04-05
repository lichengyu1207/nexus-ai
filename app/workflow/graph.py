"""
LangGraph工作流定义
实现图式化工作流编排
"""
from typing import Literal
from langgraph.graph import StateGraph, END
from app.workflow.state import AgentState
from app.workflow.nodes import (
    requirement_node,
    collector_node,
    analyst_node,
    report_node,
    should_collect_more
)
import logging

logger = logging.getLogger(__name__)


def create_workflow() -> StateGraph:
    """
    创建工作流图
    
    Returns:
        StateGraph: 工作流图
    """
    # 创建工作流
    workflow = StateGraph(AgentState)
    
    # 添加节点
    workflow.add_node("requirement", requirement_node)
    workflow.add_node("collector", collector_node)
    workflow.add_node("analyst", analyst_node)
    workflow.add_node("report", report_node)
    
    # 添加边
    workflow.add_edge("requirement", "collector")
    
    # 添加条件边：判断是否需要补充数据采集
    workflow.add_conditional_edges(
        "collector",
        should_collect_more,
        {
            "continue": "collector",  # 重新采集
            "skip": "analyst"         # 跳过，继续分析
        }
    )
    
    workflow.add_edge("analyst", "report")
    workflow.add_edge("report", END)
    
    # 设置入口点
    workflow.set_entry_point("requirement")
    
    logger.info("Workflow graph created successfully")
    
    return workflow


def get_workflow_mermaid() -> str:
    """
    获取工作流的Mermaid图表示
    
    Returns:
        str: Mermaid图代码
    """
    return """
graph TD
    A[开始] --> B[需求分析]
    B --> C[数据采集]
    C --> D{数据置信度>=0.7?}
    D -->|否| C
    D -->|是| E[市场分析]
    E --> F[报告生成]
    F --> G[结束]
    
    style A fill:#e1f5e1
    style G fill:#e1f5e1
    style B fill:#e3f2fd
    style C fill:#fff3e0
    style E fill:#f3e5f5
    style F fill:#fce4ec
    style D fill:#fff9c4
"""


# 创建全局工作流实例
workflow_graph = create_workflow()
