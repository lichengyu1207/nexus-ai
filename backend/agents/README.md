# 智能体消息总线系统

## 📋 概述

这是一个轻量级的智能体协同框架，实现了基于消息总线的代理间通信机制。

## 🏗️ 架构

```
┌─────────────────────────────────────┐
│          MessageBus                 │
│  ┌──────────┐  ┌──────────┐       │
│  │  Queue1  │  │  Queue2  │ ...   │
│  └──────────┘  └──────────┘       │
│                                     │
│  History: [msg1, msg2, msg3, ...]  │
└─────────────────────────────────────┘
         ↑              ↑
         │              │
    ┌────┴────┐    ┌────┴────┐
    │ Agent1  │    │ Agent2  │
    └─────────┘    └─────────┘
```

## 📦 核心组件

### 1. AgentMessage（消息格式）

```python
from backend.agents import AgentMessage, MessageType

msg = AgentMessage(
    task_id="task-123",
    sender="data_collector",
    recipient="market_analyst",  # None表示广播
    type=MessageType.REQUEST,
    content={"query": "深圳南山区房价"}
)
```

### 2. MessageBus（消息总线）

```python
from backend.agents import MessageBus

# 创建消息总线
bus = MessageBus(task_id="task-123")

# 注册代理
bus.register_agent("agent1")
bus.register_agent("agent2")

# 发送消息
await bus.publish(msg)

# 接收消息
queue = await bus.subscribe("agent1")
message = await queue.get()
```

### 3. BaseAgent（基础代理）

```python
from backend.agents import BaseAgent, MessageType

class MyAgent(BaseAgent):
    async def handle_message(self, message):
        if message.type == MessageType.REQUEST:
            # 处理请求
            result = await self.process(message.content)
            
            # 发送响应
            await self.respond(message, {"result": result})
```

## 🚀 快速开始

### 安装依赖

```bash
pip install pydantic asyncio
```

### 运行示例

```python
import asyncio
from backend.agents import MessageBus, DataCollectorAgent, MarketAnalystAgent

async def main():
    # 1. 创建消息总线
    bus = MessageBus(task_id="task-123")
    
    # 2. 创建代理
    collector = DataCollectorAgent("data_collector", "task-123", bus)
    analyst = MarketAnalystAgent("market_analyst", "task-123", bus)
    
    # 3. 启动代理
    await collector.start()
    await analyst.start()
    
    # 4. 发送请求
    response = await analyst.request(
        recipient="data_collector",
        content={"query": "深圳南山区房价"}
    )
    
    print(f"Response: {response}")
    
    # 5. 停止代理
    await collector.stop()
    await analyst.stop()

asyncio.run(main())
```

## 🧪 运行测试

```bash
cd backend/agents
python test_agents.py
```

## 📖 API文档

### MessageBus

| 方法 | 说明 |
|------|------|
| `register_agent(agent_name)` | 注册代理 |
| `unregister_agent(agent_name)` | 注销代理 |
| `publish(message)` | 发布消息 |
| `subscribe(agent_name)` | 订阅消息队列 |
| `receive(agent_name, timeout)` | 接收消息 |
| `get_history()` | 获取消息历史 |

### BaseAgent

| 方法 | 说明 |
|------|------|
| `start()` | 启动代理 |
| `stop()` | 停止代理 |
| `send(recipient, type, content)` | 发送消息 |
| `broadcast(type, content)` | 广播消息 |
| `request(recipient, content, timeout)` | 请求-响应 |
| `respond(original_message, content)` | 回复消息 |
| `handle_message(message)` | 处理消息（抽象方法） |

## 🎯 使用场景

1. **点对点通信**：代理之间直接发送消息
2. **广播通知**：向所有代理发送通知
3. **请求-响应**：发送请求并等待响应
4. **消息历史**：追踪所有消息记录

## 📊 性能特点

- ✅ 异步消息传递
- ✅ 支持广播和点对点
- ✅ 消息历史追踪
- ✅ 超时控制
- ✅ 错误隔离

## 🔧 扩展

可以基于此框架实现：
- 持久化存储
- WebSocket实时通信
- 消息优先级
- 消息重试机制
- 分布式消息总线

## 📝 License

MIT
