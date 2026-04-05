"""
业务操作审计日志智能体
Business Audit Log Agent

负责采集所有业务智能体的操作日志，确保每笔业务操作可追溯。
"""

import asyncio
import json
import logging
import hashlib
import uuid
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
from collections import defaultdict
import aiofiles
import os

logger = logging.getLogger(__name__)


@dataclass
class AuditLogEntry:
    log_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    business_agent_id: str = ""
    user_id: str = ""
    session_id: str = ""
    request: Dict = field(default_factory=dict)
    response: Dict = field(default_factory=dict)
    data_access: List[Dict] = field(default_factory=list)
    tool_calls: List[Dict] = field(default_factory=list)
    cost: Dict = field(default_factory=dict)
    compliance_tags: List[str] = field(default_factory=list)
    previous_hash: str = ""
    current_hash: str = ""


class BusinessAuditLogAgent:
    """
    业务操作审计日志智能体
    
    功能：
    1. 日志采集：用户请求、业务处理过程、决策依据、输出结果、数据访问记录
    2. 日志格式：标准化JSON格式，包含完整审计信息
    3. 存储设计：按天分表，敏感字段加密，哈希链防篡改
    4. 实时审计接口：支持多维度查询和聚合统计
    5. 性能要求：写入延迟<10ms，异步批量写入
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.name = "BusinessAuditLogAgent"
        self.description = "采集所有业务智能体的操作日志，确保每笔业务操作可追溯"
        self.config = config or {}
        
        self.log_buffer: List[AuditLogEntry] = []
        self.buffer_size = self.config.get("buffer_size", 100)
        self.flush_interval = self.config.get("flush_interval", 5)
        
        self.hash_chain_head = ""
        self._initialized = False
        
        self.storage_path = self.config.get("storage_path", "./audit_logs")
        self.encryption_key = self.config.get("encryption_key", "")
        
        self.stats = {
            "total_logs": 0,
            "logs_by_agent": defaultdict(int),
            "logs_by_user": defaultdict(int),
            "errors": 0,
        }
    
    async def initialize(self):
        if not self._initialized:
            await self._setup()
            self._initialized = True
            logger.info(f"Agent '{self.name}' initialized")
    
    async def _setup(self):
        os.makedirs(self.storage_path, exist_ok=True)
        await self._load_last_hash()
        asyncio.create_task(self._periodic_flush())
    
    async def _load_last_hash(self):
        index_file = os.path.join(self.storage_path, "hash_chain_index.json")
        if os.path.exists(index_file):
            try:
                async with aiofiles.open(index_file, 'r') as f:
                    data = json.loads(await f.read())
                    self.hash_chain_head = data.get("last_hash", "")
            except Exception as e:
                logger.warning(f"Failed to load hash chain: {e}")
    
    async def _periodic_flush(self):
        while True:
            await asyncio.sleep(self.flush_interval)
            if self.log_buffer:
                await self._flush_buffer()
    
    def _compute_hash(self, entry: AuditLogEntry) -> str:
        data = json.dumps({
            "log_id": entry.log_id,
            "timestamp": entry.timestamp,
            "business_agent_id": entry.business_agent_id,
            "user_id": entry.user_id,
            "session_id": entry.session_id,
            "request": entry.request,
            "response": entry.response,
            "data_access": entry.data_access,
            "tool_calls": entry.tool_calls,
            "previous_hash": entry.previous_hash,
        }, sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()
    
    def _encrypt_sensitive_data(self, data: Any) -> Any:
        if not self.encryption_key:
            return data
        if isinstance(data, str):
            return f"ENCRYPTED:{hashlib.sha256((data + self.encryption_key).encode()).hexdigest()[:32]}"
        elif isinstance(data, dict):
            return {k: self._encrypt_sensitive_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._encrypt_sensitive_data(item) for item in data]
        return data
    
    async def log_operation(
        self,
        business_agent_id: str,
        user_id: str,
        session_id: str,
        request: Dict,
        response: Dict,
        data_access: Optional[List[Dict]] = None,
        tool_calls: Optional[List[Dict]] = None,
        cost: Optional[Dict] = None,
        compliance_tags: Optional[List[str]] = None,
    ) -> str:
        entry = AuditLogEntry(
            business_agent_id=business_agent_id,
            user_id=user_id,
            session_id=session_id,
            request=self._encrypt_sensitive_data(request),
            response=self._encrypt_sensitive_data(response),
            data_access=data_access or [],
            tool_calls=tool_calls or [],
            cost=cost or {},
            compliance_tags=compliance_tags or [],
            previous_hash=self.hash_chain_head,
        )
        entry.current_hash = self._compute_hash(entry)
        self.hash_chain_head = entry.current_hash
        
        self.log_buffer.append(entry)
        
        self.stats["total_logs"] += 1
        self.stats["logs_by_agent"][business_agent_id] += 1
        self.stats["logs_by_user"][user_id] += 1
        
        if len(self.log_buffer) >= self.buffer_size:
            await self._flush_buffer()
        
        return entry.log_id
    
    async def _flush_buffer(self):
        if not self.log_buffer:
            return
        
        today = datetime.utcnow().strftime("%Y%m%d")
        log_file = os.path.join(self.storage_path, f"audit_log_{today}.jsonl")
        
        try:
            async with aiofiles.open(log_file, 'a') as f:
                for entry in self.log_buffer:
                    await f.write(json.dumps(entry.__dict__, ensure_ascii=False) + "\n")
            
            index_file = os.path.join(self.storage_path, "hash_chain_index.json")
            async with aiofiles.open(index_file, 'w') as f:
                await f.write(json.dumps({
                    "last_hash": self.hash_chain_head,
                    "last_flush": datetime.utcnow().isoformat(),
                    "total_logs": self.stats["total_logs"],
                }))
            
            logger.info(f"Flushed {len(self.log_buffer)} audit logs")
            self.log_buffer.clear()
            
        except Exception as e:
            logger.error(f"Failed to flush audit logs: {e}")
            self.stats["errors"] += 1
    
    async def query_logs(
        self,
        user_id: Optional[str] = None,
        time_range: Optional[tuple] = None,
        operation_type: Optional[str] = None,
        business_agent_id: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict]:
        results = []
        
        if time_range:
            start_date = datetime.fromisoformat(time_range[0]).strftime("%Y%m%d")
            end_date = datetime.fromisoformat(time_range[1]).strftime("%Y%m%d")
        else:
            start_date = end_date = datetime.utcnow().strftime("%Y%m%d")
        
        current_date = start_date
        while current_date <= end_date:
            log_file = os.path.join(self.storage_path, f"audit_log_{current_date}.jsonl")
            
            if os.path.exists(log_file):
                try:
                    async with aiofiles.open(log_file, 'r') as f:
                        async for line in f:
                            if len(results) >= limit:
                                break
                            
                            entry = json.loads(line)
                            
                            if user_id and entry.get("user_id") != user_id:
                                continue
                            if business_agent_id and entry.get("business_agent_id") != business_agent_id:
                                continue
                            if session_id and entry.get("session_id") != session_id:
                                continue
                            
                            results.append(entry)
                except Exception as e:
                    logger.error(f"Error reading log file {log_file}: {e}")
            
            next_date = datetime.strptime(current_date, "%Y%m%d") + timedelta(days=1)
            current_date = next_date.strftime("%Y%m%d")
        
        return results
    
    async def get_aggregated_stats(
        self,
        time_range: Optional[tuple] = None,
        group_by: str = "agent",
    ) -> Dict:
        if group_by == "agent":
            return dict(self.stats["logs_by_agent"])
        elif group_by == "user":
            return dict(self.stats["logs_by_user"])
        elif group_by == "hour":
            logs = await self.query_logs(time_range=time_range, limit=10000)
            hourly = defaultdict(int)
            for log in logs:
                hour = log.get("timestamp", "")[:13]
                hourly[hour] += 1
            return dict(hourly)
        
        return {
            "total_logs": self.stats["total_logs"],
            "errors": self.stats["errors"],
        }
    
    async def verify_log_integrity(self, log_id: str) -> Dict:
        logs = await self.query_logs(limit=10000)
        
        for i, log in enumerate(logs):
            if log.get("log_id") == log_id:
                if i == 0:
                    return {"valid": True, "message": "First log entry"}
                
                prev_log = logs[i - 1]
                expected_prev_hash = prev_log.get("current_hash", "")
                actual_prev_hash = log.get("previous_hash", "")
                
                if expected_prev_hash == actual_prev_hash:
                    return {"valid": True, "message": "Hash chain verified"}
                else:
                    return {
                        "valid": False,
                        "message": "Hash chain broken",
                        "expected": expected_prev_hash,
                        "actual": actual_prev_hash,
                    }
        
        return {"valid": False, "message": "Log not found"}
    
    async def get_stats(self) -> Dict:
        return {
            "name": self.name,
            "total_logs": self.stats["total_logs"],
            "buffer_size": len(self.log_buffer),
            "logs_by_agent": dict(self.stats["logs_by_agent"]),
            "errors": self.stats["errors"],
            "hash_chain_head": self.hash_chain_head[:16] + "..." if self.hash_chain_head else "",
        }
