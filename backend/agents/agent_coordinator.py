"""
智能体协同模块
与三省六部智能体集群协同工作
"""

import os
import json
import logging
import time
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class AgentCoordinator:
    """智能体协调器"""
    
    def __init__(self):
        self.agents = self._load_agents()
        self.agent_status = {agent: "idle" for agent in self.agents}
    
    def _load_agents(self) -> Dict[str, Dict[str, Any]]:
        """加载智能体信息"""
        # 三省六部智能体集群
        agents = {
            "zhongshu": {  # 中书省
                "name": "中书省",
                "type": "decision",
                "endpoint": "http://localhost:8002/api/agents/zhongshu",
                "capabilities": ["决策", "协调", "调度"]
            },
            "menxia": {  # 门下省
                "name": "门下省",
                "type": "review",
                "endpoint": "http://localhost:8002/api/agents/menxia",
                "capabilities": ["审核", "监督", "反馈"]
            },
            "shangshu": {  # 尚书省
                "name": "尚书省",
                "type": "execution",
                "endpoint": "http://localhost:8002/api/agents/shangshu",
                "capabilities": ["执行", "管理", "协调"]
            },
            "li_bu": {  # 吏部
                "name": "吏部",
                "type": "personnel",
                "endpoint": "http://localhost:8002/api/agents/libu",
                "capabilities": ["人事", "考核", "任免"]
            },
            "hu_bu": {  # 户部
                "name": "户部",
                "type": "finance",
                "endpoint": "http://localhost:8002/api/agents/hubu",
                "capabilities": ["财务", "统计", "户籍"]
            },
            "li_bu2": {  # 礼部
                "name": "礼部",
                "type": "ritual",
                "endpoint": "http://localhost:8002/api/agents/libu2",
                "capabilities": ["礼仪", "教育", "外交"]
            },
            "bing_bu": {  # 兵部
                "name": "兵部",
                "type": "military",
                "endpoint": "http://localhost:8002/api/agents/bingbu",
                "capabilities": ["军事", "国防", "战略"]
            },
            "xing_bu": {  # 刑部
                "name": "刑部",
                "type": "justice",
                "endpoint": "http://localhost:8002/api/agents/xingbu",
                "capabilities": ["司法", "审判", "执法"]
            },
            "gong_bu": {  # 工部
                "name": "工部",
                "type": "engineering",
                "endpoint": "http://localhost:8002/api/agents/gongbu",
                "capabilities": ["工程", "建设", "制造"]
            }
        }
        return agents
    
    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """获取智能体信息
        
        Args:
            agent_id: 智能体ID
            
        Returns:
            智能体信息
        """
        return self.agents.get(agent_id)
    
    def get_agents_by_type(self, agent_type: str) -> List[str]:
        """根据类型获取智能体
        
        Args:
            agent_type: 智能体类型
            
        Returns:
            智能体ID列表
        """
        return [agent_id for agent_id, agent_info in self.agents.items() 
                if agent_info["type"] == agent_type]
    
    def get_agents_by_capability(self, capability: str) -> List[str]:
        """根据能力获取智能体
        
        Args:
            capability: 能力
            
        Returns:
            智能体ID列表
        """
        return [agent_id for agent_id, agent_info in self.agents.items() 
                if capability in agent_info["capabilities"]]
    
    def set_agent_status(self, agent_id: str, status: str):
        """设置智能体状态
        
        Args:
            agent_id: 智能体ID
            status: 状态（idle, busy, error）
        """
        if agent_id in self.agent_status:
            self.agent_status[agent_id] = status
            logger.info(f"设置智能体 {agent_id} 状态为 {status}")
    
    def get_agent_status(self, agent_id: str) -> Optional[str]:
        """获取智能体状态
        
        Args:
            agent_id: 智能体ID
            
        Returns:
            状态
        """
        return self.agent_status.get(agent_id)
    
    def get_all_agents(self) -> Dict[str, Dict[str, Any]]:
        """获取所有智能体
        
        Returns:
            智能体信息字典
        """
        return self.agents
    
    def get_agent_statuses(self) -> Dict[str, str]:
        """获取所有智能体状态
        
        Returns:
            智能体状态字典
        """
        return self.agent_status
    
    def coordinate_task(self, task_type: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """协调任务
        
        Args:
            task_type: 任务类型
            task_data: 任务数据
            
        Returns:
            协调结果
        """
        logger.info(f"协调任务: {task_type}")
        
        # 根据任务类型选择合适的智能体
        agent_mapping = {
            "data_collection": ["hu_bu"],  # 数据采集
            "analysis": ["zhongshu", "shangshu"],  # 分析
            "generation": ["li_bu2", "shangshu"],  # 生成
            "report": ["shangshu", "menxia"]  # 报告
        }
        
        # 获取适合的智能体
        suitable_agents = agent_mapping.get(task_type, ["shangshu"])
        
        # 选择空闲的智能体
        available_agents = [agent for agent in suitable_agents 
                           if self.agent_status.get(agent) == "idle"]
        
        if not available_agents:
            # 如果没有空闲智能体，选择状态不是error的智能体
            available_agents = [agent for agent in suitable_agents 
                               if self.agent_status.get(agent) != "error"]
        
        if not available_agents:
            logger.error(f"没有可用的智能体处理任务: {task_type}")
            return {
                "success": False,
                "error": "没有可用的智能体"
            }
        
        # 选择第一个可用的智能体
        selected_agent = available_agents[0]
        
        # 设置智能体状态为忙碌
        self.set_agent_status(selected_agent, "busy")
        
        try:
            # 模拟调用智能体
            result = self._call_agent(selected_agent, task_data)
            
            # 设置智能体状态为空闲
            self.set_agent_status(selected_agent, "idle")
            
            return {
                "success": True,
                "agent": selected_agent,
                "result": result
            }
        except Exception as e:
            logger.error(f"调用智能体 {selected_agent} 失败: {e}")
            self.set_agent_status(selected_agent, "error")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _call_agent(self, agent_id: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """调用智能体
        
        Args:
            agent_id: 智能体ID
            task_data: 任务数据
            
        Returns:
            调用结果
        """
        # 模拟智能体调用
        agent_info = self.agents.get(agent_id)
        if not agent_info:
            raise Exception(f"智能体 {agent_id} 不存在")
        
        # 模拟处理时间
        time.sleep(0.5)
        
        # 根据智能体类型返回不同的结果
        if agent_id == "hu_bu":
            # 户部处理数据采集
            if "房价" in task_data.get("query", ""):
                return {
                    "data": {
                        "average_price": 98000,
                        "unit": "元/㎡",
                        "area": "南山区",
                        "city": "深圳"
                    }
                }
        elif agent_id == "li_bu2":
            # 礼部处理对话生成
            if "房价" in task_data.get("query", ""):
                return {
                    "response": "南山区二手房均价约9.8万/㎡"
                }
        elif agent_id == "shangshu":
            # 尚书省处理复杂任务
            if "分析" in task_data.get("query", ""):
                return {
                    "analysis": "根据历史数据，深圳南山区房价呈现稳定上涨趋势..."
                }
        
        # 默认响应
        return {
            "message": f"智能体 {agent_info['name']} 处理了任务"
        }


# 全局协调器实例
agent_coordinator: Optional[AgentCoordinator] = None


def get_agent_coordinator() -> AgentCoordinator:
    """获取智能体协调器实例"""
    global agent_coordinator
    if agent_coordinator is None:
        agent_coordinator = AgentCoordinator()
    return agent_coordinator


def coordinate_task(task_type: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
    """协调任务"""
    coordinator = get_agent_coordinator()
    return coordinator.coordinate_task(task_type, task_data)


def get_all_agents() -> Dict[str, Dict[str, Any]]:
    """获取所有智能体"""
    coordinator = get_agent_coordinator()
    return coordinator.get_all_agents()


def get_agent_statuses() -> Dict[str, str]:
    """获取所有智能体状态"""
    coordinator = get_agent_coordinator()
    return coordinator.get_agent_statuses()
