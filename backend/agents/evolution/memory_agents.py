"""
记忆智能体集群模块
Memory Agent Cluster Module

实现情景记忆、语义记忆、程序性记忆智能体
"""

import os
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import random
import numpy as np

import torch
import torch.nn as nn

logger = logging.getLogger(__name__)


class MemoryType(Enum):
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"


@dataclass
class MemoryRecord:
    memory_id: str
    memory_type: MemoryType
    content: Any
    embedding: Optional[np.ndarray] = None
    metadata: Dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    importance_score: float = 0.5
    
    def to_dict(self) -> Dict:
        return {
            "memory_id": self.memory_id,
            "memory_type": self.memory_type.value,
            "content": self.content if not isinstance(self.content, np.ndarray) else self.content.tolist(),
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "access_count": self.access_count,
            "importance_score": self.importance_score
        }


class MemoryEncoder(nn.Module):
    
    def __init__(self, input_dim: int = 256, hidden_dim: int = 128, output_dim: int = 64):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, output_dim)
        )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class MemoryRetriever(nn.Module):
    
    def __init__(self, query_dim: int = 64, memory_dim: int = 64):
        super().__init__()
        self.attention = nn.MultiheadAttention(
            embed_dim=memory_dim,
            num_heads=4
        )
    
    def forward(self, query: torch.Tensor, memories: torch.Tensor) -> torch.Tensor:
        if memories.dim() == 2:
            memories = memories.unsqueeze(0)
        
        attended, _ = self.attention(query, memories, memories)
        return attended


class BaseMemoryAgent:
    
    def __init__(
        self,
        agent_id: str,
        memory_type: MemoryType,
        capacity: int = 10000,
        embedding_dim: int = 64
    ):
        self.agent_id = agent_id
        self.memory_type = memory_type
        self.capacity = capacity
        self.embedding_dim = embedding_dim
        
        self.memories: Dict[str, MemoryRecord] = {}
        self.memory_order: deque = deque(maxlen=capacity)
        
        self.encoder = MemoryEncoder(output_dim=embedding_dim)
        self.retriever = MemoryRetriever(embedding_dim)
        
        self.access_stats = {
            "total_stores": 0,
            "total_retrieves": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }
        
        self.diagnosis_history: List[Dict] = []
    
    def store(self, key: str, value: Any, metadata: Optional[Dict] = None) -> str:
        memory_id = f"mem_{self.memory_type.value}_{int(time.time() * 1000)}"
        
        embedding = self._encode(value)
        
        record = MemoryRecord(
            memory_id=memory_id,
            memory_type=self.memory_type,
            content=value,
            embedding=embedding,
            metadata=metadata or {}
        )
        
        if len(self.memories) >= self.capacity:
            self._evict()
        
        self.memories[memory_id] = record
        self.memory_order.append(memory_id)
        
        self.access_stats["total_stores"] += 1
        
        return memory_id
    
    def retrieve(self, query: Any, top_k: int = 5) -> List[MemoryRecord]:
        self.access_stats["total_retrieves"] += 1
        
        if not self.memories:
            self.access_stats["cache_misses"] += 1
            return []
        
        query_embedding = self._encode(query)
        
        similarities = []
        for memory_id, record in self.memories.items():
            if record.embedding is not None:
                sim = self._cosine_similarity(query_embedding, record.embedding)
                similarities.append((memory_id, sim))
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        results = []
        for memory_id, sim in similarities[:top_k]:
            if memory_id in self.memories:
                record = self.memories[memory_id]
                record.last_accessed = datetime.now()
                record.access_count += 1
                results.append(record)
        
        if results:
            self.access_stats["cache_hits"] += 1
        else:
            self.access_stats["cache_misses"] += 1
        
        return results
    
    def _encode(self, value: Any) -> np.ndarray:
        if isinstance(value, np.ndarray):
            tensor = torch.FloatTensor(value)
        elif isinstance(value, dict):
            tensor = torch.FloatTensor(list(value.values())[:256])
            if len(tensor) < 256:
                tensor = torch.cat([tensor, torch.zeros(256 - len(tensor))])
        elif isinstance(value, str):
            tensor = torch.zeros(256)
            for i, c in enumerate(value[:256]):
                tensor[i] = ord(c) / 255.0
        else:
            tensor = torch.zeros(256)
        
        with torch.no_grad():
            embedding = self.encoder(tensor.unsqueeze(0)).squeeze(0).numpy()
        
        return embedding
    
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))
    
    def _evict(self):
        if not self.memory_order:
            return
        
        oldest_id = self.memory_order[0]
        
        min_access = float('inf')
        evict_id = oldest_id
        for mid in list(self.memory_order)[:100]:
            if mid in self.memories:
                record = self.memories[mid]
                score = record.access_count / (record.importance_score + 0.1)
                if score < min_access:
                    min_access = score
                    evict_id = mid
        
        if evict_id in self.memories:
            del self.memories[evict_id]
            self.memory_order.remove(evict_id)
    
    def analyze(self) -> Dict:
        if not self.memories:
            return {
                "status": "no_memories",
                "suggestion": None
            }
        
        recent = [
            r for r in self.memories.values()
            if (datetime.now() - r.created_at).total_seconds() < 86400
        ]
        
        if not recent:
            return {
                "status": "stale",
                "suggestion": f"{self.memory_type.value}记忆库已超过24小时无更新，建议检查数据源"
            }
        
        avg_importance = np.mean([r.importance_score for r in recent])
        avg_access = np.mean([r.access_count for r in recent])
        
        if avg_importance < 0.3:
            return {
                "status": "low_quality",
                "suggestion": f"{self.memory_type.value}记忆平均重要性过低({avg_importance:.2f})，建议检查数据质量"
            }
        
        if avg_access < 1:
            return {
                "status": "underutilized",
                "suggestion": f"{self.memory_type.value}记忆利用率低，建议优化检索策略或清理无用记忆"
            }
        
        return {
            "status": "healthy",
            "memory_count": len(self.memories),
            "avg_importance": avg_importance,
            "avg_access": avg_access
        }
    
    def get_status(self) -> Dict:
        return {
            "agent_id": self.agent_id,
            "memory_type": self.memory_type.value,
            "memory_count": len(self.memories),
            "capacity": self.capacity,
            "access_stats": self.access_stats.copy()
        }


class EpisodicMemoryAgent(BaseMemoryAgent):
    
    def __init__(self, agent_id: str = "episodic_memory", capacity: int = 50000):
        super().__init__(agent_id, MemoryType.EPISODIC, capacity)
        
        self.user_sessions: Dict[str, List[str]] = {}
        self.interest_tracker: Dict[str, Dict] = {}
    
    def store_interaction(
        self,
        user_id: str,
        interaction_type: str,
        content: Dict,
        session_id: Optional[str] = None
    ):
        if session_id is None:
            session_id = f"session_{int(time.time())}"
        
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = []
        self.user_sessions[user_id].append(session_id)
        
        memory_id = self.store(
            key=f"{user_id}_{session_id}",
            value={
                "user_id": user_id,
                "session_id": session_id,
                "interaction_type": interaction_type,
                "content": content,
                "timestamp": datetime.now().isoformat()
            },
            metadata={"user_id": user_id, "session_id": session_id}
        )
        
        self._update_interest(user_id, interaction_type, content)
        
        return memory_id
    
    def _update_interest(self, user_id: str, interaction_type: str, content: Dict):
        if user_id not in self.interest_tracker:
            self.interest_tracker[user_id] = {}
        
        if interaction_type not in self.interest_tracker[user_id]:
            self.interest_tracker[user_id][interaction_type] = 0
        
        self.interest_tracker[user_id][interaction_type] += 1
    
    def detect_interest_change(self, user_id: str) -> Optional[Dict]:
        if user_id not in self.interest_tracker:
            return None
        
        interests = self.interest_tracker[user_id]
        if not interests:
            return None
        
        sorted_interests = sorted(interests.items(), key=lambda x: x[1], reverse=True)
        
        if len(sorted_interests) < 2:
            return None
        
        top_interest = sorted_interests[0][0]
        
        recent_memories = [
            r for r in self.memories.values()
            if r.metadata.get("user_id") == user_id
            and (datetime.now() - r.created_at).total_seconds() < 86400
        ]
        
        if not recent_memories:
            return None
        
        recent_top_interests = {}
        for r in recent_memories[-100:]:
            interaction_type = r.content.get("interaction_type")
            if interaction_type:
                recent_top_interests[interaction_type] = recent_top_interests.get(interaction_type, 0) + 1
        
        if not recent_top_interests:
            return None
        
        current_top = max(recent_top_interests.items(), key=lambda x: x[1])[0]
        
        if current_top != top_interest:
            return {
                "previous_top_interest": top_interest,
                "current_top_interest": current_top,
                "suggestion": f"用户{user_id}兴趣从{top_interest}转向{current_top}，建议更新用户画像"
            }
        
        return None
    
    def get_user_history(self, user_id: str, limit: int = 50) -> List[MemoryRecord]:
        user_memories = [
            r for r in self.memories.values()
            if r.metadata.get("user_id") == user_id
        ]
        
        user_memories.sort(key=lambda r: r.created_at, reverse=True)
        
        return user_memories[:limit]


class SemanticMemoryAgent(BaseMemoryAgent):
    
    def __init__(self, agent_id: str = "semantic_memory", capacity: int = 100000):
        super().__init__(agent_id, MemoryType.SEMANTIC, capacity)
        
        self.knowledge_graph: Dict[str, Dict] = {}
        self.entity_index: Dict[str, List[str]] = {}
        self.last_update: Dict[str, datetime] = {}
    
    def store_knowledge(
        self,
        entity_type: str,
        entity_id: str,
        knowledge: Dict,
        relations: Optional[List[Dict]] = None
    ):
        memory_id = self.store(
            key=f"{entity_type}_{entity_id}",
            value=knowledge,
            metadata={
                "entity_type": entity_type,
                "entity_id": entity_id,
                "relations": relations or []
            }
        )
        
        if entity_type not in self.knowledge_graph:
            self.knowledge_graph[entity_type] = {}
        self.knowledge_graph[entity_type][entity_id] = {
            "memory_id": memory_id,
            "relations": relations or []
        }
        
        if entity_id not in self.entity_index:
            self.entity_index[entity_id] = []
        self.entity_index[entity_id].append(memory_id)
        
        self.last_update[f"{entity_type}_{entity_id}"] = datetime.now()
        
        return memory_id
    
    def query_knowledge(
        self,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        query: Optional[str] = None
    ) -> List[MemoryRecord]:
        if entity_type and entity_id:
            key = f"{entity_type}_{entity_id}"
            if key in self.memories:
                return [self.memories[key]]
        
        if query:
            return self.retrieve(query)
        
        return []
    
    def check_stale_knowledge(self, days: int = 90) -> List[Dict]:
        cutoff = datetime.now() - timedelta(days=days)
        stale_entities = []
        
        for key, last_update in self.last_update.items():
            if last_update < cutoff:
                parts = key.split("_", 1)
                if len(parts) == 2:
                    stale_entities.append({
                        "entity_type": parts[0],
                        "entity_id": parts[1],
                        "last_update": last_update.isoformat(),
                        "suggestion": f"{key}知识已超过{days}天未更新，建议重新爬取数据"
                    })
        
        return stale_entities
    
    def get_related_knowledge(self, entity_type: str, entity_id: str, depth: int = 2) -> List[MemoryRecord]:
        if entity_type not in self.knowledge_graph:
            return []
        
        if entity_id not in self.knowledge_graph[entity_type]:
            return []
        
        visited = set()
        results = []
        queue = [(entity_type, entity_id, 0)]
        
        while queue:
            current_type, current_id, current_depth = queue.pop(0)
            
            key = f"{current_type}_{current_id}"
            if key in visited:
                continue
            
            visited.add(key)
            
            if key in self.memories:
                results.append(self.memories[key])
            
            if current_depth < depth:
                if current_type in self.knowledge_graph:
                    if current_id in self.knowledge_graph[current_type]:
                        for relation in self.knowledge_graph[current_type][current_id].get("relations", []):
                            target_type = relation.get("target_type")
                            target_id = relation.get("target_id")
                            if target_type and target_id:
                                queue.append((target_type, target_id, current_depth + 1))
        
        return results


class ProceduralMemoryAgent(BaseMemoryAgent):
    
    def __init__(self, agent_id: str = "procedural_memory", capacity: int = 10000):
        super().__init__(agent_id, MemoryType.PROCEDURAL, capacity)
        
        self.skill_registry: Dict[str, Dict] = {}
        self.execution_history: Dict[str, List[Dict]] = {}
    
    def store_skill(
        self,
        skill_name: str,
        skill_type: str,
        parameters: Dict,
        success_conditions: List[str],
        execution_steps: List[Dict]
    ):
        memory_id = self.store(
            key=f"skill_{skill_name}",
            value={
                "skill_name": skill_name,
                "skill_type": skill_type,
                "parameters": parameters,
                "success_conditions": success_conditions,
                "execution_steps": execution_steps
            },
            metadata={"skill_type": skill_type}
        )
        
        self.skill_registry[skill_name] = {
            "memory_id": memory_id,
            "success_rate": 0.0,
            "execution_count": 0
        }
        
        return memory_id
    
    def record_execution(
        self,
        skill_name: str,
        success: bool,
        duration_ms: float,
        context: Optional[Dict] = None
    ):
        if skill_name not in self.execution_history:
            self.execution_history[skill_name] = []
        
        execution_record = {
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "duration_ms": duration_ms,
            "context": context or {}
        }
        
        self.execution_history[skill_name].append(execution_record)
        
        if skill_name in self.skill_registry:
            registry = self.skill_registry[skill_name]
            registry["execution_count"] += 1
            
            recent = self.execution_history[skill_name][-100:]
            registry["success_rate"] = sum(1 for e in recent if e["success"]) / len(recent)
    
    def get_skill(self, skill_name: str) -> Optional[MemoryRecord]:
        key = f"skill_{skill_name}"
        if key in self.memories:
            return self.memories[key]
        return None
    
    def detect_skill_decay(self, threshold: float = 0.7) -> List[Dict]:
        decayed_skills = []
        
        for skill_name, registry in self.skill_registry.items():
            if registry["execution_count"] < 10:
                continue
            
            if registry["success_rate"] < threshold:
                recent = self.execution_history.get(skill_name, [])[-50:]
                avg_duration = np.mean([e["duration_ms"] for e in recent]) if recent else 0
                
                decayed_skills.append({
                    "skill_name": skill_name,
                    "success_rate": registry["success_rate"],
                    "execution_count": registry["execution_count"],
                    "avg_duration_ms": avg_duration,
                    "suggestion": f"技能{skill_name}成功率({registry['success_rate']:.2%})低于阈值，建议重新训练或调整参数"
                })
        
        return decayed_skills
    
    def suggest_skill_improvement(self, skill_name: str) -> Optional[Dict]:
        if skill_name not in self.execution_history:
            return None
        
        history = self.execution_history[skill_name]
        if len(history) < 20:
            return None
        
        recent = history[-50:]
        success_rate = sum(1 for e in recent if e["success"]) / len(recent)
        avg_duration = np.mean([e["duration_ms"] for e in recent])
        
        suggestions = []
        
        if success_rate < 0.8:
            suggestions.append("成功率偏低，建议增加训练样本或调整参数")
        
        if avg_duration > 1000:
            suggestions.append("执行时间过长，建议优化执行流程")
        
        durations = [e["duration_ms"] for e in recent]
        duration_std = np.std(durations)
        if duration_std > avg_duration * 0.5:
            suggestions.append("执行时间波动大，建议检查环境稳定性")
        
        if suggestions:
            return {
                "skill_name": skill_name,
                "success_rate": success_rate,
                "avg_duration_ms": avg_duration,
                "suggestions": suggestions
            }
        
        return None


class MemoryAgentCluster:
    
    def __init__(self):
        self.episodic = EpisodicMemoryAgent()
        self.semantic = SemanticMemoryAgent()
        self.procedural = ProceduralMemoryAgent()
        
        self.message_queue: Dict[str, List[Dict]] = {
            "episodic": [],
            "semantic": [],
            "procedural": []
        }
    
    def store_user_interaction(
        self,
        user_id: str,
        interaction_type: str,
        content: Dict
    ) -> str:
        memory_id = self.episodic.store_interaction(
            user_id, interaction_type, content
        )
        
        if interaction_type in ["property_query", "valuation_request"]:
            self._notify_semantic(user_id, content)
        
        return memory_id
    
    def store_knowledge(
        self,
        entity_type: str,
        entity_id: str,
        knowledge: Dict,
        relations: Optional[List[Dict]] = None
    ) -> str:
        return self.semantic.store_knowledge(
            entity_type, entity_id, knowledge, relations
        )
    
    def store_skill(
        self,
        skill_name: str,
        skill_type: str,
        parameters: Dict,
        success_conditions: List[str],
        execution_steps: List[Dict]
    ) -> str:
        return self.procedural.store_skill(
            skill_name, skill_type, parameters, success_conditions, execution_steps
        )
    
    def _notify_semantic(self, user_id: str, content: Dict):
        if "property_id" in content:
            self.message_queue["semantic"].append({
                "type": "preload_request",
                "user_id": user_id,
                "property_id": content["property_id"],
                "timestamp": datetime.now().isoformat()
            })
    
    def process_messages(self):
        semantic_messages = self.message_queue["semantic"]
        
        for msg in semantic_messages:
            if msg["type"] == "preload_request":
                property_id = msg.get("property_id")
                if property_id:
                    knowledge = self.semantic.query_knowledge(
                        entity_type="property",
                        entity_id=property_id
                    )
                    
                    if not knowledge:
                        self.message_queue["episodic"].append({
                            "type": "knowledge_missing",
                            "property_id": property_id,
                            "timestamp": datetime.now().isoformat()
                        })
        
        self.message_queue["semantic"] = []
    
    def analyze_all(self) -> Dict:
        results = {
            "episodic": self.episodic.analyze(),
            "semantic": {
                "stale_knowledge": self.semantic.check_stale_knowledge(),
                "memory_count": len(self.semantic.memories)
            },
            "procedural": {
                "decayed_skills": self.procedural.detect_skill_decay(),
                "skill_count": len(self.procedural.skill_registry)
            }
        }
        
        suggestions = []
        
        if results["episodic"].get("suggestion"):
            suggestions.append(results["episodic"]["suggestion"])
        
        for stale in results["semantic"]["stale_knowledge"]:
            suggestions.append(stale["suggestion"])
        
        for decayed in results["procedural"]["decayed_skills"]:
            suggestions.append(decayed["suggestion"])
        
        results["suggestions"] = suggestions
        
        return results
    
    def get_cluster_status(self) -> Dict:
        return {
            "episodic": self.episodic.get_status(),
            "semantic": self.semantic.get_status(),
            "procedural": self.procedural.get_status(),
            "pending_messages": {
                k: len(v) for k, v in self.message_queue.items()
            }
        }


memory_cluster = MemoryAgentCluster()
