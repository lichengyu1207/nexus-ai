# -*- coding: utf-8 -*-
"""
Workflow Engine
Orchestrates skill combinations and workflows
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Callable
from datetime import datetime
import asyncio
import json
import uuid


@dataclass
class WorkflowNode:
    id: str
    type: str
    skill_id: Optional[str] = None
    config: Dict[str, Any] = field(default_factory=dict)
    condition: Optional[str] = None
    name: Optional[str] = None


@dataclass
class WorkflowEdge:
    from_node: str
    to_node: str
    label: Optional[str] = None
    condition: Optional[str] = None


@dataclass
class Workflow:
    id: str
    name: str
    description: str
    nodes: List[WorkflowNode]
    edges: List[WorkflowEdge]
    created_by: str
    is_template: bool = False
    is_active: bool = True
    execution_count: int = 0
    avg_duration_ms: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Workflow":
        nodes = [WorkflowNode(**n) for n in data.get("nodes", [])]
        edges = [WorkflowEdge(**e) for e in data.get("edges", [])]
        
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            description=data.get("description", ""),
            nodes=nodes,
            edges=edges,
            created_by=data.get("created_by", ""),
            is_template=data.get("is_template", False),
            is_active=data.get("is_active", True),
            execution_count=data.get("execution_count", 0),
            avg_duration_ms=data.get("avg_duration_ms", 0),
            created_at=data.get("created_at", datetime.now()),
            updated_at=data.get("updated_at", datetime.now())
        )


@dataclass
class WorkflowExecution:
    id: str
    workflow_id: str
    user_id: str
    agent_id: Optional[str]
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    status: str
    duration_ms: int
    node_results: Dict[str, Any]
    error_message: Optional[str] = None
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


class WorkflowEngine:
    def __init__(self, db_pool, skill_executor):
        self.db_pool = db_pool
        self.skill_executor = skill_executor

    async def create_workflow(self, workflow: Workflow) -> Workflow:
        workflow.id = str(uuid.uuid4())
        workflow.created_at = datetime.now()
        workflow.updated_at = datetime.now()
        
        nodes_json = json.dumps([{
            "id": n.id, "type": n.type, "skill_id": n.skill_id,
            "config": n.config, "condition": n.condition, "name": n.name
        } for n in workflow.nodes])
        
        edges_json = json.dumps([{
            "from_node": e.from_node, "to_node": e.to_node,
            "label": e.label, "condition": e.condition
        } for e in workflow.edges])
        
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO workflows (id, name, description, nodes, edges, created_by, is_template, is_active)
                VALUES ($1, $2, $3, $4::jsonb, $5::jsonb, $6, $7, $8)
            """, workflow.id, workflow.name, workflow.description,
                nodes_json, edges_json, workflow.created_by,
                workflow.is_template, workflow.is_active)
        
        return workflow

    async def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM workflows WHERE id = $1", workflow_id
            )
            
            if not row:
                return None
            
            return Workflow.from_dict({
                "id": str(row["id"]),
                "name": row["name"],
                "description": row["description"],
                "nodes": row["nodes"],
                "edges": row["edges"],
                "created_by": str(row["created_by"]) if row["created_by"] else "",
                "is_template": row["is_template"],
                "is_active": row["is_active"],
                "execution_count": row["execution_count"],
                "avg_duration_ms": row["avg_duration_ms"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            })

    async def list_workflows(
        self,
        created_by: Optional[str] = None,
        is_template: Optional[bool] = None,
        page: int = 1,
        size: int = 20
    ) -> tuple[List[Workflow], int]:
        conditions = []
        params = []
        param_idx = 1
        
        if created_by:
            conditions.append(f"created_by = ${param_idx}")
            params.append(created_by)
            param_idx += 1
        
        if is_template is not None:
            conditions.append(f"is_template = ${param_idx}")
            params.append(is_template)
            param_idx += 1
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        async with self.db_pool.acquire() as conn:
            count_row = await conn.fetchrow(
                f"SELECT COUNT(*) as total FROM workflows WHERE {where_clause}", *params
            )
            total = count_row["total"] if count_row else 0
            
            offset = (page - 1) * size
            rows = await conn.fetch(
                f"SELECT * FROM workflows WHERE {where_clause} ORDER BY created_at DESC LIMIT ${param_idx} OFFSET ${param_idx + 1}",
                *params, size, offset
            )
            
            workflows = []
            for row in rows:
                workflows.append(Workflow.from_dict({
                    "id": str(row["id"]),
                    "name": row["name"],
                    "description": row["description"],
                    "nodes": row["nodes"],
                    "edges": row["edges"],
                    "created_by": str(row["created_by"]) if row["created_by"] else "",
                    "is_template": row["is_template"],
                    "is_active": row["is_active"],
                    "execution_count": row["execution_count"],
                    "avg_duration_ms": row["avg_duration_ms"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"]
                }))
            
            return workflows, total

    async def execute(
        self,
        workflow_id: str,
        input_data: Dict[str, Any],
        user_id: str,
        agent_id: Optional[str] = None
    ) -> WorkflowExecution:
        workflow = await self.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        execution_id = str(uuid.uuid4())
        started_at = datetime.now()
        
        node_results = {}
        current_data = input_data.copy()
        
        try:
            entry_nodes = self._find_entry_nodes(workflow)
            
            for node in entry_nodes:
                result = await self._execute_node(workflow, node, current_data, user_id, agent_id, node_results)
                node_results[node.id] = result
                
                if result.get("status") == "error":
                    raise Exception(result.get("error", "Node execution failed"))
                
                current_data.update(result.get("output", {}))
            
            status = "success"
            error_message = None
            
        except Exception as e:
            status = "error"
            error_message = str(e)
        
        completed_at = datetime.now()
        duration_ms = int((completed_at - started_at).total_seconds() * 1000)
        
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO workflow_executions (id, workflow_id, user_id, agent_id, input_data, output_data, status, duration_ms, node_results, started_at, completed_at, error_message)
                VALUES ($1, $2, $3, $4, $5::jsonb, $6::jsonb, $7, $8, $9::jsonb, $10, $11, $12)
            """, execution_id, workflow_id, user_id, agent_id,
                json.dumps(input_data), json.dumps(current_data),
                status, duration_ms, json.dumps(node_results),
                started_at, completed_at, error_message)
            
            await conn.execute("""
                UPDATE workflows SET 
                    execution_count = execution_count + 1,
                    avg_duration_ms = (avg_duration_ms * execution_count + $1) / (execution_count + 1),
                    updated_at = NOW()
                WHERE id = $2
            """, duration_ms, workflow_id)
        
        return WorkflowExecution(
            id=execution_id,
            workflow_id=workflow_id,
            user_id=user_id,
            agent_id=agent_id,
            input_data=input_data,
            output_data=current_data,
            status=status,
            duration_ms=duration_ms,
            node_results=node_results,
            error_message=error_message,
            started_at=started_at,
            completed_at=completed_at
        )

    def _find_entry_nodes(self, workflow: Workflow) -> List[WorkflowNode]:
        target_nodes = {e.to_node for e in workflow.edges}
        entry_nodes = [n for n in workflow.nodes if n.id not in target_nodes]
        return entry_nodes if entry_nodes else workflow.nodes[:1]

    async def _execute_node(
        self,
        workflow: Workflow,
        node: WorkflowNode,
        input_data: Dict[str, Any],
        user_id: str,
        agent_id: Optional[str],
        node_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        if node.type == "skill" and node.skill_id:
            result = await self.skill_executor.execute(
                node.skill_id,
                {**input_data, **node.config},
                user_id,
                agent_id
            )
            
            return {
                "status": result.status,
                "output": result.output_data,
                "duration_ms": result.duration_ms,
                "error": result.error_message
            }
        
        elif node.type == "condition":
            condition_result = self._evaluate_condition(node.condition, input_data, node_results)
            
            next_nodes = self._find_next_nodes(workflow, node.id, condition_result)
            
            for next_node in next_nodes:
                result = await self._execute_node(workflow, next_node, input_data, user_id, agent_id, node_results)
                node_results[next_node.id] = result
            
            return {"status": "success", "condition_result": condition_result}
        
        elif node.type == "parallel":
            next_nodes = self._find_next_nodes(workflow, node.id)
            
            tasks = [
                self._execute_node(workflow, n, input_data, user_id, agent_id, node_results)
                for n in next_nodes
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for n, r in zip(next_nodes, results):
                if isinstance(r, Exception):
                    node_results[n.id] = {"status": "error", "error": str(r)}
                else:
                    node_results[n.id] = r
            
            return {"status": "success", "parallel_count": len(next_nodes)}
        
        else:
            return {"status": "success", "output": input_data}

    def _evaluate_condition(self, condition: Optional[str], data: Dict[str, Any], node_results: Dict[str, Any]) -> Any:
        if not condition:
            return True
        
        try:
            context = {**data, **node_results}
            return eval(condition, {"__builtins__": {}}, context)
        except Exception:
            return True

    def _find_next_nodes(self, workflow: Workflow, node_id: str, condition_result: Any = None) -> List[WorkflowNode]:
        next_node_ids = []
        
        for edge in workflow.edges:
            if edge.from_node == node_id:
                if edge.condition:
                    try:
                        if eval(edge.condition, {"__builtins__": {}, "result": condition_result}):
                            next_node_ids.append(edge.to_node)
                    except Exception:
                        pass
                else:
                    next_node_ids.append(edge.to_node)
        
        return [n for n in workflow.nodes if n.id in next_node_ids]

    async def delete_workflow(self, workflow_id: str) -> bool:
        async with self.db_pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM workflows WHERE id = $1", workflow_id
            )
            return result == "DELETE 1"


_workflow_engine: Optional[WorkflowEngine] = None


def get_workflow_engine() -> Optional[WorkflowEngine]:
    return _workflow_engine


async def init_workflow_engine(db_pool, skill_executor):
    global _workflow_engine
    _workflow_engine = WorkflowEngine(db_pool, skill_executor)
    return _workflow_engine
