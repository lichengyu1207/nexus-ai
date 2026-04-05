"""
数据样本库存储系统
存储原始数据、标注数据、元数据，支持向量检索
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

import asyncpg
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class SampleType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    STRUCTURED = "structured"
    INTERACTION = "interaction"
    AGENT_TRACE = "agent_trace"
    KNOWLEDGE = "knowledge"


class SampleStatus(str, Enum):
    RAW = "raw"
    VALIDATED = "validated"
    ANNOTATED = "annotated"
    ARCHIVED = "archived"
    DELETED = "deleted"


class Sample(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    type: SampleType
    source_agent_id: str
    content: Dict[str, Any]
    embedding_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    quality: float = 0.5
    status: SampleStatus = SampleStatus.RAW
    annotations: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    usage_count: int = 0
    created_at: datetime = Field(default_factory=datetime.now)
    last_used: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class SampleQuery(BaseModel):
    types: Optional[List[SampleType]] = None
    tags: Optional[List[str]] = None
    min_quality: float = 0.0
    max_quality: float = 1.0
    source_agent_id: Optional[str] = None
    status: Optional[SampleStatus] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    limit: int = 100
    offset: int = 0
    order_by: str = "created_at"
    order_desc: bool = True


class VectorStoreInterface:
    async def store_embedding(self, sample_id: str, embedding: List[float]) -> str:
        raise NotImplementedError
    
    async def search_similar(
        self,
        embedding: List[float],
        top_k: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[str, float]]:
        raise NotImplementedError
    
    async def delete_embedding(self, embedding_id: str) -> bool:
        raise NotImplementedError


class MockVectorStore(VectorStoreInterface):
    def __init__(self):
        self.embeddings: Dict[str, List[float]] = {}
        self.sample_to_embedding: Dict[str, str] = {}
    
    async def store_embedding(self, sample_id: str, embedding: List[float]) -> str:
        embedding_id = f"emb_{sample_id}"
        self.embeddings[embedding_id] = embedding
        self.sample_to_embedding[sample_id] = embedding_id
        return embedding_id
    
    async def search_similar(
        self,
        embedding: List[float],
        top_k: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[str, float]]:
        results = []
        for emb_id, emb in self.embeddings.items():
            similarity = self._cosine_similarity(embedding, emb)
            results.append((emb_id, similarity))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
    
    async def delete_embedding(self, embedding_id: str) -> bool:
        if embedding_id in self.embeddings:
            del self.embeddings[embedding_id]
            return True
        return False
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        if len(a) != len(b):
            return 0.0
        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot_product / (norm_a * norm_b)


class ObjectStoreInterface:
    async def store_object(self, key: str, data: bytes, metadata: Optional[Dict[str, Any]] = None) -> str:
        raise NotImplementedError
    
    async def get_object(self, key: str) -> Optional[bytes]:
        raise NotImplementedError
    
    async def delete_object(self, key: str) -> bool:
        raise NotImplementedError


class MockObjectStore(ObjectStoreInterface):
    def __init__(self):
        self.objects: Dict[str, bytes] = {}
        self.metadata: Dict[str, Dict[str, Any]] = {}
    
    async def store_object(self, key: str, data: bytes, metadata: Optional[Dict[str, Any]] = None) -> str:
        self.objects[key] = data
        if metadata:
            self.metadata[key] = metadata
        return key
    
    async def get_object(self, key: str) -> Optional[bytes]:
        return self.objects.get(key)
    
    async def delete_object(self, key: str) -> bool:
        if key in self.objects:
            del self.objects[key]
            if key in self.metadata:
                del self.metadata[key]
            return True
        return False


class CapacityManager:
    def __init__(
        self,
        max_samples: int = 100000,
        max_storage_bytes: int = 10 * 1024 * 1024 * 1024,
        quality_threshold: float = 0.3,
        usage_threshold: int = 5
    ):
        self.max_samples = max_samples
        self.max_storage_bytes = max_storage_bytes
        self.quality_threshold = quality_threshold
        self.usage_threshold = usage_threshold
    
    def should_evict(self, sample: Sample, total_count: int) -> bool:
        if total_count < self.max_samples:
            return False
        
        if sample.quality < self.quality_threshold:
            return True
        
        if sample.usage_count < self.usage_threshold:
            days_since_creation = (datetime.now() - sample.created_at).days
            if days_since_creation > 30:
                return True
        
        return False
    
    def get_eviction_candidates(self, samples: List[Sample]) -> List[Sample]:
        candidates = []
        
        for sample in samples:
            score = self._calculate_eviction_score(sample)
            candidates.append((sample, score))
        
        candidates.sort(key=lambda x: x[1], reverse=True)
        return [s for s, _ in candidates]
    
    def _calculate_eviction_score(self, sample: Sample) -> float:
        score = 0.0
        
        score += (1.0 - sample.quality) * 0.4
        
        score += (1.0 / (sample.usage_count + 1)) * 0.3
        
        if sample.last_used:
            days_unused = (datetime.now() - sample.last_used).days
            score += min(days_unused / 365, 1.0) * 0.2
        else:
            score += 0.2
        
        if sample.expires_at and sample.expires_at < datetime.now():
            score += 0.1
        
        return score


class SampleRepository:
    def __init__(
        self,
        db_pool: Optional[asyncpg.Pool] = None,
        vector_store: Optional[VectorStoreInterface] = None,
        object_store: Optional[ObjectStoreInterface] = None,
        capacity_manager: Optional[CapacityManager] = None
    ):
        self.db_pool = db_pool
        self.vector_store = vector_store or MockVectorStore()
        self.object_store = object_store or MockObjectStore()
        self.capacity_manager = capacity_manager or CapacityManager()
        
        self._in_memory_store: Dict[str, Sample] = {}
        self._initialized = False
    
    async def initialize(self, db_url: Optional[str] = None):
        if db_url:
            self.db_pool = await asyncpg.create_pool(db_url)
            await self._create_tables()
        self._initialized = True
        logger.info("SampleRepository initialized")
    
    async def _create_tables(self):
        if not self.db_pool:
            return
        
        async with self.db_pool.acquire() as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS samples (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    source_agent_id TEXT NOT NULL,
                    content JSONB NOT NULL,
                    embedding_id TEXT,
                    tags TEXT[],
                    quality REAL DEFAULT 0.5,
                    status TEXT DEFAULT 'raw',
                    annotations JSONB DEFAULT '{}',
                    metadata JSONB DEFAULT '{}',
                    usage_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used TIMESTAMP,
                    expires_at TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_samples_type ON samples(type);
                CREATE INDEX IF NOT EXISTS idx_samples_tags ON samples USING GIN(tags);
                CREATE INDEX IF NOT EXISTS idx_samples_quality ON samples(quality);
                CREATE INDEX IF NOT EXISTS idx_samples_created_at ON samples(created_at);
                CREATE INDEX IF NOT EXISTS idx_samples_source_agent ON samples(source_agent_id);
            ''')
    
    async def store(self, sample_data: Dict[str, Any]) -> str:
        sample = Sample(
            id=sample_data.get("id", str(uuid4())),
            type=SampleType(sample_data.get("type", "text")),
            source_agent_id=sample_data.get("source_agent_id", "unknown"),
            content=sample_data.get("content", {}),
            tags=sample_data.get("tags", []),
            quality=sample_data.get("quality", 0.5),
            status=SampleStatus(sample_data.get("status", "raw")),
            annotations=sample_data.get("annotations", {}),
            metadata=sample_data.get("metadata", {}),
            expires_at=sample_data.get("expires_at")
        )
        
        if sample_data.get("embedding"):
            sample.embedding_id = await self.vector_store.store_embedding(
                sample.id,
                sample_data["embedding"]
            )
        
        if sample_data.get("raw_data"):
            object_key = f"raw_{sample.id}"
            await self.object_store.store_object(
                object_key,
                sample_data["raw_data"],
                {"sample_id": sample.id}
            )
            sample.metadata["raw_data_key"] = object_key
        
        if self.db_pool:
            await self._store_to_db(sample)
        else:
            self._in_memory_store[sample.id] = sample
        
        await self._check_capacity()
        
        return sample.id
    
    async def _store_to_db(self, sample: Sample):
        if not self.db_pool:
            return
        
        async with self.db_pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO samples (
                    id, type, source_agent_id, content, embedding_id, tags,
                    quality, status, annotations, metadata, usage_count,
                    created_at, last_used, expires_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                ON CONFLICT (id) DO UPDATE SET
                    content = EXCLUDED.content,
                    quality = EXCLUDED.quality,
                    status = EXCLUDED.status,
                    annotations = EXCLUDED.annotations,
                    metadata = EXCLUDED.metadata,
                    usage_count = EXCLUDED.usage_count,
                    last_used = EXCLUDED.last_used
            ''',
                sample.id, sample.type.value, sample.source_agent_id,
                json.dumps(sample.content), sample.embedding_id, sample.tags,
                sample.quality, sample.status.value,
                json.dumps(sample.annotations), json.dumps(sample.metadata),
                sample.usage_count, sample.created_at, sample.last_used, sample.expires_at
            )
    
    async def get(self, sample_id: str) -> Optional[Sample]:
        if self.db_pool:
            return await self._get_from_db(sample_id)
        return self._in_memory_store.get(sample_id)
    
    async def _get_from_db(self, sample_id: str) -> Optional[Sample]:
        if not self.db_pool:
            return None
        
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM samples WHERE id = $1", sample_id
            )
            
            if row:
                return Sample(
                    id=row["id"],
                    type=SampleType(row["type"]),
                    source_agent_id=row["source_agent_id"],
                    content=json.loads(row["content"]) if isinstance(row["content"], str) else row["content"],
                    embedding_id=row["embedding_id"],
                    tags=row["tags"] or [],
                    quality=row["quality"],
                    status=SampleStatus(row["status"]),
                    annotations=json.loads(row["annotations"]) if isinstance(row["annotations"], str) else row["annotations"],
                    metadata=json.loads(row["metadata"]) if isinstance(row["metadata"], str) else row["metadata"],
                    usage_count=row["usage_count"],
                    created_at=row["created_at"],
                    last_used=row["last_used"],
                    expires_at=row["expires_at"]
                )
        return None
    
    async def query(self, query: SampleQuery) -> List[Sample]:
        if self.db_pool:
            return await self._query_from_db(query)
        return self._query_from_memory(query)
    
    def _query_from_memory(self, query: SampleQuery) -> List[Sample]:
        samples = list(self._in_memory_store.values())
        
        if query.types:
            samples = [s for s in samples if s.type in query.types]
        
        if query.tags:
            samples = [s for s in samples if any(tag in s.tags for tag in query.tags)]
        
        samples = [s for s in samples if query.min_quality <= s.quality <= query.max_quality]
        
        if query.source_agent_id:
            samples = [s for s in samples if s.source_agent_id == query.source_agent_id]
        
        if query.status:
            samples = [s for s in samples if s.status == query.status]
        
        if query.created_after:
            samples = [s for s in samples if s.created_at >= query.created_after]
        
        if query.created_before:
            samples = [s for s in samples if s.created_at <= query.created_before]
        
        reverse = query.order_desc
        if query.order_by == "created_at":
            samples.sort(key=lambda s: s.created_at, reverse=reverse)
        elif query.order_by == "quality":
            samples.sort(key=lambda s: s.quality, reverse=reverse)
        elif query.order_by == "usage_count":
            samples.sort(key=lambda s: s.usage_count, reverse=reverse)
        
        return samples[query.offset:query.offset + query.limit]
    
    async def _query_from_db(self, query: SampleQuery) -> List[Sample]:
        if not self.db_pool:
            return []
        
        conditions = []
        params = []
        param_idx = 1
        
        if query.types:
            conditions.append(f"type = ANY(${param_idx})")
            params.append([t.value for t in query.types])
            param_idx += 1
        
        if query.tags:
            conditions.append(f"tags && ${param_idx}")
            params.append(query.tags)
            param_idx += 1
        
        if query.min_quality > 0:
            conditions.append(f"quality >= ${param_idx}")
            params.append(query.min_quality)
            param_idx += 1
        
        if query.max_quality < 1:
            conditions.append(f"quality <= ${param_idx}")
            params.append(query.max_quality)
            param_idx += 1
        
        if query.source_agent_id:
            conditions.append(f"source_agent_id = ${param_idx}")
            params.append(query.source_agent_id)
            param_idx += 1
        
        if query.status:
            conditions.append(f"status = ${param_idx}")
            params.append(query.status.value)
            param_idx += 1
        
        if query.created_after:
            conditions.append(f"created_at >= ${param_idx}")
            params.append(query.created_after)
            param_idx += 1
        
        if query.created_before:
            conditions.append(f"created_at <= ${param_idx}")
            params.append(query.created_before)
            param_idx += 1
        
        where_clause = " AND ".join(conditions) if conditions else "TRUE"
        order_direction = "DESC" if query.order_desc else "ASC"
        
        sql = f'''
            SELECT * FROM samples
            WHERE {where_clause}
            ORDER BY {query.order_by} {order_direction}
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        '''
        params.extend([query.limit, query.offset])
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(sql, *params)
            
            return [
                Sample(
                    id=row["id"],
                    type=SampleType(row["type"]),
                    source_agent_id=row["source_agent_id"],
                    content=json.loads(row["content"]) if isinstance(row["content"], str) else row["content"],
                    embedding_id=row["embedding_id"],
                    tags=row["tags"] or [],
                    quality=row["quality"],
                    status=SampleStatus(row["status"]),
                    annotations=json.loads(row["annotations"]) if isinstance(row["annotations"], str) else row["annotations"],
                    metadata=json.loads(row["metadata"]) if isinstance(row["metadata"], str) else row["metadata"],
                    usage_count=row["usage_count"],
                    created_at=row["created_at"],
                    last_used=row["last_used"],
                    expires_at=row["expires_at"]
                )
                for row in rows
            ]
    
    async def update(self, sample_id: str, updates: Dict[str, Any]) -> bool:
        sample = await self.get(sample_id)
        if not sample:
            return False
        
        for key, value in updates.items():
            if hasattr(sample, key):
                setattr(sample, key, value)
        
        if self.db_pool:
            await self._store_to_db(sample)
        else:
            self._in_memory_store[sample_id] = sample
        
        return True
    
    async def increment_usage(self, sample_id: str) -> bool:
        sample = await self.get(sample_id)
        if not sample:
            return False
        
        sample.usage_count += 1
        sample.last_used = datetime.now()
        
        if self.db_pool:
            await self._store_to_db(sample)
        else:
            self._in_memory_store[sample_id] = sample
        
        return True
    
    async def delete(self, sample_id: str) -> bool:
        sample = await self.get(sample_id)
        if not sample:
            return False
        
        if sample.embedding_id:
            await self.vector_store.delete_embedding(sample.embedding_id)
        
        if sample.metadata.get("raw_data_key"):
            await self.object_store.delete_object(sample.metadata["raw_data_key"])
        
        if self.db_pool:
            async with self.db_pool.acquire() as conn:
                await conn.execute("DELETE FROM samples WHERE id = $1", sample_id)
        else:
            if sample_id in self._in_memory_store:
                del self._in_memory_store[sample_id]
        
        return True
    
    async def search_similar(
        self,
        embedding: List[float],
        top_k: int = 10,
        filter_query: Optional[SampleQuery] = None
    ) -> List[Tuple[Sample, float]]:
        similar_ids = await self.vector_store.search_similar(embedding, top_k * 2)
        
        results = []
        for embedding_id, similarity in similar_ids:
            samples = await self.query(SampleQuery(
                limit=1,
                offset=0
            ))
            
            for sample in samples:
                if sample.embedding_id == embedding_id:
                    if filter_query:
                        if self._matches_query(sample, filter_query):
                            results.append((sample, similarity))
                    else:
                        results.append((sample, similarity))
                    break
            
            if len(results) >= top_k:
                break
        
        return results
    
    def _matches_query(self, sample: Sample, query: SampleQuery) -> bool:
        if query.types and sample.type not in query.types:
            return False
        if query.tags and not any(tag in sample.tags for tag in query.tags):
            return False
        if not (query.min_quality <= sample.quality <= query.max_quality):
            return False
        if query.source_agent_id and sample.source_agent_id != query.source_agent_id:
            return False
        if query.status and sample.status != query.status:
            return False
        return True
    
    async def _check_capacity(self):
        total_count = len(self._in_memory_store) if not self.db_pool else await self._get_db_count()
        
        if total_count > self.capacity_manager.max_samples:
            await self._evict_samples(total_count - self.capacity_manager.max_samples + 100)
    
    async def _get_db_count(self) -> int:
        if not self.db_pool:
            return len(self._in_memory_store)
        
        async with self.db_pool.acquire() as conn:
            return await conn.fetchval("SELECT COUNT(*) FROM samples")
    
    async def _evict_samples(self, count: int):
        samples = await self.query(SampleQuery(limit=10000, order_by="quality", order_desc=False))
        
        candidates = self.capacity_manager.get_eviction_candidates(samples)
        
        for sample in candidates[:count]:
            await self.delete(sample.id)
            logger.info(f"Evicted sample {sample.id} (quality: {sample.quality}, usage: {sample.usage_count})")
    
    async def get_statistics(self) -> Dict[str, Any]:
        samples = await self.query(SampleQuery(limit=100000))
        
        type_counts = {}
        for sample in samples:
            type_counts[sample.type.value] = type_counts.get(sample.type.value, 0) + 1
        
        quality_distribution = {
            "high": len([s for s in samples if s.quality >= 0.7]),
            "medium": len([s for s in samples if 0.3 <= s.quality < 0.7]),
            "low": len([s for s in samples if s.quality < 0.3])
        }
        
        return {
            "total_samples": len(samples),
            "by_type": type_counts,
            "quality_distribution": quality_distribution,
            "avg_quality": sum(s.quality for s in samples) / len(samples) if samples else 0,
            "total_usage": sum(s.usage_count for s in samples)
        }
    
    async def archive_low_quality(self, quality_threshold: float = 0.3):
        samples = await self.query(SampleQuery(min_quality=0.0, max_quality=quality_threshold, limit=1000))
        
        for sample in samples:
            sample.status = SampleStatus.ARCHIVED
            if self.db_pool:
                await self._store_to_db(sample)
            else:
                self._in_memory_store[sample.id] = sample
        
        logger.info(f"Archived {len(samples)} low-quality samples")
    
    async def close(self):
        if self.db_pool:
            await self.db_pool.close()
