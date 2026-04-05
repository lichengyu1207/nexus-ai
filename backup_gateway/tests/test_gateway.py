"""
备用网关模块单元测试
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone

from backup_gateway.config import GatewayConfig, settings
from backup_gateway.gateway import BackupGateway, ProxyHandler
from backup_gateway.health_monitor import HealthMonitor, HealthStatus, HealthCheckResult
from backup_gateway.notifier import FailoverNotifier, FailoverEvent, NodeState


class TestGatewayConfig:
    def test_default_config(self):
        config = GatewayConfig()
        assert config.PORT == 18790
        assert config.BACKEND_URL == "http://localhost:8000"
        assert config.CHECK_INTERVAL == 2

    def test_custom_config(self):
        config = GatewayConfig(
            PORT=8080,
            BACKEND_URL="http://backend:9000",
        )
        assert config.PORT == 8080
        assert config.BACKEND_URL == "http://backend:9000"


class TestBackupGateway:
    @pytest.fixture
    def gateway(self):
        return BackupGateway(port=18790, backend_url="http://localhost:8000")

    def test_init(self, gateway):
        assert gateway.port == 18790
        assert gateway.backend_url == "http://localhost:8000"
        assert gateway._running is False

    def test_get_stats(self, gateway):
        stats = gateway.get_stats()
        assert "running" in stats
        assert "port" in stats
        assert "backend_url" in stats

    def test_is_healthy(self, gateway):
        assert gateway.is_healthy() is False
        gateway._running = True
        assert gateway.is_healthy() is True


class TestHealthMonitor:
    @pytest.fixture
    def monitor(self):
        return HealthMonitor(check_interval=1)

    @pytest.mark.asyncio
    async def test_register_check(self, monitor):
        async def dummy_check():
            return HealthCheckResult("test", HealthStatus.HEALTHY)

        monitor.register_check("test", dummy_check)
        assert "test" in monitor._checks

    @pytest.mark.asyncio
    async def test_run_check(self, monitor):
        async def passing_check():
            return HealthCheckResult("pass", HealthStatus.HEALTHY)

        monitor.register_check("pass", passing_check)
        result = await monitor.run_check("pass")
        assert result.status == HealthStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_get_status(self, monitor):
        async def failing_check():
            return HealthCheckResult("fail", HealthStatus.UNHEALTHY)

        monitor.register_check("fail", failing_check)
        monitor._consecutive_failures["fail"] = 3
        status = monitor.get_status("fail")
        assert status == HealthStatus.UNHEALTHY


class TestFailoverNotifier:
    @pytest.fixture
    def notifier(self):
        return FailoverNotifier(webhook_url=None)

    def test_event_creation(self):
        event = FailoverEvent(
            old_state=NodeState.BACKUP,
            new_state=NodeState.MASTER,
            vip="192.168.1.100",
            reason="Test failover",
        )
        assert event.old_state == NodeState.BACKUP
        assert event.new_state == NodeState.MASTER
        assert event.vip == "192.168.1.100"

    def test_event_to_dict(self):
        event = FailoverEvent(
            old_state=NodeState.BACKUP,
            new_state=NodeState.MASTER,
            vip="192.168.1.100",
        )
        d = event.to_dict()
        assert d["old_state"] == "BACKUP"
        assert d["new_state"] == "MASTER"
        assert d["vip"] == "192.168.1.100"

    def test_event_message(self):
        event = FailoverEvent(
            old_state=NodeState.BACKUP,
            new_state=NodeState.MASTER,
            vip="192.168.1.100",
        )
        message = event.get_message()
        assert "MASTER" in message
        assert "192.168.1.100" in message

    @pytest.mark.asyncio
    async def test_notify_without_webhook(self, notifier):
        event = FailoverEvent(
            old_state=NodeState.BACKUP,
            new_state=NodeState.MASTER,
            vip="192.168.1.100",
        )
        result = await notifier.notify(event)
        assert result is False

    def test_history(self, notifier):
        event = FailoverEvent(
            old_state=NodeState.BACKUP,
            new_state=NodeState.MASTER,
            vip="192.168.1.100",
        )
        notifier._event_history.append(event)
        history = notifier.get_history()
        assert len(history) == 1


class TestHealthCheckResult:
    def test_creation(self):
        result = HealthCheckResult(
            name="test",
            status=HealthStatus.HEALTHY,
            message="OK",
            latency_ms=10.5,
        )
        assert result.name == "test"
        assert result.status == HealthStatus.HEALTHY
        assert result.message == "OK"
        assert result.latency_ms == 10.5

    def test_to_dict(self):
        result = HealthCheckResult(
            name="test",
            status=HealthStatus.HEALTHY,
            message="OK",
        )
        d = result.to_dict()
        assert d["name"] == "test"
        assert d["status"] == "healthy"


class TestNodeState:
    def test_values(self):
        assert NodeState.MASTER.value == "MASTER"
        assert NodeState.BACKUP.value == "BACKUP"
        assert NodeState.FAULT.value == "FAULT"


class TestHealthStatus:
    def test_values(self):
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"
        assert HealthStatus.UNKNOWN.value == "unknown"


class TestIntegration:
    @pytest.mark.asyncio
    async def test_health_monitor_with_notifier(self):
        monitor = HealthMonitor(check_interval=1)
        notifier = FailoverNotifier(webhook_url=None)

        status_changes = []

        async def callback(name, status):
            status_changes.append((name, status))

        monitor.register_callback(callback)

        async def check():
            return HealthCheckResult("test", HealthStatus.HEALTHY)

        monitor.register_check("test", check)
        await monitor.run_check("test")

        assert len(status_changes) >= 1
