# -*- coding: utf-8 -*-
"""
扣子数据接收配置模块
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import os


@dataclass
class KouziConfig:
    webhook_secret: str = ""
    max_retry_count: int = 3
    batch_size: int = 100
    stream_timeout_seconds: int = 300
    crawler_timeout_seconds: int = 600
    enable_auto_transform: bool = True
    enable_data_validation: bool = True
    
    pssq_property_fields: List[str] = field(default_factory=lambda: [
        "property_name", "property_type", "address", "city", "district",
        "area_size", "price", "price_unit", "build_year", "floor_info",
        "orientation", "decoration", "property_rights"
    ])
    
    required_property_fields: List[str] = field(default_factory=lambda: [
        "property_name", "address", "city"
    ])
    
    supported_source_types: List[str] = field(default_factory=lambda: [
        "property_listing", "market_data", "crawler_result",
        "webhook_event", "api_push", "file_upload"
    ])
    
    supported_crawler_types: List[str] = field(default_factory=lambda: [
        "property_crawler", "market_crawler", "news_crawler",
        "price_crawler", "transaction_crawler"
    ])
    
    def get_webhook_secret(self) -> str:
        return self.webhook_secret or os.getenv("KOUZI_WEBHOOK_SECRET", "")
    
    def is_valid_source_type(self, source_type: str) -> bool:
        return source_type in self.supported_source_types
    
    def is_valid_crawler_type(self, crawler_type: str) -> bool:
        return crawler_type in self.supported_crawler_types
    
    def to_dict(self) -> Dict:
        return {
            "webhook_secret": "***" if self.webhook_secret else "",
            "max_retry_count": self.max_retry_count,
            "batch_size": self.batch_size,
            "stream_timeout_seconds": self.stream_timeout_seconds,
            "crawler_timeout_seconds": self.crawler_timeout_seconds,
            "enable_auto_transform": self.enable_auto_transform,
            "enable_data_validation": self.enable_data_validation,
            "pssq_property_fields": self.pssq_property_fields,
            "required_property_fields": self.required_property_fields,
            "supported_source_types": self.supported_source_types,
            "supported_crawler_types": self.supported_crawler_types
        }


DEFAULT_CONFIG = KouziConfig()


def get_kouzi_config() -> KouziConfig:
    return DEFAULT_CONFIG
