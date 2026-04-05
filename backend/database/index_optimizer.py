"""
PostgreSQL 索引优化模块
针对五端Agent集群的高性能索引策略
"""

from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
import asyncio
import asyncpg
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)


class IndexType(Enum):
    BTREE = "btree"
    HASH = "hash"
    GIN = "gin"
    GIST = "gist"
    BRIN = "brin"
    SPGIST = "spgist"


class IndexStrategy(Enum):
    EQUALITY = "equality"
    RANGE = "range"
    FULL_TEXT = "full_text"
    COMPOSITE = "composite"
    PARTIAL = "partial"
    EXPRESSION = "expression"


@dataclass
class IndexDefinition:
    name: str
    table: str
    columns: List[str]
    index_type: IndexType
    strategy: IndexStrategy
    is_unique: bool = False
    is_partial: bool = False
    partial_condition: Optional[str] = None
    expression: Optional[str] = None
    tablespace: Optional[str] = None
    fillfactor: int = 90
    concurrent: bool = True
    
    def generate_sql(self) -> str:
        unique_clause = "UNIQUE " if self.is_unique else ""
        
        if self.expression:
            columns_clause = f"({self.expression})"
        else:
            columns_clause = ", ".join(self.columns)
            
        sql = f"CREATE {unique_clause}INDEX "
        
        if self.concurrent:
            sql += "CONCURRENTLY "
            
        sql += f"IF NOT EXISTS {self.name} ON {self.table} "
        
        if self.index_type != IndexType.BTREE:
            sql += f"USING {self.index_type.value} "
            
        sql += f"({columns_clause})"
        
        if self.is_partial and self.partial_condition:
            sql += f" WHERE {self.partial_condition}"
            
        options = []
        if self.fillfactor != 90:
            options.append(f"fillfactor = {self.fillfactor}")
        if self.tablespace:
            options.append(f"tablespace = {self.tablespace}")
            
        if options:
            sql += " WITH (" + ", ".join(options) + ")"
            
        sql += ";"
        return sql


@dataclass
class IndexUsageStats:
    index_name: str
    table_name: str
    idx_scan: int
    idx_tup_read: int
    idx_tup_fetch: int
    size_bytes: int
    last_used: Optional[datetime] = None
    
    @property
    def usage_ratio(self) -> float:
        if self.idx_scan == 0:
            return 0.0
        return self.idx_tup_read / max(self.idx_scan, 1)
    
    @property
    def is_unused(self) -> bool:
        return self.idx_scan == 0


class PostgresIndexOptimizer:
    def __init__(self, connection_pool: asyncpg.Pool):
        self.pool = connection_pool
        self._index_definitions: Dict[str, IndexDefinition] = {}
        self._usage_stats: Dict[str, IndexUsageStats] = {}
        self._recommendations: List[Dict[str, Any]] = []
        
    async def initialize(self):
        await self._register_core_indexes()
        await self._create_registered_indexes()
        
    async def _register_core_indexes(self):
        self._index_definitions.update({
            "idx_agents_endpoint_status": IndexDefinition(
                name="idx_agents_endpoint_status",
                table="agents",
                columns=["endpoint_type", "status"],
                index_type=IndexType.BTREE,
                strategy=IndexStrategy.COMPOSITE,
                fillfactor=85
            ),
            "idx_agents_created_desc": IndexDefinition(
                name="idx_agents_created_desc",
                table="agents",
                columns=["created_at DESC"],
                index_type=IndexType.BTREE,
                strategy=IndexStrategy.RANGE,
                fillfactor=90
            ),
            "idx_agents_owner_active": IndexDefinition(
                name="idx_agents_owner_active",
                table="agents",
                columns=["owner_id"],
                index_type=IndexType.BTREE,
                strategy=IndexStrategy.EQUALITY,
                is_partial=True,
                partial_condition="status = 'active'"
            ),
            "idx_valuations_asset_date": IndexDefinition(
                name="idx_valuations_asset_date",
                table="valuations",
                columns=["asset_id", "valuation_date DESC"],
                index_type=IndexType.BTREE,
                strategy=IndexStrategy.COMPOSITE,
                fillfactor=80
            ),
            "idx_valuations_range": IndexDefinition(
                name="idx_valuations_range",
                table="valuations",
                columns=["estimated_value"],
                index_type=IndexType.BRIN,
                strategy=IndexStrategy.RANGE,
                fillfactor=90
            ),
            "idx_memory_agent_timestamp": IndexDefinition(
                name="idx_memory_agent_timestamp",
                table="agent_memory",
                columns=["agent_id", "timestamp DESC"],
                index_type=IndexType.BTREE,
                strategy=IndexStrategy.COMPOSITE,
                fillfactor=85
            ),
            "idx_memory_type_importance": IndexDefinition(
                name="idx_memory_type_importance",
                table="agent_memory",
                columns=["memory_type", "importance DESC"],
                index_type=IndexType.BTREE,
                strategy=IndexStrategy.COMPOSITE
            ),
            "idx_transactions_status_created": IndexDefinition(
                name="idx_transactions_status_created",
                table="transactions",
                columns=["status", "created_at DESC"],
                index_type=IndexType.BTREE,
                strategy=IndexStrategy.COMPOSITE
            ),
            "idx_transactions_parties": IndexDefinition(
                name="idx_transactions_parties",
                table="transactions",
                columns=["buyer_id", "seller_id"],
                index_type=IndexType.BTREE,
                strategy=IndexStrategy.COMPOSITE
            ),
            "idx_users_email_lower": IndexDefinition(
                name="idx_users_email_lower",
                table="users",
                columns=[],
                index_type=IndexType.BTREE,
                strategy=IndexStrategy.EXPRESSION,
                expression="LOWER(email)",
                is_unique=True
            ),
            "idx_users_endpoint_role": IndexDefinition(
                name="idx_users_endpoint_role",
                table="users",
                columns=["endpoint_type", "role"],
                index_type=IndexType.BTREE,
                strategy=IndexStrategy.COMPOSITE
            ),
            "idx_audit_log_timestamp": IndexDefinition(
                name="idx_audit_log_timestamp",
                table="audit_logs",
                columns=["timestamp DESC"],
                index_type=IndexType.BRIN,
                strategy=IndexStrategy.RANGE,
                fillfactor=90
            ),
            "idx_audit_log_user_action": IndexDefinition(
                name="idx_audit_log_user_action",
                table="audit_logs",
                columns=["user_id", "action"],
                index_type=IndexType.BTREE,
                strategy=IndexStrategy.COMPOSITE
            ),
            "idx_nft_owner_token": IndexDefinition(
                name="idx_nft_owner_token",
                table="nft_tokens",
                columns=["owner_id", "token_id"],
                index_type=IndexType.BTREE,
                strategy=IndexStrategy.COMPOSITE
            ),
            "idx_nft_metadata_gin": IndexDefinition(
                name="idx_nft_metadata_gin",
                table="nft_tokens",
                columns=["metadata"],
                index_type=IndexType.GIN,
                strategy=IndexStrategy.COMPOSITE
            ),
            "idx_messages_conversation_created": IndexDefinition(
                name="idx_messages_conversation_created",
                table="messages",
                columns=["conversation_id", "created_at DESC"],
                index_type=IndexType.BTREE,
                strategy=IndexStrategy.COMPOSITE,
                fillfactor=85
            ),
            "idx_messages_sender_partial": IndexDefinition(
                name="idx_messages_sender_partial",
                table="messages",
                columns=["sender_id"],
                index_type=IndexType.BTREE,
                strategy=IndexStrategy.EQUALITY,
                is_partial=True,
                partial_condition="is_deleted = false"
            ),
            "idx_reports_status_generated": IndexDefinition(
                name="idx_reports_status_generated",
                table="valuation_reports",
                columns=["status", "generated_at DESC"],
                index_type=IndexType.BTREE,
                strategy=IndexStrategy.COMPOSITE
            ),
            "idx_fulltext_assets": IndexDefinition(
                name="idx_fulltext_assets",
                table="assets",
                columns=[],
                index_type=IndexType.GIN,
                strategy=IndexStrategy.FULL_TEXT,
                expression="to_tsvector('english', description || ' ' || address)"
            ),
            "idx_fulltext_agents": IndexDefinition(
                name="idx_fulltext_agents",
                table="agents",
                columns=[],
                index_type=IndexType.GIN,
                strategy=IndexStrategy.FULL_TEXT,
                expression="to_tsvector('english', name || ' ' || description)"
            ),
        })
        
    async def _create_registered_indexes(self):
        async with self.pool.acquire() as conn:
            for name, definition in self._index_definitions.items():
                try:
                    sql = definition.generate_sql()
                    await conn.execute(sql)
                    logger.info(f"Created index: {name}")
                except Exception as e:
                    logger.warning(f"Failed to create index {name}: {e}")
                    
    async def analyze_index_usage(self) -> Dict[str, IndexUsageStats]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    schemaname,
                    relname as table_name,
                    indexrelname as index_name,
                    idx_scan,
                    idx_tup_read,
                    idx_tup_fetch,
                    pg_relation_size(indexrelid) as size_bytes
                FROM pg_stat_user_indexes
                ORDER BY idx_scan DESC
            """)
            
            for row in rows:
                stats = IndexUsageStats(
                    index_name=row["index_name"],
                    table_name=row["table_name"],
                    idx_scan=row["idx_scan"],
                    idx_tup_read=row["idx_tup_read"],
                    idx_tup_fetch=row["idx_tup_fetch"],
                    size_bytes=row["size_bytes"]
                )
                self._usage_stats[row["index_name"]] = stats
                
        return self._usage_stats
    
    async def find_unused_indexes(self) -> List[IndexUsageStats]:
        if not self._usage_stats:
            await self.analyze_index_usage()
            
        return [
            stats for stats in self._usage_stats.values()
            if stats.is_unused and not stats.index_name.endswith("_pkey")
        ]
    
    async def find_duplicate_indexes(self) -> List[Tuple[str, str]]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT
                    pg_get_indexdef(i.oid) as index_def,
                    array_agg(i.relname) as indexes
                FROM pg_index ix
                JOIN pg_class i ON i.oid = ix.indexrelid
                JOIN pg_class t ON t.oid = ix.indrelid
                GROUP BY pg_get_indexdef(i.oid), ix.indrelid
                HAVING count(*) > 1
            """)
            
        duplicates = []
        for row in rows:
            indexes = row["indexes"]
            for i in range(len(indexes)):
                for j in range(i + 1, len(indexes)):
                    duplicates.append((indexes[i], indexes[j]))
                    
        return duplicates
    
    async def get_index_size_report(self) -> Dict[str, Any]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT
                    schemaname,
                    relname as table_name,
                    indexrelname as index_name,
                    pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
                    pg_relation_size(indexrelid) as size_bytes
                FROM pg_stat_user_indexes
                ORDER BY pg_relation_size(indexrelid) DESC
            """)
            
        total_size = sum(r["size_bytes"] for r in rows)
        
        return {
            "total_index_size_bytes": total_size,
            "total_index_size_pretty": self._format_size(total_size),
            "indexes": [
                {
                    "name": r["index_name"],
                    "table": r["table_name"],
                    "size": r["index_size"],
                    "size_bytes": r["size_bytes"]
                }
                for r in rows
            ]
        }
    
    def _format_size(self, size_bytes: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.2f} PB"
    
    async def get_missing_index_recommendations(self) -> List[Dict[str, Any]]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT
                    schemaname,
                    relname as table_name,
                    array_agg(DISTINCT attname) as columns
                FROM pg_stat_user_indexes
                JOIN pg_attribute ON attrelid = indrelid AND attnum = ANY(indkey)
                WHERE idx_scan = 0
                GROUP BY schemaname, relname
            """)
            
        recommendations = []
        for row in rows:
            recommendations.append({
                "table": row["table_name"],
                "suggested_columns": row["columns"],
                "reason": "Table has sequential scans - consider adding index"
            })
            
        return recommendations
    
    async def reindex_table(self, table_name: str, concurrent: bool = True):
        async with self.pool.acquire() as conn:
            if concurrent:
                await conn.execute(f"REINDEX TABLE CONCURRENTLY {table_name};")
            else:
                await conn.execute(f"REINDEX TABLE {table_name};")
            logger.info(f"Reindexed table: {table_name}")
            
    async def drop_unused_indexes(self, dry_run: bool = True) -> List[str]:
        unused = await self.find_unused_indexes()
        dropped = []
        
        async with self.pool.acquire() as conn:
            for stats in unused:
                if stats.index_name.endswith("_pkey"):
                    continue
                    
                if dry_run:
                    logger.info(f"Would drop unused index: {stats.index_name}")
                    dropped.append(stats.index_name)
                else:
                    try:
                        await conn.execute(f"DROP INDEX CONCURRENTLY IF EXISTS {stats.index_name};")
                        dropped.append(stats.index_name)
                        logger.info(f"Dropped unused index: {stats.index_name}")
                    except Exception as e:
                        logger.error(f"Failed to drop index {stats.index_name}: {e}")
                        
        return dropped
    
    async def analyze_table_statistics(self, table_name: str):
        async with self.pool.acquire() as conn:
            await conn.execute(f"ANALYZE {table_name};")
            logger.info(f"Analyzed table statistics: {table_name}")
            
    async def get_table_bloat(self) -> List[Dict[str, Any]]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT
                    schemaname,
                    relname as table_name,
                    n_live_tup,
                    n_dead_tup,
                    ROUND(100.0 * n_dead_tup / NULLIF(n_live_tup + n_dead_tup, 0), 2) as bloat_ratio
                FROM pg_stat_user_tables
                WHERE n_dead_tup > 0
                ORDER BY n_dead_tup DESC
            """)
            
        return [dict(r) for r in rows]
    
    async def vacuum_analyze(self, table_name: Optional[str] = None):
        async with self.pool.acquire() as conn:
            if table_name:
                await conn.execute(f"VACUUM ANALYZE {table_name};")
                logger.info(f"Vacuum analyzed: {table_name}")
            else:
                await conn.execute("VACUUM ANALYZE;")
                logger.info("Vacuum analyzed all tables")
                
    async def get_index_recommendations(self) -> Dict[str, Any]:
        usage_stats = await self.analyze_index_usage()
        unused = await self.find_unused_indexes()
        duplicates = await self.find_duplicate_indexes()
        missing = await self.get_missing_index_recommendations()
        size_report = await self.get_index_size_report()
        bloat = await self.get_table_bloat()
        
        return {
            "summary": {
                "total_indexes": len(usage_stats),
                "unused_indexes": len(unused),
                "duplicate_pairs": len(duplicates),
                "missing_recommendations": len(missing),
                "total_index_size": size_report["total_index_size_pretty"]
            },
            "unused_indexes": [
                {
                    "name": s.index_name,
                    "table": s.table_name,
                    "size": self._format_size(s.size_bytes)
                }
                for s in unused
            ],
            "duplicate_indexes": [
                {"index1": d[0], "index2": d[1]}
                for d in duplicates
            ],
            "missing_indexes": missing,
            "table_bloat": bloat,
            "recommendations": self._generate_recommendations(unused, duplicates, bloat)
        }
    
    def _generate_recommendations(
        self, 
        unused: List[IndexUsageStats],
        duplicates: List[Tuple[str, str]],
        bloat: List[Dict[str, Any]]
    ) -> List[str]:
        recommendations = []
        
        if unused:
            recommendations.append(
                f"Consider dropping {len(unused)} unused indexes to save space"
            )
            
        if duplicates:
            recommendations.append(
                f"Found {len(duplicates)} duplicate index pairs - consolidate them"
            )
            
        high_bloat = [b for b in bloat if b.get("bloat_ratio", 0) > 20]
        if high_bloat:
            recommendations.append(
                f"{len(high_bloat)} tables have >20% bloat - run VACUUM FULL"
            )
            
        return recommendations


async def create_index_optimizer(pool: asyncpg.Pool) -> PostgresIndexOptimizer:
    optimizer = PostgresIndexOptimizer(pool)
    await optimizer.initialize()
    return optimizer
