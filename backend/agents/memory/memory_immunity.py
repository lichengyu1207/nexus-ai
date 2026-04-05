"""
记忆系统免疫核心模块
Memory System Immunity Core Module

实现记忆污染检测、多源验证、置信度管理、对抗性净化等功能
"""

import asyncio
import hashlib
import json
import logging
import math
import os
import random
import threading
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

logger = logging.getLogger(__name__)


class MemoryStatus(Enum):
    VALID = "valid"
    SUSPICIOUS = "suspicious"
    QUARANTINED = "quarantined"
    POLLUTED = "polluted"
    DELETED = "deleted"


class SourceType(Enum):
    USER_INPUT = "user_input"
    API_RESPONSE = "api_response"
    CRAWLER_DATA = "crawler_data"
    AGENT_GENERATED = "agent_generated"
    SYSTEM_EVENT = "system_event"
    EXTERNAL_FEED = "external_feed"
    FEDERATED_NODE = "federated_node"


class ValidationLevel(Enum):
    STRICT = "strict"
    NORMAL = "normal"
    RELAXED = "relaxed"


@dataclass
class SourceReputation:
    source_id: str
    source_type: SourceType
    reputation_score: float
    total_contributions: int
    successful_validations: int
    failed_validations: int
    last_updated: datetime
    trust_history: List[float] = field(default_factory=list)
    penalty_points: float = 0.0
    bonus_points: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "source_type": self.source_type.value,
            "reputation_score": self.reputation_score,
            "total_contributions": self.total_contributions,
            "successful_validations": self.successful_validations,
            "failed_validations": self.failed_validations,
            "last_updated": self.last_updated.isoformat(),
            "trust_history": self.trust_history[-100:],
            "penalty_points": self.penalty_points,
            "bonus_points": self.bonus_points,
        }


@dataclass
class MemoryEntity:
    entity_id: str
    entity_type: str
    entity_value: str
    confidence: float
    source_count: int
    sources: List[str]
    first_seen: datetime
    last_updated: datetime
    is_verified: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "entity_value": self.entity_value,
            "confidence": self.confidence,
            "source_count": self.source_count,
            "sources": self.sources,
            "first_seen": self.first_seen.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "is_verified": self.is_verified,
        }


@dataclass
class ValidatedMemory:
    memory_id: str
    content: str
    summary: str
    entities: List[str]
    source: str
    source_type: SourceType
    source_reputation: float
    confidence: float
    status: MemoryStatus
    validation_sources: List[str]
    cross_validated: bool
    pollution_score: float
    created_at: datetime
    last_accessed: datetime
    access_count: int
    ttl: Optional[int] = None
    expires_at: Optional[datetime] = None
    embedding: Optional[List[float]] = None
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "content": self.content,
            "summary": self.summary,
            "entities": self.entities,
            "source": self.source,
            "source_type": self.source_type.value,
            "source_reputation": self.source_reputation,
            "confidence": self.confidence,
            "status": self.status.value,
            "validation_sources": self.validation_sources,
            "cross_validated": self.cross_validated,
            "pollution_score": self.pollution_score,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "access_count": self.access_count,
            "ttl": self.ttl,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "context": self.context,
        }
    
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
    def access(self):
        self.access_count += 1
        self.last_accessed = datetime.now()


class SourceReputationManager:
    """来源信誉管理器"""
    
    def __init__(self):
        self.reputations: Dict[str, SourceReputation] = {}
        self._lock = threading.Lock()
        self.decay_rate = 0.01
        self.min_reputation = 0.0
        self.max_reputation = 100.0
        self.initial_reputation = 50.0
        
        self._init_default_sources()
        
        self.stats = {
            "total_sources": 0,
            "reputation_updates": 0,
            "penalties_applied": 0,
            "bonuses_applied": 0,
        }
    
    def _init_default_sources(self):
        default_sources = [
            ("system", SourceType.SYSTEM_EVENT, 100.0),
            ("api_internal", SourceType.API_RESPONSE, 90.0),
            ("crawler_verified", SourceType.CRAWLER_DATA, 70.0),
            ("user_verified", SourceType.USER_INPUT, 60.0),
            ("external_feed", SourceType.EXTERNAL_FEED, 50.0),
            ("federated_node", SourceType.FEDERATED_NODE, 60.0),
        ]
        
        for source_id, source_type, reputation in default_sources:
            self.reputations[source_id] = SourceReputation(
                source_id=source_id,
                source_type=source_type,
                reputation_score=reputation,
                total_contributions=0,
                successful_validations=0,
                failed_validations=0,
                last_updated=datetime.now(),
            )
    
    def get_reputation(self, source_id: str) -> float:
        with self._lock:
            if source_id in self.reputations:
                return self.reputations[source_id].reputation_score
            return self.initial_reputation
    
    def update_reputation(
        self,
        source_id: str,
        source_type: SourceType,
        success: bool,
        magnitude: float = 1.0
    ):
        with self._lock:
            if source_id not in self.reputations:
                self.reputations[source_id] = SourceReputation(
                    source_id=source_id,
                    source_type=source_type,
                    reputation_score=self.initial_reputation,
                    total_contributions=0,
                    successful_validations=0,
                    failed_validations=0,
                    last_updated=datetime.now(),
                )
                self.stats["total_sources"] += 1
            
            rep = self.reputations[source_id]
            rep.total_contributions += 1
            rep.last_updated = datetime.now()
            
            if success:
                delta = min(2.0, 1.0 * magnitude)
                rep.reputation_score = min(self.max_reputation, rep.reputation_score + delta)
                rep.successful_validations += 1
                rep.bonus_points += delta
                self.stats["bonuses_applied"] += 1
            else:
                delta = min(10.0, 5.0 * magnitude)
                rep.reputation_score = max(self.min_reputation, rep.reputation_score - delta)
                rep.failed_validations += 1
                rep.penalty_points += delta
                self.stats["penalties_applied"] += 1
            
            rep.trust_history.append(rep.reputation_score)
            if len(rep.trust_history) > 100:
                rep.trust_history = rep.trust_history[-100:]
            
            self.stats["reputation_updates"] += 1
    
    def is_trusted(self, source_id: str, threshold: float = 50.0) -> bool:
        return self.get_reputation(source_id) >= threshold
    
    def get_low_trust_sources(self, threshold: float = 30.0) -> List[str]:
        with self._lock:
            return [
                source_id for source_id, rep in self.reputations.items()
                if rep.reputation_score < threshold
            ]
    
    def apply_decay(self):
        with self._lock:
            for rep in self.reputations.values():
                if rep.source_type != SourceType.SYSTEM_EVENT:
                    decay = rep.reputation_score * self.decay_rate
                    rep.reputation_score = max(
                        self.min_reputation,
                        rep.reputation_score - decay
                    )
                    rep.trust_history.append(rep.reputation_score)


class MemoryPollutionDetector:
    """记忆污染检测器"""
    
    def __init__(self, reputation_manager: SourceReputationManager):
        self.reputation_manager = reputation_manager
        self.entity_knowledge: Dict[str, MemoryEntity] = {}
        self.conflict_patterns: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        
        self.pollution_indicators = {
            "entity_conflict": 0.4,
            "low_source_reputation": 0.3,
            "content_anomaly": 0.2,
            "temporal_inconsistency": 0.15,
            "source_pattern_anomaly": 0.25,
        }
        
        self.stats = {
            "total_checks": 0,
            "pollution_detected": 0,
            "conflicts_found": 0,
            "anomalies_found": 0,
        }
    
    def extract_entities(self, content: str) -> List[Tuple[str, str, str]]:
        entities = []
        
        import re
        
        patterns = {
            "location": r'(北京|上海|广州|深圳|杭州|南京|武汉|成都|西安|重庆|天津|苏州|郑州|长沙|东莞|青岛|沈阳|宁波|昆明)',
            "price": r'(\d+(?:\.\d+)?(?:万|亿元|元/㎡|元/平|元))',
            "area": r'(\d+(?:\.\d+)?(?:平方米|平米|㎡|平))',
            "date": r'(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?)',
            "phone": r'(1[3-9]\d{9})',
            "id_number": r'(\d{17}[\dXx])',
        }
        
        for entity_type, pattern in patterns.items():
            matches = re.findall(pattern, content)
            for match in matches:
                entity_id = hashlib.md5(f"{entity_type}:{match}".encode()).hexdigest()[:12]
                entities.append((entity_id, entity_type, match))
        
        return entities
    
    def check_entity_conflict(
        self,
        entity_id: str,
        entity_value: str,
        source: str
    ) -> Tuple[bool, float, Optional[str]]:
        with self._lock:
            if entity_id not in self.entity_knowledge:
                return False, 0.0, None
            
            known_entity = self.entity_knowledge[entity_id]
            
            if known_entity.entity_value != entity_value:
                conflict_score = self._calculate_conflict_score(
                    known_entity, entity_value, source
                )
                self.stats["conflicts_found"] += 1
                return True, conflict_score, known_entity.entity_value
            
            return False, 0.0, None
    
    def _calculate_conflict_score(
        self,
        known_entity: MemoryEntity,
        new_value: str,
        source: str
    ) -> float:
        base_score = 0.5
        
        if known_entity.is_verified:
            base_score += 0.3
        
        source_rep = self.reputation_manager.get_reputation(source)
        if source_rep < 50:
            base_score += 0.2
        elif source_rep > 80:
            base_score -= 0.2
        
        if known_entity.source_count >= 3:
            base_score += 0.1
        
        return min(1.0, base_score)
    
    def detect_pollution(
        self,
        content: str,
        source: str,
        source_type: SourceType,
        context: Dict[str, Any] = None
    ) -> Tuple[float, List[str], Dict[str, Any]]:
        self.stats["total_checks"] += 1
        
        pollution_score = 0.0
        indicators = []
        details = {
            "entity_conflicts": [],
            "content_anomalies": [],
            "source_issues": [],
        }
        
        source_rep = self.reputation_manager.get_reputation(source)
        if source_rep < 30:
            score = self.pollution_indicators["low_source_reputation"] * (1 - source_rep / 30)
            pollution_score += score
            indicators.append(f"low_source_reputation:{source_rep:.1f}")
            details["source_issues"].append({
                "type": "low_reputation",
                "score": source_rep,
                "contribution": score,
            })
        
        entities = self.extract_entities(content)
        for entity_id, entity_type, entity_value in entities:
            has_conflict, conflict_score, known_value = self.check_entity_conflict(
                entity_id, entity_value, source
            )
            if has_conflict:
                pollution_score += self.pollution_indicators["entity_conflict"] * conflict_score
                indicators.append(f"entity_conflict:{entity_type}")
                details["entity_conflicts"].append({
                    "entity_type": entity_type,
                    "new_value": entity_value,
                    "known_value": known_value,
                    "conflict_score": conflict_score,
                })
        
        anomaly_score = self._detect_content_anomaly(content)
        if anomaly_score > 0.3:
            pollution_score += self.pollution_indicators["content_anomaly"] * anomaly_score
            indicators.append(f"content_anomaly:{anomaly_score:.2f}")
            details["content_anomalies"].append({
                "score": anomaly_score,
                "type": "statistical",
            })
        
        pollution_score = min(1.0, pollution_score)
        
        if pollution_score > 0.3:
            self.stats["pollution_detected"] += 1
        
        return pollution_score, indicators, details
    
    def _detect_content_anomaly(self, content: str) -> float:
        anomaly_score = 0.0
        
        suspicious_patterns = [
            r'免费.{0,5}领取',
            r'点击.{0,5}链接',
            r'立即.{0,5}购买',
            r'限时.{0,5}优惠',
            r'恭喜.{0,5}中奖',
            r'验证码.{0,5}\d{4,6}',
        ]
        
        import re
        for pattern in suspicious_patterns:
            if re.search(pattern, content):
                anomaly_score += 0.2
        
        if len(content) > 0:
            special_char_ratio = sum(1 for c in content if not c.isalnum() and not c.isspace()) / len(content)
            if special_char_ratio > 0.3:
                anomaly_score += 0.2
        
        return min(1.0, anomaly_score)
    
    def register_entity(
        self,
        entity_id: str,
        entity_type: str,
        entity_value: str,
        source: str
    ):
        with self._lock:
            if entity_id in self.entity_knowledge:
                entity = self.entity_knowledge[entity_id]
                if source not in entity.sources:
                    entity.sources.append(source)
                    entity.source_count += 1
                entity.last_updated = datetime.now()
                if entity.source_count >= 3:
                    entity.is_verified = True
            else:
                self.entity_knowledge[entity_id] = MemoryEntity(
                    entity_id=entity_id,
                    entity_type=entity_type,
                    entity_value=entity_value,
                    confidence=0.5,
                    source_count=1,
                    sources=[source],
                    first_seen=datetime.now(),
                    last_updated=datetime.now(),
                )


class CrossValidator:
    """多源交叉验证器"""
    
    def __init__(self, min_sources: int = 2, consensus_threshold: float = 0.7):
        self.min_sources = min_sources
        self.consensus_threshold = consensus_threshold
        self._lock = threading.Lock()
        self.stats = {
            "total_validations": 0,
            "successful_validations": 0,
            "failed_validations": 0,
            "consensus_achieved": 0,
        }
    
    async def cross_validate(
        self,
        content: str,
        source: str,
        entities: List[Tuple[str, str, str]],
        external_sources: List[Callable] = None
    ) -> Tuple[bool, float, List[str]]:
        self.stats["total_validations"] += 1
        
        validation_sources = [source]
        validation_results = {source: True}
        
        if external_sources:
            for ext_source in external_sources:
                try:
                    result = await ext_source(content, entities)
                    validation_sources.append(result.get("source_id", "external"))
                    validation_results[result.get("source_id", "external")] = result.get("valid", True)
                except Exception as e:
                    logger.warning(f"External validation failed: {e}")
        
        if len(validation_sources) < self.min_sources:
            self.stats["failed_validations"] += 1
            return False, 0.5, validation_sources
        
        positive_count = sum(1 for v in validation_results.values() if v)
        consensus_ratio = positive_count / len(validation_results)
        
        if consensus_ratio >= self.consensus_threshold:
            self.stats["successful_validations"] += 1
            self.stats["consensus_achieved"] += 1
            return True, consensus_ratio, validation_sources
        else:
            self.stats["failed_validations"] += 1
            return False, consensus_ratio, validation_sources
    
    def validate_consistency(
        self,
        memories: List[ValidatedMemory]
    ) -> Tuple[bool, float, List[str]]:
        if len(memories) < 2:
            return True, 1.0, []
        
        inconsistencies = []
        
        entity_values: Dict[str, List[str]] = defaultdict(list)
        for memory in memories:
            for entity_id in memory.entities:
                entity_values[entity_id].append(memory.content)
        
        for entity_id, values in entity_values.items():
            if len(set(values)) > 1:
                inconsistencies.append(f"entity_{entity_id}")
        
        if inconsistencies:
            return False, 1.0 - len(inconsistencies) / len(entity_values), inconsistencies
        
        return True, 1.0, []


class ConfidenceManager:
    """置信度管理器"""
    
    def __init__(
        self,
        initial_confidence: float = 1.0,
        success_increment: float = 0.01,
        failure_decrement: float = 0.05,
        decay_rate: float = 0.05,
        cleanup_threshold: float = 0.3,
        cleanup_age_days: int = 180
    ):
        self.initial_confidence = initial_confidence
        self.success_increment = success_increment
        self.failure_decrement = failure_decrement
        self.decay_rate = decay_rate
        self.cleanup_threshold = cleanup_threshold
        self.cleanup_age_days = cleanup_age_days
        
        self._lock = threading.Lock()
        self.stats = {
            "total_updates": 0,
            "success_updates": 0,
            "failure_updates": 0,
            "decay_applied": 0,
            "memories_cleaned": 0,
        }
    
    def update_confidence(
        self,
        memory: ValidatedMemory,
        success: bool
    ) -> float:
        with self._lock:
            self.stats["total_updates"] += 1
            
            if success:
                memory.confidence = min(1.0, memory.confidence + self.success_increment)
                self.stats["success_updates"] += 1
            else:
                memory.confidence = max(0.0, memory.confidence - self.failure_decrement)
                self.stats["failure_updates"] += 1
            
            return memory.confidence
    
    def apply_decay(self, memories: List[ValidatedMemory]) -> int:
        decayed = 0
        with self._lock:
            for memory in memories:
                old_confidence = memory.confidence
                memory.confidence *= (1 - self.decay_rate)
                if memory.confidence != old_confidence:
                    decayed += 1
                    self.stats["decay_applied"] += 1
        
        return decayed
    
    def should_cleanup(self, memory: ValidatedMemory) -> bool:
        if memory.confidence < self.cleanup_threshold:
            age_days = (datetime.now() - memory.created_at).days
            if age_days > self.cleanup_age_days:
                return True
        return False
    
    def get_memories_to_cleanup(
        self,
        memories: List[ValidatedMemory]
    ) -> List[str]:
        to_cleanup = []
        for memory in memories:
            if self.should_cleanup(memory):
                to_cleanup.append(memory.memory_id)
                self.stats["memories_cleaned"] += 1
        
        return to_cleanup
    
    def handle_user_feedback(
        self,
        memory: ValidatedMemory,
        is_correct: bool
    ) -> float:
        if not is_correct:
            memory.confidence *= 0.5
            memory.status = MemoryStatus.SUSPICIOUS
        else:
            memory.confidence = min(1.0, memory.confidence + 0.1)
        
        return memory.confidence


class AdversarialMemoryCleaner:
    """对抗性记忆净化器"""
    
    def __init__(
        self,
        pollution_threshold: float = 0.8,
        retrain_interval_days: int = 7
    ):
        self.pollution_threshold = pollution_threshold
        self.retrain_interval_days = retrain_interval_days
        
        self.training_data: List[Tuple[List[float], int]] = []
        self.model_weights: Optional[List[float]] = None
        self.last_trained: Optional[datetime] = None
        
        self._lock = threading.Lock()
        self.stats = {
            "total_scans": 0,
            "pollution_detected": 0,
            "memories_cleaned": 0,
            "model_retrains": 0,
        }
    
    def prepare_training_data(
        self,
        clean_memories: List[ValidatedMemory],
        polluted_samples: List[Dict[str, Any]]
    ):
        with self._lock:
            self.training_data = []
            
            for memory in clean_memories:
                if memory.embedding:
                    self.training_data.append((memory.embedding, 0))
            
            for sample in polluted_samples:
                if "embedding" in sample:
                    self.training_data.append((sample["embedding"], 1))
            
            random.shuffle(self.training_data)
    
    def train(self, epochs: int = 100, learning_rate: float = 0.01):
        if not self.training_data:
            logger.warning("No training data available")
            return
        
        embedding_dim = len(self.training_data[0][0])
        
        if self.model_weights is None:
            self.model_weights = [random.gauss(0, 0.1) for _ in range(embedding_dim)]
            self.model_weights.append(0.0)
        
        for epoch in range(epochs):
            total_loss = 0.0
            
            for embedding, label in self.training_data:
                features = embedding + [1.0]
                logit = sum(w * f for w, f in zip(self.model_weights, features))
                prob = 1.0 / (1.0 + math.exp(-logit))
                
                error = label - prob
                for i in range(len(self.model_weights)):
                    self.model_weights[i] += learning_rate * error * features[i]
                
                loss = -(label * math.log(prob + 1e-10) + (1 - label) * math.log(1 - prob + 1e-10))
                total_loss += loss
            
            if (epoch + 1) % 20 == 0:
                logger.debug(f"Epoch {epoch + 1}, Loss: {total_loss / len(self.training_data):.4f}")
        
        self.last_trained = datetime.now()
        self.stats["model_retrains"] += 1
    
    def predict_pollution(self, embedding: List[float]) -> float:
        if self.model_weights is None:
            return 0.5
        
        features = embedding + [1.0]
        logit = sum(w * f for w, f in zip(self.model_weights, features))
        prob = 1.0 / (1.0 + math.exp(-logit))
        
        return prob
    
    def scan_memory(self, memory: ValidatedMemory) -> Tuple[bool, float]:
        self.stats["total_scans"] += 1
        
        if not memory.embedding:
            return False, 0.5
        
        pollution_prob = self.predict_pollution(memory.embedding)
        
        if pollution_prob > self.pollution_threshold:
            self.stats["pollution_detected"] += 1
            return True, pollution_prob
        
        return False, pollution_prob
    
    def scan_all_memories(
        self,
        memories: List[ValidatedMemory]
    ) -> List[Tuple[str, float]]:
        polluted = []
        
        for memory in memories:
            is_polluted, prob = self.scan_memory(memory)
            if is_polluted:
                polluted.append((memory.memory_id, prob))
        
        return polluted
    
    def needs_retraining(self) -> bool:
        if self.last_trained is None:
            return True
        
        days_since = (datetime.now() - self.last_trained).days
        return days_since >= self.retrain_interval_days
    
    def repair_memory(
        self,
        memory: ValidatedMemory,
        similar_memories: List[ValidatedMemory]
    ) -> ValidatedMemory:
        if not similar_memories:
            memory.status = MemoryStatus.QUARANTINED
            return memory
        
        best_replacement = max(similar_memories, key=lambda m: m.confidence)
        
        memory.content = best_replacement.content
        memory.confidence = best_replacement.confidence * 0.9
        memory.status = MemoryStatus.VALID
        memory.pollution_score = 0.0
        
        self.stats["memories_cleaned"] += 1
        
        return memory


class MemoryIsolationZone:
    """记忆隔离区"""
    
    def __init__(self, max_size: int = 10000, auto_cleanup_days: int = 30):
        self.max_size = max_size
        self.auto_cleanup_days = auto_cleanup_days
        
        self.quarantined_memories: Dict[str, ValidatedMemory] = {}
        self.review_queue: deque = deque(maxlen=1000)
        self.review_results: Dict[str, Dict[str, Any]] = {}
        
        self._lock = threading.Lock()
        self.stats = {
            "total_quarantined": 0,
            "total_released": 0,
            "total_deleted": 0,
            "pending_reviews": 0,
        }
    
    def quarantine(self, memory: ValidatedMemory, reason: str) -> bool:
        with self._lock:
            if len(self.quarantined_memories) >= self.max_size:
                self._cleanup_oldest()
            
            memory.status = MemoryStatus.QUARANTINED
            self.quarantined_memories[memory.memory_id] = memory
            
            self.review_queue.append({
                "memory_id": memory.memory_id,
                "reason": reason,
                "quarantine_time": datetime.now(),
                "status": "pending",
            })
            
            self.stats["total_quarantined"] += 1
            self.stats["pending_reviews"] = len([
                r for r in self.review_queue if r["status"] == "pending"
            ])
            
            return True
    
    def release(self, memory_id: str, reviewer: str = "system") -> Optional[ValidatedMemory]:
        with self._lock:
            if memory_id not in self.quarantined_memories:
                return None
            
            memory = self.quarantined_memories.pop(memory_id)
            memory.status = MemoryStatus.VALID
            
            self.review_results[memory_id] = {
                "action": "released",
                "reviewer": reviewer,
                "review_time": datetime.now(),
            }
            
            self.stats["total_released"] += 1
            self.stats["pending_reviews"] = len([
                r for r in self.review_queue if r["status"] == "pending"
            ])
            
            return memory
    
    def delete(self, memory_id: str, reviewer: str = "system") -> bool:
        with self._lock:
            if memory_id not in self.quarantined_memories:
                return False
            
            memory = self.quarantined_memories.pop(memory_id)
            memory.status = MemoryStatus.DELETED
            
            self.review_results[memory_id] = {
                "action": "deleted",
                "reviewer": reviewer,
                "review_time": datetime.now(),
            }
            
            self.stats["total_deleted"] += 1
            self.stats["pending_reviews"] = len([
                r for r in self.review_queue if r["status"] == "pending"
            ])
            
            return True
    
    def get_pending_reviews(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            pending = [
                r for r in self.review_queue if r["status"] == "pending"
            ]
            return pending[:limit]
    
    def _cleanup_oldest(self):
        if not self.quarantined_memories:
            return
        
        cutoff = datetime.now() - timedelta(days=self.auto_cleanup_days)
        
        to_delete = [
            mid for mid, m in self.quarantined_memories.items()
            if m.created_at < cutoff
        ]
        
        for mid in to_delete:
            self.delete(mid, "auto_cleanup")
    
    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                **self.stats,
                "current_size": len(self.quarantined_memories),
                "max_size": self.max_size,
            }


class MemoryImmunitySystem:
    """记忆免疫系统主控"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        self.reputation_manager = SourceReputationManager()
        self.pollution_detector = MemoryPollutionDetector(self.reputation_manager)
        self.cross_validator = CrossValidator(
            min_sources=self.config.get("min_sources", 2),
            consensus_threshold=self.config.get("consensus_threshold", 0.7)
        )
        self.confidence_manager = ConfidenceManager(
            initial_confidence=self.config.get("initial_confidence", 1.0),
            success_increment=self.config.get("success_increment", 0.01),
            failure_decrement=self.config.get("failure_decrement", 0.05)
        )
        self.cleaner = AdversarialMemoryCleaner(
            pollution_threshold=self.config.get("pollution_threshold", 0.8)
        )
        self.isolation_zone = MemoryIsolationZone(
            max_size=self.config.get("isolation_max_size", 10000)
        )
        
        self.memories: Dict[str, ValidatedMemory] = {}
        self._lock = threading.Lock()
        
        self._running = False
        self._maintenance_task = None
        
        self.stats = {
            "total_stored": 0,
            "total_rejected": 0,
            "total_quarantined": 0,
            "total_validated": 0,
        }
    
    async def start(self):
        self._running = True
        self._maintenance_task = asyncio.create_task(self._periodic_maintenance())
    
    def stop(self):
        self._running = False
        if self._maintenance_task:
            self._maintenance_task.cancel()
    
    async def _periodic_maintenance(self):
        while self._running:
            try:
                await self._run_maintenance()
                await asyncio.sleep(3600)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Maintenance error: {e}")
                await asyncio.sleep(60)
    
    async def _run_maintenance(self):
        self.reputation_manager.apply_decay()
        
        memories_list = list(self.memories.values())
        self.confidence_manager.apply_decay(memories_list)
        
        to_cleanup = self.confidence_manager.get_memories_to_cleanup(memories_list)
        for memory_id in to_cleanup:
            if memory_id in self.memories:
                memory = self.memories[memory_id]
                self.isolation_zone.quarantine(memory, "low_confidence_cleanup")
                del self.memories[memory_id]
        
        if self.cleaner.needs_retraining():
            clean_memories = [m for m in memories_list if m.status == MemoryStatus.VALID]
            self.cleaner.train()
    
    async def store_memory(
        self,
        content: str,
        source: str,
        source_type: SourceType,
        summary: str = "",
        entities: List[str] = None,
        context: Dict[str, Any] = None,
        external_validators: List[Callable] = None
    ) -> Tuple[bool, Optional[ValidatedMemory], str]:
        
        pollution_score, indicators, details = self.pollution_detector.detect_pollution(
            content, source, source_type, context
        )
        
        if pollution_score > 0.7:
            self.stats["total_rejected"] += 1
            self.reputation_manager.update_reputation(source, source_type, False, pollution_score)
            return False, None, f"High pollution score: {pollution_score:.2f}"
        
        extracted_entities = self.pollution_detector.extract_entities(content)
        entity_ids = [e[0] for e in extracted_entities]
        
        is_validated, consensus, validation_sources = await self.cross_validator.cross_validate(
            content, source, extracted_entities, external_validators
        )
        
        source_rep = self.reputation_manager.get_reputation(source)
        
        confidence = self.confidence_manager.initial_confidence
        confidence *= (source_rep / 100.0)
        if is_validated:
            confidence *= (0.8 + 0.2 * consensus)
        
        status = MemoryStatus.VALID
        if pollution_score > 0.4 or not is_validated:
            status = MemoryStatus.SUSPICIOUS
        
        memory_id = f"mem_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        memory = ValidatedMemory(
            memory_id=memory_id,
            content=content,
            summary=summary or content[:100],
            entities=entity_ids,
            source=source,
            source_type=source_type,
            source_reputation=source_rep,
            confidence=confidence,
            status=status,
            validation_sources=validation_sources,
            cross_validated=is_validated,
            pollution_score=pollution_score,
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            access_count=0,
            context=context or {},
        )
        
        if status == MemoryStatus.SUSPICIOUS and pollution_score > 0.5:
            self.isolation_zone.quarantine(memory, f"pollution_score:{pollution_score:.2f}")
            self.stats["total_quarantined"] += 1
            return True, memory, "Quarantined for review"
        
        with self._lock:
            self.memories[memory_id] = memory
        
        for entity_id, entity_type, entity_value in extracted_entities:
            self.pollution_detector.register_entity(entity_id, entity_type, entity_value, source)
        
        self.reputation_manager.update_reputation(source, source_type, True)
        self.stats["total_stored"] += 1
        self.stats["total_validated"] += 1
        
        return True, memory, "Success"
    
    def retrieve_memory(
        self,
        memory_id: str,
        update_access: bool = True
    ) -> Optional[ValidatedMemory]:
        with self._lock:
            memory = self.memories.get(memory_id)
            if memory and update_access:
                memory.access()
            return memory
    
    def search_memories(
        self,
        query: str,
        min_confidence: float = 0.3,
        limit: int = 10
    ) -> List[Tuple[ValidatedMemory, float]]:
        results = []
        query_lower = query.lower()
        
        with self._lock:
            for memory in self.memories.values():
                if memory.confidence < min_confidence:
                    continue
                if memory.status not in [MemoryStatus.VALID, MemoryStatus.SUSPICIOUS]:
                    continue
                
                relevance = 0.0
                if query_lower in memory.content.lower():
                    relevance = 0.8
                elif query_lower in memory.summary.lower():
                    relevance = 0.6
                elif any(query_lower in e.lower() for e in memory.entities):
                    relevance = 0.4
                
                if relevance > 0:
                    relevance *= memory.confidence
                    results.append((memory, relevance))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]
    
    def report_feedback(
        self,
        memory_id: str,
        is_correct: bool,
        user_id: str = "anonymous"
    ) -> bool:
        memory = self.retrieve_memory(memory_id)
        if not memory:
            return False
        
        self.confidence_manager.handle_user_feedback(memory, is_correct)
        
        self.reputation_manager.update_reputation(
            memory.source,
            memory.source_type,
            is_correct
        )
        
        if not is_correct and memory.confidence < 0.3:
            self.isolation_zone.quarantine(memory, f"user_feedback:{user_id}")
            with self._lock:
                if memory_id in self.memories:
                    del self.memories[memory_id]
        
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "memory_system": self.stats,
            "reputation_manager": {
                "total_sources": len(self.reputation_manager.reputations),
                **self.reputation_manager.stats,
            },
            "pollution_detector": self.pollution_detector.stats,
            "cross_validator": self.cross_validator.stats,
            "confidence_manager": self.confidence_manager.stats,
            "cleaner": self.cleaner.stats,
            "isolation_zone": self.isolation_zone.get_stats(),
        }
