"""
实体识别服务
从自然语言中提取房产相关实体信息
"""
import re
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ExtractedEntity:
    """提取的实体"""
    value: Any
    confidence: float
    source: str  # 'explicit', 'inferred', 'default'


@dataclass
class ParsedRequirement:
    """解析后的需求"""
    raw_query: str
    city: Optional[ExtractedEntity] = None
    district: Optional[ExtractedEntity] = None
    community: Optional[ExtractedEntity] = None
    
    room_count: Optional[ExtractedEntity] = None
    hall_count: Optional[ExtractedEntity] = None
    
    area_min: Optional[ExtractedEntity] = None
    area_max: Optional[ExtractedEntity] = None
    
    price_min: Optional[ExtractedEntity] = None
    price_max: Optional[ExtractedEntity] = None
    
    age_min: Optional[ExtractedEntity] = None
    age_max: Optional[ExtractedEntity] = None
    
    orientation: Optional[ExtractedEntity] = None
    floor_type: Optional[ExtractedEntity] = None
    decoration: Optional[ExtractedEntity] = None
    
    is_school_district: Optional[ExtractedEntity] = None
    is_near_subway: Optional[ExtractedEntity] = None
    
    special_requirements: List[str] = field(default_factory=list)
    
    missing_fields: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {"raw_query": self.raw_query}
        
        for field_name in [
            "city", "district", "community",
            "room_count", "hall_count",
            "area_min", "area_max",
            "price_min", "price_max",
            "age_min", "age_max",
            "orientation", "floor_type", "decoration",
            "is_school_district", "is_near_subway"
        ]:
            entity = getattr(self, field_name)
            if entity:
                result[field_name] = {
                    "value": entity.value,
                    "confidence": entity.confidence,
                    "source": entity.source
                }
            else:
                result[field_name] = None
        
        result["special_requirements"] = self.special_requirements
        result["missing_fields"] = self.missing_fields
        
        return result


CITY_ALIASES = {
    "北京": ["北京市", "帝都", "京城"],
    "上海": ["上海市", "魔都", "沪"],
    "广州": ["广州市", "羊城", "穗"],
    "深圳": ["深圳市", "鹏城", "特区"],
    "杭州": ["杭州市", "西湖"],
    "成都": ["成都市", "蓉城"],
    "武汉": ["武汉市", "江城"],
    "南京": ["南京市", "金陵"],
    "重庆": ["重庆市", "山城"],
    "西安": ["西安市", "长安"],
    "苏州": ["苏州市", "姑苏"],
    "天津": ["天津市", "津门"],
    "长沙": ["长沙市", "星城"],
    "郑州": ["郑州市", "绿城"],
    "青岛": ["青岛市", "岛城"],
    "大连": ["大连市", "滨城"],
    "厦门": ["厦门市", "鹭岛"],
    "宁波": ["宁波市", "甬城"],
    "无锡": ["无锡市", "梁溪"],
    "合肥": ["合肥市", "庐州"],
}

ORIENTATION_PATTERNS = {
    "南": ["朝南", "向南", "正南", "南向", "坐北朝南"],
    "北": ["朝北", "向北", "正北", "北向"],
    "东": ["朝东", "向东", "正东", "东向"],
    "西": ["朝西", "向西", "正西", "西向"],
    "东南": ["朝东南", "东南向"],
    "西南": ["朝西南", "西南向"],
    "东北": ["朝东北", "东北向"],
    "西北": ["朝西北", "西北向"],
    "南北通透": ["南北通透", "双朝向", "南北"],
}

FLOOR_TYPE_PATTERNS = {
    "低层": ["低层", "低楼层", "1-6层", "多层"],
    "中层": ["中层", "中楼层", "7-15层"],
    "高层": ["高层", "高楼层", "16层以上", "超高层"],
    "顶层": ["顶层", "顶楼"],
    "底层": ["底层", "底楼", "一楼", "1楼"],
    "带电梯": ["带电梯", "有电梯"],
    "无电梯": ["无电梯", "没电梯", "步梯房"],
}

DECORATION_PATTERNS = {
    "毛坯": ["毛坯", "清水房", "未装修"],
    "简装": ["简装", "简单装修", "基础装修"],
    "精装": ["精装", "精装修", "豪华装修", "豪装"],
    "中装": ["中装", "中等装修"],
    "拎包入住": ["拎包入住", "全配", "带家具家电"],
}

SCHOOL_KEYWORDS = ["学区", "名校", "重点小学", "重点中学", "学位房", "学区房"]
SUBWAY_KEYWORDS = ["地铁", "地铁站", "地铁房", "近地铁", "地铁口"]


class EntityRecognizer:
    """实体识别器"""
    
    def __init__(self):
        self.city_patterns = self._build_city_patterns()
    
    def _build_city_patterns(self) -> Dict[str, str]:
        """构建城市匹配模式"""
        patterns = {}
        for city, aliases in CITY_ALIASES.items():
            patterns[city] = city
            for alias in aliases:
                patterns[alias] = city
        return patterns
    
    def extract_city(self, query: str) -> Optional[ExtractedEntity]:
        """提取城市"""
        for pattern, city in self.city_patterns.items():
            if pattern in query:
                return ExtractedEntity(
                    value=city,
                    confidence=0.95,
                    source="explicit"
                )
        return None
    
    def extract_district(self, query: str, city: str = None) -> Optional[ExtractedEntity]:
        """提取区域"""
        district_patterns = [
            r"([\u4e00-\u9fa5]{2,4}[区县旗])",
            r"([\u4e00-\u9fa5]{2,4}新区)",
            r"([\u4e00-\u9fa5]{2,4}开发区)",
        ]
        
        for pattern in district_patterns:
            match = re.search(pattern, query)
            if match:
                return ExtractedEntity(
                    value=match.group(1),
                    confidence=0.85,
                    source="explicit"
                )
        
        return None
    
    def extract_community(self, query: str) -> Optional[ExtractedEntity]:
        """提取小区名称"""
        patterns = [
            r"([\u4e00-\u9fa5]{2,10}(小区|花园|苑|城|府|院|湾|府|庭|居|家园|公寓|大厦))",
            r"([\u4e00-\u9fa5]{2,8}(·|•)[\u4e00-\u9fa5]{2,8})",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                return ExtractedEntity(
                    value=match.group(1),
                    confidence=0.8,
                    source="explicit"
                )
        
        return None
    
    def extract_room_layout(self, query: str) -> Tuple[Optional[ExtractedEntity], Optional[ExtractedEntity]]:
        """提取户型"""
        room_count = None
        hall_count = None
        
        patterns = [
            (r"(\d)[室房居](\d)?厅?", "standard"),
            (r"([一二三四五六七八九十])[室房居](?:([一二三四五六七八九十])厅)?", "chinese"),
            (r"(\d)居室?", "simple"),
        ]
        
        chinese_num = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, 
                       "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
        
        for pattern, pattern_type in patterns:
            match = re.search(pattern, query)
            if match:
                if pattern_type == "standard":
                    room_count = ExtractedEntity(
                        value=int(match.group(1)),
                        confidence=0.95,
                        source="explicit"
                    )
                    if match.group(2):
                        hall_count = ExtractedEntity(
                            value=int(match.group(2)),
                            confidence=0.9,
                            source="explicit"
                        )
                elif pattern_type == "chinese":
                    room_count = ExtractedEntity(
                        value=chinese_num.get(match.group(1), 0),
                        confidence=0.9,
                        source="explicit"
                    )
                    if match.group(2):
                        hall_count = ExtractedEntity(
                            value=chinese_num.get(match.group(2), 0),
                            confidence=0.85,
                            source="explicit"
                        )
                elif pattern_type == "simple":
                    room_count = ExtractedEntity(
                        value=int(match.group(1)),
                        confidence=0.9,
                        source="explicit"
                    )
                break
        
        return room_count, hall_count
    
    def extract_area(self, query: str) -> Tuple[Optional[ExtractedEntity], Optional[ExtractedEntity]]:
        """提取面积"""
        area_min = None
        area_max = None
        
        patterns = [
            (r"(\d+)[-~至](\d+)\s*[平米平方米㎡]", "range"),
            (r"(\d+)\s*[平米平方米㎡](?:左右|上下)?", "single"),
            (r"(\d+)平(?:米)?(?:左右|上下)?", "short"),
            (r"面积[约大概]?(\d+)", "prefix"),
        ]
        
        for pattern, pattern_type in patterns:
            match = re.search(pattern, query)
            if match:
                if pattern_type == "range":
                    area_min = ExtractedEntity(
                        value=int(match.group(1)),
                        confidence=0.9,
                        source="explicit"
                    )
                    area_max = ExtractedEntity(
                        value=int(match.group(2)),
                        confidence=0.9,
                        source="explicit"
                    )
                else:
                    area = int(match.group(1))
                    area_min = ExtractedEntity(
                        value=area,
                        confidence=0.85,
                        source="explicit"
                    )
                    area_max = ExtractedEntity(
                        value=area,
                        confidence=0.85,
                        source="explicit"
                    )
                break
        
        return area_min, area_max
    
    def extract_price(self, query: str) -> Tuple[Optional[ExtractedEntity], Optional[ExtractedEntity]]:
        """提取价格"""
        price_min = None
        price_max = None
        
        patterns = [
            (r"(\d+)[-~至](\d+)\s*[万w](?:元)?", "range_wan"),
            (r"(\d+)[万w](?:元)?(?:左右|上下|以内|以下)?", "single_wan"),
            (r"预算[约大概]?(\d+)[万w]?", "budget"),
            (r"总价[约大概]?(\d+)[万w]?", "total"),
            (r"(\d{3,6})\s*元", "yuan"),
        ]
        
        for pattern, pattern_type in patterns:
            match = re.search(pattern, query)
            if match:
                if pattern_type == "range_wan":
                    price_min = ExtractedEntity(
                        value=int(match.group(1)) * 10000,
                        confidence=0.9,
                        source="explicit"
                    )
                    price_max = ExtractedEntity(
                        value=int(match.group(2)) * 10000,
                        confidence=0.9,
                        source="explicit"
                    )
                elif pattern_type in ["single_wan", "budget", "total"]:
                    price = int(match.group(1)) * 10000
                    price_min = ExtractedEntity(
                        value=price,
                        confidence=0.85,
                        source="explicit"
                    )
                    price_max = ExtractedEntity(
                        value=price,
                        confidence=0.85,
                        source="explicit"
                    )
                elif pattern_type == "yuan":
                    price = int(match.group(1))
                    price_min = ExtractedEntity(
                        value=price,
                        confidence=0.8,
                        source="explicit"
                    )
                    price_max = ExtractedEntity(
                        value=price,
                        confidence=0.8,
                        source="explicit"
                    )
                break
        
        return price_min, price_max
    
    def extract_age(self, query: str) -> Tuple[Optional[ExtractedEntity], Optional[ExtractedEntity]]:
        """提取房龄"""
        age_min = None
        age_max = None
        
        patterns = [
            (r"房龄(\d+)[-~至](\d+)年?", "range"),
            (r"房龄[约大概]?(\d+)年?", "single"),
            (r"(\d+)[年房龄]以内的?", "max"),
            (r"次新房", "new"),
            (r"新房", "very_new"),
        ]
        
        for pattern, pattern_type in patterns:
            match = re.search(pattern, query)
            if match:
                if pattern_type == "range":
                    age_min = ExtractedEntity(
                        value=int(match.group(1)),
                        confidence=0.85,
                        source="explicit"
                    )
                    age_max = ExtractedEntity(
                        value=int(match.group(2)),
                        confidence=0.85,
                        source="explicit"
                    )
                elif pattern_type == "single":
                    age_max = ExtractedEntity(
                        value=int(match.group(1)),
                        confidence=0.85,
                        source="explicit"
                    )
                elif pattern_type == "max":
                    age_max = ExtractedEntity(
                        value=int(match.group(1)),
                        confidence=0.8,
                        source="explicit"
                    )
                elif pattern_type == "new":
                    age_max = ExtractedEntity(
                        value=5,
                        confidence=0.7,
                        source="inferred"
                    )
                elif pattern_type == "very_new":
                    age_max = ExtractedEntity(
                        value=2,
                        confidence=0.7,
                        source="inferred"
                    )
                break
        
        return age_min, age_max
    
    def extract_orientation(self, query: str) -> Optional[ExtractedEntity]:
        """提取朝向"""
        for orientation, patterns in ORIENTATION_PATTERNS.items():
            for pattern in patterns:
                if pattern in query:
                    return ExtractedEntity(
                        value=orientation,
                        confidence=0.9,
                        source="explicit"
                    )
        return None
    
    def extract_floor_type(self, query: str) -> Optional[ExtractedEntity]:
        """提取楼层类型"""
        for floor_type, patterns in FLOOR_TYPE_PATTERNS.items():
            for pattern in patterns:
                if pattern in query:
                    return ExtractedEntity(
                        value=floor_type,
                        confidence=0.85,
                        source="explicit"
                    )
        return None
    
    def extract_decoration(self, query: str) -> Optional[ExtractedEntity]:
        """提取装修"""
        for decoration, patterns in DECORATION_PATTERNS.items():
            for pattern in patterns:
                if pattern in query:
                    return ExtractedEntity(
                        value=decoration,
                        confidence=0.85,
                        source="explicit"
                    )
        return None
    
    def extract_special_requirements(self, query: str) -> Tuple[Optional[ExtractedEntity], Optional[ExtractedEntity], List[str]]:
        """提取特殊需求"""
        is_school_district = None
        is_near_subway = None
        special_requirements = []
        
        for keyword in SCHOOL_KEYWORDS:
            if keyword in query:
                is_school_district = ExtractedEntity(
                    value=True,
                    confidence=0.9,
                    source="explicit"
                )
                special_requirements.append(f"学区房({keyword})")
                break
        
        for keyword in SUBWAY_KEYWORDS:
            if keyword in query:
                is_near_subway = ExtractedEntity(
                    value=True,
                    confidence=0.9,
                    source="explicit"
                )
                special_requirements.append(f"近地铁({keyword})")
                break
        
        other_patterns = [
            (r"带车位", "带车位"),
            (r"带花园", "带花园"),
            (r"带露台", "带露台"),
            (r"带地下室", "带地下室"),
            (r"顶层复式", "顶层复式"),
            (r"一楼带院", "一楼带院"),
            (r"电梯房", "有电梯"),
            (r"安静", "环境安静"),
            (r"采光好", "采光好"),
            (r"通风好", "通风好"),
        ]
        
        for pattern, requirement in other_patterns:
            if re.search(pattern, query):
                special_requirements.append(requirement)
        
        return is_school_district, is_near_subway, special_requirements
    
    def parse(self, query: str) -> ParsedRequirement:
        """
        解析自然语言查询
        
        Args:
            query: 用户输入的自然语言
            
        Returns:
            ParsedRequirement: 解析后的需求
        """
        result = ParsedRequirement(raw_query=query)
        
        result.city = self.extract_city(query)
        
        city = result.city.value if result.city else None
        result.district = self.extract_district(query, city)
        result.community = self.extract_community(query)
        
        result.room_count, result.hall_count = self.extract_room_layout(query)
        result.area_min, result.area_max = self.extract_area(query)
        result.price_min, result.price_max = self.extract_price(query)
        result.age_min, result.age_max = self.extract_age(query)
        
        result.orientation = self.extract_orientation(query)
        result.floor_type = self.extract_floor_type(query)
        result.decoration = self.extract_decoration(query)
        
        (result.is_school_district, 
         result.is_near_subway, 
         result.special_requirements) = self.extract_special_requirements(query)
        
        required_fields = ["city", "room_count"]
        recommended_fields = ["district", "area_min", "price_max"]
        
        for field in required_fields:
            if getattr(result, field) is None:
                result.missing_fields.append(field)
        
        for field in recommended_fields:
            if getattr(result, field) is None:
                result.missing_fields.append(field)
        
        return result


entity_recognizer = EntityRecognizer()


def parse_natural_language(query: str) -> ParsedRequirement:
    """
    解析自然语言查询（便捷函数）
    
    Args:
        query: 用户输入
        
    Returns:
        ParsedRequirement: 解析结果
    """
    return entity_recognizer.parse(query)
