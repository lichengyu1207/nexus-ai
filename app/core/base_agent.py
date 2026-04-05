"""
基础代理类
整合消息总线和共享状态，提供完整的代理功能
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from app.core.message import AgentMessage, MessageType
from app.core.bus import MessageBus
from app.core.state import SharedState
import asyncio
import logging

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    基础代理类
    提供消息通信和状态共享功能
    """
    
    def __init__(self, name: str, task_id: str):
        """
        初始化代理
        
        Args:
            name: 代理名称
            task_id: 任务ID
        """
        self.name = name
        self.task_id = task_id
        self.message_bus: Optional[MessageBus] = None
        self.shared_state: Optional[SharedState] = None
        self._running = False
    
    def set_message_bus(self, bus: MessageBus) -> None:
        """
        设置消息总线
        
        Args:
            bus: 消息总线实例
        """
        self.message_bus = bus
        bus.register_agent(self.name)
        logger.info(f"Agent {self.name} registered to message bus")
    
    def set_shared_state(self, state: SharedState) -> None:
        """
        设置共享状态
        
        Args:
            state: 共享状态实例
        """
        self.shared_state = state
    
    async def send_message(
        self,
        recipient: Optional[str],
        content: Dict[str, Any],
        message_type: MessageType = MessageType.NOTIFY
    ) -> AgentMessage:
        """
        发送消息
        
        Args:
            recipient: 接收者（None表示广播）
            content: 消息内容
            message_type: 消息类型
            
        Returns:
            AgentMessage: 发送的消息
        """
        if not self.message_bus:
            raise RuntimeError("Message bus not set")
        
        message = AgentMessage(
            task_id=self.task_id,
            sender=self.name,
            recipient=recipient,
            type=message_type,
            content=content
        )
        
        await self.message_bus.publish(message)
        logger.info(f"Agent {self.name} sent message to {recipient or 'all'}")
        
        return message
    
    async def receive_message(self, timeout: Optional[float] = None) -> Optional[AgentMessage]:
        """
        接收消息
        
        Args:
            timeout: 超时时间（秒）
            
        Returns:
            Optional[AgentMessage]: 接收到的消息
        """
        if not self.message_bus:
            raise RuntimeError("Message bus not set")
        
        message = await self.message_bus.receive(self.name, timeout=timeout)
        
        if message:
            logger.info(f"Agent {self.name} received message from {message.sender}")
        
        return message
    
    async def request_data(
        self,
        recipient: str,
        request_content: Dict[str, Any],
        timeout: float = 30.0
    ) -> Optional[Dict[str, Any]]:
        """
        请求数据（发送请求并等待响应）
        
        Args:
            recipient: 接收者
            request_content: 请求内容
            timeout: 超时时间
            
        Returns:
            Optional[Dict]: 响应数据
        """
        # 发送请求
        request_msg = await self.send_message(
            recipient=recipient,
            content=request_content,
            message_type=MessageType.REQUEST
        )
        
        # 等待响应
        start_time = asyncio.get_event_loop().time()
        
        while True:
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed >= timeout:
                logger.warning(f"Agent {self.name} request timeout")
                return None
            
            message = await self.receive_message(timeout=timeout - elapsed)
            
            if message and message.type == MessageType.RESPONSE and message.in_reply_to == request_msg.id:
                return message.content
        
        return None
    
    async def respond_to_message(
        self,
        original_message: AgentMessage,
        response_content: Dict[str, Any]
    ) -> AgentMessage:
        """
        回复消息
        
        Args:
            original_message: 原始消息
            response_content: 响应内容
            
        Returns:
            AgentMessage: 响应消息
        """
        response = AgentMessage(
            task_id=self.task_id,
            sender=self.name,
            recipient=original_message.sender,
            type=MessageType.RESPONSE,
            content=response_content,
            in_reply_to=original_message.id
        )
        
        await self.message_bus.publish(response)
        logger.info(f"Agent {self.name} responded to {original_message.sender}")
        
        return response
    
    def update_state(self, **kwargs) -> None:
        """
        更新共享状态
        
        Args:
            **kwargs: 要更新的字段
        """
        if self.shared_state:
            self.shared_state.update(**kwargs)
    
    def set_state_data(self, key: str, value: Any) -> None:
        """
        设置状态数据
        
        Args:
            key: 数据键
            value: 数据值
        """
        if self.shared_state:
            self.shared_state.set_data(key, value)
    
    def get_state_data(self, key: str, default: Any = None) -> Any:
        """
        获取状态数据
        
        Args:
            key: 数据键
            default: 默认值
            
        Returns:
            Any: 数据值
        """
        if self.shared_state:
            return self.shared_state.get_data(key, default)
        return default
    
    def set_result(self, result: Any) -> None:
        """
        设置代理结果
        
        Args:
            result: 结果数据
        """
        if self.shared_state:
            self.shared_state.set_result(self.name, result)
    
    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行代理任务（抽象方法，由子类实现）
        
        Args:
            input_data: 输入数据
            
        Returns:
            Dict: 执行结果
        """
        pass
    
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        运行代理（包含状态更新）
        
        Args:
            input_data: 输入数据
            
        Returns:
            Dict: 执行结果
        """
        self._running = True
        self.update_state(current_step=f"{self.name}_running")
        
        try:
            result = await self.execute(input_data)
            self.set_result(result)
            self.update_state(current_step=f"{self.name}_completed")
            
            logger.info(f"Agent {self.name} completed successfully")
            
            return result
        
        except Exception as e:
            logger.error(f"Agent {self.name} failed: {str(e)}")
            self.update_state(errors=[f"{self.name}: {str(e)}"])
            raise
        
        finally:
            self._running = False
