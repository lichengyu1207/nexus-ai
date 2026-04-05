"""
身份信任评分智能体
Identity Trust Score Agent

负责综合评估用户身份的可信度。
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


class TrustLevel(Enum):
    VERY_HIGH = "very_high"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    VERY_LOW = "very_low"
    UNTRUSTED = "untrusted"


class FactorCategory(Enum):
    AUTHENTICATION = "authentication"
    BEHAVIOR = "behavior"
    DEVICE = "device"
    NETWORK = "network"
    HISTORY = "history"


@dataclass
class TrustFactor:
    factor_id: str = ""
    category: str = ""
    name: str = ""
    value: float = 0.0
    weight: float = 1.0
    max_value: float = 100.0
    description: str = ""
    last_updated: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class TrustScore:
    score_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    
    total_score: float = 0.0
    trust_level: str = TrustLevel.MEDIUM.value
    
    factors: List[TrustFactor] = field(default_factory=list)
    
    risk_factors: List[str] = field(default_factory=list)
    positive_factors: List[str] = field(default_factory=list)
    
    recommendations: List[str] = field(default_factory=list)
    
    calculated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    expires_at: str = ""


class IdentityTrustScoreAgent:
    """
    身份信任评分智能体
    
    功能：
    1. 多维度评分：认证历史、行为模式、设备信任、网络环境
    2. 动态调整：根据最新行为实时更新信任分
    3. 风险预警：信任分骤降时触发预警
    4. 信任恢复：长时间正常行为可恢复信任分
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.name = "IdentityTrustScoreAgent"
        self.description = "综合评估用户身份的可信度"
        self.config = config or {}
        
        self.trust_scores: Dict[str, TrustScore] = {}
        self.user_history: Dict[str, List[str]] = defaultdict(list)
        
        self.factor_weights = {
            FactorCategory.AUTHENTICATION.value: 0.3,
            FactorCategory.BEHAVIOR.value: 0.25,
            FactorCategory.DEVICE.value: 0.2,
            FactorCategory.NETWORK.value: 0.15,
            FactorCategory.HISTORY.value: 0.1,
        }
        
        self.trust_thresholds = {
            TrustLevel.VERY_HIGH.value: 90,
            TrustLevel.HIGH.value: 75,
            TrustLevel.MEDIUM.value: 50,
            TrustLevel.LOW.value: 25,
            TrustLevel.VERY_LOW.value: 10,
        }
        
        self.trust_decay_rate = 0.01
        self.trust_recovery_rate = 0.02
        
        self.stats = {
            "total_calculations": 0,
            "scores_by_level": defaultdict(int),
            "risk_alerts": 0,
            "trust_recoveries": 0,
        }
        
        self._initialized = False
    
    async def initialize(self):
        if not self._initialized:
            await self._setup()
            self._initialized = True
            logger.info(f"Agent '{self.name}' initialized")
    
    async def _setup(self):
        asyncio.create_task(self._periodic_decay())
    
    async def _periodic_decay(self):
        while True:
            await asyncio.sleep(86400)
            await self._apply_trust_decay()
    
    async def _apply_trust_decay(self):
        for user_id, score in self.trust_scores.items():
            if score.total_score > 50:
                score.total_score -= self.trust_decay_rate * score.total_score
                score.trust_level = self._determine_trust_level(score.total_score)
    
    def _determine_trust_level(self, score: float) -> str:
        if score >= self.trust_thresholds[TrustLevel.VERY_HIGH.value]:
            return TrustLevel.VERY_HIGH.value
        elif score >= self.trust_thresholds[TrustLevel.HIGH.value]:
            return TrustLevel.HIGH.value
        elif score >= self.trust_thresholds[TrustLevel.MEDIUM.value]:
            return TrustLevel.MEDIUM.value
        elif score >= self.trust_thresholds[TrustLevel.LOW.value]:
            return TrustLevel.LOW.value
        elif score >= self.trust_thresholds[TrustLevel.VERY_LOW.value]:
            return TrustLevel.VERY_LOW.value
        else:
            return TrustLevel.UNTRUSTED.value
    
    async def calculate_trust_score(
        self,
        user_id: str,
        auth_data: Optional[Dict] = None,
        behavior_data: Optional[Dict] = None,
        device_data: Optional[Dict] = None,
        network_data: Optional[Dict] = None,
    ) -> TrustScore:
        self.stats["total_calculations"] += 1
        
        factors = []
        risk_factors = []
        positive_factors = []
        
        auth_score = self._calculate_auth_factor(auth_data or {})
        factors.append(TrustFactor(
            factor_id="auth_main",
            category=FactorCategory.AUTHENTICATION.value,
            name="认证状态",
            value=auth_score,
            weight=self.factor_weights[FactorCategory.AUTHENTICATION.value],
        ))
        if auth_score < 50:
            risk_factors.append("认证状态不佳")
        elif auth_score > 80:
            positive_factors.append("认证状态良好")
        
        behavior_score = self._calculate_behavior_factor(behavior_data or {})
        factors.append(TrustFactor(
            factor_id="behavior_main",
            category=FactorCategory.BEHAVIOR.value,
            name="行为模式",
            value=behavior_score,
            weight=self.factor_weights[FactorCategory.BEHAVIOR.value],
        ))
        if behavior_score < 50:
            risk_factors.append("行为模式异常")
        elif behavior_score > 80:
            positive_factors.append("行为模式正常")
        
        device_score = self._calculate_device_factor(device_data or {})
        factors.append(TrustFactor(
            factor_id="device_main",
            category=FactorCategory.DEVICE.value,
            name="设备信任",
            value=device_score,
            weight=self.factor_weights[FactorCategory.DEVICE.value],
        ))
        if device_score < 50:
            risk_factors.append("设备不可信")
        elif device_score > 80:
            positive_factors.append("设备可信")
        
        network_score = self._calculate_network_factor(network_data or {})
        factors.append(TrustFactor(
            factor_id="network_main",
            category=FactorCategory.NETWORK.value,
            name="网络环境",
            value=network_score,
            weight=self.factor_weights[FactorCategory.NETWORK.value],
        ))
        if network_score < 50:
            risk_factors.append("网络环境可疑")
        elif network_score > 80:
            positive_factors.append("网络环境安全")
        
        history_score = await self._calculate_history_factor(user_id)
        factors.append(TrustFactor(
            factor_id="history_main",
            category=FactorCategory.HISTORY.value,
            name="历史记录",
            value=history_score,
            weight=self.factor_weights[FactorCategory.HISTORY.value],
        ))
        if history_score > 80:
            positive_factors.append("历史记录良好")
        
        total_score = sum(f.value * f.weight for f in factors)
        
        previous_score = self.trust_scores.get(user_id)
        if previous_score:
            score_change = total_score - previous_score.total_score
            if score_change < -20:
                self.stats["risk_alerts"] += 1
                risk_factors.append(f"信任分骤降{abs(score_change):.1f}分")
            elif score_change > 10:
                self.stats["trust_recoveries"] += 1
        
        trust_level = self._determine_trust_level(total_score)
        self.stats["scores_by_level"][trust_level] += 1
        
        recommendations = self._generate_recommendations(risk_factors, trust_level)
        
        score = TrustScore(
            user_id=user_id,
            total_score=total_score,
            trust_level=trust_level,
            factors=factors,
            risk_factors=risk_factors,
            positive_factors=positive_factors,
            recommendations=recommendations,
            expires_at=(datetime.utcnow() + timedelta(hours=24)).isoformat(),
        )
        
        self.trust_scores[user_id] = score
        self.user_history[user_id].append(score.score_id)
        
        return score
    
    def _calculate_auth_factor(self, auth_data: Dict) -> float:
        score = 50.0
        
        if auth_data.get("mfa_enabled", False):
            score += 20
        
        if auth_data.get("last_auth_success", False):
            score += 10
        
        failed_attempts = auth_data.get("failed_attempts", 0)
        score -= min(30, failed_attempts * 10)
        
        if auth_data.get("password_age_days", 365) < 90:
            score += 5
        
        return max(0, min(100, score))
    
    def _calculate_behavior_factor(self, behavior_data: Dict) -> float:
        score = 50.0
        
        if behavior_data.get("typing_match", False):
            score += 15
        
        if behavior_data.get("mouse_match", False):
            score += 15
        
        if behavior_data.get("navigation_match", False):
            score += 10
        
        anomalies = behavior_data.get("anomaly_count", 0)
        score -= min(40, anomalies * 10)
        
        return max(0, min(100, score))
    
    def _calculate_device_factor(self, device_data: Dict) -> float:
        score = 50.0
        
        if device_data.get("is_known_device", False):
            score += 30
        
        if device_data.get("fingerprint_match", False):
            score += 10
        
        if device_data.get("has_security_software", False):
            score += 5
        
        if device_data.get("is_rooted", False):
            score -= 30
        
        return max(0, min(100, score))
    
    def _calculate_network_factor(self, network_data: Dict) -> float:
        score = 50.0
        
        if network_data.get("is_known_ip", False):
            score += 20
        
        if network_data.get("is_vpn", False):
            score -= 20
        
        if network_data.get("is_proxy", False):
            score -= 15
        
        if network_data.get("is_tor", False):
            score -= 40
        
        if network_data.get("is_known_location", False):
            score += 10
        
        return max(0, min(100, score))
    
    async def _calculate_history_factor(self, user_id: str) -> float:
        score = 50.0
        
        history = self.user_history.get(user_id, [])
        
        if len(history) > 30:
            score += 20
        elif len(history) > 10:
            score += 10
        
        if history:
            recent_scores = [
                self.trust_scores.get(sid)
                for sid in history[-10:]
            ]
            recent_scores = [s for s in recent_scores if s]
            
            if recent_scores:
                avg_score = sum(s.total_score for s in recent_scores) / len(recent_scores)
                if avg_score > 70:
                    score += 15
                elif avg_score > 50:
                    score += 5
        
        return max(0, min(100, score))
    
    def _generate_recommendations(
        self,
        risk_factors: List[str],
        trust_level: str,
    ) -> List[str]:
        recommendations = []
        
        if trust_level in [TrustLevel.LOW.value, TrustLevel.VERY_LOW.value]:
            recommendations.append("建议进行多因素认证")
        
        if "认证状态不佳" in risk_factors:
            recommendations.append("建议更新密码或重新认证")
        
        if "行为模式异常" in risk_factors:
            recommendations.append("建议进行身份验证")
        
        if "设备不可信" in risk_factors:
            recommendations.append("建议在可信设备上操作")
        
        if "网络环境可疑" in risk_factors:
            recommendations.append("建议使用安全网络")
        
        return recommendations
    
    async def get_trust_score(self, user_id: str) -> Optional[Dict]:
        score = self.trust_scores.get(user_id)
        if not score:
            return None
        
        return {
            "user_id": score.user_id,
            "total_score": score.total_score,
            "trust_level": score.trust_level,
            "risk_factors": score.risk_factors,
            "positive_factors": score.positive_factors,
            "recommendations": score.recommendations,
            "calculated_at": score.calculated_at,
        }
    
    async def record_positive_event(
        self,
        user_id: str,
        event_type: str,
    ) -> bool:
        score = self.trust_scores.get(user_id)
        if not score:
            return False
        
        recovery = self.trust_recovery_rate * 10
        
        if event_type == "successful_mfa":
            recovery *= 2
        elif event_type == "password_change":
            recovery *= 1.5
        
        score.total_score = min(100, score.total_score + recovery)
        score.trust_level = self._determine_trust_level(score.total_score)
        
        return True
    
    async def record_negative_event(
        self,
        user_id: str,
        event_type: str,
    ) -> bool:
        score = self.trust_scores.get(user_id)
        if not score:
            return False
        
        penalty = 10
        
        if event_type == "failed_auth":
            penalty = 15
        elif event_type == "suspicious_behavior":
            penalty = 20
        elif event_type == "security_incident":
            penalty = 30
        
        score.total_score = max(0, score.total_score - penalty)
        score.trust_level = self._determine_trust_level(score.total_score)
        score.risk_factors.append(f"负面事件: {event_type}")
        
        return True
    
    async def get_stats(self) -> Dict:
        return {
            "name": self.name,
            "total_calculations": self.stats["total_calculations"],
            "scores_by_level": dict(self.stats["scores_by_level"]),
            "risk_alerts": self.stats["risk_alerts"],
            "trust_recoveries": self.stats["trust_recoveries"],
        }
