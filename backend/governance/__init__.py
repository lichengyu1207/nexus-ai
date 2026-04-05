"""
三省六部制治理模块
实现基于中国古代官制的AI智能体集群系统
"""
from .base import GovernanceAgent, AgentLevel, Department, AgentStatus
from .scheduler import ThreeDepartmentsScheduler
from .market import AgentMarket, agent_market
from .salary import SalaryManager, salary_manager

__all__ = [
    'GovernanceAgent',
    'AgentLevel',
    'Department',
    'AgentStatus',
    'ThreeDepartmentsScheduler',
    'AgentMarket',
    'agent_market',
    'SalaryManager',
    'salary_manager',
]
