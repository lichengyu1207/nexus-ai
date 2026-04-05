"""
战术执行器
Tactical Executor

执行选定的战术，调度各智能体协同行动
"""

import asyncio
import time
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from collections import defaultdict, deque
import structlog

logger = structlog.get_logger()


class ExecutionStatus(Enum):
    PENDING = "pending"
    PREPARING = "preparing"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ExecutionResult:
    execution_id: str
    tactic_id: str
    status: ExecutionStatus
    started_at: datetime
    completed_at: Optional[datetime]
    target_identity: str
    agents_involved: List[str]
    actions_taken: List[Dict]
    effectiveness_score: float
    resource_usage: Dict
    errors: List[str]
    metrics: Dict
    
    def to_dict(self) -> Dict:
        return {
            "execution_id": self.execution_id,
            "tactic_id": self.tactic_id,
            "status": self.status.value,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "target_identity": self.target_identity,
            "agents_involved": self.agents_involved,
            "actions_taken": self.actions_taken,
            "effectiveness_score": self.effectiveness_score,
            "resource_usage": self.resource_usage,
            "errors": self.errors,
            "metrics": self.metrics
        }


class AgentPool:
    def __init__(self):
        self.available: Dict[str, Dict] = {}
        self.busy: Dict[str, str] = {}
        
    def register(self, agent_id: str, agent_type: str, capabilities: List[str]):
        self.available[agent_id] = {
            "agent_id": agent_id,
            "agent_type": agent_type,
            "capabilities": capabilities,
            "registered_at": datetime.now().isoformat()
        }
        
    def acquire(self, agent_id: str, execution_id: str) -> bool:
        if agent_id not in self.available:
            return False
            
        agent = self.available.pop(agent_id)
        self.busy[agent_id] = execution_id
        return True
        
    def release(self, agent_id: str) -> bool:
        if agent_id not in self.busy:
            return False
            
        self.available[agent_id] = {
            "agent_id": agent_id,
            "released_at": datetime.now().isoformat()
        }
        del self.busy[agent_id]
        return True
        
    def get_available_by_type(self, agent_type: str) -> List[str]:
        return [
            aid for aid, info in self.available.items()
            if info.get("agent_type") == agent_type
        ]


class TacticalExecutor:
    def __init__(
        self,
        executor_id: str = "tactical_executor_001",
        communication_bus: Optional[Any] = None,
        tactical_library: Optional[Any] = None
    ):
        self.executor_id = executor_id
        self.communication_bus = communication_bus
        self.tactical_library = tactical_library
        
        self.agent_pool = AgentPool()
        self.executions: Dict[str, ExecutionResult] = {}
        self.active_executions: Dict[str, str] = {}
        self.execution_history: deque = deque(maxlen=500)
        
        self.agent_clients: Dict[str, Any] = {}
        
        self.stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "agents_deployed": 0,
            "avg_execution_time_ms": 0.0
        }
        
        self._running = False
        self._task: Optional[asyncio.Task] = None
        
    async def start(self):
        self._running = True
        self._task = asyncio.create_task(self._execution_monitor_loop())
        logger.info(f"TacticalExecutor {self.executor_id} started")
        
    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info(f"TacticalExecutor {self.executor_id} stopped")
        
    async def _execution_monitor_loop(self):
        while self._running:
            try:
                await self._check_execution_progress()
                await asyncio.sleep(5)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in execution monitor: {e}")
                await asyncio.sleep(10)
                
    async def _check_execution_progress(self):
        for execution_id in list(self.active_executions.keys()):
            execution = self.executions.get(execution_id)
            if execution:
                progress = await self._evaluate_progress(execution)
                if progress >= 1.0:
                    await self.complete_execution(execution_id, success=True)
                    
    async def _evaluate_progress(self, execution: ExecutionResult) -> float:
        if not execution.actions_taken:
            return 0.0
            
        completed_actions = sum(
            1 for a in execution.actions_taken
            if a.get("status") == "completed"
        )
        
        return completed_actions / len(execution.actions_taken) if execution.actions_taken else 0.0
        
    def register_agent(self, agent_id: str, agent_type: str, capabilities: List[str]):
        self.agent_pool.register(agent_id, agent_type, capabilities)
        logger.debug(f"Registered agent {agent_id} of type {agent_type}")
        
    def register_agent_client(self, agent_type: str, client: Any):
        self.agent_clients[agent_type] = client
        
    async def execute_tactic(
        self,
        tactic_id: str,
        target_identity: str,
        custom_params: Optional[Dict] = None
    ) -> ExecutionResult:
        start_time = time.time()
        
        tactic = await self._get_tactic(tactic_id)
        if not tactic:
            return self._create_failed_result(tactic_id, target_identity, "Tactic not found")
            
        required_agents = tactic.get("required_agents", {})
        assigned_agents = await self._assign_agents(required_agents)
        
        if len(assigned_agents) < sum(required_agents.values()):
            return self._create_failed_result(
                tactic_id, target_identity, "Not enough agents available"
            )
            
        execution_id = self._generate_execution_id()
        
        execution = ExecutionResult(
            execution_id=execution_id,
            tactic_id=tactic_id,
            status=ExecutionStatus.PREPARING,
            started_at=datetime.now(),
            completed_at=None,
            target_identity=target_identity,
            agents_involved=list(assigned_agents.keys()),
            actions_taken=[],
            effectiveness_score=0.0,
            resource_usage={},
            errors=[],
            metrics={}
        )
        
        self.executions[execution_id] = execution
        self.active_executions[execution_id] = target_identity
        
        params = {**tactic.get("parameters", {}), **(custom_params or {})}
        
        try:
            execution.status = ExecutionStatus.RUNNING
            
            actions = await self._execute_actions(
                execution,
                tactic,
                params,
                assigned_agents
            )
            
            execution.actions_taken = actions
            
            execution.effectiveness_score = await self._calculate_effectiveness(execution)
            
            execution.status = ExecutionStatus.COMPLETED
            execution.completed_at = datetime.now()
            
            self.stats["successful_executions"] += 1
            
            if self.tactical_library:
                await self.tactical_library.update_tactic_usage(
                    tactic_id,
                    execution.effectiveness_score > 0.5
                )
                
        except Exception as e:
            execution.status = ExecutionStatus.FAILED
            execution.errors.append(str(e))
            self.stats["failed_executions"] += 1
            
        finally:
            for agent_id in assigned_agents:
                self.agent_pool.release(agent_id)
                
        self.execution_history.append(execution.to_dict())
        self.active_executions.pop(execution_id, None)
        
        duration = (time.time() - start_time) * 1000
        self._update_avg_execution_time(duration)
        self.stats["total_executions"] += 1
        self.stats["agents_deployed"] += len(assigned_agents)
        
        if self.communication_bus:
            await self.communication_bus.publish(
                "tactic_executed",
                execution.to_dict()
            )
            
        logger.info(
            f"Executed tactic {tactic_id}: status={execution.status.value}, "
            f"effectiveness={execution.effectiveness_score:.2f}"
        )
        
        return execution
        
    async def _get_tactic(self, tactic_id: str) -> Optional[Dict]:
        if self.tactical_library:
            return await self.tactical_library.get_tactic(tactic_id)
        return None
        
    async def _assign_agents(
        self,
        required: Dict[str, int]
    ) -> Dict[str, str]:
        assigned = {}
        
        for agent_type, count in required.items():
            available = self.agent_pool.get_available_by_type(agent_type)
            
            for agent_id in available[:count]:
                execution_id = f"exec_{int(time.time())}"
                if self.agent_pool.acquire(agent_id, execution_id):
                    assigned[agent_id] = agent_type
                    
        return assigned
        
    async def _execute_actions(
        self,
        execution: ExecutionResult,
        tactic: Dict,
        params: Dict,
        assigned_agents: Dict[str, str]
    ) -> List[Dict]:
        actions = []
        
        category = tactic.get("category", "")
        
        if category == "lure":
            actions = await self._execute_lure_tactic(execution, params, assigned_agents)
        elif category == "consume":
            actions = await self._execute_consume_tactic(execution, params, assigned_agents)
        elif category == "divert":
            actions = await self._execute_divert_tactic(execution, params, assigned_agents)
        elif category == "encircle":
            actions = await self._execute_encircle_tactic(execution, params, assigned_agents)
        elif category == "blockade":
            actions = await self._execute_blockade_tactic(execution, params, assigned_agents)
        elif category == "counter":
            actions = await self._execute_counter_tactic(execution, params, assigned_agents)
        elif category == "deception":
            actions = await self._execute_deception_tactic(execution, params, assigned_agents)
        else:
            actions = await self._execute_generic_tactic(execution, params, assigned_agents)
            
        return actions
        
    async def _execute_lure_tactic(
        self,
        execution: ExecutionResult,
        params: Dict,
        agents: Dict[str, str]
    ) -> List[Dict]:
        actions = []
        
        honeypot_count = params.get("honeypot_count", 2)
        
        for agent_id, agent_type in agents.items():
            if agent_type == "honeypot" and len([a for a in actions if a["type"] == "honeypot"]) < honeypot_count:
                action = {
                    "agent_id": agent_id,
                    "type": "create_honeypot",
                    "status": "completed",
                    "timestamp": datetime.now().isoformat()
                }
                actions.append(action)
                
        return actions
        
    async def _execute_consume_tactic(
        self,
        execution: ExecutionResult,
        params: Dict,
        agents: Dict[str, str]
    ) -> List[Dict]:
        actions = []
        
        for agent_id, agent_type in agents.items():
            if agent_type == "counter_strike":
                action = {
                    "agent_id": agent_id,
                    "type": "rate_limit",
                    "params": {"rate": params.get("rate_limit", 1)},
                    "status": "completed",
                    "timestamp": datetime.now().isoformat()
                }
                actions.append(action)
                
        return actions
        
    async def _execute_divert_tactic(
        self,
        execution: ExecutionResult,
        params: Dict,
        agents: Dict[str, str]
    ) -> List[Dict]:
        actions = []
        
        for agent_id, agent_type in agents.items():
            if agent_type == "honeypot":
                action = {
                    "agent_id": agent_id,
                    "type": "create_decoy",
                    "status": "completed",
                    "timestamp": datetime.now().isoformat()
                }
                actions.append(action)
            elif agent_type == "network_morph":
                action = {
                    "agent_id": agent_id,
                    "type": "ip_shift",
                    "status": "completed",
                    "timestamp": datetime.now().isoformat()
                }
                actions.append(action)
                
        return actions
        
    async def _execute_encircle_tactic(
        self,
        execution: ExecutionResult,
        params: Dict,
        agents: Dict[str, str]
    ) -> List[Dict]:
        actions = []
        
        for agent_id, agent_type in agents.items():
            action = {
                "agent_id": agent_id,
                "type": "position",
                "status": "completed",
                "timestamp": datetime.now().isoformat()
            }
            actions.append(action)
            
        return actions
        
    async def _execute_blockade_tactic(
        self,
        execution: ExecutionResult,
        params: Dict,
        agents: Dict[str, str]
    ) -> List[Dict]:
        actions = []
        
        for agent_id, agent_type in agents.items():
            action = {
                "agent_id": agent_id,
                "type": "block",
                "status": "completed",
                "timestamp": datetime.now().isoformat()
            }
            actions.append(action)
            
        return actions
        
    async def _execute_counter_tactic(
        self,
        execution: ExecutionResult,
        params: Dict,
        agents: Dict[str, str]
    ) -> List[Dict]:
        actions = []
        
        for agent_id, agent_type in agents.items():
            action = {
                "agent_id": agent_id,
                "type": "counter_strike",
                "params": params.get("counter_actions", []),
                "status": "completed",
                "timestamp": datetime.now().isoformat()
            }
            actions.append(action)
            
        return actions
        
    async def _execute_deception_tactic(
        self,
        execution: ExecutionResult,
        params: Dict,
        agents: Dict[str, str]
    ) -> List[Dict]:
        actions = []
        
        for agent_id, agent_type in agents.items():
            if agent_type == "network_morph":
                action = {
                    "agent_id": agent_id,
                    "type": "morph_network",
                    "status": "completed",
                    "timestamp": datetime.now().isoformat()
                }
                actions.append(action)
                
        return actions
        
    async def _execute_generic_tactic(
        self,
        execution: ExecutionResult,
        params: Dict,
        agents: Dict[str, str]
    ) -> List[Dict]:
        actions = []
        
        for agent_id in agents:
            action = {
                "agent_id": agent_id,
                "type": "execute",
                "status": "completed",
                "timestamp": datetime.now().isoformat()
            }
            actions.append(action)
            
        return actions
        
    async def _calculate_effectiveness(self, execution: ExecutionResult) -> float:
        if not execution.actions_taken:
            return 0.0
            
        completed = sum(
            1 for a in execution.actions_taken
            if a.get("status") == "completed"
        )
        
        return completed / len(execution.actions_taken)
        
    async def complete_execution(self, execution_id: str, success: bool) -> bool:
        execution = self.executions.get(execution_id)
        if not execution:
            return False
            
        execution.status = ExecutionStatus.COMPLETED if success else ExecutionStatus.FAILED
        execution.completed_at = datetime.now()
        
        for agent_id in execution.agents_involved:
            self.agent_pool.release(agent_id)
            
        self.active_executions.pop(execution_id, None)
        self.execution_history.append(execution.to_dict())
        
        return True
        
    async def cancel_execution(self, execution_id: str) -> bool:
        execution = self.executions.get(execution_id)
        if not execution:
            return False
            
        execution.status = ExecutionStatus.CANCELLED
        execution.completed_at = datetime.now()
        
        for agent_id in execution.agents_involved:
            self.agent_pool.release(agent_id)
            
        self.active_executions.pop(execution_id, None)
        
        return True
        
    def _create_failed_result(
        self,
        tactic_id: str,
        target_identity: str,
        error: str
    ) -> ExecutionResult:
        return ExecutionResult(
            execution_id=self._generate_execution_id(),
            tactic_id=tactic_id,
            status=ExecutionStatus.FAILED,
            started_at=datetime.now(),
            completed_at=datetime.now(),
            target_identity=target_identity,
            agents_involved=[],
            actions_taken=[],
            effectiveness_score=0.0,
            resource_usage={},
            errors=[error],
            metrics={}
        )
        
    async def get_execution(self, execution_id: str) -> Optional[Dict]:
        execution = self.executions.get(execution_id)
        return execution.to_dict() if execution else None
        
    async def get_active_executions(self) -> List[Dict]:
        return [
            self.executions[eid].to_dict()
            for eid in self.active_executions.keys()
            if eid in self.executions
        ]
        
    async def get_execution_history(self, limit: int = 50) -> List[Dict]:
        return list(self.execution_history)[-limit:]
        
    def _generate_execution_id(self) -> str:
        return f"exec_{int(time.time() * 1000)}_{hashlib.md5(str(time.time()).encode()).hexdigest()[:6]}"
        
    def _update_avg_execution_time(self, duration: float):
        current = self.stats["avg_execution_time_ms"]
        count = self.stats["total_executions"]
        self.stats["avg_execution_time_ms"] = (current * (count - 1) + duration) / count
        
    def get_stats(self) -> Dict:
        return {
            **self.stats,
            "active_executions": len(self.active_executions),
            "available_agents": len(self.agent_pool.available)
        }
