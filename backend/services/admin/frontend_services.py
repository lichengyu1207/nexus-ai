# -*- coding: utf-8 -*-
"""
前端修复模块 - 提示词12-14
前端布局与菜单修复、表格与表单交互优化、WebSocket实时数据刷新
"""
import asyncio
import json
import logging
import time
from typing import Optional, Dict, Any, List, Set, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import hashlib

logger = logging.getLogger(__name__)


class MenuItemType(Enum):
    MENU = "menu"
    SUBMENU = "submenu"
    ACTION = "action"
    SEPARATOR = "separator"


@dataclass
class MenuItem:
    id: str
    name: str
    path: str
    icon: str = ""
    order: int = 0
    parent_id: Optional[str] = None
    required_permissions: List[str] = field(default_factory=list)
    children: List["MenuItem"] = field(default_factory=list)
    is_visible: bool = True
    is_enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "path": self.path,
            "icon": self.icon,
            "order": self.order,
            "parent_id": self.parent_id,
            "required_permissions": self.required_permissions,
            "children": [c.to_dict() for c in self.children],
            "is_visible": self.is_visible,
            "is_enabled": self.is_enabled
        }


@dataclass
class BreadcrumbItem:
    name: str
    path: str


class MenuService:
    """菜单服务 - 提示词12"""

    def __init__(self, db_service=None, rbac_service=None):
        self.db_service = db_service
        self.rbac_service = rbac_service
        self._menu_cache: Dict[str, List[MenuItem]] = {}
        self._cache_ttl = 300
        self._cache_time: Dict[str, float] = {}

    async def get_menu_for_role(self, role: str, permissions: List[str]) -> List[MenuItem]:
        """根据角色和权限获取菜单"""
        cache_key = f"{role}:{','.join(sorted(permissions))}"
        
        now = time.time()
        if cache_key in self._menu_cache:
            if now - self._cache_time.get(cache_key, 0) < self._cache_ttl:
                return self._menu_cache[cache_key]

        all_menus = await self._get_all_menus()
        
        filtered_menus = self._filter_menus_by_permissions(all_menus, permissions, role)
        
        self._menu_cache[cache_key] = filtered_menus
        self._cache_time[cache_key] = now
        
        return filtered_menus

    async def _get_all_menus(self) -> List[MenuItem]:
        """获取所有菜单"""
        default_menus = self._get_default_menus()
        
        if self.db_service:
            try:
                custom_menus = await self.db_service.execute_read("""
                    SELECT id, name, path, icon, parent_id, order_index, 
                           required_permissions, is_visible, is_enabled
                    FROM admin_menus
                    WHERE is_visible = true
                    ORDER BY order_index
                """)
                
                if custom_menus:
                    return self._build_menu_tree(custom_menus)
            except Exception as e:
                logger.warning(f"Failed to load custom menus: {e}")
        
        return default_menus

    def _get_default_menus(self) -> List[MenuItem]:
        """获取默认菜单"""
        return [
            MenuItem(
                id="dashboard",
                name="仪表盘",
                path="/admin/dashboard",
                icon="DashboardOutlined",
                order=1,
                required_permissions=["admin:dashboard:view"]
            ),
            MenuItem(
                id="user-management",
                name="用户管理",
                path="/admin/users",
                icon="UserOutlined",
                order=2,
                required_permissions=["admin:users:view"],
                children=[
                    MenuItem(
                        id="user-list",
                        name="用户列表",
                        path="/admin/users/list",
                        icon="UnorderedListOutlined",
                        order=1,
                        parent_id="user-management",
                        required_permissions=["admin:users:view"]
                    ),
                    MenuItem(
                        id="user-roles",
                        name="角色管理",
                        path="/admin/users/roles",
                        icon="TeamOutlined",
                        order=2,
                        parent_id="user-management",
                        required_permissions=["admin:roles:view"]
                    ),
                ]
            ),
            MenuItem(
                id="agent-management",
                name="智能体管理",
                path="/admin/agents",
                icon="RobotOutlined",
                order=3,
                required_permissions=["admin:agents:view"],
                children=[
                    MenuItem(
                        id="agent-list",
                        name="智能体列表",
                        path="/admin/agents/list",
                        icon="UnorderedListOutlined",
                        order=1,
                        parent_id="agent-management",
                        required_permissions=["admin:agents:view"]
                    ),
                    MenuItem(
                        id="agent-monitor",
                        name="状态监控",
                        path="/admin/agents/monitor",
                        icon="MonitorOutlined",
                        order=2,
                        parent_id="agent-management",
                        required_permissions=["admin:agents:monitor"]
                    ),
                ]
            ),
            MenuItem(
                id="task-management",
                name="任务管理",
                path="/admin/tasks",
                icon="TaskOutlined",
                order=4,
                required_permissions=["admin:tasks:view"]
            ),
            MenuItem(
                id="statistics",
                name="数据统计",
                path="/admin/statistics",
                icon="BarChartOutlined",
                order=5,
                required_permissions=["admin:statistics:view"]
            ),
            MenuItem(
                id="audit-logs",
                name="审计日志",
                path="/admin/audit",
                icon="AuditOutlined",
                order=6,
                required_permissions=["admin:audit:view"]
            ),
            MenuItem(
                id="system-config",
                name="系统配置",
                path="/admin/config",
                icon="SettingOutlined",
                order=7,
                required_permissions=["admin:config:view"]
            ),
        ]

    def _filter_menus_by_permissions(
        self, 
        menus: List[MenuItem], 
        permissions: List[str],
        role: str
    ) -> List[MenuItem]:
        """根据权限过滤菜单"""
        result = []
        
        is_superuser = role == "super_admin" or "*" in permissions
        
        for menu in menus:
            if not menu.is_visible:
                continue
            
            if is_superuser or self._check_menu_permission(menu, permissions):
                filtered_menu = MenuItem(
                    id=menu.id,
                    name=menu.name,
                    path=menu.path,
                    icon=menu.icon,
                    order=menu.order,
                    parent_id=menu.parent_id,
                    required_permissions=menu.required_permissions,
                    is_visible=menu.is_visible,
                    is_enabled=menu.is_enabled
                )
                
                if menu.children:
                    filtered_children = self._filter_menus_by_permissions(
                        menu.children, permissions, role
                    )
                    filtered_menu.children = filtered_children
                
                if not menu.children or filtered_menu.children:
                    result.append(filtered_menu)
        
        return sorted(result, key=lambda x: x.order)

    def _check_menu_permission(self, menu: MenuItem, permissions: List[str]) -> bool:
        """检查菜单权限"""
        if not menu.required_permissions:
            return True
        
        for required in menu.required_permissions:
            if required in permissions:
                return True
            if required.endswith(":view") and required[:-5] + ":*" in permissions:
                return True
        
        return False

    def _build_menu_tree(self, menu_records: List[Dict]) -> List[MenuItem]:
        """构建菜单树"""
        menu_map = {}
        
        for record in menu_records:
            menu = MenuItem(
                id=record["id"],
                name=record["name"],
                path=record["path"],
                icon=record.get("icon", ""),
                order=record.get("order_index", 0),
                parent_id=record.get("parent_id"),
                required_permissions=record.get("required_permissions", []),
                is_visible=record.get("is_visible", True),
                is_enabled=record.get("is_enabled", True)
            )
            menu_map[menu.id] = menu
        
        root_menus = []
        for menu in menu_map.values():
            if menu.parent_id and menu.parent_id in menu_map:
                menu_map[menu.parent_id].children.append(menu)
            else:
                root_menus.append(menu)
        
        for menu in menu_map.values():
            menu.children.sort(key=lambda x: x.order)
        
        return sorted(root_menus, key=lambda x: x.order)

    async def get_breadcrumb(self, path: str) -> List[BreadcrumbItem]:
        """获取面包屑导航"""
        all_menus = await self._get_all_menus()
        
        path_map = {}
        self._build_path_map(all_menus, path_map)
        
        if path not in path_map:
            return [BreadcrumbItem(name="首页", path="/admin/dashboard")]
        
        breadcrumbs = []
        current = path_map[path]
        
        while current:
            breadcrumbs.insert(0, BreadcrumbItem(name=current.name, path=current.path))
            if current.parent_id and current.parent_id in path_map:
                current = path_map[current.parent_id]
            else:
                current = None
        
        breadcrumbs.insert(0, BreadcrumbItem(name="首页", path="/admin/dashboard"))
        
        return breadcrumbs

    def _build_path_map(self, menus: List[MenuItem], path_map: Dict[str, MenuItem]):
        """构建路径映射"""
        for menu in menus:
            path_map[menu.path] = menu
            path_map[menu.id] = menu
            if menu.children:
                self._build_path_map(menu.children, path_map)

    def invalidate_cache(self):
        """清除缓存"""
        self._menu_cache.clear()
        self._cache_time.clear()


class TableFormService:
    """表格与表单服务 - 提示词13"""

    def __init__(self, db_service=None):
        self.db_service = db_service
        self._validation_rules: Dict[str, Dict[str, Any]] = {}

    async def get_table_config(self, table_type: str) -> Dict[str, Any]:
        """获取表格配置"""
        default_configs = {
            "users": {
                "columns": [
                    {"key": "id", "title": "ID", "width": 80, "sortable": True},
                    {"key": "username", "title": "用户名", "width": 150, "sortable": True, "filterable": True},
                    {"key": "email", "title": "邮箱", "width": 200, "sortable": True, "filterable": True},
                    {"key": "role", "title": "角色", "width": 100, "sortable": True, "filterable": True},
                    {"key": "status", "title": "状态", "width": 100, "sortable": True, "filterable": True},
                    {"key": "created_at", "title": "创建时间", "width": 180, "sortable": True},
                    {"key": "actions", "title": "操作", "width": 200, "fixed": "right"}
                ],
                "defaultPageSize": 20,
                "pageSizeOptions": [10, 20, 50, 100],
                "defaultSort": {"field": "created_at", "order": "desc"},
                "rowKey": "id"
            },
            "agents": {
                "columns": [
                    {"key": "id", "title": "ID", "width": 80, "sortable": True},
                    {"key": "name", "title": "名称", "width": 150, "sortable": True, "filterable": True},
                    {"key": "agent_type", "title": "类型", "width": 120, "sortable": True, "filterable": True},
                    {"key": "status", "title": "状态", "width": 100, "sortable": True, "filterable": True},
                    {"key": "last_heartbeat", "title": "最后心跳", "width": 180, "sortable": True},
                    {"key": "actions", "title": "操作", "width": 200, "fixed": "right"}
                ],
                "defaultPageSize": 20,
                "pageSizeOptions": [10, 20, 50, 100],
                "defaultSort": {"field": "name", "order": "asc"},
                "rowKey": "id"
            },
            "tasks": {
                "columns": [
                    {"key": "id", "title": "ID", "width": 80, "sortable": True},
                    {"key": "task_type", "title": "类型", "width": 120, "sortable": True, "filterable": True},
                    {"key": "status", "title": "状态", "width": 100, "sortable": True, "filterable": True},
                    {"key": "user_id", "title": "用户", "width": 120, "sortable": True},
                    {"key": "created_at", "title": "创建时间", "width": 180, "sortable": True},
                    {"key": "completed_at", "title": "完成时间", "width": 180, "sortable": True},
                    {"key": "actions", "title": "操作", "width": 150, "fixed": "right"}
                ],
                "defaultPageSize": 20,
                "pageSizeOptions": [10, 20, 50, 100],
                "defaultSort": {"field": "created_at", "order": "desc"},
                "rowKey": "id"
            },
            "audit_logs": {
                "columns": [
                    {"key": "id", "title": "ID", "width": 80},
                    {"key": "admin_username", "title": "操作人", "width": 120, "filterable": True},
                    {"key": "action", "title": "操作", "width": 150, "filterable": True},
                    {"key": "resource_type", "title": "资源类型", "width": 120, "filterable": True},
                    {"key": "ip_address", "title": "IP地址", "width": 140},
                    {"key": "created_at", "title": "时间", "width": 180, "sortable": True},
                    {"key": "actions", "title": "详情", "width": 100, "fixed": "right"}
                ],
                "defaultPageSize": 50,
                "pageSizeOptions": [20, 50, 100, 200],
                "defaultSort": {"field": "created_at", "order": "desc"},
                "rowKey": "id"
            }
        }
        
        return default_configs.get(table_type, {})

    async def get_form_config(self, form_type: str) -> Dict[str, Any]:
        """获取表单配置"""
        default_configs = {
            "user_create": {
                "fields": [
                    {"name": "username", "label": "用户名", "type": "text", "required": True, 
                     "rules": [{"required": True, "message": "请输入用户名"}, {"min": 3, "message": "最少3个字符"}]},
                    {"name": "email", "label": "邮箱", "type": "email", "required": True,
                     "rules": [{"required": True, "message": "请输入邮箱"}, {"type": "email", "message": "邮箱格式不正确"}]},
                    {"name": "password", "label": "密码", "type": "password", "required": True,
                     "rules": [{"required": True, "message": "请输入密码"}, {"min": 6, "message": "最少6个字符"}]},
                    {"name": "role", "label": "角色", "type": "select", "required": True,
                     "options": [
                         {"value": "user", "label": "普通用户"},
                         {"value": "premium", "label": "高级用户"},
                         {"value": "enterprise", "label": "企业用户"},
                         {"value": "admin", "label": "管理员"}
                     ]}
                ]
            },
            "user_edit": {
                "fields": [
                    {"name": "username", "label": "用户名", "type": "text", "disabled": True},
                    {"name": "email", "label": "邮箱", "type": "email", "required": True,
                     "rules": [{"required": True, "message": "请输入邮箱"}, {"type": "email", "message": "邮箱格式不正确"}]},
                    {"name": "role", "label": "角色", "type": "select", "required": True,
                     "options": [
                         {"value": "user", "label": "普通用户"},
                         {"value": "premium", "label": "高级用户"},
                         {"value": "enterprise", "label": "企业用户"},
                         {"value": "admin", "label": "管理员"}
                     ]},
                    {"name": "status", "label": "状态", "type": "select", "required": True,
                     "options": [
                         {"value": "active", "label": "激活"},
                         {"value": "inactive", "label": "未激活"},
                         {"value": "suspended", "label": "暂停"}
                     ]}
                ]
            },
            "agent_config": {
                "fields": [
                    {"name": "name", "label": "名称", "type": "text", "required": True},
                    {"name": "agent_type", "label": "类型", "type": "select", "required": True,
                     "options": [
                         {"value": "shangshu", "label": "尚书省"},
                         {"value": "libu", "label": "吏部"},
                         {"value": "hubu", "label": "户部"},
                         {"value": "gongbu", "label": "工部"},
                         {"value": "xingbu", "label": "刑部"}
                     ]},
                    {"name": "max_concurrent_tasks", "label": "最大并发任务", "type": "number", 
                     "default": 10, "rules": [{"type": "number", "min": 1, "max": 100}]},
                    {"name": "timeout_seconds", "label": "超时时间(秒)", "type": "number",
                     "default": 300, "rules": [{"type": "number", "min": 10, "max": 3600}]}
                ]
            },
            "config_edit": {
                "fields": [
                    {"name": "key", "label": "配置键", "type": "text", "required": True},
                    {"name": "value", "label": "配置值", "type": "textarea", "required": True},
                    {"name": "value_type", "label": "值类型", "type": "select", "required": True,
                     "options": [
                         {"value": "string", "label": "字符串"},
                         {"value": "int", "label": "整数"},
                         {"value": "float", "label": "浮点数"},
                         {"value": "bool", "label": "布尔值"},
                         {"value": "json", "label": "JSON"}
                     ]},
                    {"name": "description", "label": "描述", "type": "textarea"}
                ]
            }
        }
        
        return default_configs.get(form_type, {})

    def validate_form(self, form_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """验证表单数据"""
        errors = {}
        
        config = self._validation_rules.get(form_type, {})
        
        for field_name, field_config in config.get("fields", {}).items():
            value = data.get(field_name)
            rules = field_config.get("rules", [])
            
            for rule in rules:
                error = self._validate_field(value, rule, field_config.get("label", field_name))
                if error:
                    if field_name not in errors:
                        errors[field_name] = []
                    errors[field_name].append(error)
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }

    def _validate_field(self, value: Any, rule: Dict[str, Any], label: str) -> Optional[str]:
        """验证单个字段"""
        if rule.get("required") and (value is None or value == ""):
            return rule.get("message", f"{label}不能为空")
        
        if value is None or value == "":
            return None
        
        if "min" in rule and isinstance(value, (str, list)):
            if len(value) < rule["min"]:
                return rule.get("message", f"{label}长度不能少于{rule['min']}")
        
        if "max" in rule and isinstance(value, (str, list)):
            if len(value) > rule["max"]:
                return rule.get("message", f"{label}长度不能超过{rule['max']}")
        
        if "type" in rule:
            if rule["type"] == "email":
                import re
                if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", str(value)):
                    return rule.get("message", "邮箱格式不正确")
            elif rule["type"] == "number":
                try:
                    num = float(value)
                    if "min" in rule and num < rule["min"]:
                        return rule.get("message", f"{label}不能小于{rule['min']}")
                    if "max" in rule and num > rule["max"]:
                        return rule.get("message", f"{label}不能大于{rule['max']}")
                except (ValueError, TypeError):
                    return rule.get("message", f"{label}必须是数字")
        
        return None


class WebSocketMessage:
    """WebSocket消息"""

    def __init__(
        self,
        message_type: str,
        data: Any,
        timestamp: str = None
    ):
        self.message_type = message_type
        self.data = data
        self.timestamp = timestamp or datetime.utcnow().isoformat()

    def to_json(self) -> str:
        return json.dumps({
            "type": self.message_type,
            "data": self.data,
            "timestamp": self.timestamp
        })

    @classmethod
    def from_json(cls, json_str: str) -> "WebSocketMessage":
        data = json.loads(json_str)
        return cls(
            message_type=data.get("type"),
            data=data.get("data"),
            timestamp=data.get("timestamp")
        )


class WebSocketManager:
    """WebSocket管理器 - 提示词14"""

    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        self._connections: Dict[str, Set[Any]] = {}
        self._subscriptions: Dict[str, Set[str]] = {}
        self._reconnect_handlers: Dict[str, Callable] = {}

    async def connect(self, client_id: str, websocket: Any):
        """建立连接"""
        if client_id not in self._connections:
            self._connections[client_id] = set()
        self._connections[client_id].add(websocket)

        await self._send_to_client(client_id, WebSocketMessage(
            message_type="connected",
            data={"client_id": client_id}
        ))

    async def disconnect(self, client_id: str, websocket: Any = None):
        """断开连接"""
        if websocket:
            self._connections.get(client_id, set()).discard(websocket)
            if not self._connections.get(client_id):
                del self._connections[client_id]
        else:
            self._connections.pop(client_id, None)

        for topic in list(self._subscriptions.keys()):
            self._subscriptions[topic].discard(client_id)

    async def subscribe(self, client_id: str, topic: str):
        """订阅主题"""
        if topic not in self._subscriptions:
            self._subscriptions[topic] = set()
        self._subscriptions[topic].add(client_id)

        await self._send_to_client(client_id, WebSocketMessage(
            message_type="subscribed",
            data={"topic": topic}
        ))

    async def unsubscribe(self, client_id: str, topic: str):
        """取消订阅"""
        if topic in self._subscriptions:
            self._subscriptions[topic].discard(client_id)

        await self._send_to_client(client_id, WebSocketMessage(
            message_type="unsubscribed",
            data={"topic": topic}
        ))

    async def broadcast(self, topic: str, message: WebSocketMessage):
        """广播消息到主题"""
        if topic not in self._subscriptions:
            return

        for client_id in list(self._subscriptions[topic]):
            await self._send_to_client(client_id, message)

        if self.redis_client:
            await self._publish_to_redis(topic, message)

    async def broadcast_all(self, message: WebSocketMessage):
        """广播消息到所有客户端"""
        for client_id in list(self._connections.keys()):
            await self._send_to_client(client_id, message)

    async def send_to_client(self, client_id: str, message: WebSocketMessage):
        """发送消息到指定客户端"""
        await self._send_to_client(client_id, message)

    async def _send_to_client(self, client_id: str, message: WebSocketMessage):
        """内部发送方法"""
        connections = self._connections.get(client_id, set())
        for websocket in connections:
            try:
                if hasattr(websocket, 'send'):
                    await websocket.send(message.to_json())
                elif hasattr(websocket, 'send_text'):
                    await websocket.send_text(message.to_json())
            except Exception as e:
                logger.warning(f"Failed to send message to {client_id}: {e}")

    async def _publish_to_redis(self, topic: str, message: WebSocketMessage):
        """发布到Redis"""
        if self.redis_client:
            try:
                await self.redis_client.publish(
                    f"ws:{topic}",
                    message.to_json()
                )
            except Exception as e:
                logger.warning(f"Failed to publish to Redis: {e}")

    def register_reconnect_handler(self, client_id: str, handler: Callable):
        """注册重连处理器"""
        self._reconnect_handlers[client_id] = handler

    async def handle_reconnect(self, client_id: str):
        """处理重连"""
        handler = self._reconnect_handlers.get(client_id)
        if handler:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(client_id)
                else:
                    handler(client_id)
            except Exception as e:
                logger.error(f"Reconnect handler error: {e}")

    def get_connection_count(self) -> int:
        """获取连接数"""
        return len(self._connections)

    def get_topic_subscribers(self, topic: str) -> int:
        """获取主题订阅者数量"""
        return len(self._subscriptions.get(topic, set()))


class RealTimeDataService:
    """实时数据服务"""

    def __init__(self, ws_manager: WebSocketManager, db_service=None):
        self.ws_manager = ws_manager
        self.db_service = db_service
        self._running_tasks: Dict[str, asyncio.Task] = {}

    async def start_agent_status_stream(self, interval: int = 5):
        """启动智能体状态流"""
        task_name = "agent_status_stream"
        
        if task_name in self._running_tasks:
            return

        async def stream():
            while True:
                try:
                    if self.db_service:
                        agents = await self.db_service.execute_read("""
                            SELECT id, name, status, last_heartbeat
                            FROM agent_registry
                        """)
                        
                        await self.ws_manager.broadcast(
                            "agent_status",
                            WebSocketMessage(
                                message_type="agent_status_update",
                                data={"agents": [dict(a) for a in agents]}
                            )
                        )
                except Exception as e:
                    logger.error(f"Agent status stream error: {e}")
                
                await asyncio.sleep(interval)

        self._running_tasks[task_name] = asyncio.create_task(stream())

    async def start_task_progress_stream(self, interval: int = 3):
        """启动任务进度流"""
        task_name = "task_progress_stream"
        
        if task_name in self._running_tasks:
            return

        async def stream():
            while True:
                try:
                    if self.db_service:
                        tasks = await self.db_service.execute_read("""
                            SELECT id, task_type, status, progress, created_at
                            FROM tasks
                            WHERE status = 'running'
                            ORDER BY created_at DESC
                            LIMIT 50
                        """)
                        
                        await self.ws_manager.broadcast(
                            "task_progress",
                            WebSocketMessage(
                                message_type="task_progress_update",
                                data={"tasks": [dict(t) for t in tasks]}
                            )
                        )
                except Exception as e:
                    logger.error(f"Task progress stream error: {e}")
                
                await asyncio.sleep(interval)

        self._running_tasks[task_name] = asyncio.create_task(stream())

    async def start_statistics_stream(self, interval: int = 60):
        """启动统计流"""
        task_name = "statistics_stream"
        
        if task_name in self._running_tasks:
            return

        async def stream():
            while True:
                try:
                    if self.db_service:
                        stats = await self.db_service.fetchrow_read("""
                            SELECT 
                                (SELECT COUNT(*) FROM users WHERE deleted_at IS NULL) as total_users,
                                (SELECT COUNT(*) FROM tasks WHERE created_at > NOW() - INTERVAL '1 hour') as hourly_tasks,
                                (SELECT COUNT(*) FROM agent_registry WHERE status = 'running') as running_agents
                        """)
                        
                        await self.ws_manager.broadcast(
                            "statistics",
                            WebSocketMessage(
                                message_type="statistics_update",
                                data=dict(stats) if stats else {}
                            )
                        )
                except Exception as e:
                    logger.error(f"Statistics stream error: {e}")
                
                await asyncio.sleep(interval)

        self._running_tasks[task_name] = asyncio.create_task(stream())

    async def stop_all_streams(self):
        """停止所有流"""
        for task_name, task in self._running_tasks.items():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        self._running_tasks.clear()

    def get_active_streams(self) -> List[str]:
        """获取活跃流"""
        return list(self._running_tasks.keys())


menu_service: Optional[MenuService] = None
table_form_service: Optional[TableFormService] = None
ws_manager: Optional[WebSocketManager] = None
realtime_data_service: Optional[RealTimeDataService] = None


async def get_menu_service() -> MenuService:
    global menu_service
    if menu_service is None:
        from ..database.high_performance_db import get_db_service
        db = await get_db_service()
        menu_service = MenuService(db)
    return menu_service


async def get_table_form_service() -> TableFormService:
    global table_form_service
    if table_form_service is None:
        from ..database.high_performance_db import get_db_service
        db = await get_db_service()
        table_form_service = TableFormService(db)
    return table_form_service


async def get_ws_manager() -> WebSocketManager:
    global ws_manager
    if ws_manager is None:
        ws_manager = WebSocketManager()
    return ws_manager


async def get_realtime_data_service() -> RealTimeDataService:
    global realtime_data_service
    if realtime_data_service is None:
        ws = await get_ws_manager()
        from ..database.high_performance_db import get_db_service
        db = await get_db_service()
        realtime_data_service = RealTimeDataService(ws, db)
    return realtime_data_service
