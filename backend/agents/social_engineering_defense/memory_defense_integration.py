"""
记忆防御集成智能体
负责将防社会工程系统与海马体记忆系统集成
"""
import asyncio
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class MemoryType(Enum):
    """记忆类型"""
    ATTACK_MEMORY = "attack_memory"
    USER_RISK_PROFILE = "user_risk_profile"
    DEFENSE_EXPERIENCE = "defense_experience"
    PATTERN_MEMORY = "pattern_memory"
    CONTEXT_MEMORY = "context_memory"


class MemoryPriority(Enum):
    """记忆优先级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MemoryStatus(Enum):
    """记忆状态"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    QUARANTINED = "quarantined"
    DELETED = "deleted"


@dataclass
class DefenseMemory:
    """防御记忆"""
    memory_id: str
    memory_type: MemoryType
    content: Dict[str, Any]
    priority: MemoryPriority
    confidence: float
    source: str
    created_at: datetime
    last_accessed: datetime
    access_count: int
    status: MemoryStatus
    tags: List[str] = field(default_factory=list)
    related_memories: List[str] = field(default_factory=list)


@dataclass
class UserRiskProfile:
    """用户风险画像"""
    user_id: str
    risk_score: float
    attack_attempts: int
    vulnerability_factors: List[str]
    protection_level: str
    last_attack: Optional[datetime]
    created_at: datetime
    updated_at: datetime


@dataclass
class AttackMemoryEntry:
    """攻击记忆条目"""
    attack_id: str
    attack_type: str
    attack_features: Dict[str, Any]
    attacker_profile: Dict[str, Any]
    defense_strategy: str
    defense_success: bool
    timestamp: datetime
    user_id: str


class MemoryDefenseIntegrationAgent:
    """记忆防御集成智能体"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.name = "MemoryDefenseIntegrationAgent"
        self.config = config or {}
        self.memories: Dict[str, DefenseMemory] = {}
        self.user_profiles: Dict[str, UserRiskProfile] = {}
        self.attack_memories: List[AttackMemoryEntry] = []
        self.memory_index: Dict[MemoryType, Set[str]] = defaultdict(set)
        self.tag_index: Dict[str, Set[str]] = defaultdict(set)
        self.memory_counter = 0
        self.stats = {
            "total_memories": 0,
            "memories_by_type": defaultdict(int),
            "attack_memories_stored": 0,
            "profiles_created": 0,
            "memories_quarantined": 0,
            "queries_processed": 0,
        }
    
    async def initialize(self) -> bool:
        """初始化智能体"""
        await asyncio.sleep(0.1)
        return True
    
    def store_attack_memory(
        self,
        attack_type: str,
        attack_features: Dict[str, Any],
        attacker_profile: Dict[str, Any],
        defense_strategy: str,
        defense_success: bool,
        user_id: str
    ) -> AttackMemoryEntry:
        """存储攻击记忆"""
        self.memory_counter += 1
        attack_id = f"attack_{datetime.now().strftime('%Y%m%d%H%M%S')}_{self.memory_counter}"
        
        entry = AttackMemoryEntry(
            attack_id=attack_id,
            attack_type=attack_type,
            attack_features=attack_features,
            attacker_profile=attacker_profile,
            defense_strategy=defense_strategy,
            defense_success=defense_success,
            timestamp=datetime.now(),
            user_id=user_id
        )
        
        self.attack_memories.append(entry)
        self.stats["attack_memories_stored"] += 1
        
        memory = DefenseMemory(
            memory_id=f"mem_{attack_id}",
            memory_type=MemoryType.ATTACK_MEMORY,
            content={
                "attack_type": attack_type,
                "features": attack_features,
                "defense_strategy": defense_strategy,
                "success": defense_success
            },
            priority=MemoryPriority.HIGH if not defense_success else MemoryPriority.MEDIUM,
            confidence=0.9,
            source="defense_system",
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            access_count=1,
            status=MemoryStatus.ACTIVE,
            tags=[attack_type, "attack", "defense"]
        )
        
        self._store_memory(memory)
        
        return entry
    
    def _store_memory(self, memory: DefenseMemory):
        """存储记忆"""
        self.memories[memory.memory_id] = memory
        self.memory_index[memory.memory_type].add(memory.memory_id)
        
        for tag in memory.tags:
            self.tag_index[tag.lower()].add(memory.memory_id)
        
        self.stats["total_memories"] += 1
        self.stats["memories_by_type"][memory.memory_type.value] += 1
    
    def update_user_risk_profile(
        self,
        user_id: str,
        risk_delta: float,
        attack_attempt: bool = False,
        vulnerability_factors: List[str] = None
    ) -> UserRiskProfile:
        """更新用户风险画像"""
        if user_id not in self.user_profiles:
            profile = UserRiskProfile(
                user_id=user_id,
                risk_score=50.0,
                attack_attempts=0,
                vulnerability_factors=[],
                protection_level="standard",
                last_attack=None,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            self.user_profiles[user_id] = profile
            self.stats["profiles_created"] += 1
        
        profile = self.user_profiles[user_id]
        
        profile.risk_score = max(0, min(100, profile.risk_score + risk_delta))
        
        if attack_attempt:
            profile.attack_attempts += 1
            profile.last_attack = datetime.now()
        
        if vulnerability_factors:
            for factor in vulnerability_factors:
                if factor not in profile.vulnerability_factors:
                    profile.vulnerability_factors.append(factor)
        
        if profile.risk_score >= 70:
            profile.protection_level = "enhanced"
        elif profile.risk_score >= 40:
            profile.protection_level = "standard"
        else:
            profile.protection_level = "basic"
        
        profile.updated_at = datetime.now()
        
        memory = DefenseMemory(
            memory_id=f"profile_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            memory_type=MemoryType.USER_RISK_PROFILE,
            content={
                "risk_score": profile.risk_score,
                "attack_attempts": profile.attack_attempts,
                "protection_level": profile.protection_level
            },
            priority=MemoryPriority.MEDIUM,
            confidence=0.8,
            source="risk_analysis",
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            access_count=1,
            status=MemoryStatus.ACTIVE,
            tags=["user_profile", "risk"]
        )
        
        self._store_memory(memory)
        
        return profile
    
    def store_defense_experience(
        self,
        experience_type: str,
        context: Dict[str, Any],
        action_taken: str,
        outcome: str,
        lessons_learned: List[str]
    ) -> DefenseMemory:
        """存储防御经验"""
        self.memory_counter += 1
        memory_id = f"exp_{datetime.now().strftime('%Y%m%d%H%M%S')}_{self.memory_counter}"
        
        memory = DefenseMemory(
            memory_id=memory_id,
            memory_type=MemoryType.DEFENSE_EXPERIENCE,
            content={
                "experience_type": experience_type,
                "context": context,
                "action_taken": action_taken,
                "outcome": outcome,
                "lessons_learned": lessons_learned
            },
            priority=MemoryPriority.HIGH if outcome == "success" else MemoryPriority.CRITICAL,
            confidence=0.9,
            source="defense_agent",
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            access_count=1,
            status=MemoryStatus.ACTIVE,
            tags=[experience_type, "experience", outcome]
        )
        
        self._store_memory(memory)
        
        return memory
    
    def query_similar_attacks(
        self,
        attack_features: Dict[str, Any],
        limit: int = 10
    ) -> List[AttackMemoryEntry]:
        """查询相似攻击"""
        self.stats["queries_processed"] += 1
        
        results = []
        
        for entry in self.attack_memories:
            similarity = self._calculate_similarity(attack_features, entry.attack_features)
            if similarity > 0.3:
                results.append((entry, similarity))
        
        results.sort(key=lambda x: x[1], reverse=True)
        
        return [r[0] for r in results[:limit]]
    
    def _calculate_similarity(
        self, 
        features1: Dict[str, Any], 
        features2: Dict[str, Any]
    ) -> float:
        """计算相似度"""
        if not features1 or not features2:
            return 0.0
        
        common_keys = set(features1.keys()) & set(features2.keys())
        if not common_keys:
            return 0.0
        
        matches = 0
        for key in common_keys:
            if features1[key] == features2[key]:
                matches += 1
            elif isinstance(features1[key], str) and isinstance(features2[key], str):
                if features1[key].lower() in features2[key].lower() or features2[key].lower() in features1[key].lower():
                    matches += 0.5
        
        return matches / len(common_keys)
    
    def get_user_profile(self, user_id: str) -> Optional[UserRiskProfile]:
        """获取用户画像"""
        return self.user_profiles.get(user_id)
    
    def detect_memory_pollution(self) -> List[Dict[str, Any]]:
        """检测记忆污染"""
        polluted = []
        
        for memory_id, memory in self.memories.items():
            if memory.status == MemoryStatus.QUARANTINED:
                continue
            
            if self._check_pollution_indicators(memory):
                polluted.append({
                    "memory_id": memory_id,
                    "memory_type": memory.memory_type.value,
                    "indicators": self._get_pollution_indicators(memory),
                    "confidence": 0.7
                })
        
        return polluted
    
    def _check_pollution_indicators(self, memory: DefenseMemory) -> bool:
        """检查污染指标"""
        content_str = str(memory.content).lower()
        
        pollution_patterns = [
            "忽略规则", "忘记", "新规则",
            "覆盖", "绕过", "豁免"
        ]
        
        for pattern in pollution_patterns:
            if pattern in content_str:
                return True
        
        return False
    
    def _get_pollution_indicators(self, memory: DefenseMemory) -> List[str]:
        """获取污染指标"""
        indicators = []
        content_str = str(memory.content).lower()
        
        pollution_patterns = [
            "忽略规则", "忘记", "新规则",
            "覆盖", "绕过", "豁免"
        ]
        
        for pattern in pollution_patterns:
            if pattern in content_str:
                indicators.append(f"包含可疑模式: {pattern}")
        
        return indicators
    
    def quarantine_memory(self, memory_id: str) -> bool:
        """隔离记忆"""
        memory = self.memories.get(memory_id)
        if not memory:
            return False
        
        memory.status = MemoryStatus.QUARANTINED
        self.stats["memories_quarantined"] += 1
        
        return True
    
    def clear_quarantined_memories(self):
        """清除隔离记忆"""
        to_delete = [
            mid for mid, m in self.memories.items()
            if m.status == MemoryStatus.QUARANTINED
        ]
        
        for mid in to_delete:
            memory = self.memories[mid]
            self.memory_index[memory.memory_type].discard(mid)
            for tag in memory.tags:
                self.tag_index[tag.lower()].discard(mid)
            del self.memories[mid]
    
    def get_defense_experiences(
        self, 
        experience_type: str = None,
        limit: int = 20
    ) -> List[DefenseMemory]:
        """获取防御经验"""
        memories = [
            m for m in self.memories.values()
            if m.memory_type == MemoryType.DEFENSE_EXPERIENCE
            and m.status == MemoryStatus.ACTIVE
        ]
        
        if experience_type:
            memories = [
                m for m in memories
                if m.content.get("experience_type") == experience_type
            ]
        
        return sorted(memories, key=lambda x: x.created_at, reverse=True)[:limit]
    
    def share_to_swarm(self, memory_id: str) -> Dict[str, Any]:
        """共享到蜂群"""
        memory = self.memories.get(memory_id)
        if not memory:
            return {"status": "error", "message": "Memory not found"}
        
        return {
            "status": "shared",
            "memory_id": memory_id,
            "memory_type": memory.memory_type.value,
            "content": memory.content,
            "confidence": memory.confidence,
            "shared_at": datetime.now().isoformat()
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计"""
        return {
            **self.stats,
            "memories_by_type": dict(self.stats["memories_by_type"]),
            "total_user_profiles": len(self.user_profiles),
            "total_attack_memories": len(self.attack_memories),
        }
