"""
用户反馈和举报系统单元测试
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestFeedbackAPI:
    """反馈 API 测试"""
    
    @pytest.fixture
    def client(self):
        from main import app
        return TestClient(app)
    
    @pytest.fixture
    def auth_headers(self, client):
        response = client.post("/api/auth/register", json={
            "email": "test@example.com",
            "password": "testpass123",
            "username": "testuser"
        })
        if response.status_code == 200:
            token = response.json().get("access_token")
            return {"Authorization": f"Bearer {token}"}
        response = client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "testpass123"
        })
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}"}
    
    @pytest.fixture
    def admin_headers(self, client):
        response = client.post("/api/auth/login", json={
            "email": "admin@example.com",
            "password": "admin123"
        })
        if response.status_code != 200:
            client.post("/api/auth/register", json={
                "email": "admin@example.com",
                "password": "admin123",
                "username": "admin"
            })
            response = client.post("/api/auth/login", json={
                "email": "admin@example.com",
                "password": "admin123"
            })
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}"}

    def test_submit_feedback_success(self, client, auth_headers):
        """测试成功提交反馈"""
        response = client.post("/api/feedback", 
            headers=auth_headers,
            json={
                "type": "feedback",
                "title": "测试反馈",
                "content": "这是一个测试反馈内容，长度超过十个字符"
            }
        )
        assert response.status_code in [200, 201]
        data = response.json()
        assert "id" in data.get("data", data) or "id" in data

    def test_submit_feedback_without_auth(self, client):
        """测试未登录提交反馈"""
        response = client.post("/api/feedback",
            json={
                "type": "feedback",
                "content": "测试内容"
            }
        )
        assert response.status_code == 401

    def test_submit_feedback_short_content(self, client, auth_headers):
        """测试内容过短的反馈"""
        response = client.post("/api/feedback",
            headers=auth_headers,
            json={
                "type": "feedback",
                "content": "短"
            }
        )
        assert response.status_code in [400, 422]

    def test_get_my_feedbacks(self, client, auth_headers):
        """测试获取我的反馈列表"""
        response = client.get("/api/feedback/my", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    def test_get_feedback_types(self, client):
        """测试获取反馈类型"""
        response = client.get("/api/feedback/types")
        assert response.status_code == 200
        data = response.json()
        assert "types" in data


class TestReportAPI:
    """举报 API 测试"""
    
    @pytest.fixture
    def client(self):
        from main import app
        return TestClient(app)
    
    @pytest.fixture
    def auth_headers(self, client):
        response = client.post("/api/auth/register", json={
            "email": "reporter@example.com",
            "password": "testpass123",
            "username": "reporter"
        })
        if response.status_code == 200:
            token = response.json().get("access_token")
            return {"Authorization": f"Bearer {token}"}
        response = client.post("/api/auth/login", json={
            "email": "reporter@example.com",
            "password": "testpass123"
        })
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}"}

    def test_submit_report_success(self, client, auth_headers):
        """测试成功提交举报"""
        response = client.post("/api/reports",
            headers=auth_headers,
            json={
                "reported_type": "report",
                "reported_id": "test-report-id",
                "reason": "spam",
                "details": "这是垃圾信息"
            }
        )
        assert response.status_code in [200, 201]

    def test_submit_report_without_auth(self, client):
        """测试未登录提交举报"""
        response = client.post("/api/reports",
            json={
                "reported_type": "report",
                "reported_id": "test-id",
                "reason": "spam"
            }
        )
        assert response.status_code == 401

    def test_get_my_reports(self, client, auth_headers):
        """测试获取我的举报列表"""
        response = client.get("/api/reports/my", headers=auth_headers)
        assert response.status_code == 200

    def test_get_report_reasons(self, client):
        """测试获取举报原因"""
        response = client.get("/api/reports/reasons")
        assert response.status_code == 200


class TestPrivacyAPI:
    """隐私政策 API 测试"""
    
    @pytest.fixture
    def client(self):
        from main import app
        return TestClient(app)
    
    @pytest.fixture
    def auth_headers(self, client):
        response = client.post("/api/auth/register", json={
            "email": "privacy@example.com",
            "password": "testpass123",
            "username": "privacyuser"
        })
        if response.status_code == 200:
            token = response.json().get("access_token")
            return {"Authorization": f"Bearer {token}"}
        response = client.post("/api/auth/login", json={
            "email": "privacy@example.com",
            "password": "testpass123"
        })
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}"}

    def test_get_current_privacy_policy(self, client):
        """测试获取当前隐私政策"""
        response = client.get("/api/privacy/current")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert "content" in data

    def test_get_privacy_status_unauthorized(self, client):
        """测试未登录获取隐私状态"""
        response = client.get("/api/privacy/status")
        assert response.status_code == 401

    def test_get_privacy_status(self, client, auth_headers):
        """测试获取隐私状态"""
        response = client.get("/api/privacy/status", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "agreed_latest" in data

    def test_consent_privacy_policy(self, client, auth_headers):
        """测试同意隐私政策"""
        response = client.post("/api/privacy/consent", headers=auth_headers)
        assert response.status_code == 200


class TestAdminFeedbackAPI:
    """管理员反馈 API 测试"""
    
    @pytest.fixture
    def client(self):
        from main import app
        return TestClient(app)

    def test_admin_feedback_list_unauthorized(self, client):
        """测试未授权访问管理员反馈列表"""
        response = client.get("/api/admin/feedback")
        assert response.status_code == 401

    def test_admin_feedback_stats_unauthorized(self, client):
        """测试未授权访问管理员反馈统计"""
        response = client.get("/api/admin/feedback/stats")
        assert response.status_code == 401


class TestAdminReportsAPI:
    """管理员举报 API 测试"""
    
    @pytest.fixture
    def client(self):
        from main import app
        return TestClient(app)

    def test_admin_reports_list_unauthorized(self, client):
        """测试未授权访问管理员举报列表"""
        response = client.get("/api/admin/reports")
        assert response.status_code == 401

    def test_admin_reports_stats_unauthorized(self, client):
        """测试未授权访问管理员举报统计"""
        response = client.get("/api/admin/reports/stats")
        assert response.status_code == 401


class TestAdminComplianceAPI:
    """管理员合规 API 测试"""
    
    @pytest.fixture
    def client(self):
        from main import app
        return TestClient(app)

    def test_admin_privacy_logs_unauthorized(self, client):
        """测试未授权访问隐私日志"""
        response = client.get("/api/admin/compliance/privacy-logs")
        assert response.status_code == 401

    def test_admin_privacy_logs_export_unauthorized(self, client):
        """测试未授权导出隐私日志"""
        response = client.get("/api/admin/compliance/privacy-logs/export")
        assert response.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
