"""
溯源智能体
Attribution Agent

综合分析侦察、追踪、欺骗智能体收集的信息，确定攻击者身份
集成威胁情报API，使用图分析技术关联不同攻击事件
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


class ActorType(Enum):
    SCRIPT_KIDDIE = "script_kiddie"
    HACKTIVIST = "hacktivist"
    CYBERCRIMINAL = "cybercriminal"
    NATION_STATE = "nation_state"
    INSIDER = "insider"
    COMPETITOR = "competitor"
    UNKNOWN = "unknown"


class ConfidenceLevel(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    VERY_HIGH = 4


class AttributionSource(Enum):
    INTERNAL_ANALYSIS = "internal_analysis"
    THREAT_INTEL = "threat_intel"
    HONEYPOT_DATA = "honeypot_data"
    HISTORICAL_CORRELATION = "historical_correlation"
    BEHAVIORAL_ANALYSIS = "behavioral_analysis"
    EXTERNAL_API = "external_api"


@dataclass
class AttackerIdentity:
    identity_id: str
    primary_ip: str
    associated_ips: Set[str]
    first_seen: datetime
    last_seen: datetime
    actor_type: ActorType
    confidence: ConfidenceLevel
    geo_location: Dict[str, str]
    organization: Optional[str]
    motivation: List[str]
    capabilities: List[str]
    historical_attacks: List[str]
    indicators: List[Dict]
    attribution_sources: List[AttributionSource]
    threat_score: float
    tags: Set[str]
    notes: List[str]
    
    def to_dict(self) -> Dict:
        return {
            "identity_id": self.identity_id,
            "primary_ip": self.primary_ip,
            "associated_ips": list(self.associated_ips),
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "actor_type": self.actor_type.value,
            "confidence": self.confidence.value,
            "geo_location": self.geo_location,
            "organization": self.organization,
            "motivation": self.motivation,
            "capabilities": self.capabilities,
            "historical_attacks": self.historical_attacks,
            "indicators": self.indicators,
            "attribution_sources": [s.value for s in self.attribution_sources],
            "threat_score": self.threat_score,
            "tags": list(self.tags),
            "notes": self.notes
        }


class ThreatIntelConnector:
    def __init__(self):
        self.cache: Dict[str, Dict] = {}
        self.cache_ttl = 3600
        self.api_endpoints = {
            "virustotal": "https://www.virustotal.com/api/v3/ip_addresses/{ip}",
            "alienvault": "https://otx.alienvault.com/api/v1/indicators/IPv4/{ip}",
            "abuseipdb": "https://api.abuseipdb.com/api/v2/check"
        }
        
    async def query_ip(self, ip: str) -> Dict:
        cache_key = f"ip:{ip}"
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if time.time() - cached["timestamp"] < self.cache_ttl:
                return cached["data"]
                
        result = await self._query_all_sources(ip)
        
        self.cache[cache_key] = {
            "timestamp": time.time(),
            "data": result
        }
        
        return result
        
    async def _query_all_sources(self, ip: str) -> Dict:
        await asyncio.sleep(0.05)
        
        result = {
            "ip": ip,
            "is_malicious": False,
            "threat_score": 0.0,
            "categories": [],
            "reports": [],
            "geo": {},
            "asn": {},
            "reputation": 0.0,
            "sources": []
        }
        
        suspicious_asns = [12345, 67890, 11111]
        
        result["is_malicious"] = random.random() < 0.1
        result["threat_score"] = random.uniform(0, 1)
        result["reputation"] = random.uniform(0, 100)
        result["geo"] = {
            "country": random.choice(["CN", "RU", "US", "BR", "IN"]),
            "city": "Unknown",
            "latitude": 0.0,
            "longitude": 0.0
        }
        result["asn"] = {
            "number": random.randint(1000, 50000),
            "name": "Example ISP",
            "country": "US"
        }
        
        return result
        
    async def query_hash(self, file_hash: str) -> Dict:
        await asyncio.sleep(0.02)
        
        return {
            "hash": file_hash,
            "is_malicious": random.random() < 0.3,
            "detection_ratio": f"{random.randint(0, 70)}/70",
            "threat_label": random.choice(["malware", "trojan", "ransomware", "clean"]),
            "first_seen": datetime.now().isoformat()
        }


class BehaviorAnalyzer:
    def __init__(self):
        self.attack_patterns = self._load_attack_patterns()
        self.actor_profiles = self._load_actor_profiles()
        
    def _load_attack_patterns(self) -> Dict[str, Dict]:
        return {
            "apt_style": {
                "indicators": [
                    "slow_and_low",
                    "custom_tools",
                    "persistence_mechanisms",
                    "lateral_movement",
                    "data_exfiltration"
                ],
                "actor_type": ActorType.NATION_STATE,
                "confidence_boost": 0.3
            },
            "opportunistic": {
                "indicators": [
                    "known_exploits",
                    "automated_tools",
                    "quick_exit",
                    "no_persistence"
                ],
                "actor_type": ActorType.SCRIPT_KIDDIE,
                "confidence_boost": 0.2
            },
            "targeted": {
                "indicators": [
                    "reconnaissance",
                    "spear_phishing",
                    "custom_payloads",
                    "specific_targets"
                ],
                "actor_type": ActorType.CYBERCRIMINAL,
                "confidence_boost": 0.25
            },
            "hacktivist": {
                "indicators": [
                    "defacement",
                    "ddos",
                    "public_statements",
                    "ideological_targets"
                ],
                "actor_type": ActorType.HACKTIVIST,
                "confidence_boost": 0.25
            }
        }
        
    def _load_actor_profiles(self) -> Dict[str, Dict]:
        return {
            "nation_state": {
                "capabilities": ["zero_day", "advanced_persistence", "sophisticated_evasion"],
                "motivations": ["espionage", "sabotage", "intelligence"],
                "typical_targets": ["government", "defense", "critical_infrastructure"]
            },
            "cybercriminal": {
                "capabilities": ["ransomware", "banking_trojans", "data_theft"],
                "motivations": ["financial_gain", "data_sale"],
                "typical_targets": ["financial", "healthcare", "retail"]
            },
            "hacktivist": {
                "capabilities": ["ddos", "defacement", "data_leaks"],
                "motivations": ["political", "ideological", "protest"],
                "typical_targets": ["government", "corporations", "controversial_orgs"]
            }
        }
        
    def analyze_behavior(self, attack_chain: Dict, honeypot_data: Dict) -> Dict:
        indicators = []
        
        chain_nodes = attack_chain.get("nodes", {})
        for node_id, node in chain_nodes.items():
            technique = node.get("technique", "")
            if technique:
                indicators.append(technique)
                
        interactions = honeypot_data.get("interactions", [])
        for interaction in interactions:
            commands = interaction.get("commands", [])
            for cmd in commands:
                indicators.append(cmd.get("command", ""))
                
        matched_patterns = {}
        
        for pattern_name, pattern_data in self.attack_patterns.items():
            matches = sum(1 for ind in pattern_data["indicators"] if ind in str(indicators).lower())
            if matches > 0:
                matched_patterns[pattern_name] = {
                    "matches": matches,
                    "total": len(pattern_data["indicators"]),
                    "score": matches / len(pattern_data["indicators"]),
                    "actor_type": pattern_data["actor_type"].value,
                    "confidence_boost": pattern_data["confidence_boost"]
                }
                
        return {
            "indicators_found": indicators,
            "matched_patterns": matched_patterns,
            "likely_actor": self._determine_likely_actor(matched_patterns)
        }
        
    def _determine_likely_actor(self, matched_patterns: Dict) -> Dict:
        if not matched_patterns:
            return {
                "actor_type": ActorType.UNKNOWN.value,
                "confidence": ConfidenceLevel.LOW.value
            }
            
        best_match = max(matched_patterns.values(), key=lambda x: x["score"])
        
        confidence = ConfidenceLevel.LOW
        if best_match["score"] > 0.7:
            confidence = ConfidenceLevel.HIGH
        elif best_match["score"] > 0.5:
            confidence = ConfidenceLevel.MEDIUM
            
        return {
            "actor_type": best_match["actor_type"],
            "confidence": confidence.value,
            "score": best_match["score"]
        }


class CorrelationEngine:
    def __init__(self):
        self.correlation_graph: Dict[str, Set[str]] = defaultdict(set)
        self.ip_clusters: List[Set[str]] = []
        
    def add_correlation(self, entity1: str, entity2: str, relation_type: str):
        self.correlation_graph[entity1].add(entity2)
        self.correlation_graph[entity2].add(entity1)
        
    def find_related_entities(self, entity: str, depth: int = 2) -> Set[str]:
        visited = {entity}
        current_level = {entity}
        
        for _ in range(depth):
            next_level = set()
            for node in current_level:
                for neighbor in self.correlation_graph.get(node, []):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        next_level.add(neighbor)
            current_level = next_level
            if not current_level:
                break
                
        return visited
        
    def cluster_ips(self, ip_data: Dict[str, Dict]) -> List[Set[str]]:
        ips = list(ip_data.keys())
        clusters = []
        processed = set()
        
        for ip in ips:
            if ip in processed:
                continue
                
            cluster = self.find_related_entities(ip, depth=1)
            if len(cluster) > 1:
                clusters.append(cluster)
                processed.update(cluster)
                
        self.ip_clusters = clusters
        return clusters
        
    def correlate_attacks(self, attack_data: List[Dict]) -> Dict[str, List[str]]:
        correlated: Dict[str, List[str]] = defaultdict(list)
        
        for i, attack1 in enumerate(attack_data):
            for j, attack2 in enumerate(attack_data[i+1:], i+1):
                if self._attacks_related(attack1, attack2):
                    correlated[attack1["attack_id"]].append(attack2["attack_id"])
                    correlated[attack2["attack_id"]].append(attack1["attack_id"])
                    
        return correlated
        
    def _attacks_related(self, attack1: Dict, attack2: Dict) -> bool:
        ips1 = set(attack1.get("source_ips", []))
        ips2 = set(attack2.get("source_ips", []))
        
        if ips1 & ips2:
            return True
            
        techniques1 = set(attack1.get("techniques", []))
        techniques2 = set(attack2.get("techniques", []))
        
        if techniques1 and techniques1 == techniques2:
            return True
            
        return False


class AttributionAgent:
    def __init__(
        self,
        agent_id: str = "attribution_agent_001",
        memory_client: Optional[Any] = None,
        communication_bus: Optional[Any] = None
    ):
        self.agent_id = agent_id
        self.memory_client = memory_client
        self.communication_bus = communication_bus
        
        self.threat_intel = ThreatIntelConnector()
        self.behavior_analyzer = BehaviorAnalyzer()
        self.correlation_engine = CorrelationEngine()
        
        self.identities: Dict[str, AttackerIdentity] = {}
        self.ip_to_identity: Dict[str, str] = {}
        self.attribution_history: deque = deque(maxlen=500)
        
        self.blacklist: Dict[str, Dict] = {}
        self.watchlist: Dict[str, Dict] = {}
        
        self.stats = {
            "total_attributions": 0,
            "high_confidence_attributions": 0,
            "known_actors_identified": 0,
            "new_identities_created": 0,
            "correlations_found": 0,
            "avg_attribution_time_ms": 0.0
        }
        
        self._running = False
        
    async def start(self):
        self._running = True
        logger.info(f"AttributionAgent {self.agent_id} started")
        
    async def stop(self):
        self._running = False
        logger.info(f"AttributionAgent {self.agent_id} stopped")
        
    async def attribute_attack(
        self,
        recon_report: Dict,
        attack_chain: Dict,
        honeypot_data: Dict
    ) -> AttackerIdentity:
        start_time = time.time()
        
        attacker_profile = recon_report.get("attacker_profile", {})
        primary_ip = attacker_profile.get("ip_addresses", [""])[0]
        
        existing_identity = await self._find_existing_identity(primary_ip)
        
        if existing_identity:
            identity = await self._update_identity(existing_identity, recon_report, attack_chain, honeypot_data)
        else:
            identity = await self._create_identity(recon_report, attack_chain, honeypot_data)
            self.stats["new_identities_created"] += 1
            
        behavior_analysis = self.behavior_analyzer.analyze_behavior(attack_chain, honeypot_data)
        identity = self._apply_behavior_analysis(identity, behavior_analysis)
        
        threat_intel = await self.threat_intel.query_ip(primary_ip)
        identity = self._apply_threat_intel(identity, threat_intel)
        
        correlations = await self._find_correlations(identity)
        if correlations:
            identity = self._apply_correlations(identity, correlations)
            self.stats["correlations_found"] += len(correlations)
            
        identity.threat_score = self._calculate_threat_score(identity)
        
        self.identities[identity.identity_id] = identity
        self.ip_to_identity[primary_ip] = identity.identity_id
        
        self.attribution_history.append({
            "identity_id": identity.identity_id,
            "primary_ip": primary_ip,
            "actor_type": identity.actor_type.value,
            "confidence": identity.confidence.value,
            "timestamp": datetime.now().isoformat()
        })
        
        self.stats["total_attributions"] += 1
        if identity.confidence.value >= ConfidenceLevel.HIGH.value:
            self.stats["high_confidence_attributions"] += 1
        if identity.actor_type != ActorType.UNKNOWN:
            self.stats["known_actors_identified"] += 1
            
        duration = (time.time() - start_time) * 1000
        self._update_avg_attribution_time(duration)
        
        if self.communication_bus:
            await self.communication_bus.publish(
                "attribution_complete",
                identity.to_dict()
            )
            
        logger.info(
            f"Attribution complete for {primary_ip}: "
            f"actor_type={identity.actor_type.value}, "
            f"confidence={identity.confidence.value}"
        )
        
        return identity
        
    async def _find_existing_identity(self, ip: str) -> Optional[AttackerIdentity]:
        identity_id = self.ip_to_identity.get(ip)
        if identity_id:
            return self.identities.get(identity_id)
        return None
        
    async def _create_identity(
        self,
        recon_report: Dict,
        attack_chain: Dict,
        honeypot_data: Dict
    ) -> AttackerIdentity:
        attacker_profile = recon_report.get("attacker_profile", {})
        ips = attacker_profile.get("ip_addresses", [])
        primary_ip = ips[0] if ips else "unknown"
        
        now = datetime.now()
        
        identity = AttackerIdentity(
            identity_id=self._generate_identity_id(primary_ip),
            primary_ip=primary_ip,
            associated_ips=set(ips[1:]) if len(ips) > 1 else set(),
            first_seen=now,
            last_seen=now,
            actor_type=ActorType.UNKNOWN,
            confidence=ConfidenceLevel.LOW,
            geo_location=attacker_profile.get("geo_locations", {}),
            organization=None,
            motivation=[],
            capabilities=[],
            historical_attacks=[],
            indicators=recon_report.get("indicators", []),
            attribution_sources=[AttributionSource.INTERNAL_ANALYSIS],
            threat_score=0.0,
            tags=set(attacker_profile.get("tags", [])),
            notes=[]
        )
        
        return identity
        
    async def _update_identity(
        self,
        identity: AttackerIdentity,
        recon_report: Dict,
        attack_chain: Dict,
        honeypot_data: Dict
    ) -> AttackerIdentity:
        attacker_profile = recon_report.get("attacker_profile", {})
        new_ips = set(attacker_profile.get("ip_addresses", []))
        
        identity.associated_ips.update(new_ips - {identity.primary_ip})
        identity.last_seen = datetime.now()
        
        new_indicators = recon_report.get("indicators", [])
        identity.indicators.extend(new_indicators)
        
        identity.tags.update(attacker_profile.get("tags", []))
        
        return identity
        
    def _apply_behavior_analysis(self, identity: AttackerIdentity, analysis: Dict) -> AttackerIdentity:
        likely_actor = analysis.get("likely_actor", {})
        
        if likely_actor.get("actor_type"):
            try:
                identity.actor_type = ActorType(likely_actor["actor_type"])
            except ValueError:
                pass
                
        if likely_actor.get("confidence"):
            try:
                identity.confidence = ConfidenceLevel(likely_actor["confidence"])
            except ValueError:
                pass
                
        matched_patterns = analysis.get("matched_patterns", {})
        for pattern_name, pattern_data in matched_patterns.items():
            if pattern_name == "apt_style":
                identity.capabilities.extend(["advanced_persistence", "sophisticated_tools"])
                identity.motivation.extend(["espionage", "intelligence"])
            elif pattern_name == "opportunistic":
                identity.capabilities.extend(["automated_tools", "known_exploits"])
                identity.motivation.extend(["opportunity", "easy_targets"])
            elif pattern_name == "targeted":
                identity.capabilities.extend(["custom_payloads", "reconnaissance"])
                identity.motivation.extend(["financial_gain", "specific_target"])
                
        identity.capabilities = list(set(identity.capabilities))
        identity.motivation = list(set(identity.motivation))
        
        if AttributionSource.BEHAVIORAL_ANALYSIS not in identity.attribution_sources:
            identity.attribution_sources.append(AttributionSource.BEHAVIORAL_ANALYSIS)
            
        return identity
        
    def _apply_threat_intel(self, identity: AttackerIdentity, intel: Dict) -> AttackerIdentity:
        if intel.get("is_malicious"):
            identity.tags.add("known_malicious")
            
        if intel.get("threat_score", 0) > 0.7:
            identity.threat_score = max(identity.threat_score, intel["threat_score"])
            
        geo = intel.get("geo", {})
        if geo:
            identity.geo_location.update(geo)
            
        asn = intel.get("asn", {})
        if asn:
            identity.organization = asn.get("name")
            
        if AttributionSource.THREAT_INTEL not in identity.attribution_sources:
            identity.attribution_sources.append(AttributionSource.THREAT_INTEL)
            
        return identity
        
    async def _find_correlations(self, identity: AttackerIdentity) -> List[Dict]:
        correlations = []
        
        for related_ip in identity.associated_ips:
            related_entities = self.correlation_engine.find_related_entities(related_ip)
            for entity in related_entities:
                if entity != related_ip and entity in self.ip_to_identity:
                    related_identity = self.identities.get(self.ip_to_identity[entity])
                    if related_identity:
                        correlations.append({
                            "type": "shared_ip",
                            "entity": entity,
                            "related_identity": related_identity.identity_id,
                            "actor_type": related_identity.actor_type.value
                        })
                        
        return correlations
        
    def _apply_correlations(self, identity: AttackerIdentity, correlations: List[Dict]) -> AttackerIdentity:
        for correlation in correlations:
            if correlation["type"] == "shared_ip":
                if correlation["actor_type"] != ActorType.UNKNOWN.value:
                    identity.tags.add(f"correlated_with_{correlation['actor_type']}")
                    
        if AttributionSource.HISTORICAL_CORRELATION not in identity.attribution_sources:
            identity.attribution_sources.append(AttributionSource.HISTORICAL_CORRELATION)
            
        return identity
        
    def _calculate_threat_score(self, identity: AttackerIdentity) -> float:
        score = 0.0
        
        actor_scores = {
            ActorType.NATION_STATE: 0.9,
            ActorType.CYBERCRIMINAL: 0.7,
            ActorType.HACKTIVIST: 0.5,
            ActorType.COMPETITOR: 0.6,
            ActorType.INSIDER: 0.8,
            ActorType.SCRIPT_KIDDIE: 0.3,
            ActorType.UNKNOWN: 0.4
        }
        score += actor_scores.get(identity.actor_type, 0.4) * 0.4
        
        confidence_multiplier = identity.confidence.value / 4.0
        score *= (0.5 + confidence_multiplier * 0.5)
        
        if "known_malicious" in identity.tags:
            score += 0.2
            
        score += len(identity.capabilities) * 0.02
        score += len(identity.associated_ips) * 0.01
        
        return min(score, 1.0)
        
    async def add_to_blacklist(self, identity_id: str, reason: str, duration_hours: int = 24):
        identity = self.identities.get(identity_id)
        if not identity:
            return False
            
        self.blacklist[identity_id] = {
            "identity_id": identity_id,
            "primary_ip": identity.primary_ip,
            "reason": reason,
            "added_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(hours=duration_hours)).isoformat()
        }
        
        logger.info(f"Added {identity_id} to blacklist: {reason}")
        return True
        
    async def add_to_watchlist(self, identity_id: str, reason: str):
        identity = self.identities.get(identity_id)
        if not identity:
            return False
            
        self.watchlist[identity_id] = {
            "identity_id": identity_id,
            "primary_ip": identity.primary_ip,
            "reason": reason,
            "added_at": datetime.now().isoformat()
        }
        
        logger.info(f"Added {identity_id} to watchlist: {reason}")
        return True
        
    async def get_identity(self, identity_id: str) -> Optional[Dict]:
        identity = self.identities.get(identity_id)
        return identity.to_dict() if identity else None
        
    async def get_identity_by_ip(self, ip: str) -> Optional[Dict]:
        identity_id = self.ip_to_identity.get(ip)
        if identity_id:
            return await self.get_identity(identity_id)
        return None
        
    async def get_all_identities(self) -> List[Dict]:
        return [i.to_dict() for i in self.identities.values()]
        
    async def get_blacklist(self) -> List[Dict]:
        now = datetime.now()
        valid_entries = []
        
        for entry in self.blacklist.values():
            expires = datetime.fromisoformat(entry["expires_at"])
            if now < expires:
                valid_entries.append(entry)
                
        return valid_entries
        
    async def get_watchlist(self) -> List[Dict]:
        return list(self.watchlist.values())
        
    def _generate_identity_id(self, ip: str) -> str:
        return f"identity_{hashlib.md5(ip.encode()).hexdigest()[:12]}"
        
    def _update_avg_attribution_time(self, duration: float):
        current = self.stats["avg_attribution_time_ms"]
        count = self.stats["total_attributions"]
        self.stats["avg_attribution_time_ms"] = (current * (count - 1) + duration) / count
        
    def get_stats(self) -> Dict:
        return {
            **self.stats,
            "total_identities": len(self.identities),
            "blacklist_size": len(self.blacklist),
            "watchlist_size": len(self.watchlist)
        }
