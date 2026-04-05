"""
数据库配置模块
提供PostgreSQL数据库连接和会话管理
兼容Python 3.10.19
"""

import os
import psycopg2
from psycopg2 import pool
from typing import Optional, Generator, List, Dict, Any
from contextlib import contextmanager
from config import settings


class DatabaseConfig:
    """PostgreSQL数据库配置类"""
    
    def __init__(self):
        self.database_url = settings.database_url
        self.pool_size = settings.database_pool_size
        self._connection_pool: Optional[pool.ThreadedConnectionPool] = None
        self._initialize_database()
    
    def _parse_database_url(self) -> dict:
        """解析数据库URL"""
        # postgresql://postgres:147258@Zxcvbnm@localhost:5432/eraser_db
        try:
            # 移除postgresql://前缀
            url = self.database_url.replace("postgresql://", "")
            
            # 分离用户名密码和主机端口数据库
            auth_part, host_part = url.split("@")
            
            # 解析用户名和密码
            username, password = auth_part.split(":")
            
            # 解析主机、端口和数据库名
            host_port, database = host_part.split("/")
            if ":" in host_port:
                host, port = host_port.split(":")
                port = int(port)
            else:
                host = host_port
                port = 5432
            
            return {
                "host": host,
                "port": port,
                "database": database,
                "user": username,
                "password": password
            }
        except Exception as e:
            print(f"解析数据库URL失败: {e}")
            # 返回默认配置
            return {
                "host": "localhost",
                "port": 5432,
                "database": "eraser_db",
                "user": "postgres",
                "password": "147258@Zxcvbnm"
            }
    
    def _initialize_database(self):
        """初始化数据库连接池和表结构"""
        try:
            # 解析数据库配置
            db_config = self._parse_database_url()
            
            # 创建连接池
            self._connection_pool = pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=self.pool_size,
                **db_config
            )
            
            # 创建表结构
            self._create_tables()
            
            print(f"PostgreSQL数据库连接池初始化完成: {db_config['host']}:{db_config['port']}/{db_config['database']}")
        except Exception as e:
            print(f"数据库初始化失败: {e}")
            raise
    
    def _create_tables(self):
        """创建数据库表"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 创建memories表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id VARCHAR(255) PRIMARY KEY,
                    user_message TEXT NOT NULL,
                    agent_reply TEXT NOT NULL,
                    agent VARCHAR(50) NOT NULL,
                    emotion_tag VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建reports表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reports (
                    report_id VARCHAR(255) PRIMARY KEY,
                    user_message TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建索引
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_memories_created_at 
                ON memories(created_at)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_memories_agent 
                ON memories(agent)
            """)
            
            conn.commit()
    
    @contextmanager
    def get_connection(self) -> Generator:
        """获取数据库连接"""
        if not self._connection_pool:
            raise Exception("数据库连接池未初始化")
        
        conn = None
        try:
            conn = self._connection_pool.getconn()
            yield conn
        finally:
            if conn:
                self._connection_pool.putconn(conn)
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """执行查询并返回结果"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            # 获取列名
            columns = [desc[0] for desc in cursor.description]
            
            # 转换为字典列表
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            return results
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """执行更新操作"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount
    
    def close_all(self):
        """关闭所有连接"""
        if self._connection_pool:
            self._connection_pool.closeall()
            self._connection_pool = None


# 全局数据库配置实例
db_config = DatabaseConfig()
