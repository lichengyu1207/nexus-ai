"""
审计知识共享智能体
Audit Knowledge Sharing Agent

负责审计智能体之间的知识共享。
"""

import asyncio
import json
import logging
import hashlib
import uuid
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
from enum import Enum

logger = logging.getLogger(__name__)


class KnowledgeType(Enum):
    ATTACK_PATTERN = "attack_pattern"
    AUDIT_RULE = "audit_rule"
    REGULATION_UPDATE = "regulation_update"
    BEST_PRACTICE = "best_practice"
    CASE_STUDY = "case_study"
    THREAT_INTEL = "threat_intel"


class KnowledgeStatus(Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"
    VERIFIED = "verified"


@dataclass
class KnowledgeItem:
    knowledge_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    knowledge_type: str = ""
    title: str = ""
    content: str = ""
    
    source_node: str = ""
    author: str = ""
    
    tags: List[str] = field(default_factory=list)
    category: str = ""
    
    status: str = KnowledgeStatus.DRAFT.value
    verification_score: float = 0.0
    usage_count: int = 0
    
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    published_at: str = ""
    
    votes: int = 0
    feedback: List[str] = field(default_factory=list)


@dataclass
class KnowledgeSync:
    sync_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    source_node: str = ""
    target_nodes: List[str] = field(default_factory=list)
    
    knowledge_ids: List[str] = field(default_factory=list)
    sync_type: str = "push"
    
    status: str = "pending"
    completed_at: str = ""


class AuditKnowledgeSharingAgent:
    """
    审计知识共享智能体
    
    功能：
    1. 知识类型：攻击模式、审计规则、法规更新
    2. 共享机制：通过消息总线广播，定期同步到全局图谱
    3. 学习机制：接收其他审计智能体的经验，更新本地检测模型
    4. 知识图谱：构建全局审计知识图谱
    5. 激励机制：贡献高质量知识的智能体获得奖励
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.name = "AuditKnowledgeSharingAgent"
        self.description = "负责审计智能体之间的知识共享"
        self.config = config or {}
        
        self.knowledge_base: Dict[str, KnowledgeItem] = {}
        self.knowledge_by_type: Dict[str, List[str]] = defaultdict(list)
        self.knowledge_by_tag: Dict[str, List[str]] = defaultdict(list)
        
        self.sync_records: Dict[str, KnowledgeSync] = []
        
        self.node_contributions: Dict[str, Dict] = defaultdict(lambda: {
            "total": 0,
            "verified": 0,
            "votes_received": 0,
            "reputation": 0.0,
        })
        
        self.incentive_rules = {
            "publish_base": 10,
            "verified_bonus": 20,
            "vote_bonus": 2,
            "usage_bonus": 1,
        }
        
        self.stats = {
            "total_knowledge": 0,
            "knowledge_by_type": defaultdict(int),
            "knowledge_by_status": defaultdict(int),
            "total_syncs": 0,
            "successful_syncs": 0,
            "total_contributions": 0,
        }
        
        self._initialized = False
    
    async def initialize(self):
        if not self._initialized:
            await self._setup()
            self._initialized = True
            logger.info(f"Agent '{self.name}' initialized")
    
    async def _setup(self):
        asyncio.create_task(self._periodic_sync())
        self._init_default_knowledge()
    
    def _init_default_knowledge(self):
        default_knowledge = [
            {
                "type": KnowledgeType.ATTACK_PATTERN.value,
                "title": "SQL注入攻击模式",
                "content": "检测SQL注入攻击的常见模式：union select, or 1=1, drop table等",
                "tags": ["sql", "injection", "web"],
            },
            {
                "type": KnowledgeType.ATTACK_PATTERN.value,
                "title": "XSS攻击模式",
                "content": "检测XSS攻击的常见模式：<script>, javascript:, onerror=等",
                "tags": ["xss", "injection", "web"],
            },
            {
                "type": KnowledgeType.AUDIT_RULE.value,
                "title": "数据访问审计规则",
                "content": "审计数据访问时应检查：授权状态、访问范围、访问频率",
                "tags": ["audit", "data_access", "compliance"],
            },
            {
                "type": KnowledgeType.REGULATION_UPDATE.value,
                "title": "个人信息保护法要点",
                "content": "个保法核心要求：合法正当必要原则、用户同意、最小化原则",
                "tags": ["pipl", "compliance", "privacy"],
            },
        ]
        
        for item in default_knowledge:
            knowledge = KnowledgeItem(
                knowledge_type=item["type"],
                title=item["title"],
                content=item["content"],
                tags=item["tags"],
                source_node="system",
                author="system",
                status=KnowledgeStatus.VERIFIED.value,
                verification_score=1.0,
            )
            
            self._add_knowledge(knowledge)
    
    def _add_knowledge(self, knowledge: KnowledgeItem):
        self.knowledge_base[knowledge.knowledge_id] = knowledge
        self.knowledge_by_type[knowledge.knowledge_type].append(knowledge.knowledge_id)
        
        for tag in knowledge.tags:
            self.knowledge_by_tag[tag].append(knowledge.knowledge_id)
        
        self.stats["total_knowledge"] += 1
        self.stats["knowledge_by_type"][knowledge.knowledge_type] += 1
        self.stats["knowledge_by_status"][knowledge.status] += 1
    
    async def _periodic_sync(self):
        while True:
            await asyncio.sleep(3600)
            await self._sync_with_global_graph()
    
    async def publish_knowledge(
        self,
        knowledge_type: str,
        title: str,
        content: str,
        source_node: str,
        author: str = "",
        tags: Optional[List[str]] = None,
        category: str = "",
    ) -> KnowledgeItem:
        knowledge = KnowledgeItem(
            knowledge_type=knowledge_type,
            title=title,
            content=content,
            source_node=source_node,
            author=author or source_node,
            tags=tags or [],
            category=category,
            status=KnowledgeStatus.PUBLISHED.value,
            published_at=datetime.utcnow().isoformat(),
        )
        
        self._add_knowledge(knowledge)
        
        self.node_contributions[source_node]["total"] += 1
        self.stats["total_contributions"] += 1
        
        await self._award_incentive(source_node, "publish_base")
        
        await self._broadcast_knowledge(knowledge)
        
        return knowledge
    
    async def _broadcast_knowledge(self, knowledge: KnowledgeItem):
        logger.info(f"Broadcasting knowledge: {knowledge.title}")
    
    async def _award_incentive(self, node: str, incentive_type: str):
        points = self.incentive_rules.get(incentive_type, 0)
        self.node_contributions[node]["reputation"] += points
    
    async def search_knowledge(
        self,
        query: str,
        knowledge_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 20,
    ) -> List[Dict]:
        results = []
        
        for knowledge in self.knowledge_base.values():
            if knowledge.status == KnowledgeStatus.DEPRECATED.value:
                continue
            
            if knowledge_type and knowledge.knowledge_type != knowledge_type:
                continue
            
            if tags:
                if not all(tag in knowledge.tags for tag in tags):
                    continue
            
            relevance = self._calculate_relevance(query, knowledge)
            
            if relevance > 0:
                results.append((knowledge, relevance))
        
        results.sort(key=lambda x: x[1], reverse=True)
        
        return [
            {
                "knowledge_id": k.knowledge_id,
                "type": k.knowledge_type,
                "title": k.title,
                "content": k.content[:200],
                "tags": k.tags,
                "verification_score": k.verification_score,
                "usage_count": k.usage_count,
                "relevance": r,
            }
            for k, r in results[:limit]
        ]
    
    def _calculate_relevance(self, query: str, knowledge: KnowledgeItem) -> float:
        score = 0.0
        query_lower = query.lower()
        
        if query_lower in knowledge.title.lower():
            score += 0.5
        
        if query_lower in knowledge.content.lower():
            score += 0.3
        
        for tag in knowledge.tags:
            if query_lower in tag.lower():
                score += 0.2
        
        score += knowledge.verification_score * 0.1
        
        return min(1.0, score)
    
    async def get_knowledge(self, knowledge_id: str) -> Optional[Dict]:
        knowledge = self.knowledge_base.get(knowledge_id)
        if not knowledge:
            return None
        
        knowledge.usage_count += 1
        
        await self._award_incentive(knowledge.source_node, "usage_bonus")
        
        return {
            "knowledge_id": knowledge.knowledge_id,
            "type": knowledge.knowledge_type,
            "title": knowledge.title,
            "content": knowledge.content,
            "tags": knowledge.tags,
            "category": knowledge.category,
            "status": knowledge.status,
            "verification_score": knowledge.verification_score,
            "usage_count": knowledge.usage_count,
            "source_node": knowledge.source_node,
            "created_at": knowledge.created_at,
        }
    
    async def verify_knowledge(
        self,
        knowledge_id: str,
        verifier_node: str,
        is_valid: bool,
    ) -> bool:
        knowledge = self.knowledge_base.get(knowledge_id)
        if not knowledge:
            return False
        
        if is_valid:
            knowledge.verification_score = min(1.0, knowledge.verification_score + 0.2)
            
            if knowledge.verification_score >= 0.8:
                knowledge.status = KnowledgeStatus.VERIFIED.value
                self.stats["knowledge_by_status"][KnowledgeStatus.PUBLISHED.value] -= 1
                self.stats["knowledge_by_status"][KnowledgeStatus.VERIFIED.value] += 1
                
                self.node_contributions[knowledge.source_node]["verified"] += 1
                await self._award_incentive(knowledge.source_node, "verified_bonus")
        else:
            knowledge.verification_score = max(0.0, knowledge.verification_score - 0.3)
        
        return True
    
    async def vote_knowledge(
        self,
        knowledge_id: str,
        voter_node: str,
    ) -> bool:
        knowledge = self.knowledge_base.get(knowledge_id)
        if not knowledge:
            return False
        
        knowledge.votes += 1
        
        self.node_contributions[knowledge.source_node]["votes_received"] += 1
        await self._award_incentive(knowledge.source_node, "vote_bonus")
        
        return True
    
    async def add_feedback(
        self,
        knowledge_id: str,
        feedback: str,
        feedback_node: str,
    ) -> bool:
        knowledge = self.knowledge_base.get(knowledge_id)
        if not knowledge:
            return False
        
        knowledge.feedback.append(f"[{feedback_node}] {feedback}")
        knowledge.updated_at = datetime.utcnow().isoformat()
        
        return True
    
    async def deprecate_knowledge(
        self,
        knowledge_id: str,
        reason: str,
    ) -> bool:
        knowledge = self.knowledge_base.get(knowledge_id)
        if not knowledge:
            return False
        
        knowledge.status = KnowledgeStatus.DEPRECATED.value
        knowledge.feedback.append(f"Deprecated: {reason}")
        knowledge.updated_at = datetime.utcnow().isoformat()
        
        self.stats["knowledge_by_status"][KnowledgeStatus.VERIFIED.value] -= 1
        self.stats["knowledge_by_status"][KnowledgeStatus.DEPRECATED.value] += 1
        
        return True
    
    async def _sync_with_global_graph(self):
        sync = KnowledgeSync(
            source_node="local",
            target_nodes=["global"],
            knowledge_ids=list(self.knowledge_base.keys())[-100:],
            sync_type="push",
        )
        
        self.sync_records.append(sync)
        self.stats["total_syncs"] += 1
        
        sync.status = "completed"
        sync.completed_at = datetime.utcnow().isoformat()
        self.stats["successful_syncs"] += 1
    
    async def receive_knowledge(
        self,
        knowledge_items: List[Dict],
        source_node: str,
    ) -> Dict:
        received_count = 0
        
        for item in knowledge_items:
            knowledge = KnowledgeItem(
                knowledge_type=item.get("type", ""),
                title=item.get("title", ""),
                content=item.get("content", ""),
                source_node=source_node,
                tags=item.get("tags", []),
                status=KnowledgeStatus.PUBLISHED.value,
            )
            
            existing = self._find_similar_knowledge(knowledge)
            if not existing:
                self._add_knowledge(knowledge)
                received_count += 1
        
        return {
            "received": received_count,
            "total": len(knowledge_items),
        }
    
    def _find_similar_knowledge(self, knowledge: KnowledgeItem) -> Optional[KnowledgeItem]:
        for existing in self.knowledge_base.values():
            if existing.title == knowledge.title:
                return existing
            if existing.content == knowledge.content:
                return existing
        return None
    
    async def get_node_reputation(self, node: str) -> Dict:
        contrib = self.node_contributions.get(node, {})
        
        return {
            "node": node,
            "total_contributions": contrib.get("total", 0),
            "verified_contributions": contrib.get("verified", 0),
            "votes_received": contrib.get("votes_received", 0),
            "reputation_score": contrib.get("reputation", 0.0),
        }
    
    async def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        nodes = sorted(
            self.node_contributions.items(),
            key=lambda x: x[1]["reputation"],
            reverse=True
        )
        
        return [
            {
                "rank": i + 1,
                "node": node,
                "reputation": data["reputation"],
                "contributions": data["total"],
            }
            for i, (node, data) in enumerate(nodes[:limit])
        ]
    
    async def get_stats(self) -> Dict:
        return {
            "name": self.name,
            "total_knowledge": self.stats["total_knowledge"],
            "knowledge_by_type": dict(self.stats["knowledge_by_type"]),
            "knowledge_by_status": dict(self.stats["knowledge_by_status"]),
            "total_syncs": self.stats["total_syncs"],
            "successful_syncs": self.stats["successful_syncs"],
            "total_contributions": self.stats["total_contributions"],
        }
