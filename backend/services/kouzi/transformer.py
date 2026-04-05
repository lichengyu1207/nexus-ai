# -*- coding: utf-8 -*-
"""
扣子数据转化模块
将扣子数据转化为Pssq数据库格式
"""
import asyncio
import asyncpg
import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

from .config import KouziConfig, get_kouzi_config
from .models import (
    KouziInfoStream, PssqProperty, PssqMarketData,
    TransformResult, KouziTransformLog
)


DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:147258%40Zxcvbnm@localhost:5432/fangdu")


class DataTransformer:
    def __init__(self, config: Optional[KouziConfig] = None):
        self.config = config or get_kouzi_config()
        self._pool = None
        
        self.property_mapping = {
            "title": "property_name",
            "name": "property_name",
            "小区名称": "property_name",
            "楼盘名称": "property_name",
            "type": "property_type",
            "物业类型": "property_type",
            "address": "address",
            "地址": "address",
            "位置": "address",
            "city": "city",
            "城市": "city",
            "district": "district",
            "区域": "district",
            "区县": "district",
            "area": "area_size",
            "面积": "area_size",
            "建筑面积": "area_size",
            "price": "price",
            "总价": "price",
            "售价": "price",
            "unit_price": "price_unit",
            "单价": "price_unit",
            "year": "build_year",
            "建筑年代": "build_year",
            "建成年代": "build_year",
            "floor": "floor_info",
            "楼层": "floor_info",
            "orientation": "orientation",
            "朝向": "orientation",
            "装修": "decoration",
            "装修情况": "decoration",
            "产权": "property_rights",
            "产权性质": "property_rights",
            "url": "source_url",
            "链接": "source_url",
            "图片": "images",
            "images": "images"
        }
        
        self.market_mapping = {
            "区域": "region",
            "region": "region",
            "均价": "avg_price",
            "avg_price": "avg_price",
            "环比": "price_change_rate",
            "price_change_rate": "price_change_rate",
            "成交量": "transaction_count",
            "transaction_count": "transaction_count",
            "挂牌量": "listing_count",
            "listing_count": "listing_count",
            "月份": "data_month",
            "年份": "data_year"
        }
    
    async def _get_pool(self):
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://"),
                min_size=5,
                max_size=20
            )
        return self._pool
    
    async def transform_to_property(
        self,
        stream: KouziInfoStream,
        mapping: Optional[Dict] = None
    ) -> TransformResult:
        mapping = mapping or self.property_mapping
        raw_data = stream.raw_content
        
        try:
            property_data = self._map_fields(raw_data, mapping)
            
            if self.config.enable_data_validation:
                errors = self._validate_property(property_data)
                if errors:
                    return TransformResult(
                        success=False,
                        source_id=str(stream.id),
                        transform_type="property",
                        message="Validation failed",
                        errors=errors
                    )
            
            property_data["source_platform"] = stream.source_name
            property_data["source_id"] = stream.stream_id
            property_data["kouzi_stream_id"] = stream.id
            property_data["raw_data"] = raw_data
            
            if "images" in property_data and isinstance(property_data["images"], str):
                property_data["images"] = [property_data["images"]]
            
            property_obj = PssqProperty(**{
                k: v for k, v in property_data.items()
                if hasattr(PssqProperty, k)
            })
            
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                row = await conn.fetchrow("""
                    INSERT INTO pssq_properties 
                    (property_id, property_name, property_type, address, city, district,
                     area_size, price, price_unit, build_year, floor_info, orientation,
                     decoration, property_rights, source_platform, source_url, source_id,
                     raw_data, images, contact_info, status, kouzi_stream_id)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, 
                            $15, $16, $17, $18, $19, $20, $21, $22)
                    RETURNING id
                """, property_obj.property_id or str(uuid4()),
                    property_obj.property_name, property_obj.property_type,
                    property_obj.address, property_obj.city, property_obj.district,
                    property_obj.area_size, property_obj.price, property_obj.price_unit,
                    property_obj.build_year, property_obj.floor_info, property_obj.orientation,
                    property_obj.decoration, property_obj.property_rights,
                    property_obj.source_platform, property_obj.source_url, property_obj.source_id,
                    json.dumps(property_obj.raw_data), json.dumps(property_obj.images),
                    json.dumps(property_obj.contact_info), property_obj.status,
                    property_obj.kouzi_stream_id)
                
                await self._log_transform(
                    source_table="kouzi_info_streams",
                    source_id=stream.id,
                    target_table="pssq_properties",
                    target_id=row["id"],
                    transform_type="property",
                    source_data=raw_data,
                    transformed_data=property_data
                )
                
                return TransformResult(
                    success=True,
                    source_id=str(stream.id),
                    target_id=str(row["id"]),
                    target_table="pssq_properties",
                    transform_type="property",
                    message="Property transformed successfully"
                )
        except Exception as e:
            return TransformResult(
                success=False,
                source_id=str(stream.id),
                transform_type="property",
                message=f"Transform failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def transform_to_market_data(
        self,
        stream: KouziInfoStream,
        mapping: Optional[Dict] = None
    ) -> TransformResult:
        mapping = mapping or self.market_mapping
        raw_data = stream.raw_content
        
        try:
            market_data = self._map_fields(raw_data, mapping)
            
            market_data["data_type"] = stream.source_type
            market_data["source"] = stream.source_name
            market_data["kouzi_stream_id"] = stream.id
            market_data["raw_data"] = raw_data
            
            market_obj = PssqMarketData(**{
                k: v for k, v in market_data.items()
                if hasattr(PssqMarketData, k)
            })
            
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                row = await conn.fetchrow("""
                    INSERT INTO pssq_market_data 
                    (data_type, region, region_code, avg_price, price_change_rate,
                     transaction_count, listing_count, data_date, data_month, data_year,
                     source, raw_data, kouzi_stream_id)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                    RETURNING id
                """, market_obj.data_type, market_obj.region, market_obj.region_code,
                    market_obj.avg_price, market_obj.price_change_rate,
                    market_obj.transaction_count, market_obj.listing_count,
                    market_obj.data_date, market_obj.data_month, market_obj.data_year,
                    market_obj.source, json.dumps(market_obj.raw_data),
                    market_obj.kouzi_stream_id)
                
                await self._log_transform(
                    source_table="kouzi_info_streams",
                    source_id=stream.id,
                    target_table="pssq_market_data",
                    target_id=row["id"],
                    transform_type="market_data",
                    source_data=raw_data,
                    transformed_data=market_data
                )
                
                return TransformResult(
                    success=True,
                    source_id=str(stream.id),
                    target_id=str(row["id"]),
                    target_table="pssq_market_data",
                    transform_type="market_data",
                    message="Market data transformed successfully"
                )
        except Exception as e:
            return TransformResult(
                success=False,
                source_id=str(stream.id),
                transform_type="market_data",
                message=f"Transform failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def auto_transform(self, stream: KouziInfoStream) -> TransformResult:
        source_type = stream.source_type
        
        if source_type in ["property_listing", "crawler_result"]:
            if "价格" in stream.raw_content or "price" in stream.raw_content:
                return await self.transform_to_property(stream)
        elif source_type in ["market_data", "statistics"]:
            return await self.transform_to_market_data(stream)
        
        return TransformResult(
            success=False,
            source_id=str(stream.id),
            transform_type="auto",
            message=f"Unknown source type: {source_type}",
            errors=["No matching transform rule"]
        )
    
    async def batch_transform(
        self,
        streams: List[KouziInfoStream]
    ) -> List[TransformResult]:
        results = []
        
        for stream in streams:
            result = await self.auto_transform(stream)
            results.append(result)
        
        return results
    
    def _map_fields(self, source: Dict, mapping: Dict) -> Dict:
        result = {}
        
        for source_key, target_key in mapping.items():
            if source_key in source:
                value = source[source_key]
                
                if target_key == "area_size" and isinstance(value, str):
                    value = self._parse_area(value)
                elif target_key == "price" and isinstance(value, str):
                    value = self._parse_price(value)
                elif target_key == "build_year" and isinstance(value, str):
                    value = self._parse_year(value)
                
                result[target_key] = value
        
        return result
    
    def _parse_area(self, value: str) -> Optional[float]:
        try:
            import re
            match = re.search(r'[\d.]+', str(value))
            if match:
                return float(match.group())
        except:
            pass
        return None
    
    def _parse_price(self, value: str) -> Optional[float]:
        try:
            import re
            match = re.search(r'[\d.]+', str(value))
            if match:
                return float(match.group())
        except:
            pass
        return None
    
    def _parse_year(self, value: str) -> Optional[int]:
        try:
            import re
            match = re.search(r'\d{4}', str(value))
            if match:
                return int(match.group())
        except:
            pass
        return None
    
    def _validate_property(self, data: Dict) -> List[str]:
        errors = []
        
        for field in self.config.required_property_fields:
            if field not in data or not data[field]:
                errors.append(f"Missing required field: {field}")
        
        return errors
    
    async def _log_transform(
        self,
        source_table: str,
        source_id: UUID,
        target_table: str,
        target_id: UUID,
        transform_type: str,
        source_data: Dict,
        transformed_data: Dict
    ):
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO kouzi_transform_logs 
                    (source_table, source_id, target_table, target_id, transform_type,
                     transform_status, source_data, transformed_data, completed_at)
                    VALUES ($1, $2, $3, $4, $5, 'completed', $6, $7, NOW())
                """, source_table, source_id, target_table, target_id, transform_type,
                    json.dumps(source_data), json.dumps(transformed_data))
        except Exception:
            pass
    
    async def get_transform_statistics(self) -> Dict:
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(*) FILTER (WHERE transform_status = 'completed') as completed,
                        COUNT(*) FILTER (WHERE transform_status = 'failed') as failed
                    FROM kouzi_transform_logs
                """)
                
                by_type = await conn.fetch("""
                    SELECT transform_type, COUNT(*) as count
                    FROM kouzi_transform_logs
                    WHERE transform_status = 'completed'
                    GROUP BY transform_type
                """)
                
                return {
                    "total": dict(stats),
                    "by_type": {row["transform_type"]: row["count"] for row in by_type}
                }
        except Exception:
            return {"total": {}, "by_type": {}}
    
    async def close(self):
        if self._pool:
            await self._pool.close()
            self._pool = None
