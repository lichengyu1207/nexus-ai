# -*- coding: utf-8 -*-
"""
扣子数据接收系统测试
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from uuid import uuid4
import json

from backend.services.kouzi.config import KouziConfig, get_kouzi_config
from backend.services.kouzi.models import (
    KouziInfoStream, KouziCrawlerData, KouziWebhook,
    ReceiveResult, TransformResult
)


class TestKouziConfig:
    def test_default_config(self):
        config = KouziConfig()
        assert config.max_retry_count == 3
        assert config.batch_size == 100
        assert config.enable_auto_transform == True
    
    def test_valid_source_types(self):
        config = KouziConfig()
        assert config.is_valid_source_type("property_listing") == True
        assert config.is_valid_source_type("market_data") == True
        assert config.is_valid_source_type("invalid_type") == False
    
    def test_valid_crawler_types(self):
        config = KouziConfig()
        assert config.is_valid_crawler_type("property_crawler") == True
        assert config.is_valid_crawler_type("market_crawler") == True
        assert config.is_valid_crawler_type("invalid_crawler") == False
    
    def test_config_to_dict(self):
        config = KouziConfig()
        d = config.to_dict()
        assert "max_retry_count" in d
        assert "supported_source_types" in d


class TestKouziModels:
    def test_info_stream_creation(self):
        stream = KouziInfoStream(
            stream_id="test_stream_001",
            source_type="property_listing",
            source_name="test_source",
            raw_content={"title": "测试房产"}
        )
        
        assert stream.stream_id == "test_stream_001"
        assert stream.source_type == "property_listing"
        assert stream.status == "pending"
    
    def test_info_stream_to_dict(self):
        stream = KouziInfoStream(
            stream_id="test_stream_002",
            source_type="market_data",
            source_name="test_source"
        )
        
        d = stream.to_dict()
        assert d["stream_id"] == "test_stream_002"
        assert d["source_type"] == "market_data"
    
    def test_crawler_data_creation(self):
        crawler = KouziCrawlerData(
            crawler_id="crawler_001",
            crawler_type="property_crawler",
            target_url="https://example.com/property/123",
            raw_data={"html": "<html>...</html>"}
        )
        
        assert crawler.crawler_id == "crawler_001"
        assert crawler.crawl_status == "pending"
    
    def test_crawler_data_to_dict(self):
        crawler = KouziCrawlerData(
            crawler_id="crawler_002",
            crawler_type="market_crawler",
            target_url="https://example.com/market"
        )
        
        d = crawler.to_dict()
        assert d["crawler_id"] == "crawler_002"
        assert d["crawler_type"] == "market_crawler"
    
    def test_webhook_creation(self):
        webhook = KouziWebhook(
            webhook_id="wh_001",
            webhook_name="测试Webhook",
            webhook_type="property_stream",
            endpoint_url="/api/kouzi/webhook/property"
        )
        
        assert webhook.webhook_id == "wh_001"
        assert webhook.is_active == True
    
    def test_receive_result_success(self):
        result = ReceiveResult(
            success=True,
            stream_id="stream_001",
            message="Success"
        )
        
        assert result.success == True
        d = result.to_dict()
        assert d["success"] == True
    
    def test_receive_result_failure(self):
        result = ReceiveResult(
            success=False,
            message="Failed",
            errors=["Error 1", "Error 2"]
        )
        
        assert result.success == False
        assert len(result.errors) == 2
    
    def test_transform_result(self):
        result = TransformResult(
            success=True,
            source_id="src_001",
            target_id="tgt_001",
            target_table="pssq_properties",
            transform_type="property"
        )
        
        assert result.success == True
        d = result.to_dict()
        assert d["target_table"] == "pssq_properties"


class TestDataTransformer:
    def test_field_mapping(self):
        from backend.services.kouzi.transformer import DataTransformer
        
        transformer = DataTransformer()
        
        source = {
            "小区名称": "阳光花园",
            "城市": "长沙",
            "面积": "120平米",
            "价格": "150万"
        }
        
        mapped = transformer._map_fields(source, transformer.property_mapping)
        
        assert mapped.get("property_name") == "阳光花园"
        assert mapped.get("city") == "长沙"
    
    def test_area_parsing(self):
        from backend.services.kouzi.transformer import DataTransformer
        
        transformer = DataTransformer()
        
        assert transformer._parse_area("120平米") == 120.0
        assert transformer._parse_area("89.5平方米") == 89.5
        assert transformer._parse_area("100") == 100.0
    
    def test_price_parsing(self):
        from backend.services.kouzi.transformer import DataTransformer
        
        transformer = DataTransformer()
        
        assert transformer._parse_price("150万") == 150.0
        assert transformer._parse_price("89.5万元") == 89.5
        assert transformer._parse_price("100") == 100.0
    
    def test_year_parsing(self):
        from backend.services.kouzi.transformer import DataTransformer
        
        transformer = DataTransformer()
        
        assert transformer._parse_year("2020年") == 2020
        assert transformer._parse_year("建成于2015") == 2015
        assert transformer._parse_year("2018") == 2018


if __name__ == "__main__":
    print("=" * 60)
    print("Running Kouzi Data Reception Tests")
    print("=" * 60)
    
    test_classes = [
        TestKouziConfig,
        TestKouziModels,
        TestDataTransformer
    ]
    
    total_tests = 0
    passed_tests = 0
    
    for test_class in test_classes:
        print(f"\n[{test_class.__name__}]")
        instance = test_class()
        
        for method_name in dir(instance):
            if method_name.startswith("test_"):
                total_tests += 1
                try:
                    getattr(instance, method_name)()
                    print(f"  [OK] {method_name}")
                    passed_tests += 1
                except Exception as e:
                    print(f"  [FAIL] {method_name}: {e}")
    
    print("\n" + "=" * 60)
    print(f"Results: {passed_tests}/{total_tests} tests passed")
    print("=" * 60)
