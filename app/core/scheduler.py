"""
智能体调度器
协调代理的执行顺序和状态管理
"""
from typing import Dict, Any, List, Optional
from app.core.message import MessageType
from app.core.bus import message_bus_manager, MessageBus
from app.core.state import state_manager, SharedState
from app.core.base_agent import BaseAgent
import asyncio
import logging

logger = logging.getLogger(__name__)


class AgentScheduler:
    """
    代理调度器
    负责协调代理的执行顺序和状态管理
    """
    
    def __init__(self, task_id: str):
        """
        初始化调度器
        
        Args:
            task_id: 任务ID
        """
        self.task_id = task_id
        self.message_bus = message_bus_manager.create_bus(task_id)
        self.shared_state = state_manager.create_state(task_id)
        self.agents: Dict[str, BaseAgent] = {}
        self.execution_order: List[str] = []
    
    def register_agent(self, agent: BaseAgent) -> None:
        """
        注册代理
        
        Args:
            agent: 代理实例
        """
        agent.set_message_bus(self.message_bus)
        agent.set_shared_state(self.shared_state)
        self.agents[agent.name] = agent
        logger.info(f"Registered agent: {agent.name}")
    
    def set_execution_order(self, order: List[str]) -> None:
        """
        设置执行顺序
        
        Args:
            order: 代理名称列表
        """
        self.execution_order = order
        logger.info(f"Execution order set: {' -> '.join(order)}")
    
    async def execute_sequential(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        顺序执行代理
        
        Args:
            input_data: 输入数据
            
        Returns:
            Dict: 执行结果
        """
        logger.info(f"Starting sequential execution for task {self.task_id}")
        
        current_data = input_data.copy()
        
        for agent_name in self.execution_order:
            if agent_name not in self.agents:
                logger.warning(f"Agent {agent_name} not found, skipping")
                continue
            
            agent = self.agents[agent_name]
            
            logger.info(f"Executing agent: {agent_name}")
            
            try:
                result = await agent.run(current_data)
                current_data.update(result)
                
                # 更新进度
                progress = (self.execution_order.index(agent_name) + 1) / len(self.execution_order)
                self.shared_state.update(progress=progress)
                
            except Exception as e:
                logger.error(f"Agent {agent_name} failed: {str(e)}")
                self.shared_state.add_error(f"{agent_name}: {str(e)}")
                raise
        
        logger.info(f"Sequential execution completed for task {self.task_id}")
        
        return {
            "task_id": self.task_id,
            "status": "SUCCESS",
            "results": self.shared_state.results,
            "message_history": [msg.to_dict() for msg in self.message_bus.get_history()]
        }
    
    async def execute_parallel(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        并行执行代理
        
        Args:
            input_data: 输入数据
            
        Returns:
            Dict: 执行结果
        """
        logger.info(f"Starting parallel execution for task {self.task_id}")
        
        tasks = []
        
        for agent_name, agent in self.agents.items():
            task = asyncio.create_task(agent.run(input_data.copy()))
            tasks.append((agent_name, task))
        
        # 等待所有任务完成
        for agent_name, task in tasks:
            try:
                await task
                logger.info(f"Agent {agent_name} completed")
            except Exception as e:
                logger.error(f"Agent {agent_name} failed: {str(e)}")
                self.shared_state.add_error(f"{agent_name}: {str(e)}")
        
        logger.info(f"Parallel execution completed for task {self.task_id}")
        
        return {
            "task_id": self.task_id,
            "status": "SUCCESS",
            "results": self.shared_state.results,
            "message_history": [msg.to_dict() for msg in self.message_bus.get_history()]
        }
    
    async def execute_with_communication(
        self,
        input_data: Dict[str, Any],
        max_iterations: int = 10
    ) -> Dict[str, Any]:
        """
        执行代理并允许代理间通信
        
        Args:
            input_data: 输入数据
            max_iterations: 最大迭代次数
            
        Returns:
            Dict: 执行结果
        """
        logger.info(f"Starting execution with communication for task {self.task_id}")
        
        # 启动所有代理的消息处理循环
        message_handlers = []
        
        for agent_name, agent in self.agents.items():
            handler = asyncio.create_task(self._message_handler_loop(agent))
            message_handlers.append(handler)
        
        # 执行代理
        result = await self.execute_sequential(input_data)
        
        # 停止消息处理循环
        for handler in message_handlers:
            handler.cancel()
        
        logger.info(f"Execution with communication completed for task {self.task_id}")
        
        return result
    
    async def _message_handler_loop(self, agent: BaseAgent) -> None:
        """
        消息处理循环
        
        Args:
            agent: 代理实例
        """
        while True:
            try:
                message = await agent.receive_message(timeout=1.0)
                
                if message:
                    await self._handle_message(agent, message)
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Message handler error for {agent.name}: {str(e)}")
    
    async def _handle_message(self, agent: BaseAgent, message: Any) -> None:
        """
        处理接收到的消息
        
        Args:
            agent: 代理实例
            message: 消息对象
        """
        if message.type == MessageType.REQUEST:
            # 处理请求
            response_data = await agent.execute(message.content)
            await agent.respond_to_message(message, response_data)
        
        elif message.type == MessageType.NOTIFY:
            # 处理通知
            logger.info(f"Agent {agent.name} received notification: {message.content}")
    
    def get_state(self) -> SharedState:
        """
        获取共享状态
        
        Returns:
            SharedState: 共享状态实例
        """
        return self.shared_state
    
    def get_message_history(self) -> List[Any]:
        """
        获取消息历史
        
        Returns:
            List: 消息历史列表
        """
        return self.message_bus.get_history()
