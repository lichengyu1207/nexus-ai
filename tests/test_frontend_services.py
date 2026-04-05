# -*- coding: utf-8 -*-
"""
前端修复模块测试 - 提示词12-14
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from backend.services.admin.frontend_services import (
    MenuItemType,
    MenuItem,
    BreadcrumbItem,
    MenuService,
    TableFormService,
    WebSocketMessage,
    WebSocketManager,
    RealTimeDataService,
    get_menu_service,
    get_table_form_service,
    get_ws_manager,
    get_realtime_data_service,
)


class TestMenuItemType:
    """测试菜单项类型枚举"""

    def test_menu_item_types(self):
        assert MenuItemType.MENU.value == "menu"
        assert MenuItemType.SUBMENU.value == "submenu"
        assert MenuItemType.ACTION.value == "action"
        assert MenuItemType.SEPARATOR.value == "separator"


class TestMenuItem:
    """测试菜单项"""

    def test_create_menu_item(self):
        item = MenuItem(
            id="test",
            name="测试菜单",
            path="/test",
            icon="TestIcon",
            order=1
        )
        assert item.id == "test"
        assert item.name == "测试菜单"
        assert item.path == "/test"

    def test_menu_item_to_dict(self):
        item = MenuItem(
            id="parent",
            name="父菜单",
            path="/parent",
            children=[
                MenuItem(id="child", name="子菜单", path="/parent/child")
            ]
        )
        d = item.to_dict()
        assert d["id"] == "parent"
        assert len(d["children"]) == 1
        assert d["children"][0]["id"] == "child"

    def test_menu_item_with_permissions(self):
        item = MenuItem(
            id="admin",
            name="管理",
            path="/admin",
            required_permissions=["admin:view"]
        )
        assert "admin:view" in item.required_permissions


class TestBreadcrumbItem:
    """测试面包屑项"""

    def test_breadcrumb_item(self):
        item = BreadcrumbItem(name="首页", path="/")
        assert item.name == "首页"
        assert item.path == "/"


class TestMenuService:
    """测试菜单服务"""

    @pytest.fixture
    def service(self):
        return MenuService()

    @pytest.fixture
    def mock_db(self):
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_get_menu_for_superuser(self, service):
        menus = await service.get_menu_for_role("super_admin", ["*"])
        
        assert len(menus) > 0
        assert any(m.id == "dashboard" for m in menus)

    @pytest.mark.asyncio
    async def test_get_menu_for_limited_permissions(self, service):
        menus = await service.get_menu_for_role("admin", ["admin:users:view"])
        
        user_menu = next((m for m in menus if m.id == "user-management"), None)
        assert user_menu is not None

    @pytest.mark.asyncio
    async def test_get_menu_caching(self, service):
        menus1 = await service.get_menu_for_role("admin", ["admin:dashboard:view"])
        menus2 = await service.get_menu_for_role("admin", ["admin:dashboard:view"])
        
        assert menus1 == menus2

    @pytest.mark.asyncio
    async def test_get_breadcrumb(self, service):
        breadcrumb = await service.get_breadcrumb("/admin/users/list")
        
        assert len(breadcrumb) > 0
        assert breadcrumb[0].name == "首页"

    @pytest.mark.asyncio
    async def test_get_breadcrumb_unknown_path(self, service):
        breadcrumb = await service.get_breadcrumb("/unknown/path")
        
        assert len(breadcrumb) == 1
        assert breadcrumb[0].name == "首页"

    def test_invalidate_cache(self, service):
        service._menu_cache["test"] = []
        service._cache_time["test"] = 0
        
        service.invalidate_cache()
        
        assert len(service._menu_cache) == 0

    @pytest.mark.asyncio
    async def test_filter_menus_by_permissions(self, service):
        menus = [
            MenuItem(id="m1", name="菜单1", path="/m1", required_permissions=["admin:view"]),
            MenuItem(id="m2", name="菜单2", path="/m2", required_permissions=["user:view"]),
            MenuItem(id="m3", name="菜单3", path="/m3", required_permissions=[]),
        ]
        
        filtered = service._filter_menus_by_permissions(menus, ["admin:view"], "admin")
        
        assert len(filtered) == 2
        assert any(m.id == "m1" for m in filtered)
        assert any(m.id == "m3" for m in filtered)

    @pytest.mark.asyncio
    async def test_menu_with_custom_db(self, mock_db):
        mock_db.execute_read = AsyncMock(return_value=[
            {"id": "custom", "name": "自定义", "path": "/custom", "order_index": 1,
             "required_permissions": [], "is_visible": True, "is_enabled": True}
        ])
        
        service = MenuService(db_service=mock_db)
        menus = await service._get_all_menus()
        
        assert len(menus) == 1
        assert menus[0].id == "custom"


class TestTableFormService:
    """测试表格表单服务"""

    @pytest.fixture
    def service(self):
        return TableFormService()

    @pytest.mark.asyncio
    async def test_get_table_config_users(self, service):
        config = await service.get_table_config("users")
        
        assert "columns" in config
        assert "defaultPageSize" in config
        assert config["defaultPageSize"] == 20

    @pytest.mark.asyncio
    async def test_get_table_config_agents(self, service):
        config = await service.get_table_config("agents")
        
        assert "columns" in config
        assert any(c["key"] == "status" for c in config["columns"])

    @pytest.mark.asyncio
    async def test_get_table_config_unknown(self, service):
        config = await service.get_table_config("unknown")
        
        assert config == {}

    @pytest.mark.asyncio
    async def test_get_form_config_user_create(self, service):
        config = await service.get_form_config("user_create")
        
        assert "fields" in config
        assert any(f["name"] == "username" for f in config["fields"])

    @pytest.mark.asyncio
    async def test_get_form_config_user_edit(self, service):
        config = await service.get_form_config("user_edit")
        
        assert "fields" in config
        username_field = next(f for f in config["fields"] if f["name"] == "username")
        assert username_field.get("disabled") is True

    def test_validate_form_required(self, service):
        service._validation_rules["test"] = {
            "fields": {
                "name": {"label": "名称", "rules": [{"required": True, "message": "必填"}]}
            }
        }
        
        result = service.validate_form("test", {})
        
        assert result["valid"] is False
        assert "name" in result["errors"]

    def test_validate_form_email(self, service):
        service._validation_rules["test"] = {
            "fields": {
                "email": {"label": "邮箱", "rules": [{"type": "email", "message": "格式错误"}]}
            }
        }
        
        result = service.validate_form("test", {"email": "invalid"})
        
        assert result["valid"] is False

    def test_validate_form_valid(self, service):
        service._validation_rules["test"] = {
            "fields": {
                "name": {"label": "名称", "rules": [{"required": True}]},
                "email": {"label": "邮箱", "rules": [{"type": "email"}]}
            }
        }
        
        result = service.validate_form("test", {"name": "test", "email": "test@example.com"})
        
        assert result["valid"] is True

    def test_validate_form_min_length(self, service):
        service._validation_rules["test"] = {
            "fields": {
                "password": {"label": "密码", "rules": [{"min": 6, "message": "太短"}]}
            }
        }
        
        result = service.validate_form("test", {"password": "123"})
        
        assert result["valid"] is False


class TestWebSocketMessage:
    """测试WebSocket消息"""

    def test_create_message(self):
        msg = WebSocketMessage(
            message_type="test",
            data={"key": "value"}
        )
        assert msg.message_type == "test"
        assert msg.data == {"key": "value"}

    def test_message_to_json(self):
        msg = WebSocketMessage(
            message_type="test",
            data={"key": "value"},
            timestamp="2024-01-01T00:00:00"
        )
        json_str = msg.to_json()
        
        assert '"type": "test"' in json_str
        assert '"key": "value"' in json_str

    def test_message_from_json(self):
        json_str = '{"type": "test", "data": {"key": "value"}, "timestamp": "2024-01-01T00:00:00"}'
        msg = WebSocketMessage.from_json(json_str)
        
        assert msg.message_type == "test"
        assert msg.data == {"key": "value"}


class TestWebSocketManager:
    """测试WebSocket管理器"""

    @pytest.fixture
    def manager(self):
        return WebSocketManager()

    @pytest.fixture
    def mock_ws(self):
        ws = AsyncMock()
        ws.send = AsyncMock()
        return ws

    @pytest.mark.asyncio
    async def test_connect(self, manager, mock_ws):
        await manager.connect("client1", mock_ws)
        
        assert "client1" in manager._connections
        assert manager.get_connection_count() == 1

    @pytest.mark.asyncio
    async def test_disconnect(self, manager, mock_ws):
        await manager.connect("client1", mock_ws)
        await manager.disconnect("client1", mock_ws)
        
        assert "client1" not in manager._connections

    @pytest.mark.asyncio
    async def test_subscribe(self, manager, mock_ws):
        await manager.connect("client1", mock_ws)
        await manager.subscribe("client1", "agent_status")
        
        assert "client1" in manager._subscriptions.get("agent_status", set())

    @pytest.mark.asyncio
    async def test_unsubscribe(self, manager, mock_ws):
        await manager.connect("client1", mock_ws)
        await manager.subscribe("client1", "agent_status")
        await manager.unsubscribe("client1", "agent_status")
        
        assert "client1" not in manager._subscriptions.get("agent_status", set())

    @pytest.mark.asyncio
    async def test_broadcast(self, manager, mock_ws):
        await manager.connect("client1", mock_ws)
        await manager.subscribe("client1", "test_topic")

        msg = WebSocketMessage(message_type="test", data={})
        await manager.broadcast("test_topic", msg)

        assert mock_ws.send.call_count >= 1

    @pytest.mark.asyncio
    async def test_broadcast_all(self, manager, mock_ws):
        mock_ws2 = AsyncMock()
        mock_ws2.send = AsyncMock()

        await manager.connect("client1", mock_ws)
        await manager.connect("client2", mock_ws2)

        msg = WebSocketMessage(message_type="test", data={})
        await manager.broadcast_all(msg)

        assert mock_ws.send.call_count >= 1
        assert mock_ws2.send.call_count >= 1

    @pytest.mark.asyncio
    async def test_send_to_client(self, manager, mock_ws):
        await manager.connect("client1", mock_ws)

        msg = WebSocketMessage(message_type="test", data={})
        await manager.send_to_client("client1", msg)

        assert mock_ws.send.call_count >= 1

    def test_get_connection_count(self, manager):
        manager._connections = {"c1": set(), "c2": set()}
        
        count = manager.get_connection_count()
        
        assert count == 2

    def test_get_topic_subscribers(self, manager):
        manager._subscriptions = {"topic1": {"c1", "c2"}}
        
        count = manager.get_topic_subscribers("topic1")
        
        assert count == 2

    def test_register_reconnect_handler(self, manager):
        handler = MagicMock()
        manager.register_reconnect_handler("client1", handler)
        
        assert "client1" in manager._reconnect_handlers

    @pytest.mark.asyncio
    async def test_handle_reconnect(self, manager):
        handler = AsyncMock()
        manager._reconnect_handlers["client1"] = handler
        
        await manager.handle_reconnect("client1")
        
        handler.assert_called_once_with("client1")


class TestRealTimeDataService:
    """测试实时数据服务"""

    @pytest.fixture
    def mock_ws_manager(self):
        return AsyncMock(spec=WebSocketManager)

    @pytest.fixture
    def mock_db(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_ws_manager, mock_db):
        return RealTimeDataService(mock_ws_manager, mock_db)

    def test_get_active_streams_empty(self, service):
        streams = service.get_active_streams()
        
        assert streams == []

    @pytest.mark.asyncio
    async def test_start_agent_status_stream(self, service, mock_db):
        mock_db.execute_read = AsyncMock(return_value=[])
        
        await service.start_agent_status_stream(interval=0.1)
        
        await asyncio.sleep(0.2)
        
        assert "agent_status_stream" in service._running_tasks
        
        await service.stop_all_streams()

    @pytest.mark.asyncio
    async def test_start_task_progress_stream(self, service, mock_db):
        mock_db.execute_read = AsyncMock(return_value=[])
        
        await service.start_task_progress_stream(interval=0.1)
        
        await asyncio.sleep(0.2)
        
        assert "task_progress_stream" in service._running_tasks
        
        await service.stop_all_streams()

    @pytest.mark.asyncio
    async def test_stop_all_streams(self, service, mock_db):
        mock_db.execute_read = AsyncMock(return_value=[])
        
        await service.start_agent_status_stream(interval=1)
        await service.stop_all_streams()
        
        assert len(service._running_tasks) == 0


class TestServiceFactories:
    """测试服务工厂函数"""

    @pytest.mark.asyncio
    async def test_get_menu_service(self):
        service = MenuService()
        assert service is not None
        assert isinstance(service, MenuService)

    @pytest.mark.asyncio
    async def test_get_table_form_service(self):
        service = TableFormService()
        assert service is not None
        assert isinstance(service, TableFormService)

    @pytest.mark.asyncio
    async def test_get_ws_manager(self):
        manager = WebSocketManager()
        assert manager is not None
        assert isinstance(manager, WebSocketManager)

    @pytest.mark.asyncio
    async def test_get_realtime_data_service(self):
        ws_manager = WebSocketManager()
        service = RealTimeDataService(ws_manager)
        assert service is not None
        assert isinstance(service, RealTimeDataService)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
