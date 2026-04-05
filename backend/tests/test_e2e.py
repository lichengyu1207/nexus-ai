"""
E2E 测试 - 模糊查询场景
使用 pytest 和 httpx 测试完整用户流程
"""
import pytest
import httpx
import asyncio
from typing import Dict, Any

BASE_URL = "http://localhost:8000"


class TestFuzzyQueryE2E:
    """模糊查询端到端测试"""
    
    @pytest.fixture
    async def client(self):
        """创建异步HTTP客户端"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
            yield client
    
    @pytest.mark.asyncio
    async def test_parse_fuzzy_location_query(self, client):
        """测试模糊位置查询解析"""
        response = await client.post(
            "/api/parse/query",
            json={"query": "我想在上海浦东买套房子"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["city"] == "上海"
        assert "浦东" in (data["district"] or "")
        assert data["confidence"] > 0.5
    
    @pytest.mark.asyncio
    async def test_parse_fuzzy_budget_query(self, client):
        """测试模糊预算查询解析"""
        response = await client.post(
            "/api/parse/query",
            json={"query": "预算有限，200万左右，北京"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["city"] == "北京"
        assert data["price_max"] is not None
        assert data["price_max"] <= 2500000
    
    @pytest.mark.asyncio
    async def test_parse_fuzzy_room_query(self, client):
        """测试模糊户型查询解析"""
        response = await client.post(
            "/api/parse/query",
            json={"query": "两居室，面积差不多就行"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["room_count"] == 2
        assert "room_count" not in data.get("missing_fields", [])
    
    @pytest.mark.asyncio
    async def test_parse_complex_query(self, client):
        """测试复杂查询解析"""
        response = await client.post(
            "/api/parse/query",
            json={"query": "深圳南山区学区房，3室，预算500-800万，近地铁"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["city"] == "深圳"
        assert "南山" in (data["district"] or "")
        assert data["room_count"] == 3
        assert data["price_min"] == 5000000
        assert data["price_max"] == 8000000
        assert data["is_school_district"] == True
        assert data["is_near_subway"] == True


class TestDisambiguationE2E:
    """消歧功能端到端测试"""
    
    @pytest.fixture
    async def client(self):
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
            yield client
    
    @pytest.mark.asyncio
    async def test_disambiguate_district(self, client):
        """测试区域消歧"""
        response = await client.post(
            "/api/disambiguate/district",
            json={"city": "上海", "input": "浦东"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["matches"]) > 0
        assert any("浦东" in m["name"] for m in data["matches"])
    
    @pytest.mark.asyncio
    async def test_disambiguate_community(self, client):
        """测试小区消歧"""
        response = await client.post(
            "/api/disambiguate/community",
            json={"city": "上海", "district": "浦东新区", "input": "世纪"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "matches" in data


class TestFeedbackE2E:
    """反馈功能端到端测试"""
    
    @pytest.fixture
    async def client(self):
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
            yield client
    
    @pytest.fixture
    async def auth_token(self, client):
        """获取认证令牌"""
        response = await client.post(
            "/api/auth/login",
            data={"username": "test@example.com", "password": "testpassword"}
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        return None
    
    @pytest.mark.asyncio
    async def test_submit_feedback(self, client, auth_token):
        """测试提交反馈"""
        if not auth_token:
            pytest.skip("需要认证")
        
        response = await client.post(
            "/api/reports/test-report-id/feedback",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "rating": 1,
                "issues": ["price_accuracy"],
                "comment": "价格估算偏高",
                "contact_allowed": True
            }
        )
        
        assert response.status_code in [200, 201, 404]


class TestKnowledgeBaseE2E:
    """知识库端到端测试"""
    
    @pytest.fixture
    async def client(self):
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
            yield client
    
    @pytest.fixture
    async def admin_token(self, client):
        """获取管理员令牌"""
        response = await client.post(
            "/api/auth/login",
            data={"username": "admin@example.com", "password": "adminpassword"}
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        return None
    
    @pytest.mark.asyncio
    async def test_get_house_types(self, client, admin_token):
        """测试获取户型面积列表"""
        if not admin_token:
            pytest.skip("需要管理员认证")
        
        response = await client.get(
            "/api/admin/knowledge-base/house-types",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
    
    @pytest.mark.asyncio
    async def test_get_district_prices(self, client, admin_token):
        """测试获取区域房价列表"""
        if not admin_token:
            pytest.skip("需要管理员认证")
        
        response = await client.get(
            "/api/admin/knowledge-base/district-prices",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data


class TestDistrictInfoE2E:
    """区域介绍端到端测试"""
    
    @pytest.fixture
    async def client(self):
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
            yield client
    
    @pytest.mark.asyncio
    async def test_get_district_info(self, client):
        """测试获取区域介绍"""
        response = await client.get(
            "/api/district-info",
            params={"city": "上海", "district": "浦东新区"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        if data:
            assert "city" in data
            assert "district" in data


class TestABTestE2E:
    """A/B测试端到端测试"""
    
    @pytest.fixture
    async def client(self):
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
            yield client
    
    @pytest.fixture
    async def admin_token(self, client):
        response = await client.post(
            "/api/auth/login",
            data={"username": "admin@example.com", "password": "adminpassword"}
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        return None
    
    @pytest.mark.asyncio
    async def test_get_overall_stats(self, client, admin_token):
        """测试获取A/B测试统计"""
        if not admin_token:
            pytest.skip("需要管理员认证")
        
        response = await client.get(
            "/api/ab-tests/stats/overall",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_users" in data
        assert "control_users" in data
        assert "treatment_users" in data


class TestFullUserFlow:
    """完整用户流程测试"""
    
    @pytest.fixture
    async def client(self):
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=60.0) as client:
            yield client
    
    @pytest.mark.asyncio
    async def test_complete_analysis_flow(self, client):
        """测试完整分析流程"""
        parse_response = await client.post(
            "/api/parse/query",
            json={"query": "上海浦东新区3室2厅100平米预算500万学区房"}
        )
        
        assert parse_response.status_code == 200
        parsed = parse_response.json()
        
        assert parsed["city"] == "上海"
        assert parsed["room_count"] == 3
        assert parsed["area_min"] is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
