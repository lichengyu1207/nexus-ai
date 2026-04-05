"""
数据库连接池模块
实现高并发数据库连接管理
"""
import aiosqlite
import asyncio
from typing import Optional, List, Dict, Any
from pathlib import Path
from contextlib import asynccontextmanager
import logging
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent / "data" / "property-ai.db"

class DatabaseConnectionPool:
    """
    数据库连接池管理器
    支持高并发场景下的连接复用
    """
    
    _instance: Optional['DatabaseConnectionPool'] = None
    _lock = asyncio.Lock()
    
    def __init__(self, max_connections: int = 20, db_path: Path = DB_PATH):
        self.max_connections = max_connections
        self.db_path = db_path
        self._pool: asyncio.Queue = asyncio.Queue(maxsize=max_connections)
        self._current_connections = 0
        self._initialized = False
    
    @classmethod
    async def get_instance(cls) -> 'DatabaseConnectionPool':
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
            
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        for _ in range(min(5, self.max_connections)):
            conn = await self._create_connection()
            await self._pool.put(conn)
            self._current_connections += 1
        
        self._initialized = True
        logger.info(f"Database connection pool initialized with {self._current_connections} connections")
    
    async def _create_connection(self) -> aiosqlite.Connection:
        """创建新的数据库连接"""
        conn = await aiosqlite.connect(str(self.db_path), timeout=120.0)
        conn.row_factory = aiosqlite.Row
        
        await conn.execute("PRAGMA journal_mode=WAL")
        await conn.execute("PRAGMA busy_timeout=300000")
        await conn.execute("PRAGMA synchronous=NORMAL")
        await conn.execute("PRAGMA cache_size=50000")
        await conn.execute("PRAGMA locking_mode=NORMAL")
        await conn.execute("PRAGMA temp_store=MEMORY")
        await conn.execute("PRAGMA mmap_size=536870912")
        await conn.execute("PRAGMA wal_autocheckpoint=1000")
        
        return conn
    
    @asynccontextmanager
    async def get_connection(self):
        """获取数据库连接"""
        conn = None
        try:
            if self._pool.empty() and self._current_connections < self.max_connections:
                async with self._lock:
                    if self._current_connections < self.max_connections:
                        conn = await self._create_connection()
                        self._current_connections += 1
                        logger.debug(f"Created new connection, total: {self._current_connections}")
            
            if conn is None:
                try:
                    conn = await asyncio.wait_for(self._pool.get(), timeout=30.0)
                except asyncio.TimeoutError:
                    conn = await self._create_connection()
                    self._current_connections += 1
                    logger.warning(f"Connection pool exhausted, created emergency connection, total: {self._current_connections}")
            
            yield conn
            
        finally:
            if conn is not None:
                try:
                    await self._pool.put(conn)
                except asyncio.QueueFull:
                    await conn.close()
                    self._current_connections -= 1
    
    async def close_all(self):
        """关闭所有连接"""
        while not self._pool.empty():
            conn = await self._pool.get()
            await conn.close()
        self._current_connections = 0
        self._initialized = False
        logger.info("All database connections closed")

db_pool: Optional[DatabaseConnectionPool] = None

async def get_pool() -> DatabaseConnectionPool:
    """获取数据库连接池"""
    global db_pool
    if db_pool is None:
        db_pool = await DatabaseConnectionPool.get_instance()
    return db_pool

@asynccontextmanager
async def get_db():
    """获取数据库连接的上下文管理器"""
    pool = await get_pool()
    async with pool.get_connection() as conn:
        yield conn

async def get_db_connection() -> aiosqlite.Connection:
    """获取数据库连接 (兼容旧代码)"""
    pool = await get_pool()
    return await pool._create_connection()

async def init_db() -> None:
    """初始化数据库表"""
    pool = await get_pool()
    async with pool.get_connection() as conn:
        await _create_tables(conn)
        logger.info("Database initialized successfully with all tables")

async def _create_tables(conn: aiosqlite.Connection):
    """创建所有数据库表"""
    await conn.executescript("""
        -- 用户表
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            full_name TEXT,
            avatar_url TEXT,
            role TEXT DEFAULT 'user',
            is_admin INTEGER DEFAULT 0,
            permissions TEXT DEFAULT '{}',
            theme TEXT DEFAULT 'system',
            language TEXT DEFAULT 'zh',
            notification_preferences TEXT DEFAULT '{}',
            ab_test_group TEXT DEFAULT 'control',
            integral INTEGER DEFAULT 3,
            source TEXT,
            referred_by TEXT,
            referred_by_other TEXT,
            is_active INTEGER DEFAULT 1,
            real_name TEXT,
            id_number TEXT,
            real_name_verified INTEGER DEFAULT 0,
            verified_at DATETIME,
            verify_method TEXT,
            membership_level TEXT DEFAULT 'free',
            membership_expires DATETIME,
            rating_level INTEGER DEFAULT 0,
            rating_updated_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        
        -- 创建索引
        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
        CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
        CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
    """)
    await conn.commit()
