"""
记忆防污染系统
Memory Pollution Prevention System

实现写入前验证、事实核查智能体、记忆版本控制
"""

import asyncio
import json
import uuid
import time
import hashlib
import re
from enum import Enum
from typing import Dict, List, Optional, Any, Set, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class MemoryType(Enum):
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"
    EMOTIONAL = "emotional"
    SPATIAL = "spatial"
    TEMPORAL = "temporal"


class VerificationStatus(Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    QUARANTINED = "quarantined"
    NEEDS_REVIEW = "needs_review"


class PollutionType(Enum):
    FALSE_INFORMATION = "false_information"
    INJECTED_CONTENT = "injected_content"
    MANIPULATED_DATA = "manipulated_data"
    POISONED_SAMPLE = "poisoned_sample"
    ADVERSARIAL_INPUT = "adversarial_input"
    PRIVACY_LEAK = "privacy_leak"
    INCONSISTENT_DATA = "inconsistent_data"


class TrustLevel(Enum):
    HIGH = 0.9
    MEDIUM = 0.7
    LOW = 0.5
    UNTRUSTED = 0.3
    QUARANTINED = 0.1


SOURCE_TRUST_LEVELS = {
    "gov": TrustLevel.HIGH,
    "enterprise": TrustLevel.MEDIUM,
    "edu": TrustLevel.MEDIUM,
    "std": TrustLevel.HIGH,
    "public": TrustLevel.LOW,
    "external": TrustLevel.LOW,
    "unknown": TrustLevel.UNTRUSTED,
}


@dataclass
class MemorySnapshot:
    snapshot_id: str
    memory_id: str
    content: str
    content_hash: str
    memory_type: MemoryType
    source_end: str
    source_agent: str
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "memory_id": self.memory_id,
            "content": self.content,
            "content_hash": self.content_hash,
            "memory_type": self.memory_type.value,
            "source_end": self.source_end,
            "source_agent": self.source_agent,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }
    
    @classmethod
    def create(cls, memory_id: str, content: str, 
               memory_type: MemoryType, source_end: str, source_agent: str,
               metadata: Dict[str, Any] = None) -> "MemorySnapshot":
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        return cls(
            snapshot_id=str(uuid.uuid4()),
            memory_id=memory_id,
            content=content,
            content_hash=content_hash,
            memory_type=memory_type,
            source_end=source_end,
            source_agent=source_agent,
            metadata=metadata or {},
        )


@dataclass
class VerificationRecord:
    verification_id: str
    memory_id: str
    status: VerificationStatus
    pollution_types: List[PollutionType] = field(default_factory=list)
    confidence: float = 0.0
    verifier: str = ""
    verification_time: float = field(default_factory=time.time)
    details: Dict[str, Any] = field(default_factory=dict)
    human_review_required: bool = False
    reviewer_id: Optional[str] = None
    review_result: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "verification_id": self.verification_id,
            "memory_id": self.memory_id,
            "status": self.status.value,
            "pollution_types": [p.value for p in self.pollution_types],
            "confidence": self.confidence,
            "verifier": self.verifier,
            "verification_time": self.verification_time,
            "details": self.details,
            "human_review_required": self.human_review_required,
            "reviewer_id": self.reviewer_id,
            "review_result": self.review_result,
        }


@dataclass
class FactCheckResult:
    claim: str
    is_verified: bool
    confidence: float
    sources: List[str]
    contradictions: List[str]
    supporting_evidence: List[str]
    check_time: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim": self.claim,
            "is_verified": self.is_verified,
            "confidence": self.confidence,
            "sources": self.sources,
            "contradictions": self.contradictions,
            "supporting_evidence": self.supporting_evidence,
            "check_time": self.check_time,
        }


class InjectionPatternDetector:
    PATTERNS = [
        (r"ignore\s+(previous|all|above)\s+(instructions?|rules?)", "instruction_injection"),
        (r"forget\s+(everything|all|previous)", "memory_wipe"),
        (r"you\s+are\s+now\s+", "role_injection"),
        (r"simulate\s+(being|that you are)", "simulation_injection"),
        (r"\[.*?\].*?\[.*?\]", "bracket_injection"),
        (r"<.*?>.*?<.*?>", "tag_injection"),
        (r"system\s*:\s*override", "system_override"),
        (r"developer\s*mode", "dev_mode"),
        (r"debug\s*mode", "debug_mode"),
        (r"jailbreak", "jailbreak"),
        (r"DAN\s*:", "dan_injection"),
        (r"act\s+as\s+(if|though)", "acting_injection"),
        (r"pretend\s+(to be|that)", "pretend_injection"),
        (r"disregard\s+(safety|filter|rules)", "safety_bypass"),
    ]
    
    def __init__(self):
        self._compiled_patterns = [
            (re.compile(pattern, re.IGNORECASE), ptype)
            for pattern, ptype in self.PATTERNS
        ]
    
    def detect(self, content: str) -> List[Tuple[str, str]]:
        detected = []
        for compiled, ptype in self._compiled_patterns:
            matches = compiled.findall(content)
            if matches:
                detected.append((ptype, str(matches[0])))
        return detected
    
    def get_risk_score(self, content: str) -> float:
        detected = self.detect(content)
        if not detected:
            return 0.0
        
        severity_weights = {
            "instruction_injection": 0.8,
            "memory_wipe": 0.9,
            "role_injection": 0.7,
            "simulation_injection": 0.6,
            "bracket_injection": 0.5,
            "tag_injection": 0.5,
            "system_override": 0.95,
            "dev_mode": 0.8,
            "debug_mode": 0.7,
            "jailbreak": 0.95,
            "dan_injection": 0.9,
            "acting_injection": 0.6,
            "pretend_injection": 0.6,
            "safety_bypass": 0.9,
        }
        
        max_severity = max(
            severity_weights.get(ptype, 0.5) 
            for ptype, _ in detected
        )
        
        return min(1.0, max_severity + len(detected) * 0.05)


class PrivacyLeakDetector:
    SENSITIVE_PATTERNS = [
        (r"\b\d{17,18}[xX]?\b", "id_card"),
        (r"\b\d{6,8}\d{4}\d{2}\d{2}\d{2}\d{3}[\dXx]\b", "id_card_full"),
        (r"\b1[3-9]\d{9}\b", "phone_number"),
        (r"\b[\w\.-]+@[\w\.-]+\.\w+\b", "email"),
        (r"\b\d{16,19}\b", "bank_card"),
        (r"\b[\u4e00-\u9fa5]{2,4}[\u4e00-\u9fa5]*\b", "chinese_name"),
        (r"\b\d{4}[-\s]?\d{1,2}[-\s]?\d{1,2}\b", "date"),
        (r"\b(?:省|市|区|县|街道|路|号|栋|单元|室).{2,20}\b", "address"),
    ]
    
    def __init__(self):
        self._compiled_patterns = [
            (re.compile(pattern), ptype)
            for pattern, ptype in self.SENSITIVE_PATTERNS
        ]
    
    def detect(self, content: str) -> List[Tuple[str, str, str]]:
        detected = []
        for compiled, ptype in self._compiled_patterns:
            matches = compiled.findall(content)
            for match in matches:
                detected.append((ptype, match, self._mask_sensitive(match, ptype)))
        return detected
    
    def _mask_sensitive(self, value: str, ptype: str) -> str:
        if len(value) <= 4:
            return "*" * len(value)
        return value[:2] + "*" * (len(value) - 4) + value[-2:]
    
    def has_sensitive_data(self, content: str) -> bool:
        return len(self.detect(content)) > 0


class FactCheckingAgent:
    def __init__(self, knowledge_base: Optional[Any] = None,
                 external_fact_checker: Optional[Callable] = None):
        self.knowledge_base = knowledge_base
        self.external_fact_checker = external_fact_checker
        self._fact_cache: Dict[str, FactCheckResult] = {}
        self._agent_id = f"fact_checker_{str(uuid.uuid4())[:8]}"
    
    async def verify_claim(self, claim: str, context: Dict[str, Any] = None) -> FactCheckResult:
        cache_key = hashlib.md5(claim.encode()).hexdigest()
        if cache_key in self._fact_cache:
            return self._fact_cache[cache_key]
        
        result = await self._perform_verification(claim, context or {})
        self._fact_cache[cache_key] = result
        return result
    
    async def _perform_verification(self, claim: str, context: Dict[str, Any]) -> FactCheckResult:
        sources = []
        contradictions = []
        supporting_evidence = []
        confidence = 0.5
        
        if self.knowledge_base:
            kb_result = await self._check_knowledge_base(claim)
            if kb_result:
                sources.extend(kb_result.get("sources", []))
                contradictions.extend(kb_result.get("contradictions", []))
                supporting_evidence.extend(kb_result.get("supporting", []))
                confidence = max(confidence, kb_result.get("confidence", 0.5))
        
        if self.external_fact_checker:
            ext_result = await self.external_fact_checker(claim, context)
            if ext_result:
                sources.extend(ext_result.get("sources", []))
                contradictions.extend(ext_result.get("contradictions", []))
                supporting_evidence.extend(ext_result.get("supporting", []))
                confidence = (confidence + ext_result.get("confidence", 0.5)) / 2
        
        is_verified = confidence >= 0.7 and len(contradictions) == 0
        
        return FactCheckResult(
            claim=claim,
            is_verified=is_verified,
            confidence=confidence,
            sources=sources,
            contradictions=contradictions,
            supporting_evidence=supporting_evidence,
        )
    
    async def _check_knowledge_base(self, claim: str) -> Optional[Dict[str, Any]]:
        return {
            "sources": ["internal_kb"],
            "contradictions": [],
            "supporting": [],
            "confidence": 0.6,
        }
    
    async def verify_memory_content(self, content: str, 
                                      memory_type: MemoryType) -> List[FactCheckResult]:
        results = []
        
        claims = self._extract_claims(content, memory_type)
        
        for claim in claims:
            result = await self.verify_claim(claim)
            results.append(result)
        
        return results
    
    def _extract_claims(self, content: str, memory_type: MemoryType) -> List[str]:
        sentences = re.split(r'[。！？.!?]', content)
        claims = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            if self._is_factual_claim(sentence):
                claims.append(sentence)
        
        return claims
    
    def _is_factual_claim(self, sentence: str) -> bool:
        factual_patterns = [
            r"是", r"有", r"为", r"等于", r"包含",
            r"is", r"are", r"was", r"were", r"has", r"have",
            r"\d+", r"百分之", r"%",
        ]
        
        for pattern in factual_patterns:
            if re.search(pattern, sentence):
                return True
        return False


class MemoryPollutionPrevention:
    def __init__(self, knowledge_base: Optional[Any] = None,
                 hippocampus: Optional[Any] = None):
        self.knowledge_base = knowledge_base
        self.hippocampus = hippocampus
        
        self.injection_detector = InjectionPatternDetector()
        self.privacy_detector = PrivacyLeakDetector()
        self.fact_checker = FactCheckingAgent(knowledge_base)
        
        self._verifications: Dict[str, VerificationRecord] = {}
        self._snapshots: Dict[str, List[MemorySnapshot]] = defaultdict(list)
        self._quarantine: Dict[str, Dict[str, Any]] = {}
        
        self._lock = asyncio.Lock()
        self._verification_threshold = 0.7
        self._quarantine_threshold = 0.3
    
    async def verify_before_write(self, content: str, memory_type: MemoryType,
                                   source_end: str, source_agent: str,
                                   metadata: Dict[str, Any] = None) -> Tuple[bool, VerificationRecord]:
        verification_id = str(uuid.uuid4())
        memory_id = str(uuid.uuid4())
        
        pollution_types = []
        details = {}
        confidence = 1.0
        
        injection_risk = self.injection_detector.get_risk_score(content)
        if injection_risk > 0.3:
            pollution_types.append(PollutionType.INJECTED_CONTENT)
            details["injection_risk"] = injection_risk
            confidence -= injection_risk * 0.5
        
        privacy_detected = self.privacy_detector.detect(content)
        if privacy_detected:
            pollution_types.append(PollutionType.PRIVACY_LEAK)
            details["privacy_detected"] = [
                {"type": ptype, "value": masked}
                for ptype, _, masked in privacy_detected
            ]
            confidence -= 0.3
        
        source_trust = SOURCE_TRUST_LEVELS.get(source_end, TrustLevel.UNTRUSTED)
        confidence *= source_trust.value
        
        fact_results = await self.fact_checker.verify_memory_content(content, memory_type)
        if fact_results:
            avg_confidence = sum(r.confidence for r in fact_results) / len(fact_results)
            contradictions = [r for r in fact_results if not r.is_verified]
            
            if contradictions:
                pollution_types.append(PollutionType.FALSE_INFORMATION)
                details["contradictions"] = [r.to_dict() for r in contradictions]
                confidence *= 0.7
            
            details["fact_check_results"] = [r.to_dict() for r in fact_results]
        
        if confidence >= self._verification_threshold:
            status = VerificationStatus.VERIFIED
        elif confidence >= self._quarantine_threshold:
            status = VerificationStatus.NEEDS_REVIEW
        else:
            status = VerificationStatus.QUARANTINED
        
        human_review_required = (
            status == VerificationStatus.NEEDS_REVIEW or
            PollutionType.FALSE_INFORMATION in pollution_types or
            injection_risk > 0.5
        )
        
        record = VerificationRecord(
            verification_id=verification_id,
            memory_id=memory_id,
            status=status,
            pollution_types=pollution_types,
            confidence=confidence,
            verifier=self.fact_checker._agent_id,
            details=details,
            human_review_required=human_review_required,
        )
        
        self._verifications[verification_id] = record
        
        if status == VerificationStatus.QUARANTINED:
            self._quarantine[memory_id] = {
                "content": content,
                "memory_type": memory_type.value,
                "source_end": source_end,
                "source_agent": source_agent,
                "verification": record.to_dict(),
                "quarantined_at": time.time(),
            }
        
        is_allowed = status in [VerificationStatus.VERIFIED, VerificationStatus.NEEDS_REVIEW]
        
        logger.info(f"Memory verification: {status.value}, confidence={confidence:.2f}, "
                   f"pollution_types={[p.value for p in pollution_types]}")
        
        return is_allowed, record
    
    async def create_snapshot(self, memory_id: str, content: str,
                               memory_type: MemoryType, source_end: str, source_agent: str,
                               metadata: Dict[str, Any] = None) -> MemorySnapshot:
        async with self._lock:
            snapshot = MemorySnapshot.create(
                memory_id=memory_id,
                content=content,
                memory_type=memory_type,
                source_end=source_end,
                source_agent=source_agent,
                metadata=metadata,
            )
            
            self._snapshots[memory_id].append(snapshot)
            
            logger.info(f"Snapshot created for memory {memory_id}: {snapshot.snapshot_id}")
            return snapshot
    
    async def rollback_memory(self, memory_id: str, snapshot_id: str = None) -> Optional[MemorySnapshot]:
        async with self._lock:
            snapshots = self._snapshots.get(memory_id, [])
            
            if not snapshots:
                return None
            
            if snapshot_id:
                for snapshot in snapshots:
                    if snapshot.snapshot_id == snapshot_id:
                        return snapshot
                return None
            
            return snapshots[-1]
    
    async def get_memory_history(self, memory_id: str) -> List[MemorySnapshot]:
        return self._snapshots.get(memory_id, [])
    
    async def review_quarantined(self, memory_id: str, reviewer_id: str,
                                   action: str, notes: str = "") -> bool:
        async with self._lock:
            if memory_id not in self._quarantine:
                return False
            
            quarantined = self._quarantine[memory_id]
            verification_id = quarantined["verification"]["verification_id"]
            
            record = self._verifications.get(verification_id)
            if not record:
                return False
            
            record.reviewer_id = reviewer_id
            record.review_result = action
            
            if action == "approve":
                record.status = VerificationStatus.VERIFIED
                del self._quarantine[memory_id]
            elif action == "reject":
                record.status = VerificationStatus.REJECTED
                del self._quarantine[memory_id]
            
            logger.info(f"Quarantined memory {memory_id} reviewed: {action}")
            return True
    
    async def get_quarantine_list(self) -> List[Dict[str, Any]]:
        return [
            {"memory_id": mid, **data}
            for mid, data in self._quarantine.items()
        ]
    
    async def get_verification_stats(self) -> Dict[str, Any]:
        by_status = defaultdict(int)
        by_pollution = defaultdict(int)
        
        for record in self._verifications.values():
            by_status[record.status.value] += 1
            for ptype in record.pollution_types:
                by_pollution[ptype.value] += 1
        
        return {
            "total_verifications": len(self._verifications),
            "by_status": dict(by_status),
            "by_pollution_type": dict(by_pollution),
            "quarantine_count": len(self._quarantine),
            "total_snapshots": sum(len(s) for s in self._snapshots.values()),
        }
    
    def sanitize_content(self, content: str) -> str:
        sanitized = content
        
        privacy_detected = self.privacy_detector.detect(content)
        for ptype, value, masked in privacy_detected:
            sanitized = sanitized.replace(value, masked)
        
        return sanitized
    
    async def batch_verify(self, contents: List[Tuple[str, MemoryType, str, str]],
                           batch_size: int = 10) -> List[Tuple[bool, VerificationRecord]]:
        results = []
        
        for i in range(0, len(contents), batch_size):
            batch = contents[i:i + batch_size]
            batch_results = await asyncio.gather(*[
                self.verify_before_write(content, mtype, source, agent)
                for content, mtype, source, agent in batch
            ])
            results.extend(batch_results)
        
        return results


class MemoryPollutionMonitor:
    def __init__(self, prevention_system: MemoryPollutionPrevention):
        self.prevention = prevention_system
        self._metrics_history: List[Dict[str, Any]] = []
    
    async def collect_metrics(self) -> Dict[str, Any]:
        stats = await self.prevention.get_verification_stats()
        
        metrics = {
            "timestamp": time.time(),
            **stats,
        }
        
        self._metrics_history.append(metrics)
        return metrics
    
    async def get_pollution_trends(self, days: int = 7) -> Dict[str, Any]:
        return {
            "period_days": days,
            "trend": "stable",
            "top_pollution_types": [],
        }
    
    async def get_verification_rate(self) -> float:
        stats = await self.prevention.get_verification_stats()
        total = stats["total_verifications"]
        if total == 0:
            return 0.0
        
        verified = stats["by_status"].get("verified", 0)
        return verified / total
