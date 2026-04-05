"""
管理员API权限测试
测试不同角色用户对管理员API的访问权限
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from main import app


@pytest.fixture
def client():
    """测试客户端"""
    return TestClient(app)


@pytest.fixture
def mock_user():
    """普通用户"""
    return {
        "id": "user-123",
        "email": "user@example.com",
        "full_name": "普通用户",
        "role": "user",
        "is_admin": False,
        "permissions": {}
    }


@pytest.fixture
def mock_admin():
    """管理员用户"""
    return {
        "id": "admin-123",
        "email": "admin@example.com",
        "full_name": "管理员",
        "role": "admin",
        "is_admin": True,
        "permissions": {
            "can_manage_users": True,
            "can_view_logs": True,
            "can_manage_teams": True,
            "can_export_data": True
        }
    }


@pytest.fixture
def mock_super_admin():
    """超级管理员用户"""
    return {
        "id": "super-admin-123",
        "email": "superadmin@example.com",
        "full_name": "超级管理员",
        "role": "super_admin",
        "is_admin": True,
        "permissions": {
            "can_manage_users": True,
            "can_view_logs": True,
            "can_manage_system": True,
            "can_manage_teams": True,
            "can_export_data": True,
            "can_view_all_reports": True
        }
    }


def create_auth_header(user_id: str):
    """创建认证头"""
    from auth import create_access_token
    token = create_access_token(data={"sub": user_id})
    return {"Authorization": f"Bearer {token}"}


class TestAdminUsersAPI:
    """用户管理API权限测试"""

    @patch("auth.get_current_user")
    def test_list_users_as_user(self, mock_get_user, client, mock_user):
        """普通用户无法访问用户列表"""
        mock_get_user.return_value = mock_user
        
        response = client.get("/api/admin/users")
        
        assert response.status_code == 403
        assert "权限不足" in response.json().get("detail", "")

    @patch("auth.get_current_user")
    def test_list_users_as_admin(self, mock_get_user, client, mock_admin):
        """管理员可以访问用户列表"""
        mock_get_user.return_value = mock_admin
        
        with patch("database.AdminDB.get_all_users", new_callable=AsyncMock) as mock_db:
            mock_db.return_value = []
            with patch("database.AdminDB.get_users_count", new_callable=AsyncMock) as mock_count:
                mock_count.return_value = 0
                
                response = client.get("/api/admin/users")
                
                assert response.status_code == 200

    @patch("auth.get_current_user")
    def test_create_user_as_admin(self, mock_get_user, client, mock_admin):
        """普通管理员无法创建用户"""
        mock_get_user.return_value = mock_admin
        
        response = client.post("/api/admin/users", json={
            "email": "newuser@example.com",
            "password": "password123",
            "role": "user"
        })
        
        assert response.status_code == 403

    @patch("auth.get_current_user")
    def test_create_user_as_super_admin(self, mock_get_user, client, mock_super_admin):
        """超级管理员可以创建用户"""
        mock_get_user.return_value = mock_super_admin
        
        with patch("database.UserDB.get_user_by_email", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None
            with patch("database.UserDB.create_user", new_callable=AsyncMock) as mock_create:
                mock_create.return_value = True
                with patch("database.UserDB.get_user_by_id", new_callable=AsyncMock) as mock_get_id:
                    mock_get_id.return_value = {
                        "id": "new-user-123",
                        "email": "newuser@example.com",
                        "full_name": None,
                        "role": "user",
                        "is_admin": False,
                        "permissions": "{}",
                        "created_at": "2024-01-01T00:00:00"
                    }
                    
                    response = client.post("/api/admin/users", json={
                        "email": "newuser@example.com",
                        "password": "password123",
                        "role": "user"
                    })
                    
                    assert response.status_code == 201

    @patch("auth.get_current_user")
    def test_delete_user_as_admin(self, mock_get_user, client, mock_admin):
        """普通管理员无法删除用户"""
        mock_get_user.return_value = mock_admin
        
        response = client.delete("/api/admin/users/some-user-id")
        
        assert response.status_code == 403

    @patch("auth.get_current_user")
    def test_delete_user_as_super_admin(self, mock_get_user, client, mock_super_admin):
        """超级管理员可以删除用户"""
        mock_get_user.return_value = mock_super_admin
        
        with patch("database.UserDB.get_user_by_id", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {
                "id": "user-to-delete",
                "role": "user"
            }
            with patch("database.AdminDB.delete_user", new_callable=AsyncMock) as mock_delete:
                mock_delete.return_value = True
                
                response = client.delete("/api/admin/users/user-to-delete")
                
                assert response.status_code == 200


class TestAdminSettingsAPI:
    """系统设置API权限测试"""

    @patch("auth.get_current_user")
    def test_get_settings_as_user(self, mock_get_user, client, mock_user):
        """普通用户无法访问系统设置"""
        mock_get_user.return_value = mock_user
        
        response = client.get("/api/admin/settings")
        
        assert response.status_code == 403

    @patch("auth.get_current_user")
    def test_get_settings_as_admin(self, mock_get_user, client, mock_admin):
        """管理员可以查看系统设置"""
        mock_get_user.return_value = mock_admin
        
        with patch("utils.settings.get_all_settings_grouped", new_callable=AsyncMock) as mock_settings:
            mock_settings.return_value = {"groups": {}}
            
            response = client.get("/api/admin/settings")
            
            assert response.status_code == 200

    @patch("auth.get_current_user")
    def test_update_settings_as_admin(self, mock_get_user, client, mock_admin):
        """普通管理员无法更新系统设置"""
        mock_get_user.return_value = mock_admin
        
        response = client.put("/api/admin/settings", json={
            "settings": {"allow_registration": False}
        })
        
        assert response.status_code == 403

    @patch("auth.get_current_user")
    def test_update_settings_as_super_admin(self, mock_get_user, client, mock_super_admin):
        """超级管理员可以更新系统设置"""
        mock_get_user.return_value = mock_super_admin
        
        with patch("utils.settings.set_settings", new_callable=AsyncMock) as mock_set:
            mock_set.return_value = {"allow_registration": True}
            
            response = client.put("/api/admin/settings", json={
                "settings": {"allow_registration": False}
            })
            
            assert response.status_code == 200


class TestAdminStatsAPI:
    """统计API权限测试"""

    @patch("auth.get_current_user")
    def test_get_stats_as_user(self, mock_get_user, client, mock_user):
        """普通用户无法访问统计数据"""
        mock_get_user.return_value = mock_user
        
        response = client.get("/api/admin/stats/overview")
        
        assert response.status_code == 403

    @patch("auth.get_current_user")
    def test_get_stats_as_admin(self, mock_get_user, client, mock_admin):
        """管理员可以查看统计数据"""
        mock_get_user.return_value = mock_admin
        
        with patch("services.stats_service.get_overview_stats", new_callable=AsyncMock) as mock_stats:
            mock_stats.return_value = {
                "total_users": 100,
                "active_users": 80,
                "total_tasks": 500
            }
            
            response = client.get("/api/admin/stats/overview")
            
            assert response.status_code == 200


class TestAdminAuditAPI:
    """审计日志API权限测试"""

    @patch("auth.get_current_user")
    def test_get_audit_logs_as_user(self, mock_get_user, client, mock_user):
        """普通用户无法访问审计日志"""
        mock_get_user.return_value = mock_user
        
        response = client.get("/api/admin/audit-logs")
        
        assert response.status_code == 403

    @patch("auth.get_current_user")
    def test_get_audit_logs_as_admin(self, mock_get_user, client, mock_admin):
        """管理员可以查看审计日志"""
        mock_get_user.return_value = mock_admin
        
        with patch("routers.admin.audit.get_audit_logs_with_users", new_callable=AsyncMock) as mock_logs:
            mock_logs.return_value = ([], 0)
            
            response = client.get("/api/admin/audit-logs")
            
            assert response.status_code == 200

    @patch("auth.get_current_user")
    def test_delete_old_logs_as_admin(self, mock_get_user, client, mock_admin):
        """普通管理员无法删除旧日志"""
        mock_get_user.return_value = mock_admin
        
        response = client.delete("/api/admin/audit-logs/old?days=90")
        
        assert response.status_code == 403

    @patch("auth.get_current_user")
    def test_delete_old_logs_as_super_admin(self, mock_get_user, client, mock_super_admin):
        """超级管理员可以删除旧日志"""
        mock_get_user.return_value = mock_super_admin
        
        with patch("routers.admin.audit.delete_old_audit_logs", new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = 10
            
            response = client.delete("/api/admin/audit-logs/old?days=90")
            
            assert response.status_code == 200


class TestRoleBasedAccess:
    """角色访问控制测试"""

    @patch("auth.get_current_user")
    def test_user_cannot_access_admin_routes(self, mock_get_user, client, mock_user):
        """普通用户无法访问任何管理员路由"""
        mock_get_user.return_value = mock_user
        
        admin_routes = [
            "/api/admin/users",
            "/api/admin/settings",
            "/api/admin/stats/overview",
            "/api/admin/audit-logs",
        ]
        
        for route in admin_routes:
            response = client.get(route)
            assert response.status_code == 403, f"Route {route} should return 403"

    @patch("auth.get_current_user")
    def test_admin_can_access_all_admin_routes(self, mock_get_user, client, mock_admin):
        """管理员可以访问所有管理员路由"""
        mock_get_user.return_value = mock_admin
        
        with patch("database.AdminDB.get_all_users", new_callable=AsyncMock):
            with patch("database.AdminDB.get_users_count", new_callable=AsyncMock):
                with patch("utils.settings.get_all_settings_grouped", new_callable=AsyncMock):
                    with patch("services.stats_service.get_overview_stats", new_callable=AsyncMock):
                        with patch("routers.admin.audit.get_audit_logs_with_users", new_callable=AsyncMock):
                            admin_routes = [
                                "/api/admin/users",
                                "/api/admin/settings",
                                "/api/admin/stats/overview",
                                "/api/admin/audit-logs",
                            ]
                            
                            for route in admin_routes:
                                response = client.get(route)
                                assert response.status_code == 200, f"Route {route} should return 200"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
