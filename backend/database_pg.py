"""
PostgreSQL数据库连接模块
支持asyncpg异步连接
"""
import asyncpg
import asyncio
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager
import logging
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载.env文件（从项目根目录）
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

logger = logging.getLogger(__name__)

# 直接从环境变量获取DATABASE_URL，确保是PostgreSQL
_DATABASE_URL = os.getenv("DATABASE_URL", "")
if _DATABASE_URL.startswith("postgresql"):
    DATABASE_URL = _DATABASE_URL
else:
    # 如果不是PostgreSQL，强制使用PostgreSQL
    DATABASE_URL = "postgresql://postgres:147258%40Zxcvbnm@localhost:5432/fangdu"
    logger.warning(f"DATABASE_URL is not PostgreSQL, using default: {DATABASE_URL[:30]}...")

logger.info(f"DATABASE_URL for PostgreSQL: {DATABASE_URL[:30]}...")

class PostgreSQLConnectionPool:
    """
    PostgreSQL数据库连接池管理器
    """
    
    _instance: Optional['PostgreSQLConnectionPool'] = None
    _lock = asyncio.Lock()
    
    def __init__(self, database_url: str = DATABASE_URL, min_connections: int = 10, max_connections: int = 50):
        self.database_url = database_url
        self.min_connections = min_connections
        self.max_connections = max_connections
        self._pool: Optional[asyncpg.Pool] = None
        self._initialized = False
    
    @classmethod
    async def get_instance(cls) -> 'PostgreSQLConnectionPool':
        """获取单例实例"""
        if cls._instance is None:
            async with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
                    await cls._instance._initialize()
        return cls._instance
    
    async def _initialize(self):
        """初始化连接池"""
        if self._initialized:
            return
        
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable is not set")
        
        # 解析连接URL
        # postgresql+asyncpg://postgres:password@localhost:5432/fangdu
        self._pool = await asyncpg.create_pool(
            self.database_url.replace("postgresql+asyncpg://", "postgresql://"),
            min_size=self.min_connections,
            max_size=self.max_connections,
            command_timeout=120.0
        )
        
        self._initialized = True
        logger.info(f"PostgreSQL connection pool initialized")
    
    @asynccontextmanager
    async def get_connection(self):
        """获取数据库连接"""
        if self._pool is None:
            await self._initialize()
        
        conn = None
        try:
            conn = await asyncio.wait_for(
                self._pool.acquire(), 
                timeout=30.0
            )
            yield conn
        except asyncio.TimeoutError:
            logger.error("Database connection acquire timeout")
            raise
        except asyncio.CancelledError:
            logger.warning("Database connection acquire cancelled")
            raise
        finally:
            if conn is not None and self._pool is not None:
                try:
                    await asyncio.wait_for(
                        self._pool.release(conn),
                        timeout=10.0
                    )
                except Exception as e:
                    logger.warning(f"Error releasing connection: {e}")
    
    async def close(self):
        """关闭连接池"""
        if self._pool:
            await self._pool.close()
            self._pool = None
            self._initialized = False
            logger.info("PostgreSQL connection pool closed")


# 兼容性函数 - 模拟aiosqlite接口
class PGCursor:
    """模拟SQLite cursor，用于execute返回"""
    
    def __init__(self, rows: List['PGRow'] = None, conn: 'PGConnection' = None):
        self._rows = rows or []
        self._conn = conn
        self._last_result = None
    
    async def fetchall(self):
        return self._rows
    
    async def fetchone(self):
        return self._rows[0] if self._rows else None
    
    async def execute(self, query: str, *args, **kwargs):
        """执行SQL并存储结果"""
        if self._conn:
            pg_query = self._conn._convert_query(query)
            params = args if args else ()
            if len(params) == 1 and isinstance(params[0], (tuple, list)):
                params = tuple(params[0])
            
            if pg_query.strip().upper().startswith('SELECT'):
                rows = await self._conn._conn.fetch(pg_query, *params)
                self._rows = [PGRow(row) for row in rows]
            else:
                await self._conn._conn.execute(pg_query, *params)
                self._rows = []
        return self


class PGConnection:
    """PostgreSQL连接包装器，模拟aiosqlite接口"""
    
    def __init__(self, conn: asyncpg.Connection, pool: asyncpg.Pool = None):
        self._conn = conn
        self._pool = pool
    
    async def cursor(self):
        """返回PGCursor以支持cursor模式"""
        return PGCursor(conn=self)
    
    async def execute(self, query: str, *args, **kwargs):
        """执行SQL语句，返回兼容cursor对象"""
        pg_query = self._convert_query(query)
        
        if args:
            if len(args) == 1 and isinstance(args[0], (tuple, list)):
                params = tuple(args[0])
            else:
                params = args
            # 对于SELECT查询，返回带fetchall的cursor对象
            if pg_query.strip().upper().startswith('SELECT'):
                rows = await self._conn.fetch(pg_query, *params)
                return PGCursor([PGRow(row) for row in rows])
            else:
                result = await self._conn.execute(pg_query, *params)
                return result
        else:
            # 对于SELECT查询，返回带fetchall的cursor对象
            if pg_query.strip().upper().startswith('SELECT'):
                rows = await self._conn.fetch(pg_query)
                return PGCursor([PGRow(row) for row in rows])
            else:
                result = await self._conn.execute(pg_query)
                return result
    
    async def fetch(self, query: str, *args, **kwargs):
        """查询多行"""
        pg_query = self._convert_query(query)
        params = self._normalize_args(args)
        rows = await self._conn.fetch(pg_query, *params)
        return [PGRow(row) for row in rows]
    
    async def fetchone(self, query: str, *args, **kwargs):
        """查询单行"""
        pg_query = self._convert_query(query)
        params = self._normalize_args(args)
        row = await self._conn.fetchrow(pg_query, *params)
        return PGRow(row) if row else None
    
    async def fetchrow(self, query: str, *args, **kwargs):
        """查询单行（别名）"""
        return await self.fetchone(query, *args, **kwargs)
    
    async def fetchval(self, query: str, *args, **kwargs):
        """查询单个值"""
        pg_query = self._convert_query(query)
        params = self._normalize_args(args)
        return await self._conn.fetchval(pg_query, *params)
    
    def _normalize_args(self, args):
        """规范化参数：处理单参数tuple/list的情况"""
        if len(args) == 1 and isinstance(args[0], (tuple, list)):
            return tuple(args[0])
        return args
    
    async def executemany(self, query: str, args_list):
        """批量执行"""
        pg_query = self._convert_query(query)
        await self._conn.executemany(pg_query, args_list)
    
    async def executescript(self, script: str):
        """执行脚本（分割并逐个执行）"""
        statements = [s.strip() for s in script.split(';') if s.strip()]
        for stmt in statements:
            if stmt:
                try:
                    await self._conn.execute(stmt)
                except Exception as e:
                    logger.warning(f"Script statement failed: {e}")
    
    async def commit(self):
        """提交事务（PostgreSQL自动提交）"""
        pass
    
    async def rollback(self):
        """回滚事务"""
        pass
    
    async def close(self):
        """释放连接回连接池"""
        if self._pool and self._conn:
            await self._pool.release(self._conn)
            self._conn = None
    
    def _convert_query(self, query: str) -> str:
        """转换SQLite查询到PostgreSQL"""
        # 替换?占位符为$1, $2等
        if '?' in query:
            parts = query.split('?')
            result = parts[0]
            for i, part in enumerate(parts[1:], 1):
                result += f'${i}{part}'
            return result
        return query


class PGRow:
    """PostgreSQL行包装器，模拟aiosqlite.Row"""
    
    def __init__(self, row: asyncpg.Record):
        self._row = row
    
    def __getitem__(self, key):
        return self._row[key]
    
    def __iter__(self):
        return iter(self._row.values())
    
    def keys(self):
        return self._row.keys()
    
    def values(self):
        return self._row.values()
    
    def __repr__(self):
        return f"PGRow({dict(self._row)})"


@asynccontextmanager
async def get_db():
    """获取数据库连接上下文管理器"""
    pool = await PostgreSQLConnectionPool.get_instance()
    async with pool.get_connection() as conn:
        yield PGConnection(conn, pool._pool)


async def get_db_connection():
    """获取数据库连接（直接返回连接对象，兼容SQLite接口）
    注意：调用者需要手动释放连接，建议使用 get_db() 上下文管理器
    """
    pool = await PostgreSQLConnectionPool.get_instance()
    conn = await pool._pool.acquire()
    return PGConnection(conn, pool._pool)


async def init_db():
    """初始化数据库（PostgreSQL已在迁移时创建表）"""
    logger.info("PostgreSQL database already initialized during migration")
