"""
跨部门协同任务流引擎
Cross Department Task Flow Engine - 让多个业务智能体协同完成复杂业务

协同机制模块
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Callable
import asyncio
import json
import uuid


class FlowStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class NodeStatus(Enum):
    PENDING = "pending"
    WAITING = "waiting"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class NodeType(Enum):
    TASK = "task"
    DECISION = "decision"
    PARALLEL = "parallel"
    MERGE = "merge"
    LOOP = "loop"
    DELAY = "delay"
    NOTIFICATION = "notification"


@dataclass
class FlowNode:
    node_id: str
    node_type: NodeType
    name: str
    agent_type: str
    action: str
    parameters: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)
    timeout_seconds: int = 300
    retry_count: int = 3
    retry_interval_seconds: int = 10
    status: NodeStatus = NodeStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class TaskFlow:
    flow_id: str
    name: str
    description: str
    nodes: Dict[str, FlowNode]
    edges: List[Tuple[str, str]]
    status: FlowStatus = FlowStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    current_nodes: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    variables: Dict[str, Any] = field(default_factory=dict)
    triggered_by: str = ""
    priority: int = 5


@dataclass
class FlowExecutionLog:
    log_id: str
    flow_id: str
    node_id: str
    event_type: str
    message: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    details: Dict[str, Any] = field(default_factory=dict)


class FlowTemplate:
    def __init__(self, template_id: str, name: str):
        self.template_id = template_id
        self.name = name
        self.nodes: Dict[str, FlowNode] = {}
        self.edges: List[Tuple[str, str]] = []

    def add_node(self, node: FlowNode) -> None:
        self.nodes[node.node_id] = node

    def add_edge(self, from_node: str, to_node: str) -> None:
        self.edges.append((from_node, to_node))
        if to_node in self.nodes:
            self.nodes[to_node].dependencies.append(from_node)

    def create_flow(self, variables: Dict[str, Any] = None) -> TaskFlow:
        flow_id = f"flow_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"

        nodes_copy = {}
        for node_id, node in self.nodes.items():
            nodes_copy[node_id] = FlowNode(
                node_id=node.node_id,
                node_type=node.node_type,
                name=node.name,
                agent_type=node.agent_type,
                action=node.action,
                parameters=node.parameters.copy(),
                dependencies=node.dependencies.copy(),
                timeout_seconds=node.timeout_seconds,
                retry_count=node.retry_count,
                retry_interval_seconds=node.retry_interval_seconds,
            )

        return TaskFlow(
            flow_id=flow_id,
            name=self.name,
            description=f"Created from template {self.template_id}",
            nodes=nodes_copy,
            edges=self.edges.copy(),
            variables=variables or {},
        )


class FlowScheduler:
    def __init__(self):
        self.ready_queue: List[str] = []
        self.running_nodes: Set[str] = set()
        self.completed_nodes: Set[str] = set()

    def get_ready_nodes(self, flow: TaskFlow) -> List[str]:
        ready = []

        for node_id, node in flow.nodes.items():
            if node.status != NodeStatus.PENDING:
                continue

            if node_id in self.running_nodes or node_id in self.completed_nodes:
                continue

            dependencies_met = all(
                dep in self.completed_nodes or flow.nodes[dep].status == NodeStatus.SUCCESS
                for dep in node.dependencies
            )

            if dependencies_met:
                ready.append(node_id)

        return ready

    def mark_running(self, node_id: str) -> None:
        self.running_nodes.add(node_id)

    def mark_completed(self, node_id: str, success: bool) -> None:
        self.running_nodes.discard(node_id)
        self.completed_nodes.add(node_id)

    def reset(self) -> None:
        self.ready_queue.clear()
        self.running_nodes.clear()
        self.completed_nodes.clear()


class NodeExecutor:
    def __init__(self):
        self.agent_handlers: Dict[str, Callable] = {}
        self.execution_history: List[Dict] = []

    def register_agent_handler(self, agent_type: str, handler: Callable) -> None:
        self.agent_handlers[agent_type] = handler

    async def execute(
        self,
        node: FlowNode,
        context: Dict[str, Any],
        variables: Dict[str, Any],
    ) -> Dict[str, Any]:
        handler = self.agent_handlers.get(node.agent_type)

        merged_params = {**node.parameters, **variables, **context}

        if handler:
            try:
                result = await handler(node.action, merged_params)
                self._record_execution(node, True, result)
                return result
            except Exception as e:
                self._record_execution(node, False, {"error": str(e)})
                raise
        else:
            result = {"action": node.action, "params": merged_params, "status": "simulated"}
            self._record_execution(node, True, result)
            return result

    def _record_execution(
        self, node: FlowNode, success: bool, result: Dict
    ) -> None:
        self.execution_history.append(
            {
                "node_id": node.node_id,
                "agent_type": node.agent_type,
                "action": node.action,
                "success": success,
                "result": result,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )


class CrossDepartmentTaskFlowEngine:
    def __init__(self, engine_id: str = "task_flow_engine_001"):
        self.engine_id = engine_id
        self.templates: Dict[str, FlowTemplate] = {}
        self.active_flows: Dict[str, TaskFlow] = {}
        self.flow_history: List[TaskFlow] = []
        self.execution_logs: List[FlowExecutionLog] = []

        self.scheduler = FlowScheduler()
        self.executor = NodeExecutor()

        self._initialize_default_templates()

    def _initialize_default_templates(self) -> None:
        consultation_flow = FlowTemplate("consultation_to_report", "咨询到报告生成流程")

        consultation_flow.add_node(
            FlowNode(
                node_id="intent_recognition",
                node_type=NodeType.TASK,
                name="意图识别",
                agent_type="libu",
                action="recognize_intent",
                parameters={},
            )
        )

        consultation_flow.add_node(
            FlowNode(
                node_id="data_collection",
                node_type=NodeType.TASK,
                name="数据采集",
                agent_type="bingbu",
                action="collect_data",
                parameters={},
                dependencies=["intent_recognition"],
            )
        )

        consultation_flow.add_node(
            FlowNode(
                node_id="analysis",
                node_type=NodeType.TASK,
                name="数据分析",
                agent_type="gongbu",
                action="analyze",
                parameters={},
                dependencies=["data_collection"],
            )
        )

        consultation_flow.add_node(
            FlowNode(
                node_id="report_generation",
                node_type=NodeType.TASK,
                name="报告生成",
                agent_type="gongbu",
                action="generate_report",
                parameters={},
                dependencies=["analysis"],
            )
        )

        consultation_flow.add_node(
            FlowNode(
                node_id="points_award",
                node_type=NodeType.TASK,
                name="积分奖励",
                agent_type="hubu",
                action="award_points",
                parameters={},
                dependencies=["report_generation"],
            )
        )

        consultation_flow.add_edge("intent_recognition", "data_collection")
        consultation_flow.add_edge("data_collection", "analysis")
        consultation_flow.add_edge("analysis", "report_generation")
        consultation_flow.add_edge("report_generation", "points_award")

        self.templates["consultation_to_report"] = consultation_flow

        investment_flow = FlowTemplate("investment_analysis", "投资分析流程")

        investment_flow.add_node(
            FlowNode(
                node_id="risk_assessment",
                node_type=NodeType.TASK,
                name="风险评估",
                agent_type="xingbu",
                action="assess_risk",
                parameters={},
            )
        )

        investment_flow.add_node(
            FlowNode(
                node_id="market_analysis",
                node_type=NodeType.TASK,
                name="市场分析",
                agent_type="gongbu",
                action="analyze_market",
                parameters={},
            )
        )

        investment_flow.add_node(
            FlowNode(
                node_id="roi_calculation",
                node_type=NodeType.PARALLEL,
                name="回报计算",
                agent_type="gongbu",
                action="calculate_roi",
                parameters={},
                dependencies=["risk_assessment", "market_analysis"],
            )
        )

        investment_flow.add_edge("risk_assessment", "roi_calculation")
        investment_flow.add_edge("market_analysis", "roi_calculation")

        self.templates["investment_analysis"] = investment_flow

    def register_template(self, template: FlowTemplate) -> None:
        self.templates[template.template_id] = template

    def create_flow(
        self,
        template_id: str,
        variables: Dict[str, Any] = None,
        triggered_by: str = "",
        priority: int = 5,
    ) -> Optional[TaskFlow]:
        template = self.templates.get(template_id)
        if not template:
            return None

        flow = template.create_flow(variables)
        flow.triggered_by = triggered_by
        flow.priority = priority

        self.active_flows[flow.flow_id] = flow

        self._log_event(
            flow.flow_id, "", "flow_created", f"Flow created from template {template_id}"
        )

        return flow

    async def execute_flow(self, flow_id: str) -> TaskFlow:
        flow = self.active_flows.get(flow_id)
        if not flow:
            return None

        flow.status = FlowStatus.RUNNING
        flow.started_at = datetime.utcnow()

        self._log_event(flow_id, "", "flow_started", "Flow execution started")

        self.scheduler.reset()

        while True:
            ready_nodes = self.scheduler.get_ready_nodes(flow)

            if not ready_nodes:
                if not self.scheduler.running_nodes:
                    break
                await asyncio.sleep(0.1)
                continue

            for node_id in ready_nodes:
                node = flow.nodes[node_id]

                if node.node_type == NodeType.PARALLEL:
                    await self._execute_parallel(flow, node)
                else:
                    await self._execute_node(flow, node)

        all_success = all(
            node.status == NodeStatus.SUCCESS
            for node in flow.nodes.values()
            if node.node_type == NodeType.TASK
        )

        flow.status = FlowStatus.COMPLETED if all_success else FlowStatus.FAILED
        flow.completed_at = datetime.utcnow()

        self._log_event(
            flow_id,
            "",
            "flow_completed",
            f"Flow completed with status: {flow.status.value}",
        )

        self.flow_history.append(flow)
        del self.active_flows[flow_id]

        return flow

    async def _execute_node(self, flow: TaskFlow, node: FlowNode) -> None:
        self.scheduler.mark_running(node.node_id)
        node.status = NodeStatus.RUNNING
        node.started_at = datetime.utcnow()

        self._log_event(flow.flow_id, node.node_id, "node_started", f"Node {node.name} started")

        retry_count = 0
        while retry_count <= node.retry_count:
            try:
                result = await self.executor.execute(
                    node, flow.context, flow.variables
                )

                node.result = result
                node.status = NodeStatus.SUCCESS
                node.completed_at = datetime.utcnow()

                flow.context.update(result)
                flow.variables.update(result)

                self.scheduler.mark_completed(node.node_id, True)

                self._log_event(
                    flow.flow_id, node.node_id, "node_success", f"Node {node.name} completed"
                )
                return

            except Exception as e:
                retry_count += 1
                node.error = str(e)

                if retry_count <= node.retry_count:
                    self._log_event(
                        flow.flow_id,
                        node.node_id,
                        "node_retry",
                        f"Node {node.name} retry {retry_count}",
                    )
                    await asyncio.sleep(node.retry_interval_seconds)
                else:
                    node.status = NodeStatus.FAILED
                    node.completed_at = datetime.utcnow()
                    self.scheduler.mark_completed(node.node_id, False)

                    self._log_event(
                        flow.flow_id,
                        node.node_id,
                        "node_failed",
                        f"Node {node.name} failed: {str(e)}",
                    )

    async def _execute_parallel(self, flow: TaskFlow, node: FlowNode) -> None:
        self.scheduler.mark_running(node.node_id)
        node.status = NodeStatus.RUNNING
        node.started_at = datetime.utcnow()

        try:
            result = await self.executor.execute(node, flow.context, flow.variables)

            node.result = result
            node.status = NodeStatus.SUCCESS
            node.completed_at = datetime.utcnow()

            self.scheduler.mark_completed(node.node_id, True)

        except Exception as e:
            node.status = NodeStatus.FAILED
            node.error = str(e)
            self.scheduler.mark_completed(node.node_id, False)

    def _log_event(
        self,
        flow_id: str,
        node_id: str,
        event_type: str,
        message: str,
        details: Dict = None,
    ) -> None:
        log = FlowExecutionLog(
            log_id=f"log_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
            flow_id=flow_id,
            node_id=node_id,
            event_type=event_type,
            message=message,
            details=details or {},
        )
        self.execution_logs.append(log)

    def pause_flow(self, flow_id: str) -> bool:
        flow = self.active_flows.get(flow_id)
        if flow and flow.status == FlowStatus.RUNNING:
            flow.status = FlowStatus.PAUSED
            self._log_event(flow_id, "", "flow_paused", "Flow paused")
            return True
        return False

    def resume_flow(self, flow_id: str) -> bool:
        flow = self.active_flows.get(flow_id)
        if flow and flow.status == FlowStatus.PAUSED:
            flow.status = FlowStatus.RUNNING
            self._log_event(flow_id, "", "flow_resumed", "Flow resumed")
            return True
        return False

    def cancel_flow(self, flow_id: str) -> bool:
        flow = self.active_flows.get(flow_id)
        if flow:
            flow.status = FlowStatus.CANCELLED
            flow.completed_at = datetime.utcnow()
            self._log_event(flow_id, "", "flow_cancelled", "Flow cancelled")
            self.flow_history.append(flow)
            del self.active_flows[flow_id]
            return True
        return False

    def get_flow(self, flow_id: str) -> Optional[TaskFlow]:
        flow = self.active_flows.get(flow_id)
        if not flow:
            flow = next((f for f in self.flow_history if f.flow_id == flow_id), None)
        return flow

    def get_flow_logs(self, flow_id: str) -> List[FlowExecutionLog]:
        return [log for log in self.execution_logs if log.flow_id == flow_id]

    def register_agent_handler(self, agent_type: str, handler: Callable) -> None:
        self.executor.register_agent_handler(agent_type, handler)

    def get_engine_stats(self) -> Dict[str, Any]:
        return {
            "active_flows": len(self.active_flows),
            "completed_flows": len(self.flow_history),
            "templates_available": len(self.templates),
            "total_logs": len(self.execution_logs),
        }
