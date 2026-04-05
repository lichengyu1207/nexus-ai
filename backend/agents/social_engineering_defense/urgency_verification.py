"""
紧急度验证智能体
Urgency Verification Agent

负责验证用户声称的紧急情况是否真实。
"""

import asyncio
import json
import logging
import uuid
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
from enum import Enum

logger = logging.getLogger(__name__)


class UrgencyLevel(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    FALSE = "false"


class VerificationResult(Enum):
    VERIFIED = "verified"
    SUSPICIOUS = "suspicious"
    FALSE = "false"
    UNVERIFIABLE = "unverifiable"


@dataclass
class UrgencyClaim:
    claim_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    
    claim_text: str = ""
    claimed_urgency: str = UrgencyLevel.HIGH.value
    
    context: Dict = field(default_factory=dict)
    
    verification_status: str = VerificationResult.UNVERIFIABLE.value
    actual_urgency: str = UrgencyLevel.MEDIUM.value
    
    evidence_for: List[str] = field(default_factory=list)
    evidence_against: List[str] = field(default_factory=list)
    
    confidence: float = 0.0
    
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    verified_at: str = ""


class UrgencyVerificationAgent:
    """
    紧急度验证智能体
    
    功能：
    1. 紧急关键词检测：识别"紧急"、"马上"、"立刻"等词汇
    2. 上下文验证：检查是否有真实的紧急情况支撑
    3. 历史对比：对比用户历史行为模式
    4. 验证策略：对声称紧急的请求进行额外验证
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.name = "UrgencyVerificationAgent"
        self.description = "验证用户声称的紧急情况是否真实"
        self.config = config or {}
        
        self.claims: Dict[str, UrgencyClaim] = {}
        self.user_claim_history: Dict[str, List[str]] = defaultdict(list)
        
        self.urgency_keywords = self._init_urgency_keywords()
        self.legitimate_urgency_contexts = self._init_legitimate_contexts()
        
        self.stats = {
            "total_claims": 0,
            "claims_by_level": defaultdict(int),
            "verification_results": defaultdict(int),
            "false_urgency_detected": 0,
        }
        
        self._initialized = False
    
    def _init_urgency_keywords(self) -> Dict[str, float]:
        return {
            "马上": 0.8,
            "立刻": 0.8,
            "立即": 0.8,
            "紧急": 0.9,
            "急": 0.6,
            "现在": 0.5,
            "快点": 0.5,
            "等不及": 0.6,
            "immediately": 0.8,
            "urgent": 0.9,
            "now": 0.5,
            "asap": 0.7,
            "hurry": 0.6,
            "马上就要": 0.9,
            "只有几分钟": 0.8,
            "最后期限": 0.7,
            "截止": 0.6,
        }
    
    def _init_legitimate_contexts(self) -> Dict[str, List[str]]:
        return {
            "payment_due": ["账单", "缴费", "扣款", "逾期"],
            "contract_deadline": ["合同", "签约", "到期", "续签"],
            "security_alert": ["安全", "风险", "异常", "威胁"],
            "service_interruption": ["停机", "断网", "故障", "维修"],
            "legal_requirement": ["法规", "合规", "审计", "监管"],
        }
    
    async def initialize(self):
        if not self._initialized:
            await self._setup()
            self._initialized = True
            logger.info(f"Agent '{self.name}' initialized")
    
    async def _setup(self):
        pass
    
    def _detect_urgency_level(self, text: str) -> tuple:
        detected_keywords = []
        max_score = 0.0
        
        text_lower = text.lower()
        
        for keyword, score in self.urgency_keywords.items():
            if keyword in text_lower:
                detected_keywords.append(keyword)
                max_score = max(max_score, score)
        
        if max_score >= 0.8:
            level = UrgencyLevel.CRITICAL.value
        elif max_score >= 0.6:
            level = UrgencyLevel.HIGH.value
        elif max_score >= 0.4:
            level = UrgencyLevel.MEDIUM.value
        elif max_score > 0:
            level = UrgencyLevel.LOW.value
        else:
            level = UrgencyLevel.LOW.value
        
        return level, detected_keywords, max_score
    
    def _check_legitimate_context(
        self,
        text: str,
        context: Optional[Dict] = None,
    ) -> tuple:
        evidence_for = []
        evidence_against = []
        
        text_lower = text.lower()
        
        for context_type, keywords in self.legitimate_urgency_contexts.items():
            for keyword in keywords:
                if keyword in text_lower:
                    evidence_for.append(f"存在合法紧急上下文: {context_type}")
                    break
        
        if context:
            if context.get("is_business_hours", True) is False:
                evidence_against.append("非工作时间声称紧急")
            
            if context.get("similar_claims_count", 0) > 2:
                evidence_against.append("近期多次声称紧急")
        
        return evidence_for, evidence_against
    
    def _check_user_history(
        self,
        user_id: str,
    ) -> List[str]:
        evidence = []
        
        history = self.user_claim_history.get(user_id, [])
        
        if len(history) > 5:
            recent_claims = history[-10:]
            
            claim_ids = [self.claims.get(cid) for cid in recent_claims]
            claim_ids = [c for c in claim_ids if c]
            
            high_urgency_count = sum(
                1 for c in claim_ids
                if c.claimed_urgency in [UrgencyLevel.CRITICAL.value, UrgencyLevel.HIGH.value]
            )
            
            if high_urgency_count > 3:
                evidence.append("用户频繁声称紧急情况")
            
            false_count = sum(
                1 for c in claim_ids
                if c.verification_status == VerificationResult.FALSE.value
            )
            
            if false_count > 2:
                evidence.append("用户有虚假紧急声明历史")
        
        return evidence
    
    async def verify(
        self,
        text: str,
        user_id: str,
        context: Optional[Dict] = None,
    ) -> UrgencyClaim:
        self.stats["total_claims"] += 1
        
        claimed_level, keywords, score = self._detect_urgency_level(text)
        
        evidence_for, evidence_against = self._check_legitimate_context(text, context)
        
        history_evidence = self._check_user_history(user_id)
        evidence_against.extend(history_evidence)
        
        verification_status = VerificationResult.UNVERIFIABLE.value
        actual_level = claimed_level
        confidence = 0.5
        
        if claimed_level == UrgencyLevel.LOW.value:
            verification_status = VerificationResult.VERIFIED.value
            actual_level = UrgencyLevel.LOW.value
            confidence = 0.9
        elif len(evidence_for) > 0 and len(evidence_against) == 0:
            verification_status = VerificationResult.VERIFIED.value
            actual_level = claimed_level
            confidence = 0.8
        elif len(evidence_against) > len(evidence_for):
            verification_status = VerificationResult.SUSPICIOUS.value
            actual_level = UrgencyLevel.MEDIUM.value
            confidence = 0.7
            
            if len(evidence_against) >= 3:
                verification_status = VerificationResult.FALSE.value
                actual_level = UrgencyLevel.FALSE.value
                self.stats["false_urgency_detected"] += 1
        elif len(evidence_for) > 0:
            verification_status = VerificationResult.SUSPICIOUS.value
            actual_level = claimed_level
            confidence = 0.6
        else:
            verification_status = VerificationResult.UNVERIFIABLE.value
            actual_level = UrgencyLevel.MEDIUM.value
            confidence = 0.4
        
        claim = UrgencyClaim(
            user_id=user_id,
            claim_text=text[:200],
            claimed_urgency=claimed_level,
            context=context or {},
            verification_status=verification_status,
            actual_urgency=actual_level,
            evidence_for=evidence_for,
            evidence_against=evidence_against,
            confidence=confidence,
            verified_at=datetime.utcnow().isoformat(),
        )
        
        self.claims[claim.claim_id] = claim
        self.user_claim_history[user_id].append(claim.claim_id)
        
        self.stats["claims_by_level"][claimed_level] += 1
        self.stats["verification_results"][verification_status] += 1
        
        return claim
    
    async def get_verification_recommendation(
        self,
        claim: UrgencyClaim,
    ) -> Dict:
        if claim.verification_status == VerificationResult.VERIFIED.value:
            return {
                "action": "process_normally",
                "reason": "紧急情况已验证",
                "priority": claim.actual_urgency,
            }
        
        elif claim.verification_status == VerificationResult.SUSPICIOUS.value:
            return {
                "action": "require_additional_verification",
                "reason": "紧急情况可疑，需要额外验证",
                "priority": UrgencyLevel.MEDIUM.value,
                "suggested_verification": [
                    "要求用户提供更多上下文",
                    "验证用户身份",
                    "检查相关记录",
                ],
            }
        
        elif claim.verification_status == VerificationResult.FALSE.value:
            return {
                "action": "reject_or_delay",
                "reason": "检测到虚假紧急声明",
                "priority": UrgencyLevel.LOW.value,
                "warning": "建议记录并监控用户行为",
            }
        
        else:
            return {
                "action": "manual_review",
                "reason": "无法自动验证，需要人工审核",
                "priority": UrgencyLevel.MEDIUM.value,
            }
    
    async def get_user_claim_history(
        self,
        user_id: str,
        limit: int = 10,
    ) -> List[Dict]:
        claim_ids = self.user_claim_history.get(user_id, [])
        
        return [
            {
                "claim_id": self.claims[cid].claim_id,
                "claimed_urgency": self.claims[cid].claimed_urgency,
                "actual_urgency": self.claims[cid].actual_urgency,
                "verification_status": self.claims[cid].verification_status,
                "created_at": self.claims[cid].created_at,
            }
            for cid in claim_ids[-limit:]
            if cid in self.claims
        ]
    
    async def get_stats(self) -> Dict:
        return {
            "name": self.name,
            "total_claims": self.stats["total_claims"],
            "claims_by_level": dict(self.stats["claims_by_level"]),
            "verification_results": dict(self.stats["verification_results"]),
            "false_urgency_detected": self.stats["false_urgency_detected"],
        }
