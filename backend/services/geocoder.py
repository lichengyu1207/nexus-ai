"""
地理编码服务模块
将地址字符串转换为经纬度和结构化地址
支持高德地图、百度地图、Google Maps
"""
import os
import json
import asyncio
import hashlib
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import aiohttp
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class GeocodeResult:
    """地理编码结果"""
    country: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    street: Optional[str] = None
    community: Optional[str] = None
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    formatted_address: Optional[str] = None
    provider: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "country": self.country,
            "province": self.province,
            "city": self.city,
            "district": self.district,
            "street": self.street,
            "community": self.community,
            "longitude": self.longitude,
            "latitude": self.latitude,
            "formatted_address": self.formatted_address,
            "provider": self.provider,
        }


class MemoryCache:
    """内存缓存"""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._ttl = timedelta(days=30)
    
    def _get_key(self, address: str) -> str:
        return hashlib.md5(address.encode()).hexdigest()
    
    def get(self, address: str) -> Optional[Dict[str, Any]]:
        key = self._get_key(address)
        cached = self._cache.get(key)
        
        if cached:
            if datetime.now() - cached["timestamp"] < self._ttl:
                return cached["result"]
            else:
                del self._cache[key]
        
        return None
    
    def set(self, address: str, result: Dict[str, Any]) -> None:
        key = self._get_key(address)
        self._cache[key] = {
            "result": result,
            "timestamp": datetime.now()
        }
    
    def clear(self) -> None:
        self._cache.clear()


class DatabaseCache:
    """数据库缓存"""
    
    def __init__(self):
        from ..database import GeocodeCacheDB
        self.db = GeocodeCacheDB
    
    async def get(self, address: str) -> Optional[Dict[str, Any]]:
        return await self.db.get(address)
    
    async def set(self, address: str, result: Dict[str, Any]) -> None:
        await self.db.set(address, result)


class AmapGeocoder:
    """高德地图地理编码"""
    
    BASE_URL = "https://restapi.amap.com/v3/geocode/geo"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    async def geocode(self, address: str) -> Optional[GeocodeResult]:
        """地理编码"""
        params = {
            "key": self.api_key,
            "address": address,
            "output": "json"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.BASE_URL, params=params, timeout=10) as response:
                    data = await response.json()
                    
                    if data.get("status") != "1":
                        logger.warning(f"高德地图API错误: {data.get('info')}")
                        return None
                    
                    geocodes = data.get("geocodes", [])
                    if not geocodes:
                        return None
                    
                    geo = geocodes[0]
                    location = geo.get("location", "").split(",")
                    
                    if len(location) != 2:
                        return None
                    
                    return GeocodeResult(
                        country=geo.get("country"),
                        province=geo.get("province"),
                        city=geo.get("city") if geo.get("city") else geo.get("province"),
                        district=geo.get("district"),
                        street=geo.get("street"),
                        community=geo.get("community"),
                        longitude=float(location[0]),
                        latitude=float(location[1]),
                        formatted_address=geo.get("formatted_address"),
                        provider="amap"
                    )
        except Exception as e:
            logger.error(f"高德地图API调用失败: {e}")
            return None


class BaiduGeocoder:
    """百度地图地理编码"""
    
    BASE_URL = "https://api.map.baidu.com/geocoding/v3"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    async def geocode(self, address: str) -> Optional[GeocodeResult]:
        """地理编码"""
        params = {
            "ak": self.api_key,
            "address": address,
            "output": "json"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.BASE_URL, params=params, timeout=10) as response:
                    data = await response.json()
                    
                    if data.get("status") != 0:
                        logger.warning(f"百度地图API错误: {data.get('message')}")
                        return None
                    
                    result = data.get("result", {})
                    location = result.get("location", {})
                    
                    if not location:
                        return None
                    
                    level = result.get("level", "")
                    address_detail = result.get("address_detail", {})
                    
                    return GeocodeResult(
                        country="中国",
                        province=address_detail.get("province"),
                        city=address_detail.get("city"),
                        district=address_detail.get("district"),
                        street=address_detail.get("street"),
                        community=None,
                        longitude=location.get("lng"),
                        latitude=location.get("lat"),
                        formatted_address=result.get("formatted_address"),
                        provider="baidu"
                    )
        except Exception as e:
            logger.error(f"百度地图API调用失败: {e}")
            return None


class GoogleGeocoder:
    """Google Maps地理编码"""
    
    BASE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    async def geocode(self, address: str) -> Optional[GeocodeResult]:
        """地理编码"""
        params = {
            "key": self.api_key,
            "address": address,
            "language": "zh-CN"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.BASE_URL, params=params, timeout=10) as response:
                    data = await response.json()
                    
                    if data.get("status") != "OK":
                        logger.warning(f"Google Maps API错误: {data.get('status')}")
                        return None
                    
                    results = data.get("results", [])
                    if not results:
                        return None
                    
                    result = results[0]
                    location = result.get("geometry", {}).get("location", {})
                    
                    address_components = {}
                    for comp in result.get("address_components", []):
                        types = comp.get("types", [])
                        if "country" in types:
                            address_components["country"] = comp.get("long_name")
                        elif "administrative_area_level_1" in types:
                            address_components["province"] = comp.get("long_name")
                        elif "administrative_area_level_2" in types:
                            address_components["city"] = comp.get("long_name")
                        elif "administrative_area_level_3" in types:
                            address_components["district"] = comp.get("long_name")
                        elif "route" in types:
                            address_components["street"] = comp.get("long_name")
                    
                    return GeocodeResult(
                        country=address_components.get("country"),
                        province=address_components.get("province"),
                        city=address_components.get("city"),
                        district=address_components.get("district"),
                        street=address_components.get("street"),
                        community=None,
                        longitude=location.get("lng"),
                        latitude=location.get("lat"),
                        formatted_address=result.get("formatted_address"),
                        provider="google"
                    )
        except Exception as e:
            logger.error(f"Google Maps API调用失败: {e}")
            return None


class Geocoder:
    """
    地理编码服务
    支持多提供商，自动重试，缓存
    """
    
    def __init__(
        self,
        amap_key: Optional[str] = None,
        baidu_key: Optional[str] = None,
        google_key: Optional[str] = None,
        max_retries: int = 3,
        use_cache: bool = True,
        cache_type: str = "database"
    ):
        self.providers: List[tuple] = []
        
        if amap_key:
            self.providers.append(("amap", AmapGeocoder(amap_key)))
        if baidu_key:
            self.providers.append(("baidu", BaiduGeocoder(baidu_key)))
        if google_key:
            self.providers.append(("google", GoogleGeocoder(google_key)))
        
        self.max_retries = max_retries
        
        if use_cache:
            if cache_type == "database":
                self.cache = DatabaseCache()
            else:
                self.cache = MemoryCache()
        else:
            self.cache = None
    
    @classmethod
    def from_env(cls) -> "Geocoder":
        """从环境变量创建实例"""
        return cls(
            amap_key=os.getenv("AMAP_API_KEY"),
            baidu_key=os.getenv("BAIDU_MAP_API_KEY"),
            google_key=os.getenv("GOOGLE_MAPS_API_KEY"),
        )
    
    async def geocode(self, address: str) -> Optional[Dict[str, Any]]:
        """
        地理编码
        
        Args:
            address: 地址字符串
            
        Returns:
            地理编码结果字典，失败返回None
        """
        if not address or not address.strip():
            return None
        
        address = address.strip()
        
        if self.cache:
            cached = await self.cache.get(address)
            if cached:
                logger.debug(f"缓存命中: {address}")
                return cached
        
        for provider_name, provider in self.providers:
            for attempt in range(self.max_retries):
                try:
                    result = await provider.geocode(address)
                    
                    if result:
                        result_dict = result.to_dict()
                        
                        if self.cache:
                            await self.cache.set(address, result_dict)
                        
                        logger.info(f"地理编码成功: {address} -> {result.formatted_address} ({provider_name})")
                        return result_dict
                    
                except Exception as e:
                    logger.warning(f"{provider_name} 第 {attempt + 1} 次尝试失败: {e}")
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(1 * (attempt + 1))
        
        logger.warning(f"所有地理编码提供商均失败: {address}")
        return None
    
    async def batch_geocode(
        self,
        addresses: List[str],
        concurrency: int = 5
    ) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        批量地理编码
        
        Args:
            addresses: 地址列表
            concurrency: 并发数
            
        Returns:
            地址 -> 结果 的字典
        """
        semaphore = asyncio.Semaphore(concurrency)
        
        async def geocode_with_semaphore(address: str):
            async with semaphore:
                return address, await self.geocode(address)
        
        tasks = [geocode_with_semaphore(addr) for addr in addresses]
        results = await asyncio.gather(*tasks)
        
        return dict(results)
    
    def clear_cache(self) -> None:
        """清除缓存"""
        if self.cache:
            self.cache.clear()


_geocoder: Optional[Geocoder] = None


def get_geocoder() -> Geocoder:
    """获取地理编码器单例"""
    global _geocoder
    if _geocoder is None:
        _geocoder = Geocoder.from_env()
    return _geocoder


async def geocode_address(address: str) -> Optional[Dict[str, Any]]:
    """
    便捷函数：地理编码单个地址
    
    Args:
        address: 地址字符串
        
    Returns:
        地理编码结果
    """
    geocoder = get_geocoder()
    return await geocoder.geocode(address)
