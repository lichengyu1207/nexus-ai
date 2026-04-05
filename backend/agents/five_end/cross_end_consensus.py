"""
跨端共识投票机制
Cross-End Consensus Voting Mechanism

实现基于PBFT简化版的跨端共识系统
"""

import asyncio
import json
import uuid
import time
import hashlib
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class ProposalType(Enum):
    PUBLISH_WARNING = "PUBLISH_WARNING"
    UPDATE_STANDARD = "UPDATE_STANDARD"
    BAN_USER = "BAN_USER"
    POLICY_CHANGE = "POLICY_CHANGE"
    SYSTEM_CONFIG = "SYSTEM_CONFIG"
    CROSS_END_ACTION = "CROSS_END_ACTION"
    EMERGENCY_RESPONSE = "EMERGENCY_RESPONSE"


class VoteChoice(Enum):
    AGREE = "agree"
    DISAGREE = "disagree"
    ABSTAIN = "abstain"


class ProposalStatus(Enum):
    PENDING = "pending"
    VOTING = "voting"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    EXECUTED = "executed"


class ConsensusResult(Enum):
    CONSENSUS_REACHED = "consensus_reached"
    CONSENSUS_FAILED = "consensus_failed"
    TIMEOUT = "timeout"
    INSUFFICIENT_VOTERS = "insufficient_voters"


END_WEIGHTS = {
    "gov": 3.0,
    "enterprise": 1.5,
    "edu": 1.0,
    "std": 2.0,
    "public": 1.0,
}

VOTING_AGENTS = {
    "gov": "gov_warning_agent",
    "enterprise": "enterprise_risk_agent",
    "edu": "edu_assessment_agent",
    "std": "std_compliance_agent",
    "public": "public_community_agent",
}


@dataclass
class VotingRecord:
    vote_id: str
    proposal_id: str
    voter_end: str
    voter_agent: str
    choice: VoteChoice
    weight: float
    reason: str = ""
    timestamp: float = field(default_factory=time.time)
    signature: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "vote_id": self.vote_id,
            "proposal_id": self.proposal_id,
            "voter_end": self.voter_end,
            "voter_agent": self.voter_agent,
            "choice": self.choice.value,
            "weight": self.weight,
            "reason": self.reason,
            "timestamp": self.timestamp,
            "signature": self.signature,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VotingRecord":
        return cls(
            vote_id=data["vote_id"],
            proposal_id=data["proposal_id"],
            voter_end=data["voter_end"],
            voter_agent=data["voter_agent"],
            choice=VoteChoice(data["choice"]),
            weight=data["weight"],
            reason=data.get("reason", ""),
            timestamp=data.get("timestamp", time.time()),
            signature=data.get("signature", ""),
        )


@dataclass
class ConsensusProposal:
    proposal_id: str
    proposal_type: ProposalType
    title: str
    description: str
    content: Dict[str, Any]
    proposer_end: str
    proposer_agent: str
    status: ProposalStatus = ProposalStatus.PENDING
    created_at: float = field(default_factory=time.time)
    voting_deadline: float = 0
    required_quorum: float = 0.67
    min_voters: int = 3
    votes: List[VotingRecord] = field(default_factory=list)
    result: Optional[ConsensusResult] = None
    result_details: Dict[str, Any] = field(default_factory=dict)
    execution_time: Optional[float] = None
    tags: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if self.voting_deadline == 0:
            self.voting_deadline = self.created_at + 300
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "proposal_type": self.proposal_type.value,
            "title": self.title,
            "description": self.description,
            "content": self.content,
            "proposer_end": self.proposer_end,
            "proposer_agent": self.proposer_agent,
            "status": self.status.value,
            "created_at": self.created_at,
            "voting_deadline": self.voting_deadline,
            "required_quorum": self.required_quorum,
            "min_voters": self.min_voters,
            "votes": [v.to_dict() for v in self.votes],
            "result": self.result.value if self.result else None,
            "result_details": self.result_details,
            "execution_time": self.execution_time,
            "tags": self.tags,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConsensusProposal":
        return cls(
            proposal_id=data["proposal_id"],
            proposal_type=ProposalType(data["proposal_type"]),
            title=data["title"],
            description=data["description"],
            content=data["content"],
            proposer_end=data["proposer_end"],
            proposer_agent=data["proposer_agent"],
            status=ProposalStatus(data["status"]),
            created_at=data["created_at"],
            voting_deadline=data["voting_deadline"],
            required_quorum=data.get("required_quorum", 0.67),
            min_voters=data.get("min_voters", 3),
            votes=[VotingRecord.from_dict(v) for v in data.get("votes", [])],
            result=ConsensusResult(data["result"]) if data.get("result") else None,
            result_details=data.get("result_details", {}),
            execution_time=data.get("execution_time"),
            tags=data.get("tags", []),
        )
    
    def is_expired(self) -> bool:
        return time.time() > self.voting_deadline
    
    def has_voted(self, voter_end: str) -> bool:
        return any(v.voter_end == voter_end for v in self.votes)


class ConsensusExecutor:
    def __init__(self):
        self._executors: Dict[ProposalType, Callable] = {}
    
    def register_executor(self, proposal_type: ProposalType, executor: Callable) -> None:
        self._executors[proposal_type] = executor
    
    async def execute(self, proposal: ConsensusProposal) -> bool:
        executor = self._executors.get(proposal.proposal_type)
        if not executor:
            logger.warning(f"No executor registered for {proposal.proposal_type}")
            return False
        
        try:
            if asyncio.iscoroutinefunction(executor):
                result = await executor(proposal)
            else:
                result = executor(proposal)
            
            logger.info(f"Proposal {proposal.proposal_id} executed: {result}")
            return True
        except Exception as e:
            logger.error(f"Failed to execute proposal {proposal.proposal_id}: {e}")
            return False


class CrossEndConsensus:
    DEFAULT_VOTING_DURATION = 300
    DEFAULT_QUORUM = 0.67
    DEFAULT_MIN_VOTERS = 3
    
    def __init__(self, message_bus: Optional[Any] = None, 
                 blackboard: Optional[Any] = None,
                 hippocampus: Optional[Any] = None):
        self.message_bus = message_bus
        self.blackboard = blackboard
        self.hippocampus = hippocampus
        
        self._proposals: Dict[str, ConsensusProposal] = {}
        self._pending_proposals: Set[str] = set()
        self._completed_proposals: Set[str] = set()
        
        self.executor = ConsensusExecutor()
        self._event_handlers: Dict[str, List[Callable]] = defaultdict(list)
        
        self._lock = asyncio.Lock()
        self._running = False
        self._tasks: List[asyncio.Task] = []
        
        self._proposal_chain: List[str] = []
        self._last_hash = "0" * 64
    
    async def start(self) -> None:
        self._running = True
        self._tasks.append(asyncio.create_task(self._monitor_proposals()))
        self._tasks.append(asyncio.create_task(self._cleanup_expired()))
        logger.info("CrossEndConsensus started")
    
    async def stop(self) -> None:
        self._running = False
        for task in self._tasks:
            task.cancel()
        self._tasks.clear()
        logger.info("CrossEndConsensus stopped")
    
    def register_executor(self, proposal_type: ProposalType, executor: Callable) -> None:
        self.executor.register_executor(proposal_type, executor)
    
    def on_event(self, event_type: str, handler: Callable) -> None:
        self._event_handlers[event_type].append(handler)
    
    async def create_proposal(self, proposal_type: ProposalType, title: str,
                               description: str, content: Dict[str, Any],
                               proposer_end: str, proposer_agent: str,
                               voting_duration: int = None,
                               required_quorum: float = None,
                               min_voters: int = None,
                               tags: List[str] = None) -> str:
        async with self._lock:
            proposal_id = str(uuid.uuid4())
            
            proposal = ConsensusProposal(
                proposal_id=proposal_id,
                proposal_type=proposal_type,
                title=title,
                description=description,
                content=content,
                proposer_end=proposer_end,
                proposer_agent=proposer_agent,
                voting_deadline=time.time() + (voting_duration or self.DEFAULT_VOTING_DURATION),
                required_quorum=required_quorum or self.DEFAULT_QUORUM,
                min_voters=min_voters or self.DEFAULT_MIN_VOTERS,
                tags=tags or [],
            )
            
            self._proposals[proposal_id] = proposal
            self._pending_proposals.add(proposal_id)
            
            proposal_hash = self._compute_proposal_hash(proposal)
            self._proposal_chain.append(proposal_hash)
            self._last_hash = proposal_hash
            
            if self.hippocampus:
                await self._record_to_hippocampus(proposal, "created")
            
            if self.message_bus:
                await self._broadcast_proposal(proposal)
            
            await self._emit_event("proposal_created", proposal)
            
            logger.info(f"Proposal {proposal_id} created by {proposer_agent}")
            return proposal_id
    
    async def vote(self, proposal_id: str, voter_end: str, voter_agent: str,
                   choice: VoteChoice, reason: str = "") -> bool:
        async with self._lock:
            proposal = self._proposals.get(proposal_id)
            if not proposal:
                logger.error(f"Proposal {proposal_id} not found")
                return False
            
            if proposal.status != ProposalStatus.PENDING and proposal.status != ProposalStatus.VOTING:
                logger.error(f"Proposal {proposal_id} is not in voting state")
                return False
            
            if proposal.is_expired():
                proposal.status = ProposalStatus.EXPIRED
                return False
            
            if proposal.has_voted(voter_end):
                logger.warning(f"End {voter_end} has already voted on {proposal_id}")
                return False
            
            weight = END_WEIGHTS.get(voter_end, 1.0)
            
            vote = VotingRecord(
                vote_id=str(uuid.uuid4()),
                proposal_id=proposal_id,
                voter_end=voter_end,
                voter_agent=voter_agent,
                choice=choice,
                weight=weight,
                reason=reason,
                signature=self._sign_vote(voter_end, proposal_id, choice),
            )
            
            proposal.votes.append(vote)
            proposal.status = ProposalStatus.VOTING
            
            if self.hippocampus:
                await self._record_vote_to_hippocampus(vote)
            
            if self.message_bus:
                await self._broadcast_vote(vote)
            
            result = await self._check_consensus(proposal)
            
            if result:
                await self._finalize_proposal(proposal, result)
            
            return True
    
    async def _check_consensus(self, proposal: ConsensusProposal) -> Optional[ConsensusResult]:
        if len(proposal.votes) < proposal.min_voters:
            return None
        
        total_weight = sum(v.weight for v in proposal.votes)
        agree_weight = sum(v.weight for v in proposal.votes if v.choice == VoteChoice.AGREE)
        disagree_weight = sum(v.weight for v in proposal.votes if v.choice == VoteChoice.DISAGREE)
        
        all_ends = set(END_WEIGHTS.keys())
        voted_ends = set(v.voter_end for v in proposal.votes)
        
        if len(voted_ends) < proposal.min_voters:
            return None
        
        agree_ratio = agree_weight / total_weight if total_weight > 0 else 0
        
        if agree_ratio >= proposal.required_quorum:
            proposal.result_details = {
                "total_weight": total_weight,
                "agree_weight": agree_weight,
                "disagree_weight": disagree_weight,
                "agree_ratio": agree_ratio,
                "voted_ends": list(voted_ends),
            }
            return ConsensusResult.CONSENSUS_REACHED
        
        disagree_ratio = disagree_weight / total_weight if total_weight > 0 else 0
        if disagree_ratio > (1 - proposal.required_quorum):
            proposal.result_details = {
                "total_weight": total_weight,
                "agree_weight": agree_weight,
                "disagree_weight": disagree_weight,
                "disagree_ratio": disagree_ratio,
                "voted_ends": list(voted_ends),
            }
            return ConsensusResult.CONSENSUS_FAILED
        
        return None
    
    async def _finalize_proposal(self, proposal: ConsensusProposal, result: ConsensusResult) -> None:
        proposal.result = result
        
        if result == ConsensusResult.CONSENSUS_REACHED:
            proposal.status = ProposalStatus.APPROVED
            await self._execute_proposal(proposal)
        elif result == ConsensusResult.CONSENSUS_FAILED:
            proposal.status = ProposalStatus.REJECTED
        elif result == ConsensusResult.TIMEOUT:
            proposal.status = ProposalStatus.EXPIRED
        
        self._pending_proposals.discard(proposal.proposal_id)
        self._completed_proposals.add(proposal.proposal_id)
        
        if self.hippocampus:
            await self._record_to_hippocampus(proposal, "finalized")
        
        await self._emit_event("proposal_finalized", proposal)
        
        logger.info(f"Proposal {proposal.proposal_id} finalized with result: {result.value}")
    
    async def _execute_proposal(self, proposal: ConsensusProposal) -> bool:
        success = await self.executor.execute(proposal)
        
        if success:
            proposal.status = ProposalStatus.EXECUTED
            proposal.execution_time = time.time()
            
            if self.hippocampus:
                await self._record_to_hippocampus(proposal, "executed")
            
            await self._emit_event("proposal_executed", proposal)
        
        return success
    
    async def _monitor_proposals(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(10)
                
                async with self._lock:
                    for proposal_id in list(self._pending_proposals):
                        proposal = self._proposals.get(proposal_id)
                        if not proposal:
                            continue
                        
                        if proposal.is_expired():
                            result = await self._check_consensus(proposal)
                            if not result:
                                result = ConsensusResult.TIMEOUT
                            await self._finalize_proposal(proposal, result)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error monitoring proposals: {e}")
    
    async def _cleanup_expired(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(3600)
            except asyncio.CancelledError:
                break
    
    async def _broadcast_proposal(self, proposal: ConsensusProposal) -> None:
        if not self.message_bus:
            return
        
        from .five_end_bus import EventType, CrossEndEvent, EndType, MessagePriority
        
        event = CrossEndEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.CONSENSUS_PROPOSAL,
            source_end=EndType(proposal.proposer_end),
            source_agent=proposal.proposer_agent,
            broadcast=True,
            payload=proposal.to_dict(),
            priority=MessagePriority.HIGH,
        )
        await self.message_bus.publish(event)
    
    async def _broadcast_vote(self, vote: VotingRecord) -> None:
        if not self.message_bus:
            return
        
        from .five_end_bus import EventType, CrossEndEvent, EndType, MessagePriority
        
        event = CrossEndEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.CONSENSUS_VOTE,
            source_end=EndType(vote.voter_end),
            source_agent=vote.voter_agent,
            broadcast=True,
            payload=vote.to_dict(),
            priority=MessagePriority.NORMAL,
        )
        await self.message_bus.publish(event)
    
    async def _record_to_hippocampus(self, proposal: ConsensusProposal, action: str) -> None:
        if not self.hippocampus:
            return
        
        try:
            record = {
                "proposal_id": proposal.proposal_id,
                "action": action,
                "proposal_type": proposal.proposal_type.value,
                "status": proposal.status.value,
                "result": proposal.result.value if proposal.result else None,
                "timestamp": time.time(),
            }
            await self.hippocampus.store_memory(
                content=json.dumps(record),
                memory_type="consensus",
                source_end=proposal.proposer_end,
                tags=["consensus", action],
            )
        except Exception as e:
            logger.error(f"Failed to record to hippocampus: {e}")
    
    async def _record_vote_to_hippocampus(self, vote: VotingRecord) -> None:
        if not self.hippocampus:
            return
        
        try:
            record = {
                "vote_id": vote.vote_id,
                "proposal_id": vote.proposal_id,
                "voter_end": vote.voter_end,
                "choice": vote.choice.value,
                "timestamp": vote.timestamp,
            }
            await self.hippocampus.store_memory(
                content=json.dumps(record),
                memory_type="vote",
                source_end=vote.voter_end,
                tags=["consensus", "vote"],
            )
        except Exception as e:
            logger.error(f"Failed to record vote to hippocampus: {e}")
    
    async def _emit_event(self, event_type: str, data: Any) -> None:
        handlers = self._event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(data)
                else:
                    handler(data)
            except Exception as e:
                logger.error(f"Event handler error: {e}")
    
    def _compute_proposal_hash(self, proposal: ConsensusProposal) -> str:
        data = f"{proposal.proposal_id}{proposal.proposal_type.value}{self._last_hash}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    def _sign_vote(self, voter_end: str, proposal_id: str, choice: VoteChoice) -> str:
        data = f"{voter_end}{proposal_id}{choice.value}{time.time()}"
        return hashlib.sha256(data.encode()).hexdigest()[:32]
    
    async def get_proposal(self, proposal_id: str) -> Optional[ConsensusProposal]:
        return self._proposals.get(proposal_id)
    
    async def get_pending_proposals(self) -> List[ConsensusProposal]:
        return [self._proposals[pid] for pid in self._pending_proposals if pid in self._proposals]
    
    async def get_proposals_by_status(self, status: ProposalStatus) -> List[ConsensusProposal]:
        return [p for p in self._proposals.values() if p.status == status]
    
    async def get_proposals_by_type(self, proposal_type: ProposalType) -> List[ConsensusProposal]:
        return [p for p in self._proposals.values() if p.proposal_type == proposal_type]
    
    async def get_voting_history(self, voter_end: str = None,
                                  limit: int = 100) -> List[VotingRecord]:
        votes = []
        for proposal in self._proposals.values():
            for vote in proposal.votes:
                if voter_end is None or vote.voter_end == voter_end:
                    votes.append(vote)
        
        votes.sort(key=lambda v: v.timestamp, reverse=True)
        return votes[:limit]
    
    async def get_statistics(self) -> Dict[str, Any]:
        total = len(self._proposals)
        by_status = defaultdict(int)
        by_type = defaultdict(int)
        by_result = defaultdict(int)
        
        for proposal in self._proposals.values():
            by_status[proposal.status.value] += 1
            by_type[proposal.proposal_type.value] += 1
            if proposal.result:
                by_result[proposal.result.value] += 1
        
        return {
            "total_proposals": total,
            "pending": len(self._pending_proposals),
            "completed": len(self._completed_proposals),
            "by_status": dict(by_status),
            "by_type": dict(by_type),
            "by_result": dict(by_result),
        }
    
    async def get_proposal_chain(self, count: int = 100) -> List[str]:
        return self._proposal_chain[-count:]
    
    async def retry_proposal(self, proposal_id: str, proposer_end: str,
                              proposer_agent: str) -> Optional[str]:
        original = self._proposals.get(proposal_id)
        if not original:
            return None
        
        if original.status not in [ProposalStatus.REJECTED, ProposalStatus.EXPIRED]:
            return None
        
        return await self.create_proposal(
            proposal_type=original.proposal_type,
            title=original.title,
            description=original.description,
            content=original.content,
            proposer_end=proposer_end,
            proposer_agent=proposer_agent,
            voting_duration=int(original.voting_deadline - original.created_at),
            required_quorum=original.required_quorum,
            min_voters=original.min_voters,
            tags=original.tags,
        )


class ConsensusMonitor:
    def __init__(self, consensus: CrossEndConsensus):
        self.consensus = consensus
        self._metrics_history: List[Dict[str, Any]] = []
    
    async def collect_metrics(self) -> Dict[str, Any]:
        stats = await self.consensus.get_statistics()
        
        metrics = {
            "timestamp": time.time(),
            **stats,
        }
        
        self._metrics_history.append(metrics)
        return metrics
    
    async def get_participation_rate(self) -> Dict[str, float]:
        end_participation = defaultdict(lambda: {"total": 0, "voted": 0})
        
        for proposal in self.consensus._proposals.values():
            for end in END_WEIGHTS.keys():
                end_participation[end]["total"] += 1
                if proposal.has_voted(end):
                    end_participation[end]["voted"] += 1
        
        return {
            end: data["voted"] / data["total"] if data["total"] > 0 else 0
            for end, data in end_participation.items()
        }
    
    async def get_approval_rate(self) -> float:
        stats = await self.consensus.get_statistics()
        total = stats["total_proposals"]
        if total == 0:
            return 0
        
        approved = stats["by_result"].get("consensus_reached", 0)
        return approved / total
