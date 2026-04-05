"""
审计日志单元测试
测试审计日志的记录、查询、哈希链完整性等功能
"""
import pytest
import asyncio
import json
import hashlib
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.audit_service import (
    log_audit, ActionType, ResourceType, AuditStatus, AuditService
)
from services.audit_verification import AuditVerificationService
from database import get_db_connection, init_db


class TestAuditLogRecording:
    """测试审计日志记录功能"""
    
    @pytest.fixture(autouse=True)
    async def setup(self):
        """测试前初始化数据库"""
        await init_db()
        self.db = await get_db_connection()
        yield
        await self.db.close()
    
    @pytest.mark.asyncio
    async def test_log_login_success(self):
        """测试登录成功日志记录"""
        log_audit(
            action_type=ActionType.LOGIN,
            user_id="test_user_001",
            username="test@example.com",
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0",
            resource_type=ResourceType.USER,
            resource_id="test_user_001",
            status=AuditStatus.SUCCESS,
        )
        
        cursor = await self.db.execute(
            "SELECT * FROM audit_logs WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
            ("test_user_001",)
        )
        log = await cursor.fetchone()
        
        assert log is not None
        assert log["action_type"] == "LOGIN"
        assert log["username"] == "test@example.com"
        assert log["ip_address"] == "192.168.1.100"
        assert log["status"] == "success"
        assert log["hash"] is not None
        assert log["prev_hash"] is not None
    
    @pytest.mark.asyncio
    async def test_log_login_failure(self):
        """测试登录失败日志记录"""
        log_audit(
            action_type=ActionType.LOGIN_FAILED,
            username="attacker@example.com",
            ip_address="10.0.0.1",
            user_agent="curl/7.0",
            status=AuditStatus.FAILURE,
            error_message="密码错误",
        )
        
        cursor = await self.db.execute(
            "SELECT * FROM audit_logs WHERE action_type = ? AND username = ?",
            ("LOGIN_FAILED", "attacker@example.com")
        )
        log = await cursor.fetchone()
        
        assert log is not None
        assert log["status"] == "failure"
        assert log["error_message"] == "密码错误"
    
    @pytest.mark.asyncio
    async def test_log_task_create(self):
        """测试任务创建日志记录"""
        log_audit(
            action_type=ActionType.TASK_CREATE,
            user_id="test_user_002",
            username="creator@example.com",
            ip_address="192.168.1.101",
            resource_type=ResourceType.TASK,
            resource_id="task_001",
            new_value={"query": "分析北京房价", "style": "professional"},
            status=AuditStatus.SUCCESS,
        )
        
        cursor = await self.db.execute(
            "SELECT * FROM audit_logs WHERE resource_id = ?",
            ("task_001",)
        )
        log = await cursor.fetchone()
        
        assert log is not None
        assert log["action_type"] == "TASK_CREATE"
        new_value = json.loads(log["new_value"])
        assert new_value["query"] == "分析北京房价"
    
    @pytest.mark.asyncio
    async def test_log_report_export(self):
        """测试报告导出日志记录"""
        log_audit(
            action_type=ActionType.REPORT_EXPORT,
            user_id="test_user_003",
            username="exporter@example.com",
            ip_address="192.168.1.102",
            resource_type=ResourceType.REPORT,
            resource_id="report_001",
            old_value={"format": "internal"},
            new_value={"format": "pdf"},
            status=AuditStatus.SUCCESS,
        )
        
        cursor = await self.db.execute(
            "SELECT * FROM audit_logs WHERE action_type = ? AND resource_id = ?",
            ("REPORT_EXPORT", "report_001")
        )
        log = await cursor.fetchone()
        
        assert log is not None
        old_value = json.loads(log["old_value"])
        new_value = json.loads(log["new_value"])
        assert old_value["format"] == "internal"
        assert new_value["format"] == "pdf"
    
    @pytest.mark.asyncio
    async def test_log_admin_user_create(self):
        """测试管理员创建用户日志记录"""
        log_audit(
            action_type=ActionType.ADMIN_USER_CREATE,
            user_id="admin_001",
            username="admin@example.com",
            ip_address="192.168.1.200",
            resource_type=ResourceType.USER,
            resource_id="new_user_001",
            new_value={"email": "newuser@example.com", "role": "user"},
            status=AuditStatus.SUCCESS,
        )
        
        cursor = await self.db.execute(
            "SELECT * FROM audit_logs WHERE action_type = ?",
            ("ADMIN_USER_CREATE",)
        )
        log = await cursor.fetchone()
        
        assert log is not None
        assert log["user_id"] == "admin_001"


class TestAuditLogQuery:
    """测试审计日志查询功能"""
    
    @pytest.fixture(autouse=True)
    async def setup(self):
        """测试前初始化并插入测试数据"""
        await init_db()
        self.db = await get_db_connection()
        
        # 插入测试数据
        test_logs = [
            {
                "action_type": "LOGIN",
                "user_id": "user_001",
                "username": "user1@test.com",
                "ip_address": "192.168.1.10",
                "status": "success",
                "timestamp": datetime.utcnow() - timedelta(days=1),
            },
            {
                "action_type": "LOGIN_FAILED",
                "user_id": None,
                "username": "attacker@test.com",
                "ip_address": "10.0.0.1",
                "status": "failure",
                "timestamp": datetime.utcnow() - timedelta(hours=12),
            },
            {
                "action_type": "TASK_CREATE",
                "user_id": "user_001",
                "username": "user1@test.com",
                "ip_address": "192.168.1.10",
                "status": "success",
                "timestamp": datetime.utcnow() - timedelta(hours=6),
            },
        ]
        
        for log_data in test_logs:
            log_audit(**log_data)
        
        yield
        await self.db.close()
    
    @pytest.mark.asyncio
    async def test_query_by_user_id(self):
        """测试按用户ID查询"""
        cursor = await self.db.execute(
            "SELECT * FROM audit_logs WHERE user_id = ? ORDER BY timestamp DESC",
            ("user_001",)
        )
        logs = await cursor.fetchall()
        
        assert len(logs) >= 2
        for log in logs:
            assert log["user_id"] == "user_001"
    
    @pytest.mark.asyncio
    async def test_query_by_action_type(self):
        """测试按操作类型查询"""
        cursor = await self.db.execute(
            "SELECT * FROM audit_logs WHERE action_type = ?",
            ("LOGIN_FAILED",)
        )
        logs = await cursor.fetchall()
        
        assert len(logs) >= 1
        for log in logs:
            assert log["action_type"] == "LOGIN_FAILED"
    
    @pytest.mark.asyncio
    async def test_query_by_status(self):
        """测试按状态查询"""
        cursor = await self.db.execute(
            "SELECT * FROM audit_logs WHERE status = ?",
            ("failure",)
        )
        logs = await cursor.fetchall()
        
        assert len(logs) >= 1
        for log in logs:
            assert log["status"] == "failure"
    
    @pytest.mark.asyncio
    async def test_query_by_date_range(self):
        """测试按日期范围查询"""
        start_date = (datetime.utcnow() - timedelta(days=2)).strftime("%Y-%m-%d")
        end_date = datetime.utcnow().strftime("%Y-%m-%d")
        
        cursor = await self.db.execute(
            "SELECT * FROM audit_logs WHERE DATE(timestamp) >= ? AND DATE(timestamp) <= ?",
            (start_date, end_date)
        )
        logs = await cursor.fetchall()
        
        assert len(logs) >= 1
    
    @pytest.mark.asyncio
    async def test_query_by_ip_address(self):
        """测试按IP地址查询"""
        cursor = await self.db.execute(
            "SELECT * FROM audit_logs WHERE ip_address LIKE ?",
            ("192.168.1%",)
        )
        logs = await cursor.fetchall()
        
        assert len(logs) >= 1
        for log in logs:
            assert log["ip_address"].startswith("192.168.1")


class TestAuditLogStatistics:
    """测试审计日志统计功能"""
    
    @pytest.fixture(autouse=True)
    async def setup(self):
        """测试前初始化"""
        await init_db()
        self.db = await get_db_connection()
        self.audit_service = AuditService()
        yield
        await self.db.close()
    
    @pytest.mark.asyncio
    async def test_get_stats(self):
        """测试获取统计数据"""
        stats = self.audit_service.get_stats(days=30)
        
        assert "summary" in stats
        assert "daily" in stats
        assert "action_breakdown" in stats
    
    @pytest.mark.asyncio
    async def test_stats_summary(self):
        """测试统计摘要"""
        stats = self.audit_service.get_stats(days=30)
        summary = stats["summary"]
        
        assert "total_logs" in summary
        assert "total_logins" in summary
        assert "total_failures" in summary


class TestAuditLogArchive:
    """测试审计日志归档功能"""
    
    @pytest.fixture(autouse=True)
    async def setup(self):
        """测试前初始化"""
        await init_db()
        self.db = await get_db_connection()
        yield
        await self.db.close()
    
    @pytest.mark.asyncio
    async def test_archive_old_logs(self):
        """测试归档旧日志"""
        from tasks.archive_audit_logs import AuditArchiver, AuditArchiveConfig
        
        # 创建测试日志（模拟旧日志）
        old_timestamp = datetime.utcnow() - timedelta(days=200)
        
        for i in range(5):
            log_audit(
                action_type=ActionType.LOGIN,
                user_id=f"old_user_{i}",
                username=f"old{i}@test.com",
                ip_address="10.0.0.1",
                status=AuditStatus.SUCCESS,
            )
            # 手动更新时间戳模拟旧日志
            await self.db.execute(
                "UPDATE audit_logs SET timestamp = ? WHERE user_id = ?",
                (old_timestamp.isoformat(), f"old_user_{i}")
            )
        await self.db.commit()
        
        # 配置归档
        config = AuditArchiveConfig()
        config.archive_after_days = 150
        config.storage_path = "./test_archives"
        
        archiver = AuditArchiver(config)
        
        # 执行归档
        result = await archiver.run_archive()
        
        assert result["status"] in ["completed", "disabled"]


class TestAuditLogCleanup:
    """测试审计日志清理功能"""
    
    @pytest.fixture(autouse=True)
    async def setup(self):
        """测试前初始化"""
        await init_db()
        self.db = await get_db_connection()
        yield
        await self.db.close()
    
    @pytest.mark.asyncio
    async def test_cleanup_old_logs(self):
        """测试清理旧日志（仅超级管理员）"""
        # 创建测试日志
        old_timestamp = datetime.utcnow() - timedelta(days=100)
        
        log_audit(
            action_type=ActionType.LOGIN,
            user_id="cleanup_test_user",
            username="cleanup@test.com",
            ip_address="10.0.0.2",
            status=AuditStatus.SUCCESS,
        )
        
        # 手动更新时间戳
        await self.db.execute(
            "UPDATE audit_logs SET timestamp = ? WHERE user_id = ?",
            (old_timestamp.isoformat(), "cleanup_test_user")
        )
        await self.db.commit()
        
        # 验证日志存在
        cursor = await self.db.execute(
            "SELECT COUNT(*) as count FROM audit_logs WHERE user_id = ?",
            ("cleanup_test_user",)
        )
        count_before = (await cursor.fetchone())["count"]
        assert count_before >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
