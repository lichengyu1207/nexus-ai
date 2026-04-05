import asyncio
import hashlib
import aiohttp
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

class AtomicAction(ABC):
    """原子动作基类"""
    
    name: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    retry_policy: Dict[str, Any] = {"max_attempts": 3, "delay": 1}
    idempotent: bool = False
    
    @abstractmethod
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行动作"""
        raise NotImplementedError
    
    async def compensate(self, params: Dict[str, Any]) -> None:
        """补偿动作，用于回滚"""
        pass


class HttpAction(AtomicAction):
    """HTTP请求动作"""
    
    def __init__(self):
        self.name = "http_request"
        self.input_schema = {
            "type": "object",
            "properties": {
                "url": {"type": "string"},
                "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE"]},
                "headers": {"type": "object"},
                "body": {"type": "object"}
            },
            "required": ["url", "method"]
        }
        self.output_schema = {
            "type": "object",
            "properties": {
                "status_code": {"type": "integer"},
                "body": {"type": "object"},
                "headers": {"type": "object"}
            }
        }
        self.retry_policy = {"max_attempts": 3, "delay": 1}
        self.idempotent = False
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行HTTP请求"""
        url = params["url"]
        method = params["method"]
        headers = params.get("headers", {})
        body = params.get("body")
        
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method=method,
                url=url,
                headers=headers,
                json=body if body else None
            ) as response:
                return {
                    "status_code": response.status,
                    "body": await response.json() if response.content_type == "application/json" else await response.text(),
                    "headers": dict(response.headers)
                }


class SqlQueryAction(AtomicAction):
    """SQL查询动作"""
    
    def __init__(self, db_session):
        self.name = "sql_query"
        self.db_session = db_session
        self.input_schema = {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "params": {"type": "object"}
            },
            "required": ["query"]
        }
        self.output_schema = {
            "type": "object",
            "properties": {
                "rows": {"type": "array"},
                "row_count": {"type": "integer"}
            }
        }
        self.retry_policy = {"max_attempts": 3, "delay": 1}
        self.idempotent = True
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行SQL查询"""
        query = params["query"]
        query_params = params.get("params", {})
        
        # 只允许SELECT查询
        if not query.strip().upper().startswith("SELECT"):
            raise ValueError("只允许执行SELECT查询")
        
        result = self.db_session.execute(query, query_params)
        rows = result.fetchall()
        
        return {
            "rows": [dict(row._mapping) for row in rows],
            "row_count": len(rows)
        }


class FileWriteAction(AtomicAction):
    """文件写入动作"""
    
    def __init__(self):
        self.name = "file_write"
        self.input_schema = {
            "type": "object",
            "properties": {
                "file_path": {"type": "string"},
                "content": {"type": "string"},
                "mode": {"type": "string", "enum": ["write", "append"]}
            },
            "required": ["file_path", "content"]
        }
        self.output_schema = {
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "bytes_written": {"type": "integer"},
                "content_hash": {"type": "string"}
            }
        }
        self.retry_policy = {"max_attempts": 3, "delay": 1}
        self.idempotent = True
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行文件写入"""
        file_path = params["file_path"]
        content = params["content"]
        mode = params.get("mode", "write")
        
        # 计算内容哈希，用于幂等性检查
        content_hash = hashlib.md5(content.encode()).hexdigest()
        
        # 写入文件
        write_mode = "w" if mode == "write" else "a"
        with open(file_path, write_mode, encoding="utf-8") as f:
            bytes_written = f.write(content)
        
        return {
            "success": True,
            "bytes_written": bytes_written,
            "content_hash": content_hash
        }
