# -*- coding: utf-8 -*-
"""
Agent Swarm 可扩展多智能体协作系统
"""
from .config import SwarmConfig, get_default_config
from .models import (
    SwarmAgent, SwarmTask, SwarmBid, SwarmSession,
    SwarmTaskLog, SwarmHeartbeat, BidResult, TaskResult
)
from .agent import Agent, SwarmAgentBase, ThreeProvinceAgent, SixMinistryAgent
from .task_board import TaskBoard, Task, Bid
from .bidding import BiddingEngine, CapabilityMatcher, LoadBalancer
from .p2p_network import P2PNetwork, HeartbeatMonitor, TaskMigrator
from .collaboration import CollaborationManager, ParallelMode, SequentialMode, DebateMode
from .swarm import SwarmOrchestrator

__all__ = [
    'SwarmConfig', 'get_default_config',
    'SwarmAgent', 'SwarmTask', 'SwarmBid', 'SwarmSession',
    'SwarmTaskLog', 'SwarmHeartbeat', 'BidResult', 'TaskResult',
    'Agent', 'SwarmAgentBase', 'ThreeProvinceAgent', 'SixMinistryAgent',
    'TaskBoard', 'Task', 'Bid',
    'BiddingEngine', 'CapabilityMatcher', 'LoadBalancer',
    'P2PNetwork', 'HeartbeatMonitor', 'TaskMigrator',
    'CollaborationManager', 'ParallelMode', 'SequentialMode', 'DebateMode',
    'SwarmOrchestrator'
]
