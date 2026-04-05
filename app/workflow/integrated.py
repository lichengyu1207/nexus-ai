"""
整合工作流 - Supervisor + A2A + LangGraph
结合三种协同模式的优势
"""
from typing import Dict, Any, List
from app.ai_agents.supervisor import SupervisorAgent, SubTask, SubTaskType
from app.workflow.graph import workflow_graph
from app.workflow.state import AgentState
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class IntegratedWorkflow:
    """
    整合工作流
    结合Supervisor、A2A和LangGraph三种协同模式
    """
    
    def __init__(self):
        """初始化整合工作流"""
        self.supervisor = SupervisorAgent()
        self.workflow = workflow_graph
        self.execution_history = []
    
    async def execute(self, query: str, style: str = "balanced") -> Dict[str, Any]:
        """
        执行整合工作流
        
        Args:
            query: 用户查询
            style: 分析风格
            
        Returns:
            Dict: 执行结果
        """
        start_time = datetime.utcnow()
        
        logger.info(f"Starting integrated workflow for query: {query}")
        
        # 阶段1：Supervisor分解任务
        logger.info("Phase 1: Supervisor decomposing tasks...")
        subtasks = await self.supervisor.decompose_task(query, style)
        
        # 阶段2：使用LangGraph执行工作流
        logger.info("Phase 2: Executing LangGraph workflow...")
        initial_state = {
            "query": query,
            "requirement": {},
            "collected_data": {},
            "analysis_result": {},
            "final_report": {},
            "errors": [],
            "current_step": "initialized"
        }
        
        # 编译并执行工作流
        app = self.workflow.compile()
        final_state = await app.ainvoke(initial_state)
        
        # 阶段3：汇总结果
        logger.info("Phase 3: Synthesizing results...")
        result = {
            "query": query,
            "style": style,
            "subtasks": [task.to_dict() for task in subtasks],
            "workflow_state": final_state,
            "execution_time": (datetime.utcnow() - start_time).total_seconds(),
            "status": "SUCCESS" if not final_state.get("errors") else "PARTIAL_SUCCESS",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # 记录执行历史
        self.execution_history.append(result)
        
        logger.info(f"Integrated workflow completed in {result['execution_time']:.2f}s")
        
        return result
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """
        获取执行摘要
        
        Returns:
            Dict: 执行摘要
        """
        if not self.execution_history:
            return {"total_executions": 0}
        
        total = len(self.execution_history)
        successful = sum(1 for e in self.execution_history if e["status"] == "SUCCESS")
        avg_time = sum(e["execution_time"] for e in self.execution_history) / total
        
        return {
            "total_executions": total,
            "successful_executions": successful,
            "success_rate": (successful / total) * 100,
            "average_execution_time": avg_time,
            "last_execution": self.execution_history[-1] if self.execution_history else None
        }


# 全局整合工作流实例
integrated_workflow = IntegratedWorkflow()
