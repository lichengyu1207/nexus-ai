"""
数据库连接池模块
实现SQLite连接池以提高并发性能
"""
import aiosqlite
import asyncio
from typing import Optional, List, Dict, Any
from pathlib import Path
from contextlib import asynccontextmanager
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent / "data" / "property-ai.db"

class DatabaseConnectionPool:
    """数据库连接池"""
    
    _instance: Optional['DatabaseConnectionPool'] = None
    _lock = asyncio.Lock()
    
    def __init__(self, pool_size: int = 20, max_overflow: int = 10):
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self._pool: List[aiosqlite.Connection] = []
        self._in_use: Dict[int, aiosqlite.Connection] = {}
        self._semaphore = asyncio.Semaphore(pool_size + max_overflow)
        self._initialized = False
    
    @classmethod
    async def get_instance(cls, pool_size: int = 20, max_overflow: int = 10) -> 'DatabaseConnectionPool':
        """获取单例实例"""
        if cls._instance is None:
            async with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(pool_size, max_overflow)
                    await cls._instance._initialize()
        return cls._instance
    
    async def _initialize(self):
        """初始化连接池"""
        if self._initialized:
            return
        
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        # 预创建连接
        for _ in range(min(5, self.pool_size)):
            conn = await self._create_connection()
            self._pool.append(conn)
        
        self._initialized = True
        logger.info(f"Database connection pool initialized with {len(self._pool)} connections")
    
    async def _create_connection(self) -> aiosqlite.Connection:
        """创建新连接"""
        conn = await aiosqlite.connect(str(DB_PATH))
        conn.row_factory = aiosqlite.Row
        
        # 优化SQLite性能
        await conn.execute("PRAGMA journal_mode=WAL")
        await conn.execute("PRAGMA synchronous=NORMAL")
        await conn.execute("PRAGMA cache_size=10000")
        await conn.execute("PRAGMA temp_store=MEMORY")
        await conn.execute("PRAGMA mmap_size=268435456")
        
        return conn
    
    async def acquire(self) -> aiosqlite.Connection:
        """获取连接"""
        await self._semaphore.acquire()
        
        # 尝试从池中获取
        if self._pool:
            conn = self._pool.pop()
            conn_id = id(conn)
            self._in_use[conn_id] = conn
            return conn
        
        # 创建新连接
        conn = await self._create_connection()
        conn_id = id(conn)
        self._in_use[conn_id] = conn
        return conn
    
    async def release(self, conn: aiosqlite.Connection):
        """释放连接"""
        conn_id = id(conn)
        if conn_id in self._in_use:
            del self._in_use[conn_id]
        
        # 如果池未满，放回池中
        if len(self._pool) < self.pool_size:
            self._pool.append(conn)
        else:
            await conn.close()
        
        self._semaphore.release()
    
    async def close_all(self):
        """关闭所有连接"""
        for conn in self._pool:
            await conn.close()
        self._pool.clear()
        
        for conn in self._in_use.values():
            await conn.close()
        self._in_use.clear()
        
        self._initialized = False
        logger.info("All database connections closed")

# 全局连接池实例
_pool: Optional[DatabaseConnectionPool] = None

async def init_pool(pool_size: int = 20, max_overflow: int = 10):
    """初始化连接池"""
    global _pool
    _pool = await DatabaseConnectionPool.get_instance(pool_size, max_overflow)
    return _pool

async def get_pool() -> DatabaseConnectionPool:
    """获取连接池"""
    global _pool
    if _pool is None:
        _pool = await DatabaseConnectionPool.get_instance()
    return _pool

@asynccontextmanager
async def get_pooled_connection():
    """获取池化连接的上下文管理器"""
    pool = await get_pool()
    conn = await pool.acquire()
    try:
        yield conn
    finally:
        await pool.release(conn)

async def close_pool():
    """关闭连接池"""
    global _pool
    if _pool:
        await _pool.close_all()
        _pool = None
