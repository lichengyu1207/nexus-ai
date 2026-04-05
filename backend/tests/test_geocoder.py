"""
地理编码服务测试
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import asyncio

from services.geocoder import (
    Geocoder,
    GeocodeResult,
    MemoryCache,
    DatabaseCache,
    geocode_address,
    get_geocoder,
)


class TestGeocodeResult:
    """GeocodeResult测试"""
    
    def test_to_dict(self):
        """测试转换为字典"""
        result = GeocodeResult(
            country="中国",
            province="广东省",
            city="深圳市",
            district="南山区",
            street="科技园路",
            community="华润城",
            longitude=113.94,
            latitude=22.54,
            formatted_address="广东省深圳市南山区科技园路华润城",
            provider="amap"
        )
        
        data = result.to_dict()
        
        assert data["country"] == "中国"
        assert data["province"] == "广东省"
        assert data["city"] == "深圳市"
        assert data["longitude"] == 113.94
        assert data["latitude"] == 22.54
        assert data["provider"] == "amap"


class TestMemoryCache:
    """内存缓存测试"""
    
    def test_set_and_get(self):
        """测试设置和获取缓存"""
        cache = MemoryCache()
        
        cache.set("test_address", {"city": "深圳"})
        
        result = cache.get("test_address")
        
        assert result is not None
        assert result["city"] == "深圳"
    
    def test_get_nonexistent(self):
        """测试获取不存在的缓存"""
        cache = MemoryCache()
        
        result = cache.get("nonexistent")
        
        assert result is None
    
    def test_clear(self):
        """测试清除缓存"""
        cache = MemoryCache()
        
        cache.set("test", {"data": "value"})
        cache.clear()
        
        result = cache.get("test")
        
        assert result is None


class TestGeocoder:
    """Geocoder测试"""
    
    def test_init_with_providers(self):
        """测试初始化带提供商"""
        geocoder = Geocoder(
            amap_key="test_key",
            baidu_key="test_key",
            google_key="test_key"
        )
        
        assert len(geocoder.providers) == 3
    
    def test_init_without_providers(self):
        """测试初始化无提供商"""
        geocoder = Geocoder()
        
        assert len(geocoder.providers) == 0
    
    @pytest.mark.asyncio
    async def test_geocode_empty_address(self):
        """测试空地址"""
        geocoder = Geocoder(amap_key="test")
        
        result = await geocoder.geocode("")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_geocode_no_providers(self):
        """测试无提供商"""
        geocoder = Geocoder()
        
        result = await geocoder.geocode("深圳市南山区")
        
        assert result is None


class TestGeocoderIntegration:
    """地理编码集成测试"""
    
    @pytest.mark.asyncio
    async def test_geocode_with_mock(self):
        """测试地理编码（模拟）"""
        geocoder = Geocoder(amap_key="test_key", use_cache=False)
        
        with patch.object(geocoder.providers[0][1], 'geocode', new_callable=AsyncMock) as mock_geocode:
            mock_geocode.return_value = GeocodeResult(
                country="中国",
                province="广东省",
                city="深圳市",
                longitude=114.0,
                latitude=22.5,
                provider="amap"
            )
            
            result = await geocoder.geocode("深圳市")
            
            assert result is not None
            assert result["city"] == "深圳市"
            assert result["longitude"] == 114.0


def test_get_geocoder_singleton():
    """测试获取单例"""
    from services.geocoder import _geocoder, get_geocoder
    
    geocoder1 = get_geocoder()
    geocoder2 = get_geocoder()
    
    assert geocoder1 is geocoder2
