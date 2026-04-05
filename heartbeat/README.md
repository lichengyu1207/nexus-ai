# 智能体心跳上报模块

房都督平台智能体集群健康管理的核心组件。

## 功能特性

- ✅ 自动心跳上报（5秒间隔，可配置）
- ✅ 系统指标采集（CPU、内存、任务数）
- ✅ Redis 存储（支持 TTL 自动过期）
- ✅ 异步和同步两种实现方式
- ✅ RESTful API 查询接口
- ✅ 多智能体支持（兵部、户部、礼部）

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动 Redis

```bash
docker-compose up -d redis
```

### 3. 启动 API 服务

```bash
uvicorn heartbeat.api.main:app --reload --port 8000
```

### 4. 运行智能体

```python
import asyncio
from heartbeat.agents.bing_agent import BingAgent

async def main():
    agent = BingAgent(agent_id="bing_001")
    await agent.start()
    
    # 执行任务
    result = await agent.execute({"id": "task_1", "data": "test"})
    print(result)
    
    # 停止智能体
    await agent.stop()

asyncio.run(main())
```

## 配置

通过环境变量配置：

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `REDIS_URL` | `redis://localhost:6379/0` | Redis 连接字符串 |
| `HEARTBEAT_INTERVAL` | `5` | 心跳间隔（秒） |
| `HEARTBEAT_TTL` | `15` | 心跳数据 TTL（秒） |
| `LOG_LEVEL` | `INFO` | 日志级别 |

## API 接口

### 查询智能体心跳

```bash
GET /api/agents/{agent_id}/heartbeat
```

响应示例：
```json
{
  "agent_id": "bing_001",
  "pid": 12345,
  "cpu_percent": 12.5,
  "memory_percent": 8.2,
  "current_tasks": 3,
  "timestamp": 1711622400.123
}
```

### 列出所有活跃智能体

```bash
GET /api/agents/
```

### 获取智能体状态

```bash
GET /api/agents/{agent_id}/status
```

### 健康检查

```bash
GET /api/agents/health/check
```

## 测试

```bash
# 运行所有测试
pytest heartbeat/tests/ -v

# 运行特定测试
pytest heartbeat/tests/test_heartbeat.py -v

# 带覆盖率
pytest heartbeat/tests/ --cov=heartbeat --cov-report=html
```

## 目录结构

```
heartbeat/
├── agents/
│   ├── __init__.py
│   ├── base_agent.py      # 基类（心跳功能）
│   └── bing_agent.py      # 智能体实现
├── api/
│   ├── __init__.py
│   ├── main.py            # FastAPI 应用
│   └── agents.py          # API 路由
├── config/
│   ├── __init__.py
│   └── settings.py        # 配置管理
├── tests/
│   └── test_heartbeat.py  # 单元测试
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## 心跳数据格式

```json
{
  "agent_id": "string",      // 智能体 ID
  "pid": 12345,              // 进程 PID
  "cpu_percent": 12.5,       // CPU 使用率 (%)
  "memory_percent": 8.2,     // 内存使用率 (%)
  "current_tasks": 3,        // 当前任务数
  "timestamp": 1711622400.0  // 时间戳
}
```

## Redis 存储

- **键格式**: `agent:{agent_id}:heartbeat`
- **值**: JSON 字符串
- **TTL**: 15 秒（默认）

## 扩展建议

1. **健康检测服务**: 定期扫描 Redis，检测失联智能体
2. **负载均衡**: 根据心跳指标动态调整任务分发
3. **历史记录**: 将心跳写入时序数据库进行分析
