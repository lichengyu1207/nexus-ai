"""
心跳上报模块单元测试
"""
import asyncio
import json
import os
import time
from unittest.mock import AsyncMock, MagicMock, patch, Mock

import pytest

from heartbeat.agents.base_agent import BaseAgent
from heartbeat.agents.bing_agent import BingAgent, HubuAgent, LibuAgent
from heartbeat.config.settings import Settings


from typing import Any, Dict, List, Optional


class MockProcess:
    """模拟 psutil.Process"""
    
    def cpu_percent(self, interval=0.1):
        return 25.5
    
    def memory_percent(self):
        return 15.2


class TestSettings:
    """配置测试"""
    
    def test_default_settings(self):
        """测试默认配置"""
        settings = Settings()
        assert settings.redis_url == "redis://localhost:6379/0"
        assert settings.heartbeat_interval == 5
        assert settings.heartbeat_ttl == 15
        assert settings.log_level == "INFO"
    
    def test_custom_settings(self):
        """测试自定义配置"""
        settings = Settings(
            redis_url="redis://custom:6379/1",
            heartbeat_interval=10,
            heartbeat_ttl=30,
            log_level="DEBUG",
        )
        assert settings.redis_url == "redis://custom:6379/1"
        assert settings.heartbeat_interval == 10
        assert settings.heartbeat_ttl == 30
        assert settings.log_level == "DEBUG"
    
    def test_from_env(self, monkeypatch):
        """测试从环境变量加载"""
        monkeypatch.setenv("REDIS_URL", "redis://env:6379/2")
        monkeypatch.setenv("HEARTBEAT_INTERVAL", "20")
        monkeypatch.setenv("HEARTBEAT_TTL", "60")
        monkeypatch.setenv("LOG_LEVEL", "WARNING")
        
        settings = Settings.from_env()
        assert settings.redis_url == "redis://env:6379/2"
        assert settings.heartbeat_interval == 20
        assert settings.heartbeat_ttl == 60
        assert settings.log_level == "WARNING"


class TestableAgent(BaseAgent):
    """可测试的智能体实现"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._tasks: List[Any] = []
    
    def get_current_tasks_count(self) -> int:
        return len(self._tasks)
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        self._tasks.append(task)
        return {"status": "completed"}


class TestBaseAgent:
    """基类测试"""
    
    def test_init(self):
        """测试初始化"""
        agent = TestableAgent(agent_id="test_001")
        assert agent.agent_id == "test_001"
        assert agent.heartbeat_interval == 5
        assert agent.heartbeat_ttl == 15
    
    def test_collect_metrics(self):
        """测试指标采集"""
        agent = TestableAgent(agent_id="test_001")
        agent._process = MockProcess()
        
        metrics = agent.collect_metrics()
        
        assert metrics["agent_id"] == "test_001"
        assert metrics["pid"] == os.getpid()
        assert metrics["cpu_percent"] == 25.5
        assert metrics["memory_percent"] == 15.2
        assert metrics["current_tasks"] == 0
        assert "timestamp" in metrics
    
    def test_collect_metrics_with_tasks(self):
        """测试有任务时的指标采集"""
        agent = TestableAgent(agent_id="test_001")
        agent._process = MockProcess()
        agent._tasks = [{"id": "1"}, {"id": "2"}, {"id": "3"}]
        
        metrics = agent.collect_metrics()
        
        assert metrics["current_tasks"] == 3
    
    @pytest.mark.asyncio
    async def test_send_heartbeat_async(self):
        """测试异步发送心跳"""
        agent = TestableAgent(agent_id="test_001")
        agent._process = MockProcess()
        
        mock_redis = AsyncMock()
        
        await agent._send_heartbeat_async(mock_redis)
        
        mock_redis.setex.assert_called_once()
        args = mock_redis.setex.call_args[0]
        
        assert args[0] == "agent:test_001:heartbeat"
        assert args[1] == 15
        
        data = json.loads(args[2])
        assert data["agent_id"] == "test_001"
    
    @pytest.mark.asyncio
    async def test_heartbeat_loop_async(self):
        """测试异步心跳循环"""
        agent = TestableAgent(
            agent_id="test_001",
            heartbeat_interval=0.01,
        )
        agent._process = MockProcess()
        
        mock_redis = AsyncMock()
        call_count = 0
        
        async def mock_setex(*args):
            nonlocal call_count
            call_count += 1
        
        mock_redis.setex = mock_setex
        mock_redis.close = AsyncMock()
        
        mock_redis_module = MagicMock()
        mock_redis_module.from_url = AsyncMock(return_value=mock_redis)
        
        with patch.dict("sys.modules", {"redis.asyncio": mock_redis_module}):
            task = asyncio.create_task(agent._heartbeat_loop_async())
            
            await asyncio.sleep(0.05)
            
            agent._stop_event.set()
            
            try:
                await asyncio.wait_for(task, timeout=1)
            except asyncio.CancelledError:
                pass
        
        assert call_count >= 2
    
    @pytest.mark.asyncio
    async def test_start_stop_heartbeat_async(self):
        """测试启动和停止异步心跳"""
        agent = TestableAgent(agent_id="test_001")
        agent._process = MockProcess()
        
        mock_redis = AsyncMock()
        mock_redis.close = AsyncMock()
        
        mock_redis_module = MagicMock()
        mock_redis_module.from_url = AsyncMock(return_value=mock_redis)
        
        with patch.dict("sys.modules", {"redis.asyncio": mock_redis_module}):
            await agent.start_heartbeat_async()
            assert agent._heartbeat_task is not None
            
            await asyncio.sleep(0.01)
            
            await agent.stop_heartbeat_async()
            assert agent._heartbeat_task is None
    
    def test_sync_heartbeat(self):
        """测试同步心跳"""
        agent = TestableAgent(agent_id="test_001")
        agent._process = MockProcess()
        
        mock_redis = MagicMock()
        
        with patch("redis.from_url", return_value=mock_redis):
            agent._send_heartbeat_sync()
            
            mock_redis.setex.assert_called_once()
            mock_redis.close.assert_called_once()


class TestBingAgent:
    """兵部智能体测试"""
    
    def test_init(self):
        """测试初始化"""
        agent = BingAgent(agent_id="bing_test")
        assert agent.agent_id == "bing_test"
        assert agent._tasks == []
    
    @pytest.mark.asyncio
    async def test_add_remove_task(self):
        """测试任务添加和移除"""
        agent = BingAgent(agent_id="bing_test")
        
        agent.add_task({"id": "task_1", "data": "test"})
        assert len(agent._tasks) == 1
        
        agent.remove_task("task_1")
        assert len(agent._tasks) == 0
    
    @pytest.mark.asyncio
    async def test_execute(self):
        """测试任务执行"""
        agent = BingAgent(agent_id="bing_test")
        
        result = await agent.execute({"id": "task_1", "data": "test"})
        
        assert result["task_id"] == "task_1"
        assert result["status"] == "completed"
        assert "BingAgent" in result["result"]
    
    @pytest.mark.asyncio
    async def test_start_stop(self):
        """测试启动和停止"""
        agent = BingAgent(agent_id="bing_test")
        agent._process = MockProcess()
        
        mock_redis = AsyncMock()
        mock_redis.close = AsyncMock()
        
        mock_redis_module = MagicMock()
        mock_redis_module.from_url = AsyncMock(return_value=mock_redis)
        
        with patch.dict("sys.modules", {"redis.asyncio": mock_redis_module}):
            await agent.start()
            assert agent._is_running is True
            
            await agent.stop()
            assert agent._is_running is False


class TestHubuAgent:
    """户部智能体测试"""
    
    def test_init(self):
        agent = HubuAgent(agent_id="hubu_test")
        assert agent.agent_id == "hubu_test"
    
    @pytest.mark.asyncio
    async def test_execute(self):
        agent = HubuAgent(agent_id="hubu_test")
        result = await agent.execute({"id": "task_1"})
        assert result["status"] == "completed"


class TestLibuAgent:
    """礼部智能体测试"""
    
    def test_init(self):
        agent = LibuAgent(agent_id="libu_test")
        assert agent.agent_id == "libu_test"
    
    @pytest.mark.asyncio
    async def test_execute(self):
        agent = LibuAgent(agent_id="libu_test")
        result = await agent.execute({"id": "task_1"})
        assert result["status"] == "completed"


class TestHeartbeatIntegration:
    """心跳集成测试"""
    
    @pytest.mark.asyncio
    async def test_multiple_agents(self):
        """测试多个智能体同时运行"""
        agents = [
            BingAgent(agent_id="bing_001"),
            HubuAgent(agent_id="hubu_001"),
            LibuAgent(agent_id="libu_001"),
        ]
        
        for agent in agents:
            agent._process = MockProcess()
        
        mock_redis = AsyncMock()
        mock_redis.close = AsyncMock()
        
        call_count = 0
        
        async def mock_setex(*args):
            nonlocal call_count
            call_count += 1
        
        mock_redis.setex = mock_setex
        
        mock_redis_module = MagicMock()
        mock_redis_module.from_url = AsyncMock(return_value=mock_redis)
        
        with patch.dict("sys.modules", {"redis.asyncio": mock_redis_module}):
            for agent in agents:
                await agent.start()
            
            await asyncio.sleep(0.1)
            
            assert call_count >= 3
            
            for agent in agents:
                await agent.stop()
    
    @pytest.mark.asyncio
    async def test_heartbeat_data_format(self):
        """测试心跳数据格式"""
        agent = BingAgent(agent_id="format_test")
        agent._process = MockProcess()
        agent._tasks = [{"id": "1"}, {"id": "2"}]
        
        mock_redis = AsyncMock()
        
        await agent._send_heartbeat_async(mock_redis)
        
        args = mock_redis.setex.call_args[0]
        data = json.loads(args[2])
        
        assert "agent_id" in data
        assert "pid" in data
        assert "cpu_percent" in data
        assert "memory_percent" in data
        assert "current_tasks" in data
        assert "timestamp" in data
        
        assert isinstance(data["agent_id"], str)
        assert isinstance(data["pid"], int)
        assert isinstance(data["cpu_percent"], (int, float))
        assert isinstance(data["memory_percent"], (int, float))
        assert isinstance(data["current_tasks"], int)
        assert isinstance(data["timestamp"], (int, float))
