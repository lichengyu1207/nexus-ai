"""
任务依赖解析与并行调度模块
使用DAG（有向无环图）表示任务依赖关系
支持拓扑排序和并行调度
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any
import asyncio
from collections import defaultdict, deque
import logging

logger = logging.getLogger(__name__)


class TaskPriority(int, Enum):
    """任务优先级"""
    LOW = 1
    NORMAL = 5
    HIGH = 10
    URGENT = 20


class DependencyType(str, Enum):
    """依赖类型"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"


@dataclass
class TaskNode:
    """任务节点"""
    id: str
    task_type: str
    params: Dict[str, Any]
    priority: TaskPriority = TaskPriority.NORMAL
    dependencies: List[str] = field(default_factory=list)
    dependency_type: DependencyType = DependencyType.PARALLEL
    estimated_duration: int = 0
    status: str = "pending"
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class TaskEdge:
    """任务边（依赖关系）"""
    from_task: str
    to_task: str
    dependency_type: DependencyType = DependencyType.SEQUENTIAL
    condition: Optional[str] = None


@dataclass
class DAGResult:
    """DAG分析结果"""
    nodes: List[str]
    edges: List[Tuple[str, str]]
    execution_order: List[List[str]]
    parallel_groups: List[List[str]]
    has_cycle: bool
    cycle_nodes: List[str]


class TaskDAG:
    """任务有向无环图"""

    def __init__(self):
        self.nodes: Dict[str, TaskNode] = {}
        self.edges: Dict[str, List[TaskEdge]] = defaultdict(list)
        self.reverse_edges: Dict[str, List[TaskEdge]] = defaultdict(list)

    def add_node(self, node: TaskNode) -> None:
        """添加任务节点"""
        self.nodes[node.id] = node
        if node.id not in self.edges:
            self.edges[node.id] = []
        if node.id not in self.reverse_edges:
            self.reverse_edges[node.id] = []

    def add_edge(self, edge: TaskEdge) -> None:
        """添加依赖边"""
        if edge.from_task not in self.nodes:
            raise ValueError(f"源任务 {edge.from_task} 不存在")
        if edge.to_task not in self.nodes:
            raise ValueError(f"目标任务 {edge.to_task} 不存在")
        
        self.edges[edge.from_task].append(edge)
        self.reverse_edges[edge.to_task].append(edge)
        self.nodes[edge.to_task].dependencies.append(edge.from_task)

    def detect_cycle(self) -> Tuple[bool, List[str]]:
        """检测环"""
        WHITE, GRAY, BLACK = 0, 1, 2
        color = {node_id: WHITE for node_id in self.nodes}
        cycle_nodes: List[str] = []

        def dfs(node_id: str, path: List[str]) -> bool:
            color[node_id] = GRAY
            path.append(node_id)
            
            for edge in self.edges[node_id]:
                if color[edge.to_task] == GRAY:
                    cycle_start = path.index(edge.to_task)
                    cycle_nodes.extend(path[cycle_start:])
                    return True
                if color[edge.to_task] == WHITE:
                    if dfs(edge.to_task, path):
                        return True
            
            path.pop()
            color[node_id] = BLACK
            return False

        for node_id in self.nodes:
            if color[node_id] == WHITE:
                if dfs(node_id, []):
                    return True, cycle_nodes
        
        return False, []

    def topological_sort(self) -> List[str]:
        """拓扑排序"""
        in_degree = {node_id: 0 for node_id in self.nodes}
        
        for node_id in self.nodes:
            for edge in self.edges[node_id]:
                in_degree[edge.to_task] += 1
        
        queue = deque([node_id for node_id, degree in in_degree.items() if degree == 0])
        result = []
        
        while queue:
            node_id = queue.popleft()
            result.append(node_id)
            
            for edge in self.edges[node_id]:
                in_degree[edge.to_task] -= 1
                if in_degree[edge.to_task] == 0:
                    queue.append(edge.to_task)
        
        return result

    def get_execution_levels(self) -> List[List[str]]:
        """获取执行层级（同一层级的任务可以并行执行）"""
        in_degree = {node_id: 0 for node_id in self.nodes}
        
        for node_id in self.nodes:
            for edge in self.edges[node_id]:
                in_degree[edge.to_task] += 1
        
        levels: List[List[str]] = []
        current_level = [node_id for node_id, degree in in_degree.items() if degree == 0]
        
        while current_level:
            levels.append(sorted(current_level, key=lambda x: self.nodes[x].priority, reverse=True))
            
            next_level = []
            for node_id in current_level:
                for edge in self.edges[node_id]:
                    in_degree[edge.to_task] -= 1
                    if in_degree[edge.to_task] == 0:
                        next_level.append(edge.to_task)
            
            current_level = next_level
        
        return levels

    def get_parallel_groups(self) -> List[List[str]]:
        """获取可并行执行的任务组"""
        return self.get_execution_levels()

    def analyze(self) -> DAGResult:
        """分析DAG"""
        has_cycle, cycle_nodes = self.detect_cycle()
        
        if has_cycle:
            return DAGResult(
                nodes=list(self.nodes.keys()),
                edges=[(e.from_task, e.to_task) for edges in self.edges.values() for e in edges],
                execution_order=[],
                parallel_groups=[],
                has_cycle=True,
                cycle_nodes=cycle_nodes
            )
        
        execution_order = self.topological_sort()
        parallel_groups = self.get_parallel_groups()
        
        return DAGResult(
            nodes=list(self.nodes.keys()),
            edges=[(e.from_task, e.to_task) for edges in self.edges.values() for e in edges],
            execution_order=[execution_order],
            parallel_groups=parallel_groups,
            has_cycle=False,
            cycle_nodes=[]
        )


def build_task_dag(tasks: List[Dict[str, Any]]) -> TaskDAG:
    """
    根据任务列表构建DAG
    
    Args:
        tasks: 任务列表，每个任务包含 id, type, params, dependencies 等字段
    
    Returns:
        TaskDAG: 构建好的DAG
    """
    dag = TaskDAG()
    
    for task in tasks:
        node = TaskNode(
            id=task["id"],
            task_type=task.get("type", "unknown"),
            params=task.get("params", {}),
            priority=TaskPriority(task.get("priority", 5)),
            dependencies=task.get("dependencies", []),
            estimated_duration=task.get("estimated_duration", 0)
        )
        dag.add_node(node)
    
    for task in tasks:
        for dep_id in task.get("dependencies", []):
            if dep_id in dag.nodes:
                edge = TaskEdge(
                    from_task=dep_id,
                    to_task=task["id"],
                    dependency_type=DependencyType.SEQUENTIAL
                )
                dag.add_edge(edge)
    
    return dag


def infer_dependencies(tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    自动推断任务依赖关系
    
    规则：
    1. 数据采集任务 -> 房产分析任务
    2. 房产分析任务 -> 报告生成任务
    3. 同类型任务默认并行
    """
    TYPE_DEPENDENCIES = {
        "data_collection": ["property_analysis"],
        "property_analysis": ["report_generation"],
        "policy_query": ["report_generation"],
        "mingpan": [],
        "emotion": [],
        "report_generation": [],
    }
    
    task_by_type: Dict[str, List[str]] = defaultdict(list)
    for task in tasks:
        task_type = task.get("type", "unknown")
        task_by_type[task_type].append(task["id"])
    
    enhanced_tasks = []
    for task in tasks:
        task_type = task.get("type", "unknown")
        dependencies = list(task.get("dependencies", []))
        
        for source_type, target_types in TYPE_DEPENDENCIES.items():
            if task_type in target_types:
                for source_id in task_by_type.get(source_type, []):
                    if source_id not in dependencies:
                        dependencies.append(source_id)
        
        enhanced_task = {**task, "dependencies": dependencies}
        enhanced_tasks.append(enhanced_task)
    
    return enhanced_tasks


class BatchTaskScheduler:
    """批量任务调度器"""

    def __init__(self, max_concurrent: int = 5):
        self.max_concurrent = max_concurrent
        self.dag: Optional[TaskDAG] = None
        self.task_status: Dict[str, str] = {}
        self.task_results: Dict[str, Any] = {}
        self._callbacks: Dict[str, List[callable]] = defaultdict(list)

    def on_task_complete(self, task_id: str, callback: callable) -> None:
        """注册任务完成回调"""
        self._callbacks[task_id].append(callback)

    async def _execute_task(self, task_node: TaskNode, executor: callable) -> Any:
        """执行单个任务"""
        self.task_status[task_node.id] = "running"
        
        try:
            result = await executor(task_node)
            self.task_status[task_node.id] = "completed"
            self.task_results[task_node.id] = result
            
            for callback in self._callbacks.get(task_node.id, []):
                await callback(task_node.id, result)
            
            return result
        except Exception as e:
            self.task_status[task_node.id] = "failed"
            self.task_results[task_node.id] = {"error": str(e)}
            logger.error(f"Task {task_node.id} failed: {e}")
            raise

    async def schedule(self, tasks: List[Dict[str, Any]], executor: callable) -> Dict[str, Any]:
        """
        调度批量任务
        
        Args:
            tasks: 任务列表
            executor: 任务执行函数
        
        Returns:
            执行结果
        """
        enhanced_tasks = infer_dependencies(tasks)
        self.dag = build_task_dag(enhanced_tasks)
        
        analysis = self.dag.analyze()
        
        if analysis.has_cycle:
            raise ValueError(f"检测到循环依赖: {analysis.cycle_nodes}")
        
        for node_id in self.dag.nodes:
            self.task_status[node_id] = "pending"
        
        results = {}
        
        for level in analysis.parallel_groups:
            running_tasks = []
            
            for task_id in level:
                if self.task_status[task_id] == "pending":
                    task_node = self.dag.nodes[task_id]
                    
                    deps_complete = all(
                        self.task_status.get(dep) == "completed"
                        for dep in task_node.dependencies
                    )
                    
                    if deps_complete:
                        running_tasks.append(self._execute_task(task_node, executor))
                    
                    if len(running_tasks) >= self.max_concurrent:
                        completed = await asyncio.gather(*running_tasks, return_exceptions=True)
                        for i, result in enumerate(completed):
                            if isinstance(result, Exception):
                                logger.error(f"Task execution error: {result}")
                        running_tasks = []
            
            if running_tasks:
                completed = await asyncio.gather(*running_tasks, return_exceptions=True)
                for result in completed:
                    if isinstance(result, Exception):
                        logger.error(f"Task execution error: {result}")
        
        return {
            "status": "completed",
            "task_status": self.task_status,
            "results": self.task_results,
            "execution_order": [level for level in analysis.parallel_groups]
        }

    def get_progress(self) -> Dict[str, Any]:
        """获取执行进度"""
        if not self.task_status:
            return {"total": 0, "completed": 0, "failed": 0, "running": 0, "pending": 0, "percent": 0}
        
        total = len(self.task_status)
        completed = sum(1 for s in self.task_status.values() if s == "completed")
        failed = sum(1 for s in self.task_status.values() if s == "failed")
        running = sum(1 for s in self.task_status.values() if s == "running")
        pending = sum(1 for s in self.task_status.values() if s == "pending")
        
        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "running": running,
            "pending": pending,
            "percent": round((completed / total) * 100, 1) if total > 0 else 0
        }


def get_task_dag_info(dag: TaskDAG) -> Dict[str, Any]:
    """获取DAG信息（用于可视化）"""
    analysis = dag.analyze()
    
    nodes_info = []
    for node_id, node in dag.nodes.items():
        nodes_info.append({
            "id": node_id,
            "type": node.task_type,
            "priority": node.priority.value,
            "status": node.status,
            "dependencies": node.dependencies
        })
    
    edges_info = []
    for from_id, edges in dag.edges.items():
        for edge in edges:
            edges_info.append({
                "from": edge.from_task,
                "to": edge.to_task,
                "type": edge.dependency_type.value
            })
    
    return {
        "nodes": nodes_info,
        "edges": edges_info,
        "execution_levels": analysis.parallel_groups,
        "has_cycle": analysis.has_cycle,
        "cycle_nodes": analysis.cycle_nodes
    }
