"""
攻击情报共享智能体
负责在防御智能体之间共享攻击情报
"""
import asyncio
import hashlib
import json
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class IntelType(Enum):
    """情报类型"""
    ATTACK_PATTERN = "attack_pattern"
    ATTACKER_PROFILE = "attacker_profile"
    VICTIM_PROFILE = "victim_profile"
    DEFENSE_SUCCESS = "defense_success"
    NEW_THREAT = "new_threat"
    VULNERABILITY = "vulnerability"


class IntelPriority(Enum):
    """情报优先级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IntelStatus(Enum):
    """情报状态"""
    PENDING = "pending"
    VERIFIED = "verified"
    DISPUTED = "disputed"
    EXPIRED = "expired"


@dataclass
class AttackIntel:
    """攻击情报"""
    intel_id: str
    intel_type: IntelType
    priority: IntelPriority
    content: Dict[str, Any]
    confidence: float
    source_agent: str
    timestamp: datetime
    ttl: int
    status: IntelStatus
    verification_count: int
    subscribers: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


@dataclass
class IntelSubscription:
    """情报订阅"""
    agent_id: str
    intel_types: List[IntelType]
    priority_threshold: IntelPriority
    created_at: datetime


@dataclass
class IntelBroadcastResult:
    """情报广播结果"""
    intel_id: str
    broadcast_count: int
    subscribers_notified: List[str]
    timestamp: datetime


class AttackIntelSharingAgent:
    """攻击情报共享智能体"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.name = "AttackIntelSharingAgent"
        self.config = config or {}
        self.intel_store: Dict[str, AttackIntel] = {}
        self.subscriptions: Dict[str, IntelSubscription] = {}
        self.intel_index: Dict[IntelType, Set[str]] = defaultdict(set)
        self.verification_threshold = 2
        self.default_ttl = 3600
        self.stats = {
            "total_intel_received": 0,
            "total_intel_broadcast": 0,
            "total_verifications": 0,
            "verified_intel": 0,
            "expired_intel": 0,
            "disputed_intel": 0,
        }
    
    async def initialize(self) -> bool:
        """初始化智能体"""
        await asyncio.sleep(0.1)
        self._start_cleanup_task()
        return True
    
    def _start_cleanup_task(self):
        """启动清理任务"""
        pass
    
    def create_intel(
        self,
        intel_type: IntelType,
        content: Dict[str, Any],
        source_agent: str,
        confidence: float = 0.8,
        priority: IntelPriority = IntelPriority.MEDIUM,
        ttl: Optional[int] = None,
        tags: List[str] = None
    ) -> AttackIntel:
        """创建情报"""
        content_hash = hashlib.md5(json.dumps(content, sort_keys=True).encode()).hexdigest()[:16]
        intel_id = f"intel_{intel_type.value}_{content_hash}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        intel = AttackIntel(
            intel_id=intel_id,
            intel_type=intel_type,
            priority=priority,
            content=content,
            confidence=confidence,
            source_agent=source_agent,
            timestamp=datetime.now(),
            ttl=ttl or self.default_ttl,
            status=IntelStatus.PENDING,
            verification_count=0,
            tags=tags or []
        )
        
        self.intel_store[intel_id] = intel
        self.intel_index[intel_type].add(intel_id)
        self.stats["total_intel_received"] += 1
        
        return intel
    
    def subscribe(
        self,
        agent_id: str,
        intel_types: List[IntelType],
        priority_threshold: IntelPriority = IntelPriority.LOW
    ):
        """订阅情报"""
        subscription = IntelSubscription(
            agent_id=agent_id,
            intel_types=intel_types,
            priority_threshold=priority_threshold,
            created_at=datetime.now()
        )
        
        self.subscriptions[agent_id] = subscription
    
    def unsubscribe(self, agent_id: str):
        """取消订阅"""
        if agent_id in self.subscriptions:
            del self.subscriptions[agent_id]
    
    def broadcast_intel(self, intel_id: str) -> IntelBroadcastResult:
        """广播情报"""
        intel = self.intel_store.get(intel_id)
        if not intel:
            return IntelBroadcastResult(
                intel_id=intel_id,
                broadcast_count=0,
                subscribers_notified=[],
                timestamp=datetime.now()
            )
        
        priority_order = {
            IntelPriority.LOW: 0,
            IntelPriority.MEDIUM: 1,
            IntelPriority.HIGH: 2,
            IntelPriority.CRITICAL: 3,
        }
        
        subscribers_notified = []
        
        for agent_id, subscription in self.subscriptions.items():
            if intel.intel_type in subscription.intel_types:
                if priority_order[intel.priority] >= priority_order[subscription.priority_threshold]:
                    subscribers_notified.append(agent_id)
                    intel.subscribers.append(agent_id)
        
        self.stats["total_intel_broadcast"] += 1
        
        return IntelBroadcastResult(
            intel_id=intel_id,
            broadcast_count=len(subscribers_notified),
            subscribers_notified=subscribers_notified,
            timestamp=datetime.now()
        )
    
    def verify_intel(self, intel_id: str, verifying_agent: str) -> bool:
        """验证情报"""
        intel = self.intel_store.get(intel_id)
        if not intel:
            return False
        
        self.stats["total_verifications"] += 1
        
        intel.verification_count += 1
        
        if intel.verification_count >= self.verification_threshold:
            intel.status = IntelStatus.VERIFIED
            self.stats["verified_intel"] += 1
            
            if intel.priority in [IntelPriority.HIGH, IntelPriority.CRITICAL]:
                self.broadcast_intel(intel_id)
        
        return True
    
    def dispute_intel(self, intel_id: str, disputing_agent: str, reason: str):
        """质疑情报"""
        intel = self.intel_store.get(intel_id)
        if not intel:
            return False
        
        intel.status = IntelStatus.DISPUTED
        self.stats["disputed_intel"] += 1
        
        return True
    
    def query_intel(
        self,
        intel_type: Optional[IntelType] = None,
        priority: Optional[IntelPriority] = None,
        status: Optional[IntelStatus] = None,
        tags: Optional[List[str]] = None,
        limit: int = 100
    ) -> List[AttackIntel]:
        """查询情报"""
        results = []
        
        candidate_ids = set()
        if intel_type:
            candidate_ids = self.intel_index.get(intel_type, set())
        else:
            candidate_ids = set(self.intel_store.keys())
        
        for intel_id in candidate_ids:
            intel = self.intel_store.get(intel_id)
            if not intel:
                continue
            
            if priority and intel.priority != priority:
                continue
            
            if status and intel.status != status:
                continue
            
            if tags and not any(tag in intel.tags for tag in tags):
                continue
            
            results.append(intel)
        
        results.sort(key=lambda x: x.timestamp, reverse=True)
        
        return results[:limit]
    
    def get_intel_by_id(self, intel_id: str) -> Optional[AttackIntel]:
        """根据ID获取情报"""
        return self.intel_store.get(intel_id)
    
    def get_attack_patterns(self) -> List[Dict[str, Any]]:
        """获取攻击模式"""
        patterns = self.query_intel(intel_type=IntelType.ATTACK_PATTERN, status=IntelStatus.VERIFIED)
        return [
            {
                "intel_id": p.intel_id,
                "content": p.content,
                "confidence": p.confidence,
                "timestamp": p.timestamp.isoformat(),
            }
            for p in patterns
        ]
    
    def get_attacker_profiles(self) -> List[Dict[str, Any]]:
        """获取攻击者画像"""
        profiles = self.query_intel(intel_type=IntelType.ATTACKER_PROFILE, status=IntelStatus.VERIFIED)
        return [
            {
                "intel_id": p.intel_id,
                "content": p.content,
                "confidence": p.confidence,
            }
            for p in profiles
        ]
    
    def cleanup_expired(self):
        """清理过期情报"""
        now = datetime.now()
        expired_ids = []
        
        for intel_id, intel in self.intel_store.items():
            if (now - intel.timestamp).total_seconds() > intel.ttl:
                expired_ids.append(intel_id)
        
        for intel_id in expired_ids:
            intel = self.intel_store[intel_id]
            self.intel_index[intel.intel_type].discard(intel_id)
            del self.intel_store[intel_id]
            self.stats["expired_intel"] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "total_intel_stored": len(self.intel_store),
            "total_subscriptions": len(self.subscriptions),
            "intel_by_type": {t.value: len(ids) for t, ids in self.intel_index.items()},
        }


async def share_attack_intel(
    self,
    attack_type: str,
    attack_details: Dict[str, Any],
    source_agent: str,
    confidence: float = 0.8
) -> str:
    """共享攻击情报"""
    content = {
        "attack_type": attack_type,
        "details": attack_details,
        "indicators": attack_details.get("indicators", []),
        "mitigation": attack_details.get("mitigation", []),
    }
    
    priority = IntelPriority.HIGH if confidence > 0.8 else IntelPriority.MEDIUM
    
    intel = self.create_intel(
        intel_type=IntelType.ATTACK_PATTERN,
        content=content,
        source_agent=source_agent,
        confidence=confidence,
        priority=priority,
        tags=[attack_type]
    )
    
    self.broadcast_intel(intel.intel_id)
    
    return intel.intel_id
