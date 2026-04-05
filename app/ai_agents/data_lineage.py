from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime


class DataLineage:
    """Data lineage tracking system for tracing data origins and transformations"""
    
    def __init__(self):
        self.lineage_graph: Dict[str, Dict[str, Any]] = {}
        self.data_sources: Dict[str, Dict[str, Any]] = {}
        self.processing_steps: Dict[str, Dict[str, Any]] = {}
    
    def create_data_node(self, data: Any, source: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Create a data node with unique ID and track its origin"""
        node_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        node = {
            "id": node_id,
            "data": data,
            "source": source,
            "created_at": timestamp,
            "metadata": metadata or {},
            "transformations": [],
            "used_in": []
        }
        
        self.lineage_graph[node_id] = node
        
        # Track data source
        if source not in self.data_sources:
            self.data_sources[source] = {
                "name": source,
                "count": 0,
                "first_seen": timestamp,
                "last_seen": timestamp
            }
        
        self.data_sources[source]["count"] += 1
        self.data_sources[source]["last_seen"] = timestamp
        
        return node_id
    
    def track_transformation(self, input_node_ids: List[str], output_data: Any, 
                          transformation_type: str, agent_name: str, 
                          metadata: Optional[Dict[str, Any]] = None) -> str:
        """Track data transformation from input nodes to output"""
        output_node_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        # Create output node
        output_node = {
            "id": output_node_id,
            "data": output_data,
            "source": "transformation",
            "created_at": timestamp,
            "metadata": metadata or {},
            "transformations": [],
            "used_in": []
        }
        
        # Record transformation
        transformation_id = str(uuid.uuid4())
        transformation = {
            "id": transformation_id,
            "type": transformation_type,
            "agent": agent_name,
            "timestamp": timestamp,
            "input_nodes": input_node_ids,
            "output_node": output_node_id,
            "metadata": metadata or {}
        }
        
        # Add transformation to input nodes
        for input_node_id in input_node_ids:
            if input_node_id in self.lineage_graph:
                self.lineage_graph[input_node_id]["transformations"].append(transformation_id)
                self.lineage_graph[input_node_id]["used_in"].append(output_node_id)
        
        # Add transformation reference to output node
        output_node["transformations"].append(transformation_id)
        
        # Add to lineage graph
        self.lineage_graph[output_node_id] = output_node
        self.processing_steps[transformation_id] = transformation
        
        return output_node_id
    
    def track_usage(self, node_id: str, usage_context: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Track how data is used in the system"""
        if node_id in self.lineage_graph:
            self.lineage_graph[node_id]["used_in"].append({
                "context": usage_context,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": metadata or {}
            })
    
    def get_lineage(self, node_id: str) -> Dict[str, Any]:
        """Get complete lineage for a data node"""
        if node_id not in self.lineage_graph:
            return {"error": "Node not found"}
        
        node = self.lineage_graph[node_id]
        lineage = {
            "node": node,
            "ancestors": [],
            "descendants": [],
            "transformations": []
        }
        
        # Get ancestors (data sources and previous transformations)
        for transformation_id in node.get("transformations", []):
            if transformation_id in self.processing_steps:
                transformation = self.processing_steps[transformation_id]
                lineage["transformations"].append(transformation)
                
                # Get input nodes (ancestors)
                for input_node_id in transformation.get("input_nodes", []):
                    if input_node_id in self.lineage_graph:
                        lineage["ancestors"].append(self.lineage_graph[input_node_id])
        
        # Get descendants (nodes that use this data)
        for used_in in node.get("used_in", []):
            if isinstance(used_in, str) and used_in in self.lineage_graph:
                lineage["descendants"].append(self.lineage_graph[used_in])
        
        return lineage
    
    def get_data_sources(self) -> Dict[str, Dict[str, Any]]:
        """Get all data sources and their statistics"""
        return self.data_sources
    
    def get_processing_steps(self) -> Dict[str, Dict[str, Any]]:
        """Get all processing steps"""
        return self.processing_steps
    
    def search_by_source(self, source: str) -> List[str]:
        """Search for data nodes by source"""
        return [node_id for node_id, node in self.lineage_graph.items() 
                if node.get("source") == source]
    
    def search_by_transformation(self, transformation_type: str) -> List[str]:
        """Search for data nodes by transformation type"""
        result = []
        for transformation_id, transformation in self.processing_steps.items():
            if transformation.get("type") == transformation_type:
                output_node_id = transformation.get("output_node")
                if output_node_id:
                    result.append(output_node_id)
        return result
    
    def export_lineage(self) -> Dict[str, Any]:
        """Export complete lineage graph"""
        return {
            "lineage_graph": self.lineage_graph,
            "data_sources": self.data_sources,
            "processing_steps": self.processing_steps,
            "exported_at": datetime.utcnow().isoformat()
        }
    
    def clear(self) -> None:
        """Clear all lineage data"""
        self.lineage_graph.clear()
        self.data_sources.clear()
        self.processing_steps.clear()


# Create a global data lineage instance
lineage_tracker = DataLineage()