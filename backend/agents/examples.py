"""
示例代理类
展示如何使用 BaseAgent 实现具体的代理
"""
from .base import BaseAgent
from .message import AgentMessage, MessageType
import asyncio
import logging

logger = logging.getLogger(__name__)


class DataCollectorAgent(BaseAgent):
    """
    数据采集代理示例
    负责采集房产数据
    """
    
    async def handle_message(self, message: AgentMessage) -> None:
        """
        处理接收到的消息
        
        Args:
            message: 消息对象
        """
        logger.info(f"DataCollectorAgent received message from {message.sender}: {message.type.value}")
        
        if message.type == MessageType.REQUEST:
            # 处理数据请求
            query = message.content.get("query", "")
            
            logger.info(f"DataCollectorAgent processing request: {query}")
            
            # 模拟数据采集
            data = await self._collect_data(query)
            
            # 发送响应
            await self.respond(message, {"data": data, "status": "success"})
        
        elif message.type == MessageType.NOTIFY:
            # 处理通知
            logger.info(f"DataCollectorAgent received notification: {message.content}")
    
    async def _collect_data(self, query: str) -> dict:
        """
        模拟数据采集
        
        Args:
            query: 查询内容
            
        Returns:
            dict: 采集的数据
        """
        # 模拟延迟
        await asyncio.sleep(0.5)
        
        # 返回模拟数据
        return {
            "query": query,
            "price": 50000,
            "area": "南山区",
            "timestamp": "2024-01-01T10:00:00"
        }


class MarketAnalystAgent(BaseAgent):
    """
    市场分析代理示例
    负责分析市场趋势
    """
    
    async def handle_message(self, message: AgentMessage) -> None:
        """
        处理接收到的消息
        
        Args:
            message: 消息对象
        """
        logger.info(f"MarketAnalystAgent received message from {message.sender}: {message.type.value}")
        
        if message.type == MessageType.REQUEST:
            # 处理分析请求
            data = message.content.get("data", {})
            
            logger.info(f"MarketAnalystAgent analyzing data")
            
            # 模拟市场分析
            analysis = await self._analyze_market(data)
            
            # 发送响应
            await self.respond(message, {"analysis": analysis, "status": "success"})
        
        elif message.type == MessageType.NOTIFY:
            # 处理通知
            logger.info(f"MarketAnalystAgent received notification: {message.content}")
    
    async def _analyze_market(self, data: dict) -> dict:
        """
        模拟市场分析
        
        Args:
            data: 数据内容
            
        Returns:
            dict: 分析结果
        """
        # 模拟延迟
        await asyncio.sleep(0.5)
        
        # 返回模拟分析结果
        return {
            "trend": "上升",
            "confidence": 0.85,
            "recommendation": "建议买入",
            "timestamp": "2024-01-01T10:01:00"
        }


# ========== 使用示例 ==========

async def example_usage():
    """
    使用示例
    展示如何创建和使用代理
    """
    from .bus import MessageBus
    
    # 1. 创建消息总线
    bus = MessageBus(task_id="task-123")
    
    # 2. 创建代理
    collector = DataCollectorAgent(
        agent_name="data_collector",
        task_id="task-123",
        bus=bus
    )
    
    analyst = MarketAnalystAgent(
        agent_name="market_analyst",
        task_id="task-123",
        bus=bus
    )
    
    # 3. 启动代理
    await collector.start()
    await analyst.start()
    
    # 4. 发送消息
    # 4.1 请求-响应模式
    response = await analyst.request(
        recipient="data_collector",
        content={"query": "深圳南山区房价"}
    )
    
    print(f"Response: {response}")
    
    # 4.2 广播消息
    await collector.broadcast(
        message_type=MessageType.NOTIFY,
        content={"status": "数据采集完成"}
    )
    
    # 5. 查看消息历史
    history = bus.get_history()
    print(f"Message history: {len(history)} messages")
    
    # 6. 停止代理
    await collector.stop()
    await analyst.stop()
    
    print("Example completed!")


if __name__ == "__main__":
    # 运行示例
    asyncio.run(example_usage())
