"""
主管智能体（SupervisorAgent）
负责解析用户意图、分解任务、调度专业智能体、汇总结果
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import uuid
from datetime import datetime
from app.ai_agents.base_agent import BaseAgent


class SubTaskType(str, Enum):
    """子任务类型枚举"""
    REQUIREMENT = "requirement"
    DATA_COLLECTION = "data_collection"
    DATA_CLEANING = "data_cleaning"
    DATA_VERIFICATION = "data_verification"
    ANALYSIS = "analysis"
    REPORT_GENERATION = "report_generation"


class SubTaskStatus(str, Enum):
    """子任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class SubTask:
    """子任务定义"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: SubTaskType = SubTaskType.REQUIREMENT
    target_agent: str = ""
    input_data: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    status: SubTaskStatus = SubTaskStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "type": self.type.value if isinstance(self.type, SubTaskType) else self.type,
            "target_agent": self.target_agent,
            "input_data": self.input_data,
            "depends_on": self.depends_on,
            "status": self.status.value if isinstance(self.status, SubTaskStatus) else self.status,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at
        }


class SupervisorAgent(BaseAgent):
    """
    主管智能体
    负责任务分解、调度和结果汇总
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "supervisor"
        self.description = "主管智能体，负责解析用户意图、分解任务、调度专业智能体、汇总结果"
        self.sub_agents: Dict[str, BaseAgent] = {}
    
    def register_sub_agent(self, agent: BaseAgent) -> None:
        """
        注册子代理
        
        Args:
            agent: 子代理实例
        """
        self.sub_agents[agent.name] = agent
        self.publish_progress_event(0.1, f"注册子代理: {agent.name}")
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行主管任务
        
        Args:
            task: 任务数据
            
        Returns:
            Dict: 执行结果
        """
        query = task.get("query", "")
        style = task.get("style", "balanced")
        
        # 1. 解析用户需求
        self.publish_progress_event(0.1, "正在解析用户需求...")
        subtasks = await self.decompose_task(query, style)
        
        # 2. 执行子任务
        self.publish_progress_event(0.3, "正在执行子任务...")
        sub_results = await self.execute_subtasks(subtasks)
        
        # 3. 汇总结果
        self.publish_progress_event(0.8, "正在汇总结果...")
        final_result = await self.synthesize_results(sub_results)
        
        return final_result
    
    async def decompose_task(self, query: str, style: str = "balanced") -> List[SubTask]:
        """
        将用户需求拆解为子任务
        
        Args:
            query: 用户查询
            style: 分析风格
            
        Returns:
            List[SubTask]: 子任务列表
        """
        subtasks = []
        
        # 任务1：需求分析
        requirement_task = SubTask(
            type=SubTaskType.REQUIREMENT,
            target_agent="requirement_analyzer",
            input_data={"query": query, "style": style},
            depends_on=[]
        )
        subtasks.append(requirement_task)
        
        # 任务2：数据采集（依赖需求分析）
        data_collection_task = SubTask(
            type=SubTaskType.DATA_COLLECTION,
            target_agent="data_collector",
            input_data={"query": query},
            depends_on=[requirement_task.id]
        )
        subtasks.append(data_collection_task)
        
        # 任务3：数据清洗（依赖数据采集）
        data_cleaning_task = SubTask(
            type=SubTaskType.DATA_CLEANING,
            target_agent="data_cleaner",
            input_data={},
            depends_on=[data_collection_task.id]
        )
        subtasks.append(data_cleaning_task)
        
        # 任务4：数据验证（依赖数据清洗）
        data_verification_task = SubTask(
            type=SubTaskType.DATA_VERIFICATION,
            target_agent="data_verifier",
            input_data={},
            depends_on=[data_cleaning_task.id]
        )
        subtasks.append(data_verification_task)
        
        # 任务5：市场分析（依赖数据验证）
        analysis_task = SubTask(
            type=SubTaskType.ANALYSIS,
            target_agent="market_analyst",
            input_data={"style": style},
            depends_on=[data_verification_task.id]
        )
        subtasks.append(analysis_task)
        
        # 任务6：报告生成（依赖市场分析）
        report_task = SubTask(
            type=SubTaskType.REPORT_GENERATION,
            target_agent="report_generator",
            input_data={},
            depends_on=[analysis_task.id]
        )
        subtasks.append(report_task)
        
        self.publish_progress_event(0.2, f"已分解为 {len(subtasks)} 个子任务")
        
        return subtasks
    
    async def assign_task(self, subtask: SubTask) -> str:
        """
        分配子任务到对应代理
        
        Args:
            subtask: 子任务
            
        Returns:
            str: 分配结果
        """
        agent_name = subtask.target_agent
        
        if agent_name not in self.sub_agents:
            return f"Agent {agent_name} not found"
        
        agent = self.sub_agents[agent_name]
        
        # 执行任务
        try:
            result = await agent.execute(subtask.input_data)
            subtask.result = result
            subtask.status = SubTaskStatus.COMPLETED
            subtask.completed_at = datetime.utcnow().isoformat()
            
            return f"Task {subtask.id} assigned to {agent_name} successfully"
        except Exception as e:
            subtask.status = SubTaskStatus.FAILED
            subtask.error = str(e)
            return f"Task {subtask.id} failed: {str(e)}"
    
    async def execute_subtasks(self, subtasks: List[SubTask]) -> Dict[str, Any]:
        """
        执行子任务列表（根据依赖关系）
        
        Args:
            subtasks: 子任务列表
            
        Returns:
            Dict: 执行结果
        """
        results = {}
        completed_tasks = set()
        
        # 持续执行直到所有任务完成
        while len(completed_tasks) < len(subtasks):
            for subtask in subtasks:
                # 跳过已完成的任务
                if subtask.id in completed_tasks:
                    continue
                
                # 检查依赖是否满足
                dependencies_met = all(
                    dep_id in completed_tasks
                    for dep_id in subtask.depends_on
                )
                
                if not dependencies_met:
                    continue
                
                # 执行任务
                subtask.status = SubTaskStatus.RUNNING
                subtask.started_at = datetime.utcnow().isoformat()
                
                await self.assign_task(subtask)
                
                completed_tasks.add(subtask.id)
                results[subtask.id] = subtask.to_dict()
                
                # 更新进度
                progress = 0.3 + (len(completed_tasks) / len(subtasks)) * 0.5
                self.publish_progress_event(progress, f"完成子任务: {subtask.type.value}")
        
        return results
    
    async def synthesize_results(self, sub_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        汇总各代理结果，生成综合报告
        
        Args:
            sub_results: 各子任务的结果
            
        Returns:
            Dict: 综合报告
        """
        # 提取关键结果
        requirement_result = None
        analysis_result = None
        report_result = None
        
        for task_id, task_data in sub_results.items():
            task_type = task_data.get("type")
            result = task_data.get("result", {})
            
            if task_type == SubTaskType.REQUIREMENT.value:
                requirement_result = result
            elif task_type == SubTaskType.ANALYSIS.value:
                analysis_result = result
            elif task_type == SubTaskType.REPORT_GENERATION.value:
                report_result = result
        
        # 生成综合报告
        final_report = {
            "task_id": self.task_id,
            "status": "SUCCESS",
            "requirement_analysis": requirement_result,
            "market_analysis": analysis_result,
            "report": report_result,
            "summary": {
                "total_subtasks": len(sub_results),
                "completed_subtasks": sum(
                    1 for t in sub_results.values()
                    if t.get("status") == SubTaskStatus.COMPLETED.value
                ),
                "failed_subtasks": sum(
                    1 for t in sub_results.values()
                    if t.get("status") == SubTaskStatus.FAILED.value
                )
            },
            "created_at": datetime.utcnow().isoformat()
        }
        
        self.publish_progress_event(1.0, "任务完成，已生成综合报告")
        
        return final_report
    
    def get_task_tree(self, subtasks: List[SubTask]) -> Dict[str, Any]:
        """
        获取任务分解树
        
        Args:
            subtasks: 子任务列表
            
        Returns:
            Dict: 任务树结构
        """
        tree = {
            "name": "主管智能体",
            "type": "supervisor",
            "children": []
        }
        
        # 构建任务树
        task_map = {task.id: task for task in subtasks}
        
        for task in subtasks:
            if not task.depends_on:
                # 根任务
                tree["children"].append({
                    "id": task.id,
                    "name": task.type.value,
                    "agent": task.target_agent,
                    "status": task.status.value,
                    "children": self._build_task_children(task.id, task_map)
                })
        
        return tree
    
    def _build_task_children(
        self,
        parent_id: str,
        task_map: Dict[str, SubTask]
    ) -> List[Dict[str, Any]]:
        """
        构建任务子节点
        
        Args:
            parent_id: 父任务ID
            task_map: 任务映射
            
        Returns:
            List: 子节点列表
        """
        children = []
        
        for task in task_map.values():
            if parent_id in task.depends_on:
                children.append({
                    "id": task.id,
                    "name": task.type.value,
                    "agent": task.target_agent,
                    "status": task.status.value,
                    "children": self._build_task_children(task.id, task_map)
                })
        
        return children
