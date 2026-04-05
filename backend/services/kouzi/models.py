# -*- coding: utf-8 -*-
"""
扣子数据接收模型定义
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4
import json


@dataclass
class KouziInfoStream:
    id: UUID = field(default_factory=uuid4)
    stream_id: str = ""
    source_type: str = ""
    source_name: str = ""
    content_type: str = "text"
    raw_content: Dict = field(default_factory=dict)
    processed_content: Dict = field(default_factory=dict)
    metadata: Dict = field(default_factory=dict)
    status: str = "pending"
    priority: int = 5
    received_at: datetime = field(default_factory=datetime.now)
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": str(self.id),
            "stream_id": self.stream_id,
            "source_type": self.source_type,
            "source_name": self.source_name,
            "content_type": self.content_type,
            "raw_content": self.raw_content,
            "processed_content": self.processed_content,
            "metadata": self.metadata,
            "status": self.status,
            "priority": self.priority,
            "received_at": self.received_at.isoformat() if self.received_at else None,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "error_message": self.error_message
        }
    
    @classmethod
    def from_db_row(cls, row: Dict) -> 'KouziInfoStream':
        return cls(
            id=row["id"],
            stream_id=row.get("stream_id", ""),
            source_type=row.get("source_type", ""),
            source_name=row.get("source_name", ""),
            content_type=row.get("content_type", "text"),
            raw_content=row.get("raw_content", {}),
            processed_content=row.get("processed_content", {}),
            metadata=row.get("metadata", {}),
            status=row.get("status", "pending"),
            priority=row.get("priority", 5),
            received_at=row.get("received_at"),
            processed_at=row.get("processed_at"),
            error_message=row.get("error_message")
        )


@dataclass
class KouziCrawlerData:
    id: UUID = field(default_factory=uuid4)
    crawler_id: str = ""
    crawler_type: str = ""
    target_url: str = ""
    crawl_status: str = "pending"
    raw_data: Dict = field(default_factory=dict)
    parsed_data: Dict = field(default_factory=dict)
    images: List[Dict] = field(default_factory=list)
    documents: List[Dict] = field(default_factory=list)
    crawl_metadata: Dict = field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    error_message: Optional[str] = None
    retry_count: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "id": str(self.id),
            "crawler_id": self.crawler_id,
            "crawler_type": self.crawler_type,
            "target_url": self.target_url,
            "crawl_status": self.crawl_status,
            "raw_data": self.raw_data,
            "parsed_data": self.parsed_data,
            "images": self.images,
            "documents": self.documents,
            "crawl_metadata": self.crawl_metadata,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "error_message": self.error_message,
            "retry_count": self.retry_count
        }
    
    @classmethod
    def from_db_row(cls, row: Dict) -> 'KouziCrawlerData':
        return cls(
            id=row["id"],
            crawler_id=row.get("crawler_id", ""),
            crawler_type=row.get("crawler_type", ""),
            target_url=row.get("target_url", ""),
            crawl_status=row.get("crawl_status", "pending"),
            raw_data=row.get("raw_data", {}),
            parsed_data=row.get("parsed_data", {}),
            images=row.get("images", []),
            documents=row.get("documents", []),
            crawl_metadata=row.get("crawl_metadata", {}),
            started_at=row.get("started_at"),
            completed_at=row.get("completed_at"),
            created_at=row.get("created_at"),
            error_message=row.get("error_message"),
            retry_count=row.get("retry_count", 0)
        )


@dataclass
class KouziTransformLog:
    id: UUID = field(default_factory=uuid4)
    source_table: str = ""
    source_id: UUID = field(default_factory=uuid4)
    target_table: str = ""
    target_id: Optional[UUID] = None
    transform_type: str = ""
    transform_status: str = "pending"
    source_data: Dict = field(default_factory=dict)
    transformed_data: Dict = field(default_factory=dict)
    mapping_rules: Dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": str(self.id),
            "source_table": self.source_table,
            "source_id": str(self.source_id),
            "target_table": self.target_table,
            "target_id": str(self.target_id) if self.target_id else None,
            "transform_type": self.transform_type,
            "transform_status": self.transform_status,
            "source_data": self.source_data,
            "transformed_data": self.transformed_data,
            "mapping_rules": self.mapping_rules,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message
        }


@dataclass
class PssqProperty:
    id: UUID = field(default_factory=uuid4)
    property_id: str = ""
    property_name: str = ""
    property_type: str = ""
    address: str = ""
    city: str = ""
    district: str = ""
    area_size: Optional[float] = None
    price: Optional[float] = None
    price_unit: str = ""
    build_year: Optional[int] = None
    floor_info: str = ""
    orientation: str = ""
    decoration: str = ""
    property_rights: str = ""
    source_platform: str = ""
    source_url: str = ""
    source_id: str = ""
    raw_data: Dict = field(default_factory=dict)
    images: List[str] = field(default_factory=list)
    contact_info: Dict = field(default_factory=dict)
    status: str = "active"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    kouzi_stream_id: Optional[UUID] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": str(self.id),
            "property_id": self.property_id,
            "property_name": self.property_name,
            "property_type": self.property_type,
            "address": self.address,
            "city": self.city,
            "district": self.district,
            "area_size": self.area_size,
            "price": self.price,
            "price_unit": self.price_unit,
            "build_year": self.build_year,
            "floor_info": self.floor_info,
            "orientation": self.orientation,
            "decoration": self.decoration,
            "property_rights": self.property_rights,
            "source_platform": self.source_platform,
            "source_url": self.source_url,
            "source_id": self.source_id,
            "raw_data": self.raw_data,
            "images": self.images,
            "contact_info": self.contact_info,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "kouzi_stream_id": str(self.kouzi_stream_id) if self.kouzi_stream_id else None
        }
    
    @classmethod
    def from_db_row(cls, row: Dict) -> 'PssqProperty':
        return cls(
            id=row["id"],
            property_id=row.get("property_id", ""),
            property_name=row.get("property_name", ""),
            property_type=row.get("property_type", ""),
            address=row.get("address", ""),
            city=row.get("city", ""),
            district=row.get("district", ""),
            area_size=row.get("area_size"),
            price=row.get("price"),
            price_unit=row.get("price_unit", ""),
            build_year=row.get("build_year"),
            floor_info=row.get("floor_info", ""),
            orientation=row.get("orientation", ""),
            decoration=row.get("decoration", ""),
            property_rights=row.get("property_rights", ""),
            source_platform=row.get("source_platform", ""),
            source_url=row.get("source_url", ""),
            source_id=row.get("source_id", ""),
            raw_data=row.get("raw_data", {}),
            images=row.get("images", []),
            contact_info=row.get("contact_info", {}),
            status=row.get("status", "active"),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
            kouzi_stream_id=row.get("kouzi_stream_id")
        )


@dataclass
class PssqMarketData:
    id: UUID = field(default_factory=uuid4)
    data_type: str = ""
    region: str = ""
    region_code: str = ""
    avg_price: Optional[float] = None
    price_change_rate: Optional[float] = None
    transaction_count: Optional[int] = None
    listing_count: Optional[int] = None
    data_date: Optional[datetime] = None
    data_month: str = ""
    data_year: Optional[int] = None
    source: str = ""
    raw_data: Dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    kouzi_stream_id: Optional[UUID] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": str(self.id),
            "data_type": self.data_type,
            "region": self.region,
            "region_code": self.region_code,
            "avg_price": self.avg_price,
            "price_change_rate": self.price_change_rate,
            "transaction_count": self.transaction_count,
            "listing_count": self.listing_count,
            "data_date": self.data_date.isoformat() if self.data_date else None,
            "data_month": self.data_month,
            "data_year": self.data_year,
            "source": self.source,
            "raw_data": self.raw_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "kouzi_stream_id": str(self.kouzi_stream_id) if self.kouzi_stream_id else None
        }


@dataclass
class KouziWebhook:
    id: UUID = field(default_factory=uuid4)
    webhook_id: str = ""
    webhook_name: str = ""
    webhook_type: str = ""
    endpoint_url: str = ""
    secret_key: str = ""
    is_active: bool = True
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "id": str(self.id),
            "webhook_id": self.webhook_id,
            "webhook_name": self.webhook_name,
            "webhook_type": self.webhook_type,
            "endpoint_url": self.endpoint_url,
            "secret_key": "***" if self.secret_key else "",
            "is_active": self.is_active,
            "last_triggered": self.last_triggered.isoformat() if self.last_triggered else None,
            "trigger_count": self.trigger_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_db_row(cls, row: Dict) -> 'KouziWebhook':
        return cls(
            id=row["id"],
            webhook_id=row.get("webhook_id", ""),
            webhook_name=row.get("webhook_name", ""),
            webhook_type=row.get("webhook_type", ""),
            endpoint_url=row.get("endpoint_url", ""),
            secret_key=row.get("secret_key", ""),
            is_active=row.get("is_active", True),
            last_triggered=row.get("last_triggered"),
            trigger_count=row.get("trigger_count", 0),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at")
        )


@dataclass
class ReceiveResult:
    success: bool
    stream_id: Optional[str] = None
    message: str = ""
    data: Dict = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "stream_id": self.stream_id,
            "message": self.message,
            "data": self.data,
            "errors": self.errors
        }


@dataclass
class TransformResult:
    success: bool
    source_id: str = ""
    target_id: Optional[str] = None
    target_table: str = ""
    transform_type: str = ""
    message: str = ""
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "target_table": self.target_table,
            "transform_type": self.transform_type,
            "message": self.message,
            "errors": self.errors
        }
