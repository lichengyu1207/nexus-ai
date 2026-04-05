"""
高德地图API客户端封装
支持POI搜索、地理编码、逆地理编码等功能
支持模拟模式（当API Key不可用时使用模拟数据）
"""
import asyncio
import aiohttp
import logging
import time
import random
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)


@dataclass
class AmapConfig:
    """高德API配置"""
    api_key: str = "a55b176367bcc6d90c7518e00a27f3e1"
    secret_key: str = ""
    base_url: str = "https://restapi.amap.com/v3"
    qps_limit: int = 5
    max_retries: int = 3
    retry_delay: float = 2.0
    mock_mode: bool = False


MOCK_DATA = {
    "geocode": {
        "深圳市南山区科技园": {
            "geocodes": [{
                "formatted_address": "广东省深圳市南山区科技园",
                "location": "113.9420,22.5380",
                "province": "广东省",
                "city": "深圳市",
                "district": "南山区",
                "level": "道路"
            }]
        }
    },
    "communities": [
        {"id": f"mock_poi_{i:04d}", "name": f"华润城润府{i}期", "address": f"深圳市南山区科技园路{i}号", "location": f"{113.9420+i*0.001},{22.5380+i*0.001}", "pname": "广东省", "cityname": "深圳市", "adname": "南山区", "adcode": "440305", "type": "住宅区", "typecode": "120300"}
        for i in range(1, 51)
    ] + [
        {"id": f"mock_poi_{i:04d}", "name": f"深圳湾{i}号", "address": f"深圳市南山区深圳湾路{i}号", "location": f"{113.9520+i*0.001},{22.5280+i*0.001}", "pname": "广东省", "cityname": "深圳市", "adname": "南山区", "adcode": "440305", "type": "住宅区", "typecode": "120300"}
        for i in range(51, 101)
    ],
    "pois": {
        "school": [
            {"id": f"school_{i:04d}", "name": f"南山外国语学校{i}", "address": f"深圳市南山区学路{i}号", "location": f"{113.9420+i*0.002},{22.5380+i*0.002}", "distance": str(random.randint(200, 1500)), "type": "学校", "typecode": "050301"}
            for i in range(1, 21)
        ],
        "hospital": [
            {"id": f"hospital_{i:04d}", "name": f"南山医院{i}", "address": f"深圳市南山区医路{i}号", "location": f"{113.9420+i*0.003},{22.5380+i*0.003}", "distance": str(random.randint(500, 2000)), "type": "医院", "typecode": "060101"}
            for i in range(1, 11)
        ],
        "subway": [
            {"id": f"subway_{i:04d}", "name": f"科技园站{i}号线", "address": f"深圳市南山区地铁{i}号", "location": f"{113.9420+i*0.004},{22.5380+i*0.004}", "distance": str(random.randint(100, 800)), "type": "地铁站", "typecode": "150101"}
            for i in range(1, 6)
        ],
        "mall": [
            {"id": f"mall_{i:04d}", "name": f"万象城{i}", "address": f"深圳市南山区商路{i}号", "location": f"{113.9420+i*0.005},{22.5380+i*0.005}", "distance": str(random.randint(300, 1200)), "type": "购物中心", "typecode": "050101"}
            for i in range(1, 11)
        ],
        "park": [
            {"id": f"park_{i:04d}", "name": f"深圳湾公园{i}", "address": f"深圳市南山区公园路{i}号", "location": f"{113.9520+i*0.002},{22.5280+i*0.002}", "distance": str(random.randint(400, 1500)), "type": "公园", "typecode": "070101"}
            for i in range(1, 6)
        ],
        "bank": [
            {"id": f"bank_{i:04d}", "name": f"工商银行南山支行{i}", "address": f"深圳市南山区金融路{i}号", "location": f"{113.9420+i*0.006},{22.5380+i*0.006}", "distance": str(random.randint(100, 500)), "type": "银行", "typecode": "060201"}
            for i in range(1, 11)
        ]
    }
}


class AmapClient:
    """高德地图API客户端"""
    
    def __init__(self, config: AmapConfig = None):
        self.config = config or AmapConfig()
        self.session: Optional[aiohttp.ClientSession] = None
        self.last_request_time: float = 0
        self.request_count: int = 0
        self._api_validated: bool = False
        self._use_mock: bool = self.config.mock_mode
    
    async def __aenter__(self):
        if not self._use_mock:
            self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _check_api_key(self):
        """检查API Key是否有效"""
        if self._api_validated:
            return
        
        if self._use_mock:
            logger.info("🎭 使用模拟模式")
            return
        
        try:
            url = f"{self.config.base_url}/geocode/geo"
            params = {"key": self.config.api_key, "address": "深圳市", "output": "json"}
            async with self.session.get(url, params=params, timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("status") == "1":
                        self._api_validated = True
                        logger.info("✅ API Key验证成功")
                    else:
                        error_code = data.get("infocode")
                        if error_code == "10009":
                            logger.warning("⚠️ API Key平台不匹配，自动切换到模拟模式")
                            logger.warning("请在高德开放平台创建'Web服务'类型的Key")
                            self._use_mock = True
                        else:
                            logger.warning(f"⚠️ API Key无效: {data.get('info')}，使用模拟模式")
                            self._use_mock = True
        except Exception as e:
            logger.warning(f"⚠️ API验证失败: {e}，使用模拟模式")
            self._use_mock = True
        
        self._api_validated = True
    
    async def _rate_limit(self):
        """请求频率控制"""
        elapsed = time.time() - self.last_request_time
        min_interval = 1.0 / self.config.qps_limit
        if elapsed < min_interval:
            await asyncio.sleep(min_interval - elapsed)
        self.last_request_time = time.time()
    
    async def _request(self, endpoint: str, params: Dict) -> Dict:
        """发送API请求"""
        await self._check_api_key()
        
        if self._use_mock:
            return await self._mock_request(endpoint, params)
        
        url = f"{self.config.base_url}/{endpoint}"
        params["key"] = self.config.api_key
        params["output"] = "json"
        
        for attempt in range(self.config.max_retries):
            try:
                await self._rate_limit()
                
                async with self.session.get(url, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("status") == "1":
                            self.request_count += 1
                            return data
                        else:
                            error_info = data.get("info", "Unknown error")
                            logger.warning(f"API returned error: {error_info}")
                            if "DAILY_QUERY_OVER_LIMIT" in error_info:
                                raise Exception("API daily limit exceeded")
                            return data
                    elif response.status == 429:
                        wait_time = self.config.retry_delay * (2 ** attempt)
                        logger.warning(f"Rate limited, waiting {wait_time}s...")
                        await asyncio.sleep(wait_time)
                    else:
                        raise Exception(f"HTTP error: {response.status}")
            except asyncio.TimeoutError:
                logger.warning(f"Request timeout, attempt {attempt + 1}")
                await asyncio.sleep(self.config.retry_delay * (2 ** attempt))
            except Exception as e:
                logger.error(f"Request failed: {e}")
                if attempt == self.config.max_retries - 1:
                    raise
                await asyncio.sleep(self.config.retry_delay * (2 ** attempt))
        
        raise Exception("Max retries exceeded")
    
    async def _mock_request(self, endpoint: str, params: Dict) -> Dict:
        """模拟API请求"""
        self.request_count += 1
        await asyncio.sleep(0.01)
        
        if endpoint == "geocode/geo":
            address = params.get("address", "")
            for key, value in MOCK_DATA["geocode"].items():
                if key in address:
                    return {"status": "1", "info": "OK", "geocodes": value["geocodes"]}
            return {"status": "1", "info": "OK", "geocodes": [{
                "formatted_address": f"广东省深圳市{address}",
                "location": "113.9420,22.5380",
                "province": "广东省",
                "city": "深圳市",
                "district": "南山区"
            }]}
        
        elif endpoint == "place/text":
            page = params.get("page", 1)
            page_size = params.get("offset", 25)
            start = (page - 1) * page_size
            end = start + page_size
            communities = MOCK_DATA["communities"][start:end]
            return {
                "status": "1",
                "info": "OK",
                "pois": communities,
                "count": str(len(MOCK_DATA["communities"]))
            }
        
        elif endpoint == "place/around":
            types = params.get("types", "")
            page = params.get("page", 1)
            page_size = params.get("offset", 25)
            
            all_pois = []
            for poi_type, type_codes in POICollector.POI_TYPES.items():
                if types and types in type_codes:
                    all_pois = MOCK_DATA["pois"].get(poi_type, [])
                    break
            
            if not all_pois:
                all_pois = []
                for pois in MOCK_DATA["pois"].values():
                    all_pois.extend(pois)
            
            start = (page - 1) * page_size
            end = start + page_size
            return {
                "status": "1",
                "info": "OK",
                "pois": all_pois[start:end],
                "count": str(len(all_pois))
            }
        
        return {"status": "1", "info": "OK"}
    
    async def text_search(
        self,
        keywords: str,
        city: str = None,
        city_limit: bool = False,
        types: str = None,
        page: int = 1,
        page_size: int = 25
    ) -> Dict:
        """
        关键字搜索POI
        
        Args:
            keywords: 搜索关键词
            city: 城市名称
            city_limit: 是否限制在城市内
            types: POI类型编码
            page: 页码
            page_size: 每页数量
        """
        params = {
            "keywords": keywords,
            "offset": page_size,
            "page": page,
            "extensions": "all"
        }
        
        if city:
            params["city"] = city
            params["citylimit"] = "true" if city_limit else "false"
        
        if types:
            params["types"] = types
        
        return await self._request("place/text", params)
    
    async def around_search(
        self,
        location: str,
        radius: int = 1000,
        keywords: str = None,
        types: str = None,
        page: int = 1,
        page_size: int = 25
    ) -> Dict:
        """
        周边搜索POI
        
        Args:
            location: 中心点坐标 "lng,lat"
            radius: 搜索半径（米）
            keywords: 搜索关键词
            types: POI类型编码
            page: 页码
            page_size: 每页数量
        """
        params = {
            "location": location,
            "radius": radius,
            "offset": page_size,
            "page": page,
            "extensions": "all"
        }
        
        if keywords:
            params["keywords"] = keywords
        if types:
            params["types"] = types
        
        return await self._request("place/around", params)
    
    async def geocode(
        self,
        address: str,
        city: str = None
    ) -> Dict:
        """
        地理编码（地址转坐标）
        
        Args:
            address: 地址字符串
            city: 城市名称
        """
        params = {"address": address}
        if city:
            params["city"] = city
        
        return await self._request("geocode/geo", params)
    
    async def regeocode(
        self,
        location: str,
        radius: int = 1000,
        extensions: str = "all"
    ) -> Dict:
        """
        逆地理编码（坐标转地址）
        
        Args:
            location: 坐标 "lng,lat"
            radius: 搜索半径
            extensions: 返回信息详细程度
        """
        params = {
            "location": location,
            "radius": radius,
            "extensions": extensions
        }
        
        return await self._request("geocode/regeo", params)
    
    async def get_poi_detail(self, poi_id: str) -> Dict:
        """
        获取POI详情
        
        Args:
            poi_id: POI的ID
        """
        params = {"id": poi_id}
        return await self._request("place/detail", params)
    
    async def search_all_pages(
        self,
        search_func,
        max_pages: int = 20,
        **kwargs
    ) -> List[Dict]:
        """
        搜索所有页的结果
        
        Args:
            search_func: 搜索函数
            max_pages: 最大页数
            **kwargs: 搜索参数
        """
        all_pois = []
        page = 1
        
        while page <= max_pages:
            result = await search_func(page=page, **kwargs)
            pois = result.get("pois", [])
            
            if not pois:
                break
            
            all_pois.extend(pois)
            
            count = int(result.get("count", 0))
            if len(all_pois) >= count:
                break
            
            page += 1
            await asyncio.sleep(0.1)
        
        return all_pois


class POICollector:
    """POI数据采集器"""
    
    POI_TYPES = {
        "school": "050301,050302,050303",  # 小学、中学、幼儿园
        "hospital": "060101,060102",       # 综合医院、专科医院
        "subway": "150101",                 # 地铁站
        "mall": "050101,050102",           # 购物中心、超市
        "park": "070101",                   # 公园
        "bank": "060201",                   # 银行
    }
    
    def __init__(self, client: AmapClient):
        self.client = client
    
    async def collect_community_pois(
        self,
        community_location: str,
        community_id: str,
        radius_list: List[int] = None
    ) -> List[Dict]:
        """
        采集小区周边POI
        
        Args:
            community_location: 小区坐标 "lng,lat"
            community_id: 小区ID
            radius_list: 搜索半径列表
        """
        if radius_list is None:
            radius_list = [500, 1000, 2000]
        
        all_pois = []
        
        for poi_type, type_codes in self.POI_TYPES.items():
            for radius in radius_list:
                try:
                    await asyncio.sleep(0.5)
                    
                    pois = await self.client.search_all_pages(
                        self.client.around_search,
                        location=community_location,
                        radius=radius,
                        types=type_codes,
                        max_pages=5
                    )
                    
                    for poi in pois:
                        distance = float(poi.get("distance", 0))
                        location = poi.get("location", "").split(",")
                        
                        all_pois.append({
                            "community_id": community_id,
                            "poi_id": poi.get("id"),
                            "name": poi.get("name"),
                            "type": poi_type,
                            "type_code": poi.get("typecode"),
                            "address": poi.get("address"),
                            "distance": distance,
                            "lng": float(location[0]) if len(location) == 2 else None,
                            "lat": float(location[1]) if len(location) == 2 else None,
                            "radius": radius
                        })
                    
                    await asyncio.sleep(0.05)
                    
                except Exception as e:
                    logger.error(f"Failed to collect POI for {community_id}: {e}")
        
        return all_pois


class CommunityCollector:
    """小区数据采集器"""
    
    SEARCH_KEYWORDS = ["小区", "住宅区", "花园", "苑", "居", "公寓"]
    
    def __init__(self, client: AmapClient):
        self.client = client
    
    async def collect_by_district(
        self,
        city: str,
        district: str,
        max_pages: int = 20
    ) -> List[Dict]:
        """
        按区县采集小区数据
        
        Args:
            city: 城市名称
            district: 区县名称
            max_pages: 最大页数
        """
        all_communities = []
        seen_ids = set()
        
        for keyword in self.SEARCH_KEYWORDS:
            try:
                search_keyword = f"{district}{keyword}"
                
                pois = await self.client.search_all_pages(
                    self.client.text_search,
                    keywords=search_keyword,
                    city=city,
                    city_limit=True,
                    max_pages=max_pages
                )
                
                for poi in pois:
                    poi_id = poi.get("id")
                    if poi_id in seen_ids:
                        continue
                    
                    seen_ids.add(poi_id)
                    location = poi.get("location", "").split(",")
                    
                    community = {
                        "poi_id": poi_id,
                        "name": poi.get("name"),
                        "type": poi.get("type"),
                        "type_code": poi.get("typecode"),
                        "address": poi.get("address"),
                        "lng": float(location[0]) if len(location) == 2 else None,
                        "lat": float(location[1]) if len(location) == 2 else None,
                        "province": poi.get("pname"),
                        "city": poi.get("cityname"),
                        "district": poi.get("adname"),
                        "adcode": poi.get("adcode")
                    }
                    
                    all_communities.append(community)
                
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Failed to collect communities in {district}: {e}")
        
        return all_communities


async def test_amap_client():
    """测试高德API客户端"""
    print("="*60)
    print("🗺️  高德API客户端测试")
    print("="*60)
    
    config = AmapConfig()
    
    async with AmapClient(config) as client:
        # 测试地理编码
        print("\n测试地理编码...")
        result = await client.geocode("深圳市南山区科技园")
        if result.get("status") == "1":
            geocodes = result.get("geocodes", [])
            if geocodes:
                print(f"✅ 地址: 深圳市南山区科技园")
                print(f"   坐标: {geocodes[0].get('location')}")
        
        # 测试POI搜索
        print("\n测试POI搜索...")
        result = await client.text_search(
            keywords="华润城",
            city="深圳",
            page_size=5
        )
        if result.get("status") == "1":
            pois = result.get("pois", [])
            print(f"✅ 找到 {len(pois)} 个POI")
            for poi in pois[:3]:
                print(f"   - {poi.get('name')}: {poi.get('address')}")
        
        # 测试周边搜索
        print("\n测试周边搜索...")
        result = await client.around_search(
            location="113.942,22.538",  # 华润城坐标
            radius=1000,
            types="150101",  # 地铁站
            page_size=5
        )
        if result.get("status") == "1":
            pois = result.get("pois", [])
            print(f"✅ 找到 {len(pois)} 个地铁站")
            for poi in pois[:3]:
                print(f"   - {poi.get('name')}: 距离 {poi.get('distance')}米")
        
        print(f"\n总请求次数: {client.request_count}")


if __name__ == "__main__":
    asyncio.run(test_amap_client())
