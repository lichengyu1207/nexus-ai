"""
任务图模块
实现DAG任务分解、依赖管理和执行调度
"""
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Set
from enum import Enum
import json


class SubtaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    SKIPPED = "skipped"
    WAITING_FOR_USER = "waiting_for_user"


@dataclass
class TaskNode:
    id: str
    agent_name: str
    input_data: Dict[str, Any]
    depends_on: List[str] = field(default_factory=list)
    critical: bool = True
    max_retries: int = 3
    timeout_seconds: int = 60
    status: SubtaskStatus = SubtaskStatus.PENDING
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "agent_name": self.agent_name,
            "input_data": self.input_data,
            "depends_on": self.depends_on,
            "critical": self.critical,
            "max_retries": self.max_retries,
            "timeout_seconds": self.timeout_seconds,
            "status": self.status.value if isinstance(self.status, SubtaskStatus) else self.status,
            "output_data": self.output_data,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "started_at": self.started_at,
            "completed_at": self.completed_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskNode":
        status = data.get("status", "pending")
        if isinstance(status, str):
            status = SubtaskStatus(status)
        return cls(
            id=data["id"],
            agent_name=data["agent_name"],
            input_data=data.get("input_data", {}),
            depends_on=data.get("depends_on", []),
            critical=data.get("critical", True),
            max_retries=data.get("max_retries", 3),
            timeout_seconds=data.get("timeout_seconds", 60),
            status=status,
            output_data=data.get("output_data"),
            error_message=data.get("error_message"),
            retry_count=data.get("retry_count", 0),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at")
        )


class TaskGraph:
    """
    任务图类
    管理DAG结构的任务依赖关系
    """
    
    def __init__(self):
        self.nodes: Dict[str, TaskNode] = {}
        self.edges: Dict[str, List[str]] = {}
    
    def add_node(self, node: TaskNode) -> None:
        self.nodes[node.id] = node
        for dep in node.depends_on:
            if dep not in self.edges:
                self.edges[dep] = []
            self.edges[dep].append(node.id)
    
    def get_node(self, node_id: str) -> Optional[TaskNode]:
        return self.nodes.get(node_id)
    
    def update_node_status(self, node_id: str, status: SubtaskStatus) -> None:
        if node_id in self.nodes:
            self.nodes[node_id].status = status
    
    def get_all_nodes(self) -> List[TaskNode]:
        """获取所有节点"""
        return list(self.nodes.values())
    
    def get_dependencies(self, node_id: str) -> List[str]:
        """获取指定节点的所有依赖"""
        if node_id in self.nodes:
            return self.nodes[node_id].depends_on
        return []
    
    def has_cycle(self) -> bool:
        """检查图中是否存在环"""
        visited = set()
        rec_stack = set()
        
        def dfs(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)
            
            for neighbor in self.edges.get(node_id, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node_id)
            return False
        
        for node_id in self.nodes:
            if node_id not in visited:
                if dfs(node_id):
                    return True
        
        return False
    
    def validate(self) -> bool:
        """验证任务图的有效性"""
        # 检查所有依赖是否存在
        for node in self.nodes.values():
            for dep in node.depends_on:
                if dep not in self.nodes:
                    return False
        
        # 检查是否存在环
        if self.has_cycle():
            return False
        
        return True
    
    def get_ready_nodes(self, completed_nodes: Set[str], failed_nodes: Set[str] = None) -> List[TaskNode]:
        """
        获取所有就绪的节点（依赖已完成且自身未完成）
        """
        if failed_nodes is None:
            failed_nodes = set()
        
        ready = []
        for node_id, node in self.nodes.items():
            if node_id in completed_nodes:
                continue
            if node_id in failed_nodes:
                continue
            if node.status in [SubtaskStatus.RUNNING, SubtaskStatus.RETRYING]:
                continue
            
            all_deps_completed = all(
                dep in completed_nodes for dep in node.depends_on
            )
            
            any_dep_failed = any(
                dep in failed_nodes for dep in node.depends_on
            )
            
            if any_dep_failed and node.critical:
                continue
            
            if all_deps_completed:
                ready.append(node)
        
        return ready
    
    def get_dependents(self, node_id: str) -> List[str]:
        """
        获取依赖于指定节点的所有节点
        """
        return self.edges.get(node_id, [])
    
    def is_completed(self) -> bool:
        """
        检查所有节点是否已完成
        """
        return all(
            node.status in [SubtaskStatus.COMPLETED, SubtaskStatus.SKIPPED]
            for node in self.nodes.values()
        )
    
    def has_failed_critical(self) -> bool:
        """
        检查是否有失败的关键节点
        """
        return any(
            node.status == SubtaskStatus.FAILED and node.critical
            for node in self.nodes.values()
        )
    
    def get_execution_order(self) -> List[List[str]]:
        """
        获取分层执行顺序（拓扑排序分层）
        """
        layers = []
        completed: Set[str] = set()
        failed: Set[str] = set()
        
        while len(completed) < len(self.nodes):
            ready = self.get_ready_nodes(completed, failed)
            if not ready:
                remaining = set(self.nodes.keys()) - completed - failed
                if remaining:
                    failed.update(remaining)
                break
            
            layer = [node.id for node in ready]
            layers.append(layer)
            completed.update(layer)
        
        return layers
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": {node_id: node.to_dict() for node_id, node in self.nodes.items()},
            "edges": self.edges
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskGraph":
        graph = cls()
        for node_id, node_data in data.get("nodes", {}).items():
            node = TaskNode.from_dict(node_data)
            graph.nodes[node_id] = node
        graph.edges = data.get("edges", {})
        return graph
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)
    
    @classmethod
    def from_json(cls, json_str: str) -> "TaskGraph":
        return cls.from_dict(json.loads(json_str))


class TaskGraphBuilder:
    """
    任务图构建器
    根据用户请求生成任务图
    """
    
    @staticmethod
    def build_simple_analysis(query: str, location: str = None) -> TaskGraph:
        """
        构建简单分析任务图
        """
        graph = TaskGraph()
        
        graph.add_node(TaskNode(
            id="requirement",
            agent_name="requirement",
            input_data={"query": query},
            depends_on=[],
            critical=True
        ))
        
        graph.add_node(TaskNode(
            id="collector",
            agent_name="collector",
            input_data={"query": query, "location": location},
            depends_on=["requirement"],
            critical=True
        ))
        
        graph.add_node(TaskNode(
            id="analyst",
            agent_name="analyst",
            input_data={"query": query},
            depends_on=["collector"],
            critical=True
        ))
        
        return graph
    
    @staticmethod
    def build_comparison_analysis(query: str, locations: List[str]) -> TaskGraph:
        """
        构建对比分析任务图（支持并行数据采集）
        """
        graph = TaskGraph()
        
        graph.add_node(TaskNode(
            id="requirement",
            agent_name="requirement",
            input_data={"query": query, "locations": locations},
            depends_on=[],
            critical=True
        ))
        
        for i, location in enumerate(locations):
            graph.add_node(TaskNode(
                id=f"collector_{i}",
                agent_name="collector",
                input_data={"query": query, "location": location},
                depends_on=["requirement"],
                critical=False
            ))
        
        collector_ids = [f"collector_{i}" for i in range(len(locations))]
        
        graph.add_node(TaskNode(
            id="analyst_comparison",
            agent_name="analyst",
            input_data={"query": query, "comparison": True, "locations": locations},
            depends_on=collector_ids,
            critical=True
        ))
        
        return graph
    
    @staticmethod
    def build_batch_analysis(queries: List[str]) -> TaskGraph:
        """
        构建批量分析任务图
        """
        graph = TaskGraph()
        
        graph.add_node(TaskNode(
            id="requirement_batch",
            agent_name="requirement",
            input_data={"queries": queries},
            depends_on=[],
            critical=True
        ))
        
        for i, query in enumerate(queries):
            graph.add_node(TaskNode(
                id=f"collector_{i}",
                agent_name="collector",
                input_data={"query": query, "batch_index": i},
                depends_on=["requirement_batch"],
                critical=False
            ))
            
            graph.add_node(TaskNode(
                id=f"analyst_{i}",
                agent_name="analyst",
                input_data={"query": query, "batch_index": i},
                depends_on=[f"collector_{i}"],
                critical=False
            ))
        
        return graph
    
    @staticmethod
    def build_from_llm_output(llm_output: Dict[str, Any]) -> TaskGraph:
        """
        从LLM输出构建任务图
        """
        graph = TaskGraph()
        
        tasks = llm_output.get("tasks", [])
        for task in tasks:
            node = TaskNode(
                id=task.get("id", f"task_{len(graph.nodes)}"),
                agent_name=task.get("agent", "analyst"),
                input_data=task.get("input", {}),
                depends_on=task.get("depends_on", []),
                critical=task.get("critical", True),
                max_retries=task.get("max_retries", 3),
                timeout_seconds=task.get("timeout_seconds", 60)
            )
            graph.add_node(node)
        
        return graph
