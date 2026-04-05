"""
实体识别服务 V2
改进版解析算法，使用更智能的实体提取策略
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
    source: str


@dataclass
class ParsedRequirementV2:
    """解析后的需求 V2"""
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
    
    parsing_notes: List[str] = field(default_factory=list)


CITY_DATA = {
    "北京": {"aliases": ["北京市", "帝都", "京城"], "districts": ["朝阳区", "海淀区", "西城区", "东城区", "丰台区", "通州区", "大兴区", "昌平区", "顺义区", "房山区", "石景山区", "门头沟区"]},
    "上海": {"aliases": ["上海市", "魔都", "沪"], "districts": ["浦东新区", "黄浦区", "徐汇区", "长宁区", "静安区", "普陀区", "虹口区", "杨浦区", "闵行区", "宝山区", "嘉定区", "松江区", "青浦区", "奉贤区", "金山区"]},
    "广州": {"aliases": ["广州市", "羊城", "穗"], "districts": ["天河区", "越秀区", "海珠区", "荔湾区", "白云区", "番禺区", "黄埔区", "花都区", "南沙区", "增城区", "从化区"]},
    "深圳": {"aliases": ["深圳市", "鹏城", "特区"], "districts": ["南山区", "福田区", "罗湖区", "宝安区", "龙岗区", "龙华区", "光明区", "坪山区", "盐田区"]},
    "杭州": {"aliases": ["杭州市", "西湖"], "districts": ["西湖区", "上城区", "拱墅区", "滨江区", "萧山区", "余杭区", "临平区", "钱塘区", "富阳区", "临安区"]},
    "成都": {"aliases": ["成都市", "蓉城"], "districts": ["锦江区", "青羊区", "金牛区", "武侯区", "成华区", "龙泉驿区", "新都区", "温江区", "双流区", "郫都区"]},
    "武汉": {"aliases": ["武汉市", "江城"], "districts": ["武昌区", "江汉区", "江岸区", "硚口区", "汉阳区", "青山区", "洪山区", "东西湖区", "汉南区", "蔡甸区", "江夏区", "黄陂区", "新洲区"]},
    "南京": {"aliases": ["南京市", "金陵"], "districts": ["玄武区", "秦淮区", "建邺区", "鼓楼区", "浦口区", "栖霞区", "雨花台区", "江宁区", "六合区", "溧水区", "高淳区"]},
    "重庆": {"aliases": ["重庆市", "山城"], "districts": ["渝中区", "江北区", "南岸区", "九龙坡区", "沙坪坝区", "大渡口区", "渝北区", "巴南区", "北碚区"]},
    "西安": {"aliases": ["西安市", "长安"], "districts": ["碑林区", "莲湖区", "新城区", "雁塔区", "灞桥区", "未央区", "长安区", "临潼区", "阎良区"]},
    "苏州": {"aliases": ["苏州市", "姑苏"], "districts": ["姑苏区", "虎丘区", "吴中区", "相城区", "吴江区", "工业园区", "高新区"]},
    "天津": {"aliases": ["天津市", "津门"], "districts": ["和平区", "河东区", "河西区", "南开区", "河北区", "红桥区", "滨海新区", "东丽区", "西青区", "津南区", "北辰区", "武清区"]},
    "长沙": {"aliases": ["长沙市", "星城"], "districts": ["芙蓉区", "天心区", "岳麓区", "开福区", "雨花区", "望城区", "长沙县"]},
    "郑州": {"aliases": ["郑州市", "绿城"], "districts": ["中原区", "二七区", "管城区", "金水区", "上街区", "惠济区", "郑东新区", "经开区", "高新区"]},
    "合肥": {"aliases": ["合肥市", "庐州"], "districts": ["瑶海区", "庐阳区", "蜀山区", "包河区", "经开区", "高新区", "新站区"]},
}


class EntityRecognizerV2:
    """实体识别器 V2 - 改进版"""
    
    def __init__(self):
        self.city_patterns = self._build_city_patterns()
        self.district_city_map = self._build_district_map()
    
    def _build_city_patterns(self) -> Dict[str, str]:
        """构建城市匹配模式"""
        patterns = {}
        for city, data in CITY_DATA.items():
            patterns[city] = city
            for alias in data.get("aliases", []):
                patterns[alias] = city
        return patterns
    
    def _build_district_map(self) -> Dict[str, str]:
        """构建区域到城市的映射"""
        mapping = {}
        for city, data in CITY_DATA.items():
            for district in data.get("districts", []):
                mapping[district] = city
                short_name = district.replace("区", "").replace("县", "")
                if short_name:
                    mapping[short_name] = city
        return mapping
    
    def _normalize_query(self, query: str) -> str:
        """标准化查询文本"""
        query = query.replace("，", " ").replace("。", " ")
        query = re.sub(r'\s+', ' ', query)
        return query.strip()
    
    def extract_city(self, query: str) -> Optional[ExtractedEntity]:
        """提取城市 - V2 改进版"""
        for pattern, city in self.city_patterns.items():
            if pattern in query:
                return ExtractedEntity(
                    value=city,
                    confidence=0.95,
                    source="explicit"
                )
        
        for district, city in self.district_city_map.items():
            if district in query:
                return ExtractedEntity(
                    value=city,
                    confidence=0.8,
                    source="inferred"
                )
        
        return None
    
    def extract_district(self, query: str, city: str = None) -> Optional[ExtractedEntity]:
        """提取区域 - V2 改进版"""
        if city and city in CITY_DATA:
            known_districts = CITY_DATA[city].get("districts", [])
            for district in known_districts:
                if district in query:
                    return ExtractedEntity(
                        value=district,
                        confidence=0.95,
                        source="explicit"
                    )
        
        for district, mapped_city in self.district_city_map.items():
            if district in query:
                return ExtractedEntity(
                    value=district,
                    confidence=0.85,
                    source="explicit"
                )
        
        patterns = [
            r"([\u4e00-\u9fa5]{2,4}[区县旗])",
            r"([\u4e00-\u9fa5]{2,4}新区)",
            r"([\u4e00-\u9fa5]{2,4}开发区)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                return ExtractedEntity(
                    value=match.group(1),
                    confidence=0.75,
                    source="explicit"
                )
        
        return None
    
    def extract_community(self, query: str) -> Optional[ExtractedEntity]:
        """提取小区名称 - V2 改进版"""
        patterns = [
            r"([\u4e00-\u9fa5]{2,10}(小区|花园|苑|城|府|院|湾|庭|居|家园|公寓|大厦|公馆|名邸|华府|雅苑|豪庭))",
            r"([\u4e00-\u9fa5]{2,8}(·|•)[\u4e00-\u9fa5]{2,8})",
            r"([\u4e00-\u9fa5]{3,8}(壹号|二号|三号|四号|五号))",
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
        """提取户型 - V2 改进版"""
        room_count = None
        hall_count = None
        
        chinese_num = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, 
                       "六": 6, "七": 7, "八": 8, "九": 9, "十": 10,
                       "两": 2, "双": 2}
        
        patterns = [
            (r"(\d)[室房居](\d)厅", "standard"),
            (r"(\d)[室房居](\d)卫", "room_wei"),
            (r"([一二三四五六七八九十两])[室房居](?:([一二三四五六七八九十两])厅)?", "chinese"),
            (r"(\d)居室?", "simple"),
            (r"([一二三四五六七八九十两])居室?", "chinese_simple"),
            (r"小户型", "small"),
            (r"大户型", "large"),
        ]
        
        for pattern, pattern_type in patterns:
            match = re.search(pattern, query)
            if match:
                if pattern_type == "standard":
                    room_count = ExtractedEntity(value=int(match.group(1)), confidence=0.95, source="explicit")
                    hall_count = ExtractedEntity(value=int(match.group(2)), confidence=0.9, source="explicit")
                elif pattern_type == "room_wei":
                    room_count = ExtractedEntity(value=int(match.group(1)), confidence=0.95, source="explicit")
                    hall_count = ExtractedEntity(value=1, confidence=0.6, source="default")
                elif pattern_type == "chinese":
                    room_count = ExtractedEntity(value=chinese_num.get(match.group(1), 0), confidence=0.9, source="explicit")
                    if match.group(2):
                        hall_count = ExtractedEntity(value=chinese_num.get(match.group(2), 0), confidence=0.85, source="explicit")
                elif pattern_type == "simple":
                    room_count = ExtractedEntity(value=int(match.group(1)), confidence=0.9, source="explicit")
                elif pattern_type == "chinese_simple":
                    room_count = ExtractedEntity(value=chinese_num.get(match.group(1), 0), confidence=0.85, source="explicit")
                elif pattern_type == "small":
                    room_count = ExtractedEntity(value=1, confidence=0.7, source="inferred")
                elif pattern_type == "large":
                    room_count = ExtractedEntity(value=4, confidence=0.6, source="inferred")
                break
        
        return room_count, hall_count
    
    def extract_area(self, query: str) -> Tuple[Optional[ExtractedEntity], Optional[ExtractedEntity]]:
        """提取面积 - V2 改进版"""
        area_min = None
        area_max = None
        
        patterns = [
            (r"(\d+)[-~至](\d+)\s*[平米平方米㎡]", "range"),
            (r"(\d+)\s*[平米平方米㎡](?:左右|上下)?", "single"),
            (r"(\d+)平(?:米)?(?:左右|上下)?", "short"),
            (r"面积[约大概]?(\d+)", "prefix"),
            (r"建面[约大概]?(\d+)", "building_area"),
            (r"套内[约大概]?(\d+)", "inner_area"),
        ]
        
        for pattern, pattern_type in patterns:
            match = re.search(pattern, query)
            if match:
                if pattern_type == "range":
                    area_min = ExtractedEntity(value=int(match.group(1)), confidence=0.9, source="explicit")
                    area_max = ExtractedEntity(value=int(match.group(2)), confidence=0.9, source="explicit")
                else:
                    area = int(match.group(1))
                    area_min = ExtractedEntity(value=area, confidence=0.85, source="explicit")
                    area_max = ExtractedEntity(value=area, confidence=0.85, source="explicit")
                break
        
        return area_min, area_max
    
    def extract_price(self, query: str) -> Tuple[Optional[ExtractedEntity], Optional[ExtractedEntity]]:
        """提取价格 - V2 改进版"""
        price_min = None
        price_max = None
        
        patterns = [
            (r"(\d+)[-~至](\d+)\s*[万w](?:元)?", "range_wan"),
            (r"(\d+)[万w](?:元)?(?:左右|上下|以内|以下)?", "single_wan"),
            (r"预算[约大概]?(\d+)[万w]?", "budget"),
            (r"总价[约大概]?(\d+)[万w]?", "total"),
            (r"首付[约大概]?(\d+)[万w]?", "down_payment"),
            (r"(\d{3,6})\s*元", "yuan"),
        ]
        
        for pattern, pattern_type in patterns:
            match = re.search(pattern, query)
            if match:
                if pattern_type == "range_wan":
                    price_min = ExtractedEntity(value=int(match.group(1)) * 10000, confidence=0.9, source="explicit")
                    price_max = ExtractedEntity(value=int(match.group(2)) * 10000, confidence=0.9, source="explicit")
                elif pattern_type in ["single_wan", "budget", "total"]:
                    price = int(match.group(1)) * 10000
                    price_min = ExtractedEntity(value=price, confidence=0.85, source="explicit")
                    price_max = ExtractedEntity(value=price, confidence=0.85, source="explicit")
                elif pattern_type == "down_payment":
                    down_payment = int(match.group(1)) * 10000
                    estimated_total = down_payment * 3
                    price_min = ExtractedEntity(value=estimated_total * 0.8, confidence=0.5, source="inferred")
                    price_max = ExtractedEntity(value=estimated_total * 1.2, confidence=0.5, source="inferred")
                elif pattern_type == "yuan":
                    price = int(match.group(1))
                    price_min = ExtractedEntity(value=price, confidence=0.8, source="explicit")
                    price_max = ExtractedEntity(value=price, confidence=0.8, source="explicit")
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
            (r"老房", "old"),
        ]
        
        for pattern, pattern_type in patterns:
            match = re.search(pattern, query)
            if match:
                if pattern_type == "range":
                    age_min = ExtractedEntity(value=int(match.group(1)), confidence=0.85, source="explicit")
                    age_max = ExtractedEntity(value=int(match.group(2)), confidence=0.85, source="explicit")
                elif pattern_type in ["single", "max"]:
                    age_max = ExtractedEntity(value=int(match.group(1)), confidence=0.85, source="explicit")
                elif pattern_type == "new":
                    age_max = ExtractedEntity(value=5, confidence=0.7, source="inferred")
                elif pattern_type == "very_new":
                    age_max = ExtractedEntity(value=2, confidence=0.7, source="inferred")
                elif pattern_type == "old":
                    age_min = ExtractedEntity(value=15, confidence=0.6, source="inferred")
                break
        
        return age_min, age_max
    
    def extract_orientation(self, query: str) -> Optional[ExtractedEntity]:
        """提取朝向"""
        orientation_patterns = {
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
        
        for orientation, patterns in orientation_patterns.items():
            for pattern in patterns:
                if pattern in query:
                    return ExtractedEntity(value=orientation, confidence=0.9, source="explicit")
        return None
    
    def extract_floor_type(self, query: str) -> Optional[ExtractedEntity]:
        """提取楼层类型"""
        floor_patterns = {
            "低层": ["低层", "低楼层", "1-6层", "多层"],
            "中层": ["中层", "中楼层", "7-15层"],
            "高层": ["高层", "高楼层", "16层以上", "超高层"],
            "顶层": ["顶层", "顶楼"],
            "底层": ["底层", "底楼", "一楼", "1楼"],
            "带电梯": ["带电梯", "有电梯"],
            "无电梯": ["无电梯", "没电梯", "步梯房"],
        }
        
        for floor_type, patterns in floor_patterns.items():
            for pattern in patterns:
                if pattern in query:
                    return ExtractedEntity(value=floor_type, confidence=0.85, source="explicit")
        return None
    
    def extract_decoration(self, query: str) -> Optional[ExtractedEntity]:
        """提取装修"""
        decoration_patterns = {
            "毛坯": ["毛坯", "清水房", "未装修"],
            "简装": ["简装", "简单装修", "基础装修"],
            "精装": ["精装", "精装修", "豪华装修", "豪装"],
            "中装": ["中装", "中等装修"],
            "拎包入住": ["拎包入住", "全配", "带家具家电"],
        }
        
        for decoration, patterns in decoration_patterns.items():
            for pattern in patterns:
                if pattern in query:
                    return ExtractedEntity(value=decoration, confidence=0.85, source="explicit")
        return None
    
    def extract_special_requirements(self, query: str) -> Tuple[Optional[ExtractedEntity], Optional[ExtractedEntity], List[str]]:
        """提取特殊需求"""
        is_school_district = None
        is_near_subway = None
        special_requirements = []
        
        school_keywords = ["学区", "名校", "重点小学", "重点中学", "学位房", "学区房", "双学区"]
        subway_keywords = ["地铁", "地铁站", "地铁房", "近地铁", "地铁口", "地铁沿线"]
        
        for keyword in school_keywords:
            if keyword in query:
                is_school_district = ExtractedEntity(value=True, confidence=0.9, source="explicit")
                special_requirements.append(f"学区房({keyword})")
                break
        
        for keyword in subway_keywords:
            if keyword in query:
                is_near_subway = ExtractedEntity(value=True, confidence=0.9, source="explicit")
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
            (r"南北通透", "南北通透"),
            (r"精装修", "精装修"),
            (r"满五唯一", "满五唯一"),
            (r"满二", "满二"),
        ]
        
        for pattern, requirement in other_patterns:
            if re.search(pattern, query):
                special_requirements.append(requirement)
        
        return is_school_district, is_near_subway, special_requirements
    
    def parse(self, query: str) -> ParsedRequirementV2:
        """
        解析自然语言查询 V2
        
        Args:
            query: 用户输入的自然语言
            
        Returns:
            ParsedRequirementV2: 解析后的需求
        """
        normalized_query = self._normalize_query(query)
        result = ParsedRequirementV2(raw_query=query)
        
        result.city = self.extract_city(normalized_query)
        
        city = result.city.value if result.city else None
        result.district = self.extract_district(normalized_query, city)
        
        if result.district and not result.city:
            for district, mapped_city in self.district_city_map.items():
                if result.district.value == district:
                    result.city = ExtractedEntity(value=mapped_city, confidence=0.8, source="inferred")
                    result.parsing_notes.append(f"根据区域'{district}'推断城市为'{mapped_city}'")
                    break
        
        result.community = self.extract_community(normalized_query)
        
        result.room_count, result.hall_count = self.extract_room_layout(normalized_query)
        result.area_min, result.area_max = self.extract_area(normalized_query)
        result.price_min, result.price_max = self.extract_price(normalized_query)
        result.age_min, result.age_max = self.extract_age(normalized_query)
        
        result.orientation = self.extract_orientation(normalized_query)
        result.floor_type = self.extract_floor_type(normalized_query)
        result.decoration = self.extract_decoration(normalized_query)
        
        (result.is_school_district, 
         result.is_near_subway, 
         result.special_requirements) = self.extract_special_requirements(normalized_query)
        
        required_fields = ["city", "room_count"]
        recommended_fields = ["district", "area_min", "price_max"]
        
        for field in required_fields:
            if getattr(result, field) is None:
                result.missing_fields.append(field)
        
        for field in recommended_fields:
            if getattr(result, field) is None:
                result.missing_fields.append(field)
        
        return result


entity_recognizer_v2 = EntityRecognizerV2()


def parse_natural_language_v2(query: str) -> ParsedRequirementV2:
    """
    解析自然语言查询 V2（便捷函数）
    
    Args:
        query: 用户输入
        
    Returns:
        ParsedRequirementV2: 解析结果
    """
    return entity_recognizer_v2.parse(query)
