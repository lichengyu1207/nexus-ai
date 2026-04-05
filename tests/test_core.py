"""
核心功能自动化测试
覆盖：用户认证、任务创建、API健康检查
"""
import pytest
import requests
import time

BASE_URL = "http://localhost:8000"

class TestHealth:
    """健康检查测试"""
    
    def test_health_endpoint(self):
        """测试健康检查端点"""
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        assert r.status_code == 200
    
    def test_api_docs(self):
        """测试API文档可访问"""
        r = requests.get(f"{BASE_URL}/docs", timeout=5)
        assert r.status_code == 200


class TestAuth:
    """认证测试"""
    
    def test_login_success(self):
        """测试登录成功"""
        r = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "1558691995@qq.com",
            "password": "147258@Zxcvbnm"
        }, timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert "access_token" in data
    
    def test_login_wrong_password(self):
        """测试密码错误"""
        r = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "1558691995@qq.com",
            "password": "wrongpassword"
        }, timeout=10)
        assert r.status_code == 401
    
    def test_get_current_user(self):
        """测试获取当前用户"""
        # 先登录
        r = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "1558691995@qq.com",
            "password": "147258@Zxcvbnm"
        }, timeout=10)
        token = r.json().get("access_token")
        
        # 获取用户信息
        r = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {token}"
        }, timeout=10)
        assert r.status_code == 200


class TestIPPlan:
    """IP计划测试"""
    
    def get_token(self):
        r = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "1558691995@qq.com",
            "password": "147258@Zxcvbnm"
        }, timeout=10)
        return r.json().get("access_token")
    
    def test_ip_apply(self):
        """测试IP申请"""
        token = self.get_token()
        r = requests.post(f"{BASE_URL}/api/ip/apply", headers={
            "Authorization": f"Bearer {token}"
        }, json={
            "name": "测试用户",
            "contact": "test123",
            "platform": "zhihu",
            "platform_id": "test_id",
            "followers": 1000
        }, timeout=10)
        assert r.status_code == 200
    
    def test_ip_check_referral(self):
        """测试推广链接验证"""
        r = requests.get(f"{BASE_URL}/api/ip/check?ref=TEST123", timeout=10)
        assert r.status_code == 200
    
    def test_ip_dashboard(self):
        """测试IP仪表盘"""
        token = self.get_token()
        r = requests.get(f"{BASE_URL}/api/ip/dashboard", headers={
            "Authorization": f"Bearer {token}"
        }, timeout=10)
        assert r.status_code == 200


class TestAnalytics:
    """分析功能测试"""
    
    def get_token(self):
        r = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "1558691995@qq.com",
            "password": "147258@Zxcvbnm"
        }, timeout=10)
        return r.json().get("access_token")
    
    def test_track_event(self):
        """测试事件追踪"""
        token = self.get_token()
        r = requests.post(f"{BASE_URL}/api/events", headers={
            "Authorization": f"Bearer {token}"
        }, json={
            "event_type": "page_view",
            "page_url": "/test",
            "session_id": "test-session"
        }, timeout=10)
        assert r.status_code == 200
    
    def test_analytics_overview(self):
        """测试分析概览"""
        token = self.get_token()
        r = requests.get(f"{BASE_URL}/api/admin/analytics/overview", headers={
            "Authorization": f"Bearer {token}"
        }, timeout=10)
        assert r.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
