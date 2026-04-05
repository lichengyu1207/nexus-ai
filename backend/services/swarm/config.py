# -*- coding: utf-8 -*-
"""
Agent Swarm 配置管理模块
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import json


@dataclass
class SwarmConfig:
    max_agents: int = 100
    heartbeat_interval_seconds: int = 30
    heartbeat_timeout_seconds: int = 90
    bid_timeout_seconds: int = 10
    max_bid_wait_ms: int = 5000
    default_collaboration_mode: str = "parallel"
    max_decomposition_level: int = 5
    task_retry_limit: int = 3
    redundancy_level: int = 1
    flood_ttl: int = 3
    load_threshold_high: float = 0.8
    load_threshold_low: float = 0.3
    bid_score_weights: Dict[str, float] = field(default_factory=lambda: {
        "load": 0.4,
        "capability_match": 0.4,
        "history_success": 0.2
    })
    
    def get_collaboration_mode(self, task_type: str) -> str:
        mode_mapping = {
            "analysis": "parallel",
            "report": "sequential",
            "consultation": "debate",
            "data_collection": "parallel",
            "risk_assessment": "debate"
        }
        return mode_mapping.get(task_type, self.default_collaboration_mode)
    
    def should_decompose(self, task_complexity: float) -> bool:
        return task_complexity > 0.7
    
    def is_agent_overloaded(self, load: float) -> bool:
        return load >= self.load_threshold_high
    
    def is_agent_available(self, load: float) -> bool:
        return load <= self.load_threshold_low
    
    def to_dict(self) -> Dict:
        return {
            "max_agents": self.max_agents,
            "heartbeat_interval_seconds": self.heartbeat_interval_seconds,
            "heartbeat_timeout_seconds": self.heartbeat_timeout_seconds,
            "bid_timeout_seconds": self.bid_timeout_seconds,
            "max_bid_wait_ms": self.max_bid_wait_ms,
            "default_collaboration_mode": self.default_collaboration_mode,
            "max_decomposition_level": self.max_decomposition_level,
            "task_retry_limit": self.task_retry_limit,
            "redundancy_level": self.redundancy_level,
            "flood_ttl": self.flood_ttl,
            "load_threshold_high": self.load_threshold_high,
            "load_threshold_low": self.load_threshold_low,
            "bid_score_weights": self.bid_score_weights
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'SwarmConfig':
        return cls(
            max_agents=data.get("max_agents", 100),
            heartbeat_interval_seconds=data.get("heartbeat_interval_seconds", 30),
            heartbeat_timeout_seconds=data.get("heartbeat_timeout_seconds", 90),
            bid_timeout_seconds=data.get("bid_timeout_seconds", 10),
            max_bid_wait_ms=data.get("max_bid_wait_ms", 5000),
            default_collaboration_mode=data.get("default_collaboration_mode", "parallel"),
            max_decomposition_level=data.get("max_decomposition_level", 5),
            task_retry_limit=data.get("task_retry_limit", 3),
            redundancy_level=data.get("redundancy_level", 1),
            flood_ttl=data.get("flood_ttl", 3),
            load_threshold_high=data.get("load_threshold_high", 0.8),
            load_threshold_low=data.get("load_threshold_low", 0.3),
            bid_score_weights=data.get("bid_score_weights", {
                "load": 0.4, "capability_match": 0.4, "history_success": 0.2
            })
        )


DEFAULT_CONFIG = SwarmConfig()


def get_default_config() -> SwarmConfig:
    return DEFAULT_CONFIG
