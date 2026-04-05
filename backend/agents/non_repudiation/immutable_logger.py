"""
不可抵赖事件记录器模块
Immutable Event Logger Module

实现数字签名、哈希链、事件验证等功能
"""

import hashlib
import json
import logging
import threading
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class EventType(Enum):
    ATTACK = "attack"
    ATTACK_DETAIL = "attack_detail"
    DEFENSE = "defense"
    SYSTEM = "system"
    TRAINING = "training"
    MODEL_UPDATE = "model_update"
    USER_ACTION = "user_action"
    SECURITY_ALERT = "security_alert"
    AUDIT = "audit"
    FEDERATED_ROUND = "federated_round"


class EventStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    VERIFIED = "verified"
    TAMPERED = "tampered"
    INVALID = "invalid"


@dataclass
class EventRecord:
    record_id: str
    event_type: EventType
    timestamp: datetime
    details: Dict[str, Any]
    prev_hash: str
    current_hash: str
    signature: str
    sequence_num: int
    status: EventStatus
    source_node: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details,
            "prev_hash": self.prev_hash,
            "current_hash": self.current_hash,
            "signature": self.signature,
            "sequence_num": self.sequence_num,
            "status": self.status.value,
            "source_node": self.source_node,
            "metadata": self.metadata,
        }
    
    def compute_hash(self) -> str:
        content = json.dumps({
            "record_id": self.record_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details,
            "prev_hash": self.prev_hash,
            "sequence_num": self.sequence_num,
        }, sort_keys=True)
        
        return hashlib.sha256(content.encode()).hexdigest()


class DigitalSigner:
    """数字签名器"""
    
    def __init__(self, private_key: str = None):
        self.private_key = private_key or self._generate_key()
        self.public_key = self._derive_public_key()
        
        self._lock = threading.Lock()
        
        self.stats = {
            "total_signatures": 0,
            "total_verifications": 0,
            "failed_verifications": 0,
        }
    
    def _generate_key(self) -> str:
        return hashlib.sha256(f"key_{time.time()}_{uuid.uuid4().hex}".encode()).hexdigest()
    
    def _derive_public_key(self) -> str:
        return hashlib.sha256(self.private_key.encode()).hexdigest()
    
    def sign(self, data: str) -> str:
        self.stats["total_signatures"] += 1
        
        signature = hashlib.sha256(
            (self.private_key + data).encode()
        ).hexdigest()
        
        return signature
    
    def verify(self, data: str, signature: str, public_key: str = None) -> bool:
        self.stats["total_verifications"] += 1
        
        expected_signature = hashlib.sha256(
            (self.private_key + data).encode()
        ).hexdigest()
        
        result = signature == expected_signature
        
        if not result:
            self.stats["failed_verifications"] += 1
        
        return result
    
    def get_public_key(self) -> str:
        return self.public_key
    
    def get_stats(self) -> Dict[str, Any]:
        return self.stats.copy()


class HashChain:
    """哈希链"""
    
    def __init__(self, chain_id: str = "default"):
        self.chain_id = chain_id
        self.records: Dict[str, EventRecord] = {}
        self.head_hash: str = "0" * 64
        self.tail_hash: str = "0" * 64
        self.sequence: int = 0
        
        self.daily_roots: Dict[str, Dict[str, Any]] = {}
        
        self._lock = threading.Lock()
        
        self.stats = {
            "total_records": 0,
            "chain_length": 0,
            "daily_roots_published": 0,
        }
    
    def add_record(self, record: EventRecord) -> bool:
        with self._lock:
            if record.record_id in self.records:
                return False
            
            record.prev_hash = self.tail_hash
            record.current_hash = record.compute_hash()
            record.sequence_num = self.sequence
            
            self.records[record.record_id] = record
            self.tail_hash = record.current_hash
            self.sequence += 1
            
            self.stats["total_records"] += 1
            self.stats["chain_length"] = self.sequence
            
            return True
    
    def get_record(self, record_id: str) -> Optional[EventRecord]:
        return self.records.get(record_id)
    
    def get_chain_segment(
        self,
        start_seq: int,
        end_seq: int
    ) -> List[EventRecord]:
        segment = []
        
        for record in self.records.values():
            if start_seq <= record.sequence_num <= end_seq:
                segment.append(record)
        
        return sorted(segment, key=lambda r: r.sequence_num)
    
    def verify_chain(
        self,
        start_id: str = None,
        end_id: str = None
    ) -> Tuple[bool, List[str]]:
        errors = []
        
        with self._lock:
            sorted_records = sorted(
                self.records.values(),
                key=lambda r: r.sequence_num
            )
        
        prev_hash = "0" * 64
        
        for record in sorted_records:
            if start_id and record.record_id == start_id:
                prev_hash = record.prev_hash
            
            expected_hash = record.compute_hash()
            if record.current_hash != expected_hash:
                errors.append(f"Hash mismatch at record {record.record_id}")
            
            if record.prev_hash != prev_hash:
                errors.append(f"Chain break at record {record.record_id}")
            
            prev_hash = record.current_hash
            
            if end_id and record.record_id == end_id:
                break
        
        return len(errors) == 0, errors
    
    def publish_daily_root(self) -> Dict[str, Any]:
        today = datetime.now().strftime("%Y-%m-%d")
        
        root = {
            "date": today,
            "root_hash": self.tail_hash,
            "sequence": self.sequence,
            "timestamp": datetime.now().isoformat(),
            "chain_id": self.chain_id,
        }
        
        with self._lock:
            self.daily_roots[today] = root
            self.stats["daily_roots_published"] += 1
        
        return root
    
    def get_daily_root(self, date: str = None) -> Optional[Dict[str, Any]]:
        date = date or datetime.now().strftime("%Y-%m-%d")
        return self.daily_roots.get(date)
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            **self.stats,
            "head_hash": self.head_hash[:16] + "...",
            "tail_hash": self.tail_hash[:16] + "...",
        }


class EventVerifier:
    """事件验证器"""
    
    def __init__(self, signer: DigitalSigner):
        self.signer = signer
        
        self.verification_cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        
        self.stats = {
            "total_verifications": 0,
            "successful_verifications": 0,
            "failed_verifications": 0,
            "cache_hits": 0,
        }
    
    def verify_record(
        self,
        record: EventRecord,
        check_signature: bool = True
    ) -> Tuple[bool, List[str]]:
        self.stats["total_verifications"] += 1
        errors = []
        
        with self._lock:
            if record.record_id in self.verification_cache:
                cached = self.verification_cache[record.record_id]
                if cached["timestamp"] > (datetime.now() - timedelta(hours=1)).isoformat():
                    self.stats["cache_hits"] += 1
                    return cached["valid"], cached["errors"]
        
        expected_hash = record.compute_hash()
        if record.current_hash != expected_hash:
            errors.append("Hash mismatch - record may have been tampered")
        
        if check_signature:
            data_to_verify = record.current_hash
            if not self.signer.verify(data_to_verify, record.signature):
                errors.append("Signature verification failed")
        
        valid = len(errors) == 0
        
        with self._lock:
            self.verification_cache[record.record_id] = {
                "valid": valid,
                "errors": errors,
                "timestamp": datetime.now().isoformat(),
            }
            
            if valid:
                self.stats["successful_verifications"] += 1
            else:
                self.stats["failed_verifications"] += 1
        
        return valid, errors
    
    def verify_chain_segment(
        self,
        records: List[EventRecord]
    ) -> Tuple[bool, Dict[str, List[str]]]:
        all_errors: Dict[str, List[str]] = {}
        all_valid = True
        
        prev_hash = "0" * 64
        
        for record in records:
            valid, errors = self.verify_record(record)
            
            if record.prev_hash != prev_hash:
                errors.append("Chain continuity break")
                valid = False
            
            if not valid:
                all_valid = False
                all_errors[record.record_id] = errors
            
            prev_hash = record.current_hash
        
        return all_valid, all_errors
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            **self.stats,
            "cache_size": len(self.verification_cache),
        }


class ImmutableEventLogger:
    """不可抵赖事件记录器主控"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        self.signer = DigitalSigner(
            private_key=self.config.get("private_key")
        )
        self.chain = HashChain(
            chain_id=self.config.get("chain_id", "default")
        )
        self.verifier = EventVerifier(self.signer)
        
        self.event_index: Dict[EventType, List[str]] = defaultdict(list)
        self.time_index: Dict[str, List[str]] = defaultdict(list)
        
        self._lock = threading.Lock()
        
        self._running = False
        self._daily_task = None
        
        self.stats = {
            "total_events_logged": 0,
            "events_by_type": defaultdict(int),
            "last_event_time": None,
        }
    
    async def start(self):
        self._running = True
        self._daily_task = asyncio.create_task(self._daily_root_publisher())
    
    def stop(self):
        self._running = False
        if self._daily_task:
            self._daily_task.cancel()
    
    async def _daily_root_publisher(self):
        while self._running:
            try:
                await asyncio.sleep(86400)
                root = self.chain.publish_daily_root()
                logger.info(f"Published daily root: {root['root_hash'][:16]}...")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Daily root publisher error: {e}")
    
    def log_event(
        self,
        event_type: EventType,
        details: Dict[str, Any],
        source_node: str = "system",
        metadata: Dict[str, Any] = None
    ) -> EventRecord:
        record_id = f"rec_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        record = EventRecord(
            record_id=record_id,
            event_type=event_type,
            timestamp=datetime.now(),
            details=details,
            prev_hash="",
            current_hash="",
            signature="",
            sequence_num=0,
            status=EventStatus.PENDING,
            source_node=source_node,
            metadata=metadata or {},
        )
        
        self.chain.add_record(record)
        
        record.current_hash = record.compute_hash()
        record.signature = self.signer.sign(record.current_hash)
        record.status = EventStatus.CONFIRMED
        
        with self._lock:
            self.event_index[event_type].append(record_id)
            
            date_key = record.timestamp.strftime("%Y-%m-%d")
            self.time_index[date_key].append(record_id)
            
            self.stats["total_events_logged"] += 1
            self.stats["events_by_type"][event_type.value] += 1
            self.stats["last_event_time"] = record.timestamp.isoformat()
        
        return record
    
    def log_attack_event(
        self,
        attack_type: str,
        source_ip: str,
        target: str,
        defense_action: str,
        result: str,
        details: Dict[str, Any] = None
    ) -> EventRecord:
        attack_details = {
            "attack_type": attack_type,
            "source_ip": source_ip,
            "target": target,
            "defense_action": defense_action,
            "result": result,
            "timestamp": datetime.now().isoformat(),
            **(details or {}),
        }
        
        return self.log_event(
            event_type=EventType.ATTACK_DETAIL,
            details=attack_details,
            source_node="defense_system",
            metadata={"severity": "high" if "success" not in result else "medium"}
        )
    
    def get_record(self, record_id: str) -> Optional[EventRecord]:
        return self.chain.get_record(record_id)
    
    def verify_record(self, record_id: str) -> Tuple[bool, List[str]]:
        record = self.get_record(record_id)
        if not record:
            return False, ["Record not found"]
        
        return self.verifier.verify_record(record)
    
    def verify_chain(
        self,
        start_id: str = None,
        end_id: str = None
    ) -> Tuple[bool, List[str]]:
        return self.chain.verify_chain(start_id, end_id)
    
    def get_events_by_type(
        self,
        event_type: EventType,
        limit: int = 100
    ) -> List[EventRecord]:
        with self._lock:
            record_ids = self.event_index[event_type][-limit:]
        
        records = []
        for rid in record_ids:
            record = self.get_record(rid)
            if record:
                records.append(record)
        
        return records
    
    def get_events_by_date(
        self,
        date: str,
        limit: int = 1000
    ) -> List[EventRecord]:
        with self._lock:
            record_ids = self.time_index.get(date, [])[-limit:]
        
        records = []
        for rid in record_ids:
            record = self.get_record(rid)
            if record:
                records.append(record)
        
        return records
    
    def export_chain(
        self,
        start_seq: int = None,
        end_seq: int = None
    ) -> Dict[str, Any]:
        start = start_seq or 0
        end = end_seq or self.chain.sequence
        
        records = self.chain.get_chain_segment(start, end)
        
        return {
            "chain_id": self.chain.chain_id,
            "export_time": datetime.now().isoformat(),
            "start_sequence": start,
            "end_sequence": end,
            "total_records": len(records),
            "records": [r.to_dict() for r in records],
            "daily_roots": self.chain.daily_roots,
            "public_key": self.signer.get_public_key(),
        }
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "logger": {
                **self.stats,
                "events_by_type": dict(self.stats["events_by_type"]),
            },
            "chain": self.chain.get_stats(),
            "signer": self.signer.get_stats(),
            "verifier": self.verifier.get_stats(),
        }


import asyncio
