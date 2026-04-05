# -*- coding: utf-8 -*-
"""
扣子数据接收器模块
"""
import asyncio
import asyncpg
import os
import hashlib
import hmac
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

from .config import KouziConfig, get_kouzi_config
from .models import (
    KouziInfoStream, KouziCrawlerData, KouziWebhook,
    ReceiveResult
)


DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:147258%40Zxcvbnm@localhost:5432/fangdu")


class KouziReceiver:
    def __init__(self, config: Optional[KouziConfig] = None):
        self.config = config or get_kouzi_config()
        self._pool = None
    
    async def _get_pool(self):
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://"),
                min_size=5,
                max_size=20
            )
        return self._pool
    
    async def receive_stream(
        self,
        source_type: str,
        source_name: str,
        content: Dict,
        content_type: str = "json",
        metadata: Optional[Dict] = None,
        priority: int = 5
    ) -> ReceiveResult:
        if not self.config.is_valid_source_type(source_type):
            return ReceiveResult(
                success=False,
                message=f"Invalid source type: {source_type}"
            )
        
        stream_id = self._generate_stream_id(source_type, content)
        
        stream = KouziInfoStream(
            stream_id=stream_id,
            source_type=source_type,
            source_name=source_name,
            content_type=content_type,
            raw_content=content,
            metadata=metadata or {},
            priority=priority
        )
        
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                row = await conn.fetchrow("""
                    INSERT INTO kouzi_info_streams 
                    (stream_id, source_type, source_name, content_type, raw_content, metadata, priority)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    RETURNING id, stream_id
                """, stream.stream_id, stream.source_type, stream.source_name,
                    stream.content_type, json.dumps(stream.raw_content),
                    json.dumps(stream.metadata), stream.priority)
                
                return ReceiveResult(
                    success=True,
                    stream_id=row["stream_id"],
                    message="Stream received successfully",
                    data={"id": str(row["id"])}
                )
        except Exception as e:
            return ReceiveResult(
                success=False,
                stream_id=stream_id,
                message=f"Failed to receive stream: {str(e)}",
                errors=[str(e)]
            )
    
    async def receive_batch(
        self,
        items: List[Dict]
    ) -> List[ReceiveResult]:
        results = []
        
        for item in items:
            result = await self.receive_stream(
                source_type=item.get("source_type", "unknown"),
                source_name=item.get("source_name", ""),
                content=item.get("content", {}),
                content_type=item.get("content_type", "json"),
                metadata=item.get("metadata"),
                priority=item.get("priority", 5)
            )
            results.append(result)
        
        return results
    
    async def receive_crawler_data(
        self,
        crawler_id: str,
        crawler_type: str,
        target_url: str,
        raw_data: Dict,
        parsed_data: Optional[Dict] = None,
        images: Optional[List[Dict]] = None,
        documents: Optional[List[Dict]] = None,
        metadata: Optional[Dict] = None
    ) -> ReceiveResult:
        if not self.config.is_valid_crawler_type(crawler_type):
            return ReceiveResult(
                success=False,
                message=f"Invalid crawler type: {crawler_type}"
            )
        
        crawler_data = KouziCrawlerData(
            crawler_id=crawler_id,
            crawler_type=crawler_type,
            target_url=target_url,
            raw_data=raw_data,
            parsed_data=parsed_data or {},
            images=images or [],
            documents=documents or [],
            crawl_metadata=metadata or {},
            crawl_status="completed"
        )
        
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                row = await conn.fetchrow("""
                    INSERT INTO kouzi_crawler_data 
                    (crawler_id, crawler_type, target_url, raw_data, parsed_data, 
                     images, documents, crawl_metadata, crawl_status, completed_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW())
                    RETURNING id, crawler_id
                """, crawler_data.crawler_id, crawler_data.crawler_type,
                    crawler_data.target_url, json.dumps(crawler_data.raw_data),
                    json.dumps(crawler_data.parsed_data), json.dumps(crawler_data.images),
                    json.dumps(crawler_data.documents), json.dumps(crawler_data.crawl_metadata),
                    crawler_data.crawl_status)
                
                return ReceiveResult(
                    success=True,
                    stream_id=row["crawler_id"],
                    message="Crawler data received successfully",
                    data={"id": str(row["id"])}
                )
        except Exception as e:
            return ReceiveResult(
                success=False,
                message=f"Failed to receive crawler data: {str(e)}",
                errors=[str(e)]
            )
    
    async def get_stream(self, stream_id: str) -> Optional[KouziInfoStream]:
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT * FROM kouzi_info_streams WHERE stream_id = $1
                """, stream_id)
                
                if row:
                    return KouziInfoStream.from_db_row(dict(row))
                return None
        except Exception:
            return None
    
    async def get_pending_streams(self, limit: int = 100) -> List[KouziInfoStream]:
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT * FROM kouzi_info_streams 
                    WHERE status = 'pending'
                    ORDER BY priority DESC, received_at ASC
                    LIMIT $1
                """, limit)
                
                return [KouziInfoStream.from_db_row(dict(row)) for row in rows]
        except Exception:
            return []
    
    async def update_stream_status(
        self,
        stream_id: str,
        status: str,
        processed_content: Optional[Dict] = None,
        error_message: Optional[str] = None
    ) -> bool:
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                if status == "completed":
                    await conn.execute("""
                        UPDATE kouzi_info_streams 
                        SET status = $1, processed_content = $2, processed_at = NOW()
                        WHERE stream_id = $3
                    """, status, json.dumps(processed_content or {}), stream_id)
                elif status == "failed":
                    await conn.execute("""
                        UPDATE kouzi_info_streams 
                        SET status = $1, error_message = $2, processed_at = NOW()
                        WHERE stream_id = $3
                    """, status, error_message, stream_id)
                else:
                    await conn.execute("""
                        UPDATE kouzi_info_streams 
                        SET status = $1
                        WHERE stream_id = $2
                    """, status, stream_id)
                
                return True
        except Exception:
            return False
    
    async def get_statistics(self) -> Dict:
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(*) FILTER (WHERE status = 'pending') as pending,
                        COUNT(*) FILTER (WHERE status = 'processing') as processing,
                        COUNT(*) FILTER (WHERE status = 'completed') as completed,
                        COUNT(*) FILTER (WHERE status = 'failed') as failed
                    FROM kouzi_info_streams
                """)
                
                crawler_stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(*) FILTER (WHERE crawl_status = 'pending') as pending,
                        COUNT(*) FILTER (WHERE crawl_status = 'completed') as completed,
                        COUNT(*) FILTER (WHERE crawl_status = 'failed') as failed
                    FROM kouzi_crawler_data
                """)
                
                return {
                    "streams": dict(stats),
                    "crawlers": dict(crawler_stats)
                }
        except Exception:
            return {"streams": {}, "crawlers": {}}
    
    def _generate_stream_id(self, source_type: str, content: Dict) -> str:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        content_hash = hashlib.md5(
            json.dumps(content, sort_keys=True).encode()
        ).hexdigest()[:8]
        return f"{source_type}_{timestamp}_{content_hash}"
    
    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
        secret: str
    ) -> bool:
        expected = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(f"sha256={expected}", signature)
    
    async def close(self):
        if self._pool:
            await self._pool.close()
            self._pool = None
