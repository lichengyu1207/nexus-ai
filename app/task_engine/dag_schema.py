from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class Edge(BaseModel):
    """表示DAG中节点之间的依赖关系"""
    source: str = Field(..., description="源节点ID")
    target: str = Field(..., description="目标节点ID")


class DAGNode(BaseModel):
    """DAG中的节点，表示一个智能体任务"""
    id: str = Field(..., description="节点唯一标识符")
    agent_name: str = Field(..., description="要使用的智能体名称")
    input_mapping: Dict[str, str] = Field(default_factory=dict, description="输入映射，将DAG上下文中的数据映射到智能体输入")
    output_key: str = Field(..., description="智能体输出在DAG上下文中的键名")
    description: Optional[str] = Field(None, description="节点描述")
    config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="节点特定配置")


class DAG(BaseModel):
    """有向无环图，表示一个工作流"""
    id: str = Field(..., description="DAG唯一标识符")
    name: str = Field(..., description="DAG名称")
    nodes: List[DAGNode] = Field(default_factory=list, description="DAG中的节点列表")
    edges: List[Edge] = Field(default_factory=list, description="DAG中的边列表，表示节点间依赖")
    description: Optional[str] = Field(None, description="DAG描述")
    
    def get_node(self, node_id: str) -> Optional[DAGNode]:
        """根据ID获取节点"""
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None
    
    def get_nodes_by_dependency_order(self) -> List[DAGNode]:
        """获取按依赖顺序排序的节点列表"""
        # 简单的拓扑排序实现
        # 1. 计算每个节点的入度
        in_degree = {node.id: 0 for node in self.nodes}
        adjacency_list = {node.id: [] for node in self.nodes}
        
        for edge in self.edges:
            in_degree[edge.target] += 1
            adjacency_list[edge.source].append(edge.target)
        
        # 2. 使用队列进行拓扑排序
        from collections import deque
        queue = deque([node.id for node in self.nodes if in_degree[node.id] == 0])
        result = []
        
        while queue:
            node_id = queue.popleft()
            result.append(self.get_node(node_id))
            
            for neighbor_id in adjacency_list[node_id]:
                in_degree[neighbor_id] -= 1
                if in_degree[neighbor_id] == 0:
                    queue.append(neighbor_id)
        
        # 检查是否存在环
        if len(result) != len(self.nodes):
            raise ValueError("DAG contains cycles")
        
        return result