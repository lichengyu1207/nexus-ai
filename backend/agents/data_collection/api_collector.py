"""
API采集智能体
API Collector Agent

从各类API采集数据
"""

import os
import json
import time
import logging
import threading
import uuid
import asyncio
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import deque, defaultdict
import random

from .data_collector import DataCollectorAgent, DataSourceType

logger = logging.getLogger(__name__)


class APIProtocol(Enum):
    REST = "rest"
    GRAPHQL = "graphql"
    WEBSOCKET = "websocket"
    GRPC = "grpc"


@dataclass
class APIConfig:
    endpoint: str
    protocol: APIProtocol = APIProtocol.REST
    method: str = "GET"
    headers: Dict[str, str] = field(default_factory=dict)
    api_key: Optional[str] = None
    api_key_header: str = "X-API-Key"
    rate_limit_per_second: float = 10.0
    timeout_seconds: float = 30.0
    retry_count: int = 3
    cache_ttl_seconds: float = 300.0
    subscription_query: Optional[str] = None
    pagination_type: Optional[str] = None
    pagination_param: str = "page"
    
    def to_dict(self) -> Dict:
        return {
            "endpoint": self.endpoint,
            "protocol": self.protocol.value,
            "method": self.method,
            "rate_limit": self.rate_limit_per_second,
            "timeout": self.timeout_seconds,
            "cache_ttl": self.cache_ttl_seconds,
        }


@dataclass
class APIResponse:
    request_id: str
    endpoint: str
    status_code: int
    data: Any
    headers: Dict
    response_time_ms: float
    cached: bool = False
    error: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict:
        return {
            "request_id": self.request_id,
            "endpoint": self.endpoint,
            "status_code": self.status_code,
            "data_type": type(self.data).__name__,
            "response_time_ms": self.response_time_ms,
            "cached": self.cached,
            "error": self.error,
            "timestamp": self.timestamp,
        }


class RateLimiter:
    """
    令牌桶限流器
    """
    
    def __init__(self, rate_per_second: float, burst_size: int = 10):
        self.rate = rate_per_second
        self.burst_size = burst_size
        self.tokens = burst_size
        self.last_update = time.time()
        self._lock = asyncio.Lock()
    
    async def acquire(self, tokens: int = 1) -> bool:
        async with self._lock:
            now = time.time()
            elapsed = now - self.last_update
            self.tokens = min(
                self.burst_size,
                self.tokens + elapsed * self.rate
            )
            self.last_update = now
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    async def wait_for_token(self, tokens: int = 1):
        while not await self.acquire(tokens):
            wait_time = (tokens - self.tokens) / self.rate
            await asyncio.sleep(max(0.01, wait_time))


class ResponseCache:
    """
    响应缓存
    """
    
    def __init__(self, default_ttl: float = 300.0):
        self.default_ttl = default_ttl
        self.cache: Dict[str, Tuple[Any, float, float]] = {}
        self._lock = threading.RLock()
    
    def _get_cache_key(self, endpoint: str, params: Dict) -> str:
        key_data = f"{endpoint}:{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, endpoint: str, params: Dict) -> Optional[Tuple[Any, bool]]:
        with self._lock:
            key = self._get_cache_key(endpoint, params)
            
            if key in self.cache:
                data, timestamp, ttl = self.cache[key]
                
                if time.time() - timestamp < ttl:
                    return data, True
                else:
                    del self.cache[key]
            
            return None, False
    
    def set(self, endpoint: str, params: Dict, data: Any, ttl: Optional[float] = None):
        with self._lock:
            key = self._get_cache_key(endpoint, params)
            self.cache[key] = (data, time.time(), ttl or self.default_ttl)
    
    def invalidate(self, endpoint: str, params: Optional[Dict] = None):
        with self._lock:
            if params:
                key = self._get_cache_key(endpoint, params)
                if key in self.cache:
                    del self.cache[key]
            else:
                keys_to_delete = [
                    k for k in self.cache
                    if k.startswith(hashlib.md5(endpoint.encode()).hexdigest()[:8])
                ]
                for key in keys_to_delete:
                    del self.cache[key]
    
    def clear(self):
        with self._lock:
            self.cache.clear()


class APIKeyManager:
    """
    API密钥管理器
    """
    
    def __init__(self):
        self.api_keys: Dict[str, List[Dict]] = defaultdict(list)
        self.key_usage: Dict[str, Dict] = {}
        self._lock = threading.RLock()
    
    def add_key(self, service: str, api_key: str, rate_limit: int = 1000, daily_limit: int = 10000):
        with self._lock:
            key_id = hashlib.md5(f"{service}:{api_key}".encode()).hexdigest()[:8]
            
            self.api_keys[service].append({
                "key_id": key_id,
                "api_key": api_key,
                "rate_limit": rate_limit,
                "daily_limit": daily_limit,
                "usage_today": 0,
                "last_reset": time.time(),
                "is_active": True,
            })
            
            self.key_usage[key_id] = {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
            }
    
    def get_key(self, service: str) -> Optional[Dict]:
        with self._lock:
            if service not in self.api_keys:
                return None
            
            available_keys = [
                k for k in self.api_keys[service]
                if k["is_active"] and k["usage_today"] < k["daily_limit"]
            ]
            
            if not available_keys:
                return None
            
            selected = min(available_keys, key=lambda k: k["usage_today"])
            selected["usage_today"] += 1
            
            return selected
    
    def report_key_error(self, service: str, key_id: str, error_type: str):
        with self._lock:
            for key in self.api_keys.get(service, []):
                if key["key_id"] == key_id:
                    if error_type in ["invalid", "expired"]:
                        key["is_active"] = False
                    elif error_type == "rate_limited":
                        pass
                    
                    self.key_usage[key_id]["failed_requests"] += 1
                    break


class APICollectorAgent(DataCollectorAgent):
    """
    API采集智能体
    
    从各类API采集数据：
    1. 支持多种协议（REST、GraphQL、WebSocket）
    2. API密钥管理
    3. 限流处理
    4. 响应缓存
    5. 错误恢复
    """
    
    def __init__(
        self,
        agent_id: str,
        config: APIConfig,
        sample_repository: Optional[Any] = None,
        blackboard: Optional[Any] = None,
        memory_agent: Optional[Any] = None,
        compliance_checker: Optional[Any] = None,
    ):
        super().__init__(
            agent_id=agent_id,
            source_type=DataSourceType.API,
            target_url=config.endpoint,
            sample_repository=sample_repository,
            blackboard=blackboard,
            memory_agent=memory_agent,
            compliance_checker=compliance_checker,
        )
        
        self.config = config
        self.rate_limiter = RateLimiter(config.rate_limit_per_second)
        self.cache = ResponseCache(config.cache_ttl_seconds)
        self.key_manager = APIKeyManager()
        
        self.websocket_connections: Dict[str, Any] = {}
        self.subscriptions: Dict[str, asyncio.Queue] = {}
        
        self.stats.update({
            "api_calls": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "rate_limit_waits": 0,
            "websocket_messages": 0,
        })
    
    async def collect(self) -> Any:
        """
        执行API数据采集
        """
        if self.config.protocol == APIProtocol.WEBSOCKET:
            return await self._collect_websocket()
        elif self.config.protocol == APIProtocol.GRAPHQL:
            return await self._collect_graphql()
        else:
            return await self._collect_rest()
    
    async def _collect_rest(self, params: Optional[Dict] = None) -> APIResponse:
        """
        REST API采集
        """
        params = params or {}
        
        cached_data, is_cached = self.cache.get(self.config.endpoint, params)
        if is_cached:
            self.stats["cache_hits"] += 1
            return APIResponse(
                request_id=f"cached_{uuid.uuid4().hex[:8]}",
                endpoint=self.config.endpoint,
                status_code=200,
                data=cached_data,
                headers={},
                response_time_ms=0,
                cached=True,
            )
        
        self.stats["cache_misses"] += 1
        
        await self.rate_limiter.acquire()
        
        headers = self._prepare_headers()
        
        start_time = time.time()
        
        for attempt in range(self.config.retry_count):
            try:
                import aiohttp
                
                timeout = aiohttp.ClientTimeout(total=self.config.timeout_seconds)
                
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    if self.config.method.upper() == "GET":
                        async with session.get(
                            self.config.endpoint,
                            headers=headers,
                            params=params
                        ) as response:
                            data = await response.json()
                            status_code = response.status
                    else:
                        async with session.request(
                            self.config.method,
                            self.config.endpoint,
                            headers=headers,
                            json=params
                        ) as response:
                            data = await response.json()
                            status_code = response.status
                
                response_time = (time.time() - start_time) * 1000
                
                if status_code == 200:
                    self.cache.set(self.config.endpoint, params, data)
                    
                    self.stats["api_calls"] += 1
                    
                    return APIResponse(
                        request_id=f"req_{uuid.uuid4().hex[:8]}",
                        endpoint=self.config.endpoint,
                        status_code=status_code,
                        data=data,
                        headers=headers,
                        response_time_ms=response_time,
                    )
                elif status_code == 429:
                    self.stats["rate_limit_waits"] += 1
                    await asyncio.sleep(1.0 * (attempt + 1))
                    continue
                else:
                    return APIResponse(
                        request_id=f"req_{uuid.uuid4().hex[:8]}",
                        endpoint=self.config.endpoint,
                        status_code=status_code,
                        data=None,
                        headers=headers,
                        response_time_ms=response_time,
                        error=f"HTTP {status_code}",
                    )
                    
            except Exception as e:
                logger.error(f"API call attempt {attempt + 1} failed: {e}")
                if attempt < self.config.retry_count - 1:
                    await asyncio.sleep(1.0 * (attempt + 1))
        
        return APIResponse(
            request_id=f"req_{uuid.uuid4().hex[:8]}",
            endpoint=self.config.endpoint,
            status_code=0,
            data=None,
            headers={},
            response_time_ms=(time.time() - start_time) * 1000,
            error="Max retries exceeded",
        )
    
    async def _collect_graphql(self, query: Optional[str] = None, variables: Optional[Dict] = None) -> APIResponse:
        """
        GraphQL API采集
        """
        query = query or self.config.subscription_query or ""
        variables = variables or {}
        
        await self.rate_limiter.acquire()
        
        headers = self._prepare_headers()
        headers["Content-Type"] = "application/json"
        
        start_time = time.time()
        
        try:
            import aiohttp
            
            timeout = aiohttp.ClientTimeout(total=self.config.timeout_seconds)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    self.config.endpoint,
                    headers=headers,
                    json={"query": query, "variables": variables}
                ) as response:
                    data = await response.json()
                    status_code = response.status
            
            response_time = (time.time() - start_time) * 1000
            
            self.stats["api_calls"] += 1
            
            return APIResponse(
                request_id=f"gql_{uuid.uuid4().hex[:8]}",
                endpoint=self.config.endpoint,
                status_code=status_code,
                data=data,
                headers=headers,
                response_time_ms=response_time,
            )
            
        except Exception as e:
            return APIResponse(
                request_id=f"gql_{uuid.uuid4().hex[:8]}",
                endpoint=self.config.endpoint,
                status_code=0,
                data=None,
                headers={},
                response_time_ms=(time.time() - start_time) * 1000,
                error=str(e),
            )
    
    async def _collect_websocket(self) -> List[APIResponse]:
        """
        WebSocket数据采集
        """
        results = []
        
        if not self.subscriptions:
            return results
        
        for subscription_id, queue in self.subscriptions.items():
            try:
                messages = []
                while not queue.empty():
                    msg = await asyncio.wait_for(queue.get(), timeout=0.1)
                    messages.append(msg)
                    self.stats["websocket_messages"] += 1
                
                if messages:
                    results.append(APIResponse(
                        request_id=f"ws_{subscription_id}",
                        endpoint=self.config.endpoint,
                        status_code=200,
                        data=messages,
                        headers={},
                        response_time_ms=0,
                    ))
                    
            except asyncio.TimeoutError:
                continue
        
        return results
    
    def _prepare_headers(self) -> Dict[str, str]:
        """
        准备请求头
        """
        headers = dict(self.config.headers)
        
        if self.config.api_key:
            headers[self.config.api_key_header] = self.config.api_key
        
        return headers
    
    async def subscribe(self, subscription_query: str, subscription_id: Optional[str] = None) -> str:
        """
        订阅WebSocket数据流
        """
        subscription_id = subscription_id or f"sub_{uuid.uuid4().hex[:8]}"
        
        self.subscriptions[subscription_id] = asyncio.Queue()
        
        logger.info(f"Created subscription: {subscription_id}")
        
        return subscription_id
    
    async def unsubscribe(self, subscription_id: str):
        """
        取消订阅
        """
        if subscription_id in self.subscriptions:
            del self.subscriptions[subscription_id]
    
    async def parse(self, raw_data: Any) -> List[Dict]:
        """
        解析API响应
        """
        if isinstance(raw_data, APIResponse):
            if raw_data.data:
                if isinstance(raw_data.data, list):
                    return raw_data.data
                return [raw_data.data]
            return []
        
        if isinstance(raw_data, list):
            return raw_data
        if isinstance(raw_data, dict):
            return [raw_data]
        
        return []
    
    async def validate(self, sample: Dict) -> bool:
        """
        验证样本有效性
        """
        if not isinstance(sample, dict):
            return False
        
        if not sample:
            return False
        
        return True
    
    def add_api_key(self, service: str, api_key: str, rate_limit: int = 1000, daily_limit: int = 10000):
        """
        添加API密钥
        """
        self.key_manager.add_key(service, api_key, rate_limit, daily_limit)
    
    def clear_cache(self):
        """
        清除缓存
        """
        self.cache.clear()
    
    def get_stats(self) -> Dict:
        with self._lock:
            return {
                **self.stats,
                "cache_size": len(self.cache.cache),
                "active_subscriptions": len(self.subscriptions),
            }
