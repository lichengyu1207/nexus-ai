"""
单元测试
测试消息总线和代理的基本功能
测试record_step和并行执行
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.agents.message import AgentMessage, MessageType
from backend.agents.bus import MessageBus
from backend.agents.base import BaseAgent


class TestAgent(BaseAgent):
    """测试代理"""
    
    def __init__(self, agent_name: str, task_id: str, bus: MessageBus):
        super().__init__(agent_name, task_id, bus)
        self.received_messages = []
    
    async def handle_message(self, message: AgentMessage) -> None:
        """处理消息"""
        self.received_messages.append(message)


@pytest.mark.asyncio
async def test_message_bus_basic():
    """测试消息总线基本功能"""
    # 创建消息总线
    bus = MessageBus(task_id="test-task-1")
    
    # 注册代理
    bus.register_agent("agent1")
    bus.register_agent("agent2")
    
    # 检查注册状态
    assert "agent1" in bus.get_registered_agents()
    assert "agent2" in bus.get_registered_agents()
    assert len(bus.get_registered_agents()) == 2


@pytest.mark.asyncio
async def test_point_to_point_message():
    """测试点对点消息"""
    bus = MessageBus(task_id="test-task-2")
    
    # 注册代理
    bus.register_agent("sender")
    bus.register_agent("receiver")
    
    # 创建消息
    msg = AgentMessage(
        task_id="test-task-2",
        sender="sender",
        recipient="receiver",
        type=MessageType.REQUEST,
        content={"query": "test"}
    )
    
    # 发送消息
    await bus.publish(msg)
    
    # 接收消息
    queue = await bus.subscribe("receiver")
    received = await asyncio.wait_for(queue.get(), timeout=1.0)
    
    # 验证
    assert received.sender == "sender"
    assert received.recipient == "receiver"
    assert received.content == {"query": "test"}


@pytest.mark.asyncio
async def test_broadcast_message():
    """测试广播消息"""
    bus = MessageBus(task_id="test-task-3")
    
    # 注册多个代理
    bus.register_agent("agent1")
    bus.register_agent("agent2")
    bus.register_agent("agent3")
    
    # 创建广播消息
    msg = AgentMessage(
        task_id="test-task-3",
        sender="agent1",
        recipient=None,  # 广播
        type=MessageType.NOTIFY,
        content={"status": "broadcast test"}
    )
    
    # 发送广播
    await bus.publish(msg)
    
    # 验证所有代理都收到消息（除了发送者）
    queue2 = await bus.subscribe("agent2")
    queue3 = await bus.subscribe("agent3")
    
    received2 = await asyncio.wait_for(queue2.get(), timeout=1.0)
    received3 = await asyncio.wait_for(queue3.get(), timeout=1.0)
    
    assert received2.content == {"status": "broadcast test"}
    assert received3.content == {"status": "broadcast test"}


@pytest.mark.asyncio
async def test_message_history():
    """测试消息历史"""
    bus = MessageBus(task_id="test-task-4")
    
    # 注册代理
    bus.register_agent("agent1")
    bus.register_agent("agent2")
    
    # 发送多条消息
    for i in range(3):
        msg = AgentMessage(
            task_id="test-task-4",
            sender="agent1",
            recipient="agent2",
            type=MessageType.REQUEST,
            content={"index": i}
        )
        await bus.publish(msg)
    
    # 检查历史
    history = bus.get_history()
    assert len(history) == 3
    
    # 验证消息顺序
    for i, msg in enumerate(history):
        assert msg.content["index"] == i


@pytest.mark.asyncio
async def test_base_agent():
    """测试基础代理"""
    bus = MessageBus(task_id="test-task-5")
    
    # 创建测试代理
    agent1 = TestAgent("agent1", "test-task-5", bus)
    agent2 = TestAgent("agent2", "test-task-5", bus)
    
    # 启动代理
    await agent1.start()
    await agent2.start()
    
    # 发送消息
    await agent1.send(
        recipient="agent2",
        message_type=MessageType.REQUEST,
        content={"test": "message"}
    )
    
    # 等待消息处理
    await asyncio.sleep(0.5)
    
    # 验证
    assert len(agent2.received_messages) == 1
    assert agent2.received_messages[0].content == {"test": "message"}
    
    # 停止代理
    await agent1.stop()
    await agent2.stop()


@pytest.mark.asyncio
async def test_request_response():
    """测试请求-响应模式"""
    bus = MessageBus(task_id="test-task-6")
    
    # 创建代理
    agent1 = TestAgent("agent1", "test-task-6", bus)
    agent2 = TestAgent("agent2", "test-task-6", bus)
    
    # 启动代理
    await agent1.start()
    await agent2.start()
    
    # 定义响应处理
    async def handle_with_response(message):
        agent2.received_messages.append(message)
        if message.type == MessageType.REQUEST:
            await agent2.respond(message, {"response": "ok"})
    
    # 临时替换处理方法
    agent2.handle_message = handle_with_response
    
    # 发送请求并等待响应
    response = await agent1.request(
        recipient="agent2",
        content={"query": "test"},
        timeout=2.0
    )
    
    # 验证
    assert response is not None
    assert response["response"] == "ok"
    
    # 停止代理
    await agent1.stop()
    await agent2.stop()


@pytest.mark.asyncio
async def test_record_step():
    """测试record_step方法"""
    bus = MessageBus(task_id="test-task-record-step", db_enabled=False, sse_enabled=False)
    
    agent = TestAgent("test_agent", "test-task-record-step", bus)
    await agent.start()
    
    with patch('backend.agents.base.AnalysisStepDB') as mock_db:
        mock_db.create_step = AsyncMock()
        mock_db.update_step = AsyncMock()
        
        step_id = await agent.record_step(
            step_name="测试步骤",
            detail="测试详情",
            status="completed",
            input_data={"query": "test"},
            output_data={"result": "ok"}
        )
        
        assert step_id is not None
        mock_db.create_step.assert_called_once()
        mock_db.update_step.assert_called_once()
    
    await agent.stop()


@pytest.mark.asyncio
async def test_record_step_broadcast():
    """测试record_step广播步骤事件"""
    bus = MessageBus(task_id="test-task-broadcast", db_enabled=False, sse_enabled=False)
    
    bus.register_agent("listener")
    queue = await bus.subscribe("listener")
    
    agent = TestAgent("test_agent", "test-task-broadcast", bus)
    await agent.start()
    
    with patch('backend.agents.base.AnalysisStepDB'):
        await agent.record_step(
            step_name="广播测试",
            detail="测试广播",
            status="completed"
        )
    
    try:
        msg = await asyncio.wait_for(queue.get(), timeout=1.0)
        assert msg.type == MessageType.NOTIFY
        assert msg.content.get('event') == 'step'
        assert msg.content.get('step', {}).get('step_name') == "广播测试"
    except asyncio.TimeoutError:
        pytest.fail("Step broadcast not received")
    
    await agent.stop()


@pytest.mark.asyncio
async def test_parallel_agent_execution():
    """测试并行代理执行"""
    bus = MessageBus(task_id="test-task-parallel", db_enabled=False, sse_enabled=False)
    
    results = {"agent1": False, "agent2": False}
    
    class ParallelTestAgent(BaseAgent):
        def __init__(self, name, task_id, bus, results_key):
            super().__init__(name, task_id, bus)
            self.results_key = results_key
        
        async def handle_message(self, message: AgentMessage) -> None:
            if message.type == MessageType.REQUEST:
                await asyncio.sleep(0.1)
                results[self.results_key] = True
                await self.respond(message, {"done": True})
    
    agent1 = ParallelTestAgent("agent1", "test-task-parallel", bus, "agent1")
    agent2 = ParallelTestAgent("agent2", "test-task-parallel", bus, "agent2")
    controller = TestAgent("controller", "test-task-parallel", bus)
    
    await agent1.start()
    await agent2.start()
    await controller.start()
    
    msg1 = await controller.send("agent1", MessageType.REQUEST, {"task": 1})
    msg2 = await controller.send("agent2", MessageType.REQUEST, {"task": 2})
    
    await asyncio.sleep(0.3)
    
    assert results["agent1"] is True
    assert results["agent2"] is True
    
    await agent1.stop()
    await agent2.stop()
    await controller.stop()


@pytest.mark.asyncio
async def test_sse_step_event_format():
    """测试SSE步骤事件格式"""
    from backend.sse_manager import SSEEvent, sse_manager
    from backend.agents.bus import MessageBus
    
    bus = MessageBus(task_id="test-sse-format", db_enabled=False, sse_enabled=True)
    bus.register_agent("test_agent")
    
    queue = await sse_manager.subscribe("test-sse-format")
    
    step_data = {
        'id': 'step-123',
        'task_id': 'test-sse-format',
        'agent_name': 'test_agent',
        'step_name': '测试步骤',
        'detail': '测试详情',
        'status': 'completed'
    }
    
    msg = AgentMessage(
        task_id="test-sse-format",
        sender="test_agent",
        recipient=None,
        type=MessageType.NOTIFY,
        content={'event': 'step', 'step': step_data}
    )
    
    await bus.publish(msg)
    
    try:
        event = await asyncio.wait_for(queue.get(), timeout=1.0)
        assert event.event == "step"
        assert event.data.get('step_name') == "测试步骤"
        assert event.data.get('agent_name') == "test_agent"
    except asyncio.TimeoutError:
        pytest.fail("SSE event not received")
    finally:
        await sse_manager.unsubscribe("test-sse-format", queue)


def run_tests():
    """运行测试"""
    pytest.main([__file__, "-v"])


if __name__ == "__main__":
    run_tests()
