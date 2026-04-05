"""
向量化存储模块 - pgvector集成
支持Agent记忆、文档嵌入、相似度搜索的向量存储
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import asyncio
import asyncpg
import numpy as np
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)


class DistanceMetric(Enum):
    L2 = "vector_l2_ops"
    COSINE = "vector_cosine_ops"
    INNER_PRODUCT = "vector_ip_ops"


class IndexType(Enum):
    IVFFLAT = "ivfflat"
    HNSW = "hnsw"


@dataclass
class VectorConfig:
    dimensions: int
    distance_metric: DistanceMetric
    index_type: IndexType
    index_lists: int = 100
    hnsw_m: int = 16
    hnsw_ef_construction: int = 64


@dataclass
class VectorRecord:
    id: Optional[int] = None
    vector: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class SearchResult:
    id: int
    vector: List[float]
    distance: float
    metadata: Dict[str, Any]
    similarity: float


class PgVectorStore:
    DEFAULT_CONFIG = VectorConfig(
        dimensions=1536,
        distance_metric=DistanceMetric.COSINE,
        index_type=IndexType.HNSW,
        hnsw_m=16,
        hnsw_ef_construction=64
    )
    
    def __init__(
        self, 
        connection_pool: asyncpg.Pool,
        config: Optional[VectorConfig] = None
    ):
        self.pool = connection_pool
        self.config = config or self.DEFAULT_CONFIG
        self._initialized = False
        
    async def initialize(self):
        async with self.pool.acquire() as conn:
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            
            await self._create_tables(conn)
            await self._create_indexes(conn)
            
        self._initialized = True
        logger.info(f"PgVectorStore initialized with {self.config.dimensions} dimensions")
        
    async def _create_tables(self, conn: asyncpg.Connection):
        await conn.execute(f"""
            CREATE TABLE IF NOT EXISTS agent_embeddings (
                id BIGSERIAL PRIMARY KEY,
                agent_id VARCHAR(255) NOT NULL,
                embedding_type VARCHAR(50) NOT NULL,
                embedding vector({self.config.dimensions}),
                metadata JSONB DEFAULT '{{}}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(agent_id, embedding_type)
            );
        """)
        
        await conn.execute(f"""
            CREATE TABLE IF NOT EXISTS memory_embeddings (
                id BIGSERIAL PRIMARY KEY,
                memory_id VARCHAR(255) NOT NULL,
                agent_id VARCHAR(255) NOT NULL,
                embedding vector({self.config.dimensions}),
                content TEXT,
                metadata JSONB DEFAULT '{{}}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(memory_id)
            );
        """)
        
        await conn.execute(f"""
            CREATE TABLE IF NOT EXISTS document_embeddings (
                id BIGSERIAL PRIMARY KEY,
                document_id VARCHAR(255) NOT NULL,
                chunk_index INTEGER NOT NULL,
                embedding vector({self.config.dimensions}),
                content TEXT,
                metadata JSONB DEFAULT '{{}}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(document_id, chunk_index)
            );
        """)
        
        await conn.execute(f"""
            CREATE TABLE IF NOT EXISTS knowledge_embeddings (
                id BIGSERIAL PRIMARY KEY,
                knowledge_id VARCHAR(255) NOT NULL,
                domain VARCHAR(100) NOT NULL,
                embedding vector({self.config.dimensions}),
                content TEXT,
                metadata JSONB DEFAULT '{{}}',
                importance_score FLOAT DEFAULT 0.5,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(knowledge_id)
            );
        """)
        
    async def _create_indexes(self, conn: asyncpg.Connection):
        ops = self.config.distance_metric.value
        
        if self.config.index_type == IndexType.IVFFLAT:
            await conn.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_agent_embeddings_vector 
                ON agent_embeddings 
                USING ivfflat (embedding {ops})
                WITH (lists = {self.config.index_lists});
            """)
            
            await conn.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_memory_embeddings_vector 
                ON memory_embeddings 
                USING ivfflat (embedding {ops})
                WITH (lists = {self.config.index_lists});
            """)
            
        elif self.config.index_type == IndexType.HNSW:
            await conn.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_agent_embeddings_vector 
                ON agent_embeddings 
                USING hnsw (embedding {ops})
                WITH (m = {self.config.hnsw_m}, ef_construction = {self.config.hnsw_ef_construction});
            """)
            
            await conn.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_memory_embeddings_vector 
                ON memory_embeddings 
                USING hnsw (embedding {ops})
                WITH (m = {self.config.hnsw_m}, ef_construction = {self.config.hnsw_ef_construction});
            """)
            
            await conn.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_document_embeddings_vector 
                ON document_embeddings 
                USING hnsw (embedding {ops})
                WITH (m = {self.config.hnsw_m}, ef_construction = {self.config.hnsw_ef_construction});
            """)
            
            await conn.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_knowledge_embeddings_vector 
                ON knowledge_embeddings 
                USING hnsw (embedding {ops})
                WITH (m = {self.config.hnsw_m}, ef_construction = {self.config.hnsw_ef_construction});
            """)
            
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_agent_embeddings_agent_id 
            ON agent_embeddings (agent_id);
        """)
        
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_memory_embeddings_agent_id 
            ON memory_embeddings (agent_id);
        """)
        
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_document_embeddings_doc_id 
            ON document_embeddings (document_id);
        """)
        
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_knowledge_embeddings_domain 
            ON knowledge_embeddings (domain);
        """)
        
    async def upsert_agent_embedding(
        self,
        agent_id: str,
        embedding_type: str,
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        vector_str = self._vector_to_string(embedding)
        metadata_json = json.dumps(metadata or {})
        
        async with self.pool.acquire() as conn:
            result = await conn.fetchrow(f"""
                INSERT INTO agent_embeddings (agent_id, embedding_type, embedding, metadata, updated_at)
                VALUES ($1, $2, $3, $4, CURRENT_TIMESTAMP)
                ON CONFLICT (agent_id, embedding_type) 
                DO UPDATE SET embedding = $3, metadata = $4, updated_at = CURRENT_TIMESTAMP
                RETURNING id
            """, agent_id, embedding_type, vector_str, metadata_json)
            
        return result["id"]
    
    async def upsert_memory_embedding(
        self,
        memory_id: str,
        agent_id: str,
        embedding: List[float],
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        vector_str = self._vector_to_string(embedding)
        metadata_json = json.dumps(metadata or {})
        
        async with self.pool.acquire() as conn:
            result = await conn.fetchrow(f"""
                INSERT INTO memory_embeddings (memory_id, agent_id, embedding, content, metadata)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (memory_id) 
                DO UPDATE SET embedding = $3, content = $4, metadata = $5
                RETURNING id
            """, memory_id, agent_id, vector_str, content, metadata_json)
            
        return result["id"]
    
    async def upsert_document_embedding(
        self,
        document_id: str,
        chunk_index: int,
        embedding: List[float],
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        vector_str = self._vector_to_string(embedding)
        metadata_json = json.dumps(metadata or {})
        
        async with self.pool.acquire() as conn:
            result = await conn.fetchrow(f"""
                INSERT INTO document_embeddings (document_id, chunk_index, embedding, content, metadata)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (document_id, chunk_index) 
                DO UPDATE SET embedding = $3, content = $4, metadata = $5
                RETURNING id
            """, document_id, chunk_index, vector_str, content, metadata_json)
            
        return result["id"]
    
    async def upsert_knowledge_embedding(
        self,
        knowledge_id: str,
        domain: str,
        embedding: List[float],
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        importance_score: float = 0.5
    ) -> int:
        vector_str = self._vector_to_string(embedding)
        metadata_json = json.dumps(metadata or {})
        
        async with self.pool.acquire() as conn:
            result = await conn.fetchrow(f"""
                INSERT INTO knowledge_embeddings (knowledge_id, domain, embedding, content, metadata, importance_score)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (knowledge_id) 
                DO UPDATE SET embedding = $3, content = $4, metadata = $5, importance_score = $6
                RETURNING id
            """, knowledge_id, domain, vector_str, content, metadata_json, importance_score)
            
        return result["id"]
    
    async def search_similar_agents(
        self,
        query_embedding: List[float],
        embedding_type: Optional[str] = None,
        limit: int = 10,
        threshold: float = 0.0
    ) -> List[SearchResult]:
        vector_str = self._vector_to_string(query_embedding)
        
        distance_expr = self._get_distance_expression("embedding", vector_str)
        
        async with self.pool.acquire() as conn:
            if embedding_type:
                rows = await conn.fetch(f"""
                    SELECT id, agent_id, embedding_type, embedding, metadata, {distance_expr} as distance
                    FROM agent_embeddings
                    WHERE embedding_type = $1
                    ORDER BY embedding <=> $2
                    LIMIT $3
                """, embedding_type, vector_str, limit)
            else:
                rows = await conn.fetch(f"""
                    SELECT id, agent_id, embedding_type, embedding, metadata, {distance_expr} as distance
                    FROM agent_embeddings
                    ORDER BY embedding <=> $1
                    LIMIT $2
                """, vector_str, limit)
                
        results = []
        for row in rows:
            distance = row["distance"]
            similarity = self._distance_to_similarity(distance)
            
            if similarity >= threshold:
                results.append(SearchResult(
                    id=row["id"],
                    vector=self._parse_vector(row["embedding"]),
                    distance=distance,
                    metadata={
                        "agent_id": row["agent_id"],
                        "embedding_type": row["embedding_type"],
                        **(row["metadata"] or {})
                    },
                    similarity=similarity
                ))
                
        return results
    
    async def search_similar_memories(
        self,
        query_embedding: List[float],
        agent_id: Optional[str] = None,
        limit: int = 10,
        threshold: float = 0.0
    ) -> List[SearchResult]:
        vector_str = self._vector_to_string(query_embedding)
        
        async with self.pool.acquire() as conn:
            if agent_id:
                rows = await conn.fetch(f"""
                    SELECT id, memory_id, agent_id, embedding, content, metadata, 
                           embedding <=> $1 as distance
                    FROM memory_embeddings
                    WHERE agent_id = $2
                    ORDER BY embedding <=> $1
                    LIMIT $3
                """, vector_str, agent_id, limit)
            else:
                rows = await conn.fetch(f"""
                    SELECT id, memory_id, agent_id, embedding, content, metadata, 
                           embedding <=> $1 as distance
                    FROM memory_embeddings
                    ORDER BY embedding <=> $1
                    LIMIT $2
                """, vector_str, limit)
                
        results = []
        for row in rows:
            distance = row["distance"]
            similarity = self._distance_to_similarity(distance)
            
            if similarity >= threshold:
                results.append(SearchResult(
                    id=row["id"],
                    vector=self._parse_vector(row["embedding"]),
                    distance=distance,
                    metadata={
                        "memory_id": row["memory_id"],
                        "agent_id": row["agent_id"],
                        "content": row["content"],
                        **(row["metadata"] or {})
                    },
                    similarity=similarity
                ))
                
        return results
    
    async def search_similar_documents(
        self,
        query_embedding: List[float],
        document_id: Optional[str] = None,
        limit: int = 10,
        threshold: float = 0.0
    ) -> List[SearchResult]:
        vector_str = self._vector_to_string(query_embedding)
        
        async with self.pool.acquire() as conn:
            if document_id:
                rows = await conn.fetch(f"""
                    SELECT id, document_id, chunk_index, embedding, content, metadata, 
                           embedding <=> $1 as distance
                    FROM document_embeddings
                    WHERE document_id = $2
                    ORDER BY embedding <=> $1
                    LIMIT $3
                """, vector_str, document_id, limit)
            else:
                rows = await conn.fetch(f"""
                    SELECT id, document_id, chunk_index, embedding, content, metadata, 
                           embedding <=> $1 as distance
                    FROM document_embeddings
                    ORDER BY embedding <=> $1
                    LIMIT $2
                """, vector_str, limit)
                
        results = []
        for row in rows:
            distance = row["distance"]
            similarity = self._distance_to_similarity(distance)
            
            if similarity >= threshold:
                results.append(SearchResult(
                    id=row["id"],
                    vector=self._parse_vector(row["embedding"]),
                    distance=distance,
                    metadata={
                        "document_id": row["document_id"],
                        "chunk_index": row["chunk_index"],
                        "content": row["content"],
                        **(row["metadata"] or {})
                    },
                    similarity=similarity
                ))
                
        return results
    
    async def search_knowledge(
        self,
        query_embedding: List[float],
        domain: Optional[str] = None,
        limit: int = 10,
        threshold: float = 0.0,
        min_importance: float = 0.0
    ) -> List[SearchResult]:
        vector_str = self._vector_to_string(query_embedding)
        
        async with self.pool.acquire() as conn:
            if domain:
                rows = await conn.fetch(f"""
                    SELECT id, knowledge_id, domain, embedding, content, metadata, 
                           importance_score, embedding <=> $1 as distance
                    FROM knowledge_embeddings
                    WHERE domain = $2 AND importance_score >= $3
                    ORDER BY embedding <=> $1
                    LIMIT $4
                """, vector_str, domain, min_importance, limit)
            else:
                rows = await conn.fetch(f"""
                    SELECT id, knowledge_id, domain, embedding, content, metadata, 
                           importance_score, embedding <=> $1 as distance
                    FROM knowledge_embeddings
                    WHERE importance_score >= $2
                    ORDER BY embedding <=> $1
                    LIMIT $3
                """, vector_str, min_importance, limit)
                
        results = []
        for row in rows:
            distance = row["distance"]
            similarity = self._distance_to_similarity(distance)
            
            if similarity >= threshold:
                results.append(SearchResult(
                    id=row["id"],
                    vector=self._parse_vector(row["embedding"]),
                    distance=distance,
                    metadata={
                        "knowledge_id": row["knowledge_id"],
                        "domain": row["domain"],
                        "content": row["content"],
                        "importance_score": row["importance_score"],
                        **(row["metadata"] or {})
                    },
                    similarity=similarity
                ))
                
        return results
    
    async def delete_agent_embedding(self, agent_id: str, embedding_type: Optional[str] = None):
        async with self.pool.acquire() as conn:
            if embedding_type:
                await conn.execute("""
                    DELETE FROM agent_embeddings 
                    WHERE agent_id = $1 AND embedding_type = $2
                """, agent_id, embedding_type)
            else:
                await conn.execute("""
                    DELETE FROM agent_embeddings WHERE agent_id = $1
                """, agent_id)
                
    async def delete_memory_embedding(self, memory_id: str):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                DELETE FROM memory_embeddings WHERE memory_id = $1
            """, memory_id)
            
    async def delete_document_embeddings(self, document_id: str):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                DELETE FROM document_embeddings WHERE document_id = $1
            """, document_id)
            
    async def delete_knowledge_embedding(self, knowledge_id: str):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                DELETE FROM knowledge_embeddings WHERE knowledge_id = $1
            """, knowledge_id)
            
    async def batch_insert_embeddings(
        self,
        table: str,
        records: List[Dict[str, Any]]
    ) -> int:
        if not records:
            return 0
            
        async with self.pool.acquire() as conn:
            if table == "memory_embeddings":
                for record in records:
                    vector_str = self._vector_to_string(record["embedding"])
                    await conn.execute("""
                        INSERT INTO memory_embeddings (memory_id, agent_id, embedding, content, metadata)
                        VALUES ($1, $2, $3, $4, $5)
                        ON CONFLICT (memory_id) DO NOTHING
                    """, record["memory_id"], record["agent_id"], vector_str, 
                        record.get("content"), json.dumps(record.get("metadata", {})))
                    
        return len(records)
    
    async def get_embedding_stats(self) -> Dict[str, Any]:
        async with self.pool.acquire() as conn:
            agent_count = await conn.fetchval("SELECT COUNT(*) FROM agent_embeddings")
            memory_count = await conn.fetchval("SELECT COUNT(*) FROM memory_embeddings")
            doc_count = await conn.fetchval("SELECT COUNT(*) FROM document_embeddings")
            knowledge_count = await conn.fetchval("SELECT COUNT(*) FROM knowledge_embeddings")
            
            agent_size = await conn.fetchval("SELECT pg_relation_size('agent_embeddings')")
            memory_size = await conn.fetchval("SELECT pg_relation_size('memory_embeddings')")
            doc_size = await conn.fetchval("SELECT pg_relation_size('document_embeddings')")
            knowledge_size = await conn.fetchval("SELECT pg_relation_size('knowledge_embeddings')")
            
        return {
            "agent_embeddings": {
                "count": agent_count,
                "size_bytes": agent_size
            },
            "memory_embeddings": {
                "count": memory_count,
                "size_bytes": memory_size
            },
            "document_embeddings": {
                "count": doc_count,
                "size_bytes": doc_size
            },
            "knowledge_embeddings": {
                "count": knowledge_count,
                "size_bytes": knowledge_size
            },
            "config": {
                "dimensions": self.config.dimensions,
                "distance_metric": self.config.distance_metric.value,
                "index_type": self.config.index_type.value
            }
        }
    
    def _vector_to_string(self, vector: List[float]) -> str:
        return "[" + ",".join(str(v) for v in vector) + "]"
    
    def _parse_vector(self, vector_str: str) -> List[float]:
        if isinstance(vector_str, str):
            return [float(v) for v in vector_str.strip("[]").split(",")]
        return list(vector_str)
    
    def _get_distance_expression(self, column: str, query_vector: str) -> str:
        if self.config.distance_metric == DistanceMetric.L2:
            return f"{column} <-> '{query_vector}'"
        elif self.config.distance_metric == DistanceMetric.COSINE:
            return f"{column} <=> '{query_vector}'"
        else:
            return f"{column} <#> '{query_vector}'"
    
    def _distance_to_similarity(self, distance: float) -> float:
        if self.config.distance_metric == DistanceMetric.COSINE:
            return 1 - distance
        elif self.config.distance_metric == DistanceMetric.INNER_PRODUCT:
            return -distance
        else:
            return 1 / (1 + distance)


async def create_vector_store(
    pool: asyncpg.Pool,
    dimensions: int = 1536,
    distance_metric: DistanceMetric = DistanceMetric.COSINE,
    index_type: IndexType = IndexType.HNSW
) -> PgVectorStore:
    config = VectorConfig(
        dimensions=dimensions,
        distance_metric=distance_metric,
        index_type=index_type
    )
    store = PgVectorStore(pool, config)
    await store.initialize()
    return store
