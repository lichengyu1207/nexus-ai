"""
Gatekeeper 单元测试
"""
import pytest
import asyncio
import time
import json
import sys
from unittest.mock import AsyncMock, MagicMock, patch, call

from gatekeeper.config import Settings
from gatekeeper.restarter import Restarter
from gatekeeper.scanner import HeartbeatScanner
from gatekeeper.models import TriggerType, RestartResult


class TestRestarter:
    def test_init(self):
        restarter = Restarter("echo test", 60)
        assert restarter.command_template == "echo test"
        assert restarter.cooling_seconds == 60

    def test_is_in_cooling_false_initially(self):
        restarter = Restarter("echo test", 60)
        in_cooling, remaining = restarter.is_in_cooling("agent-1")
        assert in_cooling is False
        assert remaining == 0.0

    @pytest.mark.asyncio
    async def test_restart_success(self):
        cmd = "echo restarted"
        restarter = Restarter(cmd, 60)
        with patch.object(restarter, "_log_restart", new_callable=AsyncMock):
            result = await restarter.restart("test-agent", trigger="manual", operator="admin")
            assert result is True

    @pytest.mark.asyncio
    async def test_restart_cooling_period(self):
        restarter = Restarter("echo test", 60)
        restarter._last_restart_time["test-agent"] = time.time()
        with patch.object(restarter, "_log_restart", new_callable=AsyncMock):
            result = await restarter.restart("test-agent", trigger="manual", operator="admin")
            assert result is False

    @pytest.mark.asyncio
    async def test_restart_after_cooling(self):
        restarter = Restarter("echo test", 1)
        restarter._last_restart_time["test-agent"] = time.time() - 2
        with patch.object(restarter, "_log_restart", new_callable=AsyncMock):
            result = await restarter.restart("test-agent", trigger="manual", operator="admin")
            assert result is True

    def test_get_restart_count(self):
        restarter = Restarter("echo test", 60)
        assert restarter.get_restart_count("unknown") == 0
        restarter._restart_count["agent-1"] = 3
        assert restarter.get_restart_count("agent-1") == 3

    def test_reset_cooling(self):
        restarter = Restarter("echo test", 60)
        restarter._last_restart_time["agent-1"] = time.time()
        restarter.reset_cooling("agent-1")
        assert "agent-1" not in restarter._last_restart_time


class TestHeartbeatScanner:
    @pytest.fixture
    def mock_redis(self):
        redis_mock = AsyncMock()
        return redis_mock

    @pytest.fixture
    def mock_restarter(self):
        restarter = MagicMock()
        restarter.is_in_cooling.return_value = (False, 0.0)
        restarter.restart = AsyncMock(return_value=True)
        return restarter

    @pytest.mark.asyncio
    async def test_scan_detects_timeout(self, mock_redis, mock_restarter):
        mock_redis.keys = AsyncMock(return_value=["agent:test-agent:heartbeat"])
        mock_redis.get = AsyncMock(return_value=json.dumps({"timestamp": 0}))

        scanner = HeartbeatScanner(mock_redis, mock_restarter)
        await scanner.scan()

        assert "test-agent" in scanner._pending_restarts

        for _ in range(10):
            await asyncio.sleep(0.1)
            if mock_restarter.restart.call_count > 0:
                break

        mock_restarter.restart.assert_called_once()
        call_args = mock_restarter.restart.call_args
        assert call_args[0][0] == "test-agent"
        assert call_args[1]["trigger"] == "auto"

    @pytest.mark.asyncio
    async def test_scan_skips_alive_agents(self, mock_redis, mock_restarter):
        current_time = time.time()
        mock_redis.keys = AsyncMock(return_value=["agent:alive-agent:heartbeat"])
        mock_redis.get = AsyncMock(
            return_value=json.dumps({"timestamp": current_time})
        )

        scanner = HeartbeatScanner(mock_redis, mock_restarter)
        await scanner.scan()
        await asyncio.sleep(0.1)

        mock_restarter.restart.assert_not_called()

    @pytest.mark.asyncio
    async def test_scan_handles_bytes_key(self, mock_redis, mock_restarter):
        mock_redis.keys = AsyncMock(return_value=[b"agent:test-agent:heartbeat"])
        mock_redis.get = AsyncMock(return_value=json.dumps({"timestamp": 0}))

        scanner = HeartbeatScanner(mock_redis, mock_restarter)
        await scanner.scan()

        assert "test-agent" in scanner._pending_restarts

        for _ in range(10):
            await asyncio.sleep(0.1)
            if mock_restarter.restart.call_count > 0:
                break

        mock_restarter.restart.assert_called_once()

    @pytest.mark.asyncio
    async def test_scan_handles_missing_heartbeat(self, mock_redis, mock_restarter):
        mock_redis.keys = AsyncMock(return_value=["agent:test-agent:heartbeat"])
        mock_redis.get = AsyncMock(return_value=None)

        scanner = HeartbeatScanner(mock_redis, mock_restarter)
        await scanner.scan()
        await asyncio.sleep(0.1)

        mock_restarter.restart.assert_not_called()

    @pytest.mark.asyncio
    async def test_scan_handles_invalid_json(self, mock_redis, mock_restarter):
        mock_redis.keys = AsyncMock(return_value=["agent:test-agent:heartbeat"])
        mock_redis.get = AsyncMock(return_value="invalid json")

        scanner = HeartbeatScanner(mock_redis, mock_restarter)
        await scanner.scan()
        await asyncio.sleep(0.1)

        mock_restarter.restart.assert_not_called()

    def test_stop(self, mock_redis, mock_restarter):
        scanner = HeartbeatScanner(mock_redis, mock_restarter)
        assert scanner._running is True
        scanner.stop()
        assert scanner._running is False

    def test_get_agent_status(self, mock_redis, mock_restarter):
        scanner = HeartbeatScanner(mock_redis, mock_restarter)
        scanner._agent_status["agent-1"] = {"last_heartbeat": time.time(), "is_alive": True}
        status = scanner.get_agent_status("agent-1")
        assert status is not None
        assert status["is_alive"] is True

    def test_get_all_status(self, mock_redis, mock_restarter):
        scanner = HeartbeatScanner(mock_redis, mock_restarter)
        scanner._agent_status["agent-1"] = {"last_heartbeat": time.time(), "is_alive": True}
        scanner._agent_status["agent-2"] = {"last_heartbeat": time.time(), "is_alive": False}
        all_status = scanner.get_all_status()
        assert len(all_status) == 2


class TestSettings:
    def test_default_values(self):
        settings = Settings()
        assert settings.scan_interval == 10
        assert settings.heartbeat_timeout == 30
        assert settings.restart_cooling == 60

    def test_get_restart_command_default(self):
        settings = Settings()
        cmd = settings.get_restart_command("test-agent")
        assert "test-agent" in cmd

    def test_get_restart_command_custom(self):
        settings = Settings(agent_restart_commands={"custom-agent": "docker restart custom"})
        cmd = settings.get_restart_command("custom-agent")
        assert cmd == "docker restart custom"


class TestModels:
    def test_trigger_type_enum(self):
        assert TriggerType.AUTO == "auto"
        assert TriggerType.MANUAL == "manual"

    def test_restart_result_enum(self):
        assert RestartResult.SUCCESS == "success"
        assert RestartResult.FAILURE == "failure"

    def test_restart_event(self):
        from gatekeeper.models import RestartEvent
        from datetime import datetime, timezone

        event = RestartEvent(
            agent_id="test-agent",
            trigger_type=TriggerType.AUTO,
            result=RestartResult.SUCCESS,
        )
        assert event.agent_id == "test-agent"
        assert event.trigger_type == "auto"
        assert event.result == "success"
        assert isinstance(event.created_at, datetime)
