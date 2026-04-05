# -*- coding: utf-8 -*-
"""
Agent Swarm 协作模式模块
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID
import time
import asyncio

from .config import SwarmConfig
from .models import SwarmTask, TaskResult
from .agent import Agent


class CollaborationMode(ABC):
    def __init__(self, config: Optional[SwarmConfig] = None):
        self.config = config or SwarmConfig()
    
    @abstractmethod
    async def execute(
        self, 
        task: SwarmTask, 
        agents: List[Agent]
    ) -> List[TaskResult]:
        pass
    
    @abstractmethod
    def aggregate(self, results: List[TaskResult]) -> Dict:
        pass


class ParallelMode(CollaborationMode):
    async def execute(
        self, 
        task: SwarmTask, 
        agents: List[Agent]
    ) -> List[TaskResult]:
        results = []
        
        tasks = []
        for agent in agents:
            if agent.can_execute(task):
                tasks.append(self._execute_agent(agent, task))
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            results = [r for r in results if isinstance(r, TaskResult)]
        
        return results
    
    async def _execute_agent(self, agent: Agent, task: SwarmTask) -> TaskResult:
        agent.assign_task(task)
        result = agent.execute(task)
        agent.complete_task(task.id, result.success)
        return result
    
    def aggregate(self, results: List[TaskResult]) -> Dict:
        if not results:
            return {"status": "no_results", "outputs": []}
        
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        outputs = [r.result for r in successful]
        
        if outputs:
            aggregated = {
                "status": "completed",
                "total_attempts": len(results),
                "successful": len(successful),
                "failed": len(failed),
                "outputs": outputs,
                "errors": [r.error for r in failed if r.error]
            }
        else:
            aggregated = {
                "status": "failed",
                "total_attempts": len(results),
                "successful": 0,
                "failed": len(failed),
                "errors": [r.error for r in failed if r.error]
            }
        
        return aggregated


class SequentialMode(CollaborationMode):
    async def execute(
        self, 
        task: SwarmTask, 
        agents: List[Agent]
    ) -> List[TaskResult]:
        results = []
        current_payload = task.payload.copy()
        
        for i, agent in enumerate(agents):
            if not agent.can_execute(task):
                continue
            
            step_task = SwarmTask(
                id=task.id,
                task_type=task.task_type,
                required_capabilities=task.required_capabilities,
                payload=current_payload
            )
            
            agent.assign_task(step_task)
            result = agent.execute(step_task)
            agent.complete_task(step_task.id, result.success)
            
            results.append(result)
            
            if result.success:
                current_payload.update(result.result)
            else:
                break
        
        return results
    
    def aggregate(self, results: List[TaskResult]) -> Dict:
        if not results:
            return {"status": "no_results", "outputs": []}
        
        final_result = results[-1] if results else None
        
        if final_result and final_result.success:
            return {
                "status": "completed",
                "steps": len(results),
                "final_output": final_result.result,
                "all_outputs": [r.result for r in results]
            }
        else:
            return {
                "status": "failed",
                "completed_steps": len([r for r in results if r.success]),
                "failed_at_step": len(results),
                "error": final_result.error if final_result else None
            }


class DebateMode(CollaborationMode):
    def __init__(self, config: Optional[SwarmConfig] = None, max_rounds: int = 3):
        super().__init__(config)
        self.max_rounds = max_rounds
    
    async def execute(
        self, 
        task: SwarmTask, 
        agents: List[Agent]
    ) -> List[TaskResult]:
        all_results = []
        
        for round_num in range(self.max_rounds):
            round_results = []
            
            for agent in agents:
                if not agent.can_execute(task):
                    continue
                
                agent.assign_task(task)
                result = agent.execute(task)
                agent.complete_task(task.id, result.success)
                round_results.append(result)
            
            all_results.extend(round_results)
            
            if self._check_consensus(round_results):
                break
        
        return all_results
    
    def _check_consensus(self, results: List[TaskResult]) -> bool:
        if len(results) < 2:
            return True
        
        successful = [r for r in results if r.success]
        if len(successful) < 2:
            return False
        
        outputs = [r.result for r in successful]
        
        if all(o.get("decision") == outputs[0].get("decision") for o in outputs):
            return True
        
        return False
    
    def aggregate(self, results: List[TaskResult]) -> Dict:
        if not results:
            return {"status": "no_results", "outputs": []}
        
        successful = [r for r in results if r.success]
        
        if not successful:
            return {
                "status": "failed",
                "total_attempts": len(results),
                "errors": [r.error for r in results if r.error]
            }
        
        outputs = [r.result for r in successful]
        
        votes: Dict[str, int] = {}
        for output in outputs:
            decision = output.get("decision", str(output))
            votes[decision] = votes.get(decision, 0) + 1
        
        if votes:
            consensus = max(votes.items(), key=lambda x: x[1])
            return {
                "status": "completed",
                "consensus": consensus[0],
                "vote_count": consensus[1],
                "total_votes": len(successful),
                "all_proposals": outputs,
                "vote_distribution": votes
            }
        
        return {
            "status": "no_consensus",
            "proposals": outputs
        }


class CollaborationManager:
    def __init__(self, config: Optional[SwarmConfig] = None):
        self.config = config or SwarmConfig()
        self.modes = {
            "parallel": ParallelMode(config),
            "sequential": SequentialMode(config),
            "debate": DebateMode(config)
        }
    
    def get_mode(self, mode_name: str) -> Optional[CollaborationMode]:
        return self.modes.get(mode_name)
    
    def select_mode(self, task: SwarmTask) -> CollaborationMode:
        mode_name = self.config.get_collaboration_mode(task.task_type)
        return self.modes.get(mode_name, self.modes["parallel"])
    
    async def execute_task(
        self, 
        task: SwarmTask, 
        agents: List[Agent],
        mode: Optional[str] = None
    ) -> Tuple[Dict, List[TaskResult]]:
        if mode:
            collaboration_mode = self.modes.get(mode)
        else:
            collaboration_mode = self.select_mode(task)
        
        if not collaboration_mode:
            collaboration_mode = self.modes["parallel"]
        
        results = await collaboration_mode.execute(task, agents)
        aggregated = collaboration_mode.aggregate(results)
        
        return aggregated, results
    
    def register_mode(self, name: str, mode: CollaborationMode):
        self.modes[name] = mode
    
    def get_available_modes(self) -> List[str]:
        return list(self.modes.keys())
