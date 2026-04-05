"""
架构集成诊断模块
提示词4-7: 三省六部集成、海马体集成、Skill系统集成、用户画像集成
"""
import asyncio
import json
import logging
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class IntegrationStatus(Enum):
    CONNECTED = "connected"
    PARTIAL = "partial"
    DISCONNECTED = "disconnected"
    NOT_IMPLEMENTED = "not_implemented"
    ERROR = "error"


@dataclass
class IntegrationPoint:
    name: str
    description: str
    status: IntegrationStatus
    source: str
    target: str
    data_flow: str
    details: Dict[str, Any] = field(default_factory=dict)
    suggestions: List[str] = field(default_factory=list)


@dataclass
class IntegrationReport:
    timestamp: str
    total_points: int
    connected: int
    partial: int
    disconnected: int
    not_implemented: int
    errors: int
    points: List[IntegrationPoint] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "summary": {
                "total": self.total_points,
                "connected": self.connected,
                "partial": self.partial,
                "disconnected": self.disconnected,
                "not_implemented": self.not_implemented,
                "errors": self.errors,
                "health_score": round(self.connected / self.total_points * 100, 2) if self.total_points > 0 else 0
            },
            "points": [
                {
                    "name": p.name,
                    "description": p.description,
                    "status": p.status.value,
                    "source": p.source,
                    "target": p.target,
                    "data_flow": p.data_flow,
                    "details": p.details,
                    "suggestions": p.suggestions
                }
                for p in self.points
            ]
        }


class ThreeProvincesSixMinistriesChecker:
    """三省六部智能体架构集成检查器"""

    def __init__(self, db_service=None, redis_client=None):
        self.db_service = db_service
        self.redis_client = redis_client
        self.integration_points: List[IntegrationPoint] = []

    async def check_shangshu_integration(self) -> IntegrationPoint:
        """检查尚书省智能体集成（任务调度）"""
        point = IntegrationPoint(
            name="尚书省智能体集成",
            description="管理员后台通过尚书省智能体调度任务",
            source="管理员后台",
            target="尚书省智能体",
            data_flow="任务调度请求 → 尚书省 → 任务执行",
            status=IntegrationStatus.NOT_IMPLEMENTED,
            details={},
            suggestions=[]
        )

        try:
            if self.db_service:
                result = await self.db_service.execute_read(
                    "SELECT COUNT(*) as count FROM agent_registry WHERE agent_type = 'shangshu' AND status = 'active'"
                )
                if result and len(result) > 0 and result[0].get("count", 0) > 0:
                    point.status = IntegrationStatus.CONNECTED
                    point.details["agent_registered"] = True
                    point.details["active_count"] = result[0].get("count", 0)
                else:
                    point.status = IntegrationStatus.NOT_IMPLEMENTED
                    point.details["agent_registered"] = False
                    point.suggestions.append("注册尚书省智能体到agent_registry表")

            if self.redis_client:
                try:
                    heartbeat = await self.redis_client.get("agent:shangshu:heartbeat")
                    if heartbeat:
                        point.details["last_heartbeat"] = heartbeat.decode() if isinstance(heartbeat, bytes) else heartbeat
                        point.details["is_alive"] = True
                    else:
                        point.details["is_alive"] = False
                        point.suggestions.append("尚书省智能体心跳缺失，检查服务状态")
                except Exception as e:
                    point.details["redis_error"] = str(e)

            code_exists = await self._check_agent_code_exists("shangshu")
            point.details["code_exists"] = code_exists
            if not code_exists:
                point.suggestions.append("创建尚书省智能体实现代码")

        except Exception as e:
            point.status = IntegrationStatus.ERROR
            point.details["error"] = str(e)

        return point

    async def check_libu_integration(self) -> IntegrationPoint:
        """检查吏部智能体集成（用户/智能体管理）"""
        point = IntegrationPoint(
            name="吏部智能体集成",
            description="智能体状态监控通过吏部智能体获取实时状态",
            source="管理员后台",
            target="吏部智能体",
            data_flow="状态查询 → 吏部 → 实时状态返回",
            status=IntegrationStatus.NOT_IMPLEMENTED,
            details={},
            suggestions=[]
        )

        try:
            if self.db_service:
                result = await self.db_service.execute_read(
                    "SELECT COUNT(*) as count FROM agent_registry WHERE agent_type = 'libu' AND status = 'active'"
                )
                if result and len(result) > 0 and result[0].get("count", 0) > 0:
                    point.status = IntegrationStatus.CONNECTED
                    point.details["agent_registered"] = True
                else:
                    point.details["agent_registered"] = False
                    point.suggestions.append("注册吏部智能体到agent_registry表")

            point.details["user_management_api"] = await self._check_api_exists("/api/agents/libu/users")
            point.details["agent_management_api"] = await self._check_api_exists("/api/agents/libu/agents")

            if point.details.get("user_management_api") and point.details.get("agent_management_api"):
                if point.status == IntegrationStatus.NOT_IMPLEMENTED:
                    point.status = IntegrationStatus.PARTIAL
            else:
                point.suggestions.append("实现吏部智能体的用户管理API")
                point.suggestions.append("实现吏部智能体的智能体管理API")

        except Exception as e:
            point.status = IntegrationStatus.ERROR
            point.details["error"] = str(e)

        return point

    async def check_hubu_integration(self) -> IntegrationPoint:
        """检查户部智能体集成（积分管理）"""
        point = IntegrationPoint(
            name="户部智能体集成",
            description="管理员后台使用户部积分管理系统调整用户积分",
            source="管理员后台",
            target="户部智能体",
            data_flow="积分调整请求 → 户部 → 积分更新",
            status=IntegrationStatus.NOT_IMPLEMENTED,
            details={},
            suggestions=[]
        )

        try:
            if self.db_service:
                result = await self.db_service.execute_read(
                    "SELECT COUNT(*) as count FROM agent_registry WHERE agent_type = 'hubu' AND status = 'active'"
                )
                if result and len(result) > 0 and result[0].get("count", 0) > 0:
                    point.status = IntegrationStatus.CONNECTED
                    point.details["agent_registered"] = True
                else:
                    point.details["agent_registered"] = False
                    point.suggestions.append("注册户部智能体到agent_registry表")

            point.details["points_adjust_api"] = await self._check_api_exists("/api/agents/hubu/points/adjust")
            point.details["wallet_api"] = await self._check_api_exists("/api/agents/hubu/wallet")

            if not point.details.get("points_adjust_api"):
                point.suggestions.append("实现户部积分调整API")

        except Exception as e:
            point.status = IntegrationStatus.ERROR
            point.details["error"] = str(e)

        return point

    async def check_gongbu_integration(self) -> IntegrationPoint:
        """检查工部智能体集成（报表生成）"""
        point = IntegrationPoint(
            name="工部智能体集成",
            description="管理员后台通过工部生成报表",
            source="管理员后台",
            target="工部智能体",
            data_flow="报表请求 → 工部 → 报表生成/导出",
            status=IntegrationStatus.NOT_IMPLEMENTED,
            details={},
            suggestions=[]
        )

        try:
            if self.db_service:
                result = await self.db_service.execute_read(
                    "SELECT COUNT(*) as count FROM agent_registry WHERE agent_type = 'gongbu' AND status = 'active'"
                )
                if result and len(result) > 0 and result[0].get("count", 0) > 0:
                    point.status = IntegrationStatus.CONNECTED
                    point.details["agent_registered"] = True
                else:
                    point.details["agent_registered"] = False
                    point.suggestions.append("注册工部智能体到agent_registry表")

            point.details["report_generate_api"] = await self._check_api_exists("/api/agents/gongbu/report/generate")
            point.details["export_api"] = await self._check_api_exists("/api/agents/gongbu/export")

            if not point.details.get("report_generate_api"):
                point.suggestions.append("实现工部报表生成API")

        except Exception as e:
            point.status = IntegrationStatus.ERROR
            point.details["error"] = str(e)

        return point

    async def check_xingbu_integration(self) -> IntegrationPoint:
        """检查刑部智能体集成（审计日志）"""
        point = IntegrationPoint(
            name="刑部智能体集成",
            description="管理员操作日志记录到刑部审计模块",
            source="管理员后台",
            target="刑部智能体",
            data_flow="操作日志 → 刑部 → 审计记录存储",
            status=IntegrationStatus.NOT_IMPLEMENTED,
            details={},
            suggestions=[]
        )

        try:
            if self.db_service:
                result = await self.db_service.execute_read(
                    "SELECT COUNT(*) as count FROM agent_registry WHERE agent_type = 'xingbu' AND status = 'active'"
                )
                if result and len(result) > 0 and result[0].get("count", 0) > 0:
                    point.status = IntegrationStatus.CONNECTED
                    point.details["agent_registered"] = True
                else:
                    point.details["agent_registered"] = False
                    point.suggestions.append("注册刑部智能体到agent_registry表")

            if self.db_service:
                audit_result = await self.db_service.execute_read(
                    "SELECT COUNT(*) as count FROM admin_audit_logs WHERE created_at > NOW() - INTERVAL '1 day'"
                )
                if audit_result and len(audit_result) > 0:
                    point.details["recent_audit_count"] = audit_result[0].get("count", 0)
                    if point.details["recent_audit_count"] > 0:
                        point.details["audit_logging_active"] = True
                    else:
                        point.details["audit_logging_active"] = False
                        point.suggestions.append("启用审计日志记录功能")

            point.details["audit_api"] = await self._check_api_exists("/api/agents/xingbu/audit")

        except Exception as e:
            point.status = IntegrationStatus.ERROR
            point.details["error"] = str(e)

        return point

    async def _check_agent_code_exists(self, agent_type: str) -> bool:
        """检查智能体代码是否存在"""
        possible_paths = [
            f"backend/agents/{agent_type}_agent.py",
            f"backend/services/agents/{agent_type}.py",
            f"backend/agents/three_provinces/{agent_type}.py",
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return True
        return False

    async def _check_api_exists(self, api_path: str) -> bool:
        """检查API路由是否存在"""
        router_files = [
            "backend/routers/agent_router.py",
            "backend/routers/admin_router.py",
            "backend/main.py",
        ]
        for file_path in router_files:
            if os.path.exists(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        if api_path in content:
                            return True
                except Exception:
                    pass
        return False

    async def run_all_checks(self) -> List[IntegrationPoint]:
        """运行所有三省六部集成检查"""
        self.integration_points = [
            await self.check_shangshu_integration(),
            await self.check_libu_integration(),
            await self.check_hubu_integration(),
            await self.check_gongbu_integration(),
            await self.check_xingbu_integration(),
        ]
        return self.integration_points


class HippocampusMemoryChecker:
    """海马体记忆系统集成检查器"""

    def __init__(self, db_service=None, redis_client=None):
        self.db_service = db_service
        self.redis_client = redis_client

    async def check_memory_write(self) -> IntegrationPoint:
        """检查管理员操作日志写入记忆系统"""
        point = IntegrationPoint(
            name="记忆系统写入",
            description="管理员操作日志写入海马体记忆系统",
            source="管理员后台",
            target="海马体记忆系统",
            data_flow="操作日志 → 海马体 → 记忆存储",
            status=IntegrationStatus.NOT_IMPLEMENTED,
            details={},
            suggestions=[]
        )

        try:
            if self.db_service:
                result = await self.db_service.execute_read(
                    "SELECT table_name FROM information_schema.tables WHERE table_name = 'hippocampus_memories'"
                )
                if result and len(result) > 0:
                    point.details["memory_table_exists"] = True
                    point.status = IntegrationStatus.CONNECTED

                    admin_memories = await self.db_service.execute_read(
                        "SELECT COUNT(*) as count FROM hippocampus_memories WHERE source = 'admin'"
                    )
                    if admin_memories and len(admin_memories) > 0:
                        point.details["admin_memory_count"] = admin_memories[0].get("count", 0)
                else:
                    point.details["memory_table_exists"] = False
                    point.suggestions.append("创建海马体记忆表 hippocampus_memories")

            code_exists = os.path.exists("backend/services/memory/hippocampus.py")
            point.details["memory_service_exists"] = code_exists
            if not code_exists:
                point.suggestions.append("创建海马体记忆服务 backend/services/memory/hippocampus.py")

        except Exception as e:
            point.status = IntegrationStatus.ERROR
            point.details["error"] = str(e)

        return point

    async def check_user_behavior_analysis(self) -> IntegrationPoint:
        """检查用户行为分析页面从记忆系统检索数据"""
        point = IntegrationPoint(
            name="用户行为分析",
            description="管理员后台用户行为分析从记忆系统检索数据",
            source="管理员后台",
            target="海马体记忆系统",
            data_flow="行为查询 → 海马体 → 用户行为数据返回",
            status=IntegrationStatus.NOT_IMPLEMENTED,
            details={},
            suggestions=[]
        )

        try:
            behavior_api = await self._check_behavior_api()
            point.details["behavior_analysis_api"] = behavior_api

            if behavior_api:
                point.status = IntegrationStatus.CONNECTED
            else:
                point.suggestions.append("实现用户行为分析API /api/admin/users/behavior")

            if self.db_service:
                result = await self.db_service.execute_read(
                    "SELECT table_name FROM information_schema.tables WHERE table_name = 'user_behaviors'"
                )
                point.details["behavior_table_exists"] = bool(result and len(result) > 0)

        except Exception as e:
            point.status = IntegrationStatus.ERROR
            point.details["error"] = str(e)

        return point

    async def check_user_memory_query(self) -> IntegrationPoint:
        """检查管理员查询用户历史记忆功能"""
        point = IntegrationPoint(
            name="用户记忆查询",
            description="管理员查询用户历史记忆（如咨询记录）",
            source="管理员后台",
            target="海马体记忆系统",
            data_flow="用户ID → 海马体 → 用户记忆返回",
            status=IntegrationStatus.NOT_IMPLEMENTED,
            details={},
            suggestions=[]
        )

        try:
            memory_query_api = await self._check_api_exists("/api/admin/users/{id}/memories")
            point.details["memory_query_api"] = memory_query_api

            if memory_query_api:
                point.status = IntegrationStatus.CONNECTED
            else:
                point.suggestions.append("实现用户记忆查询API /api/admin/users/{id}/memories")

            point.details["permission_control"] = await self._check_memory_permission_control()

        except Exception as e:
            point.status = IntegrationStatus.ERROR
            point.details["error"] = str(e)

        return point

    async def check_memory_permission(self) -> IntegrationPoint:
        """检查记忆系统权限控制"""
        point = IntegrationPoint(
            name="记忆权限控制",
            description="限制管理员仅能查看非敏感记忆",
            source="管理员后台",
            target="海马体记忆系统",
            data_flow="记忆请求 → 权限过滤 → 非敏感记忆返回",
            status=IntegrationStatus.NOT_IMPLEMENTED,
            details={},
            suggestions=[]
        )

        try:
            if self.db_service:
                result = await self.db_service.execute_read(
                    "SELECT column_name FROM information_schema.columns WHERE table_name = 'hippocampus_memories' AND column_name = 'is_sensitive'"
                )
                point.details["sensitive_flag_exists"] = bool(result and len(result) > 0)

                if point.details["sensitive_flag_exists"]:
                    point.status = IntegrationStatus.CONNECTED
                else:
                    point.suggestions.append("在记忆表中添加 is_sensitive 字段标记敏感记忆")

            permission_middleware = await self._check_permission_middleware()
            point.details["permission_middleware"] = permission_middleware
            if not permission_middleware:
                point.suggestions.append("实现记忆访问权限中间件")

        except Exception as e:
            point.status = IntegrationStatus.ERROR
            point.details["error"] = str(e)

        return point

    async def _check_behavior_api(self) -> bool:
        """检查行为分析API"""
        router_files = [
            "backend/routers/admin_router.py",
            "backend/routers/user_router.py",
        ]
        for file_path in router_files:
            if os.path.exists(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        if "behavior" in content.lower() or "behaviour" in content.lower():
                            return True
                except Exception:
                    pass
        return False

    async def _check_api_exists(self, api_path: str) -> bool:
        """检查API是否存在"""
        router_files = [
            "backend/routers/admin_router.py",
            "backend/routers/user_router.py",
        ]
        api_pattern = api_path.replace("{id}", "").rstrip("/").split("/")[-1]
        for file_path in router_files:
            if os.path.exists(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        if api_pattern in content.lower():
                            return True
                except Exception:
                    pass
        return False

    async def _check_memory_permission_control(self) -> bool:
        """检查记忆权限控制"""
        possible_files = [
            "backend/middleware/memory_permission.py",
            "backend/services/memory/permission.py",
        ]
        for file_path in possible_files:
            if os.path.exists(file_path):
                return True
        return False

    async def run_all_checks(self) -> List[IntegrationPoint]:
        """运行所有海马体集成检查"""
        return [
            await self.check_memory_write(),
            await self.check_user_behavior_analysis(),
            await self.check_user_memory_query(),
            await self.check_memory_permission(),
        ]


class SkillSystemChecker:
    """人才市场Skill系统集成检查器"""

    def __init__(self, db_service=None, redis_client=None):
        self.db_service = db_service
        self.redis_client = redis_client

    async def check_skill_audit(self) -> IntegrationPoint:
        """检查技能审核功能"""
        point = IntegrationPoint(
            name="技能审核",
            description="管理员审核开发者上传的技能",
            source="管理员后台",
            target="Skill系统",
            data_flow="审核请求 → Skill系统 → 技能状态更新",
            status=IntegrationStatus.NOT_IMPLEMENTED,
            details={},
            suggestions=[]
        )

        try:
            if self.db_service:
                result = await self.db_service.execute_read(
                    "SELECT table_name FROM information_schema.tables WHERE table_name = 'skills'"
                )
                point.details["skill_table_exists"] = bool(result and len(result) > 0)

                if point.details["skill_table_exists"]:
                    pending = await self.db_service.execute_read(
                        "SELECT COUNT(*) as count FROM skills WHERE status = 'pending'"
                    )
                    if pending and len(pending) > 0:
                        point.details["pending_skills"] = pending[0].get("count", 0)

            audit_api = await self._check_skill_api("audit")
            point.details["audit_api_exists"] = audit_api

            if point.details["skill_table_exists"] and audit_api:
                point.status = IntegrationStatus.CONNECTED
            elif point.details["skill_table_exists"]:
                point.status = IntegrationStatus.PARTIAL
                point.suggestions.append("实现技能审核API /api/admin/skills/{id}/audit")
            else:
                point.suggestions.append("创建skills表存储技能数据")
                point.suggestions.append("实现技能审核API")

        except Exception as e:
            point.status = IntegrationStatus.ERROR
            point.details["error"] = str(e)

        return point

    async def check_skill_takedown(self) -> IntegrationPoint:
        """检查技能下架功能"""
        point = IntegrationPoint(
            name="技能下架",
            description="管理员下架技能",
            source="管理员后台",
            target="Skill系统",
            data_flow="下架请求 → Skill系统 → 技能状态更新",
            status=IntegrationStatus.NOT_IMPLEMENTED,
            details={},
            suggestions=[]
        )

        try:
            takedown_api = await self._check_skill_api("takedown")
            point.details["takedown_api_exists"] = takedown_api

            if takedown_api:
                point.status = IntegrationStatus.CONNECTED
            else:
                point.suggestions.append("实现技能下架API /api/admin/skills/{id}/takedown")

        except Exception as e:
            point.status = IntegrationStatus.ERROR
            point.details["error"] = str(e)

        return point

    async def check_skill_category(self) -> IntegrationPoint:
        """检查技能分类管理功能"""
        point = IntegrationPoint(
            name="技能分类管理",
            description="管理员管理技能分类",
            source="管理员后台",
            target="Skill系统",
            data_flow="分类操作 → Skill系统 → 分类数据更新",
            status=IntegrationStatus.NOT_IMPLEMENTED,
            details={},
            suggestions=[]
        )

        try:
            if self.db_service:
                result = await self.db_service.execute_read(
                    "SELECT table_name FROM information_schema.tables WHERE table_name = 'skill_categories'"
                )
                point.details["category_table_exists"] = bool(result and len(result) > 0)

            category_api = await self._check_skill_api("categories")
            point.details["category_api_exists"] = category_api

            if point.details.get("category_table_exists") and category_api:
                point.status = IntegrationStatus.CONNECTED
            elif point.details.get("category_table_exists"):
                point.status = IntegrationStatus.PARTIAL
                point.suggestions.append("实现技能分类管理API /api/admin/skills/categories")
            else:
                point.suggestions.append("创建skill_categories表")
                point.suggestions.append("实现技能分类管理API")

        except Exception as e:
            point.status = IntegrationStatus.ERROR
            point.details["error"] = str(e)

        return point

    async def check_skill_statistics(self) -> IntegrationPoint:
        """检查技能使用统计功能"""
        point = IntegrationPoint(
            name="技能使用统计",
            description="管理员查看技能使用统计",
            source="管理员后台",
            target="Skill系统",
            data_flow="统计请求 → Skill系统 → 统计数据返回",
            status=IntegrationStatus.NOT_IMPLEMENTED,
            details={},
            suggestions=[]
        )

        try:
            if self.db_service:
                result = await self.db_service.execute_read(
                    "SELECT table_name FROM information_schema.tables WHERE table_name = 'skill_usage_logs'"
                )
                point.details["usage_log_table_exists"] = bool(result and len(result) > 0)

            stats_api = await self._check_skill_api("statistics")
            point.details["statistics_api_exists"] = stats_api

            if point.details.get("usage_log_table_exists") and stats_api:
                point.status = IntegrationStatus.CONNECTED
            else:
                point.suggestions.append("创建skill_usage_logs表记录技能使用日志")
                point.suggestions.append("实现技能统计API /api/admin/skills/statistics")

        except Exception as e:
            point.status = IntegrationStatus.ERROR
            point.details["error"] = str(e)

        return point

    async def _check_skill_api(self, api_type: str) -> bool:
        """检查技能相关API"""
        router_files = [
            "backend/routers/admin_router.py",
            "backend/routers/skill_router.py",
        ]
        for file_path in router_files:
            if os.path.exists(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read().lower()
                        if f"skill" in content and api_type in content:
                            return True
                except Exception:
                    pass
        return False

    async def run_all_checks(self) -> List[IntegrationPoint]:
        """运行所有Skill系统检查"""
        return [
            await self.check_skill_audit(),
            await self.check_skill_takedown(),
            await self.check_skill_category(),
            await self.check_skill_statistics(),
        ]


class UserProfileChecker:
    """用户画像系统集成检查器"""

    def __init__(self, db_service=None, redis_client=None):
        self.db_service = db_service
        self.redis_client = redis_client

    async def check_profile_summary(self) -> IntegrationPoint:
        """检查用户列表展示画像摘要"""
        point = IntegrationPoint(
            name="用户画像摘要",
            description="用户列表展示用户画像摘要（偏好、活跃度）",
            source="管理员后台",
            target="用户画像系统",
            data_flow="用户列表请求 → 画像系统 → 画像摘要合并",
            status=IntegrationStatus.NOT_IMPLEMENTED,
            details={},
            suggestions=[]
        )

        try:
            if self.db_service:
                result = await self.db_service.execute_read(
                    "SELECT table_name FROM information_schema.tables WHERE table_name = 'user_profiles'"
                )
                point.details["profile_table_exists"] = bool(result and len(result) > 0)

                if point.details["profile_table_exists"]:
                    columns = await self.db_service.execute_read(
                        "SELECT column_name FROM information_schema.columns WHERE table_name = 'user_profiles'"
                    )
                    point.details["profile_columns"] = [c.get("column_name") for c in columns] if columns else []

            profile_api = await self._check_profile_api()
            point.details["profile_api_exists"] = profile_api

            if point.details.get("profile_table_exists") and profile_api:
                point.status = IntegrationStatus.CONNECTED
            elif point.details.get("profile_table_exists"):
                point.status = IntegrationStatus.PARTIAL
                point.suggestions.append("在用户列表API中集成画像摘要数据")
            else:
                point.suggestions.append("创建user_profiles表存储用户画像")
                point.suggestions.append("实现用户画像API")

        except Exception as e:
            point.status = IntegrationStatus.ERROR
            point.details["error"] = str(e)

        return point

    async def check_profile_sync(self) -> IntegrationPoint:
        """检查用户信息修改同步更新画像"""
        point = IntegrationPoint(
            name="画像同步更新",
            description="管理员修改用户信息时同步更新用户画像",
            source="管理员后台",
            target="用户画像系统",
            data_flow="用户信息修改 → 画像系统 → 画像字段更新",
            status=IntegrationStatus.NOT_IMPLEMENTED,
            details={},
            suggestions=[]
        )

        try:
            sync_logic = await self._check_sync_logic()
            point.details["sync_logic_exists"] = sync_logic

            if sync_logic:
                point.status = IntegrationStatus.CONNECTED
            else:
                point.suggestions.append("在用户更新服务中添加画像同步逻辑")
                point.suggestions.append("实现画像字段映射配置")

        except Exception as e:
            point.status = IntegrationStatus.ERROR
            point.details["error"] = str(e)

        return point

    async def check_user_tags(self) -> IntegrationPoint:
        """检查用户标签管理功能"""
        point = IntegrationPoint(
            name="用户标签管理",
            description="管理员手动添加或修改用户标签",
            source="管理员后台",
            target="用户画像系统",
            data_flow="标签操作 → 画像系统 → 标签数据更新",
            status=IntegrationStatus.NOT_IMPLEMENTED,
            details={},
            suggestions=[]
        )

        try:
            if self.db_service:
                result = await self.db_service.execute_read(
                    "SELECT table_name FROM information_schema.tables WHERE table_name = 'user_tags'"
                )
                point.details["tag_table_exists"] = bool(result and len(result) > 0)

                if point.details["tag_table_exists"]:
                    tag_count = await self.db_service.execute_read(
                        "SELECT COUNT(*) as count FROM user_tags"
                    )
                    if tag_count and len(tag_count) > 0:
                        point.details["total_tags"] = tag_count[0].get("count", 0)

            tag_api = await self._check_tag_api()
            point.details["tag_api_exists"] = tag_api

            if point.details.get("tag_table_exists") and tag_api:
                point.status = IntegrationStatus.CONNECTED
            elif point.details.get("tag_table_exists"):
                point.status = IntegrationStatus.PARTIAL
                point.suggestions.append("实现用户标签管理API /api/admin/users/{id}/tags")
            else:
                point.suggestions.append("创建user_tags表存储用户标签")
                point.suggestions.append("实现用户标签管理API")

        except Exception as e:
            point.status = IntegrationStatus.ERROR
            point.details["error"] = str(e)

        return point

    async def check_profile_decoupling(self) -> IntegrationPoint:
        """检查画像系统解耦"""
        point = IntegrationPoint(
            name="画像系统解耦",
            description="代码是否与画像系统解耦",
            source="管理员后台",
            target="用户画像系统",
            data_flow="解耦调用 → 画像服务 → 数据返回",
            status=IntegrationStatus.NOT_IMPLEMENTED,
            details={},
            suggestions=[]
        )

        try:
            profile_service = os.path.exists("backend/services/profile/profile_service.py")
            profile_interface = await self._check_profile_interface()

            point.details["profile_service_exists"] = profile_service
            point.details["profile_interface_exists"] = profile_interface

            if profile_service and profile_interface:
                point.status = IntegrationStatus.CONNECTED
                point.details["decoupling_level"] = "high"
            elif profile_service:
                point.status = IntegrationStatus.PARTIAL
                point.details["decoupling_level"] = "medium"
                point.suggestions.append("创建画像服务接口抽象层")
            else:
                point.details["decoupling_level"] = "low"
                point.suggestions.append("创建独立的画像服务模块")
                point.suggestions.append("定义画像服务接口")

        except Exception as e:
            point.status = IntegrationStatus.ERROR
            point.details["error"] = str(e)

        return point

    async def _check_profile_api(self) -> bool:
        """检查画像API"""
        router_files = [
            "backend/routers/admin_router.py",
            "backend/routers/user_router.py",
        ]
        for file_path in router_files:
            if os.path.exists(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read().lower()
                        if "profile" in content:
                            return True
                except Exception:
                    pass
        return False

    async def _check_sync_logic(self) -> bool:
        """检查同步逻辑"""
        service_files = [
            "backend/services/admin/core_services.py",
            "backend/services/user/user_service.py",
        ]
        for file_path in service_files:
            if os.path.exists(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read().lower()
                        if "profile" in content and "sync" in content:
                            return True
                        if "update_profile" in content:
                            return True
                except Exception:
                    pass
        return False

    async def _check_tag_api(self) -> bool:
        """检查标签API"""
        router_files = [
            "backend/routers/admin_router.py",
            "backend/routers/user_router.py",
        ]
        for file_path in router_files:
            if os.path.exists(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read().lower()
                        if "tag" in content:
                            return True
                except Exception:
                    pass
        return False

    async def _check_profile_interface(self) -> bool:
        """检查画像接口定义"""
        interface_files = [
            "backend/services/profile/interface.py",
            "backend/interfaces/profile_interface.py",
        ]
        for file_path in interface_files:
            if os.path.exists(file_path):
                return True
        return False

    async def run_all_checks(self) -> List[IntegrationPoint]:
        """运行所有用户画像检查"""
        return [
            await self.check_profile_summary(),
            await self.check_profile_sync(),
            await self.check_user_tags(),
            await self.check_profile_decoupling(),
        ]


async def run_integration_diagnostic(db_service=None, redis_client=None) -> IntegrationReport:
    """运行完整的架构集成诊断"""
    timestamp = datetime.now().isoformat()

    three_provinces_checker = ThreeProvincesSixMinistriesChecker(db_service, redis_client)
    hippocampus_checker = HippocampusMemoryChecker(db_service, redis_client)
    skill_checker = SkillSystemChecker(db_service, redis_client)
    profile_checker = UserProfileChecker(db_service, redis_client)

    three_provinces_results = await three_provinces_checker.run_all_checks()
    hippocampus_results = await hippocampus_checker.run_all_checks()
    skill_results = await skill_checker.run_all_checks()
    profile_results = await profile_checker.run_all_checks()

    all_points = three_provinces_results + hippocampus_results + skill_results + profile_results

    status_counts = {
        IntegrationStatus.CONNECTED: 0,
        IntegrationStatus.PARTIAL: 0,
        IntegrationStatus.DISCONNECTED: 0,
        IntegrationStatus.NOT_IMPLEMENTED: 0,
        IntegrationStatus.ERROR: 0,
    }

    for point in all_points:
        status_counts[point.status] += 1

    report = IntegrationReport(
        timestamp=timestamp,
        total_points=len(all_points),
        connected=status_counts[IntegrationStatus.CONNECTED],
        partial=status_counts[IntegrationStatus.PARTIAL],
        disconnected=status_counts[IntegrationStatus.DISCONNECTED],
        not_implemented=status_counts[IntegrationStatus.NOT_IMPLEMENTED],
        errors=status_counts[IntegrationStatus.ERROR],
        points=all_points,
    )

    return report


def generate_integration_report(report: IntegrationReport) -> str:
    """生成集成诊断报告"""
    lines = [
        "# 架构集成诊断报告",
        f"\n**诊断时间**: {report.timestamp}",
        f"\n## 总体状态\n",
        f"- 总检查点: {report.total_points}",
        f"- 已连接: {report.connected} ✅",
        f"- 部分连接: {report.partial} ⚠️",
        f"- 未实现: {report.not_implemented} ❌",
        f"- 错误: {report.errors} 🔴",
        f"- 健康度: {round(report.connected / report.total_points * 100, 2) if report.total_points > 0 else 0}%",
    ]

    three_provinces = [p for p in report.points if "省" in p.name or "部" in p.name]
    hippocampus = [p for p in report.points if "记忆" in p.name or "海马" in p.name]
    skill = [p for p in report.points if "技能" in p.name]
    profile = [p for p in report.points if "画像" in p.name or "标签" in p.name]

    def add_section(title: str, points: List[IntegrationPoint]):
        lines.append(f"\n## {title}\n")
        for point in points:
            status_icon = {
                IntegrationStatus.CONNECTED: "✅",
                IntegrationStatus.PARTIAL: "⚠️",
                IntegrationStatus.DISCONNECTED: "❌",
                IntegrationStatus.NOT_IMPLEMENTED: "⏭️",
                IntegrationStatus.ERROR: "🔴",
            }.get(point.status, "❓")

            lines.append(f"### {status_icon} {point.name}")
            lines.append(f"- 描述: {point.description}")
            lines.append(f"- 数据流: {point.data_flow}")
            lines.append(f"- 状态: {point.status.value}")

            if point.details:
                lines.append("- 详情:")
                for key, value in point.details.items():
                    lines.append(f"  - {key}: {value}")

            if point.suggestions:
                lines.append("- 建议:")
                for suggestion in point.suggestions:
                    lines.append(f"  - {suggestion}")
            lines.append("")

    add_section("三省六部智能体集成", three_provinces)
    add_section("海马体记忆系统集成", hippocampus)
    add_section("Skill系统集成", skill)
    add_section("用户画像系统集成", profile)

    return "\n".join(lines)


if __name__ == "__main__":
    async def main():
        print("=" * 60)
        print("架构集成诊断")
        print("=" * 60)

        report = await run_integration_diagnostic()
        print(generate_integration_report(report))

    asyncio.run(main())
