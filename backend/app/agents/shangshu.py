import asyncio
import networkx as nx
from datetime import datetime
from typing import Dict, Any, List
from app.models.task import Task, SubTask, TaskStatus, SubTaskStatus
from sqlalchemy.orm import Session

class ShangshuAgent:
    """尚书省智能体 - 负责DAG调度"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def schedule_task(self, task: Task) -> None:
        """
        调度任务执行
        
        Args:
            task: 任务对象
        """
        # 更新任务状态为运行中
        task.status = TaskStatus.RUNNING
        self.db.commit()
        
        # 构建DAG
        dag = self._build_dag(task.spec)
        
        # 拓扑排序，确定执行顺序
        try:
            execution_order = list(nx.topological_sort(dag))
        except nx.NetworkXUnfeasible:
            task.status = TaskStatus.FAILED
            self.db.commit()
            raise Exception("任务包含循环依赖")
        
        # 执行子任务
        subtask_results = {}
        
        # 按拓扑顺序执行
        for subtask_id in execution_order:
            # 查找子任务
            subtask = self.db.query(SubTask).filter(SubTask.id == subtask_id).first()
            if not subtask:
                continue
            
            # 检查依赖是否完成
            dependencies = subtask.dependencies
            all_deps_completed = all(
                self.db.query(SubTask).filter(
                    SubTask.id == dep_id,
                    SubTask.status == SubTaskStatus.COMPLETED
                ).first() is not None
                for dep_id in dependencies
            )
            
            if not all_deps_completed:
                continue
            
            # 执行子任务
            await self._execute_subtask(subtask)
            
            # 检查任务是否失败
            if subtask.status == SubTaskStatus.FAILED:
                task.status = TaskStatus.FAILED
                self.db.commit()
                return
        
        # 检查所有子任务是否完成
        all_completed = all(
            subtask.status == SubTaskStatus.COMPLETED
            for subtask in task.subtasks
        )
        
        if all_completed:
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            # 计算总耗时
            if task.subtasks:
                start_times = [st.start_time for st in task.subtasks if st.start_time]
                end_times = [st.end_time for st in task.subtasks if st.end_time]
                if start_times and end_times:
                    total_duration = int((max(end_times) - min(start_times)).total_seconds())
                    task.total_duration = total_duration
        else:
            task.status = TaskStatus.FAILED
        
        self.db.commit()
    
    def _build_dag(self, spec: Dict[str, Any]) -> nx.DiGraph:
        """
        构建DAG图
        
        Args:
            spec: 任务规格
            
        Returns:
            DAG图
        """
        dag = nx.DiGraph()
        
        # 添加节点
        for subtask in spec.get("subtasks", []):
            dag.add_node(subtask["id"])
        
        # 添加边（依赖关系）
        for subtask in spec.get("subtasks", []):
            for dep_id in subtask.get("dependencies", []):
                dag.add_edge(dep_id, subtask["id"])
        
        return dag
    
    async def _execute_subtask(self, subtask: SubTask) -> None:
        """
        执行子任务
        
        Args:
            subtask: 子任务对象
        """
        # 更新子任务状态为运行中
        subtask.status = SubTaskStatus.RUNNING
        subtask.start_time = datetime.utcnow()
        self.db.commit()
        
        try:
            # 模拟执行，实际项目中应该调用对应的智能体
            await asyncio.sleep(2)  # 模拟执行时间
            
            # 更新子任务状态为完成
            subtask.status = SubTaskStatus.COMPLETED
            subtask.result = {"message": "执行成功"}
            subtask.end_time = datetime.utcnow()
            subtask.duration = int((subtask.end_time - subtask.start_time).total_seconds())
        except Exception as e:
            # 更新子任务状态为失败
            subtask.status = SubTaskStatus.FAILED
            subtask.error = str(e)
            subtask.end_time = datetime.utcnow()
            if subtask.start_time:
                subtask.duration = int((subtask.end_time - subtask.start_time).total_seconds())
        
        self.db.commit()
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务状态信息
        """
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return {"error": "任务不存在"}
        
        subtasks = self.db.query(SubTask).filter(SubTask.task_id == task_id).all()
        
        return {
            "task_id": task.id,
            "status": task.status.value,
            "subtasks": [
                {
                    "id": st.id,
                    "status": st.status.value,
                    "start_time": st.start_time.isoformat() if st.start_time else None,
                    "end_time": st.end_time.isoformat() if st.end_time else None,
                    "duration": st.duration,
                    "error": st.error
                }
                for st in subtasks
            ]
        }
