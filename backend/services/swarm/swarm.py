# -*- coding: utf-8 -*-
"""
Agent Swarm 编排器模块
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4
import time
import asyncio

from .config import SwarmConfig, get_default_config
from .models import SwarmTask, SwarmSession, TaskResult
from .agent import Agent
from .task_board import TaskBoard
from .bidding import BiddingEngine
from .p2p_network import P2PNetwork, HeartbeatMonitor, TaskMigrator
from .collaboration import CollaborationManager


class SwarmOrchestrator:
    def __init__(self, config: Optional[SwarmConfig] = None):
        self.config = config or get_default_config()
        self.task_board = TaskBoard(self.config)
        self.bidding_engine = BiddingEngine(self.config)
        self.p2p_network = P2PNetwork(self.config)
        self.heartbeat_monitor = HeartbeatMonitor(self.config)
        self.task_migrator = TaskMigrator(self.config)
        self.collaboration_manager = CollaborationManager(self.config)
        
        self.agents: Dict[UUID, Agent] = {}
        self.sessions: Dict[UUID, SwarmSession] = {}
        self._running = False
    
    def register_agent(self, agent: Agent) -> UUID:
        self.agents[agent.id] = agent
        self.p2p_network.register_agent(agent)
        return agent.id
    
    def unregister_agent(self, agent_id: UUID) -> bool:
        if agent_id in self.agents:
            del self.agents[agent_id]
            self.p2p_network.unregister_agent(agent_id)
            return True
        return False
    
    def get_agent(self, agent_id: UUID) -> Optional[Agent]:
        return self.agents.get(agent_id)
    
    def get_all_agents(self) -> List[Agent]:
        return list(self.agents.values())
    
    def create_session(
        self, 
        user_id: Optional[UUID] = None,
        collaboration_mode: str = "parallel"
    ) -> SwarmSession:
        session = SwarmSession(
            id=uuid4(),
            user_id=user_id,
            collaboration_mode=collaboration_mode
        )
        self.sessions[session.id] = session
        return session
    
    def submit_task(self, task: SwarmTask, session_id: Optional[UUID] = None) -> UUID:
        if session_id:
            task.session_id = session_id
            session = self.sessions.get(session_id)
            if session:
                session.total_tasks += 1
        
        task.collaboration_mode = self.config.get_collaboration_mode(task.task_type)
        
        task_id = self.task_board.publish(task)
        
        self._process_task(task_id)
        
        return task_id
    
    def _process_task(self, task_id: UUID):
        agents = list(self.agents.values())
        
        winner_agent, bids = self.bidding_engine.run_bidding_process(
            self.task_board.get_task(task_id),
            agents
        )
        
        if winner_agent:
            from .task_board import Bid
            from .models import BidResult
            
            winner_bid = next(
                (b for b in bids if b.agent_id == winner_agent.id), None
            )
            bid = Bid(
                agent_id=winner_agent.id,
                task_id=task_id,
                score=winner_bid.score if winner_bid else 0.0,
                estimated_time=winner_bid.estimated_time if winner_bid else 0.0,
                confidence=winner_bid.confidence if winner_bid else 0.5
            )
            self.task_board.submit_bid(bid)
            self.task_board.select_winner(task_id)
    
    async def execute_task(self, task_id: UUID) -> TaskResult:
        task = self.task_board.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        if task.status != "assigned":
            raise ValueError(f"Task {task_id} is not assigned")
        
        agent = self.agents.get(task.assigned_agent_id)
        if not agent:
            raise ValueError(f"Agent {task.assigned_agent_id} not found")
        
        self.task_board.update_status(task_id, "running")
        
        result = agent.execute(task)
        
        status = "completed" if result.success else "failed"
        self.task_board.update_status(task_id, status, result.result)
        
        agent.complete_task(task_id, result.success)
        
        if task.session_id:
            session = self.sessions.get(task.session_id)
            if session:
                session.completed_tasks += 1
                session.total_latency_ms += result.latency_ms
        
        return result
    
    async def run_collaboration(
        self, 
        task: SwarmTask, 
        agents: List[Agent]
    ) -> Dict:
        mode = self.collaboration_manager.get_mode(task.collaboration_mode)
        
        results = await mode.execute(task, agents)
        
        return mode.aggregate(results)
    
    def start_heartbeat(self):
        self._running = True
        asyncio.create_task(self._heartbeat_loop())
    
    def stop_heartbeat(self):
        self._running = False
    
    async def _heartbeat_loop(self):
        while self._running:
            await asyncio.sleep(self.config.heartbeat_interval_seconds)
            
            for agent in self.agents.values():
                heartbeat = agent.heartbeat()
                self.heartbeat_monitor.record_heartbeat(
                    agent.id,
                    heartbeat["load"],
                    heartbeat["active_tasks"],
                    heartbeat["status_info"]
                )
            
            failures = self.heartbeat_monitor.detect_failures()
            
            for failed_id in failures:
                self._handle_agent_failure(failed_id)
    
    def _handle_agent_failure(self, agent_id: UUID):
        assigned_tasks = self.task_board.get_assigned_tasks(agent_id)
        
        for task in assigned_tasks:
            available_agents = [
                a for a in self.agents.values() 
                if a.id != agent_id and self.heartbeat_monitor.is_available(a.id)
            ]
            
            if available_agents:
                replacement = self.task_migrator.find_replacement(
                    self.agents[agent_id],
                    available_agents
                )
                
                if replacement:
                    self.task_migrator.migrate(
                        task.id,
                        self.agents[agent_id],
                        replacement
                    )
    
    def get_statistics(self) -> Dict:
        return {
            "total_agents": len(self.agents),
            "total_sessions": len(self.sessions),
            "task_board": self.task_board.get_statistics(),
            "heartbeat_status": {
                "healthy": len([a for a in self.agents if self.heartbeat_monitor.is_available(a.id)]),
                "failed": len(self.heartbeat_monitor.detect_failures())
            }
        }
    
    def get_session_statistics(self, session_id: UUID) -> Optional[Dict]:
        session = self.sessions.get(session_id)
        if not session:
            return None
        
        return {
            "session_id": str(session_id),
            "total_tasks": session.total_tasks,
            "completed_tasks": session.completed_tasks,
            "failed_tasks": session.failed_tasks,
            "total_latency_ms": session.total_latency_ms,
            "duration_seconds": (datetime.now() - session.started_at).total_seconds() if session.started_at else 0,
            "status": "completed" if session.ended_at else "running"
        }
    
    def reset(self):
        self.agents.clear()
        self.sessions.clear()
        self.task_board = TaskBoard(self.config)
        self.p2p_network = P2PNetwork(self.config)
        self.heartbeat_monitor = HeartbeatMonitor(self.config)
        self._running = False
