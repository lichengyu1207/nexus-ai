"""
合作博弈机制
Cooperative Game Mechanism

鼓励智能体协作完成复杂任务
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


class TeamFormationStrategy(Enum):
    SKILL_BASED = "skill_based"
    PERFORMANCE_BASED = "performance_based"
    RANDOM = "random"
    REPUTATION_BASED = "reputation_based"
    DIVERSITY_BASED = "diversity_based"


@dataclass
class TeamReward:
    team_id: str
    task_id: str
    total_reward: float
    contributions: Dict[str, float]
    allocations: Dict[str, float]
    allocation_method: str
    created_at: float
    distributed: bool = False
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "team_id": self.team_id,
            "task_id": self.task_id,
            "total_reward": self.total_reward,
            "contributions": self.contributions,
            "allocations": self.allocations,
            "allocation_method": self.allocation_method,
            "created_at": self.created_at,
            "distributed": self.distributed,
            "metadata": self.metadata
        }


class ContributionCalculator:
    """
    贡献度计算器
    
    计算团队成员的贡献度
    """
    
    def __init__(self):
        self.contribution_history: Dict[str, List[float]] = defaultdict(list)
    
    def calculate_shapley_values(
        self,
        agents: List[str],
        task_result: Dict,
    ) -> Dict[str, float]:
        n = len(agents)
        if n == 0:
            return {}
        
        if n == 1:
            return {agents[0]: 1.0}
        
        contributions = {}
        
        for agent in agents:
            shapley_value = 0.0
            
            for subset_size in range(n):
                weight = 1.0 / (n * math.comb(n - 1, subset_size))
                
                marginal_contribution = random.uniform(0.1, 0.3)
                
                shapley_value += weight * marginal_contribution * math.comb(n - 1, subset_size)
            
            contributions[agent] = shapley_value
        
        total = sum(contributions.values())
        if total > 0:
            contributions = {k: v / total for k, v in contributions.items()}
        
        return contributions
    
    def calculate_simple_ratio(
        self,
        agents: List[str],
        task_metrics: Dict,
    ) -> Dict[str, float]:
        if not agents:
            return {}
        
        n = len(agents)
        base_ratio = 1.0 / n
        
        contributions = {}
        for agent in agents:
            agent_work = task_metrics.get("agent_work", {}).get(agent, 1.0)
            contributions[agent] = base_ratio * agent_work
        
        total = sum(contributions.values())
        if total > 0:
            contributions = {k: v / total for k, v in contributions.items()}
        
        return contributions
    
    def calculate_weighted(
        self,
        agents: List[str],
        weights: Dict[str, float],
    ) -> Dict[str, float]:
        if not agents:
            return {}
        
        total_weight = sum(weights.get(a, 1.0) for a in agents)
        
        if total_weight == 0:
            return {a: 1.0 / len(agents) for a in agents}
        
        return {
            agent: weights.get(agent, 1.0) / total_weight
            for agent in agents
        }
    
    def record_contribution(self, agent_id: str, contribution: float):
        self.contribution_history[agent_id].append(contribution)
    
    def get_avg_contribution(self, agent_id: str) -> float:
        history = self.contribution_history.get(agent_id, [])
        if not history:
            return 0.0
        return sum(history) / len(history)


class CooperativeGameMechanism:
    """
    合作博弈机制
    
    鼓励智能体协作完成复杂任务：
    1. 团队奖励：按贡献度分配
    2. 默契协作：无需通信的配合
    3. 合作演化：成功团队获得繁衍机会
    """
    
    def __init__(
        self,
        collaboration_protocol: Optional[Any] = None,
        memory_agent: Optional[Any] = None,
        blackboard: Optional[Any] = None,
    ):
        self.collaboration_protocol = collaboration_protocol
        self.memory_agent = memory_agent
        self.blackboard = blackboard
        
        self.teams: Dict[str, Dict] = {}
        self.team_history: deque = deque(maxlen=1000)
        self.rewards: Dict[str, TeamReward] = {}
        
        self.contribution_calculator = ContributionCalculator()
        
        self.agent_teams: Dict[str, List[str]] = defaultdict(list)
        self.agent_partners: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        
        self._lock = threading.RLock()
        
        self.stats = {
            "teams_formed": 0,
            "teams_completed": 0,
            "teams_failed": 0,
            "total_rewards_distributed": 0.0,
            "avg_team_size": 0.0,
            "avg_team_success_rate": 0.0,
            "stable_partnerships": 0,
        }
    
    async def form_team(
        self,
        task_id: str,
        required_skills: List[str],
        available_agents: List[Any],
        strategy: TeamFormationStrategy = TeamFormationStrategy.SKILL_BASED,
        max_team_size: int = 5,
    ) -> Optional[str]:
        if not available_agents:
            return None
        
        team_id = f"team_{uuid.uuid4().hex[:8]}"
        
        if strategy == TeamFormationStrategy.SKILL_BASED:
            selected = self._select_by_skills(required_skills, available_agents, max_team_size)
        elif strategy == TeamFormationStrategy.PERFORMANCE_BASED:
            selected = self._select_by_performance(available_agents, max_team_size)
        elif strategy == TeamFormationStrategy.REPUTATION_BASED:
            selected = self._select_by_reputation(available_agents, max_team_size)
        elif strategy == TeamFormationStrategy.DIVERSITY_BASED:
            selected = self._select_by_diversity(available_agents, max_team_size)
        else:
            selected = available_agents[:max_team_size]
        
        if not selected:
            return None
        
        team = {
            "team_id": team_id,
            "task_id": task_id,
            "members": [a.agent_id for a in selected],
            "leader_id": selected[0].agent_id,
            "required_skills": required_skills,
            "strategy": strategy.value,
            "formed_at": time.time(),
            "status": "active",
            "performance": {},
        }
        
        with self._lock:
            self.teams[team_id] = team
            
            for agent in selected:
                self.agent_teams[agent.agent_id].append(team_id)
                
                for other in selected:
                    if other.agent_id != agent.agent_id:
                        self.agent_partners[agent.agent_id][other.agent_id] += 1
            
            self.stats["teams_formed"] += 1
            
            old_avg = self.stats["avg_team_size"]
            count = self.stats["teams_formed"]
            self.stats["avg_team_size"] = (
                old_avg * (count - 1) + len(selected)
            ) / count
        
        if self.collaboration_protocol:
            await self.collaboration_protocol.form_team(
                leader_id=team["leader_id"],
                member_ids=[m for m in team["members"] if m != team["leader_id"]],
                task_id=task_id,
            )
        
        logger.info(f"Team formed: {team_id} with {len(selected)} members")
        
        return team_id
    
    def _select_by_skills(
        self,
        required_skills: List[str],
        agents: List[Any],
        max_size: int,
    ) -> List[Any]:
        scored_agents = []
        
        for agent in agents:
            capabilities = getattr(agent, 'capabilities', []) or []
            skill_match = len(set(capabilities) & set(required_skills))
            scored_agents.append((agent, skill_match))
        
        scored_agents.sort(key=lambda x: x[1], reverse=True)
        
        selected = []
        covered_skills = set()
        
        for agent, score in scored_agents:
            if len(selected) >= max_size:
                break
            
            capabilities = set(getattr(agent, 'capabilities', []) or [])
            new_skills = capabilities & set(required_skills) - covered_skills
            
            if new_skills or len(selected) < len(required_skills):
                selected.append(agent)
                covered_skills |= capabilities & set(required_skills)
        
        return selected
    
    def _select_by_performance(
        self,
        agents: List[Any],
        max_size: int,
    ) -> List[Any]:
        scored_agents = []
        
        for agent in agents:
            success_rate = agent.stats.get("tasks_success_rate", 0.5)
            satisfaction = agent.stats.get("user_satisfaction", 0.5)
            
            score = success_rate * 0.6 + satisfaction * 0.4
            scored_agents.append((agent, score))
        
        scored_agents.sort(key=lambda x: x[1], reverse=True)
        
        return [a for a, _ in scored_agents[:max_size]]
    
    def _select_by_reputation(
        self,
        agents: List[Any],
        max_size: int,
    ) -> List[Any]:
        scored_agents = []
        
        for agent in agents:
            reputation = getattr(agent, 'reputation', 50)
            win_rate = self._get_collaboration_win_rate(agent.agent_id)
            
            score = reputation / 100 * 0.5 + win_rate * 0.5
            scored_agents.append((agent, score))
        
        scored_agents.sort(key=lambda x: x[1], reverse=True)
        
        return [a for a, _ in scored_agents[:max_size]]
    
    def _select_by_diversity(
        self,
        agents: List[Any],
        max_size: int,
    ) -> List[Any]:
        if not agents:
            return []
        
        selected = [agents[0]]
        
        while len(selected) < max_size and len(selected) < len(agents):
            best_agent = None
            best_diversity = -1
            
            for agent in agents:
                if agent in selected:
                    continue
                
                diversity = self._calculate_diversity(agent, selected)
                
                if diversity > best_diversity:
                    best_diversity = diversity
                    best_agent = agent
            
            if best_agent:
                selected.append(best_agent)
            else:
                break
        
        return selected
    
    def _calculate_diversity(self, agent: Any, team: List[Any]) -> float:
        if not team:
            return 1.0
        
        total_diff = 0.0
        
        for member in team:
            agent_caps = set(getattr(agent, 'capabilities', []) or [])
            member_caps = set(getattr(member, 'capabilities', []) or [])
            
            if agent_caps or member_caps:
                jaccard = len(agent_caps & member_caps) / len(agent_caps | member_caps)
                total_diff += 1 - jaccard
            else:
                total_diff += 0.5
        
        return total_diff / len(team)
    
    def _get_collaboration_win_rate(self, agent_id: str) -> float:
        partners = self.agent_partners.get(agent_id, {})
        if not partners:
            return 0.5
        
        total = sum(partners.values())
        if total == 0:
            return 0.5
        
        return min(1.0, total / 10)
    
    async def distribute_reward(
        self,
        team_id: str,
        total_reward: float,
        task_metrics: Optional[Dict] = None,
        method: str = "shapley",
    ) -> Optional[TeamReward]:
        if team_id not in self.teams:
            return None
        
        team = self.teams[team_id]
        members = team["members"]
        
        if method == "shapley":
            contributions = self.contribution_calculator.calculate_shapley_values(
                members, task_metrics or {}
            )
        elif method == "simple":
            contributions = self.contribution_calculator.calculate_simple_ratio(
                members, task_metrics or {}
            )
        else:
            contributions = {m: 1.0 / len(members) for m in members}
        
        allocations = {
            member: total_reward * contribution
            for member, contribution in contributions.items()
        }
        
        reward = TeamReward(
            team_id=team_id,
            task_id=team["task_id"],
            total_reward=total_reward,
            contributions=contributions,
            allocations=allocations,
            allocation_method=method,
            created_at=time.time(),
        )
        
        with self._lock:
            self.rewards[f"{team_id}_{time.time()}"] = reward
            
            for member, allocation in allocations.items():
                self.contribution_calculator.record_contribution(member, allocation)
            
            self.stats["total_rewards_distributed"] += total_reward
        
        logger.info(f"Reward distributed for team {team_id}: {total_reward}")
        
        return reward
    
    async def complete_team(
        self,
        team_id: str,
        success: bool,
        performance: Optional[Dict] = None,
    ):
        if team_id not in self.teams:
            return
        
        with self._lock:
            team = self.teams[team_id]
            team["status"] = "completed" if success else "failed"
            team["performance"] = performance or {}
            team["completed_at"] = time.time()
            
            self.team_history.append(team.copy())
            
            if success:
                self.stats["teams_completed"] += 1
                
                self._update_partner_success(team["members"])
            else:
                self.stats["teams_failed"] += 1
            
            total = self.stats["teams_completed"] + self.stats["teams_failed"]
            if total > 0:
                self.stats["avg_team_success_rate"] = (
                    self.stats["teams_completed"] / total
                )
            
            del self.teams[team_id]
        
        if self.collaboration_protocol:
            await self.collaboration_protocol.dissolve_team(team_id)
        
        logger.info(f"Team {team_id} {'completed' if success else 'failed'}")
    
    def _update_partner_success(self, members: List[str]):
        for i, member1 in enumerate(members):
            for member2 in members[i+1:]:
                if self.agent_partners[member1].get(member2, 0) >= 3:
                    self.stats["stable_partnerships"] += 1
    
    def get_team(self, team_id: str) -> Optional[Dict]:
        return self.teams.get(team_id)
    
    def get_agent_teams(self, agent_id: str) -> List[str]:
        return self.agent_teams.get(agent_id, [])
    
    def get_agent_partners(self, agent_id: str) -> Dict[str, int]:
        return dict(self.agent_partners.get(agent_id, {}))
    
    def get_best_partners(self, agent_id: str, limit: int = 3) -> List[Tuple[str, int]]:
        partners = self.agent_partners.get(agent_id, {})
        sorted_partners = sorted(partners.items(), key=lambda x: x[1], reverse=True)
        return sorted_partners[:limit]
    
    def get_stats(self) -> Dict:
        with self._lock:
            return {
                **self.stats,
                "active_teams": len(self.teams),
                "total_rewards": len(self.rewards),
            }
