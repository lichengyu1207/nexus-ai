"""
分布式防御共识智能体
负责在多个防御智能体之间达成防御决策共识
"""
import asyncio
import hashlib
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class ConsensusType(Enum):
    """共识类型"""
    ATTACK_CONFIRMATION = "attack_confirmation"
    BLOCK_DECISION = "block_decision"
    POLICY_UPDATE = "policy_update"
    THREAT_LEVEL = "threat_level"
    DEFENSE_STRATEGY = "defense_strategy"


class ConsensusStatus(Enum):
    """共识状态"""
    PENDING = "pending"
    VOTING = "voting"
    REACHED = "reached"
    FAILED = "failed"
    TIMEOUT = "timeout"


class VoteDecision(Enum):
    """投票决策"""
    APPROVE = "approve"
    REJECT = "reject"
    ABSTAIN = "abstain"


@dataclass
class Vote:
    """投票"""
    voter_id: str
    decision: VoteDecision
    weight: float
    timestamp: datetime
    reason: str = ""
    confidence: float = 1.0


@dataclass
class ConsensusProposal:
    """共识提案"""
    proposal_id: str
    consensus_type: ConsensusType
    content: Dict[str, Any]
    proposer: str
    created_at: datetime
    timeout_seconds: int
    status: ConsensusStatus
    votes: List[Vote] = field(default_factory=list)
    required_quorum: float = 0.66
    result: Optional[Dict[str, Any]] = None


@dataclass
class ConsensusResult:
    """共识结果"""
    proposal_id: str
    status: ConsensusStatus
    approved: bool
    total_votes: int
    approve_count: int
    reject_count: int
    approve_weight: float
    reject_weight: float
    final_decision: Optional[Dict[str, Any]]
    participants: List[str]
    completed_at: datetime


class DistributedDefenseConsensusAgent:
    """分布式防御共识智能体"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.name = "DistributedDefenseConsensusAgent"
        self.config = config or {}
        self.proposals: Dict[str, ConsensusProposal] = {}
        self.agent_weights: Dict[str, float] = {}
        self.agent_accuracy: Dict[str, Dict[str, int]] = defaultdict(lambda: {"correct": 0, "total": 0})
        self.consensus_history: List[ConsensusResult] = []
        self.default_timeout = 30
        self.default_quorum = 0.66
        self.stats = {
            "total_proposals": 0,
            "consensus_reached": 0,
            "consensus_failed": 0,
            "total_votes": 0,
            "avg_decision_time": 0,
        }
    
    async def initialize(self) -> bool:
        """初始化智能体"""
        await asyncio.sleep(0.1)
        return True
    
    def register_agent(self, agent_id: str, initial_weight: float = 1.0):
        """注册智能体"""
        self.agent_weights[agent_id] = initial_weight
        self.agent_accuracy[agent_id] = {"correct": 0, "total": 0}
    
    def unregister_agent(self, agent_id: str):
        """注销智能体"""
        if agent_id in self.agent_weights:
            del self.agent_weights[agent_id]
        if agent_id in self.agent_accuracy:
            del self.agent_accuracy[agent_id]
    
    def update_agent_weight(self, agent_id: str, is_correct: bool):
        """更新智能体权重"""
        if agent_id not in self.agent_accuracy:
            return
        
        self.agent_accuracy[agent_id]["total"] += 1
        if is_correct:
            self.agent_accuracy[agent_id]["correct"] += 1
        
        accuracy = self.agent_accuracy[agent_id]["correct"] / max(1, self.agent_accuracy[agent_id]["total"])
        
        self.agent_weights[agent_id] = 0.5 + accuracy * 0.5
    
    def create_proposal(
        self,
        consensus_type: ConsensusType,
        content: Dict[str, Any],
        proposer: str,
        timeout_seconds: Optional[int] = None,
        required_quorum: Optional[float] = None
    ) -> ConsensusProposal:
        """创建提案"""
        content_hash = hashlib.md5(str(content).encode()).hexdigest()[:8]
        proposal_id = f"prop_{consensus_type.value}_{content_hash}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        proposal = ConsensusProposal(
            proposal_id=proposal_id,
            consensus_type=consensus_type,
            content=content,
            proposer=proposer,
            created_at=datetime.now(),
            timeout_seconds=timeout_seconds or self.default_timeout,
            status=ConsensusStatus.PENDING,
            required_quorum=required_quorum or self.default_quorum
        )
        
        self.proposals[proposal_id] = proposal
        self.stats["total_proposals"] += 1
        
        return proposal
    
    def cast_vote(
        self,
        proposal_id: str,
        voter_id: str,
        decision: VoteDecision,
        reason: str = "",
        confidence: float = 1.0
    ) -> bool:
        """投票"""
        proposal = self.proposals.get(proposal_id)
        if not proposal:
            return False
        
        if proposal.status != ConsensusStatus.PENDING and proposal.status != ConsensusStatus.VOTING:
            return False
        
        if (datetime.now() - proposal.created_at).total_seconds() > proposal.timeout_seconds:
            proposal.status = ConsensusStatus.TIMEOUT
            return False
        
        weight = self.agent_weights.get(voter_id, 1.0)
        
        for existing_vote in proposal.votes:
            if existing_vote.voter_id == voter_id:
                existing_vote.decision = decision
                existing_vote.weight = weight
                existing_vote.reason = reason
                existing_vote.confidence = confidence
                existing_vote.timestamp = datetime.now()
                return True
        
        vote = Vote(
            voter_id=voter_id,
            decision=decision,
            weight=weight * confidence,
            timestamp=datetime.now(),
            reason=reason,
            confidence=confidence
        )
        
        proposal.votes.append(vote)
        proposal.status = ConsensusStatus.VOTING
        self.stats["total_votes"] += 1
        
        return True
    
    def check_consensus(self, proposal_id: str) -> ConsensusResult:
        """检查共识"""
        proposal = self.proposals.get(proposal_id)
        if not proposal:
            return self._create_failed_result(proposal_id, "Proposal not found")
        
        if proposal.status == ConsensusStatus.REACHED:
            return self._create_result_from_proposal(proposal)
        
        if (datetime.now() - proposal.created_at).total_seconds() > proposal.timeout_seconds:
            proposal.status = ConsensusStatus.TIMEOUT
            self.stats["consensus_failed"] += 1
            return self._create_failed_result(proposal_id, "Timeout")
        
        total_weight = sum(v.weight for v in proposal.votes)
        approve_weight = sum(v.weight for v in proposal.votes if v.decision == VoteDecision.APPROVE)
        reject_weight = sum(v.weight for v in proposal.votes if v.decision == VoteDecision.REJECT)
        
        total_agents = len(self.agent_weights)
        voted_agents = len(proposal.votes)
        
        if voted_agents < total_agents * 0.5:
            return self._create_pending_result(proposal)
        
        if total_weight > 0:
            approve_ratio = approve_weight / total_weight
            
            if approve_ratio >= proposal.required_quorum:
                proposal.status = ConsensusStatus.REACHED
                proposal.result = {
                    "approved": True,
                    "approve_ratio": approve_ratio,
                    "decision": proposal.content
                }
                self.stats["consensus_reached"] += 1
                return self._create_result_from_proposal(proposal)
            
            reject_ratio = reject_weight / total_weight
            if reject_ratio > (1 - proposal.required_quorum):
                proposal.status = ConsensusStatus.REACHED
                proposal.result = {
                    "approved": False,
                    "reject_ratio": reject_ratio,
                    "decision": None
                }
                self.stats["consensus_reached"] += 1
                return self._create_result_from_proposal(proposal)
        
        return self._create_pending_result(proposal)
    
    def _create_result_from_proposal(self, proposal: ConsensusProposal) -> ConsensusResult:
        """从提案创建结果"""
        approve_count = sum(1 for v in proposal.votes if v.decision == VoteDecision.APPROVE)
        reject_count = sum(1 for v in proposal.votes if v.decision == VoteDecision.REJECT)
        approve_weight = sum(v.weight for v in proposal.votes if v.decision == VoteDecision.APPROVE)
        reject_weight = sum(v.weight for v in proposal.votes if v.decision == VoteDecision.REJECT)
        
        approved = proposal.result.get("approved", False) if proposal.result else False
        
        result = ConsensusResult(
            proposal_id=proposal.proposal_id,
            status=proposal.status,
            approved=approved,
            total_votes=len(proposal.votes),
            approve_count=approve_count,
            reject_count=reject_count,
            approve_weight=approve_weight,
            reject_weight=reject_weight,
            final_decision=proposal.result,
            participants=[v.voter_id for v in proposal.votes],
            completed_at=datetime.now()
        )
        
        self.consensus_history.append(result)
        
        return result
    
    def _create_pending_result(self, proposal: ConsensusProposal) -> ConsensusResult:
        """创建待定结果"""
        return ConsensusResult(
            proposal_id=proposal.proposal_id,
            status=ConsensusStatus.VOTING,
            approved=False,
            total_votes=len(proposal.votes),
            approve_count=sum(1 for v in proposal.votes if v.decision == VoteDecision.APPROVE),
            reject_count=sum(1 for v in proposal.votes if v.decision == VoteDecision.REJECT),
            approve_weight=sum(v.weight for v in proposal.votes if v.decision == VoteDecision.APPROVE),
            reject_weight=sum(v.weight for v in proposal.votes if v.decision == VoteDecision.REJECT),
            final_decision=None,
            participants=[v.voter_id for v in proposal.votes],
            completed_at=datetime.now()
        )
    
    def _create_failed_result(self, proposal_id: str, reason: str) -> ConsensusResult:
        """创建失败结果"""
        return ConsensusResult(
            proposal_id=proposal_id,
            status=ConsensusStatus.FAILED,
            approved=False,
            total_votes=0,
            approve_count=0,
            reject_count=0,
            approve_weight=0,
            reject_weight=0,
            final_decision={"error": reason},
            participants=[],
            completed_at=datetime.now()
        )
    
    def execute_consensus_decision(
        self,
        proposal_id: str,
        execution_callback: callable = None
    ) -> Dict[str, Any]:
        """执行共识决策"""
        result = self.check_consensus(proposal_id)
        
        if result.status != ConsensusStatus.REACHED:
            return {
                "executed": False,
                "reason": f"Consensus not reached: {result.status.value}"
            }
        
        if execution_callback and result.approved:
            try:
                execution_result = execution_callback(result.final_decision)
                return {
                    "executed": True,
                    "result": execution_result
                }
            except Exception as e:
                return {
                    "executed": False,
                    "reason": f"Execution failed: {str(e)}"
                }
        
        return {
            "executed": result.approved,
            "decision": result.final_decision
        }
    
    def get_proposal(self, proposal_id: str) -> Optional[ConsensusProposal]:
        """获取提案"""
        return self.proposals.get(proposal_id)
    
    def get_active_proposals(self) -> List[ConsensusProposal]:
        """获取活跃提案"""
        return [
            p for p in self.proposals.values()
            if p.status in [ConsensusStatus.PENDING, ConsensusStatus.VOTING]
        ]
    
    def get_consensus_history(self, limit: int = 50) -> List[ConsensusResult]:
        """获取共识历史"""
        return self.consensus_history[-limit:]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_time = sum(
            (r.completed_at - self.proposals[r.proposal_id].created_at).total_seconds()
            for r in self.consensus_history
            if r.proposal_id in self.proposals
        )
        
        return {
            **self.stats,
            "registered_agents": len(self.agent_weights),
            "active_proposals": len(self.get_active_proposals()),
            "avg_decision_time": total_time / max(1, len(self.consensus_history)),
        }
