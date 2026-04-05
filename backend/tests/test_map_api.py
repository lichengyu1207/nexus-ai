"""
地图API测试
"""
import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock


class TestMapAPI:
    """地图API测试"""
    
    @pytest.mark.asyncio
    async def test_get_map_data_unauthorized(self, client: AsyncClient):
        """测试未授权访问"""
        response = await client.get("/api/admin/map/data")
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_map_data_as_admin(
        self, 
        client: AsyncClient, 
        admin_headers: dict
    ):
        """测试管理员访问地图数据"""
        with patch('routers.admin.map.get_map_data') as mock_get_data:
            mock_get_data.return_value = {
                "type": "FeatureCollection",
                "features": [],
                "metadata": {
                    "zoom_level": 5,
                    "aggregation_level": "city",
                    "total_features": 0
                }
            }
            
            response = await client.get(
                "/api/admin/map/data?zoom_level=5",
                headers=admin_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["type"] == "FeatureCollection"
    
    @pytest.mark.asyncio
    async def test_get_map_data_with_bounds(
        self,
        client: AsyncClient,
        admin_headers: dict
    ):
        """测试带边界参数的地图数据"""
        with patch('routers.admin.map.get_map_data') as mock_get_data:
            mock_get_data.return_value = {
                "type": "FeatureCollection",
                "features": [],
                "metadata": {
                    "zoom_level": 10,
                    "aggregation_level": "district",
                    "total_features": 0
                }
            }
            
            response = await client.get(
                "/api/admin/map/data?zoom_level=10&north=40&south=30&east=120&west=110",
                headers=admin_headers
            )
            
            assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_get_heatmap(self, client: AsyncClient, admin_headers: dict):
        """测试热力图数据"""
        with patch('routers.admin.map.get_heatmap_data') as mock_get_heatmap:
            mock_get_heatmap.return_value = [[113.94, 22.54], [114.0, 22.5]]
            
            response = await client.get(
                "/api/admin/map/heatmap",
                headers=admin_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "data" in data
            assert "metadata" in data
    
    @pytest.mark.asyncio
    async def test_get_summary(self, client: AsyncClient, admin_headers: dict):
        """测试位置摘要"""
        with patch('routers.admin.map.get_location_summary') as mock_get_summary:
            mock_get_summary.return_value = {
                "total_locations": 100,
                "geocoded_locations": 80,
                "top_provinces": [],
                "top_cities": [],
                "by_source": {"registration": 30, "interest": 20, "report": 50}
            }
            
            response = await client.get(
                "/api/admin/map/summary",
                headers=admin_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["total_locations"] == 100
    
    @pytest.mark.asyncio
    async def test_get_stats(self, client: AsyncClient, admin_headers: dict):
        """测试地图统计"""
        with patch('routers.admin.map.get_map_stats') as mock_get_stats:
            mock_get_stats.return_value = {
                "total_locations": 100,
                "geocoded_locations": 80,
                "by_source": {"registration": 30, "interest": 20, "report": 50},
                "top_cities": [{"name": "深圳", "count": 50}],
                "top_provinces": [{"name": "广东省", "count": 60}],
                "top_districts": [{"name": "南山区", "city": "深圳", "count": 30}],
                "new_communities_last_30d": 10
            }
            
            response = await client.get(
                "/api/admin/map/stats",
                headers=admin_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["total_locations"] == 100
            assert data["new_communities_last_30d"] == 10


class TestLocationsAPI:
    """位置管理API测试"""
    
    @pytest.mark.asyncio
    async def test_list_locations_requires_super_admin(
        self,
        client: AsyncClient,
        admin_headers: dict
    ):
        """测试需要超级管理员权限"""
        response = await client.get(
            "/api/admin/locations",
            headers=admin_headers
        )
        
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_list_locations_as_super_admin(
        self,
        client: AsyncClient,
        super_admin_headers: dict
    ):
        """测试超级管理员访问"""
        with patch('routers.admin.locations.get_db_connection') as mock_conn:
            mock_cursor = AsyncMock()
            mock_cursor.fetchone.return_value = {"count": 0}
            mock_cursor.fetchall.return_value = []
            mock_conn.return_value.execute = AsyncMock(return_value=mock_cursor)
            mock_conn.return_value.fetchone = AsyncMock(return_value={"count": 0})
            mock_conn.return_value.fetchall = AsyncMock(return_value=[])
            mock_conn.return_value.close = AsyncMock()
            
            response = await client.get(
                "/api/admin/locations",
                headers=super_admin_headers
            )
            
            assert response.status_code == 200


class TestMapAggregator:
    """地图聚合服务测试"""
    
    def test_cache_key_generation(self):
        """测试缓存键生成"""
        from services.map_aggregator import _get_cache_key
        
        key1 = _get_cache_key("test", a=1, b=2)
        key2 = _get_cache_key("test", a=1, b=2)
        key3 = _get_cache_key("test", a=2, b=1)
        
        assert key1 == key2
        assert key1 != key3
    
    def test_clear_map_cache(self):
        """测试清除缓存"""
        from services.map_aggregator import (
            _map_cache,
            _set_cache,
            clear_map_cache
        )
        
        _set_cache("test_key", {"data": "test"})
        
        clear_map_cache()
        
        from services.map_aggregator import _map_cache
        assert len(_map_cache) == 0
    
    def test_min_users_threshold(self):
        """测试最小用户数阈值"""
        from services.map_aggregator import MIN_USERS_THRESHOLD
        
        assert MIN_USERS_THRESHOLD == 3
