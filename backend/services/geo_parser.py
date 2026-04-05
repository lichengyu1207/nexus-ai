"""
地理实体解析器
从自然语言中提取标准化地理实体
"""
import re
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class GeoResult:
    """地理解析结果"""
    province: Optional[str] = None
    province_id: Optional[str] = None
    city: Optional[str] = None
    city_id: Optional[str] = None
    district: Optional[str] = None
    district_id: Optional[str] = None
    street: Optional[str] = None
    street_id: Optional[str] = None
    community: Optional[str] = None
    community_id: Optional[str] = None
    level: str = "unknown"  # province, city, district, street, community
    confidence: float = 0.0
    coordinates: Optional[Dict] = None
    raw_text: str = ""


class GeoParser:
    """地理实体解析器"""
    
    # 城市别名映射
    CITY_ALIASES = {
        "深圳": "深圳市",
        "广州": "广州市",
        "北京": "北京市",
        "上海": "上海市",
        "杭州": "杭州市",
        "南京": "南京市",
        "成都": "成都市",
        "武汉": "武汉市",
        "西安": "西安市",
        "重庆": "重庆市",
        "东莞": "东莞市",
        "佛山": "佛山市",
        "珠海": "珠海市",
        "惠州": "惠州市",
        "中山": "中山市",
    }
    
    # 区域别名映射
    DISTRICT_ALIASES = {
        "南山": "南山区",
        "福田": "福田区",
        "罗湖": "罗湖区",
        "宝安": "宝安区",
        "龙岗": "龙岗区",
        "龙华": "龙华区",
        "光明": "光明区",
        "坪山": "坪山区",
        "盐田": "盐田区",
        "大鹏": "大鹏新区",
        "天河": "天河区",
        "越秀": "越秀区",
        "海珠": "海珠区",
        "荔湾": "荔湾区",
        "番禺": "番禺区",
        "朝阳": "朝阳区",
        "海淀": "海淀区",
        "西城": "西城区",
        "东城": "东城区",
        "浦东": "浦东新区",
        "黄浦": "黄浦区",
        "徐汇": "徐汇区",
        "静安": "静安区",
    }
    
    # 城市+区域组合别名映射
    CITY_DISTRICT_COMBOS = {
        "深圳南山": {"city": "深圳市", "district": "南山区"},
        "深圳福田": {"city": "深圳市", "district": "福田区"},
        "深圳罗湖": {"city": "深圳市", "district": "罗湖区"},
        "深圳宝安": {"city": "深圳市", "district": "宝安区"},
        "深圳龙岗": {"city": "深圳市", "district": "龙岗区"},
        "深圳龙华": {"city": "深圳市", "district": "龙华区"},
        "广州天河": {"city": "广州市", "district": "天河区"},
        "广州越秀": {"city": "广州市", "district": "越秀区"},
        "北京朝阳": {"city": "北京市", "district": "朝阳区"},
        "北京海淀": {"city": "北京市", "district": "海淀区"},
        "上海浦东": {"city": "上海市", "district": "浦东新区"},
        "上海黄浦": {"city": "上海市", "district": "黄浦区"},
    }
    
    # 热门城市数据（简化版，实际应从数据库加载）
    HOT_CITIES = {
        "深圳市": {
            "id": "city-440300",
            "province": "广东省",
            "province_id": "province-440000",
            "districts": {
                "南山区": {"id": "district-440305", "avg_price": 90000},
                "福田区": {"id": "district-440304", "avg_price": 85000},
                "罗湖区": {"id": "district-440303", "avg_price": 55000},
                "宝安区": {"id": "district-440306", "avg_price": 55000},
                "龙岗区": {"id": "district-440307", "avg_price": 45000},
                "龙华区": {"id": "district-440309", "avg_price": 55000},
                "光明区": {"id": "district-440311", "avg_price": 45000},
                "坪山区": {"id": "district-440310", "avg_price": 35000},
                "盐田区": {"id": "district-440308", "avg_price": 50000},
                "大鹏新区": {"id": "district-440312", "avg_price": 35000},
            }
        },
        "广州市": {
            "id": "city-440100",
            "province": "广东省",
            "province_id": "province-440000",
            "districts": {
                "天河区": {"id": "district-440106", "avg_price": 70000},
                "越秀区": {"id": "district-440104", "avg_price": 65000},
                "海珠区": {"id": "district-440105", "avg_price": 55000},
                "荔湾区": {"id": "district-440103", "avg_price": 45000},
                "番禺区": {"id": "district-440113", "avg_price": 35000},
            }
        },
        "北京市": {
            "id": "city-110100",
            "province": "北京市",
            "province_id": "province-110000",
            "districts": {
                "朝阳区": {"id": "district-110105", "avg_price": 80000},
                "海淀区": {"id": "district-110108", "avg_price": 90000},
                "西城区": {"id": "district-110102", "avg_price": 100000},
                "东城区": {"id": "district-110101", "avg_price": 95000},
            }
        },
        "上海市": {
            "id": "city-310100",
            "province": "上海市",
            "province_id": "province-310000",
            "districts": {
                "浦东新区": {"id": "district-310115", "avg_price": 75000},
                "黄浦区": {"id": "district-310101", "avg_price": 100000},
                "徐汇区": {"id": "district-310104", "avg_price": 85000},
                "静安区": {"id": "district-310106", "avg_price": 80000},
            }
        }
    }
    
    # 热门小区数据（简化版）
    HOT_COMMUNITIES = {
        "华润城": {"city": "深圳市", "district": "南山区", "id": "community-001", "avg_price": 98000},
        "深圳湾一号": {"city": "深圳市", "district": "南山区", "id": "community-002", "avg_price": 150000},
        "半岛城邦": {"city": "深圳市", "district": "南山区", "id": "community-003", "avg_price": 120000},
        "香蜜湖一号": {"city": "深圳市", "district": "福田区", "id": "community-004", "avg_price": 130000},
        "万科云城": {"city": "深圳市", "district": "南山区", "id": "community-005", "avg_price": 85000},
        "招商双玺": {"city": "深圳市", "district": "南山区", "id": "community-006", "avg_price": 140000},
        "中海天钻": {"city": "深圳市", "district": "福田区", "id": "community-007", "avg_price": 110000},
        "龙光玖龙玺": {"city": "深圳市", "district": "龙华区", "id": "community-008", "avg_price": 75000},
    }
    
    def __init__(self):
        self.city_trie = self._build_trie(self.HOT_CITIES.keys())
        self.district_trie = self._build_trie(
            [d for city in self.HOT_CITIES.values() for d in city["districts"].keys()]
        )
        self.community_trie = self._build_trie(self.HOT_COMMUNITIES.keys())
    
    def _build_trie(self, words: List[str]) -> Dict:
        """构建前缀树"""
        trie = {}
        for word in words:
            node = trie
            for char in word:
                if char not in node:
                    node[char] = {}
                node = node[char]
            node["__end__"] = True
        return trie
    
    def _search_trie(self, text: str, trie: Dict) -> List[str]:
        """在前缀树中搜索匹配"""
        results = []
        for i in range(len(text)):
            node = trie
            match = ""
            for j in range(i, len(text)):
                char = text[j]
                if char in node:
                    match += char
                    node = node[char]
                    if "__end__" in node:
                        results.append(match)
                else:
                    break
        return results
    
    def parse(self, text: str) -> GeoResult:
        """
        解析地理实体
        输入: "深圳南山区科技园华润城"
        输出: GeoResult对象
        """
        result = GeoResult(raw_text=text)
        
        # 预处理
        text = text.replace(" ", "").replace("，", "").replace("、", "")
        
        # 0. 优先检查城市+区域组合
        for combo, combo_data in self.CITY_DISTRICT_COMBOS.items():
            if combo in text:
                city_name = combo_data["city"]
                district_name = combo_data["district"]
                
                if city_name in self.HOT_CITIES:
                    city_data = self.HOT_CITIES[city_name]
                    result.city = city_name
                    result.city_id = city_data["id"]
                    result.province = city_data["province"]
                    result.province_id = city_data["province_id"]
                    result.district = district_name
                    
                    if district_name in city_data["districts"]:
                        result.district_id = city_data["districts"][district_name]["id"]
                    
                    result.level = "district"
                    result.confidence = 0.90
                    return result
        
        # 1. 匹配小区（优先级最高）
        community_matches = self._search_trie(text, self.community_trie)
        if community_matches:
            best_match = max(community_matches, key=len)
            if best_match in self.HOT_COMMUNITIES:
                community_data = self.HOT_COMMUNITIES[best_match]
                result.community = best_match
                result.community_id = community_data["id"]
                result.city = community_data["city"]
                result.district = community_data["district"]
                result.level = "community"
                result.confidence = 0.95
                
                # 填充城市和区域信息
                if result.city in self.HOT_CITIES:
                    city_data = self.HOT_CITIES[result.city]
                    result.city_id = city_data["id"]
                    result.province = city_data["province"]
                    result.province_id = city_data["province_id"]
                    
                    if result.district in city_data["districts"]:
                        result.district_id = city_data["districts"][result.district]["id"]
                
                return result
        
        # 2. 匹配区域
        district_matches = self._search_trie(text, self.district_trie)
        if district_matches:
            best_match = max(district_matches, key=len)
            
            # 处理别名
            normalized = self.DISTRICT_ALIASES.get(best_match, best_match)
            if not normalized.endswith("区") and not normalized.endswith("县") and not normalized.endswith("新区"):
                normalized = normalized + "区"
            
            # 查找对应城市
            for city_name, city_data in self.HOT_CITIES.items():
                if normalized in city_data["districts"]:
                    result.district = normalized
                    result.district_id = city_data["districts"][normalized]["id"]
                    result.city = city_name
                    result.city_id = city_data["id"]
                    result.province = city_data["province"]
                    result.province_id = city_data["province_id"]
                    result.level = "district"
                    result.confidence = 0.85
                    return result
        
        # 3. 匹配城市
        city_matches = self._search_trie(text, self.city_trie)
        if city_matches:
            best_match = max(city_matches, key=len)
            
            # 处理别名
            normalized = self.CITY_ALIASES.get(best_match, best_match)
            if not normalized.endswith("市"):
                normalized = normalized + "市"
            
            if normalized in self.HOT_CITIES:
                city_data = self.HOT_CITIES[normalized]
                result.city = normalized
                result.city_id = city_data["id"]
                result.province = city_data["province"]
                result.province_id = city_data["province_id"]
                result.level = "city"
                result.confidence = 0.9
                return result
        
        # 4. 匹配省份
        province_patterns = ["广东", "北京", "上海", "浙江", "江苏", "四川", "湖北", "陕西"]
        for province in province_patterns:
            if province in text:
                result.province = province + "省" if province != "北京" and province != "上海" else province + "市"
                result.level = "province"
                result.confidence = 0.7
                return result
        
        # 未匹配到任何地理实体
        result.level = "unknown"
        result.confidence = 0.0
        return result
    
    def suggest(self, query: str, limit: int = 10) -> List[Dict]:
        """
        自动补全建议
        输入: "深圳南"
        输出: [{"name": "深圳市", "type": "city"}, {"name": "南山区", "type": "district"}]
        """
        suggestions = []
        
        # 搜索城市
        for city_name in self.HOT_CITIES.keys():
            if query.lower() in city_name.lower():
                suggestions.append({
                    "name": city_name,
                    "type": "city",
                    "id": self.HOT_CITIES[city_name]["id"]
                })
        
        # 搜索区域
        for city_name, city_data in self.HOT_CITIES.items():
            for district_name in city_data["districts"].keys():
                if query.lower() in district_name.lower():
                    suggestions.append({
                        "name": district_name,
                        "type": "district",
                        "id": city_data["districts"][district_name]["id"],
                        "city": city_name
                    })
        
        # 搜索小区
        for community_name, community_data in self.HOT_COMMUNITIES.items():
            if query.lower() in community_name.lower():
                suggestions.append({
                    "name": community_name,
                    "type": "community",
                    "id": community_data["id"],
                    "city": community_data["city"],
                    "district": community_data["district"]
                })
        
        return suggestions[:limit]
    
    def to_dict(self, result: GeoResult) -> Dict:
        """将GeoResult转换为字典"""
        return {
            "province": result.province,
            "province_id": result.province_id,
            "city": result.city,
            "city_id": result.city_id,
            "district": result.district,
            "district_id": result.district_id,
            "street": result.street,
            "street_id": result.street_id,
            "community": result.community,
            "community_id": result.community_id,
            "level": result.level,
            "confidence": result.confidence,
            "coordinates": result.coordinates,
            "raw_text": result.raw_text
        }


# 测试代码
if __name__ == "__main__":
    parser = GeoParser()
    
    test_cases = [
        "深圳南山区科技园华润城",
        "深圳南山",
        "广州天河区",
        "北京朝阳区",
        "上海浦东",
        "我想在深圳买房",
        "南山区的房价怎么样",
    ]
    
    print("="*60)
    print("🗺️  地理实体解析测试")
    print("="*60)
    
    for text in test_cases:
        result = parser.parse(text)
        print(f"\n输入: {text}")
        print(f"解析结果: {parser.to_dict(result)}")
    
    print("\n" + "="*60)
    print("🔍 自动补全测试")
    print("="*60)
    
    suggest_queries = ["深圳南", "华润", "天河"]
    for query in suggest_queries:
        suggestions = parser.suggest(query)
        print(f"\n查询: {query}")
        print(f"建议: {json.dumps(suggestions, ensure_ascii=False, indent=2)}")
