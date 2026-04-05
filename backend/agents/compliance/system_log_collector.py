"""
系统日志采集智能体
集中采集各系统组件的日志
"""
import asyncio
import json
import logging
import re
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class LogLevel(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class LogSource(str, Enum):
    API_GATEWAY = "api_gateway"
    AGENT_RUNTIME = "agent_runtime"
    DATABASE = "database"
    CACHE = "cache"
    MESSAGE_QUEUE = "message_queue"
    FILE_SYSTEM = "file_system"
    EXTERNAL_SERVICE = "external_service"
    SECURITY = "security"


class SystemLog(BaseModel):
    log_id: str = Field(default_factory=lambda: str(uuid4()))
    source: LogSource
    level: LogLevel
    message: str
    raw_message: str = ""
    parsed_fields: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)
    hostname: Optional[str] = None
    service_name: Optional[str] = None
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class LogCollectorConfig(BaseModel):
    source: LogSource
    enabled: bool = True
    log_path: Optional[str] = None
    log_format: str = "json"
    batch_size: int = 100
    flush_interval: int = 5


class LogParser:
    PATTERNS = {
        "timestamp": [
            r'(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?)',
            r'(\d{2}/\d{2}/\d{4}\s\d{2}:\d{2}:\d{2})',
        ],
        "level": [
            r'\[(DEBUG|INFO|WARNING|WARN|ERROR|CRITICAL|FATAL)\]',
            r'(DEBUG|INFO|WARNING|WARN|ERROR|CRITICAL|FATAL):',
        ],
        "trace_id": [
            r'trace[_-]?id[:\s]+([a-f0-9-]+)',
            r'\[([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})\]',
        ],
        "ip_address": [
            r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})',
        ],
        "user_id": [
            r'user[_-]?id[:\s]+([a-zA-Z0-9_-]+)',
            r'用户[：:]\s*([a-zA-Z0-9_-]+)',
        ],
        "request_id": [
            r'request[_-]?id[:\s]+([a-zA-Z0-9_-]+)',
        ],
        "duration": [
            r'(?:duration|耗时|用时)[：:]\s*(\d+(?:\.\d+)?)\s*(ms|s|秒|毫秒)?',
        ],
        "error_code": [
            r'(?:error[_-]?code|错误码)[：:]\s*(\d+)',
        ],
    }
    
    LEVEL_MAPPING = {
        "DEBUG": LogLevel.DEBUG,
        "INFO": LogLevel.INFO,
        "WARNING": LogLevel.WARNING,
        "WARN": LogLevel.WARNING,
        "ERROR": LogLevel.ERROR,
        "CRITICAL": LogLevel.CRITICAL,
        "FATAL": LogLevel.CRITICAL,
    }
    
    def parse(self, raw_log: str, source: LogSource) -> SystemLog:
        parsed_fields = {}
        
        for field_name, patterns in self.PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, raw_log, re.IGNORECASE)
                if match:
                    parsed_fields[field_name] = match.group(1)
                    break
        
        level = LogLevel.INFO
        if "level" in parsed_fields:
            level = self.LEVEL_MAPPING.get(
                parsed_fields["level"].upper(),
                LogLevel.INFO
            )
        
        timestamp = datetime.now()
        if "timestamp" in parsed_fields:
            try:
                ts_str = parsed_fields["timestamp"]
                for fmt in [
                    "%Y-%m-%dT%H:%M:%S.%f",
                    "%Y-%m-%dT%H:%M:%S",
                    "%Y-%m-%d %H:%M:%S.%f",
                    "%Y-%m-%d %H:%M:%S",
                    "%d/%m/%Y %H:%M:%S",
                ]:
                    try:
                        timestamp = datetime.strptime(ts_str, fmt)
                        break
                    except ValueError:
                        continue
            except Exception:
                pass
        
        message = raw_log
        if len(raw_log) > 500:
            message = raw_log[:500] + "..."
        
        return SystemLog(
            source=source,
            level=level,
            message=message,
            raw_message=raw_log,
            parsed_fields=parsed_fields,
            timestamp=timestamp,
            trace_id=parsed_fields.get("trace_id"),
            tags=self._extract_tags(raw_log)
        )
    
    def _extract_tags(self, log: str) -> List[str]:
        tags = []
        
        tag_patterns = [
            (r'\[([a-zA-Z_]+)\]', "bracket"),
            (r'#(\w+)', "hashtag"),
        ]
        
        for pattern, _ in tag_patterns:
            matches = re.findall(pattern, log)
            tags.extend(matches[:3])
        
        return list(set(tags))[:5]


class LogBuffer:
    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.buffer: List[SystemLog] = []
        self._lock = asyncio.Lock()
    
    async def add(self, log: SystemLog):
        async with self._lock:
            self.buffer.append(log)
            
            if len(self.buffer) > self.max_size:
                self.buffer = self.buffer[-self.max_size:]
    
    async def add_batch(self, logs: List[SystemLog]):
        async with self._lock:
            self.buffer.extend(logs)
            
            if len(self.buffer) > self.max_size:
                self.buffer = self.buffer[-self.max_size:]
    
    async def get_batch(self, batch_size: int) -> List[SystemLog]:
        async with self._lock:
            if not self.buffer:
                return []
            
            batch = self.buffer[:batch_size]
            self.buffer = self.buffer[batch_size:]
            return batch
    
    async def peek(self, limit: int = 100) -> List[SystemLog]:
        return self.buffer[:limit]
    
    def size(self) -> int:
        return len(self.buffer)


class LogFilter:
    def __init__(self):
        self.level_filters: Dict[LogSource, LogLevel] = {}
        self.exclude_patterns: List[str] = []
        self.include_patterns: List[str] = []
    
    def set_level_filter(self, source: LogSource, min_level: LogLevel):
        level_order = {
            LogLevel.DEBUG: 0,
            LogLevel.INFO: 1,
            LogLevel.WARNING: 2,
            LogLevel.ERROR: 3,
            LogLevel.CRITICAL: 4,
        }
        self.level_filters[source] = min_level
    
    def add_exclude_pattern(self, pattern: str):
        self.exclude_patterns.append(pattern)
    
    def add_include_pattern(self, pattern: str):
        self.include_patterns.append(pattern)
    
    def filter(self, log: SystemLog) -> bool:
        if log.source in self.level_filters:
            min_level = self.level_filters[log.source]
            level_order = {
                LogLevel.DEBUG: 0,
                LogLevel.INFO: 1,
                LogLevel.WARNING: 2,
                LogLevel.ERROR: 3,
                LogLevel.CRITICAL: 4,
            }
            
            if level_order[log.level] < level_order[min_level]:
                return False
        
        for pattern in self.exclude_patterns:
            if re.search(pattern, log.message, re.IGNORECASE):
                return False
        
        if self.include_patterns:
            included = False
            for pattern in self.include_patterns:
                if re.search(pattern, log.message, re.IGNORECASE):
                    included = True
                    break
            
            if not included:
                return False
        
        return True


class SystemLogCollectorAgent:
    def __init__(
        self,
        agent_id: str,
        name: str = "SystemLogCollector",
        storage: Optional[Any] = None,
        audit_agent: Optional[Any] = None
    ):
        self.agent_id = agent_id
        self.name = name
        self.storage = storage
        self.audit_agent = audit_agent
        
        self.parser = LogParser()
        self.buffer = LogBuffer()
        self.filter = LogFilter()
        
        self.collector_configs: Dict[LogSource, LogCollectorConfig] = {}
        self._init_default_configs()
        
        self.flush_interval = 5
        self.batch_size = 100
        self._running = False
        
        self.logger = logging.getLogger(f"{__name__}.{agent_id}")
    
    def _init_default_configs(self):
        for source in LogSource:
            self.collector_configs[source] = LogCollectorConfig(source=source)
    
    async def initialize(self):
        self.logger.info(f"SystemLogCollectorAgent {self.agent_id} initialized")
    
    async def collect_log(
        self,
        raw_log: str,
        source: LogSource
    ) -> Optional[SystemLog]:
        config = self.collector_configs.get(source)
        if not config or not config.enabled:
            return None
        
        log = self.parser.parse(raw_log, source)
        
        if not self.filter.filter(log):
            return None
        
        await self.buffer.add(log)
        
        return log
    
    async def collect_batch(
        self,
        raw_logs: List[str],
        source: LogSource
    ) -> List[SystemLog]:
        logs = []
        
        for raw_log in raw_logs:
            log = await self.collect_log(raw_log, source)
            if log:
                logs.append(log)
        
        return logs
    
    async def flush(self) -> int:
        batch = await self.buffer.get_batch(self.batch_size)
        
        if not batch:
            return 0
        
        if self.storage:
            await self._store_logs(batch)
        
        if self.audit_agent:
            for log in batch:
                await self.audit_agent.log_system_event(
                    event_type="log_collected",
                    details={
                        "source": log.source.value,
                        "level": log.level.value,
                        "message_preview": log.message[:100]
                    }
                )
        
        self.logger.debug(f"Flushed {len(batch)} logs")
        
        return len(batch)
    
    async def _store_logs(self, logs: List[SystemLog]):
        pass
    
    async def query_logs(
        self,
        source: Optional[LogSource] = None,
        level: Optional[LogLevel] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        trace_id: Optional[str] = None,
        keyword: Optional[str] = None,
        limit: int = 100
    ) -> List[SystemLog]:
        logs = await self.buffer.peek(limit * 2)
        
        results = []
        for log in logs:
            if source and log.source != source:
                continue
            if level and log.level != level:
                continue
            if start_time and log.timestamp < start_time:
                continue
            if end_time and log.timestamp > end_time:
                continue
            if trace_id and log.trace_id != trace_id:
                continue
            if keyword and keyword.lower() not in log.message.lower():
                continue
            
            results.append(log)
            
            if len(results) >= limit:
                break
        
        return results
    
    async def get_error_logs(
        self,
        hours: int = 1,
        limit: int = 100
    ) -> List[SystemLog]:
        start_time = datetime.now() - timedelta(hours=hours)
        
        return await self.query_logs(
            level=LogLevel.ERROR,
            start_time=start_time,
            limit=limit
        )
    
    async def get_logs_by_trace(self, trace_id: str) -> List[SystemLog]:
        return await self.query_logs(trace_id=trace_id, limit=1000)
    
    async def get_log_statistics(
        self,
        hours: int = 1
    ) -> Dict[str, Any]:
        start_time = datetime.now() - timedelta(hours=hours)
        logs = await self.query_logs(start_time=start_time, limit=10000)
        
        by_source = {}
        by_level = {}
        by_hour = {}
        
        for log in logs:
            by_source[log.source.value] = by_source.get(log.source.value, 0) + 1
            by_level[log.level.value] = by_level.get(log.level.value, 0) + 1
            
            hour = log.timestamp.strftime("%Y-%m-%d %H:00")
            by_hour[hour] = by_hour.get(hour, 0) + 1
        
        return {
            "total_logs": len(logs),
            "by_source": by_source,
            "by_level": by_level,
            "by_hour": by_hour,
            "buffer_size": self.buffer.size()
        }
    
    def configure_collector(
        self,
        source: LogSource,
        enabled: Optional[bool] = None,
        batch_size: Optional[int] = None,
        flush_interval: Optional[int] = None
    ):
        config = self.collector_configs.get(source)
        if config:
            if enabled is not None:
                config.enabled = enabled
            if batch_size is not None:
                config.batch_size = batch_size
            if flush_interval is not None:
                config.flush_interval = flush_interval
    
    async def start_collection(self):
        self._running = True
        asyncio.create_task(self._collection_loop())
    
    async def stop_collection(self):
        self._running = False
        await self.flush()
    
    async def _collection_loop(self):
        while self._running:
            try:
                await self.flush()
                await asyncio.sleep(self.flush_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in collection loop: {e}")
                await asyncio.sleep(1)
    
    def get_statistics(self) -> Dict[str, Any]:
        return {
            "buffer_size": self.buffer.size(),
            "collectors": {
                source.value: {
                    "enabled": config.enabled,
                    "batch_size": config.batch_size
                }
                for source, config in self.collector_configs.items()
            }
        }
