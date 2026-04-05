import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class LineageNode:
    """
    血缘节点
    """
    id: str  # 节点ID
    type: str  # 节点类型：raw_data, processed_data, golden_record, field
    name: str  # 节点名称
    metadata: Dict[str, Any] = None  # 节点元数据


@dataclass
class LineageEdge:
    """
    血缘边
    """
    source_id: str  # 源节点ID
    target_id: str  # 目标节点ID
    relationship: str  # 关系类型：derived_from, contributes_to, transformed_by
    metadata: Dict[str, Any] = None  # 边元数据


class DataLineageTracker:
    """
    数据血缘追踪器，使用python-requests式的链式调用
    """
    
    def __init__(self):
        """
        初始化数据血缘追踪器
        """
        self.nodes: Dict[str, LineageNode] = {}  # 节点字典
        self.edges: List[LineageEdge] = []  # 边列表
        self.current_node_id: Optional[str] = None  # 当前节点ID
    
    def add_node(self, node_id: str, node_type: str, name: str, metadata: Dict[str, Any] = None) -> 'DataLineageTracker':
        """
        添加节点
        
        Args:
            node_id: 节点ID
            node_type: 节点类型
            name: 节点名称
            metadata: 节点元数据
        
        Returns:
            追踪器实例，支持链式调用
        """
        node = LineageNode(
            id=node_id,
            type=node_type,
            name=name,
            metadata=metadata or {}
        )
        self.nodes[node_id] = node
        self.current_node_id = node_id
        return self
    
    def add_edge(self, target_id: str, relationship: str, metadata: Dict[str, Any] = None) -> 'DataLineageTracker':
        """
        添加边，从当前节点到目标节点
        
        Args:
            target_id: 目标节点ID
            relationship: 关系类型
            metadata: 边元数据
        
        Returns:
            追踪器实例，支持链式调用
        """
        if self.current_node_id:
            edge = LineageEdge(
                source_id=self.current_node_id,
                target_id=target_id,
                relationship=relationship,
                metadata=metadata or {}
            )
            self.edges.append(edge)
        return self
    
    def from_node(self, node_id: str) -> 'DataLineageTracker':
        """
        设置当前节点为指定节点
        
        Args:
            node_id: 节点ID
        
        Returns:
            追踪器实例，支持链式调用
        """
        if node_id in self.nodes:
            self.current_node_id = node_id
        return self
    
    def track_raw_to_golden(self, raw_data_id: str, golden_record_id: str, field_mappings: Dict[str, str]) -> 'DataLineageTracker':
        """
        追踪从原始数据到黄金记录的映射
        
        Args:
            raw_data_id: 原始数据ID
            golden_record_id: 黄金记录ID
            field_mappings: 字段映射，{原始字段: 黄金字段}
        
        Returns:
            追踪器实例，支持链式调用
        """
        # 确保原始数据节点存在
        if raw_data_id not in self.nodes:
            self.add_node(raw_data_id, 'raw_data', f'Raw Data {raw_data_id}')
        
        # 确保黄金记录节点存在
        if golden_record_id not in self.nodes:
            self.add_node(golden_record_id, 'golden_record', f'Golden Record {golden_record_id}')
        
        # 添加原始数据到黄金记录的边
        self.from_node(raw_data_id).add_edge(golden_record_id, 'contributes_to', {
            'mapping_type': 'raw_to_golden'
        })
        
        # 追踪字段级映射
        for raw_field, golden_field in field_mappings.items():
            # 创建原始字段节点
            raw_field_id = f"{raw_data_id}_field_{raw_field}"
            if raw_field_id not in self.nodes:
                self.add_node(raw_field_id, 'field', raw_field, {
                    'data_source': raw_data_id,
                    'field_type': 'raw'
                })
            
            # 创建黄金字段节点
            golden_field_id = f"{golden_record_id}_field_{golden_field}"
            if golden_field_id not in self.nodes:
                self.add_node(golden_field_id, 'field', golden_field, {
                    'record_id': golden_record_id,
                    'field_type': 'golden'
                })
            
            # 添加字段映射边
            self.from_node(raw_field_id).add_edge(golden_field_id, 'derived_from', {
                'field_mapping': f"{raw_field} -> {golden_field}"
            })
        
        return self
    
    def serialize(self) -> str:
        """
        序列化为JSON
        
        Returns:
            JSON字符串
        """
        # 转换节点为字典
        nodes_dict = {k: asdict(v) for k, v in self.nodes.items()}
        
        # 转换边为字典
        edges_dict = [asdict(edge) for edge in self.edges]
        
        # 构建序列化对象
        serialized = {
            'nodes': nodes_dict,
            'edges': edges_dict
        }
        
        return json.dumps(serialized, indent=2, ensure_ascii=False)
    
    @classmethod
    def deserialize(cls, json_str: str) -> 'DataLineageTracker':
        """
        从JSON反序列化
        
        Args:
            json_str: JSON字符串
        
        Returns:
            数据血缘追踪器实例
        """
        tracker = cls()
        
        # 解析JSON
        data = json.loads(json_str)
        
        # 加载节点
        for node_id, node_data in data.get('nodes', {}).items():
            node = LineageNode(
                id=node_data['id'],
                type=node_data['type'],
                name=node_data['name'],
                metadata=node_data.get('metadata', {})
            )
            tracker.nodes[node_id] = node
        
        # 加载边
        for edge_data in data.get('edges', []):
            edge = LineageEdge(
                source_id=edge_data['source_id'],
                target_id=edge_data['target_id'],
                relationship=edge_data['relationship'],
                metadata=edge_data.get('metadata', {})
            )
            tracker.edges.append(edge)
        
        return tracker
    
    def get_lineage_for_field(self, field_id: str) -> List[Dict[str, Any]]:
        """
        获取字段的血缘关系
        
        Args:
            field_id: 字段ID
        
        Returns:
            血缘关系列表
        """
        lineage = []
        
        # 查找与字段相关的边
        for edge in self.edges:
            if edge.target_id == field_id:
                # 查找源节点
                if edge.source_id in self.nodes:
                    source_node = self.nodes[edge.source_id]
                    lineage.append({
                        'source': {
                            'id': source_node.id,
                            'type': source_node.type,
                            'name': source_node.name
                        },
                        'relationship': edge.relationship,
                        'metadata': edge.metadata
                    })
        
        return lineage
    
    def get_lineage_for_record(self, record_id: str) -> Dict[str, Any]:
        """
        获取记录的血缘关系
        
        Args:
            record_id: 记录ID
        
        Returns:
            血缘关系字典
        """
        lineage = {
            'record_id': record_id,
            'sources': [],
            'fields': {}
        }
        
        # 查找与记录相关的边
        for edge in self.edges:
            if edge.target_id == record_id:
                # 查找源节点
                if edge.source_id in self.nodes:
                    source_node = self.nodes[edge.source_id]
                    lineage['sources'].append({
                        'id': source_node.id,
                        'type': source_node.type,
                        'name': source_node.name
                    })
        
        # 查找记录的字段血缘
        field_nodes = [node for node in self.nodes.values() if node.id.startswith(f"{record_id}_field_")]
        for field_node in field_nodes:
            field_lineage = self.get_lineage_for_field(field_node.id)
            lineage['fields'][field_node.name] = field_lineage
        
        return lineage
