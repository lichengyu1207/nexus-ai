# -*- coding: utf-8 -*-
"""
Agent Swarm 竞标机制模块
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from uuid import UUID
import time

from .config import SwarmConfig
from .models import SwarmTask, SwarmAgent, SwarmBid, BidResult
from .agent import Agent


class CapabilityMatcher:
    def __init__(self, config: Optional[SwarmConfig] = None):
        self.config = config or SwarmConfig()
    
    def match(self, agent: Agent, task: SwarmTask) -> float:
        if not task.required_capabilities:
            return 0.5
        
        required = set(task.required_capabilities)
        available = set(agent.capabilities)
        
        intersection = len(required & available)
        union = len(required | available)
        
        if union == 0:
            return 0.0
        
        jaccard = intersection / union
        
        exact_match = intersection == len(required)
        
        if exact_match:
            return 1.0
        elif intersection > 0:
            return jaccard
        else:
            return 0.0
    
    def find_capable_agents(
        self, 
        agents: List[Agent], 
        task: SwarmTask,
        min_match: float = 0.3
    ) -> List[Tuple[Agent, float]]:
        matches = []
        
        for agent in agents:
            match_score = self.match(agent, task)
            if match_score >= min_match:
                matches.append((agent, match_score))
        
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches


class LoadBalancer:
    def __init__(self, config: Optional[SwarmConfig] = None):
        self.config = config or SwarmConfig()
    
    def get_load_factor(self, agent: Agent) -> float:
        if agent.max_concurrent_tasks == 0:
            return 1.0
        
        return agent.load / agent.max_concurrent_tasks
    
    def is_available(self, agent: Agent) -> bool:
        load_factor = self.get_load_factor(agent)
        return load_factor <= self.config.load_threshold_high
    
    def is_overloaded(self, agent: Agent) -> bool:
        load_factor = self.get_load_factor(agent)
        return load_factor >= self.config.load_threshold_high
    
    def find_available_agents(self, agents: List[Agent]) -> List[Agent]:
        return [a for a in agents if self.is_available(a)]
    
    def select_least_loaded(self, agents: List[Agent]) -> Optional[Agent]:
        available = self.find_available_agents(agents)
        if not available:
            return None
        
        return min(available, key=lambda a: a.load)


class BiddingEngine:
    def __init__(self, config: Optional[SwarmConfig] = None):
        self.config = config or SwarmConfig()
        self.capability_matcher = CapabilityMatcher(config)
        self.load_balancer = LoadBalancer(config)
    
    def collect_bids(
        self, 
        task: SwarmTask, 
        agents: List[Agent],
        timeout_ms: Optional[int] = None
    ) -> List[BidResult]:
        timeout_ms = timeout_ms or self.config.max_bid_wait_ms
        bids = []
        
        for agent in agents:
            if not self.load_balancer.is_available(agent):
                continue
            
            bid_result = agent.bid(task)
            
            if bid_result.score != float('inf'):
                bids.append(bid_result)
        
        return bids
    
    def select_winner(
        self, 
        bids: List[BidResult],
        method: str = "lowest_score"
    ) -> Optional[BidResult]:
        if not bids:
            return None
        
        valid_bids = [b for b in bids if b.score != float('inf')]
        if not valid_bids:
            return None
        
        if method == "lowest_score":
            return min(valid_bids, key=lambda b: b.score)
        elif method == "highest_confidence":
            return max(valid_bids, key=lambda b: b.confidence)
        elif method == "weighted":
            def weighted_score(b):
                return b.score * 0.6 + (1 - b.confidence) * 0.4
            return min(valid_bids, key=weighted_score)
        else:
            return min(valid_bids, key=lambda b: b.score)
    
    def run_bidding_process(
        self, 
        task: SwarmTask, 
        agents: List[Agent]
    ) -> Tuple[Optional[Agent], List[BidResult]]:
        capable_agents = self.capability_matcher.find_capable_agents(
            agents, task, min_match=0.3
        )
        
        if not capable_agents:
            return None, []
        
        candidate_agents = [a for a, _ in capable_agents]
        bids = self.collect_bids(task, candidate_agents)
        
        if not bids:
            return None, []
        
        winner_bid = self.select_winner(bids)
        
        if not winner_bid:
            return None, bids
        
        winner_agent = next(
            (a for a in agents if a.id == winner_bid.agent_id), 
            None
        )
        
        return winner_agent, bids
    
    def calculate_bid_score(
        self,
        agent: Agent,
        task: SwarmTask
    ) -> float:
        capability_match = self.capability_matcher.match(agent, task)
        
        if capability_match == 0:
            return float('inf')
        
        load_factor = self.load_balancer.get_load_factor(agent)
        
        history_factor = 1 - agent.history_success_rate
        
        weights = self.config.bid_score_weights
        
        score = (
            weights.get("load", 0.4) * load_factor +
            weights.get("capability_match", 0.4) * (1 - capability_match) +
            weights.get("history_success", 0.2) * history_factor
        )
        
        return score
    
    def get_bidding_statistics(self, bids: List[BidResult]) -> Dict:
        if not bids:
            return {
                "total_bids": 0,
                "valid_bids": 0,
                "avg_score": 0,
                "avg_confidence": 0,
                "min_score": 0,
                "max_score": 0
            }
        
        valid_bids = [b for b in bids if b.score != float('inf')]
        
        return {
            "total_bids": len(bids),
            "valid_bids": len(valid_bids),
            "avg_score": sum(b.score for b in valid_bids) / len(valid_bids) if valid_bids else 0,
            "avg_confidence": sum(b.confidence for b in valid_bids) / len(valid_bids) if valid_bids else 0,
            "min_score": min(b.score for b in valid_bids) if valid_bids else 0,
            "max_score": max(b.score for b in valid_bids) if valid_bids else 0
        }
