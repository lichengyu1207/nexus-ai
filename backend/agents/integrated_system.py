"""
集成系统
将蜂群协同的多智能体自组织系统与基于分组模型路由的成本优化系统集成
"""

import os
import json
import logging
import time
from typing import Dict, Any, List, Optional, Tuple

from backend.agents.swarm_agent import SwarmSystem, Task
from backend.agents.model_router import process_request, get_router_status
from backend.agents.agent_coordinator import coordinate_task
from backend.agents.cost_monitor import get_daily_cost

logger = logging.getLogger(__name__)


class IntegratedSystem:
    """集成系统"""
    
    def __init__(self):
        self.swarm_system = SwarmSystem(num_agents=10)
        self.swarm_system.start_all_agents()
        logger.info("集成系统初始化完成")
    
    def process_user_request(self, query: str) -> Dict[str, Any]:
        """处理用户请求
        
        Args:
            query: 用户查询
            
        Returns:
            处理结果
        """
        # 步骤1: 使用蜂群系统分析请求
        logger.info(f"处理用户请求: {query}")
        
        # 步骤2: 创建任务并广播
        task = self.swarm_system.create_task(
            task_type="data_collection",
            content=query,
            location=(50.0, 50.0)
        )
        
        # 步骤3: 广播任务给蜂群智能体
        start_agent_id = "agent_0"
        self.swarm_system.broadcast_task(task, start_agent_id, max_hops=3)
        
        # 步骤4: 模拟蜂群智能体执行任务
        self.swarm_system.simulate_task_execution(task)
        
        # 步骤5: 使用基于分组模型路由的成本优化系统处理请求
        model_router_result = process_request(query)
        
        # 步骤6: 与三省六部智能体协同
        coord_result = coordinate_task("data_collection", {"query": query})
        
        # 步骤7: 整合结果
        result = {
            "query": query,
            "swarm_task_id": task.id,
            "model_router_result": model_router_result,
            "agent_coordinator_result": coord_result,
            "current_daily_cost": get_daily_cost()
        }
        
        return result
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态
        
        Returns:
            系统状态
        """
        # 获取蜂群系统状态
        swarm_status = {
            "num_agents": len(self.swarm_system.agents),
            "agent_states": [
                {
                    "id": state.id,
                    "position": (state.x, state.y),
                    "status": state.status,
                    "capabilities": state.capabilities
                }
                for state in self.swarm_system.get_all_agent_states()
            ]
        }
        
        # 获取模型路由系统状态
        model_router_status = get_router_status()
        
        # 获取成本状态
        cost_status = {
            "daily_cost": get_daily_cost()
        }
        
        return {
            "swarm_system": swarm_status,
            "model_router": model_router_status,
            "cost": cost_status
        }
    
    def simulate_agent_failure(self, agent_id: str):
        """模拟智能体故障
        
        Args:
            agent_id: 智能体ID
        """
        self.swarm_system.simulate_agent_failure(agent_id)
    
    def optimize_system(self):
        """优化系统"""
        # 模拟智能体向信息素位置移动
        for agent_id, agent in self.swarm_system.agents.items():
            agent.move_towards_pheromone()
        
        logger.info("系统优化完成")
    
    def shutdown(self):
        """关闭系统"""
        self.swarm_system.stop_all_agents()
        logger.info("集成系统已关闭")


# 全局集成系统实例
integrated_system: Optional[IntegratedSystem] = None


def get_integrated_system() -> IntegratedSystem:
    """获取集成系统实例"""
    global integrated_system
    if integrated_system is None:
        integrated_system = IntegratedSystem()
    return integrated_system


def process_integrated_request(query: str) -> Dict[str, Any]:
    """处理集成请求"""
    system = get_integrated_system()
    return system.process_user_request(query)


def get_integrated_status() -> Dict[str, Any]:
    """获取集成系统状态"""
    system = get_integrated_system()
    return system.get_system_status()


def simulate_integrated_failure(agent_id: str):
    """模拟智能体故障"""
    system = get_integrated_system()
    system.simulate_agent_failure(agent_id)


def optimize_integrated_system():
    """优化集成系统"""
    system = get_integrated_system()
    system.optimize_system()


def shutdown_integrated_system():
    """关闭集成系统"""
    system = get_integrated_system()
    system.shutdown()
