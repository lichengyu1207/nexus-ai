"""
管理员后台模块测试
验证认证、权限、核心服务功能
"""
import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import sys
import os
import hashlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestJWTManager:
    """JWT管理器测试"""
    
    def test_create_access_token(self):
        from backend.services.admin.auth_service import JWTManager
        
        jwt_mgr = JWTManager(
            secret_key="test-secret-key-for-testing",
            access_token_expire=60
        )
        
        token = jwt_mgr.create_access_token(
            admin_id="test-admin-id",
            username="testadmin",
            role="admin",
            permissions=["user:read", "user:update"]
        )
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_decode_token(self):
        from backend.services.admin.auth_service import JWTManager
        
        jwt_mgr = JWTManager(
            secret_key="test-secret-key-for-testing",
            access_token_expire=60
        )
        
        token = jwt_mgr.create_access_token(
            admin_id="test-admin-id",
            username="testadmin",
            role="admin",
            permissions=["user:read"]
        )
        
        payload = jwt_mgr.decode_token(token)
        
        assert payload is not None
        assert payload["sub"] == "test-admin-id"
        assert payload["username"] == "testadmin"
        assert payload["role"] == "admin"
        assert "user:read" in payload["permissions"]
    
    def test_expired_token(self):
        from backend.services.admin.auth_service import JWTManager
        
        jwt_mgr = JWTManager(
            secret_key="test-secret-key-for-testing",
            access_token_expire=-1
        )
        
        token = jwt_mgr.create_access_token(
            admin_id="test-admin-id",
            username="testadmin",
            role="admin",
            permissions=[]
        )
        
        time.sleep(1)
        
        payload = jwt_mgr.decode_token(token)
        
        assert payload is None
    
    def test_invalid_token(self):
        from backend.services.admin.auth_service import JWTManager
        
        jwt_mgr = JWTManager(secret_key="test-secret-key")
        
        payload = jwt_mgr.decode_token("invalid.token.here")
        
        assert payload is None
    
    def test_token_hash(self):
        from backend.services.admin.auth_service import JWTManager
        
        jwt_mgr = JWTManager(secret_key="test-secret-key")
        
        token = "test-token-string"
        hash1 = jwt_mgr.get_token_hash(token)
        hash2 = jwt_mgr.get_token_hash(token)
        
        assert hash1 == hash2
        assert len(hash1) == 64


class TestAdminUser:
    """管理员用户模型测试"""
    
    def test_admin_user_creation(self):
        from backend.services.admin.auth_service import AdminUser
        
        admin = AdminUser(
            id="test-id",
            username="testadmin",
            email="admin@test.com",
            role="admin",
            permissions={"permissions": ["user:read", "user:update"]},
            is_active=True,
            is_superuser=False,
            created_at="2024-01-01T00:00:00"
        )
        
        assert admin.id == "test-id"
        assert admin.username == "testadmin"
        assert admin.role == "admin"
        assert admin.is_active is True
    
    def test_has_permission(self):
        from backend.services.admin.auth_service import AdminUser
        
        admin = AdminUser(
            id="test-id",
            username="testadmin",
            email="admin@test.com",
            role="admin",
            permissions={"permissions": ["user:read", "user:update"]},
            is_active=True,
            is_superuser=False,
            created_at="2024-01-01T00:00:00"
        )
        
        assert admin.has_permission("user:read") is True
        assert admin.has_permission("user:update") is True
        assert admin.has_permission("user:delete") is False
    
    def test_superuser_has_all_permissions(self):
        from backend.services.admin.auth_service import AdminUser
        
        admin = AdminUser(
            id="test-id",
            username="superadmin",
            email="super@test.com",
            role="super_admin",
            permissions={},
            is_active=True,
            is_superuser=True,
            created_at="2024-01-01T00:00:00"
        )
        
        assert admin.has_permission("user:read") is True
        assert admin.has_permission("any:permission") is True


class TestRBACService:
    """RBAC权限服务测试"""
    
    @pytest.mark.asyncio
    async def test_check_permission_superuser(self):
        from backend.services.admin.auth_service import RBACService, AdminUser
        
        rbac = RBACService()
        
        admin = AdminUser(
            id="test-id",
            username="superadmin",
            email="super@test.com",
            role="super_admin",
            permissions={},
            is_active=True,
            is_superuser=True,
            created_at="2024-01-01T00:00:00"
        )
        
        result = await rbac.check_permission(admin, "user", "read")
        assert result is True
        
        result = await rbac.check_permission(admin, "any", "action")
        assert result is True
    
    @pytest.mark.asyncio
    async def test_check_permission_wildcard(self):
        from backend.services.admin.auth_service import RBACService, AdminUser
        
        rbac = RBACService()
        
        admin = AdminUser(
            id="test-id",
            username="admin",
            email="admin@test.com",
            role="admin",
            permissions={"permissions": ["user:*"]},
            is_active=True,
            is_superuser=False,
            created_at="2024-01-01T00:00:00"
        )
        
        result = await rbac.check_permission(admin, "user", "read")
        assert result is True
        
        result = await rbac.check_permission(admin, "user", "delete")
        assert result is True
        
        result = await rbac.check_permission(admin, "agent", "read")
        assert result is False


class TestUserListParams:
    """用户列表参数测试"""
    
    def test_default_params(self):
        from backend.services.admin.core_services import UserListParams
        
        params = UserListParams()
        
        assert params.page == 1
        assert params.page_size == 20
        assert params.search is None
        assert params.sort_by == "created_at"
        assert params.sort_order == "desc"
    
    def test_custom_params(self):
        from backend.services.admin.core_services import UserListParams
        
        params = UserListParams(
            page=2,
            page_size=50,
            search="test",
            role="admin",
            status="active",
            sort_by="username",
            sort_order="asc"
        )
        
        assert params.page == 2
        assert params.page_size == 50
        assert params.search == "test"
        assert params.role == "admin"


class TestDiagnosticModule:
    """诊断模块测试"""
    
    def test_check_status_enum(self):
        from backend.services.admin.diagnostic import CheckStatus
        
        assert CheckStatus.PASS.value == "pass"
        assert CheckStatus.FAIL.value == "fail"
        assert CheckStatus.WARNING.value == "warning"
        assert CheckStatus.SKIP.value == "skip"
    
    def test_check_result(self):
        from backend.services.admin.diagnostic import CheckResult, CheckStatus
        
        result = CheckResult(
            name="test_check",
            status=CheckStatus.PASS,
            message="Test passed",
            details={"key": "value"},
            duration_ms=10.5
        )
        
        assert result.name == "test_check"
        assert result.status == CheckStatus.PASS
        assert result.message == "Test passed"
        assert result.details == {"key": "value"}
        assert result.duration_ms == 10.5
    
    def test_diagnostic_report(self):
        from backend.services.admin.diagnostic import DiagnosticReport, CheckResult, CheckStatus
        
        report = DiagnosticReport(
            timestamp="2024-01-01T00:00:00Z",
            total_checks=3,
            passed=2,
            failed=1,
            warnings=0,
            skipped=0,
            results=[
                CheckResult("check1", CheckStatus.PASS, "OK"),
                CheckResult("check2", CheckStatus.PASS, "OK"),
                CheckResult("check3", CheckStatus.FAIL, "Failed")
            ],
            overall_status="degraded"
        )
        
        assert report.total_checks == 3
        assert report.passed == 2
        assert report.failed == 1
        
        report_dict = report.to_dict()
        assert "summary" in report_dict
        assert report_dict["summary"]["total"] == 3


class TestAPIModels:
    """API模型测试"""
    
    def test_login_request(self):
        from backend.routers.admin_router import LoginRequest
        
        request = LoginRequest(username="admin", password="password123")
        
        assert request.username == "admin"
        assert request.password == "password123"
    
    def test_user_update_request(self):
        from backend.routers.admin_router import UserUpdateRequest
        
        request = UserUpdateRequest(
            email="new@email.com",
            role="premium",
            status="active"
        )
        
        assert request.email == "new@email.com"
        assert request.role == "premium"
        assert request.status == "active"
    
    def test_config_update_request(self):
        from backend.routers.admin_router import ConfigUpdateRequest
        
        request = ConfigUpdateRequest(value="test_value", value_type="string")
        
        assert request.value == "test_value"
        assert request.value_type == "string"
    
    def test_points_adjust_request(self):
        from backend.routers.admin_router import PointsAdjustRequest
        
        request = PointsAdjustRequest(points=100, reason="奖励")
        
        assert request.points == 100
        assert request.reason == "奖励"


class TestIntegration:
    """集成测试"""
    
    def test_all_modules_importable(self):
        from backend.services.admin.auth_service import (
            AdminAuthService, RBACService, JWTManager, AdminUser
        )
        from backend.services.admin.core_services import (
            AdminUserManagementService, AdminAuditService, AdminConfigService
        )
        from backend.services.admin.diagnostic import (
            AdminEnvironmentChecker, APIConnectivityTester
        )
        
        assert AdminAuthService is not None
        assert RBACService is not None
        assert JWTManager is not None
        assert AdminUser is not None
        assert AdminUserManagementService is not None
        assert AdminAuditService is not None
        assert AdminConfigService is not None
        assert AdminEnvironmentChecker is not None
        assert APIConnectivityTester is not None
    
    def test_router_importable(self):
        from backend.routers.admin_router import router, include_router
        
        assert router is not None
        assert include_router is not None


def run_tests():
    pytest.main([__file__, "-v", "--tb=short"])


if __name__ == "__main__":
    run_tests()
