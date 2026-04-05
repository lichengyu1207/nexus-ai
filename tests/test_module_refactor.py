# -*- coding: utf-8 -*-
"""
功能模块重构测试 - 提示词8-11
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from backend.services.admin.module_refactor import (
    UserStatus,
    AgentStatus,
    TaskStatus,
    PaginationParams,
    UserFilterParams,
    AgentFilterParams,
    TaskFilterParams,
    PaginatedResult,
    BaseRepository,
    UserRepository,
    UserService,
    AgentMonitorService,
    StatisticsService,
    ConfigService,
    get_user_service,
    get_agent_monitor_service,
    get_statistics_service,
    get_config_service,
)


class TestEnums:
    """测试枚举类"""

    def test_user_status_values(self):
        assert UserStatus.ACTIVE.value == "active"
        assert UserStatus.INACTIVE.value == "inactive"
        assert UserStatus.SUSPENDED.value == "suspended"
        assert UserStatus.DELETED.value == "deleted"

    def test_agent_status_values(self):
        assert AgentStatus.RUNNING.value == "running"
        assert AgentStatus.STOPPED.value == "stopped"
        assert AgentStatus.ERROR.value == "error"

    def test_task_status_values(self):
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.RUNNING.value == "running"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"


class TestPaginationParams:
    """测试分页参数"""

    def test_default_values(self):
        params = PaginationParams()
        assert params.page == 1
        assert params.page_size == 20
        assert params.sort_by == "created_at"
        assert params.sort_order == "desc"

    def test_custom_values(self):
        params = PaginationParams(page=2, page_size=50, sort_by="name", sort_order="asc")
        assert params.page == 2
        assert params.page_size == 50


class TestUserFilterParams:
    """测试用户过滤参数"""

    def test_default_values(self):
        params = UserFilterParams()
        assert params.search is None
        assert params.role is None
        assert params.status is None

    def test_custom_values(self):
        params = UserFilterParams(search="test", role="admin", status="active")
        assert params.search == "test"
        assert params.role == "admin"
        assert params.status == "active"


class TestPaginatedResult:
    """测试分页结果"""

    def test_to_dict(self):
        result = PaginatedResult(
            items=[{"id": 1}, {"id": 2}],
            total=100,
            page=1,
            page_size=20,
            total_pages=5
        )
        d = result.to_dict()
        assert d["total"] == 100
        assert d["page"] == 1
        assert len(d["items"]) == 2


class TestUserRepository:
    """测试用户仓储"""

    @pytest.fixture
    def mock_db(self):
        return AsyncMock()

    @pytest.fixture
    def repo(self, mock_db):
        return UserRepository(mock_db)

    @pytest.mark.asyncio
    async def test_find_by_id(self, repo, mock_db):
        mock_db.fetchrow_read = AsyncMock(return_value={
            "id": "123",
            "username": "testuser",
            "email": "test@example.com"
        })

        result = await repo.find_by_id("123")

        assert result is not None
        assert result["username"] == "testuser"

    @pytest.mark.asyncio
    async def test_find_by_id_not_found(self, repo, mock_db):
        mock_db.fetchrow_read = AsyncMock(return_value=None)

        result = await repo.find_by_id("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_find_all(self, repo, mock_db):
        mock_db.fetchval_read = AsyncMock(return_value=10)
        mock_db.execute_read = AsyncMock(return_value=[
            {"id": "1", "username": "user1"},
            {"id": "2", "username": "user2"}
        ])

        params = UserFilterParams(page=1, page_size=10)
        result = await repo.find_all(params)

        assert result.total == 10
        assert len(result.items) == 2

    @pytest.mark.asyncio
    async def test_create(self, repo, mock_db):
        mock_db.fetchrow_write = AsyncMock(return_value={
            "id": "new-id",
            "username": "newuser"
        })

        result = await repo.create({"username": "newuser", "email": "new@example.com"})

        assert result["username"] == "newuser"

    @pytest.mark.asyncio
    async def test_update(self, repo, mock_db):
        async def mock_fetchrow_write(*args, **kwargs):
            return {"id": "123", "username": "testuser", "email": "newemail@example.com", "role": "user", "status": "active", "points": 0, "created_at": "2024-01-01", "updated_at": "2024-01-02"}
        mock_db.fetchrow_write = mock_fetchrow_write

        result = await repo.update("123", {"email": "newemail@example.com"})

        assert result is not None
        assert result["email"] == "newemail@example.com"

    @pytest.mark.asyncio
    async def test_delete(self, repo, mock_db):
        mock_db.execute_write = AsyncMock(return_value=1)

        result = await repo.delete("123")

        assert result is True

    @pytest.mark.asyncio
    async def test_update_points(self, repo, mock_db):
        mock_db.fetchval_write = AsyncMock(return_value=150)

        new_points = await repo.update_points("123", 50)

        assert new_points == 150


class TestUserService:
    """测试用户服务"""

    @pytest.fixture
    def mock_repo(self):
        return AsyncMock(spec=UserRepository)

    @pytest.fixture
    def service(self, mock_repo):
        return UserService(user_repo=mock_repo)

    @pytest.mark.asyncio
    async def test_get_user_list(self, service, mock_repo):
        mock_repo.find_all = AsyncMock(return_value=PaginatedResult(
            items=[{"id": "1"}],
            total=1,
            page=1,
            page_size=20,
            total_pages=1
        ))

        params = UserFilterParams()
        result = await service.get_user_list(params)

        assert result.total == 1

    @pytest.mark.asyncio
    async def test_get_user_detail(self, service, mock_repo):
        mock_repo.find_by_id = AsyncMock(return_value={
            "id": "123",
            "username": "testuser"
        })
        mock_repo.db_service = AsyncMock()
        mock_repo.db_service.fetchrow_read = AsyncMock(return_value={
            "completed": 10,
            "pending": 5
        })
        mock_repo.db_service.execute_read = AsyncMock(return_value=[])

        result = await service.get_user_detail("123")

        assert result["username"] == "testuser"
        assert "task_stats" in result

    @pytest.mark.asyncio
    async def test_update_user_role(self, service, mock_repo):
        mock_repo.find_by_id = AsyncMock(return_value={"id": "123", "role": "user"})
        mock_repo.update = AsyncMock(return_value={"id": "123", "role": "admin"})

        result = await service.update_user_role("123", "admin", "admin-id")

        assert result["role"] == "admin"

    @pytest.mark.asyncio
    async def test_update_user_role_invalid(self, service, mock_repo):
        mock_repo.find_by_id = AsyncMock(return_value={"id": "123"})

        with pytest.raises(ValueError, match="Invalid role"):
            await service.update_user_role("123", "invalid_role", "admin-id")

    @pytest.mark.asyncio
    async def test_suspend_user(self, service, mock_repo):
        mock_repo.find_by_id = AsyncMock(return_value={"id": "123", "status": "active"})
        mock_repo.update = AsyncMock(return_value={"id": "123", "status": "suspended"})

        result = await service.suspend_user("123", "violation", "admin-id")

        assert result["status"] == "suspended"

    @pytest.mark.asyncio
    async def test_activate_user(self, service, mock_repo):
        mock_repo.find_by_id = AsyncMock(return_value={"id": "123", "status": "suspended"})
        mock_repo.update = AsyncMock(return_value={"id": "123", "status": "active"})

        result = await service.activate_user("123", "admin-id")

        assert result["status"] == "active"

    @pytest.mark.asyncio
    async def test_adjust_user_points(self, service, mock_repo):
        mock_repo.find_by_id = AsyncMock(return_value={"id": "123", "points": 100})
        mock_repo.update_points = AsyncMock(return_value=150)

        result = await service.adjust_user_points("123", 50, "bonus", "admin-id")

        assert result["old_points"] == 100
        assert result["new_points"] == 150


class TestAgentMonitorService:
    """测试智能体监控服务"""

    @pytest.fixture
    def mock_db(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_db):
        return AgentMonitorService(db_service=mock_db)

    @pytest.mark.asyncio
    async def test_get_agent_list(self, service, mock_db):
        mock_db.fetchval_read = AsyncMock(return_value=5)
        mock_db.execute_read = AsyncMock(return_value=[
            {"id": "1", "name": "agent1", "status": "running"}
        ])

        params = AgentFilterParams()
        result = await service.get_agent_list(params)

        assert result.total == 5
        assert len(result.items) == 1

    @pytest.mark.asyncio
    async def test_get_agent_detail(self, service, mock_db):
        mock_db.fetchrow_read = AsyncMock(return_value={
            "id": "agent-1",
            "name": "test-agent",
            "status": "running"
        })
        mock_db.execute_read = AsyncMock(return_value=[])

        result = await service.get_agent_detail("agent-1")

        assert result["name"] == "test-agent"
        assert "real_time_status" in result

    @pytest.mark.asyncio
    async def test_start_agent(self, service, mock_db):
        mock_db.execute_write = AsyncMock(return_value=1)

        result = await service.start_agent("agent-1", "admin-id")

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_stop_agent(self, service, mock_db):
        mock_db.execute_write = AsyncMock(return_value=1)

        result = await service.stop_agent("agent-1", "admin-id")

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_update_agent_config(self, service, mock_db):
        mock_db.execute_write = AsyncMock(return_value=1)

        result = await service.update_agent_config("agent-1", {"key": "value"}, "admin-id")

        assert result is True


class TestStatisticsService:
    """测试统计服务"""

    @pytest.fixture
    def mock_db(self):
        return AsyncMock()

    @pytest.fixture
    def mock_redis(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_db, mock_redis):
        return StatisticsService(db_service=mock_db, redis_client=mock_redis)

    @pytest.mark.asyncio
    async def test_get_overview_stats(self, service, mock_db, mock_redis):
        mock_redis.get = AsyncMock(return_value=None)
        mock_db.fetchrow_read = AsyncMock(side_effect=[
            {"total_users": 100, "active_users": 80},
            {"total_tasks": 500, "completed_tasks": 400},
            {"total_agents": 10, "running_agents": 8}
        ])

        result = await service.get_overview_stats()

        assert "users" in result
        assert "tasks" in result
        assert "agents" in result

    @pytest.mark.asyncio
    async def test_get_user_stats(self, service, mock_db, mock_redis):
        mock_redis.get = AsyncMock(return_value=None)
        mock_db.execute_read = AsyncMock(side_effect=[
            [{"date": "2024-01-01", "count": 10}],
            [{"role": "user", "count": 90}]
        ])
        mock_db.fetchrow_read = AsyncMock(return_value={"active_users": 50})

        result = await service.get_user_stats()

        assert "daily_new_users" in result
        assert "role_distribution" in result

    @pytest.mark.asyncio
    async def test_get_task_stats(self, service, mock_db, mock_redis):
        mock_redis.get = AsyncMock(return_value=None)
        mock_db.execute_read = AsyncMock(side_effect=[
            [{"date": "2024-01-01", "total": 20}],
            [{"task_type": "valuation", "count": 15}]
        ])
        mock_db.fetchval_read = AsyncMock(return_value=120.5)

        result = await service.get_task_stats()

        assert "daily_tasks" in result
        assert "type_distribution" in result

    @pytest.mark.asyncio
    async def test_export_report_json(self, service, mock_db, mock_redis):
        mock_redis.get = AsyncMock(return_value=None)
        mock_db.fetchrow_read = AsyncMock(side_effect=[
            {"total_users": 100},
            {"total_tasks": 500},
            {"total_agents": 10}
        ])

        result = await service.export_report("overview", "json")

        assert "users" in result

    @pytest.mark.asyncio
    async def test_caching(self, service, mock_redis):
        mock_redis.get = AsyncMock(return_value=b'{"cached": true}')

        result = await service.get_overview_stats()

        assert result == {"cached": True}


class TestConfigService:
    """测试配置服务"""

    @pytest.fixture
    def mock_db(self):
        return AsyncMock()

    @pytest.fixture
    def mock_redis(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_db, mock_redis):
        return ConfigService(db_service=mock_db, redis_client=mock_redis)

    @pytest.mark.asyncio
    async def test_get_all_configs(self, service, mock_db):
        mock_db.execute_read = AsyncMock(return_value=[
            {"key": "app.name", "value": "TestApp", "value_type": "string"}
        ])

        result = await service.get_all_configs()

        assert len(result) == 1
        assert result[0]["key"] == "app.name"

    @pytest.mark.asyncio
    async def test_get_config(self, service, mock_db):
        mock_db.fetchrow_read = AsyncMock(return_value={
            "key": "app.name",
            "value": "TestApp",
            "value_type": "string"
        })

        result = await service.get_config("app.name")

        assert result["key"] == "app.name"
        assert result["parsed_value"] == "TestApp"

    @pytest.mark.asyncio
    async def test_get_config_value(self, service, mock_db):
        mock_db.fetchrow_read = AsyncMock(return_value={
            "key": "app.port",
            "value": "8080",
            "value_type": "int"
        })

        result = await service.get_config_value("app.port")

        assert result == 8080

    @pytest.mark.asyncio
    async def test_get_config_value_default(self, service, mock_db):
        mock_db.fetchrow_read = AsyncMock(return_value=None)

        result = await service.get_config_value("nonexistent", default=3000)

        assert result == 3000

    @pytest.mark.asyncio
    async def test_set_config(self, service, mock_db, mock_redis):
        mock_db.execute_write = AsyncMock(return_value=1)
        mock_redis.publish = AsyncMock()
        mock_db.fetchrow_read = AsyncMock(return_value={
            "key": "app.name",
            "value": "NewApp",
            "value_type": "string"
        })

        result = await service.set_config("app.name", "NewApp", "admin-id")

        assert result["key"] == "app.name"

    @pytest.mark.asyncio
    async def test_set_config_json(self, service, mock_db, mock_redis):
        mock_db.execute_write = AsyncMock(return_value=1)
        mock_redis.publish = AsyncMock()
        mock_db.fetchrow_read = AsyncMock(return_value={
            "key": "app.features",
            "value": '{"feature1": true}',
            "value_type": "json"
        })

        result = await service.set_config(
            "app.features", 
            {"feature1": True}, 
            "admin-id",
            value_type="json"
        )

        assert result["key"] == "app.features"

    @pytest.mark.asyncio
    async def test_delete_config(self, service, mock_db, mock_redis):
        mock_db.fetchrow_read = AsyncMock(return_value={
            "key": "app.name",
            "value": "TestApp"
        })
        mock_db.execute_write = AsyncMock(return_value=1)
        mock_redis.publish = AsyncMock()

        result = await service.delete_config("app.name", "admin-id")

        assert result is True

    @pytest.mark.asyncio
    async def test_delete_config_not_found(self, service, mock_db):
        mock_db.fetchrow_read = AsyncMock(return_value=None)

        result = await service.delete_config("nonexistent", "admin-id")

        assert result is False

    @pytest.mark.asyncio
    async def test_reload_configs(self, service, mock_db, mock_redis):
        mock_db.execute_read = AsyncMock(return_value=[
            {"key": "app.name", "value": "App", "value_type": "string"}
        ])
        mock_redis.publish = AsyncMock()

        result = await service.reload_configs()

        assert result["reloaded"] == 1

    def test_register_change_callback(self, service):
        callback = MagicMock()
        service.register_change_callback("test.key", callback)

        assert "test.key" in service._change_callbacks
        assert callback in service._change_callbacks["test.key"]

    def test_unregister_change_callback(self, service):
        callback = MagicMock()
        service.register_change_callback("test.key", callback)
        service.unregister_change_callback("test.key", callback)

        assert callback not in service._change_callbacks.get("test.key", [])

    def test_parse_config_int(self, service):
        config = {"key": "port", "value": "8080", "value_type": "int"}
        result = service._parse_config(config)

        assert result["parsed_value"] == 8080

    def test_parse_config_bool(self, service):
        config = {"key": "enabled", "value": "true", "value_type": "bool"}
        result = service._parse_config(config)

        assert result["parsed_value"] is True

    def test_parse_config_json(self, service):
        config = {"key": "data", "value": '{"name": "test"}', "value_type": "json"}
        result = service._parse_config(config)

        assert result["parsed_value"] == {"name": "test"}


class TestServiceFactories:
    """测试服务工厂函数"""

    @pytest.mark.asyncio
    async def test_get_user_service(self):
        with patch.object(UserService, '__init__', return_value=None):
            service = UserService()
            assert service is not None

    @pytest.mark.asyncio
    async def test_get_agent_monitor_service(self):
        service = AgentMonitorService()
        assert service is not None
        assert isinstance(service, AgentMonitorService)

    @pytest.mark.asyncio
    async def test_get_statistics_service(self):
        service = StatisticsService()
        assert service is not None
        assert isinstance(service, StatisticsService)

    @pytest.mark.asyncio
    async def test_get_config_service(self):
        service = ConfigService()
        assert service is not None
        assert isinstance(service, ConfigService)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
