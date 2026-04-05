# -*- coding: utf-8 -*-
"""
扣子数据接收服务主模块
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
    KouziInfoStream, KouziCrawlerData, KouziWebhook,
    ReceiveResult, TransformResult
)
from .receiver import KouziReceiver
from .transformer import DataTransformer
from .crawler_handler import CrawlerHandler


DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:147258%40Zxcvbnm@localhost:5432/fangdu")


class KouziService:
    def __init__(self, config: Optional[KouziConfig] = None):
        self.config = config or get_kouzi_config()
        self.receiver = KouziReceiver(self.config)
        self.transformer = DataTransformer(self.config)
        self.crawler_handler = CrawlerHandler(self.config)
        self._pool = None
    
    async def _get_pool(self):
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://"),
                min_size=5,
                max_size=20
            )
        return self._pool
    
    async def receive_and_transform(
        self,
        source_type: str,
        source_name: str,
        content: Dict,
        content_type: str = "json",
        metadata: Optional[Dict] = None,
        auto_transform: bool = True
    ) -> Dict:
        receive_result = await self.receiver.receive_stream(
            source_type=source_type,
            source_name=source_name,
            content=content,
            content_type=content_type,
            metadata=metadata
        )
        
        if not receive_result.success:
            return {
                "receive": receive_result.to_dict(),
                "transform": None
            }
        
        transform_result = None
        if auto_transform and self.config.enable_auto_transform:
            stream = await self.receiver.get_stream(receive_result.stream_id)
            if stream:
                transform_result = await self.transformer.auto_transform(stream)
        
        return {
            "receive": receive_result.to_dict(),
            "transform": transform_result.to_dict() if transform_result else None
        }
    
    async def receive_crawler_and_transform(
        self,
        crawler_id: str,
        crawler_type: str,
        target_url: str,
        raw_data: Dict,
        parsed_data: Optional[Dict] = None,
        images: Optional[List[Dict]] = None,
        documents: Optional[List[Dict]] = None,
        metadata: Optional[Dict] = None,
        auto_transform: bool = True
    ) -> Dict:
        receive_result = await self.crawler_handler.handle_crawler_result(
            crawler_id=crawler_id,
            crawler_type=crawler_type,
            target_url=target_url,
            raw_data=raw_data,
            parsed_data=parsed_data,
            images=images,
            documents=documents,
            metadata=metadata
        )
        
        if not receive_result.success:
            return {
                "receive": receive_result.to_dict(),
                "transform": None
            }
        
        transform_result = None
        if auto_transform and self.config.enable_auto_transform and parsed_data:
            stream = KouziInfoStream(
                stream_id=crawler_id,
                source_type=crawler_type,
                source_name=target_url,
                raw_content=parsed_data
            )
            transform_result = await self.transformer.auto_transform(stream)
        
        return {
            "receive": receive_result.to_dict(),
            "transform": transform_result.to_dict() if transform_result else None
        }
    
    async def process_webhook(
        self,
        webhook_type: str,
        payload: Dict,
        signature: Optional[str] = None
    ) -> Dict:
        webhook = await self._get_webhook_by_type(webhook_type)
        
        if not webhook:
            return {
                "success": False,
                "message": f"Webhook type not found: {webhook_type}"
            }
        
        if not webhook.is_active:
            return {
                "success": False,
                "message": f"Webhook is inactive: {webhook_type}"
            }
        
        if signature and webhook.secret_key:
            if not self.receiver.verify_webhook_signature(
                json.dumps(payload).encode(),
                signature,
                webhook.secret_key
            ):
                return {
                    "success": False,
                    "message": "Invalid webhook signature"
                }
        
        await self._update_webhook_trigger(webhook.webhook_id)
        
        if webhook_type == "property_stream":
            return await self.receive_and_transform(
                source_type="webhook_event",
                source_name=f"webhook_{webhook.webhook_id}",
                content=payload
            )
        elif webhook_type == "crawler_callback":
            return await self.receive_crawler_and_transform(
                crawler_id=payload.get("crawler_id", str(uuid4())),
                crawler_type=payload.get("crawler_type", "property_crawler"),
                target_url=payload.get("target_url", ""),
                raw_data=payload.get("raw_data", {}),
                parsed_data=payload.get("parsed_data"),
                images=payload.get("images"),
                documents=payload.get("documents"),
                metadata=payload.get("metadata")
            )
        elif webhook_type == "market_data":
            return await self.receive_and_transform(
                source_type="market_data",
                source_name=f"webhook_{webhook.webhook_id}",
                content=payload
            )
        
        return {
            "success": False,
            "message": f"Unknown webhook type: {webhook_type}"
        }
    
    async def _get_webhook_by_type(self, webhook_type: str) -> Optional[KouziWebhook]:
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT * FROM kouzi_webhooks 
                    WHERE webhook_type = $1 AND is_active = TRUE
                    LIMIT 1
                """, webhook_type)
                
                if row:
                    return KouziWebhook.from_db_row(dict(row))
                return None
        except Exception:
            return None
    
    async def _update_webhook_trigger(self, webhook_id: str):
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                await conn.execute("""
                    UPDATE kouzi_webhooks 
                    SET last_triggered = NOW(), trigger_count = trigger_count + 1
                    WHERE webhook_id = $1
                """, webhook_id)
        except Exception:
            pass
    
    async def get_statistics(self) -> Dict:
        receiver_stats = await self.receiver.get_statistics()
        transform_stats = await self.transformer.get_transform_statistics()
        crawler_stats = await self.crawler_handler.get_crawler_statistics()
        
        return {
            "streams": receiver_stats.get("streams", {}),
            "crawlers": receiver_stats.get("crawlers", {}),
            "transforms": transform_stats,
            "crawler_tasks": crawler_stats
        }
    
    async def health_check(self) -> Dict:
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            
            return {
                "status": "healthy",
                "database": "connected",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def close(self):
        await self.receiver.close()
        await self.transformer.close()
        await self.crawler_handler.close()
        
        if self._pool:
            await self._pool.close()
            self._pool = None
