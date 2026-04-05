"""
业务涌现行为观测器
Business Emergence Observer

发现业务智能体协作中的涌现模式
"""

import os
import json
import time
import logging
import threading
import uuid
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import deque, defaultdict
import random
import math

logger = logging.getLogger(__name__)


class PatternType(Enum):
    COLLABORATION = "collaboration"
    SEQUENCE = "sequence"
    PARALLEL = "parallel"
    FEEDBACK_LOOP = "feedback_loop"
    HIERARCHICAL = "hierarchical"
    EMERGENT = "emergent"


class PatternEffectiveness(Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    UNKNOWN = "unknown"


@dataclass
class EmergencePattern:
    pattern_id: str
    pattern_type: PatternType
    name: str
    description: str
    agents_involved: List[str]
    sequence: List[Dict]
    frequency: int
    first_observed: float
    last_observed: float
    effectiveness: PatternEffectiveness
    impact_score: float
    conditions: List[Dict]
    outcomes: List[Dict]
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "pattern_id": self.pattern_id,
            "pattern_type": self.pattern_type.value,
            "name": self.name,
            "description": self.description,
            "agents_involved": self.agents_involved,
            "sequence": self.sequence,
            "frequency": self.frequency,
            "first_observed": self.first_observed,
            "last_observed": self.last_observed,
            "effectiveness": self.effectiveness.value,
            "impact_score": self.impact_score,
            "conditions": self.conditions,
            "outcomes": self.outcomes,
            "metadata": self.metadata
        }


@dataclass
class CollaborationNetwork:
    network_id: str
    timestamp: float
    nodes: Dict[str, Dict]
    edges: List[Dict]
    communities: List[List[str]]
    centrality: Dict[str, float]
    density: float
    clustering_coefficient: float
    
    def to_dict(self) -> Dict:
        return {
            "network_id": self.network_id,
            "timestamp": self.timestamp,
            "nodes": self.nodes,
            "edges": self.edges,
            "communities": self.communities,
            "centrality": self.centrality,
            "density": self.density,
            "clustering_coefficient": self.clustering_coefficient
        }


class BusinessEmergenceObserver:
    """
    业务涌现行为观测器
    
    发现业务智能体协作中的涌现模式：
    1. 数据采集：订阅通信日志、任务记录、规则触发
    2. 模式识别：时间序列聚类、图神经网络分析
    3. 涌现模式存储：存入记忆智能体
    4. 可视化：涌现网络图
    5. 反馈：固化有效模式
    """
    
    def __init__(
        self,
        blackboard: Optional[Any] = None,
        communication_bus: Optional[Any] = None,
        memory_agent: Optional[Any] = None,
        observation_window: float = 3600,
        min_pattern_frequency: int = 3,
    ):
        self.blackboard = blackboard
        self.communication_bus = communication_bus
        self.memory_agent = memory_agent
        self.observation_window = observation_window
        self.min_pattern_frequency = min_pattern_frequency
        
        self.patterns: Dict[str, EmergencePattern] = {}
        self.networks: deque = deque(maxlen=100)
        
        self.event_buffer: deque = deque(maxlen=10000)
        self.interaction_graph: Dict[str, Set[str]] = defaultdict(set)
        self.interaction_weights: Dict[Tuple[str, str], float] = defaultdict(float)
        
        self._lock = threading.RLock()
        self._running = False
        self._observer_task: Optional[asyncio.Task] = None
        
        self.stats = {
            "events_collected": 0,
            "patterns_discovered": 0,
            "patterns_positive": 0,
            "patterns_negative": 0,
            "networks_analyzed": 0,
            "anomalies_detected": 0,
        }
    
    async def start(self):
        self._running = True
        self._observer_task = asyncio.create_task(self._observation_loop())
        logger.info("Business emergence observer started")
    
    async def stop(self):
        self._running = False
        if self._observer_task:
            self._observer_task.cancel()
            try:
                await self._observer_task
            except asyncio.CancelledError:
                pass
        logger.info("Business emergence observer stopped")
    
    async def _observation_loop(self):
        while self._running:
            try:
                await self._collect_events()
                await self._analyze_patterns()
                await self._build_network()
                await asyncio.sleep(30)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in observation loop: {e}")
                await asyncio.sleep(5)
    
    async def record_event(
        self,
        event_type: str,
        agent_id: str,
        data: Dict,
        timestamp: Optional[float] = None,
    ):
        event = {
            "event_id": f"evt_{uuid.uuid4().hex[:8]}",
            "event_type": event_type,
            "agent_id": agent_id,
            "data": data,
            "timestamp": timestamp or time.time(),
        }
        
        with self._lock:
            self.event_buffer.append(event)
            self.stats["events_collected"] += 1
        
        if event_type == "collaboration":
            target_agent = data.get("target_agent")
            if target_agent:
                self.interaction_graph[agent_id].add(target_agent)
                self.interaction_graph[target_agent].add(agent_id)
                edge = (min(agent_id, target_agent), max(agent_id, target_agent))
                self.interaction_weights[edge] += 1
    
    async def _collect_events(self):
        if self.blackboard:
            try:
                events = await self.blackboard.read("agent_events")
                if events:
                    for event in events:
                        await self.record_event(
                            event_type=event.get("type", "unknown"),
                            agent_id=event.get("agent_id", ""),
                            data=event.get("data", {}),
                            timestamp=event.get("timestamp")
                        )
            except Exception as e:
                logger.error(f"Failed to collect events from blackboard: {e}")
    
    async def _analyze_patterns(self):
        current_time = time.time()
        window_start = current_time - self.observation_window
        
        recent_events = [
            e for e in self.event_buffer
            if e["timestamp"] >= window_start
        ]
        
        if len(recent_events) < 10:
            return
        
        sequences = self._extract_sequences(recent_events)
        
        for seq in sequences:
            pattern = self._identify_pattern(seq)
            if pattern:
                await self._store_pattern(pattern)
        
        anomalies = self._detect_anomalies(recent_events)
        for anomaly in anomalies:
            self.stats["anomalies_detected"] += 1
            logger.info(f"Anomaly detected: {anomaly}")
    
    def _extract_sequences(self, events: List[Dict]) -> List[List[Dict]]:
        sequences = []
        
        task_events: Dict[str, List[Dict]] = defaultdict(list)
        for event in events:
            task_id = event.get("data", {}).get("task_id")
            if task_id:
                task_events[task_id].append(event)
        
        for task_id, task_event_list in task_events.items():
            task_event_list.sort(key=lambda e: e["timestamp"])
            if len(task_event_list) >= 2:
                sequences.append(task_event_list)
        
        agent_sequences = self._find_agent_sequences(events)
        sequences.extend(agent_sequences)
        
        return sequences
    
    def _find_agent_sequences(self, events: List[Dict]) -> List[List[Dict]]:
        sequences = []
        
        events_by_time = sorted(events, key=lambda e: e["timestamp"])
        
        current_sequence = []
        last_agent = None
        
        for event in events_by_time:
            agent_id = event["agent_id"]
            
            if last_agent and agent_id != last_agent:
                if len(current_sequence) >= 2:
                    sequences.append(current_sequence.copy())
                current_sequence = [event]
            else:
                current_sequence.append(event)
            
            last_agent = agent_id
        
        if len(current_sequence) >= 2:
            sequences.append(current_sequence)
        
        return sequences
    
    def _identify_pattern(self, sequence: List[Dict]) -> Optional[EmergencePattern]:
        if len(sequence) < 2:
            return None
        
        agents = list(set(e["agent_id"] for e in sequence))
        
        if len(agents) < 2:
            return None
        
        event_types = [e["event_type"] for e in sequence]
        event_pattern = "->".join(event_types)
        
        pattern_key = f"{event_pattern}_{len(agents)}"
        
        existing_pattern = None
        for p in self.patterns.values():
            if p.name == pattern_key:
                existing_pattern = p
                break
        
        if existing_pattern:
            existing_pattern.frequency += 1
            existing_pattern.last_observed = time.time()
            return None
        
        if not self._is_significant_pattern(sequence):
            return None
        
        pattern = EmergencePattern(
            pattern_id=f"pattern_{uuid.uuid4().hex[:8]}",
            pattern_type=self._determine_pattern_type(sequence),
            name=pattern_key,
            description=f"Pattern involving {len(agents)} agents: {event_pattern}",
            agents_involved=agents,
            sequence=[{"event_type": e["event_type"], "agent_id": e["agent_id"]} for e in sequence],
            frequency=1,
            first_observed=sequence[0]["timestamp"],
            last_observed=sequence[-1]["timestamp"],
            effectiveness=PatternEffectiveness.UNKNOWN,
            impact_score=0.0,
            conditions=self._extract_conditions(sequence),
            outcomes=self._extract_outcomes(sequence),
        )
        
        return pattern
    
    def _determine_pattern_type(self, sequence: List[Dict]) -> PatternType:
        agents = [e["agent_id"] for e in sequence]
        unique_agents = set(agents)
        
        if len(unique_agents) == len(agents):
            return PatternType.SEQUENCE
        
        timestamps = [e["timestamp"] for e in sequence]
        time_diffs = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
        
        if all(diff < 1.0 for diff in time_diffs):
            return PatternType.PARALLEL
        
        if len(unique_agents) < len(agents) / 2:
            return PatternType.FEEDBACK_LOOP
        
        return PatternType.COLLABORATION
    
    def _is_significant_pattern(self, sequence: List[Dict]) -> bool:
        if len(sequence) < 2:
            return False
        
        agents = set(e["agent_id"] for e in sequence)
        if len(agents) < 2:
            return False
        
        return True
    
    def _extract_conditions(self, sequence: List[Dict]) -> List[Dict]:
        conditions = []
        
        first_event = sequence[0]
        conditions.append({
            "type": "trigger",
            "event_type": first_event["event_type"],
            "agent_id": first_event["agent_id"],
        })
        
        return conditions
    
    def _extract_outcomes(self, sequence: List[Dict]) -> List[Dict]:
        outcomes = []
        
        last_event = sequence[-1]
        outcomes.append({
            "type": "result",
            "event_type": last_event["event_type"],
            "agent_id": last_event["agent_id"],
        })
        
        return outcomes
    
    async def _store_pattern(self, pattern: EmergencePattern):
        with self._lock:
            self.patterns[pattern.pattern_id] = pattern
            self.stats["patterns_discovered"] += 1
        
        if self.memory_agent:
            try:
                await self.memory_agent.store({
                    "type": "emergence_pattern",
                    "pattern": pattern.to_dict(),
                    "timestamp": time.time()
                })
            except Exception as e:
                logger.error(f"Failed to store pattern to memory: {e}")
        
        logger.info(f"Pattern discovered: {pattern.pattern_id} - {pattern.name}")
    
    def _detect_anomalies(self, events: List[Dict]) -> List[Dict]:
        anomalies = []
        
        agent_event_counts: Dict[str, int] = defaultdict(int)
        for event in events:
            agent_event_counts[event["agent_id"]] += 1
        
        if agent_event_counts:
            counts = list(agent_event_counts.values())
            mean_count = sum(counts) / len(counts)
            std_count = (sum((c - mean_count) ** 2 for c in counts) / len(counts)) ** 0.5
            
            for agent_id, count in agent_event_counts.items():
                if std_count > 0 and abs(count - mean_count) > 2 * std_count:
                    anomalies.append({
                        "type": "activity_anomaly",
                        "agent_id": agent_id,
                        "event_count": count,
                        "expected": mean_count,
                        "deviation": abs(count - mean_count) / std_count
                    })
        
        return anomalies
    
    async def _build_network(self):
        nodes = {}
        for agent_id, connections in self.interaction_graph.items():
            nodes[agent_id] = {
                "id": agent_id,
                "connections": len(connections),
                "total_interactions": sum(
                    self.interaction_weights.get((min(agent_id, c), max(agent_id, c)), 0)
                    for c in connections
                )
            }
        
        edges = []
        for (source, target), weight in self.interaction_weights.items():
            if weight > 0:
                edges.append({
                    "source": source,
                    "target": target,
                    "weight": weight
                })
        
        communities = self._detect_communities(nodes, edges)
        
        centrality = self._calculate_centrality(nodes, edges)
        
        density = self._calculate_density(nodes, edges)
        
        clustering = self._calculate_clustering(nodes, edges)
        
        network = CollaborationNetwork(
            network_id=f"net_{uuid.uuid4().hex[:8]}",
            timestamp=time.time(),
            nodes=nodes,
            edges=edges,
            communities=communities,
            centrality=centrality,
            density=density,
            clustering_coefficient=clustering,
        )
        
        with self._lock:
            self.networks.append(network)
            self.stats["networks_analyzed"] += 1
    
    def _detect_communities(self, nodes: Dict, edges: List[Dict]) -> List[List[str]]:
        communities: List[Set[str]] = []
        
        for node_id in nodes:
            placed = False
            for community in communities:
                for member in community:
                    edge_key = (min(node_id, member), max(node_id, member))
                    if any(
                        e["source"] == edge_key[0] and e["target"] == edge_key[1]
                        for e in edges
                    ):
                        community.add(node_id)
                        placed = True
                        break
                if placed:
                    break
            
            if not placed:
                communities.append({node_id})
        
        return [list(c) for c in communities]
    
    def _calculate_centrality(self, nodes: Dict, edges: List[Dict]) -> Dict[str, float]:
        centrality = {}
        
        for node_id in nodes:
            degree = sum(1 for e in edges if e["source"] == node_id or e["target"] == node_id)
            centrality[node_id] = degree / max(len(nodes) - 1, 1)
        
        return centrality
    
    def _calculate_density(self, nodes: Dict, edges: List[Dict]) -> float:
        n = len(nodes)
        if n < 2:
            return 0.0
        
        max_edges = n * (n - 1) / 2
        actual_edges = len(edges)
        
        return actual_edges / max_edges
    
    def _calculate_clustering(self, nodes: Dict, edges: List[Dict]) -> float:
        if len(nodes) < 3:
            return 0.0
        
        edge_set = {(e["source"], e["target"]) for e in edges}
        edge_set |= {(e["target"], e["source"]) for e in edges}
        
        total_coefficient = 0.0
        
        for node_id in nodes:
            neighbors = set()
            for e in edges:
                if e["source"] == node_id:
                    neighbors.add(e["target"])
                elif e["target"] == node_id:
                    neighbors.add(e["source"])
            
            if len(neighbors) < 2:
                continue
            
            triangles = 0
            possible_triangles = len(neighbors) * (len(neighbors) - 1) / 2
            
            for n1 in neighbors:
                for n2 in neighbors:
                    if n1 < n2 and (n1, n2) in edge_set:
                        triangles += 1
            
            if possible_triangles > 0:
                total_coefficient += triangles / possible_triangles
        
        return total_coefficient / len(nodes)
    
    async def evaluate_pattern_effectiveness(
        self,
        pattern_id: str,
        kpi_data: Dict,
    ) -> PatternEffectiveness:
        if pattern_id not in self.patterns:
            return PatternEffectiveness.UNKNOWN
        
        pattern = self.patterns[pattern_id]
        
        success_rate = kpi_data.get("success_rate", 0.5)
        satisfaction = kpi_data.get("user_satisfaction", 0.5)
        efficiency = kpi_data.get("efficiency", 0.5)
        
        score = success_rate * 0.4 + satisfaction * 0.3 + efficiency * 0.3
        
        if score > 0.7:
            effectiveness = PatternEffectiveness.POSITIVE
            self.stats["patterns_positive"] += 1
        elif score < 0.3:
            effectiveness = PatternEffectiveness.NEGATIVE
            self.stats["patterns_negative"] += 1
        else:
            effectiveness = PatternEffectiveness.NEUTRAL
        
        pattern.effectiveness = effectiveness
        pattern.impact_score = score
        
        return effectiveness
    
    async def solidify_pattern(self, pattern_id: str) -> bool:
        if pattern_id not in self.patterns:
            return False
        
        pattern = self.patterns[pattern_id]
        
        if pattern.effectiveness != PatternEffectiveness.POSITIVE:
            return False
        
        if self.memory_agent:
            try:
                await self.memory_agent.store({
                    "type": "solidified_pattern",
                    "pattern": pattern.to_dict(),
                    "solidified_at": time.time()
                })
            except Exception as e:
                logger.error(f"Failed to solidify pattern: {e}")
                return False
        
        logger.info(f"Pattern solidified: {pattern_id}")
        return True
    
    def get_pattern(self, pattern_id: str) -> Optional[EmergencePattern]:
        return self.patterns.get(pattern_id)
    
    def get_patterns_by_type(self, pattern_type: PatternType) -> List[EmergencePattern]:
        return [
            p for p in self.patterns.values()
            if p.pattern_type == pattern_type
        ]
    
    def get_patterns_by_agent(self, agent_id: str) -> List[EmergencePattern]:
        return [
            p for p in self.patterns.values()
            if agent_id in p.agents_involved
        ]
    
    def get_latest_network(self) -> Optional[CollaborationNetwork]:
        if self.networks:
            return self.networks[-1]
        return None
    
    def get_network_history(self, limit: int = 10) -> List[CollaborationNetwork]:
        return list(self.networks)[-limit:]
    
    def get_stats(self) -> Dict:
        with self._lock:
            return {
                **self.stats,
                "total_patterns": len(self.patterns),
                "network_snapshots": len(self.networks),
                "event_buffer_size": len(self.event_buffer),
                "interaction_graph_size": len(self.interaction_graph),
            }
