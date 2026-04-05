"""
攻击模式识别器模块
Attack Pattern Recognizer Module

实现攻击模式实时识别、新型攻击检测、集体防御协调等功能
"""

import asyncio
import hashlib
import json
import logging
import math
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


class AttackSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AttackStatus(Enum):
    DETECTED = "detected"
    ANALYZING = "analyzing"
    CONFIRMED = "confirmed"
    MITIGATED = "mitigated"
    FALSE_POSITIVE = "false_positive"


class PatternMatchType(Enum):
    EXACT = "exact"
    SIMILAR = "similar"
    NOVEL = "novel"


@dataclass
class AttackFeature:
    feature_id: str
    name: str
    value: float
    weight: float
    category: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "feature_id": self.feature_id,
            "name": self.name,
            "value": self.value,
            "weight": self.weight,
            "category": self.category,
        }


@dataclass
class AttackPattern:
    pattern_id: str
    name: str
    attack_type: str
    features: List[AttackFeature]
    feature_vector: List[float]
    severity: AttackSeverity
    description: str
    mitigation_steps: List[str]
    first_seen: datetime
    last_seen: datetime
    occurrence_count: int
    success_rate: float
    source_nodes: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_id": self.pattern_id,
            "name": self.name,
            "attack_type": self.attack_type,
            "features": [f.to_dict() for f in self.features],
            "severity": self.severity.value,
            "description": self.description,
            "mitigation_steps": self.mitigation_steps,
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "occurrence_count": self.occurrence_count,
            "success_rate": self.success_rate,
            "source_nodes": self.source_nodes,
        }
    
    def get_feature_vector(self) -> List[float]:
        return [f.value for f in self.features]


@dataclass
class AttackEvent:
    event_id: str
    timestamp: datetime
    source_ip: str
    source_node: str
    attack_type: str
    features: Dict[str, float]
    raw_data: Dict[str, Any]
    severity: AttackSeverity
    status: AttackStatus
    matched_pattern: Optional[str]
    similarity_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "source_ip": self.source_ip,
            "source_node": self.source_node,
            "attack_type": self.attack_type,
            "features": self.features,
            "severity": self.severity.value,
            "status": self.status.value,
            "matched_pattern": self.matched_pattern,
            "similarity_score": self.similarity_score,
        }


@dataclass
class NovelAttackAlert:
    alert_id: str
    event: AttackEvent
    detected_at: datetime
    priority: int
    samples_collected: int
    required_samples: int
    analysis_status: str
    assigned_analysts: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "event": self.event.to_dict(),
            "detected_at": self.detected_at.isoformat(),
            "priority": self.priority,
            "samples_collected": self.samples_collected,
            "required_samples": self.required_samples,
            "analysis_status": self.analysis_status,
            "assigned_analysts": self.assigned_analysts,
        }


class AttackPatternLibrary:
    """攻击模式库"""
    
    def __init__(self, similarity_threshold: float = 0.8):
        self.similarity_threshold = similarity_threshold
        
        self.patterns: Dict[str, AttackPattern] = {}
        self.pattern_vectors: Dict[str, List[float]] = {}
        self.feature_index: Dict[str, Set[str]] = defaultdict(set)
        
        self._lock = threading.Lock()
        
        self.stats = {
            "total_patterns": 0,
            "pattern_matches": 0,
            "novel_detections": 0,
            "pattern_updates": 0,
        }
        
        self._init_default_patterns()
    
    def _init_default_patterns(self):
        default_patterns = [
            {
                "name": "DDoS攻击",
                "attack_type": "ddos",
                "features": [
                    ("request_rate", 1000, 0.3),
                    ("unique_ips", 10000, 0.25),
                    ("bandwidth_usage", 0.9, 0.2),
                    ("connection_count", 50000, 0.15),
                    ("packet_rate", 100000, 0.1),
                ],
                "severity": AttackSeverity.HIGH,
                "description": "分布式拒绝服务攻击特征",
                "mitigation_steps": ["启用流量清洗", "限制连接速率", "启用CDN防护"],
            },
            {
                "name": "SQL注入",
                "attack_type": "sql_injection",
                "features": [
                    ("sql_keywords_count", 5, 0.3),
                    ("quote_anomaly", 1, 0.25),
                    ("union_keyword", 1, 0.2),
                    ("comment_injection", 1, 0.15),
                    ("error_message_leak", 1, 0.1),
                ],
                "severity": AttackSeverity.HIGH,
                "description": "SQL注入攻击特征",
                "mitigation_steps": ["参数化查询", "输入验证", "WAF规则更新"],
            },
            {
                "name": "暴力破解",
                "attack_type": "brute_force",
                "features": [
                    ("auth_failures", 10, 0.3),
                    ("unique_user_attempts", 5, 0.25),
                    ("rapid_requests", 100, 0.2),
                    ("common_passwords", 1, 0.15),
                    ("distributed_sources", 1, 0.1),
                ],
                "severity": AttackSeverity.MEDIUM,
                "description": "暴力破解攻击特征",
                "mitigation_steps": ["账户锁定", "验证码", "速率限制"],
            },
            {
                "name": "XSS攻击",
                "attack_type": "xss",
                "features": [
                    ("script_tags", 1, 0.3),
                    ("event_handlers", 1, 0.25),
                    ("javascript_protocol", 1, 0.2),
                    ("encoded_payload", 1, 0.15),
                    ("dom_manipulation", 1, 0.1),
                ],
                "severity": AttackSeverity.MEDIUM,
                "description": "跨站脚本攻击特征",
                "mitigation_steps": ["输出编码", "CSP策略", "输入过滤"],
            },
        ]
        
        for pattern_data in default_patterns:
            pattern_id = f"pattern_{pattern_data['attack_type']}_{uuid.uuid4().hex[:8]}"
            
            features = [
                AttackFeature(
                    feature_id=f"feat_{i}_{uuid.uuid4().hex[:6]}",
                    name=f[0],
                    value=f[1],
                    weight=f[2],
                    category="traffic"
                )
                for i, f in enumerate(pattern_data["features"])
            ]
            
            pattern = AttackPattern(
                pattern_id=pattern_id,
                name=pattern_data["name"],
                attack_type=pattern_data["attack_type"],
                features=features,
                feature_vector=[f.value for f in features],
                severity=pattern_data["severity"],
                description=pattern_data["description"],
                mitigation_steps=pattern_data["mitigation_steps"],
                first_seen=datetime.now(),
                last_seen=datetime.now(),
                occurrence_count=0,
                success_rate=0.0,
                source_nodes=[],
            )
            
            self.patterns[pattern_id] = pattern
            self.pattern_vectors[pattern_id] = pattern.feature_vector
            self.stats["total_patterns"] += 1
    
    def add_pattern(self, pattern: AttackPattern) -> str:
        with self._lock:
            self.patterns[pattern.pattern_id] = pattern
            self.pattern_vectors[pattern.pattern_id] = pattern.feature_vector
            
            for feature in pattern.features:
                self.feature_index[feature.name].add(pattern.pattern_id)
            
            self.stats["total_patterns"] += 1
            
            return pattern.pattern_id
    
    def find_matching_pattern(
        self,
        feature_vector: List[float],
        threshold: float = None
    ) -> Tuple[Optional[AttackPattern], float, PatternMatchType]:
        threshold = threshold or self.similarity_threshold
        
        if not self.pattern_vectors:
            return None, 0.0, PatternMatchType.NOVEL
        
        best_pattern = None
        best_similarity = 0.0
        
        with self._lock:
            for pattern_id, stored_vector in self.pattern_vectors.items():
                similarity = self._cosine_similarity(feature_vector, stored_vector)
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_pattern = self.patterns[pattern_id]
        
        if best_similarity >= threshold:
            self.stats["pattern_matches"] += 1
            return best_pattern, best_similarity, PatternMatchType.SIMILAR
        elif best_similarity >= threshold * 0.6:
            return best_pattern, best_similarity, PatternMatchType.SIMILAR
        else:
            self.stats["novel_detections"] += 1
            return None, best_similarity, PatternMatchType.NOVEL
    
    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        if len(v1) != len(v2):
            min_len = min(len(v1), len(v2))
            v1 = v1[:min_len]
            v2 = v2[:min_len]
        
        if not v1 or not v2:
            return 0.0
        
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = math.sqrt(sum(a * a for a in v1))
        norm2 = math.sqrt(sum(b * b for b in v2))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot / (norm1 * norm2)
    
    def update_pattern_stats(
        self,
        pattern_id: str,
        success: bool,
        source_node: str = None
    ):
        with self._lock:
            if pattern_id not in self.patterns:
                return
            
            pattern = self.patterns[pattern_id]
            pattern.occurrence_count += 1
            pattern.last_seen = datetime.now()
            
            if success:
                pattern.success_rate = (
                    pattern.success_rate * (pattern.occurrence_count - 1) + 1.0
                ) / pattern.occurrence_count
            else:
                pattern.success_rate = (
                    pattern.success_rate * (pattern.occurrence_count - 1)
                ) / pattern.occurrence_count
            
            if source_node and source_node not in pattern.source_nodes:
                pattern.source_nodes.append(source_node)
            
            self.stats["pattern_updates"] += 1
    
    def get_patterns_by_type(self, attack_type: str) -> List[AttackPattern]:
        with self._lock:
            return [
                p for p in self.patterns.values()
                if p.attack_type == attack_type
            ]


class NovelAttackHandler:
    """新型攻击处理器"""
    
    def __init__(
        self,
        pattern_library: AttackPatternLibrary,
        required_samples: int = 10
    ):
        self.pattern_library = pattern_library
        self.required_samples = required_samples
        
        self.novel_attacks: Dict[str, NovelAttackAlert] = {}
        self.sample_buffer: Dict[str, List[AttackEvent]] = defaultdict(list)
        
        self._lock = threading.Lock()
        
        self.stats = {
            "novel_attacks_detected": 0,
            "patterns_created": 0,
            "alerts_broadcast": 0,
            "samples_collected": 0,
        }
    
    def handle_novel_attack(
        self,
        event: AttackEvent,
        similarity_score: float
    ) -> NovelAttackAlert:
        self.stats["novel_attacks_detected"] += 1
        
        alert_id = f"alert_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        priority = self._calculate_priority(event, similarity_score)
        
        alert = NovelAttackAlert(
            alert_id=alert_id,
            event=event,
            detected_at=datetime.now(),
            priority=priority,
            samples_collected=1,
            required_samples=self.required_samples,
            analysis_status="collecting_samples",
            assigned_analysts=[],
        )
        
        with self._lock:
            self.novel_attacks[alert_id] = alert
            self.sample_buffer[alert_id].append(event)
        
        return alert
    
    def add_sample(self, alert_id: str, event: AttackEvent) -> bool:
        with self._lock:
            if alert_id not in self.novel_attacks:
                return False
            
            self.sample_buffer[alert_id].append(event)
            self.stats["samples_collected"] += 1
            
            alert = self.novel_attacks[alert_id]
            alert.samples_collected = len(self.sample_buffer[alert_id])
            
            if alert.samples_collected >= alert.required_samples:
                self._create_pattern_from_samples(alert_id)
                return True
            
            return False
    
    def _calculate_priority(
        self,
        event: AttackEvent,
        similarity_score: float
    ) -> int:
        priority = 5
        
        if event.severity == AttackSeverity.CRITICAL:
            priority = 1
        elif event.severity == AttackSeverity.HIGH:
            priority = 2
        elif event.severity == AttackSeverity.MEDIUM:
            priority = 3
        
        if similarity_score < 0.3:
            priority = max(1, priority - 1)
        
        return priority
    
    def _create_pattern_from_samples(self, alert_id: str):
        samples = self.sample_buffer[alert_id]
        
        if not samples:
            return
        
        feature_aggregates: Dict[str, List[float]] = defaultdict(list)
        
        for sample in samples:
            for feature_name, value in sample.features.items():
                feature_aggregates[feature_name].append(value)
        
        avg_features = {
            name: sum(values) / len(values)
            for name, values in feature_aggregates.items()
        }
        
        sorted_features = sorted(
            avg_features.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )[:10]
        
        features = [
            AttackFeature(
                feature_id=f"feat_{i}_{uuid.uuid4().hex[:6]}",
                name=name,
                value=value,
                weight=1.0 / (i + 1),
                category="derived"
            )
            for i, (name, value) in enumerate(sorted_features)
        ]
        
        pattern = AttackPattern(
            pattern_id=f"pattern_novel_{int(time.time())}_{uuid.uuid4().hex[:8]}",
            name=f"新型攻击_{alert_id[:8]}",
            attack_type="unknown",
            features=features,
            feature_vector=[f.value for f in features],
            severity=AttackSeverity.HIGH,
            description=f"从{len(samples)}个样本中自动生成的攻击模式",
            mitigation_steps=["监控", "分析", "隔离"],
            first_seen=datetime.now(),
            last_seen=datetime.now(),
            occurrence_count=len(samples),
            success_rate=0.0,
            source_nodes=list(set(s.source_node for s in samples)),
        )
        
        self.pattern_library.add_pattern(pattern)
        self.stats["patterns_created"] += 1
        
        with self._lock:
            self.novel_attacks[alert_id].analysis_status = "pattern_created"
            del self.sample_buffer[alert_id]
    
    def get_active_alerts(self, priority: int = None) -> List[NovelAttackAlert]:
        with self._lock:
            alerts = list(self.novel_attacks.values())
            
            if priority:
                alerts = [a for a in alerts if a.priority <= priority]
            
            return sorted(alerts, key=lambda a: a.priority)


class CollectiveDefenseCoordinator:
    """集体防御协调器"""
    
    def __init__(self, pattern_library: AttackPatternLibrary):
        self.pattern_library = pattern_library
        
        self.registered_nodes: Dict[str, Dict[str, Any]] = {}
        self.defense_broadcasts: deque = deque(maxlen=1000)
        self.active_defenses: Dict[str, Dict[str, Any]] = {}
        
        self._lock = threading.Lock()
        
        self.stats = {
            "nodes_registered": 0,
            "broadcasts_sent": 0,
            "defenses_coordinated": 0,
            "successful_mitigations": 0,
        }
    
    def register_node(
        self,
        node_id: str,
        capabilities: List[str],
        endpoint: str
    ) -> bool:
        with self._lock:
            self.registered_nodes[node_id] = {
                "node_id": node_id,
                "capabilities": capabilities,
                "endpoint": endpoint,
                "registered_at": datetime.now(),
                "last_heartbeat": datetime.now(),
                "active": True,
            }
            self.stats["nodes_registered"] += 1
        
        return True
    
    def unregister_node(self, node_id: str) -> bool:
        with self._lock:
            if node_id in self.registered_nodes:
                self.registered_nodes[node_id]["active"] = False
                return True
        return False
    
    def broadcast_threat(
        self,
        pattern: AttackPattern,
        source_node: str,
        severity: AttackSeverity
    ) -> str:
        broadcast_id = f"broadcast_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        broadcast = {
            "broadcast_id": broadcast_id,
            "pattern": pattern.to_dict(),
            "source_node": source_node,
            "severity": severity.value,
            "timestamp": datetime.now().isoformat(),
            "target_nodes": [],
            "responses": {},
        }
        
        with self._lock:
            for node_id, node_info in self.registered_nodes.items():
                if node_info["active"] and node_id != source_node:
                    broadcast["target_nodes"].append(node_id)
            
            self.defense_broadcasts.append(broadcast)
            self.stats["broadcasts_sent"] += 1
        
        return broadcast_id
    
    def receive_broadcast_response(
        self,
        broadcast_id: str,
        node_id: str,
        response: Dict[str, Any]
    ):
        with self._lock:
            for broadcast in self.defense_broadcasts:
                if broadcast["broadcast_id"] == broadcast_id:
                    broadcast["responses"][node_id] = {
                        "node_id": node_id,
                        "response": response,
                        "timestamp": datetime.now().isoformat(),
                    }
                    break
    
    def coordinate_defense(
        self,
        pattern_id: str,
        affected_nodes: List[str]
    ) -> Dict[str, Any]:
        coordination_id = f"coord_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        with self._lock:
            pattern = self.pattern_library.patterns.get(pattern_id)
            
            if not pattern:
                return {"error": "Pattern not found"}
            
            available_nodes = [
                n for n, info in self.registered_nodes.items()
                if info["active"] and n not in affected_nodes
            ]
            
            defense_plan = {
                "coordination_id": coordination_id,
                "pattern_id": pattern_id,
                "mitigation_steps": pattern.mitigation_steps,
                "affected_nodes": affected_nodes,
                "supporting_nodes": available_nodes[:5],
                "status": "active",
                "created_at": datetime.now().isoformat(),
            }
            
            self.active_defenses[coordination_id] = defense_plan
            self.stats["defenses_coordinated"] += 1
        
        return defense_plan
    
    def report_mitigation_result(
        self,
        coordination_id: str,
        success: bool,
        details: Dict[str, Any] = None
    ):
        with self._lock:
            if coordination_id in self.active_defenses:
                self.active_defenses[coordination_id]["status"] = "completed"
                self.active_defenses[coordination_id]["success"] = success
                self.active_defenses[coordination_id]["details"] = details
                
                if success:
                    self.stats["successful_mitigations"] += 1


class AttackPatternRecognizer:
    """攻击模式识别器主控"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        self.pattern_library = AttackPatternLibrary(
            similarity_threshold=self.config.get("similarity_threshold", 0.8)
        )
        self.novel_handler = NovelAttackHandler(
            self.pattern_library,
            required_samples=self.config.get("required_samples", 10)
        )
        self.coordinator = CollectiveDefenseCoordinator(self.pattern_library)
        
        self.event_buffer: deque = deque(maxlen=10000)
        self.subscribers: List[Callable] = []
        
        self._lock = threading.Lock()
        
        self._running = False
        self._analysis_task = None
        
        self.stats = {
            "total_events": 0,
            "patterns_matched": 0,
            "novel_detections": 0,
            "defenses_triggered": 0,
        }
    
    async def start(self):
        self._running = True
        self._analysis_task = asyncio.create_task(self._periodic_analysis())
    
    def stop(self):
        self._running = False
        if self._analysis_task:
            self._analysis_task.cancel()
    
    def subscribe(self, callback: Callable):
        self.subscribers.append(callback)
    
    async def _periodic_analysis(self):
        while self._running:
            try:
                await self._analyze_buffered_events()
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Analysis error: {e}")
                await asyncio.sleep(10)
    
    async def _analyze_buffered_events(self):
        events = list(self.event_buffer)
        
        for event in events:
            if event.status == AttackStatus.DETECTED:
                await self._process_event(event)
    
    def report_anomaly(
        self,
        source_ip: str,
        source_node: str,
        features: Dict[str, float],
        raw_data: Dict[str, Any] = None
    ) -> AttackEvent:
        self.stats["total_events"] += 1
        
        event_id = f"event_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        feature_vector = self._normalize_features(features)
        
        pattern, similarity, match_type = self.pattern_library.find_matching_pattern(
            feature_vector
        )
        
        severity = self._determine_severity(features, match_type)
        
        event = AttackEvent(
            event_id=event_id,
            timestamp=datetime.now(),
            source_ip=source_ip,
            source_node=source_node,
            attack_type=pattern.attack_type if pattern else "unknown",
            features=features,
            raw_data=raw_data or {},
            severity=severity,
            status=AttackStatus.DETECTED,
            matched_pattern=pattern.pattern_id if pattern else None,
            similarity_score=similarity,
        )
        
        self.event_buffer.append(event)
        
        if match_type == PatternMatchType.NOVEL:
            self.novel_handler.handle_novel_attack(event, similarity)
            self.stats["novel_detections"] += 1
        elif pattern:
            self.pattern_library.update_pattern_stats(
                pattern.pattern_id, False, source_node
            )
            self.stats["patterns_matched"] += 1
        
        return event
    
    def _normalize_features(self, features: Dict[str, float]) -> List[float]:
        max_len = 20
        vector = list(features.values())[:max_len]
        
        while len(vector) < max_len:
            vector.append(0.0)
        
        max_val = max(abs(v) for v in vector) if vector else 1.0
        if max_val > 0:
            vector = [v / max_val for v in vector]
        
        return vector
    
    def _determine_severity(
        self,
        features: Dict[str, float],
        match_type: PatternMatchType
    ) -> AttackSeverity:
        severity_score = 0.0
        
        high_risk_features = [
            "auth_failures", "sql_keywords_count", "script_tags",
            "malware_signatures", "data_exfil_volume"
        ]
        
        for feature, value in features.items():
            if feature in high_risk_features:
                severity_score += value * 0.3
        
        if match_type == PatternMatchType.NOVEL:
            severity_score += 0.2
        
        if severity_score >= 0.8:
            return AttackSeverity.CRITICAL
        elif severity_score >= 0.5:
            return AttackSeverity.HIGH
        elif severity_score >= 0.3:
            return AttackSeverity.MEDIUM
        else:
            return AttackSeverity.LOW
    
    async def _process_event(self, event: AttackEvent):
        event.status = AttackStatus.ANALYZING
        
        if event.matched_pattern:
            pattern = self.pattern_library.patterns.get(event.matched_pattern)
            if pattern:
                self.coordinator.broadcast_threat(
                    pattern, event.source_node, event.severity
                )
                self.stats["defenses_triggered"] += 1
        
        for callback in self.subscribers:
            try:
                await callback(event)
            except Exception as e:
                logger.error(f"Subscriber callback error: {e}")
    
    def get_pattern_library(self) -> List[Dict[str, Any]]:
        return [p.to_dict() for p in self.pattern_library.patterns.values()]
    
    def get_novel_alerts(self, priority: int = None) -> List[Dict[str, Any]]:
        return [a.to_dict() for a in self.novel_handler.get_active_alerts(priority)]
    
    def get_active_defenses(self) -> List[Dict[str, Any]]:
        return list(self.coordinator.active_defenses.values())
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "recognizer": self.stats,
            "pattern_library": self.pattern_library.stats,
            "novel_handler": self.novel_handler.stats,
            "coordinator": self.coordinator.stats,
        }
