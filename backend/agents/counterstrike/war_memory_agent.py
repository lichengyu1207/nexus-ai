"""
作战记忆智能体
War Memory Agent

存储、检索、分析所有与作战相关的记忆
实现向量检索、时序检索、关联检索
"""

import asyncio
import time
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from collections import defaultdict, deque
import structlog

logger = structlog.get_logger()


class MemoryType(Enum):
    ATTACKER_PROFILE = "attacker_profile"
    TACTICAL_PATTERN = "tactical_pattern"
    OPERATION_LOG = "operation_log"
    COUNTER_STRIKE_RESULT = "counter_strike_result"
    THREAT_INTELLIGENCE = "threat_intelligence"
    BEHAVIOR_PATTERN = "behavior_pattern"
    MITIGATION_STRATEGY = "mitigation_strategy"


class MemoryPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class WarMemory:
    memory_id: str
    memory_type: MemoryType
    timestamp: datetime
    content: Dict[str, Any]
    embedding: Optional[List[float]]
    tags: Set[str]
    priority: MemoryPriority
    access_count: int
    last_accessed: datetime
    related_memories: List[str]
    distilled: bool
    source: str
    confidence: float
    
    def to_dict(self) -> Dict:
        return {
            "memory_id": self.memory_id,
            "memory_type": self.memory_type.value,
            "timestamp": self.timestamp.isoformat(),
            "content": self.content,
            "tags": list(self.tags),
            "priority": self.priority.value,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat(),
            "related_memories": self.related_memories,
            "distilled": self.distilled,
            "source": self.source,
            "confidence": self.confidence
        }


class VectorIndex:
    def __init__(self, dimension: int = 128):
        self.dimension = dimension
        self.vectors: Dict[str, List[float]] = {}
        self.metadata: Dict[str, Dict] = {}
        
    def add(self, memory_id: str, vector: List[float], metadata: Dict):
        if len(vector) != self.dimension:
            vector = self._pad_or_truncate(vector)
            
        self.vectors[memory_id] = vector
        self.metadata[memory_id] = metadata
        
    def remove(self, memory_id: str):
        self.vectors.pop(memory_id, None)
        self.metadata.pop(memory_id, None)
        
    def search(self, query_vector: List[float], k: int = 10) -> List[Tuple[str, float]]:
        if len(query_vector) != self.dimension:
            query_vector = self._pad_or_truncate(query_vector)
            
        scores = []
        for memory_id, vector in self.vectors.items():
            score = self._cosine_similarity(query_vector, vector)
            scores.append((memory_id, score))
            
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:k]
        
    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        dot_product = sum(a * b for a, b in zip(v1, v2))
        norm1 = sum(a * a for a in v1) ** 0.5
        norm2 = sum(b * b for b in v2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        return dot_product / (norm1 * norm2)
        
    def _pad_or_truncate(self, vector: List[float]) -> List[float]:
        if len(vector) < self.dimension:
            return vector + [0.0] * (self.dimension - len(vector))
        else:
            return vector[:self.dimension]


class TimeIndex:
    def __init__(self):
        self.time_buckets: Dict[str, Set[str]] = defaultdict(set)
        
    def add(self, memory_id: str, timestamp: datetime):
        bucket_keys = [
            timestamp.strftime("%Y-%m-%d"),
            timestamp.strftime("%Y-%m-%d %H"),
            timestamp.strftime("%Y-%m")
        ]
        
        for key in bucket_keys:
            self.time_buckets[key].add(memory_id)
            
    def remove(self, memory_id: str):
        for key in list(self.time_buckets.keys()):
            self.time_buckets[key].discard(memory_id)
            if not self.time_buckets[key]:
                del self.time_buckets[key]
                
    def query_range(
        self,
        start: datetime,
        end: datetime
    ) -> Set[str]:
        result = set()
        current = start
        
        while current <= end:
            bucket_key = current.strftime("%Y-%m-%d")
            result.update(self.time_buckets.get(bucket_key, set()))
            current += timedelta(days=1)
            
        return result


class AssociationIndex:
    def __init__(self):
        self.associations: Dict[str, Set[str]] = defaultdict(set)
        self.entity_to_memories: Dict[str, Set[str]] = defaultdict(set)
        
    def add_association(self, memory_id: str, entity: str):
        self.associations[memory_id].add(entity)
        self.entity_to_memories[entity].add(memory_id)
        
    def remove_memory(self, memory_id: str):
        entities = self.associations.pop(memory_id, set())
        for entity in entities:
            self.entity_to_memories[entity].discard(memory_id)
            
    def query_by_entity(self, entity: str) -> Set[str]:
        return self.entity_to_memories.get(entity, set())
        
    def query_by_entities(self, entities: List[str]) -> Set[str]:
        if not entities:
            return set()
            
        result = self.entity_to_memories.get(entities[0], set())
        for entity in entities[1:]:
            result &= self.entity_to_memories.get(entity, set())
            
        return result


class MemoryDistiller:
    def __init__(self):
        self.distillation_rules = self._load_rules()
        
    def _load_rules(self) -> Dict[str, Dict]:
        return {
            "attacker_profile": {
                "min_samples": 3,
                "retention_days": 90,
                "extract_fields": ["actor_type", "capabilities", "motivation"]
            },
            "tactical_pattern": {
                "min_samples": 5,
                "retention_days": 180,
                "extract_fields": ["formation", "effectiveness", "conditions"]
            },
            "counter_strike_result": {
                "min_samples": 10,
                "retention_days": 30,
                "extract_fields": ["action_type", "effectiveness", "side_effects"]
            }
        }
        
    def distill(self, memories: List[WarMemory]) -> Optional[Dict]:
        if not memories:
            return None
            
        memory_type = memories[0].memory_type.value
        rule = self.distillation_rules.get(memory_type, {})
        
        if len(memories) < rule.get("min_samples", 3):
            return None
            
        distilled = {
            "memory_type": memory_type,
            "sample_count": len(memories),
            "distilled_at": datetime.now().isoformat(),
            "patterns": {}
        }
        
        extract_fields = rule.get("extract_fields", [])
        for field in extract_fields:
            values = []
            for m in memories:
                value = m.content.get(field)
                if value:
                    values.append(value)
                    
            if values:
                if isinstance(values[0], (list, set)):
                    all_items = set()
                    for v in values:
                        all_items.update(v if isinstance(v, (list, set)) else [v])
                    distilled["patterns"][field] = list(all_items)
                elif isinstance(values[0], dict):
                    distilled["patterns"][field] = values[0]
                else:
                    from collections import Counter
                    counter = Counter(values)
                    distilled["patterns"][field] = dict(counter.most_common(5))
                    
        distilled["confidence"] = min(0.9, len(memories) / 20)
        
        return distilled


class WarMemoryAgent:
    def __init__(
        self,
        agent_id: str = "war_memory_agent_001",
        communication_bus: Optional[Any] = None
    ):
        self.agent_id = agent_id
        self.communication_bus = communication_bus
        
        self.memories: Dict[str, WarMemory] = {}
        self.vector_index = VectorIndex()
        self.time_index = TimeIndex()
        self.association_index = AssociationIndex()
        self.distiller = MemoryDistiller()
        
        self.short_term_memory: deque = deque(maxlen=100)
        self.long_term_memory: Dict[str, WarMemory] = {}
        self.parameterized_knowledge: Dict[str, Dict] = {}
        
        self.stats = {
            "total_memories": 0,
            "queries_served": 0,
            "distillations_performed": 0,
            "cache_hits": 0,
            "avg_query_time_ms": 0.0
        }
        
        self._running = False
        self._task: Optional[asyncio.Task] = None
        
    async def start(self):
        self._running = True
        self._task = asyncio.create_task(self._maintenance_loop())
        logger.info(f"WarMemoryAgent {self.agent_id} started")
        
    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info(f"WarMemoryAgent {self.agent_id} stopped")
        
    async def _maintenance_loop(self):
        while self._running:
            try:
                await self._cleanup_old_memories()
                await self._run_distillation()
                await asyncio.sleep(300)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in maintenance loop: {e}")
                await asyncio.sleep(30)
                
    async def _cleanup_old_memories(self):
        cutoff = datetime.now() - timedelta(days=90)
        
        to_remove = []
        for memory_id, memory in self.memories.items():
            if memory.timestamp < cutoff and memory.priority.value < MemoryPriority.HIGH.value:
                to_remove.append(memory_id)
                
        for memory_id in to_remove:
            await self.forget_memory(memory_id)
            
        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} old memories")
            
    async def _run_distillation(self):
        for memory_type in [MemoryType.ATTACKER_PROFILE, MemoryType.TACTICAL_PATTERN, MemoryType.COUNTER_STRIKE_RESULT]:
            memories = [
                m for m in self.memories.values()
                if m.memory_type == memory_type and not m.distilled
            ]
            
            if len(memories) >= 5:
                distilled = self.distiller.distill(memories)
                if distilled:
                    knowledge_id = f"knowledge_{memory_type.value}_{int(time.time())}"
                    self.parameterized_knowledge[knowledge_id] = distilled
                    
                    for m in memories:
                        m.distilled = True
                        
                    self.stats["distillations_performed"] += 1
                    logger.info(f"Distilled {len(memories)} memories of type {memory_type.value}")
                    
    async def store(
        self,
        memory_type: MemoryType,
        content: Dict[str, Any],
        tags: Optional[Set[str]] = None,
        priority: MemoryPriority = MemoryPriority.MEDIUM,
        source: str = "unknown",
        confidence: float = 1.0
    ) -> WarMemory:
        memory_id = self._generate_memory_id()
        now = datetime.now()
        
        embedding = await self._generate_embedding(content)
        
        memory = WarMemory(
            memory_id=memory_id,
            memory_type=memory_type,
            timestamp=now,
            content=content,
            embedding=embedding,
            tags=tags or set(),
            priority=priority,
            access_count=0,
            last_accessed=now,
            related_memories=[],
            distilled=False,
            source=source,
            confidence=confidence
        )
        
        self.memories[memory_id] = memory
        self.short_term_memory.append(memory_id)
        
        if embedding:
            self.vector_index.add(memory_id, embedding, {"type": memory_type.value})
            
        self.time_index.add(memory_id, now)
        
        entities = self._extract_entities(content)
        for entity in entities:
            self.association_index.add_association(memory_id, entity)
            
        self.stats["total_memories"] += 1
        
        logger.debug(f"Stored memory {memory_id} of type {memory_type.value}")
        
        return memory
        
    async def _generate_embedding(self, content: Dict) -> List[float]:
        content_str = json.dumps(content, sort_keys=True)
        hash_bytes = hashlib.md5(content_str.encode()).digest()
        
        embedding = []
        for i in range(0, len(hash_bytes), 2):
            if i + 1 < len(hash_bytes):
                value = (hash_bytes[i] * 256 + hash_bytes[i + 1]) / 65536.0
                embedding.append(value)
                
        while len(embedding) < 128:
            embedding.append(0.0)
            
        return embedding[:128]
        
    def _extract_entities(self, content: Dict) -> List[str]:
        entities = []
        
        if "attacker_id" in content:
            entities.append(f"attacker:{content['attacker_id']}")
        if "identity_id" in content:
            entities.append(f"identity:{content['identity_id']}")
        if "ip" in content or "source_ip" in content:
            entities.append(f"ip:{content.get('ip') or content.get('source_ip')}")
        if "actor_type" in content:
            entities.append(f"actor:{content['actor_type']}")
        if "attack_type" in content:
            entities.append(f"attack:{content['attack_type']}")
        if "action_type" in content:
            entities.append(f"action:{content['action_type']}")
            
        return entities
        
    async def retrieve(self, memory_id: str) -> Optional[WarMemory]:
        memory = self.memories.get(memory_id)
        if memory:
            memory.access_count += 1
            memory.last_accessed = datetime.now()
            self.stats["cache_hits"] += 1
        return memory
        
    async def search_similar(
        self,
        query: Dict,
        k: int = 10
    ) -> List[Tuple[WarMemory, float]]:
        start_time = time.time()
        
        query_embedding = await self._generate_embedding(query)
        results = self.vector_index.search(query_embedding, k)
        
        memories = []
        for memory_id, score in results:
            memory = await self.retrieve(memory_id)
            if memory:
                memories.append((memory, score))
                
        duration = (time.time() - start_time) * 1000
        self._update_avg_query_time(duration)
        self.stats["queries_served"] += 1
        
        return memories
        
    async def search_by_time(
        self,
        start: datetime,
        end: datetime,
        memory_type: Optional[MemoryType] = None
    ) -> List[WarMemory]:
        memory_ids = self.time_index.query_range(start, end)
        
        memories = []
        for mid in memory_ids:
            memory = await self.retrieve(mid)
            if memory:
                if memory_type is None or memory.memory_type == memory_type:
                    memories.append(memory)
                    
        return sorted(memories, key=lambda m: m.timestamp)
        
    async def search_by_entity(
        self,
        entities: List[str]
    ) -> List[WarMemory]:
        memory_ids = self.association_index.query_by_entities(entities)
        
        memories = []
        for mid in memory_ids:
            memory = await self.retrieve(mid)
            if memory:
                memories.append(memory)
                
        return memories
        
    async def search_by_tags(
        self,
        tags: Set[str],
        match_all: bool = True
    ) -> List[WarMemory]:
        memories = []
        
        for memory in self.memories.values():
            if match_all:
                if tags.issubset(memory.tags):
                    memories.append(memory)
            else:
                if tags & memory.tags:
                    memories.append(memory)
                    
        return memories
        
    async def get_attacker_history(self, attacker_id: str) -> List[Dict]:
        memories = await self.search_by_entity([f"attacker:{attacker_id}", f"identity:{attacker_id}"])
        
        history = []
        for memory in memories:
            history.append({
                "memory_id": memory.memory_id,
                "memory_type": memory.memory_type.value,
                "timestamp": memory.timestamp.isoformat(),
                "content": memory.content,
                "confidence": memory.confidence
            })
            
        return sorted(history, key=lambda x: x["timestamp"])
        
    async def get_tactical_patterns(self, conditions: Dict) -> List[Dict]:
        similar = await self.search_similar(conditions, k=20)
        
        patterns = []
        for memory, score in similar:
            if memory.memory_type == MemoryType.TACTICAL_PATTERN:
                patterns.append({
                    "pattern": memory.content,
                    "relevance": score,
                    "source": memory.source
                })
                
        return patterns
        
    async def get_effective_countermeasures(
        self,
        attack_type: str,
        actor_type: Optional[str] = None
    ) -> List[Dict]:
        entities = [f"attack:{attack_type}"]
        if actor_type:
            entities.append(f"actor:{actor_type}")
            
        memories = await self.search_by_entity(entities)
        
        countermeasures = []
        for memory in memories:
            if memory.memory_type == MemoryType.COUNTER_STRIKE_RESULT:
                if memory.content.get("effectiveness", 0) > 0.5:
                    countermeasures.append({
                        "action_type": memory.content.get("action_type"),
                        "effectiveness": memory.content.get("effectiveness"),
                        "conditions": memory.content.get("conditions", {}),
                        "memory_id": memory.memory_id
                    })
                    
        return sorted(countermeasures, key=lambda x: x["effectiveness"], reverse=True)
        
    async def forget_memory(self, memory_id: str) -> bool:
        if memory_id not in self.memories:
            return False
            
        self.vector_index.remove(memory_id)
        self.time_index.remove(memory_id)
        self.association_index.remove_memory(memory_id)
        
        del self.memories[memory_id]
        
        return True
        
    async def link_memories(self, memory_id1: str, memory_id2: str):
        if memory_id1 in self.memories and memory_id2 in self.memories:
            self.memories[memory_id1].related_memories.append(memory_id2)
            self.memories[memory_id2].related_memories.append(memory_id1)
            
    async def get_parameterized_knowledge(self) -> Dict[str, Dict]:
        return self.parameterized_knowledge
        
    async def get_memory_stats(self) -> Dict:
        type_counts = defaultdict(int)
        for memory in self.memories.values():
            type_counts[memory.memory_type.value] += 1
            
        return {
            **self.stats,
            "type_distribution": dict(type_counts),
            "short_term_count": len(self.short_term_memory),
            "long_term_count": len(self.long_term_memory),
            "parameterized_count": len(self.parameterized_knowledge)
        }
        
    def _generate_memory_id(self) -> str:
        return f"mem_{int(time.time() * 1000)}_{hashlib.md5(str(time.time()).encode()).hexdigest()[:8]}"
        
    def _update_avg_query_time(self, duration: float):
        current = self.stats["avg_query_time_ms"]
        count = self.stats["queries_served"]
        self.stats["avg_query_time_ms"] = (current * (count - 1) + duration) / count
        
    def get_stats(self) -> Dict:
        return self.stats
