from typing import Dict, Any, Optional
import asyncio
from app.ai_agents.scheduler import AgentScheduler
from app.api.v1.storage import task_store
from app.api.v1.schemas.task import TaskStatusEnum
from app.ai_agents.event_system import event_manager


class TaskManager:
    """Task manager for handling analysis tasks"""
    
    def __init__(self):
        """Initialize task manager"""
        self.scheduler = AgentScheduler()
    
    async def start_analysis(self, task_id: str, query: str, **kwargs) -> Dict[str, Any]:
        """Start analysis task with multi-agent workflow
        
        Args:
            task_id: Unique task ID
            query: User query
            **kwargs: Additional parameters
                - address: Property address
                - property_type: Property type
                - area: Property area
                - age: Property age
                - description: Additional description
                
        Returns:
            Dict with workflow execution result
        """
        try:
            # 更新任务状态为运行中
            task_store.update_task(task_id, status=TaskStatusEnum.RUNNING)
            
            # 执行多代理工作流
            result = await self.scheduler.execute_workflow(task_id, query)
            
            if result.get("success"):
                # 更新任务状态为成功
                task_store.update_task(
                    task_id,
                    status=TaskStatusEnum.SUCCESS,
                    progress=1.0,
                    result={
                        "query": query,
                        **kwargs,
                        "report": result.get("result", {})
                    }
                )
            else:
                # 更新任务状态为失败
                task_store.update_task(
                    task_id,
                    status=TaskStatusEnum.FAILED,
                    error=result.get("error", "Unknown error")
                )
            
            return result
            
        except Exception as e:
            # 更新任务状态为失败
            task_store.update_task(
                task_id,
                status=TaskStatusEnum.FAILED,
                error=str(e)
            )
            
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task status with agent information
        
        Args:
            task_id: Unique task ID
            
        Returns:
            Task status dict with agent information
        """
        task = task_store.get_task(task_id)
        if not task:
            return None
        
        # 获取调度器中的任务信息
        scheduler_task = self.scheduler.get_task_status(task_id)
        
        # 添加代理信息
        if scheduler_task:
            task["agents"] = scheduler_task.get("agents", {})
        
        return task
    
    def get_task_steps(self, task_id: str, group_by_agent: bool = False) -> Dict[str, Any]:
        """Get task steps with optional agent grouping
        
        Args:
            task_id: Unique task ID
            group_by_agent: Whether to group steps by agent
            
        Returns:
            Dict with task steps
        """
        # 获取基本任务信息
        task = task_store.get_task(task_id)
        if not task:
            return {"error": "Task not found"}
        
        # 获取节点状态
        nodes = task_store.get_nodes(task_id)
        
        if group_by_agent:
            # 按代理分组步骤
            steps_by_agent = {}
            
            # 获取调度器中的任务信息
            scheduler_task = self.scheduler.get_task_status(task_id)
            if scheduler_task:
                agents = scheduler_task.get("agents", {})
                for agent_type, agent_info in agents.items():
                    steps_by_agent[agent_type] = agent_info.get("steps", [])
            
            return {
                "task_id": task_id,
                "steps_by_agent": steps_by_agent
            }
        else:
            # 返回所有步骤
            return {
                "task_id": task_id,
                "steps": nodes
            }
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task
        
        Args:
            task_id: Unique task ID
            
        Returns:
            True if task was cancelled, False otherwise
        """
        # 取消调度器中的任务
        cancelled = self.scheduler.cancel_task(task_id)
        
        if cancelled:
            # 更新任务状态为取消
            task_store.update_task(
                task_id,
                status=TaskStatusEnum.CANCELLED
            )
        
        return cancelled


# Create global task manager instance
task_manager = TaskManager()
