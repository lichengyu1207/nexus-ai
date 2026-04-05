"""
高性能数据库服务模块
整合读写分离、连接池优化、慢查询监控
"""
import asyncio
import asyncpg
import time
import logging
from typing import Optional, Dict, Any, List, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

logger = logging.getLogger(__name__)


class DatabaseRole(Enum):
    PRIMARY = "primary"
    REPLICA = "replica"


@dataclass
class DatabaseConfig:
    host: str
    port: int
    database: str
    user: str
    password: str
    min_connections: int = 5
    max_connections: int = 20
    command_timeout: float = 60.0
    
    @property
    def dsn(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class ReadWriteSeparationConfig:
    primary: DatabaseConfig
    replicas: List[DatabaseConfig] = field(default_factory=list)
    replication_lag_threshold: float = 5.0
    health_check_interval: float = 30.0
    retry_attempts: int = 3
    retry_delay: float = 0.1


@dataclass
class ConnectionPoolStats:
    pool_name: str
    size: int
    idle: int
    busy: int
    min_size: int
    max_size: int
    wait_count: int = 0
    avg_wait_time_ms: float = 0.0


@dataclass
class QueryMetrics:
    query_hash: str
    query_pattern: str
    execution_count: int
    total_time_ms: float
    avg_time_ms: float
    max_time_ms: float
    min_time_ms: float
    last_executed: datetime


class ConnectionPoolManager:
    """连接池管理器"""
    
    def __init__(self, config: DatabaseConfig, pool_name: str = "default"):
        self.config = config
        self.pool_name = pool_name
        self._pool: Optional[asyncpg.Pool] = None
        self._stats = ConnectionPoolStats(
            pool_name=pool_name,
            size=0, idle=0, busy=0,
            min_size=config.min_connections,
            max_size=config.max_connections
        )
        
    async def initialize(self) -> bool:
        try:
            self._pool = await asyncpg.create_pool(
                self.config.dsn,
                min_size=self.config.min_connections,
                max_size=self.config.max_connections,
                command_timeout=self.config.command_timeout,
            )
            self._stats.size = self.config.min_connections
            logger.info(f"Connection pool '{self.pool_name}' initialized: {self.config.host}:{self.config.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize pool '{self.pool_name}': {e}")
            return False
    
    async def close(self):
        if self._pool:
            await self._pool.close()
            self._pool = None
            logger.info(f"Connection pool '{self.pool_name}' closed")
    
    @asynccontextmanager
    async def acquire(self):
        if not self._pool:
            raise RuntimeError(f"Pool '{self.pool_name}' not initialized")
        
        start_time = time.time()
        conn = None
        try:
            conn = await asyncio.wait_for(
                self._pool.acquire(),
                timeout=30.0
            )
            self._stats.busy += 1
            self._stats.idle -= 1
            yield conn
        except asyncio.TimeoutError:
            self._stats.wait_count += 1
            logger.warning(f"Connection acquire timeout in pool '{self.pool_name}'")
            raise
        finally:
            if conn and self._pool:
                await self._pool.release(conn)
                self._stats.busy -= 1
                self._stats.idle += 1
                wait_time = (time.time() - start_time) * 1000
                self._stats.avg_wait_time_ms = (
                    self._stats.avg_wait_time_ms * 0.9 + wait_time * 0.1
                )
    
    async def execute(self, query: str, *args, timeout: float = None) -> str:
        async with self.acquire() as conn:
            return await conn.execute(query, *args, timeout=timeout)
    
    async def fetch(self, query: str, *args, timeout: float = None) -> List[asyncpg.Record]:
        async with self.acquire() as conn:
            return await conn.fetch(query, *args, timeout=timeout)
    
    async def fetchrow(self, query: str, *args, timeout: float = None) -> Optional[asyncpg.Record]:
        async with self.acquire() as conn:
            return await conn.fetchrow(query, *args, timeout=timeout)
    
    async def fetchval(self, query: str, *args, timeout: float = None) -> Any:
        async with self.acquire() as conn:
            return await conn.fetchval(query, *args, timeout=timeout)
    
    def get_stats(self) -> ConnectionPoolStats:
        if self._pool:
            self._stats.size = self._pool.get_size()
            self._stats.idle = self._pool.get_idle_size()
        return self._stats


class ReadWriteSeparationManager:
    """读写分离管理器"""
    
    def __init__(self, config: ReadWriteSeparationConfig):
        self.config = config
        self._primary_pool: Optional[ConnectionPoolManager] = None
        self._replica_pools: List[ConnectionPoolManager] = []
        self._replica_lag: Dict[str, float] = {}
        self._current_replica_index = 0
        self._health_check_task: Optional[asyncio.Task] = None
        self._is_healthy: Dict[str, bool] = {}
        
    async def initialize(self) -> bool:
        self._primary_pool = ConnectionPoolManager(
            self.config.primary, "primary"
        )
        primary_ok = await self._primary_pool.initialize()
        if not primary_ok:
            logger.error("Failed to initialize primary pool")
            return False
        
        self._is_healthy["primary"] = True
        
        for i, replica_config in enumerate(self.config.replicas):
            pool = ConnectionPoolManager(replica_config, f"replica_{i}")
            replica_ok = await pool.initialize()
            if replica_ok:
                self._replica_pools.append(pool)
                self._is_healthy[f"replica_{i}"] = True
                self._replica_lag[f"replica_{i}"] = 0.0
            else:
                logger.warning(f"Failed to initialize replica {i}")
                self._is_healthy[f"replica_{i}"] = False
        
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        
        logger.info(f"Read-write separation initialized: primary + {len(self._replica_pools)} replicas")
        return True
    
    async def close(self):
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        if self._primary_pool:
            await self._primary_pool.close()
        
        for pool in self._replica_pools:
            await pool.close()
        
        logger.info("Read-write separation closed")
    
    async def _health_check_loop(self):
        while True:
            try:
                await asyncio.sleep(self.config.health_check_interval)
                await self._check_health()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")
    
    async def _check_health(self):
        try:
            async with self._primary_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            self._is_healthy["primary"] = True
        except Exception as e:
            logger.error(f"Primary health check failed: {e}")
            self._is_healthy["primary"] = False
        
        for i, pool in enumerate(self._replica_pools):
            replica_name = f"replica_{i}"
            try:
                async with pool.acquire() as conn:
                    lag = await conn.fetchval(
                        "SELECT EXTRACT(EPOCH FROM (now() - pg_last_xact_replay_timestamp()))"
                    )
                    self._replica_lag[replica_name] = lag or 0.0
                    self._is_healthy[replica_name] = True
            except Exception as e:
                logger.error(f"Replica {i} health check failed: {e}")
                self._is_healthy[replica_name] = False
    
    def _get_read_pool(self) -> ConnectionPoolManager:
        if not self._replica_pools:
            return self._primary_pool
        
        healthy_replicas = [
            (i, pool) for i, pool in enumerate(self._replica_pools)
            if self._is_healthy.get(f"replica_{i}", False)
            and self._replica_lag.get(f"replica_{i}", float('inf')) < self.config.replication_lag_threshold
        ]
        
        if not healthy_replicas:
            logger.warning("No healthy replicas, falling back to primary")
            return self._primary_pool
        
        self._current_replica_index = (self._current_replica_index + 1) % len(healthy_replicas)
        return healthy_replicas[self._current_replica_index][1]
    
    def _get_write_pool(self) -> ConnectionPoolManager:
        if not self._is_healthy.get("primary", False):
            raise RuntimeError("Primary database is not healthy")
        return self._primary_pool
    
    @asynccontextmanager
    async def read_connection(self):
        pool = self._get_read_pool()
        async with pool.acquire() as conn:
            yield conn
    
    @asynccontextmanager
    async def write_connection(self):
        pool = self._get_write_pool()
        async with pool.acquire() as conn:
            yield conn
    
    async def execute_read(self, query: str, *args, timeout: float = None) -> List[asyncpg.Record]:
        pool = self._get_read_pool()
        return await pool.fetch(query, *args, timeout=timeout)
    
    async def execute_write(self, query: str, *args, timeout: float = None) -> str:
        pool = self._get_write_pool()
        return await pool.execute(query, *args, timeout=timeout)
    
    async def fetchrow_read(self, query: str, *args, timeout: float = None) -> Optional[asyncpg.Record]:
        pool = self._get_read_pool()
        return await pool.fetchrow(query, *args, timeout=timeout)
    
    async def fetchval_read(self, query: str, *args, timeout: float = None) -> Any:
        pool = self._get_read_pool()
        return await pool.fetchval(query, *args, timeout=timeout)
    
    def get_stats(self) -> Dict[str, Any]:
        stats = {
            "primary": self._primary_pool.get_stats().__dict__ if self._primary_pool else None,
            "replicas": [],
            "health": self._is_healthy,
            "replication_lag": self._replica_lag,
        }
        
        for i, pool in enumerate(self._replica_pools):
            stats["replicas"].append({
                "name": f"replica_{i}",
                **pool.get_stats().__dict__
            })
        
        return stats


class SlowQueryMonitor:
    """慢查询监控器"""
    
    def __init__(self, slow_threshold_ms: float = 500.0, max_queries: int = 1000):
        self.slow_threshold_ms = slow_threshold_ms
        self.max_queries = max_queries
        self._slow_queries: List[Dict[str, Any]] = []
        self._query_metrics: Dict[str, QueryMetrics] = {}
        self._query_patterns: Dict[str, str] = {}
        
    def _hash_query(self, query: str) -> str:
        import hashlib
        normalized = ' '.join(query.strip().split())
        return hashlib.md5(normalized.encode()).hexdigest()[:16]
    
    def _normalize_query(self, query: str) -> str:
        import re
        normalized = query.strip()
        normalized = re.sub(r'\$\d+', '?', normalized)
        normalized = re.sub(r'\b\d+\b', '?', normalized)
        normalized = re.sub(r"'[^']*'", '?', normalized)
        normalized = ' '.join(normalized.split())
        return normalized[:200]
    
    def record_query(self, query: str, execution_time_ms: float, success: bool = True):
        query_hash = self._hash_query(query)
        query_pattern = self._normalize_query(query)
        
        if query_hash not in self._query_metrics:
            self._query_metrics[query_hash] = QueryMetrics(
                query_hash=query_hash,
                query_pattern=query_pattern,
                execution_count=0,
                total_time_ms=0,
                avg_time_ms=0,
                max_time_ms=0,
                min_time_ms=float('inf'),
                last_executed=datetime.now()
            )
        
        metrics = self._query_metrics[query_hash]
        metrics.execution_count += 1
        metrics.total_time_ms += execution_time_ms
        metrics.avg_time_ms = metrics.total_time_ms / metrics.execution_count
        metrics.max_time_ms = max(metrics.max_time_ms, execution_time_ms)
        metrics.min_time_ms = min(metrics.min_time_ms, execution_time_ms)
        metrics.last_executed = datetime.now()
        
        if execution_time_ms > self.slow_threshold_ms:
            self._slow_queries.append({
                "query": query[:500],
                "query_pattern": query_pattern,
                "execution_time_ms": execution_time_ms,
                "timestamp": datetime.now().isoformat(),
                "success": success
            })
            
            if len(self._slow_queries) > self.max_queries:
                self._slow_queries = self._slow_queries[-self.max_queries:]
            
            logger.warning(
                f"Slow query detected: {execution_time_ms:.2f}ms - {query_pattern[:100]}"
            )
    
    def get_slow_queries(self, limit: int = 100) -> List[Dict[str, Any]]:
        return sorted(
            self._slow_queries,
            key=lambda x: x["execution_time_ms"],
            reverse=True
        )[:limit]
    
    def get_query_metrics(self) -> List[Dict[str, Any]]:
        return [
            {
                "query_hash": m.query_hash,
                "query_pattern": m.query_pattern,
                "execution_count": m.execution_count,
                "avg_time_ms": round(m.avg_time_ms, 2),
                "max_time_ms": round(m.max_time_ms, 2),
                "min_time_ms": round(m.min_time_ms, 2) if m.min_time_ms != float('inf') else 0,
                "last_executed": m.last_executed.isoformat()
            }
            for m in sorted(
                self._query_metrics.values(),
                key=lambda x: x.total_time_ms,
                reverse=True
            )
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_slow_queries": len(self._slow_queries),
            "unique_query_patterns": len(self._query_metrics),
            "slow_threshold_ms": self.slow_threshold_ms,
            "top_slow_queries": self.get_slow_queries(10),
            "top_queries_by_time": self.get_query_metrics()[:20]
        }
    
    def clear(self):
        self._slow_queries.clear()
        self._query_metrics.clear()


class HighPerformanceDatabaseService:
    """高性能数据库服务"""
    
    _instance: Optional['HighPerformanceDatabaseService'] = None
    _lock = asyncio.Lock()
    
    def __init__(self, config: Optional[ReadWriteSeparationConfig] = None):
        self._config = config or self._create_default_config()
        self._rw_manager: Optional[ReadWriteSeparationManager] = None
        self._slow_query_monitor = SlowQueryMonitor()
        self._initialized = False
        
    @classmethod
    def _create_default_config(cls) -> ReadWriteSeparationConfig:
        database_url = os.getenv("DATABASE_URL", "")
        
        if database_url.startswith("postgresql"):
            from urllib.parse import urlparse
            parsed = urlparse(database_url.replace("postgresql+asyncpg://", "postgresql://"))
            
            primary_config = DatabaseConfig(
                host=parsed.hostname or "localhost",
                port=parsed.port or 5432,
                database=parsed.path.lstrip("/") or "fangdu",
                user=parsed.username or "postgres",
                password=parsed.password or "",
                min_connections=int(os.getenv("DB_MIN_CONNECTIONS", "10")),
                max_connections=int(os.getenv("DB_MAX_CONNECTIONS", "50")),
                command_timeout=float(os.getenv("DB_COMMAND_TIMEOUT", "60"))
            )
        else:
            primary_config = DatabaseConfig(
                host=os.getenv("DB_HOST", "localhost"),
                port=int(os.getenv("DB_PORT", "5432")),
                database=os.getenv("DB_NAME", "fangdu"),
                user=os.getenv("DB_USER", "postgres"),
                password=os.getenv("DB_PASSWORD", ""),
                min_connections=10,
                max_connections=50
            )
        
        replicas = []
        replica_hosts = os.getenv("DB_REPLICA_HOSTS", "")
        if replica_hosts:
            for i, host in enumerate(replica_hosts.split(",")):
                replica_config = DatabaseConfig(
                    host=host.strip(),
                    port=primary_config.port,
                    database=primary_config.database,
                    user=primary_config.user,
                    password=primary_config.password,
                    min_connections=5,
                    max_connections=20
                )
                replicas.append(replica_config)
        
        return ReadWriteSeparationConfig(
            primary=primary_config,
            replicas=replicas
        )
    
    @classmethod
    async def get_instance(cls) -> 'HighPerformanceDatabaseService':
        if cls._instance is None:
            async with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
                    await cls._instance.initialize()
        return cls._instance
    
    async def initialize(self) -> bool:
        if self._initialized:
            return True
        
        self._rw_manager = ReadWriteSeparationManager(self._config)
        success = await self._rw_manager.initialize()
        
        if success:
            self._initialized = True
            logger.info("High performance database service initialized")
        
        return success
    
    async def close(self):
        if self._rw_manager:
            await self._rw_manager.close()
        self._initialized = False
        logger.info("High performance database service closed")
    
    def _record_query(self, query: str, execution_time_ms: float, success: bool = True):
        self._slow_query_monitor.record_query(query, execution_time_ms, success)
    
    @asynccontextmanager
    async def read_connection(self):
        start_time = time.time()
        success = True
        async with self._rw_manager.read_connection() as conn:
            try:
                yield conn
            except Exception:
                success = False
                raise
            finally:
                execution_time = (time.time() - start_time) * 1000
                self._record_query("READ_QUERY", execution_time, success)
    
    @asynccontextmanager
    async def write_connection(self):
        start_time = time.time()
        success = True
        async with self._rw_manager.write_connection() as conn:
            try:
                yield conn
            except Exception:
                success = False
                raise
            finally:
                execution_time = (time.time() - start_time) * 1000
                self._record_query("WRITE_QUERY", execution_time, success)
    
    async def execute_read(self, query: str, *args, timeout: float = None) -> List[asyncpg.Record]:
        start_time = time.time()
        try:
            result = await self._rw_manager.execute_read(query, *args, timeout=timeout)
            return result
        finally:
            execution_time = (time.time() - start_time) * 1000
            self._record_query(query, execution_time)
    
    async def execute_write(self, query: str, *args, timeout: float = None) -> str:
        start_time = time.time()
        try:
            result = await self._rw_manager.execute_write(query, *args, timeout=timeout)
            return result
        finally:
            execution_time = (time.time() - start_time) * 1000
            self._record_query(query, execution_time)
    
    async def fetchrow_read(self, query: str, *args, timeout: float = None) -> Optional[asyncpg.Record]:
        start_time = time.time()
        try:
            result = await self._rw_manager.fetchrow_read(query, *args, timeout=timeout)
            return result
        finally:
            execution_time = (time.time() - start_time) * 1000
            self._record_query(query, execution_time)
    
    async def fetchval_read(self, query: str, *args, timeout: float = None) -> Any:
        start_time = time.time()
        try:
            result = await self._rw_manager.fetchval_read(query, *args, timeout=timeout)
            return result
        finally:
            execution_time = (time.time() - start_time) * 1000
            self._record_query(query, execution_time)
    
    async def execute_batch(self, queries: List[tuple]) -> List[Any]:
        results = []
        async with self.write_connection() as conn:
            for query, args in queries:
                start_time = time.time()
                try:
                    result = await conn.execute(query, *args)
                    results.append(result)
                finally:
                    execution_time = (time.time() - start_time) * 1000
                    self._record_query(query, execution_time)
        return results
    
    async def execute_transaction(self, operations: List[tuple]) -> List[Any]:
        results = []
        async with self.write_connection() as conn:
            async with conn.transaction():
                for query, args in operations:
                    start_time = time.time()
                    try:
                        result = await conn.execute(query, *args)
                        results.append(result)
                    finally:
                        execution_time = (time.time() - start_time) * 1000
                        self._record_query(query, execution_time)
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "connection_pools": self._rw_manager.get_stats() if self._rw_manager else None,
            "slow_queries": self._slow_query_monitor.get_stats(),
            "initialized": self._initialized
        }
    
    def get_slow_queries(self, limit: int = 100) -> List[Dict[str, Any]]:
        return self._slow_query_monitor.get_slow_queries(limit)
    
    def get_query_metrics(self) -> List[Dict[str, Any]]:
        return self._slow_query_monitor.get_query_metrics()


db_service: Optional[HighPerformanceDatabaseService] = None


async def get_db_service() -> HighPerformanceDatabaseService:
    global db_service
    if db_service is None:
        db_service = await HighPerformanceDatabaseService.get_instance()
    return db_service


async def init_db_service() -> bool:
    global db_service
    db_service = await HighPerformanceDatabaseService.get_instance()
    return db_service._initialized


async def close_db_service():
    global db_service
    if db_service:
        await db_service.close()
        db_service = None
