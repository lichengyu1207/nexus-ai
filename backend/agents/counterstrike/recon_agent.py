"""
侦察智能体
Reconnaissance Agent

持续监控网络流量，识别攻击源，提取攻击特征
实现OODA循环的观察阶段
"""

import asyncio
import time
import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from collections import defaultdict, deque
import ipaddress
import structlog

logger = structlog.get_logger()


class AttackType(Enum):
    PORT_SCAN = "port_scan"
    BRUTE_FORCE = "brute_force"
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    DDoS = "ddos"
    MALWARE = "malware"
    PHISHING = "phishing"
    ZERO_DAY = "zero_day"
    DATA_EXFILTRATION = "data_exfiltration"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    LATERAL_MOVEMENT = "lateral_movement"
    UNKNOWN = "unknown"


class ThreatLevel(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class AttackerProfile:
    def __init__(
        self,
        attacker_id: str,
        ip_addresses: Set[str],
        first_seen: datetime,
        last_seen: datetime
    ):
        self.attacker_id = attacker_id
        self.ip_addresses = ip_addresses
        self.first_seen = first_seen
        self.last_seen = last_seen
        self.geo_locations: Dict[str, str] = {}
        self.device_fingerprints: Set[str] = set()
        self.attack_types: Dict[AttackType, int] = defaultdict(int)
        self.attack_count = 0
        self.success_rate = 0.0
        self.confidence_score = 0.0
        self.is_known_attacker = False
        self.associated_ips: Set[str] = set()
        self.behavior_patterns: List[Dict] = []
        self.target_preferences: Dict[str, int] = defaultdict(int)
        self.time_patterns: List[Dict] = []
        self.reputation_score = 0.0
        self.threat_level = ThreatLevel.LOW
        self.tags: Set[str] = set()
        
    def update_from_traffic(self, traffic_data: Dict):
        self.last_seen = datetime.now()
        self.attack_count += 1
        
        if "geo_location" in traffic_data:
            ip = traffic_data.get("source_ip", "")
            self.geo_locations[ip] = traffic_data["geo_location"]
            
        if "device_fingerprint" in traffic_data:
            self.device_fingerprints.add(traffic_data["device_fingerprint"])
            
        if "attack_type" in traffic_data:
            attack_type = traffic_data["attack_type"]
            if isinstance(attack_type, str):
                try:
                    attack_type = AttackType(attack_type)
                except ValueError:
                    attack_type = AttackType.UNKNOWN
            self.attack_types[attack_type] += 1
            
        if "target" in traffic_data:
            self.target_preferences[traffic_data["target"]] += 1
            
    def calculate_threat_level(self) -> ThreatLevel:
        if self.attack_count > 100 or self.success_rate > 0.5:
            self.threat_level = ThreatLevel.CRITICAL
        elif self.attack_count > 50 or self.success_rate > 0.3:
            self.threat_level = ThreatLevel.HIGH
        elif self.attack_count > 10 or self.success_rate > 0.1:
            self.threat_level = ThreatLevel.MEDIUM
        else:
            self.threat_level = ThreatLevel.LOW
        return self.threat_level
        
    def to_dict(self) -> Dict:
        return {
            "attacker_id": self.attacker_id,
            "ip_addresses": list(self.ip_addresses),
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "geo_locations": self.geo_locations,
            "device_fingerprints": list(self.device_fingerprints),
            "attack_types": {k.value: v for k, v in self.attack_types.items()},
            "attack_count": self.attack_count,
            "success_rate": self.success_rate,
            "confidence_score": self.confidence_score,
            "is_known_attacker": self.is_known_attacker,
            "associated_ips": list(self.associated_ips),
            "threat_level": self.threat_level.value,
            "reputation_score": self.reputation_score,
            "tags": list(self.tags),
            "target_preferences": dict(self.target_preferences)
        }


@dataclass
class ReconReport:
    report_id: str
    timestamp: datetime
    attacker_profile: AttackerProfile
    detected_attack_types: List[AttackType]
    threat_level: ThreatLevel
    confidence: float
    indicators: List[Dict]
    recommended_actions: List[str]
    related_historical_attacks: List[str]
    raw_traffic_samples: List[Dict]
    
    def to_dict(self) -> Dict:
        return {
            "report_id": self.report_id,
            "timestamp": self.timestamp.isoformat(),
            "attacker_profile": self.attacker_profile.to_dict(),
            "detected_attack_types": [t.value for t in self.detected_attack_types],
            "threat_level": self.threat_level.value,
            "confidence": self.confidence,
            "indicators": self.indicators,
            "recommended_actions": self.recommended_actions,
            "related_historical_attacks": self.related_historical_attacks,
            "raw_traffic_samples": self.raw_traffic_samples
        }


class TrafficAnalyzer:
    def __init__(self):
        self.patterns = self._load_attack_patterns()
        self.signature_db = self._load_signatures()
        
    def _load_attack_patterns(self) -> Dict[str, re.Pattern]:
        patterns = {
            "sql_injection": re.compile(
                r"(?i)(union\s+select|select\s+.*\s+from|"
                r"insert\s+into|delete\s+from|drop\s+table|"
                r"or\s+1\s*=\s*1|'\s*or\s*'|--|;--|\-\-)",
                re.IGNORECASE
            ),
            "xss": re.compile(
                r"(?i)(<script|javascript:|on\w+\s*=|"
                r"<iframe|<object|<embed|eval\s*\()",
                re.IGNORECASE
            ),
            "path_traversal": re.compile(
                r"(\.\.\/|\.\.\\|%2e%2e%2f|%2e%2e\/)",
                re.IGNORECASE
            ),
            "command_injection": re.compile(
                r"(;|\||`|\$\(|\$\{|&&|\|\||>\s*/|<\s*/)",
                re.IGNORECASE
            ),
            "brute_force_indicators": re.compile(
                r"(admin|root|test|user|guest|password)",
                re.IGNORECASE
            )
        }
        return patterns
        
    def _load_signatures(self) -> Dict[str, Dict]:
        return {
            "port_scan": {
                "threshold": 10,
                "time_window": 60,
                "description": "Multiple port connections in short time"
            },
            "brute_force": {
                "threshold": 5,
                "time_window": 300,
                "description": "Multiple failed authentication attempts"
            },
            "ddos": {
                "threshold": 1000,
                "time_window": 10,
                "description": "High volume requests from single source"
            }
        }
        
    def analyze_payload(self, payload: str) -> Tuple[List[AttackType], float]:
        detected_types = []
        confidence = 0.0
        
        if self.patterns["sql_injection"].search(payload):
            detected_types.append(AttackType.SQL_INJECTION)
            confidence = max(confidence, 0.9)
            
        if self.patterns["xss"].search(payload):
            detected_types.append(AttackType.XSS)
            confidence = max(confidence, 0.85)
            
        if self.patterns["path_traversal"].search(payload):
            detected_types.append(AttackType.ZERO_DAY)
            confidence = max(confidence, 0.8)
            
        if self.patterns["command_injection"].search(payload):
            detected_types.append(AttackType.ZERO_DAY)
            confidence = max(confidence, 0.85)
            
        if not detected_types:
            detected_types.append(AttackType.UNKNOWN)
            confidence = 0.3
            
        return detected_types, confidence
        
    def analyze_timing(self, requests: List[Dict]) -> Tuple[Optional[AttackType], float]:
        if not requests:
            return None, 0.0
            
        time_window = 60
        now = time.time()
        recent_requests = [r for r in requests if now - r.get("timestamp", 0) < time_window]
        
        if len(recent_requests) > self.signature_db["port_scan"]["threshold"]:
            ports = set(r.get("port", 0) for r in recent_requests)
            if len(ports) > 5:
                return AttackType.PORT_SCAN, 0.9
                
        auth_failures = [r for r in recent_requests if r.get("status_code") == 401]
        if len(auth_failures) > self.signature_db["brute_force"]["threshold"]:
            return AttackType.BRUTE_FORCE, 0.85
            
        return None, 0.0


class ThreatIntelligenceClient:
    def __init__(self):
        self.cache: Dict[str, Dict] = {}
        self.cache_ttl = 3600
        
    async def query_ip_reputation(self, ip: str) -> Dict:
        cache_key = f"ip_rep:{ip}"
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if time.time() - cached["timestamp"] < self.cache_ttl:
                return cached["data"]
                
        reputation = await self._query_external_apis(ip)
        
        self.cache[cache_key] = {
            "timestamp": time.time(),
            "data": reputation
        }
        
        return reputation
        
    async def _query_external_apis(self, ip: str) -> Dict:
        await asyncio.sleep(0.01)
        
        reputation = {
            "ip": ip,
            "is_malicious": False,
            "threat_score": 0.0,
            "categories": [],
            "first_reported": None,
            "last_reported": None,
            "confidence": 0.0,
            "sources": []
        }
        
        try:
            ip_obj = ipaddress.ip_address(ip)
            if ip_obj.is_private:
                reputation["is_malicious"] = False
                reputation["confidence"] = 1.0
                return reputation
        except ValueError:
            pass
            
        suspicious_ranges = [
            "192.168.100.0/24",
            "10.0.50.0/24"
        ]
        
        for range_str in suspicious_ranges:
            try:
                network = ipaddress.ip_network(range_str, strict=False)
                if ipaddress.ip_address(ip) in network:
                    reputation["is_malicious"] = True
                    reputation["threat_score"] = 0.7
                    reputation["categories"] = ["suspicious"]
                    break
            except ValueError:
                continue
                
        return reputation


class ReconAgent:
    def __init__(
        self,
        agent_id: str = "recon_agent_001",
        memory_client: Optional[Any] = None,
        communication_bus: Optional[Any] = None
    ):
        self.agent_id = agent_id
        self.memory_client = memory_client
        self.communication_bus = communication_bus
        
        self.traffic_analyzer = TrafficAnalyzer()
        self.threat_intel = ThreatIntelligenceClient()
        
        self.attacker_profiles: Dict[str, AttackerProfile] = {}
        self.ip_to_attacker: Dict[str, str] = {}
        self.traffic_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.recent_reports: deque = deque(maxlen=100)
        
        self.stats = {
            "total_traffic_processed": 0,
            "attacks_detected": 0,
            "unique_attackers": 0,
            "reports_generated": 0,
            "false_positives": 0,
            "avg_detection_latency_ms": 0.0
        }
        
        self._running = False
        self._task: Optional[asyncio.Task] = None
        
    async def start(self):
        self._running = True
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info(f"ReconAgent {self.agent_id} started")
        
    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info(f"ReconAgent {self.agent_id} stopped")
        
    async def _monitor_loop(self):
        while self._running:
            try:
                await self._cleanup_old_profiles()
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                await asyncio.sleep(5)
                
    async def _cleanup_old_profiles(self):
        cutoff = datetime.now() - timedelta(days=30)
        to_remove = []
        
        for attacker_id, profile in self.attacker_profiles.items():
            if profile.last_seen < cutoff:
                to_remove.append(attacker_id)
                
        for attacker_id in to_remove:
            profile = self.attacker_profiles.pop(attacker_id)
            for ip in profile.ip_addresses:
                self.ip_to_attacker.pop(ip, None)
                
        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} old attacker profiles")
            
    async def process_traffic(self, traffic_data: Dict) -> Optional[ReconReport]:
        start_time = time.time()
        self.stats["total_traffic_processed"] += 1
        
        source_ip = traffic_data.get("source_ip", "")
        if not source_ip:
            return None
            
        self.traffic_history[source_ip].append({
            "timestamp": time.time(),
            "port": traffic_data.get("port"),
            "method": traffic_data.get("method"),
            "path": traffic_data.get("path"),
            "status_code": traffic_data.get("status_code"),
            "payload": traffic_data.get("payload", "")
        })
        
        attack_types, confidence = await self._detect_attack(traffic_data)
        
        if not attack_types or attack_types == [AttackType.UNKNOWN]:
            return None
            
        self.stats["attacks_detected"] += 1
        
        attacker_profile = await self._get_or_create_attacker_profile(
            source_ip, traffic_data, attack_types
        )
        
        threat_level = attacker_profile.calculate_threat_level()
        
        historical_attacks = await self._query_historical_attacks(attacker_profile)
        
        report = ReconReport(
            report_id=self._generate_report_id(),
            timestamp=datetime.now(),
            attacker_profile=attacker_profile,
            detected_attack_types=attack_types,
            threat_level=threat_level,
            confidence=confidence,
            indicators=self._extract_indicators(traffic_data, attack_types),
            recommended_actions=self._generate_recommendations(threat_level, attack_types),
            related_historical_attacks=historical_attacks,
            raw_traffic_samples=list(self.traffic_history[source_ip])[-10:]
        )
        
        self.recent_reports.append(report)
        self.stats["reports_generated"] += 1
        
        latency = (time.time() - start_time) * 1000
        self._update_avg_latency(latency)
        
        if self.communication_bus:
            await self.communication_bus.publish(
                "recon_report",
                report.to_dict()
            )
            
        logger.info(
            f"Detected attack from {source_ip}: {[t.value for t in attack_types]}, "
            f"threat level: {threat_level.value}"
        )
        
        return report
        
    async def _detect_attack(self, traffic_data: Dict) -> Tuple[List[AttackType], float]:
        detected_types = []
        max_confidence = 0.0
        
        payload = traffic_data.get("payload", "")
        if payload:
            types, confidence = self.traffic_analyzer.analyze_payload(payload)
            detected_types.extend(types)
            max_confidence = max(max_confidence, confidence)
            
        source_ip = traffic_data.get("source_ip", "")
        history = list(self.traffic_history.get(source_ip, []))
        if history:
            timing_type, timing_conf = self.traffic_analyzer.analyze_timing(history)
            if timing_type:
                if timing_type not in detected_types:
                    detected_types.append(timing_type)
                max_confidence = max(max_confidence, timing_conf)
                
        if traffic_data.get("status_code") == 401:
            recent_401s = sum(
                1 for r in history[-10:]
                if r.get("status_code") == 401
            )
            if recent_401s >= 3:
                if AttackType.BRUTE_FORCE not in detected_types:
                    detected_types.append(AttackType.BRUTE_FORCE)
                max_confidence = max(max_confidence, 0.8)
                
        if not detected_types:
            detected_types = [AttackType.UNKNOWN]
            max_confidence = 0.3
            
        return detected_types, max_confidence
        
    async def _get_or_create_attacker_profile(
        self,
        source_ip: str,
        traffic_data: Dict,
        attack_types: List[AttackType]
    ) -> AttackerProfile:
        attacker_id = self.ip_to_attacker.get(source_ip)
        
        if attacker_id and attacker_id in self.attacker_profiles:
            profile = self.attacker_profiles[attacker_id]
            profile.update_from_traffic(traffic_data)
            return profile
            
        attacker_id = self._generate_attacker_id(source_ip)
        
        now = datetime.now()
        profile = AttackerProfile(
            attacker_id=attacker_id,
            ip_addresses={source_ip},
            first_seen=now,
            last_seen=now
        )
        
        reputation = await self.threat_intel.query_ip_reputation(source_ip)
        profile.reputation_score = reputation.get("threat_score", 0.0)
        profile.is_known_attacker = reputation.get("is_malicious", False)
        
        if reputation.get("is_malicious"):
            profile.tags.add("known_malicious")
            
        geo_location = await self._get_geo_location(source_ip)
        if geo_location:
            profile.geo_locations[source_ip] = geo_location
            
        device_fp = self._extract_device_fingerprint(traffic_data)
        if device_fp:
            profile.device_fingerprints.add(device_fp)
            
        profile.update_from_traffic(traffic_data)
        
        self.attacker_profiles[attacker_id] = profile
        self.ip_to_attacker[source_ip] = attacker_id
        self.stats["unique_attackers"] += 1
        
        return profile
        
    async def _query_historical_attacks(self, profile: AttackerProfile) -> List[str]:
        if not self.memory_client:
            return []
            
        try:
            results = await self.memory_client.search_similar_attacks(
                ip_addresses=list(profile.ip_addresses),
                attack_types=[t.value for t in profile.attack_types.keys()],
                limit=5
            )
            return results
        except Exception as e:
            logger.error(f"Failed to query historical attacks: {e}")
            return []
            
    def _extract_indicators(self, traffic_data: Dict, attack_types: List[AttackType]) -> List[Dict]:
        indicators = []
        
        source_ip = traffic_data.get("source_ip")
        if source_ip:
            indicators.append({
                "type": "ip",
                "value": source_ip,
                "confidence": 0.9
            })
            
        user_agent = traffic_data.get("user_agent")
        if user_agent:
            indicators.append({
                "type": "user_agent",
                "value": user_agent,
                "confidence": 0.7
            })
            
        payload = traffic_data.get("payload", "")
        if payload and len(payload) > 10:
            indicators.append({
                "type": "payload_pattern",
                "value": hashlib.md5(payload.encode()).hexdigest()[:16],
                "confidence": 0.8
            })
            
        return indicators
        
    def _generate_recommendations(
        self,
        threat_level: ThreatLevel,
        attack_types: List[AttackType]
    ) -> List[str]:
        recommendations = []
        
        if threat_level == ThreatLevel.CRITICAL:
            recommendations.extend([
                "立即封锁攻击源IP",
                "启动蜜罐诱捕",
                "通知安全团队",
                "准备溯源反击"
            ])
        elif threat_level == ThreatLevel.HIGH:
            recommendations.extend([
                "限制攻击源访问速率",
                "部署针对性蜜罐",
                "加强监控"
            ])
        elif threat_level == ThreatLevel.MEDIUM:
            recommendations.extend([
                "持续监控攻击源",
                "记录详细日志"
            ])
        else:
            recommendations.append("保持观察")
            
        if AttackType.SQL_INJECTION in attack_types:
            recommendations.append("检查数据库访问日志")
        if AttackType.BRUTE_FORCE in attack_types:
            recommendations.append("检查账户锁定策略")
        if AttackType.DDoS in attack_types:
            recommendations.append("启动DDoS缓解措施")
            
        return list(set(recommendations))
        
    def _generate_attacker_id(self, source_ip: str) -> str:
        hash_input = f"{source_ip}:{time.time()}"
        return f"attacker_{hashlib.md5(hash_input.encode()).hexdigest()[:12]}"
        
    def _generate_report_id(self) -> str:
        return f"recon_{int(time.time() * 1000)}_{hashlib.md5(str(time.time()).encode()).hexdigest()[:8]}"
        
    async def _get_geo_location(self, ip: str) -> Optional[str]:
        await asyncio.sleep(0.001)
        return "Unknown"
        
    def _extract_device_fingerprint(self, traffic_data: Dict) -> Optional[str]:
        components = []
        
        user_agent = traffic_data.get("user_agent", "")
        if user_agent:
            components.append(user_agent)
            
        headers = traffic_data.get("headers", {})
        for header in ["accept", "accept-language", "accept-encoding"]:
            if header in headers:
                components.append(str(headers[header]))
                
        if components:
            return hashlib.md5("|".join(components).encode()).hexdigest()[:16]
        return None
        
    def _update_avg_latency(self, latency: float):
        current = self.stats["avg_detection_latency_ms"]
        count = self.stats["reports_generated"]
        self.stats["avg_detection_latency_ms"] = (
            current * (count - 1) + latency
        ) / count
        
    async def get_attacker_profile(self, attacker_id: str) -> Optional[Dict]:
        profile = self.attacker_profiles.get(attacker_id)
        return profile.to_dict() if profile else None
        
    async def get_all_attackers(self) -> List[Dict]:
        return [p.to_dict() for p in self.attacker_profiles.values()]
        
    async def get_recent_reports(self, limit: int = 20) -> List[Dict]:
        reports = list(self.recent_reports)[-limit:]
        return [r.to_dict() for r in reports]
        
    def get_stats(self) -> Dict:
        return {
            **self.stats,
            "active_attackers": len(self.attacker_profiles),
            "tracked_ips": len(self.ip_to_attacker)
        }
