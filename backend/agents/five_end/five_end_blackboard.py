"""
五端共享黑板系统
Five-End Shared Blackboard System

实现跨端信息共享的黑板机制
"""

import asyncio
import json
import uuid
import time
import hashlib
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class BlackboardRegion(Enum):
    PUBLIC = "public"
    GOV = "gov"
    ENTERPRISE = "enterprise"
    EDU = "edu"
    STD = "std"
    PUBLIC_END = "public_end"


class KnowledgeType(Enum):
    WARNING = "warning"
    REPORT = "report"
    POLICY = "policy"
    STATISTICS = "statistics"
    CASE = "case"
    STANDARD = "standard"
    DEMAND = "demand"
    HEATMAP = "heatmap"
    TREND = "trend"
    ALERT = "alert"
    RULE = "rule"
    CONFIG = "config"


@dataclass
class SharedKnowledge:
    knowledge_id: str
    knowledge_type: KnowledgeType
    region: BlackboardRegion
    key: str
    value: Any
    source_end: str
    source_agent: str
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    ttl: int = 86400
    version: int = 1
    checksum: str = ""
    access_count: int = 0
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "knowledge_id": self.knowledge_id,
            "knowledge_type": self.knowledge_type.value,
            "region": self.region.value,
            "key": self.key,
            "value": self.value,
            "source_end": self.source_end,
            "source_agent": self.source_agent,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "ttl": self.ttl,
            "version": self.version,
            "checksum": self.checksum,
            "access_count": self.access_count,
            "tags": self.tags,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SharedKnowledge":
        return cls(
            knowledge_id=data["knowledge_id"],
            knowledge_type=KnowledgeType(data["knowledge_type"]),
            region=BlackboardRegion(data["region"]),
            key=data["key"],
            value=data["value"],
            source_end=data["source_end"],
            source_agent=data["source_agent"],
            created_at=data.get("created_at", time.time()),
            updated_at=data.get("updated_at", time.time()),
            ttl=data.get("ttl", 86400),
            version=data.get("version", 1),
            checksum=data.get("checksum", ""),
            access_count=data.get("access_count", 0),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
        )
    
    def compute_checksum(self) -> str:
        data = f"{self.key}{json.dumps(self.value, sort_keys=True)}{self.version}"
        return hashlib.md5(data.encode()).hexdigest()
    
    def is_expired(self) -> bool:
        return time.time() > self.created_at + self.ttl


class BlackboardListener:
    def __init__(self, listener_id: str, callback: Callable, 
                 key_pattern: str = "*", knowledge_types: List[KnowledgeType] = None):
        self.listener_id = listener_id
        self.callback = callback
        self.key_pattern = key_pattern
        self.knowledge_types = knowledge_types or []
        self.created_at = time.time()
    
    def matches(self, knowledge: SharedKnowledge) -> bool:
        if self.key_pattern != "*":
            if not self._match_pattern(self.key_pattern, knowledge.key):
                return False
        
        if self.knowledge_types and knowledge.knowledge_type not in self.knowledge_types:
            return False
        
        return True
    
    def _match_pattern(self, pattern: str, key: str) -> bool:
        if pattern.endswith("*"):
            return key.startswith(pattern[:-1])
        elif pattern.startswith("*"):
            return key.endswith(pattern[1:])
        else:
            return pattern == key


class RegionAccessControl:
    END_PERMISSIONS = {
        "gov": {
            BlackboardRegion.PUBLIC: ["read", "write"],
            BlackboardRegion.GOV: ["read", "write"],
            BlackboardRegion.ENTERPRISE: ["read"],
            BlackboardRegion.EDU: ["read"],
            BlackboardRegion.STD: ["read"],
            BlackboardRegion.PUBLIC_END: ["read"],
        },
        "enterprise": {
            BlackboardRegion.PUBLIC: ["read", "write"],
            BlackboardRegion.GOV: ["read"],
            BlackboardRegion.ENTERPRISE: ["read", "write"],
            BlackboardRegion.EDU: ["read"],
            BlackboardRegion.STD: ["read"],
            BlackboardRegion.PUBLIC_END: ["read"],
        },
        "edu": {
            BlackboardRegion.PUBLIC: ["read", "write"],
            BlackboardRegion.GOV: ["read"],
            BlackboardRegion.ENTERPRISE: ["read"],
            BlackboardRegion.EDU: ["read", "write"],
            BlackboardRegion.STD: ["read"],
            BlackboardRegion.PUBLIC_END: ["read"],
        },
        "std": {
            BlackboardRegion.PUBLIC: ["read", "write"],
            BlackboardRegion.GOV: ["read"],
            BlackboardRegion.ENTERPRISE: ["read"],
            BlackboardRegion.EDU: ["read"],
            BlackboardRegion.STD: ["read", "write"],
            BlackboardRegion.PUBLIC_END: ["read"],
        },
        "public": {
            BlackboardRegion.PUBLIC: ["read"],
            BlackboardRegion.GOV: [],
            BlackboardRegion.ENTERPRISE: [],
            BlackboardRegion.EDU: [],
            BlackboardRegion.STD: ["read"],
            BlackboardRegion.PUBLIC_END: ["read", "write"],
        },
    }
    
    @classmethod
    def can_read(cls, end_type: str, region: BlackboardRegion) -> bool:
        permissions = cls.END_PERMISSIONS.get(end_type, {})
        return "read" in permissions.get(region, [])
    
    @classmethod
    def can_write(cls, end_type: str, region: BlackboardRegion) -> bool:
        permissions = cls.END_PERMISSIONS.get(end_type, {})
        return "write" in permissions.get(region, [])


class FiveEndBlackboard:
    PUBLIC_KEYS = {
        "warning:region_risk",
        "report:industry",
        "policy:latest",
        "standard:rules",
        "heatmap:city",
        "trend:price",
    }
    
    def __init__(self, redis_client: Optional[Any] = None):
        self.redis_client = redis_client
        
        self._storage: Dict[str, SharedKnowledge] = {}
        self._region_index: Dict[BlackboardRegion, Set[str]] = defaultdict(set)
        self._type_index: Dict[KnowledgeType, Set[str]] = defaultdict(set)
        self._key_index: Dict[str, str] = {}
        
        self._listeners: Dict[str, BlackboardListener] = {}
        self._key_listeners: Dict[str, Set[str]] = defaultdict(set)
        
        self._lock = asyncio.Lock()
        self._operation_log: List[Dict[str, Any]] = []
        self._max_log_size = 10000
        
        self._initialize_public_region()
    
    def _initialize_public_region(self) -> None:
        initial_data = {
            "warning:region_risk": {"regions": [], "last_update": None},
            "report:industry": {"reports": [], "last_update": None},
            "policy:latest": {"policies": [], "last_update": None},
            "standard:rules": {"rules": [], "last_update": None},
            "heatmap:city": {"heatmap": {}, "last_update": None},
            "trend:price": {"trends": {}, "last_update": None},
        }
        
        for key, value in initial_data.items():
            knowledge = SharedKnowledge(
                knowledge_id=str(uuid.uuid4()),
                knowledge_type=KnowledgeType.CONFIG,
                region=BlackboardRegion.PUBLIC,
                key=key,
                value=value,
                source_end="system",
                source_agent="blackboard",
                ttl=86400 * 30,
            )
            self._storage[knowledge.knowledge_id] = knowledge
            self._region_index[BlackboardRegion.PUBLIC].add(knowledge.knowledge_id)
            self._key_index[key] = knowledge.knowledge_id
    
    async def write(self, key: str, value: Any, source_end: str, source_agent: str,
                    knowledge_type: KnowledgeType = KnowledgeType.CONFIG,
                    region: BlackboardRegion = BlackboardRegion.PUBLIC,
                    ttl: int = 86400, tags: List[str] = None,
                    metadata: Dict[str, Any] = None) -> str:
        async with self._lock:
            if not RegionAccessControl.can_write(source_end, region):
                raise PermissionError(f"End {source_end} cannot write to region {region.value}")
            
            existing_id = self._key_index.get(key)
            if existing_id:
                knowledge = self._storage[existing_id]
                knowledge.value = value
                knowledge.updated_at = time.time()
                knowledge.version += 1
                knowledge.source_end = source_end
                knowledge.source_agent = source_agent
                knowledge.ttl = ttl
                if tags:
                    knowledge.tags = tags
                if metadata:
                    knowledge.metadata.update(metadata)
                knowledge.checksum = knowledge.compute_checksum()
            else:
                knowledge = SharedKnowledge(
                    knowledge_id=str(uuid.uuid4()),
                    knowledge_type=knowledge_type,
                    region=region,
                    key=key,
                    value=value,
                    source_end=source_end,
                    source_agent=source_agent,
                    ttl=ttl,
                    tags=tags or [],
                    metadata=metadata or {},
                )
                knowledge.checksum = knowledge.compute_checksum()
                
                self._storage[knowledge.knowledge_id] = knowledge
                self._region_index[region].add(knowledge.knowledge_id)
                self._type_index[knowledge_type].add(knowledge.knowledge_id)
                self._key_index[key] = knowledge.knowledge_id
            
            self._log_operation("write", knowledge)
            
            if self.redis_client:
                await self._sync_to_redis(knowledge)
            
            await self._notify_listeners(knowledge)
            
            logger.debug(f"Knowledge {key} written to blackboard by {source_agent}")
            return knowledge.knowledge_id
    
    async def read(self, key: str, reader_end: str) -> Optional[SharedKnowledge]:
        knowledge_id = self._key_index.get(key)
        if not knowledge_id:
            return None
        
        knowledge = self._storage.get(knowledge_id)
        if not knowledge:
            return None
        
        if not RegionAccessControl.can_read(reader_end, knowledge.region):
            raise PermissionError(f"End {reader_end} cannot read from region {knowledge.region.value}")
        
        if knowledge.is_expired():
            await self._delete_knowledge(knowledge_id)
            return None
        
        knowledge.access_count += 1
        
        self._log_operation("read", knowledge)
        
        return knowledge
    
    async def delete(self, key: str, deleter_end: str) -> bool:
        async with self._lock:
            knowledge_id = self._key_index.get(key)
            if not knowledge_id:
                return False
            
            knowledge = self._storage.get(knowledge_id)
            if not knowledge:
                return False
            
            if not RegionAccessControl.can_write(deleter_end, knowledge.region):
                raise PermissionError(f"End {deleter_end} cannot delete from region {knowledge.region.value}")
            
            await self._delete_knowledge(knowledge_id)
            
            self._log_operation("delete", knowledge)
            
            return True
    
    async def _delete_knowledge(self, knowledge_id: str) -> None:
        knowledge = self._storage.pop(knowledge_id, None)
        if knowledge:
            self._region_index[knowledge.region].discard(knowledge_id)
            self._type_index[knowledge.knowledge_type].discard(knowledge_id)
            self._key_index.pop(knowledge.key, None)
            
            if self.redis_client:
                await self._delete_from_redis(knowledge.key)
    
    async def query_by_region(self, region: BlackboardRegion, reader_end: str,
                               limit: int = 100) -> List[SharedKnowledge]:
        if not RegionAccessControl.can_read(reader_end, region):
            raise PermissionError(f"End {reader_end} cannot read from region {region.value}")
        
        knowledge_ids = list(self._region_index[region])[:limit]
        results = []
        
        for kid in knowledge_ids:
            knowledge = self._storage.get(kid)
            if knowledge and not knowledge.is_expired():
                knowledge.access_count += 1
                results.append(knowledge)
        
        return results
    
    async def query_by_type(self, knowledge_type: KnowledgeType, reader_end: str,
                             region: BlackboardRegion = None,
                             limit: int = 100) -> List[SharedKnowledge]:
        knowledge_ids = list(self._type_index[knowledge_type])
        results = []
        
        for kid in knowledge_ids:
            knowledge = self._storage.get(kid)
            if not knowledge or knowledge.is_expired():
                continue
            
            if region and knowledge.region != region:
                continue
            
            if not RegionAccessControl.can_read(reader_end, knowledge.region):
                continue
            
            knowledge.access_count += 1
            results.append(knowledge)
            
            if len(results) >= limit:
                break
        
        return results
    
    async def search(self, query: Dict[str, Any], reader_end: str,
                     limit: int = 100) -> List[SharedKnowledge]:
        results = []
        
        for knowledge in self._storage.values():
            if knowledge.is_expired():
                continue
            
            if not RegionAccessControl.can_read(reader_end, knowledge.region):
                continue
            
            if query.get("key_pattern"):
                if not self._match_key_pattern(query["key_pattern"], knowledge.key):
                    continue
            
            if query.get("knowledge_type"):
                if knowledge.knowledge_type != KnowledgeType(query["knowledge_type"]):
                    continue
            
            if query.get("region"):
                if knowledge.region != BlackboardRegion(query["region"]):
                    continue
            
            if query.get("tags"):
                if not all(tag in knowledge.tags for tag in query["tags"]):
                    continue
            
            if query.get("source_end"):
                if knowledge.source_end != query["source_end"]:
                    continue
            
            knowledge.access_count += 1
            results.append(knowledge)
            
            if len(results) >= limit:
                break
        
        return results
    
    def _match_key_pattern(self, pattern: str, key: str) -> bool:
        if pattern.endswith("*"):
            return key.startswith(pattern[:-1])
        elif pattern.startswith("*"):
            return key.endswith(pattern[1:])
        else:
            return pattern == key
    
    def register_listener(self, listener_id: str, callback: Callable,
                          key_pattern: str = "*",
                          knowledge_types: List[KnowledgeType] = None) -> str:
        listener = BlackboardListener(
            listener_id=listener_id,
            callback=callback,
            key_pattern=key_pattern,
            knowledge_types=knowledge_types,
        )
        
        self._listeners[listener_id] = listener
        
        if key_pattern != "*":
            self._key_listeners[key_pattern].add(listener_id)
        
        logger.info(f"Listener {listener_id} registered for pattern {key_pattern}")
        return listener_id
    
    def unregister_listener(self, listener_id: str) -> bool:
        listener = self._listeners.pop(listener_id, None)
        if not listener:
            return False
        
        if listener.key_pattern in self._key_listeners:
            self._key_listeners[listener.key_pattern].discard(listener_id)
        
        logger.info(f"Listener {listener_id} unregistered")
        return True
    
    async def _notify_listeners(self, knowledge: SharedKnowledge) -> None:
        for listener in self._listeners.values():
            if listener.matches(knowledge):
                try:
                    if asyncio.iscoroutinefunction(listener.callback):
                        await listener.callback(knowledge)
                    else:
                        listener.callback(knowledge)
                except Exception as e:
                    logger.error(f"Listener callback error: {e}")
    
    async def _sync_to_redis(self, knowledge: SharedKnowledge) -> None:
        if not self.redis_client:
            return
        
        try:
            key = f"blackboard:{knowledge.region.value}:{knowledge.key}"
            value = json.dumps(knowledge.to_dict())
            await self.redis_client.setex(key, knowledge.ttl, value)
        except Exception as e:
            logger.error(f"Failed to sync to Redis: {e}")
    
    async def _delete_from_redis(self, key: str) -> None:
        if not self.redis_client:
            return
        
        try:
            await self.redis_client.delete(f"blackboard:*:{key}")
        except Exception as e:
            logger.error(f"Failed to delete from Redis: {e}")
    
    def _log_operation(self, operation: str, knowledge: SharedKnowledge) -> None:
        log_entry = {
            "timestamp": time.time(),
            "operation": operation,
            "knowledge_id": knowledge.knowledge_id,
            "key": knowledge.key,
            "region": knowledge.region.value,
            "source_end": knowledge.source_end,
            "source_agent": knowledge.source_agent,
        }
        
        self._operation_log.append(log_entry)
        
        if len(self._operation_log) > self._max_log_size:
            self._operation_log = self._operation_log[-int(self._max_log_size * 0.8):]
    
    async def get_operation_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        return self._operation_log[-limit:]
    
    async def get_statistics(self) -> Dict[str, Any]:
        stats = {
            "total_knowledge": len(self._storage),
            "by_region": {},
            "by_type": {},
            "total_listeners": len(self._listeners),
            "operation_log_size": len(self._operation_log),
        }
        
        for region in BlackboardRegion:
            stats["by_region"][region.value] = len(self._region_index[region])
        
        for ktype in KnowledgeType:
            stats["by_type"][ktype.value] = len(self._type_index[ktype])
        
        return stats
    
    async def cleanup_expired(self) -> int:
        async with self._lock:
            expired_ids = []
            
            for knowledge_id, knowledge in self._storage.items():
                if knowledge.is_expired():
                    expired_ids.append(knowledge_id)
            
            for kid in expired_ids:
                await self._delete_knowledge(kid)
            
            if expired_ids:
                logger.info(f"Cleaned up {len(expired_ids)} expired knowledge entries")
            
            return len(expired_ids)
    
    async def export_region(self, region: BlackboardRegion, exporter_end: str) -> Dict[str, Any]:
        if not RegionAccessControl.can_read(exporter_end, region):
            raise PermissionError(f"End {exporter_end} cannot export region {region.value}")
        
        knowledge_list = await self.query_by_region(region, exporter_end, limit=10000)
        
        return {
            "region": region.value,
            "exported_at": time.time(),
            "count": len(knowledge_list),
            "knowledge": [k.to_dict() for k in knowledge_list],
        }
    
    async def import_knowledge(self, knowledge_data: List[Dict[str, Any]], 
                                importer_end: str, importer_agent: str) -> int:
        count = 0
        
        for data in knowledge_data:
            try:
                knowledge = SharedKnowledge.from_dict(data)
                
                if not RegionAccessControl.can_write(importer_end, knowledge.region):
                    continue
                
                await self.write(
                    key=knowledge.key,
                    value=knowledge.value,
                    source_end=importer_end,
                    source_agent=importer_agent,
                    knowledge_type=knowledge.knowledge_type,
                    region=knowledge.region,
                    ttl=knowledge.ttl,
                    tags=knowledge.tags,
                    metadata=knowledge.metadata,
                )
                count += 1
            except Exception as e:
                logger.error(f"Failed to import knowledge: {e}")
        
        return count


class BlackboardMonitor:
    def __init__(self, blackboard: FiveEndBlackboard):
        self.blackboard = blackboard
        self._metrics_history: List[Dict[str, Any]] = []
        self._max_history = 1000
    
    async def collect_metrics(self) -> Dict[str, Any]:
        stats = await self.blackboard.get_statistics()
        
        metrics = {
            "timestamp": time.time(),
            **stats,
        }
        
        self._metrics_history.append(metrics)
        if len(self._metrics_history) > self._max_history:
            self._metrics_history = self._metrics_history[-int(self._max_history * 0.8):]
        
        return metrics
    
    async def get_knowledge_distribution(self) -> Dict[str, Any]:
        stats = await self.blackboard.get_statistics()
        
        return {
            "by_region": stats["by_region"],
            "by_type": stats["by_type"],
        }
    
    async def get_access_patterns(self, duration_seconds: int = 3600) -> Dict[str, Any]:
        current_time = time.time()
        cutoff_time = current_time - duration_seconds
        
        recent_ops = [
            op for op in self.blackboard._operation_log
            if op["timestamp"] >= cutoff_time
        ]
        
        by_operation = defaultdict(int)
        by_region = defaultdict(int)
        by_end = defaultdict(int)
        
        for op in recent_ops:
            by_operation[op["operation"]] += 1
            by_region[op["region"]] += 1
            by_end[op["source_end"]] += 1
        
        return {
            "duration_seconds": duration_seconds,
            "total_operations": len(recent_ops),
            "by_operation": dict(by_operation),
            "by_region": dict(by_region),
            "by_end": dict(by_end),
        }
    
    async def get_trending_keys(self, top_n: int = 10) -> List[Dict[str, Any]]:
        key_access = defaultdict(int)
        
        for knowledge in self.blackboard._storage.values():
            key_access[knowledge.key] = knowledge.access_count
        
        sorted_keys = sorted(key_access.items(), key=lambda x: x[1], reverse=True)
        
        return [
            {"key": key, "access_count": count}
            for key, count in sorted_keys[:top_n]
        ]
