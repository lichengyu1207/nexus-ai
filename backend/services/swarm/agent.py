# -*- coding: utf-8 -*-
"""
Agent Swarm 智能体模块
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from uuid import UUID, uuid4
import time

from .config import SwarmConfig
from .models import SwarmAgent, SwarmTask, SwarmBid, BidResult, TaskResult


class Agent(ABC):
    def __init__(self, name: str, capabilities: List[str], config: Optional[SwarmConfig] = None):
        self.id = uuid4()
        self.name = name
        self.capabilities = capabilities
        self.config = config or SwarmConfig()
        self.load = 0.0
        self.max_concurrent_tasks = 3
        self.neighbors: List[UUID] = []
        self.current_tasks: List[UUID] = []
        self.history_success_rate: float = 0.5
        self._executor: Optional[Callable] = None
    
    def bid(self, task: SwarmTask) -> BidResult:
        capability_match = self._evaluate_capability(task.required_capabilities)
        
        if capability_match == 0:
            return BidResult(
                agent_id=self.id,
                score=float('inf'),
                capability_match=0,
                load_factor=1.0,
                history_factor=0,
                estimated_time=0,
                confidence=0
            )
        
        load_factor = self.load / self.max_concurrent_tasks if self.max_concurrent_tasks > 0 else 1.0
        
        weights = self.config.bid_score_weights
        score = (
            weights.get("load", 0.4) * load_factor +
            weights.get("capability_match", 0.4) * (1 - capability_match) +
            weights.get("history_success", 0.2) * (1 - self.history_success_rate)
        )
        
        estimated_time = self._estimate_time(task)
        confidence = capability_match * (1 - load_factor) * self.history_success_rate
        
        return BidResult(
            agent_id=self.id,
            score=score,
            capability_match=capability_match,
            load_factor=load_factor,
            history_factor=self.history_success_rate,
            estimated_time=estimated_time,
            confidence=confidence
        )
    
    def _evaluate_capability(self, required_capabilities: List[str]) -> float:
        if not required_capabilities:
            return 0.5
        
        matched = sum(1 for cap in required_capabilities if cap in self.capabilities)
        return matched / len(required_capabilities)
    
    def _estimate_time(self, task: SwarmTask) -> float:
        base_time = 1.0
        complexity_factor = len(task.required_capabilities) * 0.5
        load_factor = self.load * 0.3
        return base_time + complexity_factor + load_factor
    
    def can_execute(self, task: SwarmTask) -> bool:
        if len(self.current_tasks) >= self.max_concurrent_tasks:
            return False
        
        required = set(task.required_capabilities)
        available = set(self.capabilities)
        return len(required & available) > 0 or len(required) == 0
    
    def assign_task(self, task: SwarmTask) -> bool:
        if not self.can_execute(task):
            return False
        
        self.current_tasks.append(task.id)
        self.load = len(self.current_tasks) / self.max_concurrent_tasks
        return True
    
    @abstractmethod
    def execute(self, task: SwarmTask) -> TaskResult:
        pass
    
    def complete_task(self, task_id: UUID, success: bool):
        if task_id in self.current_tasks:
            self.current_tasks.remove(task_id)
            self.load = len(self.current_tasks) / self.max_concurrent_tasks
            
            if success:
                self.history_success_rate = min(1.0, self.history_success_rate + 0.05)
            else:
                self.history_success_rate = max(0.0, self.history_success_rate - 0.1)
    
    def decompose(self, task: SwarmTask) -> List[SwarmTask]:
        return []
    
    def heartbeat(self) -> Dict:
        return {
            "agent_id": str(self.id),
            "name": self.name,
            "load": self.load,
            "active_tasks": len(self.current_tasks),
            "status": "busy" if self.load > 0.5 else "idle",
            "timestamp": datetime.now().isoformat()
        }
    
    def migrate_task(self, task_id: UUID, target_agent: 'Agent') -> bool:
        if task_id not in self.current_tasks:
            return False
        
        self.current_tasks.remove(task_id)
        self.load = len(self.current_tasks) / self.max_concurrent_tasks
        return True
    
    def update_neighbors(self, neighbors: List[UUID]):
        self.neighbors = neighbors
    
    def set_executor(self, executor: Callable):
        self._executor = executor


class SwarmAgentBase(Agent):
    def __init__(
        self, 
        name: str, 
        capabilities: List[str],
        role: str = "worker",
        department: str = "",
        skill_scores: Optional[Dict[str, float]] = None,
        config: Optional[SwarmConfig] = None
    ):
        super().__init__(name, capabilities, config)
        self.role = role
        self.department = department
        self.skill_scores = skill_scores or {}
    
    def _evaluate_capability(self, required_capabilities: List[str]) -> float:
        if not required_capabilities:
            return 0.5
        
        total_score = 0.0
        for cap in required_capabilities:
            if cap in self.capabilities:
                skill_score = self.skill_scores.get(cap, 0.5)
                total_score += skill_score
            else:
                total_score += 0.1
        
        return total_score / len(required_capabilities)
    
    def execute(self, task: SwarmTask) -> TaskResult:
        start_time = time.time()
        
        try:
            if self._executor:
                result = self._executor(task)
            else:
                result = self._default_execute(task)
            
            latency_ms = (time.time() - start_time) * 1000
            
            return TaskResult(
                task_id=task.id,
                agent_id=self.id,
                success=True,
                result=result,
                latency_ms=latency_ms
            )
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return TaskResult(
                task_id=task.id,
                agent_id=self.id,
                success=False,
                result={},
                latency_ms=latency_ms,
                error=str(e)
            )
    
    def _default_execute(self, task: SwarmTask) -> Dict:
        return {
            "status": "completed",
            "agent": self.name,
            "task_type": task.task_type,
            "message": f"Task {task.id} executed by {self.name}"
        }


class ThreeProvinceAgent(SwarmAgentBase):
    def __init__(
        self, 
        name: str, 
        province_type: str,
        capabilities: List[str],
        skill_scores: Optional[Dict[str, float]] = None,
        config: Optional[SwarmConfig] = None
    ):
        super().__init__(
            name=name,
            capabilities=capabilities,
            role="province",
            department=province_type,
            skill_scores=skill_scores,
            config=config
        )
        self.province_type = province_type
        self.subordinates: Dict[str, Agent] = {}
    
    def add_subordinate(self, agent: Agent):
        self.subordinates[agent.name] = agent
    
    def coordinate(self, task: SwarmTask) -> List[TaskResult]:
        results = []
        
        for name, agent in self.subordinates.items():
            if agent.can_execute(task):
                result = agent.execute(task)
                results.append(result)
        
        return results
    
    def aggregate(self, results: List[TaskResult]) -> Dict:
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        return {
            "total": len(results),
            "successful": len(successful),
            "failed": len(failed),
            "aggregated_result": {
                "outputs": [r.result for r in successful],
                "errors": [r.error for r in failed if r.error]
            }
        }
    
    def execute(self, task: SwarmTask) -> TaskResult:
        start_time = time.time()
        
        if self.province_type == "decision":
            subtasks = self.decompose(task)
            if subtasks:
                results = self.coordinate(task)
                aggregated = self.aggregate(results)
                latency_ms = (time.time() - start_time) * 1000
                return TaskResult(
                    task_id=task.id,
                    agent_id=self.id,
                    success=True,
                    result=aggregated,
                    latency_ms=latency_ms
                )
        
        return super().execute(task)


class SixMinistryAgent(SwarmAgentBase):
    def __init__(
        self, 
        name: str, 
        ministry_type: str,
        capabilities: List[str],
        specialized_skills: Optional[List[str]] = None,
        skill_scores: Optional[Dict[str, float]] = None,
        config: Optional[SwarmConfig] = None
    ):
        super().__init__(
            name=name,
            capabilities=capabilities,
            role="ministry",
            department=ministry_type,
            skill_scores=skill_scores,
            config=config
        )
        self.ministry_type = ministry_type
        self.specialized_skills = specialized_skills or []
    
    def process_specialty(self, task: SwarmTask) -> TaskResult:
        start_time = time.time()
        
        specialty_match = any(
            skill in task.required_capabilities 
            for skill in self.specialized_skills
        )
        
        if specialty_match:
            result = self._specialty_execute(task)
        else:
            result = self._default_execute(task)
        
        latency_ms = (time.time() - start_time) * 1000
        
        return TaskResult(
            task_id=task.id,
            agent_id=self.id,
            success=True,
            result=result,
            latency_ms=latency_ms
        )
    
    def _specialty_execute(self, task: SwarmTask) -> Dict:
        return {
            "status": "specialty_completed",
            "agent": self.name,
            "ministry": self.ministry_type,
            "task_type": task.task_type,
            "specialty_used": True
        }
    
    def execute(self, task: SwarmTask) -> TaskResult:
        return self.process_specialty(task)
