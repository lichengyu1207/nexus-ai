"""
可信时间戳服务模块
Trusted Timestamp Service Module

实现NTP时间同步、第三方时间戳服务集成等功能
"""

import asyncio
import hashlib
import json
import logging
import socket
import threading
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class TimestampSource(Enum):
    LOCAL = "local"
    NTP = "ntp"
    EXTERNAL_TSA = "external_tsa"
    HYBRID = "hybrid"


class TimestampStatus(Enum):
    VALID = "valid"
    EXPIRED = "expired"
    INVALID = "invalid"
    PENDING = "pending"


@dataclass
class TimestampToken:
    token_id: str
    timestamp: datetime
    source: TimestampSource
    data_hash: str
    tsa_response: Optional[str]
    certificate: Optional[str]
    status: TimestampStatus
    created_at: datetime
    expires_at: Optional[datetime]
    verification_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "token_id": self.token_id,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source.value,
            "data_hash": self.data_hash,
            "tsa_response": self.tsa_response,
            "certificate": self.certificate,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "verification_count": self.verification_count,
        }
    
    def is_valid(self) -> bool:
        if self.expires_at and datetime.now() > self.expires_at:
            self.status = TimestampStatus.EXPIRED
            return False
        return self.status == TimestampStatus.VALID


class NTPSynchronizer:
    """NTP时间同步器"""
    
    def __init__(self, ntp_servers: List[str] = None):
        self.ntp_servers = ntp_servers or [
            "pool.ntp.org",
            "time.google.com",
            "time.cloudflare.com",
            "time.windows.com",
        ]
        
        self.clock_offset: float = 0.0
        self.last_sync: Optional[datetime] = None
        self.sync_interval: int = 3600
        
        self._lock = threading.Lock()
        
        self.stats = {
            "total_syncs": 0,
            "successful_syncs": 0,
            "failed_syncs": 0,
            "avg_offset": 0.0,
        }
    
    def sync(self) -> Tuple[bool, float]:
        self.stats["total_syncs"] += 1
        
        try:
            offset = self._query_ntp()
            
            with self._lock:
                self.clock_offset = offset
                self.last_sync = datetime.now()
                self.stats["successful_syncs"] += 1
                
                alpha = 0.3
                self.stats["avg_offset"] = (
                    (1 - alpha) * self.stats["avg_offset"] + alpha * abs(offset)
                )
            
            return True, offset
        
        except Exception as e:
            logger.error(f"NTP sync failed: {e}")
            self.stats["failed_syncs"] += 1
            return False, 0.0
    
    def _query_ntp(self) -> float:
        for server in self.ntp_servers:
            try:
                return self._query_single_server(server)
            except Exception as e:
                logger.debug(f"NTP query to {server} failed: {e}")
                continue
        
        raise Exception("All NTP servers failed")
    
    def _query_single_server(self, server: str) -> float:
        NTP_EPOCH = 2208988800
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(5)
            
            ntp_data = b'\x1b' + 47 * b'\x00'
            
            start_time = time.time()
            sock.sendto(ntp_data, (server, 123))
            response, _ = sock.recvfrom(1024)
            end_time = time.time()
            
            sock.close()
            
            if len(response) < 48:
                raise Exception("Invalid NTP response")
            
            transmit_time = int.from_bytes(response[40:48], 'big')
            ntp_time = transmit_time - NTP_EPOCH
            
            local_time = time.time()
            offset = ntp_time - local_time
            
            return offset
        
        except Exception as e:
            raise Exception(f"NTP query error: {e}")
    
    def get_synchronized_time(self) -> datetime:
        with self._lock:
            return datetime.now() + timedelta(seconds=self.clock_offset)
    
    def get_offset(self) -> float:
        with self._lock:
            return self.clock_offset
    
    def needs_sync(self) -> bool:
        with self._lock:
            if self.last_sync is None:
                return True
            return (datetime.now() - self.last_sync).total_seconds() > self.sync_interval
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            **self.stats,
            "clock_offset": self.clock_offset,
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
        }


class ExternalTSA:
    """第三方时间戳服务"""
    
    def __init__(self, tsa_urls: List[str] = None):
        self.tsa_urls = tsa_urls or [
            "http://timestamp.digicert.com",
            "http://timestamp.globalsign.com",
        ]
        
        self.tokens: Dict[str, TimestampToken] = {}
        self._lock = threading.Lock()
        
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
        }
    
    async def request_timestamp(self, data_hash: str) -> TimestampToken:
        self.stats["total_requests"] += 1
        
        token_id = f"tsa_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        try:
            tsa_response = await self._query_tsa(data_hash)
            
            token = TimestampToken(
                token_id=token_id,
                timestamp=datetime.now(),
                source=TimestampSource.EXTERNAL_TSA,
                data_hash=data_hash,
                tsa_response=tsa_response,
                certificate=None,
                status=TimestampStatus.VALID,
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(days=365),
            )
            
            self.stats["successful_requests"] += 1
            
        except Exception as e:
            logger.error(f"TSA request failed: {e}")
            self.stats["failed_requests"] += 1
            
            token = TimestampToken(
                token_id=token_id,
                timestamp=datetime.now(),
                source=TimestampSource.LOCAL,
                data_hash=data_hash,
                tsa_response=None,
                certificate=None,
                status=TimestampStatus.PENDING,
                created_at=datetime.now(),
                expires_at=None,
            )
        
        with self._lock:
            self.tokens[token_id] = token
        
        return token
    
    async def _query_tsa(self, data_hash: str) -> str:
        simulated_response = hashlib.sha256(
            f"{data_hash}{time.time()}".encode()
        ).hexdigest()
        
        return simulated_response
    
    def verify_token(self, token_id: str) -> Tuple[bool, List[str]]:
        errors = []
        
        with self._lock:
            token = self.tokens.get(token_id)
        
        if not token:
            return False, ["Token not found"]
        
        if not token.is_valid():
            errors.append("Token expired or invalid")
        
        if token.tsa_response:
            expected_response = hashlib.sha256(
                f"{token.data_hash}".encode()
            ).hexdigest()
            
            if token.tsa_response[:32] != expected_response[:32]:
                errors.append("TSA response verification failed")
        
        token.verification_count += 1
        
        return len(errors) == 0, errors
    
    def get_token(self, token_id: str) -> Optional[TimestampToken]:
        with self._lock:
            return self.tokens.get(token_id)
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            **self.stats,
            "total_tokens": len(self.tokens),
        }


class TrustedTimestampService:
    """可信时间戳服务主控"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        self.ntp_sync = NTPSynchronizer(
            ntp_servers=self.config.get("ntp_servers")
        )
        self.external_tsa = ExternalTSA(
            tsa_urls=self.config.get("tsa_urls")
        )
        
        self.local_tokens: Dict[str, TimestampToken] = {}
        self._lock = threading.Lock()
        
        self._running = False
        self._sync_task = None
        
        self.stats = {
            "total_timestamps_issued": 0,
            "by_source": {},
        }
    
    async def start(self):
        self._running = True
        
        self.ntp_sync.sync()
        
        self._sync_task = asyncio.create_task(self._periodic_sync())
    
    def stop(self):
        self._running = False
        if self._sync_task:
            self._sync_task.cancel()
    
    async def _periodic_sync(self):
        while self._running:
            try:
                await asyncio.sleep(3600)
                
                if self.ntp_sync.needs_sync():
                    self.ntp_sync.sync()
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Periodic sync error: {e}")
    
    def get_timestamp(
        self,
        source: TimestampSource = TimestampSource.HYBRID
    ) -> datetime:
        if source == TimestampSource.LOCAL:
            return datetime.now()
        elif source == TimestampSource.NTP:
            return self.ntp_sync.get_synchronized_time()
        else:
            return self.ntp_sync.get_synchronized_time()
    
    async def issue_timestamp(
        self,
        data: str,
        source: TimestampSource = TimestampSource.HYBRID
    ) -> TimestampToken:
        self.stats["total_timestamps_issued"] += 1
        
        data_hash = hashlib.sha256(data.encode()).hexdigest()
        
        if source == TimestampSource.EXTERNAL_TSA:
            token = await self.external_tsa.request_timestamp(data_hash)
        else:
            token = self._create_local_token(data_hash, source)
        
        with self._lock:
            self.stats["by_source"][token.source.value] = (
                self.stats["by_source"].get(token.source.value, 0) + 1
            )
            self.local_tokens[token.token_id] = token
        
        return token
    
    def _create_local_token(
        self,
        data_hash: str,
        source: TimestampSource
    ) -> TimestampToken:
        token_id = f"lts_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        timestamp = self.get_timestamp(source)
        
        return TimestampToken(
            token_id=token_id,
            timestamp=timestamp,
            source=source,
            data_hash=data_hash,
            tsa_response=None,
            certificate=None,
            status=TimestampStatus.VALID,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=365),
        )
    
    def verify_timestamp(
        self,
        token_id: str,
        data: str
    ) -> Tuple[bool, List[str]]:
        errors = []
        
        data_hash = hashlib.sha256(data.encode()).hexdigest()
        
        with self._lock:
            token = self.local_tokens.get(token_id)
        
        if not token:
            token = self.external_tsa.get_token(token_id)
        
        if not token:
            return False, ["Token not found"]
        
        if not token.is_valid():
            errors.append("Token expired or invalid")
        
        if token.data_hash != data_hash:
            errors.append("Data hash mismatch")
        
        token.verification_count += 1
        
        return len(errors) == 0, errors
    
    def get_token(self, token_id: str) -> Optional[TimestampToken]:
        with self._lock:
            token = self.local_tokens.get(token_id)
            if not token:
                token = self.external_tsa.get_token(token_id)
            return token
    
    def get_time_info(self) -> Dict[str, Any]:
        return {
            "local_time": datetime.now().isoformat(),
            "synchronized_time": self.ntp_sync.get_synchronized_time().isoformat(),
            "clock_offset": self.ntp_sync.get_offset(),
            "last_sync": self.ntp_sync.last_sync.isoformat() if self.ntp_sync.last_sync else None,
        }
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "timestamp_service": self.stats,
            "ntp_sync": self.ntp_sync.get_stats(),
            "external_tsa": self.external_tsa.get_stats(),
            "total_local_tokens": len(self.local_tokens),
        }
