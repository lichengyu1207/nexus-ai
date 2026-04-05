"""
报告API测试
测试报告生成、搜索、分享等功能
"""
import pytest
from httpx import AsyncClient


class TestReportList:
    """报告列表测试"""
    
    @pytest.mark.asyncio
    async def test_list_reports_unauthorized(self, client: AsyncClient):
        """测试未授权访问报告列表"""
        response = await client.get("/api/reports")
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_list_reports_empty(self, auth_client: AsyncClient):
        """测试空报告列表"""
        response = await auth_client.get("/api/reports")
        assert response.status_code == 200
        data = response.json()
        assert "reports" in data
        assert "total" in data
        assert data["total"] == 0
    
    @pytest.mark.asyncio
    async def test_list_reports_with_data(self, auth_client: AsyncClient, test_report: dict):
        """测试有数据的报告列表"""
        response = await auth_client.get("/api/reports")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert len(data["reports"]) >= 1


class TestReportSearch:
    """报告搜索测试"""
    
    @pytest.mark.asyncio
    async def test_search_by_keyword(self, auth_client: AsyncClient, test_report: dict):
        """测试关键词搜索"""
        response = await auth_client.get("/api/reports", params={"q": "测试"})
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
    
    @pytest.mark.asyncio
    async def test_search_by_status(self, auth_client: AsyncClient, test_report: dict):
        """测试状态过滤"""
        response = await auth_client.get("/api/reports", params={"status": "completed"})
        assert response.status_code == 200
        data = response.json()
        for report in data["reports"]:
            assert report["status"] == "completed"
    
    @pytest.mark.asyncio
    async def test_search_by_date_range(self, auth_client: AsyncClient, test_report: dict):
        """测试日期范围过滤"""
        response = await auth_client.get(
            "/api/reports",
            params={
                "start_date": "2023-01-01",
                "end_date": "2025-12-31"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
    
    @pytest.mark.asyncio
    async def test_search_no_results(self, auth_client: AsyncClient):
        """测试搜索无结果"""
        response = await auth_client.get("/api/reports", params={"q": "不存在的关键词xyz123"})
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0


class TestReportShare:
    """报告分享测试"""
    
    @pytest.mark.asyncio
    async def test_create_share_link(self, auth_client: AsyncClient, test_report: dict):
        """测试创建分享链接"""
        response = await auth_client.post(f"/api/reports/{test_report['id']}/share")
        assert response.status_code == 200
        data = response.json()
        assert "share_token" in data
        assert "share_url" in data
        assert data["is_public"] is True
    
    @pytest.mark.asyncio
    async def test_get_share_info(self, auth_client: AsyncClient, test_report: dict):
        """测试获取分享信息"""
        await auth_client.post(f"/api/reports/{test_report['id']}/share")
        
        response = await auth_client.get(f"/api/reports/{test_report['id']}/share")
        assert response.status_code == 200
        data = response.json()
        assert data["is_public"] is True
        assert data["share_token"] is not None
    
    @pytest.mark.asyncio
    async def test_revoke_share(self, auth_client: AsyncClient, test_report: dict):
        """测试撤销分享"""
        await auth_client.post(f"/api/reports/{test_report['id']}/share")
        
        response = await auth_client.delete(f"/api/reports/{test_report['id']}/share")
        assert response.status_code == 200
        data = response.json()
        assert data["is_public"] is False
    
    @pytest.mark.asyncio
    async def test_share_unauthorized(self, client: AsyncClient, test_report: dict):
        """测试未授权分享"""
        response = await client.post(f"/api/reports/{test_report['id']}/share")
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_share_other_user_report(
        self, 
        auth_client: AsyncClient, 
        second_user_client: AsyncClient,
        test_report: dict
    ):
        """测试分享其他用户的报告"""
        response = await second_user_client.post(f"/api/reports/{test_report['id']}/share")
        assert response.status_code == 403


class TestPublicReport:
    """公开报告测试"""
    
    @pytest.mark.asyncio
    async def test_access_public_report(self, client: AsyncClient, auth_client: AsyncClient, test_report: dict):
        """测试访问公开报告"""
        share_response = await auth_client.post(f"/api/reports/{test_report['id']}/share")
        share_token = share_response.json()["share_token"]
        
        response = await client.get(f"/api/public/reports/{share_token}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_report["id"]
        assert data["status"] == "completed"
    
    @pytest.mark.asyncio
    async def test_access_invalid_token(self, client: AsyncClient):
        """测试访问无效的分享令牌"""
        response = await client.get("/api/public/reports/invalid_token_12345")
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_access_revoked_share(self, client: AsyncClient, auth_client: AsyncClient, test_report: dict):
        """测试访问已撤销的分享"""
        share_response = await auth_client.post(f"/api/reports/{test_report['id']}/share")
        share_token = share_response.json()["share_token"]
        
        await auth_client.delete(f"/api/reports/{test_report['id']}/share")
        
        response = await client.get(f"/api/public/reports/{share_token}")
        assert response.status_code == 404


class TestReportVersions:
    """报告版本测试"""
    
    @pytest.mark.asyncio
    async def test_get_task_versions(self, auth_client: AsyncClient, test_report: dict):
        """测试获取任务版本列表"""
        response = await auth_client.get(f"/api/reports/task/{test_report['task_id']}/versions")
        assert response.status_code == 200
        data = response.json()
        assert "versions" in data
        assert data["task_id"] == test_report["task_id"]
    
    @pytest.mark.asyncio
    async def test_get_version(self, auth_client: AsyncClient, test_report: dict):
        """测试获取指定版本"""
        response = await auth_client.get(f"/api/reports/{test_report['id']}/versions/1")
        assert response.status_code == 200


class TestReportPagination:
    """报告分页测试"""
    
    @pytest.mark.asyncio
    async def test_pagination_limit(self, auth_client: AsyncClient, test_report: dict):
        """测试分页限制"""
        response = await auth_client.get("/api/reports", params={"limit": 1})
        assert response.status_code == 200
        data = response.json()
        assert len(data["reports"]) <= 1
    
    @pytest.mark.asyncio
    async def test_pagination_offset(self, auth_client: AsyncClient, test_report: dict):
        """测试分页偏移"""
        response1 = await auth_client.get("/api/reports", params={"limit": 1, "offset": 0})
        response2 = await auth_client.get("/api/reports", params={"limit": 1, "offset": 1})
        
        assert response1.status_code == 200
        assert response2.status_code == 200
