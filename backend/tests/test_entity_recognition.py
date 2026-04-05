"""
需求解析服务单元测试
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.entity_recognition import (
    EntityRecognizer,
    ParsedRequirement,
    ExtractedEntity,
    parse_natural_language
)


class TestEntityRecognizer:
    """实体识别器测试"""
    
    @pytest.fixture
    def recognizer(self):
        return EntityRecognizer()
    
    def test_extract_city_explicit(self, recognizer):
        """测试显式城市提取"""
        result = recognizer.extract_city("我想在上海买房")
        assert result is not None
        assert result.value == "上海"
        assert result.confidence >= 0.9
    
    def test_extract_city_alias(self, recognizer):
        """测试城市别名提取"""
        result = recognizer.extract_city("魔都的房子怎么样")
        assert result is not None
        assert result.value == "上海"
    
    def test_extract_district(self, recognizer):
        """测试区域提取"""
        result = recognizer.extract_district("浦东新区的房价", "上海")
        assert result is not None
        assert "浦东" in result.value
    
    def test_extract_room_layout_standard(self, recognizer):
        """测试标准户型提取"""
        room, hall = recognizer.extract_room_layout("3室2厅的房子")
        assert room is not None
        assert room.value == 3
        assert hall is not None
        assert hall.value == 2
    
    def test_extract_room_layout_chinese(self, recognizer):
        """测试中文户型提取"""
        room, hall = recognizer.extract_room_layout("两室一厅")
        assert room is not None
        assert room.value == 2
        assert hall is not None
        assert hall.value == 1
    
    def test_extract_area_range(self, recognizer):
        """测试面积范围提取"""
        area_min, area_max = recognizer.extract_area("100-120平米的房子")
        assert area_min is not None
        assert area_min.value == 100
        assert area_max is not None
        assert area_max.value == 120
    
    def test_extract_area_single(self, recognizer):
        """测试单一面积提取"""
        area_min, area_max = recognizer.extract_area("90平米左右")
        assert area_min is not None
        assert area_min.value == 90
    
    def test_extract_price_wan(self, recognizer):
        """测试万元价格提取"""
        price_min, price_max = recognizer.extract_price("预算300-500万")
        assert price_min is not None
        assert price_min.value == 3000000
        assert price_max is not None
        assert price_max.value == 5000000
    
    def test_extract_price_budget(self, recognizer):
        """测试预算价格提取"""
        price_min, price_max = recognizer.extract_price("预算200万以内")
        assert price_min is not None
        assert price_max is not None
        assert price_max.value == 2000000
    
    def test_extract_orientation(self, recognizer):
        """测试朝向提取"""
        result = recognizer.extract_orientation("朝南的房子")
        assert result is not None
        assert "南" in result.value
    
    def test_extract_decoration(self, recognizer):
        """测试装修提取"""
        result = recognizer.extract_decoration("精装修")
        assert result is not None
        assert result.value == "精装"
    
    def test_extract_school_district(self, recognizer):
        """测试学区提取"""
        is_school, is_subway, _ = recognizer.extract_special_requirements("学区房")
        assert is_school is not None
        assert is_school.value == True
    
    def test_extract_near_subway(self, recognizer):
        """测试地铁提取"""
        is_school, is_subway, _ = recognizer.extract_special_requirements("近地铁")
        assert is_subway is not None
        assert is_subway.value == True
    
    def test_parse_full_query(self, recognizer):
        """测试完整查询解析"""
        result = recognizer.parse("上海浦东新区3室2厅100-120平米预算500万的学区房")
        
        assert result.city is not None
        assert result.city.value == "上海"
        assert result.district is not None
        assert "浦东" in result.district.value
        assert result.room_count.value == 3
        assert result.hall_count.value == 2
        assert result.area_min.value == 100
        assert result.area_max.value == 120
        assert result.price_max.value == 5000000
        assert result.is_school_district is not None
        assert result.is_school_district.value == True
    
    def test_parse_fuzzy_query(self, recognizer):
        """测试模糊查询解析"""
        result = recognizer.parse("北京两居室，预算有限，最好有地铁")
        
        assert result.city is not None
        assert result.city.value == "北京"
        assert result.room_count is not None
        assert result.room_count.value == 2
        assert result.is_near_subway is not None
        assert result.is_near_subway.value == True
        assert result.price_max is None


class TestParseNaturalLanguage:
    """便捷函数测试"""
    
    def test_basic_parsing(self):
        """测试基本解析"""
        result = parse_natural_language("深圳南山区3室的房子")
        assert result.city is not None
        assert result.city.value == "深圳"
        assert result.room_count is not None


class TestExtractedEntity:
    """实体类测试"""
    
    def test_entity_creation(self):
        """测试实体创建"""
        entity = ExtractedEntity(value="上海", confidence=0.95, source="explicit")
        assert entity.value == "上海"
        assert entity.confidence == 0.95
        assert entity.source == "explicit"


class TestParsedRequirement:
    """解析结果类测试"""
    
    def test_missing_fields(self):
        """测试缺失字段检测"""
        result = ParsedRequirement(raw_query="测试查询")
        result.city = None
        result.room_count = None
        
        assert "city" in result.missing_fields
        assert "room_count" in result.missing_fields


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
