"""
封禁与申诉系统
Ban and Appeal System

实现用户恶意行为检测、封禁管理和申诉处理
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


class BanType(Enum):
    ACCOUNT = "account"
    IP = "ip"
    DEVICE = "device"
    SESSION = "session"
    COMBINED = "combined"


class BanReason(Enum):
    HIGH_RISK_SCORE = "high_risk_score"
    MALICIOUS_INPUT = "malicious_input"
    PROMPT_INJECTION = "prompt_injection"
    DATA_SCRAPING = "data_scraping"
    SPAM = "spam"
    FRAUD = "fraud"
    ABUSE = "abuse"
    POLICY_VIOLATION = "policy_violation"
    REPEATED_VIOLATIONS = "repeated_violations"
    CROSS_END_ATTACK = "cross_end_attack"
    MANUAL = "manual"


class BanStatus(Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    APPEALED = "appealed"


class AppealStatus(Enum):
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"


class RiskFactor(Enum):
    INPUT_INJECTION = "input_injection"
    RAPID_REQUESTS = "rapid_requests"
    SUSPICIOUS_PATTERN = "suspicious_pattern"
    DATA_EXFILTRATION = "data_exfiltration"
    BEHAVIOR_ANOMALY = "behavior_anomaly"
    CROSS_END_ABUSE = "cross_end_abuse"


@dataclass
class BanRule:
    rule_id: str
    name: str
    description: str
    trigger_condition: Dict[str, Any]
    ban_type: BanType
    duration_seconds: int
    is_permanent: bool = False
    risk_threshold: int = 60
    priority: int = 5
    is_active: bool = True
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "description": self.description,
            "trigger_condition": self.trigger_condition,
            "ban_type": self.ban_type.value,
            "duration_seconds": self.duration_seconds,
            "is_permanent": self.is_permanent,
            "risk_threshold": self.risk_threshold,
            "priority": self.priority,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BanRule":
        return cls(
            rule_id=data["rule_id"],
            name=data["name"],
            description=data["description"],
            trigger_condition=data["trigger_condition"],
            ban_type=BanType(data["ban_type"]),
            duration_seconds=data["duration_seconds"],
            is_permanent=data.get("is_permanent", False),
            risk_threshold=data.get("risk_threshold", 60),
            priority=data.get("priority", 5),
            is_active=data.get("is_active", True),
            created_at=data.get("created_at", time.time()),
            updated_at=data.get("updated_at", time.time()),
        )


@dataclass
class BanRecord:
    ban_id: str
    ban_type: BanType
    target_value: str
    reason: BanReason
    rule_id: Optional[str]
    risk_score: int
    status: BanStatus = BanStatus.ACTIVE
    start_time: float = field(default_factory=time.time)
    end_time: float = 0
    is_permanent: bool = False
    source_end: str = ""
    source_agent: str = ""
    admin_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    revoked_at: Optional[float] = None
    revoke_reason: str = ""
    
    def __post_init__(self):
        if self.end_time == 0 and not self.is_permanent:
            self.end_time = self.start_time + 86400
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "ban_id": self.ban_id,
            "ban_type": self.ban_type.value,
            "target_value": self.target_value,
            "reason": self.reason.value,
            "rule_id": self.rule_id,
            "risk_score": self.risk_score,
            "status": self.status.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "is_permanent": self.is_permanent,
            "source_end": self.source_end,
            "source_agent": self.source_agent,
            "admin_id": self.admin_id,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "revoked_at": self.revoked_at,
            "revoke_reason": self.revoke_reason,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BanRecord":
        return cls(
            ban_id=data["ban_id"],
            ban_type=BanType(data["ban_type"]),
            target_value=data["target_value"],
            reason=BanReason(data["reason"]),
            rule_id=data.get("rule_id"),
            risk_score=data.get("risk_score", 0),
            status=BanStatus(data.get("status", "active")),
            start_time=data.get("start_time", time.time()),
            end_time=data.get("end_time", 0),
            is_permanent=data.get("is_permanent", False),
            source_end=data.get("source_end", ""),
            source_agent=data.get("source_agent", ""),
            admin_id=data.get("admin_id"),
            metadata=data.get("metadata", {}),
            created_at=data.get("created_at", time.time()),
            revoked_at=data.get("revoked_at"),
            revoke_reason=data.get("revoke_reason", ""),
        )
    
    def is_active(self) -> bool:
        if self.status != BanStatus.ACTIVE:
            return False
        if self.is_permanent:
            return True
        return time.time() < self.end_time
    
    def compute_hash(self) -> str:
        data = f"{self.ban_id}{self.target_value}{self.start_time}{self.reason.value}"
        return hashlib.sha256(data.encode()).hexdigest()


@dataclass
class AppealRecord:
    appeal_id: str
    ban_id: str
    user_id: str
    contact_info: str
    appeal_reason: str
    status: AppealStatus = AppealStatus.PENDING
    submitted_at: float = field(default_factory=time.time)
    reviewed_at: Optional[float] = None
    reviewer_id: Optional[str] = None
    review_notes: str = ""
    decision: str = ""
    evidence: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "appeal_id": self.appeal_id,
            "ban_id": self.ban_id,
            "user_id": self.user_id,
            "contact_info": self.contact_info,
            "appeal_reason": self.appeal_reason,
            "status": self.status.value,
            "submitted_at": self.submitted_at,
            "reviewed_at": self.reviewed_at,
            "reviewer_id": self.reviewer_id,
            "review_notes": self.review_notes,
            "decision": self.decision,
            "evidence": self.evidence,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AppealRecord":
        return cls(
            appeal_id=data["appeal_id"],
            ban_id=data["ban_id"],
            user_id=data["user_id"],
            contact_info=data["contact_info"],
            appeal_reason=data["appeal_reason"],
            status=AppealStatus(data.get("status", "pending")),
            submitted_at=data.get("submitted_at", time.time()),
            reviewed_at=data.get("reviewed_at"),
            reviewer_id=data.get("reviewer_id"),
            review_notes=data.get("review_notes", ""),
            decision=data.get("decision", ""),
            evidence=data.get("evidence", []),
            metadata=data.get("metadata", {}),
        )


@dataclass
class UserRiskProfile:
    user_id: str
    risk_score: int = 0
    behavior_sequence: List[Dict[str, Any]] = field(default_factory=list)
    risk_factors: Dict[str, int] = field(default_factory=dict)
    last_activity: float = field(default_factory=time.time)
    ban_count: int = 0
    appeal_count: int = 0
    trust_level: int = 50
    created_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "risk_score": self.risk_score,
            "behavior_sequence": self.behavior_sequence[-100:],
            "risk_factors": self.risk_factors,
            "last_activity": self.last_activity,
            "ban_count": self.ban_count,
            "appeal_count": self.appeal_count,
            "trust_level": self.trust_level,
            "created_at": self.created_at,
        }
    
    def add_behavior(self, behavior: Dict[str, Any]) -> None:
        self.behavior_sequence.append({
            **behavior,
            "timestamp": time.time(),
        })
        if len(self.behavior_sequence) > 100:
            self.behavior_sequence = self.behavior_sequence[-100:]
        self.last_activity = time.time()
    
    def add_risk_factor(self, factor: RiskFactor, score: int) -> None:
        self.risk_factors[factor.value] = self.risk_factors.get(factor.value, 0) + score
        self.risk_score = min(100, self.risk_score + score)
    
    def decay_risk(self, decay_rate: float = 0.1) -> None:
        self.risk_score = max(0, int(self.risk_score * (1 - decay_rate)))
        for factor in self.risk_factors:
            self.risk_factors[factor] = max(0, int(self.risk_factors[factor] * (1 - decay_rate)))


class AppealAgent:
    def __init__(self, ban_system: "BanAppealSystem"):
        self.ban_system = ban_system
        self.agent_id = f"appeal_agent_{str(uuid.uuid4())[:8]}"
        self._auto_approval_rules: List[Dict[str, Any]] = []
        self._setup_auto_approval_rules()
    
    def _setup_auto_approval_rules(self) -> None:
        self._auto_approval_rules = [
            {
                "condition": lambda appeal, profile: (
                    profile.trust_level >= 80 and
                    profile.ban_count == 0 and
                    appeal.ban_record.risk_score < 40
                ),
                "action": "auto_approve",
            },
            {
                "condition": lambda appeal, profile: (
                    profile.ban_count >= 3 or
                    appeal.ban_record.reason == BanReason.FRAUD
                ),
                "action": "auto_reject",
            },
        ]
    
    async def process_appeal(self, appeal: AppealRecord) -> Dict[str, Any]:
        ban_record = self.ban_system.get_ban(appeal.ban_id)
        if not ban_record:
            return {"action": "reject", "reason": "Ban record not found"}
        
        profile = self.ban_system.get_user_profile(appeal.user_id)
        
        for rule in self._auto_approval_rules:
            if rule["condition"](appeal, profile):
                if rule["action"] == "auto_approve":
                    return {
                        "action": "auto_approve",
                        "reason": "Auto-approved: high trust user, low risk",
                    }
                elif rule["action"] == "auto_reject":
                    return {
                        "action": "auto_reject",
                        "reason": "Auto-rejected: repeated violations or serious offense",
                    }
        
        return {
            "action": "manual_review",
            "reason": "Requires manual review",
            "priority": self._calculate_review_priority(appeal, profile),
        }
    
    def _calculate_review_priority(self, appeal: AppealRecord, 
                                    profile: UserRiskProfile) -> int:
        priority = 5
        
        if profile.trust_level >= 70:
            priority += 2
        if appeal.ban_record.is_permanent:
            priority -= 2
        if profile.ban_count > 0:
            priority -= 1
        
        return max(1, min(10, priority))
    
    async def handle_appeal(self, appeal_id: str, action: str,
                            reviewer_id: str, notes: str = "") -> bool:
        return await self.ban_system.resolve_appeal(
            appeal_id=appeal_id,
            action=action,
            reviewer_id=reviewer_id,
            notes=notes,
        )


class BanAppealSystem:
    DEFAULT_RULES = [
        {
            "name": "高风险自动封禁",
            "description": "风险分数超过阈值时自动封禁",
            "trigger_condition": {"risk_score": 60},
            "ban_type": BanType.ACCOUNT,
            "duration_seconds": 86400,
            "risk_threshold": 60,
        },
        {
            "name": "恶意输入封禁",
            "description": "检测到恶意输入时封禁",
            "trigger_condition": {"input_type": "malicious"},
            "ban_type": BanType.IP,
            "duration_seconds": 604800,
            "risk_threshold": 70,
        },
        {
            "name": "提示词注入封禁",
            "description": "检测到提示词注入攻击时封禁",
            "trigger_condition": {"attack_type": "prompt_injection"},
            "ban_type": BanType.COMBINED,
            "duration_seconds": 2592000,
            "risk_threshold": 80,
        },
    ]
    
    def __init__(self, message_bus: Optional[Any] = None,
                 hippocampus: Optional[Any] = None):
        self.message_bus = message_bus
        self.hippocampus = hippocampus
        
        self._rules: Dict[str, BanRule] = {}
        self._bans: Dict[str, BanRecord] = {}
        self._appeals: Dict[str, AppealRecord] = {}
        self._profiles: Dict[str, UserRiskProfile] = {}
        
        self._ban_index: Dict[BanType, Dict[str, Set[str]]] = {
            bt: defaultdict(set) for bt in BanType
        }
        
        self.appeal_agent = AppealAgent(self)
        
        self._lock = asyncio.Lock()
        self._running = False
        self._tasks: List[asyncio.Task] = []
        
        self._ban_chain: List[str] = []
        self._last_hash = "0" * 64
        
        self._initialize_default_rules()
    
    def _initialize_default_rules(self) -> None:
        for rule_data in self.DEFAULT_RULES:
            rule = BanRule(
                rule_id=f"rule_{str(uuid.uuid4())[:8]}",
                **rule_data,
            )
            self._rules[rule.rule_id] = rule
    
    async def start(self) -> None:
        self._running = True
        self._tasks.append(asyncio.create_task(self._cleanup_expired_bans()))
        self._tasks.append(asyncio.create_task(self._decay_risk_scores()))
        logger.info("BanAppealSystem started")
    
    async def stop(self) -> None:
        self._running = False
        for task in self._tasks:
            task.cancel()
        self._tasks.clear()
        logger.info("BanAppealSystem stopped")
    
    def get_user_profile(self, user_id: str) -> UserRiskProfile:
        if user_id not in self._profiles:
            self._profiles[user_id] = UserRiskProfile(user_id=user_id)
        return self._profiles[user_id]
    
    async def record_user_behavior(self, user_id: str, behavior: Dict[str, Any],
                                    risk_factor: RiskFactor = None,
                                    risk_increment: int = 0) -> None:
        async with self._lock:
            profile = self.get_user_profile(user_id)
            profile.add_behavior(behavior)
            
            if risk_factor and risk_increment > 0:
                profile.add_risk_factor(risk_factor, risk_increment)
                
                if profile.risk_score >= 60:
                    await self._check_auto_ban(user_id, profile)
    
    async def _check_auto_ban(self, user_id: str, profile: UserRiskProfile) -> None:
        for rule in self._rules.values():
            if not rule.is_active:
                continue
            
            if profile.risk_score >= rule.risk_threshold:
                await self.create_ban(
                    ban_type=rule.ban_type,
                    target_value=user_id,
                    reason=BanReason.HIGH_RISK_SCORE,
                    rule_id=rule.rule_id,
                    risk_score=profile.risk_score,
                    duration_seconds=rule.duration_seconds,
                    is_permanent=rule.is_permanent,
                )
                break
    
    async def create_ban(self, ban_type: BanType, target_value: str,
                          reason: BanReason, rule_id: str = None,
                          risk_score: int = 0, duration_seconds: int = 86400,
                          is_permanent: bool = False,
                          source_end: str = "system",
                          source_agent: str = "ban_system",
                          admin_id: str = None,
                          metadata: Dict[str, Any] = None) -> str:
        async with self._lock:
            ban_id = str(uuid.uuid4())
            
            ban = BanRecord(
                ban_id=ban_id,
                ban_type=ban_type,
                target_value=target_value,
                reason=reason,
                rule_id=rule_id,
                risk_score=risk_score,
                status=BanStatus.ACTIVE,
                start_time=time.time(),
                end_time=time.time() + duration_seconds if not is_permanent else 0,
                is_permanent=is_permanent,
                source_end=source_end,
                source_agent=source_agent,
                admin_id=admin_id,
                metadata=metadata or {},
            )
            
            self._bans[ban_id] = ban
            self._ban_index[ban_type][target_value].add(ban_id)
            
            ban_hash = ban.compute_hash()
            self._ban_chain.append(ban_hash)
            self._last_hash = ban_hash
            
            if target_value in self._profiles:
                self._profiles[target_value].ban_count += 1
            
            if self.hippocampus:
                await self._record_ban_in_hippocampus(ban)
            
            if self.message_bus:
                await self._broadcast_ban(ban)
            
            logger.info(f"Ban {ban_id} created for {target_value}")
            return ban_id
    
    async def revoke_ban(self, ban_id: str, revoke_reason: str,
                          admin_id: str = None) -> bool:
        async with self._lock:
            ban = self._bans.get(ban_id)
            if not ban:
                return False
            
            ban.status = BanStatus.REVOKED
            ban.revoked_at = time.time()
            ban.revoke_reason = revoke_reason
            if admin_id:
                ban.admin_id = admin_id
            
            if self.hippocampus:
                await self._record_ban_in_hippocampus(ban, action="revoked")
            
            if self.message_bus:
                await self._broadcast_unban(ban)
            
            logger.info(f"Ban {ban_id} revoked")
            return True
    
    def is_banned(self, target: str, ban_type: BanType = None) -> bool:
        if ban_type:
            ban_ids = self._ban_index[ban_type].get(target, set())
            for bid in ban_ids:
                ban = self._bans.get(bid)
                if ban and ban.is_active():
                    return True
            return False
        
        for bt in BanType:
            if self.is_banned(target, bt):
                return True
        return False
    
    def get_ban(self, ban_id: str) -> Optional[BanRecord]:
        return self._bans.get(ban_id)
    
    def get_active_bans(self, target: str = None,
                         ban_type: BanType = None) -> List[BanRecord]:
        bans = []
        
        for ban in self._bans.values():
            if not ban.is_active():
                continue
            
            if target and ban.target_value != target:
                continue
            
            if ban_type and ban.ban_type != ban_type:
                continue
            
            bans.append(ban)
        
        return bans
    
    async def submit_appeal(self, ban_id: str, user_id: str,
                             contact_info: str, appeal_reason: str,
                             evidence: List[str] = None) -> str:
        async with self._lock:
            ban = self._bans.get(ban_id)
            if not ban:
                raise ValueError(f"Ban {ban_id} not found")
            
            appeal_id = str(uuid.uuid4())
            
            appeal = AppealRecord(
                appeal_id=appeal_id,
                ban_id=ban_id,
                user_id=user_id,
                contact_info=contact_info,
                appeal_reason=appeal_reason,
                evidence=evidence or [],
            )
            
            self._appeals[appeal_id] = appeal
            ban.status = BanStatus.APPEALED
            
            if user_id in self._profiles:
                self._profiles[user_id].appeal_count += 1
            
            if self.hippocampus:
                await self._record_appeal_in_hippocampus(appeal)
            
            result = await self.appeal_agent.process_appeal(appeal)
            
            if result["action"] == "auto_approve":
                await self.resolve_appeal(appeal_id, "approve", "system", result["reason"])
            elif result["action"] == "auto_reject":
                await self.resolve_appeal(appeal_id, "reject", "system", result["reason"])
            
            logger.info(f"Appeal {appeal_id} submitted for ban {ban_id}")
            return appeal_id
    
    async def resolve_appeal(self, appeal_id: str, action: str,
                              reviewer_id: str, notes: str = "") -> bool:
        async with self._lock:
            appeal = self._appeals.get(appeal_id)
            if not appeal:
                return False
            
            appeal.reviewed_at = time.time()
            appeal.reviewer_id = reviewer_id
            appeal.review_notes = notes
            appeal.decision = action
            
            if action == "approve":
                appeal.status = AppealStatus.APPROVED
                await self.revoke_ban(appeal.ban_id, f"Appeal approved: {notes}", reviewer_id)
            elif action == "reject":
                appeal.status = AppealStatus.REJECTED
                ban = self._bans.get(appeal.ban_id)
                if ban:
                    ban.status = BanStatus.ACTIVE
            elif action == "escalate":
                appeal.status = AppealStatus.ESCALATED
            
            if self.hippocampus:
                await self._record_appeal_in_hippocampus(appeal, action="resolved")
            
            logger.info(f"Appeal {appeal_id} resolved: {action}")
            return True
    
    def get_appeal(self, appeal_id: str) -> Optional[AppealRecord]:
        return self._appeals.get(appeal_id)
    
    def get_pending_appeals(self) -> List[AppealRecord]:
        return [
            a for a in self._appeals.values()
            if a.status in [AppealStatus.PENDING, AppealStatus.UNDER_REVIEW, AppealStatus.ESCALATED]
        ]
    
    def add_rule(self, rule: BanRule) -> str:
        self._rules[rule.rule_id] = rule
        return rule.rule_id
    
    def remove_rule(self, rule_id: str) -> bool:
        if rule_id in self._rules:
            del self._rules[rule_id]
            return True
        return False
    
    def get_rules(self) -> List[BanRule]:
        return list(self._rules.values())
    
    async def _cleanup_expired_bans(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(3600)
                
                async with self._lock:
                    for ban in list(self._bans.values()):
                        if ban.status == BanStatus.ACTIVE and not ban.is_active():
                            ban.status = BanStatus.EXPIRED
                            logger.info(f"Ban {ban.ban_id} expired")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error cleaning up expired bans: {e}")
    
    async def _decay_risk_scores(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(86400)
                
                async with self._lock:
                    for profile in self._profiles.values():
                        profile.decay_risk(0.1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error decaying risk scores: {e}")
    
    async def _record_ban_in_hippocampus(self, ban: BanRecord, action: str = "created") -> None:
        if not self.hippocampus:
            return
        
        try:
            await self.hippocampus.store_memory(
                content=json.dumps(ban.to_dict()),
                memory_type="ban_record",
                source_end=ban.source_end,
                tags=["ban", action, ban.ban_type.value, ban.reason.value],
            )
        except Exception as e:
            logger.error(f"Failed to record ban in hippocampus: {e}")
    
    async def _record_appeal_in_hippocampus(self, appeal: AppealRecord, action: str = "submitted") -> None:
        if not self.hippocampus:
            return
        
        try:
            await self.hippocampus.store_memory(
                content=json.dumps(appeal.to_dict()),
                memory_type="appeal_record",
                source_end="system",
                tags=["appeal", action, appeal.status.value],
            )
        except Exception as e:
            logger.error(f"Failed to record appeal in hippocampus: {e}")
    
    async def _broadcast_ban(self, ban: BanRecord) -> None:
        if not self.message_bus:
            return
        
        try:
            from .five_end_bus import EventType, CrossEndEvent, EndType, MessagePriority
            
            event = CrossEndEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.BAN_EVENT,
                source_end=EndType(ban.source_end) if ban.source_end else EndType.GOV,
                source_agent=ban.source_agent,
                broadcast=True,
                payload=ban.to_dict(),
                priority=MessagePriority.HIGH,
            )
            await self.message_bus.publish(event)
        except Exception as e:
            logger.error(f"Failed to broadcast ban: {e}")
    
    async def _broadcast_unban(self, ban: BanRecord) -> None:
        if not self.message_bus:
            return
        
        try:
            from .five_end_bus import EventType, CrossEndEvent, EndType, MessagePriority
            
            event = CrossEndEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.UNBAN_EVENT,
                source_end=EndType.GOV,
                source_agent="ban_system",
                broadcast=True,
                payload={
                    "ban_id": ban.ban_id,
                    "target_value": ban.target_value,
                    "ban_type": ban.ban_type.value,
                    "revoke_reason": ban.revoke_reason,
                },
                priority=MessagePriority.HIGH,
            )
            await self.message_bus.publish(event)
        except Exception as e:
            logger.error(f"Failed to broadcast unban: {e}")
    
    async def get_statistics(self) -> Dict[str, Any]:
        active_bans = [b for b in self._bans.values() if b.is_active()]
        pending_appeals = self.get_pending_appeals()
        
        bans_by_type = defaultdict(int)
        for ban in active_bans:
            bans_by_type[ban.ban_type.value] += 1
        
        bans_by_reason = defaultdict(int)
        for ban in self._bans.values():
            bans_by_reason[ban.reason.value] += 1
        
        return {
            "total_bans": len(self._bans),
            "active_bans": len(active_bans),
            "total_appeals": len(self._appeals),
            "pending_appeals": len(pending_appeals),
            "total_profiles": len(self._profiles),
            "bans_by_type": dict(bans_by_type),
            "bans_by_reason": dict(bans_by_reason),
            "rules_count": len(self._rules),
        }
    
    async def get_ban_chain(self, count: int = 100) -> List[str]:
        return self._ban_chain[-count:]
    
    async def sync_ban_from_network(self, ban_data: Dict[str, Any]) -> bool:
        async with self._lock:
            try:
                ban = BanRecord.from_dict(ban_data)
                
                if ban.ban_id in self._bans:
                    return False
                
                self._bans[ban.ban_id] = ban
                self._ban_index[ban.ban_type][ban.target_value].add(ban.ban_id)
                
                logger.info(f"Ban {ban.ban_id} synced from network")
                return True
            except Exception as e:
                logger.error(f"Failed to sync ban from network: {e}")
                return False


class BanMonitor:
    def __init__(self, ban_system: BanAppealSystem):
        self.ban_system = ban_system
        self._metrics_history: List[Dict[str, Any]] = []
    
    async def collect_metrics(self) -> Dict[str, Any]:
        stats = await self.ban_system.get_statistics()
        
        metrics = {
            "timestamp": time.time(),
            **stats,
        }
        
        self._metrics_history.append(metrics)
        return metrics
    
    async def get_risk_distribution(self) -> Dict[str, int]:
        distribution = defaultdict(int)
        
        for profile in self.ban_system._profiles.values():
            if profile.risk_score < 20:
                distribution["low"] += 1
            elif profile.risk_score < 50:
                distribution["medium"] += 1
            elif profile.risk_score < 80:
                distribution["high"] += 1
            else:
                distribution["critical"] += 1
        
        return dict(distribution)
    
    async def get_appeal_success_rate(self) -> float:
        total = len(self.ban_system._appeals)
        if total == 0:
            return 0
        
        approved = sum(
            1 for a in self.ban_system._appeals.values()
            if a.status == AppealStatus.APPROVED
        )
        
        return approved / total
    
    async def get_top_risk_users(self, limit: int = 10) -> List[Dict[str, Any]]:
        profiles = sorted(
            self.ban_system._profiles.values(),
            key=lambda p: p.risk_score,
            reverse=True,
        )
        
        return [
            {
                "user_id": p.user_id,
                "risk_score": p.risk_score,
                "ban_count": p.ban_count,
                "trust_level": p.trust_level,
            }
            for p in profiles[:limit]
        ]
