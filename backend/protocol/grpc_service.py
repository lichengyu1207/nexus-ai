"""
智能体gRPC通信服务实现
基于Protobuf协议的高效智能体通信
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, AsyncIterator
from datetime import datetime
from dataclasses import dataclass, field
import uuid
import json

logger = logging.getLogger(__name__)


@dataclass
class AgentEndpoint:
    agent_id: str
    name: str
    role: int
    capabilities: List[str]
    endpoint: str
    last_heartbeat: float
    metadata: Dict[str, str]
    status: str = "active"
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    active_tasks: int = 0


@dataclass
class PendingTask:
    task_id: str
    task_type: str
    parameters: bytes
    deadline: float
    priority: int
    required_capabilities: List[str]
    assigned_agent: Optional[str] = None


class AgentRegistry:
    def __init__(self):
        self._agents: Dict[str, AgentEndpoint] = {}
        self._capabilities_index: Dict[str, List[str]] = {}
        self._role_index: Dict[int, List[str]] = {}
        self._heartbeat_timeout = 30.0
        
    def register(self, agent: AgentEndpoint) -> bool:
        self._agents[agent.agent_id] = agent
        
        for cap in agent.capabilities:
            if cap not in self._capabilities_index:
                self._capabilities_index[cap] = []
            if agent.agent_id not in self._capabilities_index[cap]:
                self._capabilities_index[cap].append(agent.agent_id)
                
        if agent.role not in self._role_index:
            self._role_index[agent.role] = []
        if agent.agent_id not in self._role_index[agent.role]:
            self._role_index[agent.role].append(agent.agent_id)
            
        logger.info(f"Registered agent: {agent.agent_id} ({agent.name})")
        return True
        
    def unregister(self, agent_id: str) -> bool:
        if agent_id not in self._agents:
            return False
            
        agent = self._agents[agent_id]
        
        for cap in agent.capabilities:
            if cap in self._capabilities_index:
                if agent_id in self._capabilities_index[cap]:
                    self._capabilities_index[cap].remove(agent_id)
                    
        if agent.role in self._role_index:
            if agent_id in self._role_index[agent.role]:
                self._role_index[agent.role].remove(agent_id)
                
        del self._agents[agent_id]
        logger.info(f"Unregistered agent: {agent_id}")
        return True
        
    def get_agent(self, agent_id: str) -> Optional[AgentEndpoint]:
        return self._agents.get(agent_id)
        
    def find_by_capabilities(self, capabilities: List[str]) -> List[AgentEndpoint]:
        if not capabilities:
            return list(self._agents.values())
            
        matching_ids = None
        for cap in capabilities:
            cap_ids = set(self._capabilities_index.get(cap, []))
            if matching_ids is None:
                matching_ids = cap_ids
            else:
                matching_ids &= cap_ids
                
        if not matching_ids:
            return []
            
        return [self._agents[aid] for aid in matching_ids if aid in self._agents]
        
    def find_by_role(self, role: int) -> List[AgentEndpoint]:
        agent_ids = self._role_index.get(role, [])
        return [self._agents[aid] for aid in agent_ids if aid in self._agents]
        
    def update_heartbeat(self, agent_id: str, heartbeat_data: Dict[str, Any]) -> bool:
        agent = self._agents.get(agent_id)
        if not agent:
            return False
            
        agent.last_heartbeat = heartbeat_data.get("timestamp", 0)
        agent.cpu_usage = heartbeat_data.get("cpu_usage", 0)
        agent.memory_usage = heartbeat_data.get("memory_usage", 0)
        agent.active_tasks = heartbeat_data.get("active_tasks", 0)
        agent.status = heartbeat_data.get("status", "active")
        
        return True
        
    def get_active_agents(self) -> List[AgentEndpoint]:
        import time
        current_time = time.time()
        return [
            agent for agent in self._agents.values()
            if current_time - agent.last_heartbeat < self._heartbeat_timeout
            and agent.status == "active"
        ]


class MessageRouter:
    def __init__(self, registry: AgentRegistry):
        self.registry = registry
        self._message_queues: Dict[str, asyncio.Queue] = {}
        self._broadcast_queue: asyncio.Queue = asyncio.Queue()
        self._pending_acks: Dict[str, asyncio.Future] = {}
        
    async def route_message(self, message: Dict[str, Any]) -> bool:
        target_id = message.get("target_agent_id")
        message_type = message.get("type", 0)
        
        if message_type == 7 or target_id == "broadcast":
            await self._broadcast_queue.put(message)
            return True
            
        if target_id:
            if target_id not in self._message_queues:
                self._message_queues[target_id] = asyncio.Queue()
            await self._message_queues[target_id].put(message)
            return True
            
        return False
        
    async def get_messages(
        self, 
        agent_id: str,
        message_types: List[int] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        if agent_id not in self._message_queues:
            self._message_queues[agent_id] = asyncio.Queue()
            
        queue = self._message_queues[agent_id]
        
        while True:
            try:
                message = await asyncio.wait_for(queue.get(), timeout=1.0)
                if message_types is None or message.get("type") in message_types:
                    yield message
            except asyncio.TimeoutError:
                continue
                
    async def get_broadcasts(self) -> AsyncIterator[Dict[str, Any]]:
        while True:
            try:
                message = await asyncio.wait_for(self._broadcast_queue.get(), timeout=1.0)
                yield message
            except asyncio.TimeoutError:
                continue


class TaskScheduler:
    def __init__(self, registry: AgentRegistry):
        self.registry = registry
        self._pending_tasks: Dict[str, PendingTask] = {}
        self._running_tasks: Dict[str, str] = {}
        self._completed_tasks: Dict[str, Dict[str, Any]] = {}
        
    async def submit_task(self, task: PendingTask) -> str:
        self._pending_tasks[task.task_id] = task
        await self._assign_task(task)
        return task.task_id
        
    async def _assign_task(self, task: PendingTask):
        candidates = self.registry.find_by_capabilities(task.required_capabilities)
        
        candidates = [
            a for a in candidates
            if a.status == "active" and a.active_tasks < 5
        ]
        
        if not candidates:
            logger.warning(f"No available agents for task {task.task_id}")
            return
            
        candidates.sort(key=lambda a: (a.active_tasks, a.cpu_usage))
        selected = candidates[0]
        
        task.assigned_agent = selected.agent_id
        self._running_tasks[task.task_id] = selected.agent_id
        
        logger.info(f"Assigned task {task.task_id} to agent {selected.agent_id}")
        
    async def complete_task(self, task_id: str, result: Dict[str, Any]):
        if task_id in self._running_tasks:
            del self._running_tasks[task_id]
            
        self._completed_tasks[task_id] = result
        
        if task_id in self._pending_tasks:
            del self._pending_tasks[task_id]
            
    def get_task_for_agent(self, agent_id: str) -> Optional[PendingTask]:
        for task_id, assigned_agent in self._running_tasks.items():
            if assigned_agent == agent_id and task_id in self._pending_tasks:
                return self._pending_tasks[task_id]
        return None


class CoordinationManager:
    def __init__(self):
        self._active_coordinations: Dict[str, Dict[str, Any]] = {}
        self._responses: Dict[str, List[Dict[str, Any]]] = {}
        
    async def initiate_coordination(
        self,
        coordination_id: str,
        participants: List[str],
        coordination_type: str,
        context: bytes,
        timeout_ms: int
    ) -> str:
        self._active_coordinations[coordination_id] = {
            "participants": participants,
            "coordination_type": coordination_type,
            "context": context,
            "timeout_ms": timeout_ms,
            "status": "pending",
            "accepted": set(),
            "rejected": set()
        }
        self._responses[coordination_id] = []
        
        return coordination_id
        
    async def submit_response(
        self,
        coordination_id: str,
        agent_id: str,
        accepted: bool,
        contribution: bytes = None,
        reason: str = None
    ):
        if coordination_id not in self._active_coordinations:
            return False
            
        coord = self._active_coordinations[coordination_id]
        
        if accepted:
            coord["accepted"].add(agent_id)
        else:
            coord["rejected"].add(agent_id)
            
        self._responses[coordination_id].append({
            "agent_id": agent_id,
            "accepted": accepted,
            "contribution": contribution,
            "reason": reason
        })
        
        if len(coord["accepted"]) == len(coord["participants"]):
            coord["status"] = "completed"
        elif len(coord["rejected"]) > len(coord["participants"]) // 2:
            coord["status"] = "rejected"
            
        return True
        
    def get_coordination_status(self, coordination_id: str) -> Optional[Dict[str, Any]]:
        return self._active_coordinations.get(coordination_id)
        
    def get_responses(self, coordination_id: str) -> List[Dict[str, Any]]:
        return self._responses.get(coordination_id, [])


class AgentCommunicationServicer:
    def __init__(self):
        self.registry = AgentRegistry()
        self.router = MessageRouter(self.registry)
        self.scheduler = TaskScheduler(self.registry)
        self.coordinator = CoordinationManager()
        
    async def SendMessage(self, request: Dict[str, Any]) -> Dict[str, Any]:
        message_id = request.get("message_id", str(uuid.uuid4()))
        
        success = await self.router.route_message(request)
        
        return {
            "message_id": message_id,
            "received": success,
            "timestamp": int(datetime.now().timestamp() * 1000)
        }
        
    async def StreamMessages(
        self, 
        request: Dict[str, Any]
    ) -> AsyncIterator[Dict[str, Any]]:
        agent_id = request.get("agent_id")
        message_types = request.get("message_types", [])
        
        async for message in self.router.get_messages(agent_id, message_types):
            yield message
            
    async def ExecuteTask(self, request: Dict[str, Any]) -> Dict[str, Any]:
        task = PendingTask(
            task_id=request.get("task_id", str(uuid.uuid4())),
            task_type=request.get("task_type", ""),
            parameters=request.get("parameters", b""),
            deadline=request.get("deadline", 0),
            priority=request.get("priority", 2),
            required_capabilities=request.get("required_capabilities", [])
        )
        
        task_id = await self.scheduler.submit_task(task)
        
        return {
            "task_id": task_id,
            "agent_id": "",
            "success": False,
            "output": b"",
            "error_message": "Task submitted, awaiting execution",
            "start_time": int(datetime.now().timestamp() * 1000),
            "end_time": 0,
            "metrics": {}
        }
        
    async def Coordinate(
        self, 
        request: Dict[str, Any]
    ) -> AsyncIterator[Dict[str, Any]]:
        coordination_id = request.get("coordination_id", str(uuid.uuid4()))
        participants = request.get("participant_ids", [])
        
        await self.coordinator.initiate_coordination(
            coordination_id,
            participants,
            request.get("coordination_type", ""),
            request.get("context", b""),
            request.get("timeout_ms", 30000)
        )
        
        import time
        start_time = time.time()
        timeout = request.get("timeout_ms", 30000) / 1000
        
        while time.time() - start_time < timeout:
            status = self.coordinator.get_coordination_status(coordination_id)
            if status and status["status"] in ["completed", "rejected"]:
                break
                
            responses = self.coordinator.get_responses(coordination_id)
            for response in responses:
                yield {
                    "coordination_id": coordination_id,
                    "agent_id": response["agent_id"],
                    "accepted": response["accepted"],
                    "contribution": response.get("contribution", b""),
                    "rejection_reason": response.get("reason", "")
                }
                
            await asyncio.sleep(0.1)
            
    async def Heartbeat(self, request: Dict[str, Any]) -> Dict[str, Any]:
        agent_id = request.get("agent_id")
        
        self.registry.update_heartbeat(agent_id, request)
        
        pending_tasks = []
        task = self.scheduler.get_task_for_agent(agent_id)
        if task:
            pending_tasks.append(task.task_id)
            
        return {
            "healthy": True,
            "pending_tasks": pending_tasks,
            "config_updates": {}
        }
        
    async def DiscoverServices(
        self, 
        request: Dict[str, Any]
    ) -> Dict[str, Any]:
        service_name = request.get("service_name")
        required_caps = request.get("required_capabilities", [])
        role_filter = request.get("role_filter", 0)
        
        if required_caps:
            agents = self.registry.find_by_capabilities(required_caps)
        elif role_filter:
            agents = self.registry.find_by_role(role_filter)
        else:
            agents = self.registry.get_active_agents()
            
        return {
            "agents": [
                {
                    "agent_id": a.agent_id,
                    "name": a.name,
                    "role": a.role,
                    "capabilities": a.capabilities,
                    "endpoint": a.endpoint,
                    "last_heartbeat": a.last_heartbeat,
                    "metadata": a.metadata
                }
                for a in agents
            ]
        }
        
    async def RegisterAgent(self, request: Dict[str, Any]) -> Dict[str, Any]:
        agent = AgentEndpoint(
            agent_id=request.get("agent_id", str(uuid.uuid4())),
            name=request.get("name", ""),
            role=request.get("role", 0),
            capabilities=request.get("capabilities", []),
            endpoint=request.get("endpoint", ""),
            last_heartbeat=int(datetime.now().timestamp()),
            metadata=request.get("metadata", {})
        )
        
        success = self.registry.register(agent)
        
        return {
            "success": success,
            "assigned_id": agent.agent_id,
            "error_message": "" if success else "Registration failed"
        }
        
    async def UnregisterAgent(self, request: Dict[str, Any]) -> Dict[str, Any]:
        agent_id = request.get("agent_id")
        success = self.registry.unregister(agent_id)
        
        return {
            "success": success,
            "error_message": "" if success else "Agent not found"
        }


class ServiceDiscoveryClient:
    def __init__(self, servicer: AgentCommunicationServicer):
        self.servicer = servicer
        
    async def find_agents_by_capability(
        self, 
        capabilities: List[str]
    ) -> List[AgentEndpoint]:
        result = await self.servicer.DiscoverServices({
            "required_capabilities": capabilities
        })
        return [
            AgentEndpoint(**a) for a in result.get("agents", [])
        ]
        
    async def find_agents_by_role(self, role: int) -> List[AgentEndpoint]:
        result = await self.servicer.DiscoverServices({
            "role_filter": role
        })
        return [
            AgentEndpoint(**a) for a in result.get("agents", [])
        ]
        
    async def get_all_active_agents(self) -> List[AgentEndpoint]:
        result = await self.servicer.DiscoverServices({})
        return [
            AgentEndpoint(**a) for a in result.get("agents", [])
        ]


async def create_grpc_server(port: int = 50051) -> tuple:
    servicer = AgentCommunicationServicer()
    discovery_client = ServiceDiscoveryClient(servicer)
    
    return servicer, discovery_client


agent_servicer = None
discovery_client = None


async def initialize_grpc():
    global agent_servicer, discovery_client
    agent_servicer, discovery_client = await create_grpc_server()
    return agent_servicer, discovery_client
