"""
追踪智能体
Trace Agent

追踪攻击者的后续行为，建立攻击链图谱
基于ATT&CK框架记录攻击时间线、技术手法、目标资产
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


class MITRETactic(Enum):
    RECONNAISSANCE = "reconnaissance"
    RESOURCE_DEVELOPMENT = "resource_development"
    INITIAL_ACCESS = "initial_access"
    EXECUTION = "execution"
    PERSISTENCE = "persistence"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DEFENSE_EVASION = "defense_evasion"
    CREDENTIAL_ACCESS = "credential_access"
    DISCOVERY = "discovery"
    LATERAL_MOVEMENT = "lateral_movement"
    COLLECTION = "collection"
    COMMAND_AND_CONTROL = "command_and_control"
    EXFILTRATION = "exfiltration"
    IMPACT = "impact"


class MITRETechnique(Enum):
    T1595 = "active_scanning"
    T1190 = "exploit_public_facing_application"
    T1133 = "external_remote_services"
    T1566 = "phishing"
    T1078 = "valid_accounts"
    T1059 = "command_and_scripting_interpreter"
    T1053 = "scheduled_task_job"
    T1543 = "create_or_modify_system_process"
    T1003 = "os_credential_dumping"
    T1110 = "brute_force"
    T1021 = "remote_services"
    T1048 = "exfiltration_over_alternative_protocol"
    T1486 = "data_encrypted_for_impact"
    T1498 = "network_denial_of_service"


class AttackNode:
    def __init__(
        self,
        node_id: str,
        tactic: MITRETactic,
        technique: MITRETechnique,
        timestamp: datetime
    ):
        self.node_id = node_id
        self.tactic = tactic
        self.technique = technique
        self.timestamp = timestamp
        self.source_ip: Optional[str] = None
        self.target_asset: Optional[str] = None
        self.payload_hash: Optional[str] = None
        self.success: bool = False
        self.detected: bool = True
        self.details: Dict[str, Any] = {}
        self.indicators: List[Dict] = []
        self.duration_ms: float = 0.0
        self.child_nodes: List[str] = []
        self.parent_nodes: List[str] = []
        
    def to_dict(self) -> Dict:
        return {
            "node_id": self.node_id,
            "tactic": self.tactic.value,
            "technique": self.technique.value,
            "timestamp": self.timestamp.isoformat(),
            "source_ip": self.source_ip,
            "target_asset": self.target_asset,
            "payload_hash": self.payload_hash,
            "success": self.success,
            "detected": self.detected,
            "details": self.details,
            "indicators": self.indicators,
            "duration_ms": self.duration_ms,
            "child_nodes": self.child_nodes,
            "parent_nodes": self.parent_nodes
        }


class AttackChain:
    def __init__(self, chain_id: str, attacker_id: str):
        self.chain_id = chain_id
        self.attacker_id = attacker_id
        self.nodes: Dict[str, AttackNode] = {}
        self.root_nodes: List[str] = []
        self.start_time = datetime.now()
        self.last_update = datetime.now()
        self.current_phase: Optional[MITRETactic] = None
        self.predicted_next_phase: Optional[MITRETactic] = None
        self.target_assets: Set[str] = set()
        self.total_duration_ms: float = 0.0
        self.success_count = 0
        self.detected_count = 0
        self.status = "active"
        
    def add_node(self, node: AttackNode, parent_ids: Optional[List[str]] = None):
        self.nodes[node.node_id] = node
        self.last_update = datetime.now()
        
        if parent_ids:
            for parent_id in parent_ids:
                if parent_id in self.nodes:
                    node.parent_nodes.append(parent_id)
                    self.nodes[parent_id].child_nodes.append(node.node_id)
        else:
            self.root_nodes.append(node.node_id)
            
        if node.target_asset:
            self.target_assets.add(node.target_asset)
            
        if node.success:
            self.success_count += 1
        if node.detected:
            self.detected_count += 1
            
        self.current_phase = node.tactic
        self._update_predictions()
        
    def _update_predictions(self):
        phase_order = list(MITRETactic)
        if self.current_phase:
            try:
                current_idx = phase_order.index(self.current_phase)
                if current_idx < len(phase_order) - 1:
                    self.predicted_next_phase = phase_order[current_idx + 1]
            except ValueError:
                pass
                
    def get_timeline(self) -> List[Dict]:
        sorted_nodes = sorted(
            self.nodes.values(),
            key=lambda n: n.timestamp
        )
        return [n.to_dict() for n in sorted_nodes]
        
    def get_graph(self) -> Dict:
        nodes = []
        edges = []
        
        for node in self.nodes.values():
            nodes.append({
                "id": node.node_id,
                "label": f"{node.tactic.value}\n{node.technique.value}",
                "timestamp": node.timestamp.isoformat(),
                "success": node.success
            })
            
            for child_id in node.child_nodes:
                edges.append({
                    "source": node.node_id,
                    "target": child_id
                })
                
        return {
            "nodes": nodes,
            "edges": edges
        }
        
    def to_dict(self) -> Dict:
        return {
            "chain_id": self.chain_id,
            "attacker_id": self.attacker_id,
            "nodes": {k: v.to_dict() for k, v in self.nodes.items()},
            "root_nodes": self.root_nodes,
            "start_time": self.start_time.isoformat(),
            "last_update": self.last_update.isoformat(),
            "current_phase": self.current_phase.value if self.current_phase else None,
            "predicted_next_phase": self.predicted_next_phase.value if self.predicted_next_phase else None,
            "target_assets": list(self.target_assets),
            "total_duration_ms": self.total_duration_ms,
            "success_count": self.success_count,
            "detected_count": self.detected_count,
            "status": self.status
        }


class BehaviorModel:
    def __init__(self):
        self.attack_sequences: Dict[str, int] = defaultdict(int)
        self.phase_transitions: Dict[Tuple[MITRETactic, MITRETactic], int] = defaultdict(int)
        self.technique_patterns: Dict[str, List[MITRETechnique]] = {}
        
    def learn_from_chain(self, chain: AttackChain):
        nodes = sorted(chain.nodes.values(), key=lambda n: n.timestamp)
        
        sequence = []
        for i, node in enumerate(nodes):
            sequence.append(node.technique.value)
            
            if i > 0:
                prev_tactic = nodes[i-1].tactic
                self.phase_transitions[(prev_tactic, node.tactic)] += 1
                
        if sequence:
            seq_key = "|".join(sequence)
            self.attack_sequences[seq_key] += 1
            
    def predict_next_technique(self, current_technique: MITRETechnique) -> List[Tuple[MITRETechnique, float]]:
        predictions = []
        
        for seq, count in self.attack_sequences.items():
            techniques = seq.split("|")
            if techniques[-1] == current_technique.value:
                for tech in MITRETechnique:
                    if tech.value not in techniques:
                        score = count / (len(techniques) + 1)
                        predictions.append((tech, score))
                        
        predictions.sort(key=lambda x: x[1], reverse=True)
        return predictions[:5]
        
    def get_common_transitions(self, tactic: MITRETactic) -> List[Tuple[MITRETactic, float]]:
        transitions = []
        total = 0
        
        for (src, dst), count in self.phase_transitions.items():
            if src == tactic:
                transitions.append((dst, count))
                total += count
                
        if total > 0:
            transitions = [(t, c/total) for t, c in transitions]
            
        transitions.sort(key=lambda x: x[1], reverse=True)
        return transitions[:3]


class BotnetDetector:
    def __init__(self):
        self.ip_clusters: Dict[str, Set[str]] = {}
        self.behavior_clusters: Dict[str, List[str]] = {}
        
    def analyze_cluster(self, chains: List[AttackChain]) -> Dict[str, Any]:
        ip_behaviors: Dict[str, List[str]] = defaultdict(list)
        
        for chain in chains:
            for node in chain.nodes.values():
                if node.source_ip:
                    ip_behaviors[node.source_ip].append(node.technique.value)
                    
        clusters = self._cluster_by_behavior(ip_behaviors)
        
        return {
            "cluster_count": len(clusters),
            "clusters": [
                {
                    "cluster_id": f"cluster_{i}",
                    "ips": list(cluster),
                    "size": len(cluster)
                }
                for i, cluster in enumerate(clusters)
            ],
            "potential_botnet": len(clusters) > 0 and any(len(c) > 3 for c in clusters)
        }
        
    def _cluster_by_behavior(self, ip_behaviors: Dict[str, List[str]]) -> List[Set[str]]:
        clusters = []
        processed = set()
        
        for ip1, behaviors1 in ip_behaviors.items():
            if ip1 in processed:
                continue
                
            cluster = {ip1}
            processed.add(ip1)
            
            for ip2, behaviors2 in ip_behaviors.items():
                if ip2 in processed:
                    continue
                    
                similarity = self._behavior_similarity(behaviors1, behaviors2)
                if similarity > 0.7:
                    cluster.add(ip2)
                    processed.add(ip2)
                    
            if len(cluster) > 1:
                clusters.append(cluster)
                
        return clusters
        
    def _behavior_similarity(self, b1: List[str], b2: List[str]) -> float:
        if not b1 or not b2:
            return 0.0
            
        set1 = set(b1)
        set2 = set(b2)
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0


class TraceAgent:
    def __init__(
        self,
        agent_id: str = "trace_agent_001",
        memory_client: Optional[Any] = None,
        communication_bus: Optional[Any] = None
    ):
        self.agent_id = agent_id
        self.memory_client = memory_client
        self.communication_bus = communication_bus
        
        self.attack_chains: Dict[str, AttackChain] = {}
        self.attacker_to_chains: Dict[str, List[str]] = defaultdict(list)
        self.behavior_model = BehaviorModel()
        self.botnet_detector = BotnetDetector()
        
        self.recent_events: deque = deque(maxlen=1000)
        self.active_traces: Dict[str, datetime] = {}
        
        self.stats = {
            "total_events_processed": 0,
            "chains_created": 0,
            "chains_completed": 0,
            "nodes_added": 0,
            "predictions_made": 0,
            "botnets_detected": 0,
            "avg_chain_length": 0.0
        }
        
        self._running = False
        self._task: Optional[asyncio.Task] = None
        
    async def start(self):
        self._running = True
        self._task = asyncio.create_task(self._trace_loop())
        logger.info(f"TraceAgent {self.agent_id} started")
        
    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info(f"TraceAgent {self.agent_id} stopped")
        
    async def _trace_loop(self):
        while self._running:
            try:
                await self._cleanup_inactive_chains()
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in trace loop: {e}")
                await asyncio.sleep(5)
                
    async def _cleanup_inactive_chains(self):
        cutoff = datetime.now() - timedelta(hours=24)
        
        for chain_id, chain in list(self.attack_chains.items()):
            if chain.last_update < cutoff:
                chain.status = "completed"
                self.stats["chains_completed"] += 1
                
                self.behavior_model.learn_from_chain(chain)
                
                if self.memory_client:
                    await self._store_chain_to_memory(chain)
                    
        inactive_traces = [
            trace_id for trace_id, last_active in self.active_traces.items()
            if last_active < cutoff
        ]
        for trace_id in inactive_traces:
            self.active_traces.pop(trace_id, None)
            
    async def process_recon_report(self, report: Dict) -> Optional[AttackChain]:
        self.stats["total_events_processed"] += 1
        
        attacker_id = report.get("attacker_profile", {}).get("attacker_id")
        if not attacker_id:
            return None
            
        chain = await self._get_or_create_chain(attacker_id)
        
        attack_types = report.get("detected_attack_types", [])
        for attack_type in attack_types:
            node = self._create_node_from_attack_type(attack_type, report)
            if node:
                chain.add_node(node)
                self.stats["nodes_added"] += 1
                
        self.recent_events.append({
            "event_type": "recon_report",
            "attacker_id": attacker_id,
            "chain_id": chain.chain_id,
            "timestamp": datetime.now().isoformat()
        })
        
        self.active_traces[chain.chain_id] = datetime.now()
        
        if self.communication_bus:
            await self.communication_bus.publish(
                "trace_update",
                {
                    "chain_id": chain.chain_id,
                    "attacker_id": attacker_id,
                    "new_nodes": len(attack_types),
                    "current_phase": chain.current_phase.value if chain.current_phase else None
                }
            )
            
        return chain
        
    async def process_defense_event(self, event: Dict) -> Optional[AttackChain]:
        self.stats["total_events_processed"] += 1
        
        source_ip = event.get("source_ip")
        if not source_ip:
            return None
            
        attacker_id = self._find_attacker_by_ip(source_ip)
        if not attacker_id:
            return None
            
        chain_id = self._get_active_chain_for_attacker(attacker_id)
        if not chain_id:
            return None
            
        chain = self.attack_chains.get(chain_id)
        if not chain:
            return None
            
        node = self._create_node_from_defense_event(event)
        if node:
            chain.add_node(node)
            self.stats["nodes_added"] += 1
            
        self.active_traces[chain.chain_id] = datetime.now()
        
        return chain
        
    async def _get_or_create_chain(self, attacker_id: str) -> AttackChain:
        active_chain_id = self._get_active_chain_for_attacker(attacker_id)
        
        if active_chain_id:
            return self.attack_chains[active_chain_id]
            
        chain_id = self._generate_chain_id(attacker_id)
        chain = AttackChain(chain_id, attacker_id)
        
        self.attack_chains[chain_id] = chain
        self.attacker_to_chains[attacker_id].append(chain_id)
        self.stats["chains_created"] += 1
        
        logger.info(f"Created new attack chain {chain_id} for attacker {attacker_id}")
        
        return chain
        
    def _get_active_chain_for_attacker(self, attacker_id: str) -> Optional[str]:
        chain_ids = self.attacker_to_chains.get(attacker_id, [])
        
        for chain_id in reversed(chain_ids):
            chain = self.attack_chains.get(chain_id)
            if chain and chain.status == "active":
                return chain_id
                
        return None
        
    def _find_attacker_by_ip(self, ip: str) -> Optional[str]:
        for chain in self.attack_chains.values():
            for node in chain.nodes.values():
                if node.source_ip == ip:
                    return chain.attacker_id
        return None
        
    def _create_node_from_attack_type(self, attack_type: str, report: Dict) -> Optional[AttackNode]:
        mapping = {
            "port_scan": (MITRETactic.RECONNAISSANCE, MITRETechnique.T1595),
            "brute_force": (MITRETactic.CREDENTIAL_ACCESS, MITRETechnique.T1110),
            "sql_injection": (MITRETactic.INITIAL_ACCESS, MITRETechnique.T1190),
            "xss": (MITRETactic.INITIAL_ACCESS, MITRETechnique.T1190),
            "ddos": (MITRETactic.IMPACT, MITRETechnique.T1498),
            "phishing": (MITRETactic.INITIAL_ACCESS, MITRETechnique.T1566),
            "malware": (MITRETactic.EXECUTION, MITRETechnique.T1059),
            "zero_day": (MITRETactic.INITIAL_ACCESS, MITRETechnique.T1190),
            "data_exfiltration": (MITRETactic.EXFILTRATION, MITRETechnique.T1048),
            "privilege_escalation": (MITRETactic.PRIVILEGE_ESCALATION, MITRETechnique.T1078),
            "lateral_movement": (MITRETactic.LATERAL_MOVEMENT, MITRETechnique.T1021),
        }
        
        tactic, technique = mapping.get(attack_type, (MITRETactic.RECONNAISSANCE, MITRETechnique.T1595))
        
        node = AttackNode(
            node_id=self._generate_node_id(),
            tactic=tactic,
            technique=technique,
            timestamp=datetime.now()
        )
        
        profile = report.get("attacker_profile", {})
        node.source_ip = profile.get("ip_addresses", [""])[0] if profile.get("ip_addresses") else None
        node.detected = True
        node.success = False
        
        indicators = report.get("indicators", [])
        node.indicators = indicators
        
        return node
        
    def _create_node_from_defense_event(self, event: Dict) -> Optional[AttackNode]:
        event_type = event.get("event_type", "")
        
        mapping = {
            "blocked": (MITRETactic.DEFENSE_EVASION, MITRETechnique.T1078),
            "detected": (MITRETactic.DISCOVERY, MITRETechnique.T1595),
            "mitigated": (MITRETactic.IMPACT, MITRETechnique.T1486)
        }
        
        if event_type not in mapping:
            return None
            
        tactic, technique = mapping[event_type]
        
        node = AttackNode(
            node_id=self._generate_node_id(),
            tactic=tactic,
            technique=technique,
            timestamp=datetime.now()
        )
        
        node.source_ip = event.get("source_ip")
        node.target_asset = event.get("target_asset")
        node.detected = True
        node.success = event.get("blocked", False) == False
        node.details = event
        
        return node
        
    async def predict_next_actions(self, attacker_id: str) -> Dict:
        self.stats["predictions_made"] += 1
        
        chain_id = self._get_active_chain_for_attacker(attacker_id)
        if not chain_id:
            return {"predictions": [], "confidence": 0.0}
            
        chain = self.attack_chains.get(chain_id)
        if not chain or not chain.nodes:
            return {"predictions": [], "confidence": 0.0}
            
        latest_node = max(chain.nodes.values(), key=lambda n: n.timestamp)
        
        technique_predictions = self.behavior_model.predict_next_technique(latest_node.technique)
        
        phase_predictions = []
        if chain.current_phase:
            phase_predictions = self.behavior_model.get_common_transitions(chain.current_phase)
            
        predictions = {
            "attacker_id": attacker_id,
            "chain_id": chain_id,
            "current_phase": chain.current_phase.value if chain.current_phase else None,
            "predicted_next_phase": chain.predicted_next_phase.value if chain.predicted_next_phase else None,
            "technique_predictions": [
                {"technique": t.value, "score": s}
                for t, s in technique_predictions
            ],
            "phase_predictions": [
                {"phase": p.value, "probability": prob}
                for p, prob in phase_predictions
            ],
            "target_assets": list(chain.target_assets),
            "confidence": min(0.9, len(chain.nodes) * 0.1)
        }
        
        return predictions
        
    async def detect_botnet_activity(self) -> Dict:
        active_chains = [
            chain for chain in self.attack_chains.values()
            if chain.status == "active"
        ]
        
        result = self.botnet_detector.analyze_cluster(active_chains)
        
        if result.get("potential_botnet"):
            self.stats["botnets_detected"] += 1
            
            if self.communication_bus:
                await self.communication_bus.publish(
                    "botnet_detected",
                    result
                )
                
        return result
        
    async def get_attack_chain(self, chain_id: str) -> Optional[Dict]:
        chain = self.attack_chains.get(chain_id)
        return chain.to_dict() if chain else None
        
    async def get_attacker_chains(self, attacker_id: str) -> List[Dict]:
        chain_ids = self.attacker_to_chains.get(attacker_id, [])
        return [
            self.attack_chains[cid].to_dict()
            for cid in chain_ids
            if cid in self.attack_chains
        ]
        
    async def get_all_chains(self, status: Optional[str] = None) -> List[Dict]:
        chains = list(self.attack_chains.values())
        
        if status:
            chains = [c for c in chains if c.status == status]
            
        return [c.to_dict() for c in chains]
        
    async def get_chain_timeline(self, chain_id: str) -> List[Dict]:
        chain = self.attack_chains.get(chain_id)
        if not chain:
            return []
        return chain.get_timeline()
        
    async def get_chain_graph(self, chain_id: str) -> Optional[Dict]:
        chain = self.attack_chains.get(chain_id)
        if not chain:
            return None
        return chain.get_graph()
        
    async def _store_chain_to_memory(self, chain: AttackChain):
        if not self.memory_client:
            return
            
        try:
            await self.memory_client.store_attack_chain(chain.to_dict())
        except Exception as e:
            logger.error(f"Failed to store chain to memory: {e}")
            
    def _generate_chain_id(self, attacker_id: str) -> str:
        return f"chain_{attacker_id}_{int(time.time())}"
        
    def _generate_node_id(self) -> str:
        return f"node_{hashlib.md5(str(time.time()).encode()).hexdigest()[:12]}"
        
    def get_stats(self) -> Dict:
        total_nodes = sum(len(c.nodes) for c in self.attack_chains.values())
        active_chains = sum(1 for c in self.attack_chains.values() if c.status == "active")
        
        return {
            **self.stats,
            "total_chains": len(self.attack_chains),
            "active_chains": active_chains,
            "total_nodes": total_nodes,
            "avg_chain_length": total_nodes / len(self.attack_chains) if self.attack_chains else 0
        }
