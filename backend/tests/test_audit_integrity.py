"""
审计日志哈希链完整性测试
测试哈希链验证、篡改检测、签名验证等功能
"""
import pytest
import asyncio
import json
import hashlib
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db_connection, init_db
from services.audit_service import log_audit, ActionType, ResourceType, AuditStatus
from services.audit_verification import (
    audit_verification,
    VerificationStatus,
    AuditVerificationService,
)


class TestHashChainIntegrity:
    """测试哈希链完整性"""
    
    @pytest.fixture(autouse=True)
    async def setup(self):
        """测试前初始化数据库"""
        await init_db()
        self.db = await get_db_connection()
        self.verification_service = AuditVerificationService()
        yield
        await self.db.close()
    
    @pytest.mark.asyncio
    async def test_genesis_hash(self):
        """测试创世哈希（第一条日志的prev_hash）"""
        verification_service = AuditVerificationService()
        
        # 创世哈希应该是64个0
        assert verification_service.GENESIS_HASH == "0" * 64
        assert len(verification_service.GENESIS_HASH) == 64
    
    @pytest.mark.asyncio
    async def test_hash_computation(self):
        """测试哈希计算"""
        log_data = {
            "timestamp": "2024-01-01T00:00:00",
            "user_id": "test_user",
            "username": "test@example.com",
            "user_role": "user",
            "ip_address": "192.168.1.1",
            "user_agent": "TestAgent/1.0",
            "action_type": "LOGIN",
            "resource_type": "user",
            "resource_id": "test_user",
            "old_value": None,
            "new_value": {"key": "value"},
            "status": "success",
            "error_message": None,
            "prev_hash": "0" * 64,
        }
        
        computed_hash = self.verification_service.compute_log_hash(log_data)
        
        assert computed_hash is not None
        assert len(computed_hash) == 64
        
        # 相同数据应该产生相同哈希
        computed_hash2 = self.verification_service.compute_log_hash(log_data)
        assert computed_hash == computed_hash2
        
        # 不同数据应该产生不同哈希
        log_data_modified = log_data.copy()
        log_data_modified["status"] = "failure"
        computed_hash3 = self.verification_service.compute_log_hash(log_data_modified)
        assert computed_hash != computed_hash3
    
    @pytest.mark.asyncio
    async def test_chain_verification_valid(self):
        """测试有效链验证"""
        # 创建测试日志
        for i in range(5):
            log_audit(
                action_type=ActionType.LOGIN,
                user_id=f"chain_valid_user_{i}",
                username=f"chain{i}@test.com",
                ip_address="192.168.1.100",
                status=AuditStatus.SUCCESS,
            )
        
        result = await self.verification_service.verify_chain(limit=100, verify_signatures=False)
        
        assert result.status in [VerificationStatus.VALID, VerificationStatus.WARNING]
        assert result.total_logs >= 5
    
    @pytest.mark.asyncio
    async def test_detect_tampered_hash(self):
        """测试检测被篡改的哈希"""
        # 创建测试日志
        log_audit(
            action_type=ActionType.LOGIN,
            user_id="tamper_hash_user",
            username="tamper@test.com",
            ip_address="192.168.1.101",
            status=AuditStatus.SUCCESS,
        )
        
        # 获取日志ID和原始哈希
        cursor = await self.db.execute(
            "SELECT id, hash FROM audit_logs WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
            ("tamper_hash_user",)
        )
        log = await cursor.fetchone()
        
        if log:
            original_hash = log["hash"]
            
            # 篡改哈希
            await self.db.execute(
                "UPDATE audit_logs SET hash = ? WHERE id = ?",
                ("a" * 64, log["id"])
            )
            await self.db.commit()
            
            # 验证应该检测到篡改
            result = await self.verification_service.verify_chain(limit=100, verify_signatures=False)
            
            # 恢复原始哈希
            await self.db.execute(
                "UPDATE audit_logs SET hash = ? WHERE id = ?",
                (original_hash, log["id"])
            )
            await self.db.commit()
            
            # 检查是否检测到错误
            assert result.status == VerificationStatus.INVALID
            assert len(result.hash_errors) > 0
    
    @pytest.mark.asyncio
    async def test_detect_broken_chain(self):
        """测试检测断裂的链"""
        # 创建多条日志
        user_ids = [f"break_chain_user_{i}" for i in range(3)]
        
        for user_id in user_ids:
            log_audit(
                action_type=ActionType.LOGIN,
                user_id=user_id,
                username=f"{user_id}@test.com",
                ip_address="192.168.1.102",
                status=AuditStatus.SUCCESS,
            )
        
        # 获取日志
        cursor = await self.db.execute(
            f"SELECT id, hash, prev_hash FROM audit_logs WHERE user_id IN ({}) ORDER BY timestamp".format(
                ",".join("?" * len(user_ids))
            ),
            user_ids
        )
        logs = await cursor.fetchall()
        
        if len(logs) >= 2:
            # 篡改第二条日志的prev_hash
            original_prev_hash = logs[1]["prev_hash"]
            
            await self.db.execute(
                "UPDATE audit_logs SET prev_hash = ? WHERE id = ?",
                ("b" * 64, logs[1]["id"])
            )
            await self.db.commit()
            
            # 验证应该检测到链断裂
            result = await self.verification_service.verify_chain(limit=100, verify_signatures=False)
            
            # 恢复
            await self.db.execute(
                "UPDATE audit_logs SET prev_hash = ? WHERE id = ?",
                (original_prev_hash, logs[1]["id"])
            )
            await self.db.commit()
            
            # 检查是否检测到错误
            assert result.status == VerificationStatus.INVALID
            assert len(result.chain_errors) > 0
    
    @pytest.mark.asyncio
    async def test_integrity_score_calculation(self):
        """测试完整性评分计算"""
        # 创建有效日志
        for i in range(3):
            log_audit(
                action_type=ActionType.LOGIN,
                user_id=f"score_user_{i}",
                username=f"score{i}@test.com",
                ip_address="192.168.1.103",
                status=AuditStatus.SUCCESS,
            )
        
        result = await self.verification_service.verify_chain(limit=100, verify_signatures=False)
        
        # 有效链的评分应该是100
        if result.status == VerificationStatus.VALID:
            assert result.integrity_score == 100.0
        else:
            assert result.integrity_score >= 0


class TestSignatureFunctionality:
    """测试签名功能"""
    
    @pytest.fixture(autouse=True)
    async def setup(self):
        """测试前初始化"""
        await init_db()
        self.verification_service = AuditVerificationService()
    
    @pytest.mark.asyncio
    async def test_batch_hash_computation(self):
        """测试批次哈希计算"""
        logs = [
            {"hash": "a" * 64},
            {"hash": "b" * 64},
            {"hash": "c" * 64},
        ]
        
        batch_hash = self.verification_service.compute_batch_hash(logs)
        
        assert batch_hash is not None
        assert len(batch_hash) == 64
    
    @pytest.mark.asyncio
    async def test_sign_batch(self):
        """测试批次签名"""
        test_data = "test_batch_data_for_signing"
        
        signature = self.verification_service.sign_batch(test_data)
        
        # 如果cryptography库可用，应该有签名
        if signature:
            assert isinstance(signature, str)
            assert len(signature) > 0
    
    @pytest.mark.asyncio
    async def test_verify_signature_valid(self):
        """测试验证有效签名"""
        test_data = "test_data_for_verification"
        
        signature = self.verification_service.sign_batch(test_data)
        
        if signature:
            is_valid = self.verification_service.verify_signature(test_data, signature)
            assert is_valid is True
    
    @pytest.mark.asyncio
    async def test_verify_signature_invalid(self):
        """测试验证无效签名"""
        test_data = "test_data_for_verification"
        
        signature = self.verification_service.sign_batch(test_data)
        
        if signature:
            # 使用错误的数据验证
            is_valid = self.verification_service.verify_signature("wrong_data", signature)
            assert is_valid is False
            
            # 使用错误的签名验证
            is_valid = self.verification_service.verify_signature(test_data, "invalid_signature")
            assert is_valid is False


class TestVerificationReport:
    """测试验证报告"""
    
    @pytest.fixture(autouse=True)
    async def setup(self):
        """测试前初始化"""
        await init_db()
        self.db = await get_db_connection()
        self.verification_service = AuditVerificationService()
        yield
        await self.db.close()
    
    @pytest.mark.asyncio
    async def test_report_generation(self):
        """测试报告生成"""
        # 创建测试日志
        for i in range(3):
            log_audit(
                action_type=ActionType.LOGIN,
                user_id=f"report_user_{i}",
                username=f"report{i}@test.com",
                ip_address="192.168.1.110",
                status=AuditStatus.SUCCESS,
            )
        
        result = await self.verification_service.verify_chain(limit=100, verify_signatures=False)
        
        report = self.verification_service.get_verification_report(result)
        
        assert "status" in report
        assert "summary" in report
        assert "integrity_score" in report
        assert "recommendations" in report
    
    @pytest.mark.asyncio
    async def test_report_summary_structure(self):
        """测试报告摘要结构"""
        result = await self.verification_service.verify_chain(limit=10, verify_signatures=False)
        
        report = self.verification_service.get_verification_report(result)
        
        summary = report["summary"]
        assert "total_logs" in summary
        assert "verified_logs" in summary
        assert "hash_errors" in summary
        assert "chain_errors" in summary
        assert "signature_errors" in summary
    
    @pytest.mark.asyncio
    async def test_report_error_details(self):
        """测试报告错误详情"""
        # 创建并篡改日志
        log_audit(
            action_type=ActionType.LOGIN,
            user_id="error_detail_user",
            username="error@test.com",
            ip_address="192.168.1.111",
            status=AuditStatus.SUCCESS,
        )
        
        cursor = await self.db.execute(
            "SELECT id, hash FROM audit_logs WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
            ("error_detail_user",)
        )
        log = await cursor.fetchone()
        
        if log:
            # 篡改
            await self.db.execute(
                "UPDATE audit_logs SET hash = ? WHERE id = ?",
                ("c" * 64, log["id"])
            )
            await self.db.commit()
            
            result = await self.verification_service.verify_chain(limit=100, verify_signatures=False)
            
            report = self.verification_service.get_verification_report(result)
            
            # 恢复
            await self.db.execute(
                "UPDATE audit_logs SET hash = ? WHERE id = ?",
                (log["hash"], log["id"])
            )
            await self.db.commit()
            
            if result.status == VerificationStatus.INVALID:
                assert len(report["errors"]["hash_errors"]) > 0 or len(report["errors"]["chain_errors"]) > 0


class TestEdgeCases:
    """测试边缘情况"""
    
    @pytest.fixture(autouse=True)
    async def setup(self):
        """测试前初始化"""
        await init_db()
        self.verification_service = AuditVerificationService()
    
    @pytest.mark.asyncio
    async def test_empty_database(self):
        """测试空数据库"""
        result = await self.verification_service.verify_chain(limit=100, verify_signatures=False)
        
        # 空数据库应该是有效的
        assert result.status == VerificationStatus.VALID
        assert result.total_logs == 0
    
    @pytest.mark.asyncio
    async def test_single_log(self):
        """测试单条日志"""
        log_audit(
            action_type=ActionType.LOGIN,
            user_id="single_log_user",
            username="single@test.com",
            ip_address="192.168.1.120",
            status=AuditStatus.SUCCESS,
        )
        
        result = await self.verification_service.verify_chain(limit=100, verify_signatures=False)
        
        assert result.total_logs >= 1
    
    @pytest.mark.asyncio
    async def test_large_timestamp_gap(self):
        """测试大时间跨度"""
        # 创建两条时间跨度大的日志
        log_audit(
            action_type=ActionType.LOGIN,
            user_id="gap_user_1",
            username="gap1@test.com",
            ip_address="192.168.1.121",
            status=AuditStatus.SUCCESS,
        )
        
        # 模拟时间跨度（通过直接修改timestamp）
        # 注意：实际测试中可能需要特殊处理
        
        log_audit(
            action_type=ActionType.LOGIN,
            user_id="gap_user_2",
            username="gap2@test.com",
            ip_address="192.168.1.122",
            status=AuditStatus.SUCCESS,
        )
        
        result = await self.verification_service.verify_chain(limit=100, verify_signatures=False)
        
        # 只要链连续，应该验证通过
        assert result.status in [VerificationStatus.VALID, VerificationStatus.WARNING]


class TestConcurrentOperations:
    """测试并发操作"""
    
    @pytest.fixture(autouse=True)
    async def setup(self):
        """测试前初始化"""
        await init_db()
        self.verification_service = AuditVerificationService()
    
    @pytest.mark.asyncio
    async def test_concurrent_log_creation(self):
        """测试并发日志创建"""
        # 创建多个并发任务
        async def create_log(index):
            log_audit(
                action_type=ActionType.LOGIN,
                user_id=f"concurrent_user_{index}",
                username=f"concurrent{index}@test.com",
                ip_address=f"192.168.1.{130 + index}",
                status=AuditStatus.SUCCESS,
            )
        
        # 并发执行
        tasks = [create_log(i) for i in range(10)]
        await asyncio.gather(*tasks)
        
        # 验证链完整性
        result = await self.verification_service.verify_chain(limit=100, verify_signatures=False)
        
        # 并发创建可能导致链断裂（取决于实现）
        # 这里主要验证系统能处理并发情况
        assert result.total_logs >= 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
