"""
记忆数据分区表模块
基于时间和大范围的分区策略，支持自动分区管理
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import asyncio
import asyncpg
import logging
from dateutil.relativedelta import relativedelta

logger = logging.getLogger(__name__)


class PartitionType(Enum):
    RANGE = "RANGE"
    LIST = "LIST"
    HASH = "HASH"


class PartitionInterval(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


@dataclass
class PartitionConfig:
    table_name: str
    partition_type: PartitionType
    partition_key: str
    interval: PartitionInterval
    retention_periods: int
    primary_key: str = "id"
    additional_indexes: List[str] = field(default_factory=list)
    
    def get_interval_delta(self) -> timedelta:
        deltas = {
            PartitionInterval.DAILY: timedelta(days=1),
            PartitionInterval.WEEKLY: timedelta(weeks=1),
            PartitionInterval.MONTHLY: relativedelta(months=1),
            PartitionInterval.QUARTERLY: relativedelta(months=3),
            PartitionInterval.YEARLY: relativedelta(years=1),
        }
        return deltas[self.interval]


@dataclass
class PartitionInfo:
    name: str
    parent_table: str
    start_value: Any
    end_value: Any
    created_at: datetime
    size_bytes: int = 0
    row_count: int = 0


class MemoryPartitionManager:
    PARTITION_CONFIGS: Dict[str, PartitionConfig] = {
        "agent_memory": PartitionConfig(
            table_name="agent_memory",
            partition_type=PartitionType.RANGE,
            partition_key="timestamp",
            interval=PartitionInterval.MONTHLY,
            retention_periods=12,
            primary_key="id",
            additional_indexes=["agent_id", "memory_type"]
        ),
        "audit_logs": PartitionConfig(
            table_name="audit_logs",
            partition_type=PartitionType.RANGE,
            partition_key="timestamp",
            interval=PartitionInterval.MONTHLY,
            retention_periods=36,
            primary_key="id",
            additional_indexes=["user_id", "action"]
        ),
        "valuations": PartitionConfig(
            table_name="valuations",
            partition_type=PartitionType.RANGE,
            partition_key="valuation_date",
            interval=PartitionInterval.QUARTERLY,
            retention_periods=24,
            primary_key="id",
            additional_indexes=["asset_id", "valuator_id"]
        ),
        "transactions": PartitionConfig(
            table_name="transactions",
            partition_type=PartitionType.RANGE,
            partition_key="created_at",
            interval=PartitionInterval.MONTHLY,
            retention_periods=60,
            primary_key="id",
            additional_indexes=["buyer_id", "seller_id", "status"]
        ),
        "agent_interactions": PartitionConfig(
            table_name="agent_interactions",
            partition_type=PartitionType.RANGE,
            partition_key="interaction_time",
            interval=PartitionInterval.WEEKLY,
            retention_periods=26,
            primary_key="id",
            additional_indexes=["agent_id", "target_agent_id"]
        ),
        "training_episodes": PartitionConfig(
            table_name="training_episodes",
            partition_type=PartitionType.RANGE,
            partition_key="episode_start",
            interval=PartitionInterval.MONTHLY,
            retention_periods=6,
            primary_key="id",
            additional_indexes=["agent_id", "algorithm"]
        ),
        "nft_events": PartitionConfig(
            table_name="nft_events",
            partition_type=PartitionType.RANGE,
            partition_key="event_time",
            interval=PartitionInterval.MONTHLY,
            retention_periods=24,
            primary_key="id",
            additional_indexes=["nft_id", "event_type"]
        ),
        "messages": PartitionConfig(
            table_name="messages",
            partition_type=PartitionType.RANGE,
            partition_key="created_at",
            interval=PartitionInterval.MONTHLY,
            retention_periods=12,
            primary_key="id",
            additional_indexes=["conversation_id", "sender_id"]
        ),
    }
    
    def __init__(self, connection_pool: asyncpg.Pool):
        self.pool = connection_pool
        self._partitions: Dict[str, List[PartitionInfo]] = {}
        
    async def initialize(self):
        for table_name in self.PARTITION_CONFIGS:
            await self._setup_partitioned_table(table_name)
            await self._sync_partition_info(table_name)
            
    async def _setup_partitioned_table(self, table_name: str):
        config = self.PARTITION_CONFIGS[table_name]
        
        async with self.pool.acquire() as conn:
            exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM pg_class WHERE relname = $1
                )
            """, table_name)
            
            if not exists:
                await self._create_partitioned_table(conn, config)
                
    async def _create_partitioned_table(self, conn: asyncpg.Connection, config: PartitionConfig):
        create_sql = f"""
            CREATE TABLE IF NOT EXISTS {config.table_name} (
                {config.primary_key} BIGSERIAL,
                {config.partition_key} TIMESTAMP NOT NULL,
                data JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY ({config.primary_key}, {config.partition_key})
            ) PARTITION BY RANGE ({config.partition_key});
        """
        
        await conn.execute(create_sql)
        
        for idx_col in config.additional_indexes:
            idx_name = f"idx_{config.table_name}_{idx_col}"
            await conn.execute(f"""
                CREATE INDEX IF NOT EXISTS {idx_name} 
                ON {config.table_name} ({idx_col});
            """)
            
        logger.info(f"Created partitioned table: {config.table_name}")
        
    async def _sync_partition_info(self, table_name: str):
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    child.relname AS partition_name,
                    parent.relname AS parent_table,
                    pg_get_expr(child.relpartbound, child.oid) AS partition_bound,
                    pg_relation_size(child.oid) AS size_bytes,
                    (SELECT reltuples::bigint FROM pg_class WHERE oid = child.oid) AS row_count
                FROM pg_inherits
                JOIN pg_class parent ON pg_inherits.inhparent = parent.oid
                JOIN pg_class child ON pg_inherits.inhrelid = child.oid
                WHERE parent.relname = $1
                ORDER BY child.relname
            """, table_name)
            
        partitions = []
        for row in rows:
            start_val, end_val = self._parse_partition_bound(row["partition_bound"])
            partitions.append(PartitionInfo(
                name=row["partition_name"],
                parent_table=row["parent_table"],
                start_value=start_val,
                end_value=end_val,
                created_at=datetime.now(),
                size_bytes=row["size_bytes"],
                row_count=int(row["row_count"])
            ))
            
        self._partitions[table_name] = partitions
        
    def _parse_partition_bound(self, bound_expr: str) -> tuple:
        import re
        match = re.search(r"FOR VALUES FROM \('([^']+)'\) TO \('([^']+)'\)", bound_expr)
        if match:
            start = datetime.fromisoformat(match.group(1).replace(" ", "T"))
            end = datetime.fromisoformat(match.group(2).replace(" ", "T"))
            return start, end
        return None, None
        
    def _generate_partition_name(self, config: PartitionConfig, start_date: datetime) -> str:
        if config.interval == PartitionInterval.DAILY:
            suffix = start_date.strftime("%Y%m%d")
        elif config.interval == PartitionInterval.WEEKLY:
            suffix = f"{start_date.strftime('%Y')}_w{start_date.isocalendar()[1]:02d}"
        elif config.interval == PartitionInterval.MONTHLY:
            suffix = start_date.strftime("%Y%m")
        elif config.interval == PartitionInterval.QUARTERLY:
            quarter = (start_date.month - 1) // 3 + 1
            suffix = f"{start_date.year}_q{quarter}"
        elif config.interval == PartitionInterval.YEARLY:
            suffix = start_date.strftime("%Y")
        else:
            suffix = start_date.strftime("%Y%m")
            
        return f"{config.table_name}_{suffix}"
    
    async def create_partition(
        self, 
        table_name: str, 
        start_date: datetime
    ) -> str:
        config = self.PARTITION_CONFIGS[table_name]
        partition_name = self._generate_partition_name(config, start_date)
        
        delta = config.get_interval_delta()
        if isinstance(delta, relativedelta):
            end_date = start_date + delta
        else:
            end_date = start_date + delta
            
        async with self.pool.acquire() as conn:
            await conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {partition_name}
                PARTITION OF {table_name}
                FOR VALUES FROM ('{start_date.isoformat()}') 
                TO ('{end_date.isoformat()}');
            """)
            
            for idx_col in config.additional_indexes:
                idx_name = f"idx_{partition_name}_{idx_col}"
                await conn.execute(f"""
                    CREATE INDEX IF NOT EXISTS {idx_name}
                    ON {partition_name} ({idx_col});
                """)
                
        logger.info(f"Created partition: {partition_name}")
        
        await self._sync_partition_info(table_name)
        
        return partition_name
    
    async def ensure_current_partitions(self):
        now = datetime.now()
        
        for table_name, config in self.PARTITION_CONFIGS.items():
            current_partition = self._get_current_partition_start(config, now)
            next_partition = self._get_next_partition_start(config, current_partition)
            
            partitions = self._partitions.get(table_name, [])
            partition_names = [p.name for p in partitions]
            
            current_name = self._generate_partition_name(config, current_partition)
            next_name = self._generate_partition_name(config, next_partition)
            
            if current_name not in partition_names:
                await self.create_partition(table_name, current_partition)
                
            if next_name not in partition_names:
                await self.create_partition(table_name, next_partition)
                
    def _get_current_partition_start(self, config: PartitionConfig, dt: datetime) -> datetime:
        if config.interval == PartitionInterval.DAILY:
            return dt.replace(hour=0, minute=0, second=0, microsecond=0)
        elif config.interval == PartitionInterval.WEEKLY:
            days_since_monday = dt.weekday()
            return (dt - timedelta(days=days_since_monday)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        elif config.interval == PartitionInterval.MONTHLY:
            return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif config.interval == PartitionInterval.QUARTERLY:
            quarter_month = ((dt.month - 1) // 3) * 3 + 1
            return dt.replace(
                month=quarter_month, day=1, 
                hour=0, minute=0, second=0, microsecond=0
            )
        elif config.interval == PartitionInterval.YEARLY:
            return dt.replace(
                month=1, day=1, 
                hour=0, minute=0, second=0, microsecond=0
            )
        return dt
    
    def _get_next_partition_start(self, config: PartitionConfig, current: datetime) -> datetime:
        delta = config.get_interval_delta()
        if isinstance(delta, relativedelta):
            return current + delta
        return current + delta
    
    async def drop_old_partitions(self) -> List[str]:
        dropped = []
        now = datetime.now()
        
        for table_name, config in self.PARTITION_CONFIGS.items():
            delta = config.get_interval_delta()
            retention_delta = delta * config.retention_periods if not isinstance(delta, relativedelta) else delta * config.retention_periods
            
            cutoff_date = now - retention_delta if not isinstance(retention_delta, relativedelta) else now - retention_delta
            
            partitions = self._partitions.get(table_name, [])
            
            for partition in partitions:
                if partition.end_value and partition.end_value < cutoff_date:
                    await self._drop_partition(table_name, partition.name)
                    dropped.append(partition.name)
                    
        return dropped
    
    async def _drop_partition(self, table_name: str, partition_name: str):
        async with self.pool.acquire() as conn:
            await conn.execute(f"DROP TABLE IF EXISTS {partition_name};")
            
        if table_name in self._partitions:
            self._partitions[table_name] = [
                p for p in self._partitions[table_name] 
                if p.name != partition_name
            ]
            
        logger.info(f"Dropped old partition: {partition_name}")
        
    async def get_partition_stats(self, table_name: str) -> Dict[str, Any]:
        partitions = self._partitions.get(table_name, [])
        
        total_size = sum(p.size_bytes for p in partitions)
        total_rows = sum(p.row_count for p in partitions)
        
        return {
            "table_name": table_name,
            "partition_count": len(partitions),
            "total_size_bytes": total_size,
            "total_rows": total_rows,
            "partitions": [
                {
                    "name": p.name,
                    "start": p.start_value.isoformat() if p.start_value else None,
                    "end": p.end_value.isoformat() if p.end_value else None,
                    "size_bytes": p.size_bytes,
                    "row_count": p.row_count
                }
                for p in partitions
            ]
        }
    
    async def get_all_partition_stats(self) -> Dict[str, Any]:
        stats = {}
        for table_name in self.PARTITION_CONFIGS:
            stats[table_name] = await self.get_partition_stats(table_name)
        return stats
    
    async def archive_partition(self, table_name: str, partition_name: str) -> str:
        async with self.pool.acquire() as conn:
            archive_name = f"{partition_name}_archive"
            
            await conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {archive_name} 
                (LIKE {partition_name} INCLUDING INDEXES);
            """)
            
            await conn.execute(f"""
                INSERT INTO {archive_name} 
                SELECT * FROM {partition_name};
            """)
            
            await conn.execute(f"DROP TABLE {partition_name};")
            
        logger.info(f"Archived partition: {partition_name} -> {archive_name}")
        return archive_name
    
    async def run_maintenance(self) -> Dict[str, Any]:
        results = {
            "created_partitions": [],
            "dropped_partitions": [],
            "errors": []
        }
        
        try:
            await self.ensure_current_partitions()
            results["created_partitions"] = ["current", "next"]
        except Exception as e:
            results["errors"].append(f"Failed to create partitions: {e}")
            
        try:
            dropped = await self.drop_old_partitions()
            results["dropped_partitions"] = dropped
        except Exception as e:
            results["errors"].append(f"Failed to drop old partitions: {e}")
            
        return results


async def create_partition_manager(pool: asyncpg.Pool) -> MemoryPartitionManager:
    manager = MemoryPartitionManager(pool)
    await manager.initialize()
    return manager
