# -*- coding: utf-8 -*-
"""
扣子爬虫数据处理模块
"""
import asyncio
import asyncpg
import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

from .config import KouziConfig, get_kouzi_config
from .models import KouziCrawlerData, ReceiveResult


DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:147258%40Zxcvbnm@localhost:5432/fangdu")


class CrawlerHandler:
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
    
    async def handle_crawler_result(
        self,
        crawler_id: str,
        crawler_type: str,
        target_url: str,
        raw_data: Dict,
        parsed_data: Optional[Dict] = None,
        images: Optional[List[Dict]] = None,
        documents: Optional[List[Dict]] = None,
        metadata: Optional[Dict] = None,
        status: str = "completed",
        error_message: Optional[str] = None
    ) -> ReceiveResult:
        if not self.config.is_valid_crawler_type(crawler_type):
            return ReceiveResult(
                success=False,
                message=f"Invalid crawler type: {crawler_type}"
            )
        
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                row = await conn.fetchrow("""
                    INSERT INTO kouzi_crawler_data 
                    (crawler_id, crawler_type, target_url, crawl_status, raw_data, 
                     parsed_data, images, documents, crawl_metadata, 
                     started_at, completed_at, error_message)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW(), NOW(), $10)
                    RETURNING id, crawler_id
                """, crawler_id, crawler_type, target_url, status,
                    json.dumps(raw_data), json.dumps(parsed_data or {}),
                    json.dumps(images or []), json.dumps(documents or []),
                    json.dumps(metadata or {}), error_message)
                
                return ReceiveResult(
                    success=True,
                    stream_id=row["crawler_id"],
                    message="Crawler data received successfully",
                    data={"id": str(row["id"])}
                )
        except Exception as e:
            return ReceiveResult(
                success=False,
                message=f"Failed to handle crawler result: {str(e)}",
                errors=[str(e)]
            )
    
    async def get_crawler_data(
        self,
        crawler_id: str
    ) -> Optional[KouziCrawlerData]:
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT * FROM kouzi_crawler_data WHERE crawler_id = $1
                """, crawler_id)
                
                if row:
                    return KouziCrawlerData.from_db_row(dict(row))
                return None
        except Exception:
            return None
    
    async def get_pending_crawls(self, limit: int = 100) -> List[KouziCrawlerData]:
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT * FROM kouzi_crawler_data 
                    WHERE crawl_status = 'pending'
                    ORDER BY created_at ASC
                    LIMIT $1
                """, limit)
                
                return [KouziCrawlerData.from_db_row(dict(row)) for row in rows]
        except Exception:
            return []
    
    async def update_crawl_status(
        self,
        crawler_id: str,
        status: str,
        parsed_data: Optional[Dict] = None,
        images: Optional[List[Dict]] = None,
        documents: Optional[List[Dict]] = None,
        error_message: Optional[str] = None
    ) -> bool:
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                if status == "completed":
                    await conn.execute("""
                        UPDATE kouzi_crawler_data 
                        SET crawl_status = $1, parsed_data = $2, images = $3, 
                            documents = $4, completed_at = NOW()
                        WHERE crawler_id = $5
                    """, status, json.dumps(parsed_data or {}),
                        json.dumps(images or []), json.dumps(documents or []),
                        crawler_id)
                elif status == "failed":
                    await conn.execute("""
                        UPDATE kouzi_crawler_data 
                        SET crawl_status = $1, error_message = $2, completed_at = NOW()
                        WHERE crawler_id = $3
                    """, status, error_message, crawler_id)
                else:
                    await conn.execute("""
                        UPDATE kouzi_crawler_data 
                        SET crawl_status = $1
                        WHERE crawler_id = $2
                    """, status, crawler_id)
                
                return True
        except Exception:
            return False
    
    async def retry_failed_crawl(self, crawler_id: str) -> bool:
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT retry_count FROM kouzi_crawler_data WHERE crawler_id = $1
                """, crawler_id)
                
                if row and row["retry_count"] < self.config.max_retry_count:
                    await conn.execute("""
                        UPDATE kouzi_crawler_data 
                        SET crawl_status = 'pending', retry_count = retry_count + 1,
                            started_at = NULL, completed_at = NULL, error_message = NULL
                        WHERE crawler_id = $1
                    """, crawler_id)
                    return True
                
                return False
        except Exception:
            return False
    
    async def get_crawler_statistics(self) -> Dict:
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(*) FILTER (WHERE crawl_status = 'pending') as pending,
                        COUNT(*) FILTER (WHERE crawl_status = 'running') as running,
                        COUNT(*) FILTER (WHERE crawl_status = 'completed') as completed,
                        COUNT(*) FILTER (WHERE crawl_status = 'failed') as failed
                    FROM kouzi_crawler_data
                """)
                
                by_type = await conn.fetch("""
                    SELECT crawler_type, COUNT(*) as count
                    FROM kouzi_crawler_data
                    GROUP BY crawler_type
                """)
                
                return {
                    "total": dict(stats),
                    "by_type": {row["crawler_type"]: row["count"] for row in by_type}
                }
        except Exception:
            return {"total": {}, "by_type": {}}
    
    async def create_crawl_task(
        self,
        crawler_type: str,
        target_url: str,
        metadata: Optional[Dict] = None
    ) -> str:
        crawler_id = f"crawl_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid4().hex[:8]}"
        
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO kouzi_crawler_data 
                    (crawler_id, crawler_type, target_url, crawl_status, crawl_metadata)
                    VALUES ($1, $2, $3, 'pending', $4)
                """, crawler_id, crawler_type, target_url, json.dumps(metadata or {}))
            
            return crawler_id
        except Exception:
            return ""
    
    async def close(self):
        if self._pool:
            await self._pool.close()
            self._pool = None
