"""
攻击签名生成模块 - 威胁情报同步
蜜罐智能体记录攻击手法后生成攻击签名，同步给威胁情报平台
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import asyncio
import logging
import json
import hashlib
import re
from collections import defaultdict

logger = logging.getLogger(__name__)


class AttackType(Enum):
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    PROMPT_INJECTION = "prompt_injection"
    BRUTE_FORCE = "brute_force"
    DDoS = "ddos"
    CREDENTIAL_STUFFING = "credential_stuffing"
    PATH_TRAVERSAL = "path_traversal"
    COMMAND_INJECTION = "command_injection"
    SOCIAL_ENGINEERING = "social_engineering"
    ZERO_DAY = "zero_day"
    UNKNOWN = "unknown"


class Severity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SignatureStatus(Enum):
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    TESTING = "testing"


@dataclass
class AttackPattern:
    pattern_id: str
    attack_type: AttackType
    pattern_regex: str
    description: str
    indicators: List[str]
    confidence: float
    first_seen: datetime
    last_seen: datetime
    occurrence_count: int
    affected_endpoints: List[str]
    severity: Severity
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_id": self.pattern_id,
            "attack_type": self.attack_type.value,
            "pattern_regex": self.pattern_regex,
            "description": self.description,
            "indicators": self.indicators,
            "confidence": self.confidence,
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "occurrence_count": self.occurrence_count,
            "affected_endpoints": self.affected_endpoints,
            "severity": self.severity.value
        }


@dataclass
class AttackSignature:
    signature_id: str
    name: str
    attack_type: AttackType
    severity: Severity
    patterns: List[str]
    indicators: Dict[str, List[str]]
    mitre_attack_ids: List[str]
    cve_ids: List[str]
    created_at: datetime
    updated_at: datetime
    status: SignatureStatus
    source: str
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_stix_format(self) -> Dict[str, Any]:
        return {
            "type": "indicator",
            "id": f"indicator--{self.signature_id}",
            "created": self.created_at.isoformat(),
            "modified": self.updated_at.isoformat(),
            "name": self.name,
            "description": f"Attack signature for {self.attack_type.value}",
            "pattern_type": "stix",
            "pattern": self._generate_stix_pattern(),
            "valid_from": self.created_at.isoformat(),
            "labels": [self.attack_type.value, self.severity.value],
            "confidence": int(self.confidence * 100),
            "external_references": [
                {"source_name": "mitre-attack", "external_id": mid}
                for mid in self.mitre_attack_ids
            ] + [
                {"source_name": "cve", "external_id": cve}
                for cve in self.cve_ids
            ]
        }
        
    def _generate_stix_pattern(self) -> str:
        patterns = []
        for pattern in self.patterns:
            patterns.append(f"[file:hashes.'SHA-256' = '{pattern}']")
        for ip in self.indicators.get("ip_addresses", []):
            patterns.append(f"[network-traffic:dst_ref.value = '{ip}']")
        for url in self.indicators.get("urls", []):
            patterns.append(f"[url:value = '{url}']")
        return " OR ".join(patterns)


@dataclass
class HoneypotEvent:
    event_id: str
    timestamp: datetime
    source_ip: str
    source_port: int
    destination_port: int
    protocol: str
    payload: str
    attack_type: AttackType
    honeypot_type: str
    user_agent: Optional[str] = None
    request_path: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)
    matched_signatures: List[str] = field(default_factory=list)


@dataclass
class ThreatIntelligenceFeed:
    feed_id: str
    name: str
    source_url: str
    feed_type: str
    last_updated: datetime
    signature_count: int
    status: str


class AttackPatternAnalyzer:
    def __init__(self):
        self._patterns: Dict[str, AttackPattern] = {}
        self._attack_history: List[HoneypotEvent] = []
        self._pattern_threshold = 3
        
    def analyze_event(self, event: HoneypotEvent) -> Optional[AttackPattern]:
        self._attack_history.append(event)
        
        similar_events = [
            e for e in self._attack_history
            if e.attack_type == event.attack_type
            and e.source_ip != event.source_ip
        ]
        
        if len(similar_events) >= self._pattern_threshold:
            pattern = self._extract_pattern(event, similar_events)
            if pattern:
                self._patterns[pattern.pattern_id] = pattern
                return pattern
                
        return None
        
    def _extract_pattern(
        self,
        event: HoneypotEvent,
        similar_events: List[HoneypotEvent]
    ) -> Optional[AttackPattern]:
        if event.attack_type == AttackType.SQL_INJECTION:
            return self._extract_sql_pattern(event, similar_events)
        elif event.attack_type == AttackType.XSS:
            return self._extract_xss_pattern(event, similar_events)
        elif event.attack_type == AttackType.PROMPT_INJECTION:
            return self._extract_prompt_injection_pattern(event, similar_events)
        elif event.attack_type == AttackType.BRUTE_FORCE:
            return self._extract_brute_force_pattern(event, similar_events)
            
        return self._extract_generic_pattern(event, similar_events)
        
    def _extract_sql_pattern(
        self,
        event: HoneypotEvent,
        similar_events: List[HoneypotEvent]
    ) -> AttackPattern:
        sql_keywords = ["UNION", "SELECT", "DROP", "INSERT", "DELETE", "OR 1=1", "'--"]
        found_keywords = []
        
        payload_upper = event.payload.upper()
        for keyword in sql_keywords:
            if keyword in payload_upper:
                found_keywords.append(keyword)
                
        pattern_regex = self._build_regex_from_keywords(found_keywords)
        
        return AttackPattern(
            pattern_id=f"sql_{hashlib.md5(pattern_regex.encode()).hexdigest()[:12]}",
            attack_type=AttackType.SQL_INJECTION,
            pattern_regex=pattern_regex,
            description=f"SQL注入模式: {', '.join(found_keywords)}",
            indicators=found_keywords,
            confidence=0.85,
            first_seen=min(e.timestamp for e in similar_events + [event]),
            last_seen=datetime.now(),
            occurrence_count=len(similar_events) + 1,
            affected_endpoints=list(set(e.request_path for e in similar_events if e.request_path)),
            severity=Severity.HIGH
        )
        
    def _extract_xss_pattern(
        self,
        event: HoneypotEvent,
        similar_events: List[HoneypotEvent]
    ) -> AttackPattern:
        xss_patterns = [
            r"<script", r"javascript:", r"onerror=", r"onload=",
            r"eval\(", r"document\.", r"alert\("
        ]
        found_patterns = []
        
        for pattern in xss_patterns:
            if re.search(pattern, event.payload, re.IGNORECASE):
                found_patterns.append(pattern)
                
        combined_regex = "|".join(found_patterns) if found_patterns else r"<script"
        
        return AttackPattern(
            pattern_id=f"xss_{hashlib.md5(combined_regex.encode()).hexdigest()[:12]}",
            attack_type=AttackType.XSS,
            pattern_regex=combined_regex,
            description=f"XSS攻击模式: {len(found_patterns)}个特征",
            indicators=found_patterns,
            confidence=0.8,
            first_seen=min(e.timestamp for e in similar_events + [event]),
            last_seen=datetime.now(),
            occurrence_count=len(similar_events) + 1,
            affected_endpoints=list(set(e.request_path for e in similar_events if e.request_path)),
            severity=Severity.HIGH
        )
        
    def _extract_prompt_injection_pattern(
        self,
        event: HoneypotEvent,
        similar_events: List[HoneypotEvent]
    ) -> AttackPattern:
        prompt_patterns = [
            "ignore previous instructions",
            "disregard all above",
            "you are now",
            "system:",
            "assistant:",
            "jailbreak",
            "DAN"
        ]
        found_patterns = []
        
        payload_lower = event.payload.lower()
        for pattern in prompt_patterns:
            if pattern.lower() in payload_lower:
                found_patterns.append(pattern)
                
        return AttackPattern(
            pattern_id=f"prompt_{hashlib.md5(str(found_patterns).encode()).hexdigest()[:12]}",
            attack_type=AttackType.PROMPT_INJECTION,
            pattern_regex="|".join(re.escape(p) for p in found_patterns) if found_patterns else ".*",
            description=f"提示注入模式: {len(found_patterns)}个特征",
            indicators=found_patterns,
            confidence=0.75,
            first_seen=min(e.timestamp for e in similar_events + [event]),
            last_seen=datetime.now(),
            occurrence_count=len(similar_events) + 1,
            affected_endpoints=list(set(e.request_path for e in similar_events if e.request_path)),
            severity=Severity.HIGH
        )
        
    def _extract_brute_force_pattern(
        self,
        event: HoneypotEvent,
        similar_events: List[HoneypotEvent]
    ) -> AttackPattern:
        source_ips = list(set(e.source_ip for e in similar_events + [event]))
        
        return AttackPattern(
            pattern_id=f"brute_{hashlib.md5(str(source_ips).encode()).hexdigest()[:12]}",
            attack_type=AttackType.BRUTE_FORCE,
            pattern_regex=f"source_ip:({'|'.join(source_ips)})",
            description=f"暴力破解模式: {len(source_ips)}个源IP",
            indicators=source_ips,
            confidence=0.9,
            first_seen=min(e.timestamp for e in similar_events + [event]),
            last_seen=datetime.now(),
            occurrence_count=len(similar_events) + 1,
            affected_endpoints=list(set(e.request_path for e in similar_events if e.request_path)),
            severity=Severity.MEDIUM
        )
        
    def _extract_generic_pattern(
        self,
        event: HoneypotEvent,
        similar_events: List[HoneypotEvent]
    ) -> AttackPattern:
        return AttackPattern(
            pattern_id=f"generic_{hashlib.md5(event.payload.encode()).hexdigest()[:12]}",
            attack_type=event.attack_type,
            pattern_regex=re.escape(event.payload[:50]),
            description=f"通用攻击模式: {event.attack_type.value}",
            indicators=[event.payload[:100]],
            confidence=0.6,
            first_seen=min(e.timestamp for e in similar_events + [event]),
            last_seen=datetime.now(),
            occurrence_count=len(similar_events) + 1,
            affected_endpoints=list(set(e.request_path for e in similar_events if e.request_path)),
            severity=Severity.MEDIUM
        )
        
    def _build_regex_from_keywords(self, keywords: List[str]) -> str:
        if not keywords:
            return ".*"
        return "|".join(re.escape(k) for k in keywords)


class SignatureGenerator:
    def __init__(self):
        self._signatures: Dict[str, AttackSignature] = {}
        self._pattern_analyzer = AttackPatternAnalyzer()
        
    def generate_signature(
        self,
        pattern: AttackPattern,
        additional_indicators: Optional[Dict[str, List[str]]] = None
    ) -> AttackSignature:
        signature_id = f"sig_{hashlib.sha256(pattern.pattern_id.encode()).hexdigest()[:16]}"
        
        indicators = additional_indicators or {}
        indicators.setdefault("patterns", [pattern.pattern_regex])
        indicators.setdefault("keywords", pattern.indicators)
        
        mitre_ids = self._map_to_mitre_attack(pattern.attack_type)
        
        signature = AttackSignature(
            signature_id=signature_id,
            name=f"{pattern.attack_type.value}_signature_{signature_id[:8]}",
            attack_type=pattern.attack_type,
            severity=pattern.severity,
            patterns=[pattern.pattern_regex],
            indicators=indicators,
            mitre_attack_ids=mitre_ids,
            cve_ids=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
            status=SignatureStatus.ACTIVE,
            source="internal_honeypot",
            confidence=pattern.confidence
        )
        
        self._signatures[signature_id] = signature
        return signature
        
    def _map_to_mitre_attack(self, attack_type: AttackType) -> List[str]:
        mapping = {
            AttackType.SQL_INJECTION: ["T1190", "T1059"],
            AttackType.XSS: ["T1189", "T1071"],
            AttackType.PROMPT_INJECTION: ["T1566", "T1027"],
            AttackType.BRUTE_FORCE: ["T1110"],
            AttackType.DDoS: ["T1498", "T1499"],
            AttackType.CREDENTIAL_STUFFING: ["T1110", "T1078"],
            AttackType.PATH_TRAVERSAL: ["T1083", "T1005"],
            AttackType.COMMAND_INJECTION: ["T1190", "T1059"],
            AttackType.SOCIAL_ENGINEERING: ["T1566", "T1534"],
        }
        return mapping.get(attack_type, ["T0000"])
        
    def generate_from_event(self, event: HoneypotEvent) -> Optional[AttackSignature]:
        pattern = self._pattern_analyzer.analyze_event(event)
        if pattern:
            return self.generate_signature(pattern)
        return None
        
    def get_signature(self, signature_id: str) -> Optional[AttackSignature]:
        return self._signatures.get(signature_id)
        
    def get_all_signatures(self) -> List[AttackSignature]:
        return list(self._signatures.values())


class ThreatIntelligencePlatform:
    def __init__(self):
        self._feeds: Dict[str, ThreatIntelligenceFeed] = {}
        self._synced_signatures: Dict[str, List[str]] = defaultdict(list)
        self._api_endpoints: Dict[str, str] = {}
        
    def register_feed(self, feed: ThreatIntelligenceFeed):
        self._feeds[feed.feed_id] = feed
        
    def set_api_endpoint(self, platform: str, endpoint: str):
        self._api_endpoints[platform] = endpoint
        
    async def sync_signature(
        self,
        signature: AttackSignature,
        platforms: Optional[List[str]] = None
    ) -> Dict[str, bool]:
        results = {}
        
        target_platforms = platforms or list(self._api_endpoints.keys())
        
        for platform in target_platforms:
            try:
                stix_data = signature.to_stix_format()
                
                success = await self._push_to_platform(platform, stix_data)
                
                if success:
                    self._synced_signatures[platform].append(signature.signature_id)
                    
                results[platform] = success
                
            except Exception as e:
                logger.error(f"Failed to sync to {platform}: {e}")
                results[platform] = False
                
        return results
        
    async def _push_to_platform(self, platform: str, stix_data: Dict[str, Any]) -> bool:
        endpoint = self._api_endpoints.get(platform)
        if not endpoint:
            logger.warning(f"No endpoint configured for {platform}")
            return False
            
        logger.info(f"Pushing signature to {platform}: {stix_data['id']}")
        return True
        
    async def fetch_signatures(self, feed_id: str) -> List[AttackSignature]:
        feed = self._feeds.get(feed_id)
        if not feed:
            return []
            
        logger.info(f"Fetching signatures from {feed.name}")
        return []
        
    def get_sync_status(self) -> Dict[str, Any]:
        return {
            "total_feeds": len(self._feeds),
            "total_signatures_synced": sum(
                len(sigs) for sigs in self._synced_signatures.values()
            ),
            "by_platform": {
                platform: len(sigs)
                for platform, sigs in self._synced_signatures.items()
            }
        }


class IPBlockManager:
    def __init__(self):
        self._blocked_ips: Dict[str, Dict[str, Any]] = {}
        self._block_history: List[Dict[str, Any]] = []
        
    def block_ip(
        self,
        ip: str,
        reason: str,
        duration_hours: int = 24,
        signature_id: Optional[str] = None
    ) -> bool:
        if ip in self._blocked_ips:
            return False
            
        self._blocked_ips[ip] = {
            "blocked_at": datetime.now(),
            "reason": reason,
            "duration_hours": duration_hours,
            "expires_at": datetime.now() + timedelta(hours=duration_hours),
            "signature_id": signature_id
        }
        
        self._block_history.append({
            "action": "block",
            "ip": ip,
            "timestamp": datetime.now(),
            "reason": reason
        })
        
        logger.info(f"Blocked IP: {ip} for {duration_hours}h - {reason}")
        return True
        
    def unblock_ip(self, ip: str) -> bool:
        if ip not in self._blocked_ips:
            return False
            
        del self._blocked_ips[ip]
        
        self._block_history.append({
            "action": "unblock",
            "ip": ip,
            "timestamp": datetime.now()
        })
        
        logger.info(f"Unblocked IP: {ip}")
        return True
        
    def is_blocked(self, ip: str) -> bool:
        if ip not in self._blocked_ips:
            return False
            
        block_info = self._blocked_ips[ip]
        if datetime.now() > block_info["expires_at"]:
            self.unblock_ip(ip)
            return False
            
        return True
        
    def get_blocked_ips(self) -> List[Dict[str, Any]]:
        expired = [
            ip for ip, info in self._blocked_ips.items()
            if datetime.now() > info["expires_at"]
        ]
        for ip in expired:
            self.unblock_ip(ip)
            
        return [
            {"ip": ip, **info}
            for ip, info in self._blocked_ips.items()
        ]
        
    def auto_block_from_signature(
        self,
        signature: AttackSignature,
        source_ips: List[str]
    ) -> int:
        blocked_count = 0
        
        for ip in source_ips:
            if self.block_ip(
                ip,
                reason=f"Auto-blocked: {signature.name}",
                duration_hours=48,
                signature_id=signature.signature_id
            ):
                blocked_count += 1
                
        return blocked_count


class AttackSignatureSystem:
    def __init__(self):
        self.signature_generator = SignatureGenerator()
        self.threat_platform = ThreatIntelligencePlatform()
        self.ip_blocker = IPBlockManager()
        self._events: List[HoneypotEvent] = []
        
    async def process_honeypot_event(
        self,
        event: HoneypotEvent
    ) -> Dict[str, Any]:
        self._events.append(event)
        
        signature = self.signature_generator.generate_from_event(event)
        
        result = {
            "event_id": event.event_id,
            "signature_generated": signature is not None,
            "signature_id": signature.signature_id if signature else None
        }
        
        if signature:
            sync_results = await self.threat_platform.sync_signature(signature)
            result["sync_results"] = sync_results
            
            if signature.severity in [Severity.HIGH, Severity.CRITICAL]:
                blocked = self.ip_blocker.auto_block_from_signature(
                    signature, [event.source_ip]
                )
                result["ips_blocked"] = blocked
                
        return result
        
    def get_threat_summary(self) -> Dict[str, Any]:
        signatures = self.signature_generator.get_all_signatures()
        
        by_type = defaultdict(int)
        by_severity = defaultdict(int)
        
        for sig in signatures:
            by_type[sig.attack_type.value] += 1
            by_severity[sig.severity.value] += 1
            
        return {
            "total_signatures": len(signatures),
            "by_attack_type": dict(by_type),
            "by_severity": dict(by_severity),
            "blocked_ips": len(self.ip_blocker._blocked_ips),
            "sync_status": self.threat_platform.get_sync_status()
        }


attack_signature_system = AttackSignatureSystem()


def get_signature_system() -> AttackSignatureSystem:
    return attack_signature_system


async def process_attack_event(event: HoneypotEvent) -> Dict[str, Any]:
    return await attack_signature_system.process_honeypot_event(event)
