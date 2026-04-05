"""任务编排引擎模块"""

from app.task_engine.dag_schema import DAG, DAGNode, Edge
from app.task_engine.dag_parser import parse_workflow_from_intent, generate_simple_collect_analyze_dag
from app.task_engine.dag_executor import DAGExecutor
from app.task_engine.llm_planner import LLMPlanner, create_llm_planner

__all__ = [
    "DAG",
    "DAGNode",
    "Edge",
    "parse_workflow_from_intent",
    "generate_simple_collect_analyze_dag",
    "DAGExecutor",
    "LLMPlanner",
    "create_llm_planner"
]

__version__ = "1.0.0"

"""
任务编排引擎模块，用于定义、解析和执行基于DAG的工作流

主要组件：
- dag_schema: 定义DAG相关的数据模型
- dag_parser: 从用户意图解析工作流，生成DAG
- dag_executor: 执行DAG工作流，协调智能体执行

使用示例：
    from app.task_engine import DAGExecutor, generate_simple_collect_analyze_dag
    
    async def run_workflow():
        dag = generate_simple_collect_analyze_dag()
        executor = DAGExecutor()
        result = await executor.execute(dag, {})
        return result
"""
