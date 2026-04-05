"""
活体记忆智能体
Living Memory Agent

具备生命特征的记忆智能体，能够主动挖掘、关联、预测
"""

import os
import json
import time
import logging
import threading
import random
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from collections import deque, defaultdict
from dataclasses import dataclass, field
from enum import Enum
import numpy as np

from .living_agent import LivingAgent, AgentRole, AgentStatus

logger = logging.getLogger(__name__)


class MemoryType(Enum):
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"
    COLLECTIVE = "collective"


class MemoryPriority(Enum):
    CRITICAL = 5
    HIGH = 4
    NORMAL = 3
    LOW = 2
    ARCHIVE = 1


@dataclass
class MemoryEntry:
    memory_id: str
    memory_type: MemoryType
    content: Dict
    importance: float = 0.5
    access_count: int = 0
    last_accessed: float = 0
    created_at: float = 0
    expires_at: Optional[float] = None
    tags: List[str] = field(default_factory=list)
    associations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "memory_id": self.memory_id,
            "memory_type": self.memory_type.value,
            "content": self.content,
            "importance": self.importance,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "tags": self.tags,
            "associations": self.associations
        }


class LivingMemoryAgent(LivingAgent):
    
    def __init__(
        self,
        agent_id: str,
        species: str = "memory",
        initial_energy: float = 100.0,
        memory_capacity: int = 10000,
        retrieval_accuracy: float = 0.8,
        **kwargs
    ):
        super().__init__(
            agent_id=agent_id,
            role=AgentRole.MEMORY,
            species=species,
            initial_energy=initial_energy,
            **kwargs
        )
        
        self.memory_capacity = memory_capacity
        self.retrieval_accuracy = retrieval_accuracy
        
        self.memory_store: Dict[str, MemoryEntry] = {}
        self.memory_index: Dict[str, Set[str]] = defaultdict(set)
        self.tag_index: Dict[str, Set[str]] = defaultdict(set)
        
        self.association_graph: Dict[str, Set[str]] = defaultdict(set)
        
        self.pending_queries: deque = deque(maxlen=1000)
        self.query_history: deque = deque(maxlen=5000)
        
        self.memory_clusters: Dict[str, List[str]] = {}
        self.predictions: List[Dict] = []
        
        self._init_memory_genes()
    
    def _init_memory_genes(self):
        from .living_agent import Gene
        
        self.gene_pool.add_gene(Gene(
            gene_id="gene_retention",
            name="memory_retention",
            value=0.8,
            mutation_rate=0.1,
            mutation_range=(-0.1, 0.1)
        ))
        
        self.gene_pool.add_gene(Gene(
            gene_id="gene_retrieval",
            name="retrieval_speed",
            value=0.7,
            mutation_rate=0.1,
            mutation_range=(-0.1, 0.1)
        ))
        
        self.gene_pool.add_gene(Gene(
            gene_id="gene_association",
            name="association_strength",
            value=0.6,
            mutation_rate=0.1,
            mutation_range=(-0.1, 0.1)
        ))
    
    def _live_cycle(self):
        self.status = AgentStatus.WORKING
        
        self._process_pending_queries()
        
        self._mine_patterns()
        
        self._build_associations()
        
        self._make_predictions()
        
        self._cleanup_expired_memories()
        
        self._rebalance_memory()
        
        self.status = AgentStatus.IDLE
    
    def store(
        self,
        key: str,
        value: Dict,
        memory_type: MemoryType = MemoryType.EPISODIC,
        importance: float = 0.5,
        tags: Optional[List[str]] = None,
        ttl: Optional[int] = None
    ) -> str:
        memory_id = self._generate_memory_id(key, value)
        
        expires_at = None
        if ttl:
            expires_at = time.time() + ttl
        
        entry = MemoryEntry(
            memory_id=memory_id,
            memory_type=memory_type,
            content={"key": key, "value": value},
            importance=importance,
            tags=tags or [],
            created_at=time.time(),
            expires_at=expires_at
        )
        
        if len(self.memory_store) >= self.memory_capacity:
            self._evict_low_importance()
        
        self.memory_store[memory_id] = entry
        
        self.memory_index[key].add(memory_id)
        
        for tag in (tags or []):
            self.tag_index[tag].add(memory_id)
        
        self.add_energy(0.5)
        
        logger.debug(f"Memory {memory_id} stored by agent {self.agent_id}")
        
        return memory_id
    
    def retrieve(
        self,
        query: str,
        top_k: int = 10,
        min_importance: float = 0.0
    ) -> List[Dict]:
        results = []
        
        retrieval_gene = self.gene_pool.get_gene("retrieval_speed")
        retrieval_accuracy = retrieval_gene.value if retrieval_gene else self.retrieval_accuracy
        
        for memory_id, entry in self.memory_store.items():
            if entry.importance < min_importance:
                continue
            
            relevance = self._calculate_relevance(query, entry)
            
            if relevance > 0.1 and random.random() < retrieval_accuracy:
                entry.access_count += 1
                entry.last_accessed = time.time()
                
                results.append({
                    "memory_id": memory_id,
                    "content": entry.content,
                    "relevance": relevance,
                    "importance": entry.importance,
                    "memory_type": entry.memory_type.value
                })
        
        results.sort(key=lambda x: x["relevance"] * x["importance"], reverse=True)
        
        self.add_energy(0.1 * min(len(results), top_k))
        
        return results[:top_k]
    
    def _calculate_relevance(self, query: str, entry: MemoryEntry) -> float:
        query_lower = query.lower()
        content_str = json.dumps(entry.content).lower()
        
        if query_lower in content_str:
            return 1.0
        
        if query_lower in entry.content.get("key", "").lower():
            return 0.9
        
        for tag in entry.tags:
            if query_lower in tag.lower():
                return 0.7
        
        query_words = set(query_lower.split())
        content_words = set(content_str.split())
        
        overlap = len(query_words & content_words)
        if overlap > 0:
            return overlap / max(len(query_words), 1) * 0.5
        
        return 0.0
    
    def _generate_memory_id(self, key: str, value: Dict) -> str:
        content = f"{key}_{json.dumps(value, sort_keys=True)}_{time.time()}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def _evict_low_importance(self):
        if not self.memory_store:
            return
        
        retention_gene = self.gene_pool.get_gene("memory_retention")
        retention = retention_gene.value if retention_gene else 0.8
        
        entries = list(self.memory_store.items())
        entries.sort(key=lambda x: x[1].importance * retention + 
                               x[1].access_count * 0.1)
        
        evict_count = max(1, int(len(entries) * 0.1))
        
        for memory_id, _ in entries[:evict_count]:
            self._delete_memory(memory_id)
    
    def _delete_memory(self, memory_id: str):
        if memory_id not in self.memory_store:
            return
        
        entry = self.memory_store[memory_id]
        
        key = entry.content.get("key", "")
        if key in self.memory_index:
            self.memory_index[key].discard(memory_id)
        
        for tag in entry.tags:
            if tag in self.tag_index:
                self.tag_index[tag].discard(memory_id)
        
        if memory_id in self.association_graph:
            for associated_id in self.association_graph[memory_id]:
                if associated_id in self.association_graph:
                    self.association_graph[associated_id].discard(memory_id)
            del self.association_graph[memory_id]
        
        del self.memory_store[memory_id]
    
    def _process_pending_queries(self):
        while self.pending_queries:
            query = self.pending_queries.popleft()
            
            results = self.retrieve(
                query.get("query", ""),
                top_k=query.get("top_k", 10)
            )
            
            self.query_history.append({
                "query": query,
                "results_count": len(results),
                "timestamp": time.time()
            })
            
            if self.blackboard:
                self.blackboard.write(
                    f"memory:result:{query.get('query_id', '')}",
                    {
                        "results": results,
                        "responder_id": self.agent_id,
                        "timestamp": time.time()
                    },
                    ttl=60
                )
    
    def _mine_patterns(self):
        if len(self.memory_store) < 100:
            return
        
        energy_cost = 5.0
        if not self.consume_energy(energy_cost):
            return
        
        type_memories = defaultdict(list)
        for memory_id, entry in self.memory_store.items():
            type_memories[entry.memory_type].append(entry)
        
        for memory_type, entries in type_memories.items():
            if len(entries) < 10:
                continue
            
            key_patterns = defaultdict(int)
            for entry in entries:
                key = entry.content.get("key", "")
                key_parts = key.split(":")
                if len(key_parts) >= 2:
                    pattern = ":".join(key_parts[:2])
                    key_patterns[pattern] += 1
            
            for pattern, count in key_patterns.items():
                if count >= 5:
                    pattern_memory = self.store(
                        f"pattern:{pattern}",
                        {
                            "pattern": pattern,
                            "occurrence_count": count,
                            "memory_type": memory_type.value,
                            "mined_at": time.time()
                        },
                        memory_type=MemoryType.COLLECTIVE,
                        importance=0.7,
                        tags=["pattern", "mined"]
                    )
    
    def _build_associations(self):
        if len(self.memory_store) < 50:
            return
        
        association_gene = self.gene_pool.get_gene("association_strength")
        association_strength = association_gene.value if association_gene else 0.6
        
        entries = list(self.memory_store.values())
        
        for i, entry1 in enumerate(entries):
            for entry2 in entries[i+1:i+10]:
                similarity = self._calculate_similarity(entry1, entry2)
                
                if similarity > association_strength:
                    self.association_graph[entry1.memory_id].add(entry2.memory_id)
                    self.association_graph[entry2.memory_id].add(entry1.memory_id)
                    
                    entry1.associations.append(entry2.memory_id)
                    entry2.associations.append(entry1.memory_id)
    
    def _calculate_similarity(self, entry1: MemoryEntry, entry2: MemoryEntry) -> float:
        tags1 = set(entry1.tags)
        tags2 = set(entry2.tags)
        
        if tags1 and tags2:
            jaccard = len(tags1 & tags2) / len(tags1 | tags2)
            if jaccard > 0.3:
                return jaccard
        
        if entry1.memory_type == entry2.memory_type:
            return 0.4
        
        return 0.0
    
    def _make_predictions(self):
        if len(self.query_history) < 20:
            return
        
        recent_queries = list(self.query_history)[-100:]
        
        query_patterns = defaultdict(int)
        for q in recent_queries:
            query_type = q.get("query", {}).get("type", "unknown")
            query_patterns[query_type] += 1
        
        predictions = []
        for query_type, count in query_patterns.items():
            if count >= 5:
                predictions.append({
                    "predicted_query_type": query_type,
                    "confidence": min(0.9, count / len(recent_queries)),
                    "based_on": "query_pattern"
                })
        
        self.predictions = predictions
        
        if predictions and self.blackboard:
            self.blackboard.write(
                f"memory:predictions:{self.agent_id}",
                {
                    "predictions": predictions,
                    "agent_id": self.agent_id,
                    "timestamp": time.time()
                },
                ttl=3600
            )
    
    def _cleanup_expired_memories(self):
        current_time = time.time()
        expired = [
            memory_id for memory_id, entry in self.memory_store.items()
            if entry.expires_at and current_time > entry.expires_at
        ]
        
        for memory_id in expired:
            self._delete_memory(memory_id)
        
        if expired:
            logger.debug(f"Cleaned up {len(expired)} expired memories")
    
    def _rebalance_memory(self):
        if len(self.memory_store) < self.memory_capacity * 0.8:
            return
        
        for memory_id, entry in self.memory_store.items():
            time_decay = 1.0
            if entry.last_accessed > 0:
                hours_since_access = (time.time() - entry.last_accessed) / 3600
                time_decay = max(0.1, 1.0 - hours_since_access / 168)
            
            entry.importance *= time_decay
    
    def get_associated_memories(self, memory_id: str, depth: int = 2) -> List[Dict]:
        if memory_id not in self.association_graph:
            return []
        
        visited = set()
        queue = [(memory_id, 0)]
        results = []
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            if current_id in self.memory_store:
                entry = self.memory_store[current_id]
                results.append({
                    "memory_id": current_id,
                    "content": entry.content,
                    "importance": entry.importance,
                    "depth": current_depth
                })
            
            for associated_id in self.association_graph.get(current_id, []):
                if associated_id not in visited:
                    queue.append((associated_id, current_depth + 1))
        
        return results[1:]
    
    def get_state(self) -> Dict:
        state = super().get_state()
        state.update({
            "memory_count": len(self.memory_store),
            "memory_capacity": self.memory_capacity,
            "utilization": len(self.memory_store) / self.memory_capacity,
            "index_count": len(self.memory_index),
            "tag_count": len(self.tag_index),
            "association_count": sum(len(v) for v in self.association_graph.values()) // 2,
            "predictions_count": len(self.predictions)
        })
        return state
