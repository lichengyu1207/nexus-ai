"""
架构集成诊断模块测试
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from backend.services.admin.integration_diagnostic import (
    IntegrationStatus,
    IntegrationPoint,
    IntegrationReport,
    ThreeProvincesSixMinistriesChecker,
    HippocampusMemoryChecker,
    SkillSystemChecker,
    UserProfileChecker,
    run_integration_diagnostic,
    generate_integration_report,
)


class TestIntegrationStatus:
    """测试集成状态枚举"""

    def test_status_values(self):
        assert IntegrationStatus.CONNECTED.value == "connected"
        assert IntegrationStatus.PARTIAL.value == "partial"
        assert IntegrationStatus.DISCONNECTED.value == "disconnected"
        assert IntegrationStatus.NOT_IMPLEMENTED.value == "not_implemented"
        assert IntegrationStatus.ERROR.value == "error"


class TestIntegrationPoint:
    """测试集成点数据类"""

    def test_create_integration_point(self):
        point = IntegrationPoint(
            name="测试集成点",
            description="测试描述",
            status=IntegrationStatus.CONNECTED,
            source="源系统",
            target="目标系统",
            data_flow="数据流向",
            details={"key": "value"},
            suggestions=["建议1"],
        )
        assert point.name == "测试集成点"
        assert point.status == IntegrationStatus.CONNECTED
        assert point.details["key"] == "value"

    def test_default_values(self):
        point = IntegrationPoint(
            name="测试",
            description="描述",
            status=IntegrationStatus.NOT_IMPLEMENTED,
            source="源",
            target="目标",
            data_flow="流",
        )
        assert point.details == {}
        assert point.suggestions == []


class TestIntegrationReport:
    """测试集成报告数据类"""

    def test_create_report(self):
        report = IntegrationReport(
            timestamp="2024-01-01T00:00:00",
            total_points=10,
            connected=5,
            partial=2,
            disconnected=1,
            not_implemented=1,
            errors=1,
        )
        assert report.total_points == 10
        assert report.connected == 5

    def test_to_dict(self):
        report = IntegrationReport(
            timestamp="2024-01-01T00:00:00",
            total_points=10,
            connected=5,
            partial=2,
            disconnected=1,
            not_implemented=1,
            errors=1,
            points=[],
        )
        result = report.to_dict()
        assert result["timestamp"] == "2024-01-01T00:00:00"
        assert result["summary"]["total"] == 10
        assert result["summary"]["health_score"] == 50.0


class TestThreeProvincesSixMinistriesChecker:
    """测试三省六部智能体检查器"""

    @pytest.fixture
    def checker(self):
        return ThreeProvincesSixMinistriesChecker()

    @pytest.fixture
    def mock_db(self):
        db = AsyncMock()
        return db

    @pytest.mark.asyncio
    async def test_check_shangshu_integration_connected(self, checker, mock_db):
        mock_db.execute_read = AsyncMock(return_value=[{"count": 1}])
        checker.db_service = mock_db

        with patch.object(checker, '_check_agent_code_exists', return_value=True):
            point = await checker.check_shangshu_integration()

        assert point.status == IntegrationStatus.CONNECTED
        assert point.details["agent_registered"] is True

    @pytest.mark.asyncio
    async def test_check_shangshu_integration_not_implemented(self, checker, mock_db):
        mock_db.execute_read = AsyncMock(return_value=[{"count": 0}])
        checker.db_service = mock_db

        with patch.object(checker, '_check_agent_code_exists', return_value=False):
            point = await checker.check_shangshu_integration()

        assert point.status == IntegrationStatus.NOT_IMPLEMENTED
        assert "注册尚书省智能体" in point.suggestions[0]

    @pytest.mark.asyncio
    async def test_check_libu_integration(self, checker, mock_db):
        mock_db.execute_read = AsyncMock(return_value=[{"count": 1}])
        checker.db_service = mock_db

        with patch.object(checker, '_check_api_exists', return_value=True):
            point = await checker.check_libu_integration()

        assert point.name == "吏部智能体集成"

    @pytest.mark.asyncio
    async def test_check_hubu_integration(self, checker, mock_db):
        mock_db.execute_read = AsyncMock(return_value=[{"count": 1}])
        checker.db_service = mock_db

        with patch.object(checker, '_check_api_exists', return_value=True):
            point = await checker.check_hubu_integration()

        assert point.name == "户部智能体集成"

    @pytest.mark.asyncio
    async def test_check_gongbu_integration(self, checker, mock_db):
        mock_db.execute_read = AsyncMock(return_value=[{"count": 1}])
        checker.db_service = mock_db

        with patch.object(checker, '_check_api_exists', return_value=True):
            point = await checker.check_gongbu_integration()

        assert point.name == "工部智能体集成"

    @pytest.mark.asyncio
    async def test_check_xingbu_integration(self, checker, mock_db):
        mock_db.execute_read = AsyncMock(side_effect=[
            [{"count": 1}],
            [{"count": 5}],
        ])
        checker.db_service = mock_db

        with patch.object(checker, '_check_api_exists', return_value=True):
            point = await checker.check_xingbu_integration()

        assert point.name == "刑部智能体集成"
        assert point.details.get("recent_audit_count") == 5

    @pytest.mark.asyncio
    async def test_run_all_checks(self, checker):
        with patch.object(checker, 'check_shangshu_integration', return_value=IntegrationPoint(
            name="尚书省", description="", status=IntegrationStatus.CONNECTED,
            source="", target="", data_flow=""
        )):
            with patch.object(checker, 'check_libu_integration', return_value=IntegrationPoint(
                name="吏部", description="", status=IntegrationStatus.CONNECTED,
                source="", target="", data_flow=""
            )):
                with patch.object(checker, 'check_hubu_integration', return_value=IntegrationPoint(
                    name="户部", description="", status=IntegrationStatus.CONNECTED,
                    source="", target="", data_flow=""
                )):
                    with patch.object(checker, 'check_gongbu_integration', return_value=IntegrationPoint(
                        name="工部", description="", status=IntegrationStatus.CONNECTED,
                        source="", target="", data_flow=""
                    )):
                        with patch.object(checker, 'check_xingbu_integration', return_value=IntegrationPoint(
                            name="刑部", description="", status=IntegrationStatus.CONNECTED,
                            source="", target="", data_flow=""
                        )):
                            results = await checker.run_all_checks()

        assert len(results) == 5


class TestHippocampusMemoryChecker:
    """测试海马体记忆系统检查器"""

    @pytest.fixture
    def checker(self):
        return HippocampusMemoryChecker()

    @pytest.fixture
    def mock_db(self):
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_check_memory_write_connected(self, checker, mock_db):
        mock_db.execute_read = AsyncMock(side_effect=[
            [{"table_name": "hippocampus_memories"}],
            [{"count": 10}],
        ])
        checker.db_service = mock_db

        with patch('os.path.exists', return_value=True):
            point = await checker.check_memory_write()

        assert point.details["memory_table_exists"] is True

    @pytest.mark.asyncio
    async def test_check_memory_write_not_implemented(self, checker, mock_db):
        mock_db.execute_read = AsyncMock(return_value=[])
        checker.db_service = mock_db

        with patch('os.path.exists', return_value=False):
            point = await checker.check_memory_write()

        assert point.details["memory_table_exists"] is False
        assert len(point.suggestions) > 0

    @pytest.mark.asyncio
    async def test_check_user_behavior_analysis(self, checker):
        with patch.object(checker, '_check_behavior_api', return_value=True):
            point = await checker.check_user_behavior_analysis()

        assert point.name == "用户行为分析"

    @pytest.mark.asyncio
    async def test_check_user_memory_query(self, checker):
        with patch.object(checker, '_check_api_exists', return_value=True):
            with patch.object(checker, '_check_memory_permission_control', return_value=True):
                point = await checker.check_user_memory_query()

        assert point.name == "用户记忆查询"

    @pytest.mark.asyncio
    async def test_check_memory_permission(self, checker, mock_db):
        mock_db.execute_read = AsyncMock(return_value=[{"column_name": "is_sensitive"}])
        checker.db_service = mock_db

        with patch('os.path.exists', return_value=True):
            point = await checker.check_memory_permission()

        assert point.details["sensitive_flag_exists"] is True

    @pytest.mark.asyncio
    async def test_run_all_checks(self, checker):
        results = await checker.run_all_checks()
        assert len(results) == 4


class TestSkillSystemChecker:
    """测试Skill系统检查器"""

    @pytest.fixture
    def checker(self):
        return SkillSystemChecker()

    @pytest.fixture
    def mock_db(self):
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_check_skill_audit_connected(self, checker, mock_db):
        mock_db.execute_read = AsyncMock(side_effect=[
            [{"table_name": "skills"}],
            [{"count": 3}],
        ])
        checker.db_service = mock_db

        with patch.object(checker, '_check_skill_api', return_value=True):
            point = await checker.check_skill_audit()

        assert point.details["skill_table_exists"] is True
        assert point.details["pending_skills"] == 3

    @pytest.mark.asyncio
    async def test_check_skill_audit_partial(self, checker, mock_db):
        mock_db.execute_read = AsyncMock(return_value=[{"table_name": "skills"}])
        checker.db_service = mock_db

        with patch.object(checker, '_check_skill_api', return_value=False):
            point = await checker.check_skill_audit()

        assert point.status == IntegrationStatus.PARTIAL

    @pytest.mark.asyncio
    async def test_check_skill_takedown(self, checker):
        with patch.object(checker, '_check_skill_api', return_value=True):
            point = await checker.check_skill_takedown()

        assert point.name == "技能下架"

    @pytest.mark.asyncio
    async def test_check_skill_category(self, checker, mock_db):
        mock_db.execute_read = AsyncMock(return_value=[{"table_name": "skill_categories"}])
        checker.db_service = mock_db

        with patch.object(checker, '_check_skill_api', return_value=True):
            point = await checker.check_skill_category()

        assert point.details["category_table_exists"] is True

    @pytest.mark.asyncio
    async def test_check_skill_statistics(self, checker, mock_db):
        mock_db.execute_read = AsyncMock(return_value=[{"table_name": "skill_usage_logs"}])
        checker.db_service = mock_db

        with patch.object(checker, '_check_skill_api', return_value=True):
            point = await checker.check_skill_statistics()

        assert point.details["usage_log_table_exists"] is True

    @pytest.mark.asyncio
    async def test_run_all_checks(self, checker):
        results = await checker.run_all_checks()
        assert len(results) == 4


class TestUserProfileChecker:
    """测试用户画像系统检查器"""

    @pytest.fixture
    def checker(self):
        return UserProfileChecker()

    @pytest.fixture
    def mock_db(self):
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_check_profile_summary_connected(self, checker, mock_db):
        mock_db.execute_read = AsyncMock(side_effect=[
            [{"table_name": "user_profiles"}],
            [{"column_name": "preferences"}, {"column_name": "activity_score"}],
        ])
        checker.db_service = mock_db

        with patch.object(checker, '_check_profile_api', return_value=True):
            point = await checker.check_profile_summary()

        assert point.details["profile_table_exists"] is True
        assert len(point.details["profile_columns"]) == 2

    @pytest.mark.asyncio
    async def test_check_profile_sync(self, checker):
        with patch.object(checker, '_check_sync_logic', return_value=True):
            point = await checker.check_profile_sync()

        assert point.details["sync_logic_exists"] is True

    @pytest.mark.asyncio
    async def test_check_user_tags(self, checker, mock_db):
        mock_db.execute_read = AsyncMock(side_effect=[
            [{"table_name": "user_tags"}],
            [{"count": 50}],
        ])
        checker.db_service = mock_db

        with patch.object(checker, '_check_tag_api', return_value=True):
            point = await checker.check_user_tags()

        assert point.details["tag_table_exists"] is True
        assert point.details["total_tags"] == 50

    @pytest.mark.asyncio
    async def test_check_profile_decoupling(self, checker):
        with patch('os.path.exists', return_value=True):
            with patch.object(checker, '_check_profile_interface', return_value=True):
                point = await checker.check_profile_decoupling()

        assert point.details["decoupling_level"] == "high"

    @pytest.mark.asyncio
    async def test_run_all_checks(self, checker):
        results = await checker.run_all_checks()
        assert len(results) == 4


class TestRunIntegrationDiagnostic:
    """测试完整集成诊断"""

    @pytest.mark.asyncio
    async def test_run_integration_diagnostic(self):
        report = await run_integration_diagnostic()

        assert report.total_points == 17
        assert report.timestamp is not None
        assert len(report.points) == 17

    @pytest.mark.asyncio
    async def test_run_with_mocks(self):
        mock_db = AsyncMock()
        mock_db.execute_read = AsyncMock(return_value=[{"count": 1}])

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=b"2024-01-01T00:00:00")

        report = await run_integration_diagnostic(mock_db, mock_redis)

        assert report is not None
        assert isinstance(report, IntegrationReport)


class TestGenerateIntegrationReport:
    """测试报告生成"""

    def test_generate_report(self):
        points = [
            IntegrationPoint(
                name="尚书省智能体集成",
                description="测试描述",
                status=IntegrationStatus.CONNECTED,
                source="管理员后台",
                target="尚书省智能体",
                data_flow="任务调度",
                details={"agent_registered": True},
                suggestions=[],
            ),
            IntegrationPoint(
                name="记忆系统写入",
                description="测试描述",
                status=IntegrationStatus.NOT_IMPLEMENTED,
                source="管理员后台",
                target="海马体",
                data_flow="日志写入",
                details={},
                suggestions=["创建记忆表"],
            ),
        ]

        report = IntegrationReport(
            timestamp="2024-01-01T00:00:00",
            total_points=2,
            connected=1,
            partial=0,
            disconnected=0,
            not_implemented=1,
            errors=0,
            points=points,
        )

        result = generate_integration_report(report)

        assert "# 架构集成诊断报告" in result
        assert "尚书省智能体集成" in result
        assert "记忆系统写入" in result
        assert "50.0%" in result

    def test_generate_report_empty(self):
        report = IntegrationReport(
            timestamp="2024-01-01T00:00:00",
            total_points=0,
            connected=0,
            partial=0,
            disconnected=0,
            not_implemented=0,
            errors=0,
            points=[],
        )

        result = generate_integration_report(report)

        assert "# 架构集成诊断报告" in result
        assert "总检查点: 0" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
